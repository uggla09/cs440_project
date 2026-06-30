import re
from datetime import date
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
        port=credentials["port"],
        user=credentials["user"],
        password=credentials["pw"],
        database=credentials["db"],
    )
except (FileNotFoundError, json.JSONDecodeError, KeyError, mysql.connector.Error) as e:
    _startup_root = tk.Tk()
    _startup_root.withdraw()
    messagebox.showerror("Startup Error", f"Could not connect to database:\n{e}")
    raise SystemExit(1)


def register_widget(widget):
    ui_values["extra"].append(widget)


def clear_err_msg():
    if ui_values["err_msg"]:
        ui_values["err_msg"].config(text="")


def show_err(text):
    ui_values["err_msg"].config(text=text)
    root.after(ERR_MSG_DURATION, clear_err_msg)


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
    except mysql.connector.Error:
        conn.rollback()
        show_err("Database Error — Could Not Post Item")
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


def logout():
    global current_user
    current_user = None
    login_page(None)


def clear_screen():
    if ui_values["title"]:
        ui_values["title"].destroy()
    if ui_values["verify_btn"]:
        ui_values["verify_btn"].destroy()
    if ui_values["diff_page_btn"]:
        ui_values["diff_page_btn"].destroy()
    if ui_values["err_msg"]:
        ui_values["err_msg"].destroy()
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
        root, text="Login", width=15, bg="#2196F3", fg="white",
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
        root, text="Register Now", width=15, bg="#4CAF50", fg="white",
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
    root.geometry("400x320")
    ui_values["title"] = tk.Label(
        root, text=f"Welcome, {current_user}!", fg="green", font=("Arial", 18, "bold"),
    )
    ui_values["title"].pack(pady=25)

    post_btn = tk.Button(
        root, text="Post New Item", width=20, bg="#4CAF50", fg="white",
        font=("Arial", 10, "bold"), command=post_item_page,
    )
    post_btn.pack(pady=8)
    register_widget(post_btn)

    search_btn = tk.Button(
        root, text="Search Items", width=20, bg="#2196F3", fg="white",
        font=("Arial", 10, "bold"), command=search_items_page,
    )
    search_btn.pack(pady=8)
    register_widget(search_btn)

    logout_btn = tk.Button(
        root, text="Logout", width=20, bg="#757575", fg="white",
        font=("Arial", 10, "bold"), command=logout,
    )
    logout_btn.pack(pady=8)
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
        root, text="Post Item", width=15, bg="#4CAF50", fg="white",
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
        search_frame, text="Search", width=10, bg="#2196F3", fg="white",
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
        root, text="Write Review", width=15, bg="#FF9800", fg="white",
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
        root, text="Submit Review", width=15, bg="#FF9800", fg="white",
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
login_page(e=None)

root.mainloop()
