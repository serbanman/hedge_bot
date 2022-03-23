import uuid

from django.db import models
from django.utils import timezone

TYPE_BUY = 'buy'
TYPE_SELL = 'sell'

TYPES = [
    (TYPE_BUY, 'Buy'),
    (TYPE_SELL, 'Sell')
]

STATUS_FILLED = 'Filled'
STATUS_NEW = 'New'
STATUS_CANCELLED = 'Cancelled'

STATUSES = [
    (STATUS_FILLED, 'Filled'),
    (STATUS_NEW, 'New'),
    (STATUS_CANCELLED, 'Cancelled')
]


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    preorder = models.ForeignKey(
        'main.Preorder',
        related_name='operations',
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )
    order_id = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=30, null=True, blank=True, choices=TYPES)
    status = models.CharField(max_length=30, null=True, blank=True, choices=STATUSES)
    text = models.TextField(max_length=300, null=True, blank=True)
    sum_btc = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    sum_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    btc_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    usd_rate = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)

    def __str__(self):
        return '%s %s %s %s %s' % (self.created_at, self.sum_btc, self.price, self.type, self.status)

    class Meta:
        ordering = ['-created_at', 'preorder_id']
