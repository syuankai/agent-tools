# AI Agent Tool Server v0.0.5

Lightweight Ubuntu 24.04 HTTP tool server for AI agents.

v0.0.5 adds structured read-only file tools (`/file/list`, `/file/read`, `/file/search`, `/file/metadata`) and system info (`/system/info`), so Agents can operate on files without composing shell commands.

## Pull the image

The default image is:

```text
ghcr.io/syuankai/agent-tools:latest
```

If the package is public:

```bash
docker pull ghcr.io/syuankai/agent-tools:latest
```

A version tag can also be used after a Git tag is pushed, for example:

```bash
docker pull ghcr.io/syuankai/agent-tools:0.0.5
```

## GitHub Actions

Every push to `main` builds and publishes `latest`. A Git tag such as `v0.0.5` publishes version tags as well. The workflow builds both `linux/amd64` and `linux/arm64`, uses the GitHub Actions cache, and publishes SBOM/provenance metadata.

The workflow is in:

```text
.github/workflows/docker-publish.yml
```

GitHub's `GITHUB_TOKEN` is used for GHCR authentication; no Docker Hub account is required. GitHub Packages publishing requires the workflow to have `packages: write` permission. See the official GitHub and Docker documentation for GHCR and Docker Actions. 

## First-time GHCR setup

After the first successful workflow run, open the published package under the repository/account's Packages and make it public if you want users to pull it without authentication.

If the package is private, users must authenticate to GHCR before pulling it.

## Run without Compose

Create the host directories:

```bash
mkdir -p ./aifile ./userfile ./workspace ./ssh
```

Copy and edit the environment file:

```bash
cp .env.example .env
```

For `/commandpc`, put the SSH private key at:

```text
./ssh/id_ed25519
```

Then run the container directly:

```bash
docker run -d \
  --name agent-tool-server \
  --restart unless-stopped \
  --add-host host.docker.internal:host-gateway \
  --network agent-network \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd)/aifile:/aifile" \
  -v "$(pwd)/userfile:/userfile" \
  -v "$(pwd)/workspace:/workspace" \
  -v /proc:/hostproc:ro \
  -v "$(pwd)/ssh:/run/agent-ssh:ro" \
  --env-file .env \
  ghcr.io/syuankai/agent-tools:latest
```

If the Agent uses a different Docker network, replace `agent-network` with that network. No host `8080:8080` mapping is required when the Agent can reach this container on the same Docker network.

The API listens inside the container on:

```text
0.0.0.0:8080
```

From another container on the same network, use:

```text
http://agent-tool-server:8080
```

## Volumes

Required for the intended v0.0.5 setup:

```text
/var/run/docker.sock:/var/run/docker.sock
./aifile:/aifile
./userfile:/userfile
./workspace:/workspace
/proc:/hostproc:ro
```

For `/commandpc`:

```text
./ssh:/run/agent-ssh:ro
```

`./ssh` is only needed when `/commandpc` is enabled.

## Environment variables

The complete example is in `.env.example`.

Important values:

| Variable | Default | Purpose |
|---|---:|---|
| `API_KEY` | required | API authentication |
| `BLOCK` | `rm` | Global command blocklist |
| `USERFILE_HOST_PATH` | required by `/filepc` | Host path mounted into the temporary `/filepc` helper |
| `COMMANDPC_HOST` | `host.docker.internal` | Host SSH address |
| `COMMANDPC_USER` | `agentpc` | Dedicated non-sudo host account |
| `COMMANDPC_KEY_FILE` | `/run/agent-ssh/id_ed25519` | SSH private key inside the container |
| `ALLOW_DOCKER_MUTATION` | `false` | Allow Docker-changing operations |
| `RATE_LIMIT_REQUESTS` | `30` | Requests per rate window |
| `RATE_LIMIT_WINDOW` | `60` | Rate window in seconds |
| `MAX_CONCURRENT_TOOLS` | `4` | Simultaneous tool executions |
| `MAX_TOOL_CALLS` | `20` | Per `X-Agent-Task-ID` budget |
| `MAX_OUTPUT_SIZE` | `1048576` | Maximum returned command output |
| `MAX_FILE_SIZE` | `104857600` | Maximum `/getfile` download |
| `MAX_DIR_ENTRIES` | `1000` | Maximum entries returned by `/file/list` |
| `MAX_SEARCH_RESULTS` | `500` | Maximum matches returned by `/file/search` |
| `MAX_SEARCH_DEPTH` | `10` | Maximum directory depth for `/file/search` |
| `ENV_ALLOWLIST` | `AGENT_NAME,AGENT_VERSION,TOOL_SERVER_NAME,BLOCK` | Variables exposed by `/env` |

## Global command blocking

Set:

```env
BLOCK=rm,apt,command,npm
```

The blocklist applies to command-capable endpoints. `rm` is permanently blocked even if it is omitted from `BLOCK`.

The policy checks command structure rather than only doing a substring search, including common shell nesting and command chaining.

## Endpoints

### Structured File Tools (v0.0.5)

- `POST /file/list` — list directory contents as structured JSON.
- `POST /file/read` — read a file's content as structured JSON.
- `POST /file/search` — search for files using glob patterns.
- `POST /file/metadata` — get file/directory metadata as structured JSON.
- `GET /system/info` — get system information (OS, CPU, memory, disk).

### Shell / Command Tools (v0.4.x)

- `POST /command` — execute a command inside the tool-server container.
- `POST /file` — alias for `/command`.
- `POST /docker` — Docker CLI through `/var/run/docker.sock`.
- `POST /filepc` — operate inside the configured `/userfile` host directory through a temporary helper container.
- `POST /commandpc` — temporary SSH connection to the configured non-sudo host account.
- `POST /proc` — read-only host `/proc` access through `/hostproc`.
- `POST /getfile` — download HTTP/HTTPS files into `/aifile` with SSRF and size protections.

### Utility

- `GET /env` — read allowlisted container environment variables with redaction.
- `GET /health` — unauthenticated health check.
- `GET /stats` — authenticated local statistics.
- `GET /help` — public API help.
- `GET /tools` — Agent auto-discovery catalog with tool definitions.

Except `/help` and `/health`, endpoints require:

```http
Authorization: Bearer YOUR_API_KEY
```

### Tool Selection Guide

When an Agent needs to work with files, prefer structured tools over shell commands:

| Task | Use | Don't Use |
|---|---|---|
| List directory | `POST /file/list` | `POST /command` with `ls` |
| Read file | `POST /file/read` | `POST /command` with `cat` |
| Find files | `POST /file/search` | `POST /command` with `find` |
| File metadata | `POST /file/metadata` | `POST /command` with `stat` |
| System info | `GET /system/info` | `POST /command` with `uname`/`free`/`df` |

## Security

- Structured file tools are restricted to `/workspace` and `/userfile` roots.
- Symlink escapes outside allowed roots are blocked.
- Binary files are detected and rejected by `/file/read`.
- Path traversal (`..`) is normalized and blocked.
- Command blocklist applies to all shell-capable endpoints.
- Docker mutations are disabled by default.
- SSRF protection blocks downloads to private/internal IPs.
- Rate limiting and concurrency limits protect against abuse.

## Security warning

Mounting `/var/run/docker.sock` gives the container very high control over the Docker daemon. Treat this service as privileged infrastructure.

The `/commandpc` account should be a dedicated host account without sudo and with only the filesystem permissions you intentionally grant it.

Do not put secrets in `ENV_ALLOWLIST`. Secret-looking names are redacted by default, but the safest practice is not to expose secrets to `/env` at all.
