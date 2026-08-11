from Modules.Auth.UserModel import User, Admin, Customer
from Modules.Common.Enums import UserRole


class UserFactory:
    """Factory Pattern to create User objects based on role."""

    @staticmethod
    def create_user(role, username, password, email, phone, user_id=None):

        if role == UserRole.ADMIN.value:
            return Admin(
                user_id=user_id,
                username=username,
                password=password,
                email=email,
                phone=phone,
            )
        elif role == UserRole.CUSTOMER.value:
            return Customer(
                user_id=user_id,
                username=username,
                password=password,
                email=email,
                phone=phone,
            )
        else:
            raise ValueError(f"Unknown UserRole: {role}")
