import mysql.connector, json, hashlib
import tkinter as tk

ui_values = {
    "title": "",
    "verify_btn": None,
    "diff_page_btn": None,
    "err_msg": "",
    "inputs": {}
}

with open("credentials.json") as json_data:
    credentials = json.load(json_data)

conn = mysql.connector.connect(
    host=credentials["host"],
    port=credentials["port"],
    user=credentials["user"],
    password=credentials["pw"],
    database=credentials["db"],
)

# Clears login error message
def clear_err_msg():
    ui_values["err_msg"].config(text="")

def check_for_empty_fields():
    for val in ui_values["inputs"].values():
        if isinstance(val, tk.Entry):
            if val.get().strip() == "":
                print("empty field")
                return True
    return False    

# Verify user/login
def verify_login():
    if check_for_empty_fields():
        ui_values["err_msg"].config(text="Please Fill Out All Fields")
        root.after(2000, clear_err_msg)
        return
    
    user = ui_values["inputs"]["user"].get()
    pw = ui_values["inputs"]["pw"].get().encode()
    hashed_pw = hashlib.sha256(pw).hexdigest()
    cursor = conn.cursor()
    sql_query = "SELECT * FROM user WHERE username=%s AND password=%s;"
    cursor.execute(sql_query, (user, hashed_pw))
    result = cursor.fetchone()
    if result is not None:
        print("User logged in")
        login_success_page()
    else:
        print("Login failed")
        ui_values["err_msg"].config(text="Invalid Username or Password")
        root.after(2000, clear_err_msg)

# Validate new user and create account
def create_new_acct():
    if check_for_empty_fields():
        ui_values["err_msg"].config(text="Please Fill Out All Fields")
        root.after(2000, clear_err_msg)
        return
    
    user = ui_values["inputs"]["user"].get()
    pw = ui_values["inputs"]["pw"].get()
    confirm_pw = ui_values["inputs"]["confirm_pw"].get()
    hashed_pw = hashlib.sha256(pw.encode()).hexdigest()
    fName = ui_values["inputs"]["fName"].get()
    lName = ui_values["inputs"]["lName"].get()
    email = ui_values["inputs"]["email"].get()
    phone = ui_values["inputs"]["phone"].get()

    if pw != confirm_pw:
        ui_values["err_msg"].config(text="Passwords Do Not Match")
        root.after(2000, clear_err_msg)
        return

    cursor = conn.cursor()
    sql_query = "INSERT INTO user (username, password, firstName, lastName, email, phone)\
        VALUES (%s, %s, %s, %s, %s, %s);"
    
    try:
        cursor.execute(sql_query, (user, hashed_pw, fName, lName, email, phone))
        conn.commit()
        create_acct_success_page()

    except mysql.connector.Error as err:
        if err.errno == 1062:
            ui_values["err_msg"].config(text="Could Not Create Account: Duplicate Username, Email, or Phone")
            root.after(2000, clear_err_msg)
        else:
            ui_values["err_msg"].config(text="Internal Database Error")
            root.after(2000, clear_err_msg)
            print(f"DB Error: {err}")

# UI - Clear current screen
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
    ui_values["inputs"].clear()

# UI - Login page
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

    ui_values["verify_btn"] = tk.Button(root, text="Login", width=15, bg="#2196F3", fg="white", font=("Arial", 10, "bold"), command=verify_login)
    ui_values["verify_btn"].pack(pady=10)

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10))
    ui_values["err_msg"].pack(pady=1)

    reg_lbl = tk.Label(root, text="Create New Account", cursor="hand2", font=("Arial", 8, "underline"))
    reg_lbl.pack(pady=1)
    reg_lbl.bind("<Button-1>", create_acct_page)
    ui_values["inputs"]["reg_lbl"] = reg_lbl

# UI - Create new acct page
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

    ui_values["verify_btn"] = tk.Button(root, text="Register Now", width=15, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=create_new_acct)
    ui_values["verify_btn"].pack(pady=10)

    ui_values["err_msg"] = tk.Label(root, text="", fg="red", font=("Arial", 10))
    ui_values["err_msg"].pack(pady=1)

    ui_values["diff_page_btn"] = tk.Label(root, text="Cancel", cursor="hand2", font=("Arial", 8, "underline"))
    ui_values["diff_page_btn"].pack(pady=1)
    ui_values["diff_page_btn"].bind("<Button-1>", login_page)
    print("result")

# Login success screen
def login_success_page():
    clear_screen()
    root.geometry("400x280")
    ui_values["title"] = tk.Label(root, text="Logged In Successfully!", fg="green", font=("Arial", 20, "bold"))
    ui_values["title"].pack(pady=100)

    ui_values["diff_page_btn"] = tk.Label(root, text="Back To Login Screen", cursor="hand2", font=("Arial", 8, "underline"))
    ui_values["diff_page_btn"].pack(pady=1)
    ui_values["diff_page_btn"].bind("<Button-1>", login_page)

# Created new account success screen
def create_acct_success_page():
    clear_screen()
    root.geometry("400x280")
    ui_values["title"] = tk.Label(root, text="Account Created Successfully!", fg="green", font=("Arial", 18, "bold"))
    ui_values["title"].pack(pady=100)
    ui_values["diff_page_btn"] = tk.Label(root, text="Back To Login Screen", cursor="hand2", font=("Arial", 8, "underline"))
    ui_values["diff_page_btn"].pack(pady=1)
    ui_values["diff_page_btn"].bind("<Button-1>", login_page)
    root.after(2000, login_page, None)

# Create UI and start UI loop
root = tk.Tk()
root.title("Project 440 - Login")
root.geometry("400x280")
root.eval('tk::PlaceWindow . center')
login_page(e=None)

root.mainloop()