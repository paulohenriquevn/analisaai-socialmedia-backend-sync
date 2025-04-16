# Analisa.ai Social Media Sync Service

Backend service for syncing social media data from platforms like Instagram, Facebook, and TikTok.

## Overview

This service is responsible for:
- Collecting social media data via the Apify.com API
- Processing and transforming data into the Analisa.ai data model
- Providing APIs for synchronizing data on-demand
- Running background tasks for regular data updates

## Features

- **Real-time Social Media Data Sync** - Pulls data from Instagram, Facebook, and TikTok
- **Asynchronous Processing** - Uses Celery for background task execution
- **Rate Limiting** - Prevents API abuse and manages quotas
- **Error Handling** - Robust error handling and reporting
- **Metrics and Monitoring** - Prometheus integration for tracking performance

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 15
- Redis 7

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Create a `.env` file in the root directory with the following variables:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/analisaai
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key-here
APIFY_API_TOKEN=your-apify-token-here
LOG_LEVEL=INFO
ENCRYPTION_KEY=your-encryption-key-here
```

### Running with Docker

The easiest way to run the service is with Docker Compose:

```bash
docker-compose up -d
```

This will start:
- The API service
- A Celery worker
- PostgreSQL database
- Redis
- Prometheus for monitoring

### Running Locally

1. Start the API server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Start the Celery worker:
   ```bash
   celery -A app.worker.celery worker --loglevel=info
   ```

## API Documentation

Once running, the API documentation is available at:
- Swagger UI: http://localhost:8001/api/docs
- ReDoc: http://localhost:8001/api/redoc

### Main Endpoints

- `POST /api/sync/user/{user_id}` - Synchronize data for a specific user
- `POST /api/sync/all-users` - Synchronize data for all active users
- `GET /health/ping` - Simple health check
- `GET /health/status` - Comprehensive health check

## Architecture

- **FastAPI** - Modern, high-performance web framework
- **SQLAlchemy** - ORM for database interactions
- **Celery** - Distributed task queue
- **Redis** - Message broker and result backend
- **Prometheus** - Monitoring and metrics

## Error Handling

The service implements comprehensive error handling:
- HTTP error responses with descriptive messages
- Structured logging for debugging
- Error tracking through Prometheus metrics

## Security

- JWT authentication for API access
- Encryption of sensitive social media tokens
- Admin-only access for certain endpoints

## Troubleshooting

Common issues:

1. **Connection errors** - Check if PostgreSQL and Redis are running
2. **Authentication failures** - Verify JWT_SECRET matches the main backend
3. **Sync failures** - Check APIFY_API_TOKEN validity and quota

## License

This project is proprietary and confidential.

## Contact

For support or questions, contact the Analisa.ai development team.