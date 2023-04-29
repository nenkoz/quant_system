import json
import datetime

from dateutil.relativedelta import relativedelta

import quantlib.data_utils as du
import quantlib.general_utils as gu

from brokerage.oanda.oanda import Oanda
from subsystems.LBMOM.subsys import Lbmom
from subsystems.LSMOM.subsys import Lsmom

with open("config/auth_config.json", "r") as f:
    auth_config = json.load(f)

with open("config/portfolio_config.json", "r") as f:
    portfolio_config = json.load(f)

with open("config/oan_config.json", "r") as f:
    brokerage_config = json.load(f)

def main():
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
    subsystems_config = portfolio_config["subsystems"]["oan"]
    strats = {}

    for subsystem in subsystems_config.keys():
        print(subsystem)
        if subsystem == "lbmom":
            strat = Lbmom(instruments_config=portfolio_config["instruments_config"][subsystem]["oan"],
                          historical_df=historical_data,
                          simulation_start=sim_start,
                          vol_target=VOL_TARGET,
                          brokerage_used="oan")
        elif subsystem == "lsmom":
            strat = Lsmom(instruments_config=portfolio_config["instruments_config"][subsystem]["oan"],
                          historical_df=historical_data,
                          simulation_start=sim_start,
                          vol_target=VOL_TARGET,
                          brokerage_used="oan")
        else:
            pass
        strats[subsystem] = strat

    for k, v in strats.items():
        print("run: ", k, v)
        #  the key, value pair of strategy name, strategy objeçct
        strat_db, strat_inst = v.get_subsys_pos(debug=True)
        print(strat_db, strat_inst)


if __name__ == "__main__":
    main()

