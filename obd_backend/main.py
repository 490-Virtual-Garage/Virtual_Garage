from fastapi import FastAPI

app = FastAPI()


@app.post("/captures")
def receive_capture(capture: dict):
    session = capture["session"]
    readings = capture["readings"]
    print(f"Got capture {session['session_id']} from {session['vehicle']}: {len(readings)} readings", flush=True)
    return {"status": "received", "session_id": session["session_id"], "readings": len(readings)}