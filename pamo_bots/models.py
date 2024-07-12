from django.db import models

class ProductsSodimac(models.Model):
    sku_sodimac = models.CharField(max_length=50, null=True, blank=True, unique=True)
    sku_pamo = models.CharField(max_length=50, null=True, blank=True, unique=True)
    ean = models.CharField(max_length=15, null=True, blank=True, unique=True)
    stock = models.IntegerField(null=True, blank=True ,default= 0)
    stock_sodi = models.IntegerField(null=True, blank=True ,default= 0)

class LogBotOrders(models.Model):
    date = models.DateTimeField(auto_now=True, blank=False, null=False)
    get_orders = models.BooleanField(blank=False, null=False)
    error = models.BooleanField(blank=False, null=False)
    log = models.CharField( max_length=700, blank=True, null=True)