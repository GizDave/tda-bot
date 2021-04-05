# requires Python 3.8

import os

os.system('pip3 freeze > requirements.txt')
os.system('install -r requirements.txt')
# os.system('pip3 install tda-api')
# os.system('pip3 install twilio')

if not os.path.exists('./model'): os.mkdir('./model')

if not os.path.exists('./data'): os.mkdir('./data')
if not os.path.exists('./data/price_data'): os.mkdir('./data/price_data')
if not os.path.exists('./data/price_data/db'): os.mkdir('./data/price_data/db')
if not os.path.exists('./data/transaction_history'): os.mkdir('./data/transaction_history')
if not os.path.exists('./token'): os.mkdir('./token')

if not os.path.exists('token//tda.pickle'):
	from tda.auth import client_from_manual_flow

	from __init__ import token_path, redirect_url, api_key

	client_from_manual_flow(api_key, redirect_url, token_path, asyncio=False, token_write_func=None)