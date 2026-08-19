"""Permission gate and confirmation manager."""

from typing import Dict, Any, Optional
import uuid
from datetime import datetime

# In-memory store for pending actions (we'll use SQLite in next module)
pending_actions = {}


class PermissionGate:
    @staticmethod
    def requires_confirmation(tool_call: Dict[str, Any]) -> bool:
        """Return True if the tool call is sensitive."""
        return tool_call.get("tool") == "send_message"

    @staticmethod
    def create_action_id(tool_call: Dict[str, Any]) -> str:
        """Generate a unique action ID and store the pending action."""
        action_id = str(uuid.uuid4())
        pending_actions[action_id] = {
            "tool_call": tool_call,
            "created_at": datetime.now(),
            "confirmed": False,
            "executed": False,
        }
        return action_id

    @staticmethod
    def confirm_action(action_id: str) -> Optional[Dict[str, Any]]:
        """Confirm and retrieve the tool call for execution."""
        if action_id not in pending_actions:
            return None
        entry = pending_actions[action_id]
        if entry["confirmed"]:
            return None  # Already confirmed
        entry["confirmed"] = True
        return entry["tool_call"]

    @staticmethod
    def mark_executed(action_id: str) -> bool:
        if action_id not in pending_actions:
            return False
        pending_actions[action_id]["executed"] = True
        return True

    @staticmethod
    def requires_confirmation(tool_call: Dict[str, Any]) -> bool:
        tool_name = tool_call.get("tool")
        return tool_name in ["send_message", "send_email"]  # Add send_email.
