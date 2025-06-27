"""
Ingestion agent for streaming sensor data into the system.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import random

from core.state import state_manager, Alert
from core.logger import logger
from utils.data_utils import data_loader


class IngestionAgent:
    """Streams sensor data from CSV files and updates the global state."""
    
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.running = False
        self.current_time_index = 0
        self.data_files = {
            'solar': 'solar_data.csv',
            'load': 'load_data.csv',
            'price': 'price_data.csv'
        }
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Load all data files into cache."""
        for data_type, filename in self.data_files.items():
            try:
                self.data_cache[data_type] = data_loader.load_csv(filename)
                print(f"Loaded {data_type} data: {len(self.data_cache[data_type])} records")
            except Exception as e:
                print(f"Error loading {data_type} data: {e}")
                # Create empty DataFrame as fallback
                self.data_cache[data_type] = pd.DataFrame()
    
    async def start(self) -> None:
        """Start the ingestion agent."""
        self.running = True
        await logger.log_event("agent_started", {"agent": "ingestion"}, "ingestion_agent")
        print("Ingestion agent started")
        
        try:
            while self.running:
                await self._process_data()
                await asyncio.sleep(self.update_interval)
        except asyncio.CancelledError:
            print("Ingestion agent cancelled")
        except Exception as e:
            await logger.log_error(f"Ingestion agent error: {e}", "ingestion_agent", e)
        finally:
            self.running = False
            await logger.log_event("agent_stopped", {"agent": "ingestion"}, "ingestion_agent")
    
    async def _process_data(self) -> None:
        """Process and update sensor data."""
        try:
            # Get current data for all sensors
            solar_data = await self._get_current_sensor_data('solar')
            load_data = await self._get_current_sensor_data('load')
            price_data = await self._get_current_sensor_data('price')
            
            # Update global state
            await state_manager.update_state(
                solar_kwh=solar_data.get('solar_kwh', 0.0),
                load_kwh=load_data.get('load_kwh', 0.0),
                grid_price=price_data.get('grid_price_eur_kwh', 0.15),
                co2_intensity=price_data.get('co2_intensity_g_kwh', 400.0)
            )
            
            # Log the update
            await logger.log_state_change({
                "solar_kwh": solar_data.get('solar_kwh', 0.0),
                "load_kwh": load_data.get('load_kwh', 0.0),
                "grid_price": price_data.get('grid_price_eur_kwh', 0.15),
                "co2_intensity": price_data.get('co2_intensity_g_kwh', 400.0)
            }, "ingestion_agent")
            
            # Check for anomalies
            await self._check_anomalies(solar_data, load_data, price_data)
            
            # Move to next time step
            self.current_time_index = (self.current_time_index + 1) % 24
            
        except Exception as e:
            await logger.log_error(f"Error processing data: {e}", "ingestion_agent", e)
    
    async def _get_current_sensor_data(self, data_type: str) -> Dict[str, float]:
        """Get current sensor data for a specific type."""
        if data_type not in self.data_cache or self.data_cache[data_type].empty:
            return self._get_fallback_data(data_type)
        
        df = self.data_cache[data_type]
        
        # Get data for current time index
        if self.current_time_index < len(df):
            row = df.iloc[self.current_time_index]
            
            # Add some realistic noise
            noise_factor = 0.05  # 5% noise
            
            if data_type == 'solar':
                solar_kwh = row.get('solar_kwh', 0.0)
                # Add time-based variation and noise
                time_factor = self._get_solar_time_factor()
                noise = random.uniform(1 - noise_factor, 1 + noise_factor)
                return {
                    'solar_kwh': max(0, solar_kwh * time_factor * noise)
                }
            
            elif data_type == 'load':
                load_kwh = row.get('load_kwh', 100.0)
                hvac_kwh = row.get('hvac_kwh', 30.0)
                lighting_kwh = row.get('lighting_kwh', 20.0)
                machines_kwh = row.get('machines_kwh', 50.0)
                
                # Add noise to each component
                noise = random.uniform(1 - noise_factor, 1 + noise_factor)
                return {
                    'load_kwh': load_kwh * noise,
                    'hvac_kwh': hvac_kwh * noise,
                    'lighting_kwh': lighting_kwh * noise,
                    'machines_kwh': machines_kwh * noise
                }
            
            elif data_type == 'price':
                grid_price = row.get('grid_price_eur_kwh', 0.15)
                co2_intensity = row.get('co2_intensity_g_kwh', 400.0)
                
                # Add small noise to price and CO2
                price_noise = random.uniform(1 - 0.02, 1 + 0.02)  # 2% noise for price
                co2_noise = random.uniform(1 - 0.1, 1 + 0.1)  # 10% noise for CO2
                
                return {
                    'grid_price_eur_kwh': grid_price * price_noise,
                    'co2_intensity_g_kwh': co2_intensity * co2_noise
                }
        
        return self._get_fallback_data(data_type)
    
    def _get_fallback_data(self, data_type: str) -> Dict[str, float]:
        """Get fallback data when CSV data is not available."""
        if data_type == 'solar':
            return {'solar_kwh': 0.0}
        elif data_type == 'load':
            return {
                'load_kwh': 100.0,
                'hvac_kwh': 30.0,
                'lighting_kwh': 20.0,
                'machines_kwh': 50.0
            }
        elif data_type == 'price':
            return {
                'grid_price_eur_kwh': 0.15,
                'co2_intensity_g_kwh': 400.0
            }
        return {}
    
    def _get_solar_time_factor(self) -> float:
        """Get time-based factor for solar generation (0-1)."""
        hour = self.current_time_index
        # Solar generation follows a bell curve, peak at hour 12 (noon)
        if 6 <= hour <= 18:  # Daylight hours
            # Bell curve centered at hour 12
            peak_hour = 12
            sigma = 3  # Standard deviation
            factor = np.exp(-((hour - peak_hour) ** 2) / (2 * sigma ** 2))
            return factor
        else:
            return 0.0  # No solar generation at night
    
    async def _check_anomalies(self, solar_data: Dict[str, float], 
                             load_data: Dict[str, float], 
                             price_data: Dict[str, float]) -> None:
        """Check for anomalies in sensor data."""
        # Check for unusually high load
        load_kwh = load_data.get('load_kwh', 0.0)
        if load_kwh > 200:  # Threshold for high load
            alert = Alert(
                level="warning",
                message=f"High load detected: {load_kwh:.1f} kWh",
                timestamp=datetime.now(),
                source="ingestion_agent"
            )
            await state_manager.add_alert(alert)
            await logger.log_alert({
                "level": "warning",
                "message": f"High load detected: {load_kwh:.1f} kWh"
            }, "ingestion_agent")
        
        # Check for unusually high grid price
        grid_price = price_data.get('grid_price_eur_kwh', 0.15)
        if grid_price > 0.25:  # Threshold for high price
            alert = Alert(
                level="warning",
                message=f"High grid price detected: €{grid_price:.3f}/kWh",
                timestamp=datetime.now(),
                source="ingestion_agent"
            )
            await state_manager.add_alert(alert)
            await logger.log_alert({
                "level": "warning",
                "message": f"High grid price detected: €{grid_price:.3f}/kWh"
            }, "ingestion_agent")
        
        # Check for zero solar generation during daylight hours
        solar_kwh = solar_data.get('solar_kwh', 0.0)
        hour = self.current_time_index
        if 8 <= hour <= 16 and solar_kwh == 0:
            alert = Alert(
                level="info",
                message="No solar generation during daylight hours - possible equipment issue",
                timestamp=datetime.now(),
                source="ingestion_agent"
            )
            await state_manager.add_alert(alert)
    
    async def stop(self) -> None:
        """Stop the ingestion agent."""
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "running": self.running,
            "current_time_index": self.current_time_index,
            "update_interval": self.update_interval,
            "data_files_loaded": list(self.data_cache.keys())
        } 