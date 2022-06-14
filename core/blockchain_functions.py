import time
import json
import ecdsa
import base64
import hashlib
import requests
from .block import Block
from .database_functions import get_peer_nodes_from_file
from .database_functions import get_blockchain_from_file, write_blockchain_to_memory

def create_genesis_block():
    """To create each block, it needs the hash of the previous one. First
    block has no previous, so it must be created manually (with index zero
     and arbitrary previous hash)"""
    return Block(0, time.time(), {
        "proof-of-work": 9,
        "transactions": None},
                 "0")

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
        return True
    else:
        return False

def proof_of_work(last_proof):
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
            new_blockchain = consensus()
            if new_blockchain == True:
                # (False: another node got proof first, new blockchain)
                return False, new_blockchain
    # Once that number is found, we can return it as a proof of our work
    return incrementer, new_blockchain


def find_new_chains():
    # Get the blockchains of every other node
    other_chains = []
    for node_url in get_peer_nodes_from_file():
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


def consensus():
    # Get the blocks from other nodes
    other_chains = find_new_chains()
    # If our chain isn't longest, then we store the longest chain
    longest_chain = []
    for chain in other_chains:
        if len(longest_chain) < len(chain):
            longest_chain = chain
    # If the longest chain wasn't ours, then we set our chain to the longest
    if longest_chain <= get_blockchain_from_file():
        # Keep searching for proof
        return False
    else:
        # Give up searching proof, update chain and start over again
        #write_blockchain_to_memory(longest_chain)
        return True

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