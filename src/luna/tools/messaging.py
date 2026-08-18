from .base import Tool
from typing import Dict, Any
import uuid


class MessagingTool(Tool):
    def name(self) -> str:
        return "send_message"

    def description(self) -> str:
        return "Send a message to a receipient, Requires explicit user confirmation."

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "recipient": {"type": "string"},
                "content": {"type": "string"},
            },
        }

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        recipient = parameters.get("recipient", "")
        content = parameters.get("content", "")

        # Mock sending
        return {
            "status": "sent",
            "recipient": recipient,
            "content": content,
            "message_id": str(uuid.uuid4()),
        }
