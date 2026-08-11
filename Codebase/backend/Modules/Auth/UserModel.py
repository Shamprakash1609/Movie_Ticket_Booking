from Modules.Common.Enums import UserRole

class User:
    def __init__(self, user_id, username, password, email, phone, role):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.phone = phone
        self.role = role

    def get_role(self):
        return self.role

class Admin(User):
    def __init__(self, user_id, username, password, email, phone):
        super().__init__(user_id, username, password, email, phone, UserRole.ADMIN)

class Customer(User):
    def __init__(self, user_id, username, password, email, phone):
        super().__init__(user_id, username, password, email, phone, UserRole.CUSTOMER)
