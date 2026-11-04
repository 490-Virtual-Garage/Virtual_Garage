### This branch builds one image and runs two containers: the ELM327 emulator, and a website container that serves the React app and the FastAPI backend (`api.py`) side by side.

# Virtual Garage - Development Environment

This is the team's reproducible development environment for Virtual Garage. A single Docker Compose file runs everything:

- **web**: serves the React website (Vite) and the FastAPI scanner API (`api.py`). This is also where you run the Python client.
- **emulator**: a simulated ELM327/OBD-II adapter.
- **backend**: the OBD backend service.
- **db**: Postgres.

The client asks the adapter for RPM, speed, coolant temperature, and stored DTCs.

## Prerequisite

Install and open Docker Desktop. You do not need Python, Node, Postgres, or the ELM327 emulator installed locally.

## Setup

### 1. Create the env files

**Frontend** (`.env.development`):

```
VITE_FIREBASE_API_KEY=paste_apiKey_here
VITE_FIREBASE_AUTH_DOMAIN=paste_authDomain_here
VITE_FIREBASE_PROJECT_ID=paste_projectId_here
VITE_FIREBASE_STORAGE_BUCKET=paste_storageBucket_here
VITE_FIREBASE_MESSAGING_SENDER_ID=paste_messagingSenderId_here
VITE_FIREBASE_APP_ID=paste_appId_here
VITE_FIREBASE_MEASUREMENT_ID=paste_measurementId_here
```

**Backend:**

- `obd_backend/.env`: local (non-Docker) backend configuration.
- `obd_backend/.env.docker`: Docker backend configuration. Must include `POSTGRES_PASSWORD=...`

Notes:
- Postgres only applies `POSTGRES_PASSWORD` the first time it initializes an empty volume. If you change it later, run `down -v` (see below) to reset the database.
- Special characters in the password (`@ : / #` etc.) must be URL-encoded, since it goes into `DATABASE_URL`.
- Never commit `.env.docker`.

### 2. Build and start everything

```bash
docker compose --env-file obd_backend/.env.docker up --build
```

Add `-d` to run in the background, then follow the logs with:

```bash
docker compose --env-file obd_backend/.env.docker logs -f
```

`--env-file` is required on every compose command. Compose only reads `POSTGRES_PASSWORD` from a root `.env` or your shell, not from `obd_backend/.env.docker`. Without the flag you get the "Set POSTGRES_PASSWORD" error.

Compose creates the network and wires the services together by name, so there is no `docker network create` or `docker run` step.

## Services and ports

| Service  | Container               | URL / Port                 |
|----------|-------------------------|----------------------------|
| Website  | virtual-garage-web      | http://localhost:5173      |
| Web API  | virtual-garage-web      | http://localhost:8000/docs |
| Backend  | obd_backend_test        | http://localhost:8001/docs |
| Postgres | vg-postgres             | localhost:5433             |
| Emulator | virtual-garage-emulator | localhost:35000            |

All ports are bound to `127.0.0.1`, so they are only reachable from your own computer.

## Running the Python client

`ELM_HOST` and `ELM_PORT` are already set by Compose, so just run:

```bash
docker compose --env-file obd_backend/.env.docker exec web python3 elm_client.py
```

This opens one connection to the emulator and shows a menu:

```text
Connected to ELM327 emulator at emulator:35000

  1) Engine RPM [010C]
  2) Vehicle speed [010D]
  3) Coolant temperature [0105]
  4) Stored trouble codes (DTCs) [03]
  q) Quit
Choose:
```

Type a number and press Enter to see the raw reply and the decoded value. The connection stays open until you choose `q`. Run the command again as often as you like.

The default emulator scenario normally has no stored DTCs, so option 4 replies `43 00`.

For an interactive shell inside the web container:

```bash
docker compose --env-file obd_backend/.env.docker exec web sh
```

Type `exit` to leave. The website keeps running.

## Common commands

```bash
# Rebuild and start (foreground)
docker compose --env-file obd_backend/.env.docker up --build

# Rebuild and start in the background
docker compose --env-file obd_backend/.env.docker up --build -d

# Stop and remove containers (keeps the database)
docker compose --env-file obd_backend/.env.docker down

# Stop and remove containers AND volumes (wipes the database)
docker compose --env-file obd_backend/.env.docker down -v

# Check running containers
docker ps

# Logs for one service (web, emulator, backend, db)
docker compose --env-file obd_backend/.env.docker logs -f web

# Restart stopped containers without rebuilding (start the DB first)
docker start vg-postgres
docker start obd_backend_test
docker start virtual-garage-emulator
docker start virtual-garage-web
```

## Verify everything works

- Website: http://localhost:5173
- Web API docs: http://localhost:8000/docs
- Backend docs (Swagger UI): http://localhost:8001/docs
- Database: connect with a GUI client on `localhost:5433`, or use the terminal

Check that Postgres is up:

```bash
docker exec -it vg-postgres pg_isready -U virtual_garage
```

Check that the backend can reach the database:

```bash
docker exec -it obd_backend_test python -c "import os; from sqlalchemy import create_engine, text; url=os.environ['DATABASE_URL']; engine=create_engine(url); conn=engine.connect(); print(conn.execute(text('SELECT current_database(), current_user')).one()); conn.close(); print('Database connection successful')"
```

## Editing code

Edits to the Python files and the React source are picked up without a rebuild: the repository is bind-mounted into the web container, Vite hot-reloads the frontend, and Uvicorn runs with `--reload` so saving `api.py` or `nhtsa_recalls.py` restarts the API.

A rebuild (`up --build`) is only needed when `requirements.txt` or `frontend/package.json` changes. For `frontend/package.json`, also remove the dependency volume so the new packages are installed:

```bash
docker compose --env-file obd_backend/.env.docker down
docker volume ls          # look for <project>_frontend_modules
docker volume rm <project>_frontend_modules
docker compose --env-file obd_backend/.env.docker up --build
```

Don't use `down -v` for this. It also deletes the Postgres data.

## Cleanup

```bash
# Remove containers, keep the database
docker compose --env-file obd_backend/.env.docker down

# Remove containers and all volumes (wipes the database)
docker compose --env-file obd_backend/.env.docker down -v

# Remove the built image
docker image rm virtual-garage-elm:dev
```

## Accessing the database

With the containers running, open a `psql` shell in the Postgres container:

```powershell
docker exec -it vg-postgres psql -U virtual_garage -d virtual_garage_users_dev
```

Useful commands once you're in:

- `\dt` lists the tables
- `\d users` shows a table's columns
- `SELECT * FROM users;` shows the saved users
- `SELECT * FROM vehicles;` shows saved vehicles
- `\q` quits

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
