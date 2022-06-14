import json
from flask import Flask, request
from multiprocessing import Process, Pipe
from miner_config import MINER_ADDRESS
from core import validate_signature, get_blockchain_from_file, get_pending_transacrions_from_file, get_wallet_balance, write_pending_transacrions_to_memory, clear_pending_transacrions

node = Flask(__name__)

pipe_input = Pipe()

@node.route('/blocks', methods=['GET'])
def get_blocks():
    # Load current blockchain. Only you should update your blockchain
    if request.args.get("update") == MINER_ADDRESS:
        BLOCKCHAIN = get_blockchain_from_file()
    chain_to_send = get_blockchain_from_file()
    # Converts our blocks into dictionaries so we can send them as json objects later
    chain_to_send_json = []
    for block in chain_to_send:
        block = {
            "index": str(block.index),
            "timestamp": str(block.timestamp),
            "data": str(block.data),
            "hash": block.hash
        }
        chain_to_send_json.append(block)

    # Send our chain to whomever requested it
    chain_to_send = json.dumps(chain_to_send_json, sort_keys=True)
    return chain_to_send


@node.route('/txion', methods=['GET', 'POST'])
def transaction():
    """Each transaction sent to this node gets validated and submitted.
    Then it waits to be added to the blockchain. Transactions only move
    coins, they don't create it.
    """
    if request.method == 'POST':
        # On each new POST request, we extract the transaction data
        new_txion = request.get_json()
        # Then we add the transaction to our list
        if validate_signature(new_txion['from'], new_txion['signature'], new_txion['message']):
            if int(get_wallet_balance(new_txion['from'])) > int(new_txion['amount']):
                write_pending_transacrions_to_memory(new_txion)
                # Because the transaction was successfully
                # submitted, we log it to our console
                # print("New transaction")
                # print("FROM: {0}".format(new_txion['from']))
                # print("TO: {0}".format(new_txion['to']))
                # print("AMOUNT: {0}\n".format(new_txion['amount']))
                # Then we let the client know it worked out
                return "Transaction submission successful\n"
            else:
                return "Transaction not successful, your balance < transaction\n"
        else:
            return "Transaction submission failed. Wrong signature\n"
    # Send pending transactions to the mining process
    elif request.method == 'GET' and request.args.get("update") == MINER_ADDRESS:
        pending = json.dumps(get_pending_transacrions_from_file(), sort_keys=True)
        # Empty transaction list
        clear_pending_transacrions()
        return pending