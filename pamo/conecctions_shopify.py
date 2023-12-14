from pamo.constants import *
import requests
import pandas as pd
import json
from pamo.functions import make_json
import os
from datetime import datetime
from pamo.queries import GET_VARIANT_ID


class ConnectionsShopify():

    headers_shopify = {}
    orders = pd.DataFrame()

    def __init__(self) -> None:
        self.headers_shopify = {'X-Shopify-Access-Token' : ACCES_TOKEN, 'Content-Type' : 'application/json'}

    def set_orders_df(self, orders):
        self.orders = orders

    def request_graphql(self, query, variables = None ):
        return requests.post(URL_GRAPHQL, headers=self.headers_shopify, data=json.dumps({"query": query, 'variables': variables}))

    def get_rest(self,url):
        return requests.get(url, headers= self.headers_shopify)

    def get_variant_id(self):
        sku_un = self.orders['SKU'].unique()
        for i in sku_un:
            query = GET_VARIANT_ID.format(skus = str(i).strip())
            response = requests.post(URL_GRAPHQL, headers=self.headers_shopify, data=json.dumps({"query": query}))
            try:
                variant_id = str(response.json()['data']['products']['edges'][0]['node']['variants']['edges'][0]['node']['id']).replace('gid://shopify/ProductVariant/', '')
                self.orders.loc[self.orders['SKU']==i, 'variant_id'] = variant_id
            except:
                print(f'No se encontro el SKU en shopify: {i}')
        return self.orders.loc[self.orders['variant_id'].notna()]

    def bucle_request(self, query, datatype):
        response = self.request_graphql(query.format(cursor=''))
        print(query.format(cursor=''))
        print(response.json())
        res  = response.json()['data'][datatype]['edges']
        print(res)
        daft_orders = make_json(res)
        print(daft_orders)
        has_next = response.json()['data'][datatype]['pageInfo']['hasNextPage']
        while has_next:
            response = self.request_graphql(query.format( cursor= f",after:\"{response.json()['data'][datatype]['pageInfo']['endCursor']}\""))
            res  = response.json()['data'][datatype]['edges']
            daft_orders.extend(make_json(res))
            has_next = response.json()['data'][datatype]['pageInfo']['hasNextPage']
        print(response.json())

    def create_orders(self):
        orders_gb = self.orders.groupby('ORDEN_COMPRA').agg({'variant_id':list, 'CANTIDAD_SKU':list,'COSTO_SKU':list}).reset_index()
        cont = 0
        print(orders_gb.shape[0])
        print(len(orders_gb))
        for i in range(len(orders_gb)):   
            products = []
            oc = orders_gb.iloc[i]['ORDEN_COMPRA']
            cantidad = orders_gb.iloc[i]['CANTIDAD_SKU']
            costo = orders_gb.iloc[i]['COSTO_SKU']
            variant_id = orders_gb.iloc[i]['variant_id']
            products = []    
            for i in range(len(variant_id)):
                products.append({"variant_id": variant_id[i], "quantity": cantidad[i], "price": costo[i]})
                data = {
                    "order": {
                        "line_items": products,
                        "customer": {
                            "id": 7247084421397
                        },
                        "financial_status": "pending",
                        "note": f"orden de compra: {oc}"
                    }
                }
                print(data)  
                try:  
                    response = requests.post(URL_CREATE_ORDERS, headers= self.headers_shopify, json = data)
                    if response.status_code == 201:
                        cont += 1
                except:
                    pass
        return cont
    
    def get_orders(self):
        return self.orders