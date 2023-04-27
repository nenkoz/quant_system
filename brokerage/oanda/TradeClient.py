# aids in executing orders in oanda

import json
import pandas as pd
import datetime
import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.instruments as instruments

from collections import defaultdict


class TradeClient():

    def __init__(self, auth_config):
        self.id = auth_config["oan_acc_id"]
        self.token = auth_config["oan_token"]
        self.env = auth_config["oan_env"]
        self.client = oandapyV20.API(access_token=self.token, environment=self.env)

    """
    Interested in getting 
    1. Capital
    2. Positions
    3. Submit Orders
    4. Get OHCLV data
    """

    def get_account_details(self):
        try:
            return self.client.request(accounts.AccountDetails(self.id))["account"]
        except Exception as err:
            print(err)

    def get_account_summary(self):
        try:
            return self.client.request(accounts.AccountSummary(self.id))["account"]
        except Exception as err:
            print(err)

    def get_account_instruments(self):
        # the list of tradable instruments for a given account
        try:
            r = self.client.request(accounts.AccountInstruments(accountID=self.id))["instruments"]
            instruments = {}
            currencies, cfds, metals = [], [], []
            tags = defaultdict(list)
            for inst in r:
                inst_name = inst["name"]
                type = inst["type"]
                tag_name = inst["tags"][0]["name"]
                tags[tag_name].append(inst_name)
                instruments[inst_name] = {
                    # we can store other variables for an instrument such as precision and margin rate
                    "type" : type,
                    "tag" : inst["tags"][0]["name"]
                }
                if type == "CFD":
                    cfds.append(inst_name)
                elif type == "CURRENCY":
                    currencies.append(inst_name)
                elif type == "METAL":
                    metals.append(inst_name)
                else:
                    print("unknown type: ", inst_name, type)
                    exit()
            return instruments, currencies, cfds, metals, tags
        except Exception as err:
            print(err)

    def get_account_capital(self):
        try:
            return float(self.get_account_summary()["NAV"])
        except Exception as err:
            print(err)

    def get_account_positions(self):
        positions_data = self.get_account_details()["positions"]
        positions = {}
        for entry in positions_data:
            instrument = entry["instrument"]
            long_pos = float(entry["long"]["units"])
            short_pos = float(entry["short"]["units"])
            net_pos = long_pos + short_pos
            if net_pos != 0:
                positions[instrument] = net_pos

        return positions

    def get_account_trades(self):
        try:
            trade_data = self.client.request(trades.OpenTrades(accountID=self.id))
            return trade_data
        except Exception as err:
            print(err)

    def format_date(self, series):
        # converting series in the form :: '2022-12-07T22:00:00.000000000Z'
        ddmmyy = series.split("T")[0].split("-")
        return datetime.date(int(ddmmyy[0]), int(ddmmyy[1]), int(ddmmyy[2]))

    def get_ohlcv(self, instrument, count, granularity):
        try:
            params = {"count": count, "granularity": granularity}
            candles = instruments.InstrumentsCandles(instrument=instrument, params=params)
            self.client.request(candles)
            ohlcv_dict = candles.response["candles"]
            ohlcv = pd.DataFrame(ohlcv_dict)
            ohlcv = ohlcv[ohlcv["complete"]] # taking only the completed candles
            ohlcv_df = ohlcv["mid"].dropna().apply(pd.Series) # converts the dictionary in every row into a separate columns
            ohlcv_df["volume"] = ohlcv["volume"]
            ohlcv_df.index = ohlcv["time"]
            ohlcv_df = ohlcv_df.apply(pd.to_numeric) # converts the object data types into numeric
            ohlcv_df.reset_index(inplace=True) # adds an index 0,1,2,...
            ohlcv_df.columns = ["date", "open", "high", "low", "close", "volume"]
            ohlcv_df["date"] = ohlcv_df["date"].apply(lambda x: self.format_date(x))
            return ohlcv_df
        except Exception as err:
            print(err)

    def market_order(self, inst, order_config={}):
        pass

