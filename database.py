import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FOLDER = BASE_DIR / "database"
DB_PATH = DB_FOLDER / "lostfound.db"

def get_db_connection():
    DB_FOLDER.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL CHECK(item_type IN ('lost', 'found')),
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            date_reported TEXT NOT NULL,
            image_filename TEXT,
            contact TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lost_item_id INTEGER NOT NULL,
            found_item_id INTEGER NOT NULL,
            similarity_score REAL NOT NULL,
            explanation TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (lost_item_id) REFERENCES items(id),
            FOREIGN KEY (found_item_id) REFERENCES items(id),
            UNIQUE(lost_item_id, found_item_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            student_usn TEXT NOT NULL,
            branch TEXT NOT NULL,
            year TEXT NOT NULL,
            contact TEXT NOT NULL,
            ownership_proof TEXT NOT NULL,
            message TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending', 'approved', 'rejected')),
            admin_note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_claims_item_status
        ON claims(item_id, status)
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
