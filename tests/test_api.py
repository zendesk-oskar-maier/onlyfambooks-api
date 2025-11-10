import csv
import tempfile
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api import app, validate_genre
from catalogue import Catalogue


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
def client(test_csv_file, monkeypatch):
    """Create a test client with test data"""
    # Mock the data path to use our test CSV
    monkeypatch.setattr(
        "api.Path", lambda x: Path(test_csv_file) if x == "data/books.csv" else Path(x)
    )

    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "OnlyFam Books API"


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["catalogue_loaded"] is True
    assert data["total_books"] == 3


def test_get_all_books(client):
    """Test getting all books"""
    response = client.get("/api/v1/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data["books"]) == 3
    assert data["total"] == 3
    assert data["limit"] == 10  # Updated to match current API default


def test_get_book_by_id(client):
    """Test getting a specific book by ID"""
    response = client.get("/api/v1/books/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Harry Potter and the Philosopher's Stone"
    assert "Fantasy" in data["genres"]


def test_get_book_by_id_not_found(client):
    """Test getting a non-existent book"""
    response = client.get("/api/v1/books/999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_get_books_by_genre(client):
    """Test filtering books by genre"""
    response = client.get("/api/v1/books?genre=Fantasy")
    assert response.status_code == 200
    data = response.json()
    assert len(data["books"]) == 2
    assert data["total"] == 2

    # Both should be fantasy books
    titles = [book["title"] for book in data["books"]]
    assert "Harry Potter and the Philosopher's Stone" in titles
    assert "The Hobbit" in titles


def test_get_books_by_title(client):
    """Test searching books by title"""
    response = client.get("/api/v1/books?title=Harry Potter")
    assert response.status_code == 200
    data = response.json()
    assert len(data["books"]) == 1
    assert data["books"][0]["title"] == "Harry Potter and the Philosopher's Stone"


def test_get_books_with_limit(client):
    """Test limiting the number of books returned"""
    response = client.get("/api/v1/books?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["books"]) == 2
    assert data["total"] == 3
    assert data["limit"] == 2


def test_get_genres(client):
    """Test getting all genres"""
    response = client.get("/api/v1/genres")
    assert response.status_code == 200
    data = response.json()
    assert len(data["genres"]) == 7
    assert "Fantasy" in data["genres"]
    assert "Classics" in data["genres"]


def test_post_genres_empty_body(client):
    """Test POST genres with empty body"""
    response = client.post("/api/v1/genres")
    assert response.status_code == 200
    data = response.json()
    assert len(data["genres"]) == 7
    assert data["limit"] == 100


def test_post_genres_with_limit(client):
    """Test POST genres with limit in body"""
    response = client.post("/api/v1/genres", json={"limit": 3})
    assert response.status_code == 200
    data = response.json()
    assert len(data["genres"]) == 3
    assert data["total"] == 7
    assert data["limit"] == 3


def test_post_genres_invalid_limit(client):
    """Test POST genres with invalid limit"""
    response = client.post("/api/v1/genres", json={"limit": 0})
    assert response.status_code == 400
    data = response.json()
    assert "greater than 0" in data["detail"]


def test_get_stats(client):
    """Test getting catalogue statistics"""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_books"] == 3
    assert data["total_genres"] == 7


def test_invalid_book_id(client):
    """Test invalid book ID returns 400"""
    response = client.get("/api/v1/books/0")
    assert response.status_code == 400
    data = response.json()
    assert "greater than 0" in data["detail"]


def test_invalid_limit(client):
    """Test invalid limit parameter"""
    response = client.get("/api/v1/books?limit=0")
    assert response.status_code == 422  # Validation error from Pydantic


def test_invalid_genre(client):
    """Test invalid genre returns 400 error"""
    response = client.get("/api/v1/books?genre=InvalidGenre")
    assert response.status_code == 400
    data = response.json()
    assert "Unknown genre" in data["detail"]
    assert "InvalidGenre" in data["detail"]
    assert "Available genres" in data["detail"]
    assert data.get("error_code") == "INVALID_GENRE"


def test_case_insensitive_genre(client):
    """Test genre validation is case-insensitive"""
    # Test lowercase
    response = client.get("/api/v1/books?genre=fantasy")
    assert response.status_code == 200
    data = response.json()
    assert len(data["books"]) == 2

    # Test uppercase
    response = client.get("/api/v1/books?genre=FANTASY")
    assert response.status_code == 200
    data = response.json()
    assert len(data["books"]) == 2

    # Test mixed case
    response = client.get("/api/v1/books?genre=FaNtAsY")
    assert response.status_code == 200
    data = response.json()
    assert len(data["books"]) == 2


def test_genre_validation_with_fuzzy_search(client):
    """Test that genre validation works with title fuzzy search"""
    # Valid genre with title search
    response = client.get("/api/v1/books?genre=Fantasy&title=Harry")
    assert response.status_code == 200
    data = response.json()
    assert len(data["books"]) == 1
    assert data["books"][0]["title"] == "Harry Potter and the Philosopher's Stone"

    # Invalid genre with title search should still fail
    response = client.get("/api/v1/books?genre=InvalidGenre&title=Harry")
    assert response.status_code == 400
    data = response.json()
    assert "Unknown genre" in data["detail"]


def test_genre_validation_error_message_format(client):
    """Test that genre validation error message contains all available genres"""
    response = client.get("/api/v1/books?genre=NonExistentGenre")
    assert response.status_code == 400
    data = response.json()

    # Check that all known genres are listed in the error message
    expected_genres = [
        "Fantasy",
        "Young Adult",
        "Magic",
        "Classics",
        "Fiction",
        "Historical Fiction",
        "Adventure",
    ]
    for genre in expected_genres:
        assert genre in data["detail"]


# Unit tests for utility functions


def test_validate_genre_valid(test_csv_file):
    """Test validate_genre function with valid genre"""
    catalogue = Catalogue(test_csv_file)

    # Test valid genre
    result = validate_genre("Fantasy", catalogue)
    assert result == "Fantasy"

    # Test case-insensitive validation
    result = validate_genre("fantasy", catalogue)
    assert result == "fantasy"


def test_validate_genre_invalid(test_csv_file):
    """Test validate_genre function with invalid genre"""
    catalogue = Catalogue(test_csv_file)

    with pytest.raises(HTTPException) as exc_info:
        validate_genre("InvalidGenre", catalogue)

    assert exc_info.value.status_code == 400
    assert "Unknown genre" in exc_info.value.detail
    assert "InvalidGenre" in exc_info.value.detail
    assert "Available genres" in exc_info.value.detail
    assert exc_info.value.headers["error_code"] == "INVALID_GENRE"
