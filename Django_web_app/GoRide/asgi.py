# flake8: noqa

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GoRide.settings")
django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from core.routing import websocket_urlpatterns as core_routes

application = ProtocolTypeRouter(
    {
        "http": ASGIStaticFilesHandler(get_asgi_application()),
        "websocket": AuthMiddlewareStack(URLRouter(core_routes)),
    }
)
