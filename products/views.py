from django.shortcuts import render, redirect
from django.http import JsonResponse
from products.models import Products, SaveMargins
from django.db.models import Q
from pamo.queries import *
from pamo.constants import COLUMNS_SHOPI
from pamo.conecctions_shopify import ConnectionsShopify
import time
from products.forms import fileForm, comparationForm
import pandas as pd
from pamo.core_df import CoreDf
from pamo.conecctions_shopify import ConnectionsShopify
import numpy as np
from unidecode import unidecode
from django.contrib.auth.decorators import login_required
from pamo.functions import update_products_db

cdf = CoreDf()

@login_required
def list_products(request):
    products =  Products.objects.all()
    context = {'products':products}
    return render(request, 'list_products.html', context)

@login_required
def update(request):
    obj_to_save = Products.objects.filter(Q(margen__gt=0) | Q(costo__gt=0))
    data_list = []
    for i in obj_to_save:
        dic = {}
        dic['id'] = i.id
        dic['margen'] = float(i.margen)
        dic['costo'] = float(i.costo)
        data_list.append(dic)
    data_to_save = [SaveMargins(**elemento) for elemento in data_list]
    SaveMargins.objects.bulk_create(data_to_save)
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
    items_saved = SaveMargins.objects.all()
    ids_saved_list = [i.id  for i in  items_saved]
    margen_saved = {i.id: float(i.margen) for i in  items_saved}
    costo_saved = {i.id: float(i.costo) for i in  items_saved}
    for i in list_products:
        for k in i:
            dic = {}    
            dic['id'] = k['node']['id'].replace('gid://shopify/Product/',"")
            dic['tags'] = ', '.join(k['node']['tags']) if len(k['node']['tags']) > 0 else None
            dic['title'] = k['node']['title']
            dic['vendor'] = k['node']['vendor']
            dic['status'] = k['node']['status']
            dic['price'] =float(k['node']['variants']['edges'][0]['node']['price']) if k['node']['variants']['edges'][0]['node']['price'] !=None else 0.0 
            dic['compareAtPrice'] =float(k['node']['variants']['edges'][0]['node']['compareAtPrice']) if k['node']['variants']['edges'][0]['node']['compareAtPrice'] !=None else 0.0 
            dic['sku'] = k['node']['variants']['edges'][0]['node']['sku']
            dic['barcode'] = k['node']['variants']['edges'][0]['node']['barcode']
            dic['inventoryQuantity'] = int(float(k['node']['variants']['edges'][0]['node']['inventoryQuantity'])) if k['node']['variants']['edges'][0]['node']['inventoryQuantity'] != None else 0.0
            if int(dic['id']) in ids_saved_list:
                dic['margen'] = margen_saved[float(dic['id'])]
                dic['costo'] = costo_saved[float(dic['id'])]
            data_list.append(dic)
    dic['cursor'] = cursor_new
    items_saved.delete()
    Products.objects.all().delete()
    data_to_save = [Products(**elemento) for elemento in data_list]
    Products.objects.bulk_create(data_to_save)
    data ={'data':'data'}
    return JsonResponse(data)

@login_required
def set_update(request):
    grupos = request.user.groups.all()
    ids_grupos = [grupo.id for grupo in grupos]
    if 1 in ids_grupos:
        if request.method == 'POST':
            form_1 = fileForm(request.POST, request.FILES)
            if form_1.is_valid():
                file = request.FILES['file']
                cdf.set_df(file)
                columns = cdf.get_df_columns()
                context = {'columns_file':columns, 'columns_shopi': COLUMNS_SHOPI}
            else: 
                print(form_1.errors)
        else:
            form = fileForm()
            context = {'form':form}
        return render(request, 'upload_file.html',context)
    else:
         return render(request, 'acceso_denegado.html', context={})

@login_required
def review_updates(request):
    if request.method == 'POST':
        data = request.POST.dict()
        cdf.rename_columns(data)
        data_file = cdf.get_df()
        skus = data_file['SKU'].values
        products = Products.objects.filter(sku__in=skus) 
        # if ('Margen' in data_file.columns) | ('Costo' in data_file.columns) | ('Margen comparación' in data_file.columns):
        data = { 'sku' : products.values_list('sku', flat=True),
            'margen_db' : products.values_list('margen', flat=True),
            'costo_db' : products.values_list('costo', flat=True),
            'margen_comparacion_db' : products.values_list('margen_comparacion_db', flat=True),
            }
        df = pd.DataFrame(data)
        # else:
        #     df = pd.DataFrame()
        shopi = ConnectionsShopify()
        responses=[]
        for i in data_file['SKU'].values:
            query = GET_PRODUCT.format(skus=f'sku:{i}')
            response = shopi.request_graphql(query)
            try:
                responses.append(response.json()['data']['products']['edges'][0])
            except Exception as error:
                print(error)
        cdf.set_df_shopi(responses)
        cdf.merge(df)
        df_rev = cdf.get_df_mer()
        # if len([i for i in df_rev.columns if '_db' in i]) == 3:
        df_rev['margen_db'] = df_rev['margen_db'].fillna('No entontrado') 
        df_rev['costo_db'] = df_rev['costo_db'].fillna('No entontrado')
        df_rev['margen_comparacion_db'] = df_rev['margen_comparacion_db'].fillna('No entontrado')
        table = df_rev.to_dict(orient = 'records')
        data = {'table' : table }
    return render(request, 'list.html',context=data)

@login_required
def update_products(request):
    df_rev = cdf.get_df_mer()
    df =  update_products_db(df_rev)
    cdf.set_costo(df)
    shopi = ConnectionsShopify()
    variables = cdf.set_variables()
    cont = 0
    not_update = []
    for variable in variables:
        try:
            res = shopi.request_graphql(UPTADE_PRODUCT, variable)
            if len(res.json()['data']['productUpdate']['userErrors']) == 0 :
                cont +=1
            else:
                not_update.append(variable['input']['variants'][0]['sku'])
        except:
            not_update.append(variable['input']['variants'][0]['sku'])
        data = {'success': cont,'not_successful':not_update}
    return JsonResponse(data)