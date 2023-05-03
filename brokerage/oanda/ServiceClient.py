# aids in the order logic and helps integrate the brokerage into the system, no external dependencies

class ServiceClient():
    def __init__(self):
        pass

    def get_size_config(self, inst):
        order_min_contracts = 1 # the min size of an order determined by the brokerage
        contract_size = 1 # the size of the contract determined by the brokerage
        return order_min_contracts, contract_size

    def get_order_spec(self, inst, units, contracts, current_contracts):
        pass

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