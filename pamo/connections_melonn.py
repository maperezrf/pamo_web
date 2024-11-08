import requests
import re
import json
from decouple import config


class connMelonn:

    def __init__(self):
        self.url = config('MELONN_URL')
        self.headers = {
        'accept': 'application/json',
        'X-Api-Key': config('MELONN_API_KEY'),
        'Content-Type': 'application/json'
        }

    def create_data(self, orders):
        data_order = {
            "orderNumber": str(orders['ORDEN_COMPRA'].unique()[0]),
            "orderId": str(orders['ORDEN_COMPRA'].unique()[0]),
            "comments": "SODIMAC",
            "requestProcessing": True,
            "holdFulfillmentAfterProcessing": False,
            "shipping": {
                "fullName": 'SODIMAC COLOMBIA SA',
                "addressL1": config('ADRESS_SODIMAC'),
                "addressL2": '',
                "city": 'BOGOTÁ, D.C.',
                "region": 'BOGOTÁ, D.C.',
                "country": 'Colombia',
                "postalCode": "00000",
                "phoneNumber": config('PHONE'),
            },
            "buyer": {
                "fullName": "SODIMAC COLOMBIA SA",
                "phoneNumber": config('PHONE'),
                "email": config('SODIMAC_EMAIL')
            }
        }

        line_items = []

        for index , row in orders.iterrows():
            dic = {}
            dic['sku'] = row['SKU']
            dic['quantity'] = row['CANTIDAD_SKU']
            line_items.append(dic)

        data_order["lineItems"] = line_items
        data_order["shippingMethodTitle"] = "Envio Sodimac"
        data_order = data_order
        self.data_order = data_order
    
    def create_order(self):
        response = requests.request("POST", self.url, headers=self.headers, data= json.dumps(self.data_order))
        return response.json()
    

    