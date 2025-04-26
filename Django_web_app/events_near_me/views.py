import requests
from django.http import JsonResponse
from django.core.cache import cache
from django.shortcuts import render
from dateutil.parser import parse  # Для дат
from .tasks import (
    DEFAULT_EVENTS_CACHE_KEY,
    TICKETMASTER_API_KEY,
)  # Імпортуємо дефолтний ключ

NEARBY_CACHE_TTL_SECONDS = 10 * 60  # Кеш для nearby запитів – 10 хвилин
NEARBY_BASE_CACHE_KEY = "ticketmaster_events_nearby"


def get_default_events(request):
    """
    Повертає дефолтні кешовані події (оновлюються Celery таскою).
    Застосовує фільтри (keyword, date) до кешованих даних.
    """
    print("Request received for default events.")
    cached_events = cache.get(DEFAULT_EVENTS_CACHE_KEY)

    if cached_events is None:
        print("Cache MISS for default events.")
        return JsonResponse(
            {
                "events": [],
                "message": "Default event data is currently being updated. Please check back soon.",
            }
        )

    print(f"Cache HIT for default events. Found {len(cached_events)} events.")
    events = cached_events
    keyword = request.GET.get("keyword", "").lower()
    start_date_str = request.GET.get("startDate")
    end_date_str = request.GET.get("endDate")

    # Фільтрація за ключовим словом
    if keyword:
        filtered_by_keyword = []
        for event in events:
            # Перевірка назви події
            if keyword in event.get("name", "").lower():
                filtered_by_keyword.append(event)
                continue

            # Перевірка жанру в класифікаціях (якщо genre є словником або списком)
            classifications = event.get("classifications", [])
            genre_match = False
            for classification in classifications:
                genre = classification.get("genre")
                if isinstance(genre, dict):
                    if keyword in genre.get("name", "").lower():
                        genre_match = True
                        break
                elif isinstance(genre, list):
                    for g in genre:
                        if keyword in g.get("name", "").lower():
                            genre_match = True
                            break
                    if genre_match:
                        break

            if genre_match:
                filtered_by_keyword.append(event)
                continue

            # Перевірка назви міста для кожного місця проведення події
            venues = event.get("_embedded", {}).get("venues", [])
            for venue in venues:
                city = venue.get("city", {}).get("name", "").lower()
                if keyword in city:
                    filtered_by_keyword.append(event)
                    break

        events = filtered_by_keyword

    # Фільтрація за датою
    start_date_filter = None
    end_date_filter = None
    if start_date_str:
        try:
            start_date_filter = parse(start_date_str).date()
            print(f"Filtering default events START date: {start_date_filter}")
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date_filter = parse(end_date_str).date()
            print(f"Filtering default events END date: {end_date_filter}")
        except ValueError:
            pass

    if start_date_filter or end_date_filter:
        filtered_by_date = []
        for event in events:
            event_date_str = event.get("dates", {}).get("start", {}).get("localDate")
            if not event_date_str:
                continue  # Пропускаємо події без дати
            try:
                event_date = parse(event_date_str).date()
            except ValueError:
                continue  # Пропускаємо події з невірним форматом дати

            if start_date_filter and event_date < start_date_filter:
                continue
            if end_date_filter and event_date > end_date_filter:
                continue

            filtered_by_date.append(event)
        events = filtered_by_date

    print(f"Returning {len(events)} filtered default events.")
    return JsonResponse({"events": events})


def search_events_near_location(request):
    """
    Шукає події за конкретною локацією (lat, lon, radius).
    Спочатку перевіряє кеш для цієї локації.
    Якщо кешу немає – робить СИНХРОННИЙ запит до Ticketmaster API,
    кешує результат і повертає його.

    Оскільки API Ticketmaster не підтримує фільтр keyword,
    якщо користувач передає ключове слово, ми спочатку отримуємо всі події,
    а потім фільтруємо їх за ключовим словом (наприклад, перевіряючи назву події,
    жанр та назву міста у місцях проведення).
    """
    print("Request received for nearby events.")
    try:
        lat = request.GET.get("lat")
        lon = request.GET.get("lon")
        radius = request.GET.get("radius", "15")
        unit = request.GET.get("unit", "km")
        # Keyword будемо застосовувати пізніше, після отримання даних з API
        keyword = request.GET.get("keyword", "").lower()
        start_date_str = request.GET.get("startDate")
        end_date_str = request.GET.get("endDate")

        if not lat or not lon:
            return JsonResponse(
                {
                    "error": "Latitude and Longitude parameters are required for nearby search."
                },
                status=400,
            )

        lat_f = float(lat)
        lon_f = float(lon)
        radius_f = float(radius)

        latlong = f"{lat_f},{lon_f}"
        cache_key = f"{NEARBY_BASE_CACHE_KEY}_{latlong}_r{radius_f}{unit}"
        print(
            f"Nearby search. Location: {latlong}, Radius: {radius_f}{unit}. Cache key: {cache_key}"
        )

        cached_events = cache.get(cache_key)
        events = []
        if cached_events is not None:
            print(f"Cache HIT for nearby key: {cache_key}")
            events = cached_events
        else:
            print(
                f"Cache MISS for nearby key: {cache_key}. Fetching SYNCHRONOUSLY from Ticketmaster..."
            )
            url = "https://app.ticketmaster.com/discovery/v2/events.json"
            # Не передаємо keyword у запит, оскільки API його не підтримує.
            params = {
                "apikey": TICKETMASTER_API_KEY,
                "latlong": latlong,
                "radius": radius,
                "unit": unit,
                "countryCode": "IE",
                "size": 100,
                "sort": "date,asc",
            }
            if start_date_str:
                try:
                    params["startDateTime"] = parse(start_date_str).strftime(
                        "%Y-%m-%dT00:00:00Z"
                    )
                except ValueError:
                    pass
            if end_date_str:
                try:
                    params["endDateTime"] = parse(end_date_str).strftime(
                        "%Y-%m-%dT23:59:59Z"
                    )
                except ValueError:
                    pass

            try:
                response = requests.get(url, params=params, timeout=25)
                response.raise_for_status()
                data = response.json()
                events = data.get("_embedded", {}).get("events", [])
                if events:
                    cache.set(cache_key, events, NEARBY_CACHE_TTL_SECONDS)
                    print(
                        f"Nearby Sync: Fetched {len(events)} events from API and cached with key: {cache_key}"
                    )
                else:
                    print("Nearby Sync: No events found from API.")
                    cache.set(cache_key, [], NEARBY_CACHE_TTL_SECONDS)
            except requests.exceptions.RequestException as e:
                print(f"Nearby Sync ERROR fetching data: {e}")
                return JsonResponse(
                    {"error": "Could not fetch data from provider."}, status=502
                )
            except Exception as e:
                print(f"Nearby Sync UNEXPECTED ERROR during API fetch: {e}")
                return JsonResponse(
                    {"error": "An internal error occurred."}, status=500
                )

        # Якщо ключове слово задане, застосовуємо фільтрацію локально:
        if keyword:
            filtered_events = []
            for event in events:
                # Перевірка за назвою події
                name = event.get("name", "").lower()
                if keyword in name:
                    filtered_events.append(event)
                    continue

                # Перевірка жанру у класифікаціях
                classifications = event.get("classifications", [])
                genre_found = False
                for classification in classifications:
                    genre = classification.get("genre")
                    if isinstance(genre, dict):
                        if keyword in genre.get("name", "").lower():
                            genre_found = True
                            break
                    elif isinstance(genre, list):
                        for g in genre:
                            if keyword in g.get("name", "").lower():
                                genre_found = True
                                break
                        if genre_found:
                            break
                if genre_found:
                    filtered_events.append(event)
                    continue

                # Перевірка назви міста у місцях проведення
                venues = event.get("_embedded", {}).get("venues", [])
                for venue in venues:
                    city = venue.get("city", {}).get("name", "").lower()
                    if keyword in city:
                        filtered_events.append(event)
                        break
            events = filtered_events
            print(
                f"After filtering by keyword '{keyword}', {len(events)} events remain."
            )

        return JsonResponse({"events": events})
    except ValueError:
        return JsonResponse(
            {"error": "Invalid parameter format (lat/lon/radius must be numbers)."},
            status=400,
        )
    except Exception as e:
        print(f"An unexpected error occurred in search_events_near_location view: {e}")
        return JsonResponse(
            {"error": "An unexpected server error occurred."}, status=500
        )


def events_page(request):
    return render(request, "events_page.html")
