#!/usr/bin/env python3


import getpass
import sys
from pathlib import Path

import mysql.connector

SCHEMA_FILE = Path(__file__).parent / "schema_all.sql"
REQUIRED_TABLES = ("user", "item", "category", "item_category", "review")


def run_schema_as_root(root_password):
    sql = SCHEMA_FILE.read_text()
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password=root_password,
    )
    cursor = conn.cursor()
    try:
        for statement in sql.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            cursor.execute(statement)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def verify_app_user():
    with open("credentials.json") as f:
        import json
        creds = json.load(f)

    conn = mysql.connector.connect(
        host=creds["host"],
        port=int(creds["port"]),
        user=creds["user"],
        password=creds["pw"],
        database=creds["db"],
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = {row[0] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    missing = [t for t in REQUIRED_TABLES if t not in tables]
    return missing


def main():
    if not SCHEMA_FILE.exists():
        print(f"Missing {SCHEMA_FILE}")
        sys.exit(1)

    print("COMP 440 database installer")
    print("Enter your MySQL ROOT password (used in MySQL Workbench).")
    root_pw = getpass.getpass("MySQL root password: ")

    if not root_pw:
        print("Cancelled.")
        sys.exit(1)

    try:
        run_schema_as_root(root_pw)
    except mysql.connector.Error as err:
        print(f"\nSetup failed: {err}")
        print("\nIf the password is wrong, try again.")
        print("Or open schema_all.sql in MySQL Workbench and click Execute.")
        sys.exit(1)

    try:
        missing = verify_app_user()
    except mysql.connector.Error as err:
        print(f"\nTables may have been created, but app login check failed: {err}")
        sys.exit(1)

    if missing:
        print("Setup incomplete. Still missing:", ", ".join(missing))
        sys.exit(1)

    print("\nSuccess! All tables created.")
    print("You can now run:  python3 main.py")


if __name__ == "__main__":
    main()
