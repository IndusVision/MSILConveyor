from django.db import models

# Create your models here.

class Reports(models.Model):
    recorded_date_time =models.CharField(max_length=100)
    order_number = models.BigIntegerField()
    clp_number= models.BigIntegerField()
    status = models.BooleanField()