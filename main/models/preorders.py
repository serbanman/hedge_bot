import uuid

from django.db import models
from django.utils import timezone


class Preorder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preorder_id = models.IntegerField(unique=True, null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)
    sum_rub = models.DecimalField(max_digits=12, decimal_places=2)
    sum_btc = models.DecimalField(max_digits=16, decimal_places=12, null=True, blank=True)
    buyer = models.CharField(max_length=30, null=True, blank=True)
    finishing_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '%s %s %s' % (self.created_at, self.sum_rub, self.buyer)

    class Meta:
        ordering = ['-created_at', 'buyer']
