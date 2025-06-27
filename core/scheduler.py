"""
Agent scheduler for orchestrating all decarbonization AI agents.
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
import signal
import sys

from .state import state_manager
from .logger import logger


class AgentScheduler:
    """Schedules and manages all agents in the decarbonization AI system."""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.running = False
        self._shutdown_event = asyncio.Event()
    
    def register_agent(self, name: str, agent_instance: Any) -> None:
        """Register an agent with the scheduler."""
        self.agents[name] = agent_instance
        print(f"Registered agent: {name}")
    
    async def start_agent(self, name: str) -> None:
        """Start a specific agent."""
        if name not in self.agents:
            raise ValueError(f"Agent {name} not registered")
        
        agent = self.agents[name]
        if hasattr(agent, 'start'):
            task = asyncio.create_task(agent.start())
            self.tasks[name] = task
            await logger.log_event("agent_started", {"agent": name}, "scheduler")
            print(f"Started agent: {name}")
        else:
            print(f"Agent {name} has no start method")
    
    async def stop_agent(self, name: str) -> None:
        """Stop a specific agent."""
        if name in self.tasks:
            task = self.tasks[name]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self.tasks[name]
            await logger.log_event("agent_stopped", {"agent": name}, "scheduler")
            print(f"Stopped agent: {name}")
    
    async def start_all_agents(self) -> None:
        """Start all registered agents."""
        self.running = True
        await logger.log_event("scheduler_started", {"agents": list(self.agents.keys())}, "scheduler")
        
        # Start all agents concurrently
        start_tasks = []
        for name in self.agents.keys():
            start_tasks.append(self.start_agent(name))
        
        await asyncio.gather(*start_tasks, return_exceptions=True)
        print("All agents started")
    
    async def stop_all_agents(self) -> None:
        """Stop all running agents."""
        self.running = False
        self._shutdown_event.set()
        
        # Stop all agents concurrently
        stop_tasks = []
        for name in list(self.tasks.keys()):
            stop_tasks.append(self.stop_agent(name))
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        await logger.log_event("scheduler_stopped", {}, "scheduler")
        print("All agents stopped")
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        status = {}
        for name, task in self.tasks.items():
            status[name] = {
                "running": not task.done(),
                "cancelled": task.cancelled(),
                "exception": str(task.exception()) if task.exception() else None
            }
        return status
    
    async def restart_agent(self, name: str) -> None:
        """Restart a specific agent."""
        await self.stop_agent(name)
        await asyncio.sleep(1)  # Brief pause
        await self.start_agent(name)
        await logger.log_event("agent_restarted", {"agent": name}, "scheduler")
    
    async def monitor_agents(self) -> None:
        """Monitor agent health and restart failed agents."""
        while self.running and not self._shutdown_event.is_set():
            try:
                for name, task in list(self.tasks.items()):
                    if task.done() and not task.cancelled():
                        exception = task.exception()
                        if exception:
                            await logger.log_error(
                                f"Agent {name} failed: {exception}",
                                "scheduler",
                                exception
                            )
                            print(f"Agent {name} failed, restarting...")
                            await self.restart_agent(name)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                await logger.log_error(f"Error in agent monitoring: {e}", "scheduler", e)
                await asyncio.sleep(60)  # Wait longer on error
    
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down gracefully...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self) -> None:
        """Graceful shutdown of the scheduler and all agents."""
        print("Shutting down scheduler...")
        await self.stop_all_agents()
        await logger.log_event("system_shutdown", {}, "scheduler")
        print("Shutdown complete")


# Global scheduler instance
scheduler = AgentScheduler() 