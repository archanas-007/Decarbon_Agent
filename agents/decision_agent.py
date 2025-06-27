"""
Decision agent for LLM-based operational action selection.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from core.state import state_manager, Decision
from core.logger import logger
from utils.gemini import llm_orchestrator


class DecisionAgent:
    """Packages state and forecast, calls LLM, and updates the global state with the chosen action."""
    
    def __init__(self, update_interval: float = 60.0):
        self.update_interval = update_interval
        self.running = False
    
    async def start(self) -> None:
        self.running = True
        await logger.log_event("agent_started", {"agent": "decision"}, "decision_agent")
        print("Decision agent started")
        try:
            while self.running:
                await self._make_decision()
                await asyncio.sleep(self.update_interval)
        except asyncio.CancelledError:
            print("Decision agent cancelled")
        except Exception as e:
            await logger.log_error(f"Decision agent error: {e}", "decision_agent", e)
        finally:
            self.running = False
            await logger.log_event("agent_stopped", {"agent": "decision"}, "decision_agent")
    
    async def _make_decision(self) -> None:
        state = await state_manager.get_state()
        try:
            # Call LLM for decision
            result = await llm_orchestrator.make_decision(
                solar_kwh=state.solar_forecast_kwh,
                load_kwh=state.load_forecast_kwh,
                battery_soc=state.battery_soc,
                price=state.grid_price,
                co2_intensity=state.co2_intensity
            )
            if result and "action" in result:
                decision = Decision(
                    action=result["action"],
                    explanation=result.get("explanation", ""),
                    timestamp=datetime.now(),
                    confidence=result.get("confidence", 1.0)
                )
                await state_manager.add_decision(decision)
                await logger.log_decision({
                    "action": decision.action,
                    "explanation": decision.explanation,
                    "confidence": decision.confidence
                }, "decision_agent")
            else:
                await logger.log_error("No valid action from LLM decision.", "decision_agent")
        except Exception as e:
            await logger.log_error(f"Error in LLM decision: {e}", "decision_agent", e)
    
    async def stop(self) -> None:
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "update_interval": self.update_interval
        } 