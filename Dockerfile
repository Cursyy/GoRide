# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


WORKDIR /code

# Copy dependecies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy whole project into the container
COPY . .

# Run collectstatic (for production; might be off for development)
# RUN python manage.py collectstatic --noinput

# By default Daphne run first, but the command redecllared in the  docker-compose
CMD ["daphne", "GoRide.asgi:application", "--bind", "0.0.0.0", "--port", "8000"]
