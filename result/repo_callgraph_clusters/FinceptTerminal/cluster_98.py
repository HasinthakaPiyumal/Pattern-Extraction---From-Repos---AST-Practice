# Cluster 98

class DataHandler:
    """
    Centralized data handler for all alternative investment data sources
    Supports multiple input formats and validates according to CFA standards
    """

    def __init__(self):
        self.config = Config()
        self.validation_rules = ValidationRules()

    def standardize_price_data(self, data: Union[Dict, pd.DataFrame, List]) -> List[MarketData]:
        """
        Standardize price data from various sources into MarketData objects

        Args:
            data: Price data in various formats

        Returns:
            List of MarketData objects
        """
        try:
            if isinstance(data, pd.DataFrame):
                return self._from_dataframe(data)
            elif isinstance(data, dict):
                return self._from_dict(data)
            elif isinstance(data, list):
                return self._from_list(data)
            else:
                raise DataValidationError(f'Unsupported data type: {type(data)}')
        except Exception as e:
            logger.error(f'Error standardizing price data: {str(e)}')
            raise DataValidationError(f'Failed to standardize price data: {str(e)}')

    def _from_dataframe(self, df: pd.DataFrame) -> List[MarketData]:
        """Convert DataFrame to MarketData objects"""
        required_columns = ['timestamp', 'price']
        if not all((col in df.columns for col in required_columns)):
            raise DataValidationError(f'DataFrame must contain columns: {required_columns}')
        market_data = []
        for _, row in df.iterrows():
            md = MarketData(timestamp=self._standardize_timestamp(row['timestamp']), price=self._to_decimal(row['price']), volume=self._to_decimal(row.get('volume')), bid=self._to_decimal(row.get('bid')), ask=self._to_decimal(row.get('ask')), high=self._to_decimal(row.get('high')), low=self._to_decimal(row.get('low')), open=self._to_decimal(row.get('open')), close=self._to_decimal(row.get('close')))
            self._validate_market_data(md)
            market_data.append(md)
        return market_data

    def _from_dict(self, data: Dict) -> List[MarketData]:
        """Convert dictionary to MarketData objects"""
        if 'data' in data:
            data = data['data']
        if isinstance(data, list):
            return [self._dict_to_market_data(item) for item in data]
        else:
            return [self._dict_to_market_data(data)]

    def _from_list(self, data: List) -> List[MarketData]:
        """Convert list to MarketData objects"""
        return [self._dict_to_market_data(item) for item in data]

    def _dict_to_market_data(self, item: Dict) -> MarketData:
        """Convert single dictionary item to MarketData"""
        md = MarketData(timestamp=self._standardize_timestamp(item.get('timestamp', item.get('date', item.get('time')))), price=self._to_decimal(item.get('price', item.get('close'))), volume=self._to_decimal(item.get('volume')), bid=self._to_decimal(item.get('bid')), ask=self._to_decimal(item.get('ask')), high=self._to_decimal(item.get('high')), low=self._to_decimal(item.get('low')), open=self._to_decimal(item.get('open')), close=self._to_decimal(item.get('close')))
        self._validate_market_data(md)
        return md

    def standardize_cash_flows(self, data: Union[Dict, pd.DataFrame, List]) -> List[CashFlow]:
        """
        Standardize cash flow data for IRR and performance calculations

        Args:
            data: Cash flow data in various formats

        Returns:
            List of CashFlow objects
        """
        try:
            if isinstance(data, pd.DataFrame):
                return self._cash_flows_from_dataframe(data)
            elif isinstance(data, dict):
                return self._cash_flows_from_dict(data)
            elif isinstance(data, list):
                return self._cash_flows_from_list(data)
            else:
                raise DataValidationError(f'Unsupported cash flow data type: {type(data)}')
        except Exception as e:
            logger.error(f'Error standardizing cash flows: {str(e)}')
            raise DataValidationError(f'Failed to standardize cash flows: {str(e)}')

    def _cash_flows_from_dataframe(self, df: pd.DataFrame) -> List[CashFlow]:
        """Convert DataFrame to CashFlow objects"""
        required_columns = ['date', 'amount']
        if not all((col in df.columns for col in required_columns)):
            raise DataValidationError(f'Cash flow DataFrame must contain columns: {required_columns}')
        cash_flows = []
        for _, row in df.iterrows():
            cf = CashFlow(date=self._standardize_date(row['date']), amount=self._to_decimal(row['amount']), cf_type=row.get('type', 'inflow' if float(row['amount']) > 0 else 'outflow'), description=row.get('description'))
            self._validate_cash_flow(cf)
            cash_flows.append(cf)
        return sorted(cash_flows, key=lambda x: x.date)

    def _cash_flows_from_dict(self, data: Dict) -> List[CashFlow]:
        """Convert dictionary to CashFlow objects"""
        if 'cash_flows' in data:
            data = data['cash_flows']
        if isinstance(data, list):
            return [self._dict_to_cash_flow(item) for item in data]
        else:
            return [self._dict_to_cash_flow(data)]

    def _cash_flows_from_list(self, data: List) -> List[CashFlow]:
        """Convert list to CashFlow objects"""
        return [self._dict_to_cash_flow(item) for item in data]

    def _dict_to_cash_flow(self, item: Dict) -> CashFlow:
        """Convert single dictionary item to CashFlow"""
        cf = CashFlow(date=self._standardize_date(item.get('date', item.get('timestamp'))), amount=self._to_decimal(item.get('amount', item.get('value'))), cf_type=item.get('type', item.get('cf_type', 'inflow' if float(item.get('amount', 0)) > 0 else 'outflow')), description=item.get('description', item.get('desc')))
        self._validate_cash_flow(cf)
        return cf

    def load_from_csv(self, file_path: str, data_type: str='price') -> Union[List[MarketData], List[CashFlow]]:
        """
        Load data from CSV file

        Args:
            file_path: Path to CSV file
            data_type: 'price' or 'cash_flow'

        Returns:
            Standardized data objects
        """
        try:
            df = pd.read_csv(file_path)
            if data_type == 'price':
                return self.standardize_price_data(df)
            elif data_type == 'cash_flow':
                return self.standardize_cash_flows(df)
            else:
                raise DataValidationError(f'Unsupported data type: {data_type}')
        except Exception as e:
            logger.error(f'Error loading CSV file {file_path}: {str(e)}')
            raise DataValidationError(f'Failed to load CSV: {str(e)}')

    def load_from_json(self, file_path: str, data_type: str='price') -> Union[List[MarketData], List[CashFlow]]:
        """
        Load data from JSON file

        Args:
            file_path: Path to JSON file
            data_type: 'price' or 'cash_flow'

        Returns:
            Standardized data objects
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            if data_type == 'price':
                return self.standardize_price_data(data)
            elif data_type == 'cash_flow':
                return self.standardize_cash_flows(data)
            else:
                raise DataValidationError(f'Unsupported data type: {data_type}')
        except Exception as e:
            logger.error(f'Error loading JSON file {file_path}: {str(e)}')
            raise DataValidationError(f'Failed to load JSON: {str(e)}')

    def calculate_returns(self, prices: List[MarketData], method: str='simple') -> pd.DataFrame:
        """
        Calculate returns from price data

        Args:
            prices: List of MarketData objects
            method: 'simple', 'log', or 'compound'

        Returns:
            DataFrame with returns
        """
        if len(prices) < 2:
            raise DataValidationError('Need at least 2 price points to calculate returns')
        df = pd.DataFrame([{'timestamp': p.timestamp, 'price': float(p.price)} for p in prices])
        df = df.sort_values('timestamp')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        if method == 'simple':
            df['return'] = df['price'].pct_change()
        elif method == 'log':
            df['return'] = np.log(df['price'] / df['price'].shift(1))
        elif method == 'compound':
            df['return'] = df['price'] / df['price'].shift(1) - 1
        else:
            raise DataValidationError(f'Unsupported return calculation method: {method}')
        return df.dropna()

    def aggregate_to_frequency(self, data: List[MarketData], frequency: str='monthly') -> List[MarketData]:
        """
        Aggregate data to specified frequency

        Args:
            data: List of MarketData objects
            frequency: 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'

        Returns:
            Aggregated MarketData objects
        """
        if not data:
            return []
        df = pd.DataFrame([{'timestamp': pd.to_datetime(d.timestamp), 'price': float(d.price), 'volume': float(d.volume) if d.volume else 0, 'high': float(d.high) if d.high else float(d.price), 'low': float(d.low) if d.low else float(d.price), 'open': float(d.open) if d.open else float(d.price), 'close': float(d.close) if d.close else float(d.price)} for d in data])
        df = df.set_index('timestamp').sort_index()
        freq_map = {'daily': 'D', 'weekly': 'W', 'monthly': 'M', 'quarterly': 'Q', 'yearly': 'Y'}
        if frequency not in freq_map:
            raise DataValidationError(f'Unsupported frequency: {frequency}')
        agg_df = df.resample(freq_map[frequency]).agg({'price': 'last', 'volume': 'sum', 'high': 'max', 'low': 'min', 'open': 'first', 'close': 'last'}).dropna()
        result = []
        for timestamp, row in agg_df.iterrows():
            md = MarketData(timestamp=timestamp.strftime('%Y-%m-%d'), price=Decimal(str(row['price'])), volume=Decimal(str(row['volume'])) if row['volume'] > 0 else None, high=Decimal(str(row['high'])), low=Decimal(str(row['low'])), open=Decimal(str(row['open'])), close=Decimal(str(row['close'])))
            result.append(md)
        return result

    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """Convert value to Decimal with validation"""
        if value is None or pd.isna(value):
            return None
        try:
            decimal_value = Decimal(str(value))
            if decimal_value < self.config.MIN_PRICE and decimal_value != 0:
                raise DataValidationError(f'Price too small: {decimal_value}')
            return decimal_value
        except (InvalidOperation, ValueError) as e:
            raise DataValidationError(f'Invalid decimal value: {value}')

    def _standardize_timestamp(self, timestamp: Any) -> str:
        """Standardize timestamp to ISO format"""
        if isinstance(timestamp, str):
            try:
                dt = pd.to_datetime(timestamp)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                return timestamp
        elif isinstance(timestamp, (datetime, date)):
            return timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return str(timestamp)

    def _standardize_date(self, date_value: Any) -> str:
        """Standardize date to ISO format"""
        if isinstance(date_value, str):
            try:
                dt = pd.to_datetime(date_value)
                return dt.strftime('%Y-%m-%d')
            except:
                return date_value
        elif isinstance(date_value, (datetime, date)):
            return date_value.strftime('%Y-%m-%d')
        else:
            return str(date_value)

    def _validate_market_data(self, md: MarketData) -> None:
        """Validate MarketData object"""
        if md.price <= 0:
            raise DataValidationError(f'Invalid price: {md.price}')
        if md.volume is not None and md.volume < 0:
            raise DataValidationError(f'Invalid volume: {md.volume}')
        if md.high and md.low and (md.high < md.low):
            raise DataValidationError(f'High price ({md.high}) less than low price ({md.low})')
        if md.bid and md.ask and (md.bid > md.ask):
            raise DataValidationError(f'Bid price ({md.bid}) greater than ask price ({md.ask})')

    def _validate_cash_flow(self, cf: CashFlow) -> None:
        """Validate CashFlow object"""
        if cf.amount == 0:
            logger.warning(f'Zero cash flow amount on {cf.date}')
        valid_types = ['inflow', 'outflow', 'distribution', 'capital_call', 'dividend', 'interest']
        if cf.cf_type not in valid_types:
            logger.warning(f'Unknown cash flow type: {cf.cf_type}')

    def get_data_summary(self, data: Union[List[MarketData], List[CashFlow]]) -> Dict[str, Any]:
        """Get summary statistics of the data"""
        if not data:
            return {'error': 'No data provided'}
        if isinstance(data[0], MarketData):
            prices = [float(d.price) for d in data]
            return {'data_type': 'MarketData', 'count': len(data), 'price_stats': {'mean': np.mean(prices), 'std': np.std(prices), 'min': np.min(prices), 'max': np.max(prices)}, 'date_range': {'start': min((d.timestamp for d in data)), 'end': max((d.timestamp for d in data))}}
        elif isinstance(data[0], CashFlow):
            amounts = [float(d.amount) for d in data]
            return {'data_type': 'CashFlow', 'count': len(data), 'amount_stats': {'total': sum(amounts), 'mean': np.mean(amounts), 'std': np.std(amounts), 'min': np.min(amounts), 'max': np.max(amounts)}, 'date_range': {'start': min((d.date for d in data)), 'end': max((d.date for d in data))}, 'inflows': sum((1 for d in data if d.amount > 0)), 'outflows': sum((1 for d in data if d.amount < 0))}
        return {'error': 'Unknown data type'}

def __init__(self):
    self.config = Config()
    self.validation_rules = ValidationRules()

class PerformanceAnalyzer:
    """
    Comprehensive performance analysis for alternative investments
    Implements CFA Institute standard performance measurement methodologies
    """

    def __init__(self):
        self.math = FinancialMath()
        self.config = Config()

    def calculate_time_weighted_return(self, prices: List[MarketData], cash_flows: List[CashFlow]=None) -> Dict[str, Decimal]:
        """
        Calculate Time-Weighted Return (TWR)
        CFA Standard: Geometric mean of sub-period returns
        Eliminates the effect of cash flow timing

        Args:
            prices: List of MarketData objects
            cash_flows: Optional cash flows for adjustment

        Returns:
            Dictionary with TWR metrics
        """
        if len(prices) < 2:
            return {'error': 'Insufficient price data'}
        sorted_prices = sorted(prices, key=lambda x: x.timestamp)
        returns = []
        for i in range(1, len(sorted_prices)):
            prev_price = sorted_prices[i - 1].price
            curr_price = sorted_prices[i].price
            period_return = (curr_price - prev_price) / prev_price
            returns.append(period_return)
        if not returns:
            return {'twr': Decimal('0')}
        cumulative_return = Decimal('1')
        for ret in returns:
            cumulative_return *= Decimal('1') + ret
        twr = cumulative_return - Decimal('1')
        total_days = (datetime.strptime(sorted_prices[-1].timestamp[:10], '%Y-%m-%d') - datetime.strptime(sorted_prices[0].timestamp[:10], '%Y-%m-%d')).days
        if total_days > 0:
            years = Decimal(str(total_days)) / Constants.DAYS_IN_YEAR
            annualized_twr = cumulative_return ** (Decimal('1') / years) - Decimal('1')
        else:
            annualized_twr = twr
        return {'twr': twr, 'annualized_twr': annualized_twr, 'cumulative_return': cumulative_return - Decimal('1'), 'number_of_periods': len(returns), 'total_days': total_days}

    def calculate_money_weighted_return(self, cash_flows: List[CashFlow]) -> Dict[str, Decimal]:
        """
        Calculate Money-Weighted Return (MWR) using IRR
        CFA Standard: IRR of all cash flows including ending value
        Reflects the effect of cash flow timing

        Args:
            cash_flows: List of CashFlow objects

        Returns:
            Dictionary with MWR metrics
        """
        if not cash_flows:
            return {'error': 'No cash flows provided'}
        irr = self.math.irr(cash_flows)
        if irr is None:
            return {'error': 'Could not calculate IRR'}
        moic = self.math.moic(cash_flows)
        dpi = self.math.dpi(cash_flows)
        return {'mwr_irr': irr, 'moic': moic, 'dpi': dpi, 'total_cash_flows': len(cash_flows)}

    def calculate_risk_adjusted_returns(self, returns: List[Decimal], benchmark_returns: List[Decimal]=None) -> Dict[str, Decimal]:
        """
        Calculate comprehensive risk-adjusted return metrics
        CFA Standards: Sharpe, Treynor, Information, Sortino ratios

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns for comparison

        Returns:
            Dictionary of risk-adjusted metrics
        """
        if len(returns) < 2:
            return {'error': 'Insufficient return data'}
        metrics = {}
        mean_return = sum(returns) / len(returns)
        volatility = self._calculate_volatility(returns)
        rf_rate = self.config.RISK_FREE_RATE / Constants.MONTHS_IN_YEAR
        sharpe = self.math.sharpe_ratio(returns, rf_rate)
        metrics['sharpe_ratio'] = sharpe
        sortino = self.math.sortino_ratio(returns)
        metrics['sortino_ratio'] = sortino
        if len(returns) > 1:
            prices = [Decimal('100')]
            for ret in returns:
                prices.append(prices[-1] * (Decimal('1') + ret))
            max_dd, _, _ = self.math.maximum_drawdown(prices)
            annualized_return = mean_return * Constants.MONTHS_IN_YEAR
            calmar = self.math.calmar_ratio(annualized_return, max_dd)
            metrics['calmar_ratio'] = calmar
            metrics['maximum_drawdown'] = max_dd
        if benchmark_returns and len(benchmark_returns) == len(returns):
            active_returns = [r - b for r, b in zip(returns, benchmark_returns)]
            tracking_error = self._calculate_volatility(active_returns)
            metrics['tracking_error'] = tracking_error
            mean_active_return = sum(active_returns) / len(active_returns)
            if tracking_error > 0:
                information_ratio = mean_active_return / tracking_error
                metrics['information_ratio'] = information_ratio
            if len(returns) > 1:
                beta = self._calculate_beta(returns, benchmark_returns)
                metrics['beta'] = beta
                if beta != 0:
                    treynor = (mean_return - rf_rate) / beta
                    metrics['treynor_ratio'] = treynor
        var_95 = self.math.var_historical(returns, Decimal('0.05'))
        var_99 = self.math.var_historical(returns, Decimal('0.01'))
        metrics['var_95'] = var_95
        metrics['var_99'] = var_99
        cvar_95 = self._calculate_cvar(returns, Decimal('0.05'))
        metrics['cvar_95'] = cvar_95
        return metrics

    def performance_attribution(self, portfolio_returns: List[Decimal], benchmark_returns: List[Decimal], sector_weights: Dict[str, Decimal]=None) -> Dict[str, Any]:
        """
        Perform return-based performance attribution analysis
        CFA Standard: Decompose excess returns into allocation and selection effects

        Args:
            portfolio_returns: Portfolio period returns
            benchmark_returns: Benchmark period returns
            sector_weights: Optional sector weight information

        Returns:
            Attribution analysis results
        """
        if len(portfolio_returns) != len(benchmark_returns):
            return {'error': 'Portfolio and benchmark return lengths must match'}
        attribution = {}
        active_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        portfolio_mean = sum(portfolio_returns) / len(portfolio_returns)
        benchmark_mean = sum(benchmark_returns) / len(benchmark_returns)
        active_mean = portfolio_mean - benchmark_mean
        attribution['total_active_return'] = active_mean
        attribution['portfolio_return'] = portfolio_mean
        attribution['benchmark_return'] = benchmark_mean
        positive_periods = sum((1 for ar in active_returns if ar > 0))
        hit_rate = Decimal(str(positive_periods)) / Decimal(str(len(active_returns)))
        attribution['hit_rate'] = hit_rate
        active_volatility = self._calculate_volatility(active_returns)
        attribution['active_volatility'] = active_volatility
        if active_volatility > 0:
            information_ratio = active_mean / active_volatility
            attribution['information_ratio'] = information_ratio
        return attribution

    def calculate_downside_metrics(self, returns: List[Decimal], target_return: Decimal=Decimal('0')) -> Dict[str, Decimal]:
        """
        Calculate comprehensive downside risk metrics
        CFA Standards: Downside deviation, downside beta, etc.

        Args:
            returns: Period returns
            target_return: Target or MAR (Minimum Acceptable Return)

        Returns:
            Dictionary of downside metrics
        """
        downside_metrics = {}
        downside_returns = [min(r - target_return, Decimal('0')) for r in returns]
        downside_variance = sum((dr ** 2 for dr in downside_returns)) / len(returns)
        downside_deviation = downside_variance.sqrt()
        downside_metrics['downside_deviation'] = downside_deviation
        mean_return = sum(returns) / len(returns)
        if downside_deviation > 0:
            sortino = (mean_return - target_return) / downside_deviation
            downside_metrics['sortino_ratio'] = sortino
        negative_periods = sum((1 for r in returns if r < target_return))
        downside_frequency = Decimal(str(negative_periods)) / Decimal(str(len(returns)))
        downside_metrics['downside_frequency'] = downside_frequency
        negative_returns = [r for r in returns if r < target_return]
        if negative_returns:
            avg_downside = sum(negative_returns) / len(negative_returns)
            downside_metrics['average_downside_return'] = avg_downside
        return downside_metrics

    def rolling_performance(self, prices: List[MarketData], window_months: int=12) -> List[Dict]:
        """
        Calculate rolling performance metrics

        Args:
            prices: List of MarketData objects
            window_months: Rolling window size in months

        Returns:
            List of rolling performance dictionaries
        """
        if len(prices) < window_months:
            return []
        rolling_results = []
        sorted_prices = sorted(prices, key=lambda x: x.timestamp)
        for i in range(window_months, len(sorted_prices)):
            window_prices = sorted_prices[i - window_months:i + 1]
            window_returns = []
            for j in range(1, len(window_prices)):
                ret = (window_prices[j].price - window_prices[j - 1].price) / window_prices[j - 1].price
                window_returns.append(ret)
            if window_returns:
                period_return = (window_prices[-1].price - window_prices[0].price) / window_prices[0].price
                volatility = self._calculate_volatility(window_returns)
                sharpe = self.math.sharpe_ratio(window_returns)
                rolling_results.append({'end_date': window_prices[-1].timestamp, 'period_return': float(period_return), 'annualized_return': float(period_return * Constants.MONTHS_IN_YEAR / window_months), 'volatility': float(volatility), 'sharpe_ratio': float(sharpe)})
        return rolling_results

    def calculate_factor_exposures(self, portfolio_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]]) -> Dict[str, Decimal]:
        """
        Calculate factor exposures using multiple regression
        CFA Standard: Multi-factor model analysis

        Args:
            portfolio_returns: Portfolio returns
            factor_returns: Dictionary of factor name -> factor returns

        Returns:
            Dictionary of factor loadings (betas)
        """
        if not factor_returns or len(portfolio_returns) < 10:
            return {}
        valid_factors = {}
        for factor_name, returns in factor_returns.items():
            if len(returns) == len(portfolio_returns):
                valid_factors[factor_name] = returns
        if not valid_factors:
            return {}
        try:
            y = np.array([float(r) for r in portfolio_returns])
            X = np.array([[float(valid_factors[factor][i]) for factor in valid_factors.keys()] for i in range(len(portfolio_returns))])
            X = np.column_stack([np.ones(len(y)), X])
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            exposures = {'alpha': Decimal(str(beta[0]))}
            for i, factor_name in enumerate(valid_factors.keys()):
                exposures[f'{factor_name}_beta'] = Decimal(str(beta[i + 1]))
            y_pred = X @ beta
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else 0
            exposures['r_squared'] = Decimal(str(r_squared))
            return exposures
        except Exception as e:
            logger.error(f'Error calculating factor exposures: {str(e)}')
            return {}

    def benchmark_analysis(self, portfolio_returns: List[Decimal], benchmark_returns: List[Decimal]) -> Dict[str, Any]:
        """
        Comprehensive benchmark analysis
        CFA Standards: Up/down capture, batting average, etc.

        Args:
            portfolio_returns: Portfolio returns
            benchmark_returns: Benchmark returns

        Returns:
            Dictionary of benchmark analysis metrics
        """
        if len(portfolio_returns) != len(benchmark_returns):
            return {'error': 'Return series length mismatch'}
        analysis = {}
        up_periods = [(p, b) for p, b in zip(portfolio_returns, benchmark_returns) if b > 0]
        down_periods = [(p, b) for p, b in zip(portfolio_returns, benchmark_returns) if b < 0]
        if up_periods:
            up_portfolio = sum((p for p, b in up_periods)) / len(up_periods)
            up_benchmark = sum((b for p, b in up_periods)) / len(up_periods)
            up_capture = up_portfolio / up_benchmark if up_benchmark != 0 else Decimal('0')
            analysis['up_capture_ratio'] = up_capture
        if down_periods:
            down_portfolio = sum((p for p, b in down_periods)) / len(down_periods)
            down_benchmark = sum((b for p, b in down_periods)) / len(down_periods)
            down_capture = down_portfolio / down_benchmark if down_benchmark != 0 else Decimal('0')
            analysis['down_capture_ratio'] = down_capture
        outperformance_periods = sum((1 for p, b in zip(portfolio_returns, benchmark_returns) if p > b))
        batting_average = Decimal(str(outperformance_periods)) / Decimal(str(len(portfolio_returns)))
        analysis['batting_average'] = batting_average
        beta = self._calculate_beta(portfolio_returns, benchmark_returns)
        correlation = self._calculate_correlation(portfolio_returns, benchmark_returns)
        analysis['beta'] = beta
        analysis['correlation'] = correlation
        return analysis

    def performance_persistence(self, returns_by_period: List[List[Decimal]]) -> Dict[str, Any]:
        """
        Analyze performance persistence across periods

        Args:
            returns_by_period: List of return lists for different periods

        Returns:
            Persistence analysis metrics
        """
        if len(returns_by_period) < 2:
            return {'error': 'Need at least 2 periods for persistence analysis'}
        persistence = {}
        period_rankings = []
        for period_returns in returns_by_period:
            if not period_returns:
                continue
            sorted_returns = sorted(period_returns, reverse=True)
            rankings = []
            for ret in period_returns:
                rank = sorted_returns.index(ret) + 1
                rankings.append(rank)
            period_rankings.append(rankings)
        if len(period_rankings) < 2:
            return {'error': 'Insufficient valid periods'}
        correlations = []
        for i in range(len(period_rankings) - 1):
            corr = self._calculate_rank_correlation(period_rankings[i], period_rankings[i + 1])
            correlations.append(corr)
        persistence['rank_correlations'] = correlations
        persistence['average_rank_correlation'] = sum(correlations) / len(correlations) if correlations else Decimal('0')
        return persistence

    def _calculate_volatility(self, returns: List[Decimal]) -> Decimal:
        """Calculate standard deviation of returns"""
        if len(returns) < 2:
            return Decimal('0')
        mean_return = sum(returns) / len(returns)
        variance = sum(((r - mean_return) ** 2 for r in returns)) / (len(returns) - 1)
        return variance.sqrt()

    def _calculate_beta(self, portfolio_returns: List[Decimal], benchmark_returns: List[Decimal]) -> Decimal:
        """Calculate beta (systematic risk measure)"""
        if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
            return Decimal('1')
        port_mean = sum(portfolio_returns) / len(portfolio_returns)
        bench_mean = sum(benchmark_returns) / len(benchmark_returns)
        covariance = sum(((p - port_mean) * (b - bench_mean) for p, b in zip(portfolio_returns, benchmark_returns))) / (len(portfolio_returns) - 1)
        bench_variance = sum(((b - bench_mean) ** 2 for b in benchmark_returns)) / (len(benchmark_returns) - 1)
        if bench_variance == 0:
            return Decimal('1')
        return Decimal(str(covariance)) / Decimal(str(bench_variance))

    def _calculate_correlation(self, x: List[Decimal], y: List[Decimal]) -> Decimal:
        """Calculate correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return Decimal('0')
        x_mean = sum(x) / len(x)
        y_mean = sum(y) / len(y)
        numerator = sum(((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)))
        x_sq_sum = sum(((xi - x_mean) ** 2 for xi in x))
        y_sq_sum = sum(((yi - y_mean) ** 2 for yi in y))
        denominator = (x_sq_sum * y_sq_sum).sqrt()
        if denominator == 0:
            return Decimal('0')
        return numerator / denominator

    def _calculate_rank_correlation(self, ranks1: List[int], ranks2: List[int]) -> Decimal:
        """Calculate Spearman rank correlation"""
        if len(ranks1) != len(ranks2) or len(ranks1) < 2:
            return Decimal('0')
        n = len(ranks1)
        d_squared_sum = sum(((r1 - r2) ** 2 for r1, r2 in zip(ranks1, ranks2)))
        correlation = Decimal('1') - Decimal('6') * Decimal(str(d_squared_sum)) / (Decimal(str(n)) * (Decimal(str(n)) ** 2 - Decimal('1')))
        return correlation

    def _calculate_cvar(self, returns: List[Decimal], confidence_level: Decimal) -> Decimal:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        if not returns:
            return Decimal('0')
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * confidence_level)
        if var_index >= len(sorted_returns):
            var_index = len(sorted_returns) - 1
        tail_returns = sorted_returns[:var_index + 1]
        if not tail_returns:
            return Decimal('0')
        cvar = sum(tail_returns) / len(tail_returns)
        return abs(cvar)

def __init__(self):
    self.math = FinancialMath()
    self.config = Config()

class FeeAnalyzer:
    """
    Analyze fee structures and their impact on performance
    CFA Standards: Fee transparency and impact analysis
    """

    def __init__(self):
        self.config = Config()

    def calculate_fee_impact(self, gross_returns: List[Decimal], management_fee: Decimal, performance_fee: Decimal=None, hurdle_rate: Decimal=None, high_water_mark: bool=True) -> Dict[str, Any]:
        """
        Calculate the impact of fees on investment returns

        Args:
            gross_returns: Gross returns before fees
            management_fee: Annual management fee rate
            performance_fee: Performance fee rate (if applicable)
            hurdle_rate: Hurdle rate for performance fees
            high_water_mark: Whether high water mark applies

        Returns:
            Fee impact analysis
        """
        if not gross_returns:
            return {'error': 'No returns provided'}
        net_returns = []
        cumulative_nav = Decimal('100')
        high_water_mark_value = cumulative_nav if high_water_mark else None
        periods_per_year = 12
        monthly_mgmt_fee = management_fee / periods_per_year
        total_mgmt_fees = Decimal('0')
        total_perf_fees = Decimal('0')
        for gross_return in gross_returns:
            period_nav = cumulative_nav * (Decimal('1') + gross_return)
            mgmt_fee_amount = cumulative_nav * monthly_mgmt_fee
            total_mgmt_fees += mgmt_fee_amount
            perf_fee_amount = Decimal('0')
            if performance_fee and performance_fee > 0:
                if hurdle_rate:
                    monthly_hurdle = hurdle_rate / periods_per_year
                    hurdle_return = cumulative_nav * monthly_hurdle
                else:
                    hurdle_return = Decimal('0')
                excess_return = max(Decimal('0'), period_nav - cumulative_nav - hurdle_return)
                if high_water_mark and high_water_mark_value:
                    if period_nav > high_water_mark_value:
                        perf_fee_amount = excess_return * performance_fee
                        high_water_mark_value = period_nav
                else:
                    perf_fee_amount = excess_return * performance_fee
                total_perf_fees += perf_fee_amount
            net_nav = period_nav - mgmt_fee_amount - perf_fee_amount
            net_return = (net_nav - cumulative_nav) / cumulative_nav
            net_returns.append(net_return)
            cumulative_nav = net_nav
        gross_cumulative = Decimal('1')
        net_cumulative = Decimal('1')
        for gross_ret, net_ret in zip(gross_returns, net_returns):
            gross_cumulative *= Decimal('1') + gross_ret
            net_cumulative *= Decimal('1') + net_ret
        fee_drag = (gross_cumulative - net_cumulative) / gross_cumulative
        return {'gross_cumulative_return': gross_cumulative - Decimal('1'), 'net_cumulative_return': net_cumulative - Decimal('1'), 'total_fee_drag': fee_drag, 'total_management_fees': total_mgmt_fees, 'total_performance_fees': total_perf_fees, 'total_fees': total_mgmt_fees + total_perf_fees, 'net_returns': net_returns, 'fee_ratio': (total_mgmt_fees + total_perf_fees) / (cumulative_nav * len(gross_returns))}

def __init__(self):
    self.config = Config()

class RiskAnalyzer:
    """
    Comprehensive risk analysis for alternative investments
    CFA Standards: Risk measurement, stress testing, scenario analysis
    """

    def __init__(self):
        self.math = FinancialMath()
        self.config = Config()

    def value_at_risk_analysis(self, returns: List[Decimal], confidence_levels: List[Decimal]=None) -> Dict[str, Any]:
        """
        Comprehensive Value at Risk analysis
        CFA Standard: Historical simulation, parametric, and Monte Carlo VaR
        """
        if not returns:
            return {'error': 'No return data provided'}
        if confidence_levels is None:
            confidence_levels = [Decimal('0.01'), Decimal('0.05'), Decimal('0.10')]
        var_analysis = {}
        historical_var = {}
        for confidence in confidence_levels:
            var_value = self.math.var_historical(returns, confidence)
            confidence_pct = int((1 - confidence) * 100)
            historical_var[f'var_{confidence_pct}'] = float(var_value)
        var_analysis['historical_var'] = historical_var
        mean_return = sum(returns) / len(returns)
        volatility = self._calculate_volatility(returns)
        parametric_var = {}
        for confidence in confidence_levels:
            z_scores = {Decimal('0.01'): Decimal('-2.326'), Decimal('0.05'): Decimal('-1.645'), Decimal('0.10'): Decimal('-1.282')}
            z_score = z_scores.get(confidence, Decimal('-1.645'))
            var_value = mean_return + z_score * volatility
            confidence_pct = int((1 - confidence) * 100)
            parametric_var[f'var_{confidence_pct}'] = float(abs(var_value))
        var_analysis['parametric_var'] = parametric_var
        conditional_var = {}
        for confidence in confidence_levels:
            cvar_value = self._calculate_conditional_var(returns, confidence)
            confidence_pct = int((1 - confidence) * 100)
            conditional_var[f'cvar_{confidence_pct}'] = float(cvar_value)
        var_analysis['conditional_var'] = conditional_var
        var_analysis['model_comparison'] = self._compare_var_models(historical_var, parametric_var, returns)
        return var_analysis

    def stress_testing(self, returns: List[Decimal], asset_class: AssetClass=None) -> Dict[str, Any]:
        """
        Comprehensive stress testing framework
        CFA Standard: Scenario analysis and stress testing
        """
        if not returns:
            return {'error': 'No return data provided'}
        stress_results = {}
        historical_scenarios = self._historical_stress_scenarios(returns)
        stress_results['historical_scenarios'] = historical_scenarios
        hypothetical_scenarios = self._hypothetical_stress_scenarios(returns, asset_class)
        stress_results['hypothetical_scenarios'] = hypothetical_scenarios
        monte_carlo_scenarios = self._monte_carlo_stress_testing(returns)
        stress_results['monte_carlo_scenarios'] = monte_carlo_scenarios
        tail_risk = self._analyze_tail_risk(returns)
        stress_results['tail_risk_analysis'] = tail_risk
        return stress_results

    def correlation_analysis(self, asset_returns: Dict[str, List[Decimal]], rolling_window: int=60) -> Dict[str, Any]:
        """
        Dynamic correlation analysis across asset classes
        CFA Standard: Correlation analysis and diversification benefits
        """
        if len(asset_returns) < 2:
            return {'error': 'Need at least 2 asset return series'}
        correlation_analysis = {}
        static_correlations = self._calculate_correlation_matrix(asset_returns)
        correlation_analysis['static_correlations'] = static_correlations
        rolling_correlations = self._calculate_rolling_correlations(asset_returns, rolling_window)
        correlation_analysis['rolling_correlations'] = rolling_correlations
        correlation_breakdown = self._analyze_correlation_breakdown(asset_returns)
        correlation_analysis['correlation_breakdown'] = correlation_breakdown
        diversification_metrics = self._calculate_diversification_metrics(static_correlations)
        correlation_analysis['diversification_metrics'] = diversification_metrics
        return correlation_analysis

    def liquidity_risk_assessment(self, trading_volumes: List[Decimal], market_caps: List[Decimal]=None, bid_ask_spreads: List[Decimal]=None) -> Dict[str, Any]:
        """
        Comprehensive liquidity risk assessment
        CFA Standard: Liquidity risk measurement and management
        """
        liquidity_assessment = {}
        if not trading_volumes:
            return {'error': 'Trading volume data required'}
        volume_metrics = self._analyze_volume_patterns(trading_volumes)
        liquidity_assessment['volume_metrics'] = volume_metrics
        if market_caps:
            market_impact = self._estimate_market_impact(trading_volumes, market_caps)
            liquidity_assessment['market_impact'] = market_impact
        if bid_ask_spreads:
            spread_analysis = self._analyze_bid_ask_spreads(bid_ask_spreads)
            liquidity_assessment['spread_analysis'] = spread_analysis
        liquidity_score = self._calculate_liquidity_score(volume_metrics, market_caps, bid_ask_spreads)
        liquidity_assessment['liquidity_score'] = liquidity_score
        return liquidity_assessment

    def drawdown_analysis(self, price_series: List[Decimal]) -> Dict[str, Any]:
        """
        Comprehensive drawdown analysis
        CFA Standard: Drawdown measurement and recovery analysis
        """
        if len(price_series) < 2:
            return {'error': 'Insufficient price data'}
        drawdown_results = {}
        drawdowns = self._calculate_drawdown_series(price_series)
        max_dd, peak_idx, trough_idx = self.math.maximum_drawdown(price_series)
        drawdown_results['maximum_drawdown'] = float(max_dd)
        drawdown_results['peak_to_trough_periods'] = trough_idx - peak_idx
        dd_stats = self._calculate_drawdown_statistics(drawdowns)
        drawdown_results['drawdown_statistics'] = dd_stats
        recovery_analysis = self._analyze_recovery_patterns(price_series, drawdowns)
        drawdown_results['recovery_analysis'] = recovery_analysis
        ulcer_index = self._calculate_ulcer_index(drawdowns)
        drawdown_results['ulcer_index'] = float(ulcer_index)
        return drawdown_results

    def risk_attribution(self, portfolio_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]]) -> Dict[str, Any]:
        """
        Risk attribution analysis using factor models
        CFA Standard: Risk factor decomposition
        """
        if not portfolio_returns or not factor_returns:
            return {'error': 'Portfolio returns and factor returns required'}
        attribution_results = {}
        factor_exposures = self._calculate_factor_exposures(portfolio_returns, factor_returns)
        attribution_results['factor_exposures'] = factor_exposures
        risk_contributions = self._calculate_risk_contributions(portfolio_returns, factor_returns, factor_exposures)
        attribution_results['risk_contributions'] = risk_contributions
        idiosyncratic_risk = self._calculate_idiosyncratic_risk(portfolio_returns, factor_returns, factor_exposures)
        attribution_results['idiosyncratic_risk'] = float(idiosyncratic_risk)
        return attribution_results

    def scenario_analysis(self, base_returns: List[Decimal], scenarios: Dict[str, Dict[str, Decimal]]) -> Dict[str, Any]:
        """
        Comprehensive scenario analysis
        CFA Standard: Scenario planning and sensitivity analysis
        """
        scenario_results = {}
        for scenario_name, scenario_params in scenarios.items():
            scenario_impact = self._calculate_scenario_impact(base_returns, scenario_params)
            scenario_results[scenario_name] = scenario_impact
        scenario_summary = self._summarize_scenario_outcomes(scenario_results)
        scenario_results['scenario_summary'] = scenario_summary
        return scenario_results

    def _calculate_volatility(self, returns: List[Decimal]) -> Decimal:
        """Calculate standard deviation of returns"""
        if len(returns) < 2:
            return Decimal('0')
        mean_return = sum(returns) / len(returns)
        variance = sum(((r - mean_return) ** 2 for r in returns)) / (len(returns) - 1)
        return variance.sqrt()

    def _calculate_conditional_var(self, returns: List[Decimal], confidence: Decimal) -> Decimal:
        """Calculate Conditional VaR (Expected Shortfall)"""
        if not returns:
            return Decimal('0')
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * confidence)
        if var_index >= len(sorted_returns):
            var_index = len(sorted_returns) - 1
        tail_returns = sorted_returns[:var_index + 1]
        if not tail_returns:
            return Decimal('0')
        cvar = sum(tail_returns) / len(tail_returns)
        return abs(cvar)

    def _compare_var_models(self, historical_var: Dict, parametric_var: Dict, returns: List[Decimal]) -> Dict[str, Any]:
        """Compare different VaR model approaches"""
        comparison = {}
        for confidence_key in historical_var.keys():
            hist_var = historical_var[confidence_key]
            param_var = parametric_var[confidence_key]
            difference = abs(hist_var - param_var)
            relative_difference = difference / hist_var if hist_var != 0 else 0
            comparison[confidence_key] = {'historical_var': hist_var, 'parametric_var': param_var, 'absolute_difference': difference, 'relative_difference': relative_difference}
        avg_relative_diff = sum((comp['relative_difference'] for comp in comparison.values())) / len(comparison)
        if avg_relative_diff < 0.1:
            comparison['recommended_model'] = 'Either (similar results)'
        elif len(returns) < 100:
            comparison['recommended_model'] = 'Parametric (limited history)'
        else:
            comparison['recommended_model'] = 'Historical (sufficient data)'
        return comparison

    def _historical_stress_scenarios(self, returns: List[Decimal]) -> Dict[str, Any]:
        """Analyze historical stress periods"""
        if len(returns) < 20:
            return {'insufficient_data': True}
        worst_returns = sorted(returns)[:10]
        scenarios = {}
        scenarios['worst_single_period'] = {'return': float(worst_returns[0]), 'impact': f'{float(worst_returns[0] * 100):.2f}%'}
        worst_consecutive = self._find_worst_consecutive_periods(returns, 5)
        scenarios['worst_5_period_sequence'] = {'cumulative_return': float(worst_consecutive), 'impact': f'{float(worst_consecutive * 100):.2f}%'}
        return scenarios

    def _hypothetical_stress_scenarios(self, returns: List[Decimal], asset_class: AssetClass=None) -> Dict[str, Any]:
        """Generate hypothetical stress scenarios"""
        scenarios = {}
        current_vol = self._calculate_volatility(returns)
        two_sigma_shock = current_vol * Decimal('2')
        scenarios['two_sigma_shock'] = {'negative_shock': float(-two_sigma_shock), 'positive_shock': float(two_sigma_shock)}
        if asset_class:
            asset_scenarios = self._get_asset_class_scenarios(asset_class)
            scenarios.update(asset_scenarios)
        return scenarios

    def _monte_carlo_stress_testing(self, returns: List[Decimal], num_simulations: int=1000) -> Dict[str, Any]:
        """Monte Carlo stress testing"""
        if len(returns) < 10:
            return {'insufficient_data': True}
        mean_return = sum(returns) / len(returns)
        volatility = self._calculate_volatility(returns)
        simulated_outcomes = []
        try:
            import random
            random.seed(42)
            for _ in range(num_simulations):
                z = Decimal(str(random.gauss(0, 1)))
                simulated_return = mean_return + volatility * z
                simulated_outcomes.append(simulated_return)
        except ImportError:
            for i in range(num_simulations):
                z = Decimal(str((i - num_simulations / 2) / (num_simulations / 4)))
                simulated_return = mean_return + volatility * z
                simulated_outcomes.append(simulated_return)
        sorted_outcomes = sorted(simulated_outcomes)
        return {'worst_1_percent': float(sorted_outcomes[int(0.01 * len(sorted_outcomes))]), 'worst_5_percent': float(sorted_outcomes[int(0.05 * len(sorted_outcomes))]), 'best_5_percent': float(sorted_outcomes[int(0.95 * len(sorted_outcomes))]), 'median_outcome': float(sorted_outcomes[len(sorted_outcomes) // 2]), 'simulations_run': num_simulations}

    def _analyze_tail_risk(self, returns: List[Decimal]) -> Dict[str, Any]:
        """Analyze tail risk characteristics"""
        if len(returns) < 20:
            return {'insufficient_data': True}
        sorted_returns = sorted(returns)
        left_tail_10pct = sorted_returns[:len(returns) // 10]
        right_tail_10pct = sorted_returns[-len(returns) // 10:]
        left_tail_mean = sum(left_tail_10pct) / len(left_tail_10pct) if left_tail_10pct else Decimal('0')
        right_tail_mean = sum(right_tail_10pct) / len(right_tail_10pct) if right_tail_10pct else Decimal('0')
        return {'left_tail_mean': float(left_tail_mean), 'right_tail_mean': float(right_tail_mean), 'tail_ratio': float(abs(left_tail_mean / right_tail_mean)) if right_tail_mean != 0 else 0, 'skewness_indicator': 'negative_skew' if abs(left_tail_mean) > right_tail_mean else 'positive_skew'}

    def _calculate_correlation_matrix(self, asset_returns: Dict[str, List[Decimal]]) -> Dict[str, Dict[str, float]]:
        """Calculate static correlation matrix"""
        assets = list(asset_returns.keys())
        correlation_matrix = {}
        for asset1 in assets:
            correlation_matrix[asset1] = {}
            for asset2 in assets:
                if asset1 == asset2:
                    correlation_matrix[asset1][asset2] = 1.0
                else:
                    returns1 = asset_returns[asset1]
                    returns2 = asset_returns[asset2]
                    if len(returns1) == len(returns2) and len(returns1) > 1:
                        correlation = self._calculate_correlation(returns1, returns2)
                        correlation_matrix[asset1][asset2] = float(correlation)
                    else:
                        correlation_matrix[asset1][asset2] = 0.0
        return correlation_matrix

    def _calculate_rolling_correlations(self, asset_returns: Dict[str, List[Decimal]], window: int) -> Dict[str, List[float]]:
        """Calculate rolling correlations between assets"""
        rolling_correlations = {}
        assets = list(asset_returns.keys())
        if len(assets) < 2:
            return rolling_correlations
        asset1, asset2 = (assets[0], assets[1])
        returns1 = asset_returns[asset1]
        returns2 = asset_returns[asset2]
        if len(returns1) != len(returns2) or len(returns1) < window:
            return rolling_correlations
        correlations = []
        for i in range(window, len(returns1)):
            window_returns1 = returns1[i - window:i]
            window_returns2 = returns2[i - window:i]
            correlation = self._calculate_correlation(window_returns1, window_returns2)
            correlations.append(float(correlation))
        rolling_correlations[f'{asset1}_vs_{asset2}'] = correlations
        return rolling_correlations

    def _calculate_correlation(self, returns1: List[Decimal], returns2: List[Decimal]) -> Decimal:
        """Calculate correlation coefficient"""
        if len(returns1) != len(returns2) or len(returns1) < 2:
            return Decimal('0')
        mean1 = sum(returns1) / len(returns1)
        mean2 = sum(returns2) / len(returns2)
        numerator = sum(((r1 - mean1) * (r2 - mean2) for r1, r2 in zip(returns1, returns2)))
        sum_sq1 = sum(((r1 - mean1) ** 2 for r1 in returns1))
        sum_sq2 = sum(((r2 - mean2) ** 2 for r2 in returns2))
        denominator = (sum_sq1 * sum_sq2).sqrt()
        if denominator == 0:
            return Decimal('0')
        return numerator / denominator

    def _analyze_correlation_breakdown(self, asset_returns: Dict[str, List[Decimal]]) -> Dict[str, Any]:
        """Analyze correlation breakdown during stress periods"""
        breakdown_analysis = {}
        assets = list(asset_returns.keys())
        if len(assets) < 2:
            return breakdown_analysis
        all_correlations = []
        correlation_matrix = self._calculate_correlation_matrix(asset_returns)
        for asset1 in assets:
            for asset2 in assets:
                if asset1 != asset2:
                    corr = correlation_matrix[asset1][asset2]
                    all_correlations.append(corr)
        if all_correlations:
            avg_correlation = sum(all_correlations) / len(all_correlations)
            breakdown_analysis['average_correlation'] = avg_correlation
            if avg_correlation > 0.7:
                breakdown_analysis['diversification_benefit'] = 'Low'
            elif avg_correlation > 0.4:
                breakdown_analysis['diversification_benefit'] = 'Medium'
            else:
                breakdown_analysis['diversification_benefit'] = 'High'
        return breakdown_analysis

    def _calculate_diversification_metrics(self, correlation_matrix: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Calculate diversification effectiveness metrics"""
        assets = list(correlation_matrix.keys())
        if len(assets) < 2:
            return {}
        all_correlations = []
        for asset1 in assets:
            for asset2 in assets:
                if asset1 != asset2:
                    all_correlations.append(correlation_matrix[asset1][asset2])
        avg_correlation = sum(all_correlations) / len(all_correlations) if all_correlations else 0
        diversification_effectiveness = 1 - abs(avg_correlation)
        return {'average_correlation': avg_correlation, 'diversification_effectiveness': diversification_effectiveness, 'number_of_assets': len(assets)}

    def _analyze_volume_patterns(self, volumes: List[Decimal]) -> Dict[str, Any]:
        """Analyze trading volume patterns for liquidity assessment"""
        if not volumes:
            return {}
        avg_volume = sum(volumes) / len(volumes)
        volume_volatility = self._calculate_volatility(volumes)
        volume_stability = 1 - volume_volatility / avg_volume if avg_volume > 0 else 0
        return {'average_volume': float(avg_volume), 'volume_volatility': float(volume_volatility), 'volume_stability': float(volume_stability)}

    def _estimate_market_impact(self, volumes: List[Decimal], market_caps: List[Decimal]) -> Dict[str, Any]:
        """Estimate market impact for liquidity assessment"""
        if len(volumes) != len(market_caps):
            return {}
        volume_ratios = []
        for vol, mcap in zip(volumes, market_caps):
            if mcap > 0:
                ratio = vol / mcap
                volume_ratios.append(ratio)
        if not volume_ratios:
            return {}
        avg_volume_ratio = sum(volume_ratios) / len(volume_ratios)
        if avg_volume_ratio > Decimal('0.1'):
            impact_assessment = 'Low'
        elif avg_volume_ratio > Decimal('0.01'):
            impact_assessment = 'Medium'
        else:
            impact_assessment = 'High'
        return {'average_volume_to_mcap': float(avg_volume_ratio), 'market_impact_assessment': impact_assessment}

    def _analyze_bid_ask_spreads(self, spreads: List[Decimal]) -> Dict[str, Any]:
        """Analyze bid-ask spreads for liquidity assessment"""
        if not spreads:
            return {}
        avg_spread = sum(spreads) / len(spreads)
        spread_volatility = self._calculate_volatility(spreads)
        return {'average_spread': float(avg_spread), 'spread_volatility': float(spread_volatility), 'spread_stability': float(1 - spread_volatility / avg_spread) if avg_spread > 0 else 0}

    def _calculate_liquidity_score(self, volume_metrics: Dict, market_caps: List[Decimal], bid_ask_spreads: List[Decimal]) -> Dict[str, Any]:
        """Calculate composite liquidity score"""
        score_components = {}
        total_score = 0
        components_count = 0
        if volume_metrics and 'volume_stability' in volume_metrics:
            volume_score = volume_metrics['volume_stability'] * 100
            score_components['volume_score'] = volume_score
            total_score += volume_score
            components_count += 1
        if market_caps:
            avg_mcap = sum(market_caps) / len(market_caps)
            mcap_score = min(100, float(avg_mcap) / 1000000)
            score_components['market_cap_score'] = mcap_score
            total_score += mcap_score
            components_count += 1
        if bid_ask_spreads:
            avg_spread = sum(bid_ask_spreads) / len(bid_ask_spreads)
            spread_score = max(0, 100 - float(avg_spread * 10000))
            score_components['spread_score'] = spread_score
            total_score += spread_score
            components_count += 1
        composite_score = total_score / components_count if components_count > 0 else 0
        return {'composite_liquidity_score': composite_score, 'score_components': score_components, 'liquidity_rating': self._get_liquidity_rating(composite_score)}

    def _get_liquidity_rating(self, score: float) -> str:
        """Convert liquidity score to rating"""
        if score >= 80:
            return 'Excellent'
        elif score >= 60:
            return 'Good'
        elif score >= 40:
            return 'Fair'
        elif score >= 20:
            return 'Poor'
        else:
            return 'Very Poor'

    def _calculate_drawdown_series(self, price_series: List[Decimal]) -> List[Decimal]:
        """Calculate drawdown series from price series"""
        if not price_series:
            return []
        drawdowns = []
        peak = price_series[0]
        for price in price_series:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            drawdowns.append(drawdown)
        return drawdowns

    def _calculate_drawdown_statistics(self, drawdowns: List[Decimal]) -> Dict[str, Any]:
        """Calculate comprehensive drawdown statistics"""
        if not drawdowns:
            return {}
        max_dd = max(drawdowns)
        avg_dd = sum(drawdowns) / len(drawdowns)
        periods_in_drawdown = sum((1 for dd in drawdowns if dd > 0))
        drawdown_frequency = periods_in_drawdown / len(drawdowns)
        return {'maximum_drawdown': float(max_dd), 'average_drawdown': float(avg_dd), 'drawdown_frequency': float(drawdown_frequency), 'periods_in_drawdown': periods_in_drawdown, 'total_periods': len(drawdowns)}

    def _analyze_recovery_patterns(self, price_series: List[Decimal], drawdowns: List[Decimal]) -> Dict[str, Any]:
        """Analyze recovery patterns from drawdowns"""
        if len(price_series) != len(drawdowns):
            return {}
        recovery_periods = []
        in_drawdown = False
        drawdown_start = 0
        for i, dd in enumerate(drawdowns):
            if dd > 0 and (not in_drawdown):
                in_drawdown = True
                drawdown_start = i
            elif dd == 0 and in_drawdown:
                recovery_period = i - drawdown_start
                recovery_periods.append(recovery_period)
                in_drawdown = False
        if not recovery_periods:
            return {'no_complete_recoveries': True}
        avg_recovery_period = sum(recovery_periods) / len(recovery_periods)
        max_recovery_period = max(recovery_periods)
        return {'average_recovery_period': avg_recovery_period, 'maximum_recovery_period': max_recovery_period, 'number_of_recoveries': len(recovery_periods)}

    def _calculate_ulcer_index(self, drawdowns: List[Decimal]) -> Decimal:
        """Calculate Ulcer Index (alternative drawdown measure)"""
        if not drawdowns:
            return Decimal('0')
        squared_drawdowns = [dd ** 2 for dd in drawdowns]
        mean_squared_dd = sum(squared_drawdowns) / len(squared_drawdowns)
        return mean_squared_dd.sqrt()

    def _calculate_factor_exposures(self, portfolio_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]]) -> Dict[str, float]:
        """Calculate factor exposures using regression"""
        try:
            y = [float(r) for r in portfolio_returns]
            factors = []
            factor_names = []
            for factor_name, returns in factor_returns.items():
                if len(returns) == len(portfolio_returns):
                    factors.append([float(r) for r in returns])
                    factor_names.append(factor_name)
            if not factors:
                return {}
            try:
                import numpy as np
                X = np.array(factors).T
                X = np.column_stack([np.ones(len(y)), X])
                coefficients = np.linalg.lstsq(X, y, rcond=None)[0]
                exposures = {'alpha': float(coefficients[0])}
                for i, factor_name in enumerate(factor_names):
                    exposures[f'{factor_name}_beta'] = float(coefficients[i + 1])
                y_pred = X @ coefficients
                ss_res = np.sum((np.array(y) - y_pred) ** 2)
                ss_tot = np.sum((np.array(y) - np.mean(y)) ** 2)
                r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else 0
                exposures['r_squared'] = float(r_squared)
                return exposures
            except ImportError:
                exposures = {}
                for factor_name, factor_rets in zip(factor_names, factors):
                    if len(factor_rets) == len(portfolio_returns):
                        correlation = self._calculate_correlation(portfolio_returns, [Decimal(str(r)) for r in factor_rets])
                        exposures[f'{factor_name}_beta'] = float(correlation)
                return exposures
        except Exception as e:
            logger.error(f'Error calculating factor exposures: {str(e)}')
            return {}

    def _calculate_risk_contributions(self, portfolio_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]], factor_exposures: Dict[str, float]) -> Dict[str, float]:
        """Calculate risk contribution by factor"""
        risk_contributions = {}
        portfolio_variance = float(self._calculate_volatility(portfolio_returns) ** 2)
        for factor_name, factor_rets in factor_returns.items():
            beta_key = f'{factor_name}_beta'
            if beta_key in factor_exposures and len(factor_rets) == len(portfolio_returns):
                factor_beta = Decimal(str(factor_exposures[beta_key]))
                factor_variance = self._calculate_volatility([Decimal(str(r)) for r in factor_rets]) ** 2
                if portfolio_variance > 0:
                    risk_contrib = float(factor_beta ** 2 * factor_variance / Decimal(str(portfolio_variance)))
                    risk_contributions[factor_name] = risk_contrib
        return risk_contributions

    def _calculate_idiosyncratic_risk(self, portfolio_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]], factor_exposures: Dict[str, float]) -> Decimal:
        """Calculate idiosyncratic (specific) risk"""
        try:
            total_variance = self._calculate_volatility(portfolio_returns) ** 2
            explained_variance = Decimal('0')
            for factor_name, factor_rets in factor_returns.items():
                beta_key = f'{factor_name}_beta'
                if beta_key in factor_exposures and len(factor_rets) == len(portfolio_returns):
                    factor_beta = Decimal(str(factor_exposures[beta_key]))
                    factor_variance = self._calculate_volatility([Decimal(str(r)) for r in factor_rets]) ** 2
                    explained_variance += factor_beta ** 2 * factor_variance
            idiosyncratic_variance = max(Decimal('0'), total_variance - explained_variance)
            return idiosyncratic_variance.sqrt()
        except Exception:
            return Decimal('0')

    def _calculate_scenario_impact(self, base_returns: List[Decimal], scenario_params: Dict[str, Decimal]) -> Dict[str, Any]:
        """Calculate impact of specific scenario"""
        scenario_impact = {}
        shock_magnitude = scenario_params.get('shock_magnitude', Decimal('0'))
        shock_probability = scenario_params.get('probability', Decimal('1'))
        base_mean = sum(base_returns) / len(base_returns) if base_returns else Decimal('0')
        scenario_return = base_mean + shock_magnitude
        scenario_impact['scenario_return'] = float(scenario_return)
        scenario_impact['shock_magnitude'] = float(shock_magnitude)
        scenario_impact['probability'] = float(shock_probability)
        expected_impact = scenario_return * shock_probability
        scenario_impact['expected_impact'] = float(expected_impact)
        return scenario_impact

    def _summarize_scenario_outcomes(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize scenario analysis outcomes"""
        summary = {}
        scenario_returns = []
        expected_impacts = []
        for scenario_name, scenario_data in scenario_results.items():
            if isinstance(scenario_data, dict) and 'scenario_return' in scenario_data:
                scenario_returns.append(scenario_data['scenario_return'])
                if 'expected_impact' in scenario_data:
                    expected_impacts.append(scenario_data['expected_impact'])
        if scenario_returns:
            summary['best_case_return'] = max(scenario_returns)
            summary['worst_case_return'] = min(scenario_returns)
            summary['scenario_range'] = max(scenario_returns) - min(scenario_returns)
        if expected_impacts:
            summary['expected_scenario_impact'] = sum(expected_impacts) / len(expected_impacts)
        return summary

    def _find_worst_consecutive_periods(self, returns: List[Decimal], num_periods: int) -> Decimal:
        """Find worst consecutive period returns"""
        if len(returns) < num_periods:
            return Decimal('0')
        worst_cumulative = Decimal('0')
        for i in range(len(returns) - num_periods + 1):
            cumulative_return = Decimal('1')
            for j in range(i, i + num_periods):
                cumulative_return *= Decimal('1') + returns[j]
            period_return = cumulative_return - Decimal('1')
            if period_return < worst_cumulative:
                worst_cumulative = period_return
        return worst_cumulative

    def _get_asset_class_scenarios(self, asset_class: AssetClass) -> Dict[str, Any]:
        """Get asset class specific stress scenarios"""
        scenarios = {}
        if asset_class == AssetClass.PRIVATE_EQUITY:
            scenarios.update({'recession_scenario': {'description': 'Economic recession impact', 'expected_impact': -0.3, 'recovery_time': '24_months'}, 'credit_crunch': {'description': 'Limited exit opportunities', 'expected_impact': -0.25, 'recovery_time': '18_months'}})
        elif asset_class == AssetClass.REAL_ESTATE:
            scenarios.update({'interest_rate_shock': {'description': '300bp rate increase', 'expected_impact': -0.2, 'recovery_time': '12_months'}, 'property_market_crash': {'description': 'Property values decline', 'expected_impact': -0.35, 'recovery_time': '36_months'}})
        elif asset_class == AssetClass.COMMODITIES:
            scenarios.update({'demand_shock': {'description': 'Global demand reduction', 'expected_impact': -0.4, 'recovery_time': '6_months'}, 'supply_disruption': {'description': 'Supply chain disruption', 'expected_impact': 0.25, 'recovery_time': '12_months'}})
        elif asset_class == AssetClass.HEDGE_FUND:
            scenarios.update({'market_volatility_spike': {'description': 'VIX above 40', 'expected_impact': -0.15, 'recovery_time': '3_months'}, 'liquidity_crisis': {'description': 'Redemption pressure', 'expected_impact': -0.2, 'recovery_time': '6_months'}})
        elif asset_class == AssetClass.DIGITAL_ASSETS:
            scenarios.update({'regulatory_crackdown': {'description': 'Major regulatory restrictions', 'expected_impact': -0.5, 'recovery_time': '12_months'}, 'crypto_winter': {'description': 'Extended bear market', 'expected_impact': -0.7, 'recovery_time': '24_months'}})
        return scenarios

def __init__(self):
    self.math = FinancialMath()
    self.config = Config()

class AlternativeInvestmentBase(ABC):
    """
    Abstract base class for all alternative investment types
    Defines common interface and shared functionality
    """

    def __init__(self, parameters: AssetParameters):
        self.parameters = parameters
        self.market_data: List[MarketData] = []
        self.cash_flows: List[CashFlow] = []
        self.performance_history: List[Performance] = []
        self.config = Config()
        self.math = FinancialMath()
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Validate asset parameters"""
        if self.parameters.management_fee:
            if not ValidationRules.validate_management_fee(self.parameters.management_fee, self.parameters.asset_class):
                raise ValueError(f'Invalid management fee: {self.parameters.management_fee}')
        if self.parameters.performance_fee:
            if not ValidationRules.validate_performance_fee(self.parameters.performance_fee, self.parameters.asset_class):
                raise ValueError(f'Invalid performance fee: {self.parameters.performance_fee}')

    def add_market_data(self, data: List[MarketData]) -> None:
        """Add market data to the investment"""
        self.market_data.extend(data)
        self.market_data.sort(key=lambda x: x.timestamp)

    def add_cash_flows(self, cash_flows: List[CashFlow]) -> None:
        """Add cash flows to the investment"""
        self.cash_flows.extend(cash_flows)
        self.cash_flows.sort(key=lambda x: x.date)

    def get_latest_price(self) -> Optional[Decimal]:
        """Get the most recent price"""
        if not self.market_data:
            return None
        return self.market_data[-1].price

    def get_price_history(self, start_date: str=None, end_date: str=None) -> List[MarketData]:
        """Get price history for specified date range"""
        filtered_data = self.market_data
        if start_date:
            filtered_data = [d for d in filtered_data if d.timestamp >= start_date]
        if end_date:
            filtered_data = [d for d in filtered_data if d.timestamp <= end_date]
        return filtered_data

    def calculate_simple_returns(self) -> List[Decimal]:
        """Calculate simple returns from price data"""
        if len(self.market_data) < 2:
            return []
        returns = []
        for i in range(1, len(self.market_data)):
            prev_price = self.market_data[i - 1].price
            curr_price = self.market_data[i].price
            ret = (curr_price - prev_price) / prev_price
            returns.append(ret)
        return returns

    def calculate_log_returns(self) -> List[Decimal]:
        """Calculate logarithmic returns from price data"""
        if len(self.market_data) < 2:
            return []
        returns = []
        for i in range(1, len(self.market_data)):
            prev_price = self.market_data[i - 1].price
            curr_price = self.market_data[i].price
            ret = (curr_price / prev_price).ln()
            returns.append(ret)
        return returns

    def calculate_volatility(self, returns: List[Decimal]=None, annualized: bool=True) -> Decimal:
        """Calculate volatility (standard deviation of returns)"""
        if returns is None:
            returns = self.calculate_simple_returns()
        if len(returns) < 2:
            return Decimal('0')
        mean_return = sum(returns) / len(returns)
        variance = sum(((r - mean_return) ** 2 for r in returns)) / (len(returns) - 1)
        volatility = variance.sqrt()
        if annualized:
            volatility *= Constants.BUSINESS_DAYS_IN_YEAR.sqrt()
        return volatility

    def calculate_total_return(self, start_date: str=None, end_date: str=None) -> Decimal:
        """Calculate total return including distributions"""
        price_data = self.get_price_history(start_date, end_date)
        if len(price_data) < 2:
            return Decimal('0')
        start_price = price_data[0].price
        end_price = price_data[-1].price
        price_return = (end_price - start_price) / start_price
        relevant_cfs = self.cash_flows
        if start_date:
            relevant_cfs = [cf for cf in relevant_cfs if cf.date >= start_date]
        if end_date:
            relevant_cfs = [cf for cf in relevant_cfs if cf.date <= end_date]
        distributions = sum((cf.amount for cf in relevant_cfs if cf.amount > 0))
        distribution_return = distributions / start_price
        return price_return + distribution_return

    def calculate_fees(self, nav: Decimal, period_days: int=365) -> Dict[str, Decimal]:
        """Calculate management and performance fees"""
        fees = {}
        if self.parameters.management_fee:
            mgmt_fee = nav * self.parameters.management_fee * (Decimal(str(period_days)) / Constants.DAYS_IN_YEAR)
            fees['management_fee'] = mgmt_fee
        if self.parameters.performance_fee:
            returns = self.calculate_simple_returns()
            if returns:
                excess_return = sum(returns) - (self.parameters.hurdle_rate or Decimal('0'))
                if excess_return > 0:
                    perf_fee = nav * excess_return * self.parameters.performance_fee
                    fees['performance_fee'] = perf_fee
        return fees

    @abstractmethod
    def calculate_nav(self) -> Decimal:
        """Calculate Net Asset Value - must be implemented by subclasses"""
        pass

    @abstractmethod
    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key performance metrics - must be implemented by subclasses"""
        pass

    @abstractmethod
    def valuation_summary(self) -> Dict[str, Any]:
        """Provide valuation summary - must be implemented by subclasses"""
        pass

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        returns = self.calculate_simple_returns()
        if not returns:
            return {'error': 'Insufficient data for performance calculation'}
        volatility = self.calculate_volatility(returns)
        sharpe = self.math.sharpe_ratio(returns)
        sortino = self.math.sortino_ratio(returns)
        prices = [md.price for md in self.market_data]
        max_dd, peak_idx, trough_idx = self.math.maximum_drawdown(prices)
        var_95 = self.math.var_historical(returns, Decimal('0.05'))
        total_return = self.calculate_total_return()
        return {'total_return': float(total_return), 'annualized_return': float(total_return * Constants.DAYS_IN_YEAR / len(self.market_data)), 'volatility': float(volatility), 'sharpe_ratio': float(sharpe), 'sortino_ratio': float(sortino), 'maximum_drawdown': float(max_dd), 'var_95': float(var_95), 'number_of_observations': len(returns), 'latest_price': float(self.get_latest_price() or 0)}

def __init__(self, parameters: AssetParameters):
    self.parameters = parameters
    self.market_data: List[MarketData] = []
    self.cash_flows: List[CashFlow] = []
    self.performance_history: List[Performance] = []
    self.config = Config()
    self.math = FinancialMath()
    self._validate_parameters()

