# AI Support Operations Platform — Project README

This document is the single source of truth for this project. If you are an LLM/assistant picking this up fresh, read this fully before helping — it captures every decision made so far so context isn't lost.

---

## 1. What this project is

**Name:** AI Support Operations Platform

**Objective:** Build a production-oriented AI support system that can understand customer requests, retrieve company knowledge, interact with business systems through tools, make bounded decisions, execute permitted actions, escalate uncertain/high-risk cases to humans, and continuously evaluate its performance.

**Why this project exists:** This is a flagship portfolio project for an AI/ML developer transitioning into an AI Engineer role (Computer Vision / GenAI / Agentic AI specialization). Previous projects were started and abandoned midway — this project is explicitly meant to be taken from messy/no data all the way to a deployed, monitored production system, without stopping halfway. A second project (Autonomous Inventory & Procurement Intelligence Agent) is planned to follow this one, reusing the same production skeleton.

---

## 2. Business scenario

- Simulated **e-commerce online store** (not a real business yet — synthetic/simulated data)
- Supports a broad scope of customer request types: **order status/tracking, refunds/returns, shipping issues** (delay, damage, wrong item)
- **Phase 1 permission scope:** the agent has **no real action-taking power**. It can look things up (read-only) and respond/inform, but anything requiring an action (refund, reship, cancel) is **escalated to a human** with the agent's reasoning and a drafted recommendation attached. Real action permissions will be added gradually in a later phase, once the reasoning layer is fully trusted.

---

## 3. Design principles agreed on

- **No vibe-coding.** Boilerplate/scaffolding code (project setup, config, standard framework code) can be AI-generated and copy-pasted. **Core logic (agent reasoning, state transitions, confidence scoring, decision-making, retrieval logic) must never be handed over as code.** The assistant explains the concept and reasoning step by step; the user writes the actual implementation himself, repeating/iterating until he understands it deeply enough to code it independently.
- System is built **spec-first**: a full system contract/architecture is defined before any code is written.
- The agent's state design is intentionally **full-featured**, closer to a real production multi-agent system — not a minimal request→response loop. It includes memory, planning, retrieval, tool use, self-evaluation, human-in-the-loop, and a feedback loop.
- RAG knowledge base uses **separate documents per topic** (shipping policy, refund policy, FAQ) rather than one combined document.

---

## 4. Tech stack decisions

| Component | Decision |
|---|---|
| LLM provider | **Groq API** (chosen for being free — watch for rate limits on heavy testing, may need a fallback later) |
| Agent framework | **Mix of hand-rolled state machine + LangGraph** — hand-roll the core learning parts (state transitions, confidence/decision logic), use LangGraph for orchestration plumbing once the underlying concept is understood |
| Backend | FastAPI (planned) |
| Vector DB | TBD in Phase 2 |
| Deployment | Docker + cloud (VM/serverless), TBD in Phase 9 |
| Dev environment | User's own responsibility — assumed ready |

---

## 5. Agent state machine (Phase 0 design)

Sequential flow with a branch point:

`Intake → Context & Intent → Planning → Retrieval & Tools → Reasoning → Confidence Check → [ Respond Directly | Escalate to Human ] → Feedback Capture → Evaluation Logging → (loops back to Context & Intent if the customer replies again)`

- **Intake:** new request arrives, gets a session/conversation ID
- **Context & Intent:** recalls prior turns of this conversation (multi-turn memory), classifies what the customer wants
- **Planning:** agent decides what steps/info it needs before acting (the actual "agentic" part, not single-shot Q&A)
- **Retrieval & Tools:** pulls relevant policy doc(s) via RAG, and calls read-only tools (order DB, customer DB, shipping tracking)
- **Reasoning:** combines policy + data + context into a conclusion
- **Confidence Check:** agent scores its own confidence in the decision — this determines the branch
- **Respond Directly:** high confidence, no risky action needed
- **Escalate to Human:** low confidence OR an action is required (since Phase 1 has no real actions) — routed to a human review queue with the agent's reasoning + draft recommendation attached
- **Feedback Capture:** the human's correction/approval gets logged
- **Evaluation Logging:** every outcome (resolved, escalated, human-corrected) is logged for the evaluation/monitoring layer

---

## 6. Full build roadmap (12 phases)

0. **System Specification** — business scenario, request types, permission boundaries, state design, escalation conditions, evaluation criteria, architecture sketch *(in progress)*
1. **Data & Environment Setup** — DB schema, synthetic data generation, policy docs, dev environment, test scenarios
2. **Knowledge Retrieval Layer (RAG)** — chunking, embeddings, vector DB, retrieval logic, retrieval quality testing
3. **Tool Layer** — tool interface definitions, implementation, tool-calling integration, error handling
4. **Agent Core (Reasoning Engine)** — intent classification, memory/context management, planning, reasoning, confidence scoring, response drafting, full state machine wiring *(hardest phase)*
5. **Human-in-the-Loop & Escalation** — escalation triggers, escalation payload design, review dashboard, feedback capture
6. **Evaluation Framework** — success metrics, test set, automated evaluation runs, feedback-driven improvement
7. **Backend & API Engineering** — FastAPI structure, endpoints, session management, auth, structured logging
8. **Frontend / Demo Interface** — customer chat UI, human review dashboard, metrics dashboard
9. **Deployment** — containerization, config/secrets management, cloud deployment, CI/CD basics
10. **Monitoring & Observability** — logging/tracing, live metrics, drift/degradation alerts, cost/latency monitoring
11. **Gradual Action Permissions (Post-MVP)** — enabling real actions one at a time, starting with lowest-risk, with audit logging and re-evaluation at each step
12. **Documentation & Portfolio Packaging** — architecture write-up, demo video, README, case study

**Estimated total time:** ~140–200 hours for the MVP (Phases 0–10), plus ~15–20 more for Phases 11–12, at the user's pace of 2–3 hours/day (~7–11 weeks). This assumes the "explain, don't code" method, which is slower by design.

---

## 7. Current status

- Phase 0 (System Specification) is in progress.
- Confirmed so far: business scenario, request scope, permission boundaries, RAG doc structure, state machine design, tech stack.
- Still to finalize in Phase 0: exact tool interfaces, precise escalation conditions/thresholds, confidence check scoring methodology, evaluation criteria detail, production architecture diagram.
- Next step once Phase 0 is finalized: Phase 1 (Data & Environment Setup).

---

## 8. How to work with the user on this project

- Explain concepts thoroughly and step-by-step before any implementation.
- Never hand over core logic as code — only boilerplate/scaffolding.
- Use the phase/sub-phase structure above to track progress — don't skip ahead without finishing the current phase's sub-topics.
- The user wants deep, interview-ready understanding, not just a working repo.