from .database_functions import get_peer_nodes_from_file
from .database_functions import get_blockchain_from_file

def get_wallet_balance(wallet_address):
    balance = 0
    chain_to_send = get_blockchain_from_file()
    for block in chain_to_send:
        data = block.data
        transactions = data['transactions']
        if transactions == None:
            pass
        else:
            for transaction in transactions:
                if transaction['from'] == wallet_address:
                    balance -= int(transaction['amount'])
                if transaction['to'] == wallet_address:
                    balance += int(transaction['amount'])
            for transaction in get_peer_nodes_from_file():
                if transaction['from'] == wallet_address:
                    balance -= int(transaction['amount'])
                if transaction['to'] == wallet_address:
                    balance += int(transaction['amount'])
    return balance