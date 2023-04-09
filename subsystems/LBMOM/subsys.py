import json


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
        pass

    # running backtest
    def run_simulation(self, historical_data):
        pass

    # getting positions form strat
    def get_subsys_pos(self):
        pass
