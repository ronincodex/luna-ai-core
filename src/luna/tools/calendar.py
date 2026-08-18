from .base import Tool
from typing import Dict, Any
import uuid

# In-memory store for mock events
_events = {}


class CalendarTool(Tool):
    def name(self) -> str:
        return "create_reminder"

    def description(self) -> str:
        return "Create a reminder or calendar event."

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "time": {
                    "type": "string",
                    "description": "Natural time like 'tomorrow 9 AM'",
                },
            },
        }

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        text = parameters.get("text", "")
        time = parameters.get("time", "now")
        event_id = str(uuid.uuid4())
        _events[event_id] = {"text": text, "time": time, "created_at": "now"}
        return {"event_id": event_id, "text": text, "time": time, "status": "created"}
