from . import views
from django.urls import path

urlpatterns = [
    path("", views.list, name="list"),
    path("<int:id>/print/", views.print_drafr, name="print"),
    path("<int:id_sho>/update/", views.update_draft, name="update"),

]