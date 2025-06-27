"""
Streamlit chatbot interface for the decarbonization AI system.
"""

import streamlit as st
import numpy as np
from datetime import datetime
import random
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import core modules, but don't fail if they're not available
GEMINI_AVAILABLE = False
try:
    # Import with error handling
    from utils.gemini import llm_orchestrator
    from core.state import state_manager
    from core.logger import logger
    GEMINI_AVAILABLE = True
except Exception as e:
    GEMINI_AVAILABLE = False
    # Store the error message to display later
    IMPORT_ERROR = str(e)


def get_mock_system_state():
    """Generate mock system state for demonstration."""
    current_time = datetime.now()
    hour = current_time.hour
    
    solar_kwh = max(0, 25 * np.sin(np.pi * (hour - 6) / 12)) if 6 <= hour <= 18 else 0
    load_kwh = 50 + 30 * np.sin(np.pi * hour / 12) + random.uniform(-10, 10)
    battery_soc = 60 + random.uniform(-5, 5)
    grid_price = 0.15 + 0.05 * np.sin(np.pi * hour / 12) + random.uniform(-0.02, 0.02)
    
    return {
        'solar_kwh': max(0, solar_kwh),
        'load_kwh': max(10, load_kwh),
        'battery_soc': max(0, min(100, battery_soc)),
        'grid_price': max(0.05, grid_price),
        'current_decision': {
            'action': 'Charge battery from solar',
            'explanation': 'Solar generation exceeds load, storing excess energy'
        }
    }


def get_real_ai_response(user_message: str) -> str:
    """Get real AI response using Gemini."""
    try:
        if not GEMINI_AVAILABLE:
            return get_mock_ai_response(user_message)
        
        # Check if API key is set
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == 'your_gemini_api_key_here':
            return get_mock_ai_response(user_message)
        
        # Get current system state for context
        try:
            state = state_manager.get_state()
            context = f"""
            Current System State:
            - Solar Generation: {state.solar_kwh:.1f} kWh
            - Load Consumption: {state.load_kwh:.1f} kWh
            - Battery SOC: {state.battery_soc:.1f}%
            - Grid Price: €{state.grid_price:.3f}/kWh
            - CO₂ Intensity: {state.co2_intensity:.0f} g/kWh
            - System Status: {state.system_status}
            """
        except:
            context = "System state unavailable"
        
        # Get AI response
        response = llm_orchestrator.chat_response(user_message, context)
        
        if response and response.strip():
            return response
        else:
            return get_mock_ai_response(user_message)
            
    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        return get_mock_ai_response(user_message)


def get_mock_ai_response(user_message: str) -> str:
    """Generate mock AI responses for demonstration."""
    message_lower = user_message.lower()
    
    if "energy status" in message_lower or "current" in message_lower:
        state = get_mock_system_state()
        return f"""**Current Energy Status:**
- Solar Generation: {state['solar_kwh']:.1f} kWh
- Load Consumption: {state['load_kwh']:.1f} kWh  
- Battery SOC: {state['battery_soc']:.1f}%
- Grid Price: €{state['grid_price']:.3f}/kWh

The system is operating normally with solar generation providing {state['solar_kwh']/state['load_kwh']*100:.1f}% of current load."""
    
    elif "savings" in message_lower:
        return """**Today's Energy Savings:**
- Solar Generation: 45.2 kWh
- Grid Consumption: 23.8 kWh
- Cost Savings: €3.45
- CO₂ Reduction: 12.3 kg

Your solar panels are performing well today!"""
    
    elif "ai decisions" in message_lower or "decisions" in message_lower:
        state = get_mock_system_state()
        return f"""**Latest AI Decision:**
**Action**: {state['current_decision']['action']}
**Explanation**: {state['current_decision']['explanation']}
**Confidence**: 85%

The AI is actively managing your energy system for optimal efficiency."""
    
    elif "upgrade" in message_lower or "infrastructure" in message_lower:
        return """**Infrastructure Recommendations:**
1. **Solar Panel Expansion** (€15,000)
   - Annual Savings: €2,500
   - ROI: 6.0 years
   - CO₂ Reduction: 5,000 kg/year

2. **Battery Storage Upgrade** (€8,000)
   - Annual Savings: €1,200  
   - ROI: 6.7 years
   - CO₂ Reduction: 2,000 kg/year

3. **Smart Thermostat** (€300)
   - Annual Savings: €180
   - ROI: 1.7 years
   - CO₂ Reduction: 400 kg/year"""
    
    elif "optimize" in message_lower or "efficiency" in message_lower:
        return """**Energy Optimization Tips:**
1. **Load Shifting**: Move high-power activities to solar peak hours (10 AM - 4 PM)
2. **Battery Management**: Charge during low-price periods, discharge during peak
3. **Smart Scheduling**: Use timers for appliances to match solar generation
4. **Efficiency Upgrades**: Consider LED lighting and energy-efficient appliances
5. **Monitoring**: Track usage patterns to identify optimization opportunities"""
    
    elif "co2" in message_lower or "carbon" in message_lower:
        return """**Today's CO₂ Impact:**
- Total CO₂ Emissions: 8.7 kg
- CO₂ Avoided (Solar): 12.3 kg
- Net CO₂ Impact: -3.6 kg (Carbon Negative!)
- Monthly Trend: 15% reduction vs last month

Your system is actively contributing to decarbonization! 🌱"""
    
    else:
        return """I'm here to help with your energy management questions! 

You can ask me about:
- Current energy status
- Daily savings and efficiency
- AI decisions and recommendations  
- Infrastructure upgrade options
- Energy optimization tips
- CO₂ impact and sustainability

This is a demo version. Add your Gemini API key to enable full AI functionality!"""


def init_chat_session():
    """Initialize chat session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def display_chat_history():
    """Display chat history."""
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.write(f"**You**: {message['content']}")
        else:
            st.info(f"**AI Assistant**: {message['content']}")


def add_message(role: str, content: str):
    """Add a message to the chat history."""
    st.session_state.messages.append({"role": role, "content": content})


def main():
    st.set_page_config(
        page_title="Decarbon AI Chat",
        page_icon="💬",
        layout="wide"
    )
    
    # Display import warning if needed
    if not GEMINI_AVAILABLE:
        st.warning(f"⚠️ Core modules not available: {IMPORT_ERROR}. Running in demo mode.")
    
    st.title("💬 Decarbon AI Assistant")
    st.markdown("Chat with the AI energy management assistant")
    
    # Initialize chat session
    init_chat_session()
    
    # Sidebar with system info
    with st.sidebar:
        st.header("System Status")
        
        # Get current state
        try:
            state = get_mock_system_state()
            
            st.metric("Solar Generation", f"{state['solar_kwh']:.1f} kWh")
            st.metric("Load Consumption", f"{state['load_kwh']:.1f} kWh")
            st.metric("Battery SOC", f"{state['battery_soc']:.1f}%")
            st.metric("Grid Price", f"€{state['grid_price']:.3f}/kWh")
            
            if state['current_decision']:
                st.info(f"**Latest AI Decision**: {state['current_decision']['action']}")
                st.caption(state['current_decision']['explanation'])
            
        except Exception as e:
            st.error("Unable to load system status")
        
        # Chat controls
        st.header("Chat Controls")
        
        if st.button("Clear Chat History"):
            st.session_state.messages.clear()
            st.rerun()
        
        # Chat statistics
        st.header("Chat Statistics")
        st.metric("Total Messages", len(st.session_state.messages))
        user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
        st.metric("User Messages", user_messages)
        st.metric("AI Responses", len(st.session_state.messages) - user_messages)
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Display chat history
        display_chat_history()
        
        # Chat input
        user_input = st.text_input("Ask me about energy management, system status, or get recommendations...", key="chat_input")
        if st.button("Send", key="send_button"):
            if user_input:
                # Add user message to chat
                add_message("user", user_input)
                st.write(f"**You**: {user_input}")
                
                # Get AI response
                with st.spinner("Thinking..."):
                    response = get_real_ai_response(user_input)
                    st.info(f"**AI Assistant**: {response}")
                    add_message("assistant", response)
    
    with col2:
        # Quick actions
        st.header("Quick Actions")
        
        quick_questions = [
            "What's the current energy status?",
            "What are today's energy savings?",
            "Show me the latest AI decisions",
            "What infrastructure upgrades do you recommend?",
            "How can I optimize energy usage?",
            "What's the CO₂ impact today?"
        ]
        
        for question in quick_questions:
            if st.button(question, key=f"quick_{question[:20]}"):
                # Add to chat
                add_message("user", question)
                st.write(f"**You**: {question}")
                
                # Get response
                with st.spinner("Thinking..."):
                    response = get_real_ai_response(question)
                    st.info(f"**AI Assistant**: {response}")
                    add_message("assistant", response)


if __name__ == "__main__":
    main() 