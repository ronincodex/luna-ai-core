"""Defining all Data Structures
The status field allow the model to run a while loop over these states. The audit_trail fullfills the condition of maintaining structured logs/state sufficient to understand what Luna decides and why
"""

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

# 1. Audit Entry: This is the Debuggable State.
# Every decision that is made by Luna will be stored here.


class AuditEntry(BaseModel):
    timestamp: datetime = datetime.now()
    node: str  # e.g., "ROUTED-TO-WEATHER", "BLOCK-ACTION"
    reason: str


# 2. State Definition: The State Object travels through the whole pipeline.
class LunaState(BaseModel):
    session_id: str

    # The user's current input
    user_input: str = ""

    memories: Dict[str, str] = {}

    # Extra field during Phase-2 implementation
    action_id: Optional[str] = None  # For pending confirmation actions

    # The current step in the state machine
    status: Literal[
        "ROUTING",  # Deciding what to do.
        "FETCHING_MEMORY",
        "FETCHING",  # To be implementd.
        "EXECUTING",  # Running a tool.
        "AWAITING_CONFIRMATION",  # Sensitive action needs a 'Yes'.
        "RESPONDING",  # Generating the final reply
        "COMPLETE",  # Done
        "FAILED",  # Something went wrong
    ] = "ROUTING"

    # Short-term memory (current conversation buffer)
    messages: List[Dict[str, str]] = []

    # Long-term memory (user profile). Gets loaded from SQLite later.
    user_profile: Dict[str, Any] = {
        "user_name": "Saurabh",
        "timezone": "Asia/Kolkata",
        "luna_name": "Luna",
        "prefrences": {},
    }

    memories: Dict[str, str] = {}

    # Planned tools to call (set by Router, used by Executor)
    pending_tool_call: Optional[Dict[str, Any]] = None

    # Result returned by the tool
    tool_result: Optional[str] = None

    # The final response to send back to the user
    final_response: str = ""

    # The Audit Trail (Requirement: "Debuggable State")
    audit_trail: List[AuditEntry] = []

    # Helper function to log every step
    def log_step(self, node: str, decision: str, reason: str):
        self.audit_trail.append(AuditEntry(node=node, decision=decision, reason=reason))
