import json
import os
import asyncio
import websockets

from enum import Enum

# Assuming you have network and blockchain modules in the same directory
import network as nw
import blockchain as bc

sockets = []
consensus = False
initialPeers = os.environ.get('PEERS', '').split(',')
p2p_port = int(os.environ.get('P2P_PORT', 6001))

getMessageCount = 0
getValidationValue = 0
leader = False
nodeNum = 0
newBlock = None

class MessageType(Enum):
    QUERY_LATEST = 0
    QUERY_ALL = 1
    RESPONSE_BLOCKCHAIN = 2
    REQUEST_PREVOTE = 3
    GET_PREVOTE = 4
    REQUEST_COMMIT = 5
    GET_COMMIT = 6

async def connectToPeers(newPeers):
    for peer in newPeers:
        async with websockets.connect(peer) as ws:
            await initConnection(ws)

async def initP2PServer():
    async with websockets.serve(initConnection, "0.0.0.0", p2p_port):
        await asyncio.Future()

async def initConnection(ws, path=None):
    sockets.append(ws)
    await initMessageHandler(ws)
    await initErrorHandler(ws)
    await write(ws, queryChainLengthMsg())

def minusNode():
    global nodeNum
    nodeNum -= 1

async def initMessageHandler(ws):
    async for data in ws:
        message = json.loads(data)
        await handleMessage(ws, message)

async def handleMessage(ws, message):
    global getMessageCount, getValidationValue, consensus, leader, nodeNum, newBlock

    if message['type'] == MessageType.QUERY_LATEST.value:
        await write(ws, responseLatestMsg())
    elif message['type'] == MessageType.QUERY_ALL.value:
        await write(ws, responseChainMsg())
    elif message['type'] == MessageType.RESPONSE_BLOCKCHAIN.value:
        await handleBlockchainResponse(message)
    elif message['type'] == MessageType.REQUEST_PREVOTE.value:
        if bc.isValidNewBlock(message['data'], bc.getLatestBlock()):
            await broadcast(sendPreVoteMsg(message['data']))
        else:
            await broadcast(sendNotPreVoteMsg(message['data']))
    elif message['type'] == MessageType.GET_PREVOTE.value:
        if not leader:
            nodeNum = len(sockets) - 1
            consensus = False
            getMessageCount += 1
            getValidationValue += message['count']
            
            if nodeNum == getMessageCount:
                if nodeNum == getValidationValue:
                    consensus = True
                
                if consensus:
                    await broadcast(RequestCOMMIT(message['data']))
                    getMessageCount = 0
                    getValidationValue = 0
                else:
                    getMessageCount = 0
                    getValidationValue = 0
    elif message['type'] == MessageType.REQUEST_COMMIT.value:
        if not leader:
            if bc.isValidNewBlock(message['data'], bc.getLatestBlock()):
                await broadcast(sendCommitMsg())
            else:
                await broadcast(sendNotCommitMsg())
                
    elif message['type'] == MessageType.GET_COMMIT.value:
        if not leader:
            nodeNum = len(sockets)
            consensus = False
            getMessageCount += 1
            getValidationValue += message['data']
            
            if nodeNum == getMessageCount:
                if nodeNum == getValidationValue:
                    consensus = True
                
                if consensus:
                    bc.addBlock(bc.getNewBlock())
                    bc.generateIPFSBlock(bc.getNewBlock())
                    await broadcast(responseLatestMsg())
                    getMessageCount = 0
                    getValidationValue = 0
                    leader = False
                else:
                    getMessageCount = 0
                    getValidationValue = 0

async def initErrorHandler(ws):
    async for _ in ws:
        await closeConnection(ws)

async def closeConnection(ws):
    sockets.remove(ws)

async def handleBlockchainResponse(message):
    receivedBlocks = sorted(json.loads(message['data']), key=lambda x: x['index'])
    latestBlockReceived = receivedBlocks[-1]
    latestBlockHeld = bc.getLatestBlock()
    
    if latestBlockReceived['index'] > latestBlockHeld['index']:
        if latestBlockHeld['hash'] == latestBlockReceived['previousHash']:
            bc.addBlock(latestBlockReceived)
            await broadcast(responseLatestMsg())
        elif len(receivedBlocks) == 1:
            await broadcast(queryAllMsg())
        else:
            await replaceChain(receivedBlocks)

def getSockets():
    return sockets

def selectLeader(result):
    global leader
    leader = result

def queryChainLengthMsg():
    return json.dumps({'type': MessageType.QUERY_LATEST.value})

def queryAllMsg():
    return json.dumps({'type': MessageType.QUERY_ALL.value})

def responseChainMsg():
    return json.dumps({'type': MessageType.RESPONSE_BLOCKCHAIN.value, 'data': json.dumps(bc.getBlockchain())})

def responseLatestMsg():
    return json.dumps({'type': MessageType.RESPONSE_BLOCKCHAIN.value, 'data': json.dumps([bc.getLatestBlock()])})

def RequestPBFT(newBlock):
    return json.dumps({'type': MessageType.REQUEST_PREVOTE.value, 'data': newBlock})

def RequestCOMMIT(newBlock):
    return json.dumps({'type': MessageType.REQUEST_COMMIT.value, 'data': newBlock})

def sendPreVoteMsg(newBlock):
    return json.dumps({'type': MessageType.GET_PREVOTE.value, 'data': newBlock, 'count': 1})

def sendNotPreVoteMsg(newBlock):
    return json.dumps({'type': MessageType.GET_PREVOTE.value, 'data': newBlock, 'count': 0})

def sendCommitMsg():
    return json.dumps({'type': MessageType.GET_COMMIT.value, 'data': 1})

def sendNotCommitMsg():
    return json.dumps({'type': MessageType.GET_COMMIT.value, 'data': 0})

async def write(ws, message):
    await ws.send(message)

async def broadcast(message):
    await asyncio.gather(*[write(socket, message) for socket in sockets])

if __name__ == "__main__":
    nw.connectToPeers(initialPeers)
    asyncio.run(initP2PServer())
