import requests
from datetime import datetime
from decouple import config
import json

class connAirtable():

    url = config('URL_AIRTABLE')
    headers = {'Authorization': f'Bearer {config("TOKEN_AIRTABLE")}',
            'Content-Type': 'application/json'}

    def get_last_id(self):
        response = requests.request("GET", self.url, headers= self.headers, data={})
        max_element = max([datetime.strptime(i['createdTime'],'%Y-%m-%dT%H:%M:%S.%fZ') for i in response.json()['records']])
        index = [datetime.strptime(i['createdTime'],'%Y-%m-%dT%H:%M:%S.%fZ') for i in response.json()['records']].index(max_element)
        return response.json()['records'][index]['fields']['Id_pedido']

    def create_records(self, orders):
        response = requests.request("POST", self.url, headers= self.headers, data = json.dumps(orders) )
        return response.json()

    def get_data_air(self, orders, id):
        orders_air= {}
        orders_air['records'] = []
        id = int(id)
        for i in orders:
            id += 1
            dic = {
                "fields": {
                "Id_pedido":str(id),
                "Orden_Sodimac": str(i),
                "Estado": "Pendiente"
                }
            }
            orders_air['records'].append(dic)
        return orders_air

    def process(self, orders):
        last_id = self.get_last_id()
        orders_air = self.get_data_air(orders, last_id)
        return self.create_records(orders_air)






