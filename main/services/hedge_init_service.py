from django.conf import settings
import bybit
import time
from main.models.hedge_logs import STATUS_SUCCESS, STATUS_ERROR
from main.services.hedge_logger import HedgeLogger


class HedgeInitService(HedgeLogger):
    def __init__(self, preorder_id=None, test=True):
        super().__init__(preorder_id)

        self._api_key = getattr(settings, 'BYBIT_API', None)
        self._api_secret = getattr(settings, 'BYBIT_SECRET', None)
        self._test = test

        self.client = self._connect()

    def _connect(self):
        INIT_CONNECT_RETRY_COUNTER = 5
        init_connect_counter = 0
        while init_connect_counter < INIT_CONNECT_RETRY_COUNTER:
            try:
                client = bybit.bybit(
                    test=self._test,
                    api_key=self._api_key,
                    api_secret=self._api_secret
                )
                self.log(
                    origin="Init connection",
                    status=STATUS_SUCCESS,
                    text=f"On {init_connect_counter} try"
                )
                return client
            except Exception as ex:
                init_connect_counter += 1
                time.sleep(5)
                self.log(
                    origin="Init connection",
                    status=STATUS_ERROR,
                    text=f"OperationsService init connection error: "
                         f"{ex}, "
                         f"retries: {init_connect_counter}"
                )
        return None
