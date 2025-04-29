"C:/Program Files/Docker/Docker/Docker Desktop.exe"

# Wait for Docker to start
while ! docker info > /dev/null 2>&1; do
    sleep 1
done

# Check if the Docker daemon is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

docker compose up -d