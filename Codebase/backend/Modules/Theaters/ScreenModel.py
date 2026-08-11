class Screen:
    def __init__(
        self,
        screen_id,
        theater_id,
        screen_name,
        capacity,
        created_at=None,
        updated_at=None,
    ):
        self.screen_id = screen_id
        self.theater_id = theater_id
        self.screen_name = screen_name
        self.capacity = capacity
        self.created_at = created_at
        self.updated_at = updated_at
