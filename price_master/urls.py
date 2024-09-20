from . import views
from django.urls import path

urlpatterns = [
    path("", views.list_products, name="products"),
]