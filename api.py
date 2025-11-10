import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from catalogue import Book, Catalogue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global catalogue instance
catalogue: Catalogue | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    global catalogue
    try:
        catalogue_path = Path("data/books.csv")
        if not catalogue_path.exists():
            logger.error(f"Books data file not found: {catalogue_path}")
            raise FileNotFoundError(f"Books data file not found: {catalogue_path}")

        catalogue = Catalogue(catalogue_path)
        logger.info(f"Catalogue initialized with {len(catalogue)} books")
    except Exception as e:
        logger.error(f"Failed to initialize catalogue: {e}")
        raise e

    yield

    # Shutdown (cleanup if needed)
    logger.info("Shutting down API")


# FastAPI app instance with lifespan
app = FastAPI(
    title="OnlyFam Books API",
    description="A REST API for browsing and searching a book catalogue",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Request models
class GetBooksRequest(BaseModel):
    """Request model for getting books"""

    limit: int = 10
    genre: str | None = None
    title: str | None = None
    fuzzy: bool = True
    threshold: int = 80


class GetBookByIdRequest(BaseModel):
    """Request model for getting a book by ID"""

    book_id: int


class GetGenresRequest(BaseModel):
    """Request model for getting genres"""

    limit: int = 100


# Response models
class BookResponse(BaseModel):
    """Response model for book data"""

    id: int
    title: str
    url: str
    description: str
    genres: list[str]


class BooksListResponse(BaseModel):
    """Response model for list of books"""

    books: list[BookResponse]
    total: int
    limit: int
    page: int = 1


class GenresResponse(BaseModel):
    """Response model for genres list"""

    genres: list[str]
    total: int
    limit: int


class ErrorResponse(BaseModel):
    """Response model for errors"""

    detail: str
    error_code: str


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTPException handler to include error_code in response body"""
    content = {"detail": exc.detail}
    if exc.headers and "error_code" in exc.headers:
        content["error_code"] = exc.headers["error_code"]
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found", "error_code": "NOT_FOUND"},
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


# Utility functions
def convert_book_to_response(book: Book) -> BookResponse:
    """Convert Book model to BookResponse"""
    return BookResponse(
        id=book.id,
        title=book.title,
        url=book.url,
        description=book.description,
        genres=book.genres,
    )


def validate_limit(limit: int) -> int:
    """Validate and normalize limit parameter"""
    if limit < 1:
        raise HTTPException(
            status_code=400,
            detail="Limit must be greater than 0",
            headers={"error_code": "INVALID_LIMIT"},
        )
    if limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="Limit cannot exceed 1000",
            headers={"error_code": "LIMIT_TOO_HIGH"},
        )
    return limit


def validate_genre(genre: str, catalogue: Catalogue) -> str:
    """Validate genre parameter against available genres"""
    available_genres = catalogue.get_all_genres()
    # Case-insensitive genre validation
    if not any(g.lower() == genre.lower() for g in available_genres):
        genre_list = ", ".join(available_genres)
        raise HTTPException(
            status_code=400,
            detail=f"Unknown genre: '{genre}'. Available genres: {genre_list}",
            headers={"error_code": "INVALID_GENRE"},
        )
    return genre


# API Routes


@app.post("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "OnlyFam Books API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {"books": "/api/v1/books", "genres": "/api/v1/genres"},
    }


@app.post("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    global catalogue
    if catalogue is None:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable - catalogue not initialized",
            headers={"error_code": "SERVICE_UNAVAILABLE"},
        )

    return {
        "status": "healthy",
        "catalogue_loaded": True,
        "total_books": len(catalogue),
        "total_genres": len(catalogue.get_all_genres()),
    }


@app.post("/api/v1/books", response_model=BooksListResponse, tags=["Books"])
async def get_books(request: GetBooksRequest):
    """
    Get books with optional filtering by genre and/or title.

    - **limit**: Maximum number of books to return (1-1000)
    - **genre**: Filter books by genre (exact match)
    - **title**: Search books by title (supports fuzzy matching)
    - **fuzzy**: Enable fuzzy matching for title search
    - **threshold**: Minimum similarity score for fuzzy matching (0-100)
    """
    global catalogue
    if catalogue is None:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable - catalogue not initialized",
            headers={"error_code": "SERVICE_UNAVAILABLE"},
        )

    try:
        limit = validate_limit(request.limit)

        # Validate genre if provided
        if request.genre:
            genre = validate_genre(request.genre, catalogue)
        else:
            genre = request.genre

        # Apply filters based on query parameters
        if request.title and genre:
            # Both title and genre filters
            books = catalogue.get_books_by_title_and_genre(
                title=request.title,
                genre=genre,
                fuzzy_title=request.fuzzy,
                title_threshold=request.threshold,
            )
        elif request.title:
            # Title filter only
            books = catalogue.get_books_by_title(
                request.title, fuzzy=request.fuzzy, threshold=request.threshold
            )
        elif genre:
            # Genre filter only
            books = catalogue.get_books_by_genre(genre)
        else:
            # No filters - get all books
            books = catalogue.get_all_books()

        # Apply limit
        total_books = len(books)
        limited_books = books[:limit]

        # Convert to response format
        book_responses = [convert_book_to_response(book) for book in limited_books]

        return BooksListResponse(books=book_responses, total=total_books, limit=limit)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_books: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve books",
            headers={"error_code": "RETRIEVAL_ERROR"},
        ) from e


@app.post("/api/v1/books/by-id", response_model=BookResponse, tags=["Books"])
async def get_book_by_id(request: GetBookByIdRequest):
    """
    Get a specific book by its ID.

    - **book_id**: The unique identifier of the book
    """
    global catalogue
    if catalogue is None:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable - catalogue not initialized",
            headers={"error_code": "SERVICE_UNAVAILABLE"},
        )

    if request.book_id < 1:
        raise HTTPException(
            status_code=400,
            detail="Book ID must be greater than 0",
            headers={"error_code": "INVALID_BOOK_ID"},
        )

    try:
        book = catalogue.get_book_by_id(request.book_id)
        if book is None:
            raise HTTPException(
                status_code=404,
                detail=f"Book with ID {request.book_id} not found",
                headers={"error_code": "BOOK_NOT_FOUND"},
            )

        return convert_book_to_response(book)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_book_by_id: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve book",
            headers={"error_code": "RETRIEVAL_ERROR"},
        ) from e


@app.post("/api/v1/genres", response_model=GenresResponse, tags=["Genres"])
async def get_genres(request: GetGenresRequest):
    """
    Get all available genres.

    - **limit**: Maximum number of genres to return (1-1000)
    """
    global catalogue
    if catalogue is None:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable - catalogue not initialized",
            headers={"error_code": "SERVICE_UNAVAILABLE"},
        )

    try:
        limit = validate_limit(request.limit)

        all_genres = catalogue.get_all_genres()
        total_genres = len(all_genres)
        limited_genres = all_genres[:limit]

        return GenresResponse(genres=limited_genres, total=total_genres, limit=limit)

    except Exception as e:
        logger.error(f"Error in get_genres: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve genres",
            headers={"error_code": "RETRIEVAL_ERROR"},
        ) from e


# Additional utility endpoints


@app.post("/api/v1/stats", tags=["Stats"])
async def get_catalogue_stats():
    """Get catalogue statistics"""
    global catalogue
    if catalogue is None:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable - catalogue not initialized",
            headers={"error_code": "SERVICE_UNAVAILABLE"},
        )

    try:
        return catalogue.get_stats()
    except Exception as e:
        logger.error(f"Error in get_catalogue_stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve statistics",
            headers={"error_code": "STATS_ERROR"},
        ) from e


# Run the application
if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
