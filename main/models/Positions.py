import uuid

from django.db import models
from django.utils import timezone


class Position(models.Model):
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'

    STATUSES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_CLOSED, 'Closed')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    preorder_id = models.ForeignKey(
        'main.Preorder',
        related_name='operations',
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )
    status = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        choices=STATUSES
    )
    btc_rate_in = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    btc_rate_out = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    btc_quantity = models.DecimalField(
        max_digits=16,
        decimal_places=12,
        null=True,
        blank=True
    )
    btc_total_comissions = models.DecimalField(
        max_digits=16,
        decimal_places=12,
        null=True,
        blank=True
    )
    comment = models.TextField(max_length=300, null=True, blank=True)