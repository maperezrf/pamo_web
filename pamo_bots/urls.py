from . import views
from django.urls import path

app_name = 'pamo_bots'

urlpatterns = [
    path("", views.sodimac_view, name="bots"),
    path("sodimac", views.create_orders, name="sodimac"),
    path("set_stock", views.set_inventario, name="set_stock")
]

