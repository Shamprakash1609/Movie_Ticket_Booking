import sys
from Db_utils import DatabaseConnectionManager
from Modules.Auth.AuthController import AuthController
from Modules.Auth.UserModel import User
from Modules.Common.Enums import UserRole
from Modules.Movies.MovieController import MovieController
from Modules.Theaters.TheaterController import TheaterController
from Modules.Showtimes.ShowtimeController import ShowtimeController
from Modules.Bookings.BookingController import BookingController
from Modules.Support.SupportController import SupportController
from Modules.Common.Helpers import Helpers

class MainCLIController:
    def __init__(self):
        self.auth_controller = AuthController()
        self.movie_controller = MovieController()
        self.theater_controller = TheaterController()
        self.showtime_controller = ShowtimeController()
        self.booking_controller = BookingController()
        self.support_controller = SupportController()

    def start(self):
        while True:
            # Helpers.clear_screen()
            print("=====================================================")
            print("       MOVIE TICKET BOOKING SYSTEM - TERMINAL        ")
            print("=====================================================")
            print("1. Login (Admin / Customer)")
            print("2. Register Customer Account")
            print("3. Browse Movies as Guest")
            print("4. View Theaters")
            print("5. Exit Application")

            choice = input("\nEnter your choice: ")

            if choice == '1':
                self.handle_login()
            elif choice == '2':
                self.auth_controller.register_customer()
            elif choice == '3':
                self.movie_controller.browse_movies_customer()
            elif choice == '4':
                self.theater_controller.view_theaters()
            elif choice == '5':
                print("Exiting application. Goodbye!")
                sys.exit(0)
            else:
                print("[Error] Invalid choice.")

    def handle_login(self):
        print("\nLogin As:")
        print("1. Customer")
        print("2. Admin")

        choice = input("Choice: ")

        if choice == '1':
            user = self.auth_controller.customer_login()
            if user:
                self.run_customer_dashboard(user)
        elif choice == '2':
            user = self.auth_controller.admin_login()
            if user:
                self.run_admin_dashboard(user)
        else:
            print("[Error] Invalid choice.")

    def run_admin_dashboard(self, admin):
        while True:
            print("\n=====================================================")
            print(f"             ADMIN DASHBOARD - {admin.username}             ")
            print("=====================================================")
            print("1. Add New Movie")
            print("2. View & Search Movies")
            print("3. Update Movie Details")
            print("4. Delete a Movie")
            print("5. Add Theatre & Screens")
            print("6. Manage Showtimes (Add)")
            print("7. View All Bookings & Export")
            print("8. Logout")

            choice = input("\nEnter your choice: ")

            if choice == '1':
                self.movie_controller.add_movie(admin.user_id)
            elif choice == '2':
                self.movie_controller.view_movies_admin()
            elif choice == '3':
                self.movie_controller.update_movie(admin.user_id)
            elif choice == '4':
                self.movie_controller.delete_movie(admin.user_id)
            elif choice == '5':
                self.theater_controller.add_theater(admin.user_id)
            elif choice == '6':
                self.showtime_controller.add_showtime(admin.user_id)
            elif choice == '7':
                self.booking_controller.view_all_bookings_admin()
            elif choice == '8':
                print("Logging out...")
                break
            else:
                print("[Error] Invalid choice.")

    def run_customer_dashboard(self, customer):
        while True:
            print("\n=====================================================")
            print(f"           CUSTOMER DASHBOARD - {customer.username}           ")
            print("=====================================================")
            print("1. Browse Movies")
            print("2. View Movie Details & Available Showtimes")
            print("3. Book Tickets")
            print("4. View My Bookings")
            print("5. Cancel Booking")
            print("6. View Theatres")
            print("7. View Showtimes by Theatre")
            print("8. User Profile Management")
            print("9. Contact Us & Support")
            print("10. Logout")

            choice = input("\nEnter your choice: ")

            if choice == '1':
                self.movie_controller.browse_movies_customer()
            elif choice == '2':
                self.showtime_controller.view_movie_details_and_showtimes()
            elif choice == '3':
                self.booking_controller.book_tickets(customer.user_id)
            elif choice == '4':
                self.booking_controller.view_my_bookings(customer.user_id)
            elif choice == '5':
                self.booking_controller.cancel_booking(customer.user_id)
            elif choice == '6':
                self.theater_controller.view_theaters()
            elif choice == '7':
                self.showtime_controller.view_showtimes_by_theater()
            elif choice == '8':
                # Re-assign back to track memory object if it changed
                customer = self.support_controller.manage_profile(customer)
            elif choice == '9':
                self.support_controller.contact_us()
            elif choice == '10':
                print("Logging out...")
                break
            else:
                print("[Error] Invalid choice.")


if __name__ == "__main__":
    # Ensure database is initialized before anything else
    db = DatabaseConnectionManager()

    app = MainCLIController()

    try:
        app.start()
    except KeyboardInterrupt:
        print("\nForce exiting application. Goodbye!")
        db.close()
        sys.exit(0)
    except Exception as e:
        # Last-resort net: an unexpected error should report itself rather than
        # dumping a traceback and losing the session.
        print(f"\n[Fatal] Unexpected error: {type(e).__name__}: {e}")
        db.close()
        sys.exit(1)
