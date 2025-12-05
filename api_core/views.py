from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api_core.serializer import OrdersFullfilmentSerializer
from api_core.models import OrdersFullfilment
from pamo.constants import TOKEN_ENVIA, URL_ENVIA
import requests

class Orders(APIView):

    def get(self, request): #TODO aqui se debe refactorizar, la idea es sacar la logica de obtener los datos y que devuelva solo el listado de los productos, hacer un solo bulk_create
        url = f"{URL_ENVIA}/orders?limit=300&page=1"
        payload = {}
        headers = {
        'timezone': 'America/Bogota',
        'Authorization': TOKEN_ENVIA
        }
        OrdersFullfilment.objects.all().delete()
        try:
            response = requests.request("GET", url, headers=headers, data=payload)
            flag= True
            page = 1
            if response.status_code == 200:
                while flag:
                    if page < 4:
                        items = response.json()
                        list_items = []
                        for item in items.get('orders', {}):
                            data_dic = {}
                            data_dic['id'] = item['orderId']
                            data_dic['external_id'] = item['identifier']
                            data_dic['ecomerce'] = item['ecommerce']
                            data_dic['customer_name'] = item['customer']['name']
                            data_dic['customer_email'] = item['customer']['name']
                            data_dic['customer_phone'] = item['customer']['phone']
                            list_items.append(data_dic)
                        serializer = OrdersFullfilmentSerializer(data = list_items, many = True)
                        if serializer.is_valid():
                            data = serializer.validated_data
                            objs = [OrdersFullfilment(**d) for d in data ] 
                            OrdersFullfilment.objects.bulk_create(objs, ignore_conflicts=True)
                        else:
                            raise(serializer.errors)
                        page+=1
                        response = requests.request("GET",  f"{URL_ENVIA}/orders?limit=300&page={page}", headers=headers, data=payload)
                    else:
                        flag = False
            else:
                raise('Error al obtener ordenes')
        except Exception as e:
            raise(e)
        return Response(status=status.HTTP_200_OK)

class OrderInfo(APIView):

    def get(self, request):
        id_obj = request.query_params['id']
        print(f'Se recibe la solicitud con el id {id_obj}')
        obj = self.get_object(id_obj)
        if obj:
            print('Se encontro el id en la base de datos')
            detail = self.get_order_details(obj)
            return  Response(data={'data':detail}, status=status.HTTP_200_OK)
        else:
            print("No se encontro nada")
            return Response(data={'message':'No se encontró el numero de pedido'}, status=status.HTTP_404_NOT_FOUND)

    def get_object(self, id_obj):
        obj = OrdersFullfilment.objects.filter(external_id = id_obj)
        if obj.exists():
            return obj.first()
        else:
            return False
    
    def get_order_details(self, id_obj):
        url =  f"{URL_ENVIA}/order/detail/{id_obj.id}"
        payload = {}
        headers = {
        'timezone': 'America/Bogota',
        'Authorization': TOKEN_ENVIA
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        print("Respuesta Envia")
        print(response)
        return response.json()

