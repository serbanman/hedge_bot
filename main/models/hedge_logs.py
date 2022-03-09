from django.db import models
from django.utils import timezone
import uuid


STATUS_SUCCESS = 'success'
STATUS_ERROR = 'error'

STATUSES = [
    (STATUS_SUCCESS, 'Success'),
    (STATUS_ERROR, 'Error')
]


class HedgeLog(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)

    preorder = models.ForeignKey(
        'main.Preorder',
        related_name='logs',
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )
    origin = models.TextField(max_length=30, null=True, blank=True)
    status = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        choices=STATUSES
    )
    text = models.TextField(max_length=300, null=True, blank=True)

    def __str__(self):
        return '%s, %s, %s %s' % (
            self.preorder.id if self.preorder else None,
            self.created_at, self.origin, self.status)

    class Meta:
        ordering = ['-created_at', 'origin']