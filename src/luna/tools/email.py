from .base import Tool
from typing import Dict, Any
import uuid


class EmailTool(Tool):
    def name(self) -> str:
        return "send_email"

    def description(self) -> str:
        return "Send an email to a recipient."

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "recipient": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
        }

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "sent",
            "recipient": parameters.get("recipient"),
            "subject": parameters.get("subject"),
            "body": parameters.get("body"),
            "message_id": str(uuid.uuid4()),
        }
