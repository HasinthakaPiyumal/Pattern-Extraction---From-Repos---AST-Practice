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
# Node: get_pair_name_by_id
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

def __str__(self):
    str_repr = '\n        Trade at Exchange: {exch}\n        Type: {deal_type}\n        Pair: {pair} for volume {vol} with price {price}\n        order_book_time {ob_time} create_time {ct_time} execute_time {ex_time}\n        Executed at: {dt}\n        order_id {order_id} trade_id {trade_id} executed_volume {ex_volume}\n        arbitrage_id {a_id}\n        '.format(exch=get_exchange_name_by_id(self.exchange_id), deal_type=get_order_type_by_id(self.trade_type), pair=get_pair_name_by_id(self.pair_id), vol=truncate_float(self.volume, 8), price=truncate_float(self.price, 8), ob_time=self.order_book_time, ct_time=self.create_time, ex_time=self.execute_time, dt=ts_to_string_local(self.execute_time), order_id=self.order_id, trade_id=self.trade_id, ex_volume=self.executed_volume, a_id=self.arbitrage_id)
    return str_repr

# Node: get_order_type_by_id
# Node: ts_to_string_local
def __eq__(self, other):
    if get_logging_level() >= LOG_ALL_DEBUG:
        msg = 'compare {u} with {b}'.format(u=self, b=other)
        log_to_file(msg, 'expire_deal.log')
    if other is None:
        return False
    return self.order_id == other.order_id and self.trade_type == other.trade_type and (self.exchange_id == other.exchange_id) and (self.pair_id == other.pair_id)

def __iter__(self):
    return iter([self.arbitrage_id, get_exchange_name_by_id(self.exchange_id), get_pair_name_by_id(self.pair_id), get_order_type_by_id(self.trade_type), self.price, self.volume, self.order_book_time, self.create_time, self.execute_time, ts_to_string_local(self.execute_time), self.order_id, self.trade_id, self.executed_volume])

# Node: iter
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

def generate_window_name(self):
    window_name = '{pair_id} - {pair_name}'.format(pair_id=self.pair_id, pair_name=get_pair_name_by_id(self.pair_id))
    return window_name

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

def log_order_book_update_failed_pre_sync(kind, exchange_id, order_book_updates):
    msg = 'Reset stage will be initiated because Orderbook update FAILED during pre-SYNC stage - {kind} - for {exch_name} Update itself: {upd}'.format(kind=kind, exch_name=get_exchange_name_by_id(exchange_id), upd=order_book_updates)
    log_to_file(msg, SOCKET_ERRORS_LOG_FILE_NAME)
    print_to_console(msg, LOG_ALL_ERRORS)

def log_order_book_update_failed_post_sync(exchange_id, order_book_updates):
    msg = 'Update after syncing FAILED = Order book update is FAILED! for {exch_name} Update itself: {upd}'.format(exch_name=get_exchange_name_by_id(exchange_id), upd=order_book_updates)
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

def log_trace_order_not_yet_expired(time_key, ts):
    msg = 'Too early for processing this key: {kkk} but ts={ts}'.format(kkk=time_key, ts=ts)
    log_to_file(msg, EXPIRED_ORDER_PROCESSING_FILE_NAME)

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
def get_balance(exchange_id, cache=get_cache()):
    exchange_name = get_exchange_name_by_id(exchange_id)
    balance = cache.get_balance(exchange_id)
    while balance is None:
        status_code, balance = update_balance_by_exchange(exchange_id)
        if not balance:
            msg = 'ERROR: BALANCE IS STILL NONE!!! for {n}'.format(n=exchange_name)
            print_to_console(msg, LOG_ALL_ERRORS)
    return balance

def get_balance_huobi_result_processor(json_document, timest):
    if not is_error(json_document) and 'data' in json_document and json_document['data']:
        return (STATUS.SUCCESS, Balance.from_huobi(timest, json_document['data']))
    msg = 'get_balance_huobi_result_processor - error response - {er}'.format(er=json_document)
    log_to_file(msg, ERROR_LOG_FILE_NAME)
    return (STATUS.FAILURE, None)

# Node: from_huobi
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

def get_matches(objs, key):
    """
        Return dict of list curresponding to key
    """
    d = defaultdict(list)
    for obj in objs:
        if obj is not None:
            d[getattr(obj, key)].append(obj)
    return d

def update_min_cap(cfg, deal_cap, processor):
    cur_timest_sec = get_now_seconds_utc()
    tickers = get_ticker_for_arbitrage(cfg.pair_id, cur_timest_sec, [cfg.buy_exchange_id, cfg.sell_exchange_id], processor)
    new_cap = compute_new_min_cap_from_tickers(cfg.pair_id, tickers)
    if new_cap > 0:
        msg = 'Updating old cap {op}'.format(op=deal_cap)
        log_to_file(msg, CAP_ADJUSTMENT_TRACE_LOG_FILE_NAME)
        deal_cap.update_min_volume_cap(new_cap, cur_timest_sec)
        msg = 'New cap {op}'.format(op=deal_cap)
        log_to_file(msg, CAP_ADJUSTMENT_TRACE_LOG_FILE_NAME)
    else:
        msg = "CAN'T update minimum_volume_cap for {pair_id} at following\n        exchanges: {exch1} {exch2}".format(pair_id=cfg.pair_id, exch1=get_exchange_name_by_id(cfg.buy_exchange_id), exch2=get_exchange_name_by_id(cfg.sell_exchange_id))
        print_to_console(msg, LOG_ALL_ERRORS)
        log_to_file(msg, cfg.log_file_name)
        log_to_file(msg, CAP_ADJUSTMENT_TRACE_LOG_FILE_NAME)

# Node: get_ticker_for_arbitrage
# Node: compute_new_min_cap_from_tickers
# Node: update_min_volume_cap
