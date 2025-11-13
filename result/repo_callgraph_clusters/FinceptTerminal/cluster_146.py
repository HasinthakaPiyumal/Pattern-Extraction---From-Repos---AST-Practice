# Cluster 146

class PortfolioOptimizer:
    """
    Comprehensive Portfolio Optimization Engine using PyPortfolioOpt

    Features:
    - Multiple optimization methods (Mean-Variance, CVaR, Semivariance, etc.)
    - Expected returns calculation methods
    - Risk models with shrinkage estimators
    - Black-Litterman model implementation
    - Hierarchical Risk Parity
    - Efficient frontier plotting
    - Discrete allocation and post-processing
    """

    def __init__(self, business_logic=None):
        """Initialize the portfolio optimizer"""
        if not PYPFOPT_AVAILABLE:
            raise ImportError('PyPortfolioOpt is required but not installed')
        self.business_logic = business_logic
        self.risk_free_rate = 0.02
        self.confidence_level = 0.95
        self.lookback_days = 252
        self.optimization_cache = {}
        self.cache_timeout = 3600
        self.optimization_methods = {'mean_variance': 'Mean-Variance Optimization', 'min_volatility': 'Minimum Volatility', 'max_sharpe': 'Maximum Sharpe Ratio', 'efficient_risk': 'Efficient Risk', 'efficient_return': 'Efficient Return', 'semivariance': 'Efficient Semivariance', 'cvar': 'Conditional Value at Risk', 'cdar': 'Conditional Drawdown at Risk', 'hrp': 'Hierarchical Risk Parity', 'black_litterman': 'Black-Litterman Model', 'cla': 'Critical Line Algorithm'}
        self.expected_returns_methods = {'mean_historical_return': 'Mean Historical Return', 'ema_historical_return': 'Exponentially Weighted Returns', 'capm_return': 'CAPM Expected Returns', 'james_stein': 'James-Stein Estimator'}
        self.risk_model_methods = {'sample_cov': 'Sample Covariance', 'semicovariance': 'Semicovariance', 'exp_cov': 'Exponentially Weighted Covariance', 'ledoit_wolf': 'Ledoit-Wolf Shrinkage', 'oracle_approximating': 'Oracle Approximating Shrinkage'}

    def get_historical_data(self, symbols: List[str], lookback_days: int=None) -> pd.DataFrame:
        """
        Get historical price data for optimization

        Args:
            symbols: List of stock symbols
            lookback_days: Number of days to look back

        Returns:
            DataFrame with historical prices
        """
        try:
            if lookback_days is None:
                lookback_days = self.lookback_days
            if self.business_logic:
                historical_data = {}
                for symbol in symbols:
                    try:
                        import yfinance as yf
                        ticker = yf.Ticker(symbol)
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=lookback_days + 50)
                        hist = ticker.history(start=start_date, end=end_date)
                        if not hist.empty:
                            historical_data[symbol] = hist['Close']
                        else:
                            logger.warning(f'No historical data for {symbol}')
                    except Exception as e:
                        logger.error(f'Error fetching data for {symbol}: {e}')
                        continue
                if historical_data:
                    df = pd.DataFrame(historical_data)
                    df = df.dropna()
                    if len(df) < 30:
                        raise ValueError(f'Insufficient historical data. Only {len(df)} days available.')
                    return df.tail(lookback_days)
                else:
                    raise ValueError('No historical data could be retrieved')
            else:
                raise ValueError('No business logic provided for data retrieval')
        except Exception as e:
            logger.error(f'Error getting historical data: {e}')
            raise

    @monitor_performance
    def calculate_expected_returns(self, prices: pd.DataFrame, method: str='mean_historical_return', **kwargs) -> pd.Series:
        """
        Calculate expected returns using various methods

        Args:
            prices: Historical price data
            method: Method to calculate expected returns
            **kwargs: Additional parameters for specific methods

        Returns:
            Series of expected returns
        """
        try:
            with operation('calculate_expected_returns', context={'method': method}):
                if method == 'mean_historical_return':
                    frequency = kwargs.get('frequency', 252)
                    return expected_returns.mean_historical_return(prices, frequency=frequency)
                elif method == 'ema_historical_return':
                    frequency = kwargs.get('frequency', 252)
                    span = kwargs.get('span', 500)
                    return expected_returns.ema_historical_return(prices, frequency=frequency, span=span)
                elif method == 'capm_return':
                    market_prices = kwargs.get('market_prices')
                    frequency = kwargs.get('frequency', 252)
                    if market_prices is None:
                        market_prices = prices.iloc[:, 0]
                    return expected_returns.capm_return(prices, market_prices=market_prices, frequency=frequency)
                elif method == 'james_stein':
                    frequency = kwargs.get('frequency', 252)
                    mu = expected_returns.mean_historical_return(prices, frequency=frequency)
                    return expected_returns.james_stein_shrinkage(mu)
                else:
                    raise ValueError(f'Unknown expected returns method: {method}')
        except Exception as e:
            logger.error(f'Error calculating expected returns: {e}')
            raise

    @monitor_performance
    def calculate_risk_model(self, prices: pd.DataFrame, method: str='sample_cov', **kwargs) -> pd.DataFrame:
        """
        Calculate risk model (covariance matrix) using various methods

        Args:
            prices: Historical price data
            method: Method to calculate risk model
            **kwargs: Additional parameters for specific methods

        Returns:
            Covariance matrix
        """
        try:
            with operation('calculate_risk_model', context={'method': method}):
                if method == 'sample_cov':
                    frequency = kwargs.get('frequency', 252)
                    return risk_models.sample_cov(prices, frequency=frequency)
                elif method == 'semicovariance':
                    frequency = kwargs.get('frequency', 252)
                    benchmark = kwargs.get('benchmark', 0)
                    return risk_models.semicovariance(prices, frequency=frequency, benchmark=benchmark)
                elif method == 'exp_cov':
                    frequency = kwargs.get('frequency', 252)
                    span = kwargs.get('span', 180)
                    return risk_models.exp_cov(prices, frequency=frequency, span=span)
                elif method == 'ledoit_wolf':
                    frequency = kwargs.get('frequency', 252)
                    cs = CovarianceShrinkage(prices, frequency=frequency)
                    return cs.ledoit_wolf()
                elif method == 'oracle_approximating':
                    frequency = kwargs.get('frequency', 252)
                    cs = CovarianceShrinkage(prices, frequency=frequency)
                    return cs.oracle_approximating()
                else:
                    raise ValueError(f'Unknown risk model method: {method}')
        except Exception as e:
            logger.error(f'Error calculating risk model: {e}')
            raise

    @monitor_performance
    def optimize_mean_variance(self, mu: pd.Series, S: pd.DataFrame, optimization_target: str='max_sharpe', target_return: float=None, target_volatility: float=None, weight_bounds: Tuple[float, float]=(0, 1), sector_mapper: Dict=None, sector_lower: Dict=None, sector_upper: Dict=None, **kwargs) -> Dict:
        """
        Perform mean-variance optimization

        Args:
            mu: Expected returns
            S: Covariance matrix
            optimization_target: Target for optimization
            target_return: Target return (for efficient_risk)
            target_volatility: Target volatility (for efficient_return)
            weight_bounds: Weight bounds for individual assets
            sector_mapper: Mapping of assets to sectors
            sector_lower: Lower bounds for sector weights
            sector_upper: Upper bounds for sector weights
            **kwargs: Additional parameters

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_mean_variance', context={'target': optimization_target}):
                ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
                if sector_mapper and (sector_lower or sector_upper):
                    ef.add_sector_constraints(sector_mapper, sector_lower, sector_upper)
                gamma = kwargs.get('gamma', 0)
                if gamma > 0:
                    ef.add_objective(objective_functions.L2_reg, gamma=gamma)
                if optimization_target == 'max_sharpe':
                    ef.max_sharpe(risk_free_rate=self.risk_free_rate)
                elif optimization_target == 'min_volatility':
                    ef.min_volatility()
                elif optimization_target == 'efficient_risk':
                    if target_return is None:
                        raise ValueError('target_return required for efficient_risk')
                    ef.efficient_risk(target_return)
                elif optimization_target == 'efficient_return':
                    if target_volatility is None:
                        raise ValueError('target_volatility required for efficient_return')
                    ef.efficient_return(target_volatility)
                else:
                    raise ValueError(f'Unknown optimization target: {optimization_target}')
                raw_weights = ef.weights
                cleaned_weights = ef.clean_weights()
                performance = ef.portfolio_performance(risk_free_rate=self.risk_free_rate, verbose=False)
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'volatility': performance[1], 'sharpe_ratio': performance[2], 'optimization_target': optimization_target, 'ef_object': ef}
        except Exception as e:
            logger.error(f'Error in mean-variance optimization: {e}')
            raise

    @monitor_performance
    def optimize_semivariance(self, prices: pd.DataFrame, optimization_target: str='max_quadratic_utility', benchmark: float=0, target_return: float=None, market_neutral: bool=False, **kwargs) -> Dict:
        """
        Perform semivariance optimization

        Args:
            prices: Historical price data
            optimization_target: Target for optimization
            benchmark: Benchmark return for semideviation
            target_return: Target return (for efficient_semivariance)
            market_neutral: Whether to make portfolio market neutral
            **kwargs: Additional parameters

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_semivariance', context={'target': optimization_target}):
                returns = prices.pct_change().dropna()
                es = EfficientSemivariance(returns, benchmark=benchmark)
                if market_neutral:
                    es.add_constraint(lambda w: sum(w) == 0)
                if optimization_target == 'max_quadratic_utility':
                    risk_aversion = kwargs.get('risk_aversion', 1)
                    es.max_quadratic_utility(risk_aversion=risk_aversion)
                elif optimization_target == 'efficient_semivariance':
                    if target_return is None:
                        raise ValueError('target_return required for efficient_semivariance')
                    es.efficient_semivariance(target_return)
                elif optimization_target == 'min_semivariance':
                    es.min_semivariance()
                else:
                    raise ValueError(f'Unknown semivariance optimization target: {optimization_target}')
                raw_weights = es.weights
                cleaned_weights = es.clean_weights()
                try:
                    performance = es.portfolio_performance(risk_free_rate=self.risk_free_rate)
                except:
                    portfolio_return = sum((raw_weights[i] * returns.mean().iloc[i] * 252 for i in range(len(raw_weights))))
                    performance = (portfolio_return, None, None)
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'semideviation': performance[1] if len(performance) > 1 else None, 'optimization_target': optimization_target, 'benchmark': benchmark}
        except Exception as e:
            logger.error(f'Error in semivariance optimization: {e}')
            raise

    @monitor_performance
    def optimize_cvar(self, prices: pd.DataFrame, optimization_target: str='max_quadratic_utility', beta: float=None, target_return: float=None, **kwargs) -> Dict:
        """
        Perform CVaR (Conditional Value at Risk) optimization

        Args:
            prices: Historical price data
            optimization_target: Target for optimization
            beta: Confidence level for CVaR (if None, uses self.confidence_level)
            target_return: Target return (for efficient_cvar)
            **kwargs: Additional parameters

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_cvar', context={'target': optimization_target}):
                if beta is None:
                    beta = self.confidence_level
                returns = prices.pct_change().dropna()
                ec = EfficientCVaR(returns, beta=beta)
                if optimization_target == 'max_quadratic_utility':
                    risk_aversion = kwargs.get('risk_aversion', 1)
                    ec.max_quadratic_utility(risk_aversion=risk_aversion)
                elif optimization_target == 'efficient_cvar':
                    if target_return is None:
                        raise ValueError('target_return required for efficient_cvar')
                    ec.efficient_cvar(target_return)
                elif optimization_target == 'min_cvar':
                    ec.min_cvar()
                else:
                    raise ValueError(f'Unknown CVaR optimization target: {optimization_target}')
                raw_weights = ec.weights
                cleaned_weights = ec.clean_weights()
                try:
                    performance = ec.portfolio_performance()
                except:
                    portfolio_return = sum((raw_weights[i] * returns.mean().iloc[i] * 252 for i in range(len(raw_weights))))
                    performance = (portfolio_return, None)
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'cvar': performance[1] if len(performance) > 1 else None, 'confidence_level': beta, 'optimization_target': optimization_target}
        except Exception as e:
            logger.error(f'Error in CVaR optimization: {e}')
            raise

    @monitor_performance
    def optimize_cdar(self, prices: pd.DataFrame, optimization_target: str='max_quadratic_utility', beta: float=None, target_return: float=None, **kwargs) -> Dict:
        """
        Perform CDaR (Conditional Drawdown at Risk) optimization

        Args:
            prices: Historical price data
            optimization_target: Target for optimization
            beta: Confidence level for CDaR (if None, uses self.confidence_level)
            target_return: Target return (for efficient_cdar)
            **kwargs: Additional parameters

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_cdar', context={'target': optimization_target}):
                if beta is None:
                    beta = self.confidence_level
                ec = EfficientCDaR(prices, beta=beta)
                if optimization_target == 'max_quadratic_utility':
                    risk_aversion = kwargs.get('risk_aversion', 1)
                    ec.max_quadratic_utility(risk_aversion=risk_aversion)
                elif optimization_target == 'efficient_cdar':
                    if target_return is None:
                        raise ValueError('target_return required for efficient_cdar')
                    ec.efficient_cdar(target_return)
                elif optimization_target == 'min_cdar':
                    ec.min_cdar()
                else:
                    raise ValueError(f'Unknown CDaR optimization target: {optimization_target}')
                raw_weights = ec.weights
                cleaned_weights = ec.clean_weights()
                try:
                    performance = ec.portfolio_performance()
                except:
                    returns = prices.pct_change().dropna()
                    portfolio_return = sum((raw_weights[i] * returns.mean().iloc[i] * 252 for i in range(len(raw_weights))))
                    performance = (portfolio_return, None)
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'cdar': performance[1] if len(performance) > 1 else None, 'confidence_level': beta, 'optimization_target': optimization_target}
        except Exception as e:
            logger.error(f'Error in CDaR optimization: {e}')
            raise

    @monitor_performance
    def optimize_hrp(self, prices: pd.DataFrame, linkage_method: str='single', max_cluster_size: int=None) -> Dict:
        """
        Perform Hierarchical Risk Parity optimization

        Args:
            prices: Historical price data
            linkage_method: Linkage method for clustering
            max_cluster_size: Maximum cluster size

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_hrp'):
                returns = prices.pct_change().dropna()
                hrp = HRPOpt(returns)
                if max_cluster_size:
                    hrp.max_cluster_size = max_cluster_size
                weights = hrp.optimize(linkage_method=linkage_method)
                cleaned_weights = hrp.clean_weights()
                performance = hrp.portfolio_performance(risk_free_rate=self.risk_free_rate)
                return {'raw_weights': dict(weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'volatility': performance[1], 'sharpe_ratio': performance[2], 'linkage_method': linkage_method, 'clustered_corr': hrp.clustered_corr, 'clusters': hrp.clusters}
        except Exception as e:
            logger.error(f'Error in HRP optimization: {e}')
            raise

    @monitor_performance
    def optimize_black_litterman(self, prices: pd.DataFrame, views: Dict[str, float]=None, view_confidences: List[float]=None, market_caps: Dict[str, float]=None, risk_aversion: float=1, tau: float=0.05, pi_method: str='market_cap', **kwargs) -> Dict:
        """
        Perform Black-Litterman optimization

        Args:
            prices: Historical price data
            views: Dictionary of views {asset: expected_return}
            view_confidences: List of confidence levels for views
            market_caps: Market capitalizations for assets
            risk_aversion: Risk aversion parameter
            tau: Tau parameter for Black-Litterman
            pi_method: Method to calculate prior returns
            **kwargs: Additional parameters

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_black_litterman'):
                mu_hist = expected_returns.mean_historical_return(prices)
                S = risk_models.sample_cov(prices)
                if market_caps is None:
                    market_caps = {asset: 1.0 for asset in prices.columns}
                bl = BlackLittermanModel(S, pi=pi_method, market_caps=market_caps, risk_aversion=risk_aversion, tau=tau)
                if views:
                    view_dict = {}
                    for asset, view_return in views.items():
                        if asset in prices.columns:
                            view_dict[asset] = view_return
                    if view_dict:
                        P = pd.DataFrame(0, index=range(len(view_dict)), columns=S.index)
                        Q = []
                        for i, (asset, view_return) in enumerate(view_dict.items()):
                            P.iloc[i][asset] = 1
                            Q.append(view_return)
                        if view_confidences is None:
                            omega = np.diag([1.0] * len(view_dict))
                        else:
                            omega = np.diag(view_confidences[:len(view_dict)])
                        bl.bl_views(P, Q, omega)
                mu_bl = bl.bl_returns()
                S_bl = bl.bl_cov()
                ef = EfficientFrontier(mu_bl, S_bl)
                ef.max_sharpe(risk_free_rate=self.risk_free_rate)
                raw_weights = ef.weights
                cleaned_weights = ef.clean_weights()
                performance = ef.portfolio_performance(risk_free_rate=self.risk_free_rate)
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'volatility': performance[1], 'sharpe_ratio': performance[2], 'bl_returns': mu_bl.to_dict(), 'prior_returns': bl.pi.to_dict() if hasattr(bl, 'pi') else {}, 'views': views or {}, 'tau': tau, 'risk_aversion': risk_aversion}
        except Exception as e:
            logger.error(f'Error in Black-Litterman optimization: {e}')
            raise

    @monitor_performance
    def optimize_cla(self, mu: pd.Series, S: pd.DataFrame) -> Dict:
        """
        Perform Critical Line Algorithm optimization

        Args:
            mu: Expected returns
            S: Covariance matrix

        Returns:
            Dictionary with optimization results
        """
        try:
            with operation('optimize_cla'):
                cla = CLA(mu, S)
                cla.max_sharpe()
                raw_weights = cla.weights
                cleaned_weights = cla.clean_weights()
                performance = cla.portfolio_performance(risk_free_rate=self.risk_free_rate)
                ef_returns, ef_volatilities, ef_weights = cla.efficient_frontier()
                return {'raw_weights': dict(raw_weights), 'cleaned_weights': cleaned_weights, 'expected_return': performance[0], 'volatility': performance[1], 'sharpe_ratio': performance[2], 'efficient_frontier': {'returns': ef_returns, 'volatilities': ef_volatilities, 'weights': ef_weights}}
        except Exception as e:
            logger.error(f'Error in CLA optimization: {e}')
            raise

    @monitor_performance
    def calculate_efficient_frontier(self, mu: pd.Series, S: pd.DataFrame, num_points: int=100, risk_range: Tuple[float, float]=None) -> Dict:
        """
        Calculate the efficient frontier

        Args:
            mu: Expected returns
            S: Covariance matrix
            num_points: Number of points on the frontier
            risk_range: Risk range (min_vol, max_vol)

        Returns:
            Dictionary with frontier data
        """
        try:
            with operation('calculate_efficient_frontier'):
                ef = EfficientFrontier(mu, S)
                if risk_range is None:
                    ef_temp = EfficientFrontier(mu, S)
                    ef_temp.min_volatility()
                    min_vol = ef_temp.portfolio_performance()[1]
                    max_return = mu.max()
                    ef_temp = EfficientFrontier(mu, S)
                    try:
                        ef_temp.efficient_return(max_return * 0.95)
                        max_vol = ef_temp.portfolio_performance()[1]
                    except:
                        max_vol = min_vol * 3
                    risk_range = (min_vol, max_vol)
                frontier_returns = []
                frontier_volatilities = []
                frontier_weights = []
                target_vols = np.linspace(risk_range[0], risk_range[1], num_points // 2)
                for target_vol in target_vols:
                    try:
                        ef_temp = EfficientFrontier(mu, S)
                        ef_temp.efficient_risk(target_vol ** 2)
                        ret, vol, _ = ef_temp.portfolio_performance()
                        if min_vol <= vol <= risk_range[1] * 1.1:
                            frontier_returns.append(ret)
                            frontier_volatilities.append(vol)
                            frontier_weights.append(dict(ef_temp.weights))
                    except Exception as e:
                        logger.debug(f'Failed to optimize for target volatility {target_vol:.4f}: {e}')
                        continue
                if frontier_returns:
                    min_return = min(frontier_returns)
                    max_return = max(frontier_returns)
                else:
                    min_return = mu.min()
                    max_return = mu.max() * 0.9
                target_returns = np.linspace(min_return, max_return, num_points // 2)
                for target_return in target_returns:
                    try:
                        ef_temp = EfficientFrontier(mu, S)
                        ef_temp.efficient_return(target_return)
                        ret, vol, _ = ef_temp.portfolio_performance()
                        if vol >= min_vol and vol <= risk_range[1] * 1.2 and (not any((abs(existing_vol - vol) < 0.001 for existing_vol in frontier_volatilities))):
                            frontier_returns.append(ret)
                            frontier_volatilities.append(vol)
                            frontier_weights.append(dict(ef_temp.weights))
                    except Exception as e:
                        logger.debug(f'Failed to optimize for target return {target_return:.4f}: {e}')
                        continue
                if frontier_returns:
                    combined_data = list(zip(frontier_volatilities, frontier_returns, frontier_weights))
                    combined_data.sort(key=lambda x: x[0])
                    filtered_data = []
                    last_vol = -1
                    for vol, ret, weights in combined_data:
                        if abs(vol - last_vol) > 0.001:
                            filtered_data.append((vol, ret, weights))
                            last_vol = vol
                    if filtered_data:
                        frontier_volatilities, frontier_returns, frontier_weights = zip(*filtered_data)
                        frontier_volatilities = list(frontier_volatilities)
                        frontier_returns = list(frontier_returns)
                        frontier_weights = list(frontier_weights)
                    else:
                        frontier_returns = []
                        frontier_volatilities = []
                        frontier_weights = []
                if len(frontier_returns) < 2:
                    logger.warning('Insufficient frontier points generated, adding key portfolios')
                    try:
                        ef_min = EfficientFrontier(mu, S)
                        ef_min.min_volatility()
                        min_ret, min_vol, _ = ef_min.portfolio_performance()
                        frontier_returns.append(min_ret)
                        frontier_volatilities.append(min_vol)
                        frontier_weights.append(dict(ef_min.weights))
                    except Exception as e:
                        logger.warning(f'Could not add min volatility portfolio: {e}')
                    try:
                        ef_sharpe = EfficientFrontier(mu, S)
                        ef_sharpe.max_sharpe(risk_free_rate=self.risk_free_rate)
                        sharpe_ret, sharpe_vol, sharpe_ratio = ef_sharpe.portfolio_performance(risk_free_rate=self.risk_free_rate)
                        if not any((abs(sharpe_vol - vol) < 0.001 for vol in frontier_volatilities)):
                            frontier_returns.append(sharpe_ret)
                            frontier_volatilities.append(sharpe_vol)
                            frontier_weights.append(dict(ef_sharpe.weights))
                    except Exception as e:
                        logger.warning(f'Could not add max Sharpe portfolio: {e}')
                try:
                    ef_sharpe = EfficientFrontier(mu, S)
                    ef_sharpe.max_sharpe(risk_free_rate=self.risk_free_rate)
                    sharpe_performance = ef_sharpe.portfolio_performance(risk_free_rate=self.risk_free_rate)
                    max_sharpe_data = {'return': sharpe_performance[0], 'volatility': sharpe_performance[1], 'sharpe_ratio': sharpe_performance[2], 'weights': dict(ef_sharpe.weights)}
                except Exception as e:
                    logger.warning(f'Could not calculate max Sharpe portfolio: {e}')
                    max_sharpe_data = {'return': 0, 'volatility': 0, 'sharpe_ratio': 0, 'weights': {}}
                efficient_frontier_stats = {}
                if frontier_returns and frontier_volatilities:
                    efficient_frontier_stats = {'num_points': len(frontier_returns), 'min_return': min(frontier_returns), 'max_return': max(frontier_returns), 'min_volatility': min(frontier_volatilities), 'max_volatility': max(frontier_volatilities), 'return_range': max(frontier_returns) - min(frontier_returns), 'volatility_range': max(frontier_volatilities) - min(frontier_volatilities)}
                return {'returns': frontier_returns, 'volatilities': frontier_volatilities, 'weights': frontier_weights, 'max_sharpe': max_sharpe_data, 'risk_range': risk_range, 'statistics': efficient_frontier_stats, 'success': len(frontier_returns) > 0}
        except Exception as e:
            logger.error(f'Error calculating efficient frontier: {e}')
            return {'returns': [], 'volatilities': [], 'weights': [], 'max_sharpe': {'return': 0, 'volatility': 0, 'sharpe_ratio': 0, 'weights': {}}, 'risk_range': (0, 0), 'statistics': {}, 'success': False, 'error': str(e)}
            ef_sharpe = EfficientFrontier(mu, S)
            ef_sharpe.max_sharpe(risk_free_rate=self.risk_free_rate)
            sharpe_performance = ef_sharpe.portfolio_performance(risk_free_rate=self.risk_free_rate)
            return {'returns': frontier_returns, 'volatilities': frontier_volatilities, 'weights': frontier_weights, 'max_sharpe': {'return': sharpe_performance[0], 'volatility': sharpe_performance[1], 'sharpe_ratio': sharpe_performance[2], 'weights': dict(ef_sharpe.weights)}, 'risk_range': risk_range}

def __init__(self, business_logic=None):
    """Initialize the portfolio optimizer"""
    if not PYPFOPT_AVAILABLE:
        raise ImportError('PyPortfolioOpt is required but not installed')
    self.business_logic = business_logic
    self.risk_free_rate = 0.02
    self.confidence_level = 0.95
    self.lookback_days = 252
    self.optimization_cache = {}
    self.cache_timeout = 3600
    self.optimization_methods = {'mean_variance': 'Mean-Variance Optimization', 'min_volatility': 'Minimum Volatility', 'max_sharpe': 'Maximum Sharpe Ratio', 'efficient_risk': 'Efficient Risk', 'efficient_return': 'Efficient Return', 'semivariance': 'Efficient Semivariance', 'cvar': 'Conditional Value at Risk', 'cdar': 'Conditional Drawdown at Risk', 'hrp': 'Hierarchical Risk Parity', 'black_litterman': 'Black-Litterman Model', 'cla': 'Critical Line Algorithm'}
    self.expected_returns_methods = {'mean_historical_return': 'Mean Historical Return', 'ema_historical_return': 'Exponentially Weighted Returns', 'capm_return': 'CAPM Expected Returns', 'james_stein': 'James-Stein Estimator'}
    self.risk_model_methods = {'sample_cov': 'Sample Covariance', 'semicovariance': 'Semicovariance', 'exp_cov': 'Exponentially Weighted Covariance', 'ledoit_wolf': 'Ledoit-Wolf Shrinkage', 'oracle_approximating': 'Oracle Approximating Shrinkage'}

