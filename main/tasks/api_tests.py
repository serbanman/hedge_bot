from celery import shared_task
from django.conf import settings
import pyotp
import bybit
from pprint import pprint


@shared_task(bind=True)
def get_exchange_rate(self):
    _api_key = getattr(settings, 'BYBIT_API', None)
    _api_secret = getattr(settings, 'BYBIT_SECRET', None)

    client = bybit.bybit(test=True, api_key=_api_key, api_secret=_api_secret)
    exchange_rate = client.Market.Market_symbolInfo().result()[0]['result'][0]['last_price']
    print(f'** Course: {exchange_rate}', end='')

    # balance
    # print(client.Wallet.Wallet_getBalance(coin="USDT").result())

    # position info
    unrealized_pnl = client.LinearPositions.LinearPositions_myPosition(
        symbol="BTCUSDT"
        ).result()[0]['result'][1]['unrealised_pnl']
    print(f' PNL: {unrealized_pnl}', end='')

    sum = 100
    btc_qty = '%.3f' % (sum / float(exchange_rate))

    # new position
    new_pos = client.LinearOrder.LinearOrder_new(
        side="Sell",
        symbol="BTCUSDT",
        order_type="Limit",
        qty="0.001",
        price=41000,
        time_in_force="GoodTillCancel",
        reduce_only=False,  # True for closing
        close_on_trigger=False
    ).result()
    order_id = ''
    if new_pos[0]['ret_msg'] == 'OK':
        order_id = new_pos[0]['result']['order_id']
        print('success')

    # list of my positions
    my_pos_list = client.LinearOrder.LinearOrder_getOrders(symbol="BTCUSDT").result()

    print(client.LinearOrder.LinearOrder_cancel(symbol="BTCUSDT",
                                                order_id="58634c94-a3c7-4ac5-85c8-ecb583b48606").result())

    client.LinearOrder.LinearOrder_replace(symbol="BTCUSDT", order_id='6a3f2a88-dc33-4b85-b5d7-737cf4a7cfd4', p_r_price="100").result()
    client.LinearOrder.LinearOrder_query(symbol="BTCUSDT", order_id='6a3f2a88-dc33-4b85-b5d7-737cf4a7cfd4').result()


# x = client.LinearKline.LinearKline_get(symbol="BTCUSDT", interval="1", limit=1, **{'from':time.time() - 50}).result()[0]['result'][0]['close']
# y = client.Market.Market_symbolInfo().result()[0]['result'][0]['last_price']
# print(x, y)

from django.conf import settings
import bybit
client = bybit.bybit(test=True, api_key=settings.BYBIT_API, api_secret=settings.BYBIT_SECRET)
x = {'order_id': '6a3f2a88-dc33-4b85-b5d7-737cf4a7cfd4'}