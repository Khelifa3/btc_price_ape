import os
from ape_accounts import import_account_from_private_key

def main():
    alias = "main_account"
    passphrase = "oddmeta12"
    private_key = os.environ["PKMM"]

    account = import_account_from_private_key(alias, passphrase, private_key)

    print(f'Your imported account address is: {account.address}')