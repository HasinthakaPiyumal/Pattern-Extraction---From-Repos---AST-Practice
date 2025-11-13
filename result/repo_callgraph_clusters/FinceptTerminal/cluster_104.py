# Cluster 104

class ML4TFramework:
    """Main orchestrator for the ML4T framework"""

    def __init__(self, config: ML4TConfig=None):
        self.config = config or ML4TConfig()
        self.logger = ML4TLogger('ML4TFramework')
        self.data_manager = DataManager(self.config)
        self.alpha_engine = AlphaFactorEngine(self.config)
        self.portfolio_optimizer = PortfolioOptimizer(self.config)
        self.backtest_engine = BacktestEngine(self.config)
        self.visualizer = ML4TVisualizer(self.config)
        self.data = {}
        self.factors = {}
        self.models = {}
        self.strategies = {}
        self.results = {}

    def load_data(self, symbols: List[str], start_date: str, end_date: str, include_fundamental: bool=True, include_alternative: bool=True):
        """Load all required data"""
        self.logger.info('Loading market data...')
        self.data['market'] = self.data_manager.load_market_data(symbols, start_date, end_date)
        if include_fundamental:
            self.logger.info('Loading fundamental data...')
            self.data['fundamental'] = self.data_manager.load_fundamental_data(symbols)
        if include_alternative:
            self.logger.info('Loading alternative data...')
            self.data['alternative'] = {'sentiment': self.data_manager.load_alternative_data('sentiment'), 'social': self.data_manager.load_alternative_data('social')}

    def engineer_features(self, symbols: List[str]):
        """Generate comprehensive feature set"""
        self.logger.info('Engineering features...')
        all_features = []
        for symbol in symbols:
            technical_data = self.alpha_engine.calculate_technical_factors(self.data['market'], symbol)
            if 'fundamental' in self.data:
                fundamental_data = self.alpha_engine.calculate_fundamental_factors(technical_data, self.data['fundamental'])
            else:
                fundamental_data = technical_data
            if 'alternative' in self.data:
                final_data = self.alpha_engine.calculate_alternative_factors(fundamental_data, self.data['alternative'])
            else:
                final_data = fundamental_data
            all_features.append(final_data)
        self.factors['engineered'] = pd.concat(all_features, ignore_index=True)
        self.factors['engineered'] = self.factors['engineered'].sort_values(['symbol', 'date'])
        self.factors['engineered']['future_returns'] = self.factors['engineered'].groupby('symbol')['returns'].shift(-1)
        self.factors['engineered'] = self.factors['engineered'].dropna(subset=['future_returns'])
        return self.factors['engineered']

    def train_models(self, feature_data: pd.DataFrame, models_config: List[Dict]):
        """Train multiple ML models"""
        self.logger.info('Training models...')
        feature_columns = [col for col in feature_data.columns if col not in ['date', 'symbol', 'future_returns', 'open', 'high', 'low', 'close', 'volume']]
        X = feature_data[feature_columns].fillna(0)
        y = feature_data['future_returns'].fillna(0)
        for model_config in models_config:
            model_name = model_config['name']
            model_type = model_config['type']
            model_params = model_config.get('params', {})
            self.logger.info(f'Training {model_name} ({model_type})...')
            if model_type in ['linear', 'ridge', 'lasso', 'logistic']:
                model = LinearModel(self.config, model_type, **model_params)
            elif model_type in ['random_forest', 'gradient_boosting']:
                model = TreeBasedModel(self.config, model_type, **model_params)
            elif model_type in ['arima']:
                model = TimeSeriesModel(self.config, model_type, **model_params)
            else:
                self.logger.warning(f'Unknown model type: {model_type}')
                continue
            model.fit(X, y)
            self.models[model_name] = model
            self.logger.info(f'Model {model_name} trained successfully')

    def create_strategies(self, strategy_configs: List[Dict]):
        """Create trading strategies"""
        self.logger.info('Creating strategies...')
        for strategy_config in strategy_configs:
            strategy_name = strategy_config['name']
            strategy_type = strategy_config['type']
            strategy_params = strategy_config.get('params', {})
            if strategy_type == 'mean_reversion':
                strategy = MeanReversionStrategy(self.config, **strategy_params)
            elif strategy_type == 'momentum':
                strategy = MomentumStrategy(self.config, **strategy_params)
            elif strategy_type == 'ml_strategy':
                model_name = strategy_params.get('model_name')
                if model_name in self.models:
                    features = strategy_params.get('features', [])
                    strategy = MLStrategy(self.config, self.models[model_name], features)
                else:
                    self.logger.warning(f'Model {model_name} not found for ML strategy')
                    continue
            else:
                self.logger.warning(f'Unknown strategy type: {strategy_type}')
                continue
            self.strategies[strategy_name] = strategy
            self.logger.info(f'Strategy {strategy_name} created successfully')

    def run_backtests(self):
        """Run backtests for all strategies"""
        self.logger.info('Running backtests...')
        for strategy_name, strategy in self.strategies.items():
            self.logger.info(f'Backtesting strategy: {strategy_name}')
            signals = strategy.generate_signals(self.factors['engineered'])
            backtest_results = self.backtest_engine.run_backtest(signals, self.data['market'], self.config.initial_capital)
            self.results[strategy_name] = backtest_results
            metrics = backtest_results['metrics']
            self.logger.info(f'Strategy {strategy_name} - Sharpe: {metrics['sharpe_ratio']:.3f}, Return: {metrics['annualized_return']:.3f}, MaxDD: {metrics['max_drawdown']:.3f}')

    def generate_report(self):
        """Generate comprehensive performance report"""
        self.logger.info('Generating performance report...')
        summary_data = []
        for strategy_name, results in self.results.items():
            metrics = results['metrics']
            summary_data.append({'Strategy': strategy_name, 'Total Return': f'{metrics['total_return']:.2%}', 'Annualized Return': f'{metrics['annualized_return']:.2%}', 'Volatility': f'{metrics['annualized_volatility']:.2%}', 'Sharpe Ratio': f'{metrics['sharpe_ratio']:.3f}', 'Max Drawdown': f'{metrics['max_drawdown']:.2%}', 'Calmar Ratio': f'{metrics['calmar_ratio']:.3f}'})
        summary_df = pd.DataFrame(summary_data)
        print('\n' + '=' * 80)
        print('ML4T FRAMEWORK - PERFORMANCE SUMMARY')
        print('=' * 80)
        print(summary_df.to_string(index=False))
        print('=' * 80)
        return summary_df

    def visualize_results(self, strategy_name: str=None):
        """Create visualizations for results"""
        if strategy_name is None:
            for name in self.results.keys():
                self.visualizer.plot_portfolio_performance(self.results[name])
        elif strategy_name in self.results:
            self.visualizer.plot_portfolio_performance(self.results[strategy_name])
        else:
            self.logger.warning(f'Strategy {strategy_name} not found in results')

def load_data(self, symbols: List[str], start_date: str, end_date: str, include_fundamental: bool=True, include_alternative: bool=True):
    """Load all required data"""
    self.logger.info('Loading market data...')
    self.data['market'] = self.data_manager.load_market_data(symbols, start_date, end_date)
    if include_fundamental:
        self.logger.info('Loading fundamental data...')
        self.data['fundamental'] = self.data_manager.load_fundamental_data(symbols)
    if include_alternative:
        self.logger.info('Loading alternative data...')
        self.data['alternative'] = {'sentiment': self.data_manager.load_alternative_data('sentiment'), 'social': self.data_manager.load_alternative_data('social')}

