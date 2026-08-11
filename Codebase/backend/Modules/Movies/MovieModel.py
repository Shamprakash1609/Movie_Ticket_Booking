class Movie:
    def __init__(
        self,
        movie_id,
        title,
        description,
        duration,
        genre,
        language,
        release_date,
        rating,
        poster_url,
        created_by,
        created_at=None,
        updated_at=None,
    ):
        self.movie_id = movie_id
        self.title = title
        self.description = description
        self.duration = duration
        self.genre = genre
        self.language = language
        self.release_date = release_date
        self.rating = rating
        self.poster_url = poster_url
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at
