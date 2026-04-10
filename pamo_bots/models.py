from django.db import models

class ProductsSodimac(models.Model):
    sku_sodimac = models.CharField(max_length=50, null=True, blank=True, unique=True)
    sku_pamo = models.CharField(max_length=100, null=True, blank=True, unique=False)
    ean = models.CharField(max_length=15, null=True, blank=True, unique=False)
    stock = models.IntegerField(null=True, blank=True ,default= 0)
    stock_sodi = models.IntegerField(null=True, blank=True ,default= 0)

class LogBotOrders(models.Model):
    date = models.DateTimeField(auto_now=True, blank=False, null=False)
    get_orders = models.BooleanField(blank=False, null=False)
    error = models.BooleanField(blank=False, null=False)
    log = models.CharField( max_length=700, blank=True, null=True)

class InvoicesSiigo(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    date = models.DateField()
    total = models.DecimalField(max_digits=15, decimal_places=2)
    items_cost = models.DecimalField(max_digits=15, decimal_places=2)
    oc = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    novelty = models.CharField(max_length=100, null=True, blank=True)

