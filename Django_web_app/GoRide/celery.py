# celery init
# https://docs.celeryq.dev/en/latest/django/first-steps-with-django.html

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GoRide.settings")

app = Celery("GoRide")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
