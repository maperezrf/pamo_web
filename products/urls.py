from . import views
from django.urls import path

urlpatterns = [
    path("", views.set_update, name="list"),
    path("update", views.update, name="update"),
    path("review_updates", views.review_updates, name="review_updates")
]