def location_context(request):
    user_latitude = request.session.get("user_latitude", None)
    user_longitude = request.session.get("user_longitude", None)

    return {
        "session_user_latitude": user_latitude,
        "session_user_longitude": user_longitude,
        "session_user_location_available": user_latitude is not None
        and user_longitude is not None,
    }
