# Friction Log Backend

![CI](https://github.com/nytomi90/friction-log-backend/actions/workflows/ci.yml/badge.svg)

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

### Example Requests

**Create a friction item**:
```bash
curl -X POST http://localhost:8000/api/friction-items \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Slow WiFi",
    "description": "Internet drops during video calls",
    "annoyance_level": 4,
    "category": "digital"
  }'
```

**Get current score**:
```bash
curl http://localhost:8000/api/analytics/score
```

**Filter items by status**:
```bash
curl "http://localhost:8000/api/friction-items?status=not_fixed"
```

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

## Database Schema

**Table: `friction_items`**

| Column         | Type     | Description                      |
|----------------|----------|----------------------------------|
| id             | INTEGER  | Primary key, auto-increment      |
| title          | TEXT     | Short description of friction    |
| description    | TEXT     | Optional detailed description    |
| annoyance_level| INTEGER  | Severity rating (1-5)            |
| category       | TEXT     | Enum: home/work/digital/health/other |
| status         | TEXT     | Enum: not_fixed/in_progress/fixed |
| created_at     | DATETIME | Timestamp (UTC)                  |
| updated_at     | DATETIME | Last modified timestamp (UTC)    |
| fixed_at       | DATETIME | Timestamp when marked as fixed   |

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
