# Cluster 38

def get_tickers_poloniex(currency_names, timest):
    final_url = get_ticker_poloniex_url(currency_names)
    err_msg = 'get_tickerS_poloniex called for list of pairS at {timest}'.format(timest=timest)
    error_code, json_response = send_request(final_url, err_msg)
    res = []
    if error_code == STATUS.SUCCESS and json_response is not None:
        for pair_name in currency_names:
            if pair_name in json_response and json_response[pair_name] is not None:
                res.append(Ticker.from_poloniex(pair_name, timest, json_response[pair_name]))
    return res

# Node: get_ticker_poloniex_url
# Node: send_request
def get_ticker_poloniex(pair_name, timest):
    final_url = get_ticker_poloniex_url(pair_name)
    err_msg = 'get_ticker_poloniex called for {pair} at {timest}'.format(pair=pair_name, timest=timest)
    error_code, json_response = send_request(final_url, err_msg)
    res = None
    if error_code == STATUS.SUCCESS:
        res = get_ticker_poloniex_result_processor(json_response, pair_name, timest)
    return res

# Node: get_ticker_poloniex_result_processor
def get_ohlc_poloniex(currency, date_start, date_end, period):
    result_set = []
    final_url = get_ohlc_poloniex_url(currency, date_start, date_end, period)
    err_msg = 'get_ohlc_poloniex called for {pair} at {timest}'.format(pair=currency, timest=date_start)
    error_code, json_responce = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        result_set = get_ohlc_poloniex_result_processor(json_responce, currency, date_start, date_end)
    return result_set

# Node: get_ohlc_poloniex_url
# Node: get_ohlc_poloniex_result_processor
def get_order_book_poloniex(pair_name, timest):
    final_url = get_order_book_poloniex_url(pair_name)
    err_msg = 'get_order_book_poloniex called for {pair} at {timest}'.format(pair=pair_name, timest=timest)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        return get_order_book_poloniex_result_processor(json_document, pair_name, timest)
    return None

# Node: get_order_book_poloniex_url
# Node: get_order_book_poloniex_result_processor
def get_history_poloniex(pair_name, prev_time, now_time):
    all_history_records = []
    final_url = get_history_poloniex_url(pair_name, prev_time, now_time)
    err_msg = 'get_history_poloniex called for {pair} at {timest}'.format(pair=pair_name, timest=now_time)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        all_history_records = get_history_poloniex_result_processor(json_document, pair_name, now_time)
    return all_history_records

# Node: get_history_poloniex_url
# Node: get_history_poloniex_result_processor
def get_ticker_huobi(pair_name, timest):
    final_url = get_ticker_huobi_url(pair_name)
    err_msg = 'get_ticker_huobi called for {pair} at {timest}'.format(pair=pair_name, timest=timest)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        return get_ticker_huobi_result_processor(json_document, pair_name, timest)
    return None

# Node: get_ticker_huobi_url
# Node: get_ticker_huobi_result_processor
def get_ohlc_huobi(currency, date_start, date_end, period):
    result_set = []
    final_url = get_ohlc_huobi_url(currency, date_start, date_end, period)
    err_msg = 'get_ohlc_huobi called for {pair} at {timest}'.format(pair=currency, timest=date_start)
    error_code, json_responce = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        result_set = get_ohlc_huobi_result_processor(json_responce, currency, date_start, date_end)
    return result_set

# Node: get_ohlc_huobi_url
# Node: get_ohlc_huobi_result_processor
def get_order_book_huobi(pair_name, timest):
    final_url = get_order_book_huobi_url(pair_name)
    err_msg = 'get_order_book_huobi called for {pair} at {timest}'.format(pair=pair_name, timest=timest)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        return get_order_book_huobi_result_processor(json_document, pair_name, timest)
    return None

# Node: get_order_book_huobi_url
# Node: get_order_book_huobi_result_processor
def get_history_huobi(pair_name, prev_time, now_time):
    final_url = get_history_huobi_url(pair_name, prev_time, now_time)
    err_msg = 'get_history_huobi called for {pair} at {timest}'.format(pair=pair_name, timest=prev_time)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        return get_history_huobi_result_processor(json_document, pair_name, now_time)
    return EMPTY_LIST

# Node: get_history_huobi_url
# Node: get_history_huobi_result_processor
def get_tickers_binance(pair_name, timest):
    """
   {"symbol":"ETHBTC","bidPrice":"0.04039700","bidQty":"4.50700000","askPrice":"0.04047500","askQty":"1.30600000"},
   {"symbol":"LTCBTC","bidPrice":"0.00875700","bidQty":"0.24000000","askPrice":"0.00876200","askQty":"0.01000000"},

    :param pair_name:
    :param timest:
    :return:
    """
    final_url = get_tickers_binance_url(pair_name)
    err_msg = 'get_tickers_binance called for list of pairS at {timest}'.format(timest=timest)
    error_code, r = send_request(final_url, err_msg)
    res = []
    if error_code == STATUS.SUCCESS and r is not None:
        for entry in r:
            if entry['symbol'] in pair_name:
                res.append(Ticker.from_binance(entry['symbol'], timest, entry))
    return res

# Node: get_tickers_binance_url
def get_ticker_binance(pair_name, timest):
    final_url = get_tickers_binance_url(pair_name)
    err_msg = 'get_ticker_binance called for {pair} at {timest}'.format(pair=pair_name, timest=timest)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        return get_ticker_binance_result_processor(json_document, pair_name, timest)
    return None

# Node: get_ticker_binance_result_processor
def get_ohlc_binance(currency, date_start, date_end, period):
    result_set = []
    final_url = get_ohlc_binance_url(currency, date_start, date_end, period)
    err_msg = 'get_ohlc_binance called for {pair} at {timest}'.format(pair=currency, timest=date_start)
    error_code, json_responce = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        result_set = get_ohlc_binance_result_processor(json_responce, currency, date_start, date_end)
    return result_set

# Node: get_ohlc_binance_url
# Node: get_ohlc_binance_result_processor
def get_history_binance(pair_name, prev_time, now_time):
    final_url = get_history_binance_url(pair_name, prev_time, now_time)
    err_msg = 'get_history_binance called for {pair} at {timest}'.format(pair=pair_name, timest=prev_time)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        return get_history_binance_result_processor(json_document, pair_name, now_time)
    return EMPTY_LIST

# Node: get_history_binance_url
# Node: get_history_binance_result_processor
def get_ticker_kraken(pair_name, timest):
    final_url = get_ticker_kraken_url(pair_name)
    err_msg = 'get_ticker_kraken called for {pair} at {timest}'.format(pair=pair_name, timest=timest)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        return get_ticker_kraken_result_processor(json_document, pair_name, timest)
    return None

# Node: get_ticker_kraken_url
# Node: get_ticker_kraken_result_processor
def get_ohlc_kraken(currency, date_start, date_end, period):
    final_url = get_ohlc_kraken_url(currency, date_start, date_end, period)
    err_msg = 'get_ohlc_kraken called for {pair} at {timest}'.format(pair=currency, timest=date_start)
    error_code, json_response = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        return get_ohlc_kraken_result_processor(json_response, currency, date_start, date_end)
    return EMPTY_LIST

# Node: get_ohlc_kraken_url
# Node: get_ohlc_kraken_result_processor
def get_order_book_kraken(pair_name, timest):
    final_url = get_order_book_kraken_url(pair_name)
    err_msg = 'get_order_book_kraken called for {pair} at {timest}'.format(pair=pair_name, timest=timest)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        return get_order_book_kraken_result_processor(json_document, pair_name, timest)
    return None

# Node: get_order_book_kraken_url
# Node: get_order_book_kraken_result_processor
def get_history_kraken(pair_name, prev_time, now_time):
    final_url = get_history_kraken_url(pair_name, prev_time, now_time)
    err_msg = 'get_history_kraken called for {pair} at {timest}'.format(pair=pair_name, timest=now_time)
    status_code, json_document = send_request(final_url, err_msg)
    if status_code == STATUS.SUCCESS:
        return get_history_kraken_result_processor(json_document, pair_name, now_time)
    return EMPTY_LIST

# Node: get_history_kraken_url
# Node: get_history_kraken_result_processor
def get_ohlc_bittrex(pair_name, date_start, date_end, period):
    result_set = []
    final_url = get_ohlc_bittrex_url(pair_name, date_start, date_end, period)
    err_msg = 'get_ohlc_bittrex called for {pair} at {timest}'.format(pair=pair_name, timest=date_start)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        result_set = get_ohlc_bittrex_result_processor(json_document, pair_name, date_start, date_end)
    return result_set

# Node: get_ohlc_bittrex_url
# Node: get_ohlc_bittrex_result_processor
def get_order_book_bittrex(pair_name, timest):
    final_url = get_order_book_bittrex_url(pair_name)
    err_msg = 'get_order_book_bittrex called for {pair} at {timest}'.format(pair=pair_name, timest=timest)
    error_code, r = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        return get_order_book_bittrex_result_processor(r, pair_name, timest)
    return None

# Node: get_order_book_bittrex_url
# Node: get_order_book_bittrex_result_processor
def get_history_bittrex(pair_name, prev_time, now_time):
    all_history_records = []
    final_url = get_history_bittrex_url(pair_name, prev_time, now_time)
    err_msg = 'get_history_bittrex called for {pair} at {timest}'.format(pair=pair_name, timest=now_time)
    error_code, json_document = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS:
        all_history_records = get_history_bittrex_result_processor(json_document, pair_name, now_time)
    return all_history_records

# Node: get_history_bittrex_url
# Node: get_history_bittrex_result_processor
