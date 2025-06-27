"""
Main entry point for the Decarbon AI system.
"""

import asyncio
import subprocess
import sys

from core.scheduler import scheduler
from agents.ingestion_agent import IngestionAgent
from agents.forecast_agent import ForecastAgent
from agents.controller_agent import ControllerAgent
from agents.decision_agent import DecisionAgent
from agents.advisor_agent import AdvisorAgent
from agents.executor_agent import ExecutorAgent
from agents.escalation_agent import EscalationAgent


def register_agents():
    scheduler.register_agent("ingestion", IngestionAgent())
    scheduler.register_agent("forecast", ForecastAgent())
    scheduler.register_agent("controller", ControllerAgent())
    scheduler.register_agent("decision", DecisionAgent())
    scheduler.register_agent("advisor", AdvisorAgent())
    scheduler.register_agent("executor", ExecutorAgent())
    scheduler.register_agent("escalation", EscalationAgent())


def launch_streamlit_apps():
    # Optionally launch dashboard and chatbot in separate processes
    try:
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "chatbot/interface.py"])
    except Exception as e:
        print(f"Could not launch Streamlit apps automatically: {e}")
        print("You can manually run: streamlit run dashboard/app.py and streamlit run chatbot/interface.py")


async def main():
    register_agents()
    scheduler.setup_signal_handlers()
    print("Starting all agents...")
    await scheduler.start_all_agents()
    # Optionally, launch Streamlit apps
    # launch_streamlit_apps()
    print("All agents running. Press Ctrl+C to stop.")
    # Keep running until interrupted
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...") 