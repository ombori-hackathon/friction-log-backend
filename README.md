# Friction Log Backend

Python FastAPI backend for tracking daily life friction.

## Overview

RESTful API server that manages friction items and provides analytics. Built with:
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Local database storage
- **Pydantic** - Data validation (generated from API contract)

## Architecture

This backend implements the API contract defined in `friction-log-api-contract`. All request/response schemas are generated from the OpenAPI specification to ensure type safety.

## Setup

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository with submodules:
```bash
git clone --recurse-submodules https://github.com/nytomi90/friction-log-backend.git
cd friction-log-backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

4. Generate API contract models:
```bash
cd contract
./scripts/generate_python.sh
cd ..
```

### Running the Server

```bash
uvicorn app.main:app --reload
```

Server will be available at: http://localhost:8000

API documentation: http://localhost:8000/docs

## Development

### Code Quality

This project uses:
- **black** - Code formatting
- **isort** - Import sorting
- **ruff** - Fast Python linter
- **pre-commit** - Git hooks for automatic formatting

Setup pre-commit hooks:
```bash
pre-commit install
```

Run formatters manually:
```bash
black .
isort .
ruff check .
```

### Testing

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

## API Endpoints

### Health Check
- `GET /health` - Server health status

### Friction Items
- `POST /api/friction-items` - Create friction item
- `GET /api/friction-items` - List all items (with filters)
- `GET /api/friction-items/{id}` - Get single item
- `PUT /api/friction-items/{id}` - Update item
- `DELETE /api/friction-items/{id}` - Delete item

### Analytics
- `GET /api/analytics/score` - Current friction score
- `GET /api/analytics/trend` - Historical trend data
- `GET /api/analytics/by-category` - Category breakdown

See full API documentation at `/docs` when server is running.

## Project Structure

```
friction-log-backend/
├── contract/              # Git submodule (API contract)
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── models.py         # SQLAlchemy models
│   ├── database.py       # Database setup
│   ├── crud.py           # CRUD operations
│   └── analytics.py      # Analytics calculations
├── tests/                # Test suite
├── requirements.txt      # Production dependencies
└── requirements-dev.txt  # Development dependencies
```

## Updating API Contract

When the API contract is updated:

1. Update submodule:
```bash
cd contract
git checkout main
git pull
cd ..
git add contract
```

2. Regenerate models:
```bash
cd contract
./scripts/generate_python.sh
cd ..
```

3. Update implementation to match new contract
4. Run tests to verify
5. Commit changes

## License

MIT
