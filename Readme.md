# Genderize Proxy API

A lightweight REST API built with Django that integrates with the [Genderize.io](https://genderize.io) API to classify names by gender and return structured, processed results.

---

## Live API

```
https://genderizeproxy.up.railway.app
```

---

## Tech Stack

- **Python 3.11**
- **Django 6.0**
- **Django REST Framework**
- **django-cors-headers**
- **Gunicorn** (production server)
- **Railway** (deployment)

---

## Local Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/gandii001/ProfileService.git
   cd ProfileService
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv

   # Mac/Linux
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the root directory:
   ```
   SECRET_KEY=your-secret-key-here
   ```

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```

---

## API Reference

### Classify Name

Calls the Genderize.io API with the provided name, processes the response, and returns a structured result.

```
GET /api/classify?name={name}
```

#### Query Parameters

| Parameter | Type   | Required | Description          |
|-----------|--------|----------|----------------------|
| `name`    | string | Yes      | The name to classify |

---

#### Success Response — `200 OK`

```json
{
  "status": "success",
  "data": {
    "name": "john",
    "gender": "male",
    "probability": 0.99,
    "sample_size": 1234,
    "is_confident": true,
    "processed_at": "2026-04-14T12:00:00Z"
  }
}
```

#### Response Fields

| Field          | Type    | Description                                                                 |
|----------------|---------|-----------------------------------------------------------------------------|
| `name`         | string  | The name that was classified                                                |
| `gender`       | string  | Predicted gender (`male` or `female`)                                       |
| `probability`  | float   | Confidence probability from Genderize (0 to 1)                              |
| `sample_size`  | integer | Number of data points used for the prediction                               |
| `is_confident` | boolean | `true` only when `probability >= 0.7` AND `sample_size >= 100`              |
| `processed_at` | string  | UTC timestamp of when the request was processed (ISO 8601)                  |

---

#### Error Responses

All errors follow this structure:
```json
{
  "status": "error",
  "message": "<error message>"
}
```

| Status Code | Reason                                              |
|-------------|-----------------------------------------------------|
| `400`       | Missing or empty `name` parameter                   |
| `422`       | `name` contains non-alphabetic characters           |
| `502`       | Genderize API is unreachable                        |
| `504`       | Genderize API request timed out                     |

#### No Prediction Available

When Genderize has no data for the provided name:
```json
{
  "status": "error",
  "message": "No prediction available for the provided name"
}
```

---

## Example Requests

**Valid name**
```bash
curl https://genderizeproxy.up.railway.app/api/classify?name=john
```

**Missing name**
```bash
curl https://genderizeproxy.up.railway.app/api/classify
# Returns 400
```

**Invalid name (contains numbers)**
```bash
curl https://genderizeproxy.up.railway.app/api/classify?name=j0hn
# Returns 422
```

---

## Confidence Logic

`is_confident` is determined by two conditions that **must both be true**:

```
probability >= 0.70  AND  sample_size >= 100
```

If either condition fails, `is_confident` is `false`.

---

## CORS

All responses include:
```
Access-Control-Allow-Origin: *
```

---

## Deployment

This project is deployed on [Railway](https://railway.app). To deploy your own instance:

1. Push the repo to GitHub
2. Create a new Railway project and connect the GitHub repo
3. Add the `SECRET_KEY` environment variable in Railway's Variables tab
4. Railway auto-detects the Python project and deploys using the `Procfile`

**`Procfile`**
```
web: gunicorn ProfileService.wsgi
```
