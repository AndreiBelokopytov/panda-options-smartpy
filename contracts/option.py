import smartpy as sp

TOptionState = sp.TVariant(Invalid = sp.TUnit, Active = sp.TUnit, Exercised = sp.TUnit, Expired = sp.TUnit)

TOption = sp.TRecord(state = TOptionState, amount=sp.TNat, strike=sp.TNat, expiration=sp.TTimestamp)

option_min_period = 1
option_max_period = 30

invalid_option_period_error = "Invalid option period"

def create_option(amount, strike, period):
    expiration = sp.timestamp_from_utc_now()
    expiration.add_days(period)
    sp.verify(period >= option_min_period, invalid_option_period_error)
    sp.verify(period <= option_max_period, invalid_option_period_error)
    return sp.record(state = sp.variant("Active", sp.unit), amount = amount, strike = strike, expiration = expiration)
