import pandas as pd
import os
import yfinance as yf
import numpy as np
import requests
import json
from yahoofinancials import YahooFinancials as YF
from bs4 import BeautifulSoup
import pytz
from datetime import datetime, timedelta
import ipywidgets as widgets
from IPython.display import display
import hvplot.pandas

ticker_list = pd.read_html('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol']

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

risk_selector = widgets.Dropdown(
    options = ['Conservative', 'Moderate', 'Aggressive'],
    value = 'Moderate',
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

coin_text = widgets.IntText(
    value = 0,
    description = f'{risk_selector.value}Coins: ',
    style = {'description_width': 'initial'}
)

coin_button = widgets.Button(
    description = 'Buy!',
    layout={'border': '1px solid black'}
)

cons_coin = widgets.IntText(
    value = 0,
    description = 'ConservativeCoins purchased: ',
    style = {'description_width': 'initial'},
    disabled = True
)

mod_coin = widgets.IntText(
    value = 0,
    description = 'ModerateCoins purchased: ',
    style = {'description_width': 'initial'},
    disabled = True
)

agg_coin = widgets.IntText(
    value = 0,
    description = 'AggressiveCoins purchased: ',
    style = {'description_width': 'initial'},
    disabled = True
)

coins_purchased_box = widgets.VBox([cons_coin, mod_coin, agg_coin])

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
        coin_text.description = f'{risk_selector.value}Coins: '

button.on_click(on_button_clicked)

def coin_button_clicked(b):
    with coin_out:
        coin_out.clear_output()
        if risk_selector.value == 'Conservative':
            cons_coin.value += coin_text.value
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
