class Theater:
    def __init__(
        self,
        theater_id,
        name,
        location,
        city,
        capacity,
        created_by,
        created_at=None,
        updated_at=None,
    ):
        self.theater_id = theater_id
        self.name = name
        self.location = location
        self.city = city
        self.capacity = capacity
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at
