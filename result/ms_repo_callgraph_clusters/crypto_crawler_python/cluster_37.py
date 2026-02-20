# Cluster 37

def get_balance_poloniex(key):
    """
    https://poloniex.com/tradingApi
    {'Key': 'QN6SDFQG-XVG2CGG3-WDDG2WDV-VXZ7MYL3',
    'Sign': '368a800fcd4bc0f0d95151ed29c9f84ddf6cae6bc366d3105db1560318da72aa82281b5ea52f4d4ec929dd0eabc7339fe0e7dc824bf0f1c64e099344cd6e74d0'}
    {'nonce': 1508507033330, 'command': 'returnCompleteBalances'}

    {"LTC":{"available":"5.015","onOrders":"1.0025","btcValue":"0.078"},"NXT:{...} ... }

    """
    post_details = get_balance_poloniex_post_details(key)
    err_msg = 'check poloniex balance called'
    timest = get_now_seconds_utc()
    error_code, res = send_post_request_with_header(post_details, err_msg, max_tries=POLONIEX_NUM_OF_DEAL_RETRY, timeout=POLONIEX_DEAL_TIMEOUT)
    if error_code == STATUS.SUCCESS:
        res = Balance.from_poloniex(timest, res)
    return (error_code, res)

# Node: get_balance_poloniex_post_details
# Node: send_post_request_with_header
def get_order_history_poloniex(key, pair_name, time_start=0, time_end=get_now_seconds_utc(), limit=POLONIEX_ORDER_HISTORY_LIMIT):
    post_details = get_order_history_poloniex_post_details(key, pair_name, time_start, time_end, limit)
    err_msg = 'get poloniex order history for time interval for pp={pp}'.format(pp=post_details)
    status_code, json_document = send_post_request_with_header(post_details, err_msg, max_tries=POLONIEX_NUM_OF_DEAL_RETRY)
    historical_orders = []
    if status_code == STATUS.SUCCESS:
        status_code, historical_orders = get_order_history_poloniex_result_processor(json_document, pair_name)
    return (status_code, historical_orders)

# Node: get_order_history_poloniex_post_details
# Node: get_order_history_poloniex_result_processor
def send_post_request_with_logging(post_details, err_msg):
    res = send_post_request_with_header(post_details, err_msg, max_tries=POLONIEX_NUM_OF_DEAL_RETRY, timeout=POLONIEX_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

def get_open_orders_poloniex(key, pair_name):
    post_details = get_open_orders_poloniex_post_details(key, pair_name)
    err_msg = 'get poloniex open orders'
    status_code, res = send_post_request_with_header(post_details, err_msg, max_tries=3)
    if get_logging_level() >= LOG_ALL_DEBUG:
        msg = 'get_open_orders_poloniex: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_DEBUG)
        log_to_file(msg, 'market_utils.log')
    orders = []
    if status_code == STATUS.SUCCESS:
        status_code, orders = get_open_orders_poloniex_result_processor(res, pair_name)
    return (status_code, orders)

# Node: get_open_orders_poloniex_post_details
# Node: get_open_orders_poloniex_result_processor
def send_post_request_with_logging(post_details, err_msg):
    res = send_post_request_with_header(post_details, err_msg, max_tries=HUOBI_NUM_OF_DEAL_RETRY, timeout=HUOBI_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

def add_sell_order_binance(key, pair_name, price, amount):
    post_details = add_sell_order_binance_url(key, pair_name, price, amount)
    err_msg = 'add_sell_order binance called for {pair} for amount = {amount} with price {price}'.format(pair=pair_name, amount=amount, price=price)
    res = send_post_request_with_header(post_details, err_msg, max_tries=BINANCE_NUM_OF_DEAL_RETRY, timeout=BINANCE_DEAL_TIMEOUT)
    '\n    {\n        "orderId": 1373492, \n        "clientOrderId": "e04JGgCpafdrR6O1lOLwgD",\n        "origQty": "1.00000000",\n        "symbol": "RDNBTC",\n        "side": "SELL",\n        "timeInForce": "GTC",\n        "status": "NEW",\n        "transactTime": 1512581721384,\n        "type": "LIMIT",\n        "price": "1.00022220",\n        "executedQty": "0.00000000"\n    }\n    '
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

# Node: add_sell_order_binance_url
def add_buy_order_binance(key, pair_name, price, amount):
    post_details = add_buy_order_binance_url(key, pair_name, price, amount)
    err_msg = 'add_buy_order_binance  called for {pair} for amount = {amount} with price {price}'.format(pair=pair_name, amount=amount, price=price)
    res = send_post_request_with_header(post_details, err_msg, max_tries=BINANCE_NUM_OF_DEAL_RETRY, timeout=BINANCE_DEAL_TIMEOUT)
    '\n    {\n        "orderId": 1373289, \n        "clientOrderId": "Is7wGaKBtLBK7JjDkNAJwn",\n        "origQty": "10.00000000",\n        "symbol": "RDNBTC",\n        "side": "BUY",\n        "timeInForce": "GTC",\n        "status": "NEW",\n        "transactTime": 1512581468544,\n        "type": "LIMIT",\n        "price": "0.00022220",\n        "executedQty": "0.00000000"\n    }\n    '
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

# Node: add_buy_order_binance_url
def get_balance_kraken(key):
    """
    Example of request and responce
        https://api.kraken.com/0/private/Balance
        {'API-Key': 'whatever',
         'API-Sign': u'whatever'}
        {'nonce': 1508503223939}

    Responce:
    {u'result': {u'DASH': u'33.2402410500', u'BCH': u'22.4980093900', u'ZUSD': u'12747.4370', u'XXBT': u'3.1387700870',
                 u'EOS': u'2450.8822990100', u'USDT': u'77.99709699', u'XXRP': u'0.24804100',
                 u'XREP': u'349.7839715600', u'XETC': u'508.0140331400', u'XETH': u'88.6104554900'}, u'error': []}
    """
    post_details = get_balance_kraken_post_details(key)
    err_msg = 'check kraken balance called'
    timest = get_now_seconds_utc()
    status_code, json_document = send_post_request_with_header(post_details, err_msg, max_tries=KRAKEN_NUM_OF_DEAL_RETRY)
    balance = None
    if status_code == STATUS.SUCCESS:
        status_code, balance = get_balance_kraken_result_processor(json_document, timest)
    return (status_code, balance)

# Node: get_balance_kraken_post_details
# Node: get_balance_kraken_result_processor
def get_order_history_kraken(key, pair_name=None, time_start=0, time_end=get_now_seconds_utc()):
    post_details = get_closed_orders_kraken_post_details(key, pair_name, time_start, time_end)
    err_msg = 'check kraken closed orders called'
    error_code, json_document = send_post_request_with_header(post_details, err_msg, max_tries=5)
    closed_orders = EMPTY_LIST
    if error_code == STATUS.SUCCESS:
        closed_orders = get_order_history_kraken_result_processor(json_document, pair_name)
    return (error_code, closed_orders)

# Node: get_closed_orders_kraken_post_details
# Node: get_order_history_kraken_result_processor
def send_post_request_with_logging(post_details, err_msg):
    res = send_post_request_with_header(post_details, err_msg, max_tries=KRAKEN_NUM_OF_DEAL_RETRY, timeout=KRAKEN_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

def get_open_orders_kraken(key, pair_name=None):
    """
     {
 	"result": {
 		"open": {
 			"OHBQIW-6R6XD-DKOE5J": {
 				"status": "open",
 				"fee": "0.00000000",
 				"expiretm": 0,
 				"descr": {
 					"leverage": "none",
 					"ordertype": "limit",
 					"price": "0.0002100",
 					"pair": "EOSXBT",
 					"price2": "0",
 					"type": "sell",
 					"order": "sell 1250.88000000 EOSXBT @ limit 0.0002100"
 				},
 				"vol": "1250.88000000",
 				"cost": "0.00000000",
 				"misc": "",
 				"price": "0.00000000",
 				"starttm": 0,
 				"userref": null,
 				"vol_exec": "0.00000000",
 				"oflags": "fciq",
 				"refid": null,
 				"opentm": 1509592448.2296
 			},
 		}
 	}
 }
    """
    post_details = get_open_orders_kraken_post_details(key, pair_name=None)
    err_msg = 'check kraken open orders called'
    status_code, res = send_post_request_with_header(post_details, err_msg, max_tries=5)
    open_orders = EMPTY_LIST
    if status_code == STATUS.SUCCESS:
        open_orders = get_open_orders_kraken_result_processor(res, pair_name)
    return (status_code, open_orders)

# Node: get_open_orders_kraken_post_details
# Node: get_open_orders_kraken_result_processor
def get_balance_bittrex(key):
    """
        https://bittrex.com/api/v1.1/account/getbalances?apikey=8a2dd16465b0469197574ec0a516badb&nonce=1508507525325
        {'apisign': 'e6bfb1cc60dcd93d291542cf6c4084e942659be7c363633f710336338a3158b37eb3f999250e5113ffc9e48c18ebe24cf9f4d496f6348a319cbd7f1bc0fc680c'} {}
        {u'message': u'',
        u'result': [{u'Available': 21300.0, u'Currency': u'ARDR', u'Balance': 21300.0, u'Pending': 0.0,
        u'CryptoAddress': u'76730d86115b49b9b7f71578feb35b7da1ca6c13e5f745aa9b630707f5439e68'},

        {u'Available': 49704.04069438, u'Currency': u'BAT', u'Balance': 49704.04069438, u'Pending': 0.0,
        u'CryptoAddress': None},

        {u'Available': 0.0, u'Currency': u'BCC', u'Balance': 0.0, u'Pending': 0.0,
        u'CryptoAddress': u'1H24rzfFWy8thV1AYQch3GByrQQuXA65LY'},

        {u'Available': 0.28912516, u'Currency': u'BTC', u'Balance': 0.28912516, u'Pending': 0.0,
        u'CryptoAddress': u'1EJztGvnKbNj3GeFbt83HhsKeLBYeu8jGq'},

        {u'Available': 0.0, u'Currency': u'BTS', u'Balance': 0.0, u'Pending': 0.0, u'CryptoAddress': u'490d0054055c43ada6e'},

        Added 07.01.2018
        Funny bittrex tend to return this:
        {u'message': u'', u'result': [], u'success': True}
        It will lead to error message - so such case should not be considered as proper response.
    """
    post_details = get_balance_bittrex_post_details(key)
    err_msg = 'check bittrex balance called'
    timest = get_now_seconds_utc()
    status_code, res = send_post_request_with_header(post_details, err_msg, max_tries=BITTREX_NUM_OF_DEAL_RETRY, timeout=BITTREX_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_DEBUG:
        log_to_file(res, DEBUG_LOG_FILE_NAME)
    if status_code == STATUS.SUCCESS:
        status_code, res = get_balance_bittrex_result_processor(res, timest)
    return (status_code, res)

# Node: get_balance_bittrex_post_details
# Node: get_balance_bittrex_result_processor
