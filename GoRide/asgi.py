# flake8: noqa

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GoRide.settings")
django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
import support.routing


application = ProtocolTypeRouter(
    {
        "http": ASGIStaticFilesHandler(get_asgi_application()),
        "websocket": AuthMiddlewareStack(
            URLRouter(support.routing.websocket_urlpatterns)
        ),
    }
)
