import pandas as pd
import os
import yfinance as yf
import numpy as np
import requests
import json
import pytz
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import ipywidgets as widgets
from IPython.display import display
import hvplot.pandas
import web3, solc, json
from solc import compile_standard
from web3.contract import ConciseContract, ContractCaller
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy
from web3.auto.gethdev import w3

#w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3 = Web3(Web3.HTTPProvider("https://kovan.infura.io/v3/c939afba949d4aa2903246e8029e4d49"))
#w3.middleware_onion.inject(geth_poa_middleware, layer=0)
#w3.eth.setGasPriceStrategy(medium_gas_price_strategy)


# Ignore
def calculate_sharpe(ticker, time_frame):
    
    stock = yf.Ticker(ticker)
    df = stock.history(period=time_frame)['Close'].to_frame()
    
    df['Daily Returns'] = df['Close'].diff()
    df.dropna(inplace=True)
    
    risk_free = 0.0067
    avg_return = df['Daily Returns'].mean()
    vol = df['Daily Returns'].std()
    sharpe = (avg_return - risk_free) / vol * np.sqrt(252)
    
    return sharpe

weights = [0.40, 0.25, 0.15, 0.10, 0.05, 0.05]

conservative_stocks = ['NEM', 'DG', 'REGN', 'DXCM', 'AAPL']
moderate_stocks = ['DXCM', 'NVDA', 'ODFL', 'DG', 'REGN', 'AAPL']
aggressive_stocks = ['NVDA', 'DXCM', 'AAPL', 'SWKS', 'ODFL']

# Ignore
def cum_return(stock_list, weight_list, time_frame):
    
    df = pd.DataFrame()
    
    for stock in stock_list:
        ticker = yf.Ticker(stock)
        df[f'{stock} Close'] = ticker.history(period=time_frame)['Close']
        df.dropna(inplace=True)
        
    cumulative_returns = []    
    
    for date in df.index:
        index = 0
        adj_closes = []
        
        for i in df.loc[date]:
            adj_close = i * weights[index]
            adj_closes.append(adj_close)
        
            index += 1
            
        cum_adj_return = sum(adj_closes)
        cumulative_returns.append(cum_adj_return)
        
    df['Portfolio Adj. Close'] = cumulative_returns
    
    df['Daily Adj. Return'] = df['Portfolio Adj. Close'].diff()
    df.dropna(inplace=True)
    
    risk_free = 0.0067
    avg_return = df['Daily Adj. Return'].mean()
    vol = df['Daily Adj. Return'].std()
    sharpe = (avg_return - risk_free) / vol * np.sqrt(252)
        
    return df, sharpe


# Need to update address and ABI if new contract deployed
pupper_coin_sale_contract = w3.eth.contract(address='0x2749f56DD2A50b8973d1E3E22839e6AeA4cA1b50', abi='''[
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "rate",
				"type": "uint256"
			},
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "symbol",
				"type": "string"
			},
			{
				"internalType": "address payable",
				"name": "wallet",
				"type": "address"
			},
			{
				"internalType": "contract PupperCoin",
				"name": "token",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "goal",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "open",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "close",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": false,
		"inputs": [],
		"name": "CrowdsaleFinalized",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "prevClosingTime",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "newClosingTime",
				"type": "uint256"
			}
		],
		"name": "TimedCrowdsaleExtended",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "address",
				"name": "purchaser",
				"type": "address"
			},
			{
				"indexed": true,
				"internalType": "address",
				"name": "beneficiary",
				"type": "address"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "value",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "amount",
				"type": "uint256"
			}
		],
		"name": "TokensPurchased",
		"type": "event"
	},
	{
		"payable": true,
		"stateMutability": "payable",
		"type": "fallback"
	},
	{
		"constant": true,
		"inputs": [
			{
				"internalType": "address",
				"name": "account",
				"type": "address"
			}
		],
		"name": "balanceOf",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": false,
		"inputs": [
			{
				"internalType": "address",
				"name": "beneficiary",
				"type": "address"
			}
		],
		"name": "buyTokens",
		"outputs": [],
		"payable": true,
		"stateMutability": "payable",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "cap",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "capReached",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": false,
		"inputs": [
			{
				"internalType": "address payable",
				"name": "refundee",
				"type": "address"
			}
		],
		"name": "claimRefund",
		"outputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "closingTime",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": false,
		"inputs": [],
		"name": "finalize",
		"outputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "finalized",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "goal",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "goalReached",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "hasClosed",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "isOpen",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "openingTime",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "rate",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "token",
		"outputs": [
			{
				"internalType": "contract IERC20",
				"name": "",
				"type": "address"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "wallet",
		"outputs": [
			{
				"internalType": "address payable",
				"name": "",
				"type": "address"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": true,
		"inputs": [],
		"name": "weiRaised",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": false,
		"inputs": [
			{
				"internalType": "address",
				"name": "beneficiary",
				"type": "address"
			}
		],
		"name": "withdrawTokens",
		"outputs": [],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	}
]''')

url = 'https://rest.coinapi.io/v1/exchangerate/ETH/USD'
headers = {'X-CoinAPI-Key' : 'AE657143-7169-4CE9-9923-73207061F320'}
response = requests.get(url, headers=headers).text
eth_rate = json.loads(response)['rate']

# Widgets
risk_selector = widgets.Dropdown(
    options = ['Conservative', 'Moderate', 'Aggressive'],
    value = 'Conservative',
    description = 'Risk Tolerance: ',
    style = {'description_width': 'initial'},
    disabled=False
)

time = widgets.IntText(
    value = 1,
    description = 'Time Frame: '
)

time_selector = widgets.Dropdown(
    options = ['year(s)', 'month(s)', 'day(s)'],
    value = 'year(s)'
)

button = widgets.Button(
    description = 'Update',
    layout={'border': '1px solid black'}
)


# for use on local network only #

#account_selector = widgets.Dropdown(
#    options = w3.eth.accounts,
#    value = w3.eth.accounts[1],
#    description = 'Account: '
#)

account_selector = widgets.Text(
    value = '',
    description = 'Account: '
)

key_input = widgets.Password(
    value = '',
    description = 'Private Key: '
)


coin_text = widgets.IntText(
    value = 0,
    description = f'{risk_selector.value[:3]}Coins: ',
    style = {'description_width': 'initial'},
    disabled = False
)

coin_button = widgets.Button(
    description = 'Buy!',
    layout={'border': '1px solid black'}
)

cons_coin = widgets.IntText(
    value = 0,
    description = 'Your ConCoins: ',
    style = {'description_width': 'initial'},
    disabled = True
)

mod_coin = widgets.IntText(
    value = 0,
    description = 'Your ModCoins: ',
    style = {'description_width': 'initial'},
    disabled = True
)

agg_coin = widgets.IntText(
    value = 0,
    description = 'Your AggCoins: ',
    style = {'description_width': 'initial'},
    disabled = True
)

cons_coin_supply = widgets.IntText(
    value = int(w3.fromWei((pupper_coin_sale_contract.caller.cap() - pupper_coin_sale_contract.caller.weiRaised())*eth_rate, 'ether')),
    description = 'Remaining supply of ConCoin: ',
    style = {'description_width': 'initial'},
    disabled = True
)

mod_coin_supply = widgets.IntText(
    value = 0,
    description = 'Remaining supply of ModCoin: ',
    style = {'description_width': 'initial'},
    disabled = True
)

agg_coin_supply = widgets.IntText(
    value = 0,
    description = 'Remaining supply of AggCoin: ',
    style = {'description_width': 'initial'},
    disabled = True
)


coins_purchased_box = widgets.VBox([account_selector, key_input, cons_coin, mod_coin, agg_coin, cons_coin_supply, mod_coin_supply, agg_coin_supply])

coin_out = widgets.Output()
with coin_out:
    display(coins_purchased_box)

def generate_portfolio(risk, time_input, time_unit):
    
    if time_unit == 'year(s)':
        time_frame = f'{time_input}y'
        
    elif time_unit == 'month(s)':
        time_frame = f'{time_input}mo'
        
    elif time_unit == 'day(s)':
        time_frame = f'{time_input}d'
    
    if risk == 'Conservative':
        portfolio, sharpe = cum_return(conservative_stocks, weights, time_frame)
        
    elif risk == 'Moderate':
        portfolio, sharpe = cum_return(moderate_stocks, weights, time_frame)
        
    elif risk == 'Aggressive':
        portfolio, sharpe = cum_return(aggressive_stocks, weights, time_frame)
        
    return portfolio

out = widgets.Output()
with out:
    port_df = generate_portfolio(risk_selector.value, time.value, time_selector.value)
    display(port_df['Portfolio Adj. Close'].hvplot())
    
def on_button_clicked(b):
    with out:
        out.clear_output()
        port_df = generate_portfolio(risk_selector.value, time.value, time_selector.value)
        display(port_df['Portfolio Adj. Close'].hvplot())
        coin_text.description = f'{risk_selector.value[:3]}Coins: '

button.on_click(on_button_clicked)

def coin_button_clicked(b):
    
    with coin_out:
        coin_out.clear_output()
        
        buyer_address = account_selector.value
        cons_coin.value = int(w3.fromWei(pupper_coin_sale_contract.caller.balanceOf(account_selector.value)*eth_rate, 'ether'))
        
        if risk_selector.value == 'Conservative':
            
            if pupper_coin_sale_contract.caller.capReached() or pupper_coin_sale_contract.caller.hasClosed():
                coin_text.disabled = True
                
            elif coin_text.value > cons_coin_supply.value:
                nonce = w3.eth.getTransactionCount(buyer_address)
            
                transaction = pupper_coin_sale_contract.functions.buyTokens(
                    buyer_address).buildTransaction({
                        'value': w3.toWei(cons_coin_supply.value/eth_rate, 'ether'),
                        'gas': 3000000,
                        'nonce': nonce
                    })

                signed_txn = w3.eth.account.signTransaction(
                    transaction, key_input.value
                )

                txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            
                cons_coin.value += cons_coin_supply.value
                
                cons_coin_supply.value = int(w3.fromWei((pupper_coin_sale_contract.caller.cap() - pupper_coin_sale_contract.caller.weiRaised())*eth_rate, 'ether'))
                
            else:
            
                nonce = w3.eth.getTransactionCount(buyer_address)

                transaction = pupper_coin_sale_contract.functions.buyTokens(
                    buyer_address).buildTransaction({
                        'value': w3.toWei(coin_text.value/eth_rate, 'ether'),
                        'gas': 3000000,
                        'nonce': nonce
                    })

                signed_txn = w3.eth.account.signTransaction(
                    transaction, key_input.value
                )

                txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

                cons_coin.value += coin_text.value
                
                cons_coin_supply.value = int(w3.fromWei((pupper_coin_sale_contract.caller.cap() - pupper_coin_sale_contract.caller.weiRaised())*eth_rate, 'ether'))
            
        elif risk_selector.value == 'Moderate':
            mod_coin.value += coin_text.value
            
        elif risk_selector.value == 'Aggressive':
            agg_coin.value += coin_text.value
            
        display(coins_purchased_box)
            
coin_button.on_click(coin_button_clicked)

interactions = widgets.HBox([risk_selector, button])
time_interactions = widgets.HBox([time, time_selector])
user_input = widgets.VBox([interactions, time_interactions])
user_box = widgets.VBox([user_input, out])
coin_purchase_box = widgets.HBox([coin_text, coin_button])
coin_box = widgets.VBox([coin_purchase_box, coin_out])

dash = widgets.VBox([user_box, coin_box], layout={'border': '2px solid black'})
