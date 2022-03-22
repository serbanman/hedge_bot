import time

import bybit
from celery import shared_task
from django.conf import settings

from hedge.main.models import HedgeLog
from hedge.main.models.hedge_logs import STATUS_ERROR, STATUS_SUCCESS


class MarketHandler:
    def __init__(self, test=True):
        self._api_key = getattr(settings, 'BYBIT_API', None)
        self._api_secret = getattr(settings, 'BYBIT_SECRET', None)

        self.INIT_CONNECT_RETRY_COUNTER = 5
        self.init_connect_counter = 0
        while self.init_connect_counter < self.INIT_CONNECT_RETRY_COUNTER:
            try:
                self.client = bybit.bybit(
                    test=test,
                    api_key=self._api_key,
                    api_secret=self._api_secret
                )
                log = HedgeLog(
                    preorder=self.preorder_instance,
                    origin="OperationsService init connection",
                    status=STATUS_SUCCESS,
                    text=f"On {self.init_connect_counter} try"
                )
                log.save()
                break
            except Exception as ex:
                self.init_connect_counter += 1
                time.sleep(5)
                log = HedgeLog(
                    preorder=self.preorder_instance,
                    origin="OperationsService init connection",
                    status=STATUS_ERROR,
                    text=f"OperationsService init connection error: "
                         f"{ex}, "
                         f"retries: {self.init_connect_counter}"
                )
                log.save()