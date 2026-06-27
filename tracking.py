import requests

print('se incia desde el bot')

url = 'https://pamoweb-production.up.railway.app/pamo_bots/get_status_shippments'
response = requests.get(url)

if response.status_code == 200:
    print(f"Solicitud GET exitosa: {response.text}")

else:
    print(f"Error al enviar solicitud GET: {response.status_code}")