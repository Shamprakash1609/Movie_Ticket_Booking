import sqlite3

from Db_utils import DatabaseConnectionManager
from Modules.Auth.UserModel import User
from Modules.Auth.UserFactory import UserFactory
from Modules.Common.Exceptions import RegistrationError


class UserDAO:
    """DAO Pattern for Users table"""

    def __init__(self):
        self.db = DatabaseConnectionManager()

    def get_by_username(self, username):
        query = "SELECT * FROM users WHERE username = ?"
        row = self.db.fetchone(query, (username,))
        return self._map_to_object(row) if row else None

    def get_by_email(self, email):
        query = "SELECT * FROM users WHERE email = ?"
        row = self.db.fetchone(query, (email,))
        return self._map_to_object(row) if row else None

    def get_by_id(self, user_id):
        query = "SELECT * FROM users WHERE user_id = ?"
        row = self.db.fetchone(query, (user_id,))
        return self._map_to_object(row) if row else None

    def insert(self, user):
        query = """
            INSERT INTO users (username, password, email, phone, role)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor = self.db.execute(
            query,
            (user.username, user.password, user.email, user.phone, user.role.value)
        )
        self.db.commit()
        return cursor.lastrowid

    def update(self, user):
        query = """
            UPDATE users
            SET username = ?, password = ?, email = ?, phone = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """
        try:
            self.db.execute(
                query,
                (user.username, user.password, user.email, user.phone, user.user_id)
            )
            self.db.commit()
        except sqlite3.IntegrityError as e:
            # username and email are UNIQUE; without this the raw driver error escapes
            # every "except MovieTicketSystemError" handler and kills the CLI.
            self.db.rollback()
            detail = str(e)
            if "username" in detail:
                raise RegistrationError("Username already exists.")
            if "email" in detail:
                raise RegistrationError("Email already exists.")
            raise RegistrationError("Could not update profile.")

    def _map_to_object(self, row):
        return UserFactory.create_user(
            role=row['role'],
            username=row['username'],
            password=row['password'],
            email=row['email'],
            phone=row['phone'],
            user_id=row['user_id']
        )
