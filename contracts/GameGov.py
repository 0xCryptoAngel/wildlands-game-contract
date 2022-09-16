import smartpy as sp

NFTandVault = sp.io.import_template("NFTandVault.py")


FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")
Utils = sp.io.import_script_from_url(
    "https://raw.githubusercontent.com/RomarQ/tezos-sc-utils/main/smartpy/utils.py")


T_BALANCE_OF_REQUEST = sp.TRecord(owner=sp.TAddress, token_id=sp.TNat).layout(
    ("owner", "token_id")
)

T_CITY_RESOURCE = sp.TRecord(
    city_level=sp.TNat,
    faith=sp.TNat,
    beauty=sp.TNat,
    food=sp.TNat,
    wood=sp.TNat,
    stone=sp.TNat,
    iron=sp.TNat,
    aurum=sp.TNat,

    last_claim_time=sp.TTimestamp,

    food_per_epoch=sp.TNat,
    wood_per_epoch=sp.TNat,
    stone_per_epoch=sp.TNat,
    iron_per_epoch=sp.TNat,
)
# .layout('city_level', 'faith', 'beauty',
#          'food', 'wood', 'stone', 'iron', 'aurum',
#          'last_claim_time',
#          'food_per_epoch', 'wood_per_epoch', 'stone_per_epoch', 'iron_per_epoch')


class NftOwnerCheck:
    def __init__(self, nft_contract):
        self.update_initial_storage(
            nft_contract=nft_contract,
            temp_balances=sp.list(l=[],
                                  t=sp.TRecord(
                request=T_BALANCE_OF_REQUEST,
                balance=sp.TNat,
            ))
        )

    @sp.entry_point
    def set_balance_callback(self, balances):
        sp.verify(sp.sender == self.data.nft_contract, "Not authorised")
        self.data.temp_balances = balances

    def is_valid_owner(self, owner, token_id):
        contract = sp.contract(
            sp.TPair(sp.TList(T_BALANCE_OF_REQUEST), sp.TContract(sp.TList(
                sp.TRecord(
                    request=T_BALANCE_OF_REQUEST,
                    balance=sp.TNat,
                )))),
            self.data.nft_contract,
            "balance_of"
        ).open_some()
        sp.transfer(sp.pair([sp.record(owner=owner, token_id=token_id)],
                            sp.self_entry_point("set_balance_callback")),
                    sp.tez(0), contract)
        sp.trace(self.data.temp_balances)


class ResourceStorage(sp.Contract):
    def __init__(self):
        self.update_initial_storage(
            resource_map=sp.big_map(
                {}, tkey=sp.TNat, tvalue=T_CITY_RESOURCE),
        )

    def initialize_city(self, token_id):
        self.data.resource_map[token_id] = sp.record(
            city_level=0,
            faith=0,
            beauty=0,
            food=0,
            wood=0,
            stone=0,
            iron=0,
            aurum=0,

            last_claim_time=sp.now,

            food_per_epoch=45,
            wood_per_epoch=30,
            stone_per_epoch=30,
            iron_per_epoch=30)


class GameGov(FA2.Admin, FA2.WithdrawMutez, NftOwnerCheck, ResourceStorage):
    def __init__(self, admin, nft_contract, **kwargs):
        FA2.Admin.__init__(self, admin)
        ResourceStorage.__init__(self)
        NftOwnerCheck.__init__(self, nft_contract)

    @sp.entry_point
    def start_game(self, token_id):
        self.is_valid_owner(sp.sender, token_id)
        sp.set_type(token_id, sp.TNat)
        self.initialize_city(token_id)
        sp.trace(self.data.resource_map)


@ sp.add_test(name="Game Gov with Resource manager")
def test():
    sc = sp.test_scenario()

    nft_contract = NFTandVault.NftWithAdmin(
        admin=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"),
        metadata={},
        token_metadata=[],
    )
    sc += nft_contract
    c1.mint([sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR")]).run(
        sender=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"), amount=sp.mutez(20500000))

    c1.mint([sp.address("tz1Zn3WK57gjcsk6WH8MD6jf4VEqXuRfgPFM")]).run(
        sender=sp.address("tz1Zn3WK57gjcsk6WH8MD6jf4VEqXuRfgPFM"), amount=sp.mutez(20500000))

    sc.show(nft_contract.data)

    c1 = GameGov(
        admin=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"),
        nft_contract=sp.address("KT1KFczzgYkxLqTGmhbBvmew12WN3qbkBq4E")
    )
    sc += c1
    c1.start_game(10).run(sender=sp.address(
        "tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"))
    print(c1)


# A a compilation target (produces compiled code)
sp.add_compilation_target("GameGov_Compiled", GameGov(
    admin=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"),
    nft_contract=sp.address("KT1KFczzgYkxLqTGmhbBvmew12WN3qbkBq4E")
))
