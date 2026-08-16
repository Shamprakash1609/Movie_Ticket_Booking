from Modules.Auth.AuthService import AuthService
from Modules.Auth.UserModel import User
from Modules.Common.Exceptions import AuthenticationError, RegistrationError
from Modules.Common.Helpers import Helpers
import getpass

class AuthController:
    def __init__(self):
        self.auth_service = AuthService()

    def admin_login(self):
        print("\n--- Admin Login ---")
        username = input("Username/Email: ")
        password = getpass.getpass("Password: ")

        try:
            user = self.auth_service.authenticate(username, password, as_admin=True)
            print(f"\nWelcome back, Admin {user.username}!")
            return user
        except AuthenticationError as e:
            print(f"\n[Error] {str(e)}")
            return None

    def customer_login(self):
        print("\n--- Customer Login ---")
        email = input("Email/Username: ")
        password = getpass.getpass("Password: ")

        try:
            user = self.auth_service.authenticate(email, password, as_admin=False)
            print(f"\nWelcome back, {user.username}!")
            return user
        except AuthenticationError as e:
            print(f"\n[Error] {str(e)}")
            return None

    def register_customer(self):
        print("\n--- Customer Registration ---")
        print("(Note: Type 'c' or 'cancel' at any prompt to cancel registration)")

        username = Helpers.prompt_non_empty("Username (e.g., john_doe): ")
        if not username: return

        while True:
            email = Helpers.prompt_non_empty("Email (e.g., john@example.com): ")
            if not email: return
            if Helpers.is_valid_email(email):
                break
            print("[Input Error] Invalid email format. Example: user@domain.com. Please try again.")

        phone = input("Phone Number (e.g., +15551234567) [Optional]: ").strip()

        while True:
            password = getpass.getpass("Password (at least 4 characters): ")
            if len(password) >= 4:
                break
            print("[Input Error] Password must be at least 4 characters long. Please try again.")

        try:
            user = self.auth_service.register_customer(username, password, email, phone)
            print(f"\n[Success] Registration successful! Welcome, {user.username}. You can now log in.")
            return user
        except RegistrationError as e:
            print(f"\n[Error] {str(e)}")
            return None
