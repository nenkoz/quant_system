import pandas as pd
import quantlib.general_utils as gu
import quantlib.data_utils as du
import random
import json
from subsystems.LBMOM.subsys import Lbmom
from dateutil.relativedelta import relativedelta

df, instruments = gu.load_file("./data/data.obj")
print(df, instruments)

VOL_TARGET = 0.2
print(df.index[-1]) # last date: 2023-04-06
sim_start = df.index[-1] - relativedelta(years=5)
print(sim_start)

start = Lbmom(instruments_config="./subsystems/LBMOM/config.json", historical_df=df, simulation_start=sim_start, vol_target=VOL_TARGET)
start.get_subsys_pos()
