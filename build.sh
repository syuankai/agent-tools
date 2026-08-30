#!/bin/sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_CTX="/tmp/agent-tools-build-ctx"

rm -rf "$BUILD_CTX"
mkdir -p "$BUILD_CTX"

cp "$SCRIPT_DIR/requirements.txt" "$BUILD_CTX/"
cp "$SCRIPT_DIR/entrypoint.sh" "$BUILD_CTX/"
cp -r "$SCRIPT_DIR/app" "$BUILD_CTX/app"
cp -r "$SCRIPT_DIR/webcon" "$BUILD_CTX/webcon"
cp "$SCRIPT_DIR/Dockerfile" "$BUILD_CTX/Dockerfile"

docker build -t agent-tools:v0.4.5 -t agent-tools:latest "$BUILD_CTX/"

rm -rf "$BUILD_CTX"

echo "Build complete: agent-tools:v0.4.5 and agent-tools:latest"
