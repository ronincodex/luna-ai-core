from .base import Tool
from typing import Dict, Any
import random


class TrafficTool(Tool):
    def name(self) -> str:
        return "get_traffic"

    def description(self) -> str:
        return "Get estimated travel time for a route."

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "route": {
                    "type": "string",
                    "enum": ["home_to_office", "office_to_home"],
                },
                "arrival_time": {"type": "string", "description": "HH:MM AM/PM"},
            },
        }

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        route = parameters.get("route", "home_to_office")
        # Mock: base travel time 30 min + random delay
        base = 30 if route == "home_to_office" else 25
        delay = random.randint(0, 30)
        total = base + delay
        return {
            "route": route,
            "travel_time_minutes": total,
            "delay_minutes": delay,
            "traffic_level": (
                "heavy" if delay > 20 else "moderate" if delay > 10 else "light"
            ),
        }
