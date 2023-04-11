"""
A calculator for indicators and other functionalities
"""

import talib
import numpy as np
import pandas as pd


def adx_series(high, low, close, n):
    return talib.ADX(high, low, close, timeperiod=n)


def ema_series(series, n):
    return talib.EMA(series, timeperiod=n)


def sma_series(series, n):
    return talib.SMA(series, timeperiod=n)
