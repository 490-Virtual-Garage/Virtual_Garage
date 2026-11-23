import type { Send } from "../hooks/useSerialAdapter";
import type { ScanKind, ScanPayload } from "./scanApi";

const MODES: Record<ScanKind, string> = { stored: "03", pending: "07", permanent: "0A" };

// "BUS INIT: OK" is a success on K-line cars, so only match the error forms.
const ERROR_RE =
  /NO DATA|UNABLE TO CONNECT|BUS INIT:\s*(\.\.\.)?\s*ERROR|CAN ERROR|BUS BUSY|BUS ERROR|FB ERROR|STOPPED|DATA ERROR|BUFFER FULL|TIMEOUT|NOT CONNECTED|\?/;

const isError = (reply: string) => ERROR_RE.test(reply);
const isNoData = (reply: string) => reply.includes("NO DATA");
const isDead = (reply: string) => reply === "NOT CONNECTED" || reply === "TIMEOUT";

export interface RetrieveResult {
  payload: ScanPayload | null; //null = never got a usable reply from the car
  failures: Partial<Record<ScanKind, string>>; //why each kind failed
  fatal: string | null; //set when the whole scan was aborted
}

const abort = (fatal: string): RetrieveResult => ({ payload: null, failures: {}, fatal });

export async function retrieveObdHex(send: Send): Promise<RetrieveResult> {
  for (const cmd of ["ATZ", "ATE0", "ATL0", "ATS1", "ATH0", "ATSP0"]) {
    const reply = await send(cmd);
    if (reply === "NOT CONNECTED") return abort("Adapter disconnected");
    if (reply === "TIMEOUT") return abort(`Adapter didn't answer ${cmd}. Check the connection and baud rate`);
  }

  //Wakes the car and triggers protocol detection, which can take 10+ seconds
  const probe = await send("0100", 15000);
  if (probe === "NOT CONNECTED") return abort("Adapter disconnected");
  if (isError(probe)) {
    return abort(`Couldn't talk to the car (${probe}). Turn the ignition on and retry`);
  }
  const protocol = await send("ATDPN");

  const results: ScanPayload["results"] = {};
  const failures: RetrieveResult["failures"] = {};

  for (const kind of Object.keys(MODES) as ScanKind[]) {
    const reply = await send(MODES[kind]);
    if (reply === "NOT CONNECTED") return abort("Adapter disconnected mid-scan");

    if (isNoData(reply) && kind !== "stored") {
      results[kind] = ""; // clean cars commonly answer NO DATA for 07/0A: no codes, not a failure
    } else if (isError(reply)) {
      failures[kind] = reply;
    } else {
      results[kind] = reply;
    }
  }

  if (Object.keys(results).length === 0) return { payload: null, failures, fatal: null };
  return {
    payload: { protocol, scannedAt: new Date().toISOString(), results },
    failures,
    fatal: null,
  };
}