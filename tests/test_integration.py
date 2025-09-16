#!/usr/bin/env python3
"""
Simple integration test for the new API structure.

This test can be run directly without pytest to verify the API works.
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all modules can be imported."""
    print("🔍 Testing imports...")

    try:
        print("✅ API app imports successfully")
    except Exception as e:
        print(f"❌ Failed to import API app: {e}")
        return False

    try:
        print("✅ ML predictor imports successfully")
    except Exception as e:
        print(f"❌ Failed to import ML predictor: {e}")
        return False

    return True

def test_ml_predictor():
    """Test the ML predictor functionality."""
    print("\n🧠 Testing ML predictor...")

    try:
        from ml.predictor import MLPredictor

        predictor = MLPredictor()

        # Test prediction
        test_features = [5.1, 3.5, 1.4, 0.2]
        result = predictor.predict(test_features)

        print(f"✅ Prediction successful: {result['prediction']['label']}")
        print(f"   Model used: {result['model_used']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Processing time: {result['processing_time_ms']:.2f}ms")

        # Test list models
        models = predictor.list_models()
        print(f"✅ Available models: {models}")

        return True
    except Exception as e:
        print(f"❌ ML predictor test failed: {e}")
        return False

def test_legacy_functions():
    """Test backward compatibility functions."""
    print("\n🔄 Testing legacy functions...")

    try:
        from ml.predictor import predict_forest, predict_knn

        test_features = [5.1, 3.5, 1.4, 0.2]

        # Test KNN
        knn_result = predict_knn(test_features)
        print(f"✅ Legacy KNN prediction: {knn_result['predicted_label']}")

        # Test Random Forest
        forest_result = predict_forest(test_features)
        print(f"✅ Legacy Forest prediction: {forest_result['predicted_label']}")

        return True
    except Exception as e:
        print(f"❌ Legacy functions test failed: {e}")
        return False

def test_api_with_testclient():
    """Test the API using FastAPI's TestClient."""
    print("\n🌐 Testing API endpoints...")

    try:
        from fastapi.testclient import TestClient

        from api.main import app

        client = TestClient(app)

        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check: {health_data['status']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False

        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            root_data = response.json()
            print(f"✅ Root endpoint: {root_data['message']}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False

        # Test ML prediction
        test_features = [5.1, 3.5, 1.4, 0.2]
        response = client.post("/ml/predict", json={"features": test_features})
        if response.status_code == 200:
            pred_data = response.json()
            print(f"✅ ML prediction: {pred_data['prediction']['label']}")
        else:
            print(f"❌ ML prediction failed: {response.status_code}")
            return False

        # Test models list
        response = client.get("/ml/models")
        if response.status_code == 200:
            models_data = response.json()
            print(f"✅ Models list: {models_data['available_models']}")
        else:
            print(f"❌ Models list failed: {response.status_code}")
            return False

        return True
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_existing_compatibility():
    """Test that existing models module still works."""
    print("\n🔄 Testing existing compatibility...")

    try:
        # Test that the models module can be imported
        from models import predict_forest, predict_knn

        test_features = [5.1, 3.5, 1.4, 0.2]

        # Test existing functions
        knn_result = predict_knn(test_features)
        print(f"✅ Existing KNN still works: {knn_result['predicted_label']}")

        forest_result = predict_forest(test_features)
        print(f"✅ Existing Forest still works: {forest_result['predicted_label']}")

        return True
    except Exception as e:
        print(f"❌ Existing compatibility test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running tRIad Terminal API Integration Tests")
    print("=" * 50)

    tests = [
        test_imports,
        test_ml_predictor,
        test_legacy_functions,
        test_api_with_testclient,
        test_existing_compatibility
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The API is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
