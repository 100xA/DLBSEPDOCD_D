"""Logistics URL configuration."""

from django.urls import path

from . import views

app_name = "logistics"

urlpatterns = [
    path("track/<str:tracking_number>/", views.track_shipment, name="track_shipment"),
    path("status/<int:order_id>/", views.shipping_status, name="shipping_status"),
    path("history/", views.shipping_history, name="shipping_history"),
] 