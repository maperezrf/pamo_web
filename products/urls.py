from . import views
from django.urls import path

app_name = 'products'

urlpatterns = [
    path("", views.list_products, name="list_products"),
    path("upload", views.set_update, name="upload"),
    path("update", views.update, name="update"),
    path("review_updates", views.review_updates, name="review_updates"),
    path("update_products", views.update_products, name="update_products"),
    path("export_products", views.export_products, name="export_products"),
    path("index", views.test_view, name="index"),
]