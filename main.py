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

# Verify user/login
# TODO: Need to pass vars to function (username_val and pw_val)
def verify_login():
    user = ui_values["inputs"]["user"].get()
    pw = ui_values["inputs"]["pw"].get().encode()
    hashed_pw = hashlib.sha256(pw).hexdigest()
    cursor = conn.cursor()
    sql_query = "SELECT * FROM user WHERE username=%s AND password=%s;"
    cursor.execute(sql_query, (user, hashed_pw))
    result = cursor.fetchone()
    if result is not None:
        print("User logged in")
    else:
        print("Login failed")
        ui_values["err_msg"].config(text="Invalid Username or Password")
        root.after(2000, clear_err_msg)

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
    reg_lbl.bind("<Button-1>", create_new_acct)
    ui_values["inputs"]["reg_lbl"] = reg_lbl

# UI - Create new acct page
def create_new_acct(e):
    clear_screen()
    ui_values["title"] = tk.Label(root, text="Create Account", font=("Arial", 16, "bold"))
    ui_values["title"].pack(pady=15)

    ui_values["verify_btn"] = tk.Button(root, text="Register Now", width=15, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
    ui_values["verify_btn"].pack(pady=20)

    sql_query = "SELECT * from user where username=%s, password=%s, firstName=%s, lastName=%s, email=%s, phone=%d;"

    ui_values["diff_page_btn"] = tk.Label(root, text="Cancel", cursor="hand2", font=("Arial", 8, "underline"))
    ui_values["diff_page_btn"].pack(pady=1)
    ui_values["diff_page_btn"].bind("<Button-1>", login_page)
    print("result")

# Create UI and start UI loop
root = tk.Tk()
root.title("Project 440 - Login")
root.geometry("400x280")
root.eval('tk::PlaceWindow . center')
login_page(e=None)

root.mainloop()