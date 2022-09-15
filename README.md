`Compile`

rm compilation -r & ~/smartpy-cli/SmartPy.sh compile ./contracts/result.py compilation

`Test`

rm test -r & ~/smartpy-cli/SmartPy.sh test ./contracts/result.py test

`Deploy`

~/smartpy-cli/SmartPy.sh originate-contract --code ~/Documents/tezos/smartpy-fa2/compilation/NftWithAdmin_Compiled/step_000_cont_0_contract.tz --storage ~/Documents/tezos/smartpy-fa2/compilation/NftWithAdmin_Compiled/step_000_cont_0_storage.tz --rpc https://rpc.tzkt.io/ghostnet --private-key [PVK]
