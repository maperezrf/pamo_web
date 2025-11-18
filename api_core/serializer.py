from rest_framework import serializers
from api_core.models import OrdersFullfilment

class OrdersFullfilmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrdersFullfilment
        fields = "__all__"
