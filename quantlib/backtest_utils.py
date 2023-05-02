import numpy as np


def get_backtest_day_stats(portfolio_df, instruments, date, date_prev, date_idx, historical_data):
    pnl = 0  # pnl for the day
    nominal_ret = 0  # nominal returns

    for inst in instruments:
        previous_holdings = portfolio_df.loc[date_idx - 1, "{} units".format(inst)]
        if previous_holdings != 0:
            price_change = historical_data.loc[date, "{} close".format(inst)] - historical_data.loc[date_prev, "{} close".format(inst)]

            dollar_change = unit_val_change(from_prod=inst, val_change=price_change, historical_data=historical_data, date=date_prev)  # FX Conversion

            inst_pnl = dollar_change * previous_holdings
            pnl += inst_pnl
            nominal_ret += portfolio_df.loc[date_idx - 1, "{} w".format(inst)] * historical_data.loc[date, "{} % ret".format(inst)]

    capital_ret = nominal_ret * portfolio_df.loc[date_idx - 1, "leverage"]
    portfolio_df.loc[date_idx, "capital"] = portfolio_df.loc[date_idx - 1, "capital"] + pnl
    portfolio_df.loc[date_idx, "daily pnl"] = pnl
    portfolio_df.loc[date_idx, "nominal ret"] = nominal_ret
    portfolio_df.loc[date_idx, "capital ret"] = capital_ret
    return pnl, capital_ret


def get_strat_scaler(portfolio_df, lookback, vol_target, idx, default):
    capital_ret_history = portfolio_df.loc[:idx].dropna().tail(lookback)["capital ret"]
    strat_scaler_history = portfolio_df.loc[:idx].dropna().tail(lookback)["strat scalar"]
    if len(capital_ret_history) == lookback:
        # enough data, then increase or decrease the scalar based on empirical vol of the strategy equity curve relative to target vol
        annualized_vol = capital_ret_history.std() * np.sqrt(253)  # annualise the vol from daily vol
        scalar_hist_avg = np.mean(strat_scaler_history)
        strat_scalar = scalar_hist_avg * vol_target / annualized_vol
        return strat_scalar
    else:
        # not enough data, just return a default value
        return default


def unit_val_change(from_prod, val_change, historical_data, date):
    """

    :param from_prod: instrument traded, e.g. HK33_HKD
    :param val_change: change in price quote
    :param historical_data:
    :param date:
    :return:
    """
    is_denominated = len(from_prod.split("_")) == 2
    if not is_denominated:
        return val_change  # assume USD denomination, e.g. AAPL
    elif is_denominated and from_prod.split("_")[1] == "USD":
        return val_change  # USD denominated, e.g. AAPL_USD
    else:
        # e.g. HK33_HKD, USD_JPY (X_Y)
        # take delta price * (Y_USD)
        return val_change * historical_data.loc[date, "{}_USD close".format(from_prod.split("_")[1])]


def unit_dollar_value(from_prod, historical_data, date):
    #  how much is 1 contract worth
    is_denominated = len(from_prod.split("_")) == 2
    if not is_denominated:
        return historical_data.loc[date, "{} close".format(date)]  # e.g. AAPL units is worth the price of 1 AAPL unit
    if is_denominated and from_prod.split("_")[0] == "USD":
        return 1
    if is_denominated and not from_prod.split("_")[0] == "USD":
        #  e.g.  HK33_USD, EUR_USD, (X_Y) -> then you want to take the price change in the denominated currency, which is unit_price * (Y_USD)
        unit_price = historical_data.loc[date, "{} close".format(from_prod)]
        fx_inst = "{}_{}".format(from_prod.split("_")[1], "USD")
        fx_quote = 1 if fx_inst == "USD_USD" else historical_data.loc[date, "{} close".format(fx_inst)]
        return unit_price * fx_quote


def set_leverage_cap(portfolio_df, instruments, date, idx, nominal_tot, leverage_cap, historical_data):
    leverage = nominal_tot / portfolio_df.loc[idx, "capital"]
    if leverage > leverage_cap:
        new_nominals = 0
        leverage_scalar = leverage_cap / leverage
        for inst in instruments:
            newpos = portfolio_df.loc[idx, "{} units".format(inst)] * leverage_scalar
            portfolio_df.loc[idx, "{} units".format(inst)] = newpos
            if newpos != 0:
                new_nominals += abs(newpos * unit_dollar_value(inst, historical_data, date))
        return new_nominals
    else:
        return nominal_tot


def kpis(df):
    portfolio_df = df.copy()
    portfolio_df["cum ret"] = (1 + portfolio_df["capital ret"]).cumprod()
    portfolio_df["drawdown"] = portfolio_df["cum ret"] / portfolio_df["cum ret"].cummax() - 1
    sharpe = portfolio_df["capital ret"].mean() / portfolio_df["capital ret"].std() * np.sqrt(253)
    drawdown_max = portfolio_df["drawdown"].min() * 100
    volatility = portfolio_df["capital ret"].std() * np.sqrt(253) * 100  # annualised percent vol
    return portfolio_df, sharpe, drawdown_max, volatility
