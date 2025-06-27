"""
Forecast agent for predicting solar and load values.
"""

import asyncio
import numpy as np
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import joblib

from core.state import state_manager
from core.logger import logger
from utils.data_utils import RollingWindow


class ForecastAgent:
    """Forecasts solar and load values using rolling means and ML models."""
    
    def __init__(self, update_interval: float = 60.0):
        self.update_interval = update_interval
        self.running = False
        
        # Rolling windows for historical data
        self.solar_window = RollingWindow(window_size=24)
        self.load_window = RollingWindow(window_size=24)
        
        # ML models
        self.solar_model = LinearRegression()
        self.load_model = LinearRegression()
        
        # Scalers for feature normalization
        self.solar_scaler = StandardScaler()
        self.load_scaler = StandardScaler()
        
        # Model training state
        self.solar_model_trained = False
        self.load_model_trained = False
        
        # Feature engineering
        self.feature_names = ['hour', 'day_of_week', 'is_business_hour', 'is_peak_hour']
    
    async def start(self) -> None:
        """Start the forecast agent."""
        self.running = True
        await logger.log_event("agent_started", {"agent": "forecast"}, "forecast_agent")
        print("Forecast agent started")
        
        try:
            while self.running:
                await self._update_forecasts()
                await asyncio.sleep(self.update_interval)
        except asyncio.CancelledError:
            print("Forecast agent cancelled")
        except Exception as e:
            await logger.log_error(f"Forecast agent error: {e}", "forecast_agent", e)
        finally:
            self.running = False
            await logger.log_event("agent_stopped", {"agent": "forecast"}, "forecast_agent")
    
    async def _update_forecasts(self) -> None:
        """Update solar and load forecasts."""
        try:
            # Get current state
            state = await state_manager.get_state()
            
            # Add current values to rolling windows
            self.solar_window.add_value(state.solar_kwh)
            self.load_window.add_value(state.load_kwh)
            
            # Generate forecasts
            solar_forecast = await self._forecast_solar()
            load_forecast = await self._forecast_load()
            
            # Update state with forecasts
            await state_manager.update_state(
                solar_forecast_kwh=solar_forecast,
                load_forecast_kwh=load_forecast
            )
            
            # Log forecasts
            await logger.log_event("forecast_updated", {
                "solar_forecast": solar_forecast,
                "load_forecast": load_forecast,
                "solar_window_size": len(self.solar_window.data),
                "load_window_size": len(self.load_window.data)
            }, "forecast_agent")
            
            # Train models if we have enough data
            if len(self.solar_window.data) >= 12 and not self.solar_model_trained:
                await self._train_solar_model()
            
            if len(self.load_window.data) >= 12 and not self.load_model_trained:
                await self._train_load_model()
            
        except Exception as e:
            await logger.log_error(f"Error updating forecasts: {e}", "forecast_agent", e)
    
    async def _forecast_solar(self) -> float:
        """Forecast solar generation for the next hour."""
        if not self.solar_window.is_full():
            # Use simple time-based prediction if not enough data
            return self._simple_solar_forecast()
        
        if self.solar_model_trained:
            # Use ML model for prediction
            return await self._ml_solar_forecast()
        else:
            # Use rolling mean with trend
            return self._rolling_mean_solar_forecast()
    
    async def _forecast_load(self) -> float:
        """Forecast load consumption for the next hour."""
        if not self.load_window.is_full():
            # Use simple time-based prediction if not enough data
            return self._simple_load_forecast()
        
        if self.load_model_trained:
            # Use ML model for prediction
            return await self._ml_load_forecast()
        else:
            # Use rolling mean with trend
            return self._rolling_mean_load_forecast()
    
    def _simple_solar_forecast(self) -> float:
        """Simple time-based solar forecast."""
        current_hour = datetime.now().hour
        
        # Solar generation follows a bell curve
        if 6 <= current_hour <= 18:
            peak_hour = 12
            sigma = 3
            factor = np.exp(-((current_hour - peak_hour) ** 2) / (2 * sigma ** 2))
            return 50 * factor  # Max 50 kWh at peak
        else:
            return 0.0
    
    def _simple_load_forecast(self) -> float:
        """Simple time-based load forecast."""
        current_hour = datetime.now().hour
        
        # Higher load during business hours
        if 8 <= current_hour <= 18:
            base_load = 120
        else:
            base_load = 60
        
        # Add some randomness
        return base_load + np.random.normal(0, 10)
    
    def _rolling_mean_solar_forecast(self) -> float:
        """Forecast solar using rolling mean and trend."""
        mean = self.solar_window.get_mean()
        trend = self.solar_window.get_trend()
        
        # Apply trend to mean
        forecast = mean + trend
        
        # Ensure non-negative
        return max(0, forecast)
    
    def _rolling_mean_load_forecast(self) -> float:
        """Forecast load using rolling mean and trend."""
        mean = self.load_window.get_mean()
        trend = self.load_window.get_trend()
        
        # Apply trend to mean
        forecast = mean + trend
        
        # Ensure reasonable range
        return max(20, min(200, forecast))
    
    async def _ml_solar_forecast(self) -> float:
        """Forecast solar using trained ML model."""
        try:
            features = self._extract_features()
            features_scaled = self.solar_scaler.transform([features])
            prediction = self.solar_model.predict(features_scaled)[0]
            
            # Ensure non-negative
            return max(0, prediction)
        except Exception as e:
            await logger.log_error(f"ML solar forecast error: {e}", "forecast_agent", e)
            return self._rolling_mean_solar_forecast()
    
    async def _ml_load_forecast(self) -> float:
        """Forecast load using trained ML model."""
        try:
            features = self._extract_features()
            features_scaled = self.load_scaler.transform([features])
            prediction = self.load_model.predict(features_scaled)[0]
            
            # Ensure reasonable range
            return max(20, min(200, prediction))
        except Exception as e:
            await logger.log_error(f"ML load forecast error: {e}", "forecast_agent", e)
            return self._rolling_mean_load_forecast()
    
    def _extract_features(self) -> np.ndarray:
        """Extract features for ML prediction."""
        current_time = datetime.now()
        
        hour = current_time.hour
        day_of_week = current_time.weekday()
        is_business_hour = 1 if 8 <= hour <= 18 else 0
        is_peak_hour = 1 if 17 <= hour <= 21 else 0
        
        return np.array([hour, day_of_week, is_business_hour, is_peak_hour])
    
    async def _train_solar_model(self) -> None:
        """Train the solar forecasting model."""
        try:
            if len(self.solar_window.data) < 12:
                return
            
            # Prepare training data
            X = []
            y = []
            
            for i in range(len(self.solar_window.data) - 1):
                features = self._extract_features_for_training(i)
                X.append(features)
                y.append(self.solar_window.data[i + 1])
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.solar_scaler.fit_transform(X)
            
            # Train model
            self.solar_model.fit(X_scaled, y)
            self.solar_model_trained = True
            
            await logger.log_event("model_trained", {
                "model": "solar",
                "training_samples": len(X),
                "r2_score": self.solar_model.score(X_scaled, y)
            }, "forecast_agent")
            
        except Exception as e:
            await logger.log_error(f"Error training solar model: {e}", "forecast_agent", e)
    
    async def _train_load_model(self) -> None:
        """Train the load forecasting model."""
        try:
            if len(self.load_window.data) < 12:
                return
            
            # Prepare training data
            X = []
            y = []
            
            for i in range(len(self.load_window.data) - 1):
                features = self._extract_features_for_training(i)
                X.append(features)
                y.append(self.load_window.data[i + 1])
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.load_scaler.fit_transform(X)
            
            # Train model
            self.load_model.fit(X_scaled, y)
            self.load_model_trained = True
            
            await logger.log_event("model_trained", {
                "model": "load",
                "training_samples": len(X),
                "r2_score": self.load_model.score(X_scaled, y)
            }, "forecast_agent")
            
        except Exception as e:
            await logger.log_error(f"Error training load model: {e}", "forecast_agent", e)
    
    def _extract_features_for_training(self, index: int) -> np.ndarray:
        """Extract features for training at a specific time index."""
        # Simulate time features for training
        hour = index % 24
        day_of_week = (index // 24) % 7
        is_business_hour = 1 if 8 <= hour <= 18 else 0
        is_peak_hour = 1 if 17 <= hour <= 21 else 0
        
        return np.array([hour, day_of_week, is_business_hour, is_peak_hour])
    
    async def stop(self) -> None:
        """Stop the forecast agent."""
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "running": self.running,
            "update_interval": self.update_interval,
            "solar_window_size": len(self.solar_window.data),
            "load_window_size": len(self.load_window.data),
            "solar_model_trained": self.solar_model_trained,
            "load_model_trained": self.load_model_trained
        }
    
    def save_models(self, filepath: str) -> None:
        """Save trained models to disk."""
        if self.solar_model_trained or self.load_model_trained:
            model_data = {
                "solar_model": self.solar_model if self.solar_model_trained else None,
                "load_model": self.load_model if self.load_model_trained else None,
                "solar_scaler": self.solar_scaler if self.solar_model_trained else None,
                "load_scaler": self.load_scaler if self.load_model_trained else None,
                "solar_model_trained": self.solar_model_trained,
                "load_model_trained": self.load_model_trained
            }
            joblib.dump(model_data, filepath)
    
    def load_models(self, filepath: str) -> None:
        """Load trained models from disk."""
        try:
            model_data = joblib.load(filepath)
            self.solar_model = model_data.get("solar_model", LinearRegression())
            self.load_model = model_data.get("load_model", LinearRegression())
            self.solar_scaler = model_data.get("solar_scaler", StandardScaler())
            self.load_scaler = model_data.get("load_scaler", StandardScaler())
            self.solar_model_trained = model_data.get("solar_model_trained", False)
            self.load_model_trained = model_data.get("load_model_trained", False)
        except Exception as e:
            print(f"Error loading models: {e}") 