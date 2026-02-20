# Cluster 9

# Node: _urlencode
def die_hard(msg):
    log_to_file(msg, FATAL_ERROR_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)
    os._exit(1)

# Node: print_to_console
# Node: _exit
# Node: get_logging_level
# Node: get_now_seconds_utc_ms
def log_init_reset():
    msg = 'reset_arbitrage_state: started'
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_reset_final_stage():
    msg = 'reset_arbitrage_state invoked: before final stage check'
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_reset_stage_successfully():
    msg = 'reset_arbitrage_state - success!'
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_dont_have_open_orders(cfg):
    msg = 'process_expired_deals - list of open orders from both exchanges is empty, REMOVING all watched deals - consider them closed!'
    print_to_console(msg, LOG_ALL_ERRORS)
    log_to_file(msg, cfg.log_file_name)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_open_orders_bad_result(cfg):
    msg = 'Detected NONE at open_orders - we have to skip this cycle of iteration'
    print_to_console(msg, LOG_ALL_ERRORS)
    log_to_file(msg, cfg.log_file_name)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_wrong_exchange_id(exchange_id):
    msg = 'UNKNOWN exchange id provided - {idx}'.format(idx=exchange_id)
    print_to_console(msg, LOG_ALL_ERRORS)

def get_balance_poloniex_post_details(key):
    body = {'command': 'returnCompleteBalances', 'nonce': generate_nonce()}
    headers = {'Key': key.api_key, 'Sign': signed_body(body, key.secret)}
    final_url = POLONIEX_CHECK_BALANCE
    res = PostRequestDetails(final_url, headers, body)
    if should_print_debug():
        print_to_console(res, LOG_ALL_MARKET_NETWORK_RELATED_CRAP)
    return res

# Node: generate_nonce
# Node: signed_body
# Node: PostRequestDetails
# Node: should_print_debug
# Node: send_post_request_with_header
def get_order_history_poloniex_post_details(key, pair_name, time_start, time_end, limit):
    body = {'command': 'returnTradeHistory', 'currencyPair': pair_name, 'start': time_start, 'end': time_end, 'limit': limit, 'nonce': generate_nonce()}
    headers = {'Key': key.api_key, 'Sign': signed_body(body, key.secret)}
    final_url = POLONIEX_GET_ORDER_HISTORY
    post_details = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'get orders history poloniex: {res}'.format(res=post_details)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return post_details

def add_sell_order_poloniex_url(key, pair_name, price, amount):
    body = generate_body(pair_name, price, amount, 'sell')
    headers = {'Key': key.api_key, 'Sign': signed_body(body, key.secret)}
    final_url = POLONIEX_SELL_ORDER
    res = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'add_sell_order_poloniex: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return res

# Node: generate_body
def add_sell_order_poloniex(key, pair_name, price, amount):
    post_details = add_sell_order_poloniex_url(key, pair_name, price, amount)
    err_msg = 'add_sell_order poloniex called for {pair} for amount = {amount} with price {price}'.format(pair=pair_name, amount=amount, price=price)
    return send_post_request_with_logging(post_details, err_msg)

# Node: add_sell_order_poloniex_url
# Node: send_post_request_with_logging
def get_ticker_poloniex_url(currency_names):
    """

    :param currency_names: for backwards compatibility
    :param timest: for backwards compatibility
    :return:
    """
    final_url = POLONIEX_GET_TICKER
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def get_ohlc_poloniex_url(currency, date_start, date_end, period):
    final_url = POLONIEX_GET_OHLC + currency + '&start=' + str(date_start) + '&end=' + str(date_end) + '&period=' + str(period)
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def generate_body(pair_name, price, amount, order_type):
    return {'command': order_type, 'currencyPair': pair_name, 'rate': float_to_str(price), 'amount': float_to_str(amount), 'nonce': generate_nonce()}

def send_post_request_with_logging(post_details, err_msg):
    res = send_post_request_with_header(post_details, err_msg, max_tries=POLONIEX_NUM_OF_DEAL_RETRY, timeout=POLONIEX_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

def add_buy_order_poloniex_url(key, pair_name, price, amount):
    body = generate_body(pair_name, price, amount, 'buy')
    headers = {'Key': key.api_key, 'Sign': signed_body(body, key.secret)}
    final_url = POLONIEX_BUY_ORDER
    res = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'add_buy_order_poloniex: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return res

def add_buy_order_poloniex(key, pair_name, price, amount):
    post_details = add_buy_order_poloniex_url(key, pair_name, price, amount)
    err_msg = 'add_buy_order poloniex called for {pair} for amount = {amount} with price {price}'.format(pair=pair_name, amount=amount, price=price)
    return send_post_request_with_logging(post_details, err_msg)

# Node: add_buy_order_poloniex_url
def get_order_book_poloniex_url(pair_name):
    final_url = POLONIEX_GET_ORDER_BOOK + pair_name
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def get_open_orders_poloniex_post_details(key, pair_name):
    body = {'command': 'returnOpenOrders', 'currencyPair': pair_name, 'nonce': generate_nonce()}
    headers = {'Key': key.api_key, 'Sign': signed_body(body, key.secret)}
    final_url = POLONIEX_GET_OPEN_ORDERS
    res = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'get_open_order_poloniex: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
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
def cancel_order_poloniex(key, order_id):
    body = {'command': 'cancelOrder', 'orderNumber': order_id, 'nonce': generate_nonce()}
    headers = {'Key': key.api_key, 'Sign': signed_body(body, key.secret)}
    final_url = POLONIEX_CANCEL_ORDER
    post_details = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'add_sell_order_poloniex: {res}'.format(res=post_details)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    err_msg = 'cancel poloniex called for {order_id}'.format(order_id=order_id)
    return send_post_request_with_logging(post_details, err_msg)

def get_history_poloniex_url(pair_name, prev_time, now_time):
    final_url = POLONIEX_GET_HISTORY + pair_name + '&start=' + str(prev_time) + '&end=' + str(now_time)
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_OTHER_STUFF)
    return final_url

class MessageQueue(RedisConnection):

    def add_message(self, topic_id, msg):
        msg_with_ts = '{msg}\nTS:{ts}'.format(msg=msg, ts=get_now_seconds_utc_ms())
        self.r.rpush(topic_id, msg_with_ts)

    def get_topic_size(self, topic_id):
        return self.r.llen(topic_id)

    def empty(self, topic_id):
        return self.get_topic_size(topic_id) == 0

    def get_message(self, topic_id, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        item = self.r.lpop(topic_id)
        return item

    def get_message_nowait(self, topic_id):
        """Equivalent to get(False)."""
        return self.get_message(topic_id, True)

    def add_message_to_start(self, topic_id, msg):
        self.r.lpush(topic_id, msg)

    def add_order(self, topic_id, balance):
        self.r.lpush(topic_id, pickle.dumps(balance))

    def get_next_order(self, topic_id):
        entry = self.get_message(topic_id, True)
        if entry:
            return pickle.loads(entry)
        return None

def add_message(self, topic_id, msg):
    msg_with_ts = '{msg}\nTS:{ts}'.format(msg=msg, ts=get_now_seconds_utc_ms())
    self.r.rpush(topic_id, msg_with_ts)

# Node: rpush
def get_balance_huobi_post_details(key):
    path = HUOBI_CHECK_BALANCE + get_huobi_account(key) + '/balance'
    final_url = HUOBI_API_URL + path + '?'
    body, url = generate_body_and_url_get_request(key, HUOBI_API_ONLY, path)
    final_url += url
    res = PostRequestDetails(final_url, HUOBI_GET_HEADERS, body)
    if should_print_debug():
        print_to_console(res, LOG_ALL_MARKET_NETWORK_RELATED_CRAP)
    return res

# Node: get_huobi_account
# Node: generate_body_and_url_get_request
# Node: send_get_request_with_header
def get_order_history_huobi(key, pair_name, time_start=0, time_end=get_now_seconds_utc()):
    post_details = get_order_history_huobi_post_details(key, pair_name, time_start, time_end)
    err_msg = 'get_all_orders_huobi for {pair_name}'.format(pair_name=pair_name)
    status_code, json_response = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=HUOBI_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_DEBUG:
        msg = 'get_order_history_huobi: {sc} {resp}'.format(sc=status_code, resp=json_response)
        print_to_console(msg, LOG_ALL_DEBUG)
        log_to_file(msg, DEBUG_LOG_FILE_NAME)
    historical_orders = []
    if status_code == STATUS.SUCCESS:
        status_code, historical_orders = get_orders_huobi_result_processor(json_response, pair_name)
    return (status_code, historical_orders)

# Node: get_order_history_huobi_post_details
# Node: get_orders_huobi_result_processor
def add_sell_order_huobi_url(key, pair_name, price, amount):
    final_url = SELL_URL + generate_url(key, HUOBI_API_ONLY, HUOBI_SELL_ORDER)
    params = json.dumps({'amount': float_to_str(amount), 'price': float_to_str(price), 'symbol': pair_name, 'source': 'api', 'type': 'sell-limit', 'account-id': get_huobi_account(key)})
    res = PostRequestDetails(final_url, HUOBI_POST_HEADERS, params)
    return res

# Node: generate_url
def add_sell_order_huobi(key, pair_name, price, amount):
    post_details = add_sell_order_huobi_url(key, pair_name, price, amount)
    err_msg = 'add_sell_order huobi called for {pair} for amount = {amount} with price {price}'.format(pair=pair_name, amount=amount, price=price)
    return send_post_request_with_logging(post_details, err_msg)

# Node: add_sell_order_huobi_url
def get_ticker_huobi_url(pair_name):
    final_url = HUOBI_GET_TICKER + pair_name
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_OTHER_STUFF)
    return final_url

def get_ohlc_huobi_url(pair_name, date_start, date_end, period):
    date_start_ms = 1000 * date_start
    final_url = HUOBI_GET_OHLC + pair_name + '&period=' + period
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def get_huobi_account_impl(key):
    final_url = HUOBI_API_URL + HUOBI_GET_ACCOUNT_INFO + '?'
    body, url = generate_body_and_url_get_request(key, HUOBI_API_ONLY, HUOBI_GET_ACCOUNT_INFO)
    final_url += url
    post_details = PostRequestDetails(final_url, HUOBI_GET_HEADERS, body)
    err_msg = 'get_huobi_account'
    error_code, res = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=HUOBI_DEAL_TIMEOUT)
    if error_code == STATUS.SUCCESS and 'data' in res and (len(res['data']) > 0):
        return res['data'][0]['id']
    return None

def send_post_request_with_logging(post_details, err_msg):
    res = send_post_request_with_header(post_details, err_msg, max_tries=HUOBI_NUM_OF_DEAL_RETRY, timeout=HUOBI_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

def add_buy_order_huobi_url(key, pair_name, price, amount):
    final_url = BUY_URL + generate_url(key, HUOBI_API_ONLY, HUOBI_BUY_ORDER)
    params = json.dumps({'account-id': get_huobi_account(key), 'amount': float_to_str(amount), 'price': float_to_str(price), 'source': 'api', 'symbol': pair_name, 'type': 'buy-limit'})
    res = PostRequestDetails(final_url, HUOBI_POST_HEADERS, params)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'add_buy_order_huobi: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return res

def add_buy_order_huobi(key, pair_name, price, amount):
    post_details = add_buy_order_huobi_url(key, pair_name, price, amount)
    err_msg = 'add_buy_order_huobi  called for {pair} for amount = {amount} with price {price}'.format(pair=pair_name, amount=amount, price=price)
    return send_post_request_with_logging(post_details, err_msg)

# Node: add_buy_order_huobi_url
def get_order_book_huobi_url(pair_name):
    final_url = HUOBI_GET_ORDER_BOOK + pair_name + '&type=step0'
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def get_open_orders_huobi(key, pair_name):
    post_details = get_open_orders_huobi_post_details(key, pair_name)
    err_msg = 'get_orders_huobi'
    status_code, res = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=HUOBI_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_DEBUG:
        msg = 'get_open_orders_huobi: {r}'.format(r=res)
        print_to_console(msg, LOG_ALL_DEBUG)
        log_to_file(msg, DEBUG_LOG_FILE_NAME)
    orders = []
    if status_code == STATUS.SUCCESS:
        status_code, orders = get_orders_huobi_result_processor(res, pair_name)
    return (status_code, orders)

# Node: get_open_orders_huobi_post_details
def cancel_order_huobi(key, order_id):
    HUOBI_CANCEL_PATH = HUOBI_CANCEL_ORDER + str(order_id) + '/submitcancel'
    final_url = HUOBI_API_URL + HUOBI_CANCEL_PATH + '?'
    body = init_body(key)
    message = _urlencode(body).encode('utf8')
    msg = 'POST\n{base_url}\n{path}\n{msg1}'.format(base_url=HUOBI_API_ONLY, path=HUOBI_CANCEL_PATH, msg1=message)
    signature = sign_string_256_base64(key.secret, msg)
    body.append(('Signature', signature))
    final_url += _urlencode(body).encode('utf8')
    body = {}
    post_details = PostRequestDetails(final_url, HUOBI_POST_HEADERS, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'cancel_order_huobi: url - {url} headers - {headers} body - {body}'.format(url=final_url, headers=HUOBI_POST_HEADERS, body=body)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    err_msg = 'cancel huobi order with id {id}'.format(id=order_id)
    return send_post_request_with_logging(post_details, err_msg)

def get_history_huobi_url(pair_name, date_start, date_end):
    final_url = HUOBI_GET_HISTORY + pair_name + '&size=1000'
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_OTHER_STUFF)
    return final_url

def get_balance_binance_post_details(key):
    final_url = BINANCE_CHECK_BALANCE
    body = {'timestamp': get_now_seconds_utc_ms(), 'recvWindow': 5000}
    res = generate_post_request(final_url, body, key)
    if should_print_debug():
        print_to_console(res, LOG_ALL_MARKET_NETWORK_RELATED_CRAP)
    return res

# Node: generate_post_request
def get_order_history_binance_post_details(key, pair_name, limit, last_order_id=None):
    body = {'symbol': pair_name, 'limit': limit, 'timestamp': get_now_seconds_utc_ms(), 'recvWindow': 5000}
    if last_order_id is not None:
        body['orderId'] = last_order_id
    post_details = generate_post_request(BINANCE_GET_ALL_ORDERS, body, key)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'get orders history binance: {res}'.format(res=post_details)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return post_details

def get_order_history_binance(key, pair_name, limit=BINANCE_ORDER_HISTORY_LIMIT, last_order_id=None):
    post_details = get_order_history_binance_post_details(key, pair_name, limit, last_order_id)
    err_msg = 'get_all_orders_binance for {pair_name}'.format(pair_name=pair_name)
    status_code, json_response = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=BINANCE_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_DEBUG:
        msg = 'get_order_history_binance: {sc} {resp}'.format(sc=status_code, resp=json_response)
        print_to_console(msg, LOG_ALL_DEBUG)
        log_to_file(msg, DEBUG_LOG_FILE_NAME)
    historical_orders = []
    if status_code == STATUS.SUCCESS:
        msg = '{fn} - error response - {er}'.format(fn=get_order_history_binance.func_name, er=json_response)
        status_code, historical_orders = get_orders_binance_result_processor(json_response, pair_name, msg)
    return (status_code, historical_orders)

# Node: get_order_history_binance_post_details
# Node: get_orders_binance_result_processor
def add_sell_order_binance_url(key, pair_name, price, amount):
    final_url = BINANCE_SELL_ORDER
    body = {'symbol': pair_name, 'side': 'SELL', 'type': 'LIMIT', 'timeInForce': 'GTC', 'recvWindow': 5000, 'timestamp': get_now_seconds_utc_ms(), 'quantity': amount, 'price': float_to_str(price)}
    res = generate_post_request(final_url, body, key)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'add_sell_order_binance: url - {url} headers - {headers} body - {body}'.format(url=res.final_url, headers=res.headers, body=res.body)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
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
def get_tickers_binance_url(pair_name):
    final_url = BINANCE_GET_TICKER
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_OTHER_STUFF)
    return final_url

def get_ohlc_binance_url(currency, date_start, date_end, period):
    date_start_ms = 1000 * date_start
    final_url = BINANCE_GET_OHLC + currency + '&interval=' + period + '&startTime=' + str(date_start_ms)
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def generate_post_request(final_url, body, key):
    signature = signed_body_256(body, key.secret)
    body['signature'] = signature
    final_url += _urlencode(body)
    headers = {'X-MBX-APIKEY': key.api_key}
    body = {}
    return PostRequestDetails(final_url, headers, body)

# Node: signed_body_256
def add_buy_order_binance_url(key, pair_name, price, amount):
    body = {'symbol': pair_name, 'side': 'BUY', 'type': 'LIMIT', 'timeInForce': 'GTC', 'recvWindow': 5000, 'timestamp': get_now_seconds_utc_ms(), 'quantity': amount, 'price': float_to_str(price)}
    res = generate_post_request(BINANCE_BUY_ORDER, body, key)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'add_buy_order_binance: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return res

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
def get_order_book_binance_url(currency):
    final_url = BINANCE_GET_ORDER_BOOK + currency
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def get_open_orders_binance_post_details(key, pair_name):
    body = {'symbol': pair_name, 'timestamp': get_now_seconds_utc_ms(), 'recvWindow': 5000}
    post_details = generate_post_request(BINANCE_GET_ALL_OPEN_ORDERS, body, key)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'get_open_orders_binance_post_details: {res}'.format(res=post_details)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return post_details

def get_open_orders_binance(key, pair_name):
    post_details = get_open_orders_binance_post_details(key, pair_name)
    err_msg = 'get_orders_binance'
    status_code, res = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=BINANCE_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_DEBUG:
        msg = 'get_open_orders_binance: {r}'.format(r=res)
        print_to_console(msg, LOG_ALL_DEBUG)
        log_to_file(msg, DEBUG_LOG_FILE_NAME)
    orders = []
    if status_code == STATUS.SUCCESS:
        status_code, orders = get_open_orders_binance_result_processor(res, pair_name)
    return (status_code, orders)

# Node: get_open_orders_binance_post_details
# Node: get_open_orders_binance_result_processor
def get_open_orders_binance_result_processor(json_document, pair_name):
    """
    json_document - response from exchange api as json string
    pair_name - for backwords compabilities
    """
    msg = 'get_open_orders_binance_result_processor - error response - {er}'.format(er=json_document)
    return get_orders_binance_result_processor(json_document, pair_name, msg)

def cancel_order_binance(key, pair_name, order_id):
    body = {'recvWindow': 5000, 'timestamp': get_now_seconds_utc_ms(), 'symbol': pair_name, 'orderId': order_id}
    post_details = generate_post_request(BINANCE_CANCEL_ORDER, body, key)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'cancel_order_binance: url - {url} headers - {headers} body - {body}'.format(url=post_details.final_url, headers=post_details.headers, body=post_details.body)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    err_msg = 'cancel binance order with id {id}'.format(id=order_id)
    res = send_delete_request_with_header(post_details, err_msg, max_tries=3)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

# Node: send_delete_request_with_header
def get_trades_history_binance(key, pair_name, limit, last_order_id=None):
    final_url = BINANCE_GET_ALL_TRADES
    body = []
    if last_order_id is not None:
        body.append(('fromId', last_order_id))
    body.append(('symbol', pair_name))
    body.append(('limit', limit))
    body.append(('timestamp', get_now_seconds_utc_ms()))
    body.append(('recvWindow', 5000))
    body.append(('signature', signed_body_256(body, key.secret)))
    post_details = generate_post_request(final_url, body, key)
    if get_logging_level() >= LOG_ALL_DEBUG:
        msg = 'get_trades_history_binance: {res}'.format(res=post_details)
        print_to_console(msg, LOG_ALL_DEBUG)
        log_to_file(msg, DEBUG_LOG_FILE_NAME)
    err_msg = 'get_all_trades_binance for {pair_name}'.format(pair_name=pair_name)
    error_code, res = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=BINANCE_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_DEBUG:
        msg = 'get_all_trades_binance: {er_c} {r}'.format(er_c=error_code, r=res)
        print_to_console(msg, LOG_ALL_DEBUG)
        log_to_file(msg, DEBUG_LOG_FILE_NAME)
    return (error_code, res)

def get_history_binance_url(pair_name, date_start, date_end):
    final_url = BINANCE_GET_HISTORY + pair_name
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_OTHER_STUFF)
    return final_url

def get_balance_kraken_post_details(key):
    final_url = KRAKEN_BASE_API_URL + KRAKEN_CHECK_BALANCE
    body = {'nonce': generate_nonce()}
    headers = {'API-Key': key.api_key, 'API-Sign': sign_kraken(body, KRAKEN_CHECK_BALANCE, key.secret)}
    res = PostRequestDetails(final_url, headers, body)
    if should_print_debug():
        print_to_console(res, LOG_ALL_MARKET_NETWORK_RELATED_CRAP)
    return res

# Node: sign_kraken
def get_closed_orders_kraken_post_details(key, pair_name=None, time_start=0, time_end=get_now_seconds_utc()):
    final_url = KRAKEN_BASE_API_URL + KRAKEN_GET_CLOSE_ORDERS
    body = {'nonce': generate_nonce(), 'start': time_start, 'end': time_end}
    headers = {'API-Key': key.api_key, 'API-Sign': sign_kraken(body, KRAKEN_GET_CLOSE_ORDERS, key.secret)}
    res = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'get_closed_orders_kraken: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return res

def add_sell_order_kraken_url(key, pair_name, price, amount):
    final_url = KRAKEN_BASE_API_URL + KRAKEN_SELL_ORDER
    body = generate_body(pair_name, price, amount, 'sell')
    headers = {'API-Key': key.api_key, 'API-Sign': sign_kraken(body, KRAKEN_SELL_ORDER, key.secret)}
    res = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'add_sell_order_kraken_url: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return res

def add_sell_order_kraken(key, pair_name, price, amount):
    post_details = add_sell_order_kraken_url(key, pair_name, price, amount)
    err_msg = 'add_sell_order kraken called for {pair} for amount = {amount} with price {price}'.format(pair=pair_name, amount=amount, price=price)
    return send_post_request_with_logging(post_details, err_msg)

# Node: add_sell_order_kraken_url
def get_ticker_kraken_url(pair_name):
    final_url = KRAKEN_GET_TICKER + pair_name
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def get_ohlc_kraken_url(currency, date_start, date_end, period):
    final_url = KRAKEN_GET_OHLC + currency + '&since=' + str(date_start) + '&interval=' + str(period)
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def send_post_request_with_logging(post_details, err_msg):
    res = send_post_request_with_header(post_details, err_msg, max_tries=KRAKEN_NUM_OF_DEAL_RETRY, timeout=KRAKEN_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

def generate_body(pair_name, price, amount, order_type):
    return {'pair': pair_name, 'type': order_type, 'ordertype': 'limit', 'price': float_to_str(price), 'volume': float_to_str(amount), 'nonce': generate_nonce()}

def add_buy_order_kraken_url(key, pair_name, price, amount):
    final_url = KRAKEN_BASE_API_URL + KRAKEN_BUY_ORDER
    body = generate_body(pair_name, price, amount, 'buy')
    headers = {'API-Key': key.api_key, 'API-Sign': sign_kraken(body, KRAKEN_BUY_ORDER, key.secret)}
    res = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'add_buy_order_kraken: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return res

def add_buy_order_kraken(key, pair_name, price, amount):
    post_details = add_buy_order_kraken_url(key, pair_name, price, amount)
    err_msg = 'add_buy_order kraken called for {pair} for amount = {amount} with price {price}'.format(pair=pair_name, amount=amount, price=price)
    return send_post_request_with_logging(post_details, err_msg)

# Node: add_buy_order_kraken_url
def get_order_book_kraken_url(pair_name):
    final_url = KRAKEN_GET_ORDER_BOOK + pair_name
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def get_open_orders_kraken_post_details(key, pair_name=None):
    final_url = KRAKEN_BASE_API_URL + KRAKEN_GET_OPEN_ORDERS
    body = {'nonce': generate_nonce()}
    headers = {'API-Key': key.api_key, 'API-Sign': sign_kraken(body, KRAKEN_GET_OPEN_ORDERS, key.secret)}
    res = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'ger_open_orders_kraken: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
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
def cancel_order_kraken(key, order_id):
    final_url = KRAKEN_BASE_API_URL + KRAKEN_CANCEL_ORDER
    body = {'txid': order_id, 'nonce': generate_nonce()}
    headers = {'API-Key': key.api_key, 'API-Sign': sign_kraken(body, KRAKEN_CANCEL_ORDER, key.secret)}
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'cancel_order_kraken: url - {url} headers - {headers} body - {body}'.format(url=final_url, headers=headers, body=body)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    post_details = PostRequestDetails(final_url, headers, body)
    err_msg = 'cancel kraken called for {order_id}'.format(order_id=order_id)
    return send_post_request_with_logging(post_details, err_msg)

def get_history_kraken_url(pair_name, prev_time, now_time):
    """

    :param pair_name:
    :param prev_time:
    :param now_time: for backwards compatibility
    :return:
    """
    final_url = KRAKEN_GET_HISTORY + pair_name + '&since=' + str(prev_time)
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_OTHER_STUFF)
    return final_url

def get_balance_bittrex_post_details(key):
    final_url = BITTREX_CHECK_BALANCE + key.api_key + '&nonce=' + str(generate_nonce())
    body = {}
    final_url += _urlencode(body)
    headers = {'apisign': signed_string(final_url, key.secret)}
    res = PostRequestDetails(final_url, headers, body)
    if should_print_debug():
        print_to_console(res, LOG_ALL_MARKET_NETWORK_RELATED_CRAP)
    return res

# Node: signed_string
def get_order_history_bittrex_post_details(key, pair_name):
    final_url = BITTREX_GET_TRADE_HISTORY + key.api_key + '&nonce=' + str(generate_nonce())
    if pair_name != 'all':
        body = {'market': pair_name}
    else:
        body = {}
    final_url += _urlencode(body)
    headers = {'apisign': signed_string(final_url, key.secret)}
    post_details = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'get_order_history_bittrex_post_details: {res}'.format(res=post_details)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return post_details

def get_order_history_bittrex(key, pair_name):
    post_details = get_order_history_bittrex_post_details(key, pair_name)
    err_msg = 'get bittrex order history for time interval for pp={pp}'.format(pp=post_details)
    status_code, json_response = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg)
    historical_orders = []
    if status_code == STATUS.SUCCESS:
        status_code, historical_orders = get_order_history_bittrex_result_processor(json_response, pair_name)
    return (status_code, historical_orders)

# Node: get_order_history_bittrex_post_details
# Node: get_order_history_bittrex_result_processor
def add_sell_order_bittrex_url(key, pair_name, price, amount):
    final_url = BITTREX_SELL_ORDER + key.api_key + '&nonce=' + str(generate_nonce())
    body = {'market': pair_name, 'quantity': float_to_str(amount), 'rate': float_to_str(price)}
    final_url += _urlencode(body)
    headers = {'apisign': signed_string(final_url, key.secret)}
    res = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'add_sell_order_bittrex: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return res

def add_sell_order_bittrex(key, pair_name, price, amount):
    post_details = add_sell_order_bittrex_url(key, pair_name, price, amount)
    err_msg = 'add_sell_order bittrex called for {pair} for amount = {amount} with price {price}'.format(pair=pair_name, amount=amount, price=price)
    res = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=BITTREX_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

# Node: add_sell_order_bittrex_url
def get_ohlc_bittrex_url(pair_name, date_start, date_end, period):
    result_set = []
    final_url = BITTREX_GET_OHLC + period + '&marketName=' + pair_name + '&_=' + str(date_start)
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def add_buy_order_bittrex_url(key, pair_name, price, amount):
    final_url = BITTREX_BUY_ORDER + key.api_key + '&nonce=' + str(generate_nonce())
    body = {'market': pair_name, 'quantity': float_to_str(amount), 'rate': float_to_str(price)}
    final_url += _urlencode(body)
    headers = {'apisign': signed_string(final_url, key.secret)}
    post_details = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'add_buy_order_bittrex: {res}'.format(res=post_details)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return post_details

def add_buy_order_bittrex(key, pair_name, price, amount):
    post_details = add_buy_order_bittrex_url(key, pair_name, price, amount)
    err_msg = 'add_buy_order bittrex called for {pair} for amount = {amount} with price {price}'.format(pair=pair_name, amount=amount, price=price)
    res = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=BITTREX_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

# Node: add_buy_order_bittrex_url
def get_order_book_bittrex_url(pair_name):
    final_url = BITTREX_GET_ORDER_BOOK + pair_name
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_DEBUG)
    return final_url

def get_open_orders_bittrix_post_details(key, pair_name):
    final_url = BITTREX_GET_OPEN_ORDERS + key.api_key + '&nonce=' + str(generate_nonce())
    body = {'market': pair_name} if pair_name is not None else {}
    final_url += _urlencode(body)
    headers = {'apisign': signed_string(final_url, key.secret)}
    res = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'get_open_orders_bittrix: {res}'.format(res=res)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    return res

def get_open_orders_bittrix(key, pair_name):
    post_details = get_open_orders_bittrix_post_details(key, pair_name)
    err_msg = 'get_orders_bittrix'
    status_code, res = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=BITTREX_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_DEBUG:
        msg = 'get_open_orders_bittrix: {r}'.format(r=res)
        print_to_console(msg, LOG_ALL_DEBUG)
        log_to_file(msg, DEBUG_LOG_FILE_NAME)
    orders = []
    if status_code == STATUS.SUCCESS:
        status_code, orders = get_open_orders_bittrex_result_processor(res, pair_name)
    return (status_code, orders)

# Node: get_open_orders_bittrix_post_details
# Node: get_open_orders_bittrex_result_processor
def cancel_order_bittrex(key, order_id):
    final_url = BITTREX_CANCEL_ORDER + key.api_key + '&nonce=' + str(generate_nonce())
    body = {'uuid': order_id}
    final_url += _urlencode(body)
    headers = {'apisign': signed_string(final_url, key.secret)}
    post_details = PostRequestDetails(final_url, headers, body)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        msg = 'cancel_order_bittrex: {res}'.format(res=post_details)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(msg, 'market_utils.log')
    err_msg = 'cancel bittrex order with id {id}'.format(id=order_id)
    res = send_get_request_with_header(post_details.final_url, post_details.headers, err_msg, timeout=BITTREX_DEAL_TIMEOUT)
    if get_logging_level() >= LOG_ALL_MARKET_RELATED_CRAP:
        print_to_console(res, LOG_ALL_MARKET_RELATED_CRAP)
        log_to_file(res, 'market_utils.log')
    return res

def get_history_bittrex_url(pair_name, prev_time, now_time):
    final_url = BITTREX_GET_HISTORY + pair_name + '&since=' + str(prev_time)
    if should_print_debug():
        print_to_console(final_url, LOG_ALL_OTHER_STUFF)
    return final_url

def get_diff_lowest_ask_vs_highest_bid(first_one, second_one, threshold):
    difference = get_change(first_one.ask, second_one.bid)
    if should_print_debug():
        msg = 'get_diff_lowest_ask_vs_highest_bid: ASK = {ask} BID = {bid} DIFF={diff}'.format(ask=first_one.ask, bid=second_one.bid, diff=difference)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
    if difference >= threshold:
        msg = 'Lowest ask differ from highest bid more than {num} %'.format(num=threshold)
        return (msg, first_one.pair_id, first_one, second_one)
    return ()

# Node: get_change
def check_highest_bid_bigger_than_lowest_ask(first_one, second_one, threshold):
    if not first_one.bid or not second_one.ask:
        return
    difference = get_change(first_one.bid, second_one.ask, provide_abs=False)
    if should_print_debug():
        msg = 'check_highest_bid_bigger_than_lowest_ask called for\n        threshold = {threshold}\n        BID: {bid:.7f}\n        AKS: {ask:.7f}\n        DIFF: {diff:.7f}\n        '.format(threshold=threshold, bid=first_one.bid, ask=second_one.ask, diff=difference)
        print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
    if difference >= threshold:
        factual_threshold = threshold
        severity_flag = ''
        if 5.0 < difference < 10.0:
            severity_flag = '<b> ! ACT NOW ! </b>'
            factual_threshold = 5.0
        elif difference > 10.0:
            severity_flag = '<b>!!! ACT IMMEDIATELY !!!</b>'
            factual_threshold = 10.0
        msg = '{severity_flag}\n        highest bid bigger than Lowest ask for more than {num} - <b>{diff:.7f}</b>'.format(severity_flag=severity_flag, num=factual_threshold, diff=difference)
        return (msg, first_one.pair_id, first_one, second_one)
    return ()

