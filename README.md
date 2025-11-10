# 📚 OnlyFamBooks API

A FastAPI-based REST API that simulates a book catalogue.

## 🚀 API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /api/v1/books` - Get books with optional filtering and pagination
  - `GET /api/v1/books?title=harry` - Search books by title
  - `GET /api/v1/books?genre=fantasy` - Filter books by genre
  - `GET /api/v1/books?title=harry&genre=fantasy` - Search by both title and genre
- `GET /api/v1/books/{id}` - Get a specific book by ID
- `GET /api/v1/genres` - Get all available genres
- `POST /api/v1/genres` - Get all available genres via POST
- `GET /api/v1/stats` - Get catalogue statistics

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
- Follows REST principles
- Uses FastAPI
- Returns meaningful error codes
- Returns meaningful error messages

### ⚙️ Application
- Runs on uvicorn
- Handles errors gracefully

