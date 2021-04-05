from datetime import datetime, timedelta, date
import pandas as pd
import json
import os

from tda.auth import easy_client
from tda.client import Client

from __init__ import token_path, redirect_url, api_key, account_id
from __init__ import p_folder as excel_folder, p_db_folder as db_folder, t_folder

folder = './data/transaction_history/'

def getTransactionHistory(start_date, end_date):
	df = pd.DataFrame(columns=[
		'TIMESTAMP',
		'SYMBOL',
		'PRICE',
		'AMOUNT',
		'COST',
		'INSTRUCTION',
		'ASSETTYPE'
	])

	c = easy_client(
	        api_key=api_key,
	        redirect_uri=redirect_url,
	        token_path=token_path)

	trade = c.get_transactions(account_id, transaction_type=c.Transactions.TransactionType.TRADE, symbol=None, start_date=start_date, end_date=end_date)

	row = 2
	for t in json.loads(trade.read().decode('utf-8')):
		# not implemented for options expiry or withdrawls/deposits
		if t['type'] != 'TRADE':
			continue
		
		transaction = t["transactionItem"]

		timestamp = datetime.strptime(t['orderDate'].replace('T', ' ')[:-5], '%Y-%m-%d %H:%M:%S') - timedelta(hours=4)

		new_row = {
			'TIMESTAMP': timestamp,
			'SYMBOL': transaction['instrument']['symbol'],
			'PRICE': transaction['price'],
			'AMOUNT': transaction['amount'],
			'COST': transaction['cost'],
			'INSTRUCTION': transaction['instruction'],
			'ASSETTYPE': transaction['instrument']['assetType']
		}
		df = df.append(new_row, ignore_index=True)

	df.TIMESTAMP = pd.to_datetime(df.TIMESTAMP, format="%Y/%m/%d %H:%M:%S").apply(lambda x: x.replace(microsecond=0)).dt.time
	
	return df

# TDA does not mark short selling and covering
def markShort(df):
	df.TIMESTAMP = pd.to_datetime(df.TIMESTAMP, format='%H:%M:%S')
	df.sort_values('TIMESTAMP', inplace=True)
	df['T_TEMP'] = df.AMOUNT * df.INSTRUCTION.apply(lambda x: 1 if x == 'BUY' else -1)
	df['T_TEMP'] = df.groupby('SYMBOL')['T_TEMP'].transform(pd.Series.cumsum)

	df.loc[(df.COST > 0) & (df.T_TEMP < 0), 'INSTRUCTION'] = 'SHORT'
	df.loc[(df.COST < 0) & (df.T_TEMP <= 0) & (df.INSTRUCTION == 'BUY'), 'INSTRUCTION'] = 'COVER'

	df.drop(columns=['T_TEMP'], inplace=True)
	df.TIMESTAMP = df.TIMESTAMP.dt.time

	return df

# Combine price data and transaction history
def combineTP(pd_path, th_path):
	df_p = pd.read_excel(pd_path)
	df_t = pd.read_excel(th_path)
	df = pd.merge(df_p, df_t, on=['SYMBOL', 'TIMESTAMP'], how='left')

	"""Customization"""

	return df
  
# Year-Month-Day Hour-Minute-Seconds
# Max date range is one year
def run(start_date, end_date):
	pd_path = os.path.join(excel_folder, date.today().strftime("%m-%d-%Y")+'.xlsx')
	th_path = os.path.join(t_folder, '{}-{}.xlsx'.format(int(datetime.timestamp(start_date)), int(datetime.timestamp(end_date))))

	# Create file for transaction history
	df = getTransactionHistory(start_date, end_date)
	df = markShort(df)
	df.to_excel(th_path, index=False)

	# Combine price data and transaction history
	df = combineTP(pd_path, th_path)
	df.to_excel(pd_path, index=False)
	# os.system('rm {}'.format(th_path)) # linux
	os.system('del {}'.format(th_path)) # windows
	return df
