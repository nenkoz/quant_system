import requests
import pandas as pd
import yfinance as yf
import datetime
from bs4 import BeautifulSoup


def get_sp500_instruments():
    res = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = BeautifulSoup(res.content,'lxml')
    table = soup.find_all('table')[0]
    df = pd.read_html(str(table))
    return list(df[0]["Symbol"])


def get_sp500_df():
    symbols = get_sp500_instruments()
    ohlcvs = {}
    symbols = symbols[:30]
    for symbol in symbols:
        symbol_df = yf.Ticker(symbol).history(period="10y") #Gives the OHLCV Dividents + Stock Splits
        print(symbol_df)
        # Interested in OHLCV, renaming them
        ohlcvs[symbol] = symbol_df[["Open", "High", "Low", "Close", "Volume"]].rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            }
        )

    df = pd.DataFrame(index=ohlcvs["GOOGL"].index)
    df.index.name = "date"
    instruments = list(ohlcvs.keys())

    for inst in instruments:
        inst_df = ohlcvs[inst]
        # Transforming open, high, ... to AAPL open, AAPL high and so on
        columns = list(map(lambda x: "{} {}".format(inst, x), inst_df.columns))
        df[columns] = inst_df

    return df, instruments


# adding some statistics to the price/vol data
def extend_dataframe(traded, df):
    # standardizing the index of the dataframe
    df.index = pd.Series(df.index).apply(lambda x: format_date(x))
    open_cols = list(map(lambda x: str(x) + " open", traded))
    high_cols = list(map(lambda x: str(x) + " high", traded))
    low_cols = list(map(lambda x: str(x) + " low", traded))
    close_cols = list(map(lambda x: str(x) + " close", traded))
    volume_cols = list(map(lambda x: str(x) + " volume", traded))
    historical_data = df.copy()
    historical_data = historical_data[open_cols + high_cols + low_cols + close_cols + volume_cols]
    historical_data.fillna(method="ffill", inplace=True)  # forward fill
    historical_data.fillna(method="bfill", inplace=True)  # backward fill
    for inst in traded:
        # close to close return stats
        historical_data["{} % ret".format(inst)] = historical_data["{} close".format(inst)] / \
                                                   historical_data["{} close".format(inst)].shift(1) - 1
        # historical standard deviation of returns as realised volatility proxy
        historical_data["{} % ret vol".format(inst)] = historical_data["{} % ret".format(inst)].rolling(25).std()
        # testing if ticker is actively traded
        historical_data["{} active".format(inst)] = historical_data["{} close".format(inst)] != \
            historical_data["{} close".format(inst)].shift(1)
    return historical_data


def format_date(date):
    # convert 2020-01-02 00:00:00 >> datetime.date(2020, 01, 02)
    yymmdd = list(map(lambda x: int(x), str(date).split(" ")[0].split("-")))
    return datetime.date(yymmdd[0], yymmdd[1], yymmdd[2])

"""
Note:
There are different ways to fill missing data depending on requirements and purpose:
Some options:
1. ffill and bfill for backtesting
2. Brownian motion/bridge for simulation of stock market dynamics
3. GARCH/GARCH Copula for modelling multivariate dependencies
4. Synthetic data, such as GAN and Stochastic Volatility Neural Networks for training neural models
"""

