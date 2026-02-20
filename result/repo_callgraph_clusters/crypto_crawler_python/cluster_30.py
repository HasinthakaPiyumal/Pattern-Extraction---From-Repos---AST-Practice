# Cluster 30

def group_trades_by_orders(orders, history_trades):
    missing_orders = defaultdict(list)
    failed_orders = defaultdict(list)
    orders_with_corresponding_trades = []
    for order in orders:
        if order.order_id is None:
            failed_orders[order.exchange_id].append(order)
        else:
            res = next((x for x in history_trades if x.order_id == order.order_id), None)
            if res is None:
                missing_orders[order.exchange_id].append(order)
            else:
                current_trades_list = []
                for x in history_trades:
                    if x.order_id == order.order_id:
                        current_trades_list.append(x)
                orders_with_corresponding_trades.append((order, current_trades_list))
    return (missing_orders, failed_orders, orders_with_corresponding_trades)

# Node: next
class ExchangeKey(object):

    def __init__(self, api_key, secret):
        self.api_key = api_key
        self.secret = secret

    @classmethod
    def from_file(cls, path, exchange_name):
        array = []
        full_path = os.path.join(path, exchange_name.lower() + '.key')
        with open(full_path, 'r') as myfile:
            for line in myfile:
                array.append(line.rstrip())
                if len(array) == 2:
                    break
        return ExchangeKey(array[0], array[1])

@classmethod
def from_file(cls, path, exchange_name):
    array = []
    full_path = os.path.join(path, exchange_name.lower() + '.key')
    with open(full_path, 'r') as myfile:
        for line in myfile:
            array.append(line.rstrip())
            if len(array) == 2:
                break
    return ExchangeKey(array[0], array[1])

# Node: join
# Node: open
# Node: rstrip
# Node: ExchangeKey
def save_list_to_file(some_data, file_name):
    with open(file_name, 'a') as myfile:
        for entry in some_data:
            myfile.write('%s\n' % str(entry))

# Node: write
def log_to_file(data, file_name, log_dir=None):
    if log_dir is None:
        log_dir = get_log_folder()
    full_path = os.path.join(log_dir, file_name)
    with open(full_path, 'a') as the_file:
        ts = get_now_seconds_utc()
        pid = os.getpid()
        the_file.write('{ts}: PID: {pid} {data}\n'.format(ts=ts, pid=pid, data=str(data)))

# Node: get_log_folder
# Node: getpid
def save_to_csv_file(file_name, fields_list, array_list):
    with open(file_name, 'w') as f:
        writer = csv.writer(f, delimiter=';', quotechar=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(fields_list)
        for entry in array_list:
            writer.writerow(list(entry))

# Node: writer
# Node: writerow
# Node: list
class BaseData(object):

    def __str__(self):
        attr_list = [a for a in dir(self) if not a.startswith('__') and (not callable(getattr(self, a)))]
        str_repr = '['
        for every_attr in attr_list:
            str_repr += every_attr + ' - ' + str(getattr(self, every_attr)) + ' '
        str_repr += ']'
        return str_repr

def __str__(self):
    attr_list = [a for a in dir(self) if not a.startswith('__') and (not callable(getattr(self, a)))]
    str_repr = '['
    for every_attr in attr_list:
        str_repr += every_attr + ' - ' + str(getattr(self, every_attr)) + ' '
    str_repr += ']'
    return str_repr

# Node: dir
# Node: startswith
# Node: callable
# Node: getattr
class OrderBookUpdate(BaseData):

    def __init__(self, sequence_id, bid, ask, timest_ms, trades_sell, trades_buy, sequence_id_end=None):
        self.sequence_id = sequence_id
        self.sequence_id_end = sequence_id_end
        self.bid = bid
        self.ask = ask
        self.timest_ms = timest_ms
        self.trades_sell = trades_sell
        self.trades_buy = trades_buy

    def __str__(self):
        attr_list = [a for a in dir(self) if not a.startswith('__') and (not a.startswith('ask')) and (not a.startswith('bid')) and (not a.startswith('trades')) and (not callable(getattr(self, a)))]
        str_repr = '['
        for every_attr in attr_list:
            str_repr += every_attr + ' - ' + str(getattr(self, every_attr)) + ' '
        str_repr += 'bids - [' + '\n'.join(map(str, self.bid)) + '] '
        str_repr += 'asks - [' + '\n'.join(map(str, self.ask)) + ']]'
        str_repr += 'trades_sell - [' + '\n'.join(map(str, self.trades_sell)) + '] '
        str_repr += 'trades_buy - [' + '\n'.join(map(str, self.trades_buy)) + ']'
        return str_repr

def __str__(self):
    attr_list = [a for a in dir(self) if not a.startswith('__') and (not a.startswith('ask')) and (not a.startswith('bid')) and (not a.startswith('trades')) and (not callable(getattr(self, a)))]
    str_repr = '['
    for every_attr in attr_list:
        str_repr += every_attr + ' - ' + str(getattr(self, every_attr)) + ' '
    str_repr += 'bids - [' + '\n'.join(map(str, self.bid)) + '] '
    str_repr += 'asks - [' + '\n'.join(map(str, self.ask)) + ']]'
    str_repr += 'trades_sell - [' + '\n'.join(map(str, self.trades_sell)) + '] '
    str_repr += 'trades_buy - [' + '\n'.join(map(str, self.trades_buy)) + ']'
    return str_repr

# Node: map
class Deal(BaseData):

    def __init__(self, price, volume):
        self.price = Decimal(str(price))
        self.volume = Decimal(str(volume))

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(self, other.__class__):
            return self.price == other.price
        return False

    def __str__(self):
        return '[price: {:16.8f} volume: {:16.8f} ]'.format(self.price, self.volume)
    __repr__ = __str__

def __eq__(self, other):
    """Overrides the default implementation"""
    if isinstance(self, other.__class__):
        return self.price == other.price
    return False

# Node: isinstance
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

def __str__(self):
    attr_list = [a for a in dir(self) if not a.startswith('__') and (not a.startswith('ask')) and (not a.startswith('bid')) and (not a.startswith('insert')) and (not callable(getattr(self, a)))]
    str_repr = '['
    for every_attr in attr_list:
        str_repr += every_attr + ' - ' + str(getattr(self, every_attr)) + ' '
    str_repr += 'bids - [' + '\n'.join(map(str, self.bid)) + '] '
    str_repr += 'asks - [' + '\n'.join(map(str, self.ask)) + ']]'
    return str_repr

def default_on_public(exchange_id, args):
    if get_logging_level() >= LOG_ALL_DEBUG:
        print('Poloniex: default_on_public')
        print(' - '.join([exchange_id, args]))

# Node: print
def default_on_error():
    print('Poloniex: default_on_error')

def default_on_close():
    print('Poloniex: default_on_close')

class SubscriptionPoloniex:

    def __init__(self, pair_id, on_update=default_on_public, base_url=POLONIEX_WEBSCOKET_URL):
        """
        :param pair_id:     - currency pair to be used for trading
        :param base_url:    - web-socket subscription end points
        :param on_update:   - idea is the following:
            we pass reference to method WITH initialized order book for that pair_id
            whenever we receive update we update order book and trigger checks for arbitrage
        """
        self.url = base_url
        self.pair_id = pair_id
        self.pair_name = get_currency_pair_to_poloniex(self.pair_id)
        self.on_update = on_update
        self.order_book_is_received = False
        self.should_run = False
        self.last_heartbeat_ts = None
        self.ws = None
        self.subscribe_string = json.dumps({'command': 'subscribe', 'channel': self.pair_name})
        self.subscribe_heartbeat = json.dumps({'command': 'subscribe', 'channel': WEBSOCKET_SUBSCRIBE_HEARTBEAT})

    def on_open(self):

        def run():
            log_subscribe_to_exchange_heartbeat('Poloniex')
            self.ws.send(self.subscribe_string)
            try:
                while self.should_run:
                    self.ws.send(self.subscribe_heartbeat)
                    sleep_for(1)
            except Exception as e:
                log_send_heart_beat_failed('Poloniex', e)
            log_unsubscribe_to_exchange_heartbeat('Poloniex')
        thread.start_new_thread(run, ())

    def on_public(self, compressed_data):
        msg = process_message(compressed_data)
        if not self.order_book_is_received and 'orderBook' in compressed_data:
            self.order_book_is_received = True
            order_book_delta = parse_socket_order_book_poloniex(msg, self.pair_id)
        else:
            order_book_delta = parse_socket_update_poloniex(msg)
        if order_book_delta is None:
            str_msg = str(msg)
            if '1010' in str_msg:
                self.last_heartbeat_ts = get_now_seconds_utc()
            else:
                err_msg = 'Poloniex - cant parse update from message: {msg}'.format(msg=str_msg)
                log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
        else:
            self.last_heartbeat_ts = get_now_seconds_utc()
            self.on_update(EXCHANGE.POLONIEX, order_book_delta)

    def subscribe(self):
        if self.should_run:
            die_hard('Poloniex - another subcription thread running?')
        if get_logging_level() == LOG_ALL_TRACE:
            msg = 'Poloniex - call subscribe!'
            log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
            print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
        self.should_run = True
        if get_logging_level() == LOG_ALL_TRACE:
            websocket.enableTrace(True)
        try:
            self.ws = create_connection(POLONIEX_WEBSCOKET_URL, enable_multithread=True)
            self.ws.settimeout(15)
        except Exception as e:
            msg = 'Poloniex - connect ws error - {}, retry...'.format(str(e))
            print_to_console(msg, LOG_ALL_ERRORS)
            self.disconnect()
            return
        self.ws.send(self.subscribe_string)
        log_conect_to_websocket('Poloniex')
        while self.should_run:
            try:
                compressed_data = self.ws.recv()
                self.on_public(compressed_data)
            except Exception as e:
                log_error_on_receive_from_socket('Poloniex', e)
                break
            if self.last_heartbeat_ts:
                ts_now = get_now_seconds_utc()
                if ts_now - self.last_heartbeat_ts > POLONIEX_WEBSOCKET_TIMEOUT:
                    log_heartbeat_is_missing('Poloniex', POLONIEX_WEBSOCKET_TIMEOUT, self.last_heartbeat_ts, ts_now)
                    break
        log_subscription_cancelled('Poloniex')
        self.disconnect()

    def disconnect(self):
        self.should_run = False
        self.order_book_is_received = False
        self.last_heartbeat_ts = None
        try:
            self.ws.close()
        except Exception as e:
            log_websocket_disconnect('Poloniex', e)

    def is_running(self):
        return self.should_run

def disconnect(self):
    self.should_run = False
    self.order_book_is_received = False
    self.last_heartbeat_ts = None
    try:
        self.ws.close()
    except Exception as e:
        log_websocket_disconnect('Poloniex', e)

# Node: close
# Node: log_websocket_disconnect
class IteratorFile(io.TextIOBase):
    """ given an iterator which yields strings,
    return a file like object for reading those strings

    credits: https://gist.github.com/jsheedy/ed81cdf18190183b3b7d
    discussion: https://stackoverflow.com/questions/8134602/psycopg2-insert-multiple-rows-with-one-query

    """

    def __init__(self, it):
        self._it = it
        self._f = io.StringIO()

    def read(self, length=sys.maxsize):
        try:
            while self._f.tell() < length:
                self._f.write(next(self._it) + '\n')
        except StopIteration as e:
            pass
        except Exception as e:
            print('uncaught exception: {}'.format(e))
        finally:
            self._f.seek(0)
            data = self._f.read(length)
            remainder = self._f.read()
            self._f.seek(0)
            self._f.truncate(0)
            self._f.write(remainder)
            return data

    def readline(self):
        return next(self._it)

def read(self, length=sys.maxsize):
    try:
        while self._f.tell() < length:
            self._f.write(next(self._it) + '\n')
    except StopIteration as e:
        pass
    except Exception as e:
        print('uncaught exception: {}'.format(e))
    finally:
        self._f.seek(0)
        data = self._f.read(length)
        remainder = self._f.read()
        self._f.seek(0)
        self._f.truncate(0)
        self._f.write(remainder)
        return data

# Node: tell
# Node: seek
# Node: read
# Node: truncate
def readline(self):
    return next(self._it)

def default_on_public(exchange_id, args):
    if get_logging_level() >= LOG_ALL_DEBUG:
        print('on_public')
        print(''.join([str(exchange_id), str(args)]))

def default_on_error(ws, error):
    ws.close()
    print(error)

class SubscriptionHuobi(object):

    def __init__(self, pair_id, on_update=default_on_public, base_url=HUOBI_WEBSOCKET_URL):
        """
        :param pair_id:     - currency pair to be used for trading
        :param base_url:    - web-socket subscription end points
        :param on_update:   - idea is the following:
            we pass reference to method WITH initialized order book for that pair_id
            whenever we receive update we update order book and trigger checks for arbitrage
        """
        self.url = base_url
        self.pair_id = pair_id
        self.pair_name = get_currency_pair_to_huobi(self.pair_id)
        self.subscription_url = HUOBI_SUBSCRIPTION_STRING.format(pair_name=self.pair_name, uuid_id=uuid.uuid4())
        self.on_update = on_update
        self.should_run = False

    def on_public(self, args):
        msg = process_message(args)
        updated_order_book = parse_socket_update_huobi(msg, self.pair_id)
        if updated_order_book is None:
            if 'ping' in msg or 'pong' in msg or ('status' in msg and 'ok' == msg['status']):
                return
            err_msg = 'Huobi - cant parse update from message: {msg}'.format(msg=msg)
            log_to_file(err_msg, SOCKET_ERRORS_LOG_FILE_NAME)
        else:
            self.on_update(EXCHANGE.HUOBI, updated_order_book)

    def on_open(self):

        def run():
            log_subscribe_to_exchange_heartbeat('Huobi')
            self.ws.send(self.subscription_url)
            try:
                while self.should_run:
                    self.ws.send(json.dumps({'ping': 18212558000}))
                    sleep_for(1)
                self.ws.close()
            except Exception as e:
                log_send_heart_beat_failed('Huobi', e)
            log_unsubscribe_to_exchange_heartbeat('Huobi')
        thread.start_new_thread(run, ())

    def subscribe(self):
        if self.should_run:
            die_hard('Huobi - another subcription thread running?')
        self.should_run = True
        if get_logging_level() == LOG_ALL_TRACE:
            websocket.enableTrace(True)
        try:
            self.ws = create_connection(HUOBI_WEBSOCKET_URL, enable_multithread=True, sslopt={'cert_reqs': ssl.CERT_NONE})
            self.ws.settimeout(15)
        except Exception as e:
            print('Huobi - connect ws error - {}, retry...'.format(str(e)))
            self.disconnect()
            return
        self.on_open()
        log_conect_to_websocket('Huobi')
        while self.should_run:
            try:
                compress_data = self.ws.recv()
                if compress_data:
                    self.on_public(compress_data)
            except Exception as e:
                log_error_on_receive_from_socket('Huobi', e)
                break
        log_subscription_cancelled('Huobi')
        self.disconnect()

    def disconnect(self):
        self.should_run = False
        try:
            self.ws.close()
        except Exception as e:
            log_websocket_disconnect('Huobi', e)

    def is_running(self):
        return self.should_run

def disconnect(self):
    self.should_run = False
    try:
        self.ws.close()
    except Exception as e:
        log_websocket_disconnect('Huobi', e)

def is_screen_present(screen_name):
    var = check_output(['screen -ls; true'], shell=True)
    if '.{}\t('.format(screen_name) in var:
        print('Screen with name {} is running!'.format(screen_name))
        return True
    print('Screen with name {} is not running'.format(screen_name))
    return False

# Node: check_output
# Node: getoutput
def create_screen(screen_name):
    """
    Create screen on local machine

    :param screen_name:
    :return: output if any
    """
    if is_screen_present(screen_name):
        print('NONONO! You already have with exact same name - {screen_name} It will lead to trouble.'.format(screen_name=screen_name))
        assert False
    if isinstance(screen_name, str):
        out = commands.getoutput('screen -dmS "%s"' % screen_name)
        print(out)
    else:
        out = 'No screen name provided'
    return out

# Node: is_screen_present
def create_screen_window(screen_name, window_name):
    """

    Create numerous named screen consoles in screen with name screen_name

    :param screen_name:
    :param window_name:
    :return: False, if assert failed or command output
    """
    cmd = "screen -S '{screen_name}' -X screen -t '{window_name}'".format(screen_name=screen_name, window_name=window_name)
    return commands.getoutput(cmd)

def run_command_in_screen(screen_name, window_name, command):
    """
    :param screen_name:
    :param window_name:
    :param command: full command with ALL arguments
    :return: command execution output if any
    """
    cmd_line = "screen -S '{sn}' -p '{wn}' -X stuff '{exe}\n' ".format(sn=screen_name, wn=window_name, exe=command)
    print('Executing command:\n{}'.format(cmd_line))
    return commands.getoutput(cmd_line)

class CommonSettings(BaseData):

    def __init__(self, logging_level_id=LOG_ALL_DEBUG, log_folder=LOGS_FOLDER, key_path=API_KEY_PATH, cache_host=CACHE_HOST, cache_port=CACHE_PORT, db_host=DB_HOST, db_port=DB_PORT, db_name=DB_NAME, exchanges_ids=None):
        self.logging_level_id = logging_level_id
        self.logging_level_name = get_debug_level_name_by_id(self.logging_level_id)
        self.log_folder = log_folder
        self.key_path = key_path
        self.cache_host = cache_host
        self.cache_port = cache_port
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        if not exchanges_ids:
            self.exchanges = EXCHANGE.values()
        else:
            self.exchanges = exchanges_ids

    @classmethod
    def from_cfg(cls, file_name):
        config = ConfigParser.RawConfigParser()
        config.read(file_name)
        log_level_name = config.get('logging', 'log_level')
        log_level_id = get_logging_level_id_by_name(log_level_name)
        exchanges_ids = parse_exchange_ids(config.get('common', 'exchanges'))
        return CommonSettings(log_level_id, config.get('logging', 'logs_folder'), config.get('keys', 'path_to_api_keys'), config.get('redis', 'redis_host'), config.get('redis', 'redis_port'), config.get('postgres', 'db_host'), config.get('postgres', 'db_port'), config.get('postgres', 'db_name'), exchanges_ids)

@classmethod
def from_cfg(cls, file_name):
    config = ConfigParser.RawConfigParser()
    config.read(file_name)
    log_level_name = config.get('logging', 'log_level')
    log_level_id = get_logging_level_id_by_name(log_level_name)
    exchanges_ids = parse_exchange_ids(config.get('common', 'exchanges'))
    return CommonSettings(log_level_id, config.get('logging', 'logs_folder'), config.get('keys', 'path_to_api_keys'), config.get('redis', 'redis_host'), config.get('redis', 'redis_port'), config.get('postgres', 'db_host'), config.get('postgres', 'db_port'), config.get('postgres', 'db_name'), exchanges_ids)

# Node: RawConfigParser
# Node: get_logging_level_id_by_name
# Node: parse_exchange_ids
# Node: CommonSettings
def get_all_combination(my_dict, max_len):
    """
    :param my_dict:
    :param max_len:
    :return: list of possible combination of dictionary values

    Example:
        wtf= {}
        wtf[1] = "UNO"
        wtf[2] = "TWO"
        wtf[3] = "THREE"
        wtf[3] = "FOUR"

        res = get_all_combination(wtf, 2)
        print res
        [[1, 2], [1, 3], [2, 3]]

    """
    return map(list, itertools.combinations(my_dict.keys(), max_len))

# Node: combinations
# Node: keys
def get_all_permutation(my_dict, max_len):
    """
    :param my_dict:
    :param max_len:
    :return: list of possible permutation of dictionary values


    Example:
        wtf= {}
        wtf[1] = "UNO"
        wtf[2] = "TWO"
        wtf[3] = "THREE"
        wtf[3] = "FOUR"

        res = get_all_permutation(wtf, 2)
        print res
        [[1, 2], [1, 3], [2, 1], [2, 3], [3, 1], [3, 2]]

    """
    return map(list, itertools.permutations(my_dict.keys(), max_len))

# Node: permutations
def get_all_permutation_list(my_list, max_len):
    """
    :param my_list:
    :param max_len:
    :return: list of possible permutation of dictionary values


    Example:
        wtf= []
        wtf[1] = "UNO"
        wtf[2] = "TWO"
        wtf[3] = "THREE"
        wtf[3] = "FOUR"

        res = get_all_permutation(wtf, 2)
        print res
        [[1, 2], [1, 3], [2, 1], [2, 3], [3, 1], [3, 2]]
    """
    return map(list, itertools.permutations(my_list, max_len))

