from pamo.constants import *
import requests
import pandas as pd
import json
from io import StringIO
from pamo_bots.models import ProductsSodimac
from quote_print.models import SodimacKits, SodimacOrders
import time
from dateutil import parser as dateutil_parser

class ConnectionsSodimac():

    headers = {}
    orders = pd.DataFrame()

    def __init__(self) -> None:
        self.headers = {"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,"Content-Type": "application/json"}
    
    def _fetch_raw_orders(self, tipo_orden="1"):
        """Helper: llama al API y retorna la lista cruda de órdenes, o [] si no hay datos."""
        data = {"ReferenciaProveedor": REFERENCIA_FPRN, "TipoOrden": tipo_orden}
        response = requests.post(URL_SODIMAC, headers=self.headers, json=data)
        msg = response.json().get('Mensaje', '')
        if msg == 'Sentencia ejecutada con éxito.':
            print(f"se encontraron {len(response.json()['Value'])} ordenes (TipoOrden={tipo_orden})")
            return response.json()['Value']
        return []

    def get_orders_api(self, tipo_orden="1"):
        raw = self._fetch_raw_orders(tipo_orden)
        if not raw:
            return False
        ordenes = []
        for orden in raw:
            obj, _ = SodimacOrders.objects.get_or_create(id=str(orden['ORDEN_COMPRA']))
            obj.total_cost = orden.get('COSTO_TOT_OC')
            obj.last_status = orden.get('ESTADO_OC')
            fecha_raw = orden.get('FECHA_TRANSMISION')
            obj.fecha_transmision = dateutil_parser.parse(fecha_raw, dayfirst=True).date()
            obj.save()
            for producto in orden['PRODUCTOS']:
                ordenes.append([orden['ORDEN_COMPRA'], orden['ESTADO_OC'], orden['FECHA_TRANSMISION'], producto['SKU'], producto['CANTIDAD_SKU'], producto['COSTO_SKU']])
        df_nuevas = pd.DataFrame(ordenes, columns=['ORDEN_COMPRA', 'ESTADO_OC', 'FECHA_TRANSMISION', 'SKU', 'CANTIDAD_SKU', 'COSTO_SKU'])
        df_nuevas['COSTO_SKU_IVA'] = df_nuevas['COSTO_SKU'] * 1.19
        self.orders = pd.concat([self.orders, df_nuevas], ignore_index=True)
        print(self.orders)
        return True

    def get_oc_costs(self, ocs):
        """Reinyecta OCs y retorna [{oc, costo_total}] con el COSTO_TOT_OC directo del API."""
        if ocs:
            self.reinyectar_oc(ocs)
        costs = []
        for tipo in ["1", "4"]:
            for orden in self._fetch_raw_orders(tipo):
                costs.append({
                    'oc': str(orden['ORDEN_COMPRA']),
                    'costo_total': orden['COSTO_TOT_OC']
                })
        return costs
            
    def make_merge(self):
        skus_objects = ProductsSodimac.objects.all()
        skus =  pd.DataFrame(list(skus_objects.values()))
        skus.drop_duplicates('sku_sodimac', inplace=True)
        self.orders['SKU'] = self.orders['SKU'].apply(lambda x:x.strip())
        self.orders = self.orders.merge(skus, how='left', left_on='SKU', right_on='sku_sodimac')
        self.orders.loc[self.orders['sku_pamo'].notna(), 'SKU'] =  self.orders.loc[self.orders['sku_pamo'].notna(), 'sku_pamo']
    
    def set_kits(self):
        skus_kits = pd.DataFrame(SodimacKits.objects.all().values())
        self.orders = self.orders.merge(skus_kits, how='left', left_on='SKU',right_on='kitnumber')
        self.orders.loc[self.orders['kitnumber'].notna(), ['SKU', 'CANTIDAD_SKU']] = self.orders.loc[self.orders['kitnumber'].notna(), ['sku','quantity']]
        gb = self.orders.groupby(['ORDEN_COMPRA','kitnumber', 'COSTO_SKU']).agg({'quantity':'sum'}).reset_index()
        gb['COSTO_SKU'] = gb['COSTO_SKU'] / gb['quantity']
        self.orders = self.orders.merge(gb, how='left', on='ORDEN_COMPRA')
        self.orders.loc[self.orders['COSTO_SKU_y'].notna(),'COSTO_SKU_x'] = self.orders.loc[self.orders['COSTO_SKU_y'].notna(),'COSTO_SKU_y'].values
        self.orders.rename(columns= {'COSTO_SKU_x':'COSTO_SKU'}, inplace=True)
        print(self.orders)

    def get_orders(self):
        return self.orders
    
    def get_inventory(self):
        products = ProductsSodimac.objects.exclude(cod_barras='')
        df_products = pd.DataFrame.from_records(products.values())
        df_products.loc[df_products['Indicador'] == 'KIT', 'RF_pamo'] = df_products.loc[df_products['Indicador'] == 'KIT', 'SKU'] 
        stock_list = []
        for i in range(df_products.shape[0]):
            if df_products.iloc[i].cod_barras != '':    
                response = self.request_inventory_api(df_products.iloc[i].cod_barras)
                try:
                    dic = {}
                    dic['codigo_barras'] = df_products.iloc[i].cod_barras
                    dic['stock_sodimac'] = response[0]['EXISTENCIA']
                    dic['sku'] = df_products.iloc[i].RF_pamo
                    stock_list.append(dic)
                except:
                    pass    
        return pd.DataFrame(stock_list)

    def set_inventory(self, df):
        data = self.get_data_inventory(df)
        for i in data:
            response_get_inventory = self.request_inventory_api(i['ean'])
            if len(response_get_inventory) > 0 :
                response = requests.post(URL_SET_INVENTARIO, headers = self.headers, json=[i]).json()
                print(response)
                data = {'success':True, "message":"Actializacion exitosa"}
            else:
                data = {'success':False, "message":"No se encontró ningun producto con el Ean proporcionado"}
        return data

    def get_data_inventory(self, df):
        data_list = []
        for i in range(df.shape[0]):
            dic = {}
            dic["proveedor"] = REFERENCIA_FPRN
            dic["ean"] = df.iloc[i].ean
            dic["inventarioDispo"] = df.iloc[i].stock
            dic["stockMinimo"] = 0
            dic["canal"] = "Bogota"
            dic["usuario"] = "Bot"
            data_list.append(dic)
        return data_list

    def get_inventario(self, ean_list):
        responses_list = []
        for i in ean_list:
            response = self.request_inventory_api(i)
            print(response)
            if len(response) == 0:
                responses_list.append({'success':False, 'ean': i, "message":"No se encontró ningun producto con el Ean proporcionado" })
            else:
                item = ProductsSodimac.objects.get(ean = i)
                item.stock_sodi = response[0]['EXISTENCIA']
                item.save()
                responses_list.append({'success':True, 'ean': i, "message":"Se actualizo correctamente el stock en la base de datos" })
        return responses_list
    
    def get_multiple_inventory(self, products):
        pass
    
    def request_inventory_api(self, ean):
            data = {
            "proveedor": REFERENCIA_FPRN,
            "ean": ean[0:12]
            }
            response = requests.post(URL_GET_INVENTARIO, headers = self.headers, json=data).json()
            return response

    def reinyectar_oc(self, orders):
        try:
            for i in orders:
                data = {
                "ReferenciaProveedor": REFERENCIA_FPRN,
                "PMG_PO_NUMBER": i
                }
                
                response = requests.post(URL_REINYECTAR_OC, headers = self.headers, json=data)
                if response.json()['Value'][0]['DESCRIPCION'] == 'TRANSACCION EXITOSA':
                    print(f"orden {i} reinyectada")
                else:
                    print(f"error al reinyectar orden {i}")
        except:
            print('Ocurrio un error')
        