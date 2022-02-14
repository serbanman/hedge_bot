import uuid

from django.db import models
from django.utils import timezone


class Operation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    position_id = models.ForeignKey(
        'main.Position',
        related_name='operations',
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )
    type = models.CharField(max_length=30, null=True, blank=True)
    text = models.TextField(max_length=300, null=True, blank=True)
    btc_quantity = models.DecimalField(max_digits=16, decimal_places=12, null=True, blank=True)
    btc_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)