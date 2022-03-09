from django.conf import settings
import bybit
import time
import requests
from ..models import HedgeLog, Order, Preorder, Position
from ..models.hedge_logs import STATUS_SUCCESS, STATUS_ERROR
from ..models.orders import TYPE_BUY, TYPE_SELL, STATUS_FILLED, STATUS_NEW, STATUS_CANCELLED


class OperationsService:
    SPREAD = 1

    def __init__(self, preorder_id, test=True):
        try:
            self.preorder_instance = Preorder.objects.get(id=preorder_id)
        except Exception as ex:
            self.preorder_instance = None
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="OperationsService init instance",
                status=STATUS_ERROR,
                text=f"ex {ex}"
            )
            log.save()
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
                log = HedgeLog(
                    preorder=self.preorder_instance,
                    origin="OperationsService init connection",
                    status=STATUS_ERROR,
                    text=f"OperationsService init connection error: "
                         f"{ex}, "
                         f"retries: {self.init_connect_counter}"
                )
                log.save()

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
                    log = HedgeLog(
                        preorder=self.preorder_instance,
                        origin="get_btc_usd_rate",
                        status=STATUS_SUCCESS,
                        text=f'On {counter} try, rate: {rate}'
                    )
                    log.save()
                    break
                elif gross_data[0]['ret_msg'] == 'OK' and len(gross_data[0]['result']) == 0:
                    log = HedgeLog(
                        preorder=self.preorder_instance,
                        origin="get_btc_usd_rate",
                        status=STATUS_ERROR,
                        text=f"Query is empty on {counter} try. Gross data: {gross_data}"
                    )
                    log.save()
                    counter += 1
                elif gross_data[0]['ret_msg'] != 'OK':
                    log = HedgeLog(
                        preorder=self.preorder_instance,
                        origin="get_btc_usd_rate",
                        status=STATUS_ERROR,
                        text=f"ret_msg is not OK on {counter} try. Gross data: {gross_data}"
                    )
                    log.save()
                    counter += 1
                else:
                    log = HedgeLog(
                        preorder=self.preorder_instance,
                        origin="get_btc_usd_rate",
                        status=STATUS_ERROR,
                        text=f"Other case; didn't get rate in {counter} try. Gross data: {gross_data}"
                    )
                    log.save()
                    counter += 1
        except Exception as ex:
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="get_btc_usd_date",
                status=STATUS_ERROR,
                text=f"GOT EXCEPTION IN get_btc_usd_date: {ex}"
            )
            log.save()

        return rate

    def get_usd_rub_rate(self):
        rate = float('inf')
        try:
            data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
            rate = data['Valute']['USD']['Value']
        except Exception as ex:
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="usd_rub rate",
                status=STATUS_ERROR,
                text=f"Didn't get proper rates: {ex}; rub {rate}"
            )
            log.save()

        return rate

    def create_sell_order(self, sum_rub: float, preorder_id: str = None):  # sell order == buy short
        rate_btc_usdt = self.get_btc_usdt_rate()
        rate_usd_rub = self.get_usd_rub_rate()
        if rate_usd_rub == float('inf') or rate_btc_usdt == float('inf'):
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="create_sell_order stage rates",
                status=STATUS_ERROR,
                text=f"Didn't get proper rates: btc {rate_btc_usdt}; rub {rate_usd_rub}"
            )
            log.save()
            return
        else:
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="create_sell_order stage rates",
                status=STATUS_SUCCESS,
                text=f"Got rates: btc {rate_btc_usdt}; rub {rate_usd_rub}"
            )
            log.save()

        sum_usd = float(sum_rub) / rate_usd_rub
        btc_qty = '%.3f' % (sum_usd / rate_btc_usdt)
        try:
            RETRY_COUNT = 5
            counter = 0
            while counter < RETRY_COUNT:
                new_order_gross_data = self.client.LinearOrder.LinearOrder_new(
                    side="Sell",
                    symbol="BTCUSDT",
                    order_type="Limit",
                    qty=btc_qty,
                    price=rate_btc_usdt - self.SPREAD,
                    time_in_force="GoodTillCancel",
                    reduce_only=False,  # True for closing
                    close_on_trigger=False
                ).result()
                order_id = ''
                if new_order_gross_data[0]['ret_msg'] == 'OK' and new_order_gross_data[0]['result']:
                    order_id = new_order_gross_data[0]['result']['order_id']
                    if preorder_id:
                        preorder_instance = Preorder.objects.get(id=preorder_id)
                    else:
                        preorder_instance = None
                    new_order = Order(
                        preorder=preorder_instance,
                        order_id=order_id,
                        type=TYPE_SELL,
                        btc_quantity=btc_qty,
                        price=rate_btc_usdt - self.SPREAD,
                        btc_rate=rate_btc_usdt,
                        usd_rate=rate_usd_rub
                    )
                    new_order.save()

                    log = HedgeLog(
                        preorder=self.preorder_instance,
                        origin="create_sell_order stage order",
                        status=STATUS_SUCCESS,
                        text=f"OK data: {new_order_gross_data}. New order id: {new_order.id}, count: {counter}"
                    )
                    log.save()
                    return new_order.id
                else:
                    log = HedgeLog(
                        preorder=self.preorder_instance,
                        origin="create_sell_order stage order",
                        status=STATUS_ERROR,
                        text=f"Not OK data: {new_order_gross_data}, count: {counter}"
                    )
                    log.save()
                    counter += 1
                    time.sleep(5)
            return None
        except Exception as ex:
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="create_sell_order stage order",
                status=STATUS_ERROR,
                text=f"Error, exception: {ex}"
            )
            log.save()
            return None

    def create_buy_order(self, preorder_id: str, position_id: str):
        preorder_instance = Preorder.objects.get(id=preorder_id)
        position_instance = Position.objects.get(id=position_id)
        rate_btc_usdt = self.get_btc_usdt_rate()
        if rate_btc_usdt == float('inf'):
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="create_buy_order stage rates",
                status=STATUS_ERROR,
                text=f"Didn't get proper rates: btc {rate_btc_usdt}; preorder_id: {preorder_id}"
            )
            log.save()
            return
        else:
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="create_buy_order stage rates",
                status=STATUS_SUCCESS,
                text=f"Got rates: btc {rate_btc_usdt}; preorder_id: {preorder_id}"
            )
            log.save()
        btc_qty = position_instance.btc_quantity
        try:
            RETRY_COUNT = 5
            counter = 0
            while counter < RETRY_COUNT:
                new_order_gross_data = self.client.LinearOrder.LinearOrder_new(
                    side="Buy",
                    symbol="BTCUSDT",
                    order_type="Limit",
                    qty=btc_qty,
                    price=rate_btc_usdt + self.SPREAD,
                    time_in_force="GoodTillCancel",
                    reduce_only=True,  # True for closing
                    close_on_trigger=False
                ).result()
                order_id = ''
                if new_order_gross_data[0]['ret_msg'] == 'OK' and new_order_gross_data[0]['result']:
                    order_id = new_order_gross_data[0]['result']['order_id']
                    new_order = Order(
                        preorder=preorder_instance,
                        order_id=order_id,
                        type=TYPE_BUY,
                        btc_quantity=btc_qty,
                        price=rate_btc_usdt + self.SPREAD,
                        btc_rate=rate_btc_usdt
                    )
                    new_order.save()

                    log = HedgeLog(
                        preorder=self.preorder_instance,
                        origin="create_buy_order stage order",
                        status=STATUS_SUCCESS,
                        text=f"OK data: {new_order_gross_data}. New order id: {new_order.id}, count: {counter}"
                    )
                    log.save()
                    return new_order.id
                else:
                    log = HedgeLog(
                        preorder=self.preorder_instance,
                        origin="create_buy_order stage order",
                        status=STATUS_ERROR,
                        text=f"Not OK data: {new_order_gross_data}, count: {counter}"
                    )
                    log.save()
                    counter += 1
                    time.sleep(5)
            return None
        except Exception as ex:
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="create_buy_order stage order",
                status=STATUS_ERROR,
                text=f"Error, exception: {ex}"
            )
            log.save()
            return None

    def is_order_filled(self, order_id):
        try:
            orders_gross_data = self.client.\
                LinearOrder.\
                LinearOrder_query(
                symbol="BTCUSDT", order_id=order_id
            ).result()
            if orders_gross_data[0]['ret_msg'] == 'OK':
                order_data = orders_gross_data[0]['result']
                if order_data['order_status'] in [
                    STATUS_FILLED,
                    STATUS_CANCELLED,
                    STATUS_NEW
                ]:
                    order_instance = Order.objects.get(order_id=order_id)
                    order_instance.status = order_data['order_status']
                    order_instance.save()

                    if order_data['order_status'] == STATUS_FILLED:
                        log = HedgeLog(
                            preorder=self.preorder_instance,
                            origin="is_order_filled status found",
                            status=STATUS_SUCCESS,
                            text=f"Found status: {order_data['order_status']}; order_id: {order_id}"
                        )
                        log.save()
                        return True
                    else:
                        log = HedgeLog(
                            preorder=self.preorder_instance,
                            origin="is_order_filled status found",
                            status=STATUS_ERROR,
                            text=f"Found status: {order_data['order_status']}; order_id: {order_id}"
                        )
                        log.save()
                        return False

                else:
                    log = HedgeLog(
                        preorder=self.preorder_instance,
                        origin="is_order_filled",
                        status=STATUS_ERROR,
                        text=f"Ambiguous status: {order_data['order_status']}; order_id: {order_id}"
                    )
                    log.save()

            elif orders_gross_data[0]['ret_msg'] == 'Order not exists':
                log = HedgeLog(
                    preorder=self.preorder_instance,
                    origin="is_order_filled",
                    status=STATUS_ERROR,
                    text=f"Order not exists: {orders_gross_data}; order_id: {order_id}"
                )
                log.save()
            else:
                log = HedgeLog(
                    preorder=self.preorder_instance,
                    origin="is_order_filled",
                    status=STATUS_ERROR,
                    text=f"Else Response is not OK: {orders_gross_data}; order_id: {order_id}"
                )
                log.save()
            return None
        except Exception as ex:
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="is_order_filled",
                status=STATUS_ERROR,
                text=f"Error, exception: {ex}; order_id: {order_id}"
            )
            log.save()
            return None

    def change_order_price(self, order_id: str, price: int, btc_rate: float):
        try:
            res = self.client.LinearOrder.LinearOrder_replace(
                symbol="BTCUSDT",
                order_id=order_id,
                p_r_price=price
            ).result()
            if res[0]['ret_msg'] == 'OK':
                order_instance = Order.objects.get(order_id=order_id)
                order_instance.btc_rate = btc_rate
                order_instance.price = price
                order_instance.save()

                log = HedgeLog(
                    preorder=self.preorder_instance,
                    origin="change_order_price",
                    status=STATUS_SUCCESS,
                    text=f"Price changed: {price}; order_id: {order_id}"
                )
                log.save()
            else:
                log = HedgeLog(
                    preorder=self.preorder_instance,
                    origin="change_order_price",
                    status=STATUS_ERROR,
                    text=f"Response is not OK: {res}; order_id: {order_id}"
                )
                log.save()
        except Exception as ex:
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="change_order_price",
                status=STATUS_ERROR,
                text=f"Exception: {ex}; order_id: {order_id}"
            )
            log.save()

    def order_price_handler(self, order_id, operation):
        spread = -self.SPREAD if operation == 'sell' else self.SPREAD
        try:
            btc_rate = self.get_btc_usdt_rate()
            if btc_rate < float('inf'):
                self.change_order_price(order_id=order_id, price=int(btc_rate)+spread, btc_rate=btc_rate)
            else:
                log = HedgeLog(
                    preorder=self.preorder_instance,
                    origin="order_price_handler",
                    status=STATUS_ERROR,
                    text=f"Ambiguous btc rate: {btc_rate}; order_id: {order_id}"
                )
                log.save()
        except Exception as ex:
            log = HedgeLog(
                preorder=self.preorder_instance,
                origin="order_price_handler",
                status=STATUS_ERROR,
                text=f"Exception: {ex}; order_id: {order_id}"
            )
            log.save()






