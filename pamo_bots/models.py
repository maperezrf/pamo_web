from django.db import models

class ProductsSodimac(models.Model):
    SKU = models.CharField(max_length=50, null=True, blank=True)
    RF_pamo = models.CharField(max_length=50, null=True, blank=True)
    Indicador = models.CharField(max_length=100, null=True, blank=True)
    cod_barras = models.CharField(max_length=15, null=True, blank=True)
    stock = models.IntegerField(null=True, blank=True ,default= 0)

class LogBotOrders(models.Model):
    date = models.DateTimeField(auto_now=True, blank=False, null=False)
    get_orders = models.BooleanField(blank=False, null=False)
    error = models.BooleanField(blank=False, null=False)
    log = models.CharField( max_length=700, blank=True, null=True)