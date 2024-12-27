from ape import accounts, project, networks
import os, json, yaml, shutil
from web3 import Web3

# from web3.middleware import ExtraDataToPOAMiddleware
PRICE_FEED_ADDRESS_TEST = "0x5741306c21795FdCBb9b265Ea0255F499DFe515C"
PRICE_FEED_ADDRESS = "0x264990fbd0A4796A3E3d8E37C4d5F87a3aCa5Ebf"
INITIAL_SEED = Web3.to_wei(0.01, "ether")

def deploy(publish_source=False):
    account = accounts.load("main_account")
    # Connect to BSC Testnet
    with networks.bsc.testnet.use_provider("https://data-seed-prebsc-1-s1.binance.org:8545") as provider:
        print(provider.name)
        print(account.balance)
        contract = account.deploy(
            project.Predictify,
            PRICE_FEED_ADDRESS_TEST,
            INITIAL_SEED,
            value=INITIAL_SEED,
        )
        print(f"contract deployed at: {contract.address}")
        with open('./.build/contract.json', "w") as f:
            json_data = {"contract_address" : contract.address, "abi":contract.abi}
            json.dump(json_data, f)
    return contract


def update_front_end():  #
    # Send the build folder
    dest_path = "./predictify/src/"
    copy_folders_to_front_end("./.build", dest_path + "chain-info")

    # Sending the front end our config in JSON format
    with open("ape-config.yaml", "r") as brownie_config:
        config_dict = yaml.load(brownie_config, Loader=yaml.FullLoader)
        with open(dest_path + "brownie-config.json", "w") as brownie_config_json:
            json.dump(config_dict, brownie_config_json)
    print("Front end updated!")


def copy_folders_to_front_end(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def main():
    #deploy(publish_source=False)
    update_front_end()
