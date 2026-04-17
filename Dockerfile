# 1. Use the lightweight Python 3.12 slim image
FROM python:3.12-slim

# 2. Set environment variables
# Prevents Python from writing .pyc files and ensures output isn't buffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Install system dependencies for PostgreSQL (psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
# Copy requirements first to leverage Docker's cache
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code
COPY . .

# 7. Railway uses the PORT environment variable automatically
# We'll use Gunicorn to serve the app
EXPOSE 8080

# 8. Start the application with Gunicorn
#CMD ["uvicorn", "ProfileService.asgi:application", "--bind", "0.0.0.0:8080"]
CMD sh -c "python manage.py migrate && \
           daphne -b 0.0.0.0 -p 8000 ProfileService.asgi:appl