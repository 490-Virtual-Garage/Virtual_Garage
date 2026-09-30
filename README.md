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

