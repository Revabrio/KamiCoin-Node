import os
import json
from .block import Block

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
    BLOCKCHAIN = []
    with open("blocks/blockchain", 'r') as f:
        try:
            blockchain = json.loads(f.read())
            for key in blockchain.keys():
                block = json.loads(blockchain[key])
                saved_block = Block(block['index'], block['timestamp'], block['data'], block['previous_hash'])
                BLOCKCHAIN.append(saved_block)
        except:
            return BLOCKCHAIN
    return BLOCKCHAIN


def write_blockchain_to_memory(blockchain):
    with open("blocks/blockchain", 'w') as f:
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
        f.close()


def get_peer_nodes_from_file():
    peer_nodes = []
    with open('blocks/peer_nodes', 'r') as f:
        try:
            nodes = json.loads(f.read())
            for node in nodes:
                peer_nodes.append(node)
        except:
            return peer_nodes
    return peer_nodes

def write_peer_nodes_to_memory(node):
    with open('blocks/peer_nodes', 'a') as f:
        f.write(node)
        f.close()

def get_pending_transacrions_from_file():
    pending_transactions = []
    num_blocks = 0
    with open("blocks/pending_transactions", 'r') as f:
        try:
            transactions = json.loads(f.read())
            for key in transactions.keys():
                transaction = json.loads(transactions[key])
                pending_transactions.append(transaction)
                num_blocks +=1
        except:
            return pending_transactions
    return pending_transactions


def write_pending_transacrions_to_memory(transaction):
    with open("blocks/pending_transactions", 'a') as f:
        transactions_json = {}
        transactions_json[str(transaction['signature'])] = json.dumps({
            "from": transaction['from'],
            "to": transaction['to'],
            "amount": transaction['amount'],
            "signature": transaction['signature'],
            "message": transaction['message']
        })
        f.write(json.dumps(transactions_json))
        f.close()

def clear_blockchain():
    with open("blocks/blockchain", 'w'):
        pass

def clear_peer_nodes():
    with open("blocks/peer_nodes" 'w'):
        pass

def clear_pending_transacrions():
    with open("blocks/pending_transactions", 'w'):
        pass