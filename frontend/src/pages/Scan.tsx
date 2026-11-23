import { useState } from "react";
import { useSerialAdapter } from "../hooks/useSerialAdapter";
import { retrieveObdHex } from "../obd/retrieveObdHex";
import { submitScan, type DtcResult } from "../obd/scanApi";

export default function Scan() {
  const { connect, send, disconnect, connected, log } = useSerialAdapter();
  const [dtcs, setDtcs] = useState<DtcResult[] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleConnect() {
    setError("");
    try {
      await connect();
    } catch (e) {
      if (e instanceof DOMException && e.name === "NotFoundError") return; //user closed the port picker
      setError(e instanceof Error ? e.message : "Couldn't open the adapter");
    }
  }

  async function handleScan() {
    setLoading(true);
    setError("");
    setDtcs(null);
    try {
      const { payload, failures, fatal } = await retrieveObdHex(send);
      if (!payload) {
        //Don't send anything: a failed read must not look like a healthy car
        const detail = Object.values(failures).join(", ");
        setError(fatal ?? `Couldn't read the car: ${detail || "no reply"}`);
        return;
      }

      setDtcs(await submitScan(payload));

      const failed = Object.keys(failures);
      if (failed.length) {
        setError(`Couldn't read: ${failed.join(", ")}. Results below are incomplete.`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button onClick={handleConnect} disabled={connected}>Connect</button>
      <button onClick={handleScan} disabled={!connected || loading}>
        {loading ? "Scanning..." : "Scan"}
      </button>
      <button onClick={disconnect} disabled={!connected}>Disconnect</button>

      {error && <p role="alert">{error}</p>}
      {dtcs && dtcs.length === 0 && !error && <p>No codes found.</p>}
      {dtcs?.map((d) => (
        <div key={`${d.status}-${d.code}`}>
          <strong>{d.code}</strong> ({d.status}): {d.description ?? "No description yet"}
        </div>
      ))}

      <details>
        <summary>Raw adapter log</summary>
        <pre>{log.join("\n")}</pre>
      </details>
    </div>
  );
}