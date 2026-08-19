from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProactiveEngine:
    @staticmethod
    def evaluate_traffic_event(user_id: str, severity: str, context: dict) -> dict:
        """Return dict with 'notify' and 'message' if relevant, else {'notify': False}"""
        # Hardcoded rules for POC
        if severity.lower() != "severe":
            return {"notify": False, "reason": "Severity not severe"}
        # Check if user has a meeting in the next hour (simplified)
        # In production, fetch from calendar tool
        if context.get("meeting_soon", False):
            return {
                "notify": True,
                "message": "Severe traffic on your route. Consider leaving 20 minutes early.",
            }
        return {"notify": False, "reason": "No immediate meeting"}
