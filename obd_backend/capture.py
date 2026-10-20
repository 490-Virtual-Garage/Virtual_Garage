import json, os, time, uuid
from datetime import datetime
import obd
import urllib.request
import urllib.error

PORT = "COM3"
API_URL = "http://127.0.0.1:8000/captures"
DURATION_S = 60
VEHICLE = "2025 Hyundai Elantra"

WANTED = [obd.commands.RPM, obd.commands.SPEED, obd.commands.ENGINE_LOAD,
          obd.commands.THROTTLE_POS, obd.commands.INTAKE_TEMP, obd.commands.MAF,
          obd.commands.SHORT_FUEL_TRIM_1, obd.commands.LONG_FUEL_TRIM_1, obd.commands.O2_B1S1]


def now():
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def to_row(cmd, response):
    if response.is_null():
        value, unit = None, None
    else:
        value = response.value.magnitude
        unit = str(response.value.units)
    return {"t": now(), "pid": cmd.name, "value": value, "unit": unit}


def dtc_list(response):
    # python-obd gives DTCs as (code, description) tuples; JSON wants dicts
    if response.is_null() or not response.value:
        return []
    return [{"code": code, "description": desc} for code, desc in response.value]


def post_capture(capture):
    data = json.dumps(capture).encode("utf-8")
    request = urllib.request.Request(
        API_URL, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            print("Uploaded:", response.status, json.loads(response.read()))
    except urllib.error.URLError as e:
        print("Upload failed (capture is still saved locally):", e)

def main():
    conn = obd.OBD(portstr=PORT, baudrate=115200, fast=False, timeout=10)
    if conn.status() != obd.OBDStatus.CAR_CONNECTED:
        print("Could not reach the car.")
        conn.close()
        return

    # TODO 1: session info
    vin = conn.query(obd.commands.VIN)
    vin = None if vin.is_null() else vin.value
    if isinstance(vin, (bytes, bytearray)):
        vin = vin.decode(errors="ignore").strip()

    session = {
        "session_id": str(uuid.uuid4()),
        "vehicle": VEHICLE,
        "vin": vin,
        "protocol": conn.protocol_name(),
        "started_at": now(),
        "ended_at": None,
    }
    print("Session:", session)

    # TODO 2: only poll the PIDs this car actually supports
    pids = [cmd for cmd in WANTED if conn.supports(cmd)]
    print("Polling:", [cmd.name for cmd in pids])

    # TODO 3: stored and pending DTCs
    dtcs = {
        "stored": dtc_list(conn.query(obd.commands.GET_DTC)),
        "pending": dtc_list(conn.query(obd.commands.GET_CURRENT_DTC)),
    }
    print("DTCs:", dtcs)

    # TODO 4: polling loop
    readings = []
    start = time.monotonic()
    print(f"Capturing for {DURATION_S}s (Ctrl+C to stop early)...")
    try:
        while time.monotonic() - start < DURATION_S:
            for cmd in pids:
                readings.append(to_row(cmd, conn.query(cmd)))
    except KeyboardInterrupt:
        print("Stopped early, saving what was captured.")
    finally:
        conn.close()

    # TODO 5: save to captures/<timestamp>.json
    session["ended_at"] = now()
    capture = {
        "session": session,
        "supported_pids": [cmd.name for cmd in pids],
        "dtcs": dtcs,
        "readings": readings,
    }
    os.makedirs("captures", exist_ok=True)
    filename = datetime.now().strftime("captures/%Y-%m-%d_%H-%M-%S.json")
    with open(filename, "w") as f:
        json.dump(capture, f, indent=2)
    print(f"Saved {len(readings)} readings to {filename}")

    post_capture(capture) 
    
if __name__ == "__main__":
    main()