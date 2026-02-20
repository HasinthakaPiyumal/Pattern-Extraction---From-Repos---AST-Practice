# Cluster 11

def signed_body(body, secret):
    payload = hmac.new(secret, _urlencode(body), hashlib.sha512).hexdigest()
    return payload

# Node: hexdigest
# Node: new
def signed_body_256(body, secret):
    payload = hmac.new(secret.encode('utf-8'), _urlencode(body).encode('utf-8'), hashlib.sha256).hexdigest()
    return payload

def sign_string_256_base64(secret, msg):
    hmac_obj = hmac.new(key=secret.encode('utf-8'), msg=msg.encode('utf-8'), digestmod=hashlib.sha256)
    return base64.b64encode(hmac_obj.digest())

# Node: b64encode
# Node: digest
def signed_string(body, secret):
    payload = hmac.new(secret, body, hashlib.sha512).hexdigest()
    return payload

def sign_kraken(body, urlpath, secret):
    """ Sign request data according to Kraken's scheme.
    :param body: API request parameters
    :type body: dict
    :param urlpath: API URL path sans host
    :type urlpath: str
    :returns: signature digest
    """
    postdata = _urlencode(body)
    encoded = (str(body['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    signature = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(signature.digest())
    return sigdigest.decode()

# Node: sha256
# Node: b64decode
# Node: decode
class Candle(BaseData):
    insert_query = CANDLE_INSERT_QUERY
    type = CANDLE_TYPE_NAME
    table_name = CANDLE_TABLE_NAME
    columns = CANDLE_COLUMNS

    def __init__(self, pair_id, timest, price_high, price_low, price_open, price_close, exchange_id):
        self.pair_id = int(pair_id)
        self.pair = get_pair_name_by_id(self.pair_id)
        self.timest = long(timest)
        self.high = Decimal(price_high)
        self.low = Decimal(price_low)
        self.open = Decimal(price_open)
        self.close = Decimal(price_close)
        self.exchange_id = int(exchange_id)
        self.exchange = get_exchange_name_by_id(self.exchange_id)

    def tsv(self):
        return "{}\t{}\t{}\t{}\t{}\t{}\t{}\t'{}'".format(self.pair_id, self.exchange_id, self.open, self.close, self.high, self.low, self.timest, get_date_time_from_epoch(self.timest)).decode('utf8')

    def get_pg_arg_list(self):
        return (self.pair_id, self.exchange_id, self.open, self.close, self.high, self.low, self.timest, get_date_time_from_epoch(self.timest))

    @classmethod
    def from_poloniex(cls, json_document, currency):
        timest = json_document['date']
        price_high = json_document['high']
        price_low = json_document['low']
        price_open = json_document['open']
        price_close = json_document['close']
        currency_pair = get_currency_pair_from_poloniex(currency)
        return Candle(currency_pair, timest, price_high, price_low, price_open, price_close, EXCHANGE.POLONIEX)

    @classmethod
    def from_kraken(cls, json_document, currency):
        timest = json_document[0]
        price_high = json_document[2]
        price_low = json_document[3]
        price_open = json_document[1]
        price_close = json_document[4]
        currency_pair = get_currency_pair_from_kraken(currency)
        return Candle(currency_pair, timest, price_high, price_low, price_open, price_close, EXCHANGE.KRAKEN)

    @classmethod
    def from_bittrex(cls, json_document, currency):
        """
        result":[
        {"O":0.08184725,"H":0.08184725,"L":0.08181559,"C":0.08181559,"V":9.56201864,"T":"2017-07-21T17:26:00","BV":0.78232812},
        {"O":0.08181559,"H":0.08184725,"L":0.08181559,"C":0.08184725,"V":3.28483907,"T":"2017-07-21T17:27:00","BV":0.26876032}
        FIXME:  ISO 8601-formatted date
        """
        utc_time = datetime.strptime(json_document['T'], '%Y-%m-%dT%H:%M:%S')
        timest = (utc_time - datetime(1970, 1, 1)).total_seconds()
        price_high = json_document['H']
        price_low = json_document['L']
        price_open = json_document['O']
        price_close = json_document['C']
        currency_pair = get_currency_pair_from_bittrex(currency)
        return Candle(currency_pair, timest, price_high, price_low, price_open, price_close, EXCHANGE.BITTREX)

    @classmethod
    def from_binance(cls, json_document, currency):
        """
        [
        1499040000000,      // Open time
        "0.01634790",       // Open
        "0.80000000",       // High
        "0.01575800",       // Low
        "0.01577100",       // Close
        "148976.11427815",  // Volume
        1499644799999,      // Close time
        "2434.19055334",    // Quote asset volume
        308,                // Number of trades
        "1756.87402397",    // Taker buy base asset volume
        "28.46694368",      // Taker buy quote asset volume
        "17928899.62484339" // Can be ignored
        ]
        :return:
        """
        timest = 0.001 * long(json_document[0])
        price_high = json_document[2]
        price_low = json_document[3]
        price_open = json_document[1]
        price_close = json_document[4]
        currency_pair = get_currency_pair_from_binance(currency)
        return Candle(currency_pair, timest, price_high, price_low, price_open, price_close, EXCHANGE.BINANCE)

    @classmethod
    def from_huobi(cls, json_document, currency):
        """
                "id": 1499184000,
                "amount": 37593.0266,
                "count": 0,
                "open": 1935.2000,
                "close": 1879.0000,
                "low": 1856.0000,
                "high": 1940.0000,
                "vol": 71031537.97866500

        :param json_document:
        :param currency:
        :return:
        """
        timest = 0.001 * long(json_document['artifical_ts'])
        price_high = json_document['high']
        price_low = json_document['low']
        price_open = json_document['open']
        price_close = json_document['close']
        currency_pair = get_currency_pair_from_huobi(currency)
        return Candle(currency_pair, timest, price_high, price_low, price_open, price_close, EXCHANGE.HUOBI)

    @classmethod
    def from_string(cls, some_string):
        results = regex.findall(some_string)
        price_close = results[0][0]
        exchange_id = results[0][2]
        price_high = results[0][3]
        price_low = results[0][4]
        price_open = results[0][5]
        currency_pair_id = results[0][7]
        timest = results[0][8]
        return Candle(currency_pair_id, timest, price_high, price_low, price_open, price_close, exchange_id)

    @classmethod
    def from_row(cls, db_row):
        currency_pair_id = db_row[1]
        timest = db_row[7]
        price_high = db_row[5]
        price_low = db_row[6]
        price_open = db_row[3]
        price_close = db_row[4]
        exchange_id = db_row[2]
        return Candle(currency_pair_id, timest, price_high, price_low, price_open, price_close, exchange_id)

def tsv(self):
    return "{}\t{}\t{}\t{}\t{}\t{}\t{}\t'{}'".format(self.pair_id, self.exchange_id, self.open, self.close, self.high, self.low, self.timest, get_date_time_from_epoch(self.timest)).decode('utf8')

# Node: get_date_time_from_epoch
def get_pg_arg_list(self):
    return (self.pair_id, self.exchange_id, self.open, self.close, self.high, self.low, self.timest, get_date_time_from_epoch(self.timest))

class TradeHistory(BaseData):
    insert_query = TRADE_HISTORY_INSERT_QUERY
    type = TRADE_HISTORY_TYPE_NAME
    table_name = TRADE_HISTORY_TABLE_NAME
    columns = TRADE_HISTORY_COLUMNS

    def __init__(self, pair_id, timest, deal_type, price, amount, total, exchange_id):
        self.pair_id = int(pair_id)
        self.pair = get_pair_name_by_id(self.pair_id)
        self.timest = long(timest)
        self.deal_type = deal_type
        self.price = Decimal(price)
        self.amount = Decimal(amount)
        self.total = Decimal(total)
        self.exchange_id = int(exchange_id)
        self.exchange = get_exchange_name_by_id(self.exchange_id)

    def tsv(self):
        return "{}\t{}\t{}\t{}\t{}\t{}\t{}\t'{}'".format(self.pair_id, self.exchange_id, self.deal_type, self.price, self.amount, self.total, self.timest, get_date_time_from_epoch(self.timest)).decode('utf8')

    def get_pg_arg_list(self):
        return (self.pair_id, self.exchange_id, self.deal_type, self.price, self.amount, self.total, self.timest, get_date_time_from_epoch(self.timest))

    @classmethod
    def from_poloniex(cls, json_document, pair, timest):
        """
        {
          "globalTradeID":202950655,
          "tradeID":2459916,
          "date":"2017-08-02 17:06:09",
          "type":"sell",
          "rate":"0.00006476",
          "amount":"323.78885919",
          "total":"0.02096856"
        }
        """
        utc_time = datetime.strptime(json_document['date'], '%Y-%m-%d %H:%M:%S')
        deal_timest = (utc_time - datetime(1970, 1, 1)).total_seconds()
        deal_type = DEAL_TYPE.BUY
        if 'sell' in json_document['type']:
            deal_type = DEAL_TYPE.SELL
        price = json_document['rate']
        amount = json_document['amount']
        total = json_document['total']
        currency_pair = get_currency_pair_from_poloniex(pair)
        return TradeHistory(currency_pair, deal_timest, deal_type, price, amount, total, EXCHANGE.POLONIEX)

    @classmethod
    def from_kraken(cls, json_document, pair, timest):
        """
        <pair_name> = pair name
            array of array entries(<price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>)
        last = id to be used as since when polling for new trade data
        """
        deal_timest = json_document[2]
        deal_type = DEAL_TYPE.BUY
        if 's' in json_document[3]:
            deal_type = DEAL_TYPE.SELL
        price = Decimal(json_document[0])
        amount = Decimal(json_document[1])
        total = price * amount
        currency_pair = get_currency_pair_from_kraken(pair)
        return TradeHistory(currency_pair, deal_timest, deal_type, price, amount, total, EXCHANGE.KRAKEN)

    @classmethod
    def from_bittrex(cls, json_document, pair, timest):
        """
        [
           {
              "Id":59926023,
              "TimeStamp":"2017-08-02T17:11:28.033",
              "Quantity":3.49909364,
              "Price":0.01565000,
              "Total":0.05476081,
              "FillType":"FILL",
              "OrderType":"SELL"
           },
           {
              "Id":59926007,
              "TimeStamp":"2017-08-02T17:11:15.83",
              "Quantity":0.11242970,
              "Price":0.01566000,
              "Total":0.00176064,
              "FillType":"FILL",
              "OrderType":"BUY"
           }
        ]
        """
        try:
            utc_time = datetime.strptime(json_document['TimeStamp'], '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            utc_time = datetime.strptime(json_document['TimeStamp'], '%Y-%m-%dT%H:%M:%S')
        deal_timest = (utc_time - datetime(1970, 1, 1)).total_seconds()
        deal_type = DEAL_TYPE.BUY
        if 'SELL' in json_document['OrderType']:
            deal_type = DEAL_TYPE.SELL
        price = Decimal(json_document['Price'])
        amount = Decimal(json_document['Quantity'])
        total = json_document['Total']
        currency_pair = get_currency_pair_from_bittrex(pair)
        return TradeHistory(currency_pair, deal_timest, deal_type, price, amount, total, EXCHANGE.BITTREX)

    @classmethod
    def from_binance(cls, json_document, pair, timest):
        """
         {
                "a": 26129,         // Aggregate tradeId
                "p": "0.01633102",  // Price
                "q": "4.70443515",  // Quantity
                "f": 27781,         // First tradeId
                "l": 27781,         // Last tradeId
                "T": 1498793709153, // Timestamp
                "m": true,          // Was the buyer the maker?
                "M": true           // Was the trade the best price match?
              }
        """
        currency_pair = get_currency_pair_from_binance(pair)
        deal_timest = 0.001 * long(json_document['T'])
        deal_type = DEAL_TYPE.BUY
        if json_document['m'] is True:
            deal_type = DEAL_TYPE.SELL
        price = Decimal(json_document['p'])
        amount = Decimal(json_document['q'])
        total = price * amount
        return TradeHistory(currency_pair, deal_timest, deal_type, price, amount, total, EXCHANGE.BINANCE)

    @classmethod
    def from_huobi(cls, json_document, pair_name, timest):
        """
            {
                "status": "ok",
                "ch": "market.ethusdt.trade.detail",
                "ts": 1502448925216,
                "data": [
                    {
                        "id": 31459998,
                        "ts": 1502448920106,
                        "data": [
                            {
                                "id": 17592256642623,
                                "amount": 0.04,
                                "price": 1997,
                                "direction": "buy",
                                "ts": 1502448920106
                            }
                        ]
                    }
                ]
            }
        :param json_document:
        :param pair_name:
        :param timest:
        :return:
        """
        currency_pair = get_currency_pair_from_huobi(pair_name)
        deal_timest = 0.001 * long(json_document['ts'])
        deal_type = DEAL_TYPE.BUY
        if 'buy' not in json_document['direction']:
            deal_type = DEAL_TYPE.SELL
        price = Decimal(json_document['price'])
        amount = Decimal(json_document['amount'])
        total = price * amount
        return TradeHistory(currency_pair, deal_timest, deal_type, price, amount, total, EXCHANGE.BINANCE)

    @classmethod
    def from_string(cls, some_string):
        results = regex.findall(some_string)
        amount = Decimal(results[0][0])
        deal_type = results[0][1]
        exchange_id = results[0][3]
        currency_pair_id = results[0][5]
        price = Decimal(results[0][6])
        deal_timest = results[0][7]
        total = price * amount
        return TradeHistory(currency_pair_id, deal_timest, deal_type, price, amount, total, exchange_id)

    @classmethod
    def from_row(cls, db_row):
        currency_pair_id = db_row[1]
        exchange_id = db_row[2]
        deal_type = db_row[3]
        price = db_row[4]
        amount = db_row[5]
        total = db_row[6]
        deal_timest = db_row[7]
        return TradeHistory(currency_pair_id, deal_timest, deal_type, price, amount, total, exchange_id)

def tsv(self):
    return "{}\t{}\t{}\t{}\t{}\t{}\t{}\t'{}'".format(self.pair_id, self.exchange_id, self.deal_type, self.price, self.amount, self.total, self.timest, get_date_time_from_epoch(self.timest)).decode('utf8')

def get_pg_arg_list(self):
    return (self.pair_id, self.exchange_id, self.deal_type, self.price, self.amount, self.total, self.timest, get_date_time_from_epoch(self.timest))

class Ticker(BaseData):
    insert_query = TICKERS_INSERT_QUERY
    type = TICKER_TYPE_NAME
    table_name = TICKERS_TABLE_NAME
    columns = TICKERS_COLUMNS

    def __init__(self, pair_id, lowest_ask, highest_bid, timest, exchange_id):
        self.pair_id = int(pair_id)
        self.pair = get_pair_name_by_id(self.pair_id)
        self.ask = Decimal(lowest_ask)
        self.bid = Decimal(highest_bid)
        self.timest = long(timest)
        self.exchange_id = int(exchange_id)
        self.exchange = get_exchange_name_by_id(self.exchange_id)

    def tsv(self):
        return "{}\t{}\t{}\t{}\t{}\t'{}'".format(self.pair_id, self.exchange_id, self.ask, self.bid, self.timest, get_date_time_from_epoch(self.timest)).decode('utf8')

    def get_pg_arg_list(self):
        return (self.pair_id, self.exchange_id, self.ask, self.bid, self.timest, get_date_time_from_epoch(self.timest))

    @classmethod
    def from_poloniex(cls, pair_name, timest, json_document):
        """
        BTC_BCN":{"id": 7, "last": "0.00000047", "lowestAsk": "0.00000048", "highestBid": "0.00000047",
                   "percentChange": "-0.09615384", "baseVolume": "105.01337711", "quoteVolume": "217142084.64192474",
                   "isFrozen": "0", "high24hr": "0.00000052", "low24hr": "0.00000045"}
        """
        lowest_ask = json_document['lowestAsk']
        highest_bid = json_document['highestBid']
        currency_pair = get_currency_pair_from_poloniex(pair_name)
        return Ticker(currency_pair, lowest_ask, highest_bid, timest, EXCHANGE.POLONIEX)

    @classmethod
    def from_kraken(cls, pair_name, timest, json_document):
        """{"error":[],"result":{"DASHXBT":
        {"a":["0.06295700","1","1.000"],
        "b":["0.06230800","113","113.000"],
        "c":["0.06295700","9.74800000"],
        "v":["5894.96333766","6925.68918665"],
        "p":["0.06294513","0.06302664"],
        "t":[844,1030],
        "l":["0.06079200","0.06079200"],
        "h":["0.06488000","0.06516300"],
        "o":"0.06210000"}}}

        a = ask array(<price>, <whole lot volume>, <lot volume>),
        b = bid array(<price>, <whole lot volume>, <lot volume>),
        c = last trade closed array(<price>, <lot volume>),
        v = volume array(<today>, <last 24 hours>),
        p = volume weighted average price array(<today>, <last 24 hours>),
        t = number of trades array(<today>, <last 24 hours>),
        l = low array(<today>, <last 24 hours>),
        h = high array(<today>, <last 24 hours>),
        o = today's opening price

        """
        lowest_ask = json_document['a'][0]
        highest_bid = json_document['b'][0]
        currency_pair_id = get_currency_pair_from_kraken(pair_name)
        return Ticker(currency_pair_id, lowest_ask, highest_bid, timest, EXCHANGE.KRAKEN)

    @classmethod
    def from_bittrex(cls, pair_name, timest, json_document):
        """
            {"success":true,"message":"","result":{"Bid":0.01490996,"Ask":0.01491000,"Last":0.01490996}}
        """
        lowest_ask = json_document['Ask']
        highest_bid = json_document['Bid']
        currency_pair_id = get_currency_pair_from_bittrex(pair_name)
        return Ticker(currency_pair_id, lowest_ask, highest_bid, timest, EXCHANGE.BITTREX)

    @classmethod
    def from_binance(cls, pair_name, timest, json_document):
        lowest_ask = json_document['askPrice']
        highest_bid = json_document['bidPrice']
        currency_pair_id = get_currency_pair_from_binance(pair_name)
        return Ticker(currency_pair_id, lowest_ask, highest_bid, timest, EXCHANGE.BINANCE)

    @classmethod
    def from_huobi(cls, pair_name, timest, json_document):
        """
        {
            "status":"ok",
            "ch":"market.ethusdt.detail.merged",
            "ts":1499225276950,
            "tick":{
              "id":1499225271,
              "ts":1499225271000,
              "close":1885.0000,
              "open":1960.0000,
              "high":1985.0000,
              "low":1856.0000,
              "amount":81486.2926,
              "count":42122,
              "vol":157052744.85708200,
              "ask":[1885.0000,21.8804],
              "bid":[1884.0000,1.6702]
            }
        }

        :return:
        """
        lowest_ask = json_document['ask'][0]
        highest_bid = json_document['bid'][0]
        currency_pair_id = get_currency_pair_from_huobi(pair_name)
        return Ticker(currency_pair_id, lowest_ask, highest_bid, timest, EXCHANGE.HUOBI)

    @classmethod
    def from_string(cls, some_string):
        results = regex.findall(some_string)
        ask = results[0][0]
        bid = results[0][1]
        exchange_id = results[0][3]
        currency_pair_id = results[0][5]
        timest = results[0][6]
        return Ticker(currency_pair_id, ask, bid, timest, exchange_id)

    @classmethod
    def from_row(cls, db_row):
        exchange_id = db_row[1]
        currency_pair_id = db_row[2]
        ask = db_row[3]
        bid = db_row[4]
        timest = db_row[5]
        return Ticker(currency_pair_id, ask, bid, timest, exchange_id)

def tsv(self):
    return "{}\t{}\t{}\t{}\t{}\t'{}'".format(self.pair_id, self.exchange_id, self.ask, self.bid, self.timest, get_date_time_from_epoch(self.timest)).decode('utf8')

def get_pg_arg_list(self):
    return (self.pair_id, self.exchange_id, self.ask, self.bid, self.timest, get_date_time_from_epoch(self.timest))

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

def get_pg_arg_list(self):
    return (self.pair_id, self.exchange_id, self.timest, get_date_time_from_epoch(self.timest))

