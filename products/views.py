from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from products.models import Products, SaveMargins
from pamo_bots.models import ProductsSodimac
from django.db.models import Q
from pamo.queries import *
from pamo.constants import COLUMNS_SHOPI
from pamo.conecctions_shopify import ConnectionsShopify
import time
from products.forms import fileForm
import pandas as pd
from pamo.core_df import CoreDf
from django.contrib.auth.decorators import login_required
from pamo.functions import update_products_db, create_file_products
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font
from datetime import datetime
from pamo import settings
import os
pd.options.display.max_columns= 500

cdf = CoreDf()

@login_required
def list_products(request):
    print(f'*** inicia vista productos {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    products_mg = create_file_products()
    context = {'products':products_mg.to_dict( orient ='records')}
    print(f'*** finaliza vista productos {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return render(request, 'list_products.html', context)

@login_required
def update(request):
    print(f'*** inicia actualizacion base productos {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    try:
        obj_to_save = Products.objects.filter(Q(margen__gt=0) | Q(costo__gt=0) | Q(margen_comparacion_db__gt=0))
        data_list = []
        for i in obj_to_save:
            dic = {}
            dic['id'] = i.id
            dic['margen'] = float(i.margen)
            dic['costo'] = float(i.costo)
            dic['margen_comparacion_db'] = float(i.margen_comparacion_db)
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
            print(response.json()['extensions'])
            cursor_new = response.json()['data']['products']['pageInfo']['endCursor']
            list_products.append(response.json()['data']['products']['edges'])
            print(len(list_products))
        data_list = []
        items_saved = SaveMargins.objects.all()
        ids_saved_list = [i.id  for i in  items_saved]
        margen_saved = {i.id: float(i.margen) for i in  items_saved}
        costo_saved = {i.id: float(i.costo) for i in  items_saved}
        margen_comp_saved = {i.id: float(i.margen_comparacion_db) for i in  items_saved}
        try:
            for i in list_products:
                for k in i:
                    variants_cont = 1 
                    while len(k['node']['variants']['edges']) >= variants_cont:
                        dic = {}
                        dic['idShopi'] = k['node']['id'].replace('gid://shopify/Product/',"")
                        dic['tags'] = ', '.join(k['node']['tags']) if len(k['node']['tags']) > 0 else None
                        dic['title'] = k['node']['title']
                        dic['vendor'] = k['node']['vendor']
                        dic['status'] = k['node']['status']
                        dic['price'] =float(k['node']['variants']['edges'][variants_cont - 1]['node']['price']) if k['node']['variants']['edges'][variants_cont - 1]['node']['price'] !=None else 0.0 
                        dic['compareAtPrice'] =float(k['node']['variants']['edges'][variants_cont - 1]['node']['compareAtPrice']) if k['node']['variants']['edges'][variants_cont - 1]['node']['compareAtPrice'] !=None else 0.0 
                        dic['sku'] = k['node']['variants']['edges'][variants_cont - 1]['node']['sku']
                        dic['barcode'] = k['node']['variants']['edges'][variants_cont - 1]['node']['barcode']
                        dic['inventoryQuantity'] = int(float(k['node']['variants']['edges'][variants_cont - 1]['node']['inventoryQuantity'])) if float(k['node']['variants']['edges'][variants_cont - 1]['node']['inventoryQuantity']) != None else 0.0
                        variants_cont += 1
                        if int(dic['idShopi']) in ids_saved_list:
                            dic['margen'] = margen_saved[float(dic['idShopi'])]
                            dic['costo'] = costo_saved[float(dic['idShopi'])]
                            dic['margen_comparacion_db'] = margen_comp_saved[float(dic['idShopi'])]
                        data_list.append(dic)
        except Exception as e:
            print (e)
        dic['cursor'] = cursor_new
        items_saved.delete()
        Products.objects.all().delete()
        data_to_save = [Products(**elemento) for elemento in data_list]
        Products.objects.bulk_create(data_to_save)
        data = {'status': 'success'}
        print(f'*** inicia actualizacion base productos {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    except:
        if items_saved:
            items_saved.delete()
        print(f'*** la actualizacion de productos fallo {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return JsonResponse(data)

@login_required
def set_update(request):
    print(f'*** inicia seteo de archivo actualizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
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
                print(f'*** finaliza seteo de archivo actualizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
            else: 
                print(form_1.errors)
                print(f'*** error en seteo de archivo actualizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
        else:
            form = fileForm()
            context = {'form':form}
        return render(request, 'upload_file.html',context)
    else:
         return render(request, 'acceso_denegado.html', context={})

@login_required
def review_updates(request):
    print(f'*** inicia revision de actualizaciones {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    if request.method == 'POST':
        data = request.POST.dict()
        cdf.rename_columns(data)
        data_file = cdf.get_df()
        # inicio modificacion
        conn = ConnectionsShopify()
        responses = []
        skus_no_found = []
        for i in range(data_file.shape[0]):
            query = GET_PRODUCTS_FULL.format(sku= data_file.iloc[i]['SKU'])
            response = conn.request_graphql(query).json()
            response['data']['products']['sku'] = data_file.iloc[i]['SKU']
            products = response['data']['products']['edges']
            responses.append(response)
            if len([j[0]['node']['id'] for j in [i['node']['variants']['edges'] for i in response['data']['products']['edges']] if j[0]['node']['sku'] == data_file.iloc[i]['SKU']]) == 0:
                skus_no_found.append(data_file.iloc[i]['SKU'])
                data_file.loc[data_file['SKU'].isin(skus_no_found), 'NOVEDAD'] = 'SKU no encontrado'
        df_shopi, sku_duplicated = cdf.set_df_shopi(responses)
        data_file.loc[data_file['SKU'].isin(sku_duplicated), 'NOVEDAD'] = 'SKU duplicado en archivo'
        df_filter = df_shopi[['idShopi', 'sku_shopi']].rename(columns={'sku_shopi':'sku'}).to_dict('records')
        consulta = Q()
        for filtro in df_filter:
            consulta |= Q(**filtro)
        products = Products.objects.filter(consulta) 
        data = { 
            'idShopi' : products.values_list('idShopi', flat=True),
            'sku' : products.values_list('sku', flat=True),
            'margen_db' : products.values_list('margen', flat=True),
            'costo_db' : products.values_list('costo', flat=True),
            'price' : products.values_list('price', flat=True),
            'compareAtPrice' : products.values_list('compareAtPrice', flat=True),
            'margen_comparacion_db' : products.values_list('margen_comparacion_db', flat=True),
            }
        df_base = pd.DataFrame(data).reset_index(drop=True)
        cdf.merge(df_base)
        df_rev = cdf.get_df_mer()
        df_rev['margen_db'] = df_rev['margen_db'].fillna(0) 
        df_rev['costo_db'] = df_rev['costo_db'].fillna(0)
        df_rev['margen_comparacion_db'] = df_rev['margen_comparacion_db'].fillna(0)
        table = df_rev.to_dict(orient = 'records')
        df_rev.to_excel(os.path.join(settings.MEDIA_ROOT, 'temp_upload.xlsx'), index=False)
        data = {'table' : table }
        data_file['NOVEDAD'].fillna('Sin Novedad', inplace=True)
        data_file.to_excel( os.path.join(settings.MEDIA_ROOT, 'review_report.xlsx'), index=False)
        print(f'*** finaliza revision de actualizaciones {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return render(request, 'list.html',context=data)

@login_required
def update_products(request):
    print(f'*** inicia actualizacion de productos shopify{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    try:
        df_rev = cdf.get_df_mer()
        df = update_products_db(df_rev.reset_index(drop=True))
        cdf.set_costo(df)
        shopi = ConnectionsShopify() 
        variables = cdf.set_variables()
        cont = 0
        not_update = []
        check = []
        for variable in variables:
            print(variable)
            try:
                product_var = product_hql = variant_var = variant_hql = inventory_var = inventory_hql = ''
                if "productInput" in variable :
                    product_var = "$productInput: ProductInput!,"
                    product_hql = UPTADE_PRODUCT
                if "variantInput" in variable:
                    variant_var = '$variantInput: ProductVariantInput!,'
                    variant_hql = PRODUCT_VARIANT_UPDATE
                if "inventoryAdjustInput" in variable:
                    inventory_var = '$inventoryAdjustInput: InventoryAdjustQuantityInput!,'
                    inventory_hql = INVENTORY_ADJUST
                query = UPDATE_QUERY.format(productInput = product_var, variantInput = variant_var, inventoryAdjustInput = inventory_var, productUpdateq = product_hql, productVariantUpdateq = variant_hql, inventoryAdjustQuantity = inventory_hql)
                res = shopi.request_graphql(query, variable)
                for i in ['productUpdate', 'productVariantUpdate']:
                    try:
                        if (i in res.json()['data']):
                            if len(res.json()['data'][i]['userErrors']) == 0:
                                check.append({'sku':variable['variantInput']['sku'], 'Resultado':'Proceso exitoso'})
                            else:
                                check.append({'sku':variable['variantInput']['sku'], 'Resultado':'Proceso no exitoso'}) 
                        print(check)
                    except:
                        pass
                    try:
                        if res.json()['errors']:
                            check.append({'sku':variable['variantInput']['sku'], 'Resultado':'Proceso no exitoso'})
                    except:
                        pass
                if all(check):
                    cont +=1
                else:
                    not_update.append(variable['variantInput']['sku'])
            except:
                not_update.append(variable['variantInput']['sku'])
            data = {'success': True, 'element_success': cont,'not_successful':not_update}
        print(f'*** finaliza actualizacion de productos shopify{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    except Exception as e:
        data =  {'success': False}
        print(e)
        print('guardando archivo')
    pd.DataFrame(check).to_excel(os.path.join(settings.MEDIA_ROOT, 'final_review.xlsx'),index=False)
    return JsonResponse(data)

def export_products(request):
    print(f'*** inicia vista productos {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    df = create_file_products()
    df.replace(0,"Sin información", inplace = True)
    df.fillna("Sin información", inplace = True)
    df = df[['id', 'title', 'tags', 'vendor', 'status', 'price', 'compareAtPrice', 'sku', 'barcode', 'inventoryQuantity', 'margen', 'costo', 'margen_comparacion_db', 'sku_sodimac']]
    df.rename(columns = {'title':'titulo', 'vendor':'proveedor', 'status':'estado publicacion', 'price':'precio', 'compareAtPrice': 'precio comparación', 'barcode':'Codigo de barras', 'inventoryQuantity':'stock','sku_sodimac':'sodimac'}, inplace=True)
    folder = settings.MEDIA_ROOT
    file = f'products_{current_time}.xlsx'

    file_path = os.path.join(folder, file)

    column_names = list(df.columns)
    wb =Workbook()
    ws = wb.active
    for index, col_name in enumerate(column_names, start=1):
        cell = ws.cell(row=1, column=index)
        cell.value = col_name
        cell.font = Font(name='Calibri', size=12, color='000000')

    for row in dataframe_to_rows(df, index=False, header=False):
        ws.append(row)
    
    wb.save(file_path)


    with open(file_path, 'rb') as excel_file:
                response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{file}"'
    os.remove(file_path)
    print(f'*** finaliza vista productos {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return response

@login_required
def download_report(request, process):
    print(f'*** inicia descarga de informes de productos shopify{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    print('descargando archivo')
    if process == 1:
        name = 'review_report.xlsx'
    elif process == 2:
        name = 'final_review.xlsx'
    elif process == 3:
        name = 'plantilla cargue stock sodimac.xlsx'
    file_path = os.path.join(settings.MEDIA_ROOT, name)
    with open(file_path, 'rb') as excel_file:
                response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{name}"'
    if process != 3:
        os.remove(file_path)
    print(f'*** finaliza descarga de informes de productos shopify{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return response
