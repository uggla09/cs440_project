COMP 440 Phase 2 - Online Store
================================

Group Members & Contributions
-----------------------------
(Update with your team member names and what each person contributed.)

Install & Configure
-------------------
1. Install Python 3 and MySQL Server.
2. Install dependencies:
   pip install mysql-connector-python
3. Create the Phase 1 database and user table (see your Phase 1 SQL script).
4. Run the Phase 2 schema in MySQL Workbench or the mysql CLI:
   source schema_phase2.sql
5. Create credentials.json in the project root:
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

Phase 2 Features
----------------
1. Post Item — logged-in users can post items with title, description,
   comma-separated lowercase categories, and price. Item IDs are auto-
   generated. Users are limited to 2 items per day.
2. Search Items — search by category; results appear in a table.
3. Write Review — select an item from search results, choose a score
   (Excellent/Good/Fair/Poor), and enter a remark. Users are limited to
   2 reviews per day, cannot review their own items, and can only review
   each item once.

Demo Video
----------
(Add your YouTube demo URL here before submission.)
