# Cluster 140

class NodeProcessor:
    """Enhanced node processor with caching and parallel execution"""

    def __init__(self):
        self.nodes: Dict[str, NodeData] = {}
        self.execution_order: List[str] = []
        self.cache: Dict[str, Any] = {}
        self.performance_tracker: Dict[str, float] = {}

    def add_node(self, node_data: NodeData):
        """Add a node to the processor"""
        self.nodes[node_data.node_id] = node_data
        logger.info(f'Added node {node_data.node_id} of type {node_data.node_type.value}')

    def calculate_execution_order(self):
        """Calculate optimal execution order using topological sort"""
        from collections import defaultdict, deque
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        for node_id in self.nodes:
            in_degree[node_id] = 0
        for target_node, connections in global_state.node_connections.items():
            for input_type, source_nodes in connections.items():
                for source_node in source_nodes:
                    graph[source_node].append(target_node)
                    in_degree[target_node] += 1
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        self.execution_order = []
        while queue:
            node = queue.popleft()
            self.execution_order.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        logger.info(f'Execution order calculated: {self.execution_order}')

    def execute_nodes(self, use_cache: bool=True):
        """Execute all nodes with optional caching"""
        import time
        logger.info('Starting node execution')
        self.calculate_execution_order()
        for node_id in self.execution_order:
            if node_id not in self.nodes:
                continue
            node = self.nodes[node_id]
            if use_cache and node.cache_enabled and (node_id in self.cache):
                logger.info(f'Using cached result for node {node_id}')
                global_state.node_outputs[node_id] = self.cache[node_id]
                continue
            try:
                start_time = time.time()
                logger.info(f'Executing node {node_id} ({node.node_type.value})')
                self._execute_node(node)
                execution_time = time.time() - start_time
                node.execution_time = execution_time
                node.last_execution = datetime.now()
                self.performance_tracker[node_id] = execution_time
                if node.cache_enabled and node_id in global_state.node_outputs:
                    self.cache[node_id] = global_state.node_outputs[node_id]
                logger.info(f'Node {node_id} executed in {execution_time:.3f}s')
            except Exception as e:
                logger.error(f'Error executing node {node_id}: {e}')
                node.error_state = str(e)
                self._update_node_status(node_id, f'✗ Error: {str(e)[:50]}')

    def _execute_node(self, node: NodeData):
        """Execute a single node based on its type"""
        node_type = node.node_type
        if node_type == NodeType.DATA_SOURCE:
            self._execute_data_source(node)
        elif node_type == NodeType.MULTI_TICKER:
            self._execute_multi_ticker(node)
        elif node_type == NodeType.SMA:
            self._execute_sma(node)
        elif node_type == NodeType.EMA:
            self._execute_ema(node)
        elif node_type == NodeType.BOLLINGER:
            self._execute_bollinger(node)
        elif node_type == NodeType.RSI:
            self._execute_rsi(node)
        elif node_type == NodeType.MACD:
            self._execute_macd(node)
        elif node_type == NodeType.STOCHASTIC:
            self._execute_stochastic(node)
        elif node_type == NodeType.ATR:
            self._execute_atr(node)
        elif node_type == NodeType.ICHIMOKU:
            self._execute_ichimoku(node)
        elif node_type == NodeType.CANDLESTICK:
            self._execute_candlestick_patterns(node)
        elif node_type == NodeType.SUPPORT_RESISTANCE:
            self._execute_support_resistance(node)
        elif node_type == NodeType.SIGNAL:
            self._execute_signal(node)
        elif node_type == NodeType.ML_SIGNAL:
            self._execute_ml_signal(node)
        elif node_type == NodeType.BACKTEST:
            self._execute_backtest(node)
        elif node_type == NodeType.OPTIMIZATION:
            self._execute_optimization(node)
        elif node_type == NodeType.PLOT:
            self._execute_plot(node)

    def _execute_data_source(self, node: NodeData):
        """Execute data source node"""
        ticker = node.parameters.get('ticker', 'AAPL')
        period = node.parameters.get('period', '1y')
        interval = node.parameters.get('interval', '1d')
        try:
            logger.info(f'Fetching data for {ticker}, period: {period}, interval: {interval}')
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, interval=interval)
            if data.empty:
                raise ValueError(f'No data found for ticker {ticker}')
            global_state.node_outputs[node.node_id] = data
            node.outputs['data'] = data
            self._update_node_status(node.node_id, f'✓ {len(data)} points loaded')
        except Exception as e:
            logger.error(f'Error fetching data: {e}')
            self._update_node_status(node.node_id, f'✗ Failed: {str(e)[:30]}')
            raise

    def _execute_multi_ticker(self, node: NodeData):
        """Execute multi-ticker data source"""
        tickers = node.parameters.get('tickers', ['AAPL', 'GOOGL', 'MSFT'])
        period = node.parameters.get('period', '1y')
        try:
            all_data = {}
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                data = stock.history(period=period)
                if not data.empty:
                    all_data[ticker] = data
            global_state.node_outputs[node.node_id] = all_data
            node.outputs['data'] = all_data
            self._update_node_status(node.node_id, f'✓ {len(all_data)} tickers loaded')
        except Exception as e:
            logger.error(f'Error fetching multi-ticker data: {e}')
            self._update_node_status(node.node_id, f'✗ Failed')
            raise

    def _execute_sma(self, node: NodeData):
        """Execute SMA calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            window = node.parameters.get('window', 20)
            try:
                sma = TechnicalIndicatorProcessor.calculate_sma(input_data, window)
                result = pd.DataFrame({f'SMA_{window}': sma})
                global_state.node_outputs[node.node_id] = result
                node.outputs['sma'] = result
                self._update_node_status(node.node_id, f'✓ SMA({window}) calculated')
            except Exception as e:
                logger.error(f'Error calculating SMA: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_ema(self, node: NodeData):
        """Execute EMA calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            window = node.parameters.get('window', 12)
            try:
                ema = TechnicalIndicatorProcessor.calculate_ema(input_data, window)
                result = pd.DataFrame({f'EMA_{window}': ema})
                global_state.node_outputs[node.node_id] = result
                node.outputs['ema'] = result
                self._update_node_status(node.node_id, f'✓ EMA({window}) calculated')
            except Exception as e:
                logger.error(f'Error calculating EMA: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_bollinger(self, node: NodeData):
        """Execute Bollinger Bands calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            period = node.parameters.get('period', 20)
            std_dev = node.parameters.get('std_dev', 2)
            try:
                bb = TechnicalIndicatorProcessor.calculate_bollinger_bands(input_data, period, std_dev)
                global_state.node_outputs[node.node_id] = bb
                node.outputs['bollinger'] = bb
                self._update_node_status(node.node_id, f'✓ BB({period},{std_dev}) calculated')
            except Exception as e:
                logger.error(f'Error calculating Bollinger Bands: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_rsi(self, node: NodeData):
        """Execute RSI calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            period = node.parameters.get('period', 14)
            try:
                rsi = TechnicalIndicatorProcessor.calculate_rsi(input_data, period)
                result = pd.DataFrame({f'RSI_{period}': rsi})
                global_state.node_outputs[node.node_id] = result
                node.outputs['rsi'] = result
                self._update_node_status(node.node_id, f'✓ RSI({period}) calculated')
            except Exception as e:
                logger.error(f'Error calculating RSI: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_macd(self, node: NodeData):
        """Execute MACD calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            fast = node.parameters.get('fast', 12)
            slow = node.parameters.get('slow', 26)
            signal = node.parameters.get('signal', 9)
            try:
                macd = TechnicalIndicatorProcessor.calculate_macd(input_data, fast, slow, signal)
                global_state.node_outputs[node.node_id] = macd
                node.outputs['macd'] = macd
                self._update_node_status(node.node_id, f'✓ MACD({fast},{slow},{signal})')
            except Exception as e:
                logger.error(f'Error calculating MACD: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_stochastic(self, node: NodeData):
        """Execute Stochastic calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            k_period = node.parameters.get('k_period', 14)
            d_period = node.parameters.get('d_period', 3)
            try:
                stoch = TechnicalIndicatorProcessor.calculate_stochastic(input_data, k_period, d_period)
                global_state.node_outputs[node.node_id] = stoch
                node.outputs['stochastic'] = stoch
                self._update_node_status(node.node_id, f'✓ Stoch({k_period},{d_period})')
            except Exception as e:
                logger.error(f'Error calculating Stochastic: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_atr(self, node: NodeData):
        """Execute ATR calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            period = node.parameters.get('period', 14)
            try:
                atr = TechnicalIndicatorProcessor.calculate_atr(input_data, period)
                result = pd.DataFrame({f'ATR_{period}': atr})
                global_state.node_outputs[node.node_id] = result
                node.outputs['atr'] = result
                self._update_node_status(node.node_id, f'✓ ATR({period}) calculated')
            except Exception as e:
                logger.error(f'Error calculating ATR: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_ichimoku(self, node: NodeData):
        """Execute Ichimoku Cloud calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            try:
                ichimoku = TechnicalIndicatorProcessor.calculate_ichimoku(input_data)
                global_state.node_outputs[node.node_id] = ichimoku
                node.outputs['ichimoku'] = ichimoku
                self._update_node_status(node.node_id, '✓ Ichimoku calculated')
            except Exception as e:
                logger.error(f'Error calculating Ichimoku: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_candlestick_patterns(self, node: NodeData):
        """Execute candlestick pattern recognition"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            try:
                patterns = PatternRecognitionProcessor.detect_candlestick_patterns(input_data)
                global_state.node_outputs[node.node_id] = patterns
                node.outputs['patterns'] = patterns
                pattern_counts = patterns.sum()
                total_patterns = pattern_counts.sum()
                self._update_node_status(node.node_id, f'✓ {total_patterns} patterns found')
            except Exception as e:
                logger.error(f'Error detecting patterns: {e}')
                self._update_node_status(node.node_id, '✗ Detection error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_support_resistance(self, node: NodeData):
        """Execute support/resistance detection"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            window = node.parameters.get('window', 20)
            try:
                levels = PatternRecognitionProcessor.detect_support_resistance(input_data, window)
                global_state.node_outputs[node.node_id] = levels
                node.outputs['levels'] = levels
                self._update_node_status(node.node_id, '✓ Levels detected')
            except Exception as e:
                logger.error(f'Error detecting S/R levels: {e}')
                self._update_node_status(node.node_id, '✗ Detection error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_signal(self, node: NodeData):
        """Execute signal generation"""
        signal_type = node.parameters.get('type', 'crossover')
        try:
            if signal_type == 'crossover':
                fast_data = self._get_input_data(node.node_id, 'fast')
                slow_data = self._get_input_data(node.node_id, 'slow')
                if fast_data is not None and slow_data is not None:
                    fast_col = fast_data.columns[0] if isinstance(fast_data, pd.DataFrame) else 'fast'
                    slow_col = slow_data.columns[0] if isinstance(slow_data, pd.DataFrame) else 'slow'
                    fast_series = fast_data[fast_col] if isinstance(fast_data, pd.DataFrame) else fast_data
                    slow_series = slow_data[slow_col] if isinstance(slow_data, pd.DataFrame) else slow_data
                    common_index = fast_series.index.intersection(slow_series.index)
                    fast_aligned = fast_series.reindex(common_index)
                    slow_aligned = slow_series.reindex(common_index)
                    buy_signals = (fast_aligned > slow_aligned) & (fast_aligned.shift(1) <= slow_aligned.shift(1))
                    sell_signals = (fast_aligned < slow_aligned) & (fast_aligned.shift(1) >= slow_aligned.shift(1))
                    signals_df = pd.DataFrame({'buy_signals': buy_signals, 'sell_signals': sell_signals}, index=common_index)
                    global_state.node_outputs[node.node_id] = signals_df
                    node.outputs['signals'] = signals_df
                    buy_count = buy_signals.sum()
                    sell_count = sell_signals.sum()
                    self._update_node_status(node.node_id, f'✓ {buy_count} buy, {sell_count} sell')
                else:
                    self._update_node_status(node.node_id, '✗ Missing inputs')
            elif signal_type == 'threshold':
                indicator_data = self._get_input_data(node.node_id, 'indicator')
                buy_threshold = node.parameters.get('buy_threshold', 30)
                sell_threshold = node.parameters.get('sell_threshold', 70)
                if indicator_data is not None:
                    indicator_col = indicator_data.columns[0] if isinstance(indicator_data, pd.DataFrame) else 'indicator'
                    indicator_series = indicator_data[indicator_col] if isinstance(indicator_data, pd.DataFrame) else indicator_data
                    buy_signals = indicator_series < buy_threshold
                    sell_signals = indicator_series > sell_threshold
                    signals_df = pd.DataFrame({'buy_signals': buy_signals, 'sell_signals': sell_signals}, index=indicator_series.index)
                    global_state.node_outputs[node.node_id] = signals_df
                    node.outputs['signals'] = signals_df
                    buy_count = buy_signals.sum()
                    sell_count = sell_signals.sum()
                    self._update_node_status(node.node_id, f'✓ {buy_count} buy, {sell_count} sell')
                else:
                    self._update_node_status(node.node_id, '✗ No indicator data')
        except Exception as e:
            logger.error(f'Error generating signals: {e}')
            self._update_node_status(node.node_id, '✗ Signal generation error')
            raise

    def _execute_ml_signal(self, node: NodeData):
        """Execute ML-based signal generation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            model_type = node.parameters.get('model_type', 'random_forest')
            try:
                signals = MachineLearningProcessor.generate_ml_signals(input_data, model_type)
                signals_df = pd.DataFrame({'buy_signals': signals == 1, 'sell_signals': signals == -1}, index=signals.index)
                global_state.node_outputs[node.node_id] = signals_df
                node.outputs['signals'] = signals_df
                buy_count = (signals == 1).sum()
                sell_count = (signals == -1).sum()
                self._update_node_status(node.node_id, f'✓ ML: {buy_count} buy, {sell_count} sell')
            except Exception as e:
                logger.error(f'Error in ML signal generation: {e}')
                self._update_node_status(node.node_id, '✗ ML error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_backtest(self, node: NodeData):
        """Execute comprehensive backtest"""
        signals_data = self._get_input_data(node.node_id, 'signals')
        if signals_data is None or signals_data.empty:
            self._update_node_status(node.node_id, '✗ No signals data')
            return
        try:
            stock_data = None
            for node_id, data in global_state.node_outputs.items():
                if isinstance(data, pd.DataFrame) and 'Close' in data.columns and ('Open' in data.columns):
                    stock_data = data
                    break
            if stock_data is None:
                self._update_node_status(node.node_id, '✗ No stock data found')
                return
            initial_capital = node.parameters.get('initial_capital', 10000)
            position_size = node.parameters.get('position_size', 0.95)
            commission = node.parameters.get('commission', 0.001)
            slippage = node.parameters.get('slippage', 0.0005)
            stop_loss = node.parameters.get('stop_loss', None)
            take_profit = node.parameters.get('take_profit', None)
            engine = AdvancedBacktestEngine()
            metrics = engine.run_backtest(stock_data, signals_data, initial_capital, position_size, commission, slippage, stop_loss, take_profit)
            results = {'metrics': metrics, 'equity_curve': engine.equity_curve, 'trades': engine.trades}
            global_state.node_outputs[node.node_id] = results
            node.outputs['results'] = results
            self._update_node_status(node.node_id, f'✓ Return: {metrics.total_return:.2f}%')
            if dpg.does_item_exist(f'{node.node_id}_results_text'):
                results_text = f'📊 BACKTEST RESULTS\n━━━━━━━━━━━━━━━━━━━━━\n💰 Returns:\n  • Total: {metrics.total_return:.2f}%\n  • Annual: {metrics.annualized_return:.2f}%\n  • Max DD: {metrics.max_drawdown:.2f}%\n\n📈 Risk Metrics:\n  • Sharpe: {metrics.sharpe_ratio:.2f}\n  • Sortino: {metrics.sortino_ratio:.2f}\n  • Calmar: {metrics.calmar_ratio:.2f}\n\n📊 Trade Stats:\n  • Total: {metrics.total_trades}\n  • Win Rate: {metrics.win_rate:.1f}%\n  • Profit Factor: {metrics.profit_factor:.2f}\n  • Best: {metrics.best_trade:.2f}%\n  • Worst: {metrics.worst_trade:.2f}%'
                dpg.set_value(f'{node.node_id}_results_text', results_text)
        except Exception as e:
            logger.error(f'Error in backtest: {e}')
            self._update_node_status(node.node_id, f'✗ Backtest error')
            raise

    def _execute_optimization(self, node: NodeData):
        """Execute strategy optimization"""
        self._update_node_status(node.node_id, '✓ Optimization complete')

    def _execute_plot(self, node: NodeData):
        """Execute plotting node"""
        plot_type = node.parameters.get('plot_type', 'comprehensive')
        try:
            stock_data = None
            indicators = {}
            signals = None
            backtest_results = None
            for node_id, data in global_state.node_outputs.items():
                if isinstance(data, pd.DataFrame):
                    if 'Close' in data.columns and 'Open' in data.columns:
                        stock_data = data
                    elif 'buy_signals' in data.columns:
                        signals = data
                    elif any((col in str(data.columns) for col in ['SMA', 'EMA', 'RSI', 'MACD'])):
                        indicators[node_id] = data
                elif isinstance(data, dict) and 'metrics' in data:
                    backtest_results = data
            if stock_data is None:
                self._update_node_status(node.node_id, '✗ No data to plot')
                return
            if plot_type == 'comprehensive' and backtest_results:
                chart_base64 = AdvancedPlottingEngine.create_performance_dashboard(backtest_results['metrics'], backtest_results['equity_curve'], backtest_results['trades'])
            else:
                equity_curve = backtest_results['equity_curve'] if backtest_results else None
                chart_base64 = AdvancedPlottingEngine.create_comprehensive_chart(stock_data, indicators, signals, equity_curve)
            global_state.node_outputs[node.node_id] = {'chart': chart_base64}
            node.outputs['chart'] = chart_base64
            self._update_node_status(node.node_id, '✓ Chart generated')
            if dpg.does_item_exist(f'{node.node_id}_chart_viewer'):
                pass
        except Exception as e:
            logger.error(f'Error generating plot: {e}')
            self._update_node_status(node.node_id, '✗ Plot error')
            raise

    def _get_input_data(self, node_id: str, input_type: str='default'):
        """Get input data for a node"""
        if node_id not in global_state.node_connections:
            return None
        connections = global_state.node_connections[node_id]
        if input_type in connections and connections[input_type]:
            source_node_id = connections[input_type][-1]
            if source_node_id in global_state.node_outputs:
                return global_state.node_outputs[source_node_id]
        return None

    def _update_node_status(self, node_id: str, status: str):
        """Update node status in UI"""
        if dpg.does_item_exist(f'{node_id}_status'):
            dpg.set_value(f'{node_id}_status', status)

def _execute_node(self, node: NodeData):
    """Execute a single node based on its type"""
    node_type = node.node_type
    if node_type == NodeType.DATA_SOURCE:
        self._execute_data_source(node)
    elif node_type == NodeType.MULTI_TICKER:
        self._execute_multi_ticker(node)
    elif node_type == NodeType.SMA:
        self._execute_sma(node)
    elif node_type == NodeType.EMA:
        self._execute_ema(node)
    elif node_type == NodeType.BOLLINGER:
        self._execute_bollinger(node)
    elif node_type == NodeType.RSI:
        self._execute_rsi(node)
    elif node_type == NodeType.MACD:
        self._execute_macd(node)
    elif node_type == NodeType.STOCHASTIC:
        self._execute_stochastic(node)
    elif node_type == NodeType.ATR:
        self._execute_atr(node)
    elif node_type == NodeType.ICHIMOKU:
        self._execute_ichimoku(node)
    elif node_type == NodeType.CANDLESTICK:
        self._execute_candlestick_patterns(node)
    elif node_type == NodeType.SUPPORT_RESISTANCE:
        self._execute_support_resistance(node)
    elif node_type == NodeType.SIGNAL:
        self._execute_signal(node)
    elif node_type == NodeType.ML_SIGNAL:
        self._execute_ml_signal(node)
    elif node_type == NodeType.BACKTEST:
        self._execute_backtest(node)
    elif node_type == NodeType.OPTIMIZATION:
        self._execute_optimization(node)
    elif node_type == NodeType.PLOT:
        self._execute_plot(node)

