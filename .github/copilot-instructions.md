# tRIad Terminal Development Instructions

**ALWAYS follow these instructions first** and only fall back to additional search and context gathering if the information here is incomplete or found to be in error.

tRIad Terminal is a Python-first extensible terminal environment with:
- FastAPI-based web API with ML endpoints
- Git repository management with GitHub integration  
- Voice assistant and AI integration capabilities
- Security/authentication system with optional biometrics
- Theme/UI utilities and development installers

## Quick Start (5 minutes)

Bootstrap the development environment:

```bash
# Install core dependencies - takes 60-90 seconds, NEVER CANCEL
python -m pip install -r requirements.txt

# Install development tools - takes 60-90 seconds, NEVER CANCEL  
make install

# Validate environment - completes in 10-15 seconds
python scripts/check_ml_env.py
```

**Expected output**: Core ML components working, API functionality verified.

## Working Entry Points

**CRITICAL**: Many entry points have syntax errors. Use only these validated entry points:

### API Server (Primary Working Entry Point)
```bash
# Start development API server - starts in <5 seconds
python scripts/run_api.py

# API available at: http://127.0.0.1:8000
# API docs at: http://127.0.0.1:8000/docs  
# Interactive docs at: http://127.0.0.1:8000/redoc
```

### Alternative API Start Methods
```bash
# Direct API start
python start_api.py

# Using app module directly  
python app.py
```

### Environment Validation
```bash
# Check ML environment status - completes in 5-10 seconds
python scripts/check_ml_env.py

# Expected: Core dependencies OK, some optional dependencies may be missing
```

## Broken Entry Points - DO NOT USE

**WARNING**: These entry points have syntax errors and will fail:

- `python triad-terminal.py` - file appears corrupted/incomplete
- `python optimized_terminal.py` - syntax errors at line 545
- `python integrated_terminal_Version2.py` - invalid syntax at line 8  
- `python secure_terminal_Version2.py` - missing security_system module

Use the API server entry points above instead.

## Development Workflow

### 1. Setup Development Environment
```bash
# Use the provided dev setup script - takes 15-20 seconds
./scripts/dev-setup.sh

# Manually setup virtual environment if needed
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
```

### 2. Install Dependencies with Timing
```bash
# Core dependencies - NEVER CANCEL, takes 60-90 seconds  
python -m pip install -r requirements.txt

# Development dependencies - NEVER CANCEL, takes 60-90 seconds
make install

# Test dependencies (for API testing)
python -m pip install httpx
```

### 3. Validation and Testing

**NEVER CANCEL test commands - they complete quickly but validation is critical**

```bash
# Run smoke tests - completes in 2-5 seconds
python -m pytest tests/test_smoke.py -v

# Run integration tests - completes in 10-15 seconds  
python -m pytest tests/test_integration.py tests/test_ml_import.py -v

# Expected: 13/15 tests pass (2 failures due to file corruption issues)
```

### 4. Development Server Testing

**CRITICAL VALIDATION**: Always test the API server after changes:

```bash
# Start API server - NEVER CANCEL, starts in <5 seconds
python scripts/run_api.py

# In another terminal, test API health
curl http://127.0.0.1:8000/health
# Expected: {"status": "healthy", "timestamp": "..."}

# Test ML status endpoint  
curl http://127.0.0.1:8000/ml/status
# Expected: {"status": "ready", "models": [...]}

# Stop server with Ctrl+C
```

### 5. Code Quality (Optional - Has Known Issues)

```bash
# Linting - NEVER CANCEL, takes 30-60 seconds but will show many violations
make lint

# Expected: Many style violations exist in current codebase
# Focus only on new code you add, not existing violations

# Formatting (use with caution)
make fmt
```

## Common Development Tasks

### Adding New API Endpoints
1. Edit files in `api/routers/` directory
2. Import new router in `api/main.py`  
3. **ALWAYS test immediately**: `python scripts/run_api.py`
4. **ALWAYS validate**: `curl http://127.0.0.1:8000/docs`

### Working with ML Components
1. Core ML functionality uses scikit-learn (included in requirements.txt)
2. Optional heavy dependencies (TensorFlow, PyTorch) not installed by default
3. **ALWAYS test ML changes**: `python scripts/check_ml_env.py`

### Repository Management
```bash
# Use the working repo manager  
python repo_manager_Version2.py --help

# Common commands:
python repo_manager_Version2.py list
python repo_manager_Version2.py status <name>
```

## Build and Test Timing

**CRITICAL**: Set appropriate timeouts for these operations:

| Operation | Expected Time | Timeout Setting |
|-----------|---------------|-----------------|
| `pip install -r requirements.txt` | 60-90 seconds | 120+ seconds |
| `make install` | 60-90 seconds | 120+ seconds |  
| `python scripts/run_api.py` | <5 seconds | 30 seconds |
| `pytest tests/test_smoke.py` | 2-5 seconds | 30 seconds |
| `pytest tests/test_integration.py` | 10-15 seconds | 60 seconds |
| `python scripts/check_ml_env.py` | 5-10 seconds | 30 seconds |
| `make lint` | 30-60 seconds | 120 seconds |

**NEVER CANCEL builds or long-running commands** - they will complete within expected times.

## Manual Validation Scenarios

After making changes, **ALWAYS** run these validation scenarios:

### API Functionality Test
```bash
# 1. Start API server
python scripts/run_api.py

# 2. Test health endpoint (in new terminal)
curl http://127.0.0.1:8000/health

# 3. Test ML status
curl http://127.0.0.1:8000/ml/status  

# 4. Browse API docs
# Open http://127.0.0.1:8000/docs in browser

# Expected: All endpoints respond, documentation loads
```

### ML Environment Test
```bash
# Run environment check
python scripts/check_ml_env.py

# Expected output:
# ✓ Core Dependencies: 5/5 available
# ✓ ML Predictor: OK  
# ✓ Assistant importable: OK
# Some optional dependencies may show FAIL (expected)
```

### Basic Import Test
```bash
# Test critical imports work
python -c "import app; print('App imports successfully')"
python -c "from api.main import app; print('FastAPI app imports')"  
python -c "from ml.predictor import MLPredictor; print('ML predictor imports')"

# All should complete without errors
```

## Repository Structure

Key directories and their purposes:

```
.
├── .github/workflows/      # CI pipelines (runs tests on PRs)
├── api/                    # FastAPI application code  
├── agents/                 # AI agent implementations
├── docs/                   # Documentation
├── ml/                     # Machine learning components  
├── scripts/                # Development and utility scripts
├── tests/                  # Test suite (partial functionality)
├── utils/                  # Utility functions
├── requirements.txt        # Core Python dependencies
├── requirements-dev.txt    # Development dependencies  
├── pyproject.toml         # Build configuration (ruff, black, mypy)
├── Makefile               # Development commands
└── README.md              # Project overview
```

## Dependencies and Installation

### Required Dependencies (Always Install)
```bash
pip install -r requirements.txt
```
Contains:
- fastapi>=0.111.0 (web framework)
- uvicorn[standard]>=0.30.0 (ASGI server) 
- scikit-learn>=1.3.0 (core ML - lightweight)
- numpy>=1.24.0 (numerical computing)
- pyttsx3>=2.90 (text-to-speech)
- Additional voice/audio libraries

### Development Dependencies
```bash
make install
```
Installs: pytest, pre-commit, black, isort, flake8, and related tools.

### Optional Heavy Dependencies (Not Auto-Installed)
```bash
# Only install if needed for advanced features
pip install tensorflow>=2.10.0    # Deep learning (500MB+)
pip install torch>=1.12.0         # PyTorch alternative  
pip install xgboost>=1.6.0        # Gradient boosting
```

## CI/CD Integration

The repository has GitHub Actions that run on push/PR:

```bash
# CI runs these commands:
python -m pip install -U pip
python -m pip install -U pytest  
pytest -q || true  # Currently allows test failures
```

**Before pushing changes, always run**:
```bash
# Test what CI will test - takes 10-15 seconds
python -m pytest tests/test_smoke.py tests/test_integration.py

# Validate your changes don't break API
python scripts/run_api.py  # Start server, test endpoints, stop with Ctrl+C
```

## Troubleshooting

### "sklearn not available" errors
```bash
pip install scikit-learn
```

### "httpx not available" during testing
```bash  
pip install httpx
```

### API server won't start
```bash
# Check if dependencies are installed
python scripts/check_ml_env.py

# Verify core imports work
python -c "import fastapi, uvicorn; print('OK')"
```

### Performance issues
```bash
# Enable performance logging
export TRIAD_PERF=1

# Run with timing
time python scripts/run_api.py --help
```

## Security Considerations

- Never commit API keys or secrets to version control
- Use environment variables for configuration: `.env` files supported
- The security system modules have known issues - validate any auth changes thoroughly

## Performance Notes

- API server starts quickly (<5 seconds) and handles requests efficiently
- ML predictions use lightweight scikit-learn models by default
- Heavy ML dependencies (TensorFlow/PyTorch) are optional to keep installation fast
- Use caching for expensive operations (examples in `optimized_terminal.py`)

## When Instructions Are Incomplete

If these instructions don't cover your use case:
1. Check the `docs/` directory for additional documentation
2. Search for examples in the working test files (`tests/test_integration.py`)
3. Examine the API code in `api/` for patterns and endpoints
4. Use `python scripts/check_ml_env.py` to understand current environment state

Remember: **Focus on the API server functionality as the primary working interface** to the tRIad Terminal system.