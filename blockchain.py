from hashlib import sha256
import simplejson as json
import time
import pickle
import requests
from dotenv import load_dotenv
load_dotenv()
import os
import threading

# from config import Transaction

# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session

# from config import metadata, Transaction

from dbtest import sql_connection, is_mining, set_mining, set_notmining

# engine = create_engine('postgres+psycopg2://{}'.format(os.environ["DATABASE_URL"][11:]))

peers = set()

def create_chain_from_dump(chain_dump):
    blockchain = Blockchain(genesis=False)
    for idx, block_data in enumerate(chain_dump):
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        if 'hash' in block_data:
            proof = block_data['hash']
        else:
            proof = block.compute_hash()
        if idx > 0:
            added = blockchain.add_block(block, proof)
            if not added:
                raise Exception("The chain dump is tampered!!")
        else:
            blockchain.chain.append(block)
    return blockchain

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    # difficulty of our PoW algorithm
    difficulty = 3

    def __init__(self, storage=None, genesis=True):
        self.unconfirmed_transactions = []
        self.chain = []
        # self.storage = storage
        if os.environ['LOAD_CHAIN'] == "true" and storage is not None:
            # storage.child("/blockchain.pkl").download("blockchain.pkl")
            # try:
            #     with open("blockchain.pkl", "rb") as f:
            #         self.chain = pickle.load(f)
            # except FileNotFoundError:
            #     self.chain = []
            #     self.create_genesis_block()
            try:
                storage.child("/blockchain.json").download("blockchain.json")
                with open("blockchain.json", "rt") as f:
                    newchain = create_chain_from_dump(json.load(f)["chain"])
                    self.__dict__.update(newchain.__dict__)
            except (FileNotFoundError, AttributeError) as e:
                print(e)
                # raise e
                self.chain = []
                if genesis:
                    self.create_genesis_block()
        else:
            self.chain = []
            if genesis:
                self.create_genesis_block()

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """
        # print(block.__dict__)
        try:
            previous_hash = self.last_block.hash
        except AttributeError:
            previous_hash = block.previous_hash

        if previous_hash != block.previous_hash:
            print("Hashes don't match\n{}\n{}".format(previous_hash, block.previous_hash))
            return False

        if not self.is_valid_proof(block, proof):
            print("block is not valid")
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def proof_of_work(self, block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            # remove the hash field to recompute the hash again
            # using `compute_hash` method.
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block.hash) or \
                    previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self, storage):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """
        if not self.unconfirmed_transactions:
            return False

        while is_mining():
            time.sleep(0.1)

        set_mining()
        last_block = self.last_block

        # session = Session(engine)
        # pending_txns = session.query(Transaction).all()

        # print(pending_txns)

        # if len(pending_txns) <= 0:
            # return False
        
        # pending_txns2 = [{"sender": i.sender, "receiver": i.receiver, "value": i.value, "message": bytes(i.message), "timestamp": i.timestamp} for i in pending_txns]
        # print(pending_txns2)
        # print(self.unconfirmed_transactions)

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        # pending_txns.delete()

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []
        # announce it to the network
        announce_new_block(new_block)
        # with open("blockchain.pkl", "wb") as f:
        #     pickle.dump(self.chain, f)
        # with open("blockchain.json", "wb") as f:
        #     f.write(self.get_chain_json())
        # storage.child("/blockchain.pkl").put("blockchain.pkl")
        # # storage.child("/blockchain.pkl").put("blockchain.pkl")
        # set_notmining()
        # print("starting thread")
        upload_thread = threading.Thread(target=self.upload_files, args=(storage,))
        upload_thread.start()
        # print("started thread")
        return new_block.index

    def upload_files(self, storage):
        # with open("blockchain.pkl", "wb") as f:
        #     pickle.dump(self.chain, f)
        print("getting json...")
        with open("blockchain.json", "wb") as f:
            f.write(bytes(self.get_chain_json(), encoding="utf-8"))
        # storage.child("/blockchain.pkl").put("blockchain.pkl")
        storage.child("/blockchain.json").put("blockchain.json")
        print("uploaded json...")
        set_notmining()
        return True

    def get_chain_json(self):
        chain_data = []
        for block in self.chain:
            # print(block.__dict__)
            chain_data.append(block.__dict__)
        return json.dumps({"length": len(chain_data),
                        "chain": chain_data,
                        "peers": list(peers)})

def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "{}add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))