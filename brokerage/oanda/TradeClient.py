# aids in executing orders in oanda

import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.instruments as instruments


class TradeClient():

    def __init__(self, auth_config):
        self.id = auth_config["oan_acc_id"]
        self.token = auth_config["oan_token"]
        self.env = auth_config["oan_env"]
        self.client = oandapyV20.API(access_token=self.token, environment=self.env)
        print(self.client)

    """
    Interested in getting 
    1. Capital
    2. Positions
    3. Submit Orders
    4. Get OHCLV data
    """

    def get_account_details(self):
        pass

    def get_account_summary(self):
        pass

    def get_account_capital(self):
        pass

    def get_account_positions(self):
        pass

    def get_account_trades(self):
        pass

    def get_account_orders(self):
        pass

    def get_ohlcv(self, instrument, count, granularity):
        pass

    def market_order(self, inst, order_config={}):
        pass

