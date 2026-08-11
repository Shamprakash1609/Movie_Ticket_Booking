from Db_utils import DatabaseConnectionManager
from Modules.Support.SupportModel import ContactRequest
import sqlite3


class SupportDAO:
    def __init__(self):
        self.db = DatabaseConnectionManager()
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        query = """
        CREATE TABLE IF NOT EXISTS contact_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute(query)
        self.db.commit()

    def insert(self, request):
        query = "INSERT INTO contact_requests (name, email, message) VALUES (?, ?, ?)"
        cursor = self.db.execute(query, (request.name, request.email, request.message))
        self.db.commit()
        return cursor.lastrowid
