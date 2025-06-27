"""
Controller agent for rule-based control of HVAC, lighting, and machines.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from core.state import state_manager
from core.logger import logger


class ControllerAgent:
    """Rule-based control for HVAC, lighting, and machines."""
    
    def __init__(self, update_interval: float = 60.0):
        self.update_interval = update_interval
        self.running = False
    
    async def start(self) -> None:
        self.running = True
        await logger.log_event("agent_started", {"agent": "controller"}, "controller_agent")
        print("Controller agent started")
        try:
            while self.running:
                await self._control_logic()
                await asyncio.sleep(self.update_interval)
        except asyncio.CancelledError:
            print("Controller agent cancelled")
        except Exception as e:
            await logger.log_error(f"Controller agent error: {e}", "controller_agent", e)
        finally:
            self.running = False
            await logger.log_event("agent_stopped", {"agent": "controller"}, "controller_agent")
    
    async def _control_logic(self) -> None:
        state = await state_manager.get_state()
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        
        # Example rules:
        # Business hours: 8-18, weekdays
        business_hours = 8 <= hour <= 18 and weekday < 5
        occupancy = business_hours  # Simulate occupancy
        
        hvac_status = "on" if occupancy else "eco"
        lighting_status = "on" if occupancy else "off"
        machine_status = "on" if business_hours else "standby"
        
        await state_manager.update_state(
            hvac_status=hvac_status,
            lighting_status=lighting_status,
            machine_status=machine_status
        )
        
        await logger.log_event("controller_update", {
            "hvac_status": hvac_status,
            "lighting_status": lighting_status,
            "machine_status": machine_status
        }, "controller_agent")
    
    async def stop(self) -> None:
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "update_interval": self.update_interval
        } 