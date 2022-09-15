import smartpy as sp

FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/fa2_lib.py")
Utils = sp.io.import_script_from_url(
    "https://raw.githubusercontent.com/RomarQ/tezos-sc-utils/main/smartpy/utils.py")


def string_of_nat(params):
    c = sp.map({x: str(x) for x in range(0, 10)})
    x = sp.local('x', params)
    res = sp.local('res', [])
    with sp.if_(x.value == 0):
        res.value.push('0')
    with sp.while_(0 < x.value):
        res.value.push(c[x.value % 10])
        x.value //= 10
    return sp.concat(res.value)


class MultiAdmin:
    """(Mixin) Provide the basics for having an administrator in the contract.

    Adds an `administrator` attribute in the storage record. Provides a
    `set_administrator` entrypoint. Provides a `is_administrator` meta-
    programming function.
    """

    def __init__(self, administrators=[]):
        self.update_initial_storage(administrators=administrators)

    def is_administrator(self, sender):
        result = sp.local('result', False)
        with sp.for_("administrator", self.data.administrators) as administrator:
            with sp.if_(sp.fst(administrator) == sender):
                result.value = True
        sp.trace(result.value)
        return result.value

    @sp.entry_point
    def set_administrators(self, params):

        sp.set_type(
            params,
            sp.TList(
                sp.TPair(
                    sp.TAddress,
                    sp.TNat
                )
            ),
        )
        """(Admin only) Set the contract administrator."""
        sp.verify(self.is_administrator(sp.sender), message="FA2_NOT_ADMIN")
        self.data.administrators = params


class PublicMintNft(sp.Contract):
    """(Mixin) Non-standard `mint` entrypoint for FA2Nft with incrementing id.

    Requires the `Admin` mixin.
    """

    def __init__(self, whitelist=[]):
        self.update_initial_storage(
            whitelist=sp.set(
                whitelist
            ),
            string_of_nat=''
        )

    @sp.entry_point
    def toggleWhitelist(self, params):
        sp.verify(self.is_administrator(sp.sender), "FA2_NOT_ADMIN")
        with sp.if_(self.data.whitelist.contains(params)):
            self.data.whitelist.remove(params)
        with sp.else_():
            self.data.whitelist.add(params)

    @sp.offchain_view()
    def whitelist(self):
        sp.result(self.data.whitelist)

    # check sp.amount
    # sef.data.whitelist

    @sp.entry_point
    def test_string_of_nat(self, params):
        self.data.string_of_nat = string_of_nat(params)

    @sp.entry_point
    def mint(self, batch):
        """Admin can mint new or existing tokens."""
        sp.set_type(
            batch,
            sp.TList(
                sp.TRecord(
                    to_=sp.TAddress,
                ).layout(("to_"))
            ),
        )
        # sp.verify(self.is_administrator(sp.sender), "FA2_NOT_ADMIN")

        with sp.if_(self.data.whitelist.contains(sp.sender)):
            sp.verify(sp.amount >= sp.tez(15),
                      "INSUFFICIENT AMOUNT OF TEZOS - WHITELISTED")
        with sp.else_():
            sp.verify(sp.amount >= sp.tez(20),
                      "INSUFFICIENT AMOUNT OF TEZOS - NOT WHITELISTED")

        with sp.for_("action", batch) as action:
            token_id = sp.compute(self.data.last_token_id)
            metadata = sp.record(token_id=token_id, token_info=sp.map(
                l={
                    '':  Utils.Bytes.of_string(sp.concat([
                        "ipfs://QmWoCRq4iXnUwzMF2JUUxSbXsTSiuitxvWiYQ27XXusfNu/",
                        string_of_nat(token_id), ".json"])),
                    # sp.utils.bytes_of_string(
                    #     sp.concat([
                    #         "ipfs://QmWoCRq4iXnUwzMF2JUUxSbXsTSiuitxvWiYQ27XXusfNu/",
                    #         res, ".json"])
                    # ),
                }))
            self.data.token_metadata[token_id] = metadata
            self.data.ledger[token_id] = action.to_
            self.data.last_token_id += 1


class NftWithAdmin(FA2.Admin, FA2.WithdrawMutez, PublicMintNft, FA2.Fa2Nft):
    def __init__(self, admin, **kwargs):
        FA2.Fa2Nft.__init__(self, **kwargs)
        FA2.Admin.__init__(self, admin)
        PublicMintNft.__init__(self)


class VaultContract(MultiAdmin, sp.Contract):
    def __init__(self, administrators, **kwargs):
        MultiAdmin.__init__(self, administrators)

    @sp.entry_point
    def default(self):
        pass

    @sp.entry_point
    def distribute_mutez(self):
        """(Admin only) Transfer `amount` mutez to `destination`."""
        sp.verify(self.is_administrator(sp.sender), message="FA2_NOT_ADMIN")
        _current_balance = sp.balance

        with sp.for_("administrator", self.data.administrators) as administrator:
            sp.send(sp.fst(administrator),
                    sp.split_tokens(_current_balance, sp.snd(administrator), 100))

        # sp.send(self.data.administrators[1],
        #         sp.mutez(_current_balance - _current_balance * 5 / 100))

    @sp.offchain_view()
    def some_computation(self, sender):
        sp.result(self.is_administrator(sender))


tok0_md = sp.map(l={
    "": sp.utils.bytes_of_string(
        "ipfs://QmTq1FXht8jFc9CaW2j2hJ3bMjLqgAJhr3bxjcJ723TaHT"
    ),
})


tok1_md = FA2.make_metadata(name="Token One", decimals=1, symbol="Tok1")
tok2_md = FA2.make_metadata(name="Token Two", decimals=1, symbol="Tok2")
TOKEN_METADATA = [tok0_md, tok1_md, tok2_md]
METADATA = sp.utils.metadata_of_url(
    "ipfs://bafkreiels7nywfxi6tcmj7j6cbmtqh7uoeneun6hqc4i5ngd3w74p2thn4")


alice = sp.test_account("Alice")
bob = sp.test_account("bob")
cat = sp.test_account("cat")


@ sp.add_test(name="NFT with admin and mint")
def test():
    sc = sp.test_scenario()

    # c1 = NftWithAdmin(
    #     admin=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"),
    #     metadata=METADATA,
    #     token_metadata=[],
    # )
    # sc += c1
    # c1.test_string_of_nat(12345678901234)
    # sc.show(c1.data)

    # c1.toggleWhitelist(sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR")).run(
    #     sender=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"))

    # c1.mint([sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR")]).run(
    #     sender=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"), amount=sp.mutez(20500000))

    # sc.show(c1.testString())

    c2 = VaultContract(administrators=sp.list([
        sp.pair(sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"), 5),
        sp.pair(sp.address("tz1RvzEdTPbT3Y6h1LEjzw6PcVrZoryCHY7S"), 95)
    ]))
    #  Below line must be written before contract interaction
    sc += c2

    sc.show(c2.some_computation(sp.address(
        "tz1RvzEdTPbT3Y6h1LEjzw6PcVrZoryCHY7S")))
    sc.show(c2.some_computation(sp.address(
        "tz1Zn3WK57gjcsk6WH8MD6jf4VEqXuRfgPFM")))


# A a compilation target (produces compiled code)
sp.add_compilation_target("NftWithAdmin_Compiled", NftWithAdmin(
    admin=sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"),
    metadata=sp.utils.metadata_of_url(
        "ipfs://bafkreigb6nsuvwc7vzx6oqzoaeaxno6liyr5rigbheg2ol7ndac75kawoe"
    ),
    token_metadata=[],
))

# A a compilation target (produces compiled code)
sp.add_compilation_target("Vault_Compiled", VaultContract(
    administrators=sp.list([
        sp.pair(sp.address("tz1i66XefcqsNVSGa2iFsWb8qxokm3neVpFR"), 5),
        sp.pair(sp.address("tz1RvzEdTPbT3Y6h1LEjzw6PcVrZoryCHY7S"), 95)
    ])
))
