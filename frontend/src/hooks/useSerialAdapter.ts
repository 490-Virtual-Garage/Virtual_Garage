import { useCallback, useRef, useState } from "react";

export type Send = (cmd: string, timeoutMs?: number) => Promise<string>;

const MAX_LOG_LINES = 200;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function useSerialAdapter() {
    const portRef = useRef<SerialPort | null>(null);
    const writerRef = useRef<WritableStreamDefaultWriter | null>(null);
    const readerRef = useRef<ReadableStreamDefaultReader | null>(null);
    const loopRef = useRef<Promise<void> | null>(null);
    const bufferRef = useRef("");
    const [connected, setConnected] = useState(false);
    const [log, setLog] = useState<string[]>([]);

    const addLog = (line: string) => setLog((l) => [...l.slice(-(MAX_LOG_LINES - 1)), line]);

    const connect = useCallback(async (baudRate = 115200) => {
        if (!("serial" in navigator)) throw new Error("Web Serial needs Chrome or Edge");
        if (portRef.current) return; // already connected

        const port = await navigator.serial.requestPort(); //must come from a click
        await port.open({ baudRate });

        let writer: WritableStreamDefaultWriter;
        let reader: ReadableStreamDefaultReader;
        try {
            writer = port.writable!.getWriter();
            reader = port.readable!.getReader();
        } catch (e) {
            await port.close().catch(() => {});
            throw e;
        }

        portRef.current = port;
        writerRef.current = writer;
        readerRef.current = reader;
        const decoder = new TextDecoder();

        loopRef.current = (async () => {
            try {
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    if (value) bufferRef.current += decoder.decode(value, { stream: true });
                }
            } catch {
                /* adapter unplugged or port errored */
            } finally {
                // Single cleanup path for both unplug and user disconnect
                try { reader.releaseLock(); } catch { /* ignore */ }
                try { writer.releaseLock(); } catch { /* ignore */ }
                try { await port.close(); } catch { /* already closed / gone */ }
                readerRef.current = null;
                writerRef.current = null;
                portRef.current = null;
                setConnected(false);
            }
        })();

        setConnected(true);
    }, []);

    // After a timeout the adapter may still answer late. Flush it so it can't
    // leak into the next command's reply.
    const resync = async (writer: WritableStreamDefaultWriter) => {
        try {
            bufferRef.current = "";
            await writer.write(new TextEncoder().encode("\r"));
            const start = Date.now();
            while (!bufferRef.current.includes(">") && Date.now() - start < 1000) {
                await sleep(20);
            }
        } catch {
            /* port is gone, nothing to flush */
        } finally {
            bufferRef.current = "";
        }
    };

    const send: Send = useCallback(async (cmd, timeoutMs = 5000) => {
        const writer = writerRef.current;
        if (!writer) return "NOT CONNECTED";

        bufferRef.current = "";
        try {
            await writer.write(new TextEncoder().encode(cmd + "\r"));
        } catch {
            addLog(`${cmd} -> NOT CONNECTED (write failed)`);
            return "NOT CONNECTED";
        }

        const start = Date.now();
        while (!bufferRef.current.includes(">")) {
            if (!writerRef.current) return "NOT CONNECTED"; // unplugged while waiting
            if (Date.now() - start > timeoutMs) {
                addLog(`${cmd} -> TIMEOUT ${JSON.stringify(bufferRef.current)}`);
                await resync(writer);
                return "TIMEOUT";
            }
            await sleep(20);
        }
        const reply = bufferRef.current.replace(">", "").trim();
        addLog(`${cmd} -> ${JSON.stringify(reply)}`); // raw reply, always logged
        return reply;
    }, []);

    const disconnect = useCallback(async () => {
        try {
            await readerRef.current?.cancel(); // makes the read loop exit and run its cleanup
        } catch {
            /* ignore */
        }
        await loopRef.current;
        setConnected(false);
    }, []);

    return { connect, send, disconnect, connected, log };
}