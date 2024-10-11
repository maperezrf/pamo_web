import pandas as pd
from pamo.constants import COLUMNS_SHOPI
from unidecode import unidecode
import ast

class CoreDf():

    df = pd.DataFrame() 
    df_shopi = pd.DataFrame() 
    df_rev = pd.DataFrame() 

    def __init__(self) -> None:
        pass

    def set_df(self, file):
        self.df = pd.read_excel(file, dtype = str)

    def get_df(self):
        return self.df
    
    def get_df_columns(self):
        return self.df.columns.values

    def rename_columns(self, dic_columns):
        self.df.columns = [i.strip() for i in self.df.columns ] 
        columns_end = []
        del(dic_columns['csrfmiddlewaretoken'])
        Change_colums={}
        for key, value in dic_columns.items():
            if value != 'N/A':
                key = key.replace('~',' ').strip()
                Change_colums[key] = value
                columns_end.append(value)
        self.df.rename(columns=Change_colums, inplace=True)
        self.df = self.df[columns_end]
        self.df['SKU'] = self.df['SKU'].str.replace('"','\\"' )

    
    def get_df(self):
        return self.df
    
    def set_df_shopi(self, responses):
        id_products = [] 
        titles=[]
        tags = []
        vendor = []
        status = []
        published = []
        sku = []

        id_variant = []
        sku_variant = []
        barcode = []
        inventoryQuantity = []
        inventoryItemId = []
        inventoryLevelsId = []
        id_products_variant = []

        data_products = {}
        data_variants = {}

        for i in  responses:
            for j in i['data']['products']['edges']:
                sku.append(i['data']['products']['sku'])
                titles.append(j['node']['title'])
                id_products.append(j['node']['id'].replace('gid://shopify/Product/',''))
                tags.append(j['node']['tags'])
                status.append(j['node']['status'])
                vendor.append(j['node']['vendor'])
                published.append(j['node']['status'])
                for k in j['node']['variants']['edges']:
                    id_products_variant.append(j['node']['id'].replace('gid://shopify/Product/',''))
                    id_variant.append(k['node']['id'])
                    sku_variant.append(k['node']['sku'])
                    barcode.append(k['node']['barcode'])
                    inventoryQuantity.append(k['node']['inventoryQuantity'])
                    inventoryItemId.append(k['node']['inventoryItem']['id'])
                    inventoryLevelsId.append(k['node']['inventoryItem']['inventoryLevels']['edges'][0]['node']['id'])

        data_products = {
            'id_products':id_products,
            'title_shopi': titles,
            'tags_shopi': tags,
            'vendor_shopi': vendor,
            'status_shopi': status,
            'published_shopi': published,
            'sku_shopi':sku
            }
        df_products = pd.DataFrame(data_products).reset_index(drop=True)
        df_products['sku_shopi'] = df_products['sku_shopi'].str.replace('\\"', '"')
        data_variants = {
            'idShopi' : id_products_variant,
            'id_variant': id_variant,
            'sku_variant': sku_variant,
            'barcode_shopi': barcode,
            'inventoryQuantity_shopi': inventoryQuantity,
            'inventoryItemId': inventoryItemId,
            'inventoryLevelsId': inventoryLevelsId
        }
        df_variants = pd.DataFrame(data_variants).reset_index(drop=True)
        df_variants.drop_duplicates(inplace=True)

        df = df_variants.merge(df_products, how= 'left', right_on = ['sku_shopi', 'id_products'], left_on=  ['sku_variant', 'idShopi'])
        df = df.loc[df['id_products'].notna()]
        sku_duplicated = df.loc[df.duplicated('sku_variant', keep=False)]['sku_variant'].unique() #devolver informacion front
        self.df_shopi = df
        return self.df_shopi, sku_duplicated 

    def merge(self, df_base = None,):
        self.df['SKU'] = self.df['SKU'].str.replace('\\"', '"')
        if 'Margen' in self.df.columns:
            self.df['Margen'] = pd.to_numeric(self.df['Margen'])/100
        if 'Margen comparación' in self.df.columns:
            self.df['Margen comparación'] = pd.to_numeric(self.df['Margen comparación'])/100
        df_m1 = self.df_shopi.merge(self.df, how='left', left_on='sku_variant', right_on='SKU')
        self.df_rev = df_m1.merge(df_base, how='left', left_on = ['sku_shopi', 'idShopi'], right_on=['sku', 'idShopi'])
        self.df_rev.fillna('nan', inplace=True)
        self.df_rev.columns = [unidecode(i).replace(' ','_').lower() for i in self.df_rev]
        # if not df_shopi.empty:
        # self.df_rev = self.df_rev.merge(df, how = 'left', on='sku')
        self.df_rev.drop_duplicates(subset=['sku_shopi','idshopi'], inplace=True)
        # self.df_rev.loc[self.df_rev.duplicated('sku_shopi', keep=False), 'duplicate'] = True 
        # self.df_rev.sort_values(['sku_shopi','duplicate']).reset_index(inplace = True, drop=True)

    def get_df_mer(self):
        return self.df_rev
    
    def set_costo(self, df):
        # if "precio" not in self.df_rev.columns:
        self.df_rev['precio'] = df['precio']
        # self.df_rev['precio'] = self.df_rev['price']
        # if "precio_comparacion" not in self.df_rev.columns:
        self.df_rev['precio_comparacion'] = df['precio_comparacion'] 
        # self.df_rev['precio_comparacion'] = self.df_rev['compareatprice']

    def set_variables(self):
        variables = []
        self.df_rev = self.df_rev.loc[self.df_rev['id_products'] != 'nan'].reset_index(drop=True)
        for i in range(self.df_rev.shape[0]):
            variants = {'id':self.df_rev.loc[i]['id_variant']}
            # variants['sku'] = self.df_rev.loc[i]['sku_shopi']
            product = {'id':f"gid://shopify/Product/{self.df_rev.loc[i]['id_products']}"}
            inventory = {'inventoryLevelId':self.df_rev.loc[i]['inventorylevelsid']}
            try:
                product['title'] = self.df_rev.loc[i]['titulo']
            except:
                pass
            try:
                product['vendor'] = self.df_rev.loc[i]['proveedor'] 
            except:
                pass
            try:
                product['status'] = 'ACTIVE' if self.df_rev.loc[i]['estado_publicacion'] == '1' else 'DRAFT'
            except:
                pass
            try:
                tags_archive= self.df_rev.loc[i]['tags'].strip(',').split(',')
                tags_shopi = self.df_rev.loc[i]['tags_shopi']
                tags_new = [i.upper() for i in [i.lower().strip() for i in tags_archive] if i not in [j.lower().strip() for j in tags_shopi ]]
                tags_shopi.extend(tags_new)
                product['tags'] = tags_shopi
                if 'PAUSADO' in product['tags']:
                    variants['inventoryPolicy'] = 'DENY'
            except:
                pass
            try:
                variants['barcode'] = self.df_rev.loc[i]['codigo_barras']
            except:
                pass
            try:
                variants['compareAtPrice'] = str(self.df_rev.loc[i]['precio_comparacion'])
            except:
                pass
            try:
                variants['price'] = str(self.df_rev.loc[i]['precio'])
            except:
                pass
            try:
                variants["inventoryItem"]={'cost':str(self.df_rev.loc[i]['costo'])}
            except:
                pass
            try:
                inventory["availableDelta"] = int(self.df_rev.loc[i]['stock']) - int(self.df_rev.loc[i]['inventoryquantity_shopi'])
            except:
                pass

            var ={}
            if any([True for i in ['title','vendor','status','tags'] if i in product]):
                var['productInput'] = product
            if any([True for i in ['sku','barcode','compareAtPrice','price','inventoryItem'] if i in variants ]):
                var['variantInput'] = variants
            if 'availableDelta' in inventory:
                var['inventoryAdjustInput'] = inventory
            variables.append(var)
        return variables