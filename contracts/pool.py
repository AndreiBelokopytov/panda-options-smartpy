import smartpy as sp

option = sp.io.import_script_from_url("file:contracts/option.py")
constants = sp.io.import_script_from_url("file:contracts/utils/constants.py")
harbinger_facade = sp.io.import_script_from_url(
    "file:contracts/facades/harbinger_facade.py")
harbinger_mock = sp.io.import_script_from_url(
    "file:contracts/mocks/harbinger_mock.py")


class Pool(sp.Contract):
    def __init__(self, base_asset, normalizer_address, next_option_id):
        self.normalizer_address = normalizer_address
        self.base_asset = base_asset
        self.init(next_option_id=next_option_id, options=sp.big_map(
            tkey=sp.TNat, tvalue=option.TOption))

    @sp.entry_point
    def sell_option(self, amount, strike, period):
        strike_ = sp.local('strike_', strike)
        with sp.if_(strike == 0):
            strike_.value = sp.snd(harbinger_facade.get_price_from_harbinger(
                asset_code=self.base_asset, address=self.normalizer_address))
        self.data.options[self.data.next_option_id] = option.create_option(
            amount, strike_.value, period)
        self.data.next_option_id += 1

    @sp.entry_point
    def exercise_option(self):
        pass

    @sp.entry_point
    def deposit(self):
        pass

    @sp.entry_point
    def withdraw(self):
        pass


@sp.add_test(name="Pool")
def test():
    base_asset = "XTZ/USD"
    alice = sp.test_account("alice")
    # init
    normalizer_contract = harbinger_mock.Normalizer()
    pool_contract = Pool(
        base_asset=base_asset, normalizer_address=normalizer_contract.address, next_option_id=0)
    scenario = sp.test_scenario()
    scenario += pool_contract
    scenario += normalizer_contract

    scenario.h1("Pool contract")

    scenario.h2("Sell option")
    amount = 1
    strike = 360000
    period = 14
    too_short_period = 0
    too_long_period = 31
    base_asset_price = 350000

    scenario.p("it should create an option correctly")
    scenario += pool_contract.sell_option(amount=amount,
                                          strike=strike, period=period).run(sender=alice)
    option_id = sp.as_nat(pool_contract.data.next_option_id - 1)
    option = pool_contract.data.options[option_id]
    normalizer_contract.setPrice(
        asset_code=base_asset, value=base_asset_price)

    scenario.verify(option.amount == amount)
    scenario.verify(option.strike == strike)
    scenario.verify(option.expiration - sp.now >=
                    period * constants.seconds_in_a_day)
    scenario.verify(option.state.is_variant("Active"))

    scenario.p("it should revert if the strike is less than 1 day")
    scenario += pool_contract.sell_option(
        amount=amount, strike=strike, period=too_short_period).run(valid=False)

    scenario.p("it should revert if the strike is more than 30 days")
    scenario += pool_contract.sell_option(amount=amount,
                                          strike=strike, period=too_long_period).run(valid=False)

    scenario.p("it should set the strike to the spot price if 0 is given")
    scenario += pool_contract.sell_option(amount=amount,
                                          strike=0, period=period).run(sender=alice)
    option_id = sp.as_nat(pool_contract.data.next_option_id - 1)
    option = pool_contract.data.options[option_id]
    quote = normalizer_contract.getPrice(base_asset)
    scenario.verify(option.strike == sp.snd(quote))


sp.add_compilation_target("PoolTest", Pool(base_asset="XTZ/USD", next_option_id=0,
                          normalizer_address=sp.address("KT1PMQZxQTrFPJn3pEaj9rvGfJA9Hvx7Z1CL")))
