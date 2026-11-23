"""
Virtual Garage API.

Runs inside the website container next to the Vite dev server and is
published on host port 8000.

Endpoints:
    GET  /health
    GET  /recalls?make=honda&model=civic&year=2012
    GET  /vin/{vin}               decode a VIN (NHTSA vPIC)
    GET  /vin/{vin}/recalls       decode a VIN, then look up its recalls
    POST /captures
"""

from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from nhtsa_recalls import RecallLookup, RecallsClient, VinLookup, VinStatus

app = FastAPI(title="Virtual Garage API")

# The React dev server runs on a different origin, so it needs CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# One client for the process -- the response cache lives on the instance.
client = RecallsClient()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/recalls")
def recalls(
    make: str = Query(..., examples=["honda"]),
    model: str = Query(..., examples=["civic"]),
    year: int = Query(..., ge=1966, le=2030),
):
    return _recalls_json(client.get_recalls(make, model, year))


@app.get("/vin/{vin}")
def decode_vin(vin: str):
    decoded = client.decode_vin(vin)
    _raise_for_vin(decoded)
    return _vin_json(decoded)


@app.get("/vin/{vin}/recalls")
def recalls_by_vin(vin: str):
    decoded, recalls = client.get_recalls_by_vin(vin)
    _raise_for_vin(decoded)
    return {
        "vin": _vin_json(decoded),
        "recalls": _recalls_json(recalls) if recalls else None,
    }


def _raise_for_vin(decoded: VinLookup) -> None:
    if decoded.status is VinStatus.INVALID:
        raise HTTPException(status_code=422, detail=decoded.message or "Invalid VIN.")
    if decoded.status is VinStatus.ERROR:
        raise HTTPException(status_code=502, detail=f"NHTSA vPIC unavailable: {decoded.message}")


def _vin_json(decoded: VinLookup) -> dict:
    return {
        "status": decoded.status.value,
        "message": decoded.message,
        "error_codes": decoded.error_codes,
        "vehicle": asdict(decoded.vehicle) if decoded.vehicle else None,
    }


def _recalls_json(result: RecallLookup) -> dict:
    return {
        "status": result.status.value,
        "message": result.message,
        "count": len(result.recalls),
        "urgent_count": len(result.urgent),
        "recalls": [
            {
                "campaign_number": r.campaign_number,
                "manufacturer": r.manufacturer,
                "component": r.component,
                "summary": r.summary,
                "consequence": r.consequence,
                "remedy": r.remedy,
                "report_received_date": (
                    r.report_received_date.isoformat() if r.report_received_date else None
                ),
                "park_it": r.park_it,
                "park_outside": r.park_outside,
                "is_urgent": r.is_urgent,
                "nhtsa_url": r.nhtsa_url,
            }
            for r in result.recalls
        ],
    }


@app.post("/captures")
def receive_capture(capture: dict):
    session = capture["session"]
    readings = capture["readings"]
    print(f"Got capture {session['session_id']} from {session['vehicle']}: {len(readings)} readings", flush=True)
    return {"status": "received", "session_id": session["session_id"], "readings": len(readings)}
