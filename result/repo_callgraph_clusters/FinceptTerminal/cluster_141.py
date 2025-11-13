# Cluster 141

class PresetStrategyTemplates:
    """Production-ready strategy templates"""

    @staticmethod
    def get_available_strategies():
        """Get list of available preset strategies"""
        return [{'name': 'Golden Cross', 'description': 'Classic SMA 50/200 crossover strategy', 'category': 'Trend Following'}, {'name': 'RSI Mean Reversion', 'description': 'Buy oversold, sell overbought using RSI', 'category': 'Mean Reversion'}, {'name': 'MACD Momentum', 'description': 'MACD crossover with signal line', 'category': 'Momentum'}, {'name': 'Bollinger Squeeze', 'description': 'Trade breakouts from Bollinger Band squeezes', 'category': 'Volatility'}, {'name': 'Triple Screen', 'description': "Elder's triple screen trading system", 'category': 'Complex'}, {'name': 'Ichimoku Cloud', 'description': 'Complete Ichimoku trading system', 'category': 'Complex'}, {'name': 'Machine Learning', 'description': 'ML-based predictive signals', 'category': 'Advanced'}]

    @staticmethod
    def create_golden_cross_strategy(tab):
        """Create Golden Cross strategy"""
        tab.clear_all_nodes()
        data_node = tab.add_node_with_params(NodeType.DATA_SOURCE, {'ticker': 'SPY', 'period': '2y'})
        sma50_node = tab.add_node_with_params(NodeType.SMA, {'window': 50})
        sma200_node = tab.add_node_with_params(NodeType.SMA, {'window': 200})
        signal_node = tab.add_node_with_params(NodeType.SIGNAL, {'type': 'crossover'})
        backtest_node = tab.add_node_with_params(NodeType.BACKTEST, {'initial_capital': 100000})
        plot_node = tab.add_node_with_params(NodeType.PLOT, {'plot_type': 'comprehensive'})
        tab.connect_nodes(data_node, sma50_node, 'default')
        tab.connect_nodes(data_node, sma200_node, 'default')
        tab.connect_nodes(sma50_node, signal_node, 'fast')
        tab.connect_nodes(sma200_node, signal_node, 'slow')
        tab.connect_nodes(signal_node, backtest_node, 'signals')
        tab.connect_nodes(backtest_node, plot_node, 'default')
        return 'Golden Cross strategy created and connected'

    @staticmethod
    def create_rsi_mean_reversion_strategy(tab):
        """Create RSI Mean Reversion strategy"""
        tab.clear_all_nodes()
        data_node = tab.add_node_with_params(NodeType.DATA_SOURCE, {'ticker': 'QQQ', 'period': '1y'})
        rsi_node = tab.add_node_with_params(NodeType.RSI, {'period': 14})
        signal_node = tab.add_node_with_params(NodeType.SIGNAL, {'type': 'threshold', 'buy_threshold': 30, 'sell_threshold': 70})
        backtest_node = tab.add_node_with_params(NodeType.BACKTEST, {'initial_capital': 50000, 'stop_loss': 0.02, 'take_profit': 0.05})
        plot_node = tab.add_node_with_params(NodeType.PLOT, {'plot_type': 'comprehensive'})
        tab.connect_nodes(data_node, rsi_node, 'default')
        tab.connect_nodes(rsi_node, signal_node, 'indicator')
        tab.connect_nodes(signal_node, backtest_node, 'signals')
        tab.connect_nodes(backtest_node, plot_node, 'default')
        return 'RSI Mean Reversion strategy created'

@staticmethod
def create_golden_cross_strategy(tab):
    """Create Golden Cross strategy"""
    tab.clear_all_nodes()
    data_node = tab.add_node_with_params(NodeType.DATA_SOURCE, {'ticker': 'SPY', 'period': '2y'})
    sma50_node = tab.add_node_with_params(NodeType.SMA, {'window': 50})
    sma200_node = tab.add_node_with_params(NodeType.SMA, {'window': 200})
    signal_node = tab.add_node_with_params(NodeType.SIGNAL, {'type': 'crossover'})
    backtest_node = tab.add_node_with_params(NodeType.BACKTEST, {'initial_capital': 100000})
    plot_node = tab.add_node_with_params(NodeType.PLOT, {'plot_type': 'comprehensive'})
    tab.connect_nodes(data_node, sma50_node, 'default')
    tab.connect_nodes(data_node, sma200_node, 'default')
    tab.connect_nodes(sma50_node, signal_node, 'fast')
    tab.connect_nodes(sma200_node, signal_node, 'slow')
    tab.connect_nodes(signal_node, backtest_node, 'signals')
    tab.connect_nodes(backtest_node, plot_node, 'default')
    return 'Golden Cross strategy created and connected'

@staticmethod
def create_rsi_mean_reversion_strategy(tab):
    """Create RSI Mean Reversion strategy"""
    tab.clear_all_nodes()
    data_node = tab.add_node_with_params(NodeType.DATA_SOURCE, {'ticker': 'QQQ', 'period': '1y'})
    rsi_node = tab.add_node_with_params(NodeType.RSI, {'period': 14})
    signal_node = tab.add_node_with_params(NodeType.SIGNAL, {'type': 'threshold', 'buy_threshold': 30, 'sell_threshold': 70})
    backtest_node = tab.add_node_with_params(NodeType.BACKTEST, {'initial_capital': 50000, 'stop_loss': 0.02, 'take_profit': 0.05})
    plot_node = tab.add_node_with_params(NodeType.PLOT, {'plot_type': 'comprehensive'})
    tab.connect_nodes(data_node, rsi_node, 'default')
    tab.connect_nodes(rsi_node, signal_node, 'indicator')
    tab.connect_nodes(signal_node, backtest_node, 'signals')
    tab.connect_nodes(backtest_node, plot_node, 'default')
    return 'RSI Mean Reversion strategy created'

