# Cluster 106

class OptionCalculations:
    """Option pricing and Greeks calculations"""

    @staticmethod
    def black_scholes(spot_price: float, strike_price: float, time_to_expiry: float, risk_free_rate: float, volatility: float, option_type: str='call') -> Dict[str, float]:
        """Calculate Black-Scholes option price and Greeks"""
        d1 = (math.log(spot_price / strike_price) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (volatility * math.sqrt(time_to_expiry))
        d2 = d1 - volatility * math.sqrt(time_to_expiry)
        N_d1 = stats.norm.cdf(d1)
        N_d2 = stats.norm.cdf(d2)
        N_neg_d1 = stats.norm.cdf(-d1)
        N_neg_d2 = stats.norm.cdf(-d2)
        n_d1 = stats.norm.pdf(d1)
        if option_type.lower() == 'call':
            option_price = spot_price * N_d1 - strike_price * math.exp(-risk_free_rate * time_to_expiry) * N_d2
            delta = N_d1
            gamma = n_d1 / (spot_price * volatility * math.sqrt(time_to_expiry))
            theta = (-spot_price * n_d1 * volatility / (2 * math.sqrt(time_to_expiry)) - risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry) * N_d2) / 365
        else:
            option_price = strike_price * math.exp(-risk_free_rate * time_to_expiry) * N_neg_d2 - spot_price * N_neg_d1
            delta = N_d1 - 1
            gamma = n_d1 / (spot_price * volatility * math.sqrt(time_to_expiry))
            theta = (-spot_price * n_d1 * volatility / (2 * math.sqrt(time_to_expiry)) + risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry) * N_neg_d2) / 365
        vega = spot_price * n_d1 * math.sqrt(time_to_expiry) / 100
        rho = strike_price * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * (N_d2 if option_type.lower() == 'call' else N_neg_d2) / 100
        return {'option_price': option_price, 'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega, 'rho': rho, 'd1': d1, 'd2': d2, 'intrinsic_value': max(0, spot_price - strike_price) if option_type.lower() == 'call' else max(0, strike_price - spot_price), 'time_value': option_price - max(0, spot_price - strike_price if option_type.lower() == 'call' else strike_price - spot_price)}

    @staticmethod
    def implied_volatility(option_price: float, spot_price: float, strike_price: float, time_to_expiry: float, risk_free_rate: float, option_type: str='call') -> float:
        """Calculate implied volatility using Newton-Raphson method"""

        def bs_price_diff(vol):
            bs_result = OptionCalculations.black_scholes(spot_price, strike_price, time_to_expiry, risk_free_rate, vol, option_type)
            return bs_result['option_price'] - option_price
        try:
            initial_vol = 0.2
            implied_vol = fsolve(bs_price_diff, initial_vol)[0]
            if implied_vol < 0 or implied_vol > 5:
                return np.nan
            return implied_vol
        except:
            return np.nan

@staticmethod
def implied_volatility(option_price: float, spot_price: float, strike_price: float, time_to_expiry: float, risk_free_rate: float, option_type: str='call') -> float:
    """Calculate implied volatility using Newton-Raphson method"""

    def bs_price_diff(vol):
        bs_result = OptionCalculations.black_scholes(spot_price, strike_price, time_to_expiry, risk_free_rate, vol, option_type)
        return bs_result['option_price'] - option_price
    try:
        initial_vol = 0.2
        implied_vol = fsolve(bs_price_diff, initial_vol)[0]
        if implied_vol < 0 or implied_vol > 5:
            return np.nan
        return implied_vol
    except:
        return np.nan

