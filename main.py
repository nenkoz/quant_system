import json
import pandas as pd

from dateutil.relativedelta import relativedelta

import quantlib.data_utils as du
import quantlib.general_utils as gu

from subsystems.LBMOM.subsys import Lbmom
from brokerage.oanda.oanda import Oanda

with open("config/auth_config.json", "r") as f:
    auth_config = json.load(f)

df, instruments = gu.load_file("./Data/data.obj")
print(df, instruments)

#run simulation for 5 years
VOL_TARGET = 0.20
sim_start = df.index[-1] - relativedelta(years=1)

oanda = Oanda(auth_config=auth_config)

trade_client = oanda.get_trade_client()

trade_client.get_ohlcv("USD_JPY", 100, "D")
exit()
instruments, currencies, cfds, metals, tags = trade_client.get_account_instruments()

print(currencies)
print(cfds)
print(metals)
print(tags)
# results = trade_client.get_account_instruments()
# print(json.dumps(results, indent= 2))
exit()

strat = Lbmom(instruments_config="./subsystems/LBMOM/config.json", historical_df=df, simulation_start=sim_start, vol_target=VOL_TARGET)
strat.get_subsys_pos()

