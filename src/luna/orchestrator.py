"""The custom State Machine.
1. The process() method, takes the user input and creates a fresh LunaState
2. The while loop is the Agentic Graph. Rather than using LangGraph, controlling the flow explicitly. It only moves if the state is ROUTING, EXECUTING or RESPONDING.
3. The _router() is the 'Product Thinking' method. To save the CPU resources because LLM is running locally with (4-6) tokens/seconds, saving the LLM call on obvious intents. Will be using if/elif checks and adding deterministic code where an LLM adds no value.
4. In the Permission gate, send_message sets state.status = "AWAITING_CONFIRMATION" and breaks the loop.
5. The fail-Safe, the loop breaks after 10 iterations. This prevents infinite loops if the state machine misbehaves4. In the Permission gate, send_message sets state.status = "AWAITING_CONFIRMATION" and breaks the loop.
5. The fail-Safe, the loop breaks after 10 iterations. This prevents infinite loops if the state machine misbehaves4. In the Permission gate, send_message sets state.status = "AWAITING_CONFIRMATION" and breaks the loop.
5. The fail-Safe, the loop breaks after 10 iterations. This prevents infinite loops if the state machine misbehaves.
"""

from luna.state import LunaState
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LunaOrchestrator:
    """
    This is the brain. Following protocols are followed:
        Step-1: Using Deterministic Routing (keyword matching)
        Step-2: Replacing the keyword matching with an LLM call for ambiguity.
    """

    def process(self, session_id: str, user_input: str) -> LunaState:
        # Step 1. Initialize the state
        state = LunaState(session_id=session_id, user_input=user_input)
        state.log_step("Orchestrator", "INIT", "State initialized for new input.")

        # Step 2: The State Loop(The Engine)
        # Loops are done until the status is COMPLETE, AWAITING_CONFIRMATION, or FAILED.
        while state.status not in ["COMPLETE", "AWAITING_CONFIRMATION", "FAILED"]:

            if state.status == "ROUTING":
                state = self._router(state)

            elif state.status == "EXECUTING":
                state = self._executor(state)  # Build it in future modules

            elif state.status == "RESPONDING":
                state = self._responder(state)  # Build it in future modules

            # Safety break to prevent infinite loops
            if len(state.audit_trail) > 10:
                state.status = "FAILED"
                state.final_response = "I'm stuck in a loop, Please try again."
                state.log_step(
                    "Orchestrator", "FAIL_SAFE", "Exceeded max state transitions."
                )
                break

        return state

    def _router(self, state: LunaState) -> LunaState:
        """
        This is The Router (Step-1: Deterministic).
        It determines what to do based on the keywords. This saves massive CPU/RAM because we don't want to call the slow LLM for easy stuff.
        """

        input_lower = state.user_input.lower()

        # Rule 1: Weather
        if any(
            keyword in input_lower
            for keyword in ["weather", "rain", "umbrella", "temperature"]
        ):
            state.status = "EXECUTING"
            state.pending_tool_call = {
                "tool": "get_weather",
                "parameters": {"location": "home", "date": "tomorrow"},
            }
            state.log_step("Router", "ROUTED_TO_WEATHER", "Keyword 'weather' detected.")
            return state

        # Rule 2: Reminder / Calendar
        if any(
            keyword in input_lower
            for keyword in ["remind", "remainder", "calender", "meeting"]
        ):
            state.status = "EXECUTING"
            state.pending_tool_call = {
                "tool": "create_reminder",
                "parameters": {"text": state.user_input, "time": "tomorrow 9 AM"},
            }
            state.log_step("Router", "ROUTED_TO_CALENDER", "Keyword 'remind' detected.")
            return state

        # Rule 3: Traffic / Travel
        if any(
            keyword in input_lower
            for keyword in ["traffic", "leave", "reach", "office"]
        ):
            state.status = "EXECUTING"
            state.pending_tool_call = {
                "tool": "get_traffic",
                "parameters": {"route": "home_to_office", "arrival_time": "09:30 AM"},
            }
            state.log_step(
                "Router", "ROUTED_TO_TRAFFIC", "Keyword 'traffic' or 'office' detected."
            )
            return state

        # Rule 4: Messaging / Email (Sensitive Action)
        if any(
            keyword in input_lower
            for keyword in ["send", "message", "email", "tell mom"]
        ):
            state.status = "AWAITING_CONFIRMATION"  # The Permission Gate
            state.pending_tool_call = {
                "tool": "send_message",
                "parameters": {"recipient": "Mom", "content": state.user_input},
            }
            state.log_step(
                "PermissionGate",
                "BLOCKED_SENSITIVE",
                "Messaging requires user confirmation.",
            )
            return state

        # Rule 5: If nothing matches, LLM must be called.
        # For Step 1, responding generically to test the loop.
        state.status = "RESPONDING"
        state.final_response = (
            f"I heard you say: '{state.user_input}'. I'm still learning to handle that."
        )
        state.log_step(
            "Router",
            "ROUTED_TO_GENERIC",
            "No keyword matched, falling back to generic response.",
        )
        return state

    def _executor(self, state: LunaState) -> LunaState:
        """This is Placeholder Executor (State 2 will implement real mocks)
        For Step 1, we just simulate success to close the loop.
        """
        state.tool_result = "Mock execution successful."
        state.status = "RESPONDING"
        state.final_response = (
            f"Executed {state.pending_tool_call['tool']}. Result: {state.tool_result}"
        )
        state.log_step("Executor", "EXECUTED_MOCK", "Placeholder execution for Step 1.")
        return state

    """ Placeholder Responder (Step 2 will use LLM to neutralize)"""

    def _responder(self, state: LunaState) -> LunaState:
        # Step 1 just passes whatever we set in the router/executor.
        if not state.final_response:
            state.final_response = "Processing complete, but no response generated."
        state.status = "COMPLETE"
        state.log_step("Responder", "RESPONSE_READY", "Final response set.")
        return state
