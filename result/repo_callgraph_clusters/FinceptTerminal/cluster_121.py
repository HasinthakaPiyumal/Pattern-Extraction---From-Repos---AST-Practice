# Cluster 121

class IndexConstructor:
    """Index construction and management framework"""

    def __init__(self, name: str, weighting_method: IndexWeightingMethod):
        self.name = name
        self.weighting_method = weighting_method
        self.constituents = []
        self.base_value = 1000
        self.base_date = None
        self.divisor = 1.0

    def add_constituent(self, constituent: IndexConstituent):
        """Add a constituent to the index"""
        self.constituents.append(constituent)

    def remove_constituent(self, symbol: str):
        """Remove a constituent from the index"""
        self.constituents = [c for c in self.constituents if c.symbol != symbol]

    def calculate_weights(self) -> Dict[str, float]:
        """Calculate weights based on weighting methodology"""
        if not self.constituents:
            return {}
        weights = {}
        if self.weighting_method == IndexWeightingMethod.PRICE_WEIGHTED:
            total_price = sum((c.current_price for c in self.constituents))
            for constituent in self.constituents:
                weights[constituent.symbol] = constituent.current_price / total_price
        elif self.weighting_method == IndexWeightingMethod.MARKET_CAP_WEIGHTED:
            total_market_cap = sum((c.market_cap for c in self.constituents))
            for constituent in self.constituents:
                weights[constituent.symbol] = constituent.market_cap / total_market_cap
        elif self.weighting_method == IndexWeightingMethod.EQUAL_WEIGHTED:
            equal_weight = 1.0 / len(self.constituents)
            for constituent in self.constituents:
                weights[constituent.symbol] = equal_weight
        elif self.weighting_method == IndexWeightingMethod.FLOAT_ADJUSTED:
            total_float_cap = sum((c.float_shares * c.current_price for c in self.constituents))
            for constituent in self.constituents:
                float_cap = constituent.float_shares * constituent.current_price
                weights[constituent.symbol] = float_cap / total_float_cap
        elif self.weighting_method == IndexWeightingMethod.FUNDAMENTAL_WEIGHTED:
            total_fundamental = sum((c.market_cap for c in self.constituents))
            for constituent in self.constituents:
                weights[constituent.symbol] = constituent.market_cap / total_fundamental
        return weights

    def calculate_index_value(self, prices: Dict[str, float], base_prices: Dict[str, float]=None) -> float:
        """Calculate current index value"""
        if not self.constituents:
            return self.base_value
        if base_prices is None:
            base_prices = {c.symbol: c.current_price for c in self.constituents}
        if self.weighting_method == IndexWeightingMethod.PRICE_WEIGHTED:
            return self._calculate_price_weighted_value(prices, base_prices)
        elif self.weighting_method in [IndexWeightingMethod.MARKET_CAP_WEIGHTED, IndexWeightingMethod.FLOAT_ADJUSTED]:
            return self._calculate_cap_weighted_value(prices, base_prices)
        elif self.weighting_method == IndexWeightingMethod.EQUAL_WEIGHTED:
            return self._calculate_equal_weighted_value(prices, base_prices)
        else:
            return self._calculate_cap_weighted_value(prices, base_prices)

    def _calculate_price_weighted_value(self, prices: Dict[str, float], base_prices: Dict[str, float]) -> float:
        """Calculate price-weighted index value"""
        current_sum = sum((prices.get(c.symbol, c.current_price) for c in self.constituents))
        base_sum = sum((base_prices.get(c.symbol, c.current_price) for c in self.constituents))
        return self.base_value * (current_sum / base_sum) / self.divisor

    def _calculate_cap_weighted_value(self, prices: Dict[str, float], base_prices: Dict[str, float]) -> float:
        """Calculate market cap weighted index value"""
        current_cap = 0
        base_cap = 0
        for constituent in self.constituents:
            shares = constituent.float_shares if self.weighting_method == IndexWeightingMethod.FLOAT_ADJUSTED else constituent.shares_outstanding
            current_price = prices.get(constituent.symbol, constituent.current_price)
            base_price = base_prices.get(constituent.symbol, constituent.current_price)
            current_cap += shares * current_price
            base_cap += shares * base_price
        return self.base_value * (current_cap / base_cap) if base_cap > 0 else self.base_value

    def _calculate_equal_weighted_value(self, prices: Dict[str, float], base_prices: Dict[str, float]) -> float:
        """Calculate equal-weighted index value"""
        returns = []
        for constituent in self.constituents:
            current_price = prices.get(constituent.symbol, constituent.current_price)
            base_price = base_prices.get(constituent.symbol, constituent.current_price)
            if base_price > 0:
                returns.append(current_price / base_price)
        if returns:
            avg_return = np.mean(returns)
            return self.base_value * avg_return
        else:
            return self.base_value

def calculate_index_value(self, prices: Dict[str, float], base_prices: Dict[str, float]=None) -> float:
    """Calculate current index value"""
    if not self.constituents:
        return self.base_value
    if base_prices is None:
        base_prices = {c.symbol: c.current_price for c in self.constituents}
    if self.weighting_method == IndexWeightingMethod.PRICE_WEIGHTED:
        return self._calculate_price_weighted_value(prices, base_prices)
    elif self.weighting_method in [IndexWeightingMethod.MARKET_CAP_WEIGHTED, IndexWeightingMethod.FLOAT_ADJUSTED]:
        return self._calculate_cap_weighted_value(prices, base_prices)
    elif self.weighting_method == IndexWeightingMethod.EQUAL_WEIGHTED:
        return self._calculate_equal_weighted_value(prices, base_prices)
    else:
        return self._calculate_cap_weighted_value(prices, base_prices)

