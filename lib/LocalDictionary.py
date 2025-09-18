import sqlite3
import random

class LocalDictionary:
    def __init__(self, db_path="responses.db"):
        """Initialize the database connection and create table if missing."""
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.c = self.conn.cursor()
        self.c.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                prompt TEXT,
                reply  TEXT
            )
        """)
        self.conn.commit()

    def set(self, key: str, value: str):
        """Insert a new response for a given key (does not overwrite existing ones)."""
        self.c.execute("INSERT INTO responses (prompt, reply) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def getSome(self, key: str) -> str:
        """Get a random response for a given key. Returns None if not found."""
        self.c.execute("SELECT reply FROM responses WHERE prompt = ?", (key,))
        rows = self.c.fetchall()
        if rows:
            return random.choice([r[0] for r in rows])
        return None

    def count(self, key: str) -> int:
        """Return the number of responses stored for a given key."""
        self.c.execute("SELECT COUNT(*) FROM responses WHERE prompt = ?", (key,))
        return self.c.fetchone()[0]
    

    def exists(self, key: str, value: str) -> bool:
        """Return True if a key–value pair exists in the dictionary."""
        self.c.execute(
            "SELECT 1 FROM responses WHERE prompt = ? AND reply = ? LIMIT 1",
            (key, value)
        )
        return self.c.fetchone() is not None

    def __del__(self):
        """Ensure the database connection is closed when the object is deleted."""
        self.conn.close()
