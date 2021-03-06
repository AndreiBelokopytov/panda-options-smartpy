import smartpy as sp
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/FA2.py")

option_manager_config = FA2.FA2_config(
    non_fungible=True, use_token_metadata_offchain_view=True)

metadata_url = "https://gist.githubusercontent.com/AndreiBelokopytov/03225777c35c1a6ec4bd3e3f971cb06d/raw/bb2d0afb015c4a3ce279697f453df0539ab8e795/gistfile1.txt"


class OptionFA2(FA2.FA2):

    def __init__(self, admin, config=option_manager_config, metadata_url=metadata_url):
        metadata = {
            "name": "Panda Option",
            "description": "Panda is an options trading app on Tezos blockchain",
            "version": "0.1.0",
            "interfaces": ["TZIP-012", "TZIP-016"],
        }

        self.init_metadata("content", metadata)

        FA2.FA2_core.__init__(self, config,
                              paused=False,
                              administrator=admin, metadata=sp.utils.metadata_of_url(
                                  metadata_url))


sp.add_compilation_target(
    "option_fa2",
    OptionFA2(
        admin=sp.address("tz1Xf1CJtexgmpEprsxBS8cNMZYyusSSfEsw")
    )
)
