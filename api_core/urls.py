from . import views
from django.urls import path

app_name = 'api_core'

urlpatterns = [
    path("data_orders/",views.Orders.as_view(),name='data_orders'),
    path("order_info/",views.OrderInfo.as_view(),name='order_info'),
]

