"""
Global system state management for the decarbonization AI system.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from dataclasses import dataclass


@dataclass
class Decision:
    """Represents an AI decision with action and explanation."""
    action: str
    explanation: str
    timestamp: datetime
    confidence: float = 0.0


@dataclass
class Alert:
    """Represents a system alert."""
    level: str  # "info", "warning", "error", "critical"
    message: str
    timestamp: datetime
    source: str


class SystemState(BaseModel):
    """Global system state for the decarbonization AI system."""
    
    # Real-time sensor data
    solar_kwh: float = Field(default=0.0, description="Current solar generation in kWh")
    load_kwh: float = Field(default=0.0, description="Current load consumption in kWh")
    battery_soc: float = Field(default=50.0, description="Battery state of charge (0-100%)")
    grid_price: float = Field(default=0.15, description="Current grid price in EUR/kWh")
    co2_intensity: float = Field(default=400.0, description="Grid CO2 intensity in g/kWh")
    
    # Forecasted values
    solar_forecast_kwh: float = Field(default=0.0, description="Forecasted solar generation (1h)")
    load_forecast_kwh: float = Field(default=0.0, description="Forecasted load consumption (1h)")
    
    # System status
    timestamp: datetime = Field(default_factory=datetime.now, description="Current timestamp")
    system_status: str = Field(default="running", description="System status")
    
    # Control variables
    hvac_status: str = Field(default="auto", description="HVAC control status")
    lighting_status: str = Field(default="auto", description="Lighting control status")
    machine_status: str = Field(default="auto", description="Machine control status")
    
    # Financial tracking
    total_cost_eur: float = Field(default=0.0, description="Total energy cost today")
    total_co2_kg: float = Field(default=0.0, description="Total CO2 emissions today")
    energy_savings_eur: float = Field(default=0.0, description="Energy savings from AI decisions")
    
    # AI decisions and history
    current_decision: Optional[Decision] = Field(default=None, description="Current AI decision")
    decision_history: List[Decision] = Field(default_factory=list, description="History of AI decisions")
    
    # Alerts and notifications
    active_alerts: List[Alert] = Field(default_factory=list, description="Active system alerts")
    alert_history: List[Alert] = Field(default_factory=list, description="History of all alerts")
    
    # Infrastructure recommendations
    infrastructure_advice: Dict[str, Any] = Field(default_factory=dict, description="AI infrastructure recommendations")
    
    # Simulation parameters
    simulation_speed: float = Field(default=1.0, description="Simulation speed multiplier")
    auto_control_enabled: bool = Field(default=True, description="Whether AI control is enabled")
    
    class Config:
        arbitrary_types_allowed = True


class StateManager:
    """Manages the global system state with thread-safe operations."""
    
    def __init__(self):
        self._state = SystemState()
        self._lock = asyncio.Lock()
        self._subscribers: List[callable] = []
    
    async def get_state(self) -> SystemState:
        """Get a copy of the current state."""
        async with self._lock:
            return self._state.model_copy()
    
    async def update_state(self, **kwargs) -> None:
        """Update the state with new values."""
        async with self._lock:
            for key, value in kwargs.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)
            
            # Update timestamp
            self._state.timestamp = datetime.now()
            
            # Notify subscribers
            await self._notify_subscribers()
    
    async def add_decision(self, decision: Decision) -> None:
        """Add a new AI decision to the state."""
        async with self._lock:
            self._state.current_decision = decision
            self._state.decision_history.append(decision)
            
            # Keep only last 100 decisions
            if len(self._state.decision_history) > 100:
                self._state.decision_history = self._state.decision_history[-100:]
    
    async def add_alert(self, alert: Alert) -> None:
        """Add a new alert to the state."""
        async with self._lock:
            self._state.active_alerts.append(alert)
            self._state.alert_history.append(alert)
            
            # Keep only last 50 alerts
            if len(self._state.alert_history) > 50:
                self._state.alert_history = self._state.alert_history[-50:]
    
    async def clear_resolved_alerts(self) -> None:
        """Clear resolved alerts (implement based on your logic)."""
        async with self._lock:
            # For now, keep all alerts active
            pass
    
    async def subscribe(self, callback: callable) -> None:
        """Subscribe to state changes."""
        self._subscribers.append(callback)
    
    async def _notify_subscribers(self) -> None:
        """Notify all subscribers of state changes."""
        for callback in self._subscribers:
            try:
                await callback(self._state.model_copy())
            except Exception as e:
                print(f"Error notifying subscriber: {e}")


# Global state manager instance
state_manager = StateManager() 