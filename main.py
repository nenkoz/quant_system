import json
import pandas as pd

from dateutil.relativedelta import relativedelta

import quantlib.data_utils as du
import quantlib.general_utils as gu

from subsystems.LBMOM.subsys import Lbmom
from brokerage.oanda.oanda import Oanda

with open("config/auth_config.json", "r") as f:
    auth_config = json.load(f)

with open("config/oan_config.json", "r") as f:
    brokerage_config = json.load(f)

VOL_TARGET = 0.20

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
historical_data = du.extend_dataframe(traded=db_instruments, df=database_df)


#
# trade_client = brokerage.get_trade_client()
#
# exit()
#
# strat = Lbmom(instruments_config="./subsystems/LBMOM/config.json", historical_df=df, simulation_start=sim_start, vol_target=VOL_TARGET)
# strat.get_subsys_pos()

