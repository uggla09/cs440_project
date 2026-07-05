import re
from datetime import date
from decimal import Decimal
import mysql.connector
import json
import hashlib
import tkinter as tk
from tkinter import messagebox, ttk

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CATEGORY_PATTERN = re.compile(r"^[a-z]+$")
ERR_MSG_DURATION = 3000
MAX_ITEMS_PER_DAY = 2
MAX_REVIEWS_PER_DAY = 2
REVIEW_SCORES = ("Excellent", "Good", "Fair", "Poor")
JULY_FOURTH_2024 = date(2024, 7, 4)
REQUIRED_TABLES = ("user", "item", "category", "item_category", "review")
_err_after_id = None

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS user (
      username VARCHAR(255) PRIMARY KEY,
      password VARCHAR(255) NOT NULL,
      firstName VARCHAR(255) NOT NULL,
      lastName VARCHAR(255) NOT NULL,
      email VARCHAR(255) NOT NULL,
      phone VARCHAR(255) NOT NULL,
      CONSTRAINT u_email UNIQUE (email),
      CONSTRAINT u_phone UNIQUE (phone)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS item (
      itemId INT AUTO_INCREMENT PRIMARY KEY,
      title VARCHAR(255) NOT NULL,
      description TEXT NOT NULL,
      postDate DATE NOT NULL,
      price DECIMAL(10, 2) NOT NULL,
      postedBy VARCHAR(255) NOT NULL,
      CONSTRAINT fk_item_posted_by FOREIGN KEY (postedBy) REFERENCES user(username)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS category (
      categoryName VARCHAR(255) PRIMARY KEY
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS item_category (
      itemId INT NOT NULL,
      categoryName VARCHAR(255) NOT NULL,
      PRIMARY KEY (itemId, categoryName),
      CONSTRAINT fk_item_category_item FOREIGN KEY (itemId) REFERENCES item(itemId) ON DELETE CASCADE,
      CONSTRAINT fk_item_category_category FOREIGN KEY (categoryName) REFERENCES category(categoryName)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review (
      reviewId INT AUTO_INCREMENT PRIMARY KEY,
      itemId INT NOT NULL,
      reviewer VARCHAR(255) NOT NULL,
      score ENUM('Excellent', 'Good', 'Fair', 'Poor') NOT NULL,
      remark TEXT NOT NULL,
      reviewDate DATE NOT NULL,
      CONSTRAINT uq_review_item_reviewer UNIQUE (itemId, reviewer),
      CONSTRAINT fk_review_item FOREIGN KEY (itemId) REFERENCES item(itemId) ON DELETE CASCADE,
      CONSTRAINT fk_review_reviewer FOREIGN KEY (reviewer) REFERENCES user(username)
    )
    """,
]

current_user = None

ui_values = {
    "title": "",
    "verify_btn": None,
    "diff_page_btn": None,
    "err_msg": "",
    "inputs": {},
    "extra": [],
    "selected_item": None,
}

try:
    with open("credentials.json") as json_data:
        credentials = json.load(json_data)
    conn = mysql.connector.connect(
        host=credentials["host"],
        port=int(credentials["port"]),
        user=credentials["user"],
        password=credentials["pw"],
        database=credentials["db"],
    )
except (FileNotFoundError, json.JSONDecodeError, KeyError, mysql.connector.Error) as e:
    _startup_root = tk.Tk()
    _startup_root.withdraw()
    messagebox.showerror("Startup Error", f"Could not connect to database:\n{e}")
    raise SystemExit(1)

_schema_setup_error = ""


def get_missing_tables():
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW TABLES")
        existing = {row[0] for row in cursor.fetchall()}
    finally:
        cursor.close()
    return [table for table in REQUIRED_TABLES if table not in existing]


def ensure_database_schema():
    missing = get_missing_tables()
    if not missing:
        return True, ""

    cursor = conn.cursor()
    try:
        for statement in SCHEMA_STATEMENTS:
            cursor.execute(statement)
        conn.commit()
    except mysql.connector.Error as err:
        conn.rollback()
        return False, str(err)
    finally:
        cursor.close()

    still_missing = get_missing_tables()
    if still_missing:
        return False, "Still missing tables: " + ", ".join(still_missing)
    return True, ""


_schema_ok, _schema_setup_error = ensure_database_schema()


def register_widget(widget):
    ui_values["extra"].append(widget)


def cancel_err_timer():
    global _err_after_id
    if _err_after_id is not None:
        try:
            root.after_cancel(_err_after_id)
        except (tk.TclError, ValueError):
            pass
        _err_after_id = None


def widget_exists(widget):
    if not widget:
        return False
    try:
        return bool(widget.winfo_exists())
    except tk.TclError:
        return False


def clear_err_msg():
    if widget_exists(ui_values["err_msg"]):
        ui_values["err_msg"].config(text="")


def show_err(text):
    global _err_after_id
    cancel_err_timer()
    if not widget_exists(ui_values["err_msg"]):
        return
    ui_values["err_msg"].config(text=text)
    _err_after_id = root.after(ERR_MSG_DURATION, clear_err_msg)


def check_for_empty_fields():
    for val in ui_values["inputs"].values():
        if isinstance(val, tk.Entry):
            if val.get().strip() == "":
                return True
    return False


def parse_categories(raw_categories):
    categories = []
    for part in raw_categories.split(","):
        category = part.strip().lower()
        if not category:
            continue
        if not CATEGORY_PATTERN.match(category):
            return None, f"Invalid Category '{category}' — Use Lowercase Single Words Only"
        if category not in categories:
            categories.append(category)
    if not categories:
        return None, "Please Enter At Least One Category"
    return categories, None


def verify_login():
    if check_for_empty_fields():
        show_err("Please Fill Out All Fields")
        return

    user = ui_values["inputs"]["user"].get().strip()
    pw = ui_values["inputs"]["pw"].get().encode()
    hashed_pw = hashlib.sha256(pw).hexdigest()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT username FROM user WHERE username=%s AND password=%s;",
            (user, hashed_pw),
        )
        result = cursor.fetchone()
    except mysql.connector.Error:
        show_err("Database Error — Please Try Again")
        return
    finally:
        cursor.close()

    if result is not None:
        login_success_page(user)
    else:
        show_err("Invalid Username or Password")


def create_new_acct():
    if check_for_empty_fields():
        show_err("Please Fill Out All Fields")
        return

    user = ui_values["inputs"]["user"].get().strip()
    pw = ui_values["inputs"]["pw"].get()
    confirm_pw = ui_values["inputs"]["confirm_pw"].get()
    fName = ui_values["inputs"]["fName"].get().strip()
    lName = ui_values["inputs"]["lName"].get().strip()
    email = ui_values["inputs"]["email"].get().strip()
    phone = re.sub(r"\D", "", ui_values["inputs"]["phone"].get().strip())

    if pw != confirm_pw:
        show_err("Passwords Do Not Match")
        return

    if len(pw) < 8:
        show_err("Password Must Be At Least 8 Characters")
        return

    if not EMAIL_PATTERN.match(email):
        show_err("Please Enter a Valid Email Address")
        return

    if len(phone) != 10:
        show_err("Please Enter a Valid 10-Digit Phone Number")
        return

    hashed_pw = hashlib.sha256(pw.encode()).hexdigest()
    sql_query = (
        "INSERT INTO user (username, password, firstName, lastName, email, phone) "
        "VALUES (%s, %s, %s, %s, %s, %s);"
    )

    cursor = conn.cursor()
    try:
        cursor.execute(sql_query, (user, hashed_pw, fName, lName, email, phone))
        conn.commit()
        create_acct_success_page()
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062:
            msg = err.msg.lower()
            if "username" in msg:
                show_err("Username Already Taken")
            elif "email" in msg:
                show_err("Email Already Registered")
            elif "phone" in msg:
                show_err("Phone Number Already Registered")
            else:
                show_err("Could Not Create Account: Duplicate Entry")
        else:
            show_err("Database Error — Please Try Again")
    finally:
        cursor.close()


def submit_item():
    if check_for_empty_fields():
        show_err("Please Fill Out All Fields")
        return

    title = ui_values["inputs"]["title"].get().strip()
    description = ui_values["inputs"]["description"].get().strip()
    raw_categories = ui_values["inputs"]["categories"].get().strip()
    price_text = ui_values["inputs"]["price"].get().strip()

    categories, category_err = parse_categories(raw_categories)
    if category_err:
        show_err(category_err)
        return

    try:
        price = float(price_text)
        if price <= 0:
            raise ValueError
    except ValueError:
        show_err("Please Enter a Valid Price Greater Than 0")
        return

    today = date.today()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM item WHERE postedBy = %s AND postDate = %s;",
            (current_user, today),
        )
        items_today = cursor.fetchone()[0]
        if items_today >= MAX_ITEMS_PER_DAY:
            show_err(f"You Can Only Post {MAX_ITEMS_PER_DAY} Items Per Day")
            return

        cursor.execute(
            "INSERT INTO item (title, description, postDate, price, postedBy) "
            "VALUES (%s, %s, %s, %s, %s);",
            (title, description, today, price, current_user),
        )
        item_id = cursor.lastrowid

        for category in categories:
            cursor.execute(
                "INSERT IGNORE INTO category (categoryName) VALUES (%s);",
                (category,),
            )
            cursor.execute(
                "INSERT INTO item_category (itemId, categoryName) VALUES (%s, %s);",
                (item_id, category),
            )

        conn.commit()
        messagebox.showinfo("Success", f"Item Posted Successfully (ID: {item_id})")
        home_menu(None)
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1146:
            show_err("Database Not Set Up — Run: python setup_database.py")
        else:
            show_err(f"Database Error — Could Not Post Item ({err.msg})")
        print(f"Post item DB error: {err}")
    finally:
        cursor.close()


def perform_search():
    category = ui_values["inputs"]["category"].get().strip().lower()
    if not category:
        show_err("Please Enter a Category")
        return

    if not CATEGORY_PATTERN.match(category):
        show_err("Category Must Be a Lowercase Single Word")
        return

    tree = ui_values["inputs"]["results_tree"]
    for row in tree.get_children():
        tree.delete(row)

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT i.itemId, i.title, i.price, i.postedBy, i.postDate, "
            "GROUP_CONCAT(ic.categoryName ORDER BY ic.categoryName SEPARATOR ', ') "
            "FROM item i "
            "JOIN item_category ic ON i.itemId = ic.itemId "
            "WHERE ic.categoryName = %s "
            "GROUP BY i.itemId, i.title, i.price, i.postedBy, i.postDate "
            "ORDER BY i.itemId;",
            (category,),
        )
        results = cursor.fetchall()
    except mysql.connector.Error:
        show_err("Database Error — Search Failed")
        return
    finally:
        cursor.close()

    if not results:
        show_err("No Items Found For That Category")
        return

    clear_err_msg()
    for row in results:
        item_id, title, price, posted_by, post_date, categories = row
        tree.insert(
            "",
            tk.END,
            iid=str(item_id),
            values=(item_id, title, f"${price:.2f}", posted_by, post_date, categories),
        )


def get_selected_item_id():
    tree = ui_values["inputs"].get("results_tree")
    if tree is None:
        return None
    selection = tree.selection()
    if not selection:
        return None
    return int(selection[0])


def open_review_page():
    item_id = get_selected_item_id()
    if item_id is None:
        show_err("Please Select an Item From the List")
        return

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT title, postedBy FROM item WHERE itemId = %s;",
            (item_id,),
        )
        row = cursor.fetchone()
        if row is None:
            show_err("Selected Item No Longer Exists")
            return

        title, posted_by = row
        if posted_by == current_user:
            show_err("You Cannot Review Your Own Item")
            return

        cursor.execute(
            "SELECT 1 FROM review WHERE itemId = %s AND reviewer = %s;",
            (item_id, current_user),
        )
        if cursor.fetchone():
            show_err("You Have Already Reviewed This Item")
            return
    except mysql.connector.Error:
        show_err("Database Error — Please Try Again")
        return
    finally:
        cursor.close()

    ui_values["selected_item"] = {"itemId": item_id, "title": title}
    review_page()


def submit_review():
    item = ui_values["selected_item"]
    if not item:
        show_err("No Item Selected For Review")
        return

    score = ui_values["inputs"]["score"].get().strip()
    remark = ui_values["inputs"]["remark"].get().strip()

    if score not in REVIEW_SCORES:
        show_err("Please Select a Valid Score")
        return

    if remark == "":
        show_err("Please Enter a Review Description")
        return

    today = date.today()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT postedBy FROM item WHERE itemId = %s;",
            (item["itemId"],),
        )
        row = cursor.fetchone()
        if row is None:
            show_err("Selected Item No Longer Exists")
            return
        if row[0] == current_user:
            show_err("You Cannot Review Your Own Item")
            return

        cursor.execute(
            "SELECT COUNT(*) FROM review WHERE reviewer = %s AND reviewDate = %s;",
            (current_user, today),
        )
        reviews_today = cursor.fetchone()[0]
        if reviews_today >= MAX_REVIEWS_PER_DAY:
            show_err(f"You Can Only Submit {MAX_REVIEWS_PER_DAY} Reviews Per Day")
            return

        cursor.execute(
            "INSERT INTO review (itemId, reviewer, score, remark, reviewDate) "
            "VALUES (%s, %s, %s, %s, %s);",
            (item["itemId"], current_user, score, remark, today),
        )
        conn.commit()
        messagebox.showinfo("Success", "Review Submitted Successfully")
        search_items_page(None)
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062:
            show_err("You Have Already Reviewed This Item")
        else:
            show_err("Database Error — Could Not Submit Review")
    finally:
        cursor.close()


def format_cell(value):
    if isinstance(value, Decimal):
        return f"${value:.2f}"
    return value


def run_select_query(query, params=()):
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return cursor.fetchall(), None
    except mysql.connector.Error:
        return None, "Database Error — Query Failed"
    finally:
        cursor.close()


def populate_results_tree(tree, rows):
    for row in tree.get_children():
        tree.delete(row)
    for row in rows:
        tree.insert("", tk.END, values=tuple(format_cell(v) for v in row))


def create_results_tree(parent, columns, headings, widths):
    table_frame = tk.Frame(parent)
    table_frame.pack(pady=8, padx=15, fill=tk.BOTH, expand=True)
    register_widget(table_frame)

    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
    for col, heading, width in zip(columns, headings, widths):
        tree.heading(col, text=heading)
        tree.column(col, width=width, anchor=tk.CENTER if col in ("id", "price", "count", "postDate") else tk.W)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscrollcommand=scrollbar.set)
    register_widget(scrollbar)
    return tree


def query_most_expensive_per_category():
    query = (
        "SELECT ic.categoryName, i.itemId, i.title, i.price, i.postedBy "
        "FROM item i "
        "JOIN item_category ic ON i.itemId = ic.itemId "
        "JOIN ( "
        "  SELECT ic2.categoryName, MAX(i2.price) AS max_price "
        "  FROM item i2 "
        "  JOIN item_category ic2 ON i2.itemId = ic2.itemId "
        "  GROUP BY ic2.categoryName "
        ") mx ON ic.categoryName = mx.categoryName AND i.price = mx.max_price "
        "ORDER BY ic.categoryName, i.itemId;"
    )
    return run_select_query(query)


def query_users_same_day_categories(cat_x, cat_y):
    query = (
        "SELECT DISTINCT i1.postedBy, i1.postDate "
        "FROM item i1 "
        "JOIN item_category ic1 ON i1.itemId = ic1.itemId "
        "JOIN item i2 ON i1.postedBy = i2.postedBy "
        "  AND i1.postDate = i2.postDate "
        "  AND i1.itemId < i2.itemId "
        "JOIN item_category ic2 ON i2.itemId = ic2.itemId "
        "WHERE ic1.categoryName = %s AND ic2.categoryName = %s "
        "ORDER BY i1.postedBy, i1.postDate;"
    )
    return run_select_query(query, (cat_x, cat_y))


def query_user_items_good_reviews_only(username):
    query = (
        "SELECT i.itemId, i.title, i.price, i.postDate "
        "FROM item i "
        "WHERE i.postedBy = %s "
        "  AND EXISTS (SELECT 1 FROM review r WHERE r.itemId = i.itemId) "
        "  AND NOT EXISTS ( "
        "    SELECT 1 FROM review r "
        "    WHERE r.itemId = i.itemId AND r.score NOT IN ('Excellent', 'Good') "
        "  ) "
        "ORDER BY i.itemId;"
    )
    return run_select_query(query, (username,))


def query_top_posters_on_july_fourth():
    query = (
        "SELECT postedBy, COUNT(*) AS item_count "
        "FROM item "
        "WHERE postDate = %s "
        "GROUP BY postedBy "
        "HAVING COUNT(*) = ( "
        "  SELECT MAX(day_count) FROM ( "
        "    SELECT COUNT(*) AS day_count "
        "    FROM item "
        "    WHERE postDate = %s "
        "    GROUP BY postedBy "
        "  ) AS daily_totals "
        ") "
        "ORDER BY postedBy;"
    )
    return run_select_query(query, (JULY_FOURTH_2024, JULY_FOURTH_2024))


def query_users_all_poor_reviews():
    query = (
        "SELECT reviewer, COUNT(*) AS review_count "
        "FROM review "
        "GROUP BY reviewer "
        "HAVING SUM(CASE WHEN score = 'Poor' THEN 0 ELSE 1 END) = 0 "
        "ORDER BY reviewer;"
    )
    return run_select_query(query)


def query_users_no_poor_reviews_on_items():
    query = (
        "SELECT DISTINCT i.postedBy "
        "FROM item i "
        "WHERE NOT EXISTS ( "
        "  SELECT 1 "
        "  FROM item i2 "
        "  JOIN review r ON r.itemId = i2.itemId "
        "  WHERE i2.postedBy = i.postedBy AND r.score = 'Poor' "
        ") "
        "ORDER BY i.postedBy;"
    )
    return run_select_query(query)


def logout():
    global current_user
    current_user = None
    login_page(None)


def clear_screen():
    cancel_err_timer()
    if ui_values["title"]:
        ui_values["title"].destroy()
        ui_values["title"] = None
    if ui_values["verify_btn"]:
        ui_values["verify_btn"].destroy()
        ui_values["verify_btn"] = None
    if ui_values["diff_page_btn"]:
        ui_values["diff_page_btn"].destroy()
        ui_values["diff_page_btn"] = None
    if ui_values["err_msg"]:
        ui_values["err_msg"].destroy()
        ui_values["err_msg"] = None
    for val in ui_values["inputs"].values():
        if val is not None:
            val.destroy()
    for widget in ui_values["extra"]:
        if widget is not None:
            widget.destroy()
    ui_values["inputs"].clear()
    ui_values["extra"].clear()
    ui_values["selected_item"] = None


def login_page(e):
    clear_screen()
    root.geometry("400x280")
    ui_values["title"] = tk.Label(root, text="Account Login", font=("Arial", 16, "bold"))
    ui_values["title"].pack(pady=15)

    username_lbl = tk.Label(root, text="Username:")
    username_lbl.pack(anchor="w", padx=90)
    username_val = tk.Entry(root, width=35)
    username_val.pack(pady=5)
    ui_values["inputs"]["user_lbl"] = username_lbl
    ui_values["inputs"]["user"] = username_val

    pw_lbl = tk.Label(root, text="Password:")
    pw_lbl.pack(anchor="w", padx=90)
    pw_val = tk.Entry(root, width=35, show="*")
    pw_val.pack(pady=5)
    ui_values["inputs"]["pw_lbl"] = pw_lbl
    ui_values["inputs"]["pw"] = pw_val

    ui_values["verify_btn"] = tk.Button(
        root, text="Login", width=15, bg="#2196F3", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=verify_login,
    )
    ui_values["verify_btn"].pack(pady=10)

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=350)
    ui_values["err_msg"].pack(pady=1)

    reg_lbl = tk.Label(root, text="Create New Account", cursor="hand2", font=("Arial", 8, "underline"))
    reg_lbl.pack(pady=1)
    reg_lbl.bind("<Button-1>", create_acct_page)
    ui_values["inputs"]["reg_lbl"] = reg_lbl

    root.bind("<Return>", lambda event: verify_login())


def create_acct_page(e):
    clear_screen()
    root.geometry("400x530")
    ui_values["title"] = tk.Label(root, text="Create Account", font=("Arial", 16, "bold"))
    ui_values["title"].pack(pady=15)

    username_lbl = tk.Label(root, text="Username:")
    username_lbl.pack(anchor="w", padx=90)
    username_val = tk.Entry(root, width=35)
    username_val.pack(pady=5)
    ui_values["inputs"]["user_lbl"] = username_lbl
    ui_values["inputs"]["user"] = username_val

    pw_lbl = tk.Label(root, text="Password:")
    pw_lbl.pack(anchor="w", padx=90)
    pw_val = tk.Entry(root, width=35, show="*")
    pw_val.pack(pady=5)
    ui_values["inputs"]["pw_lbl"] = pw_lbl
    ui_values["inputs"]["pw"] = pw_val

    confirm_pw_lbl = tk.Label(root, text="Confirm Password:")
    confirm_pw_lbl.pack(anchor="w", padx=90)
    confirm_pw_val = tk.Entry(root, width=35, show="*")
    confirm_pw_val.pack(pady=5)
    ui_values["inputs"]["confirm_pw_lbl"] = confirm_pw_lbl
    ui_values["inputs"]["confirm_pw"] = confirm_pw_val

    fName_lbl = tk.Label(root, text="First Name:")
    fName_lbl.pack(anchor="w", padx=90)
    fName_val = tk.Entry(root, width=35)
    fName_val.pack(pady=5)
    ui_values["inputs"]["fName_lbl"] = fName_lbl
    ui_values["inputs"]["fName"] = fName_val

    lName_lbl = tk.Label(root, text="Last Name:")
    lName_lbl.pack(anchor="w", padx=90)
    lName_val = tk.Entry(root, width=35)
    lName_val.pack(pady=5)
    ui_values["inputs"]["lName_lbl"] = lName_lbl
    ui_values["inputs"]["lName"] = lName_val

    email_lbl = tk.Label(root, text="Email:")
    email_lbl.pack(anchor="w", padx=90)
    email_val = tk.Entry(root, width=35)
    email_val.pack(pady=5)
    ui_values["inputs"]["email_lbl"] = email_lbl
    ui_values["inputs"]["email"] = email_val

    phone_lbl = tk.Label(root, text="Phone:")
    phone_lbl.pack(anchor="w", padx=90)
    phone_val = tk.Entry(root, width=35)
    phone_val.pack(pady=5)
    ui_values["inputs"]["phone_lbl"] = phone_lbl
    ui_values["inputs"]["phone"] = phone_val

    ui_values["verify_btn"] = tk.Button(
        root, text="Register Now", width=15, bg="#4CAF50", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=create_new_acct,
    )
    ui_values["verify_btn"].pack(pady=10)

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=350)
    ui_values["err_msg"].pack(pady=1)

    ui_values["diff_page_btn"] = tk.Label(root, text="Cancel", cursor="hand2", font=("Arial", 8, "underline"))
    ui_values["diff_page_btn"].pack(pady=1)
    ui_values["diff_page_btn"].bind("<Button-1>", login_page)

    root.bind("<Return>", lambda event: create_new_acct())


def login_success_page(user):
    global current_user
    current_user = user
    home_menu(None)


def home_menu(e):
    clear_screen()
    root.geometry("420x420")
    ui_values["title"] = tk.Label(
        root, text=f"Welcome, {current_user}!", fg="green", font=("Arial", 18, "bold"),
    )
    ui_values["title"].pack(pady=20)

    post_btn = tk.Button(
        root, text="Post New Item", width=22, bg="#4CAF50", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=post_item_page,
    )
    post_btn.pack(pady=6)
    register_widget(post_btn)

    search_btn = tk.Button(
        root, text="Search Items", width=22, bg="#2196F3", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=search_items_page,
    )
    search_btn.pack(pady=6)
    register_widget(search_btn)

    reports_btn = tk.Button(
        root, text="Reports & Queries", width=22, bg="#9C27B0", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=reports_menu_page,
    )
    reports_btn.pack(pady=6)
    register_widget(reports_btn)

    logout_btn = tk.Button(
        root, text="Logout", width=22, bg="#757575", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=logout,
    )
    logout_btn.pack(pady=6)
    register_widget(logout_btn)


def post_item_page(e=None):
    clear_screen()
    root.geometry("450x480")
    ui_values["title"] = tk.Label(root, text="Post New Item", font=("Arial", 16, "bold"))
    ui_values["title"].pack(pady=12)

    title_lbl = tk.Label(root, text="Title:")
    title_lbl.pack(anchor="w", padx=40)
    title_val = tk.Entry(root, width=45)
    title_val.pack(pady=4)
    register_widget(title_lbl)
    ui_values["inputs"]["title"] = title_val

    desc_lbl = tk.Label(root, text="Description:")
    desc_lbl.pack(anchor="w", padx=40)
    desc_val = tk.Entry(root, width=45)
    desc_val.pack(pady=4)
    register_widget(desc_lbl)
    ui_values["inputs"]["description"] = desc_val

    cat_lbl = tk.Label(root, text="Categories (comma-separated, lowercase):")
    cat_lbl.pack(anchor="w", padx=40)
    cat_val = tk.Entry(root, width=45)
    cat_val.pack(pady=4)
    register_widget(cat_lbl)
    ui_values["inputs"]["categories"] = cat_val

    price_lbl = tk.Label(root, text="Price:")
    price_lbl.pack(anchor="w", padx=40)
    price_val = tk.Entry(root, width=45)
    price_val.pack(pady=4)
    register_widget(price_lbl)
    ui_values["inputs"]["price"] = price_val

    ui_values["verify_btn"] = tk.Button(
        root, text="Post Item", width=15, bg="#4CAF50", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=submit_item,
    )
    ui_values["verify_btn"].pack(pady=12)

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=400)
    ui_values["err_msg"].pack(pady=4)

    back_lbl = tk.Label(root, text="Back to Home", cursor="hand2", font=("Arial", 8, "underline"))
    back_lbl.pack(pady=4)
    back_lbl.bind("<Button-1>", home_menu)
    register_widget(back_lbl)

    root.bind("<Return>", lambda event: submit_item())


def search_items_page(e=None):
    clear_screen()
    root.geometry("720x480")
    ui_values["title"] = tk.Label(root, text="Search Items by Category", font=("Arial", 16, "bold"))
    ui_values["title"].pack(pady=10)

    search_frame = tk.Frame(root)
    search_frame.pack(pady=5)
    register_widget(search_frame)

    cat_lbl = tk.Label(search_frame, text="Category:")
    cat_lbl.pack(side=tk.LEFT, padx=5)
    register_widget(cat_lbl)

    cat_val = tk.Entry(search_frame, width=25)
    cat_val.pack(side=tk.LEFT, padx=5)
    ui_values["inputs"]["category"] = cat_val

    search_btn = tk.Button(
        search_frame, text="Search", width=10, bg="#2196F3", fg="black", activeforeground="black",
        font=("Arial", 9, "bold"), command=perform_search,
    )
    search_btn.pack(side=tk.LEFT, padx=5)
    register_widget(search_btn)

    table_frame = tk.Frame(root)
    table_frame.pack(pady=10, padx=15, fill=tk.BOTH, expand=True)
    register_widget(table_frame)

    columns = ("id", "title", "price", "postedBy", "postDate", "categories")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
    tree.heading("id", text="ID")
    tree.heading("title", text="Title")
    tree.heading("price", text="Price")
    tree.heading("postedBy", text="Posted By")
    tree.heading("postDate", text="Date")
    tree.heading("categories", text="Categories")
    tree.column("id", width=40, anchor=tk.CENTER)
    tree.column("title", width=140)
    tree.column("price", width=70, anchor=tk.CENTER)
    tree.column("postedBy", width=90)
    tree.column("postDate", width=90, anchor=tk.CENTER)
    tree.column("categories", width=180)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    ui_values["inputs"]["results_tree"] = tree

    scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscrollcommand=scrollbar.set)
    register_widget(scrollbar)

    ui_values["verify_btn"] = tk.Button(
        root, text="Write Review", width=15, bg="#FF9800", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=open_review_page,
    )
    ui_values["verify_btn"].pack(pady=8)

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=650)
    ui_values["err_msg"].pack(pady=4)

    back_lbl = tk.Label(root, text="Back to Home", cursor="hand2", font=("Arial", 8, "underline"))
    back_lbl.pack(pady=4)
    back_lbl.bind("<Button-1>", home_menu)
    register_widget(back_lbl)

    root.bind("<Return>", lambda event: perform_search())


def review_page():
    clear_screen()
    item = ui_values["selected_item"]
    root.geometry("450x360")
    ui_values["title"] = tk.Label(
        root, text=f"Review Item #{item['itemId']}", font=("Arial", 16, "bold"),
    )
    ui_values["title"].pack(pady=12)

    item_lbl = tk.Label(root, text=item["title"], font=("Arial", 11))
    item_lbl.pack(pady=5)
    register_widget(item_lbl)

    score_lbl = tk.Label(root, text="Score:")
    score_lbl.pack(anchor="w", padx=40, pady=(10, 0))
    register_widget(score_lbl)

    score_val = ttk.Combobox(root, values=REVIEW_SCORES, state="readonly", width=42)
    score_val.pack(pady=4)
    ui_values["inputs"]["score"] = score_val

    remark_lbl = tk.Label(root, text="Description:")
    remark_lbl.pack(anchor="w", padx=40)
    register_widget(remark_lbl)

    remark_val = tk.Entry(root, width=45)
    remark_val.pack(pady=4)
    ui_values["inputs"]["remark"] = remark_val

    ui_values["verify_btn"] = tk.Button(
        root, text="Submit Review", width=15, bg="#FF9800", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=submit_review,
    )
    ui_values["verify_btn"].pack(pady=12)

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=400)
    ui_values["err_msg"].pack(pady=4)

    back_lbl = tk.Label(root, text="Back to Search", cursor="hand2", font=("Arial", 8, "underline"))
    back_lbl.pack(pady=4)
    back_lbl.bind("<Button-1>", search_items_page)
    register_widget(back_lbl)

    root.bind("<Return>", lambda event: submit_review())


def reports_menu_page(e=None):
    clear_screen()
    root.geometry("480x460")
    ui_values["title"] = tk.Label(root, text="Phase 3 Reports", font=("Arial", 16, "bold"))
    ui_values["title"].pack(pady=12)

    report_buttons = [
        ("Most Expensive Item Per Category", report_q1_page),
        ("Same-Day Posters (Category X & Y)", report_q2_page),
        ("User Items With Only Good Reviews", report_q3_page),
        ("Top Posters on 7/4/2024", report_q4_page),
        ("Users With Only Poor Reviews", report_q5_page),
        ("Posters With No Poor Reviews", report_q6_page),
    ]
    for label, command in report_buttons:
        btn = tk.Button(
            root, text=label, width=34, bg="#673AB7", fg="black", activeforeground="black",
            font=("Arial", 9, "bold"), command=command,
        )
        btn.pack(pady=4)
        register_widget(btn)

    back_lbl = tk.Label(root, text="Back to Home", cursor="hand2", font=("Arial", 8, "underline"))
    back_lbl.pack(pady=10)
    back_lbl.bind("<Button-1>", home_menu)
    register_widget(back_lbl)


def report_q1_page(e=None):
    clear_screen()
    root.geometry("760x500")
    ui_values["title"] = tk.Label(
        root, text="Most Expensive Items in Each Category", font=("Arial", 14, "bold"),
    )
    ui_values["title"].pack(pady=8)

    ui_values["verify_btn"] = tk.Button(
        root, text="Run Query", width=15, bg="#673AB7", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=run_report_q1,
    )
    ui_values["verify_btn"].pack(pady=4)

    columns = ("category", "id", "title", "price", "postedBy")
    headings = ("Category", "ID", "Title", "Price", "Posted By")
    widths = (110, 45, 180, 80, 100)
    tree = create_results_tree(root, columns, headings, widths)
    ui_values["inputs"]["results_tree"] = tree

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=700)
    ui_values["err_msg"].pack(pady=4)

    back_lbl = tk.Label(root, text="Back to Reports", cursor="hand2", font=("Arial", 8, "underline"))
    back_lbl.pack(pady=4)
    back_lbl.bind("<Button-1>", reports_menu_page)
    register_widget(back_lbl)


def run_report_q1():
    rows, err = query_most_expensive_per_category()
    if err:
        show_err(err)
        return
    if not rows:
        show_err("No Items Found in Database")
        return
    clear_err_msg()
    populate_results_tree(ui_values["inputs"]["results_tree"], rows)


def report_q2_page(e=None):
    clear_screen()
    root.geometry("760x520")
    ui_values["title"] = tk.Label(
        root, text="Users Who Posted Category X and Y on the Same Day", font=("Arial", 14, "bold"),
    )
    ui_values["title"].pack(pady=8)

    form = tk.Frame(root)
    form.pack(pady=4)
    register_widget(form)

    cat_x_lbl = tk.Label(form, text="Category X:")
    cat_x_lbl.pack(side=tk.LEFT, padx=5)
    register_widget(cat_x_lbl)
    cat_x_val = tk.Entry(form, width=18)
    cat_x_val.pack(side=tk.LEFT, padx=5)
    ui_values["inputs"]["category_x"] = cat_x_val

    cat_y_lbl = tk.Label(form, text="Category Y:")
    cat_y_lbl.pack(side=tk.LEFT, padx=5)
    register_widget(cat_y_lbl)
    cat_y_val = tk.Entry(form, width=18)
    cat_y_val.pack(side=tk.LEFT, padx=5)
    ui_values["inputs"]["category_y"] = cat_y_val

    ui_values["verify_btn"] = tk.Button(
        root, text="Run Query", width=15, bg="#673AB7", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=run_report_q2,
    )
    ui_values["verify_btn"].pack(pady=4)

    columns = ("username", "postDate")
    headings = ("Username", "Post Date")
    widths = (180, 120)
    tree = create_results_tree(root, columns, headings, widths)
    ui_values["inputs"]["results_tree"] = tree

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=700)
    ui_values["err_msg"].pack(pady=4)

    back_lbl = tk.Label(root, text="Back to Reports", cursor="hand2", font=("Arial", 8, "underline"))
    back_lbl.pack(pady=4)
    back_lbl.bind("<Button-1>", reports_menu_page)
    register_widget(back_lbl)

    root.bind("<Return>", lambda event: run_report_q2())


def run_report_q2():
    cat_x = ui_values["inputs"]["category_x"].get().strip().lower()
    cat_y = ui_values["inputs"]["category_y"].get().strip().lower()
    if not cat_x or not cat_y:
        show_err("Please Enter Both Categories")
        return
    if not CATEGORY_PATTERN.match(cat_x) or not CATEGORY_PATTERN.match(cat_y):
        show_err("Categories Must Be Lowercase Single Words")
        return

    rows, err = query_users_same_day_categories(cat_x, cat_y)
    if err:
        show_err(err)
        return
    if not rows:
        show_err("No Matching Users Found")
        return
    clear_err_msg()
    populate_results_tree(ui_values["inputs"]["results_tree"], rows)


def report_q3_page(e=None):
    clear_screen()
    root.geometry("760x520")
    ui_values["title"] = tk.Label(
        root, text="Items With Only Excellent/Good Reviews", font=("Arial", 14, "bold"),
    )
    ui_values["title"].pack(pady=8)

    form = tk.Frame(root)
    form.pack(pady=4)
    register_widget(form)

    user_lbl = tk.Label(form, text="Username:")
    user_lbl.pack(side=tk.LEFT, padx=5)
    register_widget(user_lbl)
    user_val = tk.Entry(form, width=25)
    user_val.pack(side=tk.LEFT, padx=5)
    ui_values["inputs"]["query_user"] = user_val

    ui_values["verify_btn"] = tk.Button(
        root, text="Run Query", width=15, bg="#673AB7", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=run_report_q3,
    )
    ui_values["verify_btn"].pack(pady=4)

    columns = ("id", "title", "price", "postDate")
    headings = ("ID", "Title", "Price", "Post Date")
    widths = (45, 220, 80, 100)
    tree = create_results_tree(root, columns, headings, widths)
    ui_values["inputs"]["results_tree"] = tree

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=700)
    ui_values["err_msg"].pack(pady=4)

    back_lbl = tk.Label(root, text="Back to Reports", cursor="hand2", font=("Arial", 8, "underline"))
    back_lbl.pack(pady=4)
    back_lbl.bind("<Button-1>", reports_menu_page)
    register_widget(back_lbl)

    root.bind("<Return>", lambda event: run_report_q3())


def run_report_q3():
    username = ui_values["inputs"]["query_user"].get().strip()
    if not username:
        show_err("Please Enter a Username")
        return

    rows, err = query_user_items_good_reviews_only(username)
    if err:
        show_err(err)
        return
    if not rows:
        show_err("No Matching Items Found For That User")
        return
    clear_err_msg()
    populate_results_tree(ui_values["inputs"]["results_tree"], rows)


def report_q4_page(e=None):
    clear_screen()
    root.geometry("760x500")
    ui_values["title"] = tk.Label(
        root, text="Most Active Posters on 7/4/2024", font=("Arial", 14, "bold"),
    )
    ui_values["title"].pack(pady=8)

    ui_values["verify_btn"] = tk.Button(
        root, text="Run Query", width=15, bg="#673AB7", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=run_report_q4,
    )
    ui_values["verify_btn"].pack(pady=4)

    columns = ("username", "count")
    headings = ("Username", "Items Posted")
    widths = (180, 120)
    tree = create_results_tree(root, columns, headings, widths)
    ui_values["inputs"]["results_tree"] = tree

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=700)
    ui_values["err_msg"].pack(pady=4)

    back_lbl = tk.Label(root, text="Back to Reports", cursor="hand2", font=("Arial", 8, "underline"))
    back_lbl.pack(pady=4)
    back_lbl.bind("<Button-1>", reports_menu_page)
    register_widget(back_lbl)


def run_report_q4():
    rows, err = query_top_posters_on_july_fourth()
    if err:
        show_err(err)
        return
    if not rows:
        show_err("No Items Were Posted on 7/4/2024")
        return
    clear_err_msg()
    populate_results_tree(ui_values["inputs"]["results_tree"], rows)


def report_q5_page(e=None):
    clear_screen()
    root.geometry("760x500")
    ui_values["title"] = tk.Label(
        root, text="Users Who Gave Only Poor Reviews", font=("Arial", 14, "bold"),
    )
    ui_values["title"].pack(pady=8)

    ui_values["verify_btn"] = tk.Button(
        root, text="Run Query", width=15, bg="#673AB7", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=run_report_q5,
    )
    ui_values["verify_btn"].pack(pady=4)

    columns = ("reviewer", "count")
    headings = ("Username", "Review Count")
    widths = (180, 120)
    tree = create_results_tree(root, columns, headings, widths)
    ui_values["inputs"]["results_tree"] = tree

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=700)
    ui_values["err_msg"].pack(pady=4)

    back_lbl = tk.Label(root, text="Back to Reports", cursor="hand2", font=("Arial", 8, "underline"))
    back_lbl.pack(pady=4)
    back_lbl.bind("<Button-1>", reports_menu_page)
    register_widget(back_lbl)


def run_report_q5():
    rows, err = query_users_all_poor_reviews()
    if err:
        show_err(err)
        return
    if not rows:
        show_err("No Users Found With Only Poor Reviews")
        return
    clear_err_msg()
    populate_results_tree(ui_values["inputs"]["results_tree"], rows)


def report_q6_page(e=None):
    clear_screen()
    root.geometry("760x500")
    ui_values["title"] = tk.Label(
        root, text="Posters Whose Items Never Received Poor Reviews", font=("Arial", 14, "bold"),
    )
    ui_values["title"].pack(pady=8)

    ui_values["verify_btn"] = tk.Button(
        root, text="Run Query", width=15, bg="#673AB7", fg="black", activeforeground="black",
        font=("Arial", 10, "bold"), command=run_report_q6,
    )
    ui_values["verify_btn"].pack(pady=4)

    columns = ("username",)
    headings = ("Username",)
    widths = (220,)
    tree = create_results_tree(root, columns, headings, widths)
    ui_values["inputs"]["results_tree"] = tree

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10), wraplength=700)
    ui_values["err_msg"].pack(pady=4)

    back_lbl = tk.Label(root, text="Back to Reports", cursor="hand2", font=("Arial", 8, "underline"))
    back_lbl.pack(pady=4)
    back_lbl.bind("<Button-1>", reports_menu_page)
    register_widget(back_lbl)


def run_report_q6():
    rows, err = query_users_no_poor_reviews_on_items()
    if err:
        show_err(err)
        return
    if not rows:
        show_err("No Matching Users Found")
        return
    clear_err_msg()
    populate_results_tree(ui_values["inputs"]["results_tree"], rows)


def create_acct_success_page():
    clear_screen()
    root.geometry("400x280")
    ui_values["title"] = tk.Label(
        root, text="Account Created Successfully!", fg="green", font=("Arial", 18, "bold"),
    )
    ui_values["title"].pack(pady=100)
    ui_values["diff_page_btn"] = tk.Label(
        root, text="Back To Login Screen", cursor="hand2", font=("Arial", 8, "underline"),
    )
    ui_values["diff_page_btn"].pack(pady=1)
    ui_values["diff_page_btn"].bind("<Button-1>", login_page)


root = tk.Tk()
root.title("Project 440 - Online Store")
root.geometry("400x280")
root.resizable(False, False)
root.eval("tk::PlaceWindow . center")
if not _schema_ok:
    messagebox.showwarning(
        "Database Setup Required",
        "Required tables are missing (item, category, review, etc.).\n\n"
        "Run this once in Terminal from the project folder:\n\n"
        "  python3 install_database.py\n\n"
        "Enter your MySQL Workbench root password when prompted.\n\n"
        f"Details: {_schema_setup_error}",
    )
login_page(e=None)

root.mainloop()
