import requests
import json
import math
import time
import threading
from pamo.constants import URL_ENVIA_TRAKING
from pamo_bots.models import OrdersShopify, TrakingOrders


class EnviaConnection():

    def __init__(self):
        self.headers = {
            'content-type': 'application/json'
        }


    def _fetch_tracking_batch(self, batch, max_retries=5, backoff=3):
        payload = json.dumps({"trackingNumbers": batch})
        for attempt in range(1, max_retries + 1):
            try:
                time.sleep(10)
                response = requests.request(
                    "POST", URL_ENVIA_TRAKING, headers=self.headers, data=payload)
                response.raise_for_status()
                return response.json()['data']
            except Exception as e:
                print(f'Intento {attempt}/{max_retries} fallido para batch {batch}: {e}')
                if attempt < max_retries:
                    time.sleep(backoff ** attempt)
        return None

    def _run_traking_process(self, traking_numbers):
        TRANSIT_STATUSES = {
            'Delivered', 'Shipped', 'Picked Up', 'Undeliverable',
            'Delivery attempt', 'Information', 'Out for Delivery', 'Delivered at Origin'
        }
        total_numbers = len(traking_numbers)
        for i in range(math.ceil(total_numbers / 1)):
            batch = traking_numbers[i*5:(i+1)*5]
            data = self._fetch_tracking_batch(batch)
            if data is None:
                print(f'Se omite el batch {batch} después de varios reintentos.')
                continue
            dic_data = {item['trackingNumber']: item['status'] for item in data}
            objs = TrakingOrders.objects.filter(tracking_number__in=dic_data.keys())
            for obj in objs:
                status = dic_data[obj.tracking_number]
                obj.tracking_status = status
                print(status)
                if status in TRANSIT_STATUSES:
                    obj.in_transit = True
                obj.save()
        print('[TrakingShippments] proceso completado.')

    def get_traking_status(self, traking_numbers):
        traking_numbers = list(traking_numbers)
        hilo = threading.Thread(target=self._run_traking_process, args=(traking_numbers,), daemon=True)
        hilo.start()
        return hilo
