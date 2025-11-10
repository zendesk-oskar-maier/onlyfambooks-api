# 📚 OnlyFamBooks API

A FastAPI-based REST API that simulates a book catalogue.

## 🚀 API Endpoints

All endpoints use POST requests with JSON request bodies:

- `POST /api/v1/books` - Get all books with optional filtering
  - Request body: `{"limit": 10, "genre": "Fantasy", "title": "Harry Potter", "fuzzy": true, "threshold": 80}`
- `POST /api/v1/books/by-id` - Get a specific book by ID
  - Request body: `{"book_id": 1}`
- `POST /api/v1/genres` - Get all available genres
  - Request body: `{"limit": 100}`
- `POST /api/v1/stats` - Get catalogue statistics
  - Request body: `{}`
- `POST /health` - Health check endpoint
  - Request body: `{}`

### Request Parameters

**Books endpoint (`/api/v1/books`)**:
- `limit` (int, default: 10): Maximum number of books to return (1-1000)
- `genre` (string, optional): Filter books by genre (exact match)
- `title` (string, optional): Search books by title (supports fuzzy matching)
- `fuzzy` (bool, default: true): Enable fuzzy matching for title search
- `threshold` (int, default: 80): Minimum similarity score for fuzzy matching (0-100)

**Genres endpoint (`/api/v1/genres`)**:
- `limit` (int, default: 100): Maximum number of genres to return (1-1000)

**Book by ID endpoint (`/api/v1/books/by-id`)**:
- `book_id` (int): The unique identifier of the book

### Example Requests

**Get all books:**
```bash
curl -X POST "http://localhost:8000/api/v1/books" \
  -H "Content-Type: application/json" \
  -d "{}"
```

**Filter books by genre:**
```bash
curl -X POST "http://localhost:8000/api/v1/books" \
  -H "Content-Type: application/json" \
  -d '{"genre": "Fantasy", "limit": 5}'
```

**Search books by title:**
```bash
curl -X POST "http://localhost:8000/api/v1/books" \
  -H "Content-Type: application/json" \
  -d '{"title": "Harry Potter", "fuzzy": true, "threshold": 80}'
```

**Get a specific book:**
```bash
curl -X POST "http://localhost:8000/api/v1/books/by-id" \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1}'
```

**Get available genres:**
```bash
curl -X POST "http://localhost:8000/api/v1/genres" \
  -H "Content-Type: application/json" \
  -d '{"limit": 50}'
```

## 🛠️ Quick Start

### Install dependencies
```bash
uv sync --group dev
```

### Run the API
```bash
uv run python api.py
```
*API will be available at `http://localhost:8000` with docs at `http://localhost:8000/docs`*

### Run tests
```bash
uv run --group dev pytest tests/
```

## 🔧 Development Setup

### Install development dependencies and pre-commit hooks
```bash
# Install all dependencies including dev tools
uv sync --group dev

# Install pre-commit hooks for code quality
uv run pre-commit install
```

### Code Quality Tools
This project uses Ruff for linting and formatting with a line length of 88 characters.

**Run manually:**
```bash
# Check and fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

**Automatic on commit:**
Pre-commit hooks will automatically run Ruff on your code when you commit, ensuring consistent code style.

## 📋 Programming Principles

### 📖 Collections of Books
- Single class called `Catalogue`
- Represent each book as a Pydantic object
- Each book is represented by: `id`, `title`, `url`, `description`, `genres`
- Load whole list of books into memory on startup
- Unfold genres into lists on startup
- Provide methods to:
    - Get all books
    - Get a book by ID
    - Get books by title (fuzzy search)
    - Get books by genre
    - Get books by title and genre
    - Get all genres

### 🌐 API Design
- Uses POST endpoints with JSON request bodies
- Uses FastAPI with Pydantic models for request/response validation
- Returns meaningful error codes
- Returns meaningful error messages
- Follows consistent response structure

### ⚙️ Application
- Runs on uvicorn
- Handles errors gracefully

