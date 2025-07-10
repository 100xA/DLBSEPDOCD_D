"""DevOps Pipeline URL Configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Web interface for E2E testing
    path("", include("devops_pipeline.apps.catalog.urls")),
    path("orders/", include("devops_pipeline.apps.orders.urls")),
    path("auth/", include(("django.contrib.auth.urls", "auth"), namespace="auth")),
    # API endpoints
    path("api/v1/auth/", include("rest_framework.urls")),
    path("api/v1/orders/", include("devops_pipeline.apps.orders.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
