#!/bin/bash

# 1. Create and start containers
docker-compose build
docker-compose up
# This command will create all necessary containers (Django, Redis, PostgreSQL, etc.) and start them.
docker-compose up --build

# 2. Apply migrations in the container
# This command applies database migrations in the container.
docker-compose exec web python manage.py migrate

# 3. Create a Django superuser
# Use this command to create a superuser for accessing the Django admin panel.
docker-compose exec web python manage.py createsuperuser

# 4. Collect static files
# This command collects all static files (CSS, JavaScript, images) for serving through Nginx.
docker-compose exec web python manage.py collectstatic --noinput

# 5. Start Celery
# This command starts the Celery process for background task processing.
docker-compose exec celery celery -A GoRide.celery worker --loglevel=info

# 6. Start Celery Beat (if needed)
# This command starts Celery Beat for task scheduling.
docker-compose exec celery-beat celery -A GoRide.celery beat --loglevel=info

# 7. Run tests
# Run tests in the container to verify the functionality of the project.
docker-compose exec web python manage.py test

# 8. View container logs
# This command allows you to view container logs for debugging or monitoring.
docker-compose logs web

# 9. Restart containers (if needed)
# This command restarts all services in containers after code changes.
docker-compose restart

# 10. Open Redis CLI
# This command opens the Redis CLI for debugging or monitoring Redis on docker.
docker exec -it redis redis-cli