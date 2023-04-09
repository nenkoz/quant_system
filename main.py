import pandas as pd
import quantlib.general_utils as gu
import quantlib.data_utils as du

df, instruments = gu.load_file("./data/data.obj")
print(df, instruments)