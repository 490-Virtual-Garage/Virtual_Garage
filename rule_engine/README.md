# Rule Engine 

Diagnostic rule engine for Virtual Garage. It currently covers **P0171** only, so we can get
one DTC working end to end before adding more.

> **Work in progress (10/26/2026):** `diagnose()` is not finished. Do not merge this branch yet, I still need to finish diagnose() and work on the fastAPI calls.

## What it is

A two-layer graph, all defined in `dtc_pid.json`:

- **Knowledge layer (edges):** DTC and cause nodes linked by `CAN_CAUSE` edges, each with a
  prior. Answers *"what could cause this code?"*
- **Rule layer:** IF-THEN rules attached to causes. IF a sensor pattern appears in a capture,
  THEN the cause is supported or refuted with a weight ( still need to integrate weights) . Answers *"which cause fits the data?"*

Grant proposed a knowledge graph and I proposed a rule-based graph, so this combines both
into one graph. That way, any future agentic AI only needs to access one graph.

All knowledge (nodes, edges, rules, and condition definitions like "idle") lives in the JSON.
The graph loads it on startup, so adding a DTC means editing the JSON, not hardcoding it
in the code, in future we can scrap the JSON file and use a database instead.

## Files

- `dtc_pid.json`: nodes, edges, rules, and conditions. P0171 → vacuum leak, MAF, fuel delivery, with 4 rules.
- `graph.py`: loads the graph and checks a capture's sensor readings against the rules.
- `samplecapture.json`: fake data as of now (also my car has no DTC)

## Functions in graph.py

- `load_graph(path)`
- `group_readings(captured_data)`
- `nearest_value(values, t)`
- `build_moments(grouped)`
- `in_condition(moment, condition)`
- `check_clause(clause, moments, conditions)`
- `check_rule(rule, moments, conditions)`
- `diagnose(graph, captured_data)` (in progress)


## Run

From inside `rule_engine/`:

    python graph.py

