# Run in background
docker-compose up -d

# See logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up --build