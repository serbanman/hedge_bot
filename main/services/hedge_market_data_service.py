from main.models.hedge_logs import STATUS_SUCCESS, STATUS_ERROR
from main.services.hedge_rates_service import HedgeRatesService


class HedgeMarketDataService(HedgeRatesService):
    def __init__(self, preorder_id=None):
        super().__init__(preorder_id)

    def get_market_data(self):
        try:
            raw_pos_info = self.client.LinearPositions.LinearPositions_myPosition(
            symbol="BTCUSDT"
            ).result()[0]['result'][1]

            position_info = {
                'size': raw_pos_info['size'],
                'position_value': raw_pos_info['position_value'],
                'leverage': raw_pos_info['leverage'],
                'entry_price': raw_pos_info['entry_price'],
                'liq_price': raw_pos_info['liq_price'],
                'unrealised_pnl': raw_pos_info['unrealised_pnl']
            }

            current_rate = self.get_btc_usdt_rate()
            while current_rate == float('inf'):
                current_rate = self.get_btc_usdt_rate()

            raw_wallet_info = self.client.Wallet.Wallet_getBalance(
                coin="USDT").result()[0]['result']['USDT']
            wallet_info = {
                'available_balance': raw_wallet_info['available_balance'],
                'wallet_balance': raw_wallet_info['wallet_balance']
            }

            result = {
                'rate': current_rate,
                'position_info': position_info,
                'wallet_info': wallet_info
            }

            self.log(
                origin="get_market_data",
                status=STATUS_SUCCESS,
                text=f"Data: {result}"
            )

            return result
        except Exception as ex:
            self.log(
                origin="get_market_data",
                status=STATUS_ERROR,
                text=f"Exception: {ex}"
            )

            return {}











