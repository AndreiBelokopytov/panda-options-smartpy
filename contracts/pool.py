import smartpy as sp

constants = sp.io.import_script_from_url("file:contracts/utils/constants.py")


class Pool(sp.Contract):
    def __init__(self, base_asset):
        self.base_asset = base_asset
        self.init(total_amount=0)

    @sp.entry_point
    def deposit(self, amount):
        self.data.total_amount += amount

    @sp.entry_point
    def withdraw(self, amount):
        self.data.total_amount -= amount

    @sp.onchain_view()
    def get_base_asset(self):
        sp.result(self.base_asset)


sp.add_compilation_target(
    "pool",
    Pool(
        base_asset="XTZ-USD"
    )
)


@sp.add_test(name="pool_test")
def test():
    scenario = sp.test_scenario()
    base_asset = "XTZ-USD"
    pool_contract = Pool(base_asset=base_asset)

    scenario += pool_contract
    scenario.verify(pool_contract.get_base_asset() == base_asset)
