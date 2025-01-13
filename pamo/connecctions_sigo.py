from decouple import config
from datetime import datetime, timedelta
from quote_print.models import SigoToken, SigoCostumers
import math
import requests
import json

class SigoConnection():
    headers = {
    'Content-Type': 'application/json'
    }

    def __init__(self):
        item_token = SigoToken.objects.all().first()
        if item_token.date_expired.replace(tzinfo=None) < datetime.now():
            item_token = self.update_token()
        self.headers['Authorization'] =  item_token.token
        self.headers['Partner-Id'] =  config('SIGO_PARNER_ID')

    def update_token(self):
        data = {
        "username": config('SIGO_USERNAME'),
        "access_key": config('SIGO_ACCES_KEY')
        }
        response = requests.request("POST", config('SIGO_URL_AUTH'), headers= self.headers, data=json.dumps(data))
        date_expired = datetime.now() + timedelta(hours=23)
        item_token = SigoToken.objects.all().first()
        item_token.token = response.json()['access_token']
        item_token.date_expired = date_expired
        item_token.save()
        return item_token
    
    def synchronize_new_costumer(self):
        date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        response = requests.request("GET", f"https://api.siigo.com/v1/customers?created_start={date}", headers = self.headers).json()
        created_count = 0 
        for i in response['results']:
            item, created =  SigoCostumers.objects.get_or_create(id=i['id'],identification=i['identification'])
            if created:
                created_count += 1
        return created_count
    
    def synchronize_all_costumers(self):
        response = requests.request("GET", "https://api.siigo.com/v1/customers?", headers = self.headers).json()
        customers = []
        SigoCostumers.objects.all().delete()
        pages = math.ceil(response['pagination']['total_results']/100)

        for i in range(pages+3):
            print(i)
            response = requests.request("GET", f"https://api.siigo.com/v1/customers?page={i+1}&page_size=100", headers = self.headers).json()
            for j in response['results']:
                item = SigoCostumers()
                item.id = j['id']
                item.identification = j['identification']
                customers.append(item)
        SigoCostumers.objects.bulk_create(customers)
    
    def get_info_costumer(self, id_client):
        response = requests.request("GET", f"https://api.siigo.com/v1/customers/{id_client}", headers = self.headers).json()
        data = {}
        data['id'] = response['id']
        data['tipo_doc'] = response['id_type']['name']
        data['identificacion'] = f"{response['identification']}-{ response['check_digit']}"
        data['name'] = " ".join(response['name']).title()
        data['email'] = response['contacts'][0]['email']
        return data
        



        