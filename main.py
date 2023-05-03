import json
import datetime

import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

import quantlib.data_utils as du
import quantlib.general_utils as gu
import quantlib.backtest_utils as backtest_utils
import quantlib.diagnostics_utils as diagnostic_utils
from quantlib.printer_utils import Printer as Printer
from quantlib.printer_utils import _Colors as Colors
from quantlib.printer_utils import _Highlights as Highlights

from brokerage.oanda.oanda import Oanda
from subsystems.LBMOM.subsys import Lbmom
from subsystems.LSMOM.subsys import Lsmom
from subsystems.SKPRM.subsys import Skprm


with open("config/auth_config.json", "r") as f:
    auth_config = json.load(f)

with open("config/portfolio_config.json", "r") as f:
    portfolio_config = json.load(f)

with open("config/oan_config.json", "r") as f:
    brokerage_config = json.load(f)

brokerage_used = "oan"
if brokerage_used == "oan":
    brokerage = Oanda(auth_config=auth_config)
else:
    pass


def print_inst_details(order_config, is_held, required_change=None, percent_change=None, is_override=None):
    color = Colors.YELLOW if not is_held else Colors.BLUE
    Printer.pretty(left="INSTRUMENT:", centre=order_config["instrument"], color=color)
    Printer.pretty(left="CONTRACT SIZE:", centre=order_config["contract_size"], color=color)
    Printer.pretty(left="OPTIMAL UNITS:", centre=order_config["scaled_units"], color=color)
    Printer.pretty(left="CURRENT UNITS:", centre=order_config["current_units"], color=color)
    Printer.pretty(left="OPTIMAL CONTRACTS:", centre=order_config["optimal_contracts"], color=color)
    Printer.pretty(left="CURRENT CONTRACTS:", centre=order_config["current_contracts"], color=color)

    if not is_held:
        Printer.pretty(left="ORDER CHANGE:", centre=order_config["rounded_contracts"], color=Colors.WHITE)
    else:
        Printer.pretty(left="ORDER CHANGE:", centre=required_change, color=Colors.WHITE)
        Printer.pretty(left="% CHANGE:", centre=percent_change, color=Colors.WHITE)
        Printer.pretty(left="INERTIA OVERRIDE:", centre=str(is_override), color=Colors.WHITE)


def print_order_details(contracts):
    Printer.pretty(left="MARKET ORDER:", centre=str(contracts), color=Colors.RED)


def run_simulation(instruments, historical_data, portfolio_vol, subsystems_dict, subsystem_config, brokerage_used, debug=True, use_disk=False):
    test_ranges = []
    for subsystem in subsystems_dict.keys():
        test_ranges.append(subsystems_dict[subsystem]["strat_df"].index)
    start = max(test_ranges, key=lambda x:[0])[0]
    print(start)

    if not use_disk:
        portfolio_df = pd.DataFrame(index=historical_data[start:].index).reset_index()
        portfolio_df.loc[0, "capital"] = 10000
        is_halted = lambda inst, date: not np.isnan(historical_data.loc[date, "{} active".format(inst)]) and (~historical_data[:date].tail(3)["{} active"
                                                                                                              .format(inst)]).any()

        """
        Run Simulation
        """
        for i in portfolio_df.index:
            date = portfolio_df.loc[i, "date"]
            strat_scalar = 2  # strategy scalar (refer to post)
            """
            Get PnL, Scalars
            """
            if i != 0:
                date_prev = portfolio_df.loc[i - 1, "date"]
                pnl, nominal_ret = backtest_utils.get_backtest_day_stats(portfolio_df, instruments, date, date_prev, i, historical_data)
                # Obtain strategy scalar (or leverage)
                strat_scalar = backtest_utils.get_strat_scaler(portfolio_df, lookback=100, vol_target=portfolio_vol, idx=i, default=strat_scalar)

            portfolio_df.loc[i, "strat scalar"] = strat_scalar

            """
            Get Positions
            """
            inst_units = {}
            for inst in instruments:
                inst_dict = {}
                for subsystem in subsystems_dict.keys():
                    subdf = subsystems_dict[subsystem]["strat_df"]
                    subunits = subdf.loc[date, "{} units".format(inst)] if "{} units".format(inst) in subdf.columns and date in subdf.index else 0
                    subscalar = portfolio_df.loc[i, "capital"] / subdf.loc[date, "capital"] if date in subdf.index else 0
                    # TODO: check if this should be subsystem below
                    inst_dict[subsystem] = subunits * subscalar
                inst_units[inst] = inst_dict

            nominal_total = 0
            for inst in instruments:
                combined_sizing = 0
                for subsystem in subsystems_dict.keys():
                    combined_sizing += inst_units[inst][subsystem] * subsystem_config[subsystem]
                position = combined_sizing * strat_scalar
                portfolio_df.loc[i, "{} units".format(inst)] = position
                if position != 0:
                    nominal_total += abs(position * backtest_utils.unit_dollar_value(inst, historical_data, date))

            for inst in instruments:
                units = portfolio_df.loc[i, "{} units".format(inst)]
                if units != 0:
                    nominal_inst = units * backtest_utils.unit_dollar_value(inst, historical_data, date)
                    inst_w = nominal_inst / nominal_total
                    portfolio_df.loc[i, "{} w".format(inst)] = inst_w
                else:
                    portfolio_df.loc[i, "{} w".format(inst)] = 0

            nominal_total = backtest_utils.set_leverage_cap(portfolio_df, instruments, date, i, nominal_total, 10, historical_data)
            """
            Perform Calculations for Date
            """
            portfolio_df.loc[i, "nominal"] = nominal_total
            portfolio_df.loc[i, "leverage"] = nominal_total / portfolio_df.loc[i, "capital"]
            if True: print(portfolio_df.loc[i])

        portfolio_df.set_index("date", inplace=True)
        diagnostic_utils.save_backtests(
            portfolio_df=portfolio_df, instruments=instruments, brokerage_used=brokerage_used, sysname="TradeFlow"
        )

        diagnostic_utils.save_diagnostics(
            portfolio_df=portfolio_df, instruments=instruments, brokerage_used=brokerage_used, sysname="TradeFlow"
        )
    else:
        portfolio_df = gu.load_file("./backtests/{}_{}.obj".format(brokerage_used, "TradeFlow"))


    return portfolio_df

def main():
    use_disk = True
    db_instruments = brokerage_config["fx"] + brokerage_config["indices"] + brokerage_config["commodities"] + brokerage_config["bonds"]

    """
    Load dataframe
    """
    database_df = gu.load_file("./data/oan_ohlcv.obj")
    print(database_df)

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

    """
    Risk Parameters
    """
    VOL_TARGET = portfolio_config["vol_target"]
    sim_start = datetime.date.today() - relativedelta(years=portfolio_config["sim_years"])

    """
    Get existing positions and capital
    """
    capital = brokerage.get_trade_client().get_account_capital()
    positions = brokerage.get_trade_client().get_account_positions()
    print(capital, positions)

    """
    Get Positions of subsystems
    """
    subsystems_config = portfolio_config["subsystems"][brokerage_used]
    strats = {}

    for subsystem in subsystems_config.keys():
        if subsystem == "lbmom":
            strat = Lbmom(
                instruments_config=portfolio_config["instruments_config"][subsystem][brokerage_used],
                historical_df=historical_data,
                simulation_start=sim_start,
                vol_target=VOL_TARGET,
                brokerage_used=brokerage_used
            )
        elif subsystem == "lsmom":
            strat = Lsmom(instruments_config=portfolio_config["instruments_config"][subsystem][brokerage_used],
                          historical_df=historical_data,
                          simulation_start=sim_start,
                          vol_target=VOL_TARGET,
                          brokerage_used=brokerage_used)
        elif subsystem == "skprm":
            strat = Skprm(instruments_config=portfolio_config["instruments_config"][subsystem][brokerage_used],
                          historical_df=historical_data,
                          simulation_start=sim_start,
                          vol_target=VOL_TARGET,
                          brokerage_used=brokerage_used)
        else:
            pass
        strats[subsystem] = strat

    subsystems_dict = {}
    traded =[]
    for k, v in strats.items():
        print("run: ", k, v)
        #  the key, value pair of strategy name, strategy objeçt
        strat_df, strat_inst = v.get_subsys_pos(debug=True, use_disk=True)
        subsystems_dict[k] = {
            "strat_df": strat_df,
            "strat_inst": strat_inst
        }
        traded += strat_inst
    traded = list(set(traded))

    portfolio_df = run_simulation(traded, historical_data, VOL_TARGET, subsystems_dict, subsystems_config, brokerage_used,
                                  debug=True, use_disk=use_disk)
    print(portfolio_df)

    instruments_held = positions.keys()
    instruments_unheld = [inst for inst in traded if inst not in instruments_held]

    """
    Get Optimal Allocations
    """
    trade_on_date = portfolio_df.index[-1]
    capital_scalar = capital / portfolio_df.loc[trade_on_date, "capital"]
    portfolio_optimal = {}

    for inst in traded:
        unscaled_optimal = portfolio_df.loc[trade_on_date, "{} units".format(inst)]
        scaled_units = unscaled_optimal * capital_scalar
        portfolio_optimal[inst] = {
            "unscaled": unscaled_optimal,
            "scaled_units": scaled_units,
            "rounded_units": round(scaled_units),
            "nominal_exposure": abs(scaled_units * backtest_utils.unit_dollar_value(inst, historical_data, trade_on_date)) \
                if scaled_units != 0 else 0
        }

    print(json.dumps(portfolio_optimal, indent=4))
    """
    Edit open positions
    """
    for inst_held in instruments_held:
        Printer.pretty(left="\n******************************************************", color=Colors.BLUE)
        order_config = brokerage.get_service_client().get_order_specs(
            inst=inst_held,
            units=portfolio_optimal[inst_held]["scaled_units"],
            current_contracts=float(positions[inst_held])
        )
        required_change = round(order_config["rounded_contracts"] - order_config["current_contracts"], 2)
        percent_change = round(abs(required_change / order_config["current_contracts"]), 3)
        is_innertia_overriden = brokerage.get_service_client().is_inertia_override(percent_change=percent_change)
        print_inst_details(order_config, True, required_change, percent_change, is_innertia_overriden)
        if is_innertia_overriden:
            print_order_details(required_change)
            if portfolio_config["order_enabled"]:
                brokerage.get_trade_client().market_order(inst=inst_held, order_config=order_config)
        Printer.pretty(left="******************************************************\n", color=Colors.BLUE)
    """
    Open new positions
    """
    for inst_unheld in instruments_unheld:
        pass


if __name__ == "__main__":
    main()

