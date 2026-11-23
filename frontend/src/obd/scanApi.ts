export type ScanKind = "stored" | "pending" | "permanent";

export interface ScanPayload {
    protocol: string; //raw ATDPN reply, so the backend can tell if it's CAN
    scannedAt: string;
    results: Partial<Record<ScanKind, string>>; //raw hex text per kind
}

export interface DtcResult {
    code: string;
    status: ScanKind;
    description: string | null;
}

export async function submitScan(scan: ScanPayload): Promise<DtcResult[]> {
    const res = await fetch("/api/scans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        //add auth here (Authorization header or credentials: "include") once your backend requires it
        body: JSON.stringify(scan),
    });
    if (!res.ok) throw new Error(`Backend error ${res.status}`);
    return res.json();
}