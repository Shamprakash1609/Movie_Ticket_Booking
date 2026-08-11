# Console-Based Movie Ticket Booking System

This is a robust, terminal-based (CLI) Movie Ticket Booking application built in **Python (3.10+)** using **SQLite** for persistence. The system avoids all UI dependencies (no Flask, Django, HTML, etc.) and focuses strictly on Object-Oriented Design (OOD) principles, explicit structural Design Patterns, and a clean Model-View-Controller (MVC) architecture.

## 🏗️ Architecture & Design Patterns

The codebase is organized using the **Model-View-Controller (MVC)** pattern supplemented by a **Data Access Object (DAO)** layer to cleanly separate database persistence from core business logic.

The application explicitly implements six core Design Patterns:

1. **Singleton Pattern**: 
   - `DatabaseConnectionManager` (`Db_utils.py`) guarantees a single, thread-safe SQLite connection instance across the entire application lifecycle.
2. **Factory Method Pattern**: 
   - `UserFactory` dynamically instantiates domain models (`Admin` or `Customer`) based on roles during authentication.
3. **Builder Pattern**: 
   - `BookingBuilder` handles the step-by-step assembly of complex `Booking` objects, attaching users, showtimes, seats, and calculating total cost before an atomic database commit.
4. **Observer Pattern**: 
   - A `NotificationService` acts as a Subject, notifying a `CustomerObserver` whenever an Admin adds a new movie or modifies a showtime.
5. **Strategy Pattern**: 
   - Used for dynamic query filters (`MovieSearchStrategy`: by Title, Genre, Language) and dynamic pricing rules (`ShowtimePricingStrategy`: Base price vs. VIP row pricing).
6. **DAO / Repository Pattern**: 
   - Encapsulates all raw SQLite CRUD statements behind strictly typed classes (e.g., `UserDAO`, `MovieDAO`, `BookingDAO`).

## ✨ Key Features

### Admin Capabilities
- **Authentication**: Secure login as system administrator.
- **Movie Management**: Add, update, delete (blocked if active bookings exist), and search movies.
- **Theater Management**: Create theaters and auto-generate linked screening halls based on total capacity.
- **Showtime Scheduling**: Schedule movies to screens. Includes a built-in overlap checker to prevent scheduling conflicts.
- **System Overview**: View all active and past bookings across the system and export booking logs to CSV files.

### Customer Capabilities
- **Onboarding**: Register a new account with email validation and secure password hashing.
- **Browsing**: Browse and search movies by genre or language.
- **Booking Flow**: View interactive seat matrices for specific showtimes, select seats, and execute transactional bookings.
- **Profile & Support**: View personal booking history, cancel upcoming bookings (with auto-refunds), update profile details, and submit support tickets.

## 📂 Project Structure
```text
Codebase/backend/
├── Main.py                 # Application entry point and CLI Routing loop
├── Db_utils.py             # SQLite Singleton connection and Schema definitions
└── Modules/
    ├── Auth/               # Registration, Login, User Factory & Models
    ├── Movies/             # Movie CRUD, Views, and Search Strategies
    ├── Theaters/           # Theaters and Screens management
    ├── Showtimes/          # Showtime logic and Overlap checking
    ├── Bookings/           # Booking transactions, Pricing Strategies, Seat layouts
    ├── Notifications/      # Observer pattern implementations
    ├── Audit/              # Silent system change logger (INSERT/UPDATE/DELETE)
    ├── Support/            # Customer contact requests and profile management
    └── Common/             # Enums, custom Exceptions, Type hinting, CLI formatters
```

## 🚀 How to Run the Application

This system uses zero external dependencies. You do not need to set up a virtual environment or run `pip install`. It relies solely on Python's built-in libraries (like `sqlite3`, `hashlib`, `csv`, `datetime`, etc.).

### 1. Start the Application
Open your terminal, navigate to the root folder of this project, and execute the main entry file:

```bash
python Codebase/backend/Main.py
```

### 2. Initial Setup & Default Admin
On the very first execution, the system will automatically create the `movies.db` SQLite database file inside the `backend/` directory and populate all required tables. 

If no admins are found in the system, it automatically injects a default admin account. Use these credentials to log in as an Admin and start adding Theaters, Movies, and Showtimes:

- **Username**: `admin`
- **Password**: `admin`

### 3. Customer Usage
After logging out of the Admin account (or opening a new session), choose `Register Customer Account` from the main menu to create a standard user profile and test the ticket booking flows!
