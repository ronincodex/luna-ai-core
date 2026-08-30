# Luna AI Core – Personalized Virtual Assistant (POC)

**Luna** is a proof‑of‑concept AI orchestration layer for a voice‑first, permission‑aware personal assistant.  
It combines deterministic routing, a local LLM (Ollama), mock tools, long‑term memory, a robust permission gate, and a fully integrated UI.

---

## Table of Contents

1. [Features](#features)
2. [Quick Start](#quick-start)
   - [Local Development](#1-local-development)
   - [Docker Deployment](#2-docker-deployment)
3. [Architecture](#architecture)
4. [Test Scenarios](#test-scenarios)
5. [Demo Video](#demo-video)
6. [Production Roadmap](#production-roadmap)
7. [Limitations](#limitations)
8. [License & Acknowledgements](#license--acknowledgements)

---

## Features

- **Natural language understanding** – via Qwen2.5:7b (CPU‑only, local)
- **Five mock tools** – Weather, Traffic, Calendar, Messaging, Email
- **Permission Gate** – sensitive actions require explicit user confirmation (two‑phase commit)
- **Short‑term** (session) and **long‑term** (SQLite) memory
- **Proactive event** handling – traffic alerts with intelligent "stay quiet" logic
- **Full audit trail** – every decision is logged and returned in the API response
- **Integrated UI** – voice‑ready chat interface (Web Speech API) with quick actions
- **Instant cache** – common questions answered without LLM inference (< 50ms)
- **Dockerized** – one‑command deployment

---

## Quick Start

### 1. Local Development

```bash
# Clone the repository
git clone https://github.com/ronincodex/luna-ai-core.git
cd luna-ai-core

# Create and activate Conda environment
conda create -n luna-env python=3.12 -y
conda activate luna-env

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Start Ollama (must be bound to 0.0.0.0 for Docker)
OLLAMA_HOST=0.0.0.0 OLLAMA_VULKAN=0 OLLAMA_GPU_OVERRIDE=0 OLLAMA_MODELS="$HOME/.ollama/models" ollama serve

# In another terminal, start the FastAPI server
uvicorn luna.main:app --reload --host 0.0.0.0 --port 8000
Now open your browser and go to http://localhost:8000 to see the UI.

# 2. Docker Deployment
λbash
# Build and run
docker compose build
docker compose up -d

# Check health
curl http://localhost:8000/health

# Stop
docker compose down
Note: Ensure Ollama is running on the host with OLLAMA_HOST=0.0.0.0 for Docker connectivity.

# Architecture
Luna is built as a finite state machine with explicit states:
ROUTING → EXECUTING → AWAITING_CONFIRMATION → RESPONDING → COMPLETE / FAILED

Every transition is logged to the audit_trail, providing full provenance.

Data Flow:

text
User → Router → Memory (load) → LLM / Deterministic → Permission Gate → Tool → Response
Architecture Diagrams
luna-architecture.png

luna-architecture.svg

# Mermaid Diagram
```graph TD
    User[User] --> Router[Router]
    Router --> Memory[(Memory)]
    Memory --> LLM{LLM}
    LLM --> Gate[Permission Gate]
    ```

# Test Scenarios
Run the automated test script to validate all 10 mandatory scenarios:

λbash
chmod +x test_all_scenarios.sh
./test_all_scenarios.sh
The script covers:

# Health check

1. Weather tool

2. Traffic tool

3. Reminder tool

4. LLM direct answer (cache hit)

5. Proactive events (severe & moderate)

6. Send message + confirmation

7. Send email + confirmation

8. Injection attempt (blocked)

9. Unknown tool (graceful failure)


# Production Roadmap

# See docs/production_note.md for:
1. Scaling – Redis for sessions, PostgreSQL for memory, Kubernetes for orchestration

2. Security – OAuth2, AES‑256 encryption, injection resistance

3. Offline fallback – cached responses + deterministic commands

4. Multi‑step planning – dedicated PLANNING node for complex requests

5. Limitations

6. Multi‑step chaining is conceptual; production would add a dedicated PLANNING node.

7. All tools are mocked – real integrations require API keys and user consent.

8. Offline mode is not fully implemented (only basic deterministic commands).

# License & Acknowledgements
© 2026 Saurabh Tiwari – Developed for IT WEBHUT AI Product R&D Assessment.

Built with:

FastAPI

Ollama (Qwen2.5:7b)

SQLite

Docker

# Acknowledgements

This project was developed with the assistance of a generative AI pair‑programming tool (DeepSeek), which supported architectural design, code refinement, and real‑time debugging during development.

All AI‑generated information was thoroughly reviewed, validated, and integrated by Saurabh Tiwari, who takes full ownership and responsibility for the final implementation, system architecture, providing research insight and product decisions.

The AI tool was used strictly as an accelerator – every architectural choice, security boundary, and production trade‑off was intentionally designed, tested, and validated by the author to meet the specific requirements of the IT WEBHUT Luna AI Product R&D Assessment.
