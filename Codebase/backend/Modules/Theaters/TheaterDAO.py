from Db_utils import DatabaseConnectionManager
from Modules.Theaters.TheaterModel import Theater
from Modules.Theaters.ScreenModel import Screen


class TheaterDAO:
    def __init__(self):
        self.db = DatabaseConnectionManager()

    def insert_theater(self, theater):
        query = """
            INSERT INTO theaters (name, location, city, capacity, created_by)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor = self.db.execute(
            query,
            (
                theater.name,
                theater.location,
                theater.city,
                theater.capacity,
                theater.created_by,
            ),
        )
        self.db.commit()
        return cursor.lastrowid

    def insert_screen(self, screen):
        query = """
            INSERT INTO screens (theater_id, screen_name, capacity)
            VALUES (?, ?, ?)
        """
        cursor = self.db.execute(
            query, (screen.theater_id, screen.screen_name, screen.capacity)
        )
        self.db.commit()
        return cursor.lastrowid

    def get_all_theaters(self, city=None):
        if city:
            query = "SELECT * FROM theaters WHERE city LIKE ?"
            rows = self.db.fetchall(query, (f"%{city}%",))
        else:
            query = "SELECT * FROM theaters"
            rows = self.db.fetchall(query)

        return [self._map_theater(r) for r in rows]

    def get_theater_by_id(self, theater_id):
        query = "SELECT * FROM theaters WHERE theater_id = ?"
        row = self.db.fetchone(query, (theater_id,))
        return self._map_theater(row) if row else None

    def get_screens_by_theater(self, theater_id):
        query = "SELECT * FROM screens WHERE theater_id = ?"
        rows = self.db.fetchall(query, (theater_id,))
        return [self._map_screen(r) for r in rows]

    def _map_theater(self, row):
        return Theater(
            theater_id=row["theater_id"],
            name=row["name"],
            location=row["location"],
            city=row["city"],
            capacity=row["capacity"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _map_screen(self, row):
        return Screen(
            screen_id=row["screen_id"],
            theater_id=row["theater_id"],
            screen_name=row["screen_name"],
            capacity=row["capacity"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
