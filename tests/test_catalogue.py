import csv
import tempfile
from pathlib import Path

import pytest

from catalogue import Book, Catalogue


@pytest.fixture
def test_csv_file():
    """Create a temporary CSV file with test data"""
    test_data = [
        {
            "id": "1",
            "title": "Harry Potter and the Philosopher's Stone",
            "url": "https://example.com/book1",
            "description": "A young wizard discovers his magical heritage.",
            "genres": "['Fantasy', 'Young Adult', 'Magic']",
        },
        {
            "id": "2",
            "title": "To Kill a Mockingbird",
            "url": "https://example.com/book2",
            "description": "A classic novel about justice and morality.",
            "genres": "['Classics', 'Fiction', 'Historical Fiction']",
        },
        {
            "id": "3",
            "title": "The Hobbit",
            "url": "https://example.com/book3",
            "description": "An unexpected journey of a hobbit.",
            "genres": "['Fantasy', 'Adventure', 'Classics']",
        },
    ]

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "title", "url", "description", "genres"]
        )
        writer.writeheader()
        writer.writerows(test_data)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def catalogue(test_csv_file):
    """Create a Catalogue instance with test data"""
    return Catalogue(test_csv_file)


def test_catalogue_initialization(catalogue):
    """Test that catalogue initializes correctly"""
    assert len(catalogue) == 3
    assert (
        len(catalogue.get_all_genres()) == 7
    )  # Fantasy, Young Adult, Magic, Classics, Fiction, Historical Fiction, Adventure


def test_get_all_books(catalogue):
    """Test getting all books"""
    books = catalogue.get_all_books()
    assert len(books) == 3
    assert all(isinstance(book, Book) for book in books)


def test_get_book_by_id(catalogue):
    """Test getting book by ID"""
    book = catalogue.get_book_by_id(1)
    assert book is not None
    assert book.title == "Harry Potter and the Philosopher's Stone"
    assert book.id == 1

    # Test non-existent ID
    assert catalogue.get_book_by_id(999) is None


def test_get_books_by_title_exact(catalogue):
    """Test exact title search"""
    books = catalogue.get_books_by_title("Harry Potter", fuzzy=False)
    assert len(books) == 1
    assert books[0].title == "Harry Potter and the Philosopher's Stone"


def test_get_books_by_title_fuzzy(catalogue):
    """Test fuzzy title search"""
    books = catalogue.get_books_by_title("Harry Potter", fuzzy=True)
    assert len(books) == 1
    assert books[0].title == "Harry Potter and the Philosopher's Stone"

    # Test partial match with lower threshold
    books = catalogue.get_books_by_title("Hobbit", fuzzy=True, threshold=50)
    assert len(books) == 1
    assert books[0].title == "The Hobbit"


def test_get_books_by_genre(catalogue):
    """Test getting books by genre"""
    fantasy_books = catalogue.get_books_by_genre("Fantasy")
    assert len(fantasy_books) == 2

    classics_books = catalogue.get_books_by_genre("Classics")
    assert len(classics_books) == 2

    # Test non-existent genre
    assert len(catalogue.get_books_by_genre("Science Fiction")) == 0


def test_get_books_by_title_and_genre(catalogue):
    """Test combined title and genre search"""
    books = catalogue.get_books_by_title_and_genre(title="Harry", genre="Fantasy")
    assert len(books) == 1
    assert books[0].title == "Harry Potter and the Philosopher's Stone"

    books = catalogue.get_books_by_title_and_genre(genre="Classics")
    assert len(books) == 2


def test_get_all_genres(catalogue):
    """Test getting all genres"""
    genres = catalogue.get_all_genres()
    expected_genres = [
        "Adventure",
        "Classics",
        "Fantasy",
        "Fiction",
        "Historical Fiction",
        "Magic",
        "Young Adult",
    ]
    assert genres == expected_genres


def test_get_stats(catalogue):
    """Test getting catalogue statistics"""
    stats = catalogue.get_stats()
    assert stats["total_books"] == 3
    assert stats["total_genres"] == 7
    assert isinstance(stats["genres"], list)


def test_catalogue_repr(catalogue):
    """Test string representation"""
    repr_str = repr(catalogue)
    assert "Catalogue(3 books, 7 genres)" == repr_str
