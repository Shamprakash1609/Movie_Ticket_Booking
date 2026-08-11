from Modules.Support.SupportDAO import SupportDAO
from Modules.Support.SupportModel import ContactRequest
from Modules.Common.Helpers import Helpers
from Modules.Auth.UserDAO import UserDAO
from Modules.Auth.UserModel import User
from Modules.Audit.AuditService import AuditService
from Modules.Common.Enums import AuditAction
from Modules.Common.Exceptions import InvalidInputError, MovieTicketSystemError
import getpass


class SupportController:
    def __init__(self):
        self.support_dao = SupportDAO()
        self.user_dao = UserDAO()
        self.audit_service = AuditService()

    def contact_us(self):
        print("\n--- Contact Us ---")
        name = input("Name: ")
        email = input("Email: ")
        message = input("Message/Issue: ")

        if not name or not email or not message:
            print("[Error] All fields are required.")
            return

        if not Helpers.is_valid_email(email):
            print("[Error] Invalid email format.")
            return

        req = ContactRequest(request_id=None, name=name, email=email, message=message)

        req_id = self.support_dao.insert(req)
        # Log to audit manually with system changed_by
        self.audit_service.log_action("contact_requests", req_id, AuditAction.INSERT)

        print(
            "\n[Success] Your message has been sent. Our support team will get back to you soon."
        )

    def manage_profile(self, user):
        while True:
            print("\n--- Profile Management ---")
            print(f"Current Name: {user.username}")
            print(f"Current Email: {user.email}")
            print(f"Current Phone: {user.phone}")
            print("\n1. Edit Profile Information")
            print("2. Change Password")
            print("3. Back")

            choice = input("Choice: ")

            if choice == "1":
                new_name = input(f"New Username [{user.username}]: ") or user.username
                new_email = input(f"New Email [{user.email}]: ") or user.email
                new_phone = input(f"New Phone [{user.phone}]: ") or user.phone

                if new_email != user.email and not Helpers.is_valid_email(new_email):
                    print("[Error] Invalid email format.")
                    continue

                user.username = new_name
                user.email = new_email
                user.phone = new_phone

                self.user_dao.update(user)
                self.audit_service.log_action(
                    "users", user.user_id, AuditAction.UPDATE, user.user_id
                )
                print("[Success] Profile updated.")

            elif choice == "2":
                old_pass = getpass.getpass("Current Password: ")
                if not Helpers.verify_password(user.password, old_pass):
                    print("[Error] Incorrect current password.")
                    continue

                new_pass = getpass.getpass("New Password: ")
                if len(new_pass) < 4:
                    print("[Error] Password too short.")
                    continue

                user.password = Helpers.hash_password(new_pass)
                self.user_dao.update(user)
                self.audit_service.log_action(
                    "users", user.user_id, AuditAction.UPDATE, user.user_id
                )
                print("[Success] Password updated.")

            elif choice == "3":
                break
            else:
                print("[Error] Invalid choice.")

        return user
