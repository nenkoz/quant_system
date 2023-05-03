# oanda_id: 101-004-25556708-001
# oanda_key: dcf3670a3b789ca4e92a378e0f42b7ef-730912f748ac18daa38097916a070f26

from brokerage.oanda.TradeClient import TradeClient
from brokerage.oanda.ServiceClient import ServiceClient


class Oanda:

    def __init__(self, auth_config={}):
        self.trade_client = TradeClient(auth_config=auth_config)
        self.service_client = ServiceClient()

    def get_service_client(self):
        return self.service_client

    def get_trade_client(self):
        return self.trade_client
