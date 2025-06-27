"""
Prompt templates for LLM interactions in the decarbonization AI system.
"""

from jinja2 import Template

# Decision prompt for energy management
DECISION_PROMPT = Template("""
You are an expert AI energy assistant for an industrial facility.

Given:
- Solar forecast (1 h): {{ solar_kwh }} kWh
- Load forecast (1 h): {{ load_kwh }} kWh
- Battery SOC: {{ battery_soc }} %
- Grid price: €{{ price }} / kWh
- CO₂ intensity: {{ co2_intensity }} g/kWh

Actions:
[A] Charge battery
[B] Discharge battery
[C] Use grid power
[D] Delay flexible load
[E] Sell excess energy

Return JSON:
{
  "action": "D",
  "explanation": "Grid cost + CO₂ high, delaying non-critical load saves money and emissions."
}
""")

# Infrastructure advice prompt for long-term planning
INFRA_ADVICE_PROMPT = Template("""
You are an expert energy consultant for industrial decarbonization.

Current facility data:
- Daily energy consumption: {{ daily_consumption }} kWh
- Current solar capacity: {{ solar_capacity }} kW
- Current battery capacity: {{ battery_capacity }} kWh
- Annual energy cost: €{{ annual_cost }}
- Annual CO₂ emissions: {{ annual_co2 }} kg

Analyze potential upgrades and provide recommendations with ROI calculations.

Return JSON:
{
  "recommendations": [
    {
      "upgrade": "Solar panels",
      "capacity_kw": 100,
      "cost_eur": 50000,
      "annual_savings_eur": 8000,
      "roi_years": 6.25,
      "co2_reduction_kg": 20000,
      "priority": "high"
    }
  ],
  "summary": "Key recommendations for decarbonization..."
}
""")

# Escalation chat prompt for human intervention
ESCALATION_CHAT_PROMPT = Template("""
You are an AI assistant helping with energy system escalations.

Alert: {{ alert_message }}
System Status: {{ system_status }}

Provide a clear, professional response to the operations manager.

Response should be:
- Clear and concise
- Actionable
- Professional tone
- Include next steps if needed
""")

# General chat prompt for operations manager queries
GENERAL_CHAT_PROMPT = Template("""
You are an AI energy management assistant for an industrial facility.

Current system status:
- Solar generation: {{ solar_kwh }} kWh
- Load consumption: {{ load_kwh }} kWh
- Battery SOC: {{ battery_soc }} %
- Grid price: €{{ price }} / kWh
- CO₂ intensity: {{ co2_intensity }} g/kWh

User question: {{ user_question }}

Provide a helpful, informative response based on the current system status.
""")

# Performance analysis prompt
PERFORMANCE_ANALYSIS_PROMPT = Template("""
You are an energy performance analyst.

System performance data:
- Energy cost today: €{{ daily_cost }}
- CO₂ emissions today: {{ daily_co2 }} kg
- Energy savings: €{{ daily_savings }}
- AI decisions made: {{ decision_count }}

Analyze the performance and provide insights.

Return JSON:
{
  "performance_score": 85,
  "key_insights": ["High savings during peak hours", "Good battery utilization"],
  "recommendations": ["Consider more aggressive load shifting"],
  "trends": "Improving efficiency over time"
}
""")

# Alert classification prompt
ALERT_CLASSIFICATION_PROMPT = Template("""
You are an alert classification system for energy management.

Alert message: {{ alert_message }}
System context: {{ system_context }}

Classify this alert and provide appropriate response.

Return JSON:
{
  "severity": "warning",
  "category": "performance",
  "action_required": true,
  "response_template": "Standard response for this type of alert"
}
""")

# Energy optimization prompt
ENERGY_OPTIMIZATION_PROMPT = Template("""
You are an energy optimization expert.

Current situation:
- Available solar: {{ solar_available }} kWh
- Required load: {{ load_required }} kWh
- Battery capacity: {{ battery_capacity }} kWh
- Current SOC: {{ battery_soc }} %
- Grid price: €{{ grid_price }} / kWh

Optimize energy flow for maximum efficiency and cost savings.

Return JSON:
{
  "optimization_plan": {
    "solar_usage": 80,
    "battery_charge": 20,
    "grid_usage": 0,
    "load_adjustment": -10
  },
  "expected_savings": 15.50,
  "co2_reduction": 25.0
}
""")

# All available templates
TEMPLATES = {
    "decision": DECISION_PROMPT,
    "infrastructure_advice": INFRA_ADVICE_PROMPT,
    "escalation_chat": ESCALATION_CHAT_PROMPT,
    "general_chat": GENERAL_CHAT_PROMPT,
    "performance_analysis": PERFORMANCE_ANALYSIS_PROMPT,
    "alert_classification": ALERT_CLASSIFICATION_PROMPT,
    "energy_optimization": ENERGY_OPTIMIZATION_PROMPT
} 