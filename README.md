# Virtual Garage - Scanner Environment

This is the team's reproducible development environment for the Virtual Garage scanner feature. One image runs as two containers: a simulated ELM327/OBD-II adapter, and a development container that serves the React website and runs the Python client. The client asks the adapter for RPM, speed, coolant temperature, and stored DTCs.

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
  -p 35000:35000 \
  virtual-garage-elm:dev \
  python3 -m elm -s car -n 35000 -i 0.0.0.0
```

This starts the simulated OBD-II adapter in the background. `--network` puts it on the private Docker network, and `-p 127.0.0.1:35000:35000` makes its port reachable only from the developer's own computer.

### 4. Run the website

This is the second container. It serves the React app and is also where you run the Python client. It joins the same network, so the emulator's name resolves. The repository is mounted at `/app` so edits show up without a rebuild. The second mount keeps the frontend dependencies from the image, because the repository mount would otherwise hide them.

```bash
docker run --detach \
  --name virtual-garage-web \
  --network virtual-garage-net \
  -p 127.0.0.1:5173:5173 \
  --mount type=bind,src="$PWD",dst=/app \
  --mount type=volume,src=virtual-garage-frontend-modules,dst=/app/frontend/node_modules \
  -e ELM_HOST=virtual-garage-emulator \
  -e ELM_PORT=35000 \
  --workdir /app/frontend \
  virtual-garage-elm:dev \
  npm run dev -- --host 0.0.0.0
```

The container's main job is the website, so it stays running in the background. You get a shell inside it in step 5. `--host 0.0.0.0` lets your browser reach Vite from outside the container.

`ELM_HOST` and `ELM_PORT` tell the Python client where the emulator is, so you don't pass them on every command.

Open [http://localhost:5173](http://localhost:5173).

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

If `frontend/package.json` changes, rebuild the image, remove the dependency volume, and start the website container again:

```bash
docker volume rm virtual-garage-frontend-modules
```

## Recalls service

The scanner tells you what is wrong with a car right now. The recalls service answers a different question: whether the manufacturer has already issued a safety campaign for that vehicle. It runs as its own container and reads the free NHTSA recalls API, so it needs no key and no account.

It is a separate container from the website because it is a separate concern, and because a failure in one should not take down the other.

### Files

| File | Purpose |
| --- | --- |
| `nhtsa_recalls.py` | Client for the NHTSA API. Handles retries, caching, and date parsing. |
| `recalls_service.py` | FastAPI wrapper that exposes the client over HTTP. |
| `Dockerfile.recalls` | Builds the service image. |

### 1. Build the image

```bash
docker build -f Dockerfile.recalls -t virtual-garage-recalls:dev .
```

The `-f` flag is needed because this is the second Dockerfile in the repository. Without it, Docker would use the one named `Dockerfile`, which builds the scanner environment instead.

### 2. Run the container

```bash
docker run --detach \
  --name virtual-garage-recalls \
  --network virtual-garage-net \
  -p 127.0.0.1:8000:8000 \
  virtual-garage-recalls:dev
```

It joins `virtual-garage-net`, the same network the emulator and website use, so the other containers can reach it by name at `http://virtual-garage-recalls:8000`. Publishing to `127.0.0.1` keeps it reachable from your own computer but not from anyone else on your network.

### 3. Check that it works

```bash
curl "http://localhost:8000/recalls?make=acura&model=rdx&year=2012"
```

You should get a JSON object back listing the recall campaigns for that vehicle.

For a friendlier view, open [http://localhost:8000/docs](http://localhost:8000/docs). FastAPI generates an interactive page where you can fill in the parameters and send the request from the browser.

### Endpoints

| Method | Path | Parameters | Returns |
| --- | --- | --- | --- |
| GET | `/health` | none | `{"status": "ok"}` |
| GET | `/recalls` | `make`, `model`, `year` | Recall campaigns for the vehicle |

### Reading the response

The `status` field matters more than the recall count, because NHTSA returns an empty result both for a vehicle with a clean record and for a make or model it does not recognize. The service tells these apart by checking NHTSA's own vehicle catalog before reporting an empty result.

| `status` | Meaning |
| --- | --- |
| `ok` | Recalls were found. |
| `no_recalls` | The vehicle is real and has no open recalls. |
| `unknown_vehicle` | NHTSA has no catalog entry for that make, model, and year. Usually a spelling mistake. |
| `error` | The request to NHTSA failed. |

Two fields deserve to be shown prominently in the interface rather than listed alongside the others. `park_it` means NHTSA is advising owners not to drive the vehicle, and `park_outside` means it should not be parked indoors because of a fire risk. The `is_urgent` field is true when either applies.

### Calling it from the website

The React app runs in the browser, so requests go through your own computer rather than the Docker network:

```js
const res = await fetch(
  `http://localhost:8000/recalls?make=${make}&model=${model}&year=${year}`
);
const data = await res.json();
```

The service allows requests from `http://localhost:5173` so the development server can call it directly.

### After changing the code

This container has no bind mount, so edits to `nhtsa_recalls.py` or `recalls_service.py` do not appear until the image is rebuilt and the container replaced:

```bash
docker rm -f virtual-garage-recalls
docker build -f Dockerfile.recalls -t virtual-garage-recalls:dev .
docker run --detach \
  --name virtual-garage-recalls \
  --network virtual-garage-net \
  -p 127.0.0.1:8000:8000 \
  virtual-garage-recalls:dev
```

### Troubleshooting

If `curl` reports that it could not connect, the container is not running. `docker ps -a` shows stopped containers as well as running ones, and `docker logs virtual-garage-recalls` shows why it stopped.

### Cleaning up

```bash
docker stop virtual-garage-recalls
docker rm virtual-garage-recalls
```

