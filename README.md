`Compile`

rm compilation -r & ~/smartpy-cli/SmartPy.sh compile ./contracts/NFTandVault.py compilation

rm compilation -r & ~/smartpy-cli/SmartPy.sh compile ./contracts/GameGov.py compilation

`Test`

rm test -r & ~/smartpy-cli/SmartPy.sh test ./contracts/NFTandVault.py test

rm test -r & ~/smartpy-cli/SmartPy.sh test ./contracts/GameGov.py test

`Deploy`

`NFT Deployment`

~/smartpy-cli/SmartPy.sh originate-contract --code /home/johan/Documents/tezos/CoC-tezos-p2e-game/compilation/NftWithAdmin_Compiled/step_000_cont_0_contract.tz --storage /home/johan/Documents/tezos/CoC-tezos-p2e-game/compilation/NftWithAdmin_Compiled/step_000_cont_0_storage.tz --rpc https://rpc.tzkt.io/ghostnet --private-key [PVK]

`GameGov Contract Deployment`

~/smartpy-cli/SmartPy.sh originate-contract --code /home/johan/Documents/tezos/CoC-tezos-p2e-game/compilation/GameGov_Compiled/step_000_cont_0_contract.tz --storage /home/johan/Documents/tezos/CoC-tezos-p2e-game/compilation/GameGov_Compiled/step_000_cont_0_storage.tz --rpc https://rpc.tzkt.io/ghostnet --private-key [PVK]
