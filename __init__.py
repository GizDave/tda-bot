# Path to which the new token will be written. If the token file already exists, it will be overwritten with a new one. Updated tokens will be written to this path as well.
token_path = 'token//tda.pickle'

# Your TD Ameritrade application's redirect URL.
redirect_url = ''

# Your TD Ameritrade application's API key, also known as the client ID
api_key = '' 

# Your TD Ameritrade account ID
account_id = ''

# Stocks
ticker = ['SPY', 'DIA', 'QQQ']

##############################################################################

p_folder = './data/price_data/'
p_db_folder = './data/price_data/db/'

t_folder = './data/transaction_history'

##############################################################################

from tda.streaming import StreamClient

# Enforce input format
ticker = [x.upper() for x in ticker]

# Requested price fields
# See https://tda-api.readthedocs.io/en/stable/streaming.html#level-one-quotes
price_data_field = [
    StreamClient.LevelOneEquityFields.SYMBOL,
    StreamClient.LevelOneEquityFields.BID_PRICE,
    StreamClient.LevelOneEquityFields.ASK_PRICE,
    StreamClient.LevelOneEquityFields.LAST_PRICE,
    StreamClient.LevelOneEquityFields.BID_SIZE,
    StreamClient.LevelOneEquityFields.ASK_SIZE,
    StreamClient.LevelOneEquityFields.TOTAL_VOLUME,
    StreamClient.LevelOneEquityFields.LAST_SIZE,
    #StreamClient.LevelOneEquityFields.TRADE_TIME,
    #StreamClient.LevelOneEquityFields.QUOTE_TIME,
    StreamClient.LevelOneEquityFields.HIGH_PRICE,
    StreamClient.LevelOneEquityFields.LOW_PRICE,
    #StreamClient.LevelOneEquityFields.BID_TICK,
    #StreamClient.LevelOneEquityFields.OPEN_PRICE,
    StreamClient.LevelOneEquityFields.CLOSE_PRICE,
    #StreamClient.LevelOneEquityFields.VOLATILITY 
]

# SQL file schema
# See https://www.tutorialspoint.com/sqlite/sqlite_data_types.htm
price_data_schema = {
    'TIMESTAMP': 'CHARACTER',
    'SYMBOL': 'CHARACTER',
    'BID_PRICE': 'FLOAT',
    'ASK_PRICE': 'FLOAT',
    'LAST_PRICE': 'FLOAT',
    'BID_SIZE': 'INTEGER',
    'ASK_SIZE': 'INTEGER',
    'TOTAL_VOLUME': 'INTEGER',
    'LAST_SIZE': 'INTEGER',
    'HIGH_PRICE': 'FLOAT',
    'LOW_PRICE': 'FLOAT',
    'CLOSE_PRICE': 'FLOAT'
}
