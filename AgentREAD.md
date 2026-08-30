# AgentREAD.md — Agent Tool Box Bootstrap & Integration Guide

> **This document is written primarily for AI Agents.**
>
> If you are an AI Agent reading this repository for the first time, read this file before modifying code, installing dependencies, or asking the user to perform unnecessary manual steps.

---

# 1. Your Role

You are an AI Agent interacting with **Agent Tool Box**.

Agent Tool Box is a local Docker-based tool service that provides controlled access to:

* shell commands
* files
* processes
* Docker operations
* host/container resources
* structured file discovery
* system information
* other Agent-oriented tools

Your goal is to make the Tool Box available to yourself with the **minimum amount of user assistance**.

You should prefer:

```text
detect → install → configure → start → verify → connect → discover → use
```

instead of asking the user to manually perform every step.

---

# 2. First Principle

## Do not assume Docker already exists.

Many users will not have Docker installed.

Before attempting:

```bash
docker ps
docker compose up
docker pull
```

first determine whether Docker is available.

Check:

```bash
docker --version
docker compose version
docker info
```

Classify the environment:

```text
Docker CLI missing
Docker CLI exists but daemon unavailable
Docker available and daemon running
Docker Compose unavailable
Docker fully operational
```

Do not treat these states as equivalent.

---

# 3. Bootstrap Decision Tree

Use this decision tree.

```text
START
 │
 ├─ Is Agent Tool Box already running?
 │      │
 │      ├─ YES → verify /health → discover /tools → CONNECT
 │      │
 │      └─ NO
 │
 ├─ Is Docker installed?
 │      │
 │      ├─ YES
 │      │    │
 │      │    └─ Is Docker daemon running?
 │      │          │
 │      │          ├─ YES → continue
 │      │          └─ NO → ask user to start Docker
 │      │
 │      └─ NO
 │           │
 │           └─ guide user through Docker installation
 │
 ├─ Is Docker Compose available?
 │      │
 │      ├─ YES → continue
 │      └─ NO → install/enable Compose
 │
 ├─ Obtain Agent Tool Box source/configuration
 │
 ├─ Configure environment
 │
 ├─ Start container
 │
 ├─ Verify /health
 │
 ├─ Authenticate
 │
 ├─ GET /tools
 │
 └─ CONNECT
```

---

# 4. Never Silently Install System Software

Installing Docker can require elevated privileges and can modify the host system.

Therefore:

### Allowed

Explain what will happen and ask for confirmation before privileged installation.

Example:

```text
Docker is not installed.

Agent Tool Box requires Docker.

I can guide you through the official Docker installation for
your operating system. This may require administrator privileges.

Continue?
```

### Not allowed

Do not silently execute:

```bash
sudo apt install ...
sudo usermod ...
```

or equivalent privileged commands without user awareness.

Do not hide system-level changes from the user.

---

# 5. Docker Installation Strategy

Use the official Docker installation method appropriate for the host OS.

Docker provides:

* Docker Engine for supported Linux distributions
* Docker Desktop for Windows
* Docker Desktop for macOS
* Docker Desktop for Linux

See the official Docker documentation when current installation instructions are required:

* [Docker installation overview](https://docs.docker.com/engine/install/?utm_source=chatgpt.com)
* [Docker Desktop](https://docs.docker.com/desktop/?utm_source=chatgpt.com)
* [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/?utm_source=chatgpt.com)
* [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/?utm_source=chatgpt.com)
* [Docker Desktop for Linux](https://docs.docker.com/desktop/setup/install/linux/?utm_source=chatgpt.com)

Do not invent installation commands when official instructions are available.

---

# 6. Prefer the Repository Installer

If this repository provides:

```text
install.sh
```

prefer that workflow.

Typical usage:

```bash
./install.sh
```

or, if explicitly documented by the repository:

```bash
curl -fsSL <official-install-url> | bash
```

The installer should handle:

```text
OS detection
architecture detection
Docker detection
Docker Compose detection
configuration
image retrieval
container startup
health check
connection information
```

The installer must NOT blindly overwrite existing user configuration.

---

# 7. Repository Source

If the user gives you a repository URL:

```text
https://github.com/owner/repository
```

first determine whether the repository contains:

```text
AgentREAD.md
README.md
install.sh
docker-compose.yml
.env.example
Dockerfile
```

Prefer repository-provided instructions over assumptions.

If the repository contains `AgentREAD.md`, read it before continuing.

---

# 8. Configuration

Before starting the container, determine:

```text
API_KEY
HOST_PORT
CONTAINER_NAME
WORKSPACE_PATH
USERFILE_PATH
IMAGE
VERSION
```

Do not expose secrets in normal output.

Do not print:

```text
API_KEY=...
```

after generation.

Instead report:

```text
API key configured successfully.
```

If an API key already exists, do not replace it unless explicitly requested.

---

# 9. Starting Agent Tool Box

Prefer the repository's documented startup mechanism.

Typical example:

```bash
docker compose up -d
```

or:

```bash
docker run ...
```

Do not invent Docker arguments if the repository already provides:

```text
docker-compose.yml
compose.yaml
install.sh
```

Use the repository configuration.

---

# 10. Verify Before Connecting

Never assume that a successful Docker command means the service is ready.

After startup, verify:

```text
container exists
container is running
port is reachable
/health responds
authentication works
/tools responds
```

Typical health check:

```http
GET /health
```

Expected result resembles:

```json
{
  "status": "ok",
  "version": "0.6.0"
}
```

Only consider the Tool Box ready after the health check succeeds.

---

# 11. Discover Available Tools

After successful startup:

```http
GET /tools
```

Use the returned catalog to discover capabilities.

Do not assume that a tool exists merely because it existed in an older version.

The `/tools` response is authoritative for the running version.

Look for:

```text
name
description
when_to_use
when_not_to_use
input_schema
output_schema
examples
security
limits
```

---

# 12. Tool Selection

Prefer structured tools over shell commands when an appropriate structured tool exists.

For example:

### Bad

```bash
ls -la /workspace
```

### Prefer

```http
POST /file/list
```

with:

```json
{
  "path": "/workspace"
}
```

---

### Bad

```bash
cat /workspace/config.json
```

### Prefer

```http
POST /file/read
```

with:

```json
{
  "path": "/workspace/config.json"
}
```

---

### Bad

```bash
find /workspace -name "*.py"
```

### Prefer

```http
POST /file/search
```

with:

```json
{
  "path": "/workspace",
  "pattern": "*.py",
  "type": "file"
}
```

---

# 13. Current Structured File Tools

The current Tool Box provides structured file operations.

## `/file/list`

Use when:

```text
You need to discover files/directories.
```

Request:

```json
{
  "path": "/workspace"
}
```

---

## `/file/read`

Use when:

```text
You need text file contents.
```

Request:

```json
{
  "path": "/workspace/file.py"
}
```

Binary files should not be processed through this endpoint.

---

## `/file/search`

Use when:

```text
You need to locate files using glob patterns.
```

Example:

```json
{
  "path": "/workspace",
  "pattern": "*.py",
  "type": "file"
}
```

---

## `/file/metadata`

Use when:

```text
You need size, modification time, permissions, or file type.
```

Example:

```json
{
  "path": "/workspace/main.py"
}
```

---

## `/system/info`

Use when:

```text
You need information about the execution environment.
```

Example:

```http
GET /system/info
```

---

# 14. Security Boundaries

The Tool Box is intentionally restricted.

File operations are expected to remain inside approved roots such as:

```text
/workspace
/userfile
```

Do not attempt to bypass path validation.

Do not attempt:

```text
../
symlink escapes
/workspace_evil
absolute paths outside approved roots
null-byte tricks
```

If an operation is rejected by the Tool Box security policy:

**do not attempt to bypass the restriction.**

Instead:

1. understand why it was rejected;
2. determine whether another approved tool can perform the task;
3. ask the user if the operation genuinely requires additional access.

---

# 15. Docker Security Boundary

Do not assume that because the Tool Box uses Docker, you have unrestricted Docker host access.

Never require:

```text
/var/run/docker.sock
```

unless the repository explicitly documents and justifies it.

The Tool Box API is the intended Agent interface.

Prefer:

```text
AI Agent
   │
   │ HTTP + authentication
   ▼
Agent Tool Box
   │
   ▼
controlled operations
```

rather than:

```text
AI Agent
   │
   ▼
Docker socket
   │
   ▼
Host
```

---

# 16. API Authentication

API endpoints require authentication.

Use:

```http
Authorization: Bearer <API_KEY>
```

Do not send the API key through:

```text
URL query parameters
shell history
logs
public comments
source code
Git commits
```

Do not commit secrets to Git.

---

# 17. Failure Handling

When bootstrap fails, classify the failure.

## Docker missing

```text
DOCKER_NOT_INSTALLED
```

Tell the user how to install Docker.

---

## Docker daemon unavailable

```text
DOCKER_DAEMON_UNAVAILABLE
```

Tell the user to start Docker Desktop or the Docker daemon.

---

## Permission failure

```text
DOCKER_PERMISSION_DENIED
```

Explain the required permission.

Do not automatically weaken host security.

---

## Container startup failure

Inspect:

```bash
docker ps -a
docker logs <container>
```

Use only the minimum diagnostic information necessary.

---

## Health check failure

Verify:

```text
container status
port binding
logs
configuration
API key
```

Do not immediately reinstall everything.

---

# 18. Idempotency

Bootstrap operations should be safe to repeat.

If the Tool Box is already installed:

```text
do not reinstall Docker
do not regenerate API_KEY
do not destroy existing container
do not overwrite configuration
```

Instead:

```text
detect → reuse → verify → update only when necessary
```

---

# 19. Version Awareness

Always determine the running version.

Use:

```http
GET /health
```

and:

```http
GET /tools
```

Do not assume repository version == running container version.

If the container is old:

```text
detect
→ inform user
→ determine whether upgrade is appropriate
→ preserve configuration
→ restart safely
→ verify
```

---

# 20. User Interaction Philosophy

The user's desired experience is:

```text
User:
"Install Agent Tool Box from this repository."

AI:
1. Inspect repository.
2. Read AgentREAD.md.
3. Detect environment.
4. Detect Docker.
5. Explain missing prerequisites.
6. Guide installation if necessary.
7. Start Tool Box.
8. Verify health.
9. Authenticate.
10. Discover tools.
11. Continue the original user task.
```

Do not make the user manually execute ten unrelated commands if the repository already provides an installer.

However, do not hide privileged or destructive operations.

---

# 21. Important Principle: Continue the Original Task

Installing Tool Box is not the final goal.

For example:

```text
User:
"Find all Python files in my project and tell me which one contains the API configuration."
```

The Agent should:

```text
1. Determine whether Tool Box is available.
2. Bootstrap it if necessary.
3. Connect to Tool Box.
4. GET /tools.
5. POST /file/search.
6. POST /file/read.
7. Answer the original question.
```

Do not stop after saying:

```text
"Agent Tool Box installed successfully."
```

The installation is only infrastructure setup.

---

# 22. AgentREAD.md Priority Rules

When instructions conflict, use this priority:

```text
1. System / platform safety rules
2. Explicit user request
3. Repository security policy
4. AgentREAD.md
5. README.md
6. Comments / examples
7. Agent assumptions
```

Never override a higher-priority rule.

---

# 23. What Future Versions Should Preserve

Future versions should maintain:

```text
GET /health
GET /tools
API authentication
structured tool schemas
path security
command security
Docker mutation protection
backward compatibility
```

New tools should be added without unnecessarily breaking existing Agent workflows.

---

# 24. Recommended Bootstrap Architecture

The long-term architecture should look like:

```text
                    ┌─────────────────────┐
                    │      User           │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     AI Agent        │
                    │                     │
                    │ Read AgentREAD.md   │
                    └──────────┬──────────┘
                               │
                         Bootstrap
                               │
                ┌──────────────▼──────────────┐
                │      Host Environment       │
                │                             │
                │ Docker / Docker Desktop     │
                └──────────────┬──────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Agent Tool Box     │
                    │                     │
                    │ /health             │
                    │ /tools              │
                    │ /file/*             │
                    │ /system/*            │
                    │ /command             │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Agent Capabilities  │
                    └─────────────────────┘
```

The AI should interact with the Tool Box through its API rather than directly manipulating the host whenever possible.

---

# 25. Final Agent Checklist

Before declaring Tool Box ready:

```text
[ ] Repository instructions read
[ ] Docker detected
[ ] Docker daemon verified
[ ] Docker Compose verified
[ ] Configuration detected
[ ] Existing API key preserved
[ ] Container started
[ ] Container running
[ ] /health verified
[ ] Authentication verified
[ ] /tools discovered
[ ] Available tools understood
[ ] Security boundaries understood
[ ] Original user task continued
```

If all required checks pass:

```text
Agent Tool Box is ready.
```

Then proceed with the user's actual task.

---

# 26. For Repository Maintainers

When modifying Agent Tool Box:

**Update this file whenever any of the following changes:**

```text
installation procedure
bootstrap procedure
authentication
API endpoint
tool discovery
security boundary
configuration
Docker requirements
environment variables
version compatibility
Agent workflow
```

`AgentREAD.md` is an **Agent-facing contract**, not merely documentation.

The purpose is to allow a capable AI Agent to understand:

```text
WHAT this project is
WHY it exists
HOW to install it
HOW to connect to it
HOW to discover tools
HOW to select tools
WHAT it is allowed to do
WHAT it must not do
HOW to recover from failure
```

The ultimate goal is:

> **A user should be able to give an AI Agent this repository and a task, and the Agent should be able to bootstrap Agent Tool Box with minimal human assistance while preserving security and user control.**
