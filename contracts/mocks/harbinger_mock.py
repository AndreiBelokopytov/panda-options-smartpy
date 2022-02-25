import smartpy as sp


class Normalizer(sp.Contract):
    def __init__(self):
        self.init(asset_data=sp.big_map(tkey=sp.TString,
                  tvalue=sp.TPair(sp.TTimestamp, sp.TNat)))

    @sp.entry_point
    def setPrice(self, asset_code, value):
        self.data.asset_data[asset_code] = sp.pair(sp.now, value)

    @sp.onchain_view()
    def getPrice(self, asset_code):
        sp.result(self.data.asset_data[asset_code])
