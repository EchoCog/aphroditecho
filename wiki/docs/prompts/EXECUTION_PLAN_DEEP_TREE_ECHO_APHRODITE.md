## Deep Tree Echo ↔ Aphrodite Engine Integration: Actionable Execution Plan

This plan fuses the two strategic documents (Integration Strategy + Deep Tree Echo Integration Assistant Prompt) into a unified, production-focused execution roadmap. It emphasizes concrete contracts, phased delivery, measurable outcomes, and strict quality gates—no placeholders, only real, testable implementation.

---
### 0. Guiding Principles
1. Production-grade from first commit (tests + docs + metrics).  
2. Contract-first (schemas & proto IDL stabilized early; additive evolution).  
3. Latency budget protection (<5% overhead over current baseline per feature integration).  
4. Observability & policy hooks embedded at creation—not bolted on.  
5. Iterative de-duplication: remove legacy abstractions once parity tests pass.  
6. 4E Embodied AI & AAR semantics must inform API shape (context = agent, arena, relation graph, memory strata).  
7. Deterministic reproducibility (versioned prompts, functions, models, evolution events).  

---
### 1. Layer & Track Overview (Execution Tracks)
Track | Scope | Outcome Artifact(s)
----- | ----- | ------------------
T1 Contracts & Schemas | Agent, Function, Prompt, Memory, Arena Session, System Frame, Relations | `/contracts/json/*.schema.json`, `/contracts/proto/*.proto`, schema tests
T2 DTESN Kernel & Membranes | DTESN core (OEIS A000081 trees), P-System membranes, ESN reservoir scaffolding | `aphrodite/deep_tree_echo/dtesn/` modules + perf tests
T3 AAR Gateway & Orchestration | Unified gateway (HTTP/gRPC), arena lifecycle, agent registry | `aphrodite/aar_core/gateway.py`, OpenAPI & gRPC descriptors
T4 Prompt Kernel & Spark Migration | Versioned prompt store, lineage, semantic index | `echo.sys/prompt_kernel/`, prompt catalog manifest
T5 Function / Tool Registry | Unified registry (argc + llm-functions), invocation & safety gating | `aphrodite/aar_core/functions/registry.py`
T6 Memory & Relation Graph | Multi-tier memory + graph edges (Agent/Tool/Prompt/Session) | `aphrodite/aar_core/memory/`, `relations/graph.py`
T7 Agent Unification | Consolidated agent base + tool-enabled behaviors | `aphrodite/aar_core/agents/base.py`
T8 Frontend & CLI Integration | galatea-UI & aichat switched to gateway clients | SDKs (`sdk/ts/`, `sdk/rust/`)
T9 Echo-Self Evolution Engine | Evolution hooks + meta-learning loops | `aphrodite/deep_tree_echo/echo_self/`
T10 4E Embodiment Layer | Proprioception, sensory-motor virtual mapping | `aphrodite/deep_tree_echo/embodied/`
T11 Observability & Policy | Tracing, metrics, guardrails, cost accounting | `aphrodite/observability/`, policy config
T12 Performance & Hardening | Bench harness, regression protection, memory optimization | Bench reports & threshold CI
T13 Deployment & Governance | Secure rollout, versioning, deprecation pathways | `DEPLOYMENT_DTE.md`, migration scripts

---
### 2. Phased Timeline (Indicative 12-Week, Overlapping Tracks)
Phase | Weeks | Primary Tracks | Gate (Exit Criteria)
----- | ----- | -------------- | -------------------
P0 Inventory & Diff | 1 | T1 (foundation) | Duplicate matrix approved; baseline perf recorded
P1 Contracts Finalization | 2 | T1 → enables all | All schemas v1.0 locked; CI schema tests green
P2 Core Gateway & Registry | 3–4 | T3, T5 | End-to-end function invocation via gateway + inference augment
P3 Prompt & Memory MVP | 5–6 | T4, T6 | Prompt lineage & memory query integrated into inference path
P4 Agent & aichat Migration | 6–7 | T7, T8 | aichat using AAR gateway exclusively; parity tests
P5 DTESN & Membranes MVP | 7–8 | T2 | Membrane pre-processing + perf within micro-latency targets
P6 Evolution & 4E Hooks | 8–9 | T9, T10 | Echo-Self post-processing active; proprioceptive metrics logging
P7 Relation Graph & Policy | 9–10 | T6, T11 | Tool authorization + relation-filtered function allow-list
P8 Perf, Observability Deepening | 10–11 | T11, T12 | Bench deltas <5%; tracing coverage ≥90% spans
P9 Hardening & Deprecations | 11–12 | T12, T13 | Legacy abstractions removed; migration guide published

---
### 3. Objective Key Results (OKRs)
Objective | Key Result(s)
--------- | -------------
Unified Orchestration | 100% chat & agent requests through AAR Gateway by end P4
Consistent Function Layer | >90% tool calls via Registry by end P7
Prompt Governance | 100% served prompts versioned & hash-verified by end P6
Latency Control | Added orchestration overhead median <5%, p95 <8% vs baseline
Memory Utility | Retrieval augmentation lifts benchmark answer quality +X% (define X after baseline) by P7
Evolution Efficacy | Echo-Self reduces perplexity or chosen metric ≥3% on validation set by P8
Observability | 95% critical paths traced; zero unclassified policy violations by P9
Technical Debt Reduction | Remove ≥3 duplicate agent/function code paths by P9

---
### 4. Core Contracts (Snapshot)
Schema | Fields (Essentials) | Notes
------ | ------------------- | -----
AgentSpec | id, version, capabilities[], tools_allow[], policies[], prompt_profile | JSON Schema v1.0
FunctionSpec | name, description, params(schema), safety_class, cost_unit, impl_ref | Derived from argc & llm-functions
PromptAsset | id, version, role, tags[], sha256, parent_version, template | Stored + embedding fingerprint
ArenaSession | id, agents[], state(enum), created_at, memory_scope_ids[], events[] | Event-sourced; append-only log
RelationEdge | source_id, target_id, relation_type, attributes | Filter gating
MemoryRecord | id, type(enum), content_ref, vector[], ttl, lineage[] | Vector store + metadata DB
SystemFrame | id, active_prompt_id, policy_bundle_hash, feature_flags | Signed snapshot; cache invalidation events
InferenceRequestExt | model, sampling, agent_id, arena_id, memory_refs[], function_allow[] | Extends existing engine request

---
### 5. Initial Directory & File Additions (Planned)
Path | Purpose
---- | -------
`contracts/json/` | Versioned JSON Schemas
`contracts/proto/` | Protobuf IDL (gateway, memory, functions)
`aphrodite/aar_core/gateway.py` | HTTP/gRPC entrypoint layer
`aphrodite/aar_core/functions/registry.py` | Canonical function registry
`aphrodite/aar_core/memory/` | Memory API modules
`aphrodite/aar_core/relations/graph.py` | Relation graph abstraction
`echo.sys/prompt_kernel/` | Prompt versioning + retrieval logic
`aphrodite/deep_tree_echo/dtesn/` | DTESN kernels + membrane engine
`aphrodite/deep_tree_echo/echo_self/` | Evolution engine
`aphrodite/deep_tree_echo/embodied/` | 4E embodiment modules
`tests/aar/` | Contract & gateway integration tests
`benchmarks/aar/` | Performance harness & baselines

---
### 6. Detailed Track Execution (Condensed)
Track | Step Sequence (Ordered) | Quality Gates
----- | ----------------------- | ------------
T1 | Draft schemas → Review → Freeze v1 → Add backward-compat tests → Proto generation | Schema lint, CI diff guard
T2 | Implement A000081 tree enum → Membrane model → Evolution rules engine → ESN reservoir stub → Perf tune | Microbench (μs targets), correctness tests
T3 | Gateway skeleton → Auth/policy interceptors → OpenAPI spec → gRPC service → Load tests | 99p latency within budget
T4 | Parse spark assets → Create manifest + hashes → Embedding index → Retrieval API → Cache & lineage tests | Hash stability tests
T5 | Ingest argc & llm-functions → Normalize params → Safety class gating → Invocation adapters → Telemetry | 0 schema drift; invocation parity tests
T6 | Memory stores (working, episodic, semantic) → Vector integration → API → TTL & summarization → Relation-based filtering | Latency + recall tests
T7 | Consolidate agent base → Tool binding abstraction → Capability negotiation → Policy enforcement → Legacy removal | Agent parity tests pass
T8 | Generate SDKs → Replace direct calls in aichat/galatea → Integration tests → Feature flag fallback | 100% traffic via gateway
T9 | Evolution hooks around inference → Fitness metrics capture → Update strategies → Constrain updates → Benchmark improvement | Metric delta tests
T10 | Proprioceptive metrics exporter → Sensory abstraction → Motor command mapping → Feedback loop integration | Closed-loop stability tests
T11 | Span taxonomy → OTLP exporter → Metrics dashboards → Policy violation alerts | Coverage & alert tests
T12 | Baseline pre-integration → Continuous regression harness → Memory optimization tasks → Stress tests | Perf threshold CI green
T13 | Migration scripts → Deprecation notices → Removal PRs → Final documentation | No orphaned legacy paths

---
### 7. Dependencies & Critical Path
Dependency Chain: Schemas (T1) → Gateway & Registry (T3/T5) → Memory/Prompt (T4/T6) → Agent Migration (T7) → Evolution & 4E (T9/T10).  
Parallelization: DTESN (T2) can proceed after minimal gateway stub. Observability (T11) starts once first gateway spans exist.

Risk | Impact | Mitigation
---- | ------ | ----------
Schema churn | Rework across clients | Enforce version freeze + additive-only changes
Latency regression | User experience degradation | Perf budget CI + fast rollback toggles
Vector store scaling | Memory cost / recall variance | Start modular; abstract driver; synthetic benchmarks
Prompt governance gaps | Inconsistent model behavior | Mandate versioned prompt IDs in inference path
Evolution instability | Model drift / unpredictability | Guardrails: canary evaluation + rollback criteria

---
### 8. Metrics & Telemetry (Instrumentation Targets)
Category | Metric | Target
-------- | ------ | ------
Gateway | median / p95 request latency | < baseline + 5% / 8%
Function Registry | resolution time | < 2 ms in-process
Prompt Kernel | retrieval p95 | < 75 ms
Memory Query | semantic top_k latency p95 | < 120 ms
Evolution | improvement metric delta | ≥ +3% vs baseline after stabilization
Relation Graph | authorization check | < 1 ms cached
ESN / Membrane | per evolution cycle | within micro-targets (10μs membrane)
Tracing Coverage | traced spans / eligible | ≥ 0.9

---
### 9. Quality Gates (CI/CD)
Gate | Enforcement
---- | ----------
Schema Compatibility | Fails if breaking diff without version bump
Latency Regression | Bench harness abort if >5% median increase
Test Coverage (New Code) | Minimum 85% line & critical path branch
Prompt Hash Integrity | Fail if manifest hash mismatch
Function Parity | Old vs new invocation output diff threshold ≤ ε
Security & Policy | Static scan + policy unit tests must pass

---
### 10. Security & Policy Integration Points
Stage | Hook
----- | ----
Request Intake | AuthZ (arena & agent scope), rate limit
Function Invocation | Safety class ACL + cost quota
Memory Insert | PII classification + redaction chain
Prompt Retrieval | Version & signature verification
Evolution Update | Policy check (allowed domains / metrics pass)

---
### 11. Initial Two-Week Sprint Backlog (Sprint 1)
ID | Item | DoD
-- | ---- | ---
S1-1 | Create `/contracts/json` & draft AgentSpec, FunctionSpec, PromptAsset schemas | Linted, PR merged, tests validate JSON examples
S1-2 | Proto skeleton for gateway (ListAgents, InvokeFunction, InferenceRequestExt) | Compiles; Python & Rust stubs generated
S1-3 | Gateway minimal HTTP service (list agents hard-coded, health, version) | Runs locally; latency baseline captured
S1-4 | Function registry ingestion from argc sample commands | 3 example functions resolvable via API
S1-5 | Spark asset inventory script outputs manifest JSON (id, role, hash) | Manifest committed; hashes reproducible
S1-6 | Bench harness baseline (current inference latency distribution) | Report artifact stored in CI
S1-7 | Observability base: tracing middleware for gateway | Spans visible in local exporter
S1-8 | Risk register document initiated (`RISK_LOG.md`) | Includes owners & mitigation statuses

---
### 12. Evolution & 4E Guardrails
Guardrail | Mechanism
--------- | ---------
Evolution Safety | Canary evaluation set; abort if metric worsens >1% over 3 runs
Embodiment Feedback Loop | Rate limiter + smoothing filter to prevent oscillation
Memory Growth Control | Summarize & prune episodic > threshold; vector compaction weekly

---
### 13. Deprecation Plan (High-Level)
Legacy Item | Replacement | Trigger for Removal
----------- | ---------- | ------------------
llm agent base classes | aar_core agents | After parity tests (P7 exit)
Ad-hoc tool loaders | Function Registry | 2 sprints after registry GA
Direct aichat → engine calls | Gateway route | Once SDK adopted & flagged stable
Raw spark prompt lookups | Prompt Kernel API | After lineage/hashes validated

---
### 14. Documentation Artifacts
Artifact | Location | Timing
-------- | -------- | ------
Architecture Overview | `ARCHITECTURE_AAR.md` | End P1
Contracts Reference | `contracts/README.md` | End P1
Prompt Governance Guide | `echo.sys/prompt_kernel/README.md` | P3
Function Registry Usage | `aphrodite/aar_core/functions/README.md` | P3
Migration Guides | `docs/migration/` | Rolling (start P4)
Evolution Safety Doc | `echo_self/EVOLUTION_SAFETY.md` | P6
Performance Bench Reports | `benchmarks/reports/` | Each phase

---
### 15. Exit Criteria (Project Completion)
1. All traffic uses AAR gateway for orchestration.  
2. All prompts, functions, agents are versioned & discoverable via registry APIs.  
3. Memory + relation graph augment inference deterministically (telemetry confirmed).  
4. Evolution engine enabled behind policy gate with measurable improvement.  
5. Performance within latency budgets; no unresolved critical risks.  
6. Legacy codepaths removed & documented.  
7. Documentation set complete & current.  

---
### 16. Next Immediate Actions (Post-Plan Approval)
1. Approve schemas & directory scaffolding (start Sprint 1 backlog).  
2. Stand up contract CI jobs (schema diff + proto generation).  
3. Capture baseline performance metrics before first gateway merge.  
4. Assign track owners & publish to RISK_LOG / responsibility matrix.  

---
### 17. Responsibility Matrix (Initial Draft)
Role | Responsibility (High-Level)
---- | ---------------------------
Contract Lead | T1 schemas integrity & evolution governance
Kernel Lead | T2 DTESN & membrane performance
Gateway Lead | T3/T5 API surface & latency budgets
Prompt/Mem Lead | T4/T6 prompt & memory correctness
Agent Lead | T7 migration & parity
Frontend/CLI Lead | T8 SDK integration
Evolution Lead | T9 metric improvements & safety
Embodiment Lead | T10 proprioceptive feedback design
Observability Lead | T11 tracing & dashboards
Perf Lead | T12 benchmarks & regression gates
Governance Lead | T13 deprecation & compliance

---
### 18. Appendices
Reference the original two strategy documents for conceptual rationale; this file supersedes them for execution tracking. All deviations must be logged in `CHANGE_LOG_EXEC_PLAN.md` (to be created when first change occurs).

---
End of Execution Plan.
