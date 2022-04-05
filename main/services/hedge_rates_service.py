import time
import requests
from main.models.hedge_logs import STATUS_SUCCESS, STATUS_ERROR
from main.services.hedge_init_service import HedgeInitService


class HedgeRatesService(HedgeInitService):
    def __init__(self, preorder_id=None):
        super().__init__(preorder_id)

    def get_btc_usdt_rate(self):
        RETRY_COUNTER = 10
        counter = 0
        rate = float('inf')
        try:
            while counter < RETRY_COUNTER:
                gross_data = self.client.LinearKline.LinearKline_get(
                        symbol="BTCUSDT",
                        interval="1",
                        limit=1,
                        **{'from': time.time()-60}
                    ).result()
                if gross_data[0]['ret_msg'] == 'OK' and len(gross_data[0]['result']) > 0:
                    rate = float(gross_data[0]['result'][-1]['close'])
                    # self.log(
                    #     origin="get_btc_usd_rate",
                    #     status=STATUS_SUCCESS,
                    #     text=f'On {counter} try, rate: {rate}'
                    # )
                    break
                elif gross_data[0]['ret_msg'] == 'OK' and len(gross_data[0]['result']) == 0:
                    self.log(
                        origin="get_btc_usd_rate",
                        status=STATUS_ERROR,
                        text=f"Query is empty on {counter} try. Gross data: {gross_data}"
                    )
                    counter += 1
                    time.sleep(5)
                elif gross_data[0]['ret_msg'] != 'OK':
                    self.log(
                        origin="get_btc_usd_rate",
                        status=STATUS_ERROR,
                        text=f"ret_msg is not OK on {counter} try. Gross data: {gross_data}"
                    )
                    counter += 1
                    time.sleep(5)
                else:
                    self.log(
                        origin="get_btc_usd_rate",
                        status=STATUS_ERROR,
                        text=f"Other case; didn't get rate in {counter} try. Gross data: {gross_data}"
                    )
                    counter += 1
                    time.sleep(5)
        except Exception as ex:
            self.log(
                origin="get_btc_usd_rate",
                status=STATUS_ERROR,
                text=f"GOT EXCEPTION IN get_btc_usd_rate: {ex}"
            )

        return rate

    def get_usd_rub_rate(self):
        rate = float('inf')
        try:
            data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
            rate = data['Valute']['USD']['Value']
        except Exception as ex:
            self.log(
                origin="usd_rub rate",
                status=STATUS_ERROR,
                text=f"Didn't get proper rates: {ex}; rub {rate}"
            )
        return rate
