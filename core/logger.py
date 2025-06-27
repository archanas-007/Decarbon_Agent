"""
Unified logging system for the decarbonization AI system.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import asyncio
import threading


class DecarbonLogger:
    """Unified logger for the decarbonization AI system."""
    
    def __init__(self, log_file: str = "logs/decarbon_system.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("DecarbonAI")
        self._lock = None
        self._thread_local = threading.local()
    
    def _get_lock(self):
        """Get or create the asyncio lock for the current thread."""
        if not hasattr(self._thread_local, 'lock'):
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                self._thread_local.lock = asyncio.Lock()
            except RuntimeError:
                # No event loop in this thread, create a new one
                self._thread_local.lock = None
        return self._thread_local.lock
    
    async def log_event(self, event_type: str, data: Dict[str, Any], agent: str = "system") -> None:
        """Log an event with structured data."""
        lock = self._get_lock()
        if lock:
            async with lock:
                self._log_event_sync(event_type, data, agent)
        else:
            self._log_event_sync(event_type, data, agent)
    
    def _log_event_sync(self, event_type: str, data: Dict[str, Any], agent: str = "system") -> None:
        """Synchronous version of log_event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "agent": agent,
            "data": data
        }
        
        # Log to file
        self.logger.info(json.dumps(event))
        
        # Also log to console for debugging
        print(f"[{event['timestamp']}] {agent}: {event_type} - {data}")
    
    async def log_decision(self, decision: Dict[str, Any], agent: str = "decision_agent") -> None:
        """Log an AI decision."""
        await self.log_event("ai_decision", decision, agent)
    
    async def log_alert(self, alert: Dict[str, Any], agent: str = "system") -> None:
        """Log a system alert."""
        await self.log_event("alert", alert, agent)
    
    async def log_state_change(self, changes: Dict[str, Any], agent: str = "system") -> None:
        """Log state changes."""
        await self.log_event("state_change", changes, agent)
    
    async def log_error(self, error: str, agent: str = "system", exception: Optional[Exception] = None) -> None:
        """Log an error."""
        error_data = {
            "error": error,
            "exception": str(exception) if exception else None
        }
        await self.log_event("error", error_data, agent)
    
    async def log_performance(self, metric: str, value: float, agent: str = "system") -> None:
        """Log performance metrics."""
        await self.log_event("performance", {"metric": metric, "value": value}, agent)
    
    async def log_llm_call(self, prompt: str, response: str, agent: str = "llm") -> None:
        """Log LLM calls (with prompt and response)."""
        # Truncate long prompts/responses for logging
        truncated_prompt = prompt[:500] + "..." if len(prompt) > 500 else prompt
        truncated_response = response[:500] + "..." if len(response) > 500 else response
        
        await self.log_event("llm_call", {
            "prompt": truncated_prompt,
            "response": truncated_response
        }, agent)
    
    async def log_financial(self, cost: float, savings: float, co2_kg: float, agent: str = "system") -> None:
        """Log financial and environmental metrics."""
        await self.log_event("financial", {
            "cost_eur": cost,
            "savings_eur": savings,
            "co2_kg": co2_kg
        }, agent)
    
    def get_recent_logs(self, lines: int = 100) -> list:
        """Get recent log entries."""
        try:
            with open(self.log_file, 'r') as f:
                return f.readlines()[-lines:]
        except FileNotFoundError:
            return []
    
    def export_logs(self, output_file: str) -> None:
        """Export logs to a file."""
        try:
            with open(self.log_file, 'r') as src, open(output_file, 'w') as dst:
                dst.write(src.read())
        except FileNotFoundError:
            print(f"Log file {self.log_file} not found")


# Global logger instance - lazy initialization
_logger_instance = None

def get_logger():
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = DecarbonLogger()
    return _logger_instance

# For backward compatibility
logger = get_logger() 