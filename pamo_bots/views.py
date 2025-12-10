from django.shortcuts import render, redirect
from django.http import JsonResponse
from pamo.conecctions_shopify import ConnectionsShopify
from pamo.connections_sodimac import ConnectionsSodimac
from pamo.connections_airtable import connAirtable
from pamo.connections_melonn import connMelonn
from django.conf import settings
import datetime
from pamo.functions import create_file_products
from products.forms import fileForm
from pamo_bots.models import LogBotOrders, ProductsSodimac
from quote_print.models import SodimacOrders
import pandas as pd
from pamo_bots.core_df import Core
import json
import os
from django.contrib.auth.decorators import login_required
from pamo.connecctions_sigo import SigoConnection

@login_required
def sodimac_view(request):
    return render(request, 'sodimac_view.html', context={})

def get_orders(request):
    logs = LogBotOrders.objects.all().order_by('-date')[:20]
    return render(request, 'get_orders.html', context={'logs':logs})

def manager_database(request):
    products = ProductsSodimac.objects.all()
    data = {'table':products}
    return render(request, 'manager_database.html', context= data)


def create_orders(request):
    # try:
        print(f'*** debug inicia bot sodimac {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ***')
        print('Buscando ordenes...')
        sodi = ConnectionsSodimac()
        data_log = {}
        data_log['error'] = False
        data_log['get_orders'] = False
        data_log['log'] = 'No se encontraron ordenes.'
        descripcion_error = ''
        if sodi.get_orders_api():
            print('Haciendo cruces de SKUS')
            sodi.make_merge()
            orders = sodi.get_orders()
            orders_generated = [ int(i.id) for i in  SodimacOrders.objects.filter(id__in =orders.ORDEN_COMPRA.unique())]
            orders  = orders.loc[~orders['ORDEN_COMPRA'].isin(orders_generated)]
            if not orders.empty:
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
                print(f'*** debug termina bot sodimac {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
                descripcion_success = f'ordenes generadas: {", ".join([f"{i}" for i in orders_created])}'
                data_log['get_orders'] = True
                data_log['log'] = descripcion_error + ' ' + descripcion_success 
        else:
            data_log['get_orders'] = False
            data_log['log'] = 'No se encontraron ordenes.'
            print(f'*** debug Se ejecuto shopy satisfactoriamente {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
            print(f'*** debug No se encontraron ordenes. {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
        log_item = LogBotOrders()
        log_item.get_orders = data_log['get_orders']
        log_item.error = data_log['error']
        log_item.log = data_log['log']
        log_item.save()

        orders = [i['id'] for i in SodimacOrders.objects.filter(status = '1-PENDIENTE').values()]
        sodi.reinyectar_oc(orders)
        sodi.get_orders_api()
        sodi.make_merge()
        sodi.set_kits()
        df = sodi.get_orders()
        invoices = df.loc[df['ESTADO_OC']=='4-ESTADO FINAL']
        invoices_values = pd.DataFrame(SodimacOrders.objects.filter(novelty__contains = 'The total payments must be equal to the total invoice. The total invoice calculated is ', factura__isnull=True).values())
        if not invoices_values.empty :
            invoices_values['novelty'] = invoices_values['novelty'].apply(lambda x :x.replace('The total payments must be equal to the total invoice. The total invoice calculated is ', ''))
            invoices_values['id'] = invoices_values['id'].astype(int)
            invoices = invoices.merge(invoices_values, how='left', left_on='ORDEN_COMPRA', right_on='id')
            invoices['novelty'].fillna('0', inplace=True)
        invoices.drop_duplicates(inplace=True)
        taxes = [{'id':16104}, {'id': 13456 }]
        conn_sigo = SigoConnection()
        responses = conn_sigo.create_invoice(invoices, taxes)
        for i in responses:
            item = SodimacOrders.objects.get(id = i)
            if responses[i].status_code == 201:
                item.status = '4-ESTADO FINAL'
                item.factura = responses[i].json()['name']
                item.date_invoice = datetime.date.today()
                item.novelty = ''
                item.value = responses[i].json()['total']
            else:
                item.novelty = responses[i].json()['Errors'][0]['Message']
                if item.novelty == "The document already exists. This occurs if you are making duplicate requests simultaneously.":
                    # item.status = '4-ESTADO FINAL'
                    print(f'La factura para la oc {i} ya esta creada')
                else:
                    print(f'ocurrio un error con la factura {i}')
            item.save()
        return redirect('pamo_bots:get_orders')

def set_inventory(request):
    # se recibe un archivo en excel, actualiza los registros que se encuentran en la base y los que no los crea 
    if request.method == 'GET':
        form = fileForm()
        data = {'form':form} 
        return render(request, 'sincronizacion_sodimac.html', context=data)
    elif request.method == 'POST':
        # crea o actualiza los registros en la base de datos
        form_1 = fileForm(request.POST, request.FILES)
        if form_1.is_valid():
            file = request.FILES['file']
            core = Core()
            core.set_df(file)
            core.process()
            products, df = core.get_products()
            sodi = ConnectionsSodimac()
            response_get = sodi.get_inventario([i.ean for i in products])
            save_review(response_get)
            df_resposne = pd.DataFrame(response_get)
            df_resposne = df_resposne.loc[df_resposne['success'] == True]
            df = df_resposne.merge(df, how='left', on ='ean')
            # sodi.set_inventory(df)
            return JsonResponse({'success' :True, 'message' :''})
        else: 
            print(form_1.errors)
            print(f'*** error en seteo de archivo actualizacion {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')

def get_inventory_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        ean_list = data.get('products')
        sodi = ConnectionsSodimac()
        return JsonResponse(sodi.get_inventario(ean_list)[0])

def set_inventory_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        sku = data.get('sku')
        product = data.get('product')
        stock = data.get('stock')
        columnas = ["sku", "ean", "stock"]
        data = [[sku, product, stock]]
        df = pd.DataFrame(data, columns=columnas)
        sodi = ConnectionsSodimac()
        data = sodi.set_inventory(df)
        core = Core()
        core.update_database_item(sku, product, stock)
        return  JsonResponse(data)

def update_base(request):
    products = ProductsSodimac.objects.all()
    list_ean = [i.ean for i in products]
    sodi = ConnectionsSodimac()
    response = sodi.get_inventario(list_ean)
    save_review(response)
    return JsonResponse({'success':True, 'message': ''})

def save_review(response):
    products = ProductsSodimac.objects.all()
    products = pd.DataFrame(products.values())
    df = pd.DataFrame(response)
    df = df.merge(products, how= 'left', on = ['ean'] )
    df = df[['sku_sodimac', 'sku_pamo', 'ean', 'message']]
    df.to_excel(os.path.join(settings.MEDIA_ROOT, 'final_review.xlsx'),index=False)


('14611583','14586213','14625267','14633883','14634992','14645515','14646496','14647872','14649860','14653154','14655726','14659933','14622008','14645272','14645330','14647319','14647871','14652854','14654624','14615395','14625968','14646909','14650417')
