# aids in the order logic and helps integrate the brokerage into the system, no external dependencies

class ServiceClient():
    def __init__(self):
        pass

    def get_size_config(self, inst):
        order_min_contracts = 1 # the min size of an order determined by the brokerage
        contract_size = 1 # the size of the contract determined by the brokerage
        return order_min_contracts, contract_size

    # this is an internal 'order' object that is passed around different components of the trading system
    # it is the 'setting' of an order item, that all brokerages should implement to meet internal needs
    def get_order_specs(self, inst, units, current_contracts):
        order_min_contracts, contract_size = self.get_size_config(inst)
        order_min_units = self. contracts_to_units(label=inst, contracts=order_min_contracts)
        optimal_min_order = units / order_min_units
        rounded_min_order = round(optimal_min_order)
        specs = {
            "instrument": inst,
            "scaled_units": units,
            "contract_size": contract_size,
            "order_min_units": order_min_units,
            "optimal_contracts": optimal_min_order * order_min_contracts,
            "rounded_contracts": rounded_min_order * order_min_contracts,
            "current_contracts": current_contracts,
            "current_units": self.contracts_to_units(inst, current_contracts)
        }
        return specs

    def contracts_to_units(self, label, contracts):
        order_min_contracts, contract_size = self.get_size_config(label)
        return contracts * contract_size

    def units_to_contracts(self, label, units):
        order_min_contracts, contract_size = self.get_size_config(label)
        return units / contract_size

    # positional inertia to prevent too frequent trading
    # TODO: to be vol adjusted
    def is_inertia_override(self, percent_change):
        return percent_change > 0.05

    def code_to_label_nomeclature(self, code):
        return code

    def label_to_code_nomeclature(self, label):
        return label