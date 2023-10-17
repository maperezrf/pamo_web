from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from pamo.conecctions_shopify import ConnectionsShopify
from pamo.constants import *
from pamo.queries import *
from datetime import timedelta, datetime
import re

def index(request):
    ConnectionsShopify()
    shopify = ConnectionsShopify()
    response = shopify.request_graphql(GET_DRAFT_ORDERS.format(cursor=''))
    res  = response.json()['data']['draftOrders']['edges']
    daft_orders = make_json(res)
    has_next = response.json()['data']['draftOrders']['pageInfo']['hasNextPage']
    while has_next:
        response = shopify.request_graphql(GET_DRAFT_ORDERS.format( cursor= f",after:\"{response.json()['data']['draftOrders']['pageInfo']['endCursor']}\""))
        res  = response.json()['data']['draftOrders']['edges']
        daft_orders.extend(make_json(res))
        has_next = response.json()['data']['draftOrders']['pageInfo']['hasNextPage']
    data = {"table" :daft_orders, 'url_base':settings.BASE_URL}
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

def make_json(res):
    for i in range(len(res)):
        res[i]['node']['createdAt'] = datetime.strptime((res[i]['node']['createdAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res[i]['node']['updatedAt'] = datetime.strptime((res[i]['node']['updatedAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res[i]['node']['name'] = int(res[i]['node']['name'][2:])
    return(res)