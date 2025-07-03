# AI Personal Trainer Backend

FastAPI backend service for the AI Personal Trainer application.

## Development

This backend uses Poetry for dependency management.

### Setup

```bash
poetry install
poetry run pre-commit install
```

### Running

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Health Check

The backend provides a health endpoint at `/health` for Docker health checks.
