import smartpy as sp


def get_price_from_harbinger(address, asset_code):
    return sp.view("getPrice", address, asset_code, t=sp.TPair(
        sp.TTimestamp, sp.TNat)).open_some("Invalid getPrice view")
