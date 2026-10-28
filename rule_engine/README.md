# Rule Engine

Diagnostic rule engine for Virtual Garage. It currently covers **P0171** only, so we can get
one DTC working end to end before adding more.

> **Status (10/27/2026):** `diagnose()` works end to end on the sample capture. It still needs
> test captures where rules actually fire, and it is not wired into FastAPI yet

## What it is

A two-layer graph, all defined in `dtc_pid.json`:

- **Knowledge layer (edges):** DTC and cause nodes linked by `CAN_CAUSE` edges, each with a
  prior. Answers *"what could cause this code?"*
- **Rule layer:** IF-THEN rules attached to causes. IF a sensor pattern appears in a capture,
  THEN the cause is supported or refuted with a weight. Answers *"which cause fits the data?"*

Grant proposed a knowledge graph and I proposed a rule-based graph, so this combines both
into one graph. That way, any future agentic AI only needs to access one graph.

All knowledge (nodes, edges, rules, and condition definitions like "idle") lives in the JSON.
The graph loads it on startup, so adding a DTC means editing the JSON, not hardcoding it
in the code. In the future the JSON can move into database tables.


## Files

- `dtc_pid.json`: nodes, edges, rules, and conditions. P0171 → vacuum leak, MAF, fuel delivery, with 4 rules.
- `graph.py`: loads the graph and diagnoses a capture against it.
- `samplecapture.json`: fake placeholder data (every reading is 858.75). My car has no DTCs, so `add_test_dtc()` adds P0171 for testing.


## Run

From anywhere in the repo:

    python rule_engine/graph.py
