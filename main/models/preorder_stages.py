import uuid

from django.db import models
from django.utils import timezone


class PreorderStage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preorder = models.ForeignKey(
        'main.Preorder',
        related_name='stages',
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )

    status_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=60, null=True, blank=True)
    comment = models.CharField(max_length=60, null=True, blank=True)