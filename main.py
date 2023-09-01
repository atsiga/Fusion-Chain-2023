from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

new_block = None
http_port = int(os.environ.get('HTTP_PORT', 3001))
p2p_port = int(os.environ.get('P2P_PORT', 6001))
initial_peers = os.environ.get('PEERS', '').split(',')

import network as nw  # Assuming you have a "network.py" module
import blockchain as bc  # Assuming you have a "blockchain.py" module
import ipfsapi

# Initialize IPFS client
ipfs = ipfsapi.connect('localhost', 5001)

@app.route('/blocks', methods=['POST'])
def get_block():
    index = request.json.get('index')
    with open(f'./Blockchain/blockfile{index}.txt', 'r', encoding='utf-8') as file:
        data = json.load(file)
        ipfs_hash = data[0]['ipfsHash']
        file_data = ipfs.cat(ipfs_hash)
        return file_data.decode('utf-8')

@app.route('/mineBlock', methods=['POST'])
def mine_block():
    global new_block
    block_data = request.json.get('data')
    new_block = bc.generateNextBlock(block_data)
    nw.selectLeader(True)
    nw.broadcast(nw.RequestPBFT(new_block))
    return jsonify({'message': 'Mining in progress'})

@app.route('/peers', methods=['GET'])
def get_peers():
    peers = [s._socket.getpeername() for s in nw.getSockets()]
    peer_addresses = [f"{host}:{port}" for host, port in peers]
    return jsonify(peer_addresses)

@app.route('/addPeer', methods=['POST'])
def add_peer():
    peer = request.json.get('peer')
    nw.connectToPeers([peer])
    return jsonify({'message': 'Peer added'})

if __name__ == "__main__":
    nw.connectToPeers(initial_peers)
    app.run(host='0.0.0.0', port=http_port)
    nw.initP2PServer()
