import smartpy as sp
FA12 = sp.io.import_script_from_url("https://smartpy.io/templates/FA1.2.py")


class Token(FA12.FA12):
    def __init__(self, admin):
        FA12.FA12_core.__init__(
            self,
            administrator=admin,
            config=FA12.FA12_config(),
            paused=False,
            token_metadata={
                "decimals": "18",
                "name": "Test Token",
                "symbol": "TEST",
            }
        )
