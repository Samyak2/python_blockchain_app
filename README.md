# Python Blockchain

Used as a backend in [blockchat](https://github.com/Samyak2/blockchat/)

See the [original](https://github.com/satwikkansal/python_blockchain_app) for the tutorial on this.

## Changes made from original

 - Supports conversation between two people (instead of a common chat room)
 - Added coins
 - Encryption of messages using RSA Public-Private Key pairs
 - Transactions are stored to a file instead of using only memory
 - Transactions file is asynchronously uploaded to a Firebase Storage container
 - Tried to eliminate race condition when two users send a message simulatenously
 - Ready to be deployed to Heroku
