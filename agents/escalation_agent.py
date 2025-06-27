"""
Escalation agent for handling supervisor notifications and escalations.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from core.state import state_manager
from core.logger import logger
from utils.gemini import llm_orchestrator


class EscalationAgent:
    """Composes escalation messages for supervisor if auto-control is blocked or critical alerts are present."""
    
    def __init__(self, update_interval: float = 60.0):
        self.update_interval = update_interval
        self.running = False
    
    async def start(self) -> None:
        self.running = True
        await logger.log_event("agent_started", {"agent": "escalation"}, "escalation_agent")
        print("Escalation agent started")
        try:
            while self.running:
                await self._check_escalation()
                await asyncio.sleep(self.update_interval)
        except asyncio.CancelledError:
            print("Escalation agent cancelled")
        except Exception as e:
            await logger.log_error(f"Escalation agent error: {e}", "escalation_agent", e)
        finally:
            self.running = False
            await logger.log_event("agent_stopped", {"agent": "escalation"}, "escalation_agent")
    
    async def _check_escalation(self) -> None:
        state = await state_manager.get_state()
        if not state.auto_control_enabled:
            # Compose escalation message
            alert_message = "Auto-control is currently disabled. Manual intervention required."
            system_status = state.system_status
            response = await llm_orchestrator.handle_escalation(alert_message, system_status)
            await logger.log_event("escalation_message", {
                "alert_message": alert_message,
                "response": response
            }, "escalation_agent")
        # Check for critical alerts
        for alert in state.active_alerts:
            if alert.level in ("error", "critical"):
                response = await llm_orchestrator.handle_escalation(alert.message, state.system_status)
                await logger.log_event("escalation_message", {
                    "alert_message": alert.message,
                    "response": response
                }, "escalation_agent")
    
    async def stop(self) -> None:
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "update_interval": self.update_interval
        } 