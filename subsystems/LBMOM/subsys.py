# [(44, 100), (156, 245), (23, 184), (176, 290), (215, 288), (245, 298), (59, 127), (134, 275), (220, 286), (60, 168), (208, 249), (19, 152),
# (38, 122), (234, 254), (227, 293), (64, 186), (28, 49), (22, 106), (25, 212), (144, 148), (260, 284)]

import json
import numpy as np
import pandas as pd

import quantlib.backtest_utils as backtest_utils
import quantlib.indicators_cal as indicators_cal
import quantlib.general_utils as general_utils
import quantlib.diagnostics_utils as diagnostic_utils


class Lbmom:

    def __init__(self, instruments_config, historical_df, simulation_start, vol_target, brokerage_used):
        self.pairs = [(44, 100), (156, 245), (23, 184), (176, 290), (215, 288), (245, 298), (59, 127), (134, 275), (220, 286), (60, 168), (208, 249),
                      (19, 152), (38, 122), (234, 254), (227, 293), (64, 186), (28, 49), (22, 106), (25, 212), (144, 148), (260, 284)]
        self.historical_df = historical_df
        self.simulation_start = simulation_start
        self.vol_target = vol_target  # we adopt the volatility targetting risk framework.
        with open(instruments_config) as f:
            self.instruments_config = json.load(f)
        self.brokerage_used = brokerage_used
        self.sysname = "LBMOM"

    """
    Strategy API:
    1. Function to get data and indicators specific to strategy
    2. Function to run backtest and get positions
    """

    def extend_historicals(self, instruments, historical_data):
        # we need to obtain data with regards to the LBMOM strategy
        # in particular, we want the moving averages, which is a proxy for momentum factor
        # we also want a univariate statistical factor as an indicator of regime. We use the average directional index ADX as a proxy for momentum
        # regime indicator
        for inst in instruments:
            historical_data["{} adx".format(inst)] = indicators_cal.adx_series(
                high=historical_data["{} high".format(inst)],
                low=historical_data["{} low".format(inst)],
                close=historical_data["{} close".format(inst)],
                n=14
            )
            for pair in self.pairs:
                # calculate the fastMA - slowMA
                historical_data["{} ema{}".format(inst, str(pair))] = indicators_cal.ema_series(historical_data["{} close".format(inst)], n=pair[0]) \
                                                                      - indicators_cal.ema_series(historical_data["{} close".format(inst)], n=pair[1])
        # the historical_data has all the information required for backtesting
        return historical_data

    def run_simulation(self, historical_data, debug=False, use_disk = False):
        """
        Init Params + Pre-processing
        """
        instruments = self.instruments_config["fx"] + self.instruments_config["indices"] + self.instruments_config["commodities"] + \
                      self.instruments_config["bonds"]

        if not use_disk:
            historical_data = self.extend_historicals(instruments=instruments, historical_data=historical_data)
            portfolio_df = pd.DataFrame(index=historical_data[self.simulation_start:].index).reset_index()
            portfolio_df.loc[0, "capital"] = 10000
            is_halted = lambda inst, date: not np.isnan(historical_data.loc[date, "{} active".format(inst)]) and (
                ~historical_data[:date].tail(3)["{} active".format(inst)]).any()
            # this means that in order to `not be a halted asset`, it needs to have actively traded over the all last 3 data points at the minimum

            """
            Run Simulation
            We adopt a risk management technique at asset and strategy level called vol targeting. This in general means that we lever our capital to
            obtain a certain target annualized level of volatility, which is our proxy for risk / exposure. This is controlled by the parameter
            VOL_TARGET, that we pass from the main driver.
            The relative allocations in a vol target framework is that positions are inversely proportional to their volatility. In other words, a priori
            we assign the same risk to each position, when not taking into account the relative alpha (momentum) strengths
    
            So we assume 3 different risk/capital allocation techniques:
            1. Strategy Vol Targetting (vertical across time)
            2. Asset Vol Targetting (relative across assets)
            3. Voting Systems (Indicating the degree of momentum factor)
            """
            for i in portfolio_df.index:
                date = portfolio_df.loc[i, "date"]
                strat_scalar = 2  # strategy scalar (refer to post)

                tradable = [inst for inst in instruments if not is_halted(inst, date)]
                non_tradable = [inst for inst in instruments if inst not in tradable]

                """
                Get PnL, Scalars
                """
                if i != 0:
                    date_prev = portfolio_df.loc[i - 1, "date"]
                    pnl, nominal_ret = backtest_utils.get_backtest_day_stats(portfolio_df, instruments, date, date_prev, i, historical_data)
                    # Obtain strategy scalar (or leverage)
                    strat_scalar = backtest_utils.get_strat_scaler(portfolio_df, lookback=100, vol_target=self.vol_target, idx=i, default=strat_scalar)

                portfolio_df.loc[i, "strat scalar"] = strat_scalar

                """
                Get Positions
                """
                for inst in non_tradable:
                    # assign weight and position to 0 if not tradable
                    portfolio_df.loc[i, "{} units".format(inst)] = 0
                    portfolio_df.loc[i, "{} w".format(inst)] = 0

                nominal_total = 0
                for inst in tradable:
                    # vote long if fastMA > slowMA else no vote. We are trying to harvest momentum. We use MA pairs to proxy momentum, and define its
                    # strength by fraction of trending pairs.
                    votes = [1 if (historical_data.loc[date, "{} ema{}".format(inst, str(pair))] > 0) else 0 for pair in self.pairs]
                    forecast = np.sum(votes) / len(votes)  # degree of momentum measured from 0 to 1. 1 if all trending, 0 if none trending
                    forecast = 0 if historical_data.loc[date, "{} adx".format(inst)] < 25 else forecast  # if regime is not trending, set forecast to 0

                    # vol_targeting
                    # dollar volatility assigned to a single position
                    position_vol_target = (1 / len(tradable)) * portfolio_df.loc[i, "capital"] * self.vol_target / np.sqrt(253)
                    inst_price = historical_data.loc[date, "{} close".format(inst)]
                    # suppose an asset is not actively traded. Then its vol would be low. Taking an asset position inversely proportional to vol -> then
                    # the asset position would be large. This would blow up the position sizing if not given a default value
                    percent_ret_vol = historical_data.loc[date, "{} % ret vol".format(inst)] if historical_data.loc[:date].tail(20)["{} active".format(
                        inst)].all() else 0.025
                    # vol in nominal dollar terms. It is important to be expressed in dollar terms as otherwise, prices closer to 0 have higher
                    # percentage volatility compared to assets far away from 0. Refer to this podcast for more info:
                    # https://rb.gy/8htt7
                    # vol in nominal dollar terms of the asset under consideration (adjusted for FX conversion)
                    dollar_volatility = backtest_utils.unit_val_change(inst, inst_price * percent_ret_vol, historical_data, date)
                    # we should be using the position vol target instead of the portfolio vol target, since we already divided the capital
                    position = strat_scalar * forecast * position_vol_target / dollar_volatility
                    portfolio_df.loc[i, "{} units".format(inst)] = position
                    backtest_unit_dollar_value = backtest_utils.unit_dollar_value(inst, historical_data, date)
                    nominal_total += abs(position * backtest_unit_dollar_value)  # with FX conversion

                # we see that for the first date, we manage to obtain the positions for the different assets that we want

                nominal_total = backtest_utils.set_leverage_cap(portfolio_df, instruments, date, i, nominal_total, 10, historical_data)

                for inst in tradable:
                    units = portfolio_df.loc[i, "{} units".format(inst)]
                    nominal_inst = units * backtest_utils.unit_dollar_value(inst, historical_data, date)
                    inst_w = nominal_inst / nominal_total
                    portfolio_df.loc[i, "{} w".format(inst)] = inst_w

                """
                Perform Calculations for Date
                """
                portfolio_df.loc[i, "nominal"] = nominal_total
                portfolio_df.loc[i, "leverage"] = nominal_total / portfolio_df.loc[i, "capital"]
                if debug: print(portfolio_df.loc[i])

            # let us also store this inside an excel file, and what our strategy generates
            portfolio_df.set_index("date", inplace=True)

            diagnostic_utils.save_backtests(
                portfolio_df=portfolio_df, instruments=instruments, brokerage_used=self.brokerage_used, sysname=self.sysname
            )

            diagnostic_utils.save_diagnostics(
                portfolio_df=portfolio_df, instruments=instruments, brokerage_used=self.brokerage_used, sysname=self.sysname
            )

        else:
            portfolio_df = general_utils.load_file("./backtests/{}_{}.obj".format(self.brokerage_used, self.sysname))

        return portfolio_df, instruments

    def get_subsys_pos(self, debug):
        portfolio_df, instruments = self.run_simulation(historical_data=self.historical_df, debug=debug)
        return portfolio_df, instruments