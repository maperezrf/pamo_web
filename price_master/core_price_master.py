import pandas as pd
from products.models import Products
from pamo_bots.models import ProductsSodimac
from .models import products_meli

class PriceMaster():
    
    def __init__(self) -> None:
        pass

    def get_all_products(self):
        df_shopify = pd.DataFrame(Products.objects.all().values())
        df_sodimac = pd.DataFrame(ProductsSodimac.objects.all().values())
        df_meli = pd.DataFrame(products_meli.objects.all().values())
        df_sho_sod= df_shopify.merge(df_sodimac, how='left', left_on='sku', right_on='sku_pamo')
        return df_sho_sod.merge(df_meli, how='left', on='sku')