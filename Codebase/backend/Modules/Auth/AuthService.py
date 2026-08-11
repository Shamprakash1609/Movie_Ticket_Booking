
from Modules.Auth.UserDAO import UserDAO
from Modules.Auth.UserModel import User
from Modules.Auth.UserFactory import UserFactory
from Modules.Common.Helpers import Helpers
from Modules.Common.Exceptions import AuthenticationError, RegistrationError
from Modules.Common.Enums import UserRole, AuditAction
from Modules.Audit.AuditService import AuditService

class AuthService:
    def __init__(self):
        self.user_dao = UserDAO()
        self.audit_service = AuditService()

    def register_customer(self, username, password, email, phone):
        """Register a new customer account."""
        
        # Validations
        if not username or not password or not email:
            raise RegistrationError("Username, password, and email are required.")
            
        if not Helpers.is_valid_email(email):
            raise RegistrationError("Invalid email format.")
            
        if self.user_dao.get_by_username(username):
            raise RegistrationError("Username already exists.")
            
        if self.user_dao.get_by_email(email):
            raise RegistrationError("Email already exists.")

        hashed_password = Helpers.hash_password(password)
        
        new_customer = UserFactory.create_user(
            role=UserRole.CUSTOMER.value,
            username=username,
            password=hashed_password,
            email=email,
            phone=phone
        )
        
        user_id = self.user_dao.insert(new_customer)
        new_customer.user_id = user_id
        
        self.audit_service.log_action("users", user_id, AuditAction.INSERT, user_id)
        
        return new_customer

    def authenticate(self, username_or_email, password, as_admin= False):
        """Authenticate user (Admin or Customer)"""
        
        # Try finding by username first, then by email
        user = self.user_dao.get_by_username(username_or_email)
        if not user:
            user = self.user_dao.get_by_email(username_or_email)
            
        if not user:
            raise AuthenticationError("Invalid credentials.")
            
        if not Helpers.verify_password(user.password, password):
            raise AuthenticationError("Invalid credentials.")
            
        if as_admin and user.role != UserRole.ADMIN:
            raise AuthenticationError("Unauthorized access. Admin role required.")
            
        if not as_admin and user.role != UserRole.CUSTOMER:
            raise AuthenticationError("Unauthorized access. Customer role required.")
            
        return user
