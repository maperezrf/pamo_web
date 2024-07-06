from . import views
from django.urls import path

app_name = 'pamo_bots'

urlpatterns = [
    path("", views.sodimac_view, name="bots"),
    path("sodimac", views.create_orders, name="sodimac"),
    path("set_stock", views.set_inventory , name="set_stock"),
    path("get_orders", views.get_orders, name="get_orders"),
    path("manager_database", views.manager_database, name="manager_database"),
    path("get_inventory", views.get_inventory_view, name= "get_inventory_view"),
    path("set_inventory", views.set_inventory_view, name= "get_inventory_view")
]

