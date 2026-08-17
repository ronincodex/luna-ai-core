from fastapi import FastAPI
from pydantic import BaseModel
from luna.orchestrator import LunaOrchestrator
from luna.state import LunaState
import uuid

app = FastAPI(title="Luna AI Core - Step 1", version="0.1.0")

# In-memory store for active sessions (Short-term memory)
# In production, it's Redis. For the Proof Of Concept (POC), it's sufficient
sessions: dict[str, LunaState] = {}


# Request/Response Models
class ChatRequest(BaseModel):
    session_id: str | None = None  # If null, we create a new one.
    input: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    status: str
    audit_trail: list  # Exposing the audit trail directly in the API response!
    requires_confirmation: bool


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

    # 2. Run the Orchestrator
    orchestrator = LunaOrchestrator()
    # Passing the 'existing' state in order to maintain conversation History.
    # Currently creating a fresh state per request to keep it simple
    # Later, loading the existing state from 'session[session_id]'.
    state = orchestrator.process(session_id, request.input)

    # 3. Store the updated state back (for short-term memory later)
    sessions[session_id] = state

    # 4. Build the response
    # Problem statement mentions to distinguish action states.
    requires_conf = state.status == "AWAITING_CONFIRMATION"

    # Flatterning the audit trail for JSON serialization
    audit_logs = [entry.model_dump(mode="json") for entry in state.audit_trail]

    return ChatResponse(
        session_id=session_id,
        response=state.final_response,
        status=state.status,
        audit_trail=audit_logs,
        requires_confirmation=requires_conf,
    )


# Health check for Docker/Kubernetes
@app.get("/health")
async def health():
    return {"status": "ok"}
