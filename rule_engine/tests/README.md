# Rule engine tests

Tests for the rule-based inference engine (`rule_engine/graph.py` + `rule_engine/dtc_pid.json`). They're the safety net for migrating the knowledge base from JSON to Neo4j: the same tests must pass before and after the migration.

## What the tests check

- `test_graph.py`: `load_graph()` builds the knowledge base correctly (causes, priors, rules, conditions, nodes).
- `test_diagnose.py`: `diagnose()` turns each capture in `sample_captures/` into exactly the output in `expected_outputs/`.

## Sample captures

`sample_captures/` holds synthetic P0171 captures in the same format `capture.py` sends. Each one makes a different cause rank first:

| Capture | Top cause |
|---|---|
| `p0171_vacuum_leak.json` | vacuum_leak |
| `p0171_maf.json` | maf_sensor |
| `p0171_fuel.json` | fuel_delivery |
| `no_dtc.json` | `no_dtc` |

`expected_outputs/` holds the matching `diagnose()` output for each, under the same filename. You can also POST any capture to `/captures` at `localhost:8001/docs` and compare the response to its expected file. After the Neo4j migration, every capture must still produce its expected output.

## Run

From the repo root (not from inside `tests/`):

```powershell
python -m pip install pytest
python -m pytest rule_engine -v
```

## Why it's not in Docker

The tests don't need Docker, Postgres or Firebase, only Python and pytest, so they run faster locally. Adding pytest to the backend image would put a test tool in production. The plan is to run them automatically on every PR with GitHub Actions instead, as a CI (Continuous Integration) pipeline.

