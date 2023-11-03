from django.db import models

class Products(models.Model):

    title = models.CharField(max_length=100, null=True, blank=True)
    tags = models.CharField(max_length=500, null=False, blank=False)
    vendor = models.CharField(max_length=100, null=True, blank=True)
    price = models.IntegerField(False, null=False, blank=False ,default= 0)
    compareAtPrice =models.IntegerField(False, null=False, blank=False ,default= 0)
    sku = models.CharField(max_length=100, null=True, blank=True)
    barcode = models.CharField(max_length=100, null=True, blank=True)
    inventoryQuantity = models.IntegerField(False, null=False, blank=False ,default= 0)
    cursor = models.CharField(max_length=80, null=True, blank=True)
    
    def __str__(self) -> str:
        return self.title