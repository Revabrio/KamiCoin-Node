import time
import os
import hashlib
import json
import requests
import base64
from flask import Flask, request
from multiprocessing import Process, Pipe
import ecdsa
import logging
import log_miner
from miner_config import MINER_ADDRESS, MINER_NODE_URL, PEER_NODES

node = Flask(__name__)

#   Создание логеров для майнера
log = log_miner.create_log_flask()
logger = log_miner.create_log_console()


class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        """Returns a new Block object. Each block is "chained" to its previous
        by calling its unique hash.

        Args:
            index (int): Block number.
            timestamp (int): Block creation timestamp.
            data (str): Data to be sent.
            previous_hash(str): String representing previous block unique hash.

        Attrib:
            index (int): Block number.
            timestamp (int): Block creation timestamp.
            data (str): Data to be sent.
            previous_hash(str): String representing previous block unique hash.
            hash(str): Current block unique hash.

        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.hash_block()

    def hash_block(self):
        """Creates the unique hash for the block. It uses sha256."""
        logger.info('Создан хеш блока №%d', self.index)
        sha = hashlib.sha256()
        sha.update((str(self.index) + str(self.timestamp) + str(self.data) + str(self.previous_hash)).encode('utf-8'))
        return sha.hexdigest()


def create_genesis_block():
    """To create each block, it needs the hash of the previous one. First
    block has no previous, so it must be created manually (with index zero
     and arbitrary previous hash)"""
    logger.info('Создан первый блок')
    return Block(0, time.time(), {
        "proof-of-work": 9,
        "transactions": None},
                 "0")

"""
Это будущая реализация сохранения блокчейна по отдельным блокам. Т.е у каждого блока
будет свой уникальный файл, где он будет храниться
"""
# def get_blocks_from_memory(BLOCKCHAIN):
#     num_blocks = 0
#     blocks = []
#     for block in os.listdir("blocks"):
#         blocks.append(int(block))
#     blocks.sort()
#     for block in blocks:
#         with open(os.path.join("blocks", str(block)), 'r') as f:
#             block = json.loads(f.read())
#             mined_block = Block(block['index'], block['timestamp'], block['data'], block['previous_hash'])
#             BLOCKCHAIN.append(mined_block)
#         time.sleep(0.1)
#         num_blocks +=1
#         f.close()
#     return num_blocks, BLOCKCHAIN
#
#
# def write_new_block_to_memory(block_data):
#     with open(os.path.join("blocks", str(block_data.index)), 'w') as f:
#         block_json = json.dumps({
#             "index": block_data.index,
#             "timestamp": str(block_data.timestamp),
#             "data": block_data.data,
#             "previous_hash": block_data.previous_hash,
#             "hash": block_data.hash
#         })
#         f.write(str(block_json))
#         logger.info('Записали новый блок #%d в память', block_data.index)
#         f.close()


def get_blockchain_from_file():
    num_blocks = 0
    with open(os.path.join("blocks", 'blockchain'), 'r') as f:
        blockchain = json.loads(f.read())
        for key in blockchain.keys():
            block = json.loads(blockchain[key])
            saved_block = Block(block['index'], block['timestamp'], block['data'], block['previous_hash'])
            BLOCKCHAIN.append(saved_block)
            num_blocks +=1
    return num_blocks, BLOCKCHAIN


def write_blockchain_to_memory(blockchain):
    with open(os.path.join("blocks", 'blockchain'), 'w') as f:
        blockchain_json = {}
        for block in blockchain:
            blockchain_json[str(block.index)] = json.dumps({
                "index": block.index,
                "timestamp": str(block.timestamp),
                "data": block.data,
                "previous_hash": block.previous_hash,
                "hash": block.hash
            })
        f.write(json.dumps(blockchain_json))
        logger.info('Записали блокчейн в память')
        f.close()


BLOCKCHAIN = []
# Node's blockchain copy
try:
    num_blocks, BLOCKCHAIN = get_blockchain_from_file()
    logger.info('Нашли №%d блоков', num_blocks)
except:
    BLOCKCHAIN.append(create_genesis_block())
    write_blockchain_to_memory(BLOCKCHAIN)

"""
Это пример подгрузки по-блокового сохранения блокчейна.
"""
# try:
#     num_blocks, BLOCKCHAIN = get_blocks_from_memory(BLOCKCHAIN)
#     logger.info('Нашли №%d блоков', num_blocks)
# except:
#     BLOCKCHAIN.append(create_genesis_block())
#     block = BLOCKCHAIN[0]
#     write_new_block_to_memory(block)

""" Stores the transactions that this node has in a list.
If the node you sent the transaction adds a block
it will get accepted, but there is a chance it gets
discarded and your transaction goes back as if it was never
processed"""
NODE_PENDING_TRANSACTIONS = []


def proof_of_work(last_proof, blockchain):
    # Creates a variable that we will use to find our next proof of work
    incrementer = last_proof + 1
    # Keep incrementing the incrementer until it's equal to a number divisible by 7919
    # and the proof of work of the previous block in the chain
    start_time = time.time()
    while not (incrementer % 7919 == 0 and incrementer % last_proof == 0):
        incrementer += 1
        # Check if any node found the solution every 60 seconds
        if int((time.time() - start_time) % 60) == 0:
            # If any other node got the proof, stop searching
            new_blockchain = consensus(blockchain)
            if new_blockchain:
                # (False: another node got proof first, new blockchain)
                logger.info('Другая нода первой создала блок')
                return False, new_blockchain
    # Once that number is found, we can return it as a proof of our work
    # logger.info('Proof: %d', incrementer)
    return incrementer, blockchain


def mine(a, blockchain, node_pending_transactions):
    BLOCKCHAIN = blockchain
    NODE_PENDING_TRANSACTIONS = node_pending_transactions
    while True:
        """Mining is the only way that new coins can be created.
        In order to prevent too many coins to be created, the process
        is slowed down by a proof of work algorithm.
        """
        # Get the last proof of work
        last_block = BLOCKCHAIN[-1]
        last_proof = last_block.data['proof-of-work']
        # Find the proof of work for the current block being mined
        # Note: The program will hang here until a new proof of work is found
        proof = proof_of_work(last_proof, BLOCKCHAIN)
        # If we didn't guess the proof, start mining again
        if not proof[0]:
            # Update blockchain and save it to file
            logger.info('Proof не был найден, продолжаем майнинг')
            BLOCKCHAIN = proof[1]
            a.send(BLOCKCHAIN)
            continue
        else:
            # Once we find a valid proof of work, we know we can mine a block so
            # ...we reward the miner by adding a transaction
            # First we load all pending transactions sent to the node server
            NODE_PENDING_TRANSACTIONS = requests.get(url=MINER_NODE_URL + '/txion',
                                                     params={'update': MINER_ADDRESS}).content
            NODE_PENDING_TRANSACTIONS = json.loads(NODE_PENDING_TRANSACTIONS)
            # Then we add the mining reward
            NODE_PENDING_TRANSACTIONS.append({
                "from": "network",
                "to": MINER_ADDRESS,
                "amount": 1})
            # Now we can gather the data needed to create the new block
            new_block_data = {
                "proof-of-work": proof[0],
                "transactions": list(NODE_PENDING_TRANSACTIONS)
            }
            new_block_index = last_block.index + 1
            new_block_timestamp = time.time()
            last_block_hash = last_block.hash
            # Empty transaction list
            NODE_PENDING_TRANSACTIONS = []
            # Now create the new block
            mined_block = Block(new_block_index, new_block_timestamp, new_block_data, last_block_hash)
            logger.info('Создали новый блок:\n\tИндекс: %d\n\tДанные: %s\n\tHash: %s',
                        new_block_index, new_block_data, last_block_hash
                        )
            BLOCKCHAIN.append(mined_block)
            write_blockchain_to_memory(BLOCKCHAIN)
            a.send(BLOCKCHAIN)
            requests.get(url=MINER_NODE_URL + '/blocks', params={'update': MINER_ADDRESS})


def find_new_chains():
    # Get the blockchains of every other node
    other_chains = []
    for node_url in PEER_NODES:
        # Get their chains using a GET request
        block = requests.get(url=node_url + "/blocks").content
        # Convert the JSON object to a Python dictionary
        block = json.loads(block)
        # Verify other node block is correct
        validated = validate_blockchain(block)
        if validated:
            # Add it to our list
            other_chains.append(block)
    return other_chains


def consensus(blockchain):
    # Get the blocks from other nodes
    other_chains = find_new_chains()
    # If our chain isn't longest, then we store the longest chain
    BLOCKCHAIN = blockchain
    longest_chain = BLOCKCHAIN
    for chain in other_chains:
        if len(longest_chain) < len(chain):
            longest_chain = chain
    # If the longest chain wasn't ours, then we set our chain to the longest
    if longest_chain == BLOCKCHAIN:
        # Keep searching for proof
        return False
    else:
        # Give up searching proof, update chain and start over again
        logger.info('Обновляем цепь и перезапускаем процесс')
        BLOCKCHAIN = longest_chain
        return BLOCKCHAIN


def createBlockHash(block):
    """Creates the unique hash for the block. It uses sha256."""
    sha = hashlib.sha256()
    sha.update((str(block.index) + str(block.timestamp) + str(block.data) + str(block.previous_hash)).encode('utf-8'))
    return sha.hexdigest()


def validate_blockchain(block):
    """Проверка блока на валидность. На вход принимает блок, и с помощь функции
    createBlockHash генерирует хеш блока, и сравнивает его с хешем, записанным
    в самом блоке. Если они одинаковы, возвращает True, иначе False
    block(str): json
    """
    if createBlockHash(block) == block.hash:
        logger.info('Проверка блока №%d была успешна', block.index)
        return True
    else:
        logger.info('Проверка блока №%d была не успешна', block.index)
        return False


@node.route('/blocks', methods=['GET'])
def get_blocks():
    # Load current blockchain. Only you should update your blockchain
    if request.args.get("update") == MINER_ADDRESS:
        global BLOCKCHAIN
        BLOCKCHAIN = pipe_input.recv()
    chain_to_send = BLOCKCHAIN
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


def get_wallet_balance(wallet_address):
    balance = 0
    chain_to_send = BLOCKCHAIN
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
            for transaction in NODE_PENDING_TRANSACTIONS:
                if transaction['from'] == wallet_address:
                    balance -= int(transaction['amount'])
                if transaction['to'] == wallet_address:
                    balance += int(transaction['amount'])
    return balance


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
                NODE_PENDING_TRANSACTIONS.append(new_txion)
                # Because the transaction was successfully
                # submitted, we log it to our console
                # print("New transaction")
                # print("FROM: {0}".format(new_txion['from']))
                # print("TO: {0}".format(new_txion['to']))
                # print("AMOUNT: {0}\n".format(new_txion['amount']))
                # Then we let the client know it worked out
                logger.info('Получили новую успешную транз-акцию\n\tОт: %s\n\tК: %s\n\tСумма: %s',
                            new_txion['from'], new_txion['to'], new_txion['amount']
                            )
                return "Transaction submission successful\n"
            else:
                logger.info('Новая полученная транз-акция провалилась, недостаточный баланс у отправителя.')
                return "Transaction not successful, your balance < transaction\n"
        else:
            logger.info('Новая полученная транз-акция провалилась, подпись не верна.')
            return "Transaction submission failed. Wrong signature\n"
    # Send pending transactions to the mining process
    elif request.method == 'GET' and request.args.get("update") == MINER_ADDRESS:
        pending = json.dumps(NODE_PENDING_TRANSACTIONS, sort_keys=True)
        # Empty transaction list
        NODE_PENDING_TRANSACTIONS[:] = []
        return pending


def validate_signature(public_key, signature, message):
    """Verifies if the signature is correct. This is used to prove
    it's you (and not someone else) trying to do a transaction with your
    address. Called when a user tries to submit a new transaction.
    """
    public_key = (base64.b64decode(public_key)).hex()
    signature = base64.b64decode(signature)
    vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)
    # Try changing into an if/else statement as except is too broad.
    try:
        return vk.verify(signature, message.encode())
    except:
        return False


def welcome_msg():
    print("""       =========================================\n
            KAMICOIN v1.0.0 - BLOCKCHAIN SYSTEM\n
           =========================================\n\n
            """)


if __name__ == '__main__':
    welcome_msg()
    # Start mining
    logger.info('Запустили программу майнинга')
    pipe_output, pipe_input = Pipe()
    miner_process = Process(target=mine, args=(pipe_output, BLOCKCHAIN, NODE_PENDING_TRANSACTIONS))
    miner_process.start()

    logger.info('Запустили программу ноды')
    # Start server to receive transactions
    transactions_process = Process(target=node.run(), args=pipe_input)
    transactions_process.start()
