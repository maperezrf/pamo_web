from django.shortcuts import render
from .core_price_master import PriceMaster
# import rest_framework

def list_products(request):
    pm = PriceMaster()
    pm.get_all_products()
    return render(request, 'sodimac_view.html', context={})
