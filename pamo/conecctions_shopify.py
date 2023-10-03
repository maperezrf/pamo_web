from pamo.constants import *
import requests
import pandas as pd
import json

class ConnectionsShopify():

    headers_shopify = {}

    def __init__(self) -> None:
        self.headers_shopify = {'X-Shopify-Access-Token' : ACCES_TOKEN, 'Content-Type' : 'application/json'}

    def request_graphql(self, query):
        return requests.post(URL_GRAPHQL, headers=self.headers_shopify, data=json.dumps({"query": query}))

    def get_rest(self,url):
        return requests.get(url, headers= self.headers_shopify)