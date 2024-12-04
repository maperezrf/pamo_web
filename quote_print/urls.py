from . import views
from django.urls import path

app_name = 'quote_print'


urlpatterns = [
    path("", views.list, name="list"),
    path("<int:id>/print/", views.print_drafr, name="print"),
    path("<int:id_sho>/update/", views.update_draft, name="update"),
    path("send_sigo/", views.send_data_to_sigo, name="send_data_to_sigo"),
    
]