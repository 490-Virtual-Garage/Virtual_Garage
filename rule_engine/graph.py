import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent   # the folder graph.py lives in (rule_engine/)


def load_graph(path=HERE / "dtc_pid.json"): #so fastAPI can call load_graph() without providing the path
    """Load the diagnostic knowledge file and build the graph's lookup tables."""
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # DTC -> list of cause IDs that can produce it
    # as of right now this only supports one specific DTC with its set of possible causes
    # DTC P0171, “System Too Lean, Bank 1" in the future more DTC will be added to the json file and this will support them as well
    causes_of = {}
    for edge in data["edges"]:
        dtc = edge["to"]
        if dtc not in causes_of:
            causes_of[dtc] = []
        causes_of[dtc].append(edge["from"])

    # cause ID -> list of rules that support or refute it (the rules are from the json file)
    rules_for = {}
    for rule in data["rules"]:
        cause = rule["then"]["cause"]
        if cause not in rules_for:
            rules_for[cause] = []
        rules_for[cause].append(rule)

    prior_of = {}
    for edge in data["edges"]:
        prior_of[(edge["from"], edge["to"])] = edge["prior"]

    # final graph dictionary with all the data
    graph = {
        "causes_of": causes_of,
        "rules_for": rules_for,
        "nodes": data["nodes"],
        "conditions": data["conditions"],
        "edges": data["edges"],
        "prior_of": prior_of,
    }
    return graph


def group_readings(captured_data):
    """Group the capture's readings by PID: PID -> list of (time, value)."""
    grouped = {}
    for reading in captured_data["readings"]:
        if (
            reading["value"] is None
        ):  # skip failed reads (car couldn't respont to PID request or the PID isn't supported)
            continue
        pid = reading["pid"]
        if pid not in grouped:
            grouped[pid] = []
        seconds = datetime.fromisoformat(reading["t"]).timestamp()
        grouped[pid].append((seconds, reading["value"]))
    return grouped


def nearest_value(values, t):
    """Get the nearest value for one PIDs list at target time t, helper function for building moments."""

    best = values[
        0
    ]  # the best pair of (time,value) found so far, its the first thing in the list [0 => time][1 => value]
    gap = abs(best[0] - t)  # the gap between the best time and the target time

    for time, value in values:
        new_gap = abs(time - t)
        if new_gap < gap:
            best = (time, value)
            gap = new_gap
    return best[1]  # return the value of the best pair found so far


def build_moments(grouped):
    """One moment per RPM reading: a dict of every PID's nearest value at that time."""
    moments = []

    if (
        "RPM" not in grouped
    ):  # no RPM, no timeline to build on since the RPM should be present
        return moments

    for t, rpm in grouped["RPM"]:
        moment = {"t": t}
        for pid, values in grouped.items():
            moment[pid] = nearest_value(values, t)
        moments.append(moment)  # once per RPM reading, not per PID

    return moments  # snapshots of the car's state [rpm, engine load, long fuel trim, etc..] at each time the RPM was read


def in_condition(moment, condition):
    """Check if a moment satisfies a condition."""
    # for example, if the condition is high rpm, low engine load etc... check if the moment satisfies that condition

    pid = condition["pid"]  # find which PID this condition is reffering to
    if pid not in moment:
        return False
    value = moment[
        pid
    ]  # get the value of that PID at this moment, then check if those values are under or over the thresholds
    # for their respective conditions
    if condition["check"] == "below":
        return value < condition["value"]
    if condition["check"] == "above":
        return value > condition["value"]
    else:
        return False


def check_clause(clause, moments, conditions):
    """Check if a moment satisfies a clause during that condition."""
    condition = conditions[
        clause["during"]
    ]  # get the condition that this clause is reffering to"]

    values = []  # get the values of the PID in this clause for all moments that satisfy the condition
    for moment in moments:
        if in_condition(moment, condition) and clause["pid"] in moment:
            values.append(moment[clause["pid"]])

    if not values:  # the engine was never in this condition to begin with
        return "unknown", None
    average = sum(values) / len(values)

    # Step 5: compare the average to the clause's limit
    if clause["check"] == "above":
        return average > clause["value"], average
    if clause["check"] == "below":
        return average < clause["value"], average
    return "unknown", average


def check_rule(rule, moments, conditions):
    """Check if a rule is satisfied by the moments and conditions."""
    evidence = []
    any_unknown = False

    for clause in rule["if"]:
        result, average = check_clause(
            clause, moments, conditions
        )  # check if the clause is satisfied by the moments and conditions
        evidence.append(
            {"pid": clause["pid"], "during": clause["during"], "average": average}
        )
        # "fired' in this context means that the rule is satisfied by the IF condition
        if result is False:
            return "not_fired", evidence
        if result == "unknown":
            any_unknown = True

    if any_unknown:
        return "unknown", evidence
    return "fired", evidence


def add_test_dtc(captured_data, graph):
    """Add a test DTC to the captured data for testing purposes, this is for testing only (p0171 for now)"""
    stored = captured_data["dtcs"]["stored"]
    existing_codes = [entry[0] for entry in stored]  # codes already in the capture

    for node_id, node in (
        graph["nodes"].items()
    ):  # append dtc to the capture session's stored list if its not already there
        if node["type"] == "dtc" and node_id not in existing_codes:
            stored.append([node_id, node["description"]])


def diagnose(graph, captured_data):
    """Diagnose possible causes based on OBD data against the inference engine rules and causes."""
    new_list = captured_data["dtcs"]["stored"] + captured_data["dtcs"]["pending"]
    codes = []
    for entry in new_list:
        if entry[0] not in codes:
            codes.append(entry[0])

    if len(codes) == 0:
        return {
            "status": "no_dtc",
            "message": "no trouble codes reported",
            "causes": [],
        }
    moments = build_moments(group_readings(captured_data))

    results, unknown_dtcs = [], []

    for code in codes:
        if code not in graph["causes_of"]:
            unknown_dtcs.append(code)
            continue
        for cause in graph["causes_of"][code]:
            score = graph["prior_of"][(cause, code)]
            evidence, not_checked = [], []

            for rule in graph["rules_for"].get(cause, []):
                status, rule_evidence = check_rule(rule, moments, graph["conditions"])
                if status == "fired":
                    if rule["then"]["effect"] == "supports":
                        score += rule["then"]["weight"]
                    else:
                        score -= rule["then"]["weight"]
                    evidence.append({"rule_id": rule["id"], "explanation": rule["explain"], "readings": rule_evidence})
                elif status == "unknown":
                    not_checked.append(rule["id"])
            node = graph["nodes"][cause]
            results.append({
                "dtc": code,
                "cause": cause,
                "name": node["name"],
                "repair_tier": node["repair_tier"],
                "score": round(score, 2),
                "evidence": evidence,
                "not_checked": not_checked,
            })
    results.sort(key=lambda r: r["score"], reverse=True)
    return {"status": "ok", "dtcs": codes, "unknown_dtcs": unknown_dtcs, "causes": results}

           
if __name__ == "__main__":
    graph = load_graph()
    with open(HERE / "samplecapture.json", "r", encoding="utf-8") as file:
        captured_data = json.load(file)
    # for dtc, causes in graph["causes_of"].items():
    # print(f"{dtc} can be caused by: {causes}")

    # for cause, rules in graph["rules_for"].items():
    # print(f"{cause} rules: {[r['id'] for r in rules]}")

    add_test_dtc(captured_data, graph)
    print(json.dumps(diagnose(graph, captured_data), indent=2))
