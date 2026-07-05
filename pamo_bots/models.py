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

class LastCursor(models.Model):
    cursor = models.CharField(max_length=100, null=True, blank=True)

class OrdersShopify(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    pedido = models.CharField(max_length=20)
    created_at = models.DateTimeField()
    payment_method = models.CharField(max_length=100, null=True, blank=True)
    customer_name = models.CharField(max_length=200, null=True, blank=True)
    customer_id = models.CharField(max_length=50, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)
    order_is_cancelled = models.BooleanField(blank=False, null=False, default=False)
   
class TrakingOrders(models.Model):
    order = models.ForeignKey(OrdersShopify, on_delete=models.CASCADE, related_name='traking')
    tracking_number = models.CharField(max_length=60, null=True, blank=True)
    url_traking = models.CharField(max_length=150, null=True, blank=True)
    tracking_status = models.CharField(max_length=20, null=True, blank=True)
    in_transit = models.BooleanField(default=False)
    shipping_company = models.CharField(max_length=60, null=True, blank=True)
    comments = models.CharField(max_length=100, null=True, blank=True)

class ProductsOrders(models.Model):
    order = models.ForeignKey(OrdersShopify, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    quantity = models.IntegerField()
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)

class InvoicesSiigo(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    date = models.DateField()
    total = models.DecimalField(max_digits=15, decimal_places=2)
    items_cost = models.DecimalField(max_digits=15, decimal_places=2)
    oc = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    novelty = models.CharField(max_length=100, null=True, blank=True)
    seller = models.CharField(max_length=50, null=True, blank=True)

