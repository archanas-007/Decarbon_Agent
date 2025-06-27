"""
Streamlit dashboard for the decarbonization AI system.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import core modules, but don't fail if they're not available
CORE_AVAILABLE = False
try:
    # Import with error handling
    from core.state import state_manager
    from core.logger import logger
    from utils.gemini import llm_orchestrator
    CORE_AVAILABLE = True
except Exception as e:
    CORE_AVAILABLE = False
    # Store the error message to display later
    IMPORT_ERROR = str(e)


def get_real_ai_response(user_message: str) -> str:
    """Get real AI response using Gemini."""
    try:
        if not CORE_AVAILABLE:
            return "This is a demo version. Add your Gemini API key to enable full AI functionality!"
        
        # Check if API key is set
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == 'your_gemini_api_key_here':
            return "This is a demo version. Add your Gemini API key to enable full AI functionality!"
        
        # Get AI response
        response = llm_orchestrator.chat_response(user_message)
        
        if response and response.strip():
            return response
        else:
            return "This is a demo version. Add your Gemini API key to enable full AI functionality!"
            
    except Exception as e:
        return f"AI Error: {str(e)}. This is a demo version."


def get_mock_state():
    """Generate mock system state for demonstration."""
    current_time = datetime.now()
    
    # Simulate realistic energy data
    hour = current_time.hour
    solar_kwh = max(0, 25 * np.sin(np.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0
    load_kwh = 50 + 30 * np.sin(np.pi * hour / 12) + random.uniform(-10, 10)
    battery_soc = 60 + random.uniform(-5, 5)
    grid_price = 0.15 + 0.05 * np.sin(np.pi * hour / 12) + random.uniform(-0.02, 0.02)
    co2_intensity = 400 + 50 * np.sin(np.pi * hour / 12) + random.uniform(-20, 20)
    
    return {
        'solar_kwh': max(0, solar_kwh),
        'load_kwh': max(10, load_kwh),
        'battery_soc': max(0, min(100, battery_soc)),
        'grid_price': max(0.05, grid_price),
        'co2_intensity': max(200, co2_intensity),
        'total_cost_eur': load_kwh * grid_price,
        'system_status': 'operational',
        'timestamp': current_time,
        'current_decision': {
            'action': 'Charge battery from solar',
            'explanation': 'Solar generation exceeds load, storing excess energy',
            'confidence': 0.85
        },
        'active_alerts': [
            {'level': 'info', 'message': 'System operating normally'},
            {'level': 'warning', 'message': 'Grid price approaching peak hours'}
        ],
        'infrastructure_advice': {
            'recommendations': [
                {
                    'upgrade': 'Solar Panel Expansion',
                    'cost_eur': 15000,
                    'annual_savings_eur': 2500,
                    'roi_years': 6.0,
                    'co2_reduction_kg': 5000
                },
                {
                    'upgrade': 'Battery Storage Upgrade',
                    'cost_eur': 8000,
                    'annual_savings_eur': 1200,
                    'roi_years': 6.7,
                    'co2_reduction_kg': 2000
                }
            ]
        }
    }


def main():
    st.set_page_config(
        page_title="Decarbon AI Dashboard",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Display import warning if needed
    if not CORE_AVAILABLE:
        st.warning(f"⚠️ Core modules not available: {IMPORT_ERROR}. Running in demo mode.")
    
    st.title("🧠 Decarbon AI Master Brain")
    st.markdown("Real-time energy management and decarbonization system")
    
    # Sidebar
    with st.sidebar:
        st.header("System Controls")
        
        # Auto-control toggle
        auto_control = st.checkbox("Auto Control", value=True, key="auto_control")
        
        # Simulation speed
        sim_speed = st.slider("Simulation Speed", 0.1, 5.0, 1.0, 0.1)
        
        # System status
        st.subheader("System Status")
        status_placeholder = st.empty()
        
        # Agent status
        st.subheader("Agent Status")
        agent_placeholder = st.empty()
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Real-time energy flow
        st.subheader("⚡ Real-time Energy Flow")
        energy_placeholder = st.empty()
        
        # Energy trends
        st.subheader("📈 Energy Trends")
        trends_placeholder = st.empty()
    
    with col2:
        # Current metrics
        st.subheader("📊 Current Metrics")
        metrics_placeholder = st.empty()
        
        # AI Decisions
        st.subheader("🤖 AI Decisions")
        decisions_placeholder = st.empty()
        
        # Alerts
        st.subheader("🚨 Alerts")
        alerts_placeholder = st.empty()
    
    # Infrastructure recommendations
    st.subheader("🏗️ Infrastructure Recommendations")
    infra_placeholder = st.empty()
    
    # Chat interface
    st.subheader("💬 AI Assistant")
    chat_placeholder = st.empty()
    
    # Auto-refresh
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    # Get mock state
    state = get_mock_state()
    
    # Update sidebar
    with status_placeholder.container():
        st.metric("System Status", state['system_status'])
        st.metric("Last Update", state['timestamp'].strftime("%H:%M:%S"))
    
    # Update energy flow
    with energy_placeholder.container():
        fig = create_energy_flow_chart(state)
        st.plotly_chart(fig, use_container_width=True)
    
    # Update trends
    with trends_placeholder.container():
        fig = create_trends_chart(state)
        st.plotly_chart(fig, use_container_width=True)
    
    # Update metrics
    with metrics_placeholder.container():
        st.metric("Solar Generation", f"{state['solar_kwh']:.1f} kWh")
        st.metric("Load Consumption", f"{state['load_kwh']:.1f} kWh")
        st.metric("Battery SOC", f"{state['battery_soc']:.1f}%")
        st.metric("Grid Price", f"€{state['grid_price']:.3f}/kWh")
        st.metric("CO₂ Intensity", f"{state['co2_intensity']:.0f} g/kWh")
        st.metric("Daily Cost", f"€{state['total_cost_eur']:.2f}")
    
    # Update decisions
    with decisions_placeholder.container():
        if state['current_decision']:
            decision = state['current_decision']
            st.info(f"**Action {decision['action']}**: {decision['explanation']}")
            st.caption(f"Confidence: {decision['confidence']:.1%}")
        else:
            st.info("No recent AI decisions")
    
    # Update alerts
    with alerts_placeholder.container():
        for alert in state['active_alerts']:
            if alert['level'] == "critical":
                st.error(f"🚨 {alert['message']}")
            elif alert['level'] == "warning":
                st.warning(f"⚠️ {alert['message']}")
            elif alert['level'] == "info":
                st.info(f"ℹ️ {alert['message']}")
    
    # Update infrastructure recommendations
    with infra_placeholder.container():
        if state['infrastructure_advice']:
            advice = state['infrastructure_advice']
            if "recommendations" in advice:
                for rec in advice["recommendations"][:3]:  # Show top 3
                    with st.expander(f"💡 {rec.get('upgrade', 'Upgrade')}"):
                        st.write(f"**Cost**: €{rec.get('cost_eur', 0):,}")
                        st.write(f"**Annual Savings**: €{rec.get('annual_savings_eur', 0):,}")
                        st.write(f"**ROI**: {rec.get('roi_years', 0):.1f} years")
                        st.write(f"**CO₂ Reduction**: {rec.get('co2_reduction_kg', 0):,} kg/year")
        else:
            st.info("No infrastructure recommendations available")
    
    # Chat interface
    with chat_placeholder.container():
        user_input = st.text_input("Ask the AI assistant:", key="chat_input")
        if st.button("Send", key="send_button"):
            if user_input:
                response = get_real_ai_response(user_input)
                st.success(f"AI response: {response}")


def create_energy_flow_chart(state):
    """Create energy flow sankey diagram."""
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=["Solar", "Grid", "Battery", "Load", "Excess"],
            color=["yellow", "gray", "blue", "red", "green"]
        ),
        link=dict(
            source=[0, 1, 2, 0, 1, 2],  # indices correspond to labels
            target=[2, 3, 3, 3, 3, 4],
            value=[state['solar_kwh'] * 0.3, state['load_kwh'] * 0.4, state['load_kwh'] * 0.3,
                   state['solar_kwh'] * 0.7, state['load_kwh'] * 0.6, state['battery_soc'] * 0.1]
        )
    )])
    
    fig.update_layout(
        title_text="Energy Flow Diagram",
        font_size=10,
        height=400
    )
    return fig


def create_trends_chart(state):
    """Create energy trends chart."""
    # Simulate historical data
    hours = list(range(24))
    solar_data = [state['solar_kwh'] * (0.5 + 0.5 * (i % 12) / 12) for i in hours]
    load_data = [state['load_kwh'] * (0.8 + 0.4 * (i % 8) / 8) for i in hours]
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Solar Generation", "Load Consumption"),
        vertical_spacing=0.1
    )
    
    fig.add_trace(
        go.Scatter(x=hours, y=solar_data, mode='lines+markers', name='Solar', line=dict(color='orange')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=hours, y=load_data, mode='lines+markers', name='Load', line=dict(color='red')),
        row=2, col=1
    )
    
    fig.update_layout(
        title_text="24-Hour Energy Trends",
        height=500,
        showlegend=True
    )
    
    fig.update_xaxes(title_text="Hour of Day")
    fig.update_yaxes(title_text="kWh", row=1, col=1)
    fig.update_yaxes(title_text="kWh", row=2, col=1)
    
    return fig


if __name__ == "__main__":
    main() 