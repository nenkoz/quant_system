import json
import pandas as pd
import quantlib.indicator_cal as indicator_cal

class Lbmom:

    def __init__(self, instruments_config, historical_df, simulation_start, vol_target):
        self.pairs = [(109, 146), (199, 251), (152, 280), (68, 277), (79, 188), (193, 246), (208, 217), (22, 79),
                      (81, 274), (108, 294), (117, 204), (19, 284), (142, 289), (119, 286), (18, 147), (192, 280),
                      (115, 201), (152, 271), (39, 278), (75, 154), (222, 255)]
        self.historical_df = historical_df
        self.simulation_start = simulation_start
        self.vol_target = vol_target
        with open(instruments_config) as f:
            self.instrument_config = json.load(f)
        self.sysname = "LBMOM"

    # getting data and indicators specific to strategy
    # we need moving averages data which is a proxy for momentum factor
    # we also want a univariate statistical factor as an indicator of regimes (i.e. average directional index ADX as a
    # proxy fpr momentum regime indicator)
    def extend_dataframe(self, instruments, historical_data):
        for inst in instruments:
            historical_data["{} adx".format(inst)] = indicator_cal.adx_series(
                high=historical_data["{} high".format(inst)],
                low=historical_data["{} low".format(inst)],
                close=historical_data["{} close".format(inst)],
                n=14
            )
            for pair in self.pairs:
                historical_data["{} ema{}".format(inst, str(pair))] = indicator_cal.ema_series(historical_data["{} close".format(inst)], n=pair[0]) -\
                    indicator_cal.ema_series(historical_data["{} close".format(inst)], n=pair[1])

        return historical_data

    # running backtest
    def run_simulation(self, historical_data):
        """
        Init param
        """
        instruments = self.instrument_config["instruments"]

        """
        Pre-processing
        """
        historical_data = self.extend_dataframe(instruments=instruments, historical_data=historical_data)
        print(historical_data)
        portfolio_df = pd.DataFrame(index=historical_data[self.simulation_start:].index).reset_index()
        portfolio_df.loc[0, "capital"] = 10000
        print(portfolio_df)

        """
        Run simulation
        """
        pass

    # getting positions form strat
    def get_subsys_pos(self):
        self.run_simulation(historical_data=self.historical_df)
