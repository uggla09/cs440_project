# CS440 O

Python + Tkinter + MySQL application covering COMP 440 Phases 1–3.

## Dependencies

```bash
pip install mysql-connector-python
```

(`tkinter`, `json`, and `hashlib` are included with Python.)

## Database Setup (required once)

**If posting items fails**, the Phase 2 tables are missing. Do this once in **MySQL Workbench**:

1. Connect as **root** (or another admin account)
2. Open `schema_all.sql` from this project folder
3. Click the **Execute** (lightning bolt) button

Alternatively, if `pyconn` already has CREATE permission:

```bash
python setup_database.py
```

Then restart the app: `python main.py`

Create `credentials.json`:

```json
{
  "host": "127.0.0.1",
  "port": 3306,
  "user": "pyconn",
  "pw": "1234",
  "db": "project440"
}
```

## Run

```bash
python main.py
```

See [readme.txt](readme.txt) for full feature list, Phase 3 query descriptions, and submission notes.
