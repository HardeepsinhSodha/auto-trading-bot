# auto-trading-bot
# Goal
Buy and Sell BankNifty weekly option base on Supertrend, CMO and RSI trading strategy for HeikinAshi 3 minute interval data. 

# instruction
This program is worked for Indian Stock market only.
You have to create api_key and api_secret from https://kite.trade/.
To download historical data you have to purchase their plan.

# How to run
paste your api_key and api_secret into configLogin.py
run generateAccessToken.py to generate access_token and it will save in access_token.txt
run download_instrumentsList.py to get BankNifty weekly option stock name and their related info and save it in csv file.
open main.py in editer and change input condition as per your need and then run that file.
