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
├── .gitignore
├── pyproject.toml             # Poetry configuration
├── README.md                  # This file
└── tests/                     # Test directory
    └── __init__.py
```

## License

This project is part of a technical assessment.

