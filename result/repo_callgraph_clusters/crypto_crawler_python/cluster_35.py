# Cluster 35

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

def __init__(self, deal_1, deal_2, timest_1, timest_2, deal_type):
    self.deal_1 = deal_1
    self.deal_2 = deal_2
    self.id = get_next_id()
    self.timest1 = timest_1
    self.timest2 = timest_2
    self.deal_type = deal_type
    self.current_profit = self.compute_profit(self.deal_1, self.deal_2)

# Node: get_next_id
# Node: compute_profit
