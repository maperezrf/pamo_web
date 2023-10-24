from . import views
from django.urls import path

urlpatterns = [
    path("", views.list, name="index"),
    path("<int:id>/print/", views.print_drafr, name="print"),
]