# Cluster 123

def quick_margin_analysis(position_value: float, initial_margin: float=0.5) -> Dict[str, float]:
    """Quick margin requirement analysis"""
    calculator = MarginTradingCalculator()
    return calculator.calculate_margin_requirements(position_value, initial_margin)

def calculate_margin_call_price(initial_price: float, loan_amount: float, shares: int, maintenance_margin: float=0.25) -> float:
    """Quick margin call price calculation"""
    calculator = MarginTradingCalculator()
    return calculator.calculate_margin_call_price(initial_price, 0, loan_amount, shares, maintenance_margin)

