import io
import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Db_utils import DatabaseConnectionManager
from Main import MainCLIController

# Prepare simulated user inputs for full console interaction
inputs = [
    # 1. View Theaters as Guest
    "4",
    "", # Press enter for city filter
    
    # 2. Register Customer Account
    "2",
    "alice",
    "alice@example.com",
    "9876543210",
    "secretpassword",

    # 3. Login as Admin
    "1",
    "2", # Admin option
    "admin",
    "admin",

    # --- Admin Dashboard ---
    # Add Movie
    "1",
    "Avatar 3",
    "Return to Pandora for an epic journey",
    "190",
    "Sci-Fi",
    "English",
    "2026-12-18",

    # Add Theater
    "5",
    "PVR Superplex",
    "45 Park Street",
    "Metro City",
    "300",
    "3",

    # Manage Showtimes (Add)
    "6",
    "1", # Movie ID
    "1", # Theater ID
    "1", # Screen ID
    "2026-12-18 19:30",
    "250.00",

    # View & Search Movies
    "2",
    "1", # View All

    # View All Bookings & Export
    "7",

    # Logout Admin
    "8",

    # --- Customer Login & Flow ---
    "1",
    "1", # Customer option
    "alice@example.com",
    "secretpassword",

    # --- Customer Dashboard ---
    # Browse Movies
    "1",
    "1", # All Movies

    # View Movie Details & Showtimes
    "2",
    "1", # Movie ID 1

    # Book Tickets
    "3",
    "1", # Showtime ID 1
    "A1, A2", # Seats

    # View My Bookings
    "4",
    "3", # All

    # View Showtimes by Theater
    "7",
    "1", # Theater ID 1
    "2026-12-18", # Date

    # Contact Us & Support
    "9",
    "Alice",
    "alice@example.com",
    "Can I change my seats?",

    # Cancel Booking
    "5",
    "1", # Booking ID 1
    "y", # Confirm cancellation

    # Logout Customer
    "10",

    # Exit Application
    "5"
]

def run_cli_simulation():
    print("==========================================================")
    print("  SIMULATING FULL CONSOLE CLI APPLICATION INTERACTION     ")
    print("==========================================================")
    
    # Remove existing db if present to ensure clean run
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")
    if os.path.exists(db_file):
        os.remove(db_file)
        
    # Re-initialize DB
    db = DatabaseConnectionManager()
    
    # Mock sys.stdin with our inputs list
    sys.stdin = io.StringIO("\n".join(inputs) + "\n")
    
    controller = MainCLIController()
    
    try:
        controller.start()
    except SystemExit:
        print("\n==========================================================")
        print("  CONSOLE CLI SIMULATION COMPLETED SUCCESSFULLY!         ")
        print("==========================================================")

if __name__ == "__main__":
    run_cli_simulation()
