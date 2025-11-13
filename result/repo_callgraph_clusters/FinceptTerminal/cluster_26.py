# Cluster 26

class PyPortfolioOptAnalyticsEngine:
    """
    Advanced PyPortfolioOpt Portfolio Analytics Engine

    Features:
    - Multiple optimization methods (EF, HRP, CLA, Black-Litterman)
    - Various risk models and expected return estimators
    - Advanced constraints and regularization
    - Efficient frontier generation
    - Discrete allocation
    - Performance analysis and plotting
    - Comprehensive backtesting
    """

    def __init__(self, config: PyPortfolioOptConfig=None):
        self.config = config or PyPortfolioOptConfig()
        self.prices = None
        self.returns = None
        self.expected_returns = None
        self.risk_model = None
        self.optimizer = None
        self.weights = None
        self.discrete_allocation = None
        self.performance_metrics = {}
        self.efficient_frontier_data = {}
        self.backtest_results = {}

    def load_data(self, prices: pd.DataFrame, start_date: str=None, end_date: str=None) -> None:
        """
        Load price data and calculate returns

        Parameters:
        -----------
        prices : pd.DataFrame
            Price data with datetime index and asset columns
        start_date, end_date : str
            Date range for filtering
        """
        if start_date or end_date:
            if start_date:
                prices = prices[prices.index >= start_date]
            if end_date:
                prices = prices[prices.index <= end_date]
        self.prices = prices
        self.returns = prices.pct_change().dropna()
        print(f'Data loaded: {len(self.prices)} periods, {len(self.prices.columns)} assets')

    def calculate_expected_returns(self, method: str=None) -> pd.Series:
        """
        Calculate expected returns using specified method

        Parameters:
        -----------
        method : str
            Method for calculating expected returns

        Returns:
        --------
        Expected returns series
        """
        method = method or self.config.expected_returns_method
        if method == 'mean_historical_return':
            self.expected_returns = expected_returns.mean_historical_return(self.prices, frequency=self.config.frequency)
        elif method == 'ema_historical_return':
            self.expected_returns = expected_returns.ema_historical_return(self.prices, span=self.config.span, frequency=self.config.frequency)
        elif method == 'capm_return':
            self.expected_returns = expected_returns.capm_return(self.prices, frequency=self.config.frequency)
        else:
            raise ValueError(f'Unknown expected returns method: {method}')
        return self.expected_returns

    def calculate_risk_model(self, method: str=None) -> pd.DataFrame:
        """
        Calculate risk model (covariance matrix) using specified method

        Parameters:
        -----------
        method : str
            Method for calculating risk model

        Returns:
        --------
        Covariance matrix
        """
        method = method or self.config.risk_model_method
        if method == 'sample_cov':
            self.risk_model = risk_models.sample_cov(self.prices, frequency=self.config.frequency)
        elif method == 'semicovariance':
            self.risk_model = risk_models.semicovariance(self.prices, frequency=self.config.frequency)
        elif method == 'exp_cov':
            self.risk_model = risk_models.exp_cov(self.prices, span=self.config.span, frequency=self.config.frequency)
        elif method == 'shrunk_covariance':
            self.risk_model = risk_models.CovarianceShrinkage(self.prices, frequency=self.config.frequency).shrunk_covariance(shrinkage_target=self.config.shrinkage_target)
        elif method == 'ledoit_wolf':
            self.risk_model = risk_models.CovarianceShrinkage(self.prices, frequency=self.config.frequency).ledoit_wolf()
        else:
            raise ValueError(f'Unknown risk model method: {method}')
        return self.risk_model

    def black_litterman_optimization(self, market_caps: pd.Series=None, views: Dict[str, float]=None, view_confidences: List[float]=None, tau: float=None) -> pd.Series:
        """
        Perform Black-Litterman optimization

        Parameters:
        -----------
        market_caps : pd.Series
            Market capitalizations
        views : Dict[str, float]
            Absolute views on expected returns
        view_confidences : List[float]
            Confidence in each view (0-1)
        tau : float
            Uncertainty scaling factor

        Returns:
        --------
        Optimal portfolio weights
        """
        market_caps = market_caps or self.config.market_caps
        views = views or self.config.views
        view_confidences = view_confidences or self.config.view_confidences
        tau = tau or self.config.tau
        if market_caps is None:
            market_caps = pd.Series(1, index=self.prices.columns)
        if self.risk_model is None:
            self.calculate_risk_model()
        bl = BlackLittermanModel(cov_matrix=self.risk_model, pi='market', market_caps=market_caps, tau=tau)
        if views:
            view_dict = {}
            for asset, view_return in views.items():
                if asset in self.prices.columns:
                    view_dict[asset] = view_return
            if view_dict:
                bl.add_views(view_dict, view_confidences)
        ret_bl = bl.bl_returns()
        cov_bl = bl.bl_cov()
        ef = EfficientFrontier(ret_bl, cov_bl, weight_bounds=self.config.weight_bounds)
        if self.config.objective == 'max_sharpe':
            self.weights = ef.max_sharpe(risk_free_rate=self.config.risk_free_rate)
        elif self.config.objective == 'min_volatility':
            self.weights = ef.min_volatility()
        else:
            raise ValueError(f'Objective {self.config.objective} not supported for Black-Litterman')
        self.optimizer = ef
        return pd.Series(self.weights)

def calculate_risk_model(self, method: str=None) -> pd.DataFrame:
    """
        Calculate risk model (covariance matrix) using specified method

        Parameters:
        -----------
        method : str
            Method for calculating risk model

        Returns:
        --------
        Covariance matrix
        """
    method = method or self.config.risk_model_method
    if method == 'sample_cov':
        self.risk_model = risk_models.sample_cov(self.prices, frequency=self.config.frequency)
    elif method == 'semicovariance':
        self.risk_model = risk_models.semicovariance(self.prices, frequency=self.config.frequency)
    elif method == 'exp_cov':
        self.risk_model = risk_models.exp_cov(self.prices, span=self.config.span, frequency=self.config.frequency)
    elif method == 'shrunk_covariance':
        self.risk_model = risk_models.CovarianceShrinkage(self.prices, frequency=self.config.frequency).shrunk_covariance(shrinkage_target=self.config.shrinkage_target)
    elif method == 'ledoit_wolf':
        self.risk_model = risk_models.CovarianceShrinkage(self.prices, frequency=self.config.frequency).ledoit_wolf()
    else:
        raise ValueError(f'Unknown risk model method: {method}')
    return self.risk_model

class MultiplesValuationSuite:
    """Comprehensive multiples valuation analysis"""

    def __init__(self):
        self.price_model = PriceMultiplesModel()
        self.ev_model = EnterpriseValueMultiplesModel()
        self.comparables_analyzer = ComparablesAnalyzer()
        self.regression_analyzer = CrossSectionalRegressionAnalyzer()

    def comprehensive_multiples_valuation(self, target_company: CompanyData, comparables: List[ComparableCompany], multiples_to_use: List[str]=None) -> Dict[str, ValuationResult]:
        """Perform comprehensive multiples valuation"""
        if multiples_to_use is None:
            multiples_to_use = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'ev_ebitda', 'ev_sales']
        results = {}
        target_comparable = self._convert_to_comparable(target_company)
        for multiple_type in multiples_to_use:
            try:
                stats = self.comparables_analyzer.calculate_multiple_statistics(comparables, multiple_type)
                representative_multiple = stats['median']
                if multiple_type in ['pe_ratio', 'pb_ratio', 'ps_ratio']:
                    intrinsic_value = self._calculate_price_multiple_value(target_company, multiple_type, representative_multiple)
                else:
                    intrinsic_value = self._calculate_ev_multiple_value(target_company, multiple_type, representative_multiple)
                assumptions = {'multiple_type': multiple_type, 'representative_multiple': representative_multiple, 'comparables_count': stats['count'], 'multiple_range': f'{stats['min']:.2f} - {stats['max']:.2f}', 'multiple_std_dev': stats['std_dev'], 'method': 'Median of Comparables'}
                calculation_details = {'multiple_statistics': stats, 'target_metric': self._get_target_metric(target_company, multiple_type), 'calculation': f'{representative_multiple:.2f} × {self._get_target_metric(target_company, multiple_type):.2f}'}
                recommendation = self.price_model.generate_recommendation(intrinsic_value, target_company.current_price)
                upside_downside = self.price_model.calculate_upside_downside(intrinsic_value, target_company.current_price)
                results[multiple_type] = ValuationResult(method=ValuationMethod.MULTIPLES_PE, intrinsic_value=intrinsic_value, current_price=target_company.current_price, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)
            except Exception as e:
                results[multiple_type] = f'Error: {str(e)}'
        return results

    def _convert_to_comparable(self, company_data: CompanyData) -> ComparableCompany:
        """Convert CompanyData to ComparableCompany format"""
        financial_data = company_data.financial_data
        return ComparableCompany(symbol=company_data.symbol, name=company_data.name, sector=company_data.sector, market_cap=company_data.market_cap, enterprise_value=self.ev_model.calculate_enterprise_value(company_data.market_cap, financial_data.get('total_debt', 0), financial_data.get('cash', 0)), revenue=financial_data.get('revenue', 0), ebitda=financial_data.get('ebitda', 0), net_income=financial_data.get('net_income', 0), book_value=financial_data.get('book_value', 0) * company_data.shares_outstanding, current_price=company_data.current_price, multiples={})

    def _calculate_price_multiple_value(self, company_data: CompanyData, multiple_type: str, multiple_value: float) -> float:
        """Calculate value using price multiples"""
        financial_data = company_data.financial_data
        shares = company_data.shares_outstanding
        if multiple_type == 'pe_ratio':
            eps = financial_data.get('earnings_per_share', 0)
            return self.price_model.value_using_pe_multiple(multiple_value, eps)
        elif multiple_type == 'pb_ratio':
            book_value_total = financial_data.get('book_value', 0) * shares
            bvps = book_value_total / shares if shares > 0 else 0
            return self.price_model.value_using_pb_multiple(multiple_value, bvps)
        elif multiple_type == 'ps_ratio':
            revenue = financial_data.get('revenue', 0)
            sps = revenue / shares if shares > 0 else 0
            return self.price_model.value_using_ps_multiple(multiple_value, sps)
        else:
            raise ValidationError(f'Unknown price multiple type: {multiple_type}')

    def _calculate_ev_multiple_value(self, company_data: CompanyData, multiple_type: str, multiple_value: float) -> float:
        """Calculate value using EV multiples"""
        financial_data = company_data.financial_data
        if multiple_type == 'ev_ebitda':
            target_metric = financial_data.get('ebitda', 0)
        elif multiple_type == 'ev_sales':
            target_metric = financial_data.get('revenue', 0)
        else:
            raise ValidationError(f'Unknown EV multiple type: {multiple_type}')
        return self.ev_model.value_using_ev_multiple(multiple_value, target_metric, financial_data.get('total_debt', 0), financial_data.get('cash', 0), company_data.shares_outstanding)

    def _get_target_metric(self, company_data: CompanyData, multiple_type: str) -> float:
        """Get the target metric value for multiple calculation"""
        financial_data = company_data.financial_data
        if multiple_type == 'pe_ratio':
            return financial_data.get('earnings_per_share', 0)
        elif multiple_type == 'pb_ratio':
            return financial_data.get('book_value', 0)
        elif multiple_type == 'ps_ratio':
            return financial_data.get('revenue', 0) / company_data.shares_outstanding
        elif multiple_type == 'ev_ebitda':
            return financial_data.get('ebitda', 0)
        elif multiple_type == 'ev_sales':
            return financial_data.get('revenue', 0)
        else:
            return 0

def comprehensive_multiples_valuation(self, target_company: CompanyData, comparables: List[ComparableCompany], multiples_to_use: List[str]=None) -> Dict[str, ValuationResult]:
    """Perform comprehensive multiples valuation"""
    if multiples_to_use is None:
        multiples_to_use = ['pe_ratio', 'pb_ratio', 'ps_ratio', 'ev_ebitda', 'ev_sales']
    results = {}
    target_comparable = self._convert_to_comparable(target_company)
    for multiple_type in multiples_to_use:
        try:
            stats = self.comparables_analyzer.calculate_multiple_statistics(comparables, multiple_type)
            representative_multiple = stats['median']
            if multiple_type in ['pe_ratio', 'pb_ratio', 'ps_ratio']:
                intrinsic_value = self._calculate_price_multiple_value(target_company, multiple_type, representative_multiple)
            else:
                intrinsic_value = self._calculate_ev_multiple_value(target_company, multiple_type, representative_multiple)
            assumptions = {'multiple_type': multiple_type, 'representative_multiple': representative_multiple, 'comparables_count': stats['count'], 'multiple_range': f'{stats['min']:.2f} - {stats['max']:.2f}', 'multiple_std_dev': stats['std_dev'], 'method': 'Median of Comparables'}
            calculation_details = {'multiple_statistics': stats, 'target_metric': self._get_target_metric(target_company, multiple_type), 'calculation': f'{representative_multiple:.2f} × {self._get_target_metric(target_company, multiple_type):.2f}'}
            recommendation = self.price_model.generate_recommendation(intrinsic_value, target_company.current_price)
            upside_downside = self.price_model.calculate_upside_downside(intrinsic_value, target_company.current_price)
            results[multiple_type] = ValuationResult(method=ValuationMethod.MULTIPLES_PE, intrinsic_value=intrinsic_value, current_price=target_company.current_price, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)
        except Exception as e:
            results[multiple_type] = f'Error: {str(e)}'
    return results

def _convert_to_comparable(self, company_data: CompanyData) -> ComparableCompany:
    """Convert CompanyData to ComparableCompany format"""
    financial_data = company_data.financial_data
    return ComparableCompany(symbol=company_data.symbol, name=company_data.name, sector=company_data.sector, market_cap=company_data.market_cap, enterprise_value=self.ev_model.calculate_enterprise_value(company_data.market_cap, financial_data.get('total_debt', 0), financial_data.get('cash', 0)), revenue=financial_data.get('revenue', 0), ebitda=financial_data.get('ebitda', 0), net_income=financial_data.get('net_income', 0), book_value=financial_data.get('book_value', 0) * company_data.shares_outstanding, current_price=company_data.current_price, multiples={})

class FCFFModel(BaseValuationModel):
    """Free Cash Flow to Firm Model"""

    def __init__(self):
        super().__init__('FCFF Model', 'Free Cash Flow to Firm valuation')
        self.valuation_method = ValuationMethod.DCF_FCFF

    def validate_inputs(self, wacc: float, fcff_projections: List[float], terminal_growth: float=None) -> bool:
        """Validate FCFF model inputs"""
        ModelValidator.validate_percentage(wacc, 'WACC')
        if not fcff_projections or len(fcff_projections) == 0:
            raise ValidationError('FCFF projections cannot be empty')
        if terminal_growth is not None:
            ModelValidator.validate_percentage(terminal_growth, 'Terminal growth rate', allow_negative=True)
            ModelValidator.validate_growth_vs_required_return(terminal_growth, wacc)
        return True

    def calculate_fcff_from_components(self, ebit: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> float:
        """Calculate FCFF from financial statement components"""
        return CalculationEngine.free_cash_flow_to_firm(ebit, tax_rate, depreciation, capex, working_capital_change)

    def calculate_fcff_from_ebitda(self, ebitda: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> float:
        """Calculate FCFF starting from EBITDA"""
        ebit = ebitda - depreciation
        return self.calculate_fcff_from_components(ebit, tax_rate, depreciation, capex, working_capital_change)

    def calculate_fcff_from_net_income(self, net_income: float, interest_expense: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float) -> float:
        """Calculate FCFF starting from net income"""
        after_tax_interest = interest_expense * (1 - tax_rate)
        unlevered_net_income = net_income + after_tax_interest
        return unlevered_net_income + depreciation - capex - working_capital_change

    def calculate_fcff_from_cfo(self, cfo: float, interest_expense: float, tax_rate: float, capex: float) -> float:
        """Calculate FCFF from Cash Flow from Operations"""
        after_tax_interest = interest_expense * (1 - tax_rate)
        return cfo + after_tax_interest - capex

    def calculate_terminal_value(self, final_fcff: float, terminal_growth: float, wacc: float) -> float:
        """Calculate terminal value using Gordon Growth"""
        if terminal_growth >= wacc:
            raise ValidationError('Terminal growth rate must be less than WACC')
        terminal_fcff = final_fcff * (1 + terminal_growth)
        return terminal_fcff / (wacc - terminal_growth)

    def calculate_enterprise_value(self, fcff_projections: List[float], wacc: float, terminal_growth: float=None, terminal_value: float=None) -> Dict[str, float]:
        """Calculate enterprise value from FCFF projections"""
        pv_fcff = 0
        pv_details = []
        for year, fcff in enumerate(fcff_projections, 1):
            pv = CalculationEngine.present_value(fcff, wacc, year)
            pv_fcff += pv
            pv_details.append({'year': year, 'fcff': fcff, 'pv': pv})
        if terminal_value is None:
            if terminal_growth is None:
                raise ValidationError('Either terminal_growth or terminal_value must be provided')
            terminal_value = self.calculate_terminal_value(fcff_projections[-1], terminal_growth, wacc)
        pv_terminal = CalculationEngine.present_value(terminal_value, wacc, len(fcff_projections))
        enterprise_value = pv_fcff + pv_terminal
        return {'pv_fcff': pv_fcff, 'terminal_value': terminal_value, 'pv_terminal': pv_terminal, 'enterprise_value': enterprise_value, 'pv_details': pv_details}

    def calculate_equity_value(self, enterprise_value: float, cash: float, total_debt: float, preferred_stock: float=0) -> float:
        """Calculate equity value from enterprise value"""
        return enterprise_value + cash - total_debt - preferred_stock

    def calculate(self, fcff_projections: List[float], wacc: float, shares_outstanding: float, terminal_growth: float=None, terminal_value: float=None, cash: float=0, total_debt: float=0, preferred_stock: float=0, current_price: float=None) -> ValuationResult:
        """Calculate valuation using FCFF model"""
        self.validate_inputs(wacc, fcff_projections, terminal_growth)
        ev_components = self.calculate_enterprise_value(fcff_projections, wacc, terminal_growth, terminal_value)
        equity_value = self.calculate_equity_value(ev_components['enterprise_value'], cash, total_debt, preferred_stock)
        intrinsic_value = equity_value / shares_outstanding if shares_outstanding > 0 else 0
        assumptions = {'wacc': wacc, 'terminal_growth_rate': terminal_growth, 'projection_years': len(fcff_projections), 'terminal_value_multiple': ev_components['pv_terminal'] / ev_components['enterprise_value'] * 100, 'cash': cash, 'total_debt': total_debt, 'preferred_stock': preferred_stock, 'shares_outstanding': shares_outstanding, 'model_type': 'FCFF DCF Model'}
        calculation_details = {'fcff_projections': fcff_projections, 'pv_fcff': ev_components['pv_fcff'], 'terminal_value': ev_components['terminal_value'], 'pv_terminal': ev_components['pv_terminal'], 'enterprise_value': ev_components['enterprise_value'], 'equity_value': equity_value, 'intrinsic_value_per_share': intrinsic_value, 'pv_details': ev_components['pv_details']}
        recommendation = 'HOLD'
        upside_downside = 0
        if current_price:
            recommendation = self.generate_recommendation(intrinsic_value, current_price)
            upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
        return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

def calculate(self, fcff_projections: List[float], wacc: float, shares_outstanding: float, terminal_growth: float=None, terminal_value: float=None, cash: float=0, total_debt: float=0, preferred_stock: float=0, current_price: float=None) -> ValuationResult:
    """Calculate valuation using FCFF model"""
    self.validate_inputs(wacc, fcff_projections, terminal_growth)
    ev_components = self.calculate_enterprise_value(fcff_projections, wacc, terminal_growth, terminal_value)
    equity_value = self.calculate_equity_value(ev_components['enterprise_value'], cash, total_debt, preferred_stock)
    intrinsic_value = equity_value / shares_outstanding if shares_outstanding > 0 else 0
    assumptions = {'wacc': wacc, 'terminal_growth_rate': terminal_growth, 'projection_years': len(fcff_projections), 'terminal_value_multiple': ev_components['pv_terminal'] / ev_components['enterprise_value'] * 100, 'cash': cash, 'total_debt': total_debt, 'preferred_stock': preferred_stock, 'shares_outstanding': shares_outstanding, 'model_type': 'FCFF DCF Model'}
    calculation_details = {'fcff_projections': fcff_projections, 'pv_fcff': ev_components['pv_fcff'], 'terminal_value': ev_components['terminal_value'], 'pv_terminal': ev_components['pv_terminal'], 'enterprise_value': ev_components['enterprise_value'], 'equity_value': equity_value, 'intrinsic_value_per_share': intrinsic_value, 'pv_details': ev_components['pv_details']}
    recommendation = 'HOLD'
    upside_downside = 0
    if current_price:
        recommendation = self.generate_recommendation(intrinsic_value, current_price)
        upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
    return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

class FCFEModel(BaseValuationModel):
    """Free Cash Flow to Equity Model"""

    def __init__(self):
        super().__init__('FCFE Model', 'Free Cash Flow to Equity valuation')
        self.valuation_method = ValuationMethod.DCF_FCFE

    def validate_inputs(self, required_return: float, fcfe_projections: List[float], terminal_growth: float=None) -> bool:
        """Validate FCFE model inputs"""
        ModelValidator.validate_percentage(required_return, 'Required return on equity')
        if not fcfe_projections or len(fcfe_projections) == 0:
            raise ValidationError('FCFE projections cannot be empty')
        if terminal_growth is not None:
            ModelValidator.validate_percentage(terminal_growth, 'Terminal growth rate', allow_negative=True)
            ModelValidator.validate_growth_vs_required_return(terminal_growth, required_return)
        return True

    def calculate_fcfe_from_components(self, net_income: float, depreciation: float, capex: float, working_capital_change: float, net_borrowing: float) -> float:
        """Calculate FCFE from financial statement components"""
        return CalculationEngine.free_cash_flow_to_equity(net_income, depreciation, capex, working_capital_change, net_borrowing)

    def calculate_fcfe_from_fcff(self, fcff: float, interest_expense: float, tax_rate: float, net_borrowing: float) -> float:
        """Calculate FCFE from FCFF"""
        after_tax_interest = interest_expense * (1 - tax_rate)
        return fcff - after_tax_interest + net_borrowing

    def calculate_fcfe_from_ebit(self, ebit: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float, interest_expense: float, net_borrowing: float) -> float:
        """Calculate FCFE starting from EBIT"""
        ebt = ebit - interest_expense
        net_income = ebt * (1 - tax_rate)
        return self.calculate_fcfe_from_components(net_income, depreciation, capex, working_capital_change, net_borrowing)

    def calculate_fcfe_from_ebitda(self, ebitda: float, tax_rate: float, depreciation: float, capex: float, working_capital_change: float, interest_expense: float, net_borrowing: float) -> float:
        """Calculate FCFE starting from EBITDA"""
        ebit = ebitda - depreciation
        return self.calculate_fcfe_from_ebit(ebit, tax_rate, depreciation, capex, working_capital_change, interest_expense, net_borrowing)

    def calculate_fcfe_from_cfo(self, cfo: float, capex: float, net_borrowing: float) -> float:
        """Calculate FCFE from Cash Flow from Operations"""
        return cfo - capex + net_borrowing

    def calculate_terminal_value(self, final_fcfe: float, terminal_growth: float, required_return: float) -> float:
        """Calculate terminal value using Gordon Growth"""
        if terminal_growth >= required_return:
            raise ValidationError('Terminal growth rate must be less than required return')
        terminal_fcfe = final_fcfe * (1 + terminal_growth)
        return terminal_fcfe / (required_return - terminal_growth)

    def calculate_equity_value(self, fcfe_projections: List[float], required_return: float, terminal_growth: float=None, terminal_value: float=None) -> Dict[str, float]:
        """Calculate equity value from FCFE projections"""
        pv_fcfe = 0
        pv_details = []
        for year, fcfe in enumerate(fcfe_projections, 1):
            pv = CalculationEngine.present_value(fcfe, required_return, year)
            pv_fcfe += pv
            pv_details.append({'year': year, 'fcfe': fcfe, 'pv': pv})
        if terminal_value is None:
            if terminal_growth is None:
                raise ValidationError('Either terminal_growth or terminal_value must be provided')
            terminal_value = self.calculate_terminal_value(fcfe_projections[-1], terminal_growth, required_return)
        pv_terminal = CalculationEngine.present_value(terminal_value, required_return, len(fcfe_projections))
        equity_value = pv_fcfe + pv_terminal
        return {'pv_fcfe': pv_fcfe, 'terminal_value': terminal_value, 'pv_terminal': pv_terminal, 'equity_value': equity_value, 'pv_details': pv_details}

    def calculate(self, fcfe_projections: List[float], required_return: float, shares_outstanding: float, terminal_growth: float=None, terminal_value: float=None, current_price: float=None) -> ValuationResult:
        """Calculate valuation using FCFE model"""
        self.validate_inputs(required_return, fcfe_projections, terminal_growth)
        equity_components = self.calculate_equity_value(fcfe_projections, required_return, terminal_growth, terminal_value)
        intrinsic_value = equity_components['equity_value'] / shares_outstanding if shares_outstanding > 0 else 0
        assumptions = {'required_return': required_return, 'terminal_growth_rate': terminal_growth, 'projection_years': len(fcfe_projections), 'terminal_value_multiple': equity_components['pv_terminal'] / equity_components['equity_value'] * 100, 'shares_outstanding': shares_outstanding, 'model_type': 'FCFE DCF Model'}
        calculation_details = {'fcfe_projections': fcfe_projections, 'pv_fcfe': equity_components['pv_fcfe'], 'terminal_value': equity_components['terminal_value'], 'pv_terminal': equity_components['pv_terminal'], 'equity_value': equity_components['equity_value'], 'intrinsic_value_per_share': intrinsic_value, 'pv_details': equity_components['pv_details']}
        recommendation = 'HOLD'
        upside_downside = 0
        if current_price:
            recommendation = self.generate_recommendation(intrinsic_value, current_price)
            upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
        return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

def calculate(self, fcfe_projections: List[float], required_return: float, shares_outstanding: float, terminal_growth: float=None, terminal_value: float=None, current_price: float=None) -> ValuationResult:
    """Calculate valuation using FCFE model"""
    self.validate_inputs(required_return, fcfe_projections, terminal_growth)
    equity_components = self.calculate_equity_value(fcfe_projections, required_return, terminal_growth, terminal_value)
    intrinsic_value = equity_components['equity_value'] / shares_outstanding if shares_outstanding > 0 else 0
    assumptions = {'required_return': required_return, 'terminal_growth_rate': terminal_growth, 'projection_years': len(fcfe_projections), 'terminal_value_multiple': equity_components['pv_terminal'] / equity_components['equity_value'] * 100, 'shares_outstanding': shares_outstanding, 'model_type': 'FCFE DCF Model'}
    calculation_details = {'fcfe_projections': fcfe_projections, 'pv_fcfe': equity_components['pv_fcfe'], 'terminal_value': equity_components['terminal_value'], 'pv_terminal': equity_components['pv_terminal'], 'equity_value': equity_components['equity_value'], 'intrinsic_value_per_share': intrinsic_value, 'pv_details': equity_components['pv_details']}
    recommendation = 'HOLD'
    upside_downside = 0
    if current_price:
        recommendation = self.generate_recommendation(intrinsic_value, current_price)
        upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
    return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

class DCFSensitivityAnalyzer:
    """Sensitivity analysis for DCF models"""

    @staticmethod
    def wacc_sensitivity_analysis(base_fcff_projections: List[float], base_wacc: float, terminal_growth: float, shares_outstanding: float, wacc_range: Tuple[float, float]=(-0.02, 0.02), steps: int=5) -> pd.DataFrame:
        """Perform sensitivity analysis on WACC"""
        fcff_model = FCFFModel()
        results = []
        wacc_min, wacc_max = wacc_range
        wacc_values = np.linspace(base_wacc + wacc_min, base_wacc + wacc_max, steps)
        for wacc in wacc_values:
            try:
                ev_components = fcff_model.calculate_enterprise_value(base_fcff_projections, wacc, terminal_growth)
                equity_value = fcff_model.calculate_equity_value(ev_components['enterprise_value'], 0, 0, 0)
                per_share_value = equity_value / shares_outstanding
                results.append({'wacc': wacc, 'enterprise_value': ev_components['enterprise_value'], 'equity_value': equity_value, 'per_share_value': per_share_value})
            except:
                continue
        return pd.DataFrame(results)

    @staticmethod
    def terminal_growth_sensitivity_analysis(base_fcff_projections: List[float], wacc: float, base_terminal_growth: float, shares_outstanding: float, growth_range: Tuple[float, float]=(-0.01, 0.01), steps: int=5) -> pd.DataFrame:
        """Perform sensitivity analysis on terminal growth rate"""
        fcff_model = FCFFModel()
        results = []
        growth_min, growth_max = growth_range
        growth_values = np.linspace(base_terminal_growth + growth_min, base_terminal_growth + growth_max, steps)
        for growth in growth_values:
            if growth >= wacc:
                continue
            try:
                ev_components = fcff_model.calculate_enterprise_value(base_fcff_projections, wacc, growth)
                equity_value = fcff_model.calculate_equity_value(ev_components['enterprise_value'], 0, 0, 0)
                per_share_value = equity_value / shares_outstanding
                results.append({'terminal_growth': growth, 'enterprise_value': ev_components['enterprise_value'], 'equity_value': equity_value, 'per_share_value': per_share_value})
            except:
                continue
        return pd.DataFrame(results)

    @staticmethod
    def two_way_sensitivity_analysis(base_fcff_projections: List[float], base_wacc: float, base_terminal_growth: float, shares_outstanding: float, wacc_range: Tuple[float, float]=(-0.015, 0.015), growth_range: Tuple[float, float]=(-0.01, 0.01), steps: int=5) -> pd.DataFrame:
        """Perform two-way sensitivity analysis on WACC and terminal growth"""
        fcff_model = FCFFModel()
        results = []
        wacc_min, wacc_max = wacc_range
        growth_min, growth_max = growth_range
        wacc_values = np.linspace(base_wacc + wacc_min, base_wacc + wacc_max, steps)
        growth_values = np.linspace(base_terminal_growth + growth_min, base_terminal_growth + growth_max, steps)
        for wacc in wacc_values:
            for growth in growth_values:
                if growth >= wacc:
                    continue
                try:
                    ev_components = fcff_model.calculate_enterprise_value(base_fcff_projections, wacc, growth)
                    equity_value = fcff_model.calculate_equity_value(ev_components['enterprise_value'], 0, 0, 0)
                    per_share_value = equity_value / shares_outstanding
                    results.append({'wacc': wacc, 'terminal_growth': growth, 'per_share_value': per_share_value})
                except:
                    continue
        df = pd.DataFrame(results)
        return df.pivot_table(values='per_share_value', index='wacc', columns='terminal_growth')

@staticmethod
def wacc_sensitivity_analysis(base_fcff_projections: List[float], base_wacc: float, terminal_growth: float, shares_outstanding: float, wacc_range: Tuple[float, float]=(-0.02, 0.02), steps: int=5) -> pd.DataFrame:
    """Perform sensitivity analysis on WACC"""
    fcff_model = FCFFModel()
    results = []
    wacc_min, wacc_max = wacc_range
    wacc_values = np.linspace(base_wacc + wacc_min, base_wacc + wacc_max, steps)
    for wacc in wacc_values:
        try:
            ev_components = fcff_model.calculate_enterprise_value(base_fcff_projections, wacc, terminal_growth)
            equity_value = fcff_model.calculate_equity_value(ev_components['enterprise_value'], 0, 0, 0)
            per_share_value = equity_value / shares_outstanding
            results.append({'wacc': wacc, 'enterprise_value': ev_components['enterprise_value'], 'equity_value': equity_value, 'per_share_value': per_share_value})
        except:
            continue
    return pd.DataFrame(results)

@staticmethod
def terminal_growth_sensitivity_analysis(base_fcff_projections: List[float], wacc: float, base_terminal_growth: float, shares_outstanding: float, growth_range: Tuple[float, float]=(-0.01, 0.01), steps: int=5) -> pd.DataFrame:
    """Perform sensitivity analysis on terminal growth rate"""
    fcff_model = FCFFModel()
    results = []
    growth_min, growth_max = growth_range
    growth_values = np.linspace(base_terminal_growth + growth_min, base_terminal_growth + growth_max, steps)
    for growth in growth_values:
        if growth >= wacc:
            continue
        try:
            ev_components = fcff_model.calculate_enterprise_value(base_fcff_projections, wacc, growth)
            equity_value = fcff_model.calculate_equity_value(ev_components['enterprise_value'], 0, 0, 0)
            per_share_value = equity_value / shares_outstanding
            results.append({'terminal_growth': growth, 'enterprise_value': ev_components['enterprise_value'], 'equity_value': equity_value, 'per_share_value': per_share_value})
        except:
            continue
    return pd.DataFrame(results)

@staticmethod
def two_way_sensitivity_analysis(base_fcff_projections: List[float], base_wacc: float, base_terminal_growth: float, shares_outstanding: float, wacc_range: Tuple[float, float]=(-0.015, 0.015), growth_range: Tuple[float, float]=(-0.01, 0.01), steps: int=5) -> pd.DataFrame:
    """Perform two-way sensitivity analysis on WACC and terminal growth"""
    fcff_model = FCFFModel()
    results = []
    wacc_min, wacc_max = wacc_range
    growth_min, growth_max = growth_range
    wacc_values = np.linspace(base_wacc + wacc_min, base_wacc + wacc_max, steps)
    growth_values = np.linspace(base_terminal_growth + growth_min, base_terminal_growth + growth_max, steps)
    for wacc in wacc_values:
        for growth in growth_values:
            if growth >= wacc:
                continue
            try:
                ev_components = fcff_model.calculate_enterprise_value(base_fcff_projections, wacc, growth)
                equity_value = fcff_model.calculate_equity_value(ev_components['enterprise_value'], 0, 0, 0)
                per_share_value = equity_value / shares_outstanding
                results.append({'wacc': wacc, 'terminal_growth': growth, 'per_share_value': per_share_value})
            except:
                continue
    df = pd.DataFrame(results)
    return df.pivot_table(values='per_share_value', index='wacc', columns='terminal_growth')

class DCFAnalyzer:
    """Comprehensive DCF analysis tool"""

    def __init__(self):
        self.fcff_model = FCFFModel()
        self.fcfe_model = FCFEModel()
        self.sensitivity_analyzer = DCFSensitivityAnalyzer()

    def compare_dcf_models(self, company_data: CompanyData, market_data: MarketData, projections: Dict[str, List[float]]) -> Dict[str, ValuationResult]:
        """Compare FCFF and FCFE valuations"""
        results = {}
        if 'fcff' in projections:
            try:
                wacc = market_data.required_return * 0.8
                results['fcff'] = self.fcff_model.calculate(projections['fcff'], wacc, company_data.shares_outstanding, market_data.growth_rate, None, company_data.financial_data.get('cash', 0), company_data.financial_data.get('total_debt', 0), 0, company_data.current_price)
            except Exception as e:
                results['fcff'] = f'Error: {str(e)}'
        if 'fcfe' in projections:
            try:
                results['fcfe'] = self.fcfe_model.calculate(projections['fcfe'], market_data.required_return, company_data.shares_outstanding, market_data.growth_rate, None, company_data.current_price)
            except Exception as e:
                results['fcfe'] = f'Error: {str(e)}'
        return results

    def calculate_implicit_forecasts(self, current_price: float, shares_outstanding: float, wacc: float, terminal_growth: float, projection_years: int=5) -> Dict[str, Any]:
        """Calculate implicit FCFF forecasts based on current market price"""
        market_equity_value = current_price * shares_outstanding
        terminal_value_percentage = 0.8
        pv_terminal = market_equity_value * terminal_value_percentage
        pv_growth_stage = market_equity_value * (1 - terminal_value_percentage)
        implied_terminal_fcff = pv_terminal * (wacc - terminal_growth) / (1 + wacc) ** projection_years
        growth_factor = (1 + terminal_growth) ** projection_years
        implied_initial_fcff = implied_terminal_fcff / growth_factor
        return {'market_equity_value': market_equity_value, 'implied_terminal_fcff': implied_terminal_fcff, 'implied_initial_fcff': implied_initial_fcff, 'implied_growth_rate': terminal_growth, 'assumptions': {'terminal_value_percentage': terminal_value_percentage, 'projection_years': projection_years, 'wacc': wacc, 'terminal_growth': terminal_growth}}

    def forecast_cash_flows(self, historical_financials: pd.DataFrame, growth_assumptions: Dict[str, float], projection_years: int=5) -> Dict[str, List[float]]:
        """Forecast future cash flows based on historical data and assumptions"""
        base_year = historical_financials.iloc[-1]
        revenue_growth = growth_assumptions.get('revenue_growth', 0.05)
        ebitda_margin = growth_assumptions.get('ebitda_margin', base_year.get('ebitda', 0) / base_year.get('revenue', 1))
        tax_rate = growth_assumptions.get('tax_rate', 0.25)
        capex_percentage = growth_assumptions.get('capex_percentage', 0.03)
        depreciation_percentage = growth_assumptions.get('depreciation_percentage', 0.025)
        projections = {'revenue': [], 'ebitda': [], 'fcff': [], 'fcfe': []}
        current_revenue = base_year.get('revenue', 0)
        for year in range(1, projection_years + 1):
            current_revenue *= 1 + revenue_growth
            projections['revenue'].append(current_revenue)
            ebitda = current_revenue * ebitda_margin
            projections['ebitda'].append(ebitda)
            depreciation = current_revenue * depreciation_percentage
            ebit = ebitda - depreciation
            capex = current_revenue * capex_percentage
            fcff = self.fcff_model.calculate_fcff_from_components(ebit, tax_rate, depreciation, capex, 0)
            projections['fcff'].append(fcff)
            interest_expense = base_year.get('interest_expense', 0)
            net_borrowing = capex * 0.3
            fcfe = self.fcfe_model.calculate_fcfe_from_fcff(fcff, interest_expense, tax_rate, net_borrowing)
            projections['fcfe'].append(fcfe)
        return projections

def __init__(self):
    self.fcff_model = FCFFModel()
    self.fcfe_model = FCFEModel()
    self.sensitivity_analyzer = DCFSensitivityAnalyzer()

def compare_dcf_models(self, company_data: CompanyData, market_data: MarketData, projections: Dict[str, List[float]]) -> Dict[str, ValuationResult]:
    """Compare FCFF and FCFE valuations"""
    results = {}
    if 'fcff' in projections:
        try:
            wacc = market_data.required_return * 0.8
            results['fcff'] = self.fcff_model.calculate(projections['fcff'], wacc, company_data.shares_outstanding, market_data.growth_rate, None, company_data.financial_data.get('cash', 0), company_data.financial_data.get('total_debt', 0), 0, company_data.current_price)
        except Exception as e:
            results['fcff'] = f'Error: {str(e)}'
    if 'fcfe' in projections:
        try:
            results['fcfe'] = self.fcfe_model.calculate(projections['fcfe'], market_data.required_return, company_data.shares_outstanding, market_data.growth_rate, None, company_data.current_price)
        except Exception as e:
            results['fcfe'] = f'Error: {str(e)}'
    return results

def fcff_valuation(fcff_projections: List[float], wacc: float, shares_outstanding: float, terminal_growth: float, cash: float=0, debt: float=0, current_price: float=None) -> ValuationResult:
    """Quick FCFF valuation"""
    model = FCFFModel()
    return model.calculate(fcff_projections, wacc, shares_outstanding, terminal_growth, None, cash, debt, 0, current_price)

def fcfe_valuation(fcfe_projections: List[float], required_return: float, shares_outstanding: float, terminal_growth: float, current_price: float=None) -> ValuationResult:
    """Quick FCFE valuation"""
    model = FCFEModel()
    return model.calculate(fcfe_projections, required_return, shares_outstanding, terminal_growth, None, current_price)

class ResidualIncomeModel(BaseValuationModel):
    """Single-stage and Multi-stage Residual Income Model"""

    def __init__(self):
        super().__init__('Residual Income Model', 'Residual income valuation')
        self.valuation_method = ValuationMethod.RESIDUAL_INCOME

    def calculate_residual_income(self, net_income: float, beginning_book_value: float, required_return: float) -> float:
        """Calculate residual income for a single period"""
        return CalculationEngine.residual_income(net_income, beginning_book_value, required_return)

    def calculate_continuing_residual_income(self, final_ri: float, required_return: float, growth_rate: float) -> float:
        """Calculate continuing residual income value"""
        if growth_rate >= required_return:
            raise ValidationError('Growth rate must be less than required return for continuing RI')
        next_ri = final_ri * (1 + growth_rate)
        return next_ri / (required_return - growth_rate)

    def calculate_single_stage_ri_value(self, current_book_value: float, roe: float, required_return: float, growth_rate: float=0) -> float:
        """Calculate single-stage constant growth RI value"""
        if growth_rate >= required_return:
            raise ValidationError('Growth rate must be less than required return')
        next_net_income = current_book_value * roe * (1 + growth_rate)
        next_book_value = current_book_value * (1 + growth_rate)
        next_ri = self.calculate_residual_income(next_net_income, current_book_value, required_return)
        if growth_rate == 0:
            pv_future_ris = next_ri / required_return
        else:
            pv_future_ris = next_ri / (required_return - growth_rate)
        return current_book_value + pv_future_ris

    def calculate_multistage_ri_value(self, current_book_value: float, projected_ris: List[float], required_return: float, terminal_ri: float=None, terminal_growth: float=None) -> Dict[str, float]:
        """Calculate multi-stage RI value"""
        pv_projected_ris = 0
        pv_details = []
        for year, ri in enumerate(projected_ris, 1):
            pv_ri = CalculationEngine.present_value(ri, required_return, year)
            pv_projected_ris += pv_ri
            pv_details.append({'year': year, 'ri': ri, 'pv_ri': pv_ri})
        if terminal_ri is not None:
            if terminal_growth is None:
                terminal_growth = 0
            continuing_ri_value = self.calculate_continuing_residual_income(terminal_ri, required_return, terminal_growth)
            pv_terminal = CalculationEngine.present_value(continuing_ri_value, required_return, len(projected_ris))
        else:
            pv_terminal = 0
        total_value = current_book_value + pv_projected_ris + pv_terminal
        return {'current_book_value': current_book_value, 'pv_projected_ris': pv_projected_ris, 'pv_terminal': pv_terminal, 'total_value': total_value, 'pv_details': pv_details}

    def calculate_intrinsic_value(self, company_data: CompanyData, market_data: MarketData) -> float:
        """Calculate intrinsic value using RI model"""
        financial_data = company_data.financial_data
        book_value_total = financial_data.get('book_value', 0) * company_data.shares_outstanding
        roe = financial_data.get('roe', 0)
        required_return = market_data.required_return
        growth_rate = market_data.growth_rate
        total_value = self.calculate_single_stage_ri_value(book_value_total, roe, required_return, growth_rate)
        return total_value / company_data.shares_outstanding if company_data.shares_outstanding > 0 else 0

    def calculate(self, current_book_value: float, projected_ris: List[float], required_return: float, shares_outstanding: float, terminal_ri: float=None, terminal_growth: float=None, current_price: float=None) -> ValuationResult:
        """Calculate valuation using Residual Income model"""
        ModelValidator.validate_positive_number(current_book_value, 'Current book value')
        ModelValidator.validate_percentage(required_return, 'Required return')
        if terminal_growth is not None:
            ModelValidator.validate_growth_vs_required_return(terminal_growth, required_return)
        ri_components = self.calculate_multistage_ri_value(current_book_value, projected_ris, required_return, terminal_ri, terminal_growth)
        intrinsic_value = ri_components['total_value'] / shares_outstanding if shares_outstanding > 0 else 0
        assumptions = {'current_book_value': current_book_value, 'required_return': required_return, 'terminal_growth_rate': terminal_growth, 'projection_periods': len(projected_ris), 'book_value_percentage': current_book_value / ri_components['total_value'] * 100, 'terminal_value_percentage': ri_components['pv_terminal'] / ri_components['total_value'] * 100, 'model_type': 'Multi-stage Residual Income Model'}
        calculation_details = {'projected_ris': projected_ris, 'pv_projected_ris': ri_components['pv_projected_ris'], 'pv_terminal': ri_components['pv_terminal'], 'total_value': ri_components['total_value'], 'intrinsic_value_per_share': intrinsic_value, 'pv_details': ri_components['pv_details']}
        recommendation = 'HOLD'
        upside_downside = 0
        if current_price:
            recommendation = self.generate_recommendation(intrinsic_value, current_price)
            upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
        return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

def calculate(self, current_book_value: float, projected_ris: List[float], required_return: float, shares_outstanding: float, terminal_ri: float=None, terminal_growth: float=None, current_price: float=None) -> ValuationResult:
    """Calculate valuation using Residual Income model"""
    ModelValidator.validate_positive_number(current_book_value, 'Current book value')
    ModelValidator.validate_percentage(required_return, 'Required return')
    if terminal_growth is not None:
        ModelValidator.validate_growth_vs_required_return(terminal_growth, required_return)
    ri_components = self.calculate_multistage_ri_value(current_book_value, projected_ris, required_return, terminal_ri, terminal_growth)
    intrinsic_value = ri_components['total_value'] / shares_outstanding if shares_outstanding > 0 else 0
    assumptions = {'current_book_value': current_book_value, 'required_return': required_return, 'terminal_growth_rate': terminal_growth, 'projection_periods': len(projected_ris), 'book_value_percentage': current_book_value / ri_components['total_value'] * 100, 'terminal_value_percentage': ri_components['pv_terminal'] / ri_components['total_value'] * 100, 'model_type': 'Multi-stage Residual Income Model'}
    calculation_details = {'projected_ris': projected_ris, 'pv_projected_ris': ri_components['pv_projected_ris'], 'pv_terminal': ri_components['pv_terminal'], 'total_value': ri_components['total_value'], 'intrinsic_value_per_share': intrinsic_value, 'pv_details': ri_components['pv_details']}
    recommendation = 'HOLD'
    upside_downside = 0
    if current_price:
        recommendation = self.generate_recommendation(intrinsic_value, current_price)
        upside_downside = self.calculate_upside_downside(intrinsic_value, current_price)
    return ValuationResult(method=self.valuation_method, intrinsic_value=intrinsic_value, current_price=current_price or 0, recommendation=recommendation, upside_downside=upside_downside, confidence_level='MEDIUM', assumptions=assumptions, calculation_details=calculation_details)

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

