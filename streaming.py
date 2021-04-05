import asyncio
from asyncio import events
import json
import time
from datetime import date, datetime, timedelta, timezone
import os
import warnings
import traceback

import pandas as pd
import sqlite3

from tda.auth import easy_client
from tda.client import Client
from tda.streaming import StreamClient

from __init__ import token_path, redirect_url, api_key, account_id, ticker
from __init__ import p_folder as excel_folder, p_db_folder as db_folder
from __init__ import price_data_field, price_data_schema
from utility import timestamp_to_datetime, WindowsInhibitor

warnings.filterwarnings('ignore')

# Filepath of .db
db_filepath = None

# Filepath of .xlsx
excel_filepath = None

# SQLite
con = None
cur = None

insert_sql_query_header = None

# WindowsInhibitor
osSleep = WindowsInhibitor()
   
def refresh_filepath():
    global excel_filepath, db_filepath
    
    db_filepath = os.path.join(db_folder, date.today().strftime("%m-%d-%Y")+'.db')
    excel_filepath = os.path.join(excel_folder, date.today().strftime("%m-%d-%Y")+'.xlsx')

def refresh_db():
    global con, cur, insert_sql_query_header, db_filepath
    
    con = sqlite3.connect(db_filepath)
    cur = con.cursor()

    query = """CREATE TABLE IF NOT EXISTS PRICE_DATA({});"""
    columns = ", ".join(['{} {}'.format(dtype, price_data_schema[dtype]) for dtype in price_data_schema.keys()])
    query = query.format(columns)
    
    insert_sql_query_header = "INSERT INTO PRICE_DATA ({}) VALUES ".format(', '.join(list(price_data_schema.keys())))
    insert_sql_query_header = insert_sql_query_header + "(" + ", ".join(['?']*len(price_data_schema)) + ");"

    cur.execute(query)
    con.commit()

def get_client(token_path, redirect_url, api_key, account_id):
    """Get an instance of StreamClient with given credentials"""
    client = easy_client(
            api_key=api_key,
            redirect_uri=redirect_url,
            token_path=token_path)
    stream_client = StreamClient(client, account_id=account_id)
    return stream_client

def postprocessDF():
    """Post-process price_data_df: fill in blanks and add custom columns"""
    global con, excel_filepath
    try:
        """possible caveat: if there is one second that has no entry, the rolling window would be 1 entry short for a given ticker."""
        
        price_data_df = pd.read_sql('SELECT * FROM PRICE_DATA', con)
        
        """*Do these preprocessing first*"""

        # Change datetime to time and remove ms
        price_data_df.TIMESTAMP = pd.to_datetime(price_data_df.TIMESTAMP, unit='ms') - timedelta(hours=4)
        # Add missing tickers per time period (1s)
        price_data_df = price_data_df.set_index(['TIMESTAMP', 'SYMBOL']).reindex(
            pd.MultiIndex.from_product([price_data_df['TIMESTAMP'].unique(), ticker], names=('TIMESTAMP', 'SYMBOL')), 
            fill_value=None
        ).swaplevel(0,1).reset_index()
        # Forward filling
        price_data_df.update(price_data_df.groupby('SYMBOL', as_index=False).transform(lambda v: v.ffill()).reset_index())

        """Secondary preprocessing"""

        # Calculate middle price between bid and ask
        price_data_df['MID_PRICE'] = (price_data_df.BID_PRICE+price_data_df.ASK_PRICE)/2

        # Replace Close_Price with % from Close_Price
        price_data_df['%_FROM_CLOSE_BID'] = (price_data_df.BID_PRICE-price_data_df.CLOSE_PRICE)/price_data_df.CLOSE_PRICE*100
        price_data_df['%_FROM_CLOSE_MID'] = (price_data_df.MID_PRICE-price_data_df.CLOSE_PRICE)/price_data_df.CLOSE_PRICE*100
        price_data_df['%_FROM_CLOSE_ASK'] = (price_data_df.ASK_PRICE-price_data_df.CLOSE_PRICE)/price_data_df.CLOSE_PRICE*100
        price_data_df.drop(columns=['CLOSE_PRICE'], inplace=True)
        
        # Save changes to database
        price_data_df.to_sql('PRICE_DATA', con, if_exists='replace', index=False)
        print('Saved .db to filepath:' + db_filepath)

        """Customization"""
        
        # Save results to excel
        price_data_df.to_excel(excel_filepath, index=False)
        print('Saved .xlsx to filepath:' + excel_filepath)
    except Exception as error:
        traceback.print_exc()
        print('ERROR:', error)

async def read(stream_client, price_data_field, end_time, retry=True):
    """Start streaming TDA price data"""
    global con, osSleep

    osSleep.inhibit()
    await stream_client.login()
    await stream_client.quality_of_service(StreamClient.QOSLevel.FAST)

    # Always add handlers before subscribing because many streams start sending
    # data immediately after success, and messages with no handlers are dropped.
    
    stream_client.add_level_one_equity_handler(lambda msg: write(msg))
    await stream_client.level_one_equity_subs(ticker, fields=price_data_field)

    while datetime.now() <= end_time:
        await stream_client.handle_message()

    if datetime.now() < end_time and retry:
        # Early termination and retry
        osSleep.uninhibit()
        stream_client = get_client(token_path, redirect_url, api_key, account_id)

        print('ended stream prematurely at', datetime.now().time())
        print('restarting stream...')
        await read(stream_client, price_data_field, end_time, retry=True)
    else:
        print('ended stream at', datetime.now().time())

        postprocessDF()
        con.close()
        osSleep.uninhibit()

def write(msg):
    """Streamming data handler"""
    global con, cur, insert_sql_query_header

    timestamp = msg['timestamp']
    query_param = None
    for content in msg['content']:
        content['SYMBOL'] = content['key']
        del content['key']

        content['TIMESTAMP'] = timestamp

        query_param = tuple([content[schemaKey] if schemaKey in content else None for schemaKey in price_data_schema.keys()])
        print(query_param)
        cur.execute(
            insert_sql_query_header,
            query_param
        )
        con.commit()

def run(end_time):
    refresh_filepath()
    refresh_db()
    
    """Main function"""
    stream_client = get_client(token_path, redirect_url, api_key, account_id)
    asyncio.run(read(stream_client, price_data_field, end_time))
