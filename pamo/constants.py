from decouple import config

# SHOPIFY
ACCES_TOKEN = config("ACCES_TOKEN") 
URL_GRAPHQL = config("URL_GRAPHQL") 
URL_REST = config("URL_REST")
SECRET_KEY_DJANGO = config("SECRET_KEY")
DEBUG_VAR = config('DEBUG', cast=bool)
URL_CREATE_ORDERS = config('URL_CREATE_ORDERS')

# SODIMAC
SUBSCRIPTION_KEY = config('SUBSCRIPTION_KEY') 
REFERENCIA_FPRN = config('REFERENCIA_FPRN')
ID_SODIMAC = config('ID_SODIMAC')
URL_SODIMAC = config('URL_SODIMAC')
URL_GET_INVENTARIO = config('URL_GET_INVENTARIO')
URL_SET_INVENTARIO = config('URL_SET_INVENTARIO')
URL_REINYECTAR_OC = config('URL_REINYECTAR_OC')

# DB
NAME_VAR = config("NAME")
USER_VAR=  config("USER")
PASSWORD_VAR = config("PASSWORD")
HOST_VAR = config("HOST")
PORT_VAR = config("PORT")

# OTHERS
COLUMNS_SHOPI = ['N/A','Codigo barras','Costo','Precio','Precio comparación','Proveedor','SKU','Stock','Tags','Titulo']

SALES_PHONE = config('SALES_PHONE')