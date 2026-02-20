# Cluster 1

def group_by_pair_and_arbitrage_id(order_list):
    res = defaultdict(list)
    tmp = defaultdict(list)
    for entry in order_list:
        tmp[str(entry.volume)].append(entry)
    for arbitrage_id in tmp:
        if len(tmp[arbitrage_id]) != 2:
            log_to_file('NOT FOUND deals for volume {a_id}'.format(a_id=arbitrage_id), 'what_we_have_at_the_end.log')
        else:
            deal_1, deal_2 = tmp[arbitrage_id]
            if deal_1.trade_type == DEAL_TYPE.SELL:
                res[deal_1.pair_id].append((deal_1, deal_2))
            else:
                res[deal_1.pair_id].append((deal_2, deal_1))
    return res

# Node: defaultdict
# Node: append
# Node: log_to_file
# Node: format
def group_orders_by_arbitrage_id(order_list):
    res = defaultdict(list)
    for x in order_list:
        res[x.arbitrage_id].append(x)
    return res

def find_corresponding_trades(deal_from_bot, trade_history):
    res = []
    tot_volume = 0.0
    if deal_from_bot.exchange_id in [EXCHANGE.BITTREX, EXCHANGE.POLONIEX]:
        if deal_from_bot.pair_id in trade_history:
            res = [x for x in trade_history[deal_from_bot.pair_id] if x.order_id == deal_from_bot.order_id]
        else:
            log_to_file('NOT FOUND deal in history for {a_id}'.format(a_id=deal_from_bot), 'what_we_have_at_the_end.log')
    elif deal_from_bot.exchange_id == EXCHANGE.BINANCE:
        if deal_from_bot.pair_id in trade_history:
            for trade in trade_history[deal_from_bot.pair_id]:
                if trade.trade_type == deal_from_bot.trade_type and 0 < deal_from_bot.execute_time - trade.execute_time < 2 and (deal_from_bot.volume >= tot_volume):
                    tot_volume += trade.volume
                    res.append(trade)
        if not res:
            log_to_file('NOT FOUND deal in history for {a_id}'.format(a_id=deal_from_bot), 'what_we_have_at_the_end.log')
    else:
        assert False
    return res

def group_by_pair_and_exchange_id(history_orders):
    orders_by_exchange_and_pair = defaultdict(defaultdict(list))
    for entry in history_orders:
        orders_by_exchange_and_pair[entry.exchange_id][entry.pair_id].append(entry)
    return orders_by_exchange_and_pair

def group_by_pair_id(binance_trades):
    res = defaultdict(list)
    for entry in binance_trades:
        res[entry.pair_id].append(entry)
    return res

class LossDetails:

    def __init__(self, base_currency_id, dst_currency_id, pair_id, loss_in_coin, loss_in_base_currency):
        self.base_currency_id = base_currency_id
        self.dst_currency_id = dst_currency_id
        self.pair_id = pair_id
        self.loss_in_coin = loss_in_coin
        self.loss_in_base_currency = loss_in_base_currency

    def __str__(self):
        return 'Loss in {coin_name}: {profit_coin} Loss in {base_name}: {profit_base} '.format(coin_name=get_currency_name_by_id(self.dst_currency_id), profit_coin=float_to_str(self.loss_in_coin), base_name=get_currency_name_by_id(self.base_currency_id), profit_base=float_to_str(self.loss_in_base_currency))

def __str__(self):
    return 'Loss in {coin_name}: {profit_coin} Loss in {base_name}: {profit_base} '.format(coin_name=get_currency_name_by_id(self.dst_currency_id), profit_coin=float_to_str(self.loss_in_coin), base_name=get_currency_name_by_id(self.base_currency_id), profit_base=float_to_str(self.loss_in_base_currency))

# Node: get_currency_name_by_id
# Node: float_to_str
class ProfitDetails:

    def __init__(self, base_currency_id, dst_currency_id, pair_id, profit_in_coin, profit_in_base_currency):
        self.base_currency_id = base_currency_id
        self.dst_currency_id = dst_currency_id
        self.pair_id = pair_id
        self.profit_in_coin = profit_in_coin
        self.profit_in_base_currency = profit_in_base_currency

    def __str__(self):
        return 'Profit in {coin_name}: {profit_coin} Profit in {base_name}: {profit_base} '.format(coin_name=get_currency_name_by_id(self.dst_currency_id), profit_coin=float_to_str(self.profit_in_coin), base_name=get_currency_name_by_id(self.base_currency_id), profit_base=float_to_str(self.profit_in_base_currency))

def __str__(self):
    return 'Profit in {coin_name}: {profit_coin} Profit in {base_name}: {profit_base} '.format(coin_name=get_currency_name_by_id(self.dst_currency_id), profit_coin=float_to_str(self.profit_in_coin), base_name=get_currency_name_by_id(self.base_currency_id), profit_base=float_to_str(self.profit_in_base_currency))

# Node: get_exchange_name_by_id
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

def __eq__(self, other):
    if get_logging_level() >= LOG_ALL_DEBUG:
        msg = 'compare {u} with {b}'.format(u=self, b=other)
        log_to_file(msg, 'expire_deal.log')
    if other is None:
        return False
    return self.order_id == other.order_id and self.trade_type == other.trade_type and (self.exchange_id == other.exchange_id) and (self.pair_id == other.pair_id)

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

# Node: Trade
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

# Node: parse_time
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

def __str__(self):
    return '[price: {:16.8f} volume: {:16.8f} ]'.format(self.price, self.volume)

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

def __str__(self):
    str_repr = 'Sell=Bid exchange - {sell_exch} id = {id1} Buy-Ask exchange - {buy_exch} id = {id2} \n        currency pair - {pair} Arbitrage Threshold = {thrshld} Reverse Threshold = {rv_thr} Balance Threshold = {b_thr}\n        deal_expire_timeout = {deal_expire_timeout}\n        cfg_file_name = {cfg_file_name}\n        log_file_name = {log_file_name}\n        cap_update_timeout = {cap_update_timeout}\n        balance_update_timeout = {balance_update_timeout}\n        '.format(sell_exch=get_exchange_name_by_id(self.sell_exchange_id), id1=self.sell_exchange_id, buy_exch=get_exchange_name_by_id(self.buy_exchange_id), id2=self.buy_exchange_id, pair=get_pair_name_by_id(self.pair_id), pair_id=self.pair_id, thrshld=self.threshold, rv_thr=self.reverse_threshold, b_thr=self.balance_threshold, cfg_file_name=get_debug_level_name_by_id(self.cfg_file_name), deal_expire_timeout=self.deal_expire_timeout, log_file_name=self.log_file_name, cap_update_timeout=self.cap_update_timeout, balance_update_timeout=self.balance_update_timeout)
    return str_repr

def _generate_file_name(self):
    return '{sell_exch}==>{buy_exch}-{pair_name}.log'.format(sell_exch=get_exchange_name_by_id(self.sell_exchange_id), buy_exch=get_exchange_name_by_id(self.buy_exchange_id), pair_name=get_pair_name_by_id(self.pair_id))

def generate_command(self, full_path_to_script):
    cmd = '{cmd} --threshold {threshold} --reverse_threshold {reverse_threshold} --balance_threshold {balance_threshold} --sell_exchange_id {sell_exchange_id} --buy_exchange_id {buy_exchange_id} --pair_id {pair_id} --deal_expire_timeout {deal_expire_timeout} --cfg {cfg}'.format(cmd=full_path_to_script, threshold=self.threshold, reverse_threshold=self.reverse_threshold, balance_threshold=self.balance_threshold, sell_exchange_id=self.sell_exchange_id, buy_exchange_id=self.buy_exchange_id, pair_id=self.pair_id, deal_expire_timeout=self.deal_expire_timeout, cfg=self.cfg_file_name)
    return cmd

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

def __str__(self):
    str_repr = 'Trade #{num} at timest1: {timest1} timest2: {timest2} type: {type}\n        {deal1}\n        {deal2}\n        Current profit - {bakshish}\n        '.format(num=self.id, timest1=self.timest1, timest2=self.timest2, type=get_order_type_by_id(self.deal_type), deal1=str(self.deal_1), deal2=str(self.deal_2), bakshish=float_to_str(self.current_profit))
    return str_repr

def log_balance_expired_errors(cfg, msg_queue, balance_state):
    msg = '<b> !!! CRITICAL !!! </b>\n    Balance is OUTDATED for {exch1} or {exch2} for more than {tt} seconds\n    Arbitrage process will be stopped just in case.\n    Check log file: {lf}'.format(exch1=get_exchange_name_by_id(cfg.buy_exchange_id), exch2=get_exchange_name_by_id(cfg.sell_exchange_id), tt=BALANCE_EXPIRED_THRESHOLD, lf=cfg.log_file_name)
    print_to_console(msg, LOG_ALL_ERRORS)
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    log_to_file(msg, cfg.log_file_name)
    log_to_file(balance_state, cfg.log_file_name)

# Node: add_message
def log_failed_to_retrieve_order_book(cfg):
    msg = "CAN'T retrieve order book for {nn} or {nnn}".format(nn=get_exchange_name_by_id(cfg.sell_exchange_id), nnn=get_exchange_name_by_id(cfg.buy_exchange_id))
    print_to_console(msg, LOG_ALL_ERRORS)
    log_to_file(msg, cfg.log_file_name)

def log_dont_supported_currency(cfg, exchange_id, pair_id):
    msg = 'Not supported currency {idx}-{name} for {exch}'.format(idx=cfg.pair_id, name=pair_id, exch=get_exchange_name_by_id(exchange_id))
    print_to_console(msg, LOG_ALL_ERRORS)
    log_to_file(msg, cfg.log_file_name)

def log_dublicative_order_book(log_file_name, msg_queue, order_book, prev_order_book):
    msg = ' <b> !!! WARNING !!! </b>\n    Number of similar asks OR bids are the same for the most recent and cached version of order book for\n    exchange_name {exch} pair_name {pn}\n    cached timest: {ts1} {dt1}\n    recent timest: {ts2} {dt2}\n    Verbose information can be found in logs error & \n    '.format(exch=get_exchange_name_by_id(order_book.exchange_id), pn=get_currency_pair_name_by_exchange_id(order_book.pair_id, order_book.exchange_id), ts1=prev_order_book.timest, dt1=ts_to_string_utc(prev_order_book.timest), ts2=order_book.timest, dt2=ts_to_string_utc(order_book.timest))
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    print_to_console(msg, LOG_ALL_ERRORS)
    log_to_file(msg, log_file_name)
    msg = 'Cached version of order book: \n    {o}\n    Recent version of order book:\n    {oo}\n    '.format(o=str(prev_order_book), oo=str(order_book))
    log_to_file(msg, log_file_name)

def log_cant_update_volume_cap(pair_id, buy_exchange_id, sell_exchange_id, log_file_name):
    msg = "CAN'T update minimum_volume_cap for {pair_id} at following exchanges: {exch1} {exch2}".format(pair_id=pair_id, exch1=get_exchange_name_by_id(buy_exchange_id), exch2=get_exchange_name_by_id(sell_exchange_id))
    log_to_file(msg, log_file_name)
    log_to_file(msg, CAP_ADJUSTMENT_TRACE_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_finishing_syncing_order_book(kind):
    msg = 'Finishing syncing {kind} order book!'.format(kind=kind)
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_all_order_book_synced():
    msg = 'sync_order_books - AFTER MAIN LOOP - stage status is {}'.format(get_stage())
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_order_book_update_failed_pre_sync(kind, exchange_id, order_book_updates):
    msg = 'Reset stage will be initiated because Orderbook update FAILED during pre-SYNC stage - {kind} - for {exch_name} Update itself: {upd}'.format(kind=kind, exch_name=get_exchange_name_by_id(exchange_id), upd=order_book_updates)
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_order_book_update_failed_post_sync(exchange_id, order_book_updates):
    msg = 'Update after syncing FAILED = Order book update is FAILED! for {exch_name} Update itself: {upd}'.format(exch_name=get_exchange_name_by_id(exchange_id), upd=order_book_updates)
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_one_of_subscriptions_failed(buy_subscription, sell_subscription, curent_stage):
    msg = 'One of processes stopped: buy: {b_s} sell: {s_s} current stage is {st}'.format(b_s=buy_subscription, s_s=sell_subscription, st=curent_stage)
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_cant_cancel_deal(every_deal, msg_queue, log_file_name=EXPIRED_ORDER_PROCESSING_FILE_NAME):
    msg = "CAN'T cancel deal - {deal}".format(deal=every_deal)
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    print_to_console(msg, LOG_ALL_ERRORS)
    if log_file_name != EXPIRED_ORDER_PROCESSING_FILE_NAME:
        log_to_file(msg, log_file_name)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_expired_order_replacement_result(expired_order, json_document, msg_queue):
    msg = 'We have tried to replace existing order with new one:\n                {o}\n                and got response:\n                {r}\n                '.format(o=expired_order, r=json_document)
    msg_queue.add_message(DEBUG_INFO_MSG, msg)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_failed_order_replacement_result(failed_order, json_document, msg_queue):
    msg = 'We have tried to replace failed order with new one:\n                {o}\n                and got response:\n                {r}\n                '.format(o=failed_order, r=json_document)
    msg_queue.add_message(DEBUG_INFO_MSG, msg)
    log_to_file(msg, FAILED_ORDER_PROCESSING_FILE_NAME)

def log_placing_new_deal(every_deal, msg_queue, log_file_name=EXPIRED_ORDER_PROCESSING_FILE_NAME):
    msg = ' We try to send following order to exchange as replacement for expired or failed order.\n    Order details: {deal}'.format(deal=str(every_deal))
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    print_to_console(msg, LOG_ALL_ERRORS)
    if log_file_name != EXPIRED_ORDER_PROCESSING_FILE_NAME:
        log_to_file(msg, log_file_name)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_cant_placing_new_deal(every_deal, msg_queue, log_file_name=EXPIRED_ORDER_PROCESSING_FILE_NAME):
    msg = '   We <b> !!! FAILED !!! </b>\n    to send following order to exchange as replacement for expired or failed order.\n    Order details:\n    {deal}\n    '.format(deal=str(every_deal))
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    print_to_console(msg, LOG_ALL_ERRORS)
    if log_file_name != EXPIRED_ORDER_PROCESSING_FILE_NAME:
        log_to_file(msg, log_file_name)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_cant_retrieve_order_book(order, msg_queue, log_file_name=EXPIRED_ORDER_PROCESSING_FILE_NAME):
    msg = " Can't retrieve order book for deal with expired or failed orders!\n        Order details: {deal}".format(deal=str(order))
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    print_to_console(msg, LOG_ALL_ERRORS)
    if log_file_name != EXPIRED_ORDER_PROCESSING_FILE_NAME:
        log_to_file(msg, log_file_name)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_cant_retrieve_ticker(order, msg_queue, log_file_name=EXPIRED_ORDER_PROCESSING_FILE_NAME):
    msg = " Can't retrieve ticker for expired or failed orders!\n                Will try to re-process it later.\n            Order details: {deal}".format(deal=str(order))
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    print_to_console(msg, LOG_ALL_ERRORS)
    if log_file_name != EXPIRED_ORDER_PROCESSING_FILE_NAME:
        log_to_file(msg, log_file_name)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_open_orders_by_exchange_bad_result(order):
    msg = 'Cant retrieve open orders for analysis expired order: {o}'.format(o=order)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_open_orders_is_empty(order):
    msg = 'Empty list of open orders for analysis expired order: {o}\n    Consider it as FILLED and forgeting it.\n    '.format(o=order)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_balance_expired(exchange_id, threshold, balance_state, msg_queue):
    msg = '<b> !!! CRITICAL !!! </b>\n    Balance is OUTDATED for {exch1} for more than {tt} seconds\n    Expired or failed orders service will be stopped just in case.\n    '.format(exch1=get_exchange_name_by_id(exchange_id), tt=threshold)
    print_to_console(msg, LOG_ALL_ERRORS)
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    log_to_file(msg, ERROR_LOG_FILE_NAME)
    log_to_file(balance_state, ERROR_LOG_FILE_NAME)

def log_too_small_volume(order, max_volume, min_volume, msg_queue):
    msg = '<b> !!! NOT ENOUGH VOLUME !!! </b>\n        Balance is not enough to place order\n        {o}\n        Determined volume is: {v}\n        Minimum volume from recent tickers: {mv}\n        so we going to ABANDON and FORGET about this order.\n        '.format(o=order, v=float_to_str(max_volume), mv=float_to_str(min_volume))
    print_to_console(msg, LOG_ALL_ERRORS)
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    log_to_file(msg, ERROR_LOG_FILE_NAME)

def log_trace_all_open_orders(open_orders_at_both_exchanges):
    log_to_file('Open orders below:', EXPIRED_ORDER_PROCESSING_FILE_NAME)
    for open_order in open_orders_at_both_exchanges:
        log_to_file(open_order, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_trace_log_time_key(time_key):
    msg = 'process_expired_orders - for time key - {tk}'.format(tk=str(time_key))
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_trace_log_all_cached_orders_for_time_key(list_of_orders, ts):
    log_to_file('For key {ts} in cached orders - {num} orders'.format(ts=ts, num=len(list_of_orders[ts])), 'expire_deal.log')
    for order in list_of_orders[ts]:
        log_to_file(str(order), EXPIRED_ORDER_PROCESSING_FILE_NAME)

def log_trace_order_not_yet_expired(time_key, ts):
    msg = 'Too early for processing this key: {kkk} but ts={ts}'.format(kkk=time_key, ts=ts)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

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

def log_currency_disbalance_present(src_exchange_id, dst_exchange_id, pair_id, currency_id, balance_threshold, new_max_cap_volume, treshold):
    msg = 'We have disbalance! Exchanges {exch1} {exch2} for {pair_id} with {balance_threshold}. \n    Set max cap for {currency} to {vol} and try to find price diff more than {thrs}'.format(exch1=get_exchange_name_by_id(src_exchange_id), exch2=get_exchange_name_by_id(dst_exchange_id), pair_id=get_pair_name_by_id(pair_id), balance_threshold=balance_threshold, currency=get_currency_name_by_id(currency_id), vol=new_max_cap_volume, thrs=treshold)
    print_to_console(msg, LOG_ALL_MARKET_NETWORK_RELATED_CRAP)
    log_to_file(msg, 'history_trades.log')
    log_to_file(msg, 'cap_price_adjustment.log')

def log_currency_disbalance_heart_beat(src_exchange_id, dst_exchange_id, currency_id, treshold_reverse):
    msg = 'No disbalance at Exchanges {exch1} {exch2} for {pair_id} with {thrs}'.format(exch1=get_exchange_name_by_id(src_exchange_id), exch2=get_exchange_name_by_id(dst_exchange_id), pair_id=get_currency_name_by_id(currency_id), thrs=treshold_reverse)
    print_to_console(msg, LOG_ALL_MARKET_NETWORK_RELATED_CRAP)
    log_to_file(msg, DEBUG_LOG_FILE_NAME)

def log_arbitrage_heart_beat(sell_order_book, buy_order_book, difference):
    msg = 'check_highest_bid_bigger_than_lowest_ask:\n    \tFor pair - {pair_name}\n    \tExchange1 - {exch1} BID = {bid}\n    \tExchange2 - {exch2} ASK = {ask}\n    \tDIFF = {diff}'.format(pair_name=get_pair_name_by_id(sell_order_book.pair_id), exch1=get_exchange_name_by_id(sell_order_book.exchange_id), bid=float_to_str(sell_order_book.bid[FIRST].price), exch2=get_exchange_name_by_id(buy_order_book.exchange_id), ask=float_to_str(buy_order_book.ask[LAST].price), diff=difference)
    print_to_console(msg, LOG_ALL_MARKET_NETWORK_RELATED_CRAP)
    log_to_file(msg, DEBUG_LOG_FILE_NAME)

def log_arbitrage_determined_volume_not_enough(sell_order_book, buy_order_book, msg_queue):
    msg = 'analyse order book - DETERMINED volume of deal is not ENOUGH {pair_name}:\n    first_exchange: {first_exchange} first exchange volume: <b>{vol1}</b>\n    second_exchange: {second_exchange} second_exchange_volume: <b>{vol2}</b>'.format(pair_name=get_pair_name_by_id(sell_order_book.pair_id), first_exchange=get_exchange_name_by_id(sell_order_book.exchange_id), second_exchange=get_exchange_name_by_id(buy_order_book.exchange_id), vol1=float_to_str(sell_order_book.bid[FIRST].volume), vol2=float_to_str(buy_order_book.ask[LAST].volume))
    print_to_console(msg, LOG_ALL_MARKET_NETWORK_RELATED_CRAP)
    log_to_file(msg, DEBUG_LOG_FILE_NAME)
    if get_logging_level() >= LOG_ALL_TRACE:
        msg_queue.add_message(DEBUG_INFO_MSG, msg)

def log_arbitrage_determined_price_not_enough(sell_price, sell_price_order_book, buy_price, buy_price_order_book, difference, final_difference, pair_id, msg_queue):
    msg = 'analyse order book - adjusted prices below 0.2 hardcoded threshold:\n    \tfinal_sell: {sell_price} initial_sell: {i_sell}\n    \tfinal_buy: {final_buy} initial_buy: {i_buy}\n    \tfinal_diff: {final_diff} original_diff: {diff} \n    \tfor pair_id = {p_name}'.format(sell_price=float_to_str(sell_price), i_sell=float_to_str(sell_price_order_book), final_buy=float_to_str(buy_price), i_buy=float_to_str(buy_price_order_book), final_diff=final_difference, p_name=get_pair_name_by_id(pair_id), diff=difference)
    print_to_console(msg, LOG_ALL_MARKET_NETWORK_RELATED_CRAP)
    log_to_file(msg, DEBUG_LOG_FILE_NAME)
    msg_queue.add_message(DEBUG_INFO_MSG, msg)

def log_trace_all_closed_orders(open_orders_at_both_exchanges):
    log_to_file('Closed orders below:', FAILED_ORDER_PROCESSING_FILE_NAME)
    for open_order in open_orders_at_both_exchanges:
        log_to_file(open_order, FAILED_ORDER_PROCESSING_FILE_NAME)

def log_trace_found_failed_order_in_open(order):
    msg = 'Found order {o} among OPEN orders'.format(o=order)
    log_to_file(msg, FAILED_ORDER_PROCESSING_FILE_NAME)

def log_trace_found_failed_order_in_history(order):
    msg = 'Found order {o} among HISTORY trades'.format(o=order)
    log_to_file(msg, FAILED_ORDER_PROCESSING_FILE_NAME)

def log_conect_to_websocket(exch_name):
    msg = '{exch_name} - before main loop'.format(exch_name=exch_name)
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_error_on_receive_from_socket(exch_name, e):
    msg = '{exch_name} - triggered exception during reading from socket = {e}. Reseting stage!'.format(exch_name=exch_name, e=str(e))
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_heartbeat_is_missing(exch_name, timeout, last_heartbeat_ts, ts_now):
    msg = '{exch_name} - Havent heard from exchange more than {timeout}. Last update - {l_update} but now - {n_time}. Reseting stage!'.format(exch_name=exch_name, timeout=timeout, l_update=last_heartbeat_ts, n_time=ts_now)
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_subscription_cancelled(exch_name):
    msg = '{exch_name} - exit from main loop. Current thread will be finished.'.format(exch_name=exch_name)
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

def log_sequence_id_mismatch(exch_name, prev_sequence_id, new_sequence_id):
    msg = '{exch_name} - sequence_id mismatch! Prev: {prev} New: {new}'.format(exch_name=exch_name, prev=prev_sequence_id, new=new_sequence_id)
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_subscribe_to_exchange_heartbeat(exch_name):
    msg = '{exch_name} - subscribing to exchange heartbeat'.format(exch_name=exch_name)
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_unsubscribe_to_exchange_heartbeat(exch_name):
    msg = '{exch_name} - DISCONNECT FROM exchange heartbeat'.format(exch_name=exch_name)
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_initial_settings(msg, exchanges_ids):
    for exchange_id in exchanges_ids:
        msg += str(exchange_id) + ' - ' + get_exchange_name_by_id(exchange_id) + '\n'
    print_to_console(msg, LOG_ALL_ERRORS)
    log_to_file(msg, 'balance.log')

def log_not_enough_base_currency(exchange_id, currency_id, threshold, balance_for_exchange, msg_queue):
    msg = '<b> !!! INFO !!! </b>\n    {base_currency} balance on exchange {exch} BELOW threshold {thrs} - only {am} LEFT!'.format(base_currency=get_currency_name_by_id(currency_id), thrs=threshold, exch=get_exchange_name_by_id(exchange_id), am=balance_for_exchange.get_balance(currency_id))
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    print_to_console(msg, LOG_ALL_ERRORS)
    print_to_console(balance_for_exchange, LOG_ALL_MARKET_RELATED_CRAP)
    log_to_file(str(balance_for_exchange), 'balance.log')

def log_warn_balance_not_updating(last_balance, msg_queue):
    msg = '           <b> !!! WARNING !!! </b>\n    BALANCE were not updated for a {tm} seconds!\n    last balance {bl}'.format(tm=BALANCE_EXPIRE_TIMEOUT, bl=last_balance)
    print_to_console(msg, LOG_ALL_ERRORS)
    msg_queue.add_message(DEAL_INFO_MSG, msg)
    log_to_file(msg, 'balance.log')

def log_balance_updated(idx, balance):
    msg = 'Updated balance sucessfully for exch={exch}:\n    {balance}'.format(exch=get_exchange_name_by_id(idx), balance=balance)
    print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
    log_to_file(msg, 'balance.log')

def log_cant_update_balance(idx):
    msg = 'Balance is NONE for exchange {exch}. Will retry in 1 second...'.format(exch=get_exchange_name_by_id(idx))
    print_to_console(msg, LOG_ALL_MARKET_RELATED_CRAP)
    log_to_file(msg, 'balance.log')

def log_balance_update_heartbeat(idx):
    tr = 'Updating for exch = {exch}'.format(exch=get_exchange_name_by_id(idx))
    print_to_console(tr, LOG_ALL_DEBUG)
    log_to_file(tr, 'balance.log')

def get_balance_poloniex_result_processor(json_document, timest):
    if is_error(json_document):
        msg = 'get_balance_poloniex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    return Balance.from_poloniex(timest, json_document)

# Node: is_error
# Node: from_poloniex
def parse_orders_currency(json_document, pair_name):
    orders = []
    for entry in json_document:
        trade = Trade.from_poloniex_history(entry, pair_name)
        if trade is not None:
            orders.append(trade)
    return orders

# Node: from_poloniex_history
def get_order_history_poloniex_result_processor(json_document, pair_name):
    """
        json_document - response from exchange api as json string
        pair_name - for backwords compabilities
    """
    orders = []
    if is_error(json_document):
        msg = 'get_order_history_poloniex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return (STATUS.FAILURE, orders)
    if pair_name != 'all':
        orders = parse_orders_currency(json_document, pair_name)
    else:
        for pair in json_document:
            orders += parse_orders_currency(json_document[pair], pair)
    return (STATUS.SUCCESS, orders)

# Node: parse_orders_currency
def get_ticker_poloniex_result_processor(json_document, pair_name, timest):
    if is_error(json_document) or pair_name not in json_document or json_document[pair_name] is None:
        msg = 'get_ticker_poloniex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    return Ticker.from_poloniex(pair_name, timest, json_document[pair_name])

def get_ohlc_poloniex_result_processor(json_response, pair_name, date_start, date_end):
    result_set = []
    if is_error(json_response):
        msg = 'get_ohlc_poloniex_result_processor - error response - {er}'.format(er=json_response)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return result_set
    for record in json_response:
        if long(record['date']) != 0:
            result_set.append(Candle.from_poloniex(record, pair_name))
    return result_set

def get_order_book_poloniex_result_processor(json_document, pair_name, timest):
    if is_error(json_document):
        msg = 'get_order_book_poloniex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    return OrderBook.from_poloniex(json_document, pair_name, timest)

def get_open_orders_poloniex_result_processor(json_document, pair_name):
    orders = []
    if is_error(json_document):
        msg = 'get_open_orders_poloniex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return (STATUS.FAILURE, orders)
    for entry in json_document:
        order = Trade.from_poloniex(entry, pair_name)
        if order is not None:
            orders.append(order)
    return (STATUS.SUCCESS, orders)

def parse_order_id_poloniex(json_document):
    """
     {u'orderNumber': u'15573359248', u'resultingTrades': []}
    """
    if is_error(json_document) or 'orderNumber' not in json_document:
        msg = 'parse_order_id_poloniex - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    return json_document['orderNumber']

def get_history_poloniex_result_processor(json_document, pair_name, timest):
    all_history_records = []
    if is_error(json_document):
        msg = 'get_history_poloniex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return all_history_records
    for rr in json_document:
        all_history_records.append(TradeHistory.from_poloniex(rr, pair_name, timest))
    return all_history_records

def parse_socket_update_poloniex(order_book_delta):
    """
                Message format for ticker
                [
                    1002,                             Channel
                    null,                             Unknown
                    [
                        121,                          CurrencyPairID
                        "10777.56054438",             Last
                        "10800.00000000",             lowestAsk
                        "10789.20000001",             highestBid
                        "-0.00860373",                percentChange
                        "72542984.79776118",          baseVolume
                        "6792.60163706",              quoteVolume
                        0,                            isForzen
                        "11400.00000000",             high24hr
                        "9880.00000009"               low24hr
                    ]
                ]

                [1002,null,[158,"0.00052808","0.00053854","0.00052926","0.05571659","4.07923480","7302.01523251",0,"0.00061600","0.00049471"]]

                So the columns for orders are
                    messageType -> t/trade, o/order
                    tradeID -> only for trades, just a number
                    orderType -> 1/bid,0/ask
                    rate
                    amount
                    time
                    sequence
                148 is code for BTCETH, yeah there is no documentation.. but when trades occur You can figure out.
                Bid is always 1, cause You add something new..

                PairId, Nonce, orders	rades deltas:
                [24,219199090,[["o",1,"0.04122908","0.01636493"],["t","10026908",0,"0.04122908","0.00105314",1527880700]]]
                [24,219201009,[["o",0,"0.04111587","0.00000000"],["o",0,"0.04111174","1.52701255"]]]
                [24,219164304,[["o",1,"0.04064791","0.01435233"],["o",1,"0.04068034","0.16858384"]]]

                :param order_book_delta:
                :return:
            """
    asks = []
    bids = []
    trades_sell = []
    trades_buy = []
    if len(order_book_delta) < 3:
        return None
    timest_ms = get_now_seconds_utc_ms()
    sequence_id = long(order_book_delta[1])
    delta = order_book_delta[2]
    for entry in delta:
        if entry[0] == POLONIEX_WEBSOCKET_ORDER:
            new_deal = Deal(entry[2], entry[3])
            if entry[1] == POLONIEX_WEBSOCKET_ORDER_ASK:
                asks.append(new_deal)
            elif entry[1] == POLONIEX_WEBSOCKET_ORDER_BID:
                bids.append(new_deal)
            else:
                msg = 'Poloniex socket update parsing - {update} total: {ttt}'.format(update=entry, ttt=order_book_delta)
                log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
        elif entry[0] == POLONIEX_WEBSOCKET_TRADE:
            new_deal = Deal(entry[3], entry[4])
            if entry[2] == POLONIEX_WEBSOCKET_ORDER_BID:
                trades_sell.append(new_deal)
            elif entry[2] == POLONIEX_WEBSOCKET_ORDER_ASK:
                trades_buy.append(new_deal)
            else:
                msg = 'Poloniex socket update parsing - {wtf}'.format(wtf=entry)
                log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
        else:
            msg = 'Poloniex socket update parsing - UNKNOWN TYPE - {wtf}'.format(wtf=entry)
            log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    return OrderBookUpdate(sequence_id, bids, asks, timest_ms, trades_sell, trades_buy)

# Node: OrderBookUpdate
def log_error_send_message(func_name, some_message, exception):
    msg = '{func_name} FAILED: {msg} {ee}'.format(func_name=func_name, msg=some_message, ee=exception)
    print_to_console(msg, LOG_ALL_ERRORS)
    log_to_file(msg, 'telegram.log')

def set_stage(new_val):
    global SYNC_STAGE
    SYNC_STAGE = new_val
    log_to_file('Changed state to %s' % new_val, SOCKET_ERRORS_LOG_FILE_NAME)

def log_responce_cant_be_parsed(work_unit, file_name=None):
    json_responce = ''
    try:
        json_responce = work_unit.future_value_json
    except:
        pass
    responce_code = ''
    try:
        responce_code = work_unit.future_status_code
    except:
        pass
    msg = "   ERROR\n    For url {url} Response {resp} can't be parsed.\n    HTTP Responce code, if any: {hc}\n    JSON Data, if any: {js} \n    ".format(url=work_unit.url, resp=work_unit.future_value, hc=responce_code, js=json_responce)
    log_to_file(msg, ERROR_LOG_FILE_NAME)
    if file_name is not None:
        log_to_file(msg, file_name)
    return msg

def log_responce(work_unit):
    json_responce = ''
    try:
        json_responce = work_unit.future_value_json
    except:
        pass
    if json_responce:
        msg = 'For url {url} response {resp}'.format(url=work_unit.url, resp=json_responce)
    else:
        msg = 'For url {url} response {status_code}'.format(url=work_unit.url, status_code=work_unit.future_value)
    log_to_file(msg, POST_RESPONCE_FILE_NAME)

def get_balance_by_exchange(exchange_id):
    res = (STATUS.FAILURE, None)
    key = get_key_by_exchange(exchange_id)
    method_by_exchange = {EXCHANGE.BITTREX: get_balance_bittrex, EXCHANGE.KRAKEN: get_balance_kraken, EXCHANGE.POLONIEX: get_balance_poloniex, EXCHANGE.BINANCE: get_balance_binance, EXCHANGE.HUOBI: get_balance_huobi}
    if exchange_id in method_by_exchange:
        res = method_by_exchange[exchange_id](key)
        _, balance = res
        log_to_file(balance, 'balance.log')
    else:
        msg = 'get_balance_by_exchange - Unknown exchange_id! {idx}'.format(idx=exchange_id)
        print_to_console(msg, LOG_ALL_ERRORS)
    return res

def update_balance_by_exchange(exchange_id, cache=get_cache()):
    status_code, balance = get_balance_by_exchange(exchange_id)
    exchange_name = get_exchange_name_by_id(exchange_id)
    if status_code == STATUS.SUCCESS and balance is not None:
        cache.update_balance(exchange_name, balance)
        log_to_file('Update balance at cache', 'balance.log')
        log_to_file(balance, 'balance.log')
    msg = "Can't update balance for exchange_id = {exch1} {exch_name}".format(exch1=exchange_id, exch_name=exchange_name)
    log_to_file(msg, 'cache.log')
    log_to_file(msg, 'balance.log')
    return (status_code, balance)

# Node: get_balance_by_exchange
# Node: update_balance
def assert_trade_type(trade, expected_type):
    if trade.trade_type != expected_type:
        msg = 'Deal type do NOT correspond to method invocation. {d}'.format(d=trade)
        print_to_console(msg, LOG_ALL_ERRORS)
        log_to_file(msg, 'error.log')
        assert trade.trade_type != expected_type

def log_error_unknown_exchange(func_name, details):
    msg = '{func_name} - Unknown exchange! Details: {res}'.format(func_name=func_name, res=details)
    print_to_console(msg, LOG_ALL_ERRORS)
    log_to_file(msg, 'error.log')

def get_balance_huobi_result_processor(json_document, timest):
    if not is_error(json_document) and 'data' in json_document and json_document['data']:
        return (STATUS.SUCCESS, Balance.from_huobi(timest, json_document['data']))
    msg = 'get_balance_huobi_result_processor - error response - {er}'.format(er=json_document)
    log_to_file(msg, ERROR_LOG_FILE_NAME)
    return (STATUS.FAILURE, None)

# Node: from_huobi
def get_ticker_huobi_result_processor(json_document, pair_name, timest):
    if is_error(json_document) or json_document.get('tick') is None:
        msg = 'get_ticker_huobi_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    return Ticker.from_huobi(pair_name, timest, json_document['tick'])

def get_ohlc_huobi_result_processor(json_response, pair_name, date_start, date_end):
    """
        {
          "status": "ok",
          "ch": "market.btcusdt.kline.1day",
          "ts": 1499223904680,
          “data”: [
            {
                "id": 1499184000,
                "amount": 37593.0266,
                "count": 0,
                "open": 1935.2000,
                "close": 1879.0000,
                "low": 1856.0000,
                "high": 1940.0000,
                "vol": 71031537.97866500
            },
            // more data here
            ]
        }
    """
    result_set = []
    if is_error(json_response) or 'data' not in json_response:
        msg = 'get_ohlc_huobi_result_processor - error response - {er}'.format(er=json_response)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return result_set
    for record in json_response['data']:
        record['artifical_ts'] = json_response['ts']
        result_set.append(Candle.from_huobi(record, pair_name))
    return result_set

def get_order_book_huobi_result_processor(json_document, pair_name, timest):
    if is_error(json_document) or json_document.get('tick') is None:
        msg = 'get_order_book_huobi_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    return OrderBook.from_huobi(json_document['tick'], pair_name, timest)

def get_orders_huobi_result_processor(json_document, pair_name):
    """
    Used to parse result for order_history and open_orders end points

    :param json_document - response from exchange api as json string
    :param pair_name - for backwards capabilities

    :return pair of status code, result
    """
    orders = []
    if is_error(json_document) or 'data' not in json_document:
        msg = 'get_open_orders_huobi_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return (STATUS.FAILURE, orders)
    for entry in json_document['data']:
        order = Trade.from_huobi(entry, pair_name)
        if order is not None:
            orders.append(order)
    return (STATUS.SUCCESS, orders)

def parse_order_id_huobi(json_document):
    """
    {
        "status": "ok",
        "data": "59378"
    }
    """
    if is_error(json_document) or 'data' not in json_document:
        msg = 'parse_order_id_huobi - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    return str(json_document['data'])

def get_history_huobi_result_processor(json_document, pair_name, timest):
    all_history_records = []
    if is_error(json_document) or 'data' not in json_document:
        msg = 'get_history_huobi_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return all_history_records
    for entry in json_document['data']:
        for record in entry['data']:
            all_history_records.append(TradeHistory.from_huobi(record, pair_name, timest))
    return all_history_records

def get_balance_binance_result_processor(json_document, timest):
    if not is_error(json_document) and 'balances' in json_document:
        return (STATUS.SUCCESS, Balance.from_binance(timest, json_document))
    msg = 'get_balance_binance_result_processor - error response - {er}'.format(er=json_document)
    log_to_file(msg, ERROR_LOG_FILE_NAME)
    return (STATUS.FAILURE, None)

# Node: from_binance
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

def get_ticker_binance_result_processor(json_document, pair_name, timest):
    if is_error(json_document):
        msg = 'get_ticker_binance_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    for entry in json_document:
        if pair_name in entry['symbol']:
            return Ticker.from_binance(entry['symbol'], timest, entry)
    return None

def get_ohlc_binance_result_processor(json_response, currency, date_start, date_end):
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
    """
    result_set = []
    if is_error(json_response):
        msg = 'get_ohlc_binance_result_processor - error response - {er}'.format(er=json_response)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return result_set
    for record in json_response:
        result_set.append(Candle.from_binance(record, currency))
    return result_set

def get_orders_binance_result_processor(msg, json_document, pair_name):
    """
    json_document - response from exchange api as json string
    pair_name - for backwards compatibilities
    """
    orders = []
    if is_error(json_document):
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return (STATUS.FAILURE, orders)
    for entry in json_document:
        order = Trade.from_binance(entry)
        if order is not None:
            orders.append(order)
    return (STATUS.SUCCESS, orders)

def get_order_book_binance(pair_name, timest):
    final_url = get_order_book_binance_url(pair_name)
    err_msg = 'get_order_book_binance called for {pair} at {timest}'.format(pair=pair_name, timest=timest)
    error_code, r = send_request(final_url, err_msg)
    if error_code == STATUS.SUCCESS and r is not None:
        return OrderBook.from_binance(r, pair_name, timest)
    return None

# Node: get_order_book_binance_url
def get_order_book_binance_result_processor(json_document, pair_name, timest):
    if is_error(json_document):
        msg = 'get_order_book_binance_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    return OrderBook.from_binance(json_document, pair_name, timest)

def parse_order_id_binance(json_document):
    """
    {u'orderId': 6599290,
    u'clientOrderId': u'oGDxv6VeLXRdvUA8PiK8KR',
    u'origQty': u'27.79000000',
    u'symbol': u'OMGBTC',
    u'side': u'SELL',
    u'timeInForce': u'GTC',
    u'status': u'FILLED',
    u'transactTime': 1514223327566,
    u'type': u'LIMIT',
    u'price': u'0.00111100',
    u'executedQty': u'27.79000000'}
    """
    if is_error(json_document):
        msg = 'parse_order_id_binance - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    if 'orderId' in json_document:
        return json_document['orderId']
    return None

def get_history_binance_result_processor(json_document, pair_name, timest):
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
    all_history_records = []
    if is_error(json_document):
        msg = 'get_history_binance_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return all_history_records
    for record in json_document:
        all_history_records.append(TradeHistory.from_binance(record, pair_name, timest))
    return all_history_records

def get_balance_kraken_result_processor(json_document, timest):
    if is_error(json_document):
        msg = 'get_balance_kraken_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return (STATUS.FAILURE, None)
    return (STATUS.SUCCESS, Balance.from_kraken(timest, json_document['result']))

# Node: from_kraken
def get_order_history_kraken_result_processor(json_document, pair_name):
    """
    json_document - response from exchange api as json string
    pair_name - for backwords compabilities
    """
    orders = EMPTY_LIST
    if is_error(json_document) or 'closed' not in json_document['result']:
        msg = 'get_order_history_kraken_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return orders
    for order_id in json_document['result']['closed']:
        new_order = Trade.from_kraken(order_id, json_document['result']['closed'][order_id])
        if new_order is not None:
            orders.append(new_order)
    return orders

def get_ticker_kraken_result_processor(json_document, pair_name, timest):
    if is_error(json_document):
        msg = 'get_ticker_kraken_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    if pair_name in json_document['result']:
        return Ticker.from_kraken(pair_name, timest, json_document['result'][pair_name])
    return None

def get_ohlc_kraken_result_processor(json_responce, currency, date_start, date_end):
    result_set = EMPTY_LIST
    if is_error(json_responce):
        msg = 'get_ohlc_kraken_result_processor - error response - {er}'.format(er=json_responce)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return result_set
    if currency in json_responce['result']:
        for record in json_responce['result'][currency]:
            result_set.append(Candle.from_kraken(record, currency))
    return result_set

def get_order_book_kraken_result_processor(json_document, pair_name, timest):
    if is_error(json_document):
        msg = 'get_order_book_kraken_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    if pair_name in json_document['result']:
        return OrderBook.from_kraken(json_document['result'][pair_name], pair_name, timest)
    return None

def get_open_orders_kraken_result_processor(json_document, pair_name):
    open_orders = EMPTY_LIST
    if is_error(open_orders) or 'open' not in json_document['result']:
        msg = 'get_open_orders_kraken_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return open_orders
    for order_id in json_document['result']['open']:
        new_order = Trade.from_kraken(order_id, json_document['result']['open'][order_id])
        if new_order is not None:
            open_orders.append(new_order)
    return open_orders

def parse_order_id_kraken(json_document):
    """
    {u'result': {u'descr':
            {u'order': u'sell 10.00000000 XMRXBT @ limit 0.045000'},
            u'txid': [u'OY3ZML-PE3LG-L4NG7C']},
    u'error': []}
    """
    if is_error(json_document):
        msg = 'parse_order_id_kraken - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    if 'txid' in json_document['result']:
        return json_document['result']['txid']
    return None

def get_history_kraken_result_processor(json_document, pair_name, timest):
    all_history_records = EMPTY_LIST
    if is_error(json_document):
        msg = 'get_history_kraken_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return all_history_records
    if pair_name in json_document['result']:
        for rr in json_document['result'][pair_name]:
            all_history_records.append(TradeHistory.from_kraken(rr, pair_name, timest))
    return all_history_records

def get_balance_bittrex_result_processor(json_document, timest):
    if is_error(json_document) or len(json_document['result']) < 1:
        msg = 'get_balance_bittrex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return (STATUS.FAILURE, None)
    return (STATUS.SUCCESS, Balance.from_bittrex(timest, json_document['result']))

# Node: from_bittrex
def get_order_history_bittrex_result_processor(json_document, pair_name):
    """
    json_document - response from exchange api as json string
    pair_name - for backwords compabilities
    """
    orders = []
    if is_error(json_document) or json_document['result'] is None:
        msg = 'get_order_history_bittrex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return (STATUS.FAILURE, orders)
    for entry in json_document['result']:
        order = Trade.from_bittrex_history(entry)
        if order is not None:
            orders.append(order)
    return (STATUS.SUCCESS, orders)

# Node: from_bittrex_history
def get_ohlc_bittrex_result_processor(json_document, pair_name, date_start, date_end):
    """
            result":[{"O":0.08184725,"H":0.08184725,"L":0.08181559,"C":0.08181559,"V":9.56201864,"T":"2017-07-21T17:26:00","BV":0.78232812},
            {"O":0.08181559,"H":0.08184725,"L":0.08181559,"C":0.08184725,"V":3.28483907,"T":"2017-07-21T17:27:00","BV":0.26876032}
    """
    result_set = []
    if is_error(json_document) or json_document['result'] is None:
        msg = 'get_ohlc_bittrex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return result_set
    for record in json_document['result']:
        result_set.append(Candle.from_bittrex(record, pair_name))
    return result_set

def get_order_book_bittrex_result_processor(json_document, pair_name, timest):
    if is_error(json_document):
        msg = 'get_order_book_bittrex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    return OrderBook.from_bittrex(json_document['result'], pair_name, timest)

def get_open_orders_bittrex_result_processor(json_document, pair_name):
    """
    json_document - response from exchange api as json string
    pair_name - for backwords compabilities
    """
    orders = []
    if is_error(json_document):
        msg = 'get_open_orders_bittrex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return (STATUS.FAILURE, orders)
    for entry in json_document['result']:
        order = Trade.from_bittrex(entry)
        if order is not None:
            orders.append(order)
    return (STATUS.SUCCESS, orders)

def parse_order_id_bittrex(json_document):
    """
    {u'message': u'',
        u'result': {
            u'uuid': u'b818589b-f799-476d-9b9c-71bc1ac5c653'},
        u'success': True
    }
    """
    if is_error(json_document) or 'uuid' not in json_document['result']:
        msg = 'parse_order_id_bittrex - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return None
    return json_document['result']['uuid']

def get_history_bittrex_result_processor(json_document, pair_name, timest):
    all_history_records = []
    if is_error(json_document) or json_document['result'] is None:
        msg = 'get_history_bittrex_result_processor - error response - {er}'.format(er=json_document)
        log_to_file(msg, ERROR_LOG_FILE_NAME)
        return all_history_records
    for rr in json_document['result']:
        all_history_records.append(TradeHistory.from_bittrex(rr, pair_name, timest))
    return all_history_records

def generate_screen_name(sell_exchange_id, buy_exchange_id):
    screen_name = '{sell_exch}==>{buy_exch}'.format(sell_exch=get_exchange_name_by_id(sell_exchange_id), buy_exch=get_exchange_name_by_id(buy_exchange_id))
    return screen_name

def add_orders_to_watch_list(orders_pair, priority_queue):
    if orders_pair is None:
        return
    msg = 'Add order to watch list - {pair}'.format(pair=str(orders_pair))
    log_to_file(msg, 'expire_deal.log')
    if orders_pair.deal_1:
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, orders_pair.deal_1)
    if orders_pair.deal_2:
        priority_queue.add_order_to_watch_queue(ORDERS_EXPIRE_MSG, orders_pair.deal_2)

def get_matches(objs, key):
    """
        Return dict of list curresponding to key
    """
    d = defaultdict(list)
    for obj in objs:
        if obj is not None:
            d[getattr(obj, key)].append(obj)
    return d

