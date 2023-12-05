from django.shortcuts import render
from pamo.conecctions_shopify import ConnectionsShopify
from pamo.connections_sodimac import ConnectionsSodimac
from datetime import datetime
import os 

def sodimac_view(request):
    return render(request, 'sodimac_view.html', context={})

def create_orders(request):
    # try:
        print('inciando...')
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
            title = 'Se ejecuto shopy satisfactoriamente',
            message=f'ordenes generadas: {orders_created}'
            print(f'se generaron {orders_created} ordenes satisfactoria mente')
        else:
            title = 'Se ejecuto shopy satisfactoriamente',
            message='No se encontraron ordenes.'
    # except Exception as e:
    #     print(e)
    #     title = 'ocurrio un error'
    #     fecha_hora_actual = datetime.now()
    #     error_log = fecha_hora_actual.strftime("%Y-%m-%d_%H-%M-%S_error.txt")
    #     path_error_log = os.path.join('error_log', error_log)
    #     with open(path_error_log, 'w') as archivo:
    #         archivo.write(str(e))
    #         archivo.write('\n')
        return render(request, 'sodimac_view.html', context={})
