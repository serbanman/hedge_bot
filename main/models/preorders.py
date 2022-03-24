import uuid

from django.db import models
from django.utils import timezone


class Preorder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preorder_id = models.IntegerField(unique=True, null=False, blank=False)

    created_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    sum_rub = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sum_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sum_btc = models.DecimalField(max_digits=16, decimal_places=12, null=True, blank=True)

    buyer = models.CharField(max_length=30, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    order_date = models.DateTimeField(null=True, blank=True)
    # product_id = models.ForeignKey()
    # responsible = models.ForeignKey()
    product_name = models.CharField(max_length=100, null=True, blank=True)
    size = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=60, null=True, blank=True)
    is_garant = models.BooleanField(null=True, blank=True)
    garant_status = models.CharField(max_length=60, null=True, blank=True)

    def __str__(self):
        return '%s %s %s' % (self.created_at, self.sum_rub, self.buyer)

    class Meta:
        ordering = ['-created_at', 'buyer']
