from rule_engine.graph import diagnose, load_graph
import pytest


@pytest.fixture(scope="module") #test file reads graph once from neo4j, to avoid time bloat in testing
def graph():
    return load_graph()

def test_load_graph_notEmpty(graph):
    assert graph is not None
    assert len(graph) > 0

def test_Causes(graph):
    #causes_of is a dict that answers: what are the possible causes of this DTC?
    #to check if causes of p0171 are correct according to the dict below
    #{'P0171': ['vacuum_leak', 'maf_sensor', 'fuel_delivery']}
    assert "vacuum_leak" in graph["causes_of"]["P0171"]
    assert "maf_sensor" in graph["causes_of"]["P0171"]
    assert "fuel_delivery" in graph["causes_of"]["P0171"]
    

def test_prior_of(graph):
    #prior_of is a dict that answers: how likely is this cause, before looking at any sensor data?
    #to check if prior_of of p0171 is correct according to the dict below
    #prior_of': {('fuel_delivery', 'P0171'): 0.25, ('maf_sensor', 'P0171'): 0.35, ('vacuum_leak', 'P0171'): 0.4}

    assert graph["prior_of"][("fuel_delivery", "P0171")] == 0.25
    assert graph["prior_of"][("maf_sensor", "P0171")] == 0.35
    assert graph["prior_of"][("vacuum_leak", "P0171")] == 0.4

def test_rules_for(graph):
    #rules_for is a dict that answers: what are the rules that support or refute this cause?
    

    #check that every cause has rules
    assert "fuel_delivery" in graph["rules_for"]
    assert "maf_sensor" in graph["rules_for"]
    assert "vacuum_leak" in graph["rules_for"]


    #check every rule exists in the rules_for dict and that the cause, effect, and weight are correct
    rules = {}
    for item in graph["rules_for"].values(): #item = one cause's list of rules
        for rule in item: #rule is the dict with the rule's details
            rules[rule["id"]] = rule 
            #print("\n", rule["id"])

    assert "lean_under_load" in rules
    assert "lean_at_idle_only" in rules
    assert "lean_everywhere" in rules
    assert "lean_everywhere_not_vacuum" in rules
    assert rules["lean_under_load"]["then"]["cause"] == 'fuel_delivery'
    assert rules["lean_under_load"]["then"]["effect"] == 'supports'
    assert rules["lean_under_load"]["then"]["weight"] == 2
    

    assert rules["lean_at_idle_only"]["then"]["cause"] == 'vacuum_leak'
    assert rules["lean_at_idle_only"]["then"]["effect"] == 'supports'
    assert rules["lean_at_idle_only"]["then"]["weight"] == 2
    
    assert rules["lean_everywhere"]["then"]["cause"] == 'maf_sensor'
    assert rules["lean_everywhere"]["then"]["effect"] == 'supports'
    assert rules["lean_everywhere"]["then"]["weight"] == 2
    
    assert rules["lean_everywhere_not_vacuum"]["then"]["cause"] == 'vacuum_leak'
    assert rules["lean_everywhere_not_vacuum"]["then"]["effect"] == 'refutes'
    assert rules["lean_everywhere_not_vacuum"]["then"]["weight"] == 1
    
def test_conditions(graph):
    #conditions is a dict that answers: what are the conditions of the engine?
    #check that every condition exists in the conditions dict and that the type, sensor, and threshold are correct
  
    
    assert "high_load" in graph["conditions"]
    assert graph["conditions"]["high_load"]["check"] == "above"
    assert graph["conditions"]["high_load"]["pid"] == "ENGINE_LOAD"
    assert graph["conditions"]["high_load"]["value"] == 60

    assert "high_rpm" in graph["conditions"]
    assert graph["conditions"]["high_rpm"]["check"] == "above"
    assert graph["conditions"]["high_rpm"]["pid"] == "RPM"
    assert graph["conditions"]["high_rpm"]["value"] == 2000

    assert "idle" in graph["conditions"]
    assert graph["conditions"]["idle"]["check"] == "below"
    assert graph["conditions"]["idle"]["pid"] == "RPM"
    assert graph["conditions"]["idle"]["value"] == 1000

def test_nodes(graph):
    #nodes is a dict that holds the nodes and their details

    assert "P0171" in graph["nodes"]
    assert graph["nodes"]["P0171"]["description"] == "System too lean, bank 1"
    assert graph["nodes"]["P0171"]["type"] == "dtc"

    assert "fuel_delivery" in graph["nodes"]
    assert graph["nodes"]["fuel_delivery"]["repair_tier"] == "moderate"
    assert graph["nodes"]["fuel_delivery"]["type"] == "cause"

    assert "maf_sensor" in graph["nodes"]
    assert graph["nodes"]["maf_sensor"]["repair_tier"] == "minor"
    assert graph["nodes"]["maf_sensor"]["type"] == "cause"

    assert "vacuum_leak" in graph["nodes"]
    assert graph["nodes"]["vacuum_leak"]["repair_tier"] == "minor"
    assert graph["nodes"]["vacuum_leak"]["type"] == "cause"