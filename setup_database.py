"""One-time database setup. Run: python setup_database.py"""

import json
import sys

import mysql.connector

REQUIRED_TABLES = ("user", "item", "category", "item_category", "review")

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


def get_missing_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    existing = {row[0] for row in cursor.fetchall()}
    cursor.close()
    return [table for table in REQUIRED_TABLES if table not in existing]


def create_tables(conn):
    cursor = conn.cursor()
    try:
        for statement in SCHEMA_STATEMENTS:
            cursor.execute(statement)
        conn.commit()
    except mysql.connector.Error:
        conn.rollback()
        raise
    finally:
        cursor.close()


def main():
    with open("credentials.json") as f:
        creds = json.load(f)

    try:
        conn = mysql.connector.connect(
            host=creds["host"],
            port=int(creds["port"]),
            user=creds["user"],
            password=creds["pw"],
            database=creds["db"],
        )
    except mysql.connector.Error as err:
        print(f"Could not connect: {err}")
        sys.exit(1)

    missing = get_missing_tables(conn)
    if not missing:
        print("All required tables already exist.")
        conn.close()
        return

    print("Missing tables:", ", ".join(missing))
    try:
        create_tables(conn)
    except mysql.connector.Error as err:
        print(f"Setup failed: {err}")
        print("\nOpen MySQL Workbench as admin and run schema_all.sql once.")
        conn.close()
        sys.exit(1)

    still_missing = get_missing_tables(conn)
    conn.close()
    if still_missing:
        print("Setup incomplete. Still missing:", ", ".join(still_missing))
        sys.exit(1)

    print("Database setup complete.")


if __name__ == "__main__":
    main()
