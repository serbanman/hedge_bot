import uuid

from django.db import models
from django.utils import timezone


STATUS_OPEN = 'open'
STATUS_CLOSED = 'closed'

STATUSES = [
    (STATUS_OPEN, 'Open'),
    (STATUS_CLOSED, 'Closed')
]


class Position(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    preorder = models.ForeignKey(
        'main.Preorder',
        related_name='positions',
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
    order_in = models.ForeignKey(
        'main.Order',
        related_name='position_in',
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )
    btc_price_in = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    order_out = models.ForeignKey(
        'main.Order',
        related_name='position_out',
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )
    btc_price_out = models.DecimalField(
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

    def __str__(self):
        return '%s %s %s' % (self.created_at, self.btc_quantity, self.status)

    class Meta:
        ordering = ['-created_at', 'preorder_id']