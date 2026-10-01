"""
NHTSA Recalls client for Virtual Garage.

Wraps https://api.nhtsa.gov/recalls/recallsByVehicle
No API key, no rate limit published. Free federal data.

Usage:
    client = RecallsClient()
    result = client.get_recalls("acura", "rdx", 2012)
    if result.status is LookupStatus.OK:
        for r in result.recalls:
            print(r.campaign_number, r.component)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.nhtsa.gov"
RECALLS_ENDPOINT = f"{BASE_URL}/recalls/recallsByVehicle"
MAKES_ENDPOINT = f"{BASE_URL}/products/vehicle/makes"
MODELS_ENDPOINT = f"{BASE_URL}/products/vehicle/models"


class LookupStatus(Enum):
    """Why a lookup returned the recalls (or didn't)."""

    OK = "ok"                            # recalls found
    NO_RECALLS = "no_recalls"            # vehicle is real, record is clean
    UNKNOWN_VEHICLE = "unknown_vehicle"  # NHTSA doesn't know this make/model/year
    ERROR = "error"                      # network or API failure


@dataclass(frozen=True)
class Recall:
    """One recall campaign, normalized to snake_case."""

    campaign_number: str
    manufacturer: str
    component: str
    summary: str
    consequence: str
    remedy: str
    notes: str
    report_received_date: date | None
    park_it: bool
    park_outside: bool

    @property
    def is_urgent(self) -> bool:
        """NHTSA telling owners not to drive, or not to park indoors."""
        return self.park_it or self.park_outside

    @property
    def nhtsa_url(self) -> str:
        return f"https://www.nhtsa.gov/recalls#{self.campaign_number}"

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "Recall":
        return cls(
            campaign_number=raw.get("NHTSACampaignNumber", ""),
            manufacturer=raw.get("Manufacturer", ""),
            component=raw.get("Component", ""),
            summary=raw.get("Summary", ""),
            consequence=raw.get("Consequence", ""),
            remedy=raw.get("Remedy", ""),
            notes=raw.get("Notes", ""),
            report_received_date=_parse_date(raw.get("ReportReceivedDate")),
            # note the capital S in parkOutSide -- that's NHTSA's spelling
            park_it=bool(raw.get("parkIt", False)),
            park_outside=bool(raw.get("parkOutSide", False)),
        )


@dataclass
class RecallLookup:
    """Result of a lookup, including why it came back empty."""

    status: LookupStatus
    recalls: list[Recall] = field(default_factory=list)
    message: str = ""

    @property
    def urgent(self) -> list[Recall]:
        return [r for r in self.recalls if r.is_urgent]


def _parse_date(value: str | None) -> date | None:
    """NHTSA sends dd/mm/yyyy. Returns None rather than raising on junk."""
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


class RecallsClient:
    """Thin client with retries, timeouts and an in-memory TTL cache.

    Recall data changes on the order of weeks, so cache aggressively.
    In Virtual Garage this sits behind VehicleDataProvider alongside
    the vPIC decoder and CarVector.
    """

    def __init__(self, timeout: float = 10.0, cache_ttl: int = 86_400) -> None:
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._cache: dict[tuple, tuple[float, Any]] = {}

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "VirtualGarage/0.1 (student project)"})
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    # ------------------------------------------------------------------ #

    def get_recalls(self, make: str, model: str, model_year: int | str) -> RecallLookup:
        """Recalls for one vehicle.

        NHTSA returns Count: 0 both for a clean vehicle and for a make/model
        it doesn't recognize, so a zero result is verified against the
        makes/models catalog before being reported as UNKNOWN_VEHICLE.
        """
        params = {"make": make.strip(), "model": model.strip(), "modelYear": str(model_year)}

        try:
            payload = self._get(RECALLS_ENDPOINT, params)
        except requests.RequestException as exc:
            return RecallLookup(LookupStatus.ERROR, message=str(exc))

        results = payload.get("results") or []
        if results:
            return RecallLookup(
                LookupStatus.OK,
                recalls=[Recall.from_api(r) for r in results],
                message=payload.get("Message", ""),
            )

        if self.vehicle_exists(make, model, model_year):
            return RecallLookup(LookupStatus.NO_RECALLS, message="No open recalls on record.")
        return RecallLookup(
            LookupStatus.UNKNOWN_VEHICLE,
            message=f"NHTSA has no recall catalog entry for {model_year} {make} {model}.",
        )

    def vehicle_exists(self, make: str, model: str, model_year: int | str) -> bool:
        """True if NHTSA's recall catalog lists this make and model for the year."""
        try:
            models = self.get_models(make, model_year)
        except requests.RequestException:
            return True  # can't verify -- don't claim the vehicle is unknown
        return model.strip().lower() in {m.lower() for m in models}

    def get_makes(self, model_year: int | str) -> list[str]:
        payload = self._get(MAKES_ENDPOINT, {"modelYear": str(model_year), "issueType": "r"})
        return [r.get("make", "") for r in payload.get("results", [])]

    def get_models(self, make: str, model_year: int | str) -> list[str]:
        payload = self._get(
            MODELS_ENDPOINT,
            {"modelYear": str(model_year), "make": make.strip(), "issueType": "r"},
        )
        return [r.get("model", "") for r in payload.get("results", [])]

    # ------------------------------------------------------------------ #

    def _get(self, url: str, params: dict[str, str]) -> dict[str, Any]:
        key = (url, tuple(sorted(params.items())))
        hit = self._cache.get(key)
        if hit and time.time() - hit[0] < self.cache_ttl:
            return hit[1]

        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        self._cache[key] = (time.time(), payload)
        return payload


if __name__ == "__main__":
    client = RecallsClient()

    for make, model, year in [
        ("acura", "rdx", 2012),
        ("honda", "civic", 2012),
        ("honda", "civicc", 2012),  # typo -- should report UNKNOWN_VEHICLE
    ]:
        result = client.get_recalls(make, model, year)
        print(f"\n{year} {make} {model}  ->  {result.status.value}")

        if result.status is LookupStatus.OK:
            print(f"  {len(result.recalls)} recall(s), {len(result.urgent)} urgent")
            for r in result.recalls[:3]:
                flag = "  [URGENT]" if r.is_urgent else ""
                print(f"  - {r.campaign_number}: {r.component}{flag}")
                print(f"      remedy: {r.remedy[:90]}...")
        else:
            print(f"  {result.message}")
