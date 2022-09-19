import smartpy as sp

NFTandVault = sp.io.import_script_from_url(
    "https://raw.githubusercontent.com/toptal126/CoC-tezos-p2e-game/e459673b8f9a5a83ba1bd4c2fadd9b99a09b1d87/contracts/NFTandVault.py")


FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")
Utils = sp.io.import_script_from_url(
    "https://raw.githubusercontent.com/RomarQ/tezos-sc-utils/main/smartpy/utils.py")


T_BALANCE_OF_REQUEST = sp.TRecord(owner=sp.TAddress, token_id=sp.TNat).layout(
    ("owner", "token_id")
)

SECONDS_PER_DAY = 60
# SECONDS_PER_DAY = 86400

T_CITY_RESOURCE = sp.TRecord(
    city_level=sp.TNat,
    population_limit=sp.TNat,
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

T_BUILDING_CATEGORY = sp.TRecord(
    # Upgrading buildings
    # Resource producing buildings
    # Unit producing buildings
    # Other Buildings

    building_kind=sp.TNat,
    # Unique if for each building type
    building_id=sp.TNat,
    # Costs per level
    resource_updates=sp.TMap(sp.TNat, sp.TRecord(
        required_city_level=sp.TNat,

        food_cost=sp.TNat,
        wood_cost=sp.TNat,
        stone_cost=sp.TNat,
        iron_cost=sp.TNat,
        aurum_cost=sp.TNat,

        food_per_epoch=sp.TNat,
        wood_per_epoch=sp.TNat,
        stone_per_epoch=sp.TNat,
        iron_per_epoch=sp.TNat,

        faith_plus=sp.TNat,
        beauty_plus=sp.TNat,
    ))
)


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
        with sp.for_("temp_balance", balances) as temp_balance:
            sp.verify(temp_balance.balance > 0, "Invalid Owner")

    def is_valid_owner(self, owner, token_id):
        contract = sp.contract(
            sp.TRecord(
                requests=sp.TList(
                    sp.TRecord(
                        owner=sp.TAddress,
                        token_id=sp.TNat
                    ).layout(("owner", "token_id"))
                ),
                callback=sp.TContract(
                    sp.TList(
                        sp.TRecord(
                            request=sp.TRecord(
                                owner=sp.TAddress,
                                token_id=sp.TNat
                            ).layout(("owner", "token_id")),
                            balance=sp.TNat
                        ).layout(("request", "balance"))
                    )
                )
            ).layout(("requests", "callback")),
            self.data.nft_contract,
            entry_point="balance_of").open_some()
        requests = sp.list([sp.record(owner=owner, token_id=token_id)])
        params = sp.record(callback=sp.self_entry_point(
            entry_point="set_balance_callback"), requests=requests)
        sp.transfer(params, sp.mutez(0), contract)


class BuildingCategories(sp.Contract):
    def __init__(self, buiding_categories):
        self.update_initial_storage(
            buiding_categories=buiding_categories
        )


class ResourceStorage(sp.Contract):
    def __init__(self):
        self.update_initial_storage(
            resource_map=sp.big_map(
                {}, tkey=sp.TNat, tvalue=T_CITY_RESOURCE),
            temp1=0,
            temp2=0,
            temp3=sp.timestamp(0),
            temp4=0
        )

    def is_active_city(self, token_id):
        sp.verify(self.data.resource_map.contains(token_id),
                  "No city information for provided token_id")

    def initialize_city(self, token_id):
        self.data.resource_map[token_id] = sp.record(
            city_level=0,
            population_limit=50,
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

    def update_resource(self, token_id):
        self.is_active_city(token_id)
        duration_sec = sp.local('duration_sec', sp.now -
                                self.data.resource_map[token_id].last_claim_time)
        duration_day = sp.local('duration_day', sp.as_nat(
            duration_sec.value) // SECONDS_PER_DAY)

        self.data.resource_map[token_id].last_claim_time.add_seconds(
            duration_day.value * SECONDS_PER_DAY)
        self.data.resource_map[token_id].food += self.data.resource_map[token_id].food_per_epoch * duration_day.value
        self.data.resource_map[token_id].wood += self.data.resource_map[token_id].wood_per_epoch * duration_day.value
        self.data.resource_map[token_id].stone += self.data.resource_map[token_id].stone_per_epoch * duration_day.value
        self.data.resource_map[token_id].iron += self.data.resource_map[token_id].iron_per_epoch * duration_day.value

        self.data.temp1 = duration_sec.value
        self.data.temp2 = duration_day.value
        self.data.temp3 = self.data.resource_map[token_id].last_claim_time

    # def harvest_resource(self, token_id):


class GameGov(FA2.Admin, FA2.WithdrawMutez, NftOwnerCheck, ResourceStorage, BuildingCategories):
    def __init__(self, admin, nft_contract, building_categories, **kwargs):
        FA2.Admin.__init__(self, admin)
        ResourceStorage.__init__(self)
        NftOwnerCheck.__init__(self, nft_contract)
        BuildingCategories.__init__(self, building_categories)

    @sp.entry_point
    def start_game(self, token_id):
        self.is_valid_owner(sp.sender, token_id)
        sp.set_type(token_id, sp.TNat)
        self.initialize_city(token_id)
        sp.trace(self.data.resource_map)

    @sp.entry_point
    def harvest_resource(self, token_id):
        self.is_valid_owner(sp.sender, token_id)
        self.update_resource(token_id)


@ sp.add_test(name="Game Gov with Resource manager")
def test():
    sc = sp.test_scenario()
    nft_contract = NFTandVault.NftWithAdmin(
        admin=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"),
        metadata=sp.utils.metadata_of_url(
            "ipfs://bafkreigb6nsuvwc7vzx6oqzoaeaxno6liyr5rigbheg2ol7ndac75kawoe"
        ),
        token_metadata=[],
    )

    sc += nft_contract

    nft_contract.mint(
        [sp.record(to_=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"))]
    ).run(
        sender=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"), amount=sp.mutez(20500000))

    # nft_contract.mint([sp.address("tz1Zn3WK57gjcsk6WH8MD6jf4VEqXuRfgPFM")]).run(
    #     sender=sp.address("tz1Zn3WK57gjcsk6WH8MD6jf4VEqXuRfgPFM"), amount=sp.mutez(20500000))

    sc.show(nft_contract.data)

    c1 = GameGov(
        admin=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"),
        nft_contract=nft_contract.address,
        building_categories=sp.big_map(
            {}, tkey=sp.TNat, tvalue=T_BUILDING_CATEGORY)
    )
    sc += c1
    c1.start_game(0).run(sender=sp.address(
        "tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"))
    print(c1)


# A a compilation target (produces compiled code)
sp.add_compilation_target("GameGov_Compiled", GameGov(
    admin=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"),
    nft_contract=sp.address("KT1KFczzgYkxLqTGmhbBvmew12WN3qbkBq4E"),
    building_categories=sp.big_map(
        {}, tkey=sp.TNat, tvalue=T_BUILDING_CATEGORY)
))
