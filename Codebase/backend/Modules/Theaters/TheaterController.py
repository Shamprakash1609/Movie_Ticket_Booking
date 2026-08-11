from Modules.Theaters.TheaterService import TheaterService
from Modules.Theaters.TheaterModel import Theater
from Modules.Common.Exceptions import MovieTicketSystemError
from Modules.Common.Helpers import Helpers


class TheaterController:
    def __init__(self):
        self.theater_service = TheaterService()

    def add_theater(self, admin_id):
        print("\n--- Add New Theater & Screens ---")
        print("(Note: Type 'c' or 'cancel' at any prompt to cancel)")

        name = Helpers.prompt_non_empty("Theater Name (e.g. IMAX Cinema): ")
        if not name:
            return

        location = Helpers.prompt_non_empty("Location Address (e.g. 123 Main St): ")
        if not location:
            return

        city = Helpers.prompt_non_empty("City (e.g. New York): ")
        if not city:
            return

        capacity = Helpers.prompt_int("Total Seating Capacity (e.g. 300): ", min_val=1)
        if capacity is None:
            return

        num_screens = Helpers.prompt_int(
            "Number of default screens to auto-create (e.g. 3): ", min_val=1
        )
        if num_screens is None:
            return

        theater = Theater(
            theater_id=None,
            name=name,
            location=location,
            city=city,
            capacity=capacity,
            created_by=admin_id,
        )

        try:
            self.theater_service.add_theater_with_screens(
                theater, num_screens, admin_id
            )
            print(
                f"\n[Success] Theater '{name}' with {num_screens} screens added successfully!"
            )
        except MovieTicketSystemError as e:
            print(f"\n[Error] {str(e)}")

    def view_theaters(self):
        print("\n--- View Theaters ---")
        city_filter = input("Enter City to filter (or press Enter for all): ")

        theaters = self.theater_service.get_all_theaters(
            city_filter if city_filter else None
        )

        headers = ["ID", "Name", "Location", "City", "Total Capacity"]
        rows = [
            [t.theater_id, t.name, t.location, t.city, t.capacity] for t in theaters
        ]

        Helpers.print_table(headers, rows)
