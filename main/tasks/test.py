from celery import shared_task
from django.conf import settings
from ..services.operations_service import OperationsService
import pybit

@shared_task(bind=True)
def test_print(self):
    # request = pybit.HTTP(getattr(settings, 'BYBIT_ROOT', None))
    # print("Hello!")
    service = OperationsService()
    rate = service.get_btc_usdt_rate()
    print(f'*** RATE: {rate}')