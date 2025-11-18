from django.db import models

class OrdersFullfilment(models.Model):
    id = models.CharField(max_length=50, unique=True, primary_key=True)
    external_id = models.CharField(max_length=50, blank=True, null=True)
    ecomerce = models.CharField(max_length=50, blank=True, null=True)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    customer_email = models.CharField(max_length=200, blank=True, null=True)
    customer_phone = models.CharField(max_length=200, blank=True, null=True)