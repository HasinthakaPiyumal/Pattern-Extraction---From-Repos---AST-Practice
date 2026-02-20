# Cluster 3

def prepare_data(pg_conn, start_time, end_time):
    orders = get_all_orders(pg_conn, table_name='arbitrage_orders', time_start=start_time, time_end=end_time)
    history_trades = get_all_orders(pg_conn, table_name='arbitrage_trades', time_start=start_time, time_end=end_time)
    return (orders, history_trades)

# Node: get_all_orders
