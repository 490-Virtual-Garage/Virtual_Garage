### This branch builds one image and runs two containers: the ELM327 emulator, and a website container that serves the React app and the FastAPI backend (`api.py`) side by side.

# Virtual Garage - Scanner Environment

This is the team's reproducible development environment for the Virtual Garage scanner feature. One image runs as two containers: a simulated ELM327/OBD-II adapter, and a development container that serves the React website, runs the FastAPI backend, and is where you run the Python client. The client asks the adapter for RPM, speed, coolant temperature, and stored DTCs.

## Prerequisite

Install and open Docker Desktop. Teammates do not need to install Python, Node, or the ELM327 emulator directly.

## Build and run it

### 1. Build the image

```bash
docker build -t virtual-garage-elm:dev .
```

This reads the `Dockerfile` and creates a reusable local image named `virtual-garage-elm:dev`. The final `.` means "use this folder as the build context." The image contains Python for the scanner and Node for the website.

### 2. Create the containers' private network

```bash
docker network create virtual-garage-net
```

Run this once per computer. If Docker says the network already exists, that is fine.

### 3. Run the ELM327 emulator

```bash
docker run --detach --interactive --tty \
  --name virtual-garage-emulator \
  --network virtual-garage-net \
  -p 127.0.0.1:35000:35000 \
  virtual-garage-elm:dev \
  python3 -m elm -s car -n 35000 -i 0.0.0.0
```

This starts the simulated OBD-II adapter in the background. `--network` puts it on the private Docker network, and `-p 127.0.0.1:35000:35000` makes its port reachable only from the developer's own computer.

### 4. Run the website

This is the second container. It serves the React app, runs the FastAPI backend, and is also where you run the Python client. It joins the same network, so the emulator's name resolves. The repository is mounted at `/app` so edits show up without a rebuild. The second mount keeps the frontend dependencies from the image, because the repository mount would otherwise hide them.

```bash
docker run --detach \
  --name virtual-garage-web \
  --network virtual-garage-net \
  -p 127.0.0.1:5173:5173 \
  -p 127.0.0.1:8000:8000 \
  --mount type=bind,src="$PWD",dst=/app \
  --mount type=volume,src=virtual-garage-frontend-modules,dst=/app/frontend/node_modules \
  -e ELM_HOST=virtual-garage-emulator \
  -e ELM_PORT=35000 \
  virtual-garage-elm:dev \
  sh /app/dev.sh
```

`dev.sh` starts two processes: Uvicorn serving `api.py` on port 8000 in the background, and the Vite dev server on port 5173 in the foreground. Vite is the main process, so the container stays running as long as the website does, and stopping the container stops Uvicorn too. You get a shell inside it in step 5. `--host 0.0.0.0` lets your browser reach both servers from outside the container.

`ELM_HOST` and `ELM_PORT` tell the Python client where the emulator is, so you don't pass them on every command.

Open [http://localhost:5173](http://localhost:5173) for the website and [http://localhost:8000/docs](http://localhost:8000/docs) for the API.

Both servers log to the same place:

```bash
docker logs virtual-garage-web
```

### 5. Open a shell in the website container

```bash
docker exec -it -w /app virtual-garage-web sh
```

Your prompt changes to `#`. You are now inside the container, in the repository folder. Run the client from there:

```bash
python3 elm_client.py
```

This opens one connection to the emulator and shows a menu:

```text
Connected to ELM327 emulator at virtual-garage-emulator:35000

  1) Engine RPM [010C]
  2) Vehicle speed [010D]
  3) Coolant temperature [0105]
  4) Stored trouble codes (DTCs) [03]
  q) Quit
Choose:
```

Type a number and press Enter to see the raw reply and the decoded value. The connection stays open until you choose `q`, which returns you to the container's shell. Run `python3 elm_client.py` again as often as you like.

The default emulator scenario normally has no stored DTCs, so option 4 replies `43 00`.

To leave the container, type `exit`. The website keeps running, because `exit` only closes this shell.

## Re-run and clean up

To see the emulator's output:

```bash
docker logs virtual-garage-emulator
```

When you are finished:

```bash
docker stop virtual-garage-emulator virtual-garage-web
docker rm virtual-garage-emulator virtual-garage-web
docker network rm virtual-garage-net
```

```bash
docker image rm virtual-garage-elm:dev
```

Edits to the Python files and the React source are picked up without a rebuild: the repository is bind-mounted, Vite hot-reloads the frontend, and Uvicorn runs with `--reload` so saving `api.py` or `nhtsa_recalls.py` restarts the API. A rebuild is only needed when `requirements.txt` or `frontend/package.json` changes. For `frontend/package.json`, also remove the dependency volume before starting the website container again:

```bash
docker volume rm virtual-garage-frontend-modules
```

## API

The scanner tells you what is wrong with a car right now. The API adds two more things: a recalls lookup that asks whether the manufacturer has already issued a safety campaign for a vehicle, and an endpoint that receives OBD captures posted from a laptop plugged into a real car. The recalls lookup reads the free NHTSA recalls API, so it needs no key and no account.

The API runs inside the website container, started by `dev.sh` alongside Vite. There is no separate container or image for it. Port 8000 is published to `127.0.0.1`, which keeps it reachable from your own computer but not from anyone else on your network.

### Files

| File | Purpose |
| --- | --- |
| `api.py` | The FastAPI app. Three routes: `/health`, `/recalls`, `/captures`. Run with `uvicorn api:app`. |
| `nhtsa_recalls.py` | Client for the NHTSA API. Handles retries, caching, and date parsing. |
| `dev.sh` | Starts Uvicorn in the background and Vite in the foreground. This is the website container's command. |
| `obd_backend/capture.py` | Runs on the laptop with the OBD cable, not in a container. See below. |
| `obd_backend/sample_capture.json` | A recorded capture, useful for testing `POST /captures` without a car. |

### Check that it works

With both containers running from steps 3 and 4:

```bash
curl "http://localhost:8000/recalls?make=acura&model=rdx&year=2012"
```

You should get a JSON object back listing the recall campaigns for that vehicle.

```bash
curl -X POST http://localhost:8000/captures \
  -H "Content-Type: application/json" \
  --data-binary @obd_backend/sample_capture.json
```

You should get `{"status":"received","session_id":"...","readings":N}` back, and `docker logs virtual-garage-web` shows a line for the capture.

For a friendlier view, open [http://localhost:8000/docs](http://localhost:8000/docs). FastAPI generates an interactive page where you can fill in the parameters and send the request from the browser.

### Endpoints

| Method | Path | Parameters | Returns |
| --- | --- | --- | --- |
| GET | `/health` | none | `{"status": "ok"}` |
| GET | `/recalls` | `make`, `model`, `year` | Recall campaigns for the vehicle |
| POST | `/captures` | JSON body with `session` and `readings` | `{"status": "received", "session_id": ..., "readings": count}` |

### Reading the recalls response

The `status` field matters more than the recall count, because NHTSA returns an empty result both for a vehicle with a clean record and for a make or model it does not recognize. The service tells these apart by checking NHTSA's own vehicle catalog before reporting an empty result.

| `status` | Meaning |
| --- | --- |
| `ok` | Recalls were found. |
| `no_recalls` | The vehicle is real and has no open recalls. |
| `unknown_vehicle` | NHTSA has no catalog entry for that make, model, and year. Usually a spelling mistake. |
| `error` | The request to NHTSA failed. |

Two fields deserve to be shown prominently in the interface rather than listed alongside the others. `park_it` means NHTSA is advising owners not to drive the vehicle, and `park_outside` means it should not be parked indoors because of a fire risk. The `is_urgent` field is true when either applies.

### Calling it from the website

The React app runs in the browser, so requests go through your own computer rather than the Docker network. Vite proxies `/health`, `/recalls`, and `/captures` to Uvicorn (see `frontend/vite.config.js`), so the page can call the API on its own origin:

```js
const res = await fetch(`/recalls?make=${make}&model=${model}&year=${year}`);
const data = await res.json();
```

That request goes to `http://localhost:5173/recalls`, and Vite forwards it to the API inside the container. The API is also reachable directly at `http://localhost:8000` because that port is published, and it allows requests from `http://localhost:5173`. No page calls it yet.

### Capturing from a real car

`obd_backend/capture.py` runs on the computer plugged into the car, outside the two-container demo. It needs the `obd` package installed there (`pip install obd`), reads the adapter on serial port `COM3`, records for 60 seconds, saves the capture to `captures/<timestamp>.json`, and posts it to `http://127.0.0.1:8000/captures`. That address matches the published API port, so with the website container running on the same computer, the capture lands in the API's log.

### After changing the code

Edits to `api.py` and `nhtsa_recalls.py` are picked up without a rebuild. The repository is bind-mounted into the website container and Uvicorn runs with `--reload`, so saving a file restarts the API. A rebuild is only for `requirements.txt` or `frontend/package.json`.

### Troubleshooting

If `curl` reports that it could not connect, the website container is not running or Uvicorn failed to start. `docker ps -a` shows stopped containers as well as running ones, and `docker logs virtual-garage-web` shows both the Uvicorn and Vite output, including any Python error that stopped the API.

Stopping and removing `virtual-garage-emulator` and `virtual-garage-web` in the cleanup section above also stops the API. There is nothing else to remove.
