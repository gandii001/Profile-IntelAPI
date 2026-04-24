# Intelligence Query Engine API - Demographic Query Engine

A production-ready Django REST API for querying, filtering, and analyzing demographic profile data. Built for **Insighta Labs**, this system enables marketing teams, product teams, and growth analysts to segment users, identify patterns, and query large datasets efficiently.

## 🎯 Overview

The Profile Intelligence API is a queryable demographic database that collects profile data from external APIs, stores it in PostgreSQL, and exposes powerful endpoints for filtering, sorting, pagination, and natural language searching.

**Current Capabilities:**
- ✅ Advanced filtering (gender, age, country, probability thresholds)
- ✅ Combined multi-condition filters
- ✅ Sorting by multiple fields (age, created_at, gender_probability)
- ✅ Offset-based pagination with configurable limits
- ✅ Rule-based natural language query parsing
- ✅ 2026+ profile records seeded and ready
- ✅ UUID v7 primary keys
- ✅ CORS-enabled for frontend integration

---

## 📋 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Django REST API                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  GET /api/profiles          → Advanced filtering & sorting  │
│  POST /api/profiles         → Create new profile            │
│  GET /api/profiles/<id>     → Get single profile            │
│  DELETE /api/profiles/<id>  → Delete profile                │
│  GET /api/profiles/search   → Natural language search       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    PostgreSQL Database                       │
│  ├─ Profiles (2026 records)                                 │
│  └─ Indexes on: gender, age, country_id, age_group, ...    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 12+
- Docker & Docker Compose (optional)

### Installation (Local)

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/Profile-IntelAPI.git
cd Profile-IntelAPI
```

2. **Create virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
# Create .env file
cp .env.example .env

# Edit .env with your database credentials
DATABASE_URL=postgresql://user:password@localhost:5432/profile_intel
SECRET_KEY=your-secret-key-here
DEBUG=True
```

5. **Run migrations**:
```bash
python manage.py migrate
```

6. **Seed database**:
```bash
python manage.py seed_profiles
```

7. **Start server**:
```bash
python manage.py runserver
```

Server runs at `http://localhost:8000`

### Installation (Docker)

1. **Build and run**:
```bash
docker-compose up --build
```

2. **Seed database** (in another terminal):
```bash
docker-compose exec web python manage.py seed_profiles
```

Server runs at `http://localhost:8000`

---

## 📊 Database Schema

### Profile Model

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID v7 | Primary key, auto-generated |
| `name` | VARCHAR(255) | Unique identifier |
| `gender` | VARCHAR(20) | "male" or "female" |
| `gender_probability` | FLOAT | Confidence score (0-1) |
| `age` | INT | Exact age in years |
| `age_group` | VARCHAR(20) | "child", "teenager", "adult", "senior" |
| `country_id` | VARCHAR(2) | ISO 3166-1 alpha-2 code |
| `country_name` | VARCHAR(100) | Full country name |
| `country_probability` | FLOAT | Confidence score (0-1) |
| `created_at` | TIMESTAMP | UTC ISO 8601 format |

**Indexes**: `gender`, `age`, `country_id`, `age_group`, `created_at`

---

## 🔍 API Endpoints

### 1. List Profiles with Filtering

**Endpoint**: `GET /api/profiles`

**Query Parameters**:

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `gender` | string | `male` | Filter by gender |
| `age_group` | string | `adult` | Filter by age group |
| `country_id` | string | `NG` | Filter by ISO country code |
| `min_age` | integer | `25` | Minimum age (inclusive) |
| `max_age` | integer | `65` | Maximum age (inclusive) |
| `min_gender_probability` | float | `0.8` | Minimum gender confidence |
| `min_country_probability` | float | `0.7` | Minimum country confidence |
| `sort_by` | string | `age` | Sort field: `age`, `created_at`, `gender_probability` |
| `order` | string | `desc` | Sort order: `asc` or `desc` |
| `page` | integer | `1` | Page number (default: 1) |
| `limit` | integer | `10` | Results per page, max 50 (default: 10) |

**Examples**:

```bash
# Simple filter: males from Nigeria
curl "https://api.example.com/api/profiles?gender=male&country_id=NG"

# Age range: adults aged 25-40
curl "https://api.example.com/api/profiles?min_age=25&max_age=40&age_group=adult"

# Sorted pagination: oldest profiles first
curl "https://api.example.com/api/profiles?sort_by=age&order=desc&page=1&limit=20"

# High confidence: gender probability >= 0.9
curl "https://api.example.com/api/profiles?min_gender_probability=0.9"

# Combined complex filter
curl "https://api.example.com/api/profiles?gender=female&min_age=30&country_id=NG&sort_by=created_at&order=desc&limit=15"
```

**Response**:
```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 245,
  "data": [
    {
      "id": "018f3c4f-0000-7000-8000-000000000001",
      "name": "john doe",
      "gender": "male",
      "gender_probability": 0.95,
      "age": 35,
      "age_group": "adult",
      "country_id": "NG",
      "country_name": "Nigeria",
      "country_probability": 0.88,
      "created_at": "2026-04-23T10:30:45Z"
    }
  ]
}
```

---

### 2. Natural Language Search

**Endpoint**: `GET /api/profiles/search`

**Query Parameters**:

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `q` | string | `young males from nigeria` | Natural language query (required) |
| `page` | integer | `1` | Page number (default: 1) |
| `limit` | integer | `10` | Results per page (default: 10) |

**Supported Keywords**:

**Gender**: male, males, man, men, boy, boys, female, females, woman, women, girl, girls

**Age Groups**: child, teen, teenager, young, adult, senior, elderly

**Age Ranges**: 
- "above X", "over X" → min_age
- "below X", "under X" → max_age
- "between X and Y"
- "X years old"

**Countries**: Full country names (e.g., "Nigeria", "Kenya", "Ghana")

**Examples**:

```bash
# Young males from Nigeria
curl "https://api.example.com/api/profiles/search?q=young+males+from+nigeria"

# Females above 30
curl "https://api.example.com/api/profiles/search?q=females+above+30"

# Adult males from Kenya
curl "https://api.example.com/api/profiles/search?q=adult+males+from+kenya"

# Teenagers from South Africa
curl "https://api.example.com/api/profiles/search?q=teenagers+from+south+africa&page=2&limit=20"

# Children below 12
curl "https://api.example.com/api/profiles/search?q=children+below+12"

# Seniors aged 65+
curl "https://api.example.com/api/profiles/search?q=seniors+above+65"
```

**Query Parsing Rules**:

| Query | Interpreted As |
|-------|-----------------|
| `young males` | gender=male, min_age=16, max_age=24 |
| `females above 30` | gender=female, min_age=30 |
| `adult people from Kenya` | age_group=adult, country_id=KE |
| `male and female teenagers` | age_group=teenager (no gender filter) |
| `people from Nigeria` | country_id=NG |

**Response**:
```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 87,
  "data": [...]
}
```

---

### 3. Create Profile

**Endpoint**: `POST /api/profiles`

**Request Body**:
```json
{
  "name": "Jane Smith"
}
```

**Process**:
1. Calls external APIs (Genderize, Agify, Nationalize)
2. Validates responses
3. Stores profile in database
4. Returns profile with all enriched fields

**Response**:
```json
{
  "status": "success",
  "data": {
    "id": "018f3c4f-0000-7000-8000-000000000001",
    "name": "jane smith",
    "gender": "female",
    "gender_probability": 0.92,
    "age": 28,
    "age_group": "adult",
    "country_id": "US",
    "country_name": "United States",
    "country_probability": 0.75,
    "created_at": "2026-04-23T10:35:12Z"
  }
}
```

---

### 4. Get Single Profile

**Endpoint**: `GET /api/profiles/<id>`

**Example**:
```bash
curl "https://api.example.com/api/profiles/018f3c4f-0000-7000-8000-000000000001"
```

**Response**:
```json
{
  "status": "success",
  "data": { ... }
}
```

---

### 5. Delete Profile

**Endpoint**: `DELETE /api/profiles/<id>`

**Response**:
```
HTTP 204 No Content
```

---

## ⚠️ Error Handling

All errors return a consistent format:

```json
{
  "status": "error",
  "message": "Descriptive error message"
}
```

**HTTP Status Codes**:

| Code | Scenario |
|------|----------|
| `200 OK` | Successful query |
| `201 Created` | Profile created |
| `204 No Content` | Profile deleted |
| `400 Bad Request` | Missing required parameter |
| `404 Not Found` | Profile doesn't exist |
| `422 Unprocessable Entity` | Invalid parameter type/value |
| `500 Internal Server Error` | Server error |
| `502 Bad Gateway` | External API error |

**Example Errors**:

```bash
# Missing query parameter
curl "https://api.example.com/api/profiles/search"
# Returns: {"status": "error", "message": "Missing or empty query parameter 'q'"}

# Invalid age value
curl "https://api.example.com/api/profiles?min_age=abc"
# Returns: {"status": "error", "message": "min_age must be an integer"}

# Invalid sort field
curl "https://api.example.com/api/profiles?sort_by=invalid"
# Returns: {"status": "error", "message": "Invalid sort_by..."}

# Can't parse natural language
curl "https://api.example.com/api/profiles/search?q=xyz%20nonsense"
# Returns: {"status": "error", "message": "Unable to interpret query"}
```

---

## 🔒 Performance & Security

### Performance Features
- **Database Indexes**: On frequently filtered columns (gender, age, country_id, age_group, created_at)
- **Pagination**: Prevents loading entire dataset into memory
- **Offset-based**: Efficient for large result sets
- **Query Optimization**: Uses Django ORM with select_related/prefetch_related where applicable

### Performance Metrics
- **Database Size**: ~2026 profiles (~500KB)
- **Query Latency**: <100ms for typical filters
- **Pagination Limit**: Max 50 results per page to prevent abuse

### Security Features
- **CORS Enabled**: Access-Control-Allow-Origin: *
- **Input Validation**: All query parameters validated
- **SQL Injection Protection**: Django ORM parameterized queries
- **Rate Limiting**: Recommended to add at deployment

---

## 📚 Data Seeding

### Seed File Structure
The `seed_profiles.json` contains 2026 profiles with demographic data:

```json
{
  "profiles": [
    {
      "name": "John Doe",
      "gender": "male",
      "gender_probability": 0.95,
      "age": 35,
      "age_group": "adult",
      "country_id": "NG",
      "country_name": "Nigeria",
      "country_probability": 0.88
    }
  ]
}
```

### Seeding Process

```bash
python manage.py seed_profiles
```

**Features**:
- ✅ Idempotent (no duplicates on re-run)
- ✅ Checks by name uniqueness
- ✅ Uses pycountry for country validation
- ✅ Logs creation/skip/error counts

**Output**:
```
Starting to seed 2026 profiles...

✓ Seeding Complete!
  Created: 2026
  Skipped (already exist): 0
  Errors: 0
  Total in DB: 2026
```

---

## 🛠️ Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,localhost

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,http://localhost:3000
```

### Django Settings (ProfileService/settings.py)

Key configurations already set:
- ✅ ASGI for async support
- ✅ CORS middleware enabled
- ✅ PostgreSQL database backend
- ✅ REST framework configuration
- ✅ UUID field support

---

## 🚢 Deployment

### Railway (Current)

```bash
git push origin main
# Auto-deploys from GitHub
# Runs migrations automatically (via Procfile release command)
# Database credentials from Railway environment
```

### Docker

```bash
docker-compose up --build
```

### Heroku

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:standard-0
git push heroku main
heroku run python manage.py seed_profiles
```

### AWS/GCP/Azure

Use standard Django deployment practices with:
- Gunicorn/uWSGI for WSGI
- Nginx as reverse proxy
- PostgreSQL managed database
- Environment variables for secrets

---

## 🧪 Testing

### Using curl

```bash
# List all profiles
curl https://api.example.com/api/profiles

# Create profile
curl -X POST https://api.example.com/api/profiles \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User"}'

# Search
curl "https://api.example.com/api/profiles/search?q=young+males+from+nigeria"
```

### Using Python

```python
import requests

# List
response = requests.get('https://api.example.com/api/profiles', params={
    'gender': 'male',
    'min_age': 25,
    'country_id': 'NG'
})
print(response.json())

# Search
response = requests.get('https://api.example.com/api/profiles/search', params={
    'q': 'young females from Kenya'
})
print(response.json())
```

---

## 📁 Project Structure

```
Profile-IntelAPI/
├── api/
│   ├── management/
│   │   └── commands/
│   │       └── seed_profiles.py       # Data seeding command
│   ├── migrations/
│   │   └── 0001_initial.py            # Database schema
│   ├── models.py                      # Profile model
│   ├── views.py                       # API endpoints
│   ├── urls.py                        # URL routing
│   ├── serializers.py                 # DRF serializers
│   ├── service.py                     # Business logic
│   └── query_parser.py                # NLP query parser
├── ProfileService/
│   ├── settings.py                    # Django config
│   ├── urls.py                        # Main URL config
│   ├── wsgi.py                        # WSGI entry point
│   └── asgi.py                        # ASGI entry point
├── seed_profiles.json                 # Seed data (2026 profiles)
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Docker image
├── docker-compose.yml                 # Docker services
├── Procfile                           # Deployment config
└── README.md                          # This file
```

---

## 📦 Dependencies

- **Django 4.2+**: Web framework
- **djangorestframework**: REST API framework
- **psycopg2**: PostgreSQL adapter
- **django-cors-headers**: CORS support
- **pycountry**: Country data (ISO codes)
- **daphne**: ASGI server
- **httpx**: Async HTTP client

See `requirements.txt` for full list.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📝 License

MIT License - see LICENSE file for details

---

## 📞 Support

### Documentation
- API Documentation: See endpoints above
- Setup Guide: See SETUP_INSTRUCTIONS.md
- Troubleshooting: See common errors above

### Issues & Questions
- GitHub Issues: Report bugs
- GitHub Discussions: Ask questions
- Email: support@example.com

---

## 🎓 Learning Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [pycountry](https://pypi.org/project/pycountry/)

---

## 🗂️ Changelog

### v2.0 (Stage 2 - Current)
- ✅ Advanced filtering (7 filter types)
- ✅ Combined multi-condition filters
- ✅ Sorting (3 fields, 2 orders)
- ✅ Pagination (10-50 results per page)
- ✅ Natural language query parsing
- ✅ 2026 profiles seeded
- ✅ Database indexes for performance
- ✅ pycountry integration for country names
- ✅ Comprehensive error handling
- ✅ CORS enabled

### v1.0 (Stage 1 - Initial)
- Basic CRUD endpoints
- Profile data collection from external APIs
- PostgreSQL storage
- UUID v7 primary keys

---

## 🎯 Roadmap

**Upcoming Features**:
- [ ] Advanced aggregation (count, average confidence)
- [ ] Saved filter presets
- [ ] Bulk import/export
- [ ] API authentication (OAuth2/JWT)
- [ ] Rate limiting
- [ ] Caching layer (Redis)
- [ ] Analytics dashboard
- [ ] WebSocket real-time updates

---

**Built with love for Insighta Labs**

Last Updated: 2026-04-23