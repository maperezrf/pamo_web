from django.shortcuts import render
from django.conf import settings
from pamo.conecctions_shopify import ConnectionsShopify
from pamo.constants import *
from pamo.queries import *
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required
from quote_print.models import Quote
import re

@login_required
def list(request):
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
                nombre =  i['node']['customer']['firstName'].title() if (i['node']['customer']) and (i['node']['customer']['firstName']) else "" 
                apellido = i['node']['customer']['lastName'].title() if (i['node']['customer']) and (i['node']['customer']['lastName']) else ""     
                dic['customer'] = f"{nombre} {apellido}" 
                data_list.append(dic)
        dic['cursor'] = cursor_new
        data_to_save = [Quote(**elemento) for elemento in data_list]
        Quote.objects.bulk_create(data_to_save)
    data_table = Quote.objects.all()
    data = {"table" :data_table, 'url_base':settings.BASE_URL}
    return render(request, 'table_draft_orders.html', data)

@login_required
def print_drafr(request,id):
    ConnectionsShopify()
    shopify = ConnectionsShopify()
    query = GET_DRAFT_ORDER.format(id)
    response = shopify.request_graphql(query)
    date_update = datetime.strptime(response.json()['data']['draftOrders']['edges'][0]['node']['updatedAt'][0:10], '%Y-%m-%d')
    plazo = (date_update + timedelta(days=10)).strftime('%d/%m/%Y')
    draft = response.json()['data']['draftOrders']['edges'][0]['node']
    try:
        res = re.search(r'\[(\d+)\]' ,draft['customer']['metafields']['edges'][0]['node']['value'])
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
    data = {'info':draft, 'plazo':plazo, 'update': date_update.strftime('%d/%m/%Y'), 'nit':num}
    return render(request, 'print.html', data)

def make_json(res):
    for i in range(len(res)):
        res[i]['node']['createdAt'] = datetime.strptime((res[i]['node']['createdAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res[i]['node']['updatedAt'] = datetime.strptime((res[i]['node']['updatedAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res[i]['node']['name'] = int(res[i]['node']['name'][2:])
    return(res)