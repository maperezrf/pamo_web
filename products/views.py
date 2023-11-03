from django.shortcuts import render, redirect
from products.models import Products
from pamo.queries import *
from pamo.constants import COLUMNS_SHOPI
from pamo.conecctions_shopify import ConnectionsShopify
import time
from products.forms import fileForm, comparationForm
import pandas as pd
from pamo.core_df import CoreDf

cdf = CoreDf()

def update(request):
    shopi = ConnectionsShopify()
    list_products = []
    response =shopi.request_graphql(GET_PRODUCTS.format(cursor=''))
    list_products.append(response.json()['data']['products']['edges'])
    cursor_new = response.json()['data']['products']['pageInfo']['endCursor']
    while response.json()['data']['products']['pageInfo']['hasNextPage']:
        time.sleep(20)
        response =shopi.request_graphql(GET_PRODUCTS.format(cursor= f",after:\"{response.json()['data']['products']['pageInfo']['endCursor']}\""))
        cursor_new = response.json()['data']['products']['pageInfo']['endCursor']
        list_products.append(response.json()['data']['products']['edges'])
        data_list = []
    for i in list_products:
        for k in i:
            dic = {}    
            dic['id'] = k['node']['id'].replace('gid://shopify/Product/',"")
            dic['tags'] = k['node']['tags']
            dic['title'] = k['node']['title']
            dic['vendor'] = k['node']['vendor']
            dic['price'] = int(float(k['node']['variants']['edges'][0]['node']['price'])) if k['node']['variants']['edges'][0]['node']['price'] !=None else 0 
            dic['compareAtPrice'] = int(float(k['node']['variants']['edges'][0]['node']['compareAtPrice'])) if k['node']['variants']['edges'][0]['node']['compareAtPrice'] !=None else 0 
            dic['sku'] = k['node']['variants']['edges'][0]['node']['sku']
            dic['barcode'] = k['node']['variants']['edges'][0]['node']['barcode']
            dic['inventoryQuantity'] = int(float(k['node']['variants']['edges'][0]['node']['inventoryQuantity'])) if k['node']['variants']['edges'][0]['node']['inventoryQuantity'] != None else 0
            data_list.append(dic)
    dic['cursor'] = cursor_new
    data_to_save = [Products(**elemento) for elemento in data_list]
    Products.objects.bulk_create(data_to_save)
    return  redirect(list)

def set_update(request):
    if request.method == 'POST':
        form_1 = fileForm(request.POST, request.FILES)
        if form_1.is_valid():
            file = request.FILES['file']
            cdf.set_df(file)
            columns = cdf.get_df_columns
            context = {'columns_file':columns, 'columns_shopi': COLUMNS_SHOPI}
        else: 
            print(form_1.errors)
    else:
        form = fileForm()
        print("via")  
        context = {'form':form}
    return render(request, 'upload_file.html',context)

def review_updates(request):
    if request.method == 'POST':
        form_2 = request.POST
    return render(request, 'upload_file.html',context={})