import requests
import json
from pamo.constants import URL_ENVIA_TRAKING
import math
import time
from pamo_bots.models import OrdersShopify, TrakingOrders


class EnviaConnection():

    def __init__(self):
        self.headers = {
            'content-type': 'application/json'
        }

    def get_traking_status(self, traking_numbers):
        traking_numbers = list(traking_numbers)
        total_numbers = len(traking_numbers)
        count = 0
        total_traking = []
        for i in range(math.ceil(total_numbers / 10)):
            time.sleep(120)
            print(traking_numbers[count:count+10])
            payload = json.dumps({
                "trackingNumbers": traking_numbers[count:count+10]})
            count += 10
            print(traking_numbers[count:count+10])
            response = requests.request(
                "POST", URL_ENVIA_TRAKING, headers=self.headers, data=payload)
            try:
                data = response.json()['data']
                print(data)
                dic_data = {i['trackingNumber']: i['status'] for i in data}
                objs = TrakingOrders.objects.filter(
                    tracking_number__in=dic_data.keys())
                for obj in objs:
                    status = dic_data[obj.tracking_number]
                    obj.tracking_status = dic_data[obj.tracking_number]
                    print(status)
                    if status in ['Delivered', 'Shipped', 'Picked Up', 'Undeliverable', 'Delivery attempt', 'Information', 'Out for Delivery', 'Delivered at Origin']:
                        obj.in_transit = True
                    obj.save()
            except Exception as e:
                print(f'error al tratar de traer las ordenes {e}')
        print(total_traking)
