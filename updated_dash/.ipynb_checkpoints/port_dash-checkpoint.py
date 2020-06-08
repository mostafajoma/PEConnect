from abis_and_keys import *
from constants import *
from lstm_predictor import prediction_plot
import pandas as pd
#import os
import yfinance as yf
import numpy as np
import requests
import json
from datetime import datetime
from threading import Timer
import ipywidgets as widgets
from IPython.display import display
import hvplot.pandas
import web3
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy
from web3.auto.gethdev import w3
from eth_account import Account
from bit.network import NetworkAPI
from dotenv import load_dotenv
from pathlib import Path
import arch as arch

#Reading In First DF
file_path = Path('PrivateEquityReturnsFinal.csv')
pe_df = pd.read_csv(file_path, parse_dates=True, index_col='Date', infer_datetime_format=True)
pe_df.drop(columns='Unnamed: 8', inplace=True)
pe_df.dropna(inplace=True)

#Final PE DF
df = pd.DataFrame(pe_df['Private Equity Returns'])

#Reading In The Second DF
file_path_2 = Path('SPXReturns.csv')
eq_df = pd.read_csv(file_path_2, parse_dates=True, index_col='Date', infer_datetime_format=True)
eq_df.dropna(inplace=True)

#Returns DF
returns_df = pd.concat([df, eq_df], axis=1, join='inner')

#Calculating the Funds STD
rolling_std = returns_df.rolling(window=4).std()

#Plotting Fund Returns STD 
rolling_std_plot = rolling_std['Private Equity Returns'].hvplot(title="Fund Standard Deviation")

#Plotting Market STD 
market_std_plot = rolling_std['SPX_Return'].hvplot(title="S&P 500 Standard Deviation")

fund_and_market_std = rolling_std.hvplot(y=['Private Equity Returns', 'SPX_Return'], title='Fund vs. SPX Standard Deviation')

#Calculating Covariance 
rolling_covariance = returns_df['Private Equity Returns'].rolling(window=4).cov(returns_df['SPX_Return'])

#Calculate Rolling Variance 
rolling_variance_spx = returns_df['SPX_Return'].rolling(window=4).var()

#Calculate the rolling 1 year beta of the Fund
rolling_beta = rolling_covariance / rolling_variance_spx
rolling_beta_plot = rolling_beta.hvplot(title="Fund Beta")

#Calculate Sharpe Ratios for entire group
sharpe_ratios = (returns_df.mean()*4)/(returns_df.std()*np.sqrt(4))
sharpe_ratios.sort_values(inplace=True)

# Visualize the sharpe ratios as a bar plot
sr_plot = sharpe_ratios.hvplot.bar(title="Sharpe Ratios")

sr_cum_plot = pe_df['Cumulative'].hvplot(title="Fund's Cumulative Return")



# 1 of the following networks must be selected
# For local network
#w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# For Kovan live testnet
w3 = Web3(Web3.HTTPProvider(f"https://kovan.infura.io/v3/{INFURA_PROJECT_ID}"))


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

coinA_contract = w3.eth.contract(address=deployer_contract.functions.token_address().call(), abi=coin_abi)

coinA_sale_contract = w3.eth.contract(address=deployer_contract.functions.token_sale_address().call(), abi=sale_abi)

# API pulls exchange rate - USD/ETH
url = 'https://rest.coinapi.io/v1/exchangerate/ETH/USD'
headers = {'X-CoinAPI-Key' : exchange_rate_key}
response = requests.get(url, headers=headers).text
eth_rate = json.loads(response)['rate']


#### Widgets ####

plot_selector = widgets.Dropdown(
    options = ['Historic Returns', 'Historic Volatility', 'Sharpe Ratios', 'LSTM'],
    value = 'Historic Returns',
    description = 'Select: ',
    style = {'description_width': 'initial'},
    disabled=False
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


coin_name = coinA_contract.functions.name().call()

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


# Input token amount for purchase
coin_text = widgets.IntText(
    value = 0,
    description = f'{coin_name}s :',
    style = {'description_width': 'initial'},
    disabled = False
)

# Purchase button
coin_button = widgets.Button(
    description = 'Buy!',
    layout ={'border': '1px solid black'},
    disabled = False
)


account_input = widgets.HBox([account_selector, key_input])
purchase_coins = widgets.HBox([coin_text, coin_button])
purchase_from_acct = widgets.VBox([account_input, purchase_coins])


# Show equivalent amount in USD
dollar_conversion = widgets.Text(
    value = "{:,}".format(round(coin_text.value / (10 ** coinA_contract.functions.decimals().call())) * eth_rate, 2),
    description = '$',
    disabled = True
)

# Confirm purchase
confirm_button = widgets.Button(
    description = 'Confirm',
    layout = {'border': '1px solid black'}
)

# Keeps dollar conversion and confirm button hidden until buy button is clicked
confirm_box = widgets.HBox([dollar_conversion, confirm_button])
confirm_box.layout.visibility = 'hidden'
purchase_box = widgets.VBox([purchase_from_acct, confirm_box])


# Displays the buyer's purchased tokens
cons_coin = widgets.IntText(
    value = 0,
    description = f'Your {coin_name}s: ',
    style = {'description_width': 'initial'},
    disabled = True
)

# Remaining Token Supply
cons_coin_supply = widgets.IntText(
    value = (coinA_sale_contract.functions.cap().call() - coinA_sale_contract.functions.weiRaised().call()) / (10**coinA_contract.functions.decimals().call()),
    description = f'Remaining supply of {coin_name}: ',
    style = {'description_width': 'initial'},
    disabled = True
)


# Withdraw Tokens widgets
withdraw_account = widgets.Text(
    value = '',
    description = 'Account: ',
    placeholder = 'Enter account address: ',
    width = '100%'
)

withdraw_key_input = widgets.Password(
    value = '',
    description = 'Private key: ',
    placeholder = 'Enter private key: ',
    layout = widgets.Layout(align_items='center')
)

withdraw_button = widgets.Button(
    description = 'Withdraw Tokens',
    layout={'border': '1px solid black'}
    #layout = widgets.Layout(align_items='center')
)


token_balance = widgets.IntText(
    value = 0,
    description = coinA_contract.functions.symbol().call(),
    layout = widgets.Layout(align_items='center'),
    disabled = True
)

token_balance_button = widgets.Button(
    description = f'Get {coin_name} Balance',
    layout={'border': '1px solid black'}
    #layout = widgets.Layout(align_items='center')
)


# setting exchange rate for ETH to YodaCoins
exchange_rate = 1 / (10**(18-coinA_contract.functions.decimals().call()))

# function to convert private key into a readable format for web3 / bit
def priv_key_to_account (priv_key):
    return Account.privateKeyToAccount(priv_key)


# function to create raw, unsigned transaction
def seller_tx(coin, seller_account, buyer_account, amount):

    seller_gas_estimate = w3.eth.estimateGas({
        "from": seller_account.address, 
        "to": buyer_account, 
        "value": w3.toWei(amount,'ether') 
    })
    
    seller_details = {
        "from": seller_account.address,
        "to": buyer_account,
        "value": w3.toWei(amount,'ether') ,
        "gas": seller_gas_estimate,
        "gasPrice": w3.eth.gasPrice,
        "nonce": w3.eth.getTransactionCount(seller_account.address),
    }
    
    return seller_details


# function to create, sign, and send ethereum transaction 
def send_tx(coin, seller, seller_pk, buyer, buyer_pk, amount, rate):
    
    seller_raw_tx = seller_tx(coin, seller_pk, buyer, amount)
    seller_signed_tx = seller_pk.signTransaction(seller_raw_tx)
    
    seller_result = w3.eth.sendRawTransaction(seller_signed_tx.rawTransaction)
    
    return seller_result


# function to create, sign, and send YodaCoin transaction 
def token_tx(seller_account, seller_key, buyer_address, amount):
    
    transfer = coinA_contract.functions.transfer(buyer_address, amount).buildTransaction(
        {
            'gas' : 3000000,
            'nonce' : w3.eth.getTransactionCount(seller_account)
        }
    )
    
    signed_transfer = w3.eth.account.signTransaction(transfer, seller_key)
    
    transfer_hash = w3.eth.sendRawTransaction(signed_transfer.rawTransaction)
    
    tx_receipt = w3.eth.waitForTransactionReceipt(transfer_hash)
    
    return tx_receipt


# creating empty list to hold trade orders and dict to hold trade order metadata
trade_blotter_list = []
trade_details = {}

# establishing variable for trade amount
buy_sell_amount = None


# setting up widgets to create orders 

# address input widget
maker_account_selector = widgets.Text(
    value = '',
    description = 'Maker Account: ',
    placeholder = 'Enter account address',
    style = {'description_width': 'initial'},
)

# private key input widget
maker_key_input = widgets.Password(
    value = '',
    description = 'Private Key: ',
    placeholder = 'Enter private key'
)


# input token amount for trade
maker_coin_text = widgets.IntText(
    value = 0,
    description = 'YodaCoins',
    style = {'description_width': 'initial'},
    disabled = False
)

# sell order button
sell_order_button = widgets.Button(
    description = 'Enter Buy Order',
    layout ={'border': '1px solid black'},
    disabled = False
)

# buy order button
buy_order_button = widgets.Button(
    description = 'Enter Sell Order',
    layout ={'border': '1px solid black'},
    disabled = False
)


# function to initiate a new sell order and add to the trade blotter upon button click
def sell_order_button_clicked(b):
    
    with trade_taker_output:
        
        seller_address = maker_account_selector.value
        seller_private_key = maker_key_input.value
        seller_pk_readable = priv_key_to_account(seller_private_key)
        buy_sell_amount = maker_coin_text.value

        trade_blotter_list.append(f'Sell {buy_sell_amount} YodaCoins')
        trade_blotter.options = trade_blotter_list
        trade_details[trade_blotter_list[-1]] = [seller_address, 
                                                 seller_private_key, 
                                                 priv_key_to_account(seller_private_key), 
                                                 buy_sell_amount, 
                                                 'sell']
        
        trade_taker_output.clear_output()
        display(trade_taker)

sell_order_button.on_click(sell_order_button_clicked)


# function to initiate a new buy order and add to the trade blotter upon button click
def buy_order_button_clicked(b):
    
    with trade_taker_output:
    
        seller_address = maker_account_selector.value
        seller_private_key = maker_key_input.value
        seller_pk_readable = priv_key_to_account(seller_private_key)
        buy_sell_amount = maker_coin_text.value

        trade_blotter_list.append(f'Buy {buy_sell_amount} YodaCoins')
        trade_blotter.options = trade_blotter_list
        trade_details[trade_blotter_list[-1]] = [seller_address, 
                                                 seller_private_key, 
                                                 priv_key_to_account(seller_private_key),
                                                 buy_sell_amount, 
                                                 'buy']
        
        trade_taker_output.clear_output()
        display(trade_taker)

buy_order_button.on_click(buy_order_button_clicked)


# grouping widgets for order entry
account_input = widgets.VBox([maker_account_selector, maker_key_input])
buy_sell_buttons = widgets.HBox([sell_order_button, buy_order_button])
order_amount = widgets.VBox([maker_coin_text, buy_sell_buttons])

buy_sell_order = widgets.VBox([account_input, order_amount])


# creating widget to take trades 

trade_selection = None

account_selector_2 = widgets.Text(
    value = '',
    description = 'Taker Account: ',
    placeholder = 'Enter account address',
    style = {'description_width': 'initial'},
)

key_input_2 = widgets.Password(
    value = '',
    description = 'Private Key: ',
    placeholder = 'Enter private key'
)


trade_blotter = widgets.Select(
    options = trade_blotter_list,
    description='Available Trades:',
    style = {'description_width': 'initial'},
    disabled=False
)

# accept trade button
accept_trade_button = widgets.Button(
    description = 'Accept Trade',
    layout ={'border': '1px solid black'},
    disabled = False
)


# grouping trade taking widgets
trade_taker = widgets.VBox([account_selector_2, key_input_2, trade_blotter])


# converting trade taker widget into an output widget so that it can be updated dynamically 
trade_taker_output = widgets.Output()

with trade_taker_output:
    #trade_taker_output.clear_output()
    display(trade_taker)
    
    
# function to initiate transaction upon accepting the trade
# def token_tx(seller_account, seller_key, buyer_address, amount):
def accept_trade_button_clicked(b):
    
    with trade_taker_output:

        trade_selection = trade_blotter.value
        seller_address = trade_details[trade_selection][0]
        seller_private_key = trade_details[trade_selection][1]
        seller_pk_readable = trade_details[trade_selection][2]
        token_amount = trade_details[trade_selection][3]
        buyer_address = account_selector_2.value
        buyer_private_key = key_input_2.value
        buyer_pk_readable = priv_key_to_account(buyer_private_key)

        if trade_details[trade_selection][4] == 'sell':

            send_tx(
                ETH,
                seller_address,
                seller_pk_readable,
                buyer_address,
                buyer_pk_readable,
                token_amount * exchange_rate, # * (10**coinA_contract.functions.decimals().call()),
                exchange_rate
            )
            
            token_tx(
                buyer_address,
                buyer_private_key,
                seller_address,
                token_amount * (10**coinA_contract.functions.decimals().call())
            )

        elif trade_details[trade_selection][4] == 'buy':

            send_tx(
                ETH,
                buyer_address,
                buyer_pk_readable, 
                seller_address,
                seller_pk_readable,
                token_amount * exchange_rate, # * (10**coinA_contract.functions.decimals().call()),
                exchange_rate
            )
            
            token_tx(
                seller_address,
                seller_private_key,
                buyer_address,
                token_amount * (10**coinA_contract.functions.decimals().call())
            )
            
        trade_blotter_list.remove(trade_selection)
        trade_blotter.options = trade_blotter_list
        trade_taker_output.clear_output()
        display(trade_taker)

accept_trade_button.on_click(accept_trade_button_clicked)


# creating final exchange dashboard
trading_app_dash = widgets.VBox(
    [buy_sell_order,trade_taker_output,accept_trade_button],
    layout ={'border': '1px solid black'},
    disabled = False
)



# Withdraw tokens functionality - remains hidden until contract is finalized
account_box = widgets.VBox([withdraw_account], 
                           layout = widgets.Layout(align_items='center'),
                           width = '100%'
                          )
withdraw_box = widgets.VBox([withdraw_key_input, withdraw_button], 
                            layout = widgets.Layout(align_items='center')
                           )
token_balance_box = widgets.VBox([token_balance, token_balance_button], 
                                 layout = widgets.Layout(align_items='center')
                                )
after_sale_box = widgets.AppLayout(
    header = account_box,
    left_sidebar = withdraw_box,
    center = None,
    right_sidebar = token_balance_box,
    footer = None,
    width = '100%'
    #align_items = 'center'
)

post_sale_box = widgets.VBox([after_sale_box, trading_app_dash])


post_sale_box.layout.visibility = 'hidden'

    
coins_purchased_box = widgets.VBox([cons_coin, cons_coin_supply])
coins_box = widgets.VBox([purchase_box, coins_purchased_box])
    

def select_plots(selector):
    
    if selector == 'Historic Returns':
        plot = fund_and_market_std
        
    elif selector == 'Historic Volatility':
        plot = rolling_beta_plot
        
    elif selector == 'Sharpe Ratios':
        plot = sr_plot
        
    elif selector == 'LSTM':
        plot = prediction_plot
        
    return plot



## Output widgets ##

out = widgets.Output()
with out:
    plot = select_plots(plot_selector.value)
    display(plot)
    

coin_out = widgets.Output()
with coin_out:
    if coinA_sale_contract.functions.isOpen().call():
        display(coins_box)
    else:
        pass
    
    
confirm_out = widgets.Output()
with confirm_out:
    if coinA_sale_contract.functions.hasClosed().call():
        pass
    else:
        display(confirm_box)
        
        
withdraw_out = widgets.Output()
with withdraw_out:
    if coinA_sale_contract.functions.finalized().call():
        post_sale_box.layout.visibility = 'visible'
        display(post_sale_box)
    else:
#        #post_sale_box.layout.visibility = 'hidden'
        pass
    
    
    
## On-click event widgets ##

# Update visuals
def on_button_clicked(b):
    with out:
        out.clear_output()
        plot = select_plots(plot_selector.value)
        display(plot)

button.on_click(on_button_clicked)


# Display dollar conversion and Confirm button
def coin_button_clicked(b):
    with confirm_out:
        if coin_text.value > cons_coin_supply.value:
            coin_text.value = cons_coin_supply.value
        else:
            pass
        
        dollar_conversion.value = "{:,}".format(round(coin_text.value / (10 ** (18-coinA_contract.functions.decimals().call())) * eth_rate, 2))
        confirm_out.clear_output()
        
        confirm_box.layout.visibility = 'visible'
        display(confirm_box)
    
coin_button.on_click(coin_button_clicked)


# Declare event when Confirm button is clicked - Activate Buy Tokens function
def confirm_button_clicked(b):
    
    with coin_out:
        coin_out.clear_output()
        
        buyer_address = account_selector.value
            
        if coinA_sale_contract.functions.capReached().call() or coinA_sale_contract.functions.hasClosed().call():
            coin_text.disabled = True
            coin_button.disabled = True
                
        elif coin_text.value * coinA_contract.functions.decimals().call()  >= coinA_sale_contract.functions.cap().call() - coinA_sale_contract.functions.weiRaised().call():
                
            nonce = w3.eth.getTransactionCount(buyer_address)
            remaining_supply = coinA_sale_contract.functions.cap().call() - coinA_sale_contract.functions.weiRaised().call()
            
            transaction = coinA_sale_contract.functions.buyTokens(
                buyer_address).buildTransaction(
                {
                    'value': remaining_supply,
                    'gas': 3000000,
                    'nonce': nonce
                }
            )
            signed_txn = w3.eth.account.signTransaction(transaction, key_input.value)
            txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            tx_receipt = w3.eth.waitForTransactionReceipt(txn_hash)
            
            cons_coin.value = coinA_sale_contract.functions.balanceOf(buyer_address).call() / (10**coinA_contract.functions.decimals().call())
                
            cons_coin_supply.value = (coinA_sale_contract.functions.cap().call() - coinA_sale_contract.functions.weiRaised().call()) / (10**coinA_contract.functions.decimals().call())
                
            coin_text.disabled = True
            coin_button.disabled = True
                
        else:
            nonce = w3.eth.getTransactionCount(buyer_address)
            
            transaction = coinA_sale_contract.functions.buyTokens(
                buyer_address).buildTransaction(
                {
                    'value': coin_text.value * (10**coinA_contract.functions.decimals().call()),
                    'gas': 3000000,
                    'nonce': nonce
                }
            )
            signed_txn = w3.eth.account.signTransaction(transaction, key_input.value)
            txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            tx_receipt = w3.eth.waitForTransactionReceipt(txn_hash)
                
            cons_coin.value = coinA_sale_contract.functions.balanceOf(buyer_address).call() / (10**coinA_contract.functions.decimals().call())
                
            cons_coin_supply.value = (coinA_sale_contract.functions.cap().call() - coinA_sale_contract.functions.weiRaised().call()) / (10**coinA_contract.functions.decimals().call())
        
        coin_text.value = 0
        confirm_box.layout.visibility = 'hidden'
            
        display(coins_box)
            
confirm_button.on_click(confirm_button_clicked)


# Declare event when withdraw button is clicked - withdraw tokens that were previously purchased
def withdraw_button_clicked(b):
    with withdraw_out:
        withdraw_address = withdraw_account.value
        withdraw_key = withdraw_key_input.value
        withdraw_out.clear_output()
        #post_sale_box.layout.visibility = 'visible'
        display(post_sale_box)
        
        withdraw = coinA_sale_contract.functions.withdrawTokens(withdraw_address).buildTransaction(
            {
                'gas': 3000000,
                'nonce': w3.eth.getTransactionCount(withdraw_address)
            }
        )
        signed_txn_withdraw = w3.eth.account.signTransaction(withdraw, withdraw_key_input.value)
        txn_hash_withdraw = w3.eth.sendRawTransaction(signed_txn_withdraw.rawTransaction)
        tx_receipt_withdraw = w3.eth.waitForTransactionReceipt(txn_hash_withdraw)
    
withdraw_button.on_click(withdraw_button_clicked)


# Retrieve token balance
def token_balance_button_clicked(b):
    with withdraw_out:
        balance_address = withdraw_account.value
        token_balance.value = coinA_contract.functions.balanceOf(balance_address).call() / (10**coinA_contract.functions.decimals().call())
        
token_balance_button.on_click(token_balance_button_clicked)



# Organizes the widgets into layout boxes
interactions = widgets.HBox([plot_selector, button])
user_box = widgets.VBox([interactions, out])

# Complete dashboard
dash = widgets.VBox([user_box, coin_out, post_sale_box], layout={'border': '2px solid black'})



# Sets a timer to automatically finalize the crowdsale when closing time has been reached.
openingTime = coinA_sale_contract.functions.openingTime().call()
closingTime = coinA_sale_contract.functions.closingTime().call()
time_window = (datetime.fromtimestamp(closingTime) - datetime.fromtimestamp(openingTime))
seconds = time_window.seconds + 1

# Sets a timer to automatically finalize the crowdsale when closing time has been reached.
#now = datetime.now()
closingTime = coinA_sale_contract.functions.closingTime().call()
time_window = (datetime.fromtimestamp(closingTime) - datetime.now())
seconds = time_window.seconds + 1

# Activates Finalize function automatically when closintTime is reached.
# Then displays post-sale widgets.
def finalize_sale():
    time_till_finalize.cancel()
    
    #if coinA_sale_contract.caller.goalReached():
        
    try:
        transaction_fin = coinA_sale_contract.functions.finalize().buildTransaction(
            {
                'gas': 3000000,
                'nonce': w3.eth.getTransactionCount(owner_address)
            }
        )
        signed_txn_fin = w3.eth.account.signTransaction(
            transaction_fin, owner_private_key
        )
        txn_hash_fin = w3.eth.sendRawTransaction(signed_txn_fin.rawTransaction)
        tx_receipt_fin = w3.eth.waitForTransactionReceipt(txn_hash_fin)

    except:
        coinA_sale_contract.functions.finalized().call()
            
    #else: # Something should happen if funds are not raised when time ends
        
        #print('Funds not raised')
    
    coin_text.disabled = True
    coin_button.disabled = True
    account_selector.disabled = True
    account_selector.value = ''
    key_input.disabled = True
    key_input.value = ''
    
    coins_box.layout.visibility = 'hidden'
    post_sale_box.layout.visibility = 'visible'
    
    with withdraw_out:
        display(post_sale_box)
    

time_till_finalize = Timer(seconds, finalize_sale)

time_till_finalize.start()
