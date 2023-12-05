from django.db import models

class ProductsSodimac(models.Model):

    SKU = models.CharField(max_length=50, null=True, blank=True)
    RF_pamo = models.CharField(max_length=50, null=True, blank=True)
    Indicador = models.CharField(max_length=100, null=True, blank=True)
    