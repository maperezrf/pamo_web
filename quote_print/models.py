from django.db import models

class Quote(models.Model):
    name = models.CharField(max_length=10, null=False, blank=False)
    customer = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateField(auto_now= False, null=False, blank=False)
    cursor = models.CharField(max_length=80, null=True, blank=True)
    total = models.IntegerField(False, null=False, blank=False ,default= 0 )

    def __str__(self) -> str:
        return self.name