import random
import uuid
import string

from django.db import models
from django.utils import timezone

from main.models.orders import TYPE_SELL, TYPE_BUY

STATUS_OPEN = 'open'
STATUS_CLOSED = 'closed'

STATUSES = [
    (STATUS_OPEN, 'Open'),
    (STATUS_CLOSED, 'Closed')
]


def get_random_id():
    letter = random.choice(string.ascii_lowercase)
    number = random.randint(1, 1000)

    rid = f"{letter}{number}"

    return rid

class Position(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    r_id = models.CharField(blank=True, max_length=10, default=get_random_id)
    created_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    preorder = models.ForeignKey(
        'main.Preorder',
        related_name='positions',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        choices=STATUSES
    )
    sum_btc = models.DecimalField(
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
        return '%s %s %s' % (self.created_at, self.sum_btc, self.status)

    @property
    def order_in(self):
        order_instance = self.orders.filter(type=TYPE_SELL).first()
        if order_instance:
            return order_instance.id
        else:
            return None

    @property
    def order_out(self):
        order_instance = self.orders.filter(type=TYPE_BUY).first()
        if order_instance:
            return order_instance.id
        else:
            return None

    @property
    def btc_price_in(self):
        order_instance = self.orders.filter(type=TYPE_SELL).first()
        if order_instance:
            return order_instance.price
        else:
            return None

    @property
    def btc_price_out(self):
        order_instance = self.orders.filter(type=TYPE_BUY).first()
        if order_instance:
            return order_instance.price
        else:
            return None

    @property
    def is_by_hand(self):
        if self.preorder:
            return False
        else:
            return True

    @property
    def h_preorder_id(self):
        if self.preorder:
            return self.preorder.preorder_id
        else:
            return None

    @property
    def preorder_sum_rub(self):
        if self.preorder:
            return self.preorder.sum_rub
        else:
            return None

    @property
    def is_preorder_garant(self):
        if self.preorder:
            return self.preorder.is_garant
        else:
            return None


    class Meta:
        ordering = ['-created_at', 'preorder_id']


















