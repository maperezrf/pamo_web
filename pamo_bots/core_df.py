import pandas as pd
from pamo_bots.models import ProductsSodimac


class Core () :
    
    def __init__(self):
        pass
    
    def set_df(self, file):
        self.df = pd.read_excel(file, dtype=str)
        self.df.fillna('0', inplace=True)
    
    # SKU SODIMAC	SKU SHOPIFY	STOCK	EAN
    def process(self):
        products = ProductsSodimac.objects.filter(SKU__in = self.df['SKU SODIMAC'].unique())
        products_df = pd.DataFrame(list(products.values()))
        df_m = self.df.merge(products_df, left_on='SKU SODIMAC', right_on='SKU')
        df_m.drop_duplicates(inplace=True)
        print(df_m)
        sku_list = []
        products_list= []
        for i in products:
            data = self.df.loc[self.df['SKU SHOPIFY'] == i.RF_pamo, ['SKU SODIMAC', 'STOCK', 'EAN']].values[0]
            if data[0]:
                i.SKU = data[0]
            if data[1]:
                i.stock = data[1]
            if data[2]:
                i.cod_barras = data[2] 
            products_list.append(i)
            sku_list.append(i.RF_pamo)
        ProductsSodimac.objects.bulk_update(products_list, ['SKU', 'stock', 'cod_barras'])
        df_res = self.df.loc[~self.df['SKU SHOPIFY'].isin(sku_list)]
        if not df_res.empty:
            new_products = []
            for index, row in df_res.iterrows():
                item = ProductsSodimac()
                item.SKU = row['SKU SODIMAC']
                item.RF_pamo = row['SKU SHOPIFY']
                item.cod_barras = row['EAN']
                item.stock = row['STOCK']
                new_products.append(item)
            ProductsSodimac.objects.bulk_create(new_products)
                
            
            
            

    
        
        
        
        
        
    