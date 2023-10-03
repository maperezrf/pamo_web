from django.shortcuts import render
from django.http import HttpResponse
from pamo.conecctions_shopify import ConnectionsShopify
from pamo.constants import *
from pamo.queries import *
from datetime import timedelta, datetime
import re



def index(request):
    ConnectionsShopify()
    shopify = ConnectionsShopify()
    response = shopify.request_graphql(GET_DRAFT_ORDERS)
    # if response.json()['data']['draftOrders']['hasNextPage']:
    #     pass
    res  = response.json()
    for i in range(len(res['data']['draftOrders']['edges'])):
        res['data']['draftOrders']['edges'][i]['node']['createdAt'] = datetime.strptime((res['data']['draftOrders']['edges'][i]['node']['createdAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res['data']['draftOrders']['edges'][i]['node']['updatedAt'] = datetime.strptime((res['data']['draftOrders']['edges'][i]['node']['updatedAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
    data = {"table" : res['data']['draftOrders']['edges']}
    return render(request, 'table_draft_orders.html', data)

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
    data = {'info':draft, 'plazo':plazo, 'update': date_update.strftime('%d/%m/%Y'), 'nit':num}
    return render(request, 'print.html', data)