from django.db import models

# Create your models here.



class Reports(models.Model):
    recorded_date_time =models.CharField(max_length=100)
    order_number = models.BigIntegerField()
    clp_number= models.BigIntegerField()
    status = models.BooleanField()
    

class ExpectedCount(models.Model):
    class Meta:
        db_table = "ExpectedCount"
    
    expected_count = models.BigIntegerField(null=True)


class ExpectedData(models.Model):
    class Meta:
        db_table = "ExpectedData"
    order_number = models.CharField(max_length=100,blank=True,null=True)
    clp_number = models.CharField(max_length=100,blank=True,null=True)