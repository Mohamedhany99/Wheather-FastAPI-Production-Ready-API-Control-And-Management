# Weather API

A production-ready FastAPI service for fetching current weather data from the Weatherstack API.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **Weatherstack Integration** - Fetches current weather data for any city
- **Caching** - In-memory caching with TTL to reduce API calls
- **Rate Limiting** - Per-IP rate limiting to prevent abuse
- **Error Handling** - Comprehensive exception handling with proper HTTP status codes
- **Structured Logging** - Production-ready logging configuration
- **Health Checks** - Health check endpoint for monitoring
- **OpenAPI Documentation** - Auto-generated API documentation

## Requirements

- Python 3.11+
- Poetry for dependency management
- Weatherstack API key (free tier available at https://weatherstack.com/signup/free)

## Setup

### 1. Install Poetry

If you don't have Poetry installed, follow the instructions at https://python-poetry.org/docs/#installation

### 2. Create Virtual Environment with Python 3.11

```bash
# Using pyenv or similar to ensure Python 3.11
python3.11 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
poetry install
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Weatherstack API key:

```
WEATHERSTACK_API_KEY=your_api_key_here
WEATHERSTACK_BASE_URL=http://api.weatherstack.com
CACHE_TTL_SECONDS=300
RATE_LIMIT_PER_MINUTE=60
LOG_LEVEL=INFO
```

### 5. Run the Application

```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Docker Setup

### Using Docker Compose (Recommended)

1. **Create `.env` file** (if not already created):
   ```bash
   cp .env.example .env
   # Edit .env and add your WEATHERSTACK_API_KEY
   ```

2. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

   The API will be available at `http://localhost:8000`

3. **Run in detached mode**:
   ```bash
   docker-compose up -d
   ```

4. **View logs**:
   ```bash
   docker-compose logs -f
   ```

5. **Stop the container**:
   ```bash
   docker-compose down
   ```

### Using Docker directly

1. **Create `.env` file** (if not already created):
   ```bash
   cp .env.example .env
   # Edit .env and add your WEATHERSTACK_API_KEY
   ```

2. **Build the Docker image**:
   ```bash
   docker build -t weather-api .
   ```

3. **Run the container** (choose one method):

   **Option A: Using .env file** (recommended):
   ```bash
   docker run -d \
     --name weather-api \
     -p 8000:8000 \
     --env-file .env \
     weather-api
   ```

   **Option B: Pass environment variable directly**:
   ```bash
   docker run -d \
     --name weather-api \
     -p 8000:8000 \
     -e WEATHERSTACK_API_KEY=your_api_key_here \
     weather-api
   ```

4. **View logs**:
   ```bash
   docker logs -f weather-api
   ```

5. **Stop and remove container**:
   ```bash
   docker stop weather-api
   docker rm weather-api
   ```

**Important:** The `WEATHERSTACK_API_KEY` environment variable is **required**. Make sure to either:
- Use `--env-file .env` to load from a file, or
- Use `-e WEATHERSTACK_API_KEY=your_key` to pass it directly

### Docker Features

- **Multi-stage build** for optimized image size
- **Non-root user** for security
- **Health checks** built-in
- **Environment variable support** via `.env` file
- **Production-ready** configuration

### Troubleshooting Docker

**Error: "Field required [type=missing, input_value={}, input_type=dict]"**

This means the `WEATHERSTACK_API_KEY` environment variable is missing. Solutions:

1. **Make sure `.env` file exists** and contains `WEATHERSTACK_API_KEY=your_key`
2. **When using `docker run`**, include `--env-file .env` or `-e WEATHERSTACK_API_KEY=your_key`
3. **When using `docker-compose`**, make sure `.env` file is in the same directory

The application will now show a helpful error message if the API key is missing.

## API Endpoints

### Get Weather

**GET** `/weather?city={city_name}`

Fetches current weather data for the specified city.

**Query Parameters:**
- `city` (required): Name of the city to get weather for

**Example Request:**
```bash
curl "http://localhost:8000/weather?city=London"
```

**Example Response:**
```json
{
  "data": {
    "request": {
      "type": "City",
      "query": "London, United Kingdom",
      "language": "en",
      "unit": "m"
    },
    "location": {
      "name": "London",
      "country": "United Kingdom",
      "region": "City of London, Greater London",
      "lat": "51.517",
      "lon": "-0.106",
      "timezone_id": "Europe/London",
      "localtime": "2024-01-15 14:30",
      "localtime_epoch": 1705329000,
      "utc_offset": "0.0"
    },
    "current": {
      "observation_time": "02:30 PM",
      "temperature": 8,
      "weather_code": 116,
      "weather_icons": ["https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0002_sunny_intervals.png"],
      "weather_descriptions": ["Partly cloudy"],
      "wind_speed": 13,
      "wind_degree": 230,
      "wind_dir": "SW",
      "pressure": 1018,
      "precip": 0.0,
      "humidity": 75,
      "cloudcover": 50,
      "feelslike": 5,
      "uv_index": 1,
      "visibility": 10,
      "is_day": "yes"
    }
  },
  "metadata": {
    "cached": false,
    "stale": false,
    "age_seconds": 0,
    "source": "api",
    "retry_attempts": 0,
    "circuit_breaker_state": "closed"
  }
}
```

### Health Check

**GET** `/health`

Returns the health status of the API.

**Example Request:**
```bash
curl "http://localhost:8000/health"
```

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00Z",
  "service": "weather-api"
}
```

### Metrics

**GET** `/metrics`

Returns application metrics including request counts, error rates, cache performance, and response time percentiles.

**Example Request:**
```bash
curl "http://localhost:8000/metrics"
```

**Example Response:**
```json
{
  "counters": {
    "api_requests_total": 150,
    "api_errors_total": 5,
    "api_timeouts_total": 2,
    "cache_hits_total": 120,
    "cache_misses_total": 30,
    "stale_cache_fallbacks_total": 3,
    "circuit_breaker_opens_total": 1,
    "retry_attempts_total": 8
  },
  "errors_by_type": {
    "WeatherstackAPIError": 3,
    "timeout": 2
  },
  "rates": {
    "cache_hit_rate": 0.8,
    "error_rate": 0.033
  },
  "response_times": {
    "p50": 0.245,
    "p95": 0.892,
    "p99": 1.234,
    "count": 150
  }
}
```

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

All configuration is done through environment variables in the `.env` file:

- `WEATHERSTACK_API_KEY` (required): Your Weatherstack API key
- `WEATHERSTACK_BASE_URL` (default: `http://api.weatherstack.com`): Weatherstack API base URL
- `CACHE_TTL_SECONDS` (default: `300`): Cache time-to-live in seconds
- `RATE_LIMIT_PER_MINUTE` (default: `60`): Rate limit per IP address
- `LOG_LEVEL` (default: `INFO`): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `400` - Bad request (missing or invalid parameters)
- `401` - Authentication error (invalid API key)
- `404` - City not found
- `429` - Rate limit exceeded
- `500` - Internal server error
- `503` - Service unavailable (Weatherstack API down)

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black .
```

### Linting

```bash
poetry run ruff check .
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── dependencies.py         # Shared dependencies (cache)
│   ├── exceptions.py           # Custom exception classes
│   ├── models/
│   │   ├── __init__.py
│   │   └── weather.py          # Response models
│   ├── services/
│   │   ├── __init__.py
│   │   └── weatherstack.py    # Weatherstack API client
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── weather.py     # Weather endpoint
│   │   │   └── health.py      # Health check endpoint
│   │   └── dependencies.py    # API-level dependencies
│   └── middleware/
│       ├── __init__.py
│       └── rate_limit.py      # Rate limiting middleware
├── .env                        # Environment variables (gitignored)
├── .env.example               # Example environment file
├── .dockerignore              # Docker ignore file
├── .gitignore
├── Dockerfile                  # Docker image definition
├── docker-compose.yml         # Docker Compose configuration
├── pyproject.toml             # Poetry configuration
├── README.md                  # This file
└── tests/                     # Test directory
    └── __init__.py
```

## License

This project is part of a technical assessment.

