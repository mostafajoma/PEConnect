![name](Image.png)
# tokenization of private equity 

## Overview

In this project, we are seeking to leverage blockchain technology in order to lower the barriers to entry that are typically required to invest in private investments. Given that private companies are highly illiquid investment targets in nature given the lack of a public stock market, private equity funds typically cater to large, institutional investors that can 
- Put down large amounts of capital. 
- Have that capital locked up for the extended periods of time that are required to pursue private equity investment strategies, such as buyouts. For the everyday retail investor, private equity investments are generally unattainable due to these barriers to entry. 

Using blockchain, we plan to break down the “ownership” of a fund through tokenization, and create a market to trade these tokens so that retail investors with less deployable capital can add private equity to their investment portfolios. 

## Breakdown

The core goals of the project are to:
- Develop a fundraising mechanism for a proxy/dummy private equity fund in the form of a tokenized crowdsale on an ethereum blockchain network, in which a fixed number of tokens represent a fraction of the total value of the fund (primary market). E.g. if we had a $500M fundraising target and minted 50M tokens, each token would be worth $10 at inception. 
- Develop a mechanism for trading these tokens between investors via smart contracts (secondary market). 
- Develop a mechanism for the value of these tokens to float in response to the fund’s performance (we will use a PE index as a proxy for our fund’s performance). 
- Stretch goal to have the token market price respond to the output of some sort of asset pricing model,  supply/demand factors, expected returns from ML projections, etc. 
- We probably don’t want too much variation  in the value of the coin
- Determine how we would like these tokens to behave as a security - i.e. do we want them to have dividends, a large principal payout at fund termination, etc.? - and develop both the logic and mechanism for coordinating these payouts. 

## Technologies

- Solidity for minting tokens, defining token behavior, and smart contracts
- Python SciKit LSTM machine learning models for token price forecasting 
- Ganache for ethereum account / wallet creation 
- Metamask for simulating trades + payouts
