# importing libraries
from constants import *
import os
from dotenv import load_dotenv
import subprocess
import json
from eth_account import Account
from bit import PrivateKeyTestnet
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy
from bit.network import NetworkAPI
import ipywidgets as widgets

load_dotenv()

# calling mnemonic environment variable
mnemonic = os.getenv('MNEMONIC')