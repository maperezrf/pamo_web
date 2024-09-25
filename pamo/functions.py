from products.models import Products
from pamo_bots.models import ProductsSodimac
from datetime import datetime
import pandas as pd

def make_json(res):
    for i in range(len(res)):
        res[i]['node']['createdAt'] = datetime.strptime((res[i]['node']['createdAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res[i]['node']['updatedAt'] = datetime.strptime((res[i]['node']['updatedAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res[i]['node']['name'] = int(res[i]['node']['name'][2:])
    return(res)

def update_products_db(df):
    for i in range(df.shape[0]):          
        sku_to_search = df.loc[i,'id_products']
        if  sku_to_search != 'nan':
            try:
                element, create  = Products.objects.get_or_create(idShopi = df.loc[i,'id_products'], sku =  df.loc[i,'sku_shopi'])
                if create:
                    element.title = df.loc[i,'title_shopi']
                    element.tags = df.loc[i,'tags_shopi']
                    element.vendor = df.loc[i,'vendor_shopi']
                    element.barcode = df.loc[i,'barcode_shopi']
                    element.status = df.loc[i,'status_shopi']
                element.margen = df.loc[i,'margen'] if 'margen' in df.columns else float(element.margen)
                element.costo = df.loc[i,'costo'] if 'costo' in df.columns else float(element.costo)
                element.margen_comparacion_db = df.loc[i,'margen_comparacion'] if 'margen_comparacion' in df.columns else element.margen_comparacion_db
                element.price = int(element.costo)/(1-float(element.margen))
                element.compareAtPrice = int(element.costo)/(1-float(element.margen_comparacion_db))
                element.save()
                df.loc[i,'precio'] = float(element.price)
                df.loc[i,'precio_comparacion'] = float(element.compareAtPrice)
            except Exception as e:
                df.loc[i,'precio'] = float(element.price)
                df.loc[i,'precio_comparacion'] = float(element.compareAtPrice)
                print(f"{e} {df.loc[i,'id_products']} {df.loc[i,'sku_shopi']}")
    return df

def create_file_products():
    products =  pd.DataFrame(list(Products.objects.all().values()))
    products_sodimac = pd.DataFrame(list(ProductsSodimac.objects.all().values()))
    products_mg= products.merge(products_sodimac[['sku_sodimac', 'sku_pamo']], how='left', left_on= 'sku', right_on = 'sku_pamo')
    products_mg.drop_duplicates('id', inplace= True)
    products_mg.fillna(0.0, inplace = True)
    return  products_mg