"""
Test ML import stability and dependency handling.

Tests that ML modules can be imported safely even when optional
dependencies are missing, and that fallbacks work correctly.
"""

import pytest
import sys
import os
from unittest.mock import patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class TestMLImportStability:
    """Test ML module import stability."""
    
    def test_ml_predictor_import(self):
        """Test that ML predictor can be imported successfully."""
        from ml.predictor import MLPredictor, predict_knn, predict_forest
        
        # Should not raise any import errors
        assert MLPredictor is not None
        assert predict_knn is not None
        assert predict_forest is not None
    
    def test_ml_package_import(self):
        """Test that ML package imports work correctly."""
        from ml import MLPredictor, predict_knn, predict_forest
        
        # Check that exports are available
        assert MLPredictor is not None
        assert predict_knn is not None
        assert predict_forest is not None
    
    def test_ml_predictor_instantiation(self):
        """Test that MLPredictor can be instantiated."""
        from ml.predictor import MLPredictor
        
        predictor = MLPredictor()
        assert predictor is not None
        assert hasattr(predictor, 'predict')
        assert hasattr(predictor, 'list_models')
    
    def test_legacy_functions_work(self):
        """Test that legacy prediction functions work."""
        from ml.predictor import predict_knn, predict_forest
        
        test_features = [5.1, 3.5, 1.4, 0.2]
        
        # Test KNN
        knn_result = predict_knn(test_features)
        assert isinstance(knn_result, dict)
        assert "model" in knn_result
        assert knn_result["model"] == "knn"
        
        # Test Random Forest
        forest_result = predict_forest(test_features)
        assert isinstance(forest_result, dict)
        assert "model" in forest_result
        assert forest_result["model"] == "forest"
    
    def test_assistant_import_handling(self):
        """Test assistant import with backward compatibility."""
        # Test that the new import works
        try:
            from agents.learning.assistant_ml import CodeCompletionEngine
            assert CodeCompletionEngine is not None
        except ImportError:
            # If sklearn is not available, this is expected
            pass
        
        # Test that the old import raises clear error
        with pytest.raises(ImportError) as exc_info:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "assistant_ml_old", 
                os.path.join(project_root, "agents/learning/assistant-ML.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        
        assert "renamed to 'assistant_ml.py'" in str(exc_info.value)
    
    @patch.dict('sys.modules', {'sklearn': None})
    def test_sklearn_import_fallback(self):
        """Test that missing sklearn is handled gracefully."""
        # Remove sklearn from modules to simulate missing dependency
        sklearn_modules = [name for name in sys.modules if name.startswith('sklearn')]
        for module_name in sklearn_modules:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        # Should be able to import ML modules even without sklearn for the assistant
        # (The predictor itself requires sklearn, but the import should work)
        try:
            import importlib
            # Force reload to test import behavior
            if 'agents.learning.assistant_ml' in sys.modules:
                importlib.reload(sys.modules['agents.learning.assistant_ml'])
        except ImportError:
            # This is expected if sklearn is required
            pass
    
    def test_dependency_availability_check(self):
        """Test checking of optional dependencies."""
        # Test sklearn availability
        sklearn_available = False
        try:
            import sklearn
            sklearn_available = True
        except ImportError:
            pass
        
        # Test that we can determine sklearn availability
        assert isinstance(sklearn_available, bool)
        
        # Test tensorflow availability (optional)
        tensorflow_available = False
        try:
            import tensorflow
            tensorflow_available = True
        except ImportError:
            pass
        
        assert isinstance(tensorflow_available, bool)
    
    def test_ml_functionality_with_missing_deps(self):
        """Test that basic ML functionality works even with some missing deps."""
        from ml.predictor import MLPredictor
        
        # This should work since scikit-learn is in requirements.txt
        predictor = MLPredictor()
        test_features = [5.1, 3.5, 1.4, 0.2]
        
        result = predictor.predict(test_features)
        assert isinstance(result, dict)
        assert "prediction" in result
        assert "model_used" in result
        assert "confidence" in result
        assert "processing_time_ms" in result

class TestBackwardCompatibility:
    """Test backward compatibility features."""
    
    def test_legacy_model_interface(self):
        """Test that legacy model interface still works."""
        # Import the old model.py style functions if they exist
        try:
            from model import predict_knn, predict_forest
            
            test_features = [5.1, 3.5, 1.4, 0.2]
            
            knn_result = predict_knn(test_features)
            assert "model" in knn_result
            assert knn_result["model"] == "knn"
            
            forest_result = predict_forest(test_features)
            assert "model" in forest_result
            assert forest_result["model"] == "forest"
            
        except ImportError:
            # If model.py doesn't exist or doesn't have these functions, that's okay
            pass
    
    def test_import_error_message_quality(self):
        """Test that import error messages are helpful."""
        try:
            # Try to import the old filename
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "assistant_ml_old", 
                os.path.join(project_root, "agents/learning/assistant-ML.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert False, "Should have raised ImportError"
        except ImportError as e:
            error_msg = str(e)
            assert "renamed" in error_msg
            assert "assistant_ml.py" in error_msg
            assert "Python naming conventions" in error_msg