from . import views
from django.urls import path

app_name = 'quote_print'


urlpatterns = [
    path("", views.list, name="list"),
    path("<int:id>/print/", views.print_drafr, name="print"),
    path("<int:id_sho>/update/", views.update_draft, name="update"),
    path("set_all_constumers/", views.set_all_constumers, name="set_all_constumers"),  
    path("search_new_customers/", views.search_new_customers, name="search_new_customers"),  
    path("get_info_costumer/<id_siigo>", views.get_info_customer, name="get_info_costumer"),
    path("<int:id>/pdf/", views.generate_pdf, name="pdf"),
]