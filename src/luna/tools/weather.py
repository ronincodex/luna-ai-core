from .base import Tool
from typing import Dict, Any
import random
from datetime import datetime, timedelta


class WeatherTool(Tool):
    def name(self) -> str:
        return "get_weather"

    def description(self) -> str:
        return "Get weather forecast for a given location and date."

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD or 'tomorrow'"},
            },
        }

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        location = parameters.get("location", "home")
        date_str = parameters.get("date", "tomorrow")

        # Mock forecast
        temp = random.randint(15, 35)
        condition = random.choice(["sunny", "cloudy", "rainy", "partly cloudy"])
        return {
            "location": location,
            "date": date_str,
            "temperature": temp,
            "condition": condition,
            "humidity": random.randint(40, 80),
            "wind_speed": random.randint(5, 20),
        }

        # If the date is "invalid", raise an error
        if parameters.get("date") == "invalid":
            raise Exception("Weather service unavailable for the requested date.")
