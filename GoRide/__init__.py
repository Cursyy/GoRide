# celery conf
# https://docs.celeryq.dev/en/latest/django/first-steps-with-django.html

from .celery import app as celery_app

__all__ = ("celery_app",)
