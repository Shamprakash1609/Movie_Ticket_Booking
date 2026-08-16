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

        num_screens = Helpers.prompt_int(
            "Number of screens in this theater (e.g. 3): ", min_val=1
        )
        if num_screens is None:
            return

        # Seats are captured per screen so the booking seat map matches exactly
        # what the admin configured here.
        screens = []
        for i in range(1, num_screens + 1):
            screen_name = input(
                f"  Screen {i} name (press Enter for 'Screen {i}'): "
            ).strip()
            if screen_name.lower() in ("c", "cancel", "q", "quit"):
                print("Operation cancelled.")
                return
            if not screen_name:
                screen_name = f"Screen {i}"

            seats = Helpers.prompt_int(
                f"  Number of seats in '{screen_name}' (e.g. 120): ", min_val=1
            )
            if seats is None:
                return

            screens.append({"screen_name": screen_name, "capacity": seats})

        total_capacity = sum(s["capacity"] for s in screens)

        print("\nTheater Summary:")
        Helpers.print_table(
            ["Screen", "Seats"],
            [[s["screen_name"], s["capacity"]] for s in screens]
            + [["TOTAL", total_capacity]],
        )

        confirm = input("Save this theater? [Y/n]: ").strip().lower()
        if confirm and confirm not in ("y", "yes"):
            print("Operation cancelled.")
            return

        theater = Theater(
            theater_id=None,
            name=name,
            location=location,
            city=city,
            capacity=total_capacity,
            created_by=admin_id,
        )

        try:
            self.theater_service.add_theater_with_screens(theater, screens, admin_id)
            print(
                f"\n[Success] Theater '{name}' added with {num_screens} screen(s) "
                f"and {total_capacity} total seats!"
            )
        except MovieTicketSystemError as e:
            print(f"\n[Error] {str(e)}")

    def view_theaters(self):
        print("\n--- View Theaters ---")
        city_filter = input("Enter City to filter (or press Enter for all): ").strip()

        theaters = self.theater_service.get_all_theaters(
            city_filter if city_filter else None
        )

        if not theaters:
            print("No theaters found.")
            return

        headers = ["ID", "Name", "Location", "City", "Total Seats"]
        rows = [
            [t.theater_id, t.name, t.location, t.city, t.capacity] for t in theaters
        ]

        Helpers.print_table(headers, rows)

        print("\nScreens:")
        for t in theaters:
            screens = self.theater_service.get_screens(t.theater_id)
            breakdown = (
                " | ".join(f"{s.screen_name}: {s.capacity} seats" for s in screens)
                if screens
                else "No screens configured"
            )
            print(f"  📺 [{t.theater_id}] {t.name} — {breakdown}")
