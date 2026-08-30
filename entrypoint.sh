#!/bin/sh
set -eu

mkdir -p /aifile /userfile /workspace /run/agent-ssh

if [ -S /var/run/docker.sock ]; then
  gid="$(stat -c '%g' /var/run/docker.sock)"
  if ! getent group docker >/dev/null 2>&1; then
    groupadd -g "$gid" docker 2>/dev/null || groupadd docker
  fi
  actual="$(getent group docker | cut -d: -f3)"
  if [ "$actual" != "$gid" ]; then
    groupmod -g "$gid" docker 2>/dev/null || true
  fi
  usermod -aG docker agent 2>/dev/null || true
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8080
