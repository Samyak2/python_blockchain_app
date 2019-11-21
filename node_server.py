from hashlib import sha256
import simplejson as json
import time
import pickle

from flask import Flask, request
# from flask_sqlalchemy import SQLAlchemy
# import requests

import pyrebase
from dotenv import load_dotenv
load_dotenv()
from urllib.parse import unquote
import os
from blockchain import Block, Blockchain, peers
# from flaskdb import db
# from config import Transaction, metadata

BASE_COINS = 10.00000
MIN_COINS = 0.0001

config = {
  "apiKey": os.getenv("FIREBASE_API_KEY"),
  "authDomain": "blockchat-warriors.firebaseapp.com",
  "databaseURL": "https://blockchat-warriors.firebaseio.com/",
  "storageBucket": "blockchat-warriors.appspot.com",
#   "serviceAccount": "blockchat-warriors-firebase-adminsdk-cihe4-a592ce5c9b.json",
    'serviceAccount': {
        # Your "Service account ID," which looks like an email address.
        'client_email': os.environ['FIREBASE_CLIENT_EMAIL'], 
        # The part of your Firebase database URL before `firebaseio.com`. 
        # e.g. `fiery-flames-1234`
        'client_id': os.environ['FIREBASE_CLIENT_ID'],
        # The key itself, a long string with newlines, starting with 
        # `-----BEGIN PRIVATE KEY-----\n`
        'private_key': os.environ['FIREBASE_PRIVATE_KEY'].replace('\\n', '\n'),
        # Your service account "key ID." Mine is 40 alphanumeric characters.
        'private_key_id': os.environ['FIREBASE_PRIVATE_KEY_ID'],
        'type': 'service_account'
    },
}

firebase = pyrebase.initialize_app(config)

storage = firebase.storage()

import encryption

# class Block:
#     def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
#         self.index = index
#         self.transactions = transactions
#         self.timestamp = timestamp
#         self.previous_hash = previous_hash
#         self.nonce = nonce

#     def compute_hash(self):
#         """
#         A function that return the hash of the block contents.
#         """
#         block_string = json.dumps(self.__dict__, sort_keys=True)
#         return sha256(block_string.encode()).hexdigest()


# class Blockchain:
#     # difficulty of our PoW algorithm
#     difficulty = 3

#     def __init__(self):
#         self.unconfirmed_transactions = []
#         self.chain = []
#         if os.environ['LOAD_CHAIN'] == "true":
#             storage.child("/blockchain.pkl").download("blockchain.pkl")
#             try:
#                 with open("blockchain.pkl", "rb") as f:
#                     self.chain = pickle.load(f)
#             except FileNotFoundError:
#                 self.chain = []
#         else:
#             self.chain = []

#     def create_genesis_block(self):
#         """
#         A function to generate genesis block and appends it to
#         the chain. The block has index 0, previous_hash as 0, and
#         a valid hash.
#         """
#         genesis_block = Block(0, [], time.time(), "0")
#         genesis_block.hash = genesis_block.compute_hash()
#         self.chain.append(genesis_block)

#     @property
#     def last_block(self):
#         return self.chain[-1]

#     def add_block(self, block, proof):
#         """
#         A function that adds the block to the chain after verification.
#         Verification includes:
#         * Checking if the proof is valid.
#         * The previous_hash referred in the block and the hash of latest block
#           in the chain match.
#         """
#         previous_hash = self.last_block.hash

#         if previous_hash != block.previous_hash:
#             return False

#         if not Blockchain.is_valid_proof(block, proof):
#             return False

#         block.hash = proof
#         self.chain.append(block)
#         return True

#     def proof_of_work(self, block):
#         """
#         Function that tries different values of nonce to get a hash
#         that satisfies our difficulty criteria.
#         """
#         block.nonce = 0

#         computed_hash = block.compute_hash()
#         while not computed_hash.startswith('0' * Blockchain.difficulty):
#             block.nonce += 1
#             computed_hash = block.compute_hash()

#         return computed_hash

#     def add_new_transaction(self, transaction):
#         self.unconfirmed_transactions.append(transaction)

#     @classmethod
#     def is_valid_proof(cls, block, block_hash):
#         """
#         Check if block_hash is valid hash of block and satisfies
#         the difficulty criteria.
#         """
#         return (block_hash.startswith('0' * Blockchain.difficulty) and
#                 block_hash == block.compute_hash())

#     @classmethod
#     def check_chain_validity(cls, chain):
#         result = True
#         previous_hash = "0"

#         for block in chain:
#             block_hash = block.hash
#             # remove the hash field to recompute the hash again
#             # using `compute_hash` method.
#             delattr(block, "hash")

#             if not cls.is_valid_proof(block, block.hash) or \
#                     previous_hash != block.previous_hash:
#                 result = False
#                 break

#             block.hash, previous_hash = block_hash, block_hash

#         return result

#     def mine(self):
#         """
#         This function serves as an interface to add the pending
#         transactions to the blockchain by adding them to the block
#         and figuring out Proof Of Work.
#         """
#         if not self.unconfirmed_transactions:
#             return False

#         last_block = self.last_block

#         new_block = Block(index=last_block.index + 1,
#                           transactions=self.unconfirmed_transactions,
#                           timestamp=time.time(),
#                           previous_hash=last_block.hash)

#         proof = self.proof_of_work(new_block)
#         self.add_block(new_block, proof)

#         self.unconfirmed_transactions = []
#         # announce it to the network
#         announce_new_block(new_block)
#         with open("blockchain.pkl", "wb") as f:
#             pickle.dump(self.chain, f)
#         storage.child("/blockchain.pkl").put("blockchain.pkl")
#         return new_block.index


app = Flask(__name__)

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres+psycopg2://{}'.format(os.environ["DATABASE_URL"][11:])
# db.init_app(app)

# the node's copy of blockchain
blockchain = Blockchain(storage)
# blockchain.create_genesis_block()

# the address to other participating members of the network
# peers = set()

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)
def clean_key(key):
    key = unquote(key)
    if "+" in key[:26]:
        key = rreplace(key, "+", " ", 2).replace("+", " ", 2)
    return key
# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain

@app.route("/")
def index():
    return "<h1>This is an API please do not spam.</h1>"

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["sender", "receiver", "pubkey"]
    # print(tx_data)
    for field in required_fields:
        if not tx_data.get(field):
            return "Invlaid transaction data", 403
    if "value" not in tx_data:
        tx_data["value"] = MIN_COINS
    tx_data["pubkey"] = clean_key(tx_data["pubkey"])
    tx_data["timestamp"] = time.time()
    if "message" in tx_data:
        tx_data["message"] = encryption.encrypt_message(bytes(tx_data["message"]), encryption.read_public_key_string(tx_data.pop("pubkey", None).encode("ascii")))
    else:
        tx_data["message"] = "**TRANSFER**"

    blockchain.add_new_transaction(tx_data)

    # print(tx_data)
    # t = Transaction(tx_data["sender"], tx_data["receiver"], tx_data["value"], tx_data["message"], tx_data["timestamp"])

    # db.session.add(t)
    # db.session.commit()
    print("start mining")
    blockchain.mine(storage)


    return "Success", 201


# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    # make sure we've the longest chain
    consensus()
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)})

@app.route('/getUserMsgs', methods=['POST'])
def get_user_msgs():
    # make sure we've the longest chain
    required_fields = ["sender", "receiver", "prikey"]
    for field in required_fields:
        if field not in request.form:
            return "Sender or Receiver not provided", 404

    sender = unquote(request.form["sender"])
    receiver = unquote(request.form["receiver"])
    prikey = request.form["prikey"]
    # print(repr(prikey))
    prikey = prikey.replace("\\n", "\n")
    # print(repr(prikey))
    try:
        key = encryption.read_private_key_string(prikey.encode("ascii"))
    except ValueError as e:
        return json.dumps({"length": 0,
                       "messages": [[2, "Decryption Error. This account is probably deleted."]],
                       "peers": list(peers)})
    consensus()
    messages = []
    for block in blockchain.chain:
        # chain_data.append(block.__dict__)
        d = block.__dict__
        dt = [transaction for transaction in d["transactions"] if (transaction["sender"] == sender and transaction["receiver"] == receiver) or (transaction["sender"] == receiver and transaction["receiver"] == sender)]
        print(dt)
        for transaction in dt:
            if transaction["sender"] == sender:
                try:
                    msg = encryption.decrypt_message(bytes(transaction["message"]), key)
                    messages.append([1,msg,transaction["timestamp"]])
                except TypeError:
                    pass
            elif transaction["sender"] == receiver:
                try:
                    msg = encryption.decrypt_message(bytes(transaction["message"]), key)
                    messages.append([2,msg,transaction["timestamp"]])
                except TypeError:
                    pass
    print(messages)
    return json.dumps({"length": len(messages),
                       "messages": messages,
                       "peers": list(peers)})

@app.route('/getNewReceivedMsgs', methods=['POST'])
def get_new_received_msgs():
    # make sure we've the longest chain
    required_fields = ["sender", "receiver", "prikey", "timestamp"]
    for field in required_fields:
        if field not in request.form:
            return "Sender, Receiver, Private key or Timestamp not provided", 403

    sender = request.form["sender"]
    receiver = request.form["receiver"]
    prikey = clean_key(request.form["prikey"])
    timestamp = float(request.form["timestamp"])
    # print(repr(prikey))
    prikey = prikey.replace("\\n", "\n")
    # print(repr(prikey))
    key = encryption.read_private_key_string(prikey.encode("ascii"))
    consensus()
    messages = []
    for block in blockchain.chain:
        # chain_data.append(block.__dict__)
        d = block.__dict__
        dt = [transaction for transaction in d["transactions"] if (transaction["sender"] == receiver and transaction["receiver"] == sender)]
        # print(dt)
        for transaction in dt:
            if transaction["timestamp"] > timestamp:
                try:
                    msg = encryption.decrypt_message(bytes(transaction["message"]), key)
                    messages.append([msg,transaction["timestamp"]])
                except TypeError:
                    pass
    # print(messages)
    return json.dumps({"length": len(messages),
                       "messages": messages,
                       "peers": list(peers)})

@app.route('/getCoins', methods=['POST'])
def get_coins():
    # make sure we've the longest chain
    required_fields = ["sender"]
    for field in required_fields:
        if field not in request.form:
            return "Username not provided", 404

    sender = request.form["sender"]
    consensus()
    coins = BASE_COINS
    for block in blockchain.chain:
        # chain_data.append(block.__dict__)
        d = block.__dict__
        sent_txns = [transaction for transaction in d["transactions"] if (transaction["sender"] == sender)]
        received_txns = [transaction for transaction in d["transactions"] if (transaction["receiver"] == sender)]
        print(sent_txns, received_txns)
        for transaction in sent_txns:
            coins -= float(transaction["value"])
        for transaction in received_txns:
            coins += float(transaction["value"])
    return json.dumps(round(coins, 5))

@app.route('/getUsers', methods=['POST'])
def get_Users():
    required_fields = ["sender"]
    for field in required_fields:
        if field not in request.form:
            return "Username not provided", 404

    sender = request.form["sender"]
    consensus()
    users = set()
    recentMsgs = dict()
    for block in blockchain.chain:
        d = block.__dict__
        sent_txns = [transaction for transaction in d["transactions"] if (transaction["sender"] == sender)]
        received_txns = [transaction for transaction in d["transactions"] if (transaction["receiver"] == sender)]
        # print(sent_txns, received_txns)
        for transaction in sent_txns:
            users.add(transaction["receiver"])
            if transaction["receiver"] in recentMsgs:
                if transaction["timestamp"] > recentMsgs[transaction["receiver"]][1]:
                    recentMsgs[transaction["receiver"]] = [transaction["message"], transaction["timestamp"]]
            else:
                recentMsgs[transaction["receiver"]] = [transaction["message"], transaction["timestamp"]]
        for transaction in received_txns:
            users.add(transaction["sender"])
            if transaction["sender"] in recentMsgs:
                if transaction["timestamp"] > recentMsgs[transaction["sender"]][1]:
                    recentMsgs[transaction["sender"]] = [transaction["message"], transaction["timestamp"]]
            else:
                recentMsgs[transaction["sender"]] = [transaction["message"], transaction["timestamp"]]
    # print(users, recentMsgs)
    return json.dumps({"users": list(users), "recentmsgs": recentMsgs})

@app.route("/generateKeys", methods=["POST"])
def generate_keys():
    prikey, pubkey = encryption.generate_keys()
    prikey = encryption.get_private_key_string(prikey)
    print(repr(prikey))
    pubkey = encryption.get_public_key_string(pubkey)
    print(repr(pubkey))
    return json.dumps({"prikey": prikey, "pubkey": pubkey})

# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine(storage)
    if not result:
        return "No transactions to mine"
    return "Block #{} is mined.".format(result)


# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peers.add(node_address)

    # Return the consensus blockchain to the newly registered node
    # so that he can sync
    return get_chain()


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Internally calls the `register_node` endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    blockchain = Blockchain()
    for idx, block_data in enumerate(chain_dump):
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"])
        proof = block_data['hash']
        if idx > 0:
            added = blockchain.add_block(block, proof)
            if not added:
                raise Exception("The chain dump is tampered!!")
        else:  # the block is a genesis block, no verification needed
            blockchain.chain.append(block)
    return blockchain


# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.
@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)

@app.route('/ismining')
def is_mining():
    return json.dumps(blockchain.is_mining())


def consensus():
    """
    Our simple consnsus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        print('{}/chain'.format(node))
        response = requests.get('{}/chain'.format(node))
        print("Content", response.content)
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


# def announce_new_block(block):
#     """
#     A function to announce to the network once a block has been mined.
#     Other blocks can simply verify the proof of work and add it to their
#     respective chains.
#     """
#     for peer in peers:
#         url = "{}add_block".format(peer)
#         requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=False, processes=1)