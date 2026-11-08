import os, sqlite3
from contextlib import contextmanager
BASE_DIR=os.path.dirname(os.path.abspath(__file__))
DB_PATH=os.environ.get('DATABASE_PATH',os.path.join(BASE_DIR,'database','insurance.db'))
os.makedirs(os.path.dirname(DB_PATH),exist_ok=True)
@contextmanager
def get_db():
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; conn.execute('PRAGMA foreign_keys=ON')
    try: yield conn; conn.commit()
    except Exception: conn.rollback(); raise
    finally: conn.close()
def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS policies(id INTEGER PRIMARY KEY AUTOINCREMENT, policy_number TEXT NOT NULL UNIQUE, customer_name TEXT NOT NULL, customer_email TEXT DEFAULT '', customer_phone TEXT DEFAULT '', premium_amount REAL NOT NULL CHECK(premium_amount>0), frequency TEXT NOT NULL CHECK(frequency IN ('monthly','yearly')), start_date TEXT NOT NULL, last_payment_date TEXT NOT NULL, next_due_date TEXT NOT NULL, grace_period INTEGER NOT NULL DEFAULT 30 CHECK(grace_period>=0), status TEXT NOT NULL DEFAULT 'Active', paid_up INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY AUTOINCREMENT, policy_id INTEGER NOT NULL, message TEXT NOT NULL, kind TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(policy_id,kind), FOREIGN KEY(policy_id) REFERENCES policies(id) ON DELETE CASCADE);
        """)
        cols={r['name'] for r in db.execute('PRAGMA table_info(policies)')}
        if 'customer_phone' not in cols: db.execute("ALTER TABLE policies ADD COLUMN customer_phone TEXT DEFAULT ''")
