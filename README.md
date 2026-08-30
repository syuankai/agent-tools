# AI Agent Tool Server v0.3

Lightweight Ubuntu 24.04 HTTP tool server for AI Agents.

## What v0.3 adds

- Global `BLOCK` command deny-list.
- `rm` is permanently blocked and cannot be removed from policy.
- Rate limiting with `429` + `Retry-After`.
- Global concurrent-tool limit.
- Request body and command-output limits.
- Command execution timeouts.
- Safer Docker mutation policy; mutations are disabled by default.
- `/env` for allowlisted container environment variables with secret redaction.
- `/health`, `/stats`, and expanded `/help`.
- `/getfile` redirect-by-redirect SSRF checks and download-size limits.
- `/filepc` path restrictions for the `/userfile` area.
- Request IDs via `X-Request-ID`.
- Optional per-task tool-call budget via `X-Agent-Task-ID` + `MAX_TOOL_CALLS`.
- No host port 8080 mapping is required when the Agent shares `agent-network`.

## Build

```bash
cp .env.example .env
mkdir -p aifile userfile
# Edit .env, especially API_KEY and USERFILE_HOST_PATH.
docker build -t agent-tools:latest .
```

## Run

```bash
docker compose up -d
```

The API listens on `0.0.0.0:8080` inside the container. If the Agent is attached to `agent-network`, use:

```text
http://agent-tool-server:8080
```

Do not publish `8080:8080` unless you intentionally need host access.

## Authentication

All tool endpoints except `GET /help` and `GET /health` require:

```http
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### `POST /command`

Runs a shell command inside this container, from `/workspace`.

```text
echo hello
```

Successful empty output returns `All done.` with status 200.

### `POST /file`

Same execution environment as `/command`, intended for file operations inside the Tool Server container.

### `POST /docker`

Runs Docker CLI commands through the mounted `/var/run/docker.sock`.

By default, mutating Docker operations such as `run`, `exec`, `stop`, `rm`, `rmi`, `build`, `push`, and `pull` are denied. Set `ALLOW_DOCKER_MUTATION=true` only when you intentionally want this capability.

### `POST /filepc`

Runs a disposable restricted Ubuntu helper container with the configured host directory mounted as `/userfile`.

Set:

```env
USERFILE_HOST_PATH=/home/syuankai
```

The command must stay within `/userfile`; path traversal and namespace-changing operations are rejected.

### `POST /commandpc`

Creates a temporary SSH connection to the configured host account.

```env
COMMANDPC_HOST=host.docker.internal
COMMANDPC_PORT=22
COMMANDPC_USER=agentpc
COMMANDPC_KEY_FILE=/run/agent-ssh/id_ed25519
```

Mount a trusted SSH key and `known_hosts` when enabling this feature. Host-key verification is required; the server does not accept unknown host keys.

### `POST /proc`

Reads host `/proc` through the read-only `/hostproc` mount. The command parser only permits a small read-oriented command set and rejects write/exec patterns.

### `POST /getfile`

Downloads a public HTTP/HTTPS URL into `/aifile`.

Redirects are checked individually. Loopback, private, link-local, reserved, multicast, and unspecified addresses are rejected. The download is limited by `MAX_FILE_SIZE`.

### `GET /env`

Returns only variables listed in `ENV_ALLOWLIST`.

Example:

```env
ENV_ALLOWLIST=AGENT_NAME,AGENT_VERSION,TOOL_SERVER_NAME,BLOCK
ENV_REDACT=true
ENV_REDACT_PATTERNS=KEY,TOKEN,PASSWORD,SECRET,CREDENTIAL
```

Secret-looking variable names are returned as `[REDACTED]` by default. An empty allowlist returns no variables.

### `GET /health`

Unauthenticated health check.

### `GET /stats`

Authenticated in-process statistics. It does not record command contents.

### `GET /help`

Public machine-readable API help, including the active blocked-command list.


### Agent task budget

For a multi-tool task, the Agent can send a stable header:

```http
X-Agent-Task-ID: 2026-08-30-task-001
```

The server counts tool requests for that task and returns `429` once `MAX_TOOL_CALLS` is reached. Without this header, the normal rate limiter still applies.

## Global command blocklist

Set the container environment variable:

```env
BLOCK=rm,apt,command,npm
```

This policy is applied to command-capable endpoints (`/command`, `/file`, `/filepc`, `/commandpc`, and `/docker`). It is checked before execution and is intentionally conservative. `rm` is always blocked even if it is omitted from `BLOCK`.

For example, with `BLOCK=rm,apt,npm`:

```text
rm file.txt          -> 403
/usr/bin/rm file.txt -> 403
apt update            -> 403
npm install           -> 403
ls -la                -> allowed
```

The policy also catches common shell nesting such as `bash -c 'rm ...'` rather than relying only on the first token.

## Environment variables

| Variable | Default | Purpose |
|---|---:|---|
| `API_KEY` | required | API authentication secret |
| `APP_VERSION` | `0.3.0` | Reported application version |
| `BLOCK` | `rm` | Global custom command blocklist |
| `RATE_LIMIT_REQUESTS` | `30` | Requests per authorization key per window |
| `RATE_LIMIT_WINDOW` | `60` | Rate-limit window in seconds |
| `MAX_TOOL_CALLS` | `20` | Maximum calls for one `X-Agent-Task-ID` task |
| `MAX_CONCURRENT_TOOLS` | `4` | Maximum simultaneous requests executing through the server |
| `MAX_BODY_BYTES` | `65536` | Maximum request body |
| `MAX_OUTPUT_SIZE` | `1048576` | Maximum command output returned |
| `COMMAND_TIMEOUT` | `30` | `/command` and `/file` timeout |
| `COMMANDPC_TIMEOUT` | `30` | Remote SSH command timeout |
| `FILEPC_TIMEOUT` | `120` | `/filepc` timeout |
| `DOCKER_TIMEOUT` | `120` | `/docker` timeout |
| `DOWNLOAD_TIMEOUT` | `300` | `/getfile` timeout |
| `MAX_FILE_SIZE` | `104857600` | `/getfile` maximum file size |
| `ALLOW_DOCKER_MUTATION` | `false` | Allow Docker-changing operations |
| `FILEPC_IMAGE` | `ubuntu:24.04` | Helper image for `/filepc` |
| `USERFILE_HOST_PATH` | required | Host path exposed as `/userfile` |
| `COMMANDPC_HOST` | `host.docker.internal` | SSH host |
| `COMMANDPC_PORT` | `22` | SSH port |
| `COMMANDPC_USER` | `agentpc` | Dedicated host user |
| `COMMANDPC_KEY_FILE` | `/run/agent-ssh/id_ed25519` | SSH private key path inside container |
| `ENV_REDACT` | `true` | Redact secret-looking `/env` variables |
| `ENV_ALLOWLIST` | empty | Variables visible through `/env` |
| `ENV_DENYLIST` | empty | Variables denied even if allowlisted |
| `ENV_REDACT_PATTERNS` | `KEY,TOKEN,PASSWORD,SECRET,CREDENTIAL` | Secret-name patterns |

## Volumes

```text
/var/run/docker.sock:/var/run/docker.sock
./aifile:/aifile
./userfile:/userfile
/proc:/hostproc:ro
```

Optional for `/commandpc`:

```text
./ssh:/run/agent-ssh:ro
```

## Security notes

Mounting `/var/run/docker.sock` gives the container very high control over the Docker daemon. Treat this service as privileged infrastructure.

The `/commandpc` account should be a dedicated, non-sudo host account with only the permissions you intentionally grant it.

The in-process rate limiter and statistics are local to one server process. For multiple replicas, put a shared rate limiter/reverse proxy in front.
