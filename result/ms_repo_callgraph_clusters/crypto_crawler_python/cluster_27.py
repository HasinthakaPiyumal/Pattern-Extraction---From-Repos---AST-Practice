# Cluster 27

def binary_search(some_list, target, cmp_method):
    """

    Generic method that will return INDEX for insertion of `target` element into list `some_list`

    :param some_list: element must have implementation of __eq__ method
    :param target: elements to be inserted
    :param cmp_method:
    :return:

    """
    min_idx = 0
    max_idx = len(some_list) - 1
    mid_idx = (min_idx + max_idx) / 2
    if mid_idx < 0:
        return 0
    elif min_idx == max_idx:
        if cmp_method(some_list[mid_idx], target):
            return mid_idx + 1
        return mid_idx
    while min_idx < max_idx:
        if some_list[mid_idx] == target:
            return mid_idx
        elif cmp_method(some_list[mid_idx], target):
            return mid_idx + 1 + binary_search(some_list[mid_idx + 1:], target, cmp_method)
        else:
            return binary_search(some_list[:mid_idx], target, cmp_method)

# Node: len
# Node: cmp_method
# Node: binary_search
# Node: str
def truncate_float(float_num, n):
    str_repr = str(float_num)
    idx = str_repr.find('.')
    if idx > 0:
        return float(str_repr[0:1 + idx + n])
    else:
        return float_num

# Node: find
# Node: float
# Node: get_now_seconds_utc
class OrderState(BaseData):

    def __init__(self, exchange_id, timest, open_orders, closed_orders):
        self.exchange_id = exchange_id
        self.timest = timest
        self.open_orders = copy.deepcopy(open_orders)
        self.closed_orders = copy.deepcopy(closed_orders)

    def get_num_of_open_orders(self):
        return len(self.open_orders)

    def get_num_of_closed_orders(self):
        return len(self.closed_orders)

    def get_total_num_of_orders(self):
        return self.get_num_of_closed_orders() + self.get_num_of_open_orders()

def get_num_of_open_orders(self):
    return len(self.open_orders)

def get_num_of_closed_orders(self):
    return len(self.closed_orders)

class OrderBook(BaseData):
    insert_query = ORDER_BOOK_INSERT_QUERY
    type = ORDER_BOOK_TYPE_NAME
    table_name = ORDER_BOOK_TABLE_NAME
    columns = ORDER_BOOK_COLUMNS

    def __init__(self, pair_id, timest, sell_bids, buy_bids, exchange_id, sequence_id=None):
        self.pair_id = int(pair_id)
        self.pair_name = get_pair_name_by_id(self.pair_id)
        self.timest = timest
        self.ask = sell_bids
        self.bid = buy_bids
        self.exchange_id = int(exchange_id)
        self.exchange = get_exchange_name_by_id(self.exchange_id)
        self.sequence_id = sequence_id

    def is_valid(self):
        return self.ask and self.bid

    def sort_by_price(self):
        self.bid = sorted(self.bid, key=lambda x: x.price, reverse=True)
        self.ask = sorted(self.ask, key=lambda x: x.price, reverse=False)

    def get_pg_arg_list(self):
        return (self.pair_id, self.exchange_id, self.timest, get_date_time_from_epoch(self.timest))

    def __str__(self):
        attr_list = [a for a in dir(self) if not a.startswith('__') and (not a.startswith('ask')) and (not a.startswith('bid')) and (not a.startswith('insert')) and (not callable(getattr(self, a)))]
        str_repr = '['
        for every_attr in attr_list:
            str_repr += every_attr + ' - ' + str(getattr(self, every_attr)) + ' '
        str_repr += 'bids - [' + '\n'.join(map(str, self.bid)) + '] '
        str_repr += 'asks - [' + '\n'.join(map(str, self.ask)) + ']]'
        return str_repr

    @classmethod
    def from_poloniex(cls, json_document, currency, timest):
        """
        {"asks":[["0.00006604",11590.35669799],["0.00006606",25756.70896058]],
        "bids":[["0.00006600",46771.47390146],["0.00006591",25268.665],],
        "isFrozen":"0","seq":41049600}
        """
        sell_bids = [Deal(entry[0], entry[1]) for entry in json_document['asks']]
        buy_bids = [Deal(entry[0], entry[1]) for entry in json_document['bids']]
        pair_id = get_currency_pair_from_poloniex(currency)
        sequence_id = long(json_document['seq'])
        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.POLONIEX, sequence_id)

    @classmethod
    def from_kraken(cls, json_document, currency, timest):
        """
        {"error":[],"result":{"XETHXXBT":{"asks":[["0.081451","0.200",1501690777],["0.081496","163.150",1501691124]
        "bids":[["0.080928","0.100",1501691107],["0.080926","0.255",1501691110]
        """
        sell_bids = [Deal(entry[0], entry[1]) for entry in json_document['asks']]
        buy_bids = [Deal(entry[0], entry[1]) for entry in json_document['bids']]
        pair_id = get_currency_pair_from_kraken(currency)
        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.KRAKEN)

    @classmethod
    def from_bittrex(cls, json_document, currency, timest):
        """
        {"success":true,"message":"","result":{"buy":[{"Quantity":12.76073322,"Rate":0.01557999},{"Quantity":12.01802925,"Rate":0.01557998}
        "sell":[{"Quantity":0.38767680,"Rate":0.01560999},{"Quantity":2.24182363,"Rate":0.01561999}
        """
        sell_bids = []
        if 'sell' in json_document and json_document['sell'] is not None:
            for b in json_document['sell']:
                sell_bids.append(Deal(b['Rate'], b['Quantity']))
        buy_bids = []
        if 'buy' in json_document and json_document['buy'] is not None:
            for b in json_document['buy']:
                buy_bids.append(Deal(b['Rate'], b['Quantity']))
        pair_id = get_currency_pair_from_bittrex(currency)
        sequence_id = get_now_seconds_utc_ms()
        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.BITTREX, sequence_id)

    @classmethod
    def from_binance(cls, json_document, currency, timest):
        """
        "lastUpdateId":1668114,"bids":[["0.40303000","22.00000000",[]],],"asks":[["0.41287000","1.00000000",[]]
        """
        sell_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get('asks', [])]
        buy_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get('bids', [])]
        pair_id = get_currency_pair_from_binance(currency)
        sequence_id = long(json_document['lastUpdateId'])
        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.BINANCE, sequence_id)

    @classmethod
    def from_huobi(cls, json_document, pair_name, timest):
        """
        "tick": {
            "id": 1489464585407,
            "ts": 1489464585407,
            "bids": [
              [7964, 0.0678], // [price, amount]
              [7963, 0.9162],
              [7961, 0.1],
            ],
            "asks": [
              [7979, 0.0736],
              [7980, 1.0292],
            ]

        :param pair_name:
        :param timest:
        :return:
        """
        sell_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get('asks', [])]
        buy_bids = [Deal(price=entry[0], volume=entry[1]) for entry in json_document.get('bids', [])]
        pair_id = get_currency_pair_from_huobi(pair_name)
        sequence_id = long(json_document['version'])
        return OrderBook(pair_id, timest, sell_bids, buy_bids, EXCHANGE.HUOBI, sequence_id)

    @classmethod
    def from_row(cls, db_row, asks_rows, sell_rows):
        currency_pair_id = db_row[1]
        exchange_id = db_row[2]
        timest = db_row[3]
        ask_bids = [Deal(entry[2], entry[3]) for entry in asks_rows]
        sell_bids = [Deal(entry[2], entry[3]) for entry in sell_rows]
        return OrderBook(currency_pair_id, timest, ask_bids, sell_bids, exchange_id)

    def insert_new_bid_preserve_order(self, new_bid, overwrite_volume=True, err_msg=None):
        """
            Bids array are sorted in reversed order i.e. highest - first
            NOTE: consider new value volume as overwrite in case flag overwrite_volume is equal to be True

            Order of condition check is very IMPORTANT!

        """
        item_insert_point = binary_search(self.bid, new_bid, cmp_method_bid)
        is_present = False
        if item_insert_point < len(self.bid):
            is_present = self.bid[item_insert_point] == new_bid
        almost_zero = new_bid.volume <= MIN_VOLUME_ORDER_BOOK
        should_overwrite = is_present and overwrite_volume
        should_update_volume = is_present and (not overwrite_volume)
        update_volume_error = not is_present and (not overwrite_volume)
        should_delete = almost_zero and is_present
        if should_delete:
            del self.bid[item_insert_point]
        elif is_present:
            self.bid[item_insert_point].volume = new_bid.volume
        elif should_overwrite:
            self.bid[item_insert_point].volume = new_bid.volume
        elif should_update_volume:
            self.bid[item_insert_point].volume -= new_bid.volume
            if self.bid[item_insert_point].volume < 0:
                die_hard('Negative value of bid!')
        elif update_volume_error:
            log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
        elif not almost_zero:
            self.bid.insert(item_insert_point, new_bid)

    def insert_new_ask_preserve_order(self, new_ask, overwrite_volume=True, err_msg=None):
        """
            Ask array are sorted in reversed order i.e. lowest - first

            self.ask = sorted(self.ask, key = lambda x: x.price, reverse=False)

            NOTE: consider new value volume as overwrite in case flag overwrite_volume is equal to be True

            Order of condition check is very IMPORTANT!
        """
        item_insert_point = binary_search(self.ask, new_ask, cmp_method_ask)
        is_present = False
        if item_insert_point < len(self.ask):
            is_present = self.ask[item_insert_point] == new_ask
        almost_zero = new_ask.volume <= MIN_VOLUME_ORDER_BOOK
        should_overwrite = is_present and overwrite_volume
        should_update_volume = is_present and (not overwrite_volume)
        update_volume_error = not is_present and (not overwrite_volume)
        should_delete = almost_zero and is_present
        if should_delete:
            del self.ask[item_insert_point]
        elif should_overwrite:
            self.ask[item_insert_point].volume = new_ask.volume
        elif should_update_volume:
            self.ask[item_insert_point].volume -= new_ask.volume
            if self.ask[item_insert_point].volume < 0:
                die_hard('Negative value of ask!')
        elif update_volume_error:
            log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
        elif not almost_zero:
            self.ask.insert(item_insert_point, new_ask)

    def update_for_poloniex(self, order_book_update):
        """
        :param order_book_update:
        Can be two cases:
            1. Initial order book to init
            2. order book update
        :return:
        """
        if type(order_book_update) is OrderBook:
            self._copy_order_book(order_book_update)
            self.sort_by_price()
        else:
            if self.sequence_id >= order_book_update.sequence_id:
                return STATUS.SUCCESS
            if self.sequence_id + 1 != order_book_update.sequence_id:
                log_sequence_id_mismatch('Poloniex', self.sequence_id, order_book_update.sequence_id)
                return STATUS.FAILURE
            self.sequence_id = order_book_update.sequence_id
            for ask in order_book_update.ask:
                self.insert_new_ask_preserve_order(ask)
            for bid in order_book_update.bid:
                self.insert_new_bid_preserve_order(bid)
        return STATUS.SUCCESS

    def _copy_order_book(self, other_order_book):
        self.timest = other_order_book.timest
        self.exchange_id = other_order_book.exchange_id
        self.exchange = other_order_book.exchange_id
        self.pair_id = other_order_book.pair_id
        self.pair_name = other_order_book.pair_id
        self.ask = copy.deepcopy(other_order_book.ask)
        self.bid = copy.deepcopy(other_order_book.bid)
        self.sequence_id = other_order_book.sequence_id

    def update_for_bittrex(self, order_book_update):
        """
        :param order_book_update:
        Can be two cases:
            1. Initial order book to init
            2. order book update
        :return:
        """
        if type(order_book_update) is OrderBook:
            self._copy_order_book(order_book_update)
            self.sort_by_price()
        else:
            if self.sequence_id >= order_book_update.sequence_id:
                return STATUS.SUCCESS
            elif self.sequence_id + 1 != order_book_update.sequence_id:
                log_sequence_id_mismatch('Bittrex', self.sequence_id, order_book_update.sequence_id)
                return STATUS.FAILURE
            self.sequence_id = order_book_update.sequence_id
            for ask in order_book_update.ask:
                self.insert_new_ask_preserve_order(ask)
            for bid in order_book_update.bid:
                self.insert_new_bid_preserve_order(bid)
            for trade_sell in order_book_update.trades_sell:
                err_msg = 'Bittrex socket CANT FIND fill request FILL AND UPDATE - SELL??? {wtf}'.format(wtf=trade_sell)
                self.insert_new_ask_preserve_order(trade_sell, overwrite_volume=False, err_msg=err_msg)
            for trade_buy in order_book_update.trades_buy:
                err_msg = 'Bittrex socket CANT FIND fill request FILL AND UPDATE - BUY??? {wtf}'.format(wtf=trade_buy)
                self.insert_new_bid_preserve_order(trade_buy, overwrite_volume=False, err_msg=err_msg)
        return STATUS.SUCCESS

    def update_for_binance(self, order_book_update):
        """
        For binance sequence_id is a range of number.
        one number for every price level updates.

        "U": 157,           // First update ID in event
        "u": 160,           // Final update ID in event

        During update parsing we are use following logic:

        sequence_id = long(order_book_delta["U"])

        :param order_book_update:
        :return:
        """
        if self.sequence_id >= order_book_update.sequence_id:
            return STATUS.SUCCESS
        if self.sequence_id + 1 != order_book_update.sequence_id:
            log_sequence_id_mismatch('Binance', self.sequence_id, order_book_update.sequence_id)
            return STATUS.FAILURE
        self.sequence_id = order_book_update.sequence_id_end
        for ask in order_book_update.ask:
            self.insert_new_ask_preserve_order(ask)
        for bid in order_book_update.bid:
            self.insert_new_bid_preserve_order(bid)
        return STATUS.SUCCESS

    def update_for_huobi(self, order_book_update):
        """
        NOTE: always get full order book
        :param order_book_update:
        :return:
        """
        self._copy_order_book(order_book_update)
        self.sort_by_price()
        return STATUS.SUCCESS

    def update(self, exchange_id, order_book_delta):
        method = {EXCHANGE.POLONIEX: self.update_for_poloniex, EXCHANGE.BITTREX: self.update_for_bittrex, EXCHANGE.BINANCE: self.update_for_binance, EXCHANGE.HUOBI: self.update_for_huobi}[exchange_id]
        return method(order_book_delta)

def insert_new_bid_preserve_order(self, new_bid, overwrite_volume=True, err_msg=None):
    """
            Bids array are sorted in reversed order i.e. highest - first
            NOTE: consider new value volume as overwrite in case flag overwrite_volume is equal to be True

            Order of condition check is very IMPORTANT!

        """
    item_insert_point = binary_search(self.bid, new_bid, cmp_method_bid)
    is_present = False
    if item_insert_point < len(self.bid):
        is_present = self.bid[item_insert_point] == new_bid
    almost_zero = new_bid.volume <= MIN_VOLUME_ORDER_BOOK
    should_overwrite = is_present and overwrite_volume
    should_update_volume = is_present and (not overwrite_volume)
    update_volume_error = not is_present and (not overwrite_volume)
    should_delete = almost_zero and is_present
    if should_delete:
        del self.bid[item_insert_point]
    elif is_present:
        self.bid[item_insert_point].volume = new_bid.volume
    elif should_overwrite:
        self.bid[item_insert_point].volume = new_bid.volume
    elif should_update_volume:
        self.bid[item_insert_point].volume -= new_bid.volume
        if self.bid[item_insert_point].volume < 0:
            die_hard('Negative value of bid!')
    elif update_volume_error:
        log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
    elif not almost_zero:
        self.bid.insert(item_insert_point, new_bid)

# Node: die_hard
# Node: insert
def insert_new_ask_preserve_order(self, new_ask, overwrite_volume=True, err_msg=None):
    """
            Ask array are sorted in reversed order i.e. lowest - first

            self.ask = sorted(self.ask, key = lambda x: x.price, reverse=False)

            NOTE: consider new value volume as overwrite in case flag overwrite_volume is equal to be True

            Order of condition check is very IMPORTANT!
        """
    item_insert_point = binary_search(self.ask, new_ask, cmp_method_ask)
    is_present = False
    if item_insert_point < len(self.ask):
        is_present = self.ask[item_insert_point] == new_ask
    almost_zero = new_ask.volume <= MIN_VOLUME_ORDER_BOOK
    should_overwrite = is_present and overwrite_volume
    should_update_volume = is_present and (not overwrite_volume)
    update_volume_error = not is_present and (not overwrite_volume)
    should_delete = almost_zero and is_present
    if should_delete:
        del self.ask[item_insert_point]
    elif should_overwrite:
        self.ask[item_insert_point].volume = new_ask.volume
    elif should_update_volume:
        self.ask[item_insert_point].volume -= new_ask.volume
        if self.ask[item_insert_point].volume < 0:
            die_hard('Negative value of ask!')
    elif update_volume_error:
        log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
    elif not almost_zero:
        self.ask.insert(item_insert_point, new_ask)

# Node: type
def log_trace_log_time_key(time_key):
    msg = 'process_expired_orders - for time key - {tk}'.format(tk=str(time_key))
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_trace_log_all_cached_orders_for_time_key(list_of_orders, ts):
    log_to_file('For key {ts} in cached orders - {num} orders'.format(ts=ts, num=len(list_of_orders[ts])), 'expire_deal.log')
    for order in list_of_orders[ts]:
        log_to_file(str(order), EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_trace_processing_oder(some_order):
    msg = 'Check order from watch list - {pair}'.format(pair=str(some_order))
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_trace_cancel_request_result(order, err_code, responce):
    msg = 'We have tried to send cancel request for order - {dd} and raw result is {er_code} {js}'.format(dd=str(order), er_code=str(err_code), js=responce)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_trace_warched_orders_after_processing(order_list):
    for time_key in order_list:
        msg = 'For ts = {ts} cached orders are:'.format(ts=str(time_key))
        log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)
        for expired_order in order_list[time_key]:
            log_to_file(str(expired_order), EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_error_on_receive_from_socket(exch_name, e):
    msg = '{exch_name} - triggered exception during reading from socket = {e}. Reseting stage!'.format(exch_name=exch_name, e=str(e))
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_websocket_disconnect(exch_name, e):
    msg = '{exch_name} - triggered exception during closing socket = {e} at disconnect!'.format(exch_name=exch_name, e=str(e))
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_send_heart_beat_failed(exch_name, e):
    msg = '{exch_name}: connection terminated with error: {er}'.format(exch_name=exch_name, er=str(e))
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_initial_settings(msg, exchanges_ids):
    for exchange_id in exchanges_ids:
        msg += str(exchange_id) + ' - ' + get_exchange_name_by_id(exchange_id) + '\n'
    print_to_console(msg, LOG_ALL_ERRORS)
    log_to_file(msg, 'balance.log')

def send_single_message_no_parsing(some_message, notification_type):
    chat_id = get_chat_id_by_type(notification_type)
    res = STATUS.FAILURE
    try:
        BOT.send_message(chat_id=chat_id, text=str(some_message), timeout=5, parse_mode=None)
        res = STATUS.SUCCESS
    except Exception as e:
        log_error_send_message('send_single_message_no_parsing', some_message, e)
    return res

# Node: get_chat_id_by_type
# Node: send_message
# Node: log_error_send_message
def send_single_message(some_message, notification_type):
    if len(some_message) > MAX_MESSAGE_LENGTH:
        some_message = some_message[:MAX_MESSAGE_LENGTH] + '... etc'
    chat_id = get_chat_id_by_type(notification_type)
    try:
        BOT.send_message(chat_id=chat_id, text=str(some_message), timeout=5, parse_mode=telegram.ParseMode.HTML)
        res = STATUS.SUCCESS
    except Exception as e:
        log_error_send_message('send_single_message', some_message, e)
        res = send_single_message_no_parsing(some_message, notification_type)
    return res

# Node: send_single_message_no_parsing
# Node: get_tickers_poloniex
# Node: get_tickers_binance
def get_tickers():
    all_tickers = {}
    timest = get_now_seconds_utc()
    bittrex_tickers = {}
    for pair_name in BITTREX_CURRENCY_PAIRS:
        ticker = get_ticker_bittrex(pair_name, timest)
        if ticker is not None:
            bittrex_tickers[ticker.pair_id] = ticker
    all_tickers[EXCHANGE.BITTREX] = bittrex_tickers
    kraken_tickers = {}
    for pair_name in KRAKEN_CURRENCY_PAIRS:
        ticker = get_ticker_kraken(pair_name, timest)
        if ticker is not None:
            kraken_tickers[ticker.pair_id] = ticker
    all_tickers[EXCHANGE.KRAKEN] = kraken_tickers
    huobi_tickers = {}
    for pair_name in HUOBI_CURRENCY_PAIRS:
        ticker = get_ticker_huobi(pair_name, timest)
        if ticker is not None:
            huobi_tickers[ticker.pair_id] = ticker
    all_tickers[EXCHANGE.HUOBI] = huobi_tickers
    poloniex_tickers = get_tickers_poloniex(POLONIEX_CURRENCY_PAIRS, timest)
    all_tickers[EXCHANGE.POLONIEX] = poloniex_tickers
    binance_tickers = get_tickers_binance(BINANCE_CURRENCY_PAIRS, timest)
    all_tickers[EXCHANGE.BINANCE] = binance_tickers
    return all_tickers

# Node: get_ticker_bittrex
# Node: get_ticker_kraken
# Node: get_ticker_huobi
def get_ohlc(date_start, date_end):
    all_ohlc = []
    for pair_name in BITTREX_CURRENCY_PAIRS:
        period = 'thirtyMin'
        all_ohlc += get_ohlc_bittrex(pair_name, date_start, date_end, period)
        sleep_for(1)
    for pair_name in KRAKEN_CURRENCY_PAIRS:
        period = 15
        all_ohlc += get_ohlc_kraken(pair_name, date_start, date_end, period)
    for pair_name in POLONIEX_CURRENCY_PAIRS:
        period = 14400
        all_ohlc += get_ohlc_poloniex(pair_name, date_start, date_end, period)
    for pair_name in BINANCE_CURRENCY_PAIRS:
        period = '15m'
        all_ohlc += get_ohlc_binance(pair_name, date_start, date_end, period)
    for pair_name in HUOBI_CURRENCY_PAIRS:
        period = '15min'
        all_ohlc += get_ohlc_huobi(pair_name, date_start, date_end, period)
    return all_ohlc

# Node: get_ohlc_bittrex
# Node: get_ohlc_kraken
# Node: get_ohlc_poloniex
# Node: get_ohlc_binance
# Node: get_ohlc_huobi
def get_history(prev_time, now_time):
    all_history = []
    for currency in POLONIEX_CURRENCY_PAIRS:
        all_history += get_history_poloniex(currency, prev_time, now_time)
    for currency in KRAKEN_CURRENCY_PAIRS:
        all_history += get_history_kraken(currency, prev_time, now_time)
    for currency in BITTREX_CURRENCY_PAIRS:
        all_history += get_history_bittrex(currency, prev_time, now_time)
    for currency in BINANCE_CURRENCY_PAIRS:
        all_history += get_history_binance(currency, prev_time, now_time)
    for currency in HUOBI_CURRENCY_PAIRS:
        all_history += get_history_huobi(currency, prev_time, now_time)
    return all_history

# Node: get_history_poloniex
# Node: get_history_kraken
# Node: get_history_bittrex
# Node: get_history_binance
# Node: get_history_huobi
def init_body(key):
    return [('AccessKeyId', key.api_key), ('SignatureMethod', 'HmacSHA256'), ('SignatureVersion', 2), ('Timestamp', ts_to_string_utc(get_now_seconds_utc(), '%Y-%m-%dT%H:%M:%S'))]

def get_orders_kraken(key):
    timest = get_now_seconds_utc()
    error_code_1, open_orders = get_open_orders_kraken(key)
    error_code_2, closed_orders = get_order_history_kraken(key)
    if error_code_1 == STATUS.FAILURE or error_code_2 == STATUS.FAILURE:
        return (STATUS.FAILURE, None)
    return (STATUS.SUCCESS, OrderState(EXCHANGE.KRAKEN, timest, open_orders, closed_orders))

# Node: get_open_orders_kraken
# Node: get_order_history_kraken
# Node: OrderState
class ArbitrageListener(ArbitrageWrapper):

    def __init__(self, cfg, app_settings):
        ArbitrageWrapper.__init__(self, cfg)
        self._init_infrastructure(app_settings)

    def start(self):
        self.reset_arbitrage_state()
        while True:
            if self.buy_subscription.is_running() and self.sell_subscription.is_running():
                sleep_for(1)
            else:
                while self.buy_subscription.is_running() or self.sell_subscription.is_running():
                    sleep_for(1)
                self.reset_arbitrage_state()

    def reset_arbitrage_state(self):
        local_timeout = 1
        while True:
            sleep_for(local_timeout)
            log_init_reset()
            set_stage(ORDER_BOOK_SYNC_STAGES.RESETTING)
            self.update_balance_run_flag = False
            self.update_min_cap_run_flag = False
            clear_queue(self.sell_exchange_updates)
            clear_queue(self.buy_exchange_updates)
            self._init_arbitrage_state()
            self.subscribe_to_order_book_update()
            self.sync_order_books()
            log_reset_final_stage()
            if get_stage() != ORDER_BOOK_SYNC_STAGES.AFTER_SYNC:
                self.shutdown_subscriptions()
                log_to_file('reset_arbitrage_state - cant sync order book, lets try one more time!', SOCKET_ERRORS_LOG_FILE_NAME)
                while self.buy_subscription.is_running() or self.sell_subscription.is_running():
                    sleep_for(1)
                local_timeout += 1
            else:
                break
        log_reset_stage_successfully()

    def _init_infrastructure(self, app_settings):
        self.priority_queue, self.msg_queue, self.local_cache = init_queues(app_settings)
        self.processor = ConnectionPool(pool_size=2)
        self.sell_exchange_updates = Queue()
        self.buy_exchange_updates = Queue()
        buy_subscription_constructor = get_subcribtion_by_exchange(self.buy_exchange_id)
        sell_subscription_constructor = get_subcribtion_by_exchange(self.sell_exchange_id)
        self.buy_subscription = buy_subscription_constructor(self.pair_id, on_update=self.on_order_book_update)
        self.sell_subscription = sell_subscription_constructor(self.pair_id, on_update=self.on_order_book_update)

    def _init_arbitrage_state(self):
        self.init_deal_cap()
        self.init_balance_state()
        self.init_order_books()
        self.sell_order_book_synced = False
        self.buy_order_book_synced = False
        set_stage(ORDER_BOOK_SYNC_STAGES.BEFORE_SYNC)

    def init_deal_cap(self):
        self.update_min_cap_run_flag = True

    def update_min_cap(self):
        log_to_file('Subscribing for updating cap updates', SOCKET_ERRORS_LOG_FILE_NAME)
        while self.update_min_cap_run_flag:
            update_min_cap(self.cfg, self.deal_cap, self.processor)
            for _ in xrange(self.cap_update_timeout):
                if self.update_min_cap_run_flag:
                    sleep_for(1)
        log_to_file('Exit from updating cap updates', SOCKET_ERRORS_LOG_FILE_NAME)

    def init_balance_state(self):
        self.update_balance_run_flag = True

    def init_order_books(self):
        cur_timest_sec = get_now_seconds_utc()
        self.order_book_sell = OrderBook(self.pair_id, cur_timest_sec, sell_bids=[], buy_bids=[], exchange_id=self.sell_exchange_id)
        self.order_book_buy = OrderBook(self.pair_id, cur_timest_sec, sell_bids=[], buy_bids=[], exchange_id=self.buy_exchange_id)

    def update_from_queue(self, exchange_id, order_book, queue):
        while True:
            if not self.buy_subscription.is_running() or not self.sell_subscription.is_running():
                return STATUS.FAILURE
            try:
                order_book_update = queue.get(block=False)
            except:
                order_book_update = None
            if order_book_update is None:
                break
            if STATUS.SUCCESS != order_book.update(exchange_id, order_book_update):
                return STATUS.FAILURE
            queue.task_done()
        return STATUS.SUCCESS

    def sync_sell_order_book(self):
        if self.sell_exchange_id in [EXCHANGE.BINANCE, EXCHANGE.BITTREX]:
            self.order_book_sell = get_order_book(self.sell_exchange_id, self.pair_id)
            if self.order_book_sell is None:
                return
            self.order_book_sell.sort_by_price()
            if STATUS.FAILURE == self.update_from_queue(self.sell_exchange_id, self.order_book_sell, self.sell_exchange_updates):
                self.sell_order_book_synced = False
                return
        log_finishing_syncing_order_book('SELL')
        self.sell_order_book_synced = True

    def sync_buy_order_book(self):
        if self.buy_exchange_id in [EXCHANGE.BINANCE, EXCHANGE.BITTREX]:
            self.order_book_buy = get_order_book(self.buy_exchange_id, self.pair_id)
            if self.order_book_buy is None:
                return
            self.order_book_buy.sort_by_price()
            if STATUS.FAILURE == self.update_from_queue(self.buy_exchange_id, self.order_book_buy, self.buy_exchange_updates):
                self.buy_order_book_synced = False
                return
        log_finishing_syncing_order_book('BUY')
        self.buy_order_book_synced = True

    def sync_order_books(self):
        msg = 'sync_order_books - stage status is {}'.format(get_stage())
        log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
        sync_sell_order_book_thread = start_process_daemon(self.sync_sell_order_book, args=())
        sync_buy_order_book_thread = start_process_daemon(self.sync_buy_order_book, args=())
        sync_sell_order_book_thread.join()
        sync_buy_order_book_thread.join()
        if self.sell_order_book_synced and self.buy_order_book_synced:
            set_stage(ORDER_BOOK_SYNC_STAGES.AFTER_SYNC)
        log_all_order_book_synced()

    def subscribe_cap_update(self):
        start_process_daemon(self.update_min_cap, args=())

    def update_balance(self):
        while self.update_balance_run_flag:
            cur_timest_sec = get_now_seconds_utc()
            self.balance_state = get_updated_balance_arbitrage(cfg, self.balance_state, self.local_cache)
            if self.balance_state.expired(cur_timest_sec, self.buy_exchange_id, self.sell_exchange_id, BALANCE_EXPIRED_THRESHOLD):
                log_balance_expired_errors(cfg, self.msg_queue, self.balance_state)
                assert False
            sleep_for(self.balance_update_timeout)

    def subscribe_balance_update(self):
        start_process_daemon(self.update_balance, args=())

    def subscribe_to_order_book_update(self):
        start_process_daemon(self.buy_subscription.subscribe, args=())
        start_process_daemon(self.sell_subscription.subscribe, args=())

    def shutdown_subscriptions(self):
        self.sell_subscription.disconnect()
        self.buy_subscription.disconnect()

    def on_order_book_update(self, exchange_id, order_book_updates):
        """
        :param exchange_id:
        :param order_book_updates:  parsed OrderBook or OrderBookUpdates according to exchange specs
        :param stage:               whether BOTH orderbook synced or NOT
        :return:
        """
        exchange_name = get_exchange_name_by_id(exchange_id)
        print_to_console('Got update for {exch} Current number of threads: {thr_num}'.format(exch=exchange_name, thr_num=threading.active_count()), LOG_ALL_ERRORS)
        current_stage = get_stage()
        if not self.buy_subscription.is_running() or not self.sell_subscription.is_running():
            log_one_of_subscriptions_failed(self.buy_subscription.is_running(), self.sell_subscription.is_running(), current_stage)
            self.shutdown_subscriptions()
            return
        if order_book_updates is None:
            print_to_console('Order book update is NONE! for {}'.format(exchange_name), LOG_ALL_ERRORS)
            return
        if current_stage == ORDER_BOOK_SYNC_STAGES.BEFORE_SYNC:
            print_to_console('Syncing in progress ...', LOG_ALL_ERRORS)
            if exchange_id == self.buy_exchange_id:
                if self.buy_order_book_synced:
                    order_book_update_status = self.order_book_buy.update(exchange_id, order_book_updates)
                    if order_book_update_status == STATUS.FAILURE:
                        log_order_book_update_failed_pre_sync('BUY', exchange_id, order_book_updates)
                        self.shutdown_subscriptions()
                else:
                    self.buy_exchange_updates.put(order_book_updates)
            elif self.sell_order_book_synced:
                order_book_update_status = self.order_book_sell.update(exchange_id, order_book_updates)
                if order_book_update_status == STATUS.FAILURE:
                    log_order_book_update_failed_pre_sync('SELL', exchange_id, order_book_updates)
                    self.shutdown_subscriptions()
            else:
                self.sell_exchange_updates.put(order_book_updates)
        elif current_stage == ORDER_BOOK_SYNC_STAGES.AFTER_SYNC:
            print_to_console('Update after syncing... {}'.format(exchange_name), LOG_ALL_ERRORS)
            if exchange_id == self.buy_exchange_id:
                order_book_update_status = self.order_book_buy.update(exchange_id, order_book_updates)
                if order_book_update_status == STATUS.FAILURE:
                    log_order_book_update_failed_post_sync(exchange_id, order_book_updates)
                    self.shutdown_subscriptions()
                    return
            else:
                order_book_update_status = self.order_book_sell.update(exchange_id, order_book_updates)
                if order_book_update_status == STATUS.FAILURE:
                    log_order_book_update_failed_post_sync(exchange_id, order_book_updates)
                    self.shutdown_subscriptions()
                    return
            print_top10(exchange_id, self.order_book_buy, self.order_book_sell)
            if not YES_I_KNOW_WHAT_AM_I_DOING:
                die_hard('LIVE TRADING!')
                ts1 = get_now_seconds_utc_ms()
                status_code, deal_pair = search_for_arbitrage(self.order_book_sell, self.order_book_buy, self.threshold, self.balance_threshold, init_deals_with_logging_speedy, self.balance_state, self.deal_cap, type_of_deal=DEAL_TYPE.ARBITRAGE, worker_pool=self.processor, msg_queue=self.msg_queue)
                ts2 = get_now_seconds_utc_ms()
                msg = 'Start: {ts1} ms End: {ts2} ms Runtime: {d} ms'.format(ts1=ts1, ts2=ts2, d=ts2 - ts1)
                log_to_file(msg, 'profile.txt')
                add_orders_to_watch_list(deal_pair, self.priority_queue)
            self.deal_cap.update_max_volume_cap(NO_MAX_CAP_LIMIT)

def _init_infrastructure(self, app_settings):
    self.priority_queue, self.msg_queue, self.local_cache = init_queues(app_settings)
    self.processor = ConnectionPool(pool_size=2)
    self.sell_exchange_updates = Queue()
    self.buy_exchange_updates = Queue()
    buy_subscription_constructor = get_subcribtion_by_exchange(self.buy_exchange_id)
    sell_subscription_constructor = get_subcribtion_by_exchange(self.sell_exchange_id)
    self.buy_subscription = buy_subscription_constructor(self.pair_id, on_update=self.on_order_book_update)
    self.sell_subscription = sell_subscription_constructor(self.pair_id, on_update=self.on_order_book_update)

# Node: ConnectionPool
# Node: Queue
# Node: get_subcribtion_by_exchange
# Node: buy_subscription_constructor
# Node: sell_subscription_constructor
def init_order_books(self):
    cur_timest_sec = get_now_seconds_utc()
    self.order_book_sell = OrderBook(self.pair_id, cur_timest_sec, sell_bids=[], buy_bids=[], exchange_id=self.sell_exchange_id)
    self.order_book_buy = OrderBook(self.pair_id, cur_timest_sec, sell_bids=[], buy_bids=[], exchange_id=self.buy_exchange_id)

def load_order_books(args):
    """
        Periodically retrieve FULL order books
        from ALL supported exchanges via REST api
        and save it for further analysis in DB.

        Under the hood requests are sent in async fashion via gevent library

    :param args: config file
    :return:
    """
    pg_conn, _ = process_args(args)
    processor = ConnectionPool()
    while True:
        ts = get_now_seconds_utc()
        results = get_order_book_speedup(ts, processor)
        order_book = filter(lambda x: type(x) != str, results)
        load_to_postgres(order_book, ORDER_BOOK_TYPE_NAME, pg_conn)
        order_book_size = len(order_book)
        order_book_ask_size = 0
        order_book_bid_size = 0
        for entry in order_book:
            if entry is not None:
                order_book_ask_size += len(entry.ask)
                order_book_bid_size += len(entry.bid)
        if should_print_debug():
            msg = 'Orderbook retrieval at {tt}:\n            Order book size - {num1} Order book asks - {num10} Order book bids - {num20}'.format(tt=ts, num1=order_book_size, num10=order_book_ask_size, num20=order_book_bid_size)
            print_to_console(msg, LOG_ALL_ERRORS)
            log_to_file(msg, 'order_book.log')
        print_to_console('Before sleep...', LOG_ALL_ERRORS)
        sleep_for(ORDER_BOOK_POLL_TIMEOUT)

# Node: get_order_book_speedup
# Node: filter
# Node: load_to_postgres
def load_all_public_data(args):
    """
                06.08.2019 As far as I remember it is NOT main data retrieval routine

                Retrieve ticker, trade history, candles and order book
                from ALL supported exchanges
                and store it within DB
                every TIMEOUT seconds through REST api.

                Majority of exchanges tend to throttle clients who send too many requests
                from the same ip - so be mindful about timeout.

    :param args:
    :return:
    """
    pg_conn, settings = process_args(args)
    processor = ConnectionPool()

    def split_on_errors(raw_response):
        valid_objects = filter(lambda x: type(x) != str, raw_response)
        error_strings = filter(lambda x: type(x) != str, raw_response)
        return (valid_objects, error_strings)
    while True:
        end_time = get_now_seconds_utc()
        start_time = end_time - POLL_PERIOD_SECONDS
        candles, errs = split_on_errors(get_ohlc_speedup(start_time, end_time, processor))
        bulk_insert_to_postgres(pg_conn, Candle.table_name, Candle.columns, candles)
        trade_history, errs = split_on_errors(get_history_speedup(start_time, end_time, processor))
        bulk_insert_to_postgres(pg_conn, TradeHistory.table_name, TradeHistory.columns, trade_history)
        tickers, errs = split_on_errors(get_ticker_speedup(end_time, processor))
        bulk_insert_to_postgres(pg_conn, Ticker.table_name, Ticker.columns, tickers)
        if should_print_debug():
            msg = 'History retrieval at {ts}:\n                Candle size - {num}\n                Ticker size - {num3}\n                Trade history size - {num2}\n                '.format(ts=end_time, num=len(candles), num3=len(tickers), num2=len(trade_history))
            print_to_console(msg, LOG_ALL_ERRORS)
            log_to_file(msg, 'candles_trade_history.log')
        print_to_console('Before sleep...', LOG_ALL_ERRORS)
        sleep_for(POLL_PERIOD_SECONDS)

# Node: split_on_errors
# Node: get_ohlc_speedup
# Node: bulk_insert_to_postgres
# Node: get_history_speedup
# Node: get_ticker_speedup
def split_on_errors(raw_response):
    valid_objects = filter(lambda x: type(x) != str, raw_response)
    error_strings = filter(lambda x: type(x) != str, raw_response)
    return (valid_objects, error_strings)

def analyse_tickers(pg_connection, notify_queue):
    """
            Retrieve tickers from ALL exchanges via REST api and save into DB.

            NOTE: Very first routine to analyse gap between rates at different exchanges.

    :param pg_connection:
    :param notify_queue:
    :return:
    """
    processor = ConnectionPool()
    while True:
        timest = get_now_seconds_utc()
        results = get_ticker_speedup(timest, processor)
        tickers = filter(lambda x: type(x) != str, results)
        res = compare_price(tickers, TRIGGER_THRESHOLD, check_highest_bid_bigger_than_lowest_ask)
        for entry in res:
            msg = 'Condition: {msg} at {ts}\n            Date: {dt}\n            Pair: {pair_name}, {ask_exchange}: {ask_price:.7f} {sell_exchange}: {sell_price:.7f}\n            TAG: {ask_exchange}-{sell_exchange}\n            '.format(msg=entry[0], ts=timest, dt=ts_to_string_local(timest), pair_name=get_pair_name_by_id(entry[1]), ask_exchange=entry[2].exchange, ask_price=entry[2].bid, sell_exchange=entry[3].exchange, sell_price=entry[3].ask)
            print_to_console(msg, LOG_ALL_ERRORS)
            notify_queue.add_message(ARBITRAGE_MSG, msg)
            save_alarm_into_pg(entry[2], entry[3], pg_connection)
        print_to_console('Total amount of tickers = {num}'.format(num=len(tickers)), LOG_ALL_DEBUG)
        load_to_postgres(tickers, TICKER_TYPE_NAME, pg_connection)
        print_to_console('Before sleep...', LOG_ALL_DEBUG)
        sleep_for(POLL_PERIOD_SECONDS)

# Node: compare_price
# Node: save_alarm_into_pg
class PoloniexPrivateApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        load_key_by_exchange(API_KEY_PATH, EXCHANGE.POLONIEX)
        self.poloniex_key = get_key_by_exchange(EXCHANGE.POLONIEX)

    def test_balance_retrieval(self):
        status, balance = get_balance_poloniex(self.poloniex_key)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(type(balance), Balance)

    def test_order_cancel(self):
        status, response = cancel_order_poloniex(self.poloniex_key, '00000000-0000-0000-0000-000000000000')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid orderNumber parameter' in str(response))

    def test_buy_order(self):
        status, response = add_buy_order_poloniex(self.poloniex_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid currencyPair parameter' in str(response))

    def test_sell_order(self):
        status, response = add_sell_order_poloniex(self.poloniex_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid currencyPair parameter' in str(response))

    def test_open_orders_retrieval(self):
        status, orders = get_open_orders_poloniex(self.poloniex_key, pair_name='NULL')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertEquals(len(orders), 0)

    def test_order_history_retrieval(self):
        status, orders = get_order_history_poloniex(self.poloniex_key, pair_name='NULL')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertEquals(len(orders), 0)

def test_balance_retrieval(self):
    status, balance = get_balance_poloniex(self.poloniex_key)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(type(balance), Balance)

# Node: get_balance_poloniex
# Node: assertEquals
def test_order_cancel(self):
    status, response = cancel_order_poloniex(self.poloniex_key, '00000000-0000-0000-0000-000000000000')
    self.assertEquals(STATUS.FAILURE, status)
    self.assertTrue('Invalid orderNumber parameter' in str(response))

# Node: cancel_order_poloniex
# Node: assertTrue
def test_buy_order(self):
    status, response = add_buy_order_poloniex(self.poloniex_key, pair_name='NULL', price=0.0, amount=0.0)
    self.assertEquals(STATUS.FAILURE, status)
    self.assertTrue('Invalid currencyPair parameter' in str(response))

# Node: add_buy_order_poloniex
def test_sell_order(self):
    status, response = add_sell_order_poloniex(self.poloniex_key, pair_name='NULL', price=0.0, amount=0.0)
    self.assertEquals(STATUS.FAILURE, status)
    self.assertTrue('Invalid currencyPair parameter' in str(response))

# Node: add_sell_order_poloniex
def test_open_orders_retrieval(self):
    status, orders = get_open_orders_poloniex(self.poloniex_key, pair_name='NULL')
    self.assertEquals(STATUS.FAILURE, status)
    self.assertEquals(len(orders), 0)

# Node: get_open_orders_poloniex
def test_order_history_retrieval(self):
    status, orders = get_order_history_poloniex(self.poloniex_key, pair_name='NULL')
    self.assertEquals(STATUS.FAILURE, status)
    self.assertEquals(len(orders), 0)

# Node: get_order_history_poloniex
class KrakenPrivateApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        load_key_by_exchange(API_KEY_PATH, EXCHANGE.KRAKEN)
        self.kraken_key = get_key_by_exchange(EXCHANGE.KRAKEN)

    def test_balance_retrieval(self):
        status, balance = get_balance_kraken(self.kraken_key)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(type(balance), Balance)

    def test_order_cancel(self):
        status, response = cancel_order_kraken(self.kraken_key, '00000000-0000-0000-0000-000000000000')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue("Invalid order'" in str(response))

    def test_buy_order(self):
        status, response = add_buy_order_kraken(self.kraken_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('Unknown asset pair' in str(response))

    def test_sell_order(self):
        status, response = add_sell_order_kraken(self.kraken_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('Unknown asset pair' in str(response))

    def test_open_orders_retrieval(self):
        status, orders = get_open_orders_kraken(self.kraken_key, pair_name='NULL')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

    def test_order_history_retrieval(self):
        status, orders = get_order_history_kraken(self.kraken_key, pair_name='NULL')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

def test_balance_retrieval(self):
    status, balance = get_balance_kraken(self.kraken_key)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(type(balance), Balance)

# Node: get_balance_kraken
def test_order_cancel(self):
    status, response = cancel_order_kraken(self.kraken_key, '00000000-0000-0000-0000-000000000000')
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertTrue("Invalid order'" in str(response))

# Node: cancel_order_kraken
def test_buy_order(self):
    status, response = add_buy_order_kraken(self.kraken_key, pair_name='NULL', price=0.0, amount=0.0)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertTrue('Unknown asset pair' in str(response))

# Node: add_buy_order_kraken
def test_sell_order(self):
    status, response = add_sell_order_kraken(self.kraken_key, pair_name='NULL', price=0.0, amount=0.0)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertTrue('Unknown asset pair' in str(response))

# Node: add_sell_order_kraken
def test_open_orders_retrieval(self):
    status, orders = get_open_orders_kraken(self.kraken_key, pair_name='NULL')
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(len(orders), 0)

def test_order_history_retrieval(self):
    status, orders = get_order_history_kraken(self.kraken_key, pair_name='NULL')
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(len(orders), 0)

class BittrexPrivateApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        load_key_by_exchange(API_KEY_PATH, EXCHANGE.BITTREX)
        self.bittrex_key = get_key_by_exchange(EXCHANGE.BITTREX)

    def test_balance_retrieval(self):
        status, balance = get_balance_bittrex(self.bittrex_key)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(type(balance), Balance)

    def test_order_cancel(self):
        status, response = cancel_order_bittrex(self.bittrex_key, '00000000-0000-0000-0000-000000000000')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('INVALID_ORDER' in str(response))

    def test_buy_order(self):
        status, response = add_buy_order_bittrex(self.bittrex_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('INVALID_MARKET' in str(response))

    def test_sell_order(self):
        status, response = add_sell_order_bittrex(self.bittrex_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('INVALID_MARKET' in str(response))

    def test_open_orders_retrieval(self):
        status, orders = get_open_orders_bittrix(self.bittrex_key, pair_name='NULL')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

    def test_order_history_retrieval(self):
        status, orders = get_order_history_bittrex(self.bittrex_key, pair_name='NULL')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

def test_balance_retrieval(self):
    status, balance = get_balance_bittrex(self.bittrex_key)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(type(balance), Balance)

# Node: get_balance_bittrex
def test_order_cancel(self):
    status, response = cancel_order_bittrex(self.bittrex_key, '00000000-0000-0000-0000-000000000000')
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertTrue('INVALID_ORDER' in str(response))

# Node: cancel_order_bittrex
def test_buy_order(self):
    status, response = add_buy_order_bittrex(self.bittrex_key, pair_name='NULL', price=0.0, amount=0.0)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertTrue('INVALID_MARKET' in str(response))

# Node: add_buy_order_bittrex
def test_sell_order(self):
    status, response = add_sell_order_bittrex(self.bittrex_key, pair_name='NULL', price=0.0, amount=0.0)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertTrue('INVALID_MARKET' in str(response))

# Node: add_sell_order_bittrex
def test_open_orders_retrieval(self):
    status, orders = get_open_orders_bittrix(self.bittrex_key, pair_name='NULL')
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(len(orders), 0)

# Node: get_open_orders_bittrix
def test_order_history_retrieval(self):
    status, orders = get_order_history_bittrex(self.bittrex_key, pair_name='NULL')
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(len(orders), 0)

# Node: get_order_history_bittrex
class HuobiPrivateApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        load_key_by_exchange(API_KEY_PATH, EXCHANGE.HUOBI)
        self.huobi_key = get_key_by_exchange(EXCHANGE.HUOBI)

    def test_balance_retrieval(self):
        status, balance = get_balance_huobi(self.huobi_key)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(type(balance), Balance)

    def test_order_cancel(self):
        status, response = cancel_order_huobi(self.huobi_key, '00000000-0000-0000-0000-000000000000')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('invalid-order-id' in str(response))

    def test_buy_order(self):
        status, response = add_buy_order_huobi(self.huobi_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('invalid-amount' in str(response) or 'invalid-symbol' in str(response))

    def test_sell_order(self):
        status, response = add_sell_order_huobi(self.huobi_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertTrue('invalid-amount' in str(response) or 'invalid-symbol' in str(response))

    def test_open_orders_retrieval(self):
        status, orders = get_open_orders_huobi(self.huobi_key, pair_name='dashbtc')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

    def test_order_history_retrieval(self):
        status, orders = get_order_history_huobi(self.huobi_key, pair_name='dashbtc')
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(len(orders), 0)

def test_balance_retrieval(self):
    status, balance = get_balance_huobi(self.huobi_key)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(type(balance), Balance)

# Node: get_balance_huobi
def test_order_cancel(self):
    status, response = cancel_order_huobi(self.huobi_key, '00000000-0000-0000-0000-000000000000')
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertTrue('invalid-order-id' in str(response))

# Node: cancel_order_huobi
def test_buy_order(self):
    status, response = add_buy_order_huobi(self.huobi_key, pair_name='NULL', price=0.0, amount=0.0)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertTrue('invalid-amount' in str(response) or 'invalid-symbol' in str(response))

# Node: add_buy_order_huobi
def test_sell_order(self):
    status, response = add_sell_order_huobi(self.huobi_key, pair_name='NULL', price=0.0, amount=0.0)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertTrue('invalid-amount' in str(response) or 'invalid-symbol' in str(response))

# Node: add_sell_order_huobi
def test_open_orders_retrieval(self):
    status, orders = get_open_orders_huobi(self.huobi_key, pair_name='dashbtc')
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(len(orders), 0)

# Node: get_open_orders_huobi
def test_order_history_retrieval(self):
    status, orders = get_order_history_huobi(self.huobi_key, pair_name='dashbtc')
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(len(orders), 0)

# Node: get_order_history_huobi
class BinancePrivateApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        load_key_by_exchange(API_KEY_PATH, EXCHANGE.BINANCE)
        self.binance_key = get_key_by_exchange(EXCHANGE.BINANCE)

    def test_balance_retrieval(self):
        status, balance = get_balance_binance(self.binance_key)
        self.assertEquals(STATUS.SUCCESS, status)
        self.assertEquals(type(balance), Balance)

    def test_order_cancel(self):
        status, response = cancel_order_binance(self.binance_key, pair_name='NULL', order_id='1234567890')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid symbol' in str(response))

    def test_buy_order(self):
        status, response = add_buy_order_binance(self.binance_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid symbol' in str(response))

    def test_sell_order(self):
        status, response = add_sell_order_binance(self.binance_key, pair_name='NULL', price=0.0, amount=0.0)
        self.assertEquals(STATUS.FAILURE, status)
        self.assertTrue('Invalid symbol' in str(response))

    def test_open_orders_retrieval(self):
        status, orders = get_open_orders_binance(self.binance_key, pair_name='NULL')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertEquals(len(orders), 0)

    def test_order_history_retrieval(self):
        status, orders = get_order_history_binance(self.binance_key, pair_name='NULL')
        self.assertEquals(STATUS.FAILURE, status)
        self.assertEquals(len(orders), 0)

def test_balance_retrieval(self):
    status, balance = get_balance_binance(self.binance_key)
    self.assertEquals(STATUS.SUCCESS, status)
    self.assertEquals(type(balance), Balance)

# Node: get_balance_binance
def test_order_cancel(self):
    status, response = cancel_order_binance(self.binance_key, pair_name='NULL', order_id='1234567890')
    self.assertEquals(STATUS.FAILURE, status)
    self.assertTrue('Invalid symbol' in str(response))

def test_buy_order(self):
    status, response = add_buy_order_binance(self.binance_key, pair_name='NULL', price=0.0, amount=0.0)
    self.assertEquals(STATUS.FAILURE, status)
    self.assertTrue('Invalid symbol' in str(response))

# Node: add_buy_order_binance
def test_sell_order(self):
    status, response = add_sell_order_binance(self.binance_key, pair_name='NULL', price=0.0, amount=0.0)
    self.assertEquals(STATUS.FAILURE, status)
    self.assertTrue('Invalid symbol' in str(response))

# Node: add_sell_order_binance
def test_open_orders_retrieval(self):
    status, orders = get_open_orders_binance(self.binance_key, pair_name='NULL')
    self.assertEquals(STATUS.FAILURE, status)
    self.assertEquals(len(orders), 0)

# Node: get_open_orders_binance
def test_order_history_retrieval(self):
    status, orders = get_order_history_binance(self.binance_key, pair_name='NULL')
    self.assertEquals(STATUS.FAILURE, status)
    self.assertEquals(len(orders), 0)

# Node: get_order_history_binance
class BinarySearchTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)
        self.first = Deal(0.03172795, 0.1)
        self.non_present = Deal(10.1, 0.1)
        self.deal_update = Deal(0.03172801, 0.4)
        unsorted = [self.first, Deal(0.03172796, 0.2), Deal(0.03172798, 0.3), self.deal_update, Deal(0.03173, 0.5)]
        self.asks = sorted(unsorted, key=lambda x: x.price, reverse=False)
        self.bids = sorted(unsorted, key=lambda x: x.price, reverse=True)

    def test_bin_search_asks(self):
        item_insert_point = binary_search(self.asks, self.first, cmp_method_ask)
        self.assertEquals(item_insert_point, 0)

    def test_bin_search_asks_not_present(self):
        item_insert_point = binary_search(self.asks, self.non_present, cmp_method_ask)
        self.assertEquals(item_insert_point, len(self.asks))

    def test_bin_search_asks_update_present(self):
        idx = binary_search(self.asks, self.deal_update, cmp_method_ask)
        is_present = False
        if idx < len(self.asks):
            is_present = self.asks[idx] == self.deal_update
        self.assertTrue(is_present)

    def test_bin_search_bids(self):
        item_insert_point = binary_search(self.bids, self.first, cmp_method_bid)
        self.assertEquals(item_insert_point, -1 + len(self.bids))

    def test_bin_search_bids_not_present(self):
        item_insert_point = binary_search(self.bids, self.non_present, cmp_method_bid)
        self.assertEquals(item_insert_point, 0)

    def test_bin_search_bids_update_present(self):
        idx = binary_search(self.bids, self.deal_update, cmp_method_bid)
        is_present = False
        if idx < len(self.bids):
            is_present = self.bids[idx] == self.deal_update
        self.assertTrue(is_present)

def test_bin_search_asks(self):
    item_insert_point = binary_search(self.asks, self.first, cmp_method_ask)
    self.assertEquals(item_insert_point, 0)

def test_bin_search_asks_not_present(self):
    item_insert_point = binary_search(self.asks, self.non_present, cmp_method_ask)
    self.assertEquals(item_insert_point, len(self.asks))

def test_bin_search_asks_update_present(self):
    idx = binary_search(self.asks, self.deal_update, cmp_method_ask)
    is_present = False
    if idx < len(self.asks):
        is_present = self.asks[idx] == self.deal_update
    self.assertTrue(is_present)

def test_bin_search_bids(self):
    item_insert_point = binary_search(self.bids, self.first, cmp_method_bid)
    self.assertEquals(item_insert_point, -1 + len(self.bids))

def test_bin_search_bids_not_present(self):
    item_insert_point = binary_search(self.bids, self.non_present, cmp_method_bid)
    self.assertEquals(item_insert_point, 0)

def test_bin_search_bids_update_present(self):
    idx = binary_search(self.bids, self.deal_update, cmp_method_bid)
    is_present = False
    if idx < len(self.bids):
        is_present = self.bids[idx] == self.deal_update
    self.assertTrue(is_present)

class BinancePublicApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_binance_ticker_retrieval(self):
        timest = get_now_seconds_local()
        tickers = get_tickers_binance(BINANCE_CURRENCY_PAIRS, timest)
        for ticker in tickers:
            if ticker:
                self.assertEquals(type(ticker), Ticker)

    def test_binance_ohlc_retrieval(self):
        date_end = get_now_seconds_utc()
        date_start = date_end - 900
        for currency in BINANCE_CURRENCY_PAIRS:
            period = '15m'
            candles = get_ohlc_binance(currency, date_start, date_end, period)
            for candle in candles:
                if candle:
                    self.assertEquals(type(candle), Candle)

    def test_binance_order_book_retrieval(self):
        timest = get_now_seconds_utc()
        for currency in BINANCE_CURRENCY_PAIRS:
            order_book = get_order_book_binance(currency, timest)
            if order_book:
                self.assertEquals(type(order_book), OrderBook)

    def test_binance_trade_history_retrieval(self):
        today = get_now_seconds_utc()
        yesterday = today - 24 * 3600
        for pair_name in BINANCE_CURRENCY_PAIRS:
            trade_history = get_history_binance(pair_name, yesterday, today)
            for entry in trade_history:
                if entry:
                    self.assertEquals(type(entry), TradeHistory)

def test_binance_ticker_retrieval(self):
    timest = get_now_seconds_local()
    tickers = get_tickers_binance(BINANCE_CURRENCY_PAIRS, timest)
    for ticker in tickers:
        if ticker:
            self.assertEquals(type(ticker), Ticker)

# Node: get_now_seconds_local
def test_binance_ohlc_retrieval(self):
    date_end = get_now_seconds_utc()
    date_start = date_end - 900
    for currency in BINANCE_CURRENCY_PAIRS:
        period = '15m'
        candles = get_ohlc_binance(currency, date_start, date_end, period)
        for candle in candles:
            if candle:
                self.assertEquals(type(candle), Candle)

def test_binance_order_book_retrieval(self):
    timest = get_now_seconds_utc()
    for currency in BINANCE_CURRENCY_PAIRS:
        order_book = get_order_book_binance(currency, timest)
        if order_book:
            self.assertEquals(type(order_book), OrderBook)

# Node: get_order_book_binance
def test_binance_trade_history_retrieval(self):
    today = get_now_seconds_utc()
    yesterday = today - 24 * 3600
    for pair_name in BINANCE_CURRENCY_PAIRS:
        trade_history = get_history_binance(pair_name, yesterday, today)
        for entry in trade_history:
            if entry:
                self.assertEquals(type(entry), TradeHistory)

class BittrexPublicApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_bittrex_ticker_retrieval(self):
        timest = get_now_seconds_local()
        for pair_name in BITTREX_CURRENCY_PAIRS:
            ticker = get_ticker_bittrex(pair_name, timest)
            if ticker:
                self.assertEquals(type(ticker), Ticker)

    def test_bittrex_ohlc_retrieval(self):
        date_end = get_now_seconds_utc()
        date_start = date_end - 900
        for pair_name in BITTREX_CURRENCY_PAIRS:
            period = 'thirtyMin'
            candles = get_ohlc_bittrex(pair_name, date_start, date_end, period)
            for candle in candles:
                if candle:
                    self.assertEquals(type(candle), Candle)

    def test_bittrex_order_book_retrieval(self):
        timest = get_now_seconds_utc()
        for currency in BITTREX_CURRENCY_PAIRS:
            order_book = get_order_book_bittrex(currency, timest)
            if order_book:
                self.assertEquals(type(order_book), OrderBook)

    def test_bittrex_trade_history_retrieval(self):
        today = get_now_seconds_utc()
        yesterday = today - 24 * 3600
        for pair_name in BITTREX_CURRENCY_PAIRS:
            trade_history = get_history_bittrex(pair_name, yesterday, today)
            for entry in trade_history:
                if entry:
                    self.assertEquals(type(entry), TradeHistory)

def test_bittrex_ticker_retrieval(self):
    timest = get_now_seconds_local()
    for pair_name in BITTREX_CURRENCY_PAIRS:
        ticker = get_ticker_bittrex(pair_name, timest)
        if ticker:
            self.assertEquals(type(ticker), Ticker)

def test_bittrex_ohlc_retrieval(self):
    date_end = get_now_seconds_utc()
    date_start = date_end - 900
    for pair_name in BITTREX_CURRENCY_PAIRS:
        period = 'thirtyMin'
        candles = get_ohlc_bittrex(pair_name, date_start, date_end, period)
        for candle in candles:
            if candle:
                self.assertEquals(type(candle), Candle)

def test_bittrex_order_book_retrieval(self):
    timest = get_now_seconds_utc()
    for currency in BITTREX_CURRENCY_PAIRS:
        order_book = get_order_book_bittrex(currency, timest)
        if order_book:
            self.assertEquals(type(order_book), OrderBook)

# Node: get_order_book_bittrex
def test_bittrex_trade_history_retrieval(self):
    today = get_now_seconds_utc()
    yesterday = today - 24 * 3600
    for pair_name in BITTREX_CURRENCY_PAIRS:
        trade_history = get_history_bittrex(pair_name, yesterday, today)
        for entry in trade_history:
            if entry:
                self.assertEquals(type(entry), TradeHistory)

class HuobiPublicApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_huobi_ticker_retrieval(self):
        timest = get_now_seconds_local()
        for currency in HUOBI_CURRENCY_PAIRS:
            ticker = get_ticker_huobi(currency, timest)
            if ticker:
                self.assertEquals(type(ticker), Ticker)

    def test_huobi_ohlc_retrieval(self):
        date_end = get_now_seconds_utc()
        date_start = date_end - 900
        for currency in HUOBI_CURRENCY_PAIRS:
            period = '15min'
            candles = get_ohlc_huobi(currency, date_start, date_end, period)
            for candle in candles:
                if candle:
                    self.assertEquals(type(candle), Candle)

    def test_huobi_order_book_retrieval(self):
        timest = get_now_seconds_utc()
        for currency in HUOBI_CURRENCY_PAIRS:
            order_book = get_order_book_huobi(currency, timest)
            if order_book:
                self.assertEquals(type(order_book), OrderBook)

    def test_huobi_trade_history_retrieval(self):
        today = get_now_seconds_utc()
        yesterday = today - 24 * 3600
        for pair_name in HUOBI_CURRENCY_PAIRS:
            trade_history = get_history_huobi(pair_name, yesterday, today)
            for entry in trade_history:
                if entry:
                    self.assertEquals(type(entry), TradeHistory)

def test_huobi_ticker_retrieval(self):
    timest = get_now_seconds_local()
    for currency in HUOBI_CURRENCY_PAIRS:
        ticker = get_ticker_huobi(currency, timest)
        if ticker:
            self.assertEquals(type(ticker), Ticker)

def test_huobi_ohlc_retrieval(self):
    date_end = get_now_seconds_utc()
    date_start = date_end - 900
    for currency in HUOBI_CURRENCY_PAIRS:
        period = '15min'
        candles = get_ohlc_huobi(currency, date_start, date_end, period)
        for candle in candles:
            if candle:
                self.assertEquals(type(candle), Candle)

def test_huobi_order_book_retrieval(self):
    timest = get_now_seconds_utc()
    for currency in HUOBI_CURRENCY_PAIRS:
        order_book = get_order_book_huobi(currency, timest)
        if order_book:
            self.assertEquals(type(order_book), OrderBook)

# Node: get_order_book_huobi
def test_huobi_trade_history_retrieval(self):
    today = get_now_seconds_utc()
    yesterday = today - 24 * 3600
    for pair_name in HUOBI_CURRENCY_PAIRS:
        trade_history = get_history_huobi(pair_name, yesterday, today)
        for entry in trade_history:
            if entry:
                self.assertEquals(type(entry), TradeHistory)

class KrakenPublicApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_kraken_ticker_retrieval(self):
        timest = get_now_seconds_local()
        for pair_name in KRAKEN_CURRENCIES:
            ticker = get_ticker_kraken(pair_name, timest)
            if ticker:
                self.assertEquals(type(ticker), Ticker)

    def test_kraken_ohlc_retrieval(self):
        date_end = get_now_seconds_utc()
        date_start = date_end - 900
        for pair_name in KRAKEN_CURRENCIES:
            period = 15
            candles = get_ohlc_kraken(pair_name, date_start, date_end, period)
            for candle in candles:
                if candle:
                    self.assertEquals(type(candle), Candle)

    def test_kraken_order_book_retrieval(self):
        timest = get_now_seconds_utc()
        for currency in KRAKEN_CURRENCIES:
            order_book = get_order_book_kraken(currency, timest)
            if order_book:
                self.assertEquals(type(order_book), OrderBook)

    def test_kraken_trade_history_retrieval(self):
        today = get_now_seconds_utc()
        yesterday = today - 24 * 3600
        for pair_name in KRAKEN_CURRENCIES:
            trade_history = get_history_kraken(pair_name, yesterday, today)
            for entry in trade_history:
                if entry:
                    self.assertEquals(type(entry), TradeHistory)

def test_kraken_ticker_retrieval(self):
    timest = get_now_seconds_local()
    for pair_name in KRAKEN_CURRENCIES:
        ticker = get_ticker_kraken(pair_name, timest)
        if ticker:
            self.assertEquals(type(ticker), Ticker)

def test_kraken_ohlc_retrieval(self):
    date_end = get_now_seconds_utc()
    date_start = date_end - 900
    for pair_name in KRAKEN_CURRENCIES:
        period = 15
        candles = get_ohlc_kraken(pair_name, date_start, date_end, period)
        for candle in candles:
            if candle:
                self.assertEquals(type(candle), Candle)

def test_kraken_order_book_retrieval(self):
    timest = get_now_seconds_utc()
    for currency in KRAKEN_CURRENCIES:
        order_book = get_order_book_kraken(currency, timest)
        if order_book:
            self.assertEquals(type(order_book), OrderBook)

# Node: get_order_book_kraken
def test_kraken_trade_history_retrieval(self):
    today = get_now_seconds_utc()
    yesterday = today - 24 * 3600
    for pair_name in KRAKEN_CURRENCIES:
        trade_history = get_history_kraken(pair_name, yesterday, today)
        for entry in trade_history:
            if entry:
                self.assertEquals(type(entry), TradeHistory)

class PoloniexPublicApiTests(unittest.TestCase):

    def setUp(self):
        set_logging_level(LOG_ALL_ERRORS)

    def test_poloniex_ticker_retrieval(self):
        timest = get_now_seconds_local()
        for pair_name in POLONIEX_CURRENCY_PAIRS:
            ticker = get_ticker_poloniex(pair_name, timest)
            if ticker:
                self.assertEquals(type(ticker), Ticker)

    def test_poloniex_ohlc_retrieval(self):
        date_end = get_now_seconds_utc()
        date_start = date_end - 900
        for pair_name in POLONIEX_CURRENCY_PAIRS:
            period = 14400
            candles = get_ohlc_poloniex(pair_name, date_start, date_end, period)
            for candle in candles:
                if candle:
                    self.assertEquals(type(candle), Candle)

    def test_poloniex_order_book_retrieval(self):
        timest = get_now_seconds_utc()
        for currency in POLONIEX_CURRENCY_PAIRS:
            order_book = get_order_book_poloniex(currency, timest)
            if order_book:
                self.assertEquals(type(order_book), OrderBook)

    def test_poloniex_trade_history_retrieval(self):
        today = get_now_seconds_utc()
        yesterday = today - 24 * 3600
        for pair_name in POLONIEX_CURRENCY_PAIRS:
            trade_history = get_history_poloniex(pair_name, yesterday, today)
            for entry in trade_history:
                if entry:
                    self.assertEquals(type(entry), TradeHistory)

def test_poloniex_ticker_retrieval(self):
    timest = get_now_seconds_local()
    for pair_name in POLONIEX_CURRENCY_PAIRS:
        ticker = get_ticker_poloniex(pair_name, timest)
        if ticker:
            self.assertEquals(type(ticker), Ticker)

# Node: get_ticker_poloniex
def test_poloniex_ohlc_retrieval(self):
    date_end = get_now_seconds_utc()
    date_start = date_end - 900
    for pair_name in POLONIEX_CURRENCY_PAIRS:
        period = 14400
        candles = get_ohlc_poloniex(pair_name, date_start, date_end, period)
        for candle in candles:
            if candle:
                self.assertEquals(type(candle), Candle)

def test_poloniex_order_book_retrieval(self):
    timest = get_now_seconds_utc()
    for currency in POLONIEX_CURRENCY_PAIRS:
        order_book = get_order_book_poloniex(currency, timest)
        if order_book:
            self.assertEquals(type(order_book), OrderBook)

# Node: get_order_book_poloniex
def test_poloniex_trade_history_retrieval(self):
    today = get_now_seconds_utc()
    yesterday = today - 24 * 3600
    for pair_name in POLONIEX_CURRENCY_PAIRS:
        trade_history = get_history_poloniex(pair_name, yesterday, today)
        for entry in trade_history:
            if entry:
                self.assertEquals(type(entry), TradeHistory)

def compare_price(tickers, threshold, predicate):
    """
    High level function that perform tickers analysis

    :param tickers: dict of dict where data are structured by exchange_id -> pair_id
    :param threshold: percentage, 0-100.0, float to trigger event
    :return: array of triplets pair_id, exchange_1.lowest_price, exchange_2.highest_bid
    """
    res = []
    sorted_tickers = get_matches(tickers, 'pair_id')
    for pair_id in CURRENCY_PAIR.values():
        if pair_id in sorted_tickers:
            tickers_to_check = sorted_tickers[pair_id]
            if len(tickers_to_check) < 2:
                for b in tickers_to_check:
                    log_to_file('Ticker: not found ticker from other markets: ' + str(b), 'ticker.log')
            else:
                current_result = check_all_combinations_list(tickers_to_check, threshold, predicate)
                if current_result:
                    res += current_result
    return res

# Node: get_matches
# Node: check_all_combinations_list
def adjust_price_by_order_book(orders, min_volume):
    """
        In order to address not immediate speed and influence of other participant of market
        We will use not the best price from order book to minimise number of non-closed deals
        Details and discussion at https://gitlab.com/crypto_trade/crypto_crawler/issues/15

        In short dive into order book, take price from level where we can place min_volume * 2

    :param orders: the most recent order book
    :param min_volume: Decimal value of volume determined according to various checks
    :return: Decimal object with exact price
    """
    new_price = Decimal(-10.0)
    acc_volume = Decimal(0.0)
    max_volume = 2 * min_volume
    max_len = len(orders)
    if min_volume == 0.0:
        msg = 'adjust_price_by_order_book: ERROR min volume is ZERO'
        log_to_file(msg, 'price_adjustment.log')
        assert min_volume == 0
    idx = 0
    while acc_volume < max_volume and idx < max_len:
        new_price = orders[idx].price
        acc_volume += orders[idx].volume
        idx += 1
    return new_price

