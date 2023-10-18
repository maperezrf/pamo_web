from . import views
from django.urls import path

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:id>/print/", views.print_drafr, name="print"),
    path("<int:id>/download/", views.download_quote, name="download"),
]