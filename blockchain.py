import hashlib
import json
import os
import ipfsapi
import time
import requests
from typing import List

# Initialize IPFS client
ipfs = ipfsapi.connect('localhost', 5001)

# Define the Block class
class Block:
    def __init__(self, index, previous_hash, timestamp, data, hash):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.hash = hash

# Define the BlockIPFS class
class BlockIPFS:
    def __init__(self, index, ipfs_hash):
        self.index = index
        self.ipfs_hash = ipfs_hash

# Initialize variables
new_block = None
blockchain = []
check_first = ""
block_file_buffer = None

# Define functions
def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

def get_genesis_block():
    global blockchain
    file_path = './Blockchain/blockfile0.txt'
    check_first = read_file(file_path)
    if os.environ.get('HTTP_PORT') == '3001' and not check_first:
        genesis_block = Block(0, "0", 1465154705, "Genesis Block", "816534932c2b7154836da6afc367695e6337db8a921823784c14378abed4f7d7")
        blockchain.append(genesis_block)
        write_file(file_path, json.dumps([block.__dict__ for block in blockchain]))
        block_array = []
        block_file_buffer = read_file(file_path).encode()
        ipfs_response = ipfs.add(block_file_buffer)
        os.remove(file_path)
        block_array.append(BlockIPFS(0, ipfs_response[0]['Hash']))
        write_file(file_path, json.dumps([block.__dict__ for block in block_array]))
    return Block(0, "0", 1465154705, "Genesis Block", "816534932c2b7154836da6afc367695e6337db8a921823784c14378abed4f7d7")

def get_blockchain():
    global blockchain
    return blockchain

def get_latest_block():
    global blockchain
    return blockchain[-1] if blockchain else None

def calculate_hash(index, previous_hash, timestamp, data):
    value = str(index) + previous_hash + str(timestamp) + data
    return hashlib.sha256(value.encode()).hexdigest()

def calculate_hash_for_block(block):
    return calculate_hash(block.index, block.previous_hash, block.timestamp, block.data)

def is_valid_new_block(new_block, previous_block):
    if previous_block.index + 1 != new_block.index:
        return False
    if previous_block.hash != new_block.previous_hash:
        return False
    if calculate_hash_for_block(new_block) != new_block.hash:
        return False
    return True

def add_block(new_block):
    global blockchain
    if is_valid_new_block(new_block, get_latest_block()):
        blockchain.append(new_block)

def get_new_block():
    global new_block
    return new_block

def generate_next_block(block_data):
    global new_block
    previous_block = get_latest_block()
    next_index = previous_block.index + 1
    next_timestamp = int(time.time())
    next_hash = calculate_hash(next_index, previous_block.hash, next_timestamp, block_data)
    new_block = Block(next_index, previous_block.hash, next_timestamp, block_data, next_hash)
    return new_block

def generate_ipfs_block(block):
    global new_block
    new_block_array = []
    block_index = block.index
    new_block_array.append(block)
    block_file_buffer = json.dumps([block.__dict__]).encode()
    new_block_array.clear()
    ipfs_response = ipfs.add_bytes(block_file_buffer)
    write_file('./Blockchain/blockfile' + str(block.index) + '.txt', json.dumps([block.__dict__ for block in new_block_array]))
    return BlockIPFS(block_index, ipfs_response[0]['Hash'])

def get_block_from_ipfs(ipfs_hash):
    return 0

def replace_chain(new_blocks):
    global blockchain
    if is_valid_chain(new_blocks) and len(new_blocks) > len(blockchain):
        blockchain = new_blocks
        nw.broadcast(response_latest_msg())

def is_valid_chain(blockchain_to_validate):
    if json.dumps(blockchain_to_validate[0].__dict__) != json.dumps(get_genesis_block().__dict__):
        return False
    temp_blocks = [blockchain_to_validate[0]]
    for i in range(1, len(blockchain_to_validate)):
        if is_valid_new_block(blockchain_to_validate[i], temp_blocks[i - 1]):
            temp_blocks.append(blockchain_to_validate[i])
        else:
            return False
    return True

def encrypt(to_encrypt, relative_or_absolute_path_to_public_key):
    absolute_path = os.path.abspath(relative_or_absolute_path_to_public_key)
    with open(absolute_path, 'r') as public_key_file:
        public_key = public_key_file.read()
    encrypted = crypto.public_encrypt(to_encrypt.encode(), crypto.load_publickey(crypto.FILETYPE_PEM, public_key))
    return encrypted.decode()

def decrypt(to_decrypt, relative_or_absolute_path_to_private_key):
    absolute_path = os.path.abspath(relative_or_absolute_path_to_private_key)
    with open(absolute_path, 'r') as private_key_file:
        private_key = private_key_file.read()
    decrypted = crypto.private_decrypt(to_decrypt.encode(), crypto.load_privatekey(crypto.FILETYPE_PEM, private_key))
    return decrypted

# Exported functions
def response_latest_msg():
    return {'type': 2, 'data': json.dumps([get_latest_block().__dict__])}

def init_p2p_server():
    pass

def select_leader(result):
    pass

def request_prevote(new_block):
    pass

def request_commit(new_block):
    pass

def send_prevote_msg(new_block):
    pass

def send_not_prevote_msg(new_block):
    pass

def send_commit_msg():
    pass

def send_not_commit_msg():
    pass

# Main execution
if __name__ == "__main__":
    # Modify this section to execute the desired functionality.
    pass
