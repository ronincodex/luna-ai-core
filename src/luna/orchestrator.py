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
from luna.llm.client import OllamaClient
from luna.tools.weather import WeatherTool
from luna.tools.traffic import TrafficTool
from luna.tools.calendar import CalendarTool
from luna.tools.messaging import MessagingTool
from luna.permissions.gate import PermissionGate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tool registry
TOOLS = {
    "get_weather": WeatherTool(),
    "get_traffic": TrafficTool(),
    "create_reminder": CalendarTool(),
    "send_message": MessagingTool(),
}


class LunaOrchestrator:
    """
    This is the brain. Following protocols are followed:
        Step-1: Using Deterministic Routing (keyword matching)
        Step-2: Replacing the keyword matching with an LLM call for ambiguity.
    """

    def __init__(self):
        self.llm = OllamaClient()

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
            action_id = PermissionGate.create_action_id(state.pending_tool_call)
            state.action_id = action_id
            state.log_step(
                "PermissionGate",
                "BLOCKED_SENSITIVE",
                f"Action {action_id} requires confirmation.",
            )
            return state

        # Rule 5: If nothing matches, LLM must be called.
        logger.info("No Keyword match, calling LLM.")
        llm_response = self.llm.ask_for_tool(state.user_input)
        if llm_response is None:
            # LLM failed or didn't produce valid JSON
            state.status = "RESPONDING"
            state.final_response = (
                "I'm sorry, I couldn't understand that. Could you  rephrase?"
            )
            state.log_step(
                "Router", "LLM_FAILED", "LLM did not return a vlid response."
            )
            return state

        if llm_response.get("action") == "direct_answer":
            state.status = "RESPONDING"
            state.final_response = llm_response.get(
                "answer", "I'm not sure how to answer that."
            )
            state.log_step("Router", "DIRECT_ANSWER", "LLM chose direct answer.")
            return state

        if llm_response.get("action") == "tool_call":
            tool_name = llm_response.get("tool_name")
            params = llm_response.get("parameters", {})
            if tool_name not in TOOLS:
                state.status = "RESPONDING"
                state.final_response = f"I don't have a tool called {tool_name}."
                state.log_step("Router", "UNKNOWN_TOOL", f"Tool {tool_name} not found.")
                return state
            state.status = "EXECUTING"
            state.pending_tool_call = {"tool": tool_name, "parameters": params}
            state.log_step("Router", "ROUTED_TO_LLM_CALL", f"LLM chose {tool_name}.")
            return state

        # For Step 1, responding generically to test the loop.
        state.status = "RESPONDING"
        state.final_response = "I'm still learning. Could you try again?"
        state.log_step(
            "Router",
            "ROUTED_TO_GENERIC",
            "No keyword matched, falling back to generic response.",
        )
        return state

    def _executor(self, state: LunaState) -> LunaState:
        tool_name = state.pending_tool_call.get("tool")
        params = state.pending_tool_call.get("parameters", {})
        tool = TOOLS.get(tool_name)
        if not tool:
            state.status = "FAILED"
            state.final_repsonse = f"Tool {tool_name} not available."
            state.log_step(
                "Executor", "TOOL_NOT_FOUND", f"Tool {tool_name} not registered."
            )
            return state

        # Check if this tool requires confirmation already handled
        if PermissionGate.requires_confirmation(state.pending_tool_call):
            # Should have been caught earlier, but just in case
            state.status = "AWAITING_CONFIRMATION"
            state.log_step(
                "Executor",
                "MISSING_CONFIRMATION",
                "Sensitive tool called without confirmation.",
            )
            return state

        try:
            result = tool.execute(params)
            state.tool_result = str(result)
            state.status = "RESPONDING"
            # Generate a simple response; we'll let responder format nicely
            state.final_response = f"Executed {tool_name}. Result: {result}"
            state.log_step(
                "Executor", "EXECUTED", f"Tool {tool_name} executed successfully."
            )

        except Exception as e:
            state.status = "FAILED"
            state.final_response = f"Tool Executin failed: {str(e)}"
            state.log_step("Executor", "EXECUTION_FAILED", str(e))

        return state
        """This is Placeholder Executor (State 2 will implement real mocks)
        For Step 1, we just simulate success to close the loop.
        """
        # state.tool_result = "Mock execution successful."
        # state.status = "RESPONDING"
        # state.final_response = (
        # f"Executed {state.pending_tool_call['tool']}. Result: {state.tool_result}"
        # )
        # state.log_step("Executor", "EXECUTED_MOCK", "Placeholder execution for Step 1.")
        # return state

    """ Placeholder Responder (Step 2 will use LLM to neutralize)"""

    def _responder(self, state: LunaState) -> LunaState:
        # Step 1 just passes whatever we set in the router/executor.
        if not state.final_response:
            state.final_response = "Processing complete, but no response generated."
        state.status = "COMPLETE"
        state.log_step("Responder", "RESPONSE_READY", "Final response set.")
        return state

    # Methods to Execute confirmed action (for the confirmation endpoint)

    def execute_confirmed_action(self, state: LunaState, action_id: str) -> LunaState:
        """Execute a previously confirmed action directly without re-checking permissions."""
        tool_call = PermissionGate.confirm_action(action_id)
        if not tool_call:
            state.status = "FAILED"
            state.final_response = "Invalid or already confirmed action."
            state.log_step(
                "Executor",
                "INVALID_CONFIRMATION",
                f"Action {action_id} not found or already used.",
            )
            return state

        # Directly execute the tool (bypass permission check)
        tool_name = tool_call.get("tool")
        params = tool_call.get("parameters", {})
        tool = TOOLS.get(tool_name)
        if not tool:
            state.status = "FAILED"
            state.final_repsonse = f"Tool {tool_name} not available."
            state.log_step(
                "Executor", "TOOL_NOT_FOUND", f"Tool {tool_name} not registered."
            )
            return state

        try:
            result = tool.execute(params)
            state.tool_result = str(result)
            state.final_response = f"Executed {tool_name}. Result: {result}"
            state.status = "COMPLETE"
            state.log_step(
                "Executor",
                "CONFIRMED_EXECUTED",
                f"Confirmed tool {tool_name} executed successfully.",
            )
            PermissionGate.mark_executed(action_id)
        except Exception as e:
            state.status = "FAILED"
            state.final_response = f"Tool execution failed: {str(e)}"
            state.log_step("Executor", "CONFIRMED_EXECUTION_FAILED", str(e))

        return state
