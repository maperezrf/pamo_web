from django.db import models

class Quote(models.Model):
    name = models.CharField(max_length=10, null=False, blank=False)
    customer = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateField(auto_now= False, null=False, blank=False)
    seller = models.CharField(max_length=50, null=True, blank=True)
    cursor = models.CharField(max_length=80, null=True, blank=True)
    total = models.IntegerField(False, null=False, blank=False ,default= 0 )
    nit = models.CharField(max_length=25, null=True, blank=True)

    def __str__(self) -> str:
        return self.name
    
class SigoToken(models.Model):
    token =  models.CharField(max_length=1400, null=False, blank=False)
    date_expired = models.DateTimeField()

class SigoCostumers(models.Model):
    id = models.CharField(max_length=40, primary_key=True)
    identification = models.CharField(max_length=40, null=False, blank=False)

class SodimacOrders(models.Model):
    id = models.CharField(max_length=40, primary_key=True)
    status = models.CharField(max_length=20, default= '1-PENDIENTE')
    factura = models.CharField(max_length=20, null=True, blank=True)
    novelty = models.CharField(max_length=200, null=True, blank=True)
    date_invoice = models.DateField(blank=True, null=True)
 
class SodimacKits(models.Model):
    kitnumber = models.CharField(max_length=50,null=False, blank=False)
    sku = models.CharField(max_length=50,null=False, blank=False)
    quantity = models.IntegerField(null=False, blank=False ,default= 0 )
