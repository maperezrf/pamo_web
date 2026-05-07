from . import views
from django.urls import path

app_name = 'pamo_bots'

urlpatterns = [
    path("", views.sodimac_view, name="bots"),
    path("sodimac", views.create_orders, name="sodimac"),
    path("upload", views.set_inventory , name="upload"),
    path("get_orders", views.get_orders, name="get_orders"),
    path("manager_database", views.manager_database, name="manager_database"),
    path("report_invoices_view", views.report_invoices_view, name="report_invoices_view"),
    # path("get_inventory", views.get_inventory_view, name= "get_inventory_view"),
    # path("set_inventory", views.set_inventory_view, name= "get_inventory_view"),
    path("update_base", views.update_base, name= "update_base"),
    path("invoices/monthly/", views.get_monthly_invoices, name="monthly_invoices"),
    path("download/products/", views.download_products_excel, name="download_products"),
    path("download/kits/", views.download_kits_excel, name="download_kits"),
    path("products_sodimac/", views.create_product_sodimac, name="create_product_sodimac"),
    path("products_sodimac/<int:id>/", views.edit_product_sodimac, name="edit_product_sodimac"),
    path("sodimac_kits/", views.create_sodimac_kit, name="create_sodimac_kit"),
    path("sodimac_kits/<int:id>/", views.edit_sodimac_kit, name="edit_sodimac_kit"),
    path("upload/products/", views.upload_products_excel, name="upload_products_excel"),
    path("upload/kits/", views.upload_kits_excel, name="upload_kits_excel"),
    path("download/report/", views.download_report_invoices, name="download_report_invoices"),
    path("reinyectar_oc/", views.reinyectar_oc_view, name="reinyectar_oc"),
]