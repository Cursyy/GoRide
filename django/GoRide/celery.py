# celery init
# https://docs.celeryq.dev/en/latest/django/first-steps-with-django.html

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GoRide.settings")

app = Celery("GoRide")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "fetch-ticketmaster-events-every-10-mins": {
        "task": "events_near_me.tasks.fetch_and_cache_default_events",
        "schedule": crontab(minute="*/10"),
    },
}

app.conf.timezone = "Europe/Dublin"


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
