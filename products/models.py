from django.db import models

class Products(models.Model):
    idShopi = models.CharField(max_length=20, null=False, blank=False, default = '') 
    title = models.CharField(max_length=300, null=True, blank=True)
    tags = models.CharField(max_length=500, null=True, blank=True)
    vendor = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    price = models.FloatField(null=True, blank=True, default=0)
    compareAtPrice =models.FloatField(null=True, blank=True, default=0)
    sku = models.CharField(max_length=100, null=True, blank=True)
    barcode = models.CharField(max_length=100, null=True, blank=True)
    inventoryQuantity = models.IntegerField(null=True, blank=True ,default= 0)
    cursor = models.CharField(max_length=80, null=True, blank=True)
    margen = models.FloatField(null=True, blank=True, default=0)
    costo = models.FloatField(null=True, blank=True, default=0)
    margen_comparacion_db = models.FloatField(null=True, blank=True, default=0)

    def __str__(self) -> str:
        return self.title
    
class SaveMargins(models.Model):
    margen = models.FloatField(null=True, blank=True, default=0)
    costo = models.FloatField(null=True, blank=True, default=0)
    margen_comparacion_db = models.FloatField(null=True, blank=True, default=0)