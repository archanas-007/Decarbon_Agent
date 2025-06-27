"""
Data utilities for loading and processing sensor data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import asyncio
from datetime import datetime, timedelta


class DataLoader:
    """Handles loading and processing of sensor data files."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, pd.DataFrame] = {}
    
    def load_csv(self, filename: str) -> pd.DataFrame:
        """Load a CSV file with sensor data."""
        filepath = self.data_dir / filename
        
        if filepath in self._cache:
            return self._cache[filepath]
        
        if not filepath.exists():
            # Create sample data if file doesn't exist
            df = self._create_sample_data(filename)
            df.to_csv(filepath, index=False)
        else:
            df = pd.read_csv(filepath)
        
        # Ensure datetime column exists
        if 'timestamp' not in df.columns:
            df['timestamp'] = pd.date_range(
                start=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                periods=len(df),
                freq='H'
            )
        else:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        self._cache[filepath] = df
        return df
    
    def _create_sample_data(self, filename: str) -> pd.DataFrame:
        """Create sample sensor data for testing."""
        hours = 24
        base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if 'solar' in filename.lower():
            # Solar generation data (peak at noon)
            hours_range = np.arange(hours)
            solar_data = 50 * np.sin(np.pi * (hours_range - 6) / 12) ** 2
            solar_data = np.maximum(solar_data, 0)  # No negative values
            
            return pd.DataFrame({
                'timestamp': pd.date_range(base_time, periods=hours, freq='H'),
                'solar_kwh': solar_data,
                'efficiency': np.random.uniform(0.8, 0.95, hours)
            })
        
        elif 'load' in filename.lower():
            # Load consumption data (higher during business hours)
            hours_range = np.arange(hours)
            base_load = 100  # Base load in kWh
            business_hours = np.where((hours_range >= 8) & (hours_range <= 18), 1.5, 0.3)
            load_data = base_load * business_hours + np.random.normal(0, 10, hours)
            
            return pd.DataFrame({
                'timestamp': pd.date_range(base_time, periods=hours, freq='H'),
                'load_kwh': np.maximum(load_data, 20),  # Minimum load
                'hvac_kwh': np.random.uniform(20, 40, hours),
                'lighting_kwh': np.random.uniform(10, 25, hours),
                'machines_kwh': np.random.uniform(30, 80, hours)
            })
        
        elif 'price' in filename.lower():
            # Grid price data (higher during peak hours)
            hours_range = np.arange(hours)
            base_price = 0.15  # Base price in EUR/kWh
            peak_hours = np.where((hours_range >= 17) & (hours_range <= 21), 1.3, 1.0)
            price_data = base_price * peak_hours + np.random.normal(0, 0.02, hours)
            
            return pd.DataFrame({
                'timestamp': pd.date_range(base_time, periods=hours, freq='H'),
                'grid_price_eur_kwh': np.maximum(price_data, 0.05),
                'co2_intensity_g_kwh': np.random.uniform(350, 450, hours)
            })
        
        else:
            # Generic sensor data
            return pd.DataFrame({
                'timestamp': pd.date_range(base_time, periods=hours, freq='H'),
                'value': np.random.uniform(0, 100, hours)
            })
    
    def get_latest_data(self, filename: str, hours: int = 1) -> pd.DataFrame:
        """Get the latest N hours of data from a file."""
        df = self.load_csv(filename)
        return df.tail(hours)
    
    def get_data_at_time(self, filename: str, target_time: datetime) -> Optional[pd.Series]:
        """Get data for a specific timestamp."""
        df = self.load_csv(filename)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Find closest timestamp
        time_diff = abs(df['timestamp'] - target_time)
        closest_idx = time_diff.idxmin()
        
        if time_diff[closest_idx] <= timedelta(hours=1):
            return df.iloc[closest_idx]
        return None


class RollingWindow:
    """Manages rolling window calculations for time series data."""
    
    def __init__(self, window_size: int = 24):
        self.window_size = window_size
        self.data: List[float] = []
    
    def add_value(self, value: float) -> None:
        """Add a new value to the rolling window."""
        self.data.append(value)
        if len(self.data) > self.window_size:
            self.data.pop(0)
    
    def get_mean(self) -> float:
        """Get the mean of the current window."""
        return np.mean(self.data) if self.data else 0.0
    
    def get_std(self) -> float:
        """Get the standard deviation of the current window."""
        return np.std(self.data) if len(self.data) > 1 else 0.0
    
    def get_trend(self) -> float:
        """Get the trend (slope) of the current window."""
        if len(self.data) < 2:
            return 0.0
        
        x = np.arange(len(self.data))
        y = np.array(self.data)
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def is_full(self) -> bool:
        """Check if the window is full."""
        return len(self.data) >= self.window_size


class DataProcessor:
    """Processes and transforms sensor data."""
    
    @staticmethod
    def normalize_data(data: np.ndarray, min_val: float = 0, max_val: float = 1) -> np.ndarray:
        """Normalize data to a given range."""
        if len(data) == 0:
            return data
        
        data_min, data_max = np.min(data), np.max(data)
        if data_max == data_min:
            return np.full_like(data, (min_val + max_val) / 2)
        
        normalized = (data - data_min) / (data_max - data_min)
        return normalized * (max_val - min_val) + min_val
    
    @staticmethod
    def calculate_moving_average(data: np.ndarray, window: int = 5) -> np.ndarray:
        """Calculate moving average of data."""
        if len(data) < window:
            return data
        
        result = np.convolve(data, np.ones(window) / window, mode='valid')
        # Pad the beginning with the first value
        padding = np.full(window - 1, data[0])
        return np.concatenate([padding, result])
    
    @staticmethod
    def detect_anomalies(data: np.ndarray, threshold: float = 2.0) -> np.ndarray:
        """Detect anomalies using z-score method."""
        if len(data) < 3:
            return np.zeros_like(data, dtype=bool)
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return np.zeros_like(data, dtype=bool)
        
        z_scores = np.abs((data - mean) / std)
        return z_scores > threshold
    
    @staticmethod
    def interpolate_missing(data: pd.Series) -> pd.Series:
        """Interpolate missing values in time series data."""
        return data.interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')


# Global instances
data_loader = DataLoader() 