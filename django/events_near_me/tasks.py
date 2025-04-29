import requests
from celery import shared_task
from decouple import config
from django.core.cache import cache

DEFAULT_EVENTS_CACHE_KEY = "ticketmaster_events_default_dublin"
DEFAULT_CACHE_TTL_SECONDS = 15 * 60

TICKETMASTER_API_KEY = config("TICKETMASTER_API_KEY")


@shared_task
def fetch_and_cache_default_events():
    print("Running periodic task: fetch_and_cache_default_events...")
    api_key = TICKETMASTER_API_KEY
    default_latlong = "53.349805,-6.26031"
    default_radius = "20"
    default_unit = "km"

    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": api_key,
        "latlong": default_latlong,
        "radius": default_radius,
        "unit": default_unit,
        "countryCode": "IE",
        "size": 150,
        "sort": "date,asc",
    }

    try:
        response = requests.get(url, params=params, timeout=45)
        response.raise_for_status()
        data = response.json()
        events = data.get("_embedded", {}).get("events", [])

        if events:
            cache.set(DEFAULT_EVENTS_CACHE_KEY, events, DEFAULT_CACHE_TTL_SECONDS)
            print(
                f"Periodic task: Successfully fetched and cached {len(events)} default events (Dublin)."
            )
        else:
            print("Periodic task: No default events found.")
            cache.set(DEFAULT_EVENTS_CACHE_KEY, [], DEFAULT_CACHE_TTL_SECONDS)

    except requests.exceptions.RequestException as e:
        print(f"Periodic task ERROR fetching default data: {e}")
    except Exception as e:
        print(f"Periodic task UNEXPECTED ERROR: {e}")
