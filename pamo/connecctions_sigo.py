from decouple import config
from datetime import datetime, timedelta
from quote_print.models import SigoToken, SigoCostumers
from pamo_bots.models import InvoicesSiigo
from django.db.models import Count
import math
import requests
import json
from datetime import datetime
import math
from pamo.constants import NIT_SODIMAC

class SigoConnection():
    headers = {
    'Content-Type': 'application/json'
    }


    def __init__(self):
        self.today_str = datetime.now().strftime('%Y-%m-%d')
        print(f'La fecha de hoy es: {self.today_str}')
        item_token = SigoToken.objects.all().first()
        # if item_token.date_expired.replace(tzinfo=None) < datetime.now():
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
        df['created'] = False
        for index, row in df.loc[(df['ORDEN_COMPRA']== oc) & (df['created']== False)].iterrows():
            item = {}
            item["code"] = row.SKU
            item["quantity"] =row.CANTIDAD_SKU
            item["price"] =round(row.COSTO_SKU,2)
            item["discount"] = 0
            item["taxes"] = taxes
            cost_unique = row.COSTO_SKU * row.CANTIDAD_SKU
            total_cost += cost_unique
            iva = total_cost *.19
            reteica = round(total_cost * 0.01104, 2)
            reteiva = iva* 0.15
            retencion = total_cost * 0.025
            items.append(item)    
            value_api = row.get('novelty', None)
            df.loc[df['ORDEN_COMPRA']== oc, 'created'] = True
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
                "send":True
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
            print(f'respuesta**********************:{response}')
            print(response)
            try:
                print(response.json())
            except Exception as e:
                print('error')
                print(e)
            responses[oc] = response
        return responses


    def get_monthly_invoices(self):
        """
        Trae las facturas del mes y filtra por Sodimac.
        No sabe nada de la base de datos.
        """
        today = datetime.now()
        date_start = today.replace(day=1).strftime('%Y-%m-%d')
        date_end =  (today + timedelta(days=1)).strftime('%Y-%m-%d')
        page_size = 100
        base_url = (
            f"https://api.siigo.com/v1/invoices?"
            f"date_start={date_start}&"
            f"date_end={date_end}&"
            f"page_size={page_size}"
        )
        
        all_results = []
        
        try:
            first_response = requests.get(f"{base_url}&page=1", headers=self.headers)
            if first_response.status_code != 200:
                return []
            
            first_data = first_response.json()
            total_results = first_data.get('pagination', {}).get('total_results', 0)
            all_results.extend(first_data.get('results', [])) # Corregido el extend
            
            total_pages = math.ceil(total_results / page_size)
            
            for page in range(2, total_pages + 1):
                response = requests.get(f"{base_url}&page={page}", headers=self.headers)
                if response.status_code == 200:
                    all_results.extend(response.json().get('results', []))
            
            invoices_sodimac = [i for i in all_results if i.get("customer", {}).get('identification') == NIT_SODIMAC]
            return invoices_sodimac
            
        except Exception as e:
            raise(f"Error en la consulta: {e}")

    def process_and_save_invoices(self, invoices_list):
        """
        procesa los datos complejos 
        (costos, OC) y guarda en la base de datos.
        """

        db_invoices = [i['name'] for i in list(InvoicesSiigo.objects.all().values('name'))]
        invoices_list = [ i for i in  invoices_list if i.get('name') not in db_invoices]
        stats = {'created': 0, 'skipped': 0}

        for invoice_json in invoices_list:
            try:
               
                invoice_id = invoice_json.get('id')
                if not invoice_id:
                    continue
                items = invoice_json.get('items', [])
                total_items_cost = sum([float(item.get('price', 0) * item.get('quantity', 0)) for item in items])
                additional_fields = invoice_json.get('additional_fields', {})
                purchase_order_data = additional_fields.get('purchase_order', {})
                oc_number = purchase_order_data.get('number', None)
                obj, created = InvoicesSiigo.objects.update_or_create(
                    id=invoice_id,
                    defaults={
                        'name': invoice_json.get('name'),
                        'date': invoice_json.get('date'),
                        'total': invoice_json.get('total', 0),
                        'items_cost': total_items_cost,
                        'oc': oc_number
                    }
                )
                if created:
                    stats['created'] += 1
            except Exception as e:
                print(f"Error procesando factura {invoice_json.get('id')}: {e}")
                stats['skipped'] += 1
        print(f"Sincronización completada: {stats}")
        return [ i.get('oc') for i in  InvoicesSiigo.objects.exclude(oc__isnull=True).values('oc')]
    
    
    def check_invoice_novelties(self):
        """
        Revisa las facturas en DB y setea la columna novelty según las novedades encontradas:
        1. Factura sin OC relacionada (oc vacía o nula)
        2. OC duplicada (mismo número de OC en facturas con diferente name)
        3. Costo diferente al total_cost almacenado en SodimacOrders
        """
        from quote_print.models import SodimacOrders
        costos = {
            str(o.id): float(o.total_cost)
            for o in SodimacOrders.objects.exclude(total_cost__isnull=True)
        }

        ocs_duplicadas = set(
            InvoicesSiigo.objects
            .exclude(oc__isnull=True).exclude(oc='')
            .values('oc')
            .annotate(total=Count('id'))
            .filter(total__gt=1)
            .values_list('oc', flat=True)
        )

        sin_oc_ids, oc_duplicada_ids, costo_diferente_ids = [], [], []
        for inv in InvoicesSiigo.objects.all():
            if not inv.oc:
                sin_oc_ids.append(inv.id)
            elif inv.oc in ocs_duplicadas:
                oc_duplicada_ids.append(inv.id)
            elif inv.oc in costos:
                if round(float(inv.items_cost), 0) != round(costos[inv.oc], 0):
                    costo_diferente_ids.append(inv.id)
        InvoicesSiigo.objects.update(novelty=None)
        if sin_oc_ids:
            InvoicesSiigo.objects.filter(id__in=sin_oc_ids).update(novelty='factura sin oc relacionada')
        if oc_duplicada_ids:
            InvoicesSiigo.objects.filter(id__in=oc_duplicada_ids).update(novelty='oc duplicada')
        if costo_diferente_ids:
            InvoicesSiigo.objects.filter(id__in=costo_diferente_ids).update(novelty='costo diferente')
        InvoicesSiigo.objects.filter(novelty__isnull=True).update(novelty='Sin Novedad')

    def sync_siigo_to_db(self):
        print("Iniciando sincronización con Siigo...")

        invoices = self.get_monthly_invoices()

        if not invoices:
            print("No se encontraron facturas nuevas para procesar.")
            return
        return self.process_and_save_invoices(invoices)