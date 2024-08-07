import pandas as pd
from pamo_bots.models import ProductsSodimac


class Core () :
    
    def __init__(self):
        pass
    
    def set_df(self, file):
        self.df = pd.read_excel(file, dtype=str)
        self.df.fillna('0', inplace=True)

    def get_products(self):
        return ProductsSodimac.objects.filter(sku_pamo__in = self.df['sku_pamo'].unique()), self.df
        
    def process(self):
        products = ProductsSodimac.objects.filter(sku_pamo__in = self.df['sku_pamo'].unique())
        sku_list = []
        products_list= []
        for i in products:
            data = self.df.loc[self.df['sku_pamo'] == i.sku_pamo, ['sku_sodimac', 'stock', 'ean']].values[0]
            if data[0] !='0':
                i.sku_sodimac = data[0]
            if data[1] !='0':
                i.stock = data[1]
            if data[2] !='0':
                i.ean = data[2] 
            products_list.append(i)
            sku_list.append(i.sku_pamo)
        ProductsSodimac.objects.bulk_update(products_list, ['sku_sodimac', 'stock', 'ean'])
        df_res = self.df.loc[~self.df['sku_pamo'].isin(sku_list)]
        if not df_res.empty:
            new_products = []
            for index, row in df_res.iterrows():
                item = ProductsSodimac()
                item.sku_sodimac = row['sku_sodimac']
                item.sku_pamo = row['sku_pamo']
                item.ean = row['ean']
                item.stock = row['stock']
                new_products.append(item)
            ProductsSodimac.objects.bulk_create(new_products)
    
    def update_database_item(self, sku, ean, stock):
        item = ProductsSodimac.objects.get(sku_sodimac = sku)
        item.ean = ean
        item.stock = stock
        item.save()