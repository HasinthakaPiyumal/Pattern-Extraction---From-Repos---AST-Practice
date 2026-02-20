# Cluster 28

def float_to_str(f):
    """
    :param f:   Float or Decimal number
    :return: to be represented within EXACT precision as string
    NOTE: For Decimal you may end up with following numbers:
    0.0019120000000000000710265180003943896736018359661102294921875
    """
    float_string = str(f).lower()
    if 'e' in float_string:
        digits, exp = float_string.split('e')
        digits = digits.replace('.', '').replace('-', '')
        exp = int(exp)
        zero_padding = '0' * (abs(int(exp)) - 1)
        sign = '-' if f < 0 else ''
        if exp > 0:
            float_string = '{}{}{}.0'.format(sign, digits, zero_padding)
        else:
            float_string = '{}0.{}{}'.format(sign, zero_padding, digits)
    elif float_string[-2:] == '.0':
        float_string = float_string[:-2]
    return float_string

# Node: lower
# Node: replace
# Node: int
# Node: abs
def convert_to_epoch_time(some_string):
    utc_time = datetime.strptime(some_string, '%Y-%m-%d')
    epoch_time = (utc_time - datetime(1970, 1, 1)).total_seconds()
    return long(epoch_time)

# Node: strptime
# Node: total_seconds
# Node: datetime
# Node: long
def convert_to_epoch_midnight(some_string):
    utc_time = datetime.strptime(some_string, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (utc_time - datetime(1970, 1, 1)).total_seconds()
    return long(seconds_since_midnight)

def get_now_seconds_local():
    return long((datetime.now() - datetime(1970, 1, 1)).total_seconds())

# Node: now
def get_now_seconds_utc():
    return long((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

# Node: utcnow
def get_now_seconds_utc_ms():
    """
        For a long discussion what is optimal way check this:
            https://stackoverflow.com/questions/38319606/how-to-get-millisecond-and-microsecond-resolution-timestamps-in-python
            https://stackoverflow.com/questions/5998245/get-current-time-in-milliseconds-in-python/21858377#21858377
    """
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)

def get_date_time_from_epoch(ts_epoch):
    if not ts_epoch:
        raise Exception('get_date_time_from_epoch - empty date? - {}'.format(ts_epoch))
    return datetime.fromtimestamp(1.0 * long(ts_epoch))

# Node: Exception
# Node: fromtimestamp
def parse_time(time_string, regex_string):
    utc_time = datetime.strptime(time_string, regex_string)
    epoch_time = (utc_time - datetime(1970, 1, 1)).total_seconds()
    return long(epoch_time)

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

# Node: get_pair_name_by_id
# Node: Decimal
@classmethod
def from_poloniex(cls, json_document, currency):
    timest = json_document['date']
    price_high = json_document['high']
    price_low = json_document['low']
    price_open = json_document['open']
    price_close = json_document['close']
    currency_pair = get_currency_pair_from_poloniex(currency)
    return Candle(currency_pair, timest, price_high, price_low, price_open, price_close, EXCHANGE.POLONIEX)

# Node: get_currency_pair_from_poloniex
# Node: Candle
@classmethod
def from_kraken(cls, json_document, currency):
    timest = json_document[0]
    price_high = json_document[2]
    price_low = json_document[3]
    price_open = json_document[1]
    price_close = json_document[4]
    currency_pair = get_currency_pair_from_kraken(currency)
    return Candle(currency_pair, timest, price_high, price_low, price_open, price_close, EXCHANGE.KRAKEN)

# Node: get_currency_pair_from_kraken
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

# Node: get_currency_pair_from_bittrex
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

# Node: get_currency_pair_from_binance
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

# Node: get_currency_pair_from_huobi
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

# Node: findall
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

# Node: TradeHistory
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

def __init__(self, pair_id, lowest_ask, highest_bid, timest, exchange_id):
    self.pair_id = int(pair_id)
    self.pair = get_pair_name_by_id(self.pair_id)
    self.ask = Decimal(lowest_ask)
    self.bid = Decimal(highest_bid)
    self.timest = long(timest)
    self.exchange_id = int(exchange_id)
    self.exchange = get_exchange_name_by_id(self.exchange_id)

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

# Node: Ticker
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

class Trade(Deal):

    def __init__(self, trade_type, exchange_id, pair_id, price, volume, order_book_time, create_time, execute_time=None, order_id=None, trade_id=None, executed_volume=None, arbitrage_id=-13):
        Deal.__init__(self, price, volume)
        self.trade_type = int(trade_type)
        self.exchange_id = int(exchange_id)
        self.pair_id = int(pair_id)
        self.order_book_time = long(order_book_time)
        self.create_time = long(create_time)
        self.execute_time = long(execute_time) if execute_time is not None else execute_time
        self.order_id = order_id
        self.trade_id = trade_id
        self.executed_volume = Decimal(executed_volume) if executed_volume is not None else executed_volume
        self.arbitrage_id = long(arbitrage_id)

    def __str__(self):
        str_repr = '\n        Trade at Exchange: {exch}\n        Type: {deal_type}\n        Pair: {pair} for volume {vol} with price {price}\n        order_book_time {ob_time} create_time {ct_time} execute_time {ex_time}\n        Executed at: {dt}\n        order_id {order_id} trade_id {trade_id} executed_volume {ex_volume}\n        arbitrage_id {a_id}\n        '.format(exch=get_exchange_name_by_id(self.exchange_id), deal_type=get_order_type_by_id(self.trade_type), pair=get_pair_name_by_id(self.pair_id), vol=truncate_float(self.volume, 8), price=truncate_float(self.price, 8), ob_time=self.order_book_time, ct_time=self.create_time, ex_time=self.execute_time, dt=ts_to_string_local(self.execute_time), order_id=self.order_id, trade_id=self.trade_id, ex_volume=self.executed_volume, a_id=self.arbitrage_id)
        return str_repr

    def __cmp__(self, other):
        return self.__eq__(other)

    def __eq__(self, other):
        if get_logging_level() >= LOG_ALL_DEBUG:
            msg = 'compare {u} with {b}'.format(u=self, b=other)
            log_to_file(msg, 'expire_deal.log')
        if other is None:
            return False
        return self.order_id == other.order_id and self.trade_type == other.trade_type and (self.exchange_id == other.exchange_id) and (self.pair_id == other.pair_id)

    def set_order_id(self, order_id):
        self.order_id = order_id

    @classmethod
    def get_fields(cls):
        return ('arbitrage_id', 'exchange_id', 'pair_id', 'trade_type', 'price', 'volume', 'order_book_time', 'create_time', 'execute_time', 'execute_datetime', 'order_id', 'executed_volume')

    def __iter__(self):
        return iter([self.arbitrage_id, get_exchange_name_by_id(self.exchange_id), get_pair_name_by_id(self.pair_id), get_order_type_by_id(self.trade_type), self.price, self.volume, self.order_book_time, self.create_time, self.execute_time, ts_to_string_local(self.execute_time), self.order_id, self.trade_id, self.executed_volume])

    @classmethod
    def from_kraken(cls, order_id, json_doc):
        """
        "OMO3YX-5HSZM-26CQ36": {
            "status": "open",
            "fee": "0.000000",
            "expiretm": 0,
                "descr": {
                    "leverage": "none",
                    "ordertype": "limit",
                    "price": "0.003310",
                    "pair": "REPXBT",
                    "price2": "0",
                    "type": "sell",
                    "order": "sell 349.78000000 REPXBT @ limit 0.003310"
                },
                "vol": "349.78000000",
                "cost": "0.000000",
                "misc": "",
                "price": "0.000000",
                "starttm": 0,
                "userref": null,
                "vol_exec": "0.00000000",
                "oflags": "fciq",
                "refid": null,
                "opentm": 1509591188.429
        }
        """
        price = json_doc['descr']['price']
        volume = json_doc['vol']
        executed_volume = json_doc['vol_exec']
        create_time = json_doc['opentm']
        order_book_time = create_time
        trade_type_str = json_doc['descr']['type']
        trade_type = DEAL_TYPE.BUY
        if 'sell' in trade_type_str:
            trade_type = DEAL_TYPE.SELL
        pair_name = json_doc['descr']['pair']
        pair_id = get_currency_pair_from_kraken(pair_name)
        if pair_id is None:
            msg = 'Trade.from_kraken - unsupported pair_name - {n}'.format(n=pair_name)
            print_to_console(msg, LOG_ALL_ERRORS)
            log_to_file(msg, ERROR_LOG_FILE_NAME)
            return None
        return Trade(trade_type, EXCHANGE.KRAKEN, pair_id, price, volume, order_book_time, create_time, execute_time=create_time, order_id=order_id, trade_id=order_id, executed_volume=executed_volume)

    @classmethod
    def from_binance(cls, json_document):
        """
        {u'orderId': 3542537,
        u'clientOrderId': u'L0LbifBNp65Gy2BWTNOOYR',
        u'origQty': u'50.00000000',
        u'icebergQty': u'0.00000000',
        u'symbol': u'XMRBTC',
        u'side': u'SELL',
        u'timeInForce': u'GTC',
        u'status': u'NEW',
        u'stopPrice': u'0.01981500',
        u'time': 1514321524235,
        u'isWorking': False,
        u'type': u'STOP_LOSS_LIMIT',
        u'price': u'0.01975600',
        u'executedQty': u'0.00000000'}
        """
        pair_id = get_currency_pair_from_binance(json_document['symbol'])
        if pair_id is None:
            msg = 'Trade.from_binance - unsupported pair_name - {n}'.format(n=json_document['symbol'])
            print_to_console(msg, LOG_ALL_ERRORS)
            log_to_file(msg, 'error.log')
            return None
        timest = 0.001 * long(json_document['time'])
        price = json_document['price']
        volume = json_document['origQty']
        trade_type = DEAL_TYPE.BUY
        if 'SELL' in json_document['side']:
            trade_type = DEAL_TYPE.SELL
        order_id = json_document['orderId']
        executed_volume = json_document['executedQty']
        return Trade(trade_type, EXCHANGE.BINANCE, pair_id, price, volume, timest, timest, execute_time=timest, order_id=order_id, trade_id=order_id, executed_volume=executed_volume)

    @classmethod
    def from_binance_history(cls, json_document, pair_name):
        """
            u'orderId': 7632926,
            u'isBuyer': False,
            u'price': u'0.00933400',
            u'isMaker': False,
            u'qty': u'14.95000000',
            u'commission': u'0.00013954',
            u'time': 1520011967196,
            u'commissionAsset': u'ETH',
            u'id': 346792,
            u'isBestMatch': True

        :param json_document:
        :return:
        """
        pair_id = get_currency_pair_from_binance(pair_name)
        if pair_id is None:
            msg = 'Trade.from_binance - unsupported pair_name - {n}'.format(n=json_document['symbol'])
            print_to_console(msg, LOG_ALL_ERRORS)
            log_to_file(msg, 'error.log')
            return None
        timest = 0.001 * long(json_document['time'])
        price = json_document['price']
        volume = json_document['qty']
        trade_type = DEAL_TYPE.BUY
        if not json_document['isBuyer']:
            trade_type = DEAL_TYPE.SELL
        order_id = json_document['orderId']
        trade_id = json_document['id']
        executed_volume = volume
        return Trade(trade_type, EXCHANGE.BINANCE, pair_id, price, volume, timest, timest, execute_time=timest, order_id=order_id, trade_id=trade_id, executed_volume=executed_volume)

    @classmethod
    def from_bittrex(cls, json_document):
        """
        {u'OrderUuid': u'262a63f5-b901-4efb-b0fb-b6f2f6d203ea',
        u'QuantityRemaining': 8500.0,
        u'IsConditional': False,
        u'ImmediateOrCancel': False,
        u'Uuid': None,
        u'Exchange': u'BTC-GRS',
        u'OrderType': u'LIMIT_BUY',
        u'Price': 0.0,
        u'CommissionPaid': 0.0,
        u'Opened': u'2017-12-26T20:22:41.07',
        u'Limit': 8.969e-05,
        u'Closed': None,
        u'ConditionTarget': None,
        u'CancelInitiated': False,
        u'PricePerUnit': None,
        u'Condition': u'NONE',
        u'Quantity': 8500.0}
        """
        pair_id = get_currency_pair_from_bittrex(json_document['Exchange'])
        if pair_id is None:
            msg = 'Trade.from_bittrex - unsupported pair_name - {n}'.format(n=json_document['Exchange'])
            print_to_console(msg, LOG_ALL_ERRORS)
            log_to_file(msg, 'error.log')
            return None
        try:
            timest = parse_time(json_document['Opened'], '%Y-%m-%dT%H:%M:%S.%f')
        except:
            timest = parse_time(json_document['Opened'], '%Y-%m-%dT%H:%M:%S')
        price = json_document['Limit']
        volume = Decimal(json_document['Quantity'])
        trade_type = DEAL_TYPE.BUY
        if 'SELL' in json_document['OrderType']:
            trade_type = DEAL_TYPE.SELL
        trade_id = json_document['OrderUuid']
        executed_volume = volume - Decimal(json_document['QuantityRemaining'])
        return Trade(trade_type, EXCHANGE.BITTREX, pair_id, price, volume, timest, timest, execute_time=timest, order_id=trade_id, executed_volume=executed_volume)

    @classmethod
    def from_bittrex_history(cls, json_document):
        """
        {
           u'OrderUuid':u'b9f52a13-571f-4560-91af-a52f0c0c3f1f',
           u'QuantityRemaining':0.0,
           u'ImmediateOrCancel':False,
           u'IsConditional':False,
           u'Exchange':u'BTC-STRAT',
           u'TimeStamp':   u'2018-02-07T19:50:03.01   ', u'   Price':0.00440505,
           u'ConditionTarget':None,
           u'Commission':1.101e-05,
           u'Limit':0.00088101,
           u'Closed':   u'2018-02-08T13:25:55.133   ', u'   OrderType':u'LIMIT_SELL',
           u'PricePerUnit':0.00088101,
           u'Condition':u'NONE',
           u'Quantity':5.0
        }

        :param json_document:
        :return:
        """
        order_id = json_document['OrderUuid']
        pair_id = get_currency_pair_from_bittrex(json_document['Exchange'])
        if pair_id is None:
            msg = 'Trade.from_bittrex - unsupported pair_name - {n}'.format(n=json_document['Exchange'])
            print_to_console(msg, LOG_ALL_ERRORS)
            log_to_file(msg, 'error.log')
            return None
        try:
            timest = parse_time(json_document['TimeStamp'], '%Y-%m-%dT%H:%M:%S.%f')
        except:
            timest = parse_time(json_document['TimeStamp'], '%Y-%m-%dT%H:%M:%S')
        try:
            execute_timest = parse_time(json_document['Closed'], '%Y-%m-%dT%H:%M:%S.%f')
        except:
            execute_timest = parse_time(json_document['Closed'], '%Y-%m-%dT%H:%M:%S')
        trade_type = DEAL_TYPE.BUY
        if 'SELL' in json_document['OrderType']:
            trade_type = DEAL_TYPE.SELL
        price = json_document['PricePerUnit']
        volume = Decimal(json_document['Quantity'])
        executed_volume = volume - Decimal(json_document['QuantityRemaining'])
        return Trade(trade_type, EXCHANGE.BITTREX, pair_id, price, volume, order_book_time=timest, create_time=timest, execute_time=execute_timest, order_id=order_id, trade_id=order_id, executed_volume=executed_volume)

    @classmethod
    def from_poloniex(cls, json_document, pair_name):
        """
        {u'orderNumber': u'22641967545',
        u'margin': 0,
        u'amount': u'10000.00000000',
        u'rate': u'0.00014568',
        u'date': u'2017-12-27 20:29:56',
        u'total': u'1.45680000',
        u'type': u'sell',
        u'startingAmount': u'10000.00000000'}
        """
        pair_id = get_currency_pair_from_poloniex(pair_name)
        if pair_id is None:
            msg = 'Trade.from_poloniex - unsupported pair_name - {n}'.format(n=pair_name)
            print_to_console(msg, LOG_ALL_ERRORS)
            log_to_file(msg, ERROR_LOG_FILE_NAME)
            return None
        timest = parse_time(json_document['date'], '%Y-%m-%d %H:%M:%S')
        price = json_document['rate']
        volume = Decimal(json_document['startingAmount'])
        trade_type = DEAL_TYPE.BUY
        if 'sell' in json_document['type']:
            trade_type = DEAL_TYPE.SELL
        order_id = json_document['orderNumber']
        executed_volume = volume - Decimal(json_document['amount'])
        return Trade(trade_type, EXCHANGE.POLONIEX, pair_id, price, volume, timest, timest, execute_time=timest, order_id=order_id, trade_id=order_id, executed_volume=executed_volume)

    @classmethod
    def from_poloniex_history(cls, json_document, pair_name):
        """
        { "globalTradeID": 25129732,
        "tradeID": "6325758",
        "date": "2016-04-05 08:08:40",
         "rate": "0.02565498",
         "amount": "0.10000000",
         "total": "0.00256549",
         "fee": "0.00200000",
         "orderNumber": "34225313575",
         "type": "sell",
         "category": "exchange" }
        :return:
        """
        pair_id = get_currency_pair_from_poloniex(pair_name)
        trade_type = DEAL_TYPE.BUY
        if 'sell' in json_document['type']:
            trade_type = DEAL_TYPE.SELL
        order_id = json_document['orderNumber']
        trade_id = json_document['tradeID']
        timest = parse_time(json_document['date'], '%Y-%m-%d %H:%M:%S')
        price = json_document['rate']
        volume = Decimal(json_document['amount'])
        return Trade(trade_type, EXCHANGE.POLONIEX, pair_id, price, volume, timest, timest, execute_time=timest, order_id=order_id, trade_id=trade_id, executed_volume=volume)

    @classmethod
    def from_huobi(cls, json_document, pair_name):
        """
            06.04.2018 NOTE - no filled amount, have to use special method to retrieve this data

            "id": 59378,
            "symbol": "ethusdt",
            "account-id": 100009,
            "amount": "10.1000000000",
            "price": "100.1000000000",
            "created-at": 1494901162595,
            "type": "buy-limit",
            "field-amount": "10.1000000000",
            "field-cash-amount": "1011.0100000000",
            "field-fees": "0.0202000000",
            "finished-at": 1494901400468,
            "user-id": 1000,
            "source": "api",
            "state": "filled",
            "canceled-at": 0,
            "exchange": "huobi",
            "batch": ""
        :return:
        """
        pair_id = get_currency_pair_from_huobi(pair_name)
        trade_type = DEAL_TYPE.BUY
        if 'sell' in json_document['type']:
            trade_type = DEAL_TYPE.SELL
        order_id = str(json_document['id'])
        trade_id = json_document['id']
        create_timest = 0.001 * long(json_document['created-at'])
        executed_timest = 0.001 * long(json_document['finished-at'])
        price = json_document['price']
        volume = Decimal(json_document['amount'])
        executed_volume = Decimal(json_document['field-amount'])
        return Trade(trade_type, EXCHANGE.HUOBI, pair_id, price, volume, create_timest, create_timest, execute_time=executed_timest, order_id=order_id, trade_id=trade_id, executed_volume=executed_volume)

    @classmethod
    def from_row(cls, db_row):
        """
        row order:
        arbitrage_id, exchange_id, trade_type, pair_id, price, volume, executed_volume, order_id, trade_id,
        order_book_time, create_time, execute_time

        2, 4, 2, 11, 0.001554, 2.0, None, '9103224', 151612795
        :param row:
        :return:
        """
        arbitrage_id = db_row[0]
        exchange_id = db_row[1]
        trade_type = db_row[2]
        pair_id = db_row[3]
        price = db_row[4]
        volume = Decimal(db_row[5])
        executed_volume = db_row[6]
        order_id = db_row[7]
        trade_id = db_row[8]
        order_book_time = db_row[9]
        create_time = db_row[10]
        execute_time = db_row[11]
        res = Trade(trade_type, exchange_id, pair_id, price, volume, order_book_time, create_time, execute_time, order_id, trade_id, executed_volume, arbitrage_id)
        return res

    @classmethod
    def from_bittrex_scv(cls, row):
        """
            Export from bittrex history:


            OrderUuid, 8269d382-b7f6-4ac2-9e7f-33ce45887b72,
            Exchange, BTC-XRP,
            Type, LIMIT_BUY,
            Quantity, 478.7867564,
            Limit, 0.00002155,
            CommissionPaid, 0.00002579,
            Price, 0.01031785,
            Opened, 12/4/2017 4:02:43 AM,
            Closed 12/4/2017 4:05:11 AM

        """
        order_id = row[0]
        pair_id = get_currency_pair_from_bittrex(row[1])
        trade_type = DEAL_TYPE.BUY
        if 'SELL' in row[2]:
            trade_type = DEAL_TYPE.SELL
        volume = Decimal(row[3])
        price = Decimal(row[5])
        arbitrage_id = -50
        exchange_id = EXCHANGE.BITTREX
        executed_volume = row[6]
        trade_id = row[8]
        order_book_time = row[9]
        create_time = row[10]
        execute_time = row[11]
        res = Trade(trade_type, exchange_id, pair_id, price, volume, order_book_time, create_time, execute_time, order_id, trade_id, executed_volume, arbitrage_id)
        return res

def __init__(self, trade_type, exchange_id, pair_id, price, volume, order_book_time, create_time, execute_time=None, order_id=None, trade_id=None, executed_volume=None, arbitrage_id=-13):
    Deal.__init__(self, price, volume)
    self.trade_type = int(trade_type)
    self.exchange_id = int(exchange_id)
    self.pair_id = int(pair_id)
    self.order_book_time = long(order_book_time)
    self.create_time = long(create_time)
    self.execute_time = long(execute_time) if execute_time is not None else execute_time
    self.order_id = order_id
    self.trade_id = trade_id
    self.executed_volume = Decimal(executed_volume) if executed_volume is not None else executed_volume
    self.arbitrage_id = long(arbitrage_id)

# Node: __init__
def __str__(self):
    str_repr = '\n        Trade at Exchange: {exch}\n        Type: {deal_type}\n        Pair: {pair} for volume {vol} with price {price}\n        order_book_time {ob_time} create_time {ct_time} execute_time {ex_time}\n        Executed at: {dt}\n        order_id {order_id} trade_id {trade_id} executed_volume {ex_volume}\n        arbitrage_id {a_id}\n        '.format(exch=get_exchange_name_by_id(self.exchange_id), deal_type=get_order_type_by_id(self.trade_type), pair=get_pair_name_by_id(self.pair_id), vol=truncate_float(self.volume, 8), price=truncate_float(self.price, 8), ob_time=self.order_book_time, ct_time=self.create_time, ex_time=self.execute_time, dt=ts_to_string_local(self.execute_time), order_id=self.order_id, trade_id=self.trade_id, ex_volume=self.executed_volume, a_id=self.arbitrage_id)
    return str_repr

# Node: get_order_type_by_id
# Node: ts_to_string_local
def __iter__(self):
    return iter([self.arbitrage_id, get_exchange_name_by_id(self.exchange_id), get_pair_name_by_id(self.pair_id), get_order_type_by_id(self.trade_type), self.price, self.volume, self.order_book_time, self.create_time, self.execute_time, ts_to_string_local(self.execute_time), self.order_id, self.trade_id, self.executed_volume])

# Node: iter
@classmethod
def from_huobi(cls, json_document, pair_name):
    """
            06.04.2018 NOTE - no filled amount, have to use special method to retrieve this data

            "id": 59378,
            "symbol": "ethusdt",
            "account-id": 100009,
            "amount": "10.1000000000",
            "price": "100.1000000000",
            "created-at": 1494901162595,
            "type": "buy-limit",
            "field-amount": "10.1000000000",
            "field-cash-amount": "1011.0100000000",
            "field-fees": "0.0202000000",
            "finished-at": 1494901400468,
            "user-id": 1000,
            "source": "api",
            "state": "filled",
            "canceled-at": 0,
            "exchange": "huobi",
            "batch": ""
        :return:
        """
    pair_id = get_currency_pair_from_huobi(pair_name)
    trade_type = DEAL_TYPE.BUY
    if 'sell' in json_document['type']:
        trade_type = DEAL_TYPE.SELL
    order_id = str(json_document['id'])
    trade_id = json_document['id']
    create_timest = 0.001 * long(json_document['created-at'])
    executed_timest = 0.001 * long(json_document['finished-at'])
    price = json_document['price']
    volume = Decimal(json_document['amount'])
    executed_volume = Decimal(json_document['field-amount'])
    return Trade(trade_type, EXCHANGE.HUOBI, pair_id, price, volume, create_timest, create_timest, execute_time=executed_timest, order_id=order_id, trade_id=trade_id, executed_volume=executed_volume)

@classmethod
def from_row(cls, db_row):
    """
        row order:
        arbitrage_id, exchange_id, trade_type, pair_id, price, volume, executed_volume, order_id, trade_id,
        order_book_time, create_time, execute_time

        2, 4, 2, 11, 0.001554, 2.0, None, '9103224', 151612795
        :param row:
        :return:
        """
    arbitrage_id = db_row[0]
    exchange_id = db_row[1]
    trade_type = db_row[2]
    pair_id = db_row[3]
    price = db_row[4]
    volume = Decimal(db_row[5])
    executed_volume = db_row[6]
    order_id = db_row[7]
    trade_id = db_row[8]
    order_book_time = db_row[9]
    create_time = db_row[10]
    execute_time = db_row[11]
    res = Trade(trade_type, exchange_id, pair_id, price, volume, order_book_time, create_time, execute_time, order_id, trade_id, executed_volume, arbitrage_id)
    return res

@classmethod
def from_bittrex_scv(cls, row):
    """
            Export from bittrex history:


            OrderUuid, 8269d382-b7f6-4ac2-9e7f-33ce45887b72,
            Exchange, BTC-XRP,
            Type, LIMIT_BUY,
            Quantity, 478.7867564,
            Limit, 0.00002155,
            CommissionPaid, 0.00002579,
            Price, 0.01031785,
            Opened, 12/4/2017 4:02:43 AM,
            Closed 12/4/2017 4:05:11 AM

        """
    order_id = row[0]
    pair_id = get_currency_pair_from_bittrex(row[1])
    trade_type = DEAL_TYPE.BUY
    if 'SELL' in row[2]:
        trade_type = DEAL_TYPE.SELL
    volume = Decimal(row[3])
    price = Decimal(row[5])
    arbitrage_id = -50
    exchange_id = EXCHANGE.BITTREX
    executed_volume = row[6]
    trade_id = row[8]
    order_book_time = row[9]
    create_time = row[10]
    execute_time = row[11]
    res = Trade(trade_type, exchange_id, pair_id, price, volume, order_book_time, create_time, execute_time, order_id, trade_id, executed_volume, arbitrage_id)
    return res

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

def __init__(self, price, volume):
    self.price = Decimal(str(price))
    self.volume = Decimal(str(volume))

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

def __init__(self, pair_id, timest, sell_bids, buy_bids, exchange_id, sequence_id=None):
    self.pair_id = int(pair_id)
    self.pair_name = get_pair_name_by_id(self.pair_id)
    self.timest = timest
    self.ask = sell_bids
    self.bid = buy_bids
    self.exchange_id = int(exchange_id)
    self.exchange = get_exchange_name_by_id(self.exchange_id)
    self.sequence_id = sequence_id

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

# Node: Deal
# Node: OrderBook
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

class ArbitrageConfig:

    def __init__(self, sell_exchange_id, buy_exchange_id, pair_id, threshold, reverse_threshold, balance_threshold, deal_expire_timeout, cfg_file_name, cap_update_timeout=MIN_CAP_UPDATE_TIMEOUT, balance_update_timeout=BALANCE_UPDATE_TIMEOUT):
        self.threshold = threshold
        self.reverse_threshold = reverse_threshold
        self.balance_threshold = balance_threshold
        self.sell_exchange_id = sell_exchange_id
        self.buy_exchange_id = buy_exchange_id
        self.pair_id = pair_id
        self.deal_expire_timeout = deal_expire_timeout
        self.cfg_file_name = cfg_file_name
        self.log_file_name = self._generate_file_name()
        self.cap_update_timeout = cap_update_timeout
        self.balance_update_timeout = balance_update_timeout

    @staticmethod
    def from_args(arguments):
        return ArbitrageConfig(arguments.sell_exchange_id, arguments.buy_exchange_id, arguments.pair_id, arguments.threshold, arguments.reverse_threshold, arguments.balance_threshold, arguments.deal_expire_timeout, arguments.cfg)

    def __str__(self):
        str_repr = 'Sell=Bid exchange - {sell_exch} id = {id1} Buy-Ask exchange - {buy_exch} id = {id2} \n        currency pair - {pair} Arbitrage Threshold = {thrshld} Reverse Threshold = {rv_thr} Balance Threshold = {b_thr}\n        deal_expire_timeout = {deal_expire_timeout}\n        cfg_file_name = {cfg_file_name}\n        log_file_name = {log_file_name}\n        cap_update_timeout = {cap_update_timeout}\n        balance_update_timeout = {balance_update_timeout}\n        '.format(sell_exch=get_exchange_name_by_id(self.sell_exchange_id), id1=self.sell_exchange_id, buy_exch=get_exchange_name_by_id(self.buy_exchange_id), id2=self.buy_exchange_id, pair=get_pair_name_by_id(self.pair_id), pair_id=self.pair_id, thrshld=self.threshold, rv_thr=self.reverse_threshold, b_thr=self.balance_threshold, cfg_file_name=get_debug_level_name_by_id(self.cfg_file_name), deal_expire_timeout=self.deal_expire_timeout, log_file_name=self.log_file_name, cap_update_timeout=self.cap_update_timeout, balance_update_timeout=self.balance_update_timeout)
        return str_repr

    def _generate_file_name(self):
        return '{sell_exch}==>{buy_exch}-{pair_name}.log'.format(sell_exch=get_exchange_name_by_id(self.sell_exchange_id), buy_exch=get_exchange_name_by_id(self.buy_exchange_id), pair_name=get_pair_name_by_id(self.pair_id))

    def generate_window_name(self):
        window_name = '{pair_id} - {pair_name}'.format(pair_id=self.pair_id, pair_name=get_pair_name_by_id(self.pair_id))
        return window_name

    def generate_command(self, full_path_to_script):
        cmd = '{cmd} --threshold {threshold} --reverse_threshold {reverse_threshold} --balance_threshold {balance_threshold} --sell_exchange_id {sell_exchange_id} --buy_exchange_id {buy_exchange_id} --pair_id {pair_id} --deal_expire_timeout {deal_expire_timeout} --cfg {cfg}'.format(cmd=full_path_to_script, threshold=self.threshold, reverse_threshold=self.reverse_threshold, balance_threshold=self.balance_threshold, sell_exchange_id=self.sell_exchange_id, buy_exchange_id=self.buy_exchange_id, pair_id=self.pair_id, deal_expire_timeout=self.deal_expire_timeout, cfg=self.cfg_file_name)
        return cmd

def generate_window_name(self):
    window_name = '{pair_id} - {pair_name}'.format(pair_id=self.pair_id, pair_name=get_pair_name_by_id(self.pair_id))
    return window_name

class TradePair(BaseData):

    def __init__(self, deal_1, deal_2, timest_1, timest_2, deal_type):
        self.deal_1 = deal_1
        self.deal_2 = deal_2
        self.id = get_next_id()
        self.timest1 = timest_1
        self.timest2 = timest_2
        self.deal_type = deal_type
        self.current_profit = self.compute_profit(self.deal_1, self.deal_2)

    def __str__(self):
        str_repr = 'Trade #{num} at timest1: {timest1} timest2: {timest2} type: {type}\n        {deal1}\n        {deal2}\n        Current profit - {bakshish}\n        '.format(num=self.id, timest1=self.timest1, timest2=self.timest2, type=get_order_type_by_id(self.deal_type), deal1=str(self.deal_1), deal2=str(self.deal_2), bakshish=float_to_str(self.current_profit))
        return str_repr

    @staticmethod
    def compute_profit(deal_1, deal_2):
        return deal_1.volume * deal_1.price * Decimal(0.01 * (100 - get_fee_by_exchange(deal_1.exchange_id))) - deal_2.volume * deal_2.price * Decimal(0.01 * (100 + get_fee_by_exchange(deal_2.exchange_id)))

@staticmethod
def compute_profit(deal_1, deal_2):
    return deal_1.volume * deal_1.price * Decimal(0.01 * (100 - get_fee_by_exchange(deal_1.exchange_id))) - deal_2.volume * deal_2.price * Decimal(0.01 * (100 + get_fee_by_exchange(deal_2.exchange_id)))

# Node: get_fee_by_exchange
def parse_socket_order_book_poloniex(order_book_snapshot, pair_id):
    """

    :param order_book_snapshot:

    [
        <channel id>,
        <sequence number>,
        [
            [
                "i",
                    {
                        "currencyPair": "<currency pair name>",
                        "orderBook": [
                        {
                            "<lowest ask price>": "<lowest ask size>",
                            "<next ask price>": "<next ask size>",
                            …
                        },
                        {
                            "<highest bid price>": "<highest bid size>",
                            "<next bid price>": "<next bid size>",
                            …
                        }
                        ]
                    }
            ]
        ]
    ]


    order_book_snapshot[2][0][1]["orderBook"][0]

    Example:
    [
        148,
        573963482,
        [
            [
                "i",
                {
                    "currencyPair": "BTC_ETH",
                    "orderBook": [
                    {
                        "0.08964203": "0.00225904",
                        "0.04069708": "15.37598559",
                        ...
                    },
                     {
                        "0.03496358": "0.32591524",
                        "0.02020000": "0.50000000",
                        ...
                    }
                    ]
                }
            ]
        ]
    ]

    :param pair_id:
    :return:
    """
    timest_ms = get_now_seconds_utc_ms()
    sequence_id = long(order_book_snapshot[1])
    asks = []
    for k, v in order_book_snapshot[2][0][1]['orderBook'][0].iteritems():
        asks.append(Deal(k, v))
    bids = []
    for k, v in order_book_snapshot[2][0][1]['orderBook'][1].iteritems():
        bids.append(Deal(k, v))
    return OrderBook(pair_id, timest_ms, asks, bids, EXCHANGE.POLONIEX, sequence_id)

# Node: iteritems
def parse_socket_update_huobi(order_book_delta, pair_id):
    if 'tick' not in order_book_delta:
        return None
    order_book_delta = order_book_delta['tick']
    sequence_id = long(order_book_delta['version'])
    asks = [Deal(price=b[0], volume=b[1]) for b in order_book_delta.get('asks', [])]
    bids = [Deal(price=b[0], volume=b[1]) for b in order_book_delta.get('bids', [])]
    timest_ms = get_now_seconds_utc_ms()
    return OrderBook(pair_id, timest_ms, asks, bids, EXCHANGE.HUOBI, sequence_id)

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

def __init__(self, cfg, app_settings):
    ArbitrageWrapper.__init__(self, cfg)
    self._init_infrastructure(app_settings)

# Node: _init_infrastructure
def init_order_books(self):
    cur_timest_sec = get_now_seconds_utc()
    self.order_book_sell = OrderBook(self.pair_id, cur_timest_sec, sell_bids=[], buy_bids=[], exchange_id=self.sell_exchange_id)
    self.order_book_buy = OrderBook(self.pair_id, cur_timest_sec, sell_bids=[], buy_bids=[], exchange_id=self.buy_exchange_id)

def stop_screen(screen_name):
    screen_pid = re.findall('\\d*\\.', commands.getoutput('screen -ls |grep %s' % screen_name))
    if screen_pid:
        commands.getoutput('kill %s' % screen_pid[0][:-1])

def compute_time_key(timest, rounding_interval):
    return rounding_interval * long(timest / rounding_interval)

def get_change(current, previous, provide_abs=True):
    """

    :param provide_abs:
    :param current:
    :param previous:
    :return: difference in percentage between current & previous
    """
    tot = Decimal(0.5) * Decimal(current + previous)
    if provide_abs:
        diff = Decimal(abs(current - previous))
    else:
        diff = Decimal(current - previous)
    percent = 0.001
    if tot != 0:
        z = diff / tot
        if z > 0.001:
            percent = truncate_float(z * 100, 2)
    return percent

