import smartpy as sp


class PriceCalculator:
    def get_option_price(self, option):
        return option.strike / sp.nat(10)
