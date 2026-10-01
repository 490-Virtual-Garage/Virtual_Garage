"""
HTTP service wrapping the NHTSA recalls client.

Runs as its own container on virtual-garage-net so the web container
can reach it at http://virtual-garage-recalls:8000

Endpoints:
    GET /health
    GET /recalls?make=honda&model=civic&year=2012
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from nhtsa_recalls import LookupStatus, RecallsClient

app = FastAPI(title="Virtual Garage - Recalls")

# The React dev server runs on a different origin, so it needs CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
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
    result = client.get_recalls(make, model, year)

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
