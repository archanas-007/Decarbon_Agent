"""
Gemini LLM integration for the decarbonization AI system.
"""

import google.generativeai as genai
import json
import asyncio
from typing import Dict, Any, Optional, List
from jinja2 import Template
import os
from dotenv import load_dotenv

from core.logger import logger

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables")
    GEMINI_API_KEY = "your-api-key-here"  # Placeholder for development

genai.configure(api_key=GEMINI_API_KEY)


class GeminiClient:
    """Client for interacting with Google's Gemini LLM."""
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        self._conversation = None
    
    async def generate_response(self, prompt: str, temperature: float = 0.1) -> str:
        """Generate a response from Gemini."""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=2048,
                )
            )
            
            if response.text:
                await logger.log_llm_call(prompt, response.text, "gemini")
                return response.text
            else:
                await logger.log_error("Empty response from Gemini", "gemini")
                return ""
                
        except Exception as e:
            await logger.log_error(f"Error calling Gemini: {e}", "gemini", e)
            return ""
    
    async def generate_json_response(self, prompt: str, temperature: float = 0.1) -> Optional[Dict[str, Any]]:
        """Generate a JSON response from Gemini."""
        try:
            # Add JSON formatting instruction to prompt
            json_prompt = f"{prompt}\n\nPlease respond with valid JSON only."
            
            response_text = await self.generate_response(json_prompt, temperature)
            
            if not response_text:
                return None
            
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                await logger.log_error("No JSON found in response", "gemini")
                return None
                
        except json.JSONDecodeError as e:
            await logger.log_error(f"Invalid JSON response: {e}", "gemini", e)
            return None
        except Exception as e:
            await logger.log_error(f"Error parsing JSON response: {e}", "gemini", e)
            return None
    
    def start_conversation(self) -> None:
        """Start a new conversation."""
        self._conversation = self.model.start_chat(history=[])
    
    async def chat_response(self, message: str) -> str:
        """Send a message in an ongoing conversation."""
        if not self._conversation:
            self.start_conversation()
        
        try:
            response = await asyncio.to_thread(
                self._conversation.send_message,
                message
            )
            
            if response.text:
                await logger.log_llm_call(message, response.text, "gemini_chat")
                return response.text
            else:
                return ""
                
        except Exception as e:
            await logger.log_error(f"Error in chat: {e}", "gemini", e)
            return ""


class PromptBuilder:
    """Builds prompts using Jinja2 templates."""
    
    def __init__(self):
        self.templates: Dict[str, Template] = {}
    
    def add_template(self, name: str, template_str: str) -> None:
        """Add a Jinja2 template."""
        self.templates[name] = Template(template_str)
    
    def render_template(self, name: str, **kwargs) -> str:
        """Render a template with given variables."""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        
        return self.templates[name].render(**kwargs)
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())


class LLMOrchestrator:
    """Orchestrates LLM interactions for the decarbonization system."""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.prompt_builder = PromptBuilder()
        self._setup_default_templates()
    
    def _setup_default_templates(self) -> None:
        """Setup default prompt templates."""
        
        # Decision prompt template
        decision_template = """
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
"""
        self.prompt_builder.add_template("decision", decision_template)
        
        # Infrastructure advice template
        advice_template = """
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
"""
        self.prompt_builder.add_template("infrastructure_advice", advice_template)
        
        # Escalation chat template
        escalation_template = """
You are an AI assistant helping with energy system escalations.

Alert: {{ alert_message }}
System Status: {{ system_status }}

Provide a clear, professional response to the operations manager.

Response should be:
- Clear and concise
- Actionable
- Professional tone
- Include next steps if needed
"""
        self.prompt_builder.add_template("escalation_chat", escalation_template)
    
    async def make_decision(self, solar_kwh: float, load_kwh: float, battery_soc: float, 
                           price: float, co2_intensity: float) -> Optional[Dict[str, Any]]:
        """Make an energy management decision."""
        prompt = self.prompt_builder.render_template("decision", 
                                                   solar_kwh=solar_kwh,
                                                   load_kwh=load_kwh,
                                                   battery_soc=battery_soc,
                                                   price=price,
                                                   co2_intensity=co2_intensity)
        
        return await self.gemini_client.generate_json_response(prompt)
    
    async def get_infrastructure_advice(self, daily_consumption: float, solar_capacity: float,
                                      battery_capacity: float, annual_cost: float, 
                                      annual_co2: float) -> Optional[Dict[str, Any]]:
        """Get infrastructure upgrade recommendations."""
        prompt = self.prompt_builder.render_template("infrastructure_advice",
                                                   daily_consumption=daily_consumption,
                                                   solar_capacity=solar_capacity,
                                                   battery_capacity=battery_capacity,
                                                   annual_cost=annual_cost,
                                                   annual_co2=annual_co2)
        
        return await self.gemini_client.generate_json_response(prompt)
    
    async def handle_escalation(self, alert_message: str, system_status: str) -> str:
        """Handle escalation with professional response."""
        prompt = self.prompt_builder.render_template("escalation_chat",
                                                   alert_message=alert_message,
                                                   system_status=system_status)
        
        return await self.gemini_client.generate_response(prompt)
    
    async def chat_response(self, message: str) -> str:
        """Get a chat response for general queries."""
        return await self.gemini_client.chat_response(message)


# Global LLM orchestrator instance
llm_orchestrator = LLMOrchestrator() 