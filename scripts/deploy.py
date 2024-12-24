from brownie import BitcoinUpDown
from scripts.helpful_script import get_account, get_contract, getGasCost
import os, json, yaml, shutil
from web3 import Web3

# from web3.middleware import ExtraDataToPOAMiddleware


class UP_DOWN:
    UP = 0
    DOWN = 1


def deploy(publish_source=False):
    account = get_account()
    initial_seed = Web3.toWei(0.01, "ether")
    bitcoinUpDown = BitcoinUpDown.deploy(
        get_contract("btc_usd_price_feed").address,
        initial_seed,
        {"from": account, "value": initial_seed},
        publish_source=publish_source,
    )
    print("contract deployed !")
    return bitcoinUpDown


def placeBet(price, value, account=get_account()):
    bitcoinUpDown = BitcoinUpDown[-1]
    tx = bitcoinUpDown.bet(price, {"from": account, "value": value})
    tx.wait(1)
    print(f"{account} bet {Web3.fromWei(value, unit='ether')} on {price} !")


def endRound():
    account = get_account()
    bitcoinUpDown = BitcoinUpDown[-1]
    tx = bitcoinUpDown.endRound({"from": account})
    tx.wait(1)
    print(f"Winners: {bitcoinUpDown.getPrice()}")
    print(
        print(f"Total fee: {Web3.fromWei(bitcoinUpDown.devFeeBalance(), unit='ether')}")
    )


def withdraw(account=get_account()):
    bitcoinUpDown = BitcoinUpDown[-1]
    balance = account.balance()
    tx = bitcoinUpDown.withdraw({"from": account})
    tx.wait(1)
    amount = account.balance() - balance
    print(f"{account} withdraw {Web3.fromWei(amount, unit='ether')} succesufly !")


def update_front_end():  #
    # Send the build folder
    dest_path = "./predictify/src/"
    copy_folders_to_front_end("./build", dest_path + "chain-info")

    # Sending the front end our config in JSON format
    with open("brownie-config.yaml", "r") as brownie_config:
        config_dict = yaml.load(brownie_config, Loader=yaml.FullLoader)
        with open(dest_path + "brownie-config.json", "w") as brownie_config_json:
            json.dump(config_dict, brownie_config_json)
    print("Front end updated!")


def copy_folders_to_front_end(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def main():
    deploy(publish_source=False)
    update_front_end()
