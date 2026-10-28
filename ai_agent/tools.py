# ai_agent/tools.py

def get_obd_data():
    """
    Temporary simulated OBD-II data.
    Replace with your OBD backend integration.
    """

    return {
        "source": "simulation",
        "rpm": 850,
        "coolant_temp_c": 92,
        "dtcs": ["P0171"],
        "stft_bank1": 12.0,
        "ltft_bank1": 18.0
    }


def get_diagnosis():
    """
    Temporary simulated rule-engine output.
    Replace with actual diagnosis results.
    """

    return {
        "dtc": "P0171",
        "candidates": [
            {
                "component_key": "intake_air_leak",
                "likelihood": "high",
                "recommended_test": "inspect_intake_leaks"
            },
            {
                "component_key": "maf_sensor",
                "likelihood": "medium",
                "recommended_test": "inspect_maf_readings"
            }
        ]
    }