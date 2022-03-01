import smartpy as sp

FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/FA2.py")
constants = sp.io.import_script_from_url("file:contracts/utils/constants.py")
pool = sp.io.import_script_from_url("file:contracts/pool.py")
option_fa2 = sp.io.import_script_from_url("file:contracts/option_fa2.py")
harbinger_mock = sp.io.import_script_from_url(
    "file:contracts/mocks/harbinger_mock.py")

TOptionState = sp.TVariant(
    Invalid=sp.TUnit, Active=sp.TUnit, Exercised=sp.TUnit, Expired=sp.TUnit)

TOption = sp.TRecord(owner=sp.TAddress, state=TOptionState, amount=sp.TNat,
                     strike=sp.TNat, expiration=sp.TTimestamp)

invalid_option_period_error = "Invalid option period"


class OptionManager(sp.Contract):
    _option_min_period = 1
    _option_max_period = 30

    def __init__(self, normalizer_address, option_fa2_address):
        self.normalizer_address = normalizer_address
        self.option_fa2_address = option_fa2_address
        self.init(options=sp.big_map(tkey=sp.TNat,
                  tvalue=TOption), next_token_id=0)

    @sp.entry_point
    def sell_option(self, pool_address, amount, strike, period):
        strike_ = sp.local("strike_", strike)
        base_asset = sp.local("base_asset", self.get_base_asset(pool_address))
        with sp.if_(strike == 0):
            strike_.value = sp.snd(self.get_price_from_harbinger(
                asset_code=base_asset.value, address=self.normalizer_address))
        option = self.create_option(
            sp.sender, amount, strike_.value, period)

        self.data.options[self.data.next_token_id] = option

        option_metadata = self.get_option_metadata(option)
        option_fa2_param = sp.TRecord(address=sp.TAddress, amount=sp.TNat,
                                      metadata=sp.TMap(sp.TString, sp.TBytes), token_id=sp.TNat)
        option_fa2_contract = sp.contract(
            option_fa2_param, self.option_fa2_address, "mint").open_some("Option FA2 interface mismatch")
        sp.transfer(sp.record(address=option.owner, amount=option.amount, metadata=option_metadata,
                    token_id=self.data.next_token_id), sp.mutez(0), option_fa2_contract)

        self.data.next_token_id += 1

    def create_option(self, owner, amount, strike, period):
        sp.verify(period >= self._option_min_period,
                  invalid_option_period_error)
        sp.verify(period <= self._option_max_period,
                  invalid_option_period_error)
        expiration = sp.timestamp_from_utc_now()
        expiration.add_days(period)
        return sp.record(owner=owner, state=sp.variant("Active", sp.unit),
                         amount=amount, strike=strike, expiration=expiration)

    def get_option_metadata(self, option):
        return FA2.FA2.make_metadata(
            decimals=0,
            name="Panda",
            symbol="TZOP")

    def get_base_asset(self, pool_address):
        return sp.view("get_base_asset", pool_address, sp.unit, t=sp.TString).open_some("Invalid get_base_asset view")

    def get_price_from_harbinger(self, address, asset_code):
        return sp.view("getPrice", address, asset_code, t=sp.TPair(
            sp.TTimestamp, sp.TNat)).open_some("Invalid getPrice view")


sp.add_compilation_target(
    "option_manager_testnet",
    OptionManager(
        normalizer_address=sp.address("KT1QnqJPr7wtAwto7QjCRqoCGkJYBqH129b8"),
        option_fa2_address=sp.address("KT1FoBPfaL5Q9nzkwbesXzqWSRwMJ2m31Qiz")
    )
)

@sp.add_test(name="option_manager_test")
def test():
    base_asset = "XTZ/USD"
    alice = sp.test_account("alice")

    # init
    sp.test_account("banana")
    normalizer_contract = harbinger_mock.Normalizer()
    pool_contract = pool.Pool(base_asset)
    option_fa2_contract = option_fa2.OptionFA2(amdin=alice.address)
    option_manager_contract = OptionManager(normalizer_address = normalizer_contract.address, option_fa2_address = option_fa2_contract.address)
    option_fa2_contract.setAdministrator(alice.address)

    scenario = sp.test_scenario()
    scenario += pool.pool_contract
    scenario += option_fa2.option_fa2_contract
    scenario += harbinger_mock.normalizer_contract
    scenario += option_manager_contract

    scenario.h1("Option")

    scenario.h2("Sell option")
    amount = 1
    strike = 360000
    period = 14
    too_short_period = 0
    too_long_period = 31
    base_asset_price = 350000

    scenario.p("it should create an option correctly")
    scenario += option_manager_contract.sell_option(pool_address=pool.pool_contract.address,
                                                    amount=amount,
                                                    strike=strike,
                                                    period=period).run(sender=alice)
    token_id = sp.as_nat(option_manager_contract.data.next_token_id - 1)
    option = option_manager_contract.data.options[token_id]
    harbinger_mock.normalizer_contract.setPrice(
        asset_code=base_asset, value=base_asset_price)

    scenario.verify(option.amount == amount)
    scenario.verify(option.strike == strike)
    scenario.verify(option.expiration - sp.now >=
                    period * constants.seconds_in_a_day)
    scenario.verify(option.state.is_variant("Active"))

    scenario.p("it should revert if the strike is less than 1 day")
    scenario += option_manager_contract.sell_option(
        pool_address=pool.pool_contract.address,
        amount=amount, strike=strike, period=too_short_period).run(valid=False)

    scenario.p("it should revert if the strike is more than 30 days")
    scenario += option_manager_contract.sell_option(pool_address=pool.pool_contract.address, amount=amount,
                                                    strike=strike, period=too_long_period).run(valid=False)

    scenario.p("it should set the strike to the spot price if 0 is given")
    scenario += option_manager_contract.sell_option(pool_address=pool.pool_contract.address, amount=amount,
                                                    strike=0, period=period).run(sender=alice)
    token_id = sp.as_nat(option_manager_contract.data.next_token_id - 1)
    option = option_manager_contract.data.options[token_id]
    quote = harbinger_mock.normalizer_contract.getPrice(base_asset)
    scenario.verify(option.strike == sp.snd(quote))

    scenario.p("it should mint an NFT token")
    scenario += option_manager_contract.sell_option(pool_address=pool.pool_contract.address, amount=amount,
                                                    strike=0, period=period).run(sender=alice)
    token_id = sp.as_nat(option_manager_contract.data.next_token_id - 1)
    scenario.verify(option_fa2.option_fa2_contract.does_token_exist(token_id))
