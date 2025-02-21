from decouple import config
from datetime import datetime, timedelta
from quote_print.models import SigoToken, SigoCostumers
import math
import requests
import json
from datetime import datetime
import math

class SigoConnection():
    headers = {
    'Content-Type': 'application/json'
    }


    def __init__(self):
        self.today_str = datetime.now().strftime('%Y-%m-%d')
        print(f'La fecha de hoy es: {self.today_str}')
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
        
    def get_data(self, df, oc, taxes):
        items = []
        total_cost = 0
        for index, row in df.loc[df['ORDEN_COMPRA']== oc].iterrows():
            item = {}
            item["code"] = row.SKU
            item["quantity"] =row.CANTIDAD_SKU
            item["price"] =round(row.COSTO_SKU_x,2)
            item["discount"] = 0
            item["taxes"] = taxes
            cost_unique = row.COSTO_SKU_x * row.CANTIDAD_SKU
            total_cost += cost_unique
            iva = total_cost *.19
            reteica = round(total_cost * 0.01104, 2)
            reteiva = iva* 0.15
            retencion = total_cost * 0.025
            items.append(item)    
            value_api = row.get('novelty', None)
        return items, total_cost, reteica, row.ORDEN_COMPRA, reteiva, retencion, value_api

    def create_invoice(self, df, taxes):
        responses = {}
        for i in df['ORDEN_COMPRA'].unique():
            items, total_cost, reteica, oc, reteiva, retencion, value_api  = self.get_data(df, i, taxes)
            if ((value_api == '0') or (value_api == None)) :
                value = round(total_cost + round((total_cost *0.19),2) - round(reteiva,2) - round(reteica,2) - round(retencion,2),2)
            else:
                value = value_api
            playload =  json.dumps( {
            "document":{
                "id":26647
            },
            "date":self.today_str,
            "customer":{
                "person_type":"Company",
                "id_type":"31",
                "identification":"800242106",
                "branch_office":0,
                "name":[
                    "SODIMAC COLOMBIA S A"
                ],
                "address":{
                    "address":"CR 68 D 80 70",
                    "city":{
                        "country_code":"Co",
                        "country_name":"Colombia",
                        "state_code":"11",
                        "city_code":"11001",
                        "city_name":"Bogotá"
                    },
                    "postal_code":"110911"
                },
                "phones":[
                    {
                        "indicative":"601",
                        "number":"5460000",
                        "extension":"000"
                    }
                ],
                "contacts":[
                    {
                        "first_name":"SODIMAC",
                        "last_name":"COLOMBIA S A",
                        "email":"recepcionfacturaelectronicasodimac2@homecenter.co",
                        "phone":{
                        "indicative":"000",
                        "number":"0000000"
                        }
                    },
                    {
                        "first_name":"FACTURACION",
                        "last_name":"",
                        "email":"recepcionfacturaelectronicasodimac2@homecenter.co",
                        "phone":{
                        
                        }
                    },
                    {
                        "first_name":"marketplace",
                        "last_name":"@pamo.co",
                        "email":"marketplace@pamo.co",
                        "phone":{
                        
                        }
                    },
                    {
                        "first_name":"LIDERCOMERCAIL1",
                        "last_name":"@PAMO.CO",
                        "email":"LIDERCOMERCAIL1@PAMO.CO",
                        "phone":{
                        
                        }
                    },
                    {
                        "first_name":"Jeffry",
                        "last_name":"Herrera",
                        "email":"jherreram@homecenter.co",
                        "phone":{
                        "indicative":"57",
                        "number":"3155549249"
                        }
                    },
                    {
                        "first_name":"omunoz",
                        "last_name":"@homecenter.co",
                        "email":"omunoz@homecenter.co",
                        "phone":{
                        
                        }
                    },
                    {
                        "first_name":"contabilidad",
                        "last_name":"@feprin.com",
                        "email":"contabilidad@feprin.com",
                        "phone":{
                        
                        }
                    },
                    {
                        "first_name":"facturacionelectronica",
                        "last_name":"@feprin.com",
                        "email":"facturacionelectronica@feprin.com",
                        "phone":{
                        
                        }
                    }
                ]
            },
            "cost_center":116,
            "seller":643,
            "retentions":[
                {
                    "id":13457
                },
                {
                    "id":13464
                }
            ],
            "reteica":reteica,
            "stamp":{
                "send":True
            },
            "mail":{
                "send":False
            },
            "observations":"Para pagos por bancos a nombre de FEPRIN S.A.S. tenga en cuenta la siguiente información:\nDAVIVIENDA Cuenta de Ahorros 457600102745\nBANCOLOMBIA Cuenta de Ahorros 17400002178\nRevisa nuestras políticas de cambios y garantías: www.pamo.co.",
            "items":items,
            "payments":[
                {
                    "id":6507,
                    "value": value,
                    "due_date":self.today_str
                }
            ],
            "additional_fields":{
                "purchase_order":{
                    "number":f"{oc}"
                }
            }
            })
            print(playload)
            response = requests.request("POST", config('URL_CREATE_INVOICES'), headers=self.headers, data=playload)
            print(response)
            print(response.json())
            responses[oc] = response
        return responses