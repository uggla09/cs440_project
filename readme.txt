COMP 440 Phase 2 - Online Store
================================

Group Members & Contributions
-----------------------------
Kipp Reitzel - GUI and database code
Sofiia Unkovskaia - GUI and database code, recorded video #1
Gor Navasardyan - GUI and database code, recorded video #2

Install & Configure
-------------------
1. Install Python 3 and MySQL Server.
2. Install dependencies:
   pip install mysql-connector-python
3. Run the Phase 1 and Phase 2 schema in MySQL Workbench or the mysql CLI:
   source schema_phase1.sql and source schema_phase2.sql
4. Create credentials.json in the project root (to run locally for testing):
   {
     "host": "127.0.0.1",
     "port": 3306,
     "user": "pyconn",
     "pw": "1234",
     "db": "project440"
   }

Run
---
python main.py

Phase 1 Features
----------------
1. Log In Page - Validates user credential for login (user name and password).
2. Create Account Page - Allows user to create account. Verifies that username, email, and phone number do
   not already exist prior to creating new account. Also, verifies passwords match and email and phone number
   are in correct format.

Phase 2 Features
----------------
1. Post Item Page- Logged-in users can post items with title, description,
   comma-separated lowercase categories, and price. Item IDs are auto-
   generated. Users are limited to 2 items per day.
2. Search Items Page - Search by category; results appear in a table.
3. Write Review Page - Select an item from search results, choose a score
   (Excellent/Good/Fair/Poor), and enter a remark. Users are limited to
   2 reviews per day, cannot review their own items, and can only review
   each item once.

Demo Video
----------
https://youtu.be/mrOegX8nRZg