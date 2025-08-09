#!/usr/bin/env bash
set -euo pipefail

# Prebuilt local image tag (override with IMAGE=...)
IMAGE="${IMAGE:-kasanoma-piper:latest}"
PORT="${PORT:-8000}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$SCRIPT_DIR/model"
IMAGE_TAR_DEFAULT="$SCRIPT_DIR/images/kasanoma-piper.tar"
IMAGE_TAR="${IMAGE_TAR:-$IMAGE_TAR_DEFAULT}"

if [ ! -d "$MODEL_DIR" ]; then
  echo "Error: model directory not found at $MODEL_DIR"
  echo "Expected files: model.onnx and config.json"
  exit 1
fi

# Ensure image exists locally; if not, try to load from a local tarball
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  if [ -f "$IMAGE_TAR" ]; then
    echo "Loading Docker image from $IMAGE_TAR ..."
    docker load -i "$IMAGE_TAR"
  else
    echo "Error: Docker image '$IMAGE' not found locally and no tarball at $IMAGE_TAR."
    echo "Provide a local image tar (set IMAGE_TAR=...) or pre-load the image:"
    echo "  docker load -i /path/to/kasanoma-piper.tar"
    echo "Expected tag: $IMAGE"
    exit 1
  fi
fi

echo "Running $IMAGE on http://localhost:$PORT"
exec docker run --rm -p "$PORT:8000" -v "$MODEL_DIR:/data/model" "$IMAGE"
