from django.shortcuts import render, redirect
from django.conf import settings
from pamo.conecctions_shopify import ConnectionsShopify
from django.http import JsonResponse
from pamo.constants import *
from pamo.queries import *
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required
from quote_print.models import Quote
from pamo.functions import make_json
from pamo.connecctions_sigo import SigoConnection
from quote_print.models import SigoCostumers
import pandas as pd
import re
import json
from django.contrib.auth.decorators import login_required


@login_required
def list(request):
    try:
        code = request.GET.get('code')
    except:
        pass
    print(f'*** inicia lista cotizaciones {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    last_element = Quote.objects.latest('id')
    end_cursor = last_element.cursor
    ConnectionsShopify()
    shopify = ConnectionsShopify()
    response = shopify.request_graphql(GET_DRAFT_ORDERS.format( cursor= f",after:\"{end_cursor}\""))
    if response.json()['data']['draftOrders']['pageInfo']['endCursor'] != None:
        res  = response.json()['data']['draftOrders']['edges']
        cursor_new = response.json()['data']['draftOrders']['pageInfo']['endCursor']
        daft_orders = make_json(res)
        data_list =[]
        for i in daft_orders:
            if str(i['node']['name']) != last_element.name:
                dic = {}
                dic['id'] = i['node']['id'].replace('gid://shopify/DraftOrder/',"")
                dic['name'] = i['node']['name']
                dic['created_at'] = i['node']['createdAt']
                dic['total'] = int(float(i['node']['totalPrice']))
                try:
                    dic['nit'] = i['node']['customer']['addresses'][0]['company'].split('-')[0][:24]
                except:
                    dic['nit'] = None
                dic['seller'] = i['node']['tags']if i['node']['tags'] else None
                dic['seller'] = dic['seller'][0] if dic['seller'] else None
                nombre =  i['node']['customer']['firstName'].title() if (i['node']['customer']) and (i['node']['customer']['firstName']) else "" 
                apellido = i['node']['customer']['lastName'].title() if (i['node']['customer']) and (i['node']['customer']['lastName']) else ""     
                dic['customer'] = f"{nombre} {apellido}" 
                data_list.append(dic)
        dic['cursor'] = cursor_new
        data_to_save = [Quote(**elemento) for elemento in data_list]
        Quote.objects.bulk_create(data_to_save)
    quote_data = pd.DataFrame(Quote.objects.all().order_by('-id')[:500].values())
    # quote_data = pd.DataFrame([{'id':i.id, 'name':i.name, 'customer':i.customer, 'total':i.total, 'created_at':i.created_at} for i in data_table])
    sigo_costumers = pd.DataFrame(SigoCostumers.objects.all().values())
    merge_sigo = quote_data.merge(sigo_costumers, how = 'left', left_on='nit', right_on='identification', suffixes=('','_siigo'))
    merge_sigo.fillna('0', inplace=True)
    quote_data = merge_sigo.to_dict(orient='records')
    data = {"table" :quote_data, 'url_base':settings.BASE_URL}
    print(f'*** finaliza lista cotizaciones {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return render(request, 'table_draft_orders.html', data)

@login_required
def print_drafr(request,id):
    print(f'*** inicia impresion de cotizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    ConnectionsShopify()
    shopify = ConnectionsShopify()
    query = GET_DRAFT_ORDER.format(id)
    response = shopify.request_graphql(query)
    date_update = datetime.strptime(response.json()['data']['draftOrders']['edges'][0]['node']['updatedAt'][0:10], '%Y-%m-%d')
    plazo = (date_update + timedelta(days=10)).strftime('%d/%m/%Y')
    draft = response.json()['data']['draftOrders']['edges'][0]['node']
    try:
        draft['customer']['metafields']['edges'][0]['node']['value'] = ''
        draft['customer']['metafields']['edges'][1]['node']['value'] = ''
    except:
        pass
    try:
        res = re.search(r'\[(\d+)\]' ,[i['node']['value'] for i in draft['customer']['metafields']['edges'] if i['node']['key'] == 'numero_documento_identificaci_n'][0])
        num = res.group(1)
    except:
        num = None
    for i in draft['lineItems']['edges']:
        try:
            i['sku'] = i['node']['product']['variants']['edges'][0]['node']['sku']
            i['scr'] = i['node']['product']['images']['edges'][0]['node']['originalSrc']
        except:
            pass
        if str(i['node']['title']).__contains__('"'): 
            i['node']['title'] = i['node']['title'].replace('"','~')
        if str(i['node']['title']).__contains__("'"): 
            i['node']['title'] = i['node']['title'].replace("'",'~')    
    data = {'info':draft, 'plazo':plazo, 'update': date_update.strftime('%d/%m/%Y'), 'nit':num, 'url':f"https://api.whatsapp.com/send?phone={SALES_PHONE}&text=Hola,%20deseo%20revisar%20mi%20cotización%20{draft['name'][1]}"}
    print(f'*** finaliza impresion de cotizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    data = {'info': {'id': 'gid://shopify/DraftOrder/1203036029205', 'name': '#D5100', 'totalPrice': '6876659.40', 'createdAt': '2025-06-19T16:26:53Z', 'updatedAt': '2025-06-19T16:37:08Z', 'appliedDiscount': {'amount': '1509510.60', 'title': ''}, 'customer': {'displayName': 'VIVVI SAS', 'email': 'facturacion.vivvidero@gmail.com', 'defaultAddress': {'company': 'VIVVI SAS', 'phone': '+57 311 7763671'}, 'metafields': {'edges': [{'node': {'key': 'tipo_de_documento', 'value': ''}}, {'node': {'key': 'numero_documento_identificaci_n', 'value': ''}}, {'node': {'key': 'tipo', 'value': '[\'Empresa\']'}}]}}, 'invoiceUrl': 'https://www.pamo.co/61785079974/invoices/85f36f2b89eed0b25237b1acd13bdef5', 'lineItems': {'edges': [{'node': {'title': 'Grifería Para Lavaplatos Cuello Cisne Negra', 'originalUnitPrice': '103760.00', 'quantity': 10, 'product': {'images': {'edges': [{'node': {'originalSrc': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/1_7cfbf6ca-12c4-45ba-9edb-d408f16bb370.jpg?v=1743629364'}}]}, 'variants': {'edges': [{'node': {'sku': 'BC001'}}]}}}, 'sku': 'BC001', 'scr': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/1_7cfbf6ca-12c4-45ba-9edb-d408f16bb370.jpg?v=1743629364'}, {'node': {'title': 'Grifería Poste Alto Negra para Lavamanos - Agua Fría, 1/2~ Universal', 'originalUnitPrice': '55802.00', 'quantity': 15, 'product': {'images': {'edges': [{'node': {'originalSrc': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/1_7f7c903d-979e-4843-85f3-bbea13e43170.jpg?v=1749093796'}}]}, 'variants': {'edges': [{'node': {'sku': 'PAC5925BL'}}]}}}, 'sku': 'PAC5925BL', 'scr': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/1_7f7c903d-979e-4843-85f3-bbea13e43170.jpg?v=1749093796'}, {'node': {'title': 'griferia sencilla alta cromo ', 'originalUnitPrice': '63325.00', 'quantity': 15, 'product': None}}, {'node': {'title': 'Grifería Lavamanos Poste Bajo Rio Agua Fria', 'originalUnitPrice': '46527.00', 'quantity': 10, 'product': {'images': {'edges': [{'node': {'originalSrc': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/IMG-0169.jpg?v=1717873143'}}]}, 'variants': {'edges': [{'node': {'sku': '5693;PAC5924BLACK'}}]}}}, 'sku': '5693;PAC5924BLACK', 'scr': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/IMG-0169.jpg?v=1717873143'}, {'node': {'title': 'griferia sencilla baja cromo ', 'originalUnitPrice': '58160.00', 'quantity': 10, 'product': None}}, {'node': {'title': 'Regadera Redonda 25 cm Negra + Tubo', 'originalUnitPrice': '83383.00', 'quantity': 10, 'product': {'images': {'edges': [{'node': {'originalSrc': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/4_dbec6130-f572-4662-9dff-7eb66c1ce29f.png?v=1703619793'}}]}, 'variants': {'edges': [{'node': {'sku': '16165170'}}]}}}, 'sku': '16165170', 'scr': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/4_dbec6130-f572-4662-9dff-7eb66c1ce29f.png?v=1703619793'}, {'node': {'title': 'Regadera Acero Ultraplana 25 cms Redonda Alta Calidad Sin Tubo', 'originalUnitPrice': '59299.00', 'quantity': 7, 'product': {'images': {'edges': [{'node': {'originalSrc': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/PAMO_SR010.jpg?v=1743124757'}}]}, 'variants': {'edges': [{'node': {'sku': 'PAMO_SR010'}}]}}}, 'sku': 'PAMO_SR010', 'scr': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/PAMO_SR010.jpg?v=1743124757'}, {'node': {'title': 'Tubo Regadera 40 cm Tipo L Acero inoxidable', 'originalUnitPrice': '20006.00', 'quantity': 7, 'product': {'images': {'edges': [{'node': {'originalSrc': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/1_d7dd323d-7c70-4258-b8ed-c9e99eed066c.jpg?v=1709388453'}}]}, 'variants': {'edges': [{'node': {'sku': 'DF-1001'}}]}}}, 'sku': 'DF-1001', 'scr': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/1_d7dd323d-7c70-4258-b8ed-c9e99eed066c.jpg?v=1709388453'}, {'node': {'title': 'monocontrol lavamanos alto redondo cromo', 'originalUnitPrice': '94600.00', 'quantity': 7, 'product': None}}, {'node': {'title': 'Grifería Lavamanos Monocontrol Cromada Poste Alto Original Pamo', 'originalUnitPrice': '112626.00', 'quantity': 5, 'product': {'images': {'edges': [{'node': {'originalSrc': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/1_82bd520f-d0c4-4f70-b6de-32bdb11b15d9.jpg?v=1740433997'}}]}, 'variants': {'edges': [{'node': {'sku': 'PAMO_F10008H'}}]}}}, 'sku': 'PAMO_F10008H', 'scr': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/1_82bd520f-d0c4-4f70-b6de-32bdb11b15d9.jpg?v=1740433997'}, {'node': {'title': 'poste monocontrol alto cuadrado', 'originalUnitPrice': '98600.00', 'quantity': 5, 'product': None}}, {'node': {'title': 'acople str 40 cm ', 'originalUnitPrice': '6200.00', 'quantity': 20, 'product': None}}, {'node': {'title': 'sifon lavaplatos en p blanco ', 'originalUnitPrice': '14400.00', 'quantity': 15, 'product': None}}, {'node': {'title': 'Sifon Flexible Para Lavaplatos O Lavamanos Blanco.', 'originalUnitPrice': '21860.00', 'quantity': 20, 'product': {'images': {'edges': [{'node': {'originalSrc': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/products/D_955363-MCO31061938384_062019-F.jpg?v=1694193036'}}]}, 'variants': {'edges': [{'node': {'sku': 'F6101-1'}}]}}}, 'sku': 'F6101-1', 'scr': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/products/D_955363-MCO31061938384_062019-F.jpg?v=1694193036'}, {'node': {'title': 'Desague Push Lavamanos Negro Metálico Lujo Universal Diseño Moderno', 'originalUnitPrice': '31515.00', 'quantity': 20, 'product': {'images': {'edges': [{'node': {'originalSrc': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/1_8eaf1c88-99d6-42a3-b452-32ba15f853cc.jpg?v=1748267562'}}]}, 'variants': {'edges': [{'node': {'sku': '16164783'}}]}}}, 'sku': '16164783', 'scr': 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/1_8eaf1c88-99d6-42a3-b452-32ba15f853cc.jpg?v=1748267562'}]}}, 'plazo': '29/06/2025', 'update': '19/06/2025', 'nit': None, 'url': 'https://api.whatsapp.com/send?phone=576019142738&text=Hola,%20deseo%20revisar%20mi%20cotización%20D'}
    return render(request, 'print.html', data)

@login_required
def update_draft (request,id_sho):
    print(f'*** inicia actualizacion de cotizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    print('esta entrando')
    ConnectionsShopify()
    shopify = ConnectionsShopify()
    query = GET_DRAFT_ORDER_UPDATE.format(id_sho)
    print(query)
    response = shopify.request_graphql(query)
    print(response.json())
    res = response.json()['data']['draftOrders']['edges'][0]
    total = int(float(res['node']['totalPrice']))
    nombre =  res['node']['customer']['firstName'].title() if (res['node']['customer']) and (res['node']['customer']['firstName']) else "" 
    apellido = res['node']['customer']['lastName'].title() if (res['node']['customer']) and (res['node']['customer']['lastName']) else ""     
    customer = f"{nombre} {apellido}" 
    quote = Quote.objects.get(id=id_sho)
    quote.customer = customer
    quote.total = total
    quote.nit = res['node']['customer']['addresses'][0]['company'].split('-')[0][:24] if (res['node']['customer']) and ('addresses' in res['node']['customer']) and (res['node']['customer']['addresses'][0]['company']) else None
    seller = res['node']['tags']if res['node']['tags'] else None
    quote.seller = seller[0] if seller else None

    quote.save()
    print(f'*** inicia actualizacion de cotizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return JsonResponse({'success':True, 'message': ''})

@login_required
def set_all_constumers(request):
    try:
        sigo_con = SigoConnection()
        sigo_con.synchronize_all_costumers()
        return JsonResponse({'success':True, 'message': ''})
    except Exception as e:
        print(e)
        return JsonResponse({'success':False, 'message': f'No se completó la carga {str(e)}'})

@login_required
def search_new_customers(request):
    try:
        sigo_con = SigoConnection()
        customer_created = sigo_con.synchronize_new_costumer()
        return JsonResponse({'success':True, 'message': f'clientes encontrados: {customer_created}'})
    except Exception as e:
        print(e)
        return JsonResponse({'success':False, 'message': f'No se completó la carga {str(e)}'})

@login_required
def get_info_customer(request, id_siigo):
    try:
        sigo_con = SigoConnection()
        data = sigo_con.get_info_costumer(id_siigo)
        return JsonResponse({'success':True, 'data': json.dumps(data)})
    except Exception as e:
        print(e)
        return JsonResponse({'success':False, 'message': f'No se completó la carga {str(e)}'})
    


