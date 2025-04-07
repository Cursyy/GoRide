# flake8: noqa

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GoRide.settings")
django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from support.routing import websocket_urlpatterns as support_routes
from get_direction.routing import websocket_urlpatterns as get_direction_routes


application = ProtocolTypeRouter(
    {
        "http": ASGIStaticFilesHandler(get_asgi_application()),
        "websocket": AuthMiddlewareStack(
            URLRouter(support_routes + get_direction_routes)
        ),
    }
)
