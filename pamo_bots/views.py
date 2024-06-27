from django.shortcuts import render, redirect

from pamo.conecctions_shopify import ConnectionsShopify
from pamo.connections_sodimac import ConnectionsSodimac
from datetime import datetime
from pamo.functions import create_file_products
from products.forms import fileForm
from pamo_bots.models import LogBotOrders, ProductsSodimac


def sodimac_view(request):
    return render(request, 'sodimac_view.html', context={})

def get_orders(request):
    logs = LogBotOrders.objects.all().order_by('-date')[:20]
    return render(request, 'get_orders.html', context={'logs':logs})

def manager_database(request):
    products = ProductsSodimac.objects.all()
    data = {'form':fileForm, 'table':products}
    return render(request, 'manager_database.html', context= data)

def create_orders(request):
    # try:
        print(f'*** debug inicia bot sodimac {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ***')
        print('Buscando ordenes...')
        sodi = ConnectionsSodimac()
        data_log = {}
        data_log['error'] = False
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
            success_len = len(orders_created['success']) 
            error_len = len(orders_created['error']) 
            print('Se ejecuto shopy satisfactoriamente')
            descripcion_error=''
            descripcion_success=''
            if success_len > 0:
                descripcion_success = f'ordenes generadas: {", ".join([f"{i}" for i in  orders_created["success"]])}'
                print(f'ordenes generadas: {", ".join([f"{i}" for i in  orders_created["success"]])}')
                print(f'se generaron {success_len} ordenes satisfactoria mente')
            if error_len > 0:
                 data_log['error'] = True
                 descripcion_error = f'se encotraron errores en las ordenes: {", ".join([f"{i}" for i in  orders_created["error"]])}'
                 print(f'se encotraron errores en las ordenes: {", ".join([f"{i}" for i in  orders_created["error"]])}')
            print(f'*** debug termina bot sodimac {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
            data_log['get_orders'] = True
            data_log['log'] = descripcion_error + ' ' + descripcion_success
        else:
            data_log['get_orders'] = False
            data_log['log'] = 'No se encontraron ordenes.'
            print(f'*** debug Se ejecuto shopy satisfactoriamente {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
            print(f'*** debug No se encontraron ordenes. {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
        log_item = LogBotOrders()
        log_item.get_orders = data_log['get_orders']
        log_item.error = data_log['error']
        log_item.log = data_log['log']
        log_item.save()
        return redirect('pamo_bots:get_orders')

# 1. Generar vista para traer toda la información de sodimac vinculado con shopify.
# 2. Generar vista para traer el stock de sodimac, y actualizar base de datos
# 3. Generar vista para setear datos de stock utilizar api
# 4. Generar vista para cargar archivo excel, actualizar el inventario y base de datos

def set_inventario(request):
    print('Comparando inventario....')
    products = create_file_products()
    
    # sodi = ConnectionsSodimac()
    # stock_sodimac = sodi.get_inventory()
    # shopi = ConnectionsShopify()
    # df = shopi.get_inventory(stock_sodimac)
    # request = sodi.set_inventory(df)
    return render(request, 'sincronizacion_sodimac.html', context={'form':fileForm})
    


     
