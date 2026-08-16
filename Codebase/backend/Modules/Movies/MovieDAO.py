from Db_utils import DatabaseConnectionManager
from Modules.Movies.MovieModel import Movie


class MovieDAO:
    def __init__(self):
        self.db = DatabaseConnectionManager()

    def insert(self, movie):
        query = """
            INSERT INTO movies (title, description, duration, genre, language, release_date, rating, poster_url, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.db.execute(
            query,
            (
                movie.title,
                movie.description,
                movie.duration,
                movie.genre,
                movie.language,
                movie.release_date,
                movie.rating,
                movie.poster_url,
                movie.created_by,
            ),
        )
        self.db.commit()
        return cursor.lastrowid

    def update(self, movie):
        query = """
            UPDATE movies
            SET title = ?, description = ?, duration = ?, genre = ?, language = ?,
                release_date = ?, rating = ?, poster_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE movie_id = ?
        """
        self.db.execute(
            query,
            (
                movie.title,
                movie.description,
                movie.duration,
                movie.genre,
                movie.language,
                movie.release_date,
                movie.rating,
                movie.poster_url,
                movie.movie_id,
            ),
        )
        self.db.commit()

    def delete(self, movie_id):
        query = "DELETE FROM movies WHERE movie_id = ?"
        self.db.execute(query, (movie_id,))
        self.db.commit()

    def get_by_id(self, movie_id):
        query = "SELECT * FROM movies WHERE movie_id = ?"
        row = self.db.fetchone(query, (movie_id,))
        return self._map_to_object(row) if row else None

    def get_all(self, limit=100, offset=0):
        query = "SELECT * FROM movies ORDER BY created_at DESC LIMIT ? OFFSET ?"
        rows = self.db.fetchall(query, (limit, offset))
        return [self._map_to_object(row) for row in rows]

    def get_by_query(self, query, params):
        """Used by strategies for custom querying"""
        rows = self.db.fetchall(query, params)
        return [self._map_to_object(row) for row in rows]

    def _map_to_object(self, row):
        return Movie(
            movie_id=row["movie_id"],
            title=row["title"],
            description=row["description"],
            duration=row["duration"],
            genre=row["genre"],
            language=row["language"],
            release_date=row["release_date"],
            rating=row["rating"],
            poster_url=row["poster_url"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
