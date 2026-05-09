import requests
import json
import logging
import os
from typing import Dict, Any, List
from src.config import OLLAMA_API_URL, OLLAMA_MODEL
from pathlib import Path

logger = logging.getLogger(__name__)

class AIAdvisor:
    """Ollama AI Client for generating insights and recommendations."""
    
    def __init__(self):
        self.api_url = OLLAMA_API_URL
        self.model = OLLAMA_MODEL
        self.timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "12"))
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
            }, timeout=self.timeout_seconds)
            
            response.raise_for_status()
            data = response.json()
            return data.get("response", "No recommendation generated.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to local Ollama instance: {e}")
            return "WARNING: Local AI Assistant (Ollama) is unavailable or timing out. Please ensure Ollama is running and the Mistral model is downloaded."

    def generate_route_analysis(
        self,
        source_hospital: Dict[str, Any],
        target_hospital: Dict[str, Any],
        recommended_route: Dict[str, Any],
        alternatives: List[Dict[str, Any]],
        active_alerts: List[Dict[str, Any]],
        blocked_routes: int,
    ) -> str:
        """Ask Ollama for concise alternate route guidance for hospital transfers."""
        alternate_lines = []
        for idx, route in enumerate(alternatives, start=1):
            names = [item.get("hospital_name", item.get("hospital_id", "")) for item in route.get("path_details", [])]
            alternate_lines.append(
                f"{idx}. {route.get('strategy', 'route')}: {' -> '.join(names)} "
                f"({route.get('total_distance_km', 0)} km, {route.get('total_time_minutes', 0)} min, "
                f"danger {route.get('max_danger_level', 0)})"
            )

        alert_lines = [
            f"- {alert.get('disaster_type')} near {alert.get('location_name')}, {alert.get('district')} "
            f"(severity {alert.get('severity')}, radius {alert.get('affected_radius_km')} km)"
            for alert in active_alerts[:8]
        ]

        recommended_names = [
            item.get("hospital_name", item.get("hospital_id", "")) for item in recommended_route.get("path_details", [])
        ]

        prompt = f"""
You are an emergency hospital supply-chain route planner for Karnataka, India.

SOURCE:
- {source_hospital.get('hospital_name')} in {source_hospital.get('district')}
- Available beds: {source_hospital.get('available_beds')}
- Oxygen: {source_hospital.get('oxygen_available')}

TARGET:
- {target_hospital.get('hospital_name')} in {target_hospital.get('district')}
- Available beds: {target_hospital.get('available_beds')}
- Oxygen: {target_hospital.get('oxygen_available')}

RECOMMENDED ROUTE:
{' -> '.join(recommended_names)}
- Strategy: {recommended_route.get('strategy')}
- Distance: {recommended_route.get('total_distance_km')} km
- Time: {recommended_route.get('total_time_minutes')} minutes
- Max danger: {recommended_route.get('max_danger_level')}
- Blocked segments on recommended route: {recommended_route.get('blocked_segments', 0)}

ALTERNATE ROUTES:
{chr(10).join(alternate_lines) if alternate_lines else 'No alternate route available.'}

ACTIVE DISASTERS:
{chr(10).join(alert_lines) if alert_lines else 'No active disaster alerts.'}

Network-wide blocked routes: {blocked_routes}

Give a concise 4-sentence recommendation:
1. Say whether the recommended route is acceptable now.
2. Name the best alternate route strategy if conditions worsen.
3. Mention the main disaster risk.
4. Give one operational action for dispatchers.
"""

        logger.info("Sending hospital route prompt to local Ollama (%s)...", self.model)

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.25},
                },
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()
            data = response.json()
            return data.get("response", "No route analysis generated.")
        except requests.exceptions.RequestException as e:
            logger.error("Failed to connect to local Ollama instance: %s", e)
            return "AI route suggestions are unavailable because Ollama is not responding. Start Ollama locally to receive alternate-route guidance."

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
