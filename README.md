# FastAPI Backend

A modern, production-ready FastAPI boilerplate backend application.

## Features

- ✅ FastAPI with async support
- ✅ Structured project layout
- ✅ Pydantic schemas for request/response validation
- ✅ CORS middleware configuration
- ✅ Health check endpoints
- ✅ Environment-based configuration
- ✅ Type hints throughout
- ✅ Auto-generated API documentation

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # Main FastAPI application
│   ├── config.py            # Application configuration
│   ├── routers/             # API route handlers
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoints
│   │   └── api.py           # Main API endpoints
│   ├── schemas/             # Pydantic models
│   │   ├── __init__.py
│   │   └── example.py
│   └── models/              # Database models (if needed)
│       └── __init__.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Checks
- `GET /health/` - Basic health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check

### Example API
- `GET /api/v1/` - Example GET endpoint
- `POST /api/v1/example` - Example POST endpoint
- `GET /api/v1/example/{item_id}` - Get example by ID

## Development

### Running with auto-reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running in production:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Next Steps

1. Add database models in `app/models/`
2. Set up database connection in `app/config.py`
3. Add authentication/authorization if needed
4. Add more routers and schemas as your application grows
5. Set up testing with pytest
6. Configure CI/CD pipeline

## License

MIT

