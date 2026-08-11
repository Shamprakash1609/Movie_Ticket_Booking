from Modules.Theaters.TheaterDAO import TheaterDAO
from Modules.Theaters.TheaterModel import Theater
from Modules.Theaters.ScreenModel import Screen
from Modules.Audit.AuditService import AuditService
from Modules.Common.Enums import AuditAction
from Modules.Common.Exceptions import InvalidInputError


class TheaterService:
    def __init__(self):
        self.theater_dao = TheaterDAO()
        self.audit_service = AuditService()

    def add_theater_with_screens(self, theater, num_screens, admin_id):
        if not theater.name or not theater.city:
            raise InvalidInputError("Theater name and city are required.")

        if theater.capacity <= 0:
            raise InvalidInputError("Total capacity must be greater than 0.")

        if num_screens <= 0:
            raise InvalidInputError("Number of screens must be at least 1.")

        theater_id = self.theater_dao.insert_theater(theater)
        theater.theater_id = theater_id
        self.audit_service.log_action(
            "theaters", theater_id, AuditAction.INSERT, admin_id
        )

        # Auto-generate screens (capacity divided roughly equally)
        screen_capacity = theater.capacity // num_screens

        for i in range(1, num_screens + 1):
            s = Screen(
                screen_id=None,
                theater_id=theater_id,
                screen_name=f"Screen {i}",
                capacity=screen_capacity,
            )
            screen_id = self.theater_dao.insert_screen(s)
            self.audit_service.log_action(
                "screens", screen_id, AuditAction.INSERT, admin_id
            )

        return theater

    def get_all_theaters(self, city=None):
        return self.theater_dao.get_all_theaters(city)

    def get_screens(self, theater_id):
        return self.theater_dao.get_screens_by_theater(theater_id)
