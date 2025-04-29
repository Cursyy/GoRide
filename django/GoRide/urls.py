from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog


urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path("silk/", include("silk.urls", namespace="silk")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path("", include("main.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", include("accounts.urls")),
    path("support/", include("support.urls")),
    path("find_transport/", include("find_transport.urls")),
    path("subscriptions/", include("subscriptions.urls")),
    path("events/", include("events_near_me.urls")),
    path("get_direction/", include("get_direction.urls")),
    path("booking/", include("booking.urls")),
    path("payments/", include("payments.urls")),
    path("vouchers/", include("vouchers.urls")),
    path("careers/", include("careers.urls")),
    path("reviews/", include("reviews.urls")),
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
