"""
ASGI config for GoRide project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""


import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
import support.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GoRide.settings")
django.setup()

application = ProtocolTypeRouter(
    {
        "http": ASGIStaticFilesHandler(get_asgi_application()),
        "websocket": AuthMiddlewareStack(
            URLRouter(support.routing.websocket_urlpatterns)
        ),
    }
)
