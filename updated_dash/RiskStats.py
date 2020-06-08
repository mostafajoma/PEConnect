# Initial imports
import numpy as np
import pandas as pd
from pathlib import Path
import arch as arch

%matplotlib inline

#Reading In First DF
file_path = Path('PrivateEquityReturnsFinal.csv')
pe_df = pd.read_csv(file_path, parse_dates=True, index_col='Date', infer_datetime_format=True)
pe_df

#Final PE DF
df = pd.DataFrame(pe_df['Private Equity Returns'])
df

#Reading In The Second DF
file_path_2 = Path('SPXReturns.csv')
eq_df = pd.read_csv(file_path_2, parse_dates=True, index_col='Date', infer_datetime_format=True)
eq_df

#Returns DF
returns_df = pd.concat([df, eq_df], axis=1, join='inner')
returns_df

#Calculating the Funds STD
rolling_std = returns_df.rolling(window=4).std()
rolling_std

#Plotting Fund Returns STD 
rolling_std['Private Equity Returns'].plot(title="Fund Standard Deviation")

#Plotting Market STD 
rolling_std['SPX_Return'].plot(title="S&P 500 Standard Deviation")

#Calculating Covariance 
rolling_covariance = returns_df['Private Equity Returns'].rolling(window=4).cov(returns_df['SPX_Return'])
rolling_covariance

#Calculate Rolling Variance 
rolling_variance_spx = returns_df['SPX_Return'].rolling(window=4).var()
rolling_variance_spx

#Calculate the rolling 1 year beta of the Fund
rolling_beta = rolling_covariance / rolling_variance_spx
rolling_beta.plot(title="Fund Beta")

#Calculate Sharpe Ratios for entire group
sharpe_ratios = (returns_df.mean()*4)/(returns_df.std()*np.sqrt(4))
sharpe_ratios.sort_values(inplace=True)
sharpe_ratios

# Visualize the sharpe ratios as a bar plot
sharpe_ratios.plot.bar(title="Sharpe Ratios")

pe_df['Cumulative'].plot(title="Fund's Cumulative Return")

