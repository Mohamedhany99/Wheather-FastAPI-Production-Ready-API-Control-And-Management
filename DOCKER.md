# Docker Guide

This document provides detailed instructions for running the Weather API using Docker.

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose 2.0+ (optional, for docker-compose)

## Quick Start

### Using Docker Compose (Recommended)

1. **Create `.env` file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** and add your Weatherstack API key:
   ```bash
   WEATHERSTACK_API_KEY=your_api_key_here
   ```

3. **Start the service**:
   ```bash
   docker-compose up --build
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health
   - Metrics: http://localhost:8000/metrics

### Using Docker directly

1. **Build the image**:
   ```bash
   docker build -t weather-api .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name weather-api \
     -p 8000:8000 \
     --env-file .env \
     weather-api
   ```

3. **View logs**:
   ```bash
   docker logs -f weather-api
   ```

## Docker Compose Commands

```bash
# Start services
docker-compose up

# Start in detached mode
docker-compose up -d

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart services
docker-compose restart
```

## Docker Commands

```bash
# Build image
docker build -t weather-api .

# Run container
docker run -d --name weather-api -p 8000:8000 --env-file .env weather-api

# Run with custom environment variables
docker run -d \
  --name weather-api \
  -p 8000:8000 \
  -e WEATHERSTACK_API_KEY=your_key \
  -e LOG_LEVEL=DEBUG \
  weather-api

# View logs
docker logs -f weather-api

# Execute command in container
docker exec -it weather-api /bin/bash

# Stop container
docker stop weather-api

# Remove container
docker rm weather-api

# Remove image
docker rmi weather-api
```

## Environment Variables

All configuration can be provided via environment variables. See `.env.example` for all available options.

Key variables:
- `WEATHERSTACK_API_KEY` (required) - Your Weatherstack API key
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `CACHE_TTL_SECONDS` - Cache TTL in seconds
- `RATE_LIMIT_PER_MINUTE` - Rate limit per IP

## Health Checks

The Docker image includes a built-in health check that monitors the `/health` endpoint:

```bash
# Check container health
docker ps  # Shows health status

# Inspect health check
docker inspect --format='{{json .State.Health}}' weather-api | jq
```

## Production Deployment

### Best Practices

1. **Use specific image tags** instead of `latest`:
   ```bash
   docker build -t weather-api:v1.0.0 .
   ```

2. **Use secrets management** for API keys:
   ```bash
   # Docker secrets (Docker Swarm)
   echo "your_api_key" | docker secret create weatherstack_api_key -
   
   # Or use environment files with restricted permissions
   chmod 600 .env
   ```

3. **Set resource limits**:
   ```yaml
   # In docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 512M
       reservations:
         cpus: '0.5'
         memory: 256M
   ```

4. **Use reverse proxy** (nginx, traefik) for production:
   - SSL/TLS termination
   - Load balancing
   - Rate limiting at edge

5. **Monitor and log**:
   ```bash
   # Log aggregation
   docker run --log-driver=syslog --log-opt syslog-address=tcp://logs:514 weather-api
   ```

## Troubleshooting

### Container won't start

1. **Check logs**:
   ```bash
   docker logs weather-api
   ```

2. **Verify environment variables**:
   ```bash
   docker exec weather-api env | grep WEATHERSTACK
   ```

3. **Check health endpoint**:
   ```bash
   curl http://localhost:8000/health
   ```

### Port already in use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use different port
docker run -p 8080:8000 weather-api
```

### Build fails

1. **Clear Docker cache**:
   ```bash
   docker builder prune
   ```

2. **Rebuild without cache**:
   ```bash
   docker build --no-cache -t weather-api .
   ```

### Permission issues

The container runs as non-root user (`appuser`). If you need to modify files:

```bash
# Run as root (not recommended for production)
docker run --user root weather-api
```

## Image Details

- **Base Image**: `python:3.11-slim`
- **Size**: ~200MB (optimized)
- **User**: `appuser` (UID 1000, non-root)
- **Port**: 8000
- **Health Check**: `/health` endpoint every 30s

## Multi-stage Build

The Dockerfile uses a multi-stage build:
1. **Builder stage**: Installs Poetry and dependencies
2. **Runtime stage**: Copies only necessary files, smaller final image

This reduces the final image size by excluding build tools and Poetry.

## Security

- Runs as non-root user
- Minimal base image (slim variant)
- No unnecessary packages
- Health checks for monitoring
- Environment variables for secrets (never hardcode)

