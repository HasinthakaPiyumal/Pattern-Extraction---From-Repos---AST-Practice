# Cluster 40

def check_all_combinations(tickers_to_check, threshold, predicate):
    res_list = []
    pair_of_tickers = get_all_permutation(tickers_to_check, 2)
    for first_ticker, second_ticker in pair_of_tickers:
        res = predicate(first_ticker, second_ticker, threshold)
        if res:
            res_list.append(res)
    return res_list

# Node: get_all_permutation
# Node: predicate
def check_all_combinations_list(tickers_to_check, threshold, predicate):
    res_list = []
    pair_of_tickers = get_all_permutation_list(tickers_to_check, 2)
    for first_ticker, second_ticker in pair_of_tickers:
        res = predicate(first_ticker, second_ticker, threshold)
        if res:
            res_list.append(res)
    return res_list

# Node: get_all_permutation_list
