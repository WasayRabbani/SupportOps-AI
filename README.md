# SupportOPS AI

**An agentic AI platform for e-commerce customer support — built end-to-end from messy data to a deployed, monitored production system.**

> Understands customer requests, retrieves company knowledge, reasons over live business data through tool calling, drafts responses, and knows when to escalate to a human — with a full evaluation and monitoring layer, not just a demo.

---

## Table of contents
- [Overview](#overview)
- [Why this project exists](#why-this-project-exists)
- [Key features](#key-features)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Roadmap](#roadmap)
- [Getting started](#getting-started)
- [Evaluation](#evaluation)
- [Status](#status)
- [License](#license)

---

## Overview

Aegis Support is a simulated e-commerce customer support agent that goes beyond a typical "RAG chatbot" project. It combines retrieval-augmented generation, multi-step agentic reasoning, tool use against live business data, human-in-the-loop escalation, and continuous evaluation — deployed as a real service with monitoring, not just a notebook.

The system handles order status inquiries, refund/return requests, and shipping issues. In its current phase, it **does not take real actions** (no auto-refunds, no auto-cancellations) — every actionable case is escalated to a human reviewer with the agent's full reasoning and a drafted recommendation attached. Action permissions will be added incrementally as the reasoning layer proves reliable through evaluation.

## Why this project exists

Most portfolio "AI agent" projects stop at "I built a chatbot with RAG." This one is built to demonstrate the full lifecycle a production AI system actually requires:

- **Messy-to-clean data pipeline**, not a pre-cleaned dataset
- **Real agentic reasoning** — planning, multi-step decisions, self-evaluation — not single-shot prompting
- **Human-in-the-loop design**, the part most agent projects skip entirely
- **Evaluation as a first-class citizen**, not an afterthought
- **Actual deployment and monitoring**, not just "it runs on my machine"

## Key features

- 🔍 **RAG over structured policy knowledge** — separate, topic-scoped documents (shipping, refunds, FAQ)
- 🛠️ **Tool-calling agent** — reads live order/customer data through defined tool interfaces
- 🧠 **Multi-step agent state machine** — intake → context & intent → planning → retrieval & tools → reasoning → confidence check → respond or escalate
- 🧑‍⚖️ **Human-in-the-loop escalation** — every uncertain or risky case is routed to a review queue with full reasoning attached, never silently auto-resolved
- 📊 **Evaluation framework** — tracks resolution accuracy, escalation rate, and false-confidence rate against a curated test set
- 📈 **Production monitoring** — live metrics dashboard, drift/degradation alerts, cost and latency tracking
- 🐳 **Fully containerized and deployed**, not just a local script

## How it works

```
Customer request
       │
       ▼
   Intake ──► Context & Intent ──► Planning ──► Retrieval & Tools ──► Reasoning
                                                                          │
                                                                          ▼
                                                                 Confidence Check
                                                                    /         \
                                                      High confidence      Low confidence
                                                       / no action           or action
                                                          needed              required
                                                            │                    │
                                                            ▼                    ▼
                                                    Respond directly     Escalate to human
                                                            │                    │
                                                            └────────┬───────────┘
                                                                     ▼
                                                        Feedback capture + evaluation logging
                                                                     │
                                                                     ▼
                                                  (loops back to Context & Intent on next reply)
```

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Groq API |
| Agent orchestration | Hand-rolled state machine + LangGraph |
| Backend | FastAPI |
| Vector store | TBD (Phase 2) |
| Frontend / demo | TBD (Phase 8) |
| Deployment | Docker, cloud (VM/serverless) |
| Monitoring | Custom metrics + logging/tracing |

## Project structure

```
aegis-support/
├── data/                  # synthetic business data, schemas, generators
├── knowledge/             # policy documents (RAG source docs)
├── tools/                 # tool interfaces (order lookup, refund eligibility, etc.)
├── agent/                 # core reasoning engine, state machine
├── evaluation/            # test scenarios, evaluation harness
├── api/                   # FastAPI backend
├── frontend/              # demo chat UI + human review dashboard
├── deployment/            # Dockerfiles, deploy scripts
├── docs/                  # architecture notes, case study write-up
└── README.md
```

## Roadmap

- [x] Phase 0 — System specification & architecture
- [ ] Phase 1 — Data & environment setup
- [ ] Phase 2 — Knowledge retrieval layer (RAG)
- [ ] Phase 3 — Tool layer
- [ ] Phase 4 — Agent core (reasoning engine)
- [ ] Phase 5 — Human-in-the-loop & escalation
- [ ] Phase 6 — Evaluation framework
- [ ] Phase 7 — Backend & API engineering
- [ ] Phase 8 — Frontend / demo interface
- [ ] Phase 9 — Deployment
- [ ] Phase 10 — Monitoring & observability
- [ ] Phase 11 — Gradual action permissions (post-MVP)
- [ ] Phase 12 — Documentation & portfolio packaging

## Getting started

> Setup instructions will be filled in as Phase 1 (environment setup) is completed.

```bash
git clone https://github.com/<your-username>/aegis-support.git
cd aegis-support
# setup steps to be added
```

## Evaluation

A structured evaluation framework (Phase 6) will report:
- Resolution accuracy against a curated test set
- Escalation rate and false-confidence rate
- Human-correction feedback trends over time

Results will be published here once available.

## Status

🚧 **Active development.** This project is being built incrementally and documented phase by phase — see the [Roadmap](#roadmap) above for current progress.

## License

MIT (or your preferred license — update before publishing)