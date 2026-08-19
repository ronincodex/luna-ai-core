# Luna AI Core – Production Roadmap

**Author:** Saurabh Tiwari  
**Project:** Luna AI Core POC for IT WEBHUT  
**Date:** August 2026

---

## 1. Executive Summary

The current POC demonstrates a secure, auditable, and modular AI orchestration layer. It successfully implements deterministic routing, local LLM inference (Ollama), mock tools, a permission gate, long-term memory, and proactive event handling. This document outlines the architectural evolution required to scale this foundation into a production-grade, multi-tenant personal assistant.

The core philosophy remains unchanged: **LLMs reason, but deterministic code controls execution.** Every sensitive action must pass a permission gate, and every decision is logged for full provenance.

---

## 2. Scaling from 1,000 to 1,000,000 Users

### 2.1 Stateless API Layer
- **Current:** Session state is stored in an in-memory dictionary (`sessions: dict[str, LunaState]`). This is a single-point-of-failure and does not scale horizontally.
- **Production:** Store state in **Redis** (with persistence and replication). Each request loads the user's session via `session_id`. Redis provides sub-millisecond latency and supports TTL for automatic cleanup of inactive sessions.

### 2.2 Database
- **Current:** SQLite (`~/.luna/luna.db`). Ideal for single-user POC but not for concurrent writes.
- **Production:** Use **PostgreSQL** for relational data (user profiles, preferences, audit logs) and **TimescaleDB** for time-series event logs. Implement:
  - Connection pooling (`PgBouncer`).
  - Read replicas for analytical queries.
  - Partitioning for audit logs (by date) to maintain query performance.

### 2.3 Horizontal Scaling
- Deploy multiple FastAPI instances behind a **load balancer** (Nginx / HAProxy).
- Use **Kubernetes** with HPA (Horizontal Pod Autoscaler) to scale pods based on CPU and request queue depth.
- For stateful components, externalize everything to Redis and PostgreSQL – the application pods remain stateless.

### 2.4 LLM Scaling
- **Option A (Managed)**: Use a hosted LLM API (e.g., OpenAI GPT-4, Anthropic Claude) with auto-scaling. This offloads infrastructure complexity.
- **Option B (Self-Hosted)**: Deploy multiple Ollama workers on GPU nodes. Use a **model sharding** strategy or a simple round-robin load balancer. For cost efficiency, use smaller distilled models (e.g., Qwen2.5:7b) for simple tasks and larger models (e.g., Llama 3 70B) for complex reasoning – a **model router** selects based on task complexity.
- **Fallback**: Cache frequent queries (e.g., "What's the weather?") in Redis to avoid redundant LLM calls.

---

## 3. Security & Privacy

### 3.1 Authentication & Authorization
- **Current:** No authentication (single-user POC).
- **Production:** Implement **OAuth2 / JWT** for user identification. Integrate with a third-party identity provider (Auth0, Okta) or implement a custom solution with refresh tokens.
- Each tool (weather, traffic, send_message, etc.) has a **permission scope**. Users and AI agents are scoped to the tools they are authorized to use.

### 3.2 Encryption
- **Data at Rest**: Encrypt user profiles and memories using **AES-256-GCM** before storing in PostgreSQL. Use a key management service (AWS KMS, HashiCorp Vault) to rotate keys.
- **Data in Transit**: All API endpoints exposed over **TLS 1.3**. Internal service-to-service communication uses mTLS.

### 3.3 Audit & Provenance
- **Current:** Every state transition is logged in `audit_trail` and returned in the API response. This is excellent for debugging but not for long-term storage.
- **Production:** Ship audit logs to a **centralized logging system** (Elasticsearch / OpenSearch) with a structured schema. Each entry includes:
  - `user_id`, `session_id`, `action_id`
  - `node` (Router, PermissionGate, Executor, etc.)
  - `decision` and `reason`
  - Timestamp with nanosecond precision
  - Full request/response payloads (sanitized for PII).

### 3.4 Prompt Injection Resistance
- **Current:** The permission gate blocks sensitive actions before the LLM processes the instruction. The LLM never directly controls tool execution.
- **Production**: This separation is fundamental. Additionally:
  - Sanitize user inputs before passing to the LLM (strip control characters, limit length).
  - Use a dedicated **"Guardrail" LLM** (small and fast) to classify inputs as malicious before they reach the main orchestrator.
  - Always validate tool parameters against a strict JSON schema (already implemented in `TOOLS`).

---

## 4. Offline / Degraded Mode

### 4.1 Local Cache
- Cache the last **N LLM responses** (e.g., 100) for common queries (e.g., "What is the capital of France?"). Use a simple key-value store (LevelDB / RocksDB) on the device.
- When offline, if a cached answer exists, return it immediately. If not, fall back to deterministic commands (time, local reminders, simple math) and prompt the user that advanced features are unavailable.

### 4.2 Deterministic Fallback
- The deterministic router (keyword matching) already works without the LLM. Extend this to include:
  - Local time/date queries.
  - Basic arithmetic.
  - Pre-defined responses for "What is your name?" etc.
- This ensures Luna remains responsive even when the network is down.

### 4.3 Queue & Retry
- For requests that require the LLM or external APIs, enqueue them in a local FIFO queue. When connectivity is restored, process them in order. Provide a visual indicator to the user (e.g., "Pending tasks: 3").

---

## 5. On-device vs. Cloud

| Component | On‑device | Cloud |
|-----------|-----------|-------|
| Wake‑word detection | ✅ Yes (hotword engines like Porcupine) | ❌ |
| STT / TTS | ✅ Yes (local models for low latency) | ✅ Optional for higher quality |
| Deterministic Router | ✅ Yes (cached rules) | ✅ Yes (for updates) |
| LLM Inference | ❌ Not feasible on mobile (except tiny models) | ✅ Yes |
| Long‑term Memory | 🔄 Cached read-only copy | ✅ Yes (PostgreSQL) |
| Audit / Provenance | 🔄 Batched and uploaded | ✅ Yes (Centralized) |
| Tool Execution | 🔄 Permission confirmation only | ✅ Yes (actual execution) |

**Rationale:** Sensitive data (raw transcripts, user locations) should never leave the device without explicit consent. The cloud handles heavy computation and global state, while the device ensures privacy and low-latency responses for common tasks.

---

## 6. Multi-step Execution (Planning Node)

### 6.1 The Missing Piece
The current POC executes only one tool per user turn. Production requires handling complex requests like: *"Check the weather and if it's raining, set a reminder to take an umbrella."*

### 6.2 The Solution: A `PLANNING` Node
Extend the state machine with a new state: `PLANNING`. This node:
1. Receives the user input and any previous tool results.
2. Calls the LLM with a system prompt asking: *"Break this request into a sequence of tool calls. Output a DAG (Directed Acyclic Graph) of steps."*
3. The LLM returns a JSON array: `[{"tool": "get_weather", "params": {...}}, {"tool": "create_reminder", "params": {...}}]`.
4. The orchestrator iterates through this list, executes each step, feeds the result into the next, and accumulates a final response.
5. **Idempotency:** Each step is assigned a unique `step_id`. If a step fails, the system retries up to 3 times before failing gracefully and informing the user.

### 6.3 Context Management
- The context window is managed by **selective summarization**. Instead of passing the entire conversation history, use a sliding window (last 5 turns) + a concise summary of key facts (extracted by a separate summarization LLM call).

---

## 7. Proactive Intelligence

### 7.1 Event Ingestion
- **Current:** Single `/event` endpoint for manual testing.
- **Production:** Events (traffic, calendar changes, health alerts) are pushed to a **message queue** (Apache Kafka / RabbitMQ). Each event is typed and versioned.
- A dedicated **Event Evaluator** service consumes events, applies user-defined rules (e.g., "Notify me only if severity > moderate AND not during DND hours"), and decides whether to escalate to the orchestrator.

### 7.2 Notification System
- After a positive evaluation, the orchestrator generates a concise, personalized notification using the LLM.
- Notifications are delivered via:
  - **Push notifications** (FCM / APNS) for immediate alerts.
  - **In-app inbox** for non-urgent messages.
  - **Email digest** for daily summaries.

### 7.3 User Control
- Users can configure **quiet hours** and **priority levels** per event type.
- All proactive notifications are logged and allow the user to provide feedback (e.g., "This was helpful" / "This was annoying") to fine-tune the evaluation rules.

---

## 8. Health & Well-being (Future Direction)

- **Data Source**: Synthetic sensor data (steps, sleep, heart rate) with explicit user consent. No real medical data in POC.
- **Processing**:
  1. **Raw data** stored in a secure time-series DB (InfluxDB).
  2. **Derived metrics** (e.g., average sleep over 7 days) computed by a separate analytics service.
  3. **AI Guidance** generated by the LLM, but always presented as *suggestions* (e.g., "You've been sleeping less than 6 hours. Consider a wind-down routine.") – never as a diagnosis.
- **Compliance**: GDPR / HIPAA compliance by design – data minimization, retention policies, and user deletion requests.

---

## 9. Testing, Observability & CI/CD

### 9.1 Automated Testing
- **Unit tests** for each tool, state transition, and permission gate.
- **Integration tests** for the 10 mandatory scenarios (already provided as `test_all_scenarios.sh`).
- **Performance tests**: Simulate 1000 concurrent users with `locust` to measure latency and throughput.

### 9.2 Observability
- **Metrics**: Prometheus + Grafana. Track request latency, error rates, LLM token usage, and tool execution times.
- **Tracing**: OpenTelemetry for distributed tracing – visualize the entire lifecycle of a user request across microservices.
- **Logging**: Structured logs (JSON format) shipped to Elasticsearch.

### 9.3 CI/CD Pipeline
- **GitHub Actions** or **GitLab CI**:
  1. Lint and format (black, flake8).
  2. Run unit and integration tests.
  3. Build Docker image.
  4. Scan for vulnerabilities (Trivy / Snyk).
  5. Deploy to staging environment.
  6. Run smoke tests.
  7. Promote to production (blue-green deployment).

---

## 10. Deployment & Infrastructure

- **Orchestration**: Kubernetes (EKS / GKE / AKS) for auto-scaling and self-healing.
- **Service Mesh**: Istio or Linkerd for secure service-to-service communication, circuit breaking, and retry policies.
- **Disaster Recovery**: Regular backups of PostgreSQL to S3 (with cross-region replication). Recovery Point Objective (RPO) ≤ 1 hour.
- **Cost Optimization**: Use spot instances for non-production environments. Implement auto-scaling based on CPU and memory usage to avoid over-provisioning.

---

## 11. Conclusion

The Luna AI Core POC provides a robust, secure, and auditable foundation. The architectural decisions – especially the separation of reasoning from execution, the state machine with full provenance, and the permission gate – translate directly to production without fundamental re-architecture. By adopting Redis, PostgreSQL, Kubernetes, and a message queue, Luna can scale from a single user to millions while maintaining security, privacy, and responsiveness.

The next milestones are:
1. Implement the `PLANNING` node for multi-step execution.
2. Integrate real APIs for weather, traffic, and messaging.
3. Develop native mobile apps (iOS/Android) with wake-word and offline support.
4. Roll out the proactive event pipeline.

This roadmap transforms Luna from a promising POC into a world-class personal assistant.

---

## 12. References & Related Work

- BONSAI (2026) – Mixed-initiative workspace for co-development. Inspired the bounded agent model.
- IT WEBHUT Luna Product Requirements (2026) – The assessment PDF.
- Ollama Documentation (2026) – Local LLM inference.
- FastAPI Production Best Practices (2026).
