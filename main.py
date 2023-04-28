import json
import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta

import quantlib.data_utils as du
import quantlib.general_utils as gu

from subsystems.LBMOM.subsys import Lbmom
from brokerage.oanda.oanda import Oanda


import matplotlib.pyplot as plt
df = pd.read_excel("lbmom.xlsx")
(1 + df["capital ret"]).cumprod().plot()
plt.show()

exit()
with open("config/auth_config.json", "r") as f:
    auth_config = json.load(f)

with open("config/portfolio_config.json", "r") as f:
    portfolio_config = json.load(f)

with open("config/oan_config.json", "r") as f:
    brokerage_config = json.load(f)

brokerage = Oanda(auth_config=auth_config)
db_instruments = brokerage_config["fx"] + brokerage_config["indices"] + brokerage_config["commodities"] + brokerage_config["bonds"]

"""
Load dataframe
"""
database_df = gu.load_file("./data/oan_ohlcv.obj")

# poll_df = pd.DataFrame()
# for db_inst in db_instruments:
#     df = brokerage.get_trade_client().get_ohlcv(instrument=db_inst, count=50, granularity="D")
#     df.set_index("date", inplace=True)
#
#     cols = list(map(lambda x: "{} {}".format(db_inst, x), df.columns))  # adds identifier
#     df.columns = cols
#     if len(poll_df) == 0:
#         poll_df[cols] = df
#     else:
#         poll_df = poll_df.combine_first(df)  # inefficient but combines the dataframes without losing data
#
# print("BEFORE :", database_df)
# database_df = database_df.loc[:poll_df.index[0]][:-1]  # dropping the last overlapping data point
# database_df = pd.concat([database_df, poll_df])
# print("NEW :", poll_df)
# print("COMBINED :", database_df)
# gu.save_file("./data/oan_ohlcv.obj", database_df)

"""
Extend the database
"""
historical_data = du.extend_dataframe(traded=db_instruments, df=database_df, fx_codes=brokerage_config["fx_codes"])
print(list(historical_data))

"""
Risk Parameters
"""
VOL_TARGET = portfolio_config["vol_target"]
sim_start = datetime.date.today() - relativedelta(years=portfolio_config["sim_years"])

"""
Get Positions of subsystems
"""
# trade_client = brokerage.get_trade_client()

strat = Lbmom(instruments_config="./subsystems/LBMOM/config.json", historical_df=historical_data, simulation_start=sim_start, vol_target=VOL_TARGET,
              brokerage_used="oan")
strat.get_subsys_pos()

