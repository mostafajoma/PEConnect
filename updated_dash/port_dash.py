from abis_and_keys import *
import pandas as pd
import os
import yfinance as yf
import numpy as np
import requests
import json
from datetime import datetime
from threading import Timer
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

# 1 of the following networks must be selected
# For local network
#w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# For Kovan live testnet
w3 = Web3(Web3.HTTPProvider("https://kovan.infura.io/v3/c939afba949d4aa2903246e8029e4d49"))



w3 = Web3(Web3.HTTPProvider("https://kovan.infura.io/v3/{INFURA_PROJECT_ID}"))

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


# Creates contract instances for deployer, token, and token sale
# Need to update address for deployer contract if redeployed
deployer_contract = w3.eth.contract(address=deployer_contract_address, abi=deployer_abi)

coinA_contract = w3.eth.contract(address=deployer_contract.caller.token_address(), abi=coin_abi)

CoinA_sale_contract = w3.eth.contract(address=deployer_contract.caller.token_sale_address(), abi=sale_abi)

# API pulls exchange rate - USD/ETH
url = 'https://rest.coinapi.io/v1/exchangerate/ETH/USD'
headers = {'X-CoinAPI-Key' : 'AE657143-7169-4CE9-9923-73207061F320'}
response = requests.get(url, headers=headers).text
eth_rate = json.loads(response)['rate']


#### Widgets ####
risk_selector = widgets.Dropdown(
    options = ['Conservative', 'Moderate', 'Aggressive'],
    value = 'Conservative',
    description = 'Risk Tolerance',
    style = {'description_width': 'initial'},
    disabled=False
)

time = widgets.IntText(
    value = 1,
    description = 'Time Frame'
)

time_selector = widgets.Dropdown(
    options = ['year(s)', 'month(s)', 'day(s)'],
    value = 'year(s)'
)

button = widgets.Button(
    description = 'Update',
    layout={'border': '1px solid black'}
)


# for use on local blockchain only #

#account_selector = widgets.Dropdown(
#    options = w3.eth.accounts,
#    value = w3.eth.accounts[1],
#    description = 'Account: '
#)

# Must input account address and private key manually on live testnet
account_selector = widgets.Text(
    value = '',
    description = 'Account: ',
    placeholder = 'Enter account address'
)

key_input = widgets.Password(
    value = '',
    description = 'Private Key: ',
    placeholder = 'Enter private key'
)


coin_text = widgets.IntText(
    value = 0,
    description = f'{risk_selector.value[:3]}Coins: ',
    style = {'description_width': 'initial'},
    disabled = False
)

coin_button = widgets.Button(
    description = 'Buy!',
    layout={'border': '1px solid black'},
    disabled = False
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
    value = CoinA_sale_contract.caller.cap() - CoinA_sale_contract.caller.weiRaised(),
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



withdraw_account = widgets.Text(
    value = '',
    description = 'Account: ',
    placeholder = 'Enter account address: '
)

withdraw_key_input = widgets.Password(
    value = '',
    description = 'Private key: ',
    placeholder = 'Enter private key: '
)

withdraw_button = widgets.Button(
    description = 'Withdraw',
    layout={'border': '1px solid black'}
)



withdraw_box = widgets.VBox([withdraw_account, withdraw_key_input, withdraw_button])
withdraw_box.layout.visibility = 'hidden'

withdraw_out = widgets.Output()
with withdraw_out:
    display(withdraw_box)
    
coins_purchased_box = widgets.VBox([account_selector, key_input, cons_coin, mod_coin, agg_coin, cons_coin_supply, mod_coin_supply, agg_coin_supply])
    

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
    
coin_out = widgets.Output()
with coin_out:
    display(coins_purchased_box)
    
    
    
def on_button_clicked(b):
    with out:
        out.clear_output()
        port_df = generate_portfolio(risk_selector.value, time.value, time_selector.value)
        display(port_df['Portfolio Adj. Close'].hvplot())
        coin_text.description = f'{risk_selector.value[:3]}Coins: '

button.on_click(on_button_clicked)


def withdraw_button_clicked(b):
    with withdraw_out:
        withdraw_address = withdraw_account.value
        withdraw_key = withdraw_key_input.value
        withdraw_out.clear_output()
        withdraw_box.layout.visibility = 'visible'
        display(withdraw_box)
        
        withdraw = CoinA_sale_contract.functions.withdrawTokens(withdraw_address).buildTransaction({
            'gas': 3000000,
            'nonce': w3.eth.getTransactionCount(withdraw_address)
        })

        signed_txn_withdraw = w3.eth.account.signTransaction(withdraw, withdraw_key_input.value)
        txn_hash_withdraw = w3.eth.sendRawTransaction(signed_txn_withdraw.rawTransaction)
        tx_receipt_withdraw = w3.eth.waitForTransactionReceipt(txn_hash_withdraw)
    
withdraw_button.on_click(withdraw_button_clicked)


def coin_button_clicked(b):
    
    with coin_out:
        coin_out.clear_output()
        
        buyer_address = account_selector.value
        
        if risk_selector.value == 'Conservative':
            
            if CoinA_sale_contract.caller.capReached() or CoinA_sale_contract.caller.hasClosed():
                coin_text.disabled = True
                
            elif w3.toWei(coin_text.value/eth_rate, 'wei') > CoinA_sale_contract.caller.cap() - CoinA_sale_contract.caller.weiRaised():
                
                nonce = w3.eth.getTransactionCount(buyer_address)
                remaining_supply = CoinA_sale_contract.caller.cap() - CoinA_sale_contract.caller.weiRaised()
                
                remainder = remaining_supply % CoinA_sale_contract.caller.rate()
            
                transaction = CoinA_sale_contract.functions.buyTokens(
                    buyer_address).buildTransaction({
                        'value': remaining_supply,
                        'gas': 3000000,
                        'nonce': nonce
                    })
                signed_txn = w3.eth.account.signTransaction(
                    transaction, key_input.value
                )
                txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
                tx_receipt = w3.eth.waitForTransactionReceipt(txn_hash)
            
                cons_coin.value += cons_coin_supply.value
                
                cons_coin_supply.value = CoinA_sale_contract.caller.cap() - CoinA_sale_contract.caller.weiRaised()
                
            else:
                nonce = w3.eth.getTransactionCount(buyer_address)
                remainder = w3.toWei(coin_text.value/eth_rate, 'ether') % CoinA_sale_contract.caller.rate()

                transaction = CoinA_sale_contract.functions.buyTokens(
                    buyer_address).buildTransaction({
                        'value': coin_text.value,
                        'gas': 3000000,
                        'nonce': nonce
                    })
                signed_txn = w3.eth.account.signTransaction(
                    transaction, key_input.value
                )
                txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
                tx_receipt = w3.eth.waitForTransactionReceipt(txn_hash)
                
                cons_coin.value += coin_text.value
                
                cons_coin_supply.value = CoinA_sale_contract.caller.cap() - CoinA_sale_contract.caller.weiRaised()
            
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

dash = widgets.VBox([user_box, coin_box, withdraw_out], layout={'border': '2px solid black'})



# Sets a timer to automatically finalize the crowdsale when closing time has been reached.
openingTime = CoinA_sale_contract.caller.openingTime()
closingTime = CoinA_sale_contract.caller.closingTime()
time_window = (datetime.fromtimestamp(closingTime) - datetime.fromtimestamp(openingTime))
seconds = time_window.seconds + 1

def finalize_sale():
    time_till_finalize.cancel()
    
    try:
        transaction_fin = CoinA_sale_contract.functions.finalize().buildTransaction({
        'gas': 3000000,
        'nonce': w3.eth.getTransactionCount(owner_address)
        })
        signed_txn_fin = w3.eth.account.signTransaction(
            transaction_fin, owner_private_key
        )
        txn_hash_fin = w3.eth.sendRawTransaction(signed_txn_fin.rawTransaction)
        tx_receipt_fin = w3.eth.waitForTransactionReceipt(txn_hash_fin)
        
    except:
        CoinA_sale_contract.caller.finalized()
    
    coin_text.disabled = True
    coin_button.disabled = True
    account_selector.disabled = True
    account_selector.value = ''
    key_input.disabled = True
    key_input.value = ''
    
    coin_box.layout.visibility = 'hidden'
    
    withdraw_box.layout.visibility = 'visible'
    #withdraw_out.layout.visibility = 'visible'
    
    with withdraw_out:
        display(withdraw_box)
    

time_till_finalize = Timer(seconds, finalize_sale)

time_till_finalize.start()
