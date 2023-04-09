import data as du
import general_utils as gu

# df, instruments = du.get_sp500_df()
# df = du.extend_dataframe(traded=instruments, df=df)
# gu.save_file("./data/data.obj", (df, instruments))

df, instruments = gu.load_file("./data/data.obj")
print(df, instruments)