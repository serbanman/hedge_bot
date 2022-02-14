from celery import shared_task
from django.conf import settings
import pybit

@shared_task(bind=True)
def test_print(self):
    request = pybit.HTTP(getattr(settings, 'BYBIT_ROOT', None))
    print("Hello!")