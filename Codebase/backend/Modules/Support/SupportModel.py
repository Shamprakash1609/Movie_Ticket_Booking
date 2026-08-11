class ContactRequest:
    def __init__(self, request_id, name, email, message, created_at=None):
        self.request_id = request_id
        self.name = name
        self.email = email
        self.message = message
        self.created_at = created_at
