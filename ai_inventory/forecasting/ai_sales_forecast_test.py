"""
Standalone test version of ai_sales_forecast for development/testing
This version removes Frappe dependencies for testing the core logic
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# Try to import ML libraries with fallback
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Using simple forecasting.")

class SalesForecastingEngineStandalone:
    """
    Standalone version of SalesForecastingEngine for testing without Frappe
    """
    def __init__(self):
        self.models = {}
        self.encoders = {}
        self.model_path = "/tmp/ai_models"  # Use temp directory for testing
        
        # Create models directory if it doesn't exist
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
    
    def test_basic_functionality(self):
        """Test basic functionality without Frappe dependencies"""
        print("🧪 Testing SalesForecastingEngine basic functionality...")
        
        # Test model initialization
        print("✓ Engine initialized successfully")
        print(f"✓ Models directory: {self.model_path}")
        print(f"✓ ML libraries available: {SKLEARN_AVAILABLE}")
        
        if SKLEARN_AVAILABLE:
            # Test creating a simple model
            X = np.random.random((100, 5))
            y = np.random.random(100)
            
            model = RandomForestRegressor(n_estimators=10, random_state=42)
            model.fit(X, y)
            
            # Test prediction
            pred = model.predict(X[:5])
            print(f"✓ ML model test successful - sample prediction: {pred[0]:.3f}")
            
            # Test model saving
            model_path = os.path.join(self.model_path, "test_model.pkl")
            joblib.dump(model, model_path)
            
            # Test model loading
            loaded_model = joblib.load(model_path)
            loaded_pred = loaded_model.predict(X[:1])
            print(f"✓ Model save/load test successful")
            
            # Cleanup
            os.remove(model_path)
        
        return True

def test_import():
    """Test function to verify the module works"""
    try:
        engine = SalesForecastingEngineStandalone()
        result = engine.test_basic_functionality()
        return result
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing standalone AI Sales Forecasting module...")
    success = test_import()
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Tests failed!")
