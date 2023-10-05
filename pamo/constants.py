from decouple import config

ACCES_TOKEN = config("ACCES_TOKEN") 
URL_GRAPHQL = config("URL_GRAPHQL") 
URL_REST = config("URL_REST")
SECRET_KEY_DJANGO = config("SECRET_KEY")
DEBUG_VAR = config('DEBUG')
DATABASE_URL = config('DATABASE_URL')
