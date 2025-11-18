import requests

url = "https://pamoweb-production.up.railway.app/orders_api/data_orders/"

payload = {}
headers = {}

response = requests.request("GET", url, headers=headers, data=payload)