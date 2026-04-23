
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD python manage.py migrate && \
     python manage.py seed_profiles_command && \
     daphne -b 0.0.0.0 -p 8000 ProfileService.asgi:application
#python manage.py migrate && daphne -b 0.0.0.0 -p ${PORT:-8000} ProfileService.asgi:application