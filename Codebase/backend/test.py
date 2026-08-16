"""Scripted end-to-end walkthrough of the console application.

Drives Main.py through a full admin + customer session using a canned list of
keystrokes, then ASSERTS on what actually happened. Exits non-zero if any step
did not produce the expected result, so a broken build cannot report success.

    python3 test.py
"""

import getpass
import io
import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Db_utils import DatabaseConnectionManager
from Main import MainCLIController

# The simulation runs against its own database file so the real movies.db
# (with your live theatres, users and bookings) is never touched.
TEST_DB_NAME = "test_movies.db"

# Logins and password changes use getpass, which reads from the terminal and
# would ignore our scripted input. Route it through stdin for the simulation.
def _scripted_getpass(prompt="Password: "):
    print(prompt, end="")
    return sys.stdin.readline().rstrip("\n")


getpass.getpass = _scripted_getpass

# Prepare simulated user inputs for full console interaction.
#
# NOTE: booking is a five-step wizard (movie -> theatre -> date -> screen -> time).
# A screen step only appears when the movie runs on more than one screen at that
# theatre, so the counts below follow the data this script creates.
inputs = [
    # 1. View Theaters as Guest (none exist yet)
    "4",
    "",  # Press enter for city filter

    # 2. Register Customer Account
    "2",
    "alice",
    "alice@example.com",
    "9876543210",
    "secretpassword",

    # 2b. Register second customer
    "2",
    "Shamprakash R",
    "shamstark17a@gmail.com",
    "878123493",
    "sham1234",

    # 3. Login as Admin
    "1",
    "2",       # Admin option
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

    # Add Theater (3 screens, seats entered per screen)
    "5",
    "PVR Superplex",
    "45 Park Street",
    "Metro City",
    "3",      # Number of screens
    "",       # Screen 1 name -> default "Screen 1"
    "100",    # Screen 1 seats
    "",       # Screen 2 name -> default "Screen 2"
    "80",     # Screen 2 seats
    "IMAX",   # Screen 3 name
    "120",    # Screen 3 seats
    "y",      # Confirm save

    # Manage Showtimes (Add) - Screen 1, 100 seats
    "6",
    "1",      # Movie ID
    "1",      # Theater ID
    "1",      # Screen ID
    "2026-12-18 19:30",
    "14.50",

    # Manage Showtimes (Add) - IMAX, 120 seats
    "6",
    "1",      # Movie ID
    "1",      # Theater ID
    "3",      # Screen ID (IMAX)
    "2026-12-19 21:00",
    "350.00",

    # View & Search Movies
    "2",
    "1",      # View All

    # View All Bookings & Export
    "7",
    "n",      # Skip CSV export

    # Logout Admin
    "8",

    # --- Customer Login & Flow (alice) ---
    "1",
    "1",      # Customer option
    "alice@example.com",
    "secretpassword",

    # Browse Movies
    "1",
    "1",      # All Movies

    # View Movie Details & Showtimes
    "2",
    "1",      # Movie ID 1

    # Book Tickets: movie 1 -> theatre 1 -> "All dates" -> screen 1 -> first show
    "3",
    "1",      # movie
    "1",      # theatre
    "3",      # date: the synthetic "All dates" row (2 real dates + 1)
    "1",      # screen (movie runs on 2 screens here, so this step appears)
    "1",      # show time
    "A1, A2",
    "1",      # Pay by UPI

    # View My Bookings
    "4",
    "3",      # All

    # View Showtimes by Theatre
    "7",
    "1",      # theatre #1
    "1",      # first date

    # Contact Us & Support
    "9",
    "Alice",
    "alice@example.com",
    "Can I change my seats?",

    # Cancel Booking (entire booking)
    "5",
    "1",      # Booking ID 1
    "1",      # Cancel the entire booking
    "y",      # Confirm

    # Logout Customer
    "10",

    # --- Customer Login & Flow (Shamprakash R) ---
    "1",
    "1",
    "shamstark17a@gmail.com",
    "sham1234",

    # Book 6 seats on the 100-seat screen.
    # Screens are listed alphabetically, so #1 is "IMAX" and #2 is "Screen 1";
    # rows J* only exist on the 100-seat screen (10 x 10), not on IMAX (8 x 15).
    "3",
    "1", "1", "3", "2", "1",
    "J5, J6, J7, J8, J9, J10",
    "2",      # Pay by Credit / Debit Card

    # View My Bookings - all three filters
    "4", "1",
    "4", "2",
    "4", "3",

    # Cancel only 2 of the 6 seats
    "5",
    "2",      # Booking ID 2
    "2",      # Cancel only some seats
    "J9, J10",
    "y",

    # Confirm the booking now holds 4 seats
    "4", "1",

    # Seat map shows J9/J10 free again, then back out
    "3",
    "1", "1", "3", "2", "1",
    "c",      # Cancel out of the seat prompt

    # View Theatres (with the per-screen seat breakdown)
    "6",
    "",

    # View Showtimes by Theatre - every upcoming date
    "7",
    "1",
    "3",      # the synthetic "All dates" row

    # User Profile Management
    "8",
    "1",                    # Edit Profile Information
    "",                     # Keep username
    "sham.r@example.com",   # New email
    "9876500011",           # New phone
    "2",                    # Change Password
    "sham1234",             # Current password
    "sham5678",             # New password
    "3",                    # Back

    # Cancel the rest of the booking
    "5",
    "2",
    "1",
    "y",

    # Logout Customer
    "10",

    # Exit Application
    "5",
]

# (label, needle) pairs that must appear in the transcript.
EXPECTED = [
    ("guest sees empty theatre list", "No theaters found."),
    ("alice registered", "Welcome, alice"),
    ("second customer registered", "Welcome, Shamprakash R"),
    ("admin logged in", "Welcome back, Admin admin"),
    ("movie added", "Movie 'Avatar 3' (190 mins) added successfully"),
    ("theatre added with 3 screens", "added with 3 screen(s) and 300 total seats"),
    ("showtime scheduled", "Showtime scheduled successfully"),
    ("alice logged in", "Welcome back, alice"),
    ("alice booked seats", "Booking confirmed"),
    ("support message stored", "Your message has been sent"),
    ("alice cancelled her booking", "Booking cancelled. Refund"),
    ("second customer logged in", "Welcome back, Shamprakash R"),
    ("partial seat release", "seat(s) released"),
    ("profile updated", "Profile updated"),
    ("password updated", "Password updated"),
    ("application exited", "Goodbye"),
]

# Substrings that must NOT appear -- an unhandled error escaping to the console.
FORBIDDEN = [
    ("python traceback", "Traceback (most recent call last)"),
    ("raw sqlite error", "sqlite3."),
    ("fatal handler tripped", "[Fatal]"),
]


def run_cli_simulation():
    print("==========================================================")
    print("  SIMULATING FULL CONSOLE CLI APPLICATION INTERACTION     ")
    print("==========================================================")

    here = os.path.dirname(os.path.abspath(__file__))
    db_file = os.path.join(here, TEST_DB_NAME)
    if os.path.exists(db_file):
        os.remove(db_file)

    # Re-initialize DB. This is the singleton every DAO will reuse, so the whole
    # simulation runs against TEST_DB_NAME instead of the real movies.db.
    DatabaseConnectionManager._instance = None
    db = DatabaseConnectionManager(TEST_DB_NAME)
    if not db.conn or TEST_DB_NAME not in "".join(
        r["file"] or "" for r in db.fetchall("PRAGMA database_list")
    ):
        print("[Abort] Refusing to run: the simulation is not pointed at the test database.")
        return 1

    real_stdin = sys.stdin
    sys.stdin = io.StringIO("\n".join(inputs) + "\n")

    # Tee the transcript so it is both printed and available for assertions.
    transcript = io.StringIO()

    class Tee:
        def write(self, text):
            transcript.write(text)
            real_stdout.write(text)

        def flush(self):
            real_stdout.flush()

    real_stdout = sys.stdout
    sys.stdout = Tee()

    controller = MainCLIController()
    crashed = None
    try:
        controller.start()
    except SystemExit:
        pass
    except Exception as e:  # noqa: BLE001 - the simulation must report, not propagate
        crashed = f"{type(e).__name__}: {e}"
    finally:
        sys.stdout, sys.stdin = real_stdout, real_stdin

    out = transcript.getvalue()
    failures = []
    if crashed:
        failures.append(f"the application raised {crashed}")

    for label, needle in EXPECTED:
        if needle not in out:
            failures.append(f"missing: {label}  (expected to see {needle!r})")
    for label, needle in FORBIDDEN:
        if needle in out:
            failures.append(f"unexpected: {label}  (found {needle!r})")

    # The run must also have left real data behind.
    counts = {
        t: db.fetchone(f"SELECT COUNT(*) AS c FROM {t}")["c"]
        for t in ("users", "movies", "theaters", "screens", "showtimes",
                  "bookings", "booking_seats", "contact_requests", "audit_logs")
    }
    for table, minimum in (("users", 3), ("movies", 1), ("theaters", 1), ("screens", 3),
                           ("showtimes", 2), ("bookings", 2), ("contact_requests", 1),
                           ("audit_logs", 5)):
        if counts[table] < minimum:
            failures.append(f"table {table} has {counts[table]} rows, expected at least {minimum}")

    cancelled = db.fetchone("SELECT COUNT(*) AS c FROM bookings WHERE status = 'CANCELLED'")["c"]
    if cancelled < 2:
        failures.append(f"expected both bookings to end up CANCELLED, found {cancelled}")

    print("\n==========================================================")
    print("  ROW COUNTS: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    print("==========================================================")
    if failures:
        for f in failures:
            print("  FAIL  " + f)
        print("==========================================================")
        print(f"  CONSOLE CLI SIMULATION FAILED ({len(failures)} problem(s))")
        print("==========================================================")
        return 1

    print("  CONSOLE CLI SIMULATION COMPLETED SUCCESSFULLY!")
    print(f"  {len(EXPECTED)} expected outcomes verified, no unhandled errors.")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_cli_simulation())
