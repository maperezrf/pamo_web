from decouple import config

ACCES_TOKEN = config("ACCES_TOKEN") 
URL_GRAPHQL = config("URL_GRAPHQL") 
URL_REST = config("URL_REST")
SECRET_KEY_DJANGO = config("SECRET_KEY")
DEBUG_VAR = config('DEBUG', cast=bool)

NAME_VAR = config("NAME")
USER_VAR=  config("USER")
PASSWORD_VAR = config("PASSWORD")
HOST_VAR = config("HOST")
PORT_VAR = config("PORT")

COLUMNS_SHOPI = ['N/A','Codigo barras','Costo','Precio','Precio comparación','Proveedor','SKU','Stock','Tags','Titulo']