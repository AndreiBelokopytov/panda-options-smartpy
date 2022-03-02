import smartpy as sp

FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/FA2.py").FA2
pool = sp.io.import_script_from_url("file:contracts/pool.py")
option_fa2 = sp.io.import_script_from_url("file:contracts/option_fa2.py")
harbinger_mock = sp.io.import_script_from_url(
    "file:contracts/mocks/harbinger_mock.py")
constants = sp.io.import_script_from_url("file:contracts/utils/constants.py")

TOptionState = sp.TVariant(
    Invalid=sp.TUnit, Active=sp.TUnit, Exercised=sp.TUnit, Expired=sp.TUnit)

TOption = sp.TRecord(owner=sp.TAddress, base_asset=sp.TString, state=TOptionState, amount=sp.TNat,
                     strike=sp.TNat, expiration=sp.TTimestamp)

invalid_option_period_error = "Invalid option period"
invalid_amount_error = "Invalid amount"

default_min_amount = 1000000


class OptionMarket(sp.Contract):
    _option_min_period = 1
    _option_max_period = 30

    def __init__(self, admin, base_asset, option_type, normalizer_address,
                 min_amount=1000000, option_fa2_address=sp.none, pool_address=sp.none):
        self.base_asset = base_asset
        self.option_type = option_type
        self.min_amount = min_amount
        self.normalizer_address = normalizer_address
        self.init_type(sp.TRecord(admin=sp.TAddress, option_fa2_address=sp.TOption(sp.TAddress), pool_address=sp.TOption(
            sp.TAddress), options=sp.TBigMap(sp.TNat, TOption), next_token_id=sp.TNat))
        self.init(admin=admin, option_fa2_address=option_fa2_address, pool_address=pool_address, options=sp.big_map(tkey=sp.TNat,
                  tvalue=TOption), next_token_id=0)

    @sp.entry_point
    def sell_option(self, amount, strike, period):
        strike_ = sp.local("strike_", strike)
        with sp.if_(strike == 0):
            strike_.value = sp.snd(self.get_price_from_harbinger(
                asset_code=self.base_asset, address=self.normalizer_address))
        option = self.create_option(
            sp.sender, self.base_asset, amount, strike_.value, period)

        self.data.options[self.data.next_token_id] = option

        option_metadata = self.get_option_metadata()
        option_fa2_param = sp.TRecord(address=sp.TAddress, amount=sp.TNat,
                                      metadata=sp.TMap(sp.TString, sp.TBytes), token_id=sp.TNat)
        option_fa2_address = self.data.option_fa2_address.open_some(
            "Option FA2 address does not set")
        option_fa2_contract = sp.contract(
            option_fa2_param, option_fa2_address, "mint").open_some("Option FA2 interface mismatch")
        sp.transfer(sp.record(address=option.owner, amount=1, metadata=option_metadata,
                    token_id=self.data.next_token_id), sp.mutez(0), option_fa2_contract)

        self.data.next_token_id += 1

    @sp.entry_point
    def set_option_fa2_address(self, address):
        self.verify_is_admin(sp.sender)
        self.data.option_fa2_address = sp.some(address)

    @sp.entry_point
    def set_pool_address(self, address):
        self.verify_is_admin(sp.sender)
        self.data.pool_address = sp.some(address)

    @sp.offchain_view(pure=True)
    def get_base_asset(self):
        sp.result(self.base_asset)

    def create_option(self, owner, base_asset, amount, strike, period):
        sp.verify(period >= self._option_min_period,
                  invalid_option_period_error)
        sp.verify(period <= self._option_max_period,
                  invalid_option_period_error)
        sp.verify(amount >= self.min_amount, invalid_amount_error)
        expiration = sp.now
        expiration.add_days(period)
        return sp.record(owner=owner, base_asset=base_asset, state=sp.variant("Active", sp.unit),
                         amount=amount, strike=strike, expiration=expiration)

    def get_option_metadata(self):
        return FA2.make_metadata(
            decimals=0,
            name=self.base_asset + " " + self.option_type + " Option",
            symbol="POP"
        )

    def get_price_from_harbinger(self, address, asset_code):
        return sp.view("getPrice", address, asset_code, t=sp.TPair(
            sp.TTimestamp, sp.TNat)).open_some("Invalid getPrice view")

    def verify_is_admin(self, address):
        sp.verify(address == self.data.admin)


sp.add_compilation_target(
    "xtz_usd_call_option_market",
    OptionMarket(
        admin=sp.address("tz1Xf1CJtexgmpEprsxBS8cNMZYyusSSfEsw"),
        base_asset="XTZ-USD",
        option_type="Call",
        normalizer_address=sp.address("KT1PMQZxQTrFPJn3pEaj9rvGfJA9Hvx7Z1CL"),
    )
)

sp.add_compilation_target(
    "xtz_usd_put_option_market",
    OptionMarket(
        admin=sp.address("tz1Xf1CJtexgmpEprsxBS8cNMZYyusSSfEsw"),
        base_asset="XTZ-USD",
        option_type="Put",
        normalizer_address=sp.address("KT1PMQZxQTrFPJn3pEaj9rvGfJA9Hvx7Z1CL"),
    )
)


@sp.add_test(name="option_market_test")
def test():
    base_asset = "XTZ-USD"
    alice = sp.test_account("alice")

    # init
    sp.test_account("banana")
    normalizer_contract = harbinger_mock.Normalizer()
    pool_contract = pool.Pool()
    option_fa2_contract = option_fa2.OptionFA2(admin=alice.address)
    option_market_contract = OptionMarket(
        admin=alice.address,
        base_asset=base_asset,
        option_type="Call",
        normalizer_address=normalizer_contract.address
    )

    scenario = sp.test_scenario()
    scenario += normalizer_contract
    scenario += pool_contract
    scenario += option_fa2_contract
    scenario += option_market_contract

    option_fa2_contract.set_administrator(
        option_market_contract.address).run(sender=alice.address)
    scenario.verify(option_market_contract.address ==
                    option_fa2_contract.data.administrator)

    scenario.h1("Option Market")

    scenario += option_market_contract.set_option_fa2_address(
        option_fa2_contract.address).run(sender=alice.address)

    scenario.verify(option_market_contract.data.option_fa2_address.open_some(
    ) == option_fa2_contract.address)

    scenario += option_market_contract.set_pool_address(
        pool_contract.address).run(sender=alice.address)
    scenario.verify(
        option_market_contract.data.pool_address.open_some() == pool_contract.address)

    scenario.h2("Sell option")
    amount = 1000000
    strike = 360000
    period = 14
    too_short_period = 0
    too_long_period = 31
    base_asset_price = 350000
    zero_amount = 0

    scenario.p("it should create an option correctly")
    scenario += option_market_contract.sell_option(
        amount=amount,
        strike=strike,
        period=period).run(sender=alice.address)
    token_id = sp.as_nat(option_market_contract.data.next_token_id - 1)
    option = option_market_contract.data.options[token_id]
    normalizer_contract.setPrice(
        asset_code=base_asset, value=base_asset_price)

    scenario.verify(option.amount == amount)
    scenario.verify(option.strike == strike)
    scenario.verify(option.state.is_variant("Active"))

    scenario.p("it should revert if the strike is less than 1 day")
    scenario += option_market_contract.sell_option(
        amount=amount, strike=strike, period=too_short_period).run(sender=alice.address, valid=False)

    scenario.p("it should revert if the strike is more than 30 days")
    scenario += option_market_contract.sell_option(amount=amount,
                                                   strike=strike, period=too_long_period).run(sender=alice.address, valid=False)

    scenario.p("it should revert if the amount is less than 1")
    scenario += option_market_contract.sell_option(amount=zero_amount,
                                                   strike=strike, period=period).run(sender=alice.address, valid=False)

    scenario.p("it should set option's strike to the spot price if 0 is given")
    scenario += option_market_contract.sell_option(amount=amount,
                                                   strike=0, period=period).run(sender=alice.address)
    token_id = sp.as_nat(option_market_contract.data.next_token_id - 1)
    option = option_market_contract.data.options[token_id]
    quote = normalizer_contract.getPrice(base_asset)
    scenario.verify(option.strike == sp.snd(quote))

    scenario.p("it should mint an NFT token")
    scenario += option_market_contract.sell_option(amount=amount,
                                                   strike=0, period=period).run(sender=alice.address)
    token_id = sp.as_nat(option_market_contract.data.next_token_id - 1)
    scenario.verify(option_fa2_contract.does_token_exist(token_id))
