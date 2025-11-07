import ast
import csv
from pathlib import Path

from pydantic import BaseModel, Field
from thefuzz import fuzz


class Book(BaseModel):
    """Pydantic model representing a book"""

    id: int = Field(..., description="Unique identifier for the book")
    title: str = Field(..., description="Title of the book")
    url: str = Field(..., description="URL to the book's page")
    description: str = Field(..., description="Description of the book")
    genres: list[str] = Field(
        default_factory=list, description="List of genres for the book"
    )


class Catalogue:
    """
    A collection of books loaded from CSV data.
    Provides methods to search and filter books by various criteria.
    """

    def __init__(self, csv_path: str | Path = "data/books.csv"):
        """
        Initialize the catalogue by loading books from CSV file.

        Args:
            csv_path: Path to the CSV file containing book data
        """
        self.books: list[Book] = []
        self._all_genres: set[str] = set()
        self._load_books(csv_path)

    def _load_books(self, csv_path: str | Path) -> None:
        """
        Load books from CSV file into memory.

        Args:
            csv_path: Path to the CSV file
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Parse genres from string representation of list
                genres = self._parse_genres(row["genres"])

                book = Book(
                    id=int(row["id"]),
                    title=row["title"],
                    url=row["url"],
                    description=row["description"],
                    genres=genres,
                )

                self.books.append(book)
                self._all_genres.update(genres)

    def _parse_genres(self, genres_str: str) -> list[str]:
        """
        Parse genres from string representation of list.

        Args:
            genres_str: String representation of genres list

        Returns:
            List of genre strings
        """
        try:
            # Use ast.literal_eval to safely parse the string representation
            return ast.literal_eval(genres_str)
        except (ValueError, SyntaxError):
            # Fallback: return empty list if parsing fails
            return []

    def get_all_books(self) -> list[Book]:
        """
        Get all books in the catalogue.

        Returns:
            List of all books
        """
        return self.books.copy()

    def get_book_by_id(self, book_id: int) -> Book | None:
        """
        Get a specific book by its ID.

        Args:
            book_id: The ID of the book to retrieve

        Returns:
            Book object if found, None otherwise
        """
        for book in self.books:
            if book.id == book_id:
                return book
        return None

    def get_books_by_title(
        self, title: str, fuzzy: bool = True, threshold: int = 80
    ) -> list[Book]:
        """
        Get books by title using fuzzy or exact matching.

        Args:
            title: Title to search for
            fuzzy: Whether to use fuzzy matching (default: True)
            threshold: Minimum similarity score for fuzzy matching (default: 80)

        Returns:
            List of matching books, sorted by relevance if using fuzzy search
        """
        if not fuzzy:
            # Exact match (case-insensitive)
            return [book for book in self.books if title.lower() in book.title.lower()]

        # Fuzzy matching
        matches = []
        for book in self.books:
            ratio = fuzz.ratio(title.lower(), book.title.lower())
            partial_ratio = fuzz.partial_ratio(title.lower(), book.title.lower())

            # Use the higher of the two ratios
            score = max(ratio, partial_ratio)

            if score >= threshold:
                matches.append((book, score))

        # Sort by score (descending) and return books
        matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in matches]

    def get_books_by_genre(self, genre: str, exact_match: bool = True) -> list[Book]:
        """
        Get books by genre.

        Args:
            genre: Genre to search for
            exact_match: Whether to use exact matching (default: True)

        Returns:
            List of books in the specified genre
        """
        matching_books = []

        for book in self.books:
            if exact_match:
                # Case-insensitive exact match
                if any(g.lower() == genre.lower() for g in book.genres):
                    matching_books.append(book)
            else:
                # Partial match (case-insensitive)
                if any(genre.lower() in g.lower() for g in book.genres):
                    matching_books.append(book)

        return matching_books

    def get_books_by_title_and_genre(
        self,
        title: str = "",
        genre: str = "",
        fuzzy_title: bool = True,
        title_threshold: int = 80,
        exact_genre_match: bool = True,
    ) -> list[Book]:
        """
        Get books by both title and genre criteria.

        Args:
            title: Title to search for (optional)
            genre: Genre to filter by (optional)
            fuzzy_title: Whether to use fuzzy matching for title
            title_threshold: Minimum similarity score for fuzzy title matching
            exact_genre_match: Whether to use exact matching for genre

        Returns:
            List of books matching both criteria
        """
        # Start with all books
        candidates = self.books

        # Filter by title if provided
        if title:
            if fuzzy_title:
                title_matches = []
                for book in candidates:
                    ratio = fuzz.ratio(title.lower(), book.title.lower())
                    partial_ratio = fuzz.partial_ratio(
                        title.lower(), book.title.lower()
                    )
                    score = max(ratio, partial_ratio)

                    if score >= title_threshold:
                        title_matches.append(book)
                candidates = title_matches
            else:
                candidates = [
                    book for book in candidates if title.lower() in book.title.lower()
                ]

        # Filter by genre if provided
        if genre:
            if exact_genre_match:
                candidates = [
                    book
                    for book in candidates
                    if any(g.lower() == genre.lower() for g in book.genres)
                ]
            else:
                candidates = [
                    book
                    for book in candidates
                    if any(genre.lower() in g.lower() for g in book.genres)
                ]

        return candidates

    def get_all_genres(self) -> list[str]:
        """
        Get all unique genres in the catalogue.

        Returns:
            Sorted list of all genres
        """
        return sorted(list(self._all_genres))

    def get_stats(self) -> dict:
        """
        Get basic statistics about the catalogue.

        Returns:
            Dictionary containing catalogue statistics
        """
        return {
            "total_books": len(self.books),
            "total_genres": len(self._all_genres),
            "genres": self.get_all_genres(),
        }

    def __len__(self) -> int:
        """Return the number of books in the catalogue."""
        return len(self.books)

    def __repr__(self) -> str:
        """Return string representation of the catalogue."""
        return f"Catalogue({len(self.books)} books, {len(self._all_genres)} genres)"
