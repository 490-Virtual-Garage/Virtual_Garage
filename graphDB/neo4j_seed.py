import json
from pathlib import Path
from neo4j_client import get_driver, NEO4J_DATABASE

KB_PATH = Path(__file__).resolve().parent.parent / "rule_engine" / "dtc_pid.json"

CONSTRAINTS = [
    "CREATE CONSTRAINT dtc_id IF NOT EXISTS FOR (n:DTC) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT cause_id IF NOT EXISTS FOR (n:Cause) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT condition_id IF NOT EXISTS FOR (n:Condition) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT rule_id IF NOT EXISTS FOR (n:Rule) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT clause_id IF NOT EXISTS FOR (n:Clause) REQUIRE n.id IS UNIQUE",
]

CONDITIONS = """
UNWIND $rows AS row
MERGE (c:Condition {id: row.id})
SET c.pid = row.pid, c.check = row.check, c.value = row.value
"""

DTCS = """
UNWIND $rows AS row
MERGE (d:DTC {id: row.id})
SET d.description = row.description
"""

CAUSES = """
UNWIND $rows AS row
MERGE (c:Cause {id: row.id})
SET c.name = row.name, c.repair_tier = row.repair_tier
"""

# JSON stores cause -CAN_CAUSE-> dtc; graph stores DTC -CAUSED_BY-> Cause
EDGES = """
UNWIND $rows AS row
MATCH (d:DTC {id: row.to}), (c:Cause {id: row.from})
MERGE (d)-[r:CAUSED_BY]->(c)
SET r.prior = row.prior
"""

RULES_SUPPORTS = """
UNWIND $rows AS row
MATCH (c:Cause {id: row.cause})
MERGE (r:Rule {id: row.id})
SET r.explain = row.explain
MERGE (r)-[e:SUPPORTS]->(c)
SET e.weight = row.weight
"""

RULES_REFUTES = """
UNWIND $rows AS row
MATCH (c:Cause {id: row.cause})
MERGE (r:Rule {id: row.id})
SET r.explain = row.explain
MERGE (r)-[e:REFUTES]->(c)
SET e.weight = row.weight
"""

CLAUSES = """
UNWIND $rows AS row
MATCH (r:Rule {id: row.rule}), (cond:Condition {id: row.during})
MERGE (cl:Clause {id: row.id})
SET cl.pid = row.pid, cl.check = row.check, cl.value = row.value, cl.order = row.order
MERGE (r)-[:HAS_CLAUSE]->(cl)
MERGE (cl)-[:DURING]->(cond)
"""


def seed(driver, kb):
    def run(query, **params):
        return driver.execute_query(query, database_=NEO4J_DATABASE, **params)

    for q in CONSTRAINTS:
        run(q)

    run(CONDITIONS, rows=[{"id": k, **v} for k, v in kb["conditions"].items()])

    nodes = kb["nodes"]
    run(DTCS, rows=[{"id": k, **v} for k, v in nodes.items() if v["type"] == "dtc"])
    run(CAUSES, rows=[{"id": k, **v} for k, v in nodes.items() if v["type"] == "cause"])

    run(EDGES, rows=kb["edges"])

    rule_rows = [
        {"id": r["id"], "explain": r["explain"], **r["then"]} for r in kb["rules"]
    ]
    run(RULES_SUPPORTS, rows=[r for r in rule_rows if r["effect"] == "supports"])
    run(RULES_REFUTES, rows=[r for r in rule_rows if r["effect"] == "refutes"])

    clause_rows = [
        {"id": f'{r["id"]}_{i}', "rule": r["id"], "order": i, **clause}
        for r in kb["rules"]
        for i, clause in enumerate(r["if"])
    ]
    run(CLAUSES, rows=clause_rows)


if __name__ == "__main__":
    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    with get_driver() as driver:
        seed(driver, kb)
    print("seeded")