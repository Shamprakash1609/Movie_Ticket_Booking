import sqlite3
import threading

import os


class DatabaseConnectionManager:
    """Singleton pattern for managing the SQLite database connection."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_name="movies.db"):
        with cls._lock:
            if cls._instance is None:
                # Only publish the instance once it is fully connected, otherwise a
                # failed _init_connection leaves a half-built object cached forever.
                instance = super(DatabaseConnectionManager, cls).__new__(cls)
                instance._init_connection(db_name)
                cls._instance = instance
            return cls._instance

    def _init_connection(self, db_name):
        # Use an absolute or appropriate relative path for the DB
        # To make it run consistently wherever the backend is started
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # To return dict-like objects
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        schema = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            phone VARCHAR(15),
            role TEXT CHECK(role IN ('ADMIN', 'CUSTOMER')) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS movies (
            movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            duration INTEGER NOT NULL,
            genre VARCHAR(50) NOT NULL,
            language VARCHAR(50) NOT NULL,
            release_date TEXT NOT NULL,
            rating REAL DEFAULT 0.0,
            poster_url VARCHAR(255),
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS theaters (
            theater_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            location VARCHAR(255) NOT NULL,
            city VARCHAR(50) NOT NULL,
            capacity INTEGER NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS screens (
            screen_id INTEGER PRIMARY KEY AUTOINCREMENT,
            theater_id INTEGER NOT NULL,
            screen_name VARCHAR(50) NOT NULL,
            capacity INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (theater_id) REFERENCES theaters(theater_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS showtimes (
            showtime_id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            screen_id INTEGER NOT NULL,
            start_time TEXT NOT NULL, -- Format: YYYY-MM-DD HH:MM:SS
            end_time TEXT NOT NULL,   -- Format: YYYY-MM-DD HH:MM:SS
            price REAL NOT NULL,
            available_seats INTEGER NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
            FOREIGN KEY (screen_id) REFERENCES screens(screen_id),
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            showtime_id INTEGER NOT NULL,
            booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL,
            status TEXT CHECK(status IN ('CONFIRMED', 'CANCELLED', 'COMPLETED')) DEFAULT 'CONFIRMED',
            payment_status TEXT CHECK(payment_status IN ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED')) DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (showtime_id) REFERENCES showtimes(showtime_id)
        );

        CREATE TABLE IF NOT EXISTS booking_seats (
            booking_seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            seat_number VARCHAR(10) NOT NULL,
            price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name VARCHAR(50) NOT NULL,
            record_id INTEGER NOT NULL,
            action TEXT CHECK(action IN ('INSERT', 'UPDATE', 'DELETE')) NOT NULL,
            changed_by INTEGER,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (changed_by) REFERENCES users(user_id)
        );
        """
        try:
            cursor.executescript(schema)
            self.conn.commit()

            # Check if there's any admin, if not, create a default admin
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'ADMIN'")
            if cursor.fetchone()[0] == 0:
                import hashlib

                pw = hashlib.sha256("admin".encode("utf-8")).hexdigest()
                cursor.execute(
                    "INSERT INTO users (username, password, email, phone, role) VALUES (?, ?, ?, ?, ?)",
                    ("admin", pw, "admin@system.com", "0000000000", "ADMIN"),
                )
                # The seeded admin is a real change to the users table, so it belongs
                # in the audit trail too. Written directly because AuditService imports
                # this module (importing it here would be circular).
                cursor.execute(
                    "INSERT INTO audit_logs (table_name, record_id, action, changed_by) "
                    "VALUES (?, ?, ?, ?)",
                    ("users", cursor.lastrowid, "INSERT", None),
                )
                self.conn.commit()

        except sqlite3.Error as e:
            # Re-raise: continuing on a half-created schema only turns one clear
            # startup error into confusing "no such table" failures later.
            print(f"Database error during table creation: {e}")
            self.conn.rollback()
            raise

    def execute(self, query, params=()):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor
        except sqlite3.Error as e:
            print(f"Execute Error: {e}")
            raise e

    def executemany(self, query, params):
        try:
            cursor = self.conn.cursor()
            cursor.executemany(query, params)
            return cursor
        except sqlite3.Error as e:
            print(f"Executemany Error: {e}")
            raise e

    def fetchone(self, query, params=()):
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self, query, params=()):
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        # Drop the cached instance, otherwise the next DatabaseConnectionManager()
        # hands back this closed object and every query raises ProgrammingError.
        DatabaseConnectionManager._instance = None
