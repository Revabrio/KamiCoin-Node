from multiprocessing import Process, Pipe
from core import mine, get_blockchain_from_file, write_blockchain_to_memory, create_genesis_block
from api.app import node

#   Создание логеров для майнера
#log = log_miner.create_log_flask()
#logger = log_miner.create_log_console()

if get_blockchain_from_file() == []:
    BLOCKCHAIN = []
    BLOCKCHAIN.append(create_genesis_block())
    write_blockchain_to_memory(BLOCKCHAIN)

# # Node's blockchain copy
# try:
#     num_blocks, BLOCKCHAIN = get_blockchain_from_file()
#     #logger.info('Нашли №%d блоков', num_blocks)
# except:
#     BLOCKCHAIN.append(create_genesis_block())
#     write_blockchain_to_memory(BLOCKCHAIN)

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



def welcome_msg():
    print("""       =========================================\n
            KAMICOIN v1.0.0 - BLOCKCHAIN SYSTEM\n
           =========================================\n\n
            """)



if __name__ == '__main__':
    welcome_msg()
    # Start mining
    pipe_output, pipe_input = Pipe()
    miner_process = Process(target=mine, args=(pipe_output,))
    miner_process.start()

    # Start server to receive transactions
    transactions_process = Process(target=node.run(), args=pipe_input)
    transactions_process.start()
