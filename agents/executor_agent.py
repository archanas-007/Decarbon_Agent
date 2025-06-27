"""
Executor agent for applying actions to the system state.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from core.state import state_manager
from core.logger import logger


class ExecutorAgent:
    """Reads decisions, mutates battery SOC, and schedules load shifts."""
    
    def __init__(self, update_interval: float = 60.0):
        self.update_interval = update_interval
        self.running = False
    
    async def start(self) -> None:
        self.running = True
        await logger.log_event("agent_started", {"agent": "executor"}, "executor_agent")
        print("Executor agent started")
        try:
            while self.running:
                await self._execute_action()
                await asyncio.sleep(self.update_interval)
        except asyncio.CancelledError:
            print("Executor agent cancelled")
        except Exception as e:
            await logger.log_error(f"Executor agent error: {e}", "executor_agent", e)
        finally:
            self.running = False
            await logger.log_event("agent_stopped", {"agent": "executor"}, "executor_agent")
    
    async def _execute_action(self) -> None:
        state = await state_manager.get_state()
        decision = state.current_decision
        if not decision:
            return
        action = decision.action
        battery_soc = state.battery_soc
        load_kwh = state.load_kwh
        solar_kwh = state.solar_kwh
        grid_price = state.grid_price
        co2_intensity = state.co2_intensity
        # Simulate battery and load changes
        soc_delta = 0
        load_shifted = 0
        if action == "A":  # Charge battery
            soc_delta = min(10, 100 - battery_soc)  # Charge up to 10% per cycle
        elif action == "B":  # Discharge battery
            soc_delta = -min(10, battery_soc)  # Discharge up to 10% per cycle
        elif action == "C":  # Use grid power
            pass  # No change to battery
        elif action == "D":  # Delay flexible load
            load_shifted = min(20, load_kwh * 0.2)  # Shift up to 20% of load
        elif action == "E":  # Sell excess energy
            soc_delta = -min(5, battery_soc)  # Discharge a bit to sell
        # Update battery SOC and load
        new_battery_soc = max(0, min(100, battery_soc + soc_delta))
        new_load_kwh = max(0, load_kwh - load_shifted)
        await state_manager.update_state(
            battery_soc=new_battery_soc,
            load_kwh=new_load_kwh
        )
        await logger.log_event("executor_update", {
            "action": action,
            "battery_soc": new_battery_soc,
            "load_kwh": new_load_kwh,
            "soc_delta": soc_delta,
            "load_shifted": load_shifted
        }, "executor_agent")
    
    async def stop(self) -> None:
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "update_interval": self.update_interval
        } 