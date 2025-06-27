"""
Advisor agent for LLM-based infrastructure upgrade recommendations.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from core.state import state_manager
from core.logger import logger
from utils.gemini import llm_orchestrator


class AdvisorAgent:
    """Runs daily, calls LLM for infrastructure advice, and updates the global state."""
    
    def __init__(self, update_interval: float = 24*60*60):  # Once per day
        self.update_interval = update_interval
        self.running = False
        self.last_run_date = None
    
    async def start(self) -> None:
        self.running = True
        await logger.log_event("agent_started", {"agent": "advisor"}, "advisor_agent")
        print("Advisor agent started")
        try:
            while self.running:
                await self._run_advice()
                await asyncio.sleep(self.update_interval)
        except asyncio.CancelledError:
            print("Advisor agent cancelled")
        except Exception as e:
            await logger.log_error(f"Advisor agent error: {e}", "advisor_agent", e)
        finally:
            self.running = False
            await logger.log_event("agent_stopped", {"agent": "advisor"}, "advisor_agent")
    
    async def _run_advice(self) -> None:
        state = await state_manager.get_state()
        today = datetime.now().date()
        if self.last_run_date == today:
            return  # Already ran today
        try:
            # Call LLM for infrastructure advice
            result = await llm_orchestrator.get_infrastructure_advice(
                daily_consumption=state.load_kwh,
                solar_capacity=state.solar_kwh,
                battery_capacity=state.battery_soc,  # Placeholder: use actual battery capacity if available
                annual_cost=state.total_cost_eur * 365,  # Estimate
                annual_co2=state.total_co2_kg * 365  # Estimate
            )
            if result and "recommendations" in result:
                await state_manager.update_state(infrastructure_advice=result)
                await logger.log_event("infrastructure_advice", result, "advisor_agent")
                self.last_run_date = today
            else:
                await logger.log_error("No valid infrastructure advice from LLM.", "advisor_agent")
        except Exception as e:
            await logger.log_error(f"Error in LLM infrastructure advice: {e}", "advisor_agent", e)
    
    async def stop(self) -> None:
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "update_interval": self.update_interval
        } 