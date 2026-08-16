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

    def add_theater_with_screens(self, theater, screens, admin_id):
        """Creates a theater and its screens using the seat counts supplied by the admin.

        `screens` is a list of {'screen_name': str, 'capacity': int}.
        """
        if not theater.name or not theater.city:
            raise InvalidInputError("Theater name and city are required.")

        if not screens:
            raise InvalidInputError("At least one screen is required.")

        for s in screens:
            if not s.get("screen_name"):
                raise InvalidInputError("Every screen needs a name.")
            if s.get("capacity", 0) <= 0:
                raise InvalidInputError(
                    f"Seat count for '{s.get('screen_name')}' must be greater than 0."
                )

        # The theater capacity is the sum of its screens, so no seats are lost.
        theater.capacity = sum(s["capacity"] for s in screens)

        theater_id = self.theater_dao.insert_theater(theater)
        theater.theater_id = theater_id
        self.audit_service.log_action(
            "theaters", theater_id, AuditAction.INSERT, admin_id
        )

        for spec in screens:
            s = Screen(
                screen_id=None,
                theater_id=theater_id,
                screen_name=spec["screen_name"],
                capacity=spec["capacity"],
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
