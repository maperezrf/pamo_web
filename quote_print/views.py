from django.shortcuts import render, redirect
from django.conf import settings
from pamo.conecctions_shopify import ConnectionsShopify
from pamo.constants import *
from pamo.queries import *
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required
from quote_print.models import Quote
from pamo.functions import make_json
import random
import re


def list(request):
    try:
        code = request.GET.get('code')
        print(code)
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
                nombre =  i['node']['customer']['firstName'].title() if (i['node']['customer']) and (i['node']['customer']['firstName']) else "" 
                apellido = i['node']['customer']['lastName'].title() if (i['node']['customer']) and (i['node']['customer']['lastName']) else ""     
                dic['customer'] = f"{nombre} {apellido}" 
                data_list.append(dic)
        dic['cursor'] = cursor_new
        data_to_save = [Quote(**elemento) for elemento in data_list]
        Quote.objects.bulk_create(data_to_save)
    data_table = Quote.objects.all().order_by('-id')[:500]
    data = {"table" :data_table, 'url_base':settings.BASE_URL}
    print(f'*** finaliza lista cotizaciones {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return render(request, 'table_draft_orders.html', data)

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
    data = {'info':draft, 'plazo':plazo, 'update': date_update.strftime('%d/%m/%Y'), 'nit':num}
    print(f'*** finaliza impresion de cotizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return render(request, 'print.html', data)

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
    quote.save()
    print(f'*** inicia actualizacion de cotizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return redirect(list)