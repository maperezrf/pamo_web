from django.db import models

class products_meli(models.Model):
    idShopi = models.CharField(max_length=20, null=False, blank=False) 
    idPublicationMeli = models.CharField(max_length=20, null=False, blank=False)
    title = models.CharField(max_length=300, null=True, blank=True)
    idVariantShopi = models.CharField(max_length=300, null=True, blank=True)
    pricePublication = models.FloatField(null=True, blank=True, default=0)    
    sku = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.title
    