from hashlib import sha256
import simplejson as json
import time
import pickle
import requests
from dotenv import load_dotenv
load_dotenv()
import os

# from config import Transaction

# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session

# from config import metadata, Transaction

from dbtest import sql_connection, is_mining, set_mining, set_notmining

# engine = create_engine('postgres+psycopg2://{}'.format(os.environ["DATABASE_URL"][11:]))

peers = set()

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

    def __init__(self, storage):
        self.unconfirmed_transactions = []
        self.chain = []
        # self.storage = storage
        if os.environ['LOAD_CHAIN'] == "true":
            storage.child("/blockchain.pkl").download("blockchain.pkl")
            try:
                with open("blockchain.pkl", "rb") as f:
                    self.chain = pickle.load(f)
            except FileNotFoundError:
                self.chain = []
        else:
            self.chain = []

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
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
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

        while not is_mining():
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
        with open("blockchain.pkl", "wb") as f:
            pickle.dump(self.chain, f)
        storage.child("/blockchain.pkl").put("blockchain.pkl")
        set_notmining()
        return new_block.index


def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "{}add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))