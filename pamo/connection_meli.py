import webbrowser
from constants import APP_ID, CLIENT_SECRET, URL_REDIRECT, URL_GET_TOKEN
import requests

class connMeli():
    headers = {
    'accept': 'application/json',
    'content-type': 'application/x-www-form-urlencoded'
    }
             
    def get_code (self):
        auth_url = f"https://auth.mercadolibre.com.co/authorization?response_type=code&client_id={APP_ID}&redirect_uri={URL_REDIRECT}"
        webbrowser.open(auth_url)
    
    def change_code(self, code, new):
        # introducir tg refresh
        payload = {
                'grant_type':'authorization_code',
                'client_id':APP_ID,
                'client_secret':CLIENT_SECRET,
                }
        if new:
            payload['grant_type'] ='authorization_code'    
            payload['redirect_uri'] = URL_REDIRECT
            payload['code'] = code
        else:
            payload['grant_type']='refresh_token'
            payload['refresh_token']=code
        response = requests.request("POST", URL_GET_TOKEN, headers=self.headers, data=payload)
        return response