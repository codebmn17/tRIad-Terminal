# Production API Structure

This document describes the new production-ready API structure for tRIad Terminal.

## Directory Structure

```
tRIad-Terminal/
├── api/                    # FastAPI application
│   ├── __init__.py
│   ├── main.py            # Main FastAPI app
│   └── routers/           # API route modules
│       ├── __init__.py
│       ├── health.py      # Health check endpoints
│       └── ml_router.py   # ML prediction endpoints
│
├── ml/                     # Machine Learning utilities
│   ├── __init__.py
│   └── predictor.py       # ML prediction logic
│
├── models/                 # Trained model artifacts
│   ├── .gitkeep
│   ├── __init__.py        # For backward compatibility
│   ├── iris_knn.joblib
│   └── unstoppable_iris_model.pkl
│
├── scripts/               # Utility scripts
│   ├── run_api.py         # Python API runner
│   └── start_api.sh       # Shell script API runner
│
└── tests/                 # Test suite
    ├── test_api.py        # Comprehensive API tests
    ├── test_integration.py # Simple integration tests
    └── test_smoke.py      # Existing smoke tests
```

## API Endpoints

### Health Endpoints
- `GET /health` - Health check with timestamp and service info
- `GET /` - Root endpoint with API information

### Machine Learning Endpoints
- `POST /ml/predict` - Make ML predictions
- `GET /ml/models` - List available models

### Documentation
- `GET /docs` - Interactive Swagger/OpenAPI documentation
- `GET /redoc` - Alternative ReDoc documentation

## Running the API

### Using Python Script
```bash
python scripts/run_api.py
```

### Using Shell Script
```bash
./scripts/start_api.sh
```

### Direct Uvicorn
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

## Testing

### Quick Integration Test
```bash
python tests/test_integration.py
```

### Comprehensive Tests (requires pytest)
```bash
pytest tests/test_api.py -v
```

## Backward Compatibility

The new structure maintains full backward compatibility:

- The original `app.py` continues to work
- The `models` module still exports `predict_knn` and `predict_forest`
- All existing functionality is preserved
- No breaking changes to existing code

## Features

- ✅ Production-ready FastAPI structure
- ✅ Health check endpoints
- ✅ ML prediction endpoints with multiple models
- ✅ Comprehensive error handling
- ✅ Input validation with Pydantic
- ✅ Interactive API documentation
- ✅ CORS support for browser testing
- ✅ Backward compatibility with existing code
- ✅ Comprehensive test suite
- ✅ Easy deployment scripts