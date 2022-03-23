import time
from main.models import Order
from main.models.hedge_logs import STATUS_SUCCESS, STATUS_ERROR
from main.models.orders import TYPE_BUY, TYPE_SELL, STATUS_FILLED, STATUS_NEW, STATUS_CANCELLED
from main.services.hedge_rates_service import HedgeRatesService


class HedgeOrdersService(HedgeRatesService):
    def __init__(self, preorder_id=None):
        super().__init__(preorder_id)

        self.spread = 1

    def create_order(self, sum_btc: float, sell=False, buy=False):  # sell order == buy short
        rate_btc_usdt = self.get_btc_usdt_rate()

        if sell and not buy:
            spread = -self.spread
            side = 'Sell'
            reduce_only = False
            order_type = TYPE_SELL
        elif buy and not sell:
            spread = self.spread
            side = 'Buy'
            reduce_only = True
            order_type = TYPE_BUY
        else:
            self.log(
                origin="create_order stage init",
                status=STATUS_ERROR,
                text=f"Ambiguous args: sell {sell} buy {buy}"
            )
            return None

        if rate_btc_usdt == float('inf'):
            self.log(
                origin="create_order stage rates",
                status=STATUS_ERROR,
                text=f"Didn't get proper rates: btc {rate_btc_usdt}"
            )
            return None
        else:
            self.log(
                origin="create_order stage rates",
                status=STATUS_SUCCESS,
                text=f"Got rates: btc {rate_btc_usdt}"
            )

        sum_usd = float(sum_btc) * rate_btc_usdt
        btc_qty = '%.3f' % sum_btc

        try:
            RETRY_COUNT = 5
            counter = 0
            while counter < RETRY_COUNT:
                new_order_gross_data = self.client.LinearOrder.LinearOrder_new(
                    side=side,
                    symbol="BTCUSDT",
                    order_type="Limit",
                    qty=btc_qty,
                    price=rate_btc_usdt + spread,
                    time_in_force="GoodTillCancel",
                    reduce_only=reduce_only,  # True for closing
                    close_on_trigger=False
                ).result()
                order_id = ''
                if new_order_gross_data[0]['ret_msg'] == 'OK' and new_order_gross_data[0]['result']:
                    order_id = new_order_gross_data[0]['result']['order_id']

                    new_order = Order(
                        preorder=self.preorder_instance,
                        order_id=order_id,
                        type=order_type,
                        sum_btc=btc_qty,
                        price=rate_btc_usdt + spread,
                        btc_rate=rate_btc_usdt,
                        sum_usd=sum_usd
                    )
                    new_order.save()

                    self.log(
                        origin="create_order stage order",
                        status=STATUS_SUCCESS,
                        text=f"OK data: {new_order_gross_data}. New order id: {new_order.id}, count: {counter}"
                    )
                    return new_order.id
                else:
                    self.log(
                        origin="create_order stage order",
                        status=STATUS_ERROR,
                        text=f"Not OK data: {new_order_gross_data}, count: {counter}"
                    )
                    counter += 1
                    time.sleep(5)
            return None
        except Exception as ex:
            self.log(
                origin="create_order stage order",
                status=STATUS_ERROR,
                text=f"Error, exception: {ex}"
            )
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
                        self.log(
                            origin="is_order_filled status found",
                            status=STATUS_SUCCESS,
                            text=f"Found status: {order_data['order_status']}; order_id: {order_id}"
                        )
                        return True
                    else:
                        self.log(
                            origin="is_order_filled status found",
                            status=STATUS_ERROR,
                            text=f"Found status: {order_data['order_status']}; order_id: {order_id}"
                        )
                        return False

                else:
                    self.log(
                        origin="is_order_filled",
                        status=STATUS_ERROR,
                        text=f"Ambiguous status: {order_data['order_status']}; order_id: {order_id}"
                    )

            elif orders_gross_data[0]['ret_msg'] == 'Order not exists':
                self.log(
                    origin="is_order_filled",
                    status=STATUS_ERROR,
                    text=f"Order not exists: {orders_gross_data}; order_id: {order_id}"
                )
            else:
                self.log(
                    origin="is_order_filled",
                    status=STATUS_ERROR,
                    text=f"Else Response is not OK: {orders_gross_data}; order_id: {order_id}"
                )
            return None
        except Exception as ex:
            self.log(
                origin="is_order_filled",
                status=STATUS_ERROR,
                text=f"Error, exception: {ex}; order_id: {order_id}"
            )
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

                self.log(
                    origin="change_order_price",
                    status=STATUS_SUCCESS,
                    text=f"Price changed: {price}; order_id: {order_id}"
                )
            else:
                self.log(
                    origin="change_order_price",
                    status=STATUS_ERROR,
                    text=f"Response is not OK: {res}; order_id: {order_id}"
                )
        except Exception as ex:
            self.log(
                origin="change_order_price",
                status=STATUS_ERROR,
                text=f"Exception: {ex}; order_id: {order_id}"
            )

    def order_price_handler(self, order_id):
        try:
            order_instance = Order.objects.get(order_id=order_id)
            if order_instance.type == TYPE_SELL:
                spread = -self.spread
            elif order_instance.type == TYPE_BUY:
                spread = self.spread
            else:
                raise ValueError
        except Exception as ex:
            spread = 0
            self.log(
                origin="order_price_handler",
                status=STATUS_ERROR,
                text=f"Ambiguous type: ex {ex};\n id: {order_id}"
            )

        try:
            btc_rate = self.get_btc_usdt_rate()
            if btc_rate < float('inf'):
                self.change_order_price(order_id=order_id, price=int(btc_rate)+spread, btc_rate=btc_rate)
            else:
                self.log(
                    origin="order_price_handler",
                    status=STATUS_ERROR,
                    text=f"Ambiguous btc rate: {btc_rate}; order_id: {order_id}"
                )
        except Exception as ex:
            self.log(
                origin="order_price_handler",
                status=STATUS_ERROR,
                text=f"Exception: {ex}; order_id: {order_id}"
            )
