# ML Dependencies and Requirements

This document explains the dependency strategy for tRIad Terminal's machine learning features.

## Core Philosophy

tRIad Terminal follows a **graceful degradation** approach for ML dependencies:
- **Core functionality** works without heavy ML libraries
- **Enhanced features** become available when optional dependencies are installed
- **No breaking changes** when dependencies are missing

## Required Dependencies

These are included in `requirements.txt` and are **required** for basic operation:

```
fastapi>=0.111.0          # Web API framework
uvicorn[standard]>=0.30.0 # ASGI server
scikit-learn>=1.3.0       # Core ML library (lightweight)
numpy>=1.24.0             # Numerical computing
```

### Why scikit-learn is Required

While we aim to keep heavy dependencies optional, scikit-learn is included as required because:

1. **Lightweight**: Scikit-learn is relatively small compared to TensorFlow/PyTorch
2. **Stable**: Mature library with consistent API
3. **Core Features**: Enables basic ML prediction that users expect
4. **Graceful Fallbacks**: Even with sklearn, the system degrades gracefully if models fail

## Optional Dependencies

These are **NOT** included in `requirements.txt` to keep the installation lightweight:

### Heavy ML Libraries (Not Auto-Installed)

```bash
# Deep Learning (optional)
pip install tensorflow>=2.10.0
pip install torch>=1.12.0

# Gradient Boosting (optional)
pip install xgboost>=1.6.0

# Enhanced NLP (optional)
pip install transformers>=4.20.0
```

### Why These Are Optional

- **Large size**: TensorFlow alone can be 500MB+
- **Platform-specific**: May require specific system libraries
- **Advanced use cases**: Not needed for basic terminal functionality
- **Resource intensive**: May not be suitable for all deployment environments

## Installation Strategies

### Minimal Installation (Basic ML)
```bash
pip install -r requirements.txt
# Includes: fastapi, uvicorn, scikit-learn, numpy
# Provides: Basic ML predictions, API endpoints, heuristic fallbacks
```

### Enhanced Installation (Advanced ML)
```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt  # If we add this later
# Or manually install specific components:
pip install tensorflow  # For deep learning features
```

### Development Installation
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install tensorflow  # Optional for testing enhanced features
```

## Feature Availability Matrix

| Feature | No ML Deps | sklearn Only | sklearn + tensorflow |
|---------|------------|--------------|---------------------|
| Health API | ✓ | ✓ | ✓ |
| Basic predictions | ✗ | ✓ | ✓ |
| Command completion | Heuristic | ML-enhanced | ML-enhanced |
| Code completion | Heuristic | ML-enhanced | Deep learning |
| Natural Language | Basic | Enhanced | Advanced |
| Assistant training | ✗ | ✓ | ✓ |

## Runtime Behavior

### Import Strategy
```python
# Optional import pattern used throughout the codebase
try:
    import sklearn
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Feature availability check
if HAS_SKLEARN:
    # Use ML-based predictions
    pass
else:
    # Fall back to heuristic methods
    pass
```

### API Responses
- All endpoints remain functional even without optional dependencies
- Response includes `source` field indicating "ml" or "heuristic"
- Status endpoints report feature availability

### Error Handling
- Missing dependencies result in graceful fallbacks, not crashes
- Clear error messages when ML features are requested but unavailable
- Helpful hints about installing optional dependencies

## Environment Checking

Use the provided script to verify your environment:

```bash
python scripts/check_ml_env.py
```

This will report:
- Which dependencies are available
- Which features are functional
- Recommendations for missing components

## Migration from Heavy Dependencies

If you previously had a version with heavy dependencies auto-installed:

1. **Existing installations continue to work** - no breaking changes
2. **New installations are lighter** - only essential dependencies
3. **Enhanced features available on demand** - install when needed

## Best Practices

### For Users
- Start with basic installation: `pip install -r requirements.txt`
- Add optional dependencies as needed for specific features
- Use `scripts/check_ml_env.py` to verify your setup

### For Developers
- Always provide fallbacks for optional dependencies
- Use the `HAS_SKLEARN`, `HAS_TENSORFLOW` pattern for feature detection
- Test both with and without optional dependencies
- Document which features require which dependencies

### For Deployment
- **Development**: Install all optional dependencies for full feature testing
- **Production**: Install only the dependencies you need for your use case
- **CI/CD**: Test with minimal dependencies to ensure fallbacks work
- **Docker**: Use multi-stage builds to optimize image size

## Troubleshooting

### "sklearn not available" errors
```bash
pip install scikit-learn
```

### Heavy dependency conflicts
```bash
# Create a clean environment
python -m venv triad_env
source triad_env/bin/activate  # On Windows: triad_env\Scripts\activate
pip install -r requirements.txt
```

### Performance issues
- Optional dependencies can be resource-intensive
- Consider installing only the features you need
- Use `check_ml_env.py` to verify optimal configuration

## Future Considerations

As the project evolves, we may:
- Add more optional dependencies for specialized features
- Provide pre-built configurations for common use cases
- Create dependency bundles (e.g., "ml-basic", "ml-advanced")
- Support different ML backends (sklearn, tensorflow, pytorch)

The core principle remains: **essential functionality should work with minimal dependencies, enhanced functionality available on demand**.
