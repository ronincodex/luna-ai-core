from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from luna.permissions.gate import PermissionGate
from luna.orchestrator import LunaOrchestrator
from luna.state import LunaState
from luna.proactive import ProactiveEngine
import uuid

app = FastAPI(title="Luna AI Core - UI Integration", version="0.1.0")

# --- 1. CORS (For local development if you run frontend separately) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active sessions (Short-term memory)
# In production, it's Redis. For the Proof Of Concept (POC), it's sufficient
sessions: dict[str, LunaState] = {}
orchestrator = LunaOrchestrator()


# Request/Response Models (Pydantic Models)
class ChatRequest(BaseModel):
    session_id: str | None = None  # If null, we create a new one.
    input: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    status: str
    audit_trail: list  # Exposing the audit trail directly in the API response!
    requires_confirmation: bool


class ConfirmRequest(BaseModel):
    action_id: str


class ConfirmResponse(BaseModel):
    session_id: str
    response: str
    status: str
    audit_trail: list


class ActionRequest(BaseModel):
    tool: str  # e.g., "create_reminder"
    params: dict  # e.g., {"text": "Call Mom", "time": "now"}


# --- 4. API Endpoints ---


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    The main entry point.
    Demonstrate: User -> Context -> Luna Brain -> Response.
    """

    # 1. Manage session
    if request.session_id is None or request.session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = LunaState(session_id=session_id)
    else:
        session_id = request.session_id

    state = orchestrator.process(session_id, request.input)
    sessions[session_id] = state

    return ChatResponse(
        session_id=session_id,
        response=state.final_response,
        status=state.status,
        audit_trail=[entry.model_dump(mode="json") for entry in state.audit_trail],
        requires_confirmation=(state.status == "AWAITING_CONFIRMATION"),
    )


@app.post("/confirm/{session_id}", response_model=ConfirmResponse)
async def confirm(session_id: str, req: ConfirmRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    state = sessions[session_id]
    # Execute the confirmed action
    state = orchestrator.execute_confirmed_action(state, req.action_id)
    sessions[session_id] = state
    return ConfirmResponse(
        session_id=session_id,
        response=state.final_response,
        status=state.status,
        audit_trail=[entry.model_dump(mode="json") for entry in state.audit_trail],
    )


# @app.get(
# 2. Run the Orchestrator
# orchestrator = LunaOrchestrator()
# Passing the 'existing' state in order to maintain conversation History.
# Currently creating a fresh state per request to keep it simple
# Later, loading the existing state from 'session[session_id]'.
# state = orchestrator.process(session_id, request.input)

# 3. Store the updated state back (for short-term memory later)
# sessions[session_id] = state

# 4. Build the response
# Problem statement mentions to distinguish action states.
# requires_conf = state.status == "AWAITING_CONFIRMATION"

# Flatterning the audit trail for JSON serialization
# audit_logs = [entry.model_dump(mode="json") for entry in state.audit_trail]

# return ChatResponse(
# session_id=session_id,
# response=state.final_response,
# status=state.status,
# audit_trail=audit_logs,
# requires_confirmation=requires_conf,
# j)

# from luna.proactive import ProactiveEngine


@app.post("/action")
async def quick_action(session_id: str | None, req: ActionRequest):
    """
    Bypass the router/LLM for UI quick actions (Blazing fast: < 100ms).
    For sensitive tools (send_message, send_email), we still need confirmation.
    """
    if session_id is None or session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = LunaState(session_id=session_id)

    state = sessions[session_id]

    # Check if the requested tool is sensitive
    tool_call = {"tool": req.tool, "parameters": req.params}
    if PermissionGate.requires_confirmation(tool_call):
        # Generate action_id and store pending action
        action_id = PermissionGate.create_action_id(tool_call)
        state.action_id = action_id
        state.status = "AWAITING_CONFIRMATION"
        state.pending_tool_call = tool_call

        # Log the permission block
        state.log_step(
            "PermissionGate",
            "BLOCKED_SENSITIVE",
            f"Action {action_id} requires confirmation.",
        )
        sessions[session_id] = state
        return {
            "session_id": session_id,
            "response": "",
            "status": "AWAITING_CONFIRMATION",
            "action_id": action_id,
            "audit_trail": [
                entry.model_dump(mode="json") for entry in state.audit_trail
            ],
            "requires_confirmation": True,
        }
    else:

        # Non-sensitive: execute directly
        state.pending_tool_call = tool_call
        state = orchestrator._executor(state)
        sessions[session_id] = state
        return {
            "session_id": session_id,
            "response": state.final_response,
            "status": state.status,
            "audit_trail": [
                entry.model_dump(mode="json") for entry in state.audit_trail
            ],
            "requires_confirmation": False,
        }


@app.post("/event")
async def handle_event(event: dict):
    user_id = event.get("user_id", "default")
    event_type = event.get("type")
    if event_type == "traffic":
        result = ProactiveEngine.evaluate_traffic_event(
            user_id, event.get("severity", "moderate"), event.get("context", {})
        )
        if result.get("notify"):
            # In real app, push notification; here just log and return
            return {"notified": True, "message": result["message"]}
        else:
            return {"notified": False, "reason": result.get("reason", "Not relevant")}

    return {"error": "Unknown event type"}


# Health check for Docker/Kubernetes
@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Serve Static UI (Must be at the end) ---
app.mount("/", StaticFiles(directory="static", html=True), name="static")
