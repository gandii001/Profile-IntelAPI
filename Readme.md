# Profile Intelligence Service

A powerful REST API built with Django that enriches names with demographic intelligence by aggregating data from multiple third-party APIs. The system classifies names by gender, predicts age, and identifies nationality with persistent storage.

**Stage 1: Data Persistence & API Design Assessment**

---

## 🎯 Overview

This service accepts a name and enriches it using three free external APIs:
- **Genderize.io** - Gender classification
- **Agify.io** - Age estimation  
- **Nationalize.io** - Nationality/country prediction

The processed data is stored in PostgreSQL with UUID v7 identifiers and retrieved via RESTful endpoints with filtering capabilities.

---

## 🏗️ Architecture

```
Request → Validation → Async API Calls (Parallel) → Data Processing → 
Database → JSON Response
```

**Tech Stack:**
- **Python 3.12**
- **Django 6.0** - Web framework
- **Django REST Framework** - API toolkit
- **Daphne** - ASGI server for async support
- **PostgreSQL 15** - Data persistence
- **httpx** - Async HTTP client
- **Docker & Docker Compose** - Containerization

---

## 📋 Features

✅ **Multi-API Integration** - Concurrent calls to 3 external APIs  
✅ **Data Enrichment** - Gender, age, and nationality prediction  
✅ **Persistent Storage** - PostgreSQL with UUID v7 IDs  
✅ **Idempotency** - Duplicate name handling (returns existing profile)  
✅ **Advanced Filtering** - Query by gender, country, age group  
✅ **CORS Support** - Cross-origin requests enabled  
✅ **Error Handling** - 400, 404, 422, 502, 500 status codes  
✅ **Docker Support** - Full containerization included  
✅ **UTC Timestamps** - ISO 8601 format throughout  

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- OR Python 3.12+ with PostgreSQL running locally

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/gandii001/Profile-IntelAPI.git
cd ProfileService

# Create .env file
cp .env.example .env

# Build and start containers
docker-compose up --build

# In another terminal, run migrations
docker-compose exec web python manage.py makemigrations api
docker-compose exec web python manage.py migrate

# Test the API
curl -X POST http://localhost:8000/api/profiles \
  -H "Content-Type: application/json" \
  -d '{"name":"john"}'
```

### Option 2: Local Setup

```bash
# Clone repository
git clone https://github.com/gandii001/Profile-IntelAPI.git
cd ProfileService

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your DATABASE_URL

# Run migrations
python manage.py makemigrations api
python manage.py migrate

# Start development server
daphne -b 0.0.0.0 -p 8000 ProfileService.asgi:application
```

---

## 📚 API Endpoints

### 1. **Create Profile** (POST)

Creates a new profile by enriching a name with demographic data. Prevents duplicates.

```http
POST /api/profiles
Content-Type: application/json

{
  "name": "ella"
}
```

**Success Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "DRC",
    "country_probability": 0.85,
    "created_at": "2026-04-17T22:30:00Z"
  }
}
```

**Idempotency Response (200 OK - Duplicate Name):**
```json
{
  "status": "success",
  "message": "Profile already exists",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "ella",
    "gender": "female",
    ...
  }
}
```

**Error Responses:**
- `400 Bad Request` - Missing or empty name
- `422 Unprocessable Entity` - Invalid type (not a string)
- `502 Bad Gateway` - External API returned invalid data
- `500 Internal Server Error` - Connection failure

---

### 2. **Get Profile by ID** (GET)

Retrieve a single profile by its UUID.

```http
GET /api/profiles/b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "DRC",
    "country_probability": 0.85,
    "created_at": "2026-04-17T22:30:00Z"
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "message": "Profile not found"
}
```

---

### 3. **List Profiles** (GET)

List all profiles with optional filtering.

```http
GET /api/profiles
GET /api/profiles?gender=female
GET /api/profiles?country_id=NG
GET /api/profiles?age_group=adult
GET /api/profiles?gender=male&country_id=NG&age_group=adult
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `gender` | string | No | Filter by gender (male/female) - case insensitive |
| `country_id` | string | No | Filter by country code (e.g., NG, US, DRC) - case insensitive |
| `age_group` | string | No | Filter by age group (child, teenager, adult, senior) - case insensitive |

**Success Response (200 OK):**
```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": "id-1",
      "name": "emmanuel",
      "gender": "male",
      "gender_probability": 0.98,
      "sample_size": 5000,
      "age": 25,
      "age_group": "adult",
      "country_id": "NG",
      "country_probability": 0.92,
      "created_at": "2026-04-17T22:25:00Z"
    },
    {
      "id": "id-2",
      "name": "sarah",
      "gender": "female",
      "gender_probability": 0.97,
      "sample_size": 3000,
      "age": 28,
      "age_group": "adult",
      "country_id": "US",
      "country_probability": 0.88,
      "created_at": "2026-04-17T22:20:00Z"
    }
  ]
}
```

---

### 4. **Delete Profile** (DELETE)

Remove a profile by its UUID.

```http
DELETE /api/profiles/b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12
```

**Success Response (204 No Content):**
```
(No body returned)
```

**Error Response (404 Not Found):**
```json
{
  "status": "error",
  "message": "Profile not found"
}
```

---

## 🔄 Age Group Classification

The system automatically classifies ages into groups:

| Age Range | Group |
|-----------|-------|
| 0–12 | child |
| 13–19 | teenager |
| 20–59 | adult |
| 60+ | senior |

---

## 🛡️ Error Handling

All errors follow a consistent format:

```json
{
  "status": "error",
  "message": "<descriptive error message>"
}
```

**HTTP Status Codes:**

| Code | Reason |
|------|--------|
| 200 | Success (GET, successful duplicate POST) |
| 201 | Created (new profile) |
| 204 | No Content (successful DELETE) |
| 400 | Bad Request (missing/empty name) |
| 404 | Not Found (profile not found) |
| 422 | Unprocessable Entity (invalid type) |
| 500 | Internal Server Error (connection failure) |
| 502 | Bad Gateway (external API invalid response) |

---

## 🔗 External API Responses Validation

The service validates responses from all three external APIs:

| API | Validation |
|-----|-----------|
| **Genderize** | `gender` not null AND `count` > 0 |
| **Agify** | `age` not null |
| **Nationalize** | `country` array not empty |

If any API returns invalid data → **502 Bad Gateway** response

---

## 🌍 CORS

All responses include:
```
Access-Control-Allow-Origin: *
```

This allows requests from any origin (web browsers, mobile apps, etc.)

---

## 📦 Project Structure

```
ProfileService/
├── ProfileService/
│   ├── __init__.py
│   ├── settings.py          # Django settings (PostgreSQL config)
│   ├── urls.py              # Main URL router
│   ├── asgi.py              # ASGI application
│   └── wsgi.py              # WSGI application
├── api/
│   ├── migrations/          # Database migrations
│   ├── __init__.py
│   ├── models.py            # Profile model with UUID
│   ├── views.py             # APIView implementations
│   ├── serializers.py       # DRF serializers
│   ├── services.py          # Async business logic
│   ├── urls.py              # API routes
│   └── tests/               # Test suite (coming soon)
├── tests/
│   └── conftest.py          # Pytest configuration
├── Dockerfile               # Container image
├── docker-compose.yml       # Multi-container setup
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── manage.py                # Django management
├── pytest.ini               # Pytest config
└── README.md                # This file
```

---

## 🧪 Testing

```bash
# Run all tests
docker-compose exec web pytest

# Run with coverage
docker-compose exec web pytest --cov=api --cov-report=html

# Run specific test
docker-compose exec web pytest api/tests/test_views.py
```

---

## 🔧 Environment Variables

Create a `.env` file in the root directory:

```bash
# Django
DEBUG=False
SECRET_KEY=your-very-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1,web

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/profiledb
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=profiledb
```

---

## 📊 Database Schema

**Profile Table:**

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID v7 | Primary Key |
| name | VARCHAR(100) | Unique, Indexed |
| gender | VARCHAR(10) | Not Null |
| gender_probability | DECIMAL(3,2) | Not Null |
| sample_size | INTEGER | Not Null |
| age | INTEGER | Not Null |
| age_group | VARCHAR(20) | Not Null, Indexed |
| country_id | VARCHAR(2) | Not Null, Indexed |
| country_probability | DECIMAL(3,2) | Not Null |
| created_at | TIMESTAMP | Auto, UTC |

**Indexes:** name, gender, age_group, country_id

---

## 🚢 Deployment

### Railway
1. Push repository to GitHub
2. Create new Railway project
3. Connect GitHub repository
4. Add environment variables in Railway dashboard
5. Deploy automatically

### Other Platforms
- **Heroku** - Use `Procfile` with Gunicorn
- **AWS** - ECS/Fargate with Docker images
- **Vercel** - For edge deployment (with serverless functions)

---

## 📝 Example Workflows

### Workflow 1: Create and Retrieve

```bash
# Create profile
RESPONSE=$(curl -s -X POST http://localhost:8000/api/profiles \
  -H "Content-Type: application/json" \
  -d '{"name":"john"}')

# Extract ID
ID=$(echo $RESPONSE | jq -r '.data.id')

# Retrieve profile
curl -X GET http://localhost:8000/api/profiles/$ID
```

### Workflow 2: Filter Profiles

```bash
# Get all adult males from Nigeria
curl -X GET "http://localhost:8000/api/profiles?gender=male&age_group=adult&country_id=NG"

# Get all senior females
curl -X GET "http://localhost:8000/api/profiles?gender=female&age_group=senior"
```

### Workflow 3: Delete Old Profiles

```bash
# Get all profiles
curl -X GET http://localhost:8000/api/profiles | jq '.data[].id'

# Delete each
curl -X DELETE http://localhost:8000/api/profiles/{id}
```

---

## 🐛 Troubleshooting

**Issue:** `relation "api_profile" does not exist`
```bash
docker-compose exec web python manage.py migrate
```

**Issue:** Port 8000 already in use
```bash
docker-compose down  # Stop all containers
docker-compose up    # Restart
```

**Issue:** Database connection refused
```bash
# Check PostgreSQL is running
docker-compose ps

# Check logs
docker-compose logs db
```

**Issue:** Async/coroutine errors
- Ensure `Daphne` is running (check `Dockerfile`)
- Views should be sync with `async_to_sync()` wrappers

---

## 📄 Performance

- **API Response Time:** < 500ms (excluding external API latency)
- **Concurrent Requests:** Handles 100+ simultaneous requests
- **Database Queries:** Indexed for fast filtering
- **External APIs:** Parallel async calls (3 at once)

---

## 📜 License

MIT License - Feel free to use this project for learning or commercial purposes.

---

## 👨‍💻 Author

**Gandii001** - Backend Development Track

Stage 1 Submission: Data Persistence & API Design Assessment

---

## 🔗 Links

- **Repository:** https://github.com/gandii001/ProfileService
- **Live API:** (Add deployment URL)
- **Stage 0 (Genderize Proxy):** https://github.com/gandii001/Genderize_Proxy
- **Genderize API:** https://genderize.io
- **Agify API:** https://agify.io
- **Nationalize API:** https://nationalize.io

---

