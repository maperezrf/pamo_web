import pandas as pd
from pamo.constants import COLUMNS_SHOPI
from unidecode import unidecode

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
        columns_end = []
        del(dic_columns['csrfmiddlewaretoken'])
        Change_colums={}
        for key, value in dic_columns.items():
            if value != 'N/A':
                key = key.replace('~',' ')
                Change_colums[key] = value
                columns_end.append(value)
        self.df.rename(columns=Change_colums, inplace=True)
        self.df = self.df[columns_end]
    
    def get_df(self):
        return self.df
    
    def set_df_shopi(self, responses):
        data_shopi ={'id_shopi': [i['data']['product']['id'].replace('gid://shopify/Product/', '') for i in responses],
                    'title_shopi': [i['data']['product']['title'] for i in responses],
                    'tags_shopi': [i['data']['product']['tags'] for i in responses],
                    'vendor_shopi': [i['data']['product']['vendor'] for i in responses],
                    'price_shopi': [i['data']['product']['variants']['edges'][0]['node']['price'] for i in responses],
                    'sku_shopi': [i['data']['product']['variants']['edges'][0]['node']['sku'] for i in responses],
                    'status': [i['data']['product']['status'] for i in responses],
                    'barcode_shopi': [i['data']['product']['variants']['edges'][0]['node']['barcode'] for i in responses],
                    'compareAtPrice_shopi': [i['data']['product']['variants']['edges'][0]['node']['compareAtPrice'] for i in responses],
                    'inventoryQuantity_shopi': [i['data']['product']['variants']['edges'][0]['node']['inventoryQuantity'] for i in responses],
                    'id_product_variant': [i['data']['product']['variants']['edges'][0]['node']['id'] for i in responses],
                    'id_inventory_item': [i['data']['product']['variants']['edges'][0]['node']['inventoryItem']['id'] for i in responses],
                    'id_inventory_level':[i['data']['product']['variants']['edges'][0]['node']['inventoryItem']['inventoryLevels']['edges'][0]['node']['id'] for i in responses]
                    }
        self.df_shopi = pd.DataFrame.from_dict(data_shopi)

    def merge(self, df = None):
        if 'Margen' in self.df.columns:
            self.df['Margen'] = pd.to_numeric(self.df['Margen'])/100
        if 'Margen comparación' in self.df.columns:
            self.df['Margen comparación'] = pd.to_numeric(self.df['Margen comparación'])/100
        self.df_rev = self.df.merge(self.df_shopi, how='left', left_on = 'SKU', right_on = 'sku_shopi')
        self.df_rev['tags_shopi'] = self.df_rev['tags_shopi'].apply(lambda x : ','.join(x) if type(x)==list else "")
        self.df_rev.fillna('nan', inplace=True)
        self.df_rev.columns = [unidecode(i).replace(' ','_').lower() for i in self.df_rev]
        if not df.empty:
            self.df_rev = self.df_rev.merge(df, how = 'left', on='sku')
            self.df_rev.drop_duplicates(subset=['sku_shopi','id_product_variant','tags_shopi','title_shopi'], inplace=True)
            self.df_rev.loc[self.df_rev.duplicated('sku_shopi', keep=False), 'duplicate'] = True 
            self.df_rev.sort_values(['sku_shopi','duplicate']).reset_index(inplace = True, drop=True)

    def get_df_mer(self):
        return self.df_rev
    
    def set_costo(self, df):
        if "precio" not in self.df_rev.columns:
            self.df_rev['precio'] = pd.to_numeric(df['costo_db'])/ (1- pd.to_numeric(df['margen_db']))
        if "precio_comparacion" not in self.df_rev.columns:
            self.df_rev['precio_comparacion'] = pd.to_numeric(df['costo_db'])/ (1- pd.to_numeric(df['margen_comparacion_db']))
    
    def set_variables(self):
        variables = []
        self.df_rev = self.df_rev.loc[self.df_rev['id_shopi'] != 'nan'].reset_index(drop=True)
        for i in range(self.df_rev.shape[0]):
            variants = {'id':self.df_rev.loc[i]['id_product_variant']}
            variants['sku'] = self.df_rev.loc[i]['sku_shopi']
            product = {'id':f"gid://shopify/Product/{self.df_rev.loc[i]['id_shopi']}"}
            inventory = {'inventoryLevelId':self.df_rev.loc[i]['id_inventory_level']}
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
                tags_shopi = self.df_rev.loc[i]['tags_shopi'].strip(',').split(',')
                tags_new = [i.upper() for i in [i.lower().strip() for i in tags_archive] if i not in [j.lower().strip() for j in tags_shopi ]]
                tags_shopi.extend(tags_new)
                product['tags'] = tags_shopi
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
                variants["inventoryItem"]={'cost':str(self.df_rev.loc[i]['costo_db'])}
            except:
                pass
            try:
                inventory["availableDelta"] = int(self.df_rev.loc[i]['stock']) - int(self.df_rev.loc[i]['inventoryquantity_shopi'])
            except:
                pass

            var ={}
            if any([True for i in ['title','vendor','status','tags'] if i in product]):
                var['productInput'] = product
            if any([True for i in ['barcode','compareAtPrice','price','inventoryItem'] if i in variants ]):
                var['variantInput'] = variants
            if 'availableDelta' in inventory:
                var['inventoryAdjustInput'] = inventory
            variables.append(var)
        return variables