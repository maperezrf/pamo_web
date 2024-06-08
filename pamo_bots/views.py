from django.shortcuts import render
from pamo.conecctions_shopify import ConnectionsShopify
from pamo.connections_sodimac import ConnectionsSodimac
from datetime import datetime
import os 

def sodimac_view(request):
    return render(request, 'sodimac_view.html', context={})

def create_orders(request):
    # try:
        print(f'*** debug inicia bot sodimac {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ***')
        print('Buscando ordenes...')
        sodi = ConnectionsSodimac()
        if sodi.get_orders_api():
            print('Haciendo cruces de SKUS')
            sodi.make_merge()
            orders = sodi.get_orders()
            shopi = ConnectionsShopify()
            shopi.set_orders_df(orders)
            shopi.get_variant_id()
            orders = shopi.get_orders()
            print(orders)
            print('creando ordenes')
            orders_created = shopi.create_orders()
            print('Se ejecuto shopy satisfactoriamente')
            print(f'ordenes generadas: {orders_created}')
            print(f'se generaron {orders_created} ordenes satisfactoria mente')
            print(f'*** debug termina bot sodimac {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
        else:
            print(f'*** debug Se ejecuto shopy satisfactoriamente {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
            print(f'*** debug No se encontraron ordenes. {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
        return render(request, 'sodimac_view.html', context={})

def set_inventario(request):
    print('Comparando inventario....')
    sodi = ConnectionsSodimac()
    stock_sodimac = sodi.get_inventory()
    shopi = ConnectionsShopify()
    df = shopi.get_inventory(stock_sodimac)
    request = sodi.set_inventory(df)
    print(request)
    


     
