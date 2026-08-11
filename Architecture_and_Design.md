# Architecture & Design Specifications

This document outlines the architectural flow, the implementation of Object-Oriented Design (OOD) patterns, database interaction, and the audit logging mechanism within the Console-Based Movie Ticket Booking System.

---

## 1. Architectural Flow: MVC + DAO

The application is built on a strictly layered **Model-View-Controller (MVC)** architecture, supplemented by the **Data Access Object (DAO)** pattern to separate persistence from business logic.

### Request Lifecycle
1. **User Input (View/CLI)**: The user interacts with the terminal menus (e.g., entering movie details, selecting seats).
2. **Routing (Controller)**: The `MainCLIController` routes the request to the appropriate domain controller (e.g., `MovieController`, `BookingController`).
3. **Business Logic (Service)**: The Controller delegates the task to a Service layer (e.g., `MovieService`). The Service enforces business rules (e.g., ensuring a movie cannot be deleted if active bookings exist).
4. **Data Access (DAO)**: The Service calls the DAO (e.g., `MovieDAO`), which executes pure SQL commands using the Singleton database connection.
5. **Persistence (SQLite)**: The database executes the query and returns the result back up the chain to the View for rendering.

---

## 2. Design Patterns Implemented

The system extensively uses structural and behavioral design patterns to ensure scalability and clean code.

### A. Singleton Pattern
**Usage**: Database Connection Management.
**Implementation**: `DatabaseConnectionManager` (in `Db_utils.py`) overrides the `__new__` method to guarantee only one SQLite connection instance exists during the application's lifecycle. 
**Benefit**: Prevents memory leaks, connection locking issues, and ensures thread safety across all DAOs.

### B. Factory Method Pattern
**Usage**: User Authentication & Instantiation.
**Implementation**: `UserFactory` (in `Modules/Auth/UserFactory.py`) takes raw database rows and a role enum (`UserRole`), dynamically instantiating either an `Admin` or a `Customer` object based on the role.
**Benefit**: Promotes polymorphism. The system doesn't need to know the exact class of a user until runtime.

### C. Builder Pattern
**Usage**: Ticket Booking Construction.
**Implementation**: `BookingBuilder` (in `Modules/Bookings/BookingBuilder.py`) separates the complex construction of a `Booking` object from its representation. It incrementally sets the customer ID, showtime ID, applies pricing strategies, creates individual `BookingSeat` objects, and calculates the final total amount before returning the fully assembled `Booking`.
**Benefit**: Encapsulates the complexity of calculating seat prices and mapping multiple seats to a single transaction.

### D. Observer Pattern
**Usage**: Decoupled Event Notifications.
**Implementation**: `NotificationService` acts as the *Subject*. Whenever a new movie is added or a showtime is scheduled, it triggers a `notify_observers()` call. `ConsoleCustomerObserver` implements the *Observer* interface, reacting to these events (currently by printing system alerts).
**Benefit**: The `MovieService` doesn't need to know how notifications are handled, allowing for future extensions (like Email or SMS observers) without changing core logic.

### E. Strategy Pattern
**Usage 1: Dynamic Pricing**. `ShowtimePricingStrategy` (in `Modules/Bookings/PricingStrategy.py`) defines how seats are priced. `VIPRowPricingStrategy` charges base price for standard rows but adds a premium for VIP rows (e.g., Row E).
**Usage 2: Movie Search**. `SearchStrategy` (in `Modules/Movies/Strategies.py`) defines how movies are filtered. Implementations include `SearchByTitleStrategy`, `SearchByGenreStrategy`, and `SearchByLanguageStrategy`. The `MovieService` executes the search dynamically based on the injected strategy.
**Benefit**: New pricing algorithms or search filters can be added simply by creating a new Strategy class, adhering to the Open/Closed Principle.

### F. DAO (Repository) Pattern
**Usage**: Database Abstraction.
**Implementation**: Every entity has a corresponding DAO (e.g., `TheaterDAO`, `ShowtimeDAO`). These classes contain the raw `INSERT`, `UPDATE`, `SELECT`, and `DELETE` SQL statements.
**Benefit**: If the system migrates from SQLite to PostgreSQL in the future, only the DAOs need to change. The Service layer remains completely untouched.

---

## 3. Database Interactivity

The system uses `sqlite3` natively. Database interactivity is heavily managed to ensure data integrity and prevent race conditions.

- **Foreign Keys Enforced**: `PRAGMA foreign_keys = ON;` is executed on startup, ensuring that (for example) a `Booking` cannot exist if the associated `Customer` is deleted.
- **ACID Transactions**: In complex operations, specifically Ticket Booking (`BookingService.book_tickets`), transactions are used (`BEGIN`, `COMMIT`, `ROLLBACK`). 
  - When booking, the system checks seat availability. If two users try to book the exact same seat at the exact same millisecond, the transaction isolating locks the row, and a `SeatAlreadyBookedError` is raised for the slower request, preventing double-booking.
  - The `Booking` and all associated `BookingSeat` rows are inserted in a single atomic commit.
- **Seat Matrix Generation**: The database calculates available seats dynamically. It queries the total capacity of the screen, generates a matrix (e.g., A1 to J10), and queries the `booking_seats` table to mark which seats are taken (`[X]`).

---

## 4. Audit Logging Mechanism (The Log Feature)

The application features a silent, background **Audit Logger** that tracks all critical state changes (`INSERT`, `UPDATE`, `DELETE`) in the database.

### How it Works
1. **Triggering**: Whenever an Admin modifies data (e.g., Adds a Movie, Deletes a Showtime, Creates a Theater), the respective Service (e.g., `MovieService.delete_movie`) successfully completes the database transaction via the DAO.
2. **Delegation**: Immediately after the successful commit, the Service explicitly calls the `AuditService.log_action()`.
3. **Recording**: The `AuditService` constructs an `AuditModel` containing:
   - `admin_id`: Who performed the action.
   - `action`: The `AuditAction` Enum (`INSERT`, `UPDATE`, `DELETE`).
   - `table_name`: The database table affected (e.g., `movies`).
   - `record_id`: The ID of the modified record.
   - `description`: A human-readable summary (e.g., "Deleted movie 'Inception'").
4. **Persistence**: The `AuditDAO` inserts this record into the `audit_logs` table.

This feature ensures that all administrative actions are securely tracked for accountability, preventing silent/unauthorized modifications to the catalog or schedule.
