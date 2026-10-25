import json


def load_graph(path):
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

    # final graph dictionary with all the data
    graph = {
        "causes_of": causes_of,
        "rules_for": rules_for,
        "nodes": data["nodes"],
        "conditions": data["conditions"],
        "edges": data["edges"],
    }
    return graph


if __name__ == "__main__":
    graph = load_graph("dtc_pid.json")

    for dtc, causes in graph["causes_of"].items():
        print(f"{dtc} can be caused by: {causes}")

    for cause, rules in graph["rules_for"].items():
        print(f"{cause} rules: {[r['id'] for r in rules]}")
