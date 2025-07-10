"""Orders URL configuration."""

from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("create/", views.create_order, name="create"),
    path("create-web/", views.create_order_web, name="create_web"),
    path("", views.order_list, name="list"),
]
