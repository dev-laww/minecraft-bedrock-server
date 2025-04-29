#!/bin/bash

"C:/Program Files/Docker/Docker/Docker Desktop.exe"

while ! docker info > /dev/null 2>&1; do
    sleep 1
done

if ! docker info > /dev/null 2>&1; then
    echo "Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

docker compose up -d

while ! docker container ps -q | grep -q .; do
    sleep 1
done

AUTOMATIC_SHUTDOWN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --automatic-shutdown)
            AUTOMATIC_SHUTDOWN="--automatic-shutdown"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

poetry run python scripts/monitor.py $AUTOMATIC_SHUTDOWN
