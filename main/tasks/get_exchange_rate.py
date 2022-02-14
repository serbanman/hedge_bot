from celery import shared_task
from django.conf import settings
import pyotp
import bybit
from pprint import pprint


@shared_task(bind=True)
def get_exchange_rate(self):
    # _login = getattr(settings, 'BYBIT_LOGIN', None)
    # _password = getattr(settings, 'BYBIT_PASSWORD', None)
    # _otp_token = getattr(settings, 'BYBIT_2FA', None)
    #
    # _totp_code = pyotp.TOTP(_otp_token)
    # _totp = _totp_code.now()
    _api_key = getattr(settings, 'BYBIT_API', None)
    _api_secret = getattr(settings, 'BYBIT_SECRET', None)

    client = bybit.bybit(test=False, api_key=_api_key, api_secret=_api_secret)
    result = client.Market.Market_symbolInfo().result()[0]['result'][0]['bid_price']
    pprint(result)



