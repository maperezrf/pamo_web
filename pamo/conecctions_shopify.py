from pamo.constants import *
import requests
import pandas as pd
import json
from pamo.functions import make_json

class ConnectionsShopify():

    headers_shopify = {}

    def __init__(self) -> None:
        self.headers_shopify = {'X-Shopify-Access-Token' : ACCES_TOKEN, 'Content-Type' : 'application/json'}

    def request_graphql(self, query, variables = None ):
        return requests.post(URL_GRAPHQL, headers=self.headers_shopify, data=json.dumps({"query": query, 'variables': variables}))

    def get_rest(self,url):
        return requests.get(url, headers= self.headers_shopify)

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