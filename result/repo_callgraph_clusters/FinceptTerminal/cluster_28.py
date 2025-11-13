# Cluster 28

class PortfolioAnalyticsEngine:
    """
    Advanced Portfolio Analytics Engine using skfolio

    Features:
    - Multiple optimization methods
    - Risk management and analysis
    - Stress testing and scenario analysis
    - Performance attribution
    - Interactive visualizations
    - Backtesting capabilities
    """

    def __init__(self, config: PortfolioConfig=None):
        self.config = config or PortfolioConfig()
        self.prices = None
        self.returns = None
        self.factors = None
        self.factor_returns = None
        self.model = None
        self.portfolio = None
        self.backtest_results = {}
        self.optimization_history = []

    def load_data(self, prices: pd.DataFrame, factors: pd.DataFrame=None, start_date: str=None, end_date: str=None) -> None:
        """
        Load price and factor data

        Parameters:
        -----------
        prices : pd.DataFrame
            Asset prices with datetime index and asset columns
        factors : pd.DataFrame, optional
            Factor data with datetime index
        start_date, end_date : str, optional
            Date range for analysis
        """
        if start_date or end_date:
            if start_date:
                prices = prices[prices.index >= start_date]
                if factors is not None:
                    factors = factors[factors.index >= start_date]
            if end_date:
                prices = prices[prices.index <= end_date]
                if factors is not None:
                    factors = factors[factors.index <= end_date]
        self.prices = prices
        self.returns = prices_to_returns(prices)
        if factors is not None:
            self.factors = factors
            self.factor_returns = prices_to_returns(factors) if 'price' in str(factors.columns).lower() else factors
        print(f'Data loaded: {len(self.prices)} periods, {len(self.prices.columns)} assets')
        if factors is not None:
            print(f'Factor data: {len(self.factors.columns)} factors')

    def _get_estimators(self) -> Tuple[Any, Any]:
        """Get covariance and mu estimators based on config"""
        covariance_estimators = {'empirical': None, 'ledoit_wolf': LedoitWolf(), 'gerber': GerberCovariance(), 'denoise': DenoiseCovariance(), 'detone': DetoneCovariance()}
        mu_estimators = {'empirical': None, 'shrunk': ShrunkMu(), 'ew': EWMu(alpha=0.2)}
        cov_est = covariance_estimators.get(self.config.covariance_estimator)
        mu_est = mu_estimators.get(self.config.mu_estimator)
        return (cov_est, mu_est)

    def _build_prior_estimator(self) -> Any:
        """Build prior estimator based on configuration"""
        cov_est, mu_est = self._get_estimators()
        empirical_prior = EmpiricalPrior(mu_estimator=mu_est, covariance_estimator=cov_est)
        if self.config.views:
            return BlackLitterman(views=self.config.views, tau=self.config.tau, prior_estimator=empirical_prior)
        if self.config.use_factor_model and self.factor_returns is not None:
            factor_prior = BlackLitterman(views=self.config.factor_views, tau=self.config.tau) if self.config.factor_views else empirical_prior
            return FactorModel(factor_prior_estimator=factor_prior)
        return empirical_prior

    def _build_model(self) -> Any:
        """Build optimization model based on configuration"""
        obj_functions = {'minimize_risk': ObjectiveFunction.MINIMIZE_RISK, 'maximize_return': ObjectiveFunction.MAXIMIZE_RETURN, 'maximize_ratio': ObjectiveFunction.MAXIMIZE_RATIO, 'maximize_utility': ObjectiveFunction.MAXIMIZE_UTILITY}
        risk_measures = {'variance': RiskMeasure.VARIANCE, 'semi_variance': RiskMeasure.SEMI_VARIANCE, 'cvar': RiskMeasure.CVAR, 'evar': RiskMeasure.EVAR, 'max_drawdown': RiskMeasure.MAX_DRAWDOWN, 'cdar': RiskMeasure.CDAR, 'ulcer_index': RiskMeasure.ULCER_INDEX}
        prior_estimator = self._build_prior_estimator()
        uncertainty_set = BootstrapMuUncertaintySet() if self.config.use_uncertainty_set else None
        if self.config.optimization_method == 'mean_risk':
            model = MeanRisk(objective_function=obj_functions[self.config.objective_function], risk_measure=risk_measures[self.config.risk_measure], prior_estimator=prior_estimator, mu_uncertainty_set_estimator=uncertainty_set, min_weights=self.config.min_weights, max_weights=self.config.max_weights, transaction_costs=self.config.transaction_costs, l1_coef=self.config.l1_coef, l2_coef=self.config.l2_coef, risk_aversion=self.config.risk_aversion)
        elif self.config.optimization_method == 'risk_parity':
            model = RiskBudgeting(risk_measure=risk_measures[self.config.risk_measure], prior_estimator=prior_estimator, min_weights=self.config.min_weights, max_weights=self.config.max_weights)
        elif self.config.optimization_method == 'hrp':
            model = HierarchicalRiskParity(risk_measure=risk_measures[self.config.risk_measure], prior_estimator=prior_estimator, linkage_method=self.config.linkage_method)
        elif self.config.optimization_method == 'max_div':
            model = MaximumDiversification(prior_estimator=prior_estimator, min_weights=self.config.min_weights, max_weights=self.config.max_weights)
        elif self.config.optimization_method == 'equal_weight':
            model = EqualWeighted()
        elif self.config.optimization_method == 'inverse_vol':
            model = InverseVolatility(prior_estimator=prior_estimator)
        else:
            raise ValueError(f'Unknown optimization method: {self.config.optimization_method}')
        return model

    def optimize_portfolio(self, train_size: float=None, verbose: bool=True) -> Dict[str, Any]:
        """
        Optimize portfolio using configured parameters

        Returns:
        --------
        Dict with optimization results
        """
        if self.returns is None:
            raise ValueError('No data loaded. Call load_data() first.')
        train_size = train_size or self.config.train_test_split_ratio
        if self.factor_returns is not None:
            X_train, X_test, factors_train, factors_test = train_test_split(self.returns, self.factor_returns, test_size=1 - train_size, shuffle=False)
        else:
            X_train, X_test = train_test_split(self.returns, test_size=1 - train_size, shuffle=False)
            factors_train = factors_test = None
        self.model = self._build_model()
        if factors_train is not None:
            self.model.fit(X_train, factors_train)
        else:
            self.model.fit(X_train)
        self.portfolio = self.model.predict(X_test)
        results = {'weights': dict(zip(self.returns.columns, self.model.weights_)), 'train_period': (X_train.index[0], X_train.index[-1]), 'test_period': (X_test.index[0], X_test.index[-1]), 'model_type': self.config.optimization_method, 'objective': self.config.objective_function, 'risk_measure': self.config.risk_measure}
        if hasattr(self.portfolio, 'sharpe_ratio'):
            results.update({'sharpe_ratio': self.portfolio.sharpe_ratio, 'sortino_ratio': getattr(self.portfolio, 'sortino_ratio', None), 'calmar_ratio': getattr(self.portfolio, 'calmar_ratio', None), 'max_drawdown': getattr(self.portfolio, 'max_drawdown', None), 'volatility': getattr(self.portfolio, 'annualized_volatility', None), 'return': getattr(self.portfolio, 'annualized_mean', None)})
        self.optimization_history.append(results)
        if verbose:
            print(f'\nPortfolio Optimization Complete:')
            print(f'Method: {self.config.optimization_method}')
            print(f'Objective: {self.config.objective_function}')
            print(f'Risk Measure: {self.config.risk_measure}')
            print(f'Training Period: {results['train_period'][0]} to {results['train_period'][1]}')
            print(f'Test Period: {results['test_period'][0]} to {results['test_period'][1]}')
            if 'sharpe_ratio' in results:
                print(f'Sharpe Ratio: {results['sharpe_ratio']:.4f}')
        return results

    def hyperparameter_tuning(self, param_grid: Dict=None, cv_method: str=None, scoring=None, n_jobs: int=-1) -> Dict[str, Any]:
        """
        Perform hyperparameter tuning using grid search or random search

        Parameters:
        -----------
        param_grid : dict
            Parameter grid for tuning
        cv_method : str
            Cross-validation method
        scoring : str
            Scoring metric
        n_jobs : int
            Number of parallel jobs
        """
        if param_grid is None:
            param_grid = {'l1_coef': [0.0, 0.001, 0.01, 0.1], 'l2_coef': [0.0, 0.001, 0.01, 0.1], 'risk_aversion': [0.5, 1.0, 2.0, 5.0]}
        cv_method = cv_method or self.config.cv_method
        if cv_method == 'walk_forward':
            cv = WalkForward(train_size=self.config.lookback_window, test_size=self.config.rebalance_frequency)
        elif cv_method == 'combinatorial_purged':
            cv = CombinatorialPurgedCV(n_folds=self.config.cv_folds)
        else:
            cv = KFold(n_splits=self.config.cv_folds, shuffle=False)
        grid_search = GridSearchCV(estimator=self._build_model(), param_grid=param_grid, cv=cv, n_jobs=n_jobs, verbose=1)
        if self.factor_returns is not None:
            grid_search.fit(self.returns, self.factor_returns)
        else:
            grid_search.fit(self.returns)
        self.model = grid_search.best_estimator_
        return {'best_params': grid_search.best_params_, 'best_score': grid_search.best_score_, 'cv_results': grid_search.cv_results_}

    def backtest_strategy(self, rebalance_freq: int=None, window_size: int=None, start_date: str=None, end_date: str=None) -> pd.DataFrame:
        """
        Backtest the portfolio strategy using walk-forward analysis

        Parameters:
        -----------
        rebalance_freq : int
            Rebalancing frequency in days
        window_size : int
            Rolling window size for optimization
        start_date, end_date : str
            Backtest date range

        Returns:
        --------
        DataFrame with backtest results
        """
        rebalance_freq = rebalance_freq or self.config.rebalance_frequency
        window_size = window_size or self.config.lookback_window
        returns_data = self.returns.copy()
        if start_date:
            returns_data = returns_data[returns_data.index >= start_date]
        if end_date:
            returns_data = returns_data[returns_data.index <= end_date]
        backtest_dates = []
        portfolio_returns = []
        weights_history = []
        for i in range(window_size, len(returns_data), rebalance_freq):
            train_data = returns_data.iloc[i - window_size:i]
            model = self._build_model()
            try:
                if self.factor_returns is not None:
                    factor_data = self.factor_returns.iloc[i - window_size:i]
                    model.fit(train_data, factor_data)
                else:
                    model.fit(train_data)
                weights = pd.Series(model.weights_, index=train_data.columns)
                weights_history.append(weights)
                end_idx = min(i + rebalance_freq, len(returns_data))
                forward_returns = returns_data.iloc[i:end_idx]
                ptf_returns = (forward_returns * weights).sum(axis=1)
                portfolio_returns.extend(ptf_returns.values)
                backtest_dates.extend(forward_returns.index)
            except Exception as e:
                print(f'Error at period {i}: {e}')
                continue
        backtest_df = pd.DataFrame({'date': backtest_dates, 'portfolio_return': portfolio_returns}).set_index('date')
        backtest_df['cumulative_return'] = (1 + backtest_df['portfolio_return']).cumprod()
        backtest_df['drawdown'] = backtest_df['cumulative_return'] / backtest_df['cumulative_return'].expanding().max() - 1
        self.backtest_results = {'returns': backtest_df, 'weights_history': weights_history, 'metrics': self._calculate_performance_metrics(backtest_df['portfolio_return'])}
        return backtest_df

    def stress_test(self, scenarios: Dict[str, Dict]=None, n_simulations: int=10000) -> Dict[str, Any]:
        """
        Perform stress testing using various scenarios

        Parameters:
        -----------
        scenarios : dict
            Stress test scenarios
        n_simulations : int
            Number of Monte Carlo simulations
        """
        if self.model is None:
            raise ValueError('No model fitted. Run optimize_portfolio() first.')
        stress_results = {}
        if scenarios is None:
            scenarios = {'market_crash': {'market_shock': -0.2}, 'high_volatility': {'volatility_mult': 2.0}, 'recession': {'gdp_shock': -0.05}, 'inflation_spike': {'inflation_shock': 0.1}}
        if hasattr(self.model, 'prior_estimator_'):
            prior = self.model.prior_estimator_
            vine = VineCopula(log_transform=True, n_jobs=-1)
            vine.fit(self.returns)
            for scenario_name, scenario_params in scenarios.items():
                try:
                    conditioning = scenario_params if 'market_shock' in scenario_params else None
                    synthetic_returns = vine.sample(n_samples=n_simulations, conditioning=conditioning)
                    stressed_portfolio = self.model.predict(synthetic_returns)
                    stress_results[scenario_name] = {'mean_return': synthetic_returns.mean().mean(), 'volatility': synthetic_returns.std().mean(), 'portfolio_var': np.percentile(stressed_portfolio.returns, 5), 'portfolio_cvar': stressed_portfolio.returns[stressed_portfolio.returns <= np.percentile(stressed_portfolio.returns, 5)].mean()}
                except Exception as e:
                    print(f'Error in scenario {scenario_name}: {e}')
                    continue
        return stress_results

    def _calculate_performance_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        returns_annual = returns.mean() * 252
        volatility_annual = returns.std() * np.sqrt(252)
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        metrics = {'annual_return': returns_annual, 'annual_volatility': volatility_annual, 'sharpe_ratio': returns_annual / volatility_annual if volatility_annual > 0 else 0, 'max_drawdown': drawdown.min(), 'calmar_ratio': returns_annual / abs(drawdown.min()) if drawdown.min() < 0 else 0, 'sortino_ratio': returns_annual / (returns[returns < 0].std() * np.sqrt(252)) if len(returns[returns < 0]) > 0 else 0, 'skewness': returns.skew(), 'kurtosis': returns.kurt(), 'var_95': np.percentile(returns, 5), 'cvar_95': returns[returns <= np.percentile(returns, 5)].mean(), 'win_rate': (returns > 0).sum() / len(returns)}
        return metrics

    def plot_weights(self, top_n: int=15, figsize: Tuple[int, int]=(12, 8)) -> go.Figure:
        """Plot portfolio weights"""
        if self.model is None:
            raise ValueError('No model fitted. Run optimize_portfolio() first.')
        weights = pd.Series(self.model.weights_, index=self.returns.columns)
        weights = weights.sort_values(key=abs, ascending=False)[:top_n]
        fig = go.Figure(data=[go.Bar(x=weights.index, y=weights.values, marker_color=['red' if x < 0 else 'blue' for x in weights.values], text=[f'{x:.2%}' for x in weights.values], textposition='outside')])
        fig.update_layout(title=f'Portfolio Weights - {self.config.optimization_method.title()}', xaxis_title='Assets', yaxis_title='Weight', yaxis_tickformat='.1%', height=500)
        return fig

    def plot_efficient_frontier(self, n_portfolios: int=100) -> go.Figure:
        """Plot efficient frontier"""
        if self.returns is None:
            raise ValueError('No data loaded. Call load_data() first.')
        returns_range = np.linspace(self.returns.mean().min() * 252, self.returns.mean().max() * 252, n_portfolios)
        risks = []
        returns_list = []
        for target_return in returns_range:
            try:
                model = MeanRisk(objective_function=ObjectiveFunction.MINIMIZE_RISK, risk_measure=RiskMeasure.VARIANCE, min_return=target_return / 252)
                model.fit(self.returns)
                portfolio_risk = np.sqrt(model.weights_ @ self.returns.cov() @ model.weights_) * np.sqrt(252)
                risks.append(portfolio_risk)
                returns_list.append(target_return)
            except:
                continue
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=risks, y=returns_list, mode='lines+markers', name='Efficient Frontier', line=dict(color='blue', width=2)))
        if self.model is not None:
            current_return = self.portfolio.annualized_mean if hasattr(self.portfolio, 'annualized_mean') else 0
            current_risk = self.portfolio.annualized_volatility if hasattr(self.portfolio, 'annualized_volatility') else 0
            fig.add_trace(go.Scatter(x=[current_risk], y=[current_return], mode='markers', name='Current Portfolio', marker=dict(color='red', size=10, symbol='star')))
        fig.update_layout(title='Efficient Frontier', xaxis_title='Risk (Volatility)', yaxis_title='Expected Return', xaxis_tickformat='.1%', yaxis_tickformat='.1%')
        return fig

    def plot_backtest_results(self) -> go.Figure:
        """Plot backtest results"""
        if not self.backtest_results:
            raise ValueError('No backtest results. Run backtest_strategy() first.')
        df = self.backtest_results['returns']
        fig = make_subplots(rows=2, cols=1, subplot_titles=['Cumulative Returns', 'Drawdown'], vertical_spacing=0.1)
        fig.add_trace(go.Scatter(x=df.index, y=df['cumulative_return'], name='Portfolio', line=dict(color='blue')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['drawdown'], name='Drawdown', fill='tonexty', line=dict(color='red')), row=2, col=1)
        fig.update_layout(height=600, title='Backtest Results')
        fig.update_yaxes(tickformat='.1%', row=1, col=1)
        fig.update_yaxes(tickformat='.1%', row=2, col=1)
        return fig

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive portfolio analytics report"""
        if self.model is None:
            raise ValueError('No model fitted. Run optimize_portfolio() first.')
        report = {'timestamp': datetime.now().isoformat(), 'configuration': {'optimization_method': self.config.optimization_method, 'objective_function': self.config.objective_function, 'risk_measure': self.config.risk_measure, 'covariance_estimator': self.config.covariance_estimator, 'mu_estimator': self.config.mu_estimator}, 'portfolio_weights': dict(zip(self.returns.columns, self.model.weights_)), 'top_10_positions': dict(pd.Series(self.model.weights_, index=self.returns.columns).sort_values(key=abs, ascending=False)[:10]), 'performance_metrics': {}, 'risk_analysis': {}, 'optimization_history': self.optimization_history}
        if hasattr(self.portfolio, 'sharpe_ratio'):
            report['performance_metrics'] = {'sharpe_ratio': self.portfolio.sharpe_ratio, 'sortino_ratio': getattr(self.portfolio, 'sortino_ratio', None), 'calmar_ratio': getattr(self.portfolio, 'calmar_ratio', None), 'max_drawdown': getattr(self.portfolio, 'max_drawdown', None), 'annual_volatility': getattr(self.portfolio, 'annualized_volatility', None), 'annual_return': getattr(self.portfolio, 'annualized_mean', None)}
        portfolio_returns = self.portfolio.returns if hasattr(self.portfolio, 'returns') else None
        if portfolio_returns is not None:
            report['risk_analysis'] = {'var_95': np.percentile(portfolio_returns, 5), 'cvar_95': portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 5)].mean(), 'skewness': portfolio_returns.skew() if hasattr(portfolio_returns, 'skew') else None, 'kurtosis': portfolio_returns.kurtosis() if hasattr(portfolio_returns, 'kurtosis') else None, 'volatility': portfolio_returns.std() * np.sqrt(252)}
        if self.backtest_results:
            report['backtest_results'] = self.backtest_results['metrics']
        return report

    def save_report(self, filename: str=None) -> str:
        """Save portfolio analytics report to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'portfolio_report_{timestamp}.json'
        report = self.generate_report()

        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, pd.Series):
                return obj.to_dict()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict('records')
            return obj

        def recursive_convert(obj):
            if isinstance(obj, dict):
                return {k: recursive_convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [recursive_convert(v) for v in obj]
            else:
                return convert_numpy(obj)
        report_serializable = recursive_convert(report)
        with open(filename, 'w') as f:
            json.dump(report_serializable, f, indent=2, default=str)
        print(f'Report saved to: {filename}')
        return filename

    def export_weights_to_csv(self, filename: str=None) -> str:
        """Export portfolio weights to CSV file"""
        if self.model is None:
            raise ValueError('No model fitted. Run optimize_portfolio() first.')
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'portfolio_weights_{timestamp}.csv'
        weights_df = pd.DataFrame({'Asset': self.returns.columns, 'Weight': self.model.weights_, 'Weight_Percent': self.model.weights_ * 100}).sort_values('Weight', key=abs, ascending=False)
        weights_df.to_csv(filename, index=False)
        print(f'Weights exported to: {filename}')
        return filename

    def compare_strategies(self, strategies: List[Dict[str, Any]], metric: str='sharpe_ratio') -> pd.DataFrame:
        """
        Compare multiple optimization strategies

        Parameters:
        -----------
        strategies : List[Dict]
            List of strategy configurations
        metric : str
            Comparison metric

        Returns:
        --------
        DataFrame with strategy comparison results
        """
        results = []
        for i, strategy_config in enumerate(strategies):
            try:
                temp_config = PortfolioConfig(**strategy_config)
                temp_engine = PortfolioAnalyticsEngine(temp_config)
                temp_engine.load_data(self.prices, self.factors)
                result = temp_engine.optimize_portfolio(verbose=False)
                result['strategy_id'] = f'Strategy_{i + 1}'
                result['config'] = strategy_config
                results.append(result)
            except Exception as e:
                print(f'Error in strategy {i + 1}: {e}')
                continue
        comparison_df = pd.DataFrame(results)
        if metric in comparison_df.columns:
            comparison_df = comparison_df.sort_values(metric, ascending=False)
        return comparison_df

    def risk_attribution(self) -> Dict[str, pd.DataFrame]:
        """
        Perform risk attribution analysis

        Returns:
        --------
        Dictionary with risk attribution results
        """
        if self.model is None:
            raise ValueError('No model fitted. Run optimize_portfolio() first.')
        weights = pd.Series(self.model.weights_, index=self.returns.columns)
        cov_matrix = self.returns.cov() * 252
        portfolio_var = weights.T @ cov_matrix @ weights
        portfolio_vol = np.sqrt(portfolio_var)
        marginal_contrib = cov_matrix @ weights / portfolio_vol
        component_contrib = weights * marginal_contrib
        pct_contrib = component_contrib / portfolio_vol * 100
        risk_attrib_df = pd.DataFrame({'Asset': self.returns.columns, 'Weight': weights.values, 'Weight_Pct': weights.values * 100, 'Marginal_Risk': marginal_contrib.values, 'Component_Risk': component_contrib.values, 'Risk_Contribution_Pct': pct_contrib.values, 'Individual_Vol': np.sqrt(np.diag(cov_matrix)) * 100}).sort_values('Risk_Contribution_Pct', key=abs, ascending=False)
        sector_attrib = None
        if hasattr(self, 'sector_mapping') and self.sector_mapping:
            risk_attrib_df['Sector'] = risk_attrib_df['Asset'].map(self.sector_mapping)
            sector_attrib = risk_attrib_df.groupby('Sector').agg({'Weight_Pct': 'sum', 'Risk_Contribution_Pct': 'sum', 'Component_Risk': 'sum'}).sort_values('Risk_Contribution_Pct', ascending=False)
        return {'asset_attribution': risk_attrib_df, 'sector_attribution': sector_attrib, 'portfolio_volatility': portfolio_vol, 'portfolio_variance': portfolio_var}

    def scenario_analysis(self, scenarios: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Perform scenario analysis with custom return scenarios

        Parameters:
        -----------
        scenarios : Dict[str, pd.DataFrame]
            Dictionary of scenario names and their return DataFrames

        Returns:
        --------
        Dictionary with scenario analysis results
        """
        if self.model is None:
            raise ValueError('No model fitted. Run optimize_portfolio() first.')
        scenario_results = {}
        for scenario_name, scenario_returns in scenarios.items():
            try:
                common_assets = scenario_returns.columns.intersection(self.returns.columns)
                scenario_subset = scenario_returns[common_assets]
                weights_subset = pd.Series(self.model.weights_, index=self.returns.columns)[common_assets]
                weights_subset = weights_subset / weights_subset.sum()
                portfolio_returns = (scenario_subset * weights_subset).sum(axis=1)
                scenario_results[scenario_name] = {'total_return': (1 + portfolio_returns).prod() - 1, 'annualized_return': portfolio_returns.mean() * 252, 'volatility': portfolio_returns.std() * np.sqrt(252), 'sharpe_ratio': portfolio_returns.mean() * 252 / (portfolio_returns.std() * np.sqrt(252)), 'max_drawdown': ((1 + portfolio_returns).cumprod() / (1 + portfolio_returns).cumprod().expanding().max() - 1).min(), 'var_95': np.percentile(portfolio_returns, 5), 'cvar_95': portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 5)].mean(), 'worst_day': portfolio_returns.min(), 'best_day': portfolio_returns.max(), 'n_periods': len(portfolio_returns)}
            except Exception as e:
                print(f'Error in scenario {scenario_name}: {e}')
                scenario_results[scenario_name] = {'error': str(e)}
        return scenario_results

    def set_sector_mapping(self, sector_mapping: Dict[str, str]):
        """Set sector mapping for assets for sector-level analysis"""
        self.sector_mapping = sector_mapping

def _build_prior_estimator(self) -> Any:
    """Build prior estimator based on configuration"""
    cov_est, mu_est = self._get_estimators()
    empirical_prior = EmpiricalPrior(mu_estimator=mu_est, covariance_estimator=cov_est)
    if self.config.views:
        return BlackLitterman(views=self.config.views, tau=self.config.tau, prior_estimator=empirical_prior)
    if self.config.use_factor_model and self.factor_returns is not None:
        factor_prior = BlackLitterman(views=self.config.factor_views, tau=self.config.tau) if self.config.factor_views else empirical_prior
        return FactorModel(factor_prior_estimator=factor_prior)
    return empirical_prior

