import smartpy as sp

constants = sp.io.import_script_from_url("file:contracts/utils/constants.py")


class Pool(sp.Contract):
    def __init__(self):
        self.init(total_amount=0)

    @sp.entry_point
    def deposit(self, amount):
        self.data.total_amount += amount

    @sp.entry_point
    def withdraw(self, amount):
        self.data.total_amount -= amount


sp.add_compilation_target(
    "pool",
    Pool()
)


@sp.add_test(name="pool_test")
def test():
    scenario = sp.test_scenario()
    pool_contract = Pool()

    scenario += pool_contract
