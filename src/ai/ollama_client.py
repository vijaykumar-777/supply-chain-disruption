import requests
import json
import logging
from typing import Dict, Any, List
from src.config import OLLAMA_API_URL, OLLAMA_MODEL
from pathlib import Path

logger = logging.getLogger(__name__)

class AIAdvisor:
    """Ollama AI Client for generating insights and recommendations."""
    
    def __init__(self):
        self.api_url = OLLAMA_API_URL
        self.model = OLLAMA_MODEL
        self.feedback_file = Path("data/feedback_loop.json")
        self._ensure_feedback_file()
        
    def _ensure_feedback_file(self):
        """Ensure local feedback storage exists."""
        self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.feedback_file.exists():
            with open(self.feedback_file, 'w') as f:
                json.dump([], f)

    def generate_recommendation(self, event: Dict[str, Any], sim_results: Dict[str, Any], alt_route: List[str] = None) -> str:
        """
        Generate human-readable insights based on disruption data and simulation.
        PREDICT-02 & AI-02.
        """
        prompt = f"""
        You are a seasoned Supply Chain Logistics Analyst.
        
        A disruption has occurred:
        Event: {event.get('title', 'Unknown Disruption')}
        Category: {event.get('category', 'N/A')}
        Affected Locations: {', '.join(event.get('locations', []))}
        
        Our Monte Carlo simulation projects the impact on the current optimal route as follows:
        - Expected Delay (Mean): {sim_results.get('mean_days', 0):.1f} days
        - Worst Case Scenario: {sim_results.get('max_risk_days', 0):.1f} days
        
        Alternative Route Suggested by our Pathfinding Engine:
        """
        
        if alt_route:
            prompt += f"{' -> '.join(alt_route)}\n\n"
            prompt += "Based on this, what immediate 3-step action plan do you recommend to logistics managers? Keep it concise, professional, and actionable."
        else:
            prompt += "NONE AVAILABLE. The network is completely blocked.\n\n"
            prompt += "What emergency contingency actions should management take to secure inventory and mitigate the impact? Keep it concise and professional."

        logger.info(f"Sending prompt to local Ollama ({self.model})...")
        
        try:
            response = requests.post(self.api_url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2 # Keep it analytical and grounded
                }
            }, timeout=30)
            
            response.raise_for_status()
            data = response.json()
            return data.get("response", "No recommendation generated.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to local Ollama instance: {e}")
            return "WARNING: Local AI Assistant (Ollama) is unavailable or timing out. Please ensure Ollama is running and the Mistral model is downloaded."

    def submit_feedback(self, recommendation_id: str, rating: int, comment: str = ""):
        """
        Store user feedback (+1 / -1) on AI recommendations to track strategy efficacy. AI-03.
        """
        feedback = {
            "id": recommendation_id,
            "rating": rating,  # e.g. 1 for helpful, -1 for unhelpful
            "comment": comment
        }
        
        try:
            with open(self.feedback_file, 'r') as f:
                data = json.load(f)
            
            data.append(feedback)
            
            with open(self.feedback_file, 'w') as f:
                json.dump(data, f, indent=4)
                
            return True
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
            return False
