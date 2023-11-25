from products.models import Products
from datetime import datetime
import pandas as pd

def make_json(res):
    for i in range(len(res)):
        res[i]['node']['createdAt'] = datetime.strptime((res[i]['node']['createdAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res[i]['node']['updatedAt'] = datetime.strptime((res[i]['node']['updatedAt']), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
        res[i]['node']['name'] = int(res[i]['node']['name'][2:])
    return(res)

def update_products_db(df):
    if 'margen' in df.columns:
        for i in range(df.shape[0]):
            print('guardando')
            element = Products.objects.get(sku = df.loc[i,'sku'])
            element.margen = df.loc[i,'margen']
            element.save()
            df.loc[i,'margen_db'] = df.loc[i,'margen']
        return df
    else:
        return pd.DataFrame()

