from rule_engine.graph import diagnose, load_graph
import pytest
import json
from pathlib import Path



HERE = Path(__file__).parent
CAPTURE_DATA_PATH = HERE / "sample_captures"
CAPTURE_OUTPUT_PATH = HERE / "expected_outputs"

@pytest.fixture
def graph():
    return load_graph()

@pytest.mark.parametrize("name", ["no_dtc", "p0171_vacuum_leak", "p0171_maf", "p0171_fuel"])
def test_diagnose(graph, name):

    with open(CAPTURE_DATA_PATH / f"{name}.json", "r", encoding="utf-8") as file:
        captured_data = json.load(file)
    with open(CAPTURE_OUTPUT_PATH / f"{name}.json", "r", encoding="utf-8") as file:
        expected_output = json.load(file)

    check_dict = diagnose(graph, captured_data)
    assert check_dict == expected_output



