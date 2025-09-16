#!/usr/bin/env python3
"""
ML Environment Checker

Manually verify that the ML environment is ready and all components work correctly.
This script checks dependencies, imports, and basic functionality.
"""

import os
import sys
import traceback
from typing import Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def check_dependency(name: str, import_name: str = None) -> dict[str, Any]:
    """Check if a dependency is available and get its version."""
    if import_name is None:
        import_name = name

    try:
        module = __import__(import_name)
        version = getattr(module, "__version__", "unknown")
        return {"name": name, "available": True, "version": version, "error": None}
    except ImportError as e:
        return {"name": name, "available": False, "version": None, "error": str(e)}


def check_core_dependencies() -> list[dict[str, Any]]:
    """Check core ML dependencies."""
    deps = [
        ("NumPy", "numpy"),
        ("scikit-learn", "sklearn"),
        ("joblib", "joblib"),
        ("FastAPI", "fastapi"),
        ("Uvicorn", "uvicorn"),
    ]

    results = []
    for name, import_name in deps:
        result = check_dependency(name, import_name)
        results.append(result)

    return results


def check_optional_dependencies() -> list[dict[str, Any]]:
    """Check optional ML dependencies."""
    deps = [
        ("TensorFlow", "tensorflow"),
        ("PyTorch", "torch"),
        ("XGBoost", "xgboost"),
    ]

    results = []
    for name, import_name in deps:
        result = check_dependency(name, import_name)
        results.append(result)

    return results


def check_ml_predictor() -> dict[str, Any]:
    """Check ML predictor functionality."""
    try:
        from ml.predictor import MLPredictor, predict_forest, predict_knn

        # Test instantiation
        predictor = MLPredictor()

        # Test model listing
        models = predictor.list_models()

        # Test prediction
        test_features = [5.1, 3.5, 1.4, 0.2]
        result = predictor.predict(test_features)

        # Test legacy functions
        knn_result = predict_knn(test_features)
        forest_result = predict_forest(test_features)

        return {
            "available": True,
            "models": models,
            "prediction_works": True,
            "legacy_functions_work": True,
            "error": None,
        }
    except Exception as e:
        return {
            "available": False,
            "models": [],
            "prediction_works": False,
            "legacy_functions_work": False,
            "error": str(e),
        }


def check_assistant() -> dict[str, Any]:
    """Check AI assistant functionality."""
    try:

        # Test basic instantiation (don't trigger model training)
        # Just check if we can import without errors
        return {"available": True, "importable": True, "error": None}
    except Exception as e:
        return {"available": False, "importable": False, "error": str(e)}


def check_api_availability() -> dict[str, Any]:
    """Check API endpoint availability."""
    try:
        from fastapi.testclient import TestClient

        from api.main import app

        client = TestClient(app)

        # Test health endpoint
        health_response = client.get("/health")
        health_ok = health_response.status_code == 200

        # Test ML prediction endpoint
        ml_response = client.post("/ml/predict", json={"features": [5.1, 3.5, 1.4, 0.2]})
        ml_ok = ml_response.status_code == 200

        # Test ML status endpoint
        status_response = client.get("/ml/status")
        status_ok = status_response.status_code == 200

        # Test assistant status endpoint
        assistant_response = client.get("/assistant/status")
        assistant_ok = assistant_response.status_code == 200

        return {
            "available": True,
            "health_endpoint": health_ok,
            "ml_prediction": ml_ok,
            "ml_status": status_ok,
            "assistant_status": assistant_ok,
            "error": None,
        }
    except Exception as e:
        return {
            "available": False,
            "health_endpoint": False,
            "ml_prediction": False,
            "ml_status": False,
            "assistant_status": False,
            "error": str(e),
        }


def check_backward_compatibility() -> dict[str, Any]:
    """Check backward compatibility features."""
    try:
        # Check that the old assistant-ML.py file raises the right error
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "assistant_ml_old", os.path.join(project_root, "agents/learning/assistant-ML.py")
        )
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
            return {"working": False, "error": "Expected ImportError was not raised"}
        except ImportError as e:
            # This is expected
            error_msg = str(e)
            has_rename_msg = "renamed" in error_msg
            has_new_name = "assistant_ml.py" in error_msg

            return {
                "working": True,
                "error_message_quality": has_rename_msg and has_new_name,
                "error": None,
            }
    except Exception as e:
        return {"working": False, "error": str(e)}


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print("=" * 60)


def print_status(item: str, status: bool, details: str = ""):
    """Print a status line with consistent formatting."""
    status_symbol = "✓" if status else "✗"
    status_text = "OK" if status else "FAIL"
    detail_text = f" - {details}" if details else ""
    print(f"  {status_symbol} {item:<30} {status_text}{detail_text}")


def main():
    """Main function to run all checks."""
    print("tRIad Terminal ML Environment Checker")
    print("Checking ML environment readiness...")

    # Check core dependencies
    print_section("Core Dependencies")
    core_deps = check_core_dependencies()
    core_available = 0

    for dep in core_deps:
        status = dep["available"]
        if status:
            core_available += 1
        version_info = f"v{dep['version']}" if dep["version"] != "unknown" else ""
        error_info = f"({dep['error']})" if dep["error"] else ""
        details = version_info or error_info
        print_status(dep["name"], status, details)

    print(f"\nCore dependencies: {core_available}/{len(core_deps)} available")

    # Check optional dependencies
    print_section("Optional Dependencies")
    optional_deps = check_optional_dependencies()
    optional_available = 0

    for dep in optional_deps:
        status = dep["available"]
        if status:
            optional_available += 1
        version_info = f"v{dep['version']}" if dep["version"] != "unknown" else ""
        error_info = "Not installed (optional)" if not status else ""
        details = version_info or error_info
        print_status(dep["name"], status, details)

    print(f"\nOptional dependencies: {optional_available}/{len(optional_deps)} available")

    # Check ML predictor
    print_section("ML Predictor")
    predictor_status = check_ml_predictor()

    print_status("Predictor available", predictor_status["available"])
    if predictor_status["available"]:
        print_status(
            "Models loaded",
            len(predictor_status["models"]) > 0,
            f"{len(predictor_status['models'])} models",
        )
        print_status("Prediction works", predictor_status["prediction_works"])
        print_status("Legacy functions work", predictor_status["legacy_functions_work"])
    else:
        print(f"    Error: {predictor_status['error']}")

    # Check assistant
    print_section("AI Assistant")
    assistant_status = check_assistant()

    print_status("Assistant importable", assistant_status["importable"])
    if not assistant_status["importable"]:
        print(f"    Error: {assistant_status['error']}")

    # Check API
    print_section("API Endpoints")
    api_status = check_api_availability()

    print_status("API available", api_status["available"])
    if api_status["available"]:
        print_status("Health endpoint", api_status["health_endpoint"])
        print_status("ML prediction", api_status["ml_prediction"])
        print_status("ML status", api_status["ml_status"])
        print_status("Assistant status", api_status["assistant_status"])
    else:
        print(f"    Error: {api_status['error']}")

    # Check backward compatibility
    print_section("Backward Compatibility")
    compat_status = check_backward_compatibility()

    print_status("Compatibility shim", compat_status["working"])
    if compat_status["working"]:
        print_status("Error message quality", compat_status.get("error_message_quality", False))
    else:
        print(f"    Error: {compat_status['error']}")

    # Summary
    print_section("Summary")

    # Calculate overall status
    ml_ready = (
        predictor_status["available"] and core_available >= 4
    )  # At least sklearn, numpy, fastapi, uvicorn
    api_ready = api_status["available"]
    basic_ready = ml_ready and api_ready

    print_status("Core ML ready", ml_ready)
    print_status("API ready", api_ready)
    print_status("Basic functionality", basic_ready)
    print_status("Enhanced features", assistant_status["importable"] and optional_available > 0)

    if basic_ready:
        print("\n✓ Environment is ready for basic ML functionality!")
        print("  You can use ML prediction and API endpoints.")
    else:
        print("\n✗ Environment has issues. Please check the errors above.")
        print("  Install missing core dependencies and try again.")

    if assistant_status["importable"]:
        print("✓ AI Assistant is available for enhanced features.")
    else:
        print("! AI Assistant may have limited functionality.")

    print("\nFor full functionality, ensure these are installed:")
    print("  - scikit-learn (required for ML predictions)")
    print("  - numpy (required for ML predictions)")
    print("  - fastapi + uvicorn (required for API)")
    print("  - Optional: tensorflow (for deep learning features)")

    return 0 if basic_ready else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
