# Cluster 31

def parse_update_by_exchanges(exchange_id, order_book_delta):
    parse_method = {EXCHANGE.POLONIEX: parse_socket_update_poloniex, EXCHANGE.HUOBI: parse_socket_update_huobi, EXCHANGE.BINANCE: parse_socket_update_binance, EXCHANGE.BITTREX: parse_socket_update_bittrex}[exchange_id]
    return parse_method(order_book_delta)

# Node: parse_method
