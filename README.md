# Virtual Garage - Scanner Environment

This is the team's first reproducible development environment for the Virtual Garage scanner feature. It starts a simulated ELM327/OBD-II adapter and a small Python client that asks it for RPM, speed, coolant temperature, and stored DTCs.

It is intentionally a scanner proof of concept, not the finished application. It does not yet include the web/mobile interface, user accounts, vehicle history database, real Bluetooth pairing, or AWS deployment.

## Prerequisite

Install and open Docker Desktop. Teammates do not need to install Python or the ELM327 emulator directly.

## Build and run it

Run these commands from the repository root. They deliberately use Docker's lower-level commands so the team can see what Compose normally does for us.

### 1. Build the image

```bash
docker build -t virtual-garage-elm:dev .
```

This reads the `Dockerfile` and creates a reusable local image named `virtual-garage-elm:dev`. The final `.` means "use this folder as the build context."

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

This starts the simulated OBD-II adapter in the background. `--network` puts it on the private Docker network, and `-p 127.0.0.1:35000:35000` optionally makes its port reachable only from the developer's own computer—not the public internet.

### 4. Run the client against the emulator

```bash
docker run --rm -it \
  --network virtual-garage-net \
  --mount type=bind,src="$PWD",dst=/app \
  --workdir /app \
  virtual-garage-elm:dev sh
```

The client is a separate temporary container. On a named Docker network, `virtual-garage-emulator` resolves to the emulator container, so do not use `localhost` here.

Expected result: the client reports that it connected to `virtual-garage-emulator:35000`, then prints raw and decoded RPM, speed, and coolant-temperature responses. The default emulator scenario normally has no stored DTCs, so an empty DTC response is expected.

### 5. Run Commands against the Emulator

```bash
python elm_client.py --host virtual-garage-emulator --port 35000 010C
python elm_client.py --host virtual-garage-emulator --port 35000 010D
python elm_client.py --host virtual-garage-emulator --port 35000 03
```

### 6. Exiting the container

```bash
exit
```

## Re-run and clean up

To run the client again, repeat step 4. To see the emulator's output:

```bash
docker logs virtual-garage-emulator
```

When you are finished:

```bash
docker stop virtual-garage-emulator
docker rm virtual-garage-emulator
docker network rm virtual-garage-net
```



## Run another query

Ask for only RPM, speed, and stored DTCs:

```bash
docker run --rm \
  --network virtual-garage-net \
  virtual-garage-elm:dev \
  python3 elm_client.py --host virtual-garage-emulator --port 35000 010C 010D 03
```

The emulator is for development/testing. It is configured with its built-in `car` scenario and is not connected to a real vehicle.

## Team workflow

1. Clone the shared GitHub repository.
2. From the repository root, complete **Build and run it** above.
3. If the commands work, everyone has the same scanner test environment.
4. Do not commit `.env` files, AWS credentials, or SSH/private-key files.

`compose.yaml` remains in the repository as a future convenience option, but the team's onboarding instructions use the explicit commands above.

## Third-party development tool

This environment uses the [ELM327-emulator](https://github.com/Ircama/ELM327-emulator) for development and testing only. It is licensed under CC BY-NC-SA 4.0; keep the attribution and do not copy its code into the Virtual Garage application without reviewing the license.