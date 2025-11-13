# Cluster 10

class FederalReserveWrapper:
    """Modular Federal Reserve API wrapper with fault tolerance"""

    def __init__(self):
        self.base_url = FED_BASE_URL
        self.ny_fed_url = NY_FED_API_URL
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Fincept-Terminal/1.0'})

    def _make_request(self, url: str, params: Optional[Dict]=None, timeout: int=30) -> Dict[str, Any]:
        """Centralized request handler with comprehensive error handling"""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '')
            if 'json' in content_type.lower():
                return {'success': True, 'data': response.json(), 'format': 'json'}
            else:
                return {'success': True, 'data': response.content, 'format': 'binary'}
        except requests.exceptions.Timeout:
            return {'error': 'Request timeout', 'timeout': True, 'status_code': None}
        except requests.exceptions.ConnectionError:
            return {'error': 'Connection error', 'connection_error': True, 'status_code': None}
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                return {'error': 'Data not found', 'not_found': True, 'status_code': response.status_code}
            else:
                return {'error': f'HTTP error: {e}', 'http_error': True, 'status_code': response.status_code}
        except requests.exceptions.RequestException as e:
            return {'error': f'Request error: {e}', 'request_error': True, 'status_code': None}
        except Exception as e:
            return {'error': f'Unexpected error: {e}', 'general_error': True, 'status_code': None}

    def get_federal_funds_rate(self, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get Federal Funds Rate data from NY Fed"""
        try:
            if not start_date:
                start_date = '2016-03-01'
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            url = f'{self.ny_fed_url}/rates/unsecured/effr/search.json'
            params = {'startDate': start_date, 'endDate': end_date}
            result = self._make_request(url, params)
            if 'error' in result:
                return FederalReserveError('federal_funds_rate', result['error'], result.get('status_code')).to_dict()
            if result.get('format') == 'json':
                data = result.get('data', {})
                ref_rates = data.get('refRates', [])
                if not ref_rates:
                    return FederalReserveError('federal_funds_rate', 'No federal funds rate data found').to_dict()
                processed_data = []
                for rate_data in ref_rates:
                    processed_data.append({'date': rate_data.get('effectiveDate'), 'rate': float(rate_data.get('percentRate', 0)) / 100 if rate_data.get('percentRate') else None, 'target_range_upper': float(rate_data.get('targetRateTo', 0)) / 100 if rate_data.get('targetRateTo') else None, 'target_range_lower': float(rate_data.get('targetRateFrom', 0)) / 100 if rate_data.get('targetRateFrom') else None, 'percentile_1': float(rate_data.get('percentPercentile1', 0)) / 100 if rate_data.get('percentPercentile1') else None, 'percentile_25': float(rate_data.get('percentPercentile25', 0)) / 100 if rate_data.get('percentPercentile25') else None, 'percentile_75': float(rate_data.get('percentPercentile75', 0)) / 100 if rate_data.get('percentPercentile75') else None, 'percentile_99': float(rate_data.get('percentPercentile99', 0)) / 100 if rate_data.get('percentPercentile99') else None, 'volume': float(rate_data.get('volumeInBillions', 0)) if rate_data.get('volumeInBillions') else None, 'intraday_low': float(rate_data.get('intraDayLow', 0)) / 100 if rate_data.get('intraDayLow') else None, 'intraday_high': float(rate_data.get('intraDayHigh', 0)) / 100 if rate_data.get('intraDayHigh') else None, 'standard_deviation': float(rate_data.get('stdDeviation', 0)) / 100 if rate_data.get('stdDeviation') else None, 'revision_indicator': rate_data.get('revisionIndicator')})
                return {'success': True, 'endpoint': 'federal_funds_rate', 'data': processed_data, 'parameters': {'start_date': start_date, 'end_date': end_date}, 'total_records': len(processed_data), 'timestamp': int(datetime.now().timestamp())}
            else:
                return FederalReserveError('federal_funds_rate', 'Invalid response format').to_dict()
        except Exception as e:
            return FederalReserveError('federal_funds_rate', str(e)).to_dict()

    def get_sofr_rate(self, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get Secured Overnight Financing Rate (SOFR) data"""
        try:
            if not start_date:
                start_date = '2018-04-02'
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            url = f'{self.ny_fed_url}/rates/secured/sofr/search.json'
            params = {'startDate': start_date, 'endDate': end_date}
            result = self._make_request(url, params)
            if 'error' in result:
                return FederalReserveError('sofr_rate', result['error'], result.get('status_code')).to_dict()
            if result.get('format') == 'json':
                data = result.get('data', {})
                ref_rates = data.get('refRates', [])
                if not ref_rates:
                    return FederalReserveError('sofr_rate', 'No SOFR data found').to_dict()
                processed_data = []
                for rate_data in ref_rates:

                    def safe_float_convert(value):
                        """Safely convert to float, handling 'NA' and None values"""
                        if not value or value == 'NA' or value == "''":
                            return None
                        try:
                            return float(value) / 100 if float(value) != 0 else 0
                        except (ValueError, TypeError):
                            return None

                    def safe_volume_convert(value):
                        """Safely convert volume to float"""
                        if not value or value == 'NA' or value == "''":
                            return None
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return None
                    processed_data.append({'date': rate_data.get('effectiveDate'), 'rate': safe_float_convert(rate_data.get('percentRate')), 'percentile_1': safe_float_convert(rate_data.get('percentPercentile1')), 'percentile_25': safe_float_convert(rate_data.get('percentPercentile25')), 'percentile_75': safe_float_convert(rate_data.get('percentPercentile75')), 'percentile_99': safe_float_convert(rate_data.get('percentPercentile99')), 'volume': safe_volume_convert(rate_data.get('volumeInBillions'))})
                return {'success': True, 'endpoint': 'sofr_rate', 'data': processed_data, 'parameters': {'start_date': start_date, 'end_date': end_date}, 'total_records': len(processed_data), 'timestamp': int(datetime.now().timestamp())}
            else:
                return FederalReserveError('sofr_rate', 'Invalid response format').to_dict()
        except Exception as e:
            return FederalReserveError('sofr_rate', str(e)).to_dict()

    def get_treasury_rates(self, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get Treasury rates data (H.15 release)"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            url = f'{self.base_url}/datadownload/Output.aspx?rel=H15&series=bf17364827e38702b42a58cf8eaa3f78&lastobs=&from=&to=&filetype=csv&label=include&layout=seriescolumn&type=package'
            result = self._make_request(url)
            if 'error' in result:
                return FederalReserveError('treasury_rates', result['error'], result.get('status_code')).to_dict()
            if result.get('format') == 'binary':
                df = pd.read_csv(BytesIO(result['data']), header=5, index_col=None, parse_dates=True)
                df.columns = ['date'] + TREASURY_MATURITIES
                df = df.set_index('date').replace('ND', pd.NA)
                df = df.dropna(axis=0, how='all').reset_index()
                df['date'] = pd.to_datetime(df['date'])
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
                for maturity in TREASURY_MATURITIES:
                    df[maturity] = pd.to_numeric(df[maturity], errors='coerce') / 100
                df = df.fillna('N/A').replace('N/A', None)
                df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                processed_data = df.to_dict(orient='records')
                return {'success': True, 'endpoint': 'treasury_rates', 'data': processed_data, 'parameters': {'start_date': start_date, 'end_date': end_date}, 'total_records': len(processed_data), 'timestamp': int(datetime.now().timestamp())}
            else:
                return FederalReserveError('treasury_rates', 'Invalid response format').to_dict()
        except Exception as e:
            return FederalReserveError('treasury_rates', str(e)).to_dict()

    def get_yield_curve(self, date: Optional[str]=None) -> Dict[str, Any]:
        """Get yield curve data for specific date(s)"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            url = f'{self.base_url}/datadownload/Output.aspx?rel=H15&series=bf17364827e38702b42a58cf8eaa3f78&lastobs=&from=&to=&filetype=csv&label=include&layout=seriescolumn&type=package'
            result = self._make_request(url)
            if 'error' in result:
                return FederalReserveError('yield_curve', result['error'], result.get('status_code')).to_dict()
            if result.get('format') == 'binary':
                df = pd.read_csv(BytesIO(result['data']), header=5, index_col=None, parse_dates=True)
                df.columns = ['date'] + TREASURY_MATURITIES
                df = df.set_index('date').replace('ND', pd.NA)
                df = df.dropna(axis=0, how='all')
                dates = [d.strip() for d in date.split(',')]
                df.index = pd.to_datetime(df.index)
                nearest_dates = []
                for target_date in dates:
                    try:
                        target_dt = pd.to_datetime(target_date)
                        nearest = df.index.asof(target_dt)
                        if nearest is not pd.NaT:
                            nearest_dates.append(nearest)
                    except:
                        continue
                if not nearest_dates:
                    return FederalReserveError('yield_curve', 'No valid dates found').to_dict()
                df = df[df.index.isin(nearest_dates)]
                df = df.fillna('N/A').replace('N/A', None)
                flattened_data = df.reset_index().melt(id_vars='date', var_name='maturity', value_name='rate')
                flattened_data = flattened_data.sort_values(['date', 'maturity'])
                flattened_data['rate'] = pd.to_numeric(flattened_data['rate'], errors='coerce') / 100
                flattened_data['date'] = flattened_data['date'].dt.strftime('%Y-%m-%d')
                processed_data = flattened_data.to_dict(orient='records')
                return {'success': True, 'endpoint': 'yield_curve', 'data': processed_data, 'parameters': {'date': date}, 'total_records': len(processed_data), 'timestamp': int(datetime.now().timestamp())}
            else:
                return FederalReserveError('yield_curve', 'Invalid response format').to_dict()
        except Exception as e:
            return FederalReserveError('yield_curve', str(e)).to_dict()

    def get_money_measures(self, start_date: Optional[str]=None, end_date: Optional[str]=None, adjusted: bool=False) -> Dict[str, Any]:
        """Get Money Supply Measures (M1, M2) data"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=10 * 365)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            url = f'{self.base_url}/datadownload/Output.aspx?rel=H6&series=798e2796917702a5f8423426ba7e6b42&lastobs=&from=&to=&filetype=csv&label=include&layout=seriescolumn&type=package'
            result = self._make_request(url)
            if 'error' in result:
                return FederalReserveError('money_measures', result['error'], result.get('status_code')).to_dict()
            if result.get('format') == 'binary':
                df = pd.read_csv(BytesIO(result['data']), header=5, index_col=None, parse_dates=True)
                suffix = '_N' if adjusted else ''
                columns_to_get = ['Time Period'] + [col + f'{suffix}.M' for col in MONEY_MEASURES.keys()]
                df = df[columns_to_get]
                df.columns = ['month'] + list(MONEY_MEASURES.values())
                df = df.replace('ND', None)
                df['month'] = pd.to_datetime(df['month'])
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df['month'] >= start_dt) & (df['month'] <= end_dt)]
                df = df.set_index('month')
                df = df.applymap(lambda x: float(x) if x != '-' and x is not None else x)
                df = df.reset_index(drop=False)
                df['month'] = df['month'].dt.strftime('%Y-%m-%d')
                processed_data = df.to_dict(orient='records')
                return {'success': True, 'endpoint': 'money_measures', 'data': processed_data, 'parameters': {'start_date': start_date, 'end_date': end_date, 'adjusted': adjusted}, 'total_records': len(processed_data), 'timestamp': int(datetime.now().timestamp())}
            else:
                return FederalReserveError('money_measures', 'Invalid response format').to_dict()
        except Exception as e:
            return FederalReserveError('money_measures', str(e)).to_dict()

    def get_central_bank_holdings(self, holding_type: str='all_treasury', summary: bool=False, date: Optional[str]=None) -> Dict[str, Any]:
        """Get Federal Reserve Central Bank Holdings (SOMA) data"""
        try:
            if holding_type not in HOLDING_TYPES:
                return FederalReserveError('central_bank_holdings', f'Invalid holding type: {holding_type}').to_dict()
            if summary:
                return {'success': True, 'endpoint': 'central_bank_holdings', 'data': {'message': 'Central bank holdings summary - requires NY Fed API implementation', 'holding_type': holding_type, 'note': 'This endpoint requires the full NY Fed SOMA API implementation'}, 'parameters': {'holding_type': holding_type, 'summary': summary, 'date': date}, 'timestamp': int(datetime.now().timestamp())}
            else:
                return {'success': True, 'endpoint': 'central_bank_holdings', 'data': {'message': 'Central bank holdings detailed data - requires NY Fed API implementation', 'holding_type': holding_type, 'note': 'This endpoint requires the full NY Fed SOMA API implementation'}, 'parameters': {'holding_type': holding_type, 'summary': summary, 'date': date}, 'timestamp': int(datetime.now().timestamp())}
        except Exception as e:
            return FederalReserveError('central_bank_holdings', str(e)).to_dict()

    def get_overnight_bank_funding_rate(self, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get Overnight Bank Funding Rate data"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            return {'success': True, 'endpoint': 'overnight_bank_funding_rate', 'data': {'message': 'Overnight Bank Funding Rate - requires NY Fed API implementation', 'note': 'This endpoint requires the full NY Fed API implementation'}, 'parameters': {'start_date': start_date, 'end_date': end_date}, 'timestamp': int(datetime.now().timestamp())}
        except Exception as e:
            return FederalReserveError('overnight_bank_funding_rate', str(e)).to_dict()

    def get_comprehensive_monetary_data(self, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get comprehensive monetary data from multiple endpoints"""
        result = {'success': True, 'start_date': start_date, 'end_date': end_date, 'timestamp': int(datetime.now().timestamp()), 'endpoints': {}, 'failed_endpoints': []}
        endpoints = [('federal_funds_rate', lambda: self.get_federal_funds_rate(start_date, end_date)), ('sofr_rate', lambda: self.get_sofr_rate(start_date, end_date)), ('treasury_rates', lambda: self.get_treasury_rates(start_date, end_date)), ('money_measures', lambda: self.get_money_measures(start_date, end_date))]
        overall_success = False
        for endpoint_name, endpoint_func in endpoints:
            try:
                endpoint_result = endpoint_func()
                result['endpoints'][endpoint_name] = endpoint_result
                if endpoint_result.get('success'):
                    overall_success = True
                else:
                    result['failed_endpoints'].append({'endpoint': endpoint_name, 'error': endpoint_result.get('error', 'Unknown error')})
            except Exception as e:
                result['failed_endpoints'].append({'endpoint': endpoint_name, 'error': str(e)})
        result['success'] = overall_success
        return result

    def get_market_overview(self) -> Dict[str, Any]:
        """Get current market overview with key rates"""
        result = {'success': True, 'timestamp': int(datetime.now().timestamp()), 'endpoints': {}, 'failed_endpoints': []}
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        endpoints = [('federal_funds_rate', lambda: self.get_federal_funds_rate(start_date, end_date)), ('sofr_rate', lambda: self.get_sofr_rate(start_date, end_date)), ('treasury_rates', lambda: self.get_treasury_rates(start_date, end_date))]
        overall_success = False
        for endpoint_name, endpoint_func in endpoints:
            try:
                endpoint_result = endpoint_func()
                result['endpoints'][endpoint_name] = endpoint_result
                if endpoint_result.get('success'):
                    overall_success = True
                else:
                    result['failed_endpoints'].append({'endpoint': endpoint_name, 'error': endpoint_result.get('error', 'Unknown error')})
            except Exception as e:
                result['failed_endpoints'].append({'endpoint': endpoint_name, 'error': str(e)})
        result['success'] = overall_success
        return result

def safe_float_convert(value):
    """Safely convert to float, handling 'NA' and None values"""
    if not value or value == 'NA' or value == "''":
        return None
    try:
        return float(value) / 100 if float(value) != 0 else 0
    except (ValueError, TypeError):
        return None

def safe_volume_convert(value):
    """Safely convert volume to float"""
    if not value or value == 'NA' or value == "''":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

class DurationMeasures:
    """Duration calculations for fixed income securities"""

    @staticmethod
    @cache_calculation
    def macaulay_duration(bond: Bond, yield_rate: Decimal, settlement_date: Optional[date]=None) -> Decimal:
        """Calculate Macaulay duration"""
        ValidationUtils.validate_yield(yield_rate, 'Yield rate')
        if settlement_date is None:
            settlement_date = date.today()
        bond_instrument = create_bond_instrument(bond)
        cash_flows = bond_instrument.generate_cash_flows(settlement_date)
        if not cash_flows:
            return Decimal('0')
        total_pv = Decimal('0')
        weighted_time = Decimal('0')
        for cf in cash_flows:
            time_to_payment = DateUtils.calculate_day_count_fraction(settlement_date, cf.date, bond.day_count_convention)
            pv = MathUtils.present_value(cf.amount, yield_rate, time_to_payment)
            total_pv += pv
            weighted_time += time_to_payment * pv
        if total_pv == 0:
            return Decimal('0')
        return weighted_time / total_pv

    @staticmethod
    def modified_duration(bond: Bond, yield_rate: Decimal, settlement_date: Optional[date]=None) -> Decimal:
        """Calculate Modified duration"""
        mac_duration = DurationMeasures.macaulay_duration(bond, yield_rate, settlement_date)
        frequency = bond.coupon_frequency.value
        if frequency == 0:
            return mac_duration
        return mac_duration / (Decimal('1') + yield_rate / Decimal(str(frequency)))

    @staticmethod
    def effective_duration(bond: Bond, base_curve: SpotCurve, yield_shift: Decimal=Decimal('0.0001')) -> Decimal:
        """Calculate Effective duration using curve shifts"""
        ValidationUtils.validate_positive(yield_shift, 'Yield shift')
        up_curve = base_curve.shift_curve(yield_shift, 'parallel')
        down_curve = base_curve.shift_curve(-yield_shift, 'parallel')
        base_price = BondValuation.present_value_with_curve(bond, base_curve)
        up_price = BondValuation.present_value_with_curve(bond, up_curve)
        down_price = BondValuation.present_value_with_curve(bond, down_curve)
        if base_price == 0:
            return Decimal('0')
        return -(down_price - up_price) / (Decimal('2') * base_price * yield_shift)

    @staticmethod
    def money_duration(bond: Bond, yield_rate: Decimal, price: Decimal, settlement_date: Optional[date]=None) -> Decimal:
        """Calculate Money duration (Modified duration × Price)"""
        mod_duration = DurationMeasures.modified_duration(bond, yield_rate, settlement_date)
        return mod_duration * price

    @staticmethod
    def dollar_duration(bond: Bond, yield_rate: Decimal, price: Decimal, settlement_date: Optional[date]=None) -> Decimal:
        """Calculate Dollar duration (Money duration × 0.01)"""
        money_dur = DurationMeasures.money_duration(bond, yield_rate, price, settlement_date)
        return money_dur * Decimal('0.01')

    @staticmethod
    def price_value_basis_point(bond: Bond, yield_rate: Decimal, settlement_date: Optional[date]=None) -> Decimal:
        """Calculate Price Value of a Basis Point (PVBP)"""
        if settlement_date is None:
            settlement_date = date.today()
        base_price = BondValuation.present_value(bond, yield_rate, settlement_date)
        shifted_price = BondValuation.present_value(bond, yield_rate + Decimal('0.0001'), settlement_date)
        return base_price - shifted_price

@staticmethod
@cache_calculation
def macaulay_duration(bond: Bond, yield_rate: Decimal, settlement_date: Optional[date]=None) -> Decimal:
    """Calculate Macaulay duration"""
    ValidationUtils.validate_yield(yield_rate, 'Yield rate')
    if settlement_date is None:
        settlement_date = date.today()
    bond_instrument = create_bond_instrument(bond)
    cash_flows = bond_instrument.generate_cash_flows(settlement_date)
    if not cash_flows:
        return Decimal('0')
    total_pv = Decimal('0')
    weighted_time = Decimal('0')
    for cf in cash_flows:
        time_to_payment = DateUtils.calculate_day_count_fraction(settlement_date, cf.date, bond.day_count_convention)
        pv = MathUtils.present_value(cf.amount, yield_rate, time_to_payment)
        total_pv += pv
        weighted_time += time_to_payment * pv
    if total_pv == 0:
        return Decimal('0')
    return weighted_time / total_pv

@staticmethod
def modified_duration(bond: Bond, yield_rate: Decimal, settlement_date: Optional[date]=None) -> Decimal:
    """Calculate Modified duration"""
    mac_duration = DurationMeasures.macaulay_duration(bond, yield_rate, settlement_date)
    frequency = bond.coupon_frequency.value
    if frequency == 0:
        return mac_duration
    return mac_duration / (Decimal('1') + yield_rate / Decimal(str(frequency)))

@staticmethod
def effective_duration(bond: Bond, base_curve: SpotCurve, yield_shift: Decimal=Decimal('0.0001')) -> Decimal:
    """Calculate Effective duration using curve shifts"""
    ValidationUtils.validate_positive(yield_shift, 'Yield shift')
    up_curve = base_curve.shift_curve(yield_shift, 'parallel')
    down_curve = base_curve.shift_curve(-yield_shift, 'parallel')
    base_price = BondValuation.present_value_with_curve(bond, base_curve)
    up_price = BondValuation.present_value_with_curve(bond, up_curve)
    down_price = BondValuation.present_value_with_curve(bond, down_curve)
    if base_price == 0:
        return Decimal('0')
    return -(down_price - up_price) / (Decimal('2') * base_price * yield_shift)

@staticmethod
def money_duration(bond: Bond, yield_rate: Decimal, price: Decimal, settlement_date: Optional[date]=None) -> Decimal:
    """Calculate Money duration (Modified duration × Price)"""
    mod_duration = DurationMeasures.modified_duration(bond, yield_rate, settlement_date)
    return mod_duration * price

@staticmethod
def dollar_duration(bond: Bond, yield_rate: Decimal, price: Decimal, settlement_date: Optional[date]=None) -> Decimal:
    """Calculate Dollar duration (Money duration × 0.01)"""
    money_dur = DurationMeasures.money_duration(bond, yield_rate, price, settlement_date)
    return money_dur * Decimal('0.01')

@staticmethod
def price_value_basis_point(bond: Bond, yield_rate: Decimal, settlement_date: Optional[date]=None) -> Decimal:
    """Calculate Price Value of a Basis Point (PVBP)"""
    if settlement_date is None:
        settlement_date = date.today()
    base_price = BondValuation.present_value(bond, yield_rate, settlement_date)
    shifted_price = BondValuation.present_value(bond, yield_rate + Decimal('0.0001'), settlement_date)
    return base_price - shifted_price

class ConvexityMeasures:
    """Convexity calculations for fixed income securities"""

    @staticmethod
    @cache_calculation
    def effective_convexity(bond: Bond, base_curve: SpotCurve, yield_shift: Decimal=Decimal('0.0001')) -> Decimal:
        """Calculate Effective convexity using curve shifts"""
        ValidationUtils.validate_positive(yield_shift, 'Yield shift')
        up_curve = base_curve.shift_curve(yield_shift, 'parallel')
        down_curve = base_curve.shift_curve(-yield_shift, 'parallel')
        base_price = BondValuation.present_value_with_curve(bond, base_curve)
        up_price = BondValuation.present_value_with_curve(bond, up_curve)
        down_price = BondValuation.present_value_with_curve(bond, down_curve)
        if base_price == 0:
            return Decimal('0')
        numerator = up_price + down_price - Decimal('2') * base_price
        denominator = base_price * yield_shift ** 2
        return numerator / denominator

    @staticmethod
    def convexity_adjustment(duration: Decimal, convexity: Decimal, yield_change: Decimal) -> Decimal:
        """Calculate convexity adjustment to duration-based price change"""
        return Decimal('0.5') * convexity * yield_change ** 2

    @staticmethod
    def approximate_price_change(duration: Decimal, convexity: Decimal, yield_change: Decimal) -> Decimal:
        """Approximate percentage price change using duration and convexity"""
        duration_effect = -duration * yield_change
        convexity_effect = ConvexityMeasures.convexity_adjustment(duration, convexity, yield_change)
        return duration_effect + convexity_effect

@staticmethod
@cache_calculation
def effective_convexity(bond: Bond, base_curve: SpotCurve, yield_shift: Decimal=Decimal('0.0001')) -> Decimal:
    """Calculate Effective convexity using curve shifts"""
    ValidationUtils.validate_positive(yield_shift, 'Yield shift')
    up_curve = base_curve.shift_curve(yield_shift, 'parallel')
    down_curve = base_curve.shift_curve(-yield_shift, 'parallel')
    base_price = BondValuation.present_value_with_curve(bond, base_curve)
    up_price = BondValuation.present_value_with_curve(bond, up_curve)
    down_price = BondValuation.present_value_with_curve(bond, down_curve)
    if base_price == 0:
        return Decimal('0')
    numerator = up_price + down_price - Decimal('2') * base_price
    denominator = base_price * yield_shift ** 2
    return numerator / denominator

@staticmethod
def convexity_adjustment(duration: Decimal, convexity: Decimal, yield_change: Decimal) -> Decimal:
    """Calculate convexity adjustment to duration-based price change"""
    return Decimal('0.5') * convexity * yield_change ** 2

class KeyRateDuration:
    """Key Rate Duration analysis for yield curve risk"""

    @staticmethod
    def calculate_key_rate_durations(bond: Bond, base_curve: SpotCurve, key_maturities: List[Decimal], yield_shift: Decimal=Decimal('0.0001')) -> Dict[Decimal, Decimal]:
        """Calculate key rate durations for specified maturities"""
        base_price = BondValuation.present_value_with_curve(bond, base_curve)
        key_durations = {}
        for maturity in key_maturities:
            shifted_curve = KeyRateDuration._create_key_rate_shifted_curve(base_curve, maturity, yield_shift)
            shifted_price = BondValuation.present_value_with_curve(bond, shifted_curve)
            if base_price != 0:
                key_duration = -(shifted_price - base_price) / (base_price * yield_shift)
            else:
                key_duration = Decimal('0')
            key_durations[maturity] = key_duration
        return key_durations

    @staticmethod
    def _create_key_rate_shifted_curve(base_curve: SpotCurve, shift_maturity: Decimal, shift_amount: Decimal) -> SpotCurve:
        """Create curve with shift concentrated at specific maturity"""
        new_rates = []
        for i, maturity in enumerate(base_curve.curve.maturities):
            base_rate = base_curve.curve.rates[i]
            if abs(maturity - shift_maturity) <= Decimal('1'):
                weight = Decimal('1') - abs(maturity - shift_maturity)
                shift = shift_amount * weight
            else:
                shift = Decimal('0')
            new_rates.append(base_rate + shift)
        from models import YieldCurve
        new_curve = YieldCurve(curve_date=base_curve.curve.curve_date, maturities=base_curve.curve.maturities.copy(), rates=new_rates, currency=base_curve.curve.currency, curve_type='spot')
        from yield_curves import SpotCurve
        return SpotCurve(new_curve)

@staticmethod
def calculate_key_rate_durations(bond: Bond, base_curve: SpotCurve, key_maturities: List[Decimal], yield_shift: Decimal=Decimal('0.0001')) -> Dict[Decimal, Decimal]:
    """Calculate key rate durations for specified maturities"""
    base_price = BondValuation.present_value_with_curve(bond, base_curve)
    key_durations = {}
    for maturity in key_maturities:
        shifted_curve = KeyRateDuration._create_key_rate_shifted_curve(base_curve, maturity, yield_shift)
        shifted_price = BondValuation.present_value_with_curve(bond, shifted_curve)
        if base_price != 0:
            key_duration = -(shifted_price - base_price) / (base_price * yield_shift)
        else:
            key_duration = Decimal('0')
        key_durations[maturity] = key_duration
    return key_durations

@staticmethod
def _create_key_rate_shifted_curve(base_curve: SpotCurve, shift_maturity: Decimal, shift_amount: Decimal) -> SpotCurve:
    """Create curve with shift concentrated at specific maturity"""
    new_rates = []
    for i, maturity in enumerate(base_curve.curve.maturities):
        base_rate = base_curve.curve.rates[i]
        if abs(maturity - shift_maturity) <= Decimal('1'):
            weight = Decimal('1') - abs(maturity - shift_maturity)
            shift = shift_amount * weight
        else:
            shift = Decimal('0')
        new_rates.append(base_rate + shift)
    from models import YieldCurve
    new_curve = YieldCurve(curve_date=base_curve.curve.curve_date, maturities=base_curve.curve.maturities.copy(), rates=new_rates, currency=base_curve.curve.currency, curve_type='spot')
    from yield_curves import SpotCurve
    return SpotCurve(new_curve)

class PortfolioRiskMetrics:
    """Portfolio-level risk calculations"""

    @staticmethod
    def portfolio_duration(portfolio: Portfolio, yields: Dict[str, Decimal], prices: Dict[str, Decimal]) -> Decimal:
        """Calculate portfolio duration as market-value weighted average"""
        total_market_value = Decimal('0')
        weighted_duration = Decimal('0')
        for bond, quantity in portfolio.holdings:
            bond_id = bond.isin
            if bond_id not in yields or bond_id not in prices:
                continue
            bond_yield = yields[bond_id]
            bond_price = prices[bond_id]
            market_value = bond_price * quantity
            duration = DurationMeasures.modified_duration(bond, bond_yield)
            total_market_value += market_value
            weighted_duration += duration * market_value
        if total_market_value == 0:
            return Decimal('0')
        return weighted_duration / total_market_value

    @staticmethod
    def portfolio_convexity(portfolio: Portfolio, base_curve: SpotCurve, prices: Dict[str, Decimal]) -> Decimal:
        """Calculate portfolio convexity as market-value weighted average"""
        total_market_value = Decimal('0')
        weighted_convexity = Decimal('0')
        for bond, quantity in portfolio.holdings:
            bond_id = bond.isin
            if bond_id not in prices:
                continue
            bond_price = prices[bond_id]
            market_value = bond_price * quantity
            convexity = ConvexityMeasures.effective_convexity(bond, base_curve)
            total_market_value += market_value
            weighted_convexity += convexity * market_value
        if total_market_value == 0:
            return Decimal('0')
        return weighted_convexity / total_market_value

    @staticmethod
    def duration_matching_error(portfolio: Portfolio, target_duration: Decimal, yields: Dict[str, Decimal], prices: Dict[str, Decimal]) -> Decimal:
        """Calculate duration matching error"""
        portfolio_dur = PortfolioRiskMetrics.portfolio_duration(portfolio, yields, prices)
        return portfolio_dur - target_duration

    @staticmethod
    def portfolio_yield(portfolio: Portfolio, yields: Dict[str, Decimal], prices: Dict[str, Decimal]) -> Decimal:
        """Calculate portfolio yield as market-value weighted average"""
        total_market_value = Decimal('0')
        weighted_yield = Decimal('0')
        for bond, quantity in portfolio.holdings:
            bond_id = bond.isin
            if bond_id not in yields or bond_id not in prices:
                continue
            bond_yield = yields[bond_id]
            bond_price = prices[bond_id]
            market_value = bond_price * quantity
            total_market_value += market_value
            weighted_yield += bond_yield * market_value
        if total_market_value == 0:
            return Decimal('0')
        return weighted_yield / total_market_value

@staticmethod
def portfolio_duration(portfolio: Portfolio, yields: Dict[str, Decimal], prices: Dict[str, Decimal]) -> Decimal:
    """Calculate portfolio duration as market-value weighted average"""
    total_market_value = Decimal('0')
    weighted_duration = Decimal('0')
    for bond, quantity in portfolio.holdings:
        bond_id = bond.isin
        if bond_id not in yields or bond_id not in prices:
            continue
        bond_yield = yields[bond_id]
        bond_price = prices[bond_id]
        market_value = bond_price * quantity
        duration = DurationMeasures.modified_duration(bond, bond_yield)
        total_market_value += market_value
        weighted_duration += duration * market_value
    if total_market_value == 0:
        return Decimal('0')
    return weighted_duration / total_market_value

@staticmethod
def portfolio_convexity(portfolio: Portfolio, base_curve: SpotCurve, prices: Dict[str, Decimal]) -> Decimal:
    """Calculate portfolio convexity as market-value weighted average"""
    total_market_value = Decimal('0')
    weighted_convexity = Decimal('0')
    for bond, quantity in portfolio.holdings:
        bond_id = bond.isin
        if bond_id not in prices:
            continue
        bond_price = prices[bond_id]
        market_value = bond_price * quantity
        convexity = ConvexityMeasures.effective_convexity(bond, base_curve)
        total_market_value += market_value
        weighted_convexity += convexity * market_value
    if total_market_value == 0:
        return Decimal('0')
    return weighted_convexity / total_market_value

@staticmethod
def duration_matching_error(portfolio: Portfolio, target_duration: Decimal, yields: Dict[str, Decimal], prices: Dict[str, Decimal]) -> Decimal:
    """Calculate duration matching error"""
    portfolio_dur = PortfolioRiskMetrics.portfolio_duration(portfolio, yields, prices)
    return portfolio_dur - target_duration

@staticmethod
def portfolio_yield(portfolio: Portfolio, yields: Dict[str, Decimal], prices: Dict[str, Decimal]) -> Decimal:
    """Calculate portfolio yield as market-value weighted average"""
    total_market_value = Decimal('0')
    weighted_yield = Decimal('0')
    for bond, quantity in portfolio.holdings:
        bond_id = bond.isin
        if bond_id not in yields or bond_id not in prices:
            continue
        bond_yield = yields[bond_id]
        bond_price = prices[bond_id]
        market_value = bond_price * quantity
        total_market_value += market_value
        weighted_yield += bond_yield * market_value
    if total_market_value == 0:
        return Decimal('0')
    return weighted_yield / total_market_value

class ValueAtRisk:
    """Value at Risk calculations for fixed income portfolios"""

    @staticmethod
    def parametric_var(portfolio_value: Decimal, portfolio_duration: Decimal, yield_volatility: Decimal, confidence_level: Decimal=Decimal('0.95'), time_horizon: Decimal=Decimal('1')) -> Decimal:
        """Calculate parametric VaR using duration approximation"""
        ValidationUtils.validate_positive(portfolio_value, 'Portfolio value')
        ValidationUtils.validate_positive(yield_volatility, 'Yield volatility')
        ValidationUtils.validate_percentage(confidence_level, 'Confidence level')
        if confidence_level == Decimal('0.95'):
            z_score = Decimal('1.645')
        elif confidence_level == Decimal('0.99'):
            z_score = Decimal('2.326')
        else:
            z_score = Decimal('1.645')
        time_factor = time_horizon ** Decimal('0.5')
        var = portfolio_value * portfolio_duration * yield_volatility * z_score * time_factor
        return var

    @staticmethod
    def monte_carlo_var(portfolio: Portfolio, base_curve: SpotCurve, yield_volatility: Decimal, simulations: int=10000, confidence_level: Decimal=Decimal('0.95'), time_horizon: Decimal=Decimal('1')) -> Tuple[Decimal, List[Decimal]]:
        """Calculate VaR using Monte Carlo simulation"""
        import random
        current_value = Decimal('0')
        simulated_values = []
        for bond, quantity in portfolio.holdings:
            bond_value = BondValuation.present_value_with_curve(bond, base_curve)
            current_value += bond_value * quantity
        for _ in range(simulations):
            random_change = Decimal(str(random.gauss(0, float(yield_volatility * time_horizon ** Decimal('0.5')))))
            shifted_curve = base_curve.shift_curve(random_change, 'parallel')
            portfolio_value = Decimal('0')
            for bond, quantity in portfolio.holdings:
                bond_value = BondValuation.present_value_with_curve(bond, shifted_curve)
                portfolio_value += bond_value * quantity
            value_change = portfolio_value - current_value
            simulated_values.append(value_change)
        simulated_values.sort()
        var_index = int((1 - confidence_level) * simulations)
        var = -simulated_values[var_index]
        return (var, simulated_values)

@staticmethod
def parametric_var(portfolio_value: Decimal, portfolio_duration: Decimal, yield_volatility: Decimal, confidence_level: Decimal=Decimal('0.95'), time_horizon: Decimal=Decimal('1')) -> Decimal:
    """Calculate parametric VaR using duration approximation"""
    ValidationUtils.validate_positive(portfolio_value, 'Portfolio value')
    ValidationUtils.validate_positive(yield_volatility, 'Yield volatility')
    ValidationUtils.validate_percentage(confidence_level, 'Confidence level')
    if confidence_level == Decimal('0.95'):
        z_score = Decimal('1.645')
    elif confidence_level == Decimal('0.99'):
        z_score = Decimal('2.326')
    else:
        z_score = Decimal('1.645')
    time_factor = time_horizon ** Decimal('0.5')
    var = portfolio_value * portfolio_duration * yield_volatility * z_score * time_factor
    return var

@staticmethod
def monte_carlo_var(portfolio: Portfolio, base_curve: SpotCurve, yield_volatility: Decimal, simulations: int=10000, confidence_level: Decimal=Decimal('0.95'), time_horizon: Decimal=Decimal('1')) -> Tuple[Decimal, List[Decimal]]:
    """Calculate VaR using Monte Carlo simulation"""
    import random
    current_value = Decimal('0')
    simulated_values = []
    for bond, quantity in portfolio.holdings:
        bond_value = BondValuation.present_value_with_curve(bond, base_curve)
        current_value += bond_value * quantity
    for _ in range(simulations):
        random_change = Decimal(str(random.gauss(0, float(yield_volatility * time_horizon ** Decimal('0.5')))))
        shifted_curve = base_curve.shift_curve(random_change, 'parallel')
        portfolio_value = Decimal('0')
        for bond, quantity in portfolio.holdings:
            bond_value = BondValuation.present_value_with_curve(bond, shifted_curve)
            portfolio_value += bond_value * quantity
        value_change = portfolio_value - current_value
        simulated_values.append(value_change)
    simulated_values.sort()
    var_index = int((1 - confidence_level) * simulations)
    var = -simulated_values[var_index]
    return (var, simulated_values)

class StressTestingFramework:
    """Stress testing framework for fixed income portfolios"""

    @staticmethod
    def parallel_shift_stress_test(portfolio: Portfolio, base_curve: SpotCurve, stress_scenarios: List[Decimal]) -> Dict[str, Dict]:
        """Stress test portfolio under parallel yield curve shifts"""
        base_value = Decimal('0')
        for bond, quantity in portfolio.holdings:
            bond_value = BondValuation.present_value_with_curve(bond, base_curve)
            base_value += bond_value * quantity
        results = {'base_case': {'value': base_value, 'change': Decimal('0'), 'change_pct': Decimal('0')}}
        for shift in stress_scenarios:
            stressed_curve = base_curve.shift_curve(shift, 'parallel')
            stressed_value = Decimal('0')
            for bond, quantity in portfolio.holdings:
                bond_value = BondValuation.present_value_with_curve(bond, stressed_curve)
                stressed_value += bond_value * quantity
            change = stressed_value - base_value
            change_pct = change / base_value * Decimal('100') if base_value != 0 else Decimal('0')
            scenario_name = f'shift_{shift * 10000:.0f}bp'
            results[scenario_name] = {'value': stressed_value, 'change': change, 'change_pct': change_pct}
        return results

    @staticmethod
    def yield_curve_scenario_analysis(portfolio: Portfolio, base_curve: SpotCurve, scenarios: Dict[str, str]) -> Dict[str, Dict]:
        """Analyze portfolio under different yield curve scenarios"""
        base_value = Decimal('0')
        for bond, quantity in portfolio.holdings:
            bond_value = BondValuation.present_value_with_curve(bond, base_curve)
            base_value += bond_value * quantity
        results = {'base_case': {'value': base_value, 'change': Decimal('0'), 'change_pct': Decimal('0')}}
        for scenario_name, scenario_type in scenarios.items():
            if scenario_type == 'steepening':
                stressed_curve = base_curve.shift_curve(Decimal('0.01'), 'steepening')
            elif scenario_type == 'flattening':
                stressed_curve = base_curve.shift_curve(Decimal('0.01'), 'flattening')
            elif scenario_type == 'bear_steepening':
                stressed_curve = base_curve.shift_curve(Decimal('0.005'), 'parallel')
                stressed_curve = stressed_curve.shift_curve(Decimal('0.005'), 'steepening')
            elif scenario_type == 'bull_flattening':
                stressed_curve = base_curve.shift_curve(Decimal('-0.005'), 'parallel')
                stressed_curve = stressed_curve.shift_curve(Decimal('0.005'), 'flattening')
            else:
                continue
            stressed_value = Decimal('0')
            for bond, quantity in portfolio.holdings:
                bond_value = BondValuation.present_value_with_curve(bond, stressed_curve)
                stressed_value += bond_value * quantity
            change = stressed_value - base_value
            change_pct = change / base_value * Decimal('100') if base_value != 0 else Decimal('0')
            results[scenario_name] = {'value': stressed_value, 'change': change, 'change_pct': change_pct}
        return results

@staticmethod
def parallel_shift_stress_test(portfolio: Portfolio, base_curve: SpotCurve, stress_scenarios: List[Decimal]) -> Dict[str, Dict]:
    """Stress test portfolio under parallel yield curve shifts"""
    base_value = Decimal('0')
    for bond, quantity in portfolio.holdings:
        bond_value = BondValuation.present_value_with_curve(bond, base_curve)
        base_value += bond_value * quantity
    results = {'base_case': {'value': base_value, 'change': Decimal('0'), 'change_pct': Decimal('0')}}
    for shift in stress_scenarios:
        stressed_curve = base_curve.shift_curve(shift, 'parallel')
        stressed_value = Decimal('0')
        for bond, quantity in portfolio.holdings:
            bond_value = BondValuation.present_value_with_curve(bond, stressed_curve)
            stressed_value += bond_value * quantity
        change = stressed_value - base_value
        change_pct = change / base_value * Decimal('100') if base_value != 0 else Decimal('0')
        scenario_name = f'shift_{shift * 10000:.0f}bp'
        results[scenario_name] = {'value': stressed_value, 'change': change, 'change_pct': change_pct}
    return results

@staticmethod
def yield_curve_scenario_analysis(portfolio: Portfolio, base_curve: SpotCurve, scenarios: Dict[str, str]) -> Dict[str, Dict]:
    """Analyze portfolio under different yield curve scenarios"""
    base_value = Decimal('0')
    for bond, quantity in portfolio.holdings:
        bond_value = BondValuation.present_value_with_curve(bond, base_curve)
        base_value += bond_value * quantity
    results = {'base_case': {'value': base_value, 'change': Decimal('0'), 'change_pct': Decimal('0')}}
    for scenario_name, scenario_type in scenarios.items():
        if scenario_type == 'steepening':
            stressed_curve = base_curve.shift_curve(Decimal('0.01'), 'steepening')
        elif scenario_type == 'flattening':
            stressed_curve = base_curve.shift_curve(Decimal('0.01'), 'flattening')
        elif scenario_type == 'bear_steepening':
            stressed_curve = base_curve.shift_curve(Decimal('0.005'), 'parallel')
            stressed_curve = stressed_curve.shift_curve(Decimal('0.005'), 'steepening')
        elif scenario_type == 'bull_flattening':
            stressed_curve = base_curve.shift_curve(Decimal('-0.005'), 'parallel')
            stressed_curve = stressed_curve.shift_curve(Decimal('0.005'), 'flattening')
        else:
            continue
        stressed_value = Decimal('0')
        for bond, quantity in portfolio.holdings:
            bond_value = BondValuation.present_value_with_curve(bond, stressed_curve)
            stressed_value += bond_value * quantity
        change = stressed_value - base_value
        change_pct = change / base_value * Decimal('100') if base_value != 0 else Decimal('0')
        results[scenario_name] = {'value': stressed_value, 'change': change, 'change_pct': change_pct}
    return results

class HedgingAnalytics:
    """Hedging calculations and analytics"""

    @staticmethod
    def duration_hedge_ratio(target_bond: Bond, hedge_bond: Bond, target_duration: Decimal, hedge_duration: Decimal) -> Decimal:
        """Calculate hedge ratio for duration hedging"""
        if hedge_duration == 0:
            return Decimal('0')
        return target_duration / hedge_duration

    @staticmethod
    def optimal_hedge_portfolio(target_portfolio: Portfolio, hedge_instruments: List[Bond], base_curve: SpotCurve) -> Dict[str, Decimal]:
        """Calculate optimal hedge portfolio weights (simplified)"""
        target_duration = Decimal('0')
        target_value = Decimal('0')
        for bond, quantity in target_portfolio.holdings:
            bond_value = BondValuation.present_value_with_curve(bond, base_curve)
            bond_duration = DurationMeasures.effective_duration(bond, base_curve)
            position_value = bond_value * quantity
            target_value += position_value
            target_duration += bond_duration * position_value
        if target_value != 0:
            target_duration = target_duration / target_value
        if len(hedge_instruments) >= 2:
            short_bond = hedge_instruments[0]
            long_bond = hedge_instruments[1]
            short_duration = DurationMeasures.effective_duration(short_bond, base_curve)
            long_duration = DurationMeasures.effective_duration(long_bond, base_curve)
            if long_duration != short_duration:
                w2 = (-target_duration - short_duration) / (long_duration - short_duration)
                w1 = Decimal('1') - w2
                return {short_bond.isin: w1, long_bond.isin: w2}
        return {}

@staticmethod
def duration_hedge_ratio(target_bond: Bond, hedge_bond: Bond, target_duration: Decimal, hedge_duration: Decimal) -> Decimal:
    """Calculate hedge ratio for duration hedging"""
    if hedge_duration == 0:
        return Decimal('0')
    return target_duration / hedge_duration

@staticmethod
def optimal_hedge_portfolio(target_portfolio: Portfolio, hedge_instruments: List[Bond], base_curve: SpotCurve) -> Dict[str, Decimal]:
    """Calculate optimal hedge portfolio weights (simplified)"""
    target_duration = Decimal('0')
    target_value = Decimal('0')
    for bond, quantity in target_portfolio.holdings:
        bond_value = BondValuation.present_value_with_curve(bond, base_curve)
        bond_duration = DurationMeasures.effective_duration(bond, base_curve)
        position_value = bond_value * quantity
        target_value += position_value
        target_duration += bond_duration * position_value
    if target_value != 0:
        target_duration = target_duration / target_value
    if len(hedge_instruments) >= 2:
        short_bond = hedge_instruments[0]
        long_bond = hedge_instruments[1]
        short_duration = DurationMeasures.effective_duration(short_bond, base_curve)
        long_duration = DurationMeasures.effective_duration(long_bond, base_curve)
        if long_duration != short_duration:
            w2 = (-target_duration - short_duration) / (long_duration - short_duration)
            w1 = Decimal('1') - w2
            return {short_bond.isin: w1, long_bond.isin: w2}
    return {}

def generate_risk_report(portfolio: Portfolio, base_curve: SpotCurve, yields: Dict[str, Decimal], prices: Dict[str, Decimal]) -> Dict:
    """Generate comprehensive risk report for portfolio"""
    portfolio_dur = PortfolioRiskMetrics.portfolio_duration(portfolio, yields, prices)
    portfolio_conv = PortfolioRiskMetrics.portfolio_convexity(portfolio, base_curve, prices)
    portfolio_yld = PortfolioRiskMetrics.portfolio_yield(portfolio, yields, prices)
    total_value = Decimal('0')
    for bond, quantity in portfolio.holdings:
        if bond.isin in prices:
            total_value += prices[bond.isin] * quantity
    yield_vol = Decimal('0.01')
    var_95 = ValueAtRisk.parametric_var(total_value, portfolio_dur, yield_vol, Decimal('0.95'))
    var_99 = ValueAtRisk.parametric_var(total_value, portfolio_dur, yield_vol, Decimal('0.99'))
    stress_scenarios = [Decimal('-0.02'), Decimal('-0.01'), Decimal('0.01'), Decimal('0.02')]
    stress_results = StressTestingFramework.parallel_shift_stress_test(portfolio, base_curve, stress_scenarios)
    return {'portfolio_metrics': {'duration': portfolio_dur, 'convexity': portfolio_conv, 'yield': portfolio_yld, 'total_value': total_value}, 'risk_metrics': {'var_95': var_95, 'var_99': var_99}, 'stress_test_results': stress_results}

class SovereignCreditAnalysis:
    """Sovereign credit risk analysis and evaluation"""

    @staticmethod
    def sovereign_credit_factors() -> Dict[str, List[str]]:
        """Key factors for sovereign credit analysis"""
        return {'economic_factors': ['GDP growth rate', 'GDP per capita', 'Economic diversification', 'Competitiveness', 'Labor market flexibility', 'Monetary policy credibility'], 'fiscal_factors': ['Government debt/GDP ratio', 'Fiscal balance', 'Interest burden', 'Contingent liabilities', 'Fiscal flexibility', 'Revenue diversification'], 'external_factors': ['Current account balance', 'External debt', 'Foreign exchange reserves', 'Exchange rate regime', 'Export concentration', 'Capital market access'], 'political_institutional': ['Political stability', 'Institutional quality', 'Government effectiveness', 'Rule of law', 'Corruption control', 'Policy predictability']}

    @staticmethod
    def debt_sustainability_analysis(country_data: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Analyze sovereign debt sustainability"""
        debt_gdp = country_data.get('debt_to_gdp', Decimal('0.6'))
        gdp_growth = country_data.get('gdp_growth', Decimal('0.02'))
        interest_rate = country_data.get('avg_interest_rate', Decimal('0.03'))
        primary_balance = country_data.get('primary_balance_gdp', Decimal('0'))
        ValidationUtils.validate_percentage(debt_gdp, 'Debt-to-GDP ratio', allow_negative=False)
        ValidationUtils.validate_percentage(gdp_growth, 'GDP growth', allow_negative=True)
        ValidationUtils.validate_yield(interest_rate, 'Average interest rate')
        ValidationUtils.validate_percentage(primary_balance, 'Primary balance', allow_negative=True)
        real_interest_rate = interest_rate - gdp_growth
        debt_stabilizing_balance = -real_interest_rate * debt_gdp
        current_debt_change = real_interest_rate * debt_gdp - primary_balance
        projected_debt_gdp = debt_gdp
        for year in range(5):
            debt_change = real_interest_rate * projected_debt_gdp - primary_balance
            projected_debt_gdp += debt_change
        sustainability_score = SovereignCreditAnalysis._calculate_sustainability_score(debt_gdp, gdp_growth, interest_rate, primary_balance)
        return {'current_debt_gdp': debt_gdp, 'debt_stabilizing_balance': debt_stabilizing_balance, 'current_primary_balance': primary_balance, 'balance_gap': primary_balance - debt_stabilizing_balance, 'current_debt_change': current_debt_change, 'projected_debt_gdp_5y': projected_debt_gdp, 'sustainability_score': sustainability_score, 'fiscal_space': max(Decimal('0'), Decimal('0.9') - debt_gdp), 'sustainable': sustainability_score >= Decimal('0.7')}

    @staticmethod
    def _calculate_sustainability_score(debt_gdp: Decimal, gdp_growth: Decimal, interest_rate: Decimal, primary_balance: Decimal) -> Decimal:
        """Calculate composite sustainability score (0-1 scale)"""
        debt_score = max(Decimal('0'), Decimal('1') - debt_gdp / Decimal('1.5'))
        growth_score = min(Decimal('1'), max(Decimal('0'), gdp_growth * Decimal('10')))
        interest_score = max(Decimal('0'), Decimal('1') - interest_rate * Decimal('10'))
        balance_score = min(Decimal('1'), max(Decimal('0'), primary_balance * Decimal('20') + Decimal('0.5')))
        weights = [Decimal('0.3'), Decimal('0.25'), Decimal('0.25'), Decimal('0.2')]
        scores = [debt_score, growth_score, interest_score, balance_score]
        return sum((w * s for w, s in zip(weights, scores)))

    @staticmethod
    def sovereign_spread_analysis(country: str, benchmark_yield: Decimal, sovereign_yield: Decimal, factors: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Analyze sovereign credit spreads"""
        ValidationUtils.validate_yield(benchmark_yield, 'Benchmark yield')
        ValidationUtils.validate_yield(sovereign_yield, 'Sovereign yield')
        credit_spread = sovereign_yield - benchmark_yield
        spread_bps = credit_spread * Decimal('10000')
        base_spread = Decimal('0.001')
        gdp_factor = factors.get('gdp_growth', Decimal('0.02'))
        economic_contrib = max(Decimal('0'), (Decimal('0.02') - gdp_factor) * Decimal('0.5'))
        debt_gdp = factors.get('debt_gdp', Decimal('0.6'))
        fiscal_contrib = max(Decimal('0'), (debt_gdp - Decimal('0.6')) * Decimal('0.02'))
        current_account = factors.get('current_account_gdp', Decimal('0'))
        external_contrib = max(Decimal('0'), -current_account * Decimal('0.1'))
        political_score = factors.get('political_stability', Decimal('0.7'))
        political_contrib = max(Decimal('0'), (Decimal('0.7') - political_score) * Decimal('0.05'))
        theoretical_spread = base_spread + economic_contrib + fiscal_contrib + external_contrib + political_contrib
        return {'observed_spread': credit_spread, 'spread_bps': spread_bps, 'theoretical_spread': theoretical_spread, 'spread_difference': credit_spread - theoretical_spread, 'factor_contributions': {'base_spread': base_spread, 'economic_factor': economic_contrib, 'fiscal_factor': fiscal_contrib, 'external_factor': external_contrib, 'political_factor': political_contrib}, 'relative_value': 'cheap' if credit_spread > theoretical_spread else 'expensive'}

@staticmethod
def debt_sustainability_analysis(country_data: Dict[str, Decimal]) -> Dict[str, Decimal]:
    """Analyze sovereign debt sustainability"""
    debt_gdp = country_data.get('debt_to_gdp', Decimal('0.6'))
    gdp_growth = country_data.get('gdp_growth', Decimal('0.02'))
    interest_rate = country_data.get('avg_interest_rate', Decimal('0.03'))
    primary_balance = country_data.get('primary_balance_gdp', Decimal('0'))
    ValidationUtils.validate_percentage(debt_gdp, 'Debt-to-GDP ratio', allow_negative=False)
    ValidationUtils.validate_percentage(gdp_growth, 'GDP growth', allow_negative=True)
    ValidationUtils.validate_yield(interest_rate, 'Average interest rate')
    ValidationUtils.validate_percentage(primary_balance, 'Primary balance', allow_negative=True)
    real_interest_rate = interest_rate - gdp_growth
    debt_stabilizing_balance = -real_interest_rate * debt_gdp
    current_debt_change = real_interest_rate * debt_gdp - primary_balance
    projected_debt_gdp = debt_gdp
    for year in range(5):
        debt_change = real_interest_rate * projected_debt_gdp - primary_balance
        projected_debt_gdp += debt_change
    sustainability_score = SovereignCreditAnalysis._calculate_sustainability_score(debt_gdp, gdp_growth, interest_rate, primary_balance)
    return {'current_debt_gdp': debt_gdp, 'debt_stabilizing_balance': debt_stabilizing_balance, 'current_primary_balance': primary_balance, 'balance_gap': primary_balance - debt_stabilizing_balance, 'current_debt_change': current_debt_change, 'projected_debt_gdp_5y': projected_debt_gdp, 'sustainability_score': sustainability_score, 'fiscal_space': max(Decimal('0'), Decimal('0.9') - debt_gdp), 'sustainable': sustainability_score >= Decimal('0.7')}

@staticmethod
def sovereign_spread_analysis(country: str, benchmark_yield: Decimal, sovereign_yield: Decimal, factors: Dict[str, Decimal]) -> Dict[str, Decimal]:
    """Analyze sovereign credit spreads"""
    ValidationUtils.validate_yield(benchmark_yield, 'Benchmark yield')
    ValidationUtils.validate_yield(sovereign_yield, 'Sovereign yield')
    credit_spread = sovereign_yield - benchmark_yield
    spread_bps = credit_spread * Decimal('10000')
    base_spread = Decimal('0.001')
    gdp_factor = factors.get('gdp_growth', Decimal('0.02'))
    economic_contrib = max(Decimal('0'), (Decimal('0.02') - gdp_factor) * Decimal('0.5'))
    debt_gdp = factors.get('debt_gdp', Decimal('0.6'))
    fiscal_contrib = max(Decimal('0'), (debt_gdp - Decimal('0.6')) * Decimal('0.02'))
    current_account = factors.get('current_account_gdp', Decimal('0'))
    external_contrib = max(Decimal('0'), -current_account * Decimal('0.1'))
    political_score = factors.get('political_stability', Decimal('0.7'))
    political_contrib = max(Decimal('0'), (Decimal('0.7') - political_score) * Decimal('0.05'))
    theoretical_spread = base_spread + economic_contrib + fiscal_contrib + external_contrib + political_contrib
    return {'observed_spread': credit_spread, 'spread_bps': spread_bps, 'theoretical_spread': theoretical_spread, 'spread_difference': credit_spread - theoretical_spread, 'factor_contributions': {'base_spread': base_spread, 'economic_factor': economic_contrib, 'fiscal_factor': fiscal_contrib, 'external_factor': external_contrib, 'political_factor': political_contrib}, 'relative_value': 'cheap' if credit_spread > theoretical_spread else 'expensive'}

class MunicipalBondAnalysis:
    """Municipal bond analysis and evaluation"""

    @staticmethod
    def municipal_credit_factors() -> Dict[str, List[str]]:
        """Key factors for municipal credit analysis"""
        return {'economic_base': ['Economic diversity', 'Employment trends', 'Income levels', 'Population growth', 'Business environment', 'Tax base stability'], 'financial_performance': ['Operating performance', 'Debt burden', 'Liquidity position', 'Financial flexibility', 'Capital planning', 'Reserve levels'], 'debt_structure': ['Debt per capita', 'Debt service coverage', 'Direct vs overlapping debt', 'Variable rate exposure', 'Derivative usage', 'Refinancing risk'], 'governance_management': ['Management quality', 'Financial reporting', 'Budget practices', 'Transparency', 'Political environment', 'Stakeholder relations']}

    @staticmethod
    def go_bond_analysis(issuer_data: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Analyze General Obligation (GO) municipal bonds"""
        assessed_value = issuer_data.get('assessed_value', Decimal('1000000000'))
        population = issuer_data.get('population', Decimal('100000'))
        total_debt = issuer_data.get('total_debt', Decimal('50000000'))
        annual_debt_service = issuer_data.get('annual_debt_service', Decimal('5000000'))
        operating_revenues = issuer_data.get('operating_revenues', Decimal('100000000'))
        fund_balance = issuer_data.get('fund_balance', Decimal('20000000'))
        debt_per_capita = total_debt / population
        debt_to_assessed_value = total_debt / assessed_value
        debt_service_coverage = operating_revenues / annual_debt_service
        fund_balance_ratio = fund_balance / operating_revenues
        debt_burden_score = MunicipalBondAnalysis._score_debt_burden(debt_per_capita, debt_to_assessed_value)
        coverage_score = MunicipalBondAnalysis._score_coverage(debt_service_coverage)
        liquidity_score = MunicipalBondAnalysis._score_liquidity(fund_balance_ratio)
        overall_score = (debt_burden_score + coverage_score + liquidity_score) / Decimal('3')
        return {'debt_per_capita': debt_per_capita, 'debt_to_assessed_value_pct': debt_to_assessed_value * Decimal('100'), 'debt_service_coverage': debt_service_coverage, 'fund_balance_ratio_pct': fund_balance_ratio * Decimal('100'), 'credit_scores': {'debt_burden': debt_burden_score, 'coverage': coverage_score, 'liquidity': liquidity_score, 'overall': overall_score}, 'credit_quality': MunicipalBondAnalysis._interpret_score(overall_score)}

    @staticmethod
    def revenue_bond_analysis(project_data: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Analyze Revenue municipal bonds"""
        gross_revenues = project_data.get('gross_revenues', Decimal('50000000'))
        operating_expenses = project_data.get('operating_expenses', Decimal('30000000'))
        debt_service = project_data.get('debt_service', Decimal('15000000'))
        rate_covenant = project_data.get('rate_covenant', Decimal('1.25'))
        net_revenues = gross_revenues - operating_expenses
        debt_service_coverage = net_revenues / debt_service if debt_service > 0 else Decimal('999')
        additional_bonds_test = debt_service_coverage >= rate_covenant
        free_cash_flow = net_revenues - debt_service
        cash_flow_margin = free_cash_flow / gross_revenues if gross_revenues > 0 else Decimal('0')
        utilization_rate = project_data.get('utilization_rate', Decimal('0.8'))
        capacity_factor = project_data.get('capacity_factor', Decimal('0.9'))
        return {'gross_revenues': gross_revenues, 'net_revenues': net_revenues, 'debt_service_coverage': debt_service_coverage, 'rate_covenant': rate_covenant, 'covenant_compliance': additional_bonds_test, 'coverage_cushion': debt_service_coverage - rate_covenant, 'free_cash_flow': free_cash_flow, 'cash_flow_margin_pct': cash_flow_margin * Decimal('100'), 'utilization_rate_pct': utilization_rate * Decimal('100'), 'capacity_factor_pct': capacity_factor * Decimal('100'), 'project_viability': MunicipalBondAnalysis._assess_project_viability(debt_service_coverage, utilization_rate, capacity_factor)}

    @staticmethod
    def _score_debt_burden(debt_per_capita: Decimal, debt_to_av: Decimal) -> Decimal:
        """Score debt burden (0-1 scale)"""
        per_capita_score = max(Decimal('0'), Decimal('1') - debt_per_capita / Decimal('5000'))
        av_score = max(Decimal('0'), Decimal('1') - debt_to_av / Decimal('0.1'))
        return (per_capita_score + av_score) / Decimal('2')

    @staticmethod
    def _score_coverage(coverage_ratio: Decimal) -> Decimal:
        """Score debt service coverage"""
        if coverage_ratio >= Decimal('3'):
            return Decimal('1')
        elif coverage_ratio >= Decimal('2'):
            return Decimal('0.8')
        elif coverage_ratio >= Decimal('1.5'):
            return Decimal('0.6')
        elif coverage_ratio >= Decimal('1.2'):
            return Decimal('0.4')
        else:
            return Decimal('0.2')

    @staticmethod
    def _score_liquidity(fund_balance_ratio: Decimal) -> Decimal:
        """Score liquidity position"""
        if fund_balance_ratio >= Decimal('0.25'):
            return Decimal('1')
        elif fund_balance_ratio >= Decimal('0.15'):
            return Decimal('0.8')
        elif fund_balance_ratio >= Decimal('0.10'):
            return Decimal('0.6')
        elif fund_balance_ratio >= Decimal('0.05'):
            return Decimal('0.4')
        else:
            return Decimal('0.2')

    @staticmethod
    def _interpret_score(score: Decimal) -> str:
        """Interpret overall credit score"""
        if score >= Decimal('0.8'):
            return 'Strong'
        elif score >= Decimal('0.6'):
            return 'Good'
        elif score >= Decimal('0.4'):
            return 'Satisfactory'
        elif score >= Decimal('0.2'):
            return 'Weak'
        else:
            return 'Distressed'

    @staticmethod
    def _assess_project_viability(coverage: Decimal, utilization: Decimal, capacity: Decimal) -> str:
        """Assess revenue bond project viability"""
        score = (coverage / Decimal('2') + utilization + capacity) / Decimal('3')
        if score >= Decimal('0.8'):
            return 'Highly Viable'
        elif score >= Decimal('0.6'):
            return 'Viable'
        elif score >= Decimal('0.4'):
            return 'Marginal'
        else:
            return 'Distressed'

@staticmethod
def go_bond_analysis(issuer_data: Dict[str, Decimal]) -> Dict[str, Decimal]:
    """Analyze General Obligation (GO) municipal bonds"""
    assessed_value = issuer_data.get('assessed_value', Decimal('1000000000'))
    population = issuer_data.get('population', Decimal('100000'))
    total_debt = issuer_data.get('total_debt', Decimal('50000000'))
    annual_debt_service = issuer_data.get('annual_debt_service', Decimal('5000000'))
    operating_revenues = issuer_data.get('operating_revenues', Decimal('100000000'))
    fund_balance = issuer_data.get('fund_balance', Decimal('20000000'))
    debt_per_capita = total_debt / population
    debt_to_assessed_value = total_debt / assessed_value
    debt_service_coverage = operating_revenues / annual_debt_service
    fund_balance_ratio = fund_balance / operating_revenues
    debt_burden_score = MunicipalBondAnalysis._score_debt_burden(debt_per_capita, debt_to_assessed_value)
    coverage_score = MunicipalBondAnalysis._score_coverage(debt_service_coverage)
    liquidity_score = MunicipalBondAnalysis._score_liquidity(fund_balance_ratio)
    overall_score = (debt_burden_score + coverage_score + liquidity_score) / Decimal('3')
    return {'debt_per_capita': debt_per_capita, 'debt_to_assessed_value_pct': debt_to_assessed_value * Decimal('100'), 'debt_service_coverage': debt_service_coverage, 'fund_balance_ratio_pct': fund_balance_ratio * Decimal('100'), 'credit_scores': {'debt_burden': debt_burden_score, 'coverage': coverage_score, 'liquidity': liquidity_score, 'overall': overall_score}, 'credit_quality': MunicipalBondAnalysis._interpret_score(overall_score)}

@staticmethod
def revenue_bond_analysis(project_data: Dict[str, Decimal]) -> Dict[str, Decimal]:
    """Analyze Revenue municipal bonds"""
    gross_revenues = project_data.get('gross_revenues', Decimal('50000000'))
    operating_expenses = project_data.get('operating_expenses', Decimal('30000000'))
    debt_service = project_data.get('debt_service', Decimal('15000000'))
    rate_covenant = project_data.get('rate_covenant', Decimal('1.25'))
    net_revenues = gross_revenues - operating_expenses
    debt_service_coverage = net_revenues / debt_service if debt_service > 0 else Decimal('999')
    additional_bonds_test = debt_service_coverage >= rate_covenant
    free_cash_flow = net_revenues - debt_service
    cash_flow_margin = free_cash_flow / gross_revenues if gross_revenues > 0 else Decimal('0')
    utilization_rate = project_data.get('utilization_rate', Decimal('0.8'))
    capacity_factor = project_data.get('capacity_factor', Decimal('0.9'))
    return {'gross_revenues': gross_revenues, 'net_revenues': net_revenues, 'debt_service_coverage': debt_service_coverage, 'rate_covenant': rate_covenant, 'covenant_compliance': additional_bonds_test, 'coverage_cushion': debt_service_coverage - rate_covenant, 'free_cash_flow': free_cash_flow, 'cash_flow_margin_pct': cash_flow_margin * Decimal('100'), 'utilization_rate_pct': utilization_rate * Decimal('100'), 'capacity_factor_pct': capacity_factor * Decimal('100'), 'project_viability': MunicipalBondAnalysis._assess_project_viability(debt_service_coverage, utilization_rate, capacity_factor)}

@staticmethod
def _score_debt_burden(debt_per_capita: Decimal, debt_to_av: Decimal) -> Decimal:
    """Score debt burden (0-1 scale)"""
    per_capita_score = max(Decimal('0'), Decimal('1') - debt_per_capita / Decimal('5000'))
    av_score = max(Decimal('0'), Decimal('1') - debt_to_av / Decimal('0.1'))
    return (per_capita_score + av_score) / Decimal('2')

@staticmethod
def _score_coverage(coverage_ratio: Decimal) -> Decimal:
    """Score debt service coverage"""
    if coverage_ratio >= Decimal('3'):
        return Decimal('1')
    elif coverage_ratio >= Decimal('2'):
        return Decimal('0.8')
    elif coverage_ratio >= Decimal('1.5'):
        return Decimal('0.6')
    elif coverage_ratio >= Decimal('1.2'):
        return Decimal('0.4')
    else:
        return Decimal('0.2')

@staticmethod
def _score_liquidity(fund_balance_ratio: Decimal) -> Decimal:
    """Score liquidity position"""
    if fund_balance_ratio >= Decimal('0.25'):
        return Decimal('1')
    elif fund_balance_ratio >= Decimal('0.15'):
        return Decimal('0.8')
    elif fund_balance_ratio >= Decimal('0.10'):
        return Decimal('0.6')
    elif fund_balance_ratio >= Decimal('0.05'):
        return Decimal('0.4')
    else:
        return Decimal('0.2')

@staticmethod
def _interpret_score(score: Decimal) -> str:
    """Interpret overall credit score"""
    if score >= Decimal('0.8'):
        return 'Strong'
    elif score >= Decimal('0.6'):
        return 'Good'
    elif score >= Decimal('0.4'):
        return 'Satisfactory'
    elif score >= Decimal('0.2'):
        return 'Weak'
    else:
        return 'Distressed'

@staticmethod
def _assess_project_viability(coverage: Decimal, utilization: Decimal, capacity: Decimal) -> str:
    """Assess revenue bond project viability"""
    score = (coverage / Decimal('2') + utilization + capacity) / Decimal('3')
    if score >= Decimal('0.8'):
        return 'Highly Viable'
    elif score >= Decimal('0.6'):
        return 'Viable'
    elif score >= Decimal('0.4'):
        return 'Marginal'
    else:
        return 'Distressed'

class AgencyDebtAnalysis:
    """Government agency and GSE debt analysis"""

    @staticmethod
    def agency_types() -> Dict[str, Dict[str, str]]:
        """Classification of government agencies and GSEs"""
        return {'federal_agencies': {'description': 'Direct obligations of US government agencies', 'credit_support': 'Full faith and credit backing', 'examples': 'GNMA, SBA, Tennessee Valley Authority'}, 'government_sponsored_enterprises': {'description': 'Privately-owned, government-chartered entities', 'credit_support': 'Implied government support (historically)', 'examples': 'Fannie Mae, Freddie Mac, Federal Home Loan Banks'}, 'supranational_agencies': {'description': 'International organizations', 'credit_support': 'Member country support', 'examples': 'World Bank, Asian Development Bank, European Investment Bank'}}

    @staticmethod
    def gse_credit_analysis(gse_data: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Analyze Government Sponsored Enterprise credit quality"""
        tier1_capital = gse_data.get('tier1_capital', Decimal('50000000000'))
        risk_weighted_assets = gse_data.get('risk_weighted_assets', Decimal('500000000000'))
        tier1_ratio = tier1_capital / risk_weighted_assets
        total_assets = gse_data.get('total_assets', Decimal('1000000000000'))
        non_performing_assets = gse_data.get('non_performing_assets', Decimal('5000000000'))
        npa_ratio = non_performing_assets / total_assets
        net_income = gse_data.get('net_income', Decimal('10000000000'))
        average_assets = gse_data.get('average_assets', total_assets)
        roa = net_income / average_assets
        liquid_assets = gse_data.get('liquid_assets', Decimal('100000000000'))
        short_term_debt = gse_data.get('short_term_debt', Decimal('200000000000'))
        liquidity_ratio = liquid_assets / short_term_debt
        systemic_importance = gse_data.get('market_share', Decimal('0.3'))
        government_ties = gse_data.get('government_charter_score', Decimal('0.8'))
        financial_strength = AgencyDebtAnalysis._assess_financial_strength(tier1_ratio, npa_ratio, roa, liquidity_ratio)
        government_support_score = (systemic_importance + government_ties) / Decimal('2')
        return {'capital_adequacy': {'tier1_ratio_pct': tier1_ratio * Decimal('100'), 'regulatory_minimum': Decimal('4'), 'well_capitalized': tier1_ratio >= Decimal('0.06')}, 'asset_quality': {'npa_ratio_pct': npa_ratio * Decimal('100'), 'asset_quality_score': max(Decimal('0'), Decimal('1') - npa_ratio * Decimal('20'))}, 'profitability': {'roa_pct': roa * Decimal('100'), 'profitability_score': min(Decimal('1'), max(Decimal('0'), roa * Decimal('100')))}, 'liquidity': {'liquidity_ratio': liquidity_ratio, 'liquidity_adequate': liquidity_ratio >= Decimal('0.5')}, 'government_support': {'support_score': government_support_score, 'systemic_importance': systemic_importance, 'government_ties': government_ties}, 'overall_assessment': {'financial_strength': financial_strength, 'government_support': government_support_score, 'combined_rating': AgencyDebtAnalysis._derive_rating(financial_strength, government_support_score)}}

    @staticmethod
    def _assess_financial_strength(tier1_ratio: Decimal, npa_ratio: Decimal, roa: Decimal, liquidity_ratio: Decimal) -> Decimal:
        """Assess standalone financial strength (0-1 scale)"""
        capital_score = min(Decimal('1'), tier1_ratio / Decimal('0.08'))
        asset_score = max(Decimal('0'), Decimal('1') - npa_ratio * Decimal('50'))
        profit_score = min(Decimal('1'), max(Decimal('0'), roa * Decimal('100')))
        liquidity_score = min(Decimal('1'), liquidity_ratio / Decimal('1'))
        weights = [Decimal('0.3'), Decimal('0.3'), Decimal('0.2'), Decimal('0.2')]
        scores = [capital_score, asset_score, profit_score, liquidity_score]
        return sum((w * s for w, s in zip(weights, scores)))

    @staticmethod
    def _derive_rating(financial_strength: Decimal, government_support: Decimal) -> str:
        """Derive credit rating from financial strength and government support"""
        combined_score = financial_strength * Decimal('0.4') + government_support * Decimal('0.6')
        if combined_score >= Decimal('0.9'):
            return 'AAA'
        elif combined_score >= Decimal('0.8'):
            return 'AA'
        elif combined_score >= Decimal('0.7'):
            return 'A'
        elif combined_score >= Decimal('0.6'):
            return 'BBB'
        elif combined_score >= Decimal('0.5'):
            return 'BB'
        else:
            return 'B'

@staticmethod
def _derive_rating(financial_strength: Decimal, government_support: Decimal) -> str:
    """Derive credit rating from financial strength and government support"""
    combined_score = financial_strength * Decimal('0.4') + government_support * Decimal('0.6')
    if combined_score >= Decimal('0.9'):
        return 'AAA'
    elif combined_score >= Decimal('0.8'):
        return 'AA'
    elif combined_score >= Decimal('0.7'):
        return 'A'
    elif combined_score >= Decimal('0.6'):
        return 'BBB'
    elif combined_score >= Decimal('0.5'):
        return 'BB'
    else:
        return 'B'

class InflationLinkedBonds:
    """Inflation-linked government bond analysis"""

    @staticmethod
    def tips_analysis(principal: Decimal, coupon_rate: Decimal, inflation_rate: Decimal, years_remaining: Decimal) -> Dict[str, Decimal]:
        """Analyze Treasury Inflation-Protected Securities (TIPS)"""
        ValidationUtils.validate_positive(principal, 'Principal')
        ValidationUtils.validate_positive(coupon_rate, 'Coupon rate')
        ValidationUtils.validate_percentage(inflation_rate, 'Inflation rate', allow_negative=True)
        ValidationUtils.validate_positive(years_remaining, 'Years remaining')
        inflation_factor = (Decimal('1') + inflation_rate) ** years_remaining
        adjusted_principal = principal * inflation_factor
        annual_coupon = adjusted_principal * coupon_rate
        nominal_yield = coupon_rate + inflation_rate
        real_yield = coupon_rate
        nominal_bond_yield = Decimal('0.05')
        breakeven_inflation = nominal_bond_yield - real_yield
        return {'original_principal': principal, 'inflation_adjusted_principal': adjusted_principal, 'inflation_adjustment_factor': inflation_factor, 'annual_coupon_payment': annual_coupon, 'real_yield': real_yield, 'nominal_yield_equivalent': nominal_yield, 'breakeven_inflation_rate': breakeven_inflation, 'inflation_protection': inflation_rate - breakeven_inflation, 'attractive_vs_nominal': inflation_rate > breakeven_inflation}

    @staticmethod
    def inflation_swap_analysis(notional: Decimal, fixed_rate: Decimal, expected_inflation: Decimal, tenor: Decimal) -> Dict[str, Decimal]:
        """Analyze inflation swap for hedging purposes"""
        ValidationUtils.validate_positive(notional, 'Notional')
        ValidationUtils.validate_yield(fixed_rate, 'Fixed rate')
        ValidationUtils.validate_percentage(expected_inflation, 'Expected inflation', allow_negative=True)
        ValidationUtils.validate_positive(tenor, 'Tenor')
        fixed_leg_pv = notional * fixed_rate * tenor
        floating_leg_pv = notional * expected_inflation * tenor
        swap_value = floating_leg_pv - fixed_leg_pv
        breakeven = fixed_rate
        return {'notional_amount': notional, 'fixed_rate': fixed_rate, 'expected_inflation': expected_inflation, 'fixed_leg_pv': fixed_leg_pv, 'floating_leg_pv': floating_leg_pv, 'swap_value_to_payer': swap_value, 'breakeven_inflation': breakeven, 'inflation_expectation_vs_breakeven': expected_inflation - breakeven}

@staticmethod
def tips_analysis(principal: Decimal, coupon_rate: Decimal, inflation_rate: Decimal, years_remaining: Decimal) -> Dict[str, Decimal]:
    """Analyze Treasury Inflation-Protected Securities (TIPS)"""
    ValidationUtils.validate_positive(principal, 'Principal')
    ValidationUtils.validate_positive(coupon_rate, 'Coupon rate')
    ValidationUtils.validate_percentage(inflation_rate, 'Inflation rate', allow_negative=True)
    ValidationUtils.validate_positive(years_remaining, 'Years remaining')
    inflation_factor = (Decimal('1') + inflation_rate) ** years_remaining
    adjusted_principal = principal * inflation_factor
    annual_coupon = adjusted_principal * coupon_rate
    nominal_yield = coupon_rate + inflation_rate
    real_yield = coupon_rate
    nominal_bond_yield = Decimal('0.05')
    breakeven_inflation = nominal_bond_yield - real_yield
    return {'original_principal': principal, 'inflation_adjusted_principal': adjusted_principal, 'inflation_adjustment_factor': inflation_factor, 'annual_coupon_payment': annual_coupon, 'real_yield': real_yield, 'nominal_yield_equivalent': nominal_yield, 'breakeven_inflation_rate': breakeven_inflation, 'inflation_protection': inflation_rate - breakeven_inflation, 'attractive_vs_nominal': inflation_rate > breakeven_inflation}

@staticmethod
def inflation_swap_analysis(notional: Decimal, fixed_rate: Decimal, expected_inflation: Decimal, tenor: Decimal) -> Dict[str, Decimal]:
    """Analyze inflation swap for hedging purposes"""
    ValidationUtils.validate_positive(notional, 'Notional')
    ValidationUtils.validate_yield(fixed_rate, 'Fixed rate')
    ValidationUtils.validate_percentage(expected_inflation, 'Expected inflation', allow_negative=True)
    ValidationUtils.validate_positive(tenor, 'Tenor')
    fixed_leg_pv = notional * fixed_rate * tenor
    floating_leg_pv = notional * expected_inflation * tenor
    swap_value = floating_leg_pv - fixed_leg_pv
    breakeven = fixed_rate
    return {'notional_amount': notional, 'fixed_rate': fixed_rate, 'expected_inflation': expected_inflation, 'fixed_leg_pv': fixed_leg_pv, 'floating_leg_pv': floating_leg_pv, 'swap_value_to_payer': swap_value, 'breakeven_inflation': breakeven, 'inflation_expectation_vs_breakeven': expected_inflation - breakeven}

def municipal_portfolio_analysis(portfolio: Portfolio, muni_data: Dict[str, Dict[str, Decimal]]) -> Dict[str, any]:
    """Analyze municipal bond portfolio"""
    total_exposure = Decimal('0')
    go_exposure = Decimal('0')
    revenue_exposure = Decimal('0')
    issuer_analysis = {}
    for bond, quantity in portfolio.holdings:
        if bond.sector == 'Municipal':
            exposure = bond.face_value * quantity
            total_exposure += exposure
            issuer = bond.issuer_name
            if issuer in muni_data:
                issuer_data = muni_data[issuer]
                if issuer_data.get('bond_type') == 'GO':
                    go_exposure += exposure
                    analysis = MunicipalBondAnalysis.go_bond_analysis(issuer_data)
                else:
                    revenue_exposure += exposure
                    analysis = MunicipalBondAnalysis.revenue_bond_analysis(issuer_data)
                issuer_analysis[issuer] = {'exposure': exposure, 'analysis': analysis, 'weight': exposure / total_exposure if total_exposure > 0 else Decimal('0')}
    return {'portfolio_composition': {'total_municipal_exposure': total_exposure, 'go_bond_exposure': go_exposure, 'revenue_bond_exposure': revenue_exposure, 'go_percentage': go_exposure / total_exposure if total_exposure > 0 else Decimal('0'), 'revenue_percentage': revenue_exposure / total_exposure if total_exposure > 0 else Decimal('0')}, 'issuer_analysis': issuer_analysis, 'portfolio_quality_metrics': {'weighted_avg_coverage': sum((data['analysis'].get('debt_service_coverage', Decimal('1')) * data['weight'] for data in issuer_analysis.values())), 'number_of_issuers': len(issuer_analysis), 'concentration_risk': max((data['weight'] for data in issuer_analysis.values())) if issuer_analysis else Decimal('0')}}

class BondValuation:
    """Basic bond valuation methods"""

    @staticmethod
    @cache_calculation
    def present_value(bond: Bond, discount_rate: Decimal, settlement_date: Optional[date]=None) -> Decimal:
        """Calculate present value of bond using single discount rate"""
        ValidationUtils.validate_yield(discount_rate, 'Discount rate')
        if settlement_date is None:
            settlement_date = date.today()
        bond_instrument = create_bond_instrument(bond)
        cash_flows = bond_instrument.generate_cash_flows(settlement_date)
        total_pv = Decimal('0')
        for cf in cash_flows:
            time_to_payment = DateUtils.calculate_day_count_fraction(settlement_date, cf.date, bond.day_count_convention)
            pv = MathUtils.present_value(cf.amount, discount_rate, time_to_payment)
            total_pv += pv
        return total_pv

    @staticmethod
    def present_value_with_curve(bond: Bond, spot_curve: SpotCurve, settlement_date: Optional[date]=None) -> Decimal:
        """Calculate present value using spot rate curve"""
        if settlement_date is None:
            settlement_date = date.today()
        bond_instrument = create_bond_instrument(bond)
        cash_flows = bond_instrument.generate_cash_flows(settlement_date)
        total_pv = Decimal('0')
        for cf in cash_flows:
            time_to_payment = DateUtils.calculate_day_count_fraction(settlement_date, cf.date, bond.day_count_convention)
            spot_rate = spot_curve.get_rate(time_to_payment)
            pv = MathUtils.present_value(cf.amount, spot_rate, time_to_payment)
            total_pv += pv
        return total_pv

    @staticmethod
    def yield_to_maturity(bond: Bond, price: Decimal, settlement_date: Optional[date]=None) -> Decimal:
        """Calculate yield to maturity using iterative methods"""
        ValidationUtils.validate_price(price, 'Bond price')
        if settlement_date is None:
            settlement_date = date.today()

        def price_function(ytm: Decimal) -> Decimal:
            pv = BondValuation.present_value(bond, ytm, settlement_date)
            return pv - price

        def price_derivative(ytm: Decimal) -> Decimal:
            delta = Decimal('0.0001')
            pv1 = BondValuation.present_value(bond, ytm - delta, settlement_date)
            pv2 = BondValuation.present_value(bond, ytm + delta, settlement_date)
            return (pv2 - pv1) / (Decimal('2') * delta)
        if bond.coupon_rate > 0:
            initial_guess = bond.coupon_rate
        else:
            time_to_maturity = DateUtils.calculate_day_count_fraction(settlement_date, bond.maturity_date, bond.day_count_convention)
            initial_guess = (bond.face_value / price) ** (Decimal('1') / time_to_maturity) - Decimal('1')
        try:
            ytm = MathUtils.newton_raphson(price_function, price_derivative, initial_guess)
            ValidationUtils.validate_yield(ytm, 'Yield to maturity')
            return ytm
        except:
            try:
                return MathUtils.bisection_method(price_function, Decimal('0.001'), Decimal('0.50'))
            except:
                return MathUtils.brent_method(price_function, Decimal('0.001'), Decimal('0.50'))

    @staticmethod
    def current_yield(bond: Bond, price: Decimal) -> Decimal:
        """Calculate current yield (annual coupon / price)"""
        ValidationUtils.validate_price(price, 'Bond price')
        if bond.is_zero_coupon:
            return Decimal('0')
        annual_coupon = bond.face_value * bond.coupon_rate
        return annual_coupon / price

    @staticmethod
    def accrued_interest(bond: Bond, settlement_date: date) -> Decimal:
        """Calculate accrued interest"""
        bond_instrument = create_bond_instrument(bond)
        return bond_instrument.accrued_interest(settlement_date)

    @staticmethod
    def clean_price(dirty_price: Decimal, accrued: Decimal) -> Decimal:
        """Calculate clean price from dirty price"""
        return dirty_price - accrued

    @staticmethod
    def dirty_price(clean_price: Decimal, accrued: Decimal) -> Decimal:
        """Calculate dirty price from clean price"""
        return clean_price + accrued

@staticmethod
@cache_calculation
def present_value(bond: Bond, discount_rate: Decimal, settlement_date: Optional[date]=None) -> Decimal:
    """Calculate present value of bond using single discount rate"""
    ValidationUtils.validate_yield(discount_rate, 'Discount rate')
    if settlement_date is None:
        settlement_date = date.today()
    bond_instrument = create_bond_instrument(bond)
    cash_flows = bond_instrument.generate_cash_flows(settlement_date)
    total_pv = Decimal('0')
    for cf in cash_flows:
        time_to_payment = DateUtils.calculate_day_count_fraction(settlement_date, cf.date, bond.day_count_convention)
        pv = MathUtils.present_value(cf.amount, discount_rate, time_to_payment)
        total_pv += pv
    return total_pv

@staticmethod
def present_value_with_curve(bond: Bond, spot_curve: SpotCurve, settlement_date: Optional[date]=None) -> Decimal:
    """Calculate present value using spot rate curve"""
    if settlement_date is None:
        settlement_date = date.today()
    bond_instrument = create_bond_instrument(bond)
    cash_flows = bond_instrument.generate_cash_flows(settlement_date)
    total_pv = Decimal('0')
    for cf in cash_flows:
        time_to_payment = DateUtils.calculate_day_count_fraction(settlement_date, cf.date, bond.day_count_convention)
        spot_rate = spot_curve.get_rate(time_to_payment)
        pv = MathUtils.present_value(cf.amount, spot_rate, time_to_payment)
        total_pv += pv
    return total_pv

@staticmethod
def yield_to_maturity(bond: Bond, price: Decimal, settlement_date: Optional[date]=None) -> Decimal:
    """Calculate yield to maturity using iterative methods"""
    ValidationUtils.validate_price(price, 'Bond price')
    if settlement_date is None:
        settlement_date = date.today()

    def price_function(ytm: Decimal) -> Decimal:
        pv = BondValuation.present_value(bond, ytm, settlement_date)
        return pv - price

    def price_derivative(ytm: Decimal) -> Decimal:
        delta = Decimal('0.0001')
        pv1 = BondValuation.present_value(bond, ytm - delta, settlement_date)
        pv2 = BondValuation.present_value(bond, ytm + delta, settlement_date)
        return (pv2 - pv1) / (Decimal('2') * delta)
    if bond.coupon_rate > 0:
        initial_guess = bond.coupon_rate
    else:
        time_to_maturity = DateUtils.calculate_day_count_fraction(settlement_date, bond.maturity_date, bond.day_count_convention)
        initial_guess = (bond.face_value / price) ** (Decimal('1') / time_to_maturity) - Decimal('1')
    try:
        ytm = MathUtils.newton_raphson(price_function, price_derivative, initial_guess)
        ValidationUtils.validate_yield(ytm, 'Yield to maturity')
        return ytm
    except:
        try:
            return MathUtils.bisection_method(price_function, Decimal('0.001'), Decimal('0.50'))
        except:
            return MathUtils.brent_method(price_function, Decimal('0.001'), Decimal('0.50'))

def price_function(ytm: Decimal) -> Decimal:
    pv = BondValuation.present_value(bond, ytm, settlement_date)
    return pv - price

def price_derivative(ytm: Decimal) -> Decimal:
    delta = Decimal('0.0001')
    pv1 = BondValuation.present_value(bond, ytm - delta, settlement_date)
    pv2 = BondValuation.present_value(bond, ytm + delta, settlement_date)
    return (pv2 - pv1) / (Decimal('2') * delta)

@staticmethod
def current_yield(bond: Bond, price: Decimal) -> Decimal:
    """Calculate current yield (annual coupon / price)"""
    ValidationUtils.validate_price(price, 'Bond price')
    if bond.is_zero_coupon:
        return Decimal('0')
    annual_coupon = bond.face_value * bond.coupon_rate
    return annual_coupon / price

@staticmethod
def accrued_interest(bond: Bond, settlement_date: date) -> Decimal:
    """Calculate accrued interest"""
    bond_instrument = create_bond_instrument(bond)
    return bond_instrument.accrued_interest(settlement_date)

class ArbitrageFreeValuation:
    """Arbitrage-free valuation using binomial trees and Monte Carlo"""

    @staticmethod
    def binomial_tree_value(bond: Bond, spot_curve: SpotCurve, volatility: Decimal, steps: int=100) -> Decimal:
        """Value bond using binomial interest rate tree"""
        ValidationUtils.validate_positive(volatility, 'Volatility')
        ValidationUtils.validate_positive(Decimal(str(steps)), 'Steps')
        time_to_maturity = DateUtils.calculate_day_count_fraction(date.today(), bond.maturity_date, bond.day_count_convention)
        dt = time_to_maturity / Decimal(str(steps))
        rate_tree = ArbitrageFreeValuation._build_rate_tree(spot_curve, volatility, steps, dt)
        bond_instrument = create_bond_instrument(bond)
        cash_flows = bond_instrument.generate_cash_flows()
        return ArbitrageFreeValuation._backward_induction(rate_tree, cash_flows, bond, dt, steps)

    @staticmethod
    def _build_rate_tree(spot_curve: SpotCurve, volatility: Decimal, steps: int, dt: Decimal) -> List[List[Decimal]]:
        """Build binomial interest rate tree"""
        tree = []
        r0 = spot_curve.get_rate(dt)
        u = Decimal(str(2.71828182845905)) ** (volatility * dt ** Decimal('0.5'))
        d = Decimal('1') / u
        for i in range(steps + 1):
            level = []
            for j in range(i + 1):
                rate = r0 * u ** Decimal(str(j)) * d ** Decimal(str(i - j))
                level.append(rate)
            tree.append(level)
        return tree

    @staticmethod
    def _backward_induction(rate_tree: List[List[Decimal]], cash_flows: List[CashFlow], bond: Bond, dt: Decimal, steps: int) -> Decimal:
        """Perform backward induction on the tree"""
        cf_map = {}
        for cf in cash_flows:
            time_to_cf = DateUtils.calculate_day_count_fraction(date.today(), cf.date, bond.day_count_convention)
            step = int(time_to_cf / dt)
            if step <= steps:
                cf_map[step] = cf_map.get(step, Decimal('0')) + cf.amount
        values = [bond.face_value] * (steps + 1)
        for i in range(steps - 1, -1, -1):
            new_values = []
            for j in range(i + 1):
                up_value = values[j + 1] if j + 1 < len(values) else bond.face_value
                down_value = values[j] if j < len(values) else bond.face_value
                expected_value = (up_value + down_value) / Decimal('2')
                discount_rate = rate_tree[i][j]
                discounted_value = expected_value / (Decimal('1') + discount_rate * dt)
                if i in cf_map:
                    discounted_value += cf_map[i]
                new_values.append(discounted_value)
            values = new_values
        return values[0] if values else bond.face_value

    @staticmethod
    def monte_carlo_value(bond: Bond, spot_curve: SpotCurve, volatility: Decimal, paths: int=10000, steps: int=252) -> Tuple[Decimal, Decimal]:
        """Value bond using Monte Carlo simulation"""
        ValidationUtils.validate_positive(volatility, 'Volatility')
        ValidationUtils.validate_positive(Decimal(str(paths)), 'Paths')
        time_to_maturity = DateUtils.calculate_day_count_fraction(date.today(), bond.maturity_date, bond.day_count_convention)
        dt = time_to_maturity / Decimal(str(steps))
        bond_instrument = create_bond_instrument(bond)
        cash_flows = bond_instrument.generate_cash_flows()
        path_values = []
        for _ in range(paths):
            rate_path = ArbitrageFreeValuation._generate_rate_path(spot_curve, volatility, steps, dt)
            path_value = ArbitrageFreeValuation._value_along_path(cash_flows, rate_path, bond, dt)
            path_values.append(path_value)
        mean_value = sum(path_values) / Decimal(str(len(path_values)))
        variance = sum(((v - mean_value) ** 2 for v in path_values)) / Decimal(str(len(path_values) - 1))
        std_error = (variance / Decimal(str(len(path_values)))) ** Decimal('0.5')
        return (mean_value, std_error)

    @staticmethod
    def _generate_rate_path(spot_curve: SpotCurve, volatility: Decimal, steps: int, dt: Decimal) -> List[Decimal]:
        """Generate single interest rate path using Vasicek model"""
        path = []
        r = spot_curve.get_rate(dt)
        kappa = Decimal('0.1')
        theta = spot_curve.get_rate(Decimal('10'))
        for _ in range(steps):
            drift = kappa * (theta - r) * dt
            shock = volatility * dt ** Decimal('0.5') * Decimal(str(random.gauss(0, 1)))
            r = r + drift + shock
            r = max(r, Decimal('0.0001'))
            path.append(r)
        return path

    @staticmethod
    def _value_along_path(cash_flows: List[CashFlow], rate_path: List[Decimal], bond: Bond, dt: Decimal) -> Decimal:
        """Value bond along specific rate path"""
        total_value = Decimal('0')
        for cf in cash_flows:
            time_to_cf = DateUtils.calculate_day_count_fraction(date.today(), cf.date, bond.day_count_convention)
            step = min(int(time_to_cf / dt), len(rate_path) - 1)
            discount_rate = rate_path[step]
            pv = MathUtils.present_value(cf.amount, discount_rate, time_to_cf)
            total_value += pv
        return total_value

@staticmethod
def binomial_tree_value(bond: Bond, spot_curve: SpotCurve, volatility: Decimal, steps: int=100) -> Decimal:
    """Value bond using binomial interest rate tree"""
    ValidationUtils.validate_positive(volatility, 'Volatility')
    ValidationUtils.validate_positive(Decimal(str(steps)), 'Steps')
    time_to_maturity = DateUtils.calculate_day_count_fraction(date.today(), bond.maturity_date, bond.day_count_convention)
    dt = time_to_maturity / Decimal(str(steps))
    rate_tree = ArbitrageFreeValuation._build_rate_tree(spot_curve, volatility, steps, dt)
    bond_instrument = create_bond_instrument(bond)
    cash_flows = bond_instrument.generate_cash_flows()
    return ArbitrageFreeValuation._backward_induction(rate_tree, cash_flows, bond, dt, steps)

@staticmethod
def _build_rate_tree(spot_curve: SpotCurve, volatility: Decimal, steps: int, dt: Decimal) -> List[List[Decimal]]:
    """Build binomial interest rate tree"""
    tree = []
    r0 = spot_curve.get_rate(dt)
    u = Decimal(str(2.71828182845905)) ** (volatility * dt ** Decimal('0.5'))
    d = Decimal('1') / u
    for i in range(steps + 1):
        level = []
        for j in range(i + 1):
            rate = r0 * u ** Decimal(str(j)) * d ** Decimal(str(i - j))
            level.append(rate)
        tree.append(level)
    return tree

@staticmethod
def _backward_induction(rate_tree: List[List[Decimal]], cash_flows: List[CashFlow], bond: Bond, dt: Decimal, steps: int) -> Decimal:
    """Perform backward induction on the tree"""
    cf_map = {}
    for cf in cash_flows:
        time_to_cf = DateUtils.calculate_day_count_fraction(date.today(), cf.date, bond.day_count_convention)
        step = int(time_to_cf / dt)
        if step <= steps:
            cf_map[step] = cf_map.get(step, Decimal('0')) + cf.amount
    values = [bond.face_value] * (steps + 1)
    for i in range(steps - 1, -1, -1):
        new_values = []
        for j in range(i + 1):
            up_value = values[j + 1] if j + 1 < len(values) else bond.face_value
            down_value = values[j] if j < len(values) else bond.face_value
            expected_value = (up_value + down_value) / Decimal('2')
            discount_rate = rate_tree[i][j]
            discounted_value = expected_value / (Decimal('1') + discount_rate * dt)
            if i in cf_map:
                discounted_value += cf_map[i]
            new_values.append(discounted_value)
        values = new_values
    return values[0] if values else bond.face_value

@staticmethod
def monte_carlo_value(bond: Bond, spot_curve: SpotCurve, volatility: Decimal, paths: int=10000, steps: int=252) -> Tuple[Decimal, Decimal]:
    """Value bond using Monte Carlo simulation"""
    ValidationUtils.validate_positive(volatility, 'Volatility')
    ValidationUtils.validate_positive(Decimal(str(paths)), 'Paths')
    time_to_maturity = DateUtils.calculate_day_count_fraction(date.today(), bond.maturity_date, bond.day_count_convention)
    dt = time_to_maturity / Decimal(str(steps))
    bond_instrument = create_bond_instrument(bond)
    cash_flows = bond_instrument.generate_cash_flows()
    path_values = []
    for _ in range(paths):
        rate_path = ArbitrageFreeValuation._generate_rate_path(spot_curve, volatility, steps, dt)
        path_value = ArbitrageFreeValuation._value_along_path(cash_flows, rate_path, bond, dt)
        path_values.append(path_value)
    mean_value = sum(path_values) / Decimal(str(len(path_values)))
    variance = sum(((v - mean_value) ** 2 for v in path_values)) / Decimal(str(len(path_values) - 1))
    std_error = (variance / Decimal(str(len(path_values)))) ** Decimal('0.5')
    return (mean_value, std_error)

@staticmethod
def _generate_rate_path(spot_curve: SpotCurve, volatility: Decimal, steps: int, dt: Decimal) -> List[Decimal]:
    """Generate single interest rate path using Vasicek model"""
    path = []
    r = spot_curve.get_rate(dt)
    kappa = Decimal('0.1')
    theta = spot_curve.get_rate(Decimal('10'))
    for _ in range(steps):
        drift = kappa * (theta - r) * dt
        shock = volatility * dt ** Decimal('0.5') * Decimal(str(random.gauss(0, 1)))
        r = r + drift + shock
        r = max(r, Decimal('0.0001'))
        path.append(r)
    return path

@staticmethod
def _value_along_path(cash_flows: List[CashFlow], rate_path: List[Decimal], bond: Bond, dt: Decimal) -> Decimal:
    """Value bond along specific rate path"""
    total_value = Decimal('0')
    for cf in cash_flows:
        time_to_cf = DateUtils.calculate_day_count_fraction(date.today(), cf.date, bond.day_count_convention)
        step = min(int(time_to_cf / dt), len(rate_path) - 1)
        discount_rate = rate_path[step]
        pv = MathUtils.present_value(cf.amount, discount_rate, time_to_cf)
        total_value += pv
    return total_value

class OptionAdjustedSpread:
    """Option-Adjusted Spread (OAS) calculations"""

    @staticmethod
    def calculate_oas(bond: Bond, market_price: Decimal, spot_curve: SpotCurve, volatility: Decimal, steps: int=100) -> Decimal:
        """Calculate Option-Adjusted Spread"""
        ValidationUtils.validate_price(market_price, 'Market price')

        def price_difference(oas: Decimal) -> Decimal:
            shifted_curve = spot_curve.shift_curve(oas, 'parallel')
            if isinstance(bond, (CallableBond, PutableBond)):
                theoretical_price = ArbitrageFreeValuation.binomial_tree_value(bond, shifted_curve, volatility, steps)
            else:
                theoretical_price = BondValuation.present_value_with_curve(bond, shifted_curve)
            return theoretical_price - market_price
        try:
            oas = MathUtils.bisection_method(price_difference, Decimal('-0.05'), Decimal('0.05'))
            return oas
        except:
            return MathUtils.bisection_method(price_difference, Decimal('-0.10'), Decimal('0.10'))

    @staticmethod
    def oas_duration(bond: Bond, market_price: Decimal, spot_curve: SpotCurve, volatility: Decimal, steps: int=100) -> Decimal:
        """Calculate OAS duration (sensitivity to parallel curve shifts)"""
        shift_size = Decimal('0.0001')
        up_curve = spot_curve.shift_curve(shift_size, 'parallel')
        down_curve = spot_curve.shift_curve(-shift_size, 'parallel')
        oas_up = OptionAdjustedSpread.calculate_oas(bond, market_price, up_curve, volatility, steps)
        oas_down = OptionAdjustedSpread.calculate_oas(bond, market_price, down_curve, volatility, steps)
        return -(oas_up - oas_down) / (Decimal('2') * shift_size)

@staticmethod
def calculate_oas(bond: Bond, market_price: Decimal, spot_curve: SpotCurve, volatility: Decimal, steps: int=100) -> Decimal:
    """Calculate Option-Adjusted Spread"""
    ValidationUtils.validate_price(market_price, 'Market price')

    def price_difference(oas: Decimal) -> Decimal:
        shifted_curve = spot_curve.shift_curve(oas, 'parallel')
        if isinstance(bond, (CallableBond, PutableBond)):
            theoretical_price = ArbitrageFreeValuation.binomial_tree_value(bond, shifted_curve, volatility, steps)
        else:
            theoretical_price = BondValuation.present_value_with_curve(bond, shifted_curve)
        return theoretical_price - market_price
    try:
        oas = MathUtils.bisection_method(price_difference, Decimal('-0.05'), Decimal('0.05'))
        return oas
    except:
        return MathUtils.bisection_method(price_difference, Decimal('-0.10'), Decimal('0.10'))

def price_difference(oas: Decimal) -> Decimal:
    shifted_curve = spot_curve.shift_curve(oas, 'parallel')
    if isinstance(bond, (CallableBond, PutableBond)):
        theoretical_price = ArbitrageFreeValuation.binomial_tree_value(bond, shifted_curve, volatility, steps)
    else:
        theoretical_price = BondValuation.present_value_with_curve(bond, shifted_curve)
    return theoretical_price - market_price

@staticmethod
def oas_duration(bond: Bond, market_price: Decimal, spot_curve: SpotCurve, volatility: Decimal, steps: int=100) -> Decimal:
    """Calculate OAS duration (sensitivity to parallel curve shifts)"""
    shift_size = Decimal('0.0001')
    up_curve = spot_curve.shift_curve(shift_size, 'parallel')
    down_curve = spot_curve.shift_curve(-shift_size, 'parallel')
    oas_up = OptionAdjustedSpread.calculate_oas(bond, market_price, up_curve, volatility, steps)
    oas_down = OptionAdjustedSpread.calculate_oas(bond, market_price, down_curve, volatility, steps)
    return -(oas_up - oas_down) / (Decimal('2') * shift_size)

class ConvertibleBondValuation:
    """Valuation methods for convertible bonds"""

    @staticmethod
    def convertible_bond_value(convertible: ConvertibleBond, spot_curve: SpotCurve, stock_price: Decimal, stock_volatility: Decimal, risk_free_rate: Decimal) -> Dict[str, Decimal]:
        """Comprehensive convertible bond valuation"""
        ValidationUtils.validate_positive(stock_price, 'Stock price')
        ValidationUtils.validate_positive(stock_volatility, 'Stock volatility')
        ValidationUtils.validate_yield(risk_free_rate, 'Risk-free rate')
        straight_value = BondValuation.present_value_with_curve(convertible, spot_curve)
        conversion_value = convertible.conversion_ratio * stock_price
        time_to_maturity = DateUtils.calculate_day_count_fraction(date.today(), convertible.maturity_date, convertible.day_count_convention)
        conversion_option_value = black_scholes_call_price(S=stock_price, K=convertible.conversion_price, T=time_to_maturity, r=risk_free_rate, sigma=stock_volatility) * convertible.conversion_ratio
        total_value = max(straight_value, conversion_value) + conversion_option_value * Decimal('0.1')
        return {'total_value': total_value, 'straight_value': straight_value, 'conversion_value': conversion_value, 'option_value': conversion_option_value, 'conversion_premium': max(Decimal('0'), total_value - conversion_value), 'investment_premium': max(Decimal('0'), total_value - straight_value)}

@staticmethod
def convertible_bond_value(convertible: ConvertibleBond, spot_curve: SpotCurve, stock_price: Decimal, stock_volatility: Decimal, risk_free_rate: Decimal) -> Dict[str, Decimal]:
    """Comprehensive convertible bond valuation"""
    ValidationUtils.validate_positive(stock_price, 'Stock price')
    ValidationUtils.validate_positive(stock_volatility, 'Stock volatility')
    ValidationUtils.validate_yield(risk_free_rate, 'Risk-free rate')
    straight_value = BondValuation.present_value_with_curve(convertible, spot_curve)
    conversion_value = convertible.conversion_ratio * stock_price
    time_to_maturity = DateUtils.calculate_day_count_fraction(date.today(), convertible.maturity_date, convertible.day_count_convention)
    conversion_option_value = black_scholes_call_price(S=stock_price, K=convertible.conversion_price, T=time_to_maturity, r=risk_free_rate, sigma=stock_volatility) * convertible.conversion_ratio
    total_value = max(straight_value, conversion_value) + conversion_option_value * Decimal('0.1')
    return {'total_value': total_value, 'straight_value': straight_value, 'conversion_value': conversion_value, 'option_value': conversion_option_value, 'conversion_premium': max(Decimal('0'), total_value - conversion_value), 'investment_premium': max(Decimal('0'), total_value - straight_value)}

class MatrixPricing:
    """Matrix pricing for illiquid bonds"""

    @staticmethod
    def matrix_price(target_bond: Bond, comparable_bonds: List[Tuple[Bond, Decimal]], weights: Optional[List[Decimal]]=None) -> Decimal:
        """Calculate matrix price using comparable bonds"""
        if not comparable_bonds:
            raise ValueError('Need at least one comparable bond')
        if weights is None:
            weights = [Decimal('1') / Decimal(str(len(comparable_bonds)))] * len(comparable_bonds)
        if len(weights) != len(comparable_bonds):
            raise ValueError('Number of weights must match number of comparables')
        target_maturity = DateUtils.calculate_day_count_fraction(date.today(), target_bond.maturity_date, target_bond.day_count_convention)
        weighted_spread = Decimal('0')
        for i, (comp_bond, comp_price) in enumerate(comparable_bonds):
            comp_ytm = BondValuation.yield_to_maturity(comp_bond, comp_price)
            maturity_adj = MatrixPricing._maturity_adjustment(target_bond, comp_bond)
            credit_adj = MatrixPricing._credit_adjustment(target_bond, comp_bond)
            adjusted_ytm = comp_ytm + maturity_adj + credit_adj
            weighted_spread += weights[i] * adjusted_ytm
        target_price = BondValuation.present_value(target_bond, weighted_spread)
        return target_price

    @staticmethod
    def _maturity_adjustment(target: Bond, comparable: Bond) -> Decimal:
        """Calculate maturity adjustment"""
        target_maturity = DateUtils.calculate_day_count_fraction(date.today(), target.maturity_date, target.day_count_convention)
        comp_maturity = DateUtils.calculate_day_count_fraction(date.today(), comparable.maturity_date, comparable.day_count_convention)
        maturity_diff = target_maturity - comp_maturity
        return maturity_diff * Decimal('0.0005')

    @staticmethod
    def _credit_adjustment(target: Bond, comparable: Bond) -> Decimal:
        """Calculate credit quality adjustment"""
        if target.issuer_rating is None or comparable.issuer_rating is None:
            return Decimal('0')
        from config import RATING_SCORES
        target_score = RATING_SCORES.get(target.issuer_rating, 10)
        comp_score = RATING_SCORES.get(comparable.issuer_rating, 10)
        rating_diff = target_score - comp_score
        return Decimal(str(rating_diff)) * Decimal('0.0025')

@staticmethod
def matrix_price(target_bond: Bond, comparable_bonds: List[Tuple[Bond, Decimal]], weights: Optional[List[Decimal]]=None) -> Decimal:
    """Calculate matrix price using comparable bonds"""
    if not comparable_bonds:
        raise ValueError('Need at least one comparable bond')
    if weights is None:
        weights = [Decimal('1') / Decimal(str(len(comparable_bonds)))] * len(comparable_bonds)
    if len(weights) != len(comparable_bonds):
        raise ValueError('Number of weights must match number of comparables')
    target_maturity = DateUtils.calculate_day_count_fraction(date.today(), target_bond.maturity_date, target_bond.day_count_convention)
    weighted_spread = Decimal('0')
    for i, (comp_bond, comp_price) in enumerate(comparable_bonds):
        comp_ytm = BondValuation.yield_to_maturity(comp_bond, comp_price)
        maturity_adj = MatrixPricing._maturity_adjustment(target_bond, comp_bond)
        credit_adj = MatrixPricing._credit_adjustment(target_bond, comp_bond)
        adjusted_ytm = comp_ytm + maturity_adj + credit_adj
        weighted_spread += weights[i] * adjusted_ytm
    target_price = BondValuation.present_value(target_bond, weighted_spread)
    return target_price

@staticmethod
def _maturity_adjustment(target: Bond, comparable: Bond) -> Decimal:
    """Calculate maturity adjustment"""
    target_maturity = DateUtils.calculate_day_count_fraction(date.today(), target.maturity_date, target.day_count_convention)
    comp_maturity = DateUtils.calculate_day_count_fraction(date.today(), comparable.maturity_date, comparable.day_count_convention)
    maturity_diff = target_maturity - comp_maturity
    return maturity_diff * Decimal('0.0005')

@staticmethod
def _credit_adjustment(target: Bond, comparable: Bond) -> Decimal:
    """Calculate credit quality adjustment"""
    if target.issuer_rating is None or comparable.issuer_rating is None:
        return Decimal('0')
    from config import RATING_SCORES
    target_score = RATING_SCORES.get(target.issuer_rating, 10)
    comp_score = RATING_SCORES.get(comparable.issuer_rating, 10)
    rating_diff = target_score - comp_score
    return Decimal(str(rating_diff)) * Decimal('0.0025')

def value_bond_portfolio(bonds: List[Tuple[Bond, Decimal]], spot_curve: SpotCurve) -> Dict[str, Decimal]:
    """Value a portfolio of bonds"""
    total_value = Decimal('0')
    total_face_value = Decimal('0')
    individual_values = []
    for bond, quantity in bonds:
        bond_value = BondValuation.present_value_with_curve(bond, spot_curve)
        position_value = bond_value * quantity
        total_value += position_value
        total_face_value += bond.face_value * quantity
        individual_values.append({'bond': bond, 'quantity': quantity, 'unit_value': bond_value, 'position_value': position_value})
    return {'total_market_value': total_value, 'total_face_value': total_face_value, 'portfolio_yield': (total_face_value - total_value) / total_value if total_value > 0 else Decimal('0'), 'individual_positions': individual_values}

def stress_test_bond(bond: Bond, base_curve: SpotCurve, stress_scenarios: List[Tuple[str, Decimal]]) -> Dict[str, Decimal]:
    """Stress test bond value under different scenarios"""
    base_value = BondValuation.present_value_with_curve(bond, base_curve)
    results = {'base_case': base_value}
    for scenario_name, shift_amount in stress_scenarios:
        stressed_curve = base_curve.shift_curve(shift_amount, 'parallel')
        stressed_value = BondValuation.present_value_with_curve(bond, stressed_curve)
        results[scenario_name] = {'value': stressed_value, 'change': stressed_value - base_value, 'percentage_change': (stressed_value - base_value) / base_value * Decimal('100')}
    return results

class MathUtils:
    """Mathematical utility functions for fixed income calculations"""

    @staticmethod
    def newton_raphson(func: Callable[[Decimal], Decimal], derivative: Callable[[Decimal], Decimal], initial_guess: Decimal, tolerance: Decimal=ERROR_TOLERANCE['medium'], max_iterations: int=100) -> Decimal:
        """Newton-Raphson method for root finding"""
        x = initial_guess
        for i in range(max_iterations):
            fx = func(x)
            if abs(fx) < tolerance:
                return x
            dfx = derivative(x)
            if abs(dfx) < tolerance:
                raise ValueError('Derivative too small, convergence failed')
            x_new = x - fx / dfx
            if abs(x_new - x) < tolerance:
                return x_new
            x = x_new
        raise ValueError(f'Newton-Raphson failed to converge after {max_iterations} iterations')

    @staticmethod
    def bisection_method(func: Callable[[Decimal], Decimal], lower_bound: Decimal, upper_bound: Decimal, tolerance: Decimal=ERROR_TOLERANCE['medium'], max_iterations: int=100) -> Decimal:
        """Bisection method for root finding"""
        if func(lower_bound) * func(upper_bound) > 0:
            raise ValueError('Function must have opposite signs at bounds')
        for i in range(max_iterations):
            midpoint = (lower_bound + upper_bound) / Decimal('2')
            f_mid = func(midpoint)
            if abs(f_mid) < tolerance or (upper_bound - lower_bound) / Decimal('2') < tolerance:
                return midpoint
            if func(lower_bound) * f_mid < 0:
                upper_bound = midpoint
            else:
                lower_bound = midpoint
        raise ValueError(f'Bisection method failed to converge after {max_iterations} iterations')

    @staticmethod
    def brent_method(func: Callable[[Decimal], Decimal], lower_bound: Decimal, upper_bound: Decimal, tolerance: Decimal=ERROR_TOLERANCE['medium'], max_iterations: int=100) -> Decimal:
        """Brent's method for root finding (combines bisection and secant methods)"""
        a, b = (lower_bound, upper_bound)
        fa, fb = (func(a), func(b))
        if fa * fb > 0:
            raise ValueError('Function must have opposite signs at bounds')
        if abs(fa) < abs(fb):
            a, b = (b, a)
            fa, fb = (fb, fa)
        c = a
        fc = fa
        mflag = True
        for i in range(max_iterations):
            if abs(fb) < tolerance:
                return b
            if fa != fc and fb != fc:
                s = a * fb * fc / ((fa - fb) * (fa - fc)) + b * fa * fc / ((fb - fa) * (fb - fc)) + c * fa * fb / ((fc - fa) * (fc - fb))
            else:
                s = b - fb * (b - a) / (fb - fa)
            condition1 = not (Decimal('3') * a + b) / Decimal('4') <= s <= b
            condition2 = mflag and abs(s - b) >= abs(b - c) / Decimal('2')
            condition3 = not mflag and abs(s - b) >= abs(c - d) / Decimal('2')
            condition4 = mflag and abs(b - c) < tolerance
            condition5 = not mflag and abs(c - d) < tolerance
            if condition1 or condition2 or condition3 or condition4 or condition5:
                s = (a + b) / Decimal('2')
                mflag = True
            else:
                mflag = False
            fs = func(s)
            d = c
            c = b
            fc = fb
            if fa * fs < 0:
                b = s
                fb = fs
            else:
                a = s
                fa = fs
            if abs(fa) < abs(fb):
                a, b = (b, a)
                fa, fb = (fb, fa)
        raise ValueError(f"Brent's method failed to converge after {max_iterations} iterations")

    @staticmethod
    def present_value(cash_flow: Decimal, discount_rate: Decimal, time_period: Decimal) -> Decimal:
        """Calculate present value of a cash flow"""
        if discount_rate < -1:
            raise ValueError('Discount rate cannot be less than -100%')
        return cash_flow / (Decimal('1') + discount_rate) ** time_period

    @staticmethod
    def future_value(present_value: Decimal, rate: Decimal, time_period: Decimal) -> Decimal:
        """Calculate future value"""
        return present_value * (Decimal('1') + rate) ** time_period

    @staticmethod
    def compound_frequency_conversion(rate: Decimal, from_freq: CompoundingFrequency, to_freq: CompoundingFrequency) -> Decimal:
        """Convert rate between different compounding frequencies"""
        if from_freq == to_freq:
            return rate
        if from_freq == CompoundingFrequency.CONTINUOUS:
            continuous_rate = rate
        else:
            m = Decimal(str(from_freq.value))
            continuous_rate = m * Decimal(str(math.log(float(1 + rate / m))))
        if to_freq == CompoundingFrequency.CONTINUOUS:
            return continuous_rate
        else:
            n = Decimal(str(to_freq.value))
            return n * (Decimal(str(math.exp(float(continuous_rate / n)))) - Decimal('1'))

    @staticmethod
    def linear_interpolation(x: Decimal, x1: Decimal, y1: Decimal, x2: Decimal, y2: Decimal) -> Decimal:
        """Linear interpolation between two points"""
        if x1 == x2:
            return y1
        return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

    @staticmethod
    def cubic_spline_interpolation(x: Decimal, points: List[Tuple[Decimal, Decimal]]) -> Decimal:
        """Simplified cubic spline interpolation (linear for now)"""
        points = sorted(points, key=lambda p: p[0])
        if x <= points[0][0]:
            return points[0][1]
        if x >= points[-1][0]:
            return points[-1][1]
        for i in range(len(points) - 1):
            if points[i][0] <= x <= points[i + 1][0]:
                return MathUtils.linear_interpolation(x, points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
        return points[0][1]

@staticmethod
def future_value(present_value: Decimal, rate: Decimal, time_period: Decimal) -> Decimal:
    """Calculate future value"""
    return present_value * (Decimal('1') + rate) ** time_period

class DateUtils:
    """Date utility functions for fixed income calculations"""

    @staticmethod
    def add_business_days(start_date: date, business_days: int, convention: BusinessDayConvention=BusinessDayConvention.FOLLOWING) -> date:
        """Add business days to a date"""
        current_date = start_date
        days_added = 0
        while days_added < business_days:
            current_date += timedelta(days=1)
            if DateUtils.is_business_day(current_date):
                days_added += 1
        return DateUtils.adjust_for_business_day(current_date, convention)

    @staticmethod
    def is_business_day(check_date: date) -> bool:
        """Check if date is a business day (Monday-Friday, no holidays)"""
        return check_date.weekday() < 5

    @staticmethod
    def adjust_for_business_day(check_date: date, convention: BusinessDayConvention) -> date:
        """Adjust date according to business day convention"""
        if DateUtils.is_business_day(check_date):
            return check_date
        if convention == BusinessDayConvention.FOLLOWING:
            while not DateUtils.is_business_day(check_date):
                check_date += timedelta(days=1)
        elif convention == BusinessDayConvention.PRECEDING:
            while not DateUtils.is_business_day(check_date):
                check_date -= timedelta(days=1)
        elif convention == BusinessDayConvention.MODIFIED_FOLLOWING:
            original_month = check_date.month
            while not DateUtils.is_business_day(check_date):
                check_date += timedelta(days=1)
            if check_date.month != original_month:
                check_date = DateUtils.adjust_for_business_day(check_date.replace(day=1) - timedelta(days=1), BusinessDayConvention.PRECEDING)
        elif convention == BusinessDayConvention.MODIFIED_PRECEDING:
            original_month = check_date.month
            while not DateUtils.is_business_day(check_date):
                check_date -= timedelta(days=1)
            if check_date.month != original_month:
                check_date = DateUtils.adjust_for_business_day(check_date.replace(day=1), BusinessDayConvention.FOLLOWING)
        return check_date

    @staticmethod
    def calculate_day_count_fraction(start_date: date, end_date: date, convention: DayCountConvention) -> Decimal:
        """Calculate day count fraction between two dates"""
        if start_date >= end_date:
            return Decimal('0')
        if convention == DayCountConvention.ACTUAL_360:
            days = (end_date - start_date).days
            return Decimal(days) / Decimal('360')
        elif convention == DayCountConvention.ACTUAL_365:
            days = (end_date - start_date).days
            return Decimal(days) / Decimal('365')
        elif convention == DayCountConvention.ACTUAL_365_FIXED:
            days = (end_date - start_date).days
            return Decimal(days) / Decimal('365')
        elif convention == DayCountConvention.ACTUAL_ACTUAL:
            days = (end_date - start_date).days
            year_start = date(start_date.year, 1, 1)
            year_end = date(start_date.year + 1, 1, 1)
            days_in_year = (year_end - year_start).days
            return Decimal(days) / Decimal(days_in_year)
        elif convention == DayCountConvention.THIRTY_360:
            return DateUtils._thirty_360_fraction(start_date, end_date)
        elif convention == DayCountConvention.THIRTY_360_EUROPEAN:
            return DateUtils._thirty_360_european_fraction(start_date, end_date)
        else:
            days = (end_date - start_date).days
            return Decimal(days) / Decimal('365')

    @staticmethod
    def _thirty_360_fraction(start_date: date, end_date: date) -> Decimal:
        """Calculate 30/360 day count fraction (US/NASD convention)"""
        d1 = start_date.day
        d2 = end_date.day
        m1 = start_date.month
        m2 = end_date.month
        y1 = start_date.year
        y2 = end_date.year
        if d1 == 31:
            d1 = 30
        if d1 == 30 and d2 == 31:
            d2 = 30
        days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
        return Decimal(days) / Decimal('360')

    @staticmethod
    def _thirty_360_european_fraction(start_date: date, end_date: date) -> Decimal:
        """Calculate 30E/360 day count fraction (European convention)"""
        d1 = min(start_date.day, 30)
        d2 = min(end_date.day, 30)
        m1 = start_date.month
        m2 = end_date.month
        y1 = start_date.year
        y2 = end_date.year
        days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
        return Decimal(days) / Decimal('360')

    @staticmethod
    def is_leap_year(year: int) -> bool:
        """Check if year is a leap year"""
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    @staticmethod
    def days_in_year(year: int) -> int:
        """Get number of days in a year"""
        return 366 if DateUtils.is_leap_year(year) else 365

    @staticmethod
    def end_of_month(input_date: date) -> date:
        """Get last day of month for given date"""
        if input_date.month == 12:
            next_month = date(input_date.year + 1, 1, 1)
        else:
            next_month = date(input_date.year, input_date.month + 1, 1)
        return next_month - timedelta(days=1)

    @staticmethod
    def generate_schedule(start_date: date, end_date: date, frequency: CompoundingFrequency, convention: BusinessDayConvention=BusinessDayConvention.MODIFIED_FOLLOWING) -> List[date]:
        """Generate payment schedule between two dates"""
        if frequency == CompoundingFrequency.CONTINUOUS:
            return [end_date]
        schedule = []
        freq_value = frequency.value
        months_between = 12 // freq_value
        current_date = end_date
        while current_date > start_date:
            schedule.append(DateUtils.adjust_for_business_day(current_date, convention))
            if current_date.month <= months_between:
                new_month = 12 + current_date.month - months_between
                new_year = current_date.year - 1
            else:
                new_month = current_date.month - months_between
                new_year = current_date.year
            try:
                current_date = current_date.replace(year=new_year, month=new_month)
            except ValueError:
                current_date = DateUtils.end_of_month(date(new_year, new_month, 1))
        schedule.reverse()
        return schedule

@staticmethod
def _thirty_360_fraction(start_date: date, end_date: date) -> Decimal:
    """Calculate 30/360 day count fraction (US/NASD convention)"""
    d1 = start_date.day
    d2 = end_date.day
    m1 = start_date.month
    m2 = end_date.month
    y1 = start_date.year
    y2 = end_date.year
    if d1 == 31:
        d1 = 30
    if d1 == 30 and d2 == 31:
        d2 = 30
    days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
    return Decimal(days) / Decimal('360')

@staticmethod
def _thirty_360_european_fraction(start_date: date, end_date: date) -> Decimal:
    """Calculate 30E/360 day count fraction (European convention)"""
    d1 = min(start_date.day, 30)
    d2 = min(end_date.day, 30)
    m1 = start_date.month
    m2 = end_date.month
    y1 = start_date.year
    y2 = end_date.year
    days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)
    return Decimal(days) / Decimal('360')

class FormattingUtils:
    """Output formatting utilities"""

    @staticmethod
    def format_percentage(value: Decimal, decimal_places: int=2) -> str:
        """Format decimal as percentage"""
        percentage = value * Decimal('100')
        return f'{percentage:.{decimal_places}f}%'

    @staticmethod
    def format_currency(value: Decimal, currency_symbol: str='$', decimal_places: int=2) -> str:
        """Format decimal as currency"""
        return f'{currency_symbol}{value:,.{decimal_places}f}'

    @staticmethod
    def format_basis_points(value: Decimal) -> str:
        """Format decimal as basis points"""
        bps = value * Decimal('10000')
        return f'{bps:.0f} bps'

    @staticmethod
    def format_yield(value: Decimal, decimal_places: int=3) -> str:
        """Format yield with appropriate precision"""
        return FormattingUtils.format_percentage(value, decimal_places)

    @staticmethod
    def format_duration(value: Decimal, decimal_places: int=2) -> str:
        """Format duration"""
        return f'{value:.{decimal_places}f} years'

    @staticmethod
    def format_price(value: Decimal, decimal_places: int=4) -> str:
        """Format bond price"""
        return f'{value:.{decimal_places}f}'

@staticmethod
def format_percentage(value: Decimal, decimal_places: int=2) -> str:
    """Format decimal as percentage"""
    percentage = value * Decimal('100')
    return f'{percentage:.{decimal_places}f}%'

@staticmethod
def format_basis_points(value: Decimal) -> str:
    """Format decimal as basis points"""
    bps = value * Decimal('10000')
    return f'{bps:.0f} bps'

class BondInstrument:
    """Base bond instrument class with core functionality"""

    def __init__(self, bond: Bond):
        self.bond = bond
        self._cash_flows = None

    def generate_cash_flows(self, settlement_date: Optional[date]=None) -> List[CashFlow]:
        """Generate bond cash flows from settlement date to maturity"""
        if settlement_date is None:
            settlement_date = date.today()
        cash_flows = []
        if self.bond.is_zero_coupon:
            cash_flows.append(CashFlow(date=self.bond.maturity_date, amount=self.bond.face_value, type='principal'))
            return cash_flows
        coupon_dates = self._generate_coupon_dates(settlement_date)
        coupon_amount = self._calculate_coupon_amount()
        for coupon_date in coupon_dates:
            if coupon_date > settlement_date:
                cash_flows.append(CashFlow(date=coupon_date, amount=coupon_amount, type='coupon'))
        if cash_flows:
            cash_flows[-1].amount += self.bond.face_value
            cash_flows[-1].type = 'coupon_and_principal'
        else:
            cash_flows.append(CashFlow(date=self.bond.maturity_date, amount=self.bond.face_value, type='principal'))
        self._cash_flows = cash_flows
        return cash_flows

    def _generate_coupon_dates(self, start_date: date) -> List[date]:
        """Generate coupon payment dates"""
        dates = []
        frequency = self.bond.coupon_frequency.value
        if frequency == 0:
            frequency = 1
        months_between = 12 // frequency
        current_date = self.bond.maturity_date
        while current_date > self.bond.issue_date:
            dates.append(current_date)
            if current_date.month <= months_between:
                new_month = 12 + current_date.month - months_between
                new_year = current_date.year - 1
            else:
                new_month = current_date.month - months_between
                new_year = current_date.year
            try:
                current_date = current_date.replace(year=new_year, month=new_month)
            except ValueError:
                if new_month == 2 and current_date.day > 28:
                    current_date = current_date.replace(year=new_year, month=new_month, day=28)
                else:
                    current_date = current_date.replace(year=new_year, month=new_month, day=1)
                    current_date = current_date.replace(day=min(current_date.day, self._days_in_month(new_year, new_month)))
        dates.reverse()
        return dates

    def _days_in_month(self, year: int, month: int) -> int:
        """Get number of days in a month"""
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        this_month = date(year, month, 1)
        return (next_month - this_month).days

    def _calculate_coupon_amount(self) -> Decimal:
        """Calculate coupon payment amount"""
        annual_coupon = self.bond.face_value * self.bond.coupon_rate
        frequency = self.bond.coupon_frequency.value
        if frequency == 0:
            return annual_coupon
        return annual_coupon / Decimal(frequency)

    def accrued_interest(self, settlement_date: date) -> Decimal:
        """Calculate accrued interest from last coupon date"""
        if self.bond.is_zero_coupon:
            return Decimal('0')
        coupon_dates = self._generate_coupon_dates(self.bond.issue_date)
        last_coupon_date = self.bond.issue_date
        for coupon_date in coupon_dates:
            if coupon_date <= settlement_date:
                last_coupon_date = coupon_date
            else:
                break
        days_accrued = self._calculate_days(last_coupon_date, settlement_date)
        days_in_period = self._calculate_days_in_coupon_period(last_coupon_date)
        coupon_amount = self._calculate_coupon_amount()
        return coupon_amount * (Decimal(days_accrued) / Decimal(days_in_period))

    def _calculate_days(self, start_date: date, end_date: date) -> int:
        """Calculate days between dates based on day count convention"""
        if self.bond.day_count_convention == DayCountConvention.ACTUAL_360:
            return (end_date - start_date).days
        elif self.bond.day_count_convention == DayCountConvention.ACTUAL_365:
            return (end_date - start_date).days
        elif self.bond.day_count_convention == DayCountConvention.ACTUAL_ACTUAL:
            return (end_date - start_date).days
        elif self.bond.day_count_convention == DayCountConvention.THIRTY_360:
            return self._thirty_360_days(start_date, end_date)
        else:
            return (end_date - start_date).days

    def _thirty_360_days(self, start_date: date, end_date: date) -> int:
        """Calculate days using 30/360 convention"""
        d1 = min(start_date.day, 30)
        d2 = min(end_date.day, 30) if d1 == 30 else end_date.day
        return 360 * (end_date.year - start_date.year) + 30 * (end_date.month - start_date.month) + (d2 - d1)

    def _calculate_days_in_coupon_period(self, coupon_date: date) -> int:
        """Calculate days in coupon period"""
        frequency = self.bond.coupon_frequency.value
        if frequency == 0:
            frequency = 1
        if self.bond.day_count_convention == DayCountConvention.THIRTY_360:
            return 360 // frequency
        else:
            return 365 // frequency

    def time_to_maturity(self, settlement_date: Optional[date]=None) -> Decimal:
        """Calculate time to maturity in years"""
        if settlement_date is None:
            settlement_date = date.today()
        days = (self.bond.maturity_date - settlement_date).days
        if self.bond.day_count_convention == DayCountConvention.ACTUAL_365:
            return Decimal(days) / Decimal('365')
        elif self.bond.day_count_convention == DayCountConvention.ACTUAL_360:
            return Decimal(days) / Decimal('360')
        else:
            return Decimal(days) / Decimal('365.25')

def _calculate_coupon_amount(self) -> Decimal:
    """Calculate coupon payment amount"""
    annual_coupon = self.bond.face_value * self.bond.coupon_rate
    frequency = self.bond.coupon_frequency.value
    if frequency == 0:
        return annual_coupon
    return annual_coupon / Decimal(frequency)

class FloatingRateNoteInstrument(BondInstrument):
    """Floating rate note instrument"""

    def __init__(self, frn: FloatingRateNote):
        super().__init__(frn)
        self.frn = frn
        self._current_reference_rate = Decimal('0')

    def set_reference_rate(self, rate: Decimal):
        """Set current reference rate"""
        self._current_reference_rate = rate

    def current_coupon_rate(self) -> Decimal:
        """Calculate current coupon rate"""
        base_rate = self._current_reference_rate + self.frn.spread
        if self.frn.rate_cap and base_rate > self.frn.rate_cap:
            return self.frn.rate_cap
        if self.frn.rate_floor and base_rate < self.frn.rate_floor:
            return self.frn.rate_floor
        return base_rate

    def generate_cash_flows_with_rate_path(self, rate_path: List[Tuple[date, Decimal]]) -> List[CashFlow]:
        """Generate cash flows given a path of reference rates"""
        cash_flows = []
        coupon_dates = self._generate_coupon_dates(date.today())
        for i, coupon_date in enumerate(coupon_dates):
            if coupon_date > date.today():
                applicable_rate = self._find_rate_for_period(rate_path, coupon_date)
                coupon_rate = applicable_rate + self.frn.spread
                if self.frn.rate_cap:
                    coupon_rate = min(coupon_rate, self.frn.rate_cap)
                if self.frn.rate_floor:
                    coupon_rate = max(coupon_rate, self.frn.rate_floor)
                coupon_amount = self.frn.face_value * coupon_rate / Decimal(self.frn.coupon_frequency.value)
                cash_flows.append(CashFlow(date=coupon_date, amount=coupon_amount, type='coupon'))
        if cash_flows:
            cash_flows[-1].amount += self.frn.face_value
            cash_flows[-1].type = 'coupon_and_principal'
        return cash_flows

    def _find_rate_for_period(self, rate_path: List[Tuple[date, Decimal]], period_end: date) -> Decimal:
        """Find the reference rate applicable for a coupon period"""
        applicable_rate = Decimal('0')
        for rate_date, rate in rate_path:
            if rate_date <= period_end:
                applicable_rate = rate
            else:
                break
        return applicable_rate

def _find_rate_for_period(self, rate_path: List[Tuple[date, Decimal]], period_end: date) -> Decimal:
    """Find the reference rate applicable for a coupon period"""
    applicable_rate = Decimal('0')
    for rate_date, rate in rate_path:
        if rate_date <= period_end:
            applicable_rate = rate
        else:
            break
    return applicable_rate

class ConvertibleBondInstrument(BondInstrument):
    """Convertible bond instrument"""

    def __init__(self, convertible: ConvertibleBond):
        super().__init__(convertible)
        self.convertible = convertible

    def conversion_value(self, stock_price: Optional[Decimal]=None) -> Decimal:
        """Calculate conversion value"""
        if stock_price is None:
            stock_price = self.convertible.underlying_stock_price
        if stock_price is None:
            raise ValidationError('Stock price required for conversion value calculation')
        return self.convertible.conversion_ratio * stock_price

    def conversion_premium(self, bond_price: Decimal, stock_price: Optional[Decimal]=None) -> Decimal:
        """Calculate conversion premium"""
        conv_value = self.conversion_value(stock_price)
        return bond_price - conv_value

    def conversion_premium_percentage(self, bond_price: Decimal, stock_price: Optional[Decimal]=None) -> Decimal:
        """Calculate conversion premium as percentage"""
        conv_value = self.conversion_value(stock_price)
        if conv_value == 0:
            return Decimal('0')
        premium = self.conversion_premium(bond_price, stock_price)
        return premium / conv_value * Decimal('100')

    def payback_period(self, bond_price: Decimal, dividend_yield: Optional[Decimal]=None) -> Optional[Decimal]:
        """Calculate payback period in years"""
        if dividend_yield is None:
            dividend_yield = self.convertible.dividend_yield
        if dividend_yield is None or dividend_yield == 0:
            return None
        coupon_yield = self.convertible.coupon_rate * self.convertible.face_value / bond_price
        yield_advantage = coupon_yield - dividend_yield
        if yield_advantage <= 0:
            return None
        premium_pct = self.conversion_premium_percentage(bond_price) / Decimal('100')
        return premium_pct / yield_advantage

    def delta(self, bond_price: Decimal, stock_price: Decimal) -> Decimal:
        """Calculate convertible bond delta (sensitivity to stock price)"""
        conv_value = self.conversion_value(stock_price)
        if bond_price <= conv_value:
            return self.convertible.conversion_ratio
        else:
            return self.convertible.conversion_ratio * (conv_value / bond_price)

def conversion_premium(self, bond_price: Decimal, stock_price: Optional[Decimal]=None) -> Decimal:
    """Calculate conversion premium"""
    conv_value = self.conversion_value(stock_price)
    return bond_price - conv_value

def conversion_premium_percentage(self, bond_price: Decimal, stock_price: Optional[Decimal]=None) -> Decimal:
    """Calculate conversion premium as percentage"""
    conv_value = self.conversion_value(stock_price)
    if conv_value == 0:
        return Decimal('0')
    premium = self.conversion_premium(bond_price, stock_price)
    return premium / conv_value * Decimal('100')

def payback_period(self, bond_price: Decimal, dividend_yield: Optional[Decimal]=None) -> Optional[Decimal]:
    """Calculate payback period in years"""
    if dividend_yield is None:
        dividend_yield = self.convertible.dividend_yield
    if dividend_yield is None or dividend_yield == 0:
        return None
    coupon_yield = self.convertible.coupon_rate * self.convertible.face_value / bond_price
    yield_advantage = coupon_yield - dividend_yield
    if yield_advantage <= 0:
        return None
    premium_pct = self.conversion_premium_percentage(bond_price) / Decimal('100')
    return premium_pct / yield_advantage

def delta(self, bond_price: Decimal, stock_price: Decimal) -> Decimal:
    """Calculate convertible bond delta (sensitivity to stock price)"""
    conv_value = self.conversion_value(stock_price)
    if bond_price <= conv_value:
        return self.convertible.conversion_ratio
    else:
        return self.convertible.conversion_ratio * (conv_value / bond_price)

def create_bond_instrument(bond: Bond) -> BondInstrument:
    """Factory function to create appropriate instrument type"""
    if isinstance(bond, CallableBond):
        return CallableBondInstrument(bond)
    elif isinstance(bond, PutableBond):
        return PutableBondInstrument(bond)
    elif isinstance(bond, FloatingRateNote):
        return FloatingRateNoteInstrument(bond)
    elif isinstance(bond, ConvertibleBond):
        return ConvertibleBondInstrument(bond)
    else:
        return BondInstrument(bond)

def create_callable_bond_with_schedule(base_bond: Bond, call_schedule: List[Tuple[date, Decimal]]) -> CallableBondInstrument:
    """Create callable bond with call schedule"""
    call_features = [CallableFeature(call_date=date, call_price=price) for date, price in call_schedule]
    callable_bond = CallableBond(isin=base_bond.isin, cusip=base_bond.cusip, ticker=base_bond.ticker, issue_date=base_bond.issue_date, maturity_date=base_bond.maturity_date, face_value=base_bond.face_value, currency=base_bond.currency, coupon_rate=base_bond.coupon_rate, coupon_frequency=base_bond.coupon_frequency, day_count_convention=base_bond.day_count_convention, issuer_name=base_bond.issuer_name, issuer_rating=base_bond.issuer_rating, call_schedule=call_features)
    return CallableBondInstrument(callable_bond)

class SpotCurve:
    """Zero-coupon (spot) yield curve implementation"""

    def __init__(self, curve: YieldCurve):
        ValidationUtils.validate_date_order(date.today(), curve.curve_date, 'Today', 'Curve date')
        self.curve = curve
        self._validate_curve()

    def _validate_curve(self):
        """Validate curve data"""
        if len(self.curve.maturities) != len(self.curve.rates):
            raise ValueError('Maturities and rates must have same length')
        for i in range(1, len(self.curve.maturities)):
            if self.curve.maturities[i] <= self.curve.maturities[i - 1]:
                raise ValueError('Maturities must be in ascending order')
        for rate in self.curve.rates:
            ValidationUtils.validate_yield(rate, 'Spot rate')

    @cache_calculation
    def get_rate(self, maturity: Decimal) -> Decimal:
        """Get spot rate for given maturity using interpolation"""
        ValidationUtils.validate_positive(maturity, 'Maturity')
        if maturity in self.curve.maturities:
            index = self.curve.maturities.index(maturity)
            return self.curve.rates[index]
        if maturity < self.curve.maturities[0]:
            return self.curve.rates[0]
        if maturity > self.curve.maturities[-1]:
            return self.curve.rates[-1]
        for i in range(len(self.curve.maturities) - 1):
            if self.curve.maturities[i] <= maturity <= self.curve.maturities[i + 1]:
                return MathUtils.linear_interpolation(maturity, self.curve.maturities[i], self.curve.rates[i], self.curve.maturities[i + 1], self.curve.rates[i + 1])
        return self.curve.rates[0]

    def get_discount_factor(self, maturity: Decimal) -> Decimal:
        """Calculate discount factor for given maturity"""
        spot_rate = self.get_rate(maturity)
        return Decimal('1') / (Decimal('1') + spot_rate) ** maturity

    def forward_rate(self, start_maturity: Decimal, end_maturity: Decimal) -> Decimal:
        """Calculate forward rate between two maturities"""
        ValidationUtils.validate_positive(start_maturity, 'Start maturity')
        ValidationUtils.validate_positive(end_maturity, 'End maturity')
        if end_maturity <= start_maturity:
            raise ValueError('End maturity must be greater than start maturity')
        r1 = self.get_rate(start_maturity)
        r2 = self.get_rate(end_maturity)
        numerator = (Decimal('1') + r2) ** end_maturity
        denominator = (Decimal('1') + r1) ** start_maturity
        time_diff = end_maturity - start_maturity
        forward_factor = numerator / denominator
        return forward_factor ** (Decimal('1') / time_diff) - Decimal('1')

    def shift_curve(self, shift_amount: Decimal, shift_type: str='parallel') -> 'SpotCurve':
        """Apply parallel or non-parallel shifts to the curve"""
        new_rates = []
        if shift_type == 'parallel':
            new_rates = [rate + shift_amount for rate in self.curve.rates]
        elif shift_type == 'steepening':
            for i, rate in enumerate(self.curve.rates):
                maturity = self.curve.maturities[i]
                shift = shift_amount * (maturity / self.curve.maturities[-1])
                new_rates.append(rate + shift)
        elif shift_type == 'flattening':
            for i, rate in enumerate(self.curve.rates):
                maturity = self.curve.maturities[i]
                shift = -shift_amount * (maturity / self.curve.maturities[-1])
                new_rates.append(rate + shift)
        else:
            raise ValueError("Invalid shift type. Use 'parallel', 'steepening', or 'flattening'")
        for rate in new_rates:
            ValidationUtils.validate_yield(rate, 'Shifted rate')
        new_curve = YieldCurve(curve_date=self.curve.curve_date, maturities=self.curve.maturities.copy(), rates=new_rates, currency=self.curve.currency, curve_type='spot')
        return SpotCurve(new_curve)

def _validate_curve(self):
    """Validate curve data"""
    if len(self.curve.maturities) != len(self.curve.rates):
        raise ValueError('Maturities and rates must have same length')
    for i in range(1, len(self.curve.maturities)):
        if self.curve.maturities[i] <= self.curve.maturities[i - 1]:
            raise ValueError('Maturities must be in ascending order')
    for rate in self.curve.rates:
        ValidationUtils.validate_yield(rate, 'Spot rate')

def get_discount_factor(self, maturity: Decimal) -> Decimal:
    """Calculate discount factor for given maturity"""
    spot_rate = self.get_rate(maturity)
    return Decimal('1') / (Decimal('1') + spot_rate) ** maturity

def forward_rate(self, start_maturity: Decimal, end_maturity: Decimal) -> Decimal:
    """Calculate forward rate between two maturities"""
    ValidationUtils.validate_positive(start_maturity, 'Start maturity')
    ValidationUtils.validate_positive(end_maturity, 'End maturity')
    if end_maturity <= start_maturity:
        raise ValueError('End maturity must be greater than start maturity')
    r1 = self.get_rate(start_maturity)
    r2 = self.get_rate(end_maturity)
    numerator = (Decimal('1') + r2) ** end_maturity
    denominator = (Decimal('1') + r1) ** start_maturity
    time_diff = end_maturity - start_maturity
    forward_factor = numerator / denominator
    return forward_factor ** (Decimal('1') / time_diff) - Decimal('1')

def shift_curve(self, shift_amount: Decimal, shift_type: str='parallel') -> 'SpotCurve':
    """Apply parallel or non-parallel shifts to the curve"""
    new_rates = []
    if shift_type == 'parallel':
        new_rates = [rate + shift_amount for rate in self.curve.rates]
    elif shift_type == 'steepening':
        for i, rate in enumerate(self.curve.rates):
            maturity = self.curve.maturities[i]
            shift = shift_amount * (maturity / self.curve.maturities[-1])
            new_rates.append(rate + shift)
    elif shift_type == 'flattening':
        for i, rate in enumerate(self.curve.rates):
            maturity = self.curve.maturities[i]
            shift = -shift_amount * (maturity / self.curve.maturities[-1])
            new_rates.append(rate + shift)
    else:
        raise ValueError("Invalid shift type. Use 'parallel', 'steepening', or 'flattening'")
    for rate in new_rates:
        ValidationUtils.validate_yield(rate, 'Shifted rate')
    new_curve = YieldCurve(curve_date=self.curve.curve_date, maturities=self.curve.maturities.copy(), rates=new_rates, currency=self.curve.currency, curve_type='spot')
    return SpotCurve(new_curve)

class ParCurve:
    """Par yield curve implementation"""

    def __init__(self, spot_curve: SpotCurve):
        self.spot_curve = spot_curve
        self.curve_date = spot_curve.curve.curve_date
        self.currency = spot_curve.curve.currency

    @cache_calculation
    def get_par_rate(self, maturity: Decimal, frequency: CompoundingFrequency=CompoundingFrequency.SEMI_ANNUAL) -> Decimal:
        """Calculate par rate for given maturity"""
        ValidationUtils.validate_positive(maturity, 'Maturity')
        if frequency == CompoundingFrequency.CONTINUOUS:
            return self.spot_curve.get_rate(maturity)
        payments_per_year = frequency.value
        payment_interval = Decimal('1') / Decimal(str(payments_per_year))
        payment_times = []
        current_time = payment_interval
        while current_time <= maturity:
            payment_times.append(current_time)
            current_time += payment_interval
        if not payment_times or payment_times[-1] != maturity:
            payment_times.append(maturity)
        discount_sum = Decimal('0')
        for time in payment_times:
            discount_sum += self.spot_curve.get_discount_factor(time)
        final_discount = self.spot_curve.get_discount_factor(maturity)
        par_rate = (Decimal('1') - final_discount) / discount_sum
        return par_rate

    def build_par_curve(self, maturities: List[Decimal], frequency: CompoundingFrequency=CompoundingFrequency.SEMI_ANNUAL) -> YieldCurve:
        """Build complete par curve for given maturities"""
        par_rates = []
        for maturity in maturities:
            par_rate = self.get_par_rate(maturity, frequency)
            par_rates.append(par_rate)
        return YieldCurve(curve_date=self.curve_date, maturities=maturities, rates=par_rates, currency=self.currency, curve_type='par')

@cache_calculation
def get_par_rate(self, maturity: Decimal, frequency: CompoundingFrequency=CompoundingFrequency.SEMI_ANNUAL) -> Decimal:
    """Calculate par rate for given maturity"""
    ValidationUtils.validate_positive(maturity, 'Maturity')
    if frequency == CompoundingFrequency.CONTINUOUS:
        return self.spot_curve.get_rate(maturity)
    payments_per_year = frequency.value
    payment_interval = Decimal('1') / Decimal(str(payments_per_year))
    payment_times = []
    current_time = payment_interval
    while current_time <= maturity:
        payment_times.append(current_time)
        current_time += payment_interval
    if not payment_times or payment_times[-1] != maturity:
        payment_times.append(maturity)
    discount_sum = Decimal('0')
    for time in payment_times:
        discount_sum += self.spot_curve.get_discount_factor(time)
    final_discount = self.spot_curve.get_discount_factor(maturity)
    par_rate = (Decimal('1') - final_discount) / discount_sum
    return par_rate

def build_par_curve(self, maturities: List[Decimal], frequency: CompoundingFrequency=CompoundingFrequency.SEMI_ANNUAL) -> YieldCurve:
    """Build complete par curve for given maturities"""
    par_rates = []
    for maturity in maturities:
        par_rate = self.get_par_rate(maturity, frequency)
        par_rates.append(par_rate)
    return YieldCurve(curve_date=self.curve_date, maturities=maturities, rates=par_rates, currency=self.currency, curve_type='par')

class ForwardCurve:
    """Forward rate curve implementation"""

    def __init__(self, spot_curve: SpotCurve):
        self.spot_curve = spot_curve
        self.curve_date = spot_curve.curve.curve_date
        self.currency = spot_curve.curve.currency

    @cache_calculation
    def get_forward_rate(self, start_time: Decimal, end_time: Decimal) -> Decimal:
        """Calculate forward rate between two time points"""
        return self.spot_curve.forward_rate(start_time, end_time)

    def build_forward_curve(self, start_maturity: Decimal, end_maturities: List[Decimal]) -> YieldCurve:
        """Build forward curve from start maturity to various end maturities"""
        forward_rates = []
        for end_maturity in end_maturities:
            if end_maturity <= start_maturity:
                raise ValueError(f'End maturity {end_maturity} must be greater than start maturity {start_maturity}')
            forward_rate = self.get_forward_rate(start_maturity, end_maturity)
            forward_rates.append(forward_rate)
        return YieldCurve(curve_date=self.curve_date, maturities=end_maturities, rates=forward_rates, currency=self.currency, curve_type='forward')

    def instantaneous_forward_rate(self, maturity: Decimal, delta: Decimal=Decimal('0.001')) -> Decimal:
        """Calculate instantaneous forward rate at given maturity"""
        if maturity <= delta:
            return self.spot_curve.get_rate(delta)
        r1 = self.spot_curve.get_rate(maturity - delta / 2)
        r2 = self.spot_curve.get_rate(maturity + delta / 2)
        return r2 + maturity * (r2 - r1) / delta

def build_forward_curve(self, start_maturity: Decimal, end_maturities: List[Decimal]) -> YieldCurve:
    """Build forward curve from start maturity to various end maturities"""
    forward_rates = []
    for end_maturity in end_maturities:
        if end_maturity <= start_maturity:
            raise ValueError(f'End maturity {end_maturity} must be greater than start maturity {start_maturity}')
        forward_rate = self.get_forward_rate(start_maturity, end_maturity)
        forward_rates.append(forward_rate)
    return YieldCurve(curve_date=self.curve_date, maturities=end_maturities, rates=forward_rates, currency=self.currency, curve_type='forward')

def instantaneous_forward_rate(self, maturity: Decimal, delta: Decimal=Decimal('0.001')) -> Decimal:
    """Calculate instantaneous forward rate at given maturity"""
    if maturity <= delta:
        return self.spot_curve.get_rate(delta)
    r1 = self.spot_curve.get_rate(maturity - delta / 2)
    r2 = self.spot_curve.get_rate(maturity + delta / 2)
    return r2 + maturity * (r2 - r1) / delta

class SwapCurve:
    """Interest rate swap curve implementation"""

    def __init__(self, market_data: Dict[str, Decimal], currency: Currency=Currency.USD):
        """
        Initialize with market swap rates
        market_data: Dict with tenor -> rate (e.g., {'2Y': 0.025, '5Y': 0.035})
        """
        self.market_data = market_data
        self.currency = currency
        self.curve_date = date.today()
        self._tenors = []
        self._rates = []
        self._maturities = []
        self._parse_market_data()

    def _parse_market_data(self):
        """Parse market data into tenors, maturities, and rates"""
        for tenor, rate in self.market_data.items():
            self._tenors.append(tenor)
            self._rates.append(rate)
            if tenor.endswith('M'):
                months = int(tenor[:-1])
                maturity = Decimal(months) / Decimal('12')
            elif tenor.endswith('Y'):
                years = int(tenor[:-1])
                maturity = Decimal(years)
            else:
                raise ValueError(f'Invalid tenor format: {tenor}')
            self._maturities.append(maturity)
        sorted_data = sorted(zip(self._maturities, self._rates, self._tenors))
        self._maturities, self._rates, self._tenors = zip(*sorted_data)
        self._maturities = list(self._maturities)
        self._rates = list(self._rates)
        self._tenors = list(self._tenors)

    def get_swap_rate(self, maturity: Decimal) -> Decimal:
        """Get swap rate for given maturity using interpolation"""
        ValidationUtils.validate_positive(maturity, 'Maturity')
        if maturity in self._maturities:
            index = self._maturities.index(maturity)
            return self._rates[index]
        if maturity < self._maturities[0]:
            return self._rates[0]
        if maturity > self._maturities[-1]:
            return self._rates[-1]
        for i in range(len(self._maturities) - 1):
            if self._maturities[i] <= maturity <= self._maturities[i + 1]:
                return MathUtils.linear_interpolation(maturity, self._maturities[i], self._rates[i], self._maturities[i + 1], self._rates[i + 1])
        return self._rates[0]

    def swap_spread(self, maturity: Decimal, treasury_curve: SpotCurve) -> Decimal:
        """Calculate swap spread over treasury curve"""
        swap_rate = self.get_swap_rate(maturity)
        treasury_rate = treasury_curve.get_rate(maturity)
        return swap_rate - treasury_rate

    def to_yield_curve(self) -> YieldCurve:
        """Convert to YieldCurve object"""
        return YieldCurve(curve_date=self.curve_date, maturities=self._maturities, rates=self._rates, currency=self.currency, curve_type='swap')

def swap_spread(self, maturity: Decimal, treasury_curve: SpotCurve) -> Decimal:
    """Calculate swap spread over treasury curve"""
    swap_rate = self.get_swap_rate(maturity)
    treasury_rate = treasury_curve.get_rate(maturity)
    return swap_rate - treasury_rate

def to_yield_curve(self) -> YieldCurve:
    """Convert to YieldCurve object"""
    return YieldCurve(curve_date=self.curve_date, maturities=self._maturities, rates=self._rates, currency=self.currency, curve_type='swap')

class BootstrappingEngine:
    """Bootstrap yield curves from market instruments"""

    @staticmethod
    def bootstrap_from_bonds(bonds: List[Bond], prices: List[Decimal], settlement_date: Optional[date]=None) -> SpotCurve:
        """Bootstrap spot curve from bond prices"""
        if len(bonds) != len(prices):
            raise ValueError('Number of bonds must equal number of prices')
        if settlement_date is None:
            settlement_date = date.today()
        bond_price_pairs = list(zip(bonds, prices))
        bond_price_pairs.sort(key=lambda x: x[0].maturity_date)
        maturities = []
        spot_rates = []
        for bond, price in bond_price_pairs:
            maturity = DateUtils.calculate_day_count_fraction(settlement_date, bond.maturity_date, bond.day_count_convention)
            if bond.is_zero_coupon:
                spot_rate = (bond.face_value / price) ** (Decimal('1') / maturity) - Decimal('1')
            else:
                spot_rate = BootstrappingEngine._solve_coupon_bond_rate(bond, price, maturity, maturities, spot_rates)
            maturities.append(maturity)
            spot_rates.append(spot_rate)
        yield_curve = YieldCurve(curve_date=settlement_date, maturities=maturities, rates=spot_rates, currency=bonds[0].currency if bonds else Currency.USD, curve_type='spot')
        return SpotCurve(yield_curve)

    @staticmethod
    def _solve_coupon_bond_rate(bond: Bond, price: Decimal, maturity: Decimal, existing_maturities: List[Decimal], existing_rates: List[Decimal]) -> Decimal:
        """Solve for spot rate of coupon bond using existing curve"""
        from instruments import BondInstrument
        if existing_maturities:
            temp_curve = YieldCurve(curve_date=date.today(), maturities=existing_maturities, rates=existing_rates, currency=bond.currency, curve_type='spot')
            temp_spot_curve = SpotCurve(temp_curve)
        else:
            temp_spot_curve = None
        bond_instrument = BondInstrument(bond)
        cash_flows = bond_instrument.generate_cash_flows()

        def pv_function(rate: Decimal) -> Decimal:
            total_pv = Decimal('0')
            for cf in cash_flows:
                cf_maturity = DateUtils.calculate_day_count_fraction(date.today(), cf.date, bond.day_count_convention)
                if cf_maturity < maturity:
                    if temp_spot_curve:
                        discount_rate = temp_spot_curve.get_rate(cf_maturity)
                    else:
                        discount_rate = rate
                else:
                    discount_rate = rate
                pv = cf.amount / (Decimal('1') + discount_rate) ** cf_maturity
                total_pv += pv
            return total_pv - price

        def pv_derivative(rate: Decimal) -> Decimal:
            total_derivative = Decimal('0')
            for cf in cash_flows:
                cf_maturity = DateUtils.calculate_day_count_fraction(date.today(), cf.date, bond.day_count_convention)
                if cf_maturity >= maturity:
                    derivative = -cf_maturity * cf.amount / (Decimal('1') + rate) ** (cf_maturity + Decimal('1'))
                    total_derivative += derivative
            return total_derivative
        try:
            initial_guess = Decimal('0.05')
            spot_rate = MathUtils.newton_raphson(pv_function, pv_derivative, initial_guess)
            ValidationUtils.validate_yield(spot_rate, 'Bootstrapped spot rate')
            return spot_rate
        except:
            return MathUtils.bisection_method(pv_function, Decimal('0.001'), Decimal('0.50'))

@staticmethod
def bootstrap_from_bonds(bonds: List[Bond], prices: List[Decimal], settlement_date: Optional[date]=None) -> SpotCurve:
    """Bootstrap spot curve from bond prices"""
    if len(bonds) != len(prices):
        raise ValueError('Number of bonds must equal number of prices')
    if settlement_date is None:
        settlement_date = date.today()
    bond_price_pairs = list(zip(bonds, prices))
    bond_price_pairs.sort(key=lambda x: x[0].maturity_date)
    maturities = []
    spot_rates = []
    for bond, price in bond_price_pairs:
        maturity = DateUtils.calculate_day_count_fraction(settlement_date, bond.maturity_date, bond.day_count_convention)
        if bond.is_zero_coupon:
            spot_rate = (bond.face_value / price) ** (Decimal('1') / maturity) - Decimal('1')
        else:
            spot_rate = BootstrappingEngine._solve_coupon_bond_rate(bond, price, maturity, maturities, spot_rates)
        maturities.append(maturity)
        spot_rates.append(spot_rate)
    yield_curve = YieldCurve(curve_date=settlement_date, maturities=maturities, rates=spot_rates, currency=bonds[0].currency if bonds else Currency.USD, curve_type='spot')
    return SpotCurve(yield_curve)

@staticmethod
def _solve_coupon_bond_rate(bond: Bond, price: Decimal, maturity: Decimal, existing_maturities: List[Decimal], existing_rates: List[Decimal]) -> Decimal:
    """Solve for spot rate of coupon bond using existing curve"""
    from instruments import BondInstrument
    if existing_maturities:
        temp_curve = YieldCurve(curve_date=date.today(), maturities=existing_maturities, rates=existing_rates, currency=bond.currency, curve_type='spot')
        temp_spot_curve = SpotCurve(temp_curve)
    else:
        temp_spot_curve = None
    bond_instrument = BondInstrument(bond)
    cash_flows = bond_instrument.generate_cash_flows()

    def pv_function(rate: Decimal) -> Decimal:
        total_pv = Decimal('0')
        for cf in cash_flows:
            cf_maturity = DateUtils.calculate_day_count_fraction(date.today(), cf.date, bond.day_count_convention)
            if cf_maturity < maturity:
                if temp_spot_curve:
                    discount_rate = temp_spot_curve.get_rate(cf_maturity)
                else:
                    discount_rate = rate
            else:
                discount_rate = rate
            pv = cf.amount / (Decimal('1') + discount_rate) ** cf_maturity
            total_pv += pv
        return total_pv - price

    def pv_derivative(rate: Decimal) -> Decimal:
        total_derivative = Decimal('0')
        for cf in cash_flows:
            cf_maturity = DateUtils.calculate_day_count_fraction(date.today(), cf.date, bond.day_count_convention)
            if cf_maturity >= maturity:
                derivative = -cf_maturity * cf.amount / (Decimal('1') + rate) ** (cf_maturity + Decimal('1'))
                total_derivative += derivative
        return total_derivative
    try:
        initial_guess = Decimal('0.05')
        spot_rate = MathUtils.newton_raphson(pv_function, pv_derivative, initial_guess)
        ValidationUtils.validate_yield(spot_rate, 'Bootstrapped spot rate')
        return spot_rate
    except:
        return MathUtils.bisection_method(pv_function, Decimal('0.001'), Decimal('0.50'))

def pv_function(rate: Decimal) -> Decimal:
    total_pv = Decimal('0')
    for cf in cash_flows:
        cf_maturity = DateUtils.calculate_day_count_fraction(date.today(), cf.date, bond.day_count_convention)
        if cf_maturity < maturity:
            if temp_spot_curve:
                discount_rate = temp_spot_curve.get_rate(cf_maturity)
            else:
                discount_rate = rate
        else:
            discount_rate = rate
        pv = cf.amount / (Decimal('1') + discount_rate) ** cf_maturity
        total_pv += pv
    return total_pv - price

def pv_derivative(rate: Decimal) -> Decimal:
    total_derivative = Decimal('0')
    for cf in cash_flows:
        cf_maturity = DateUtils.calculate_day_count_fraction(date.today(), cf.date, bond.day_count_convention)
        if cf_maturity >= maturity:
            derivative = -cf_maturity * cf.amount / (Decimal('1') + rate) ** (cf_maturity + Decimal('1'))
            total_derivative += derivative
    return total_derivative

class CurveAnalysis:
    """Yield curve analysis and metrics"""

    @staticmethod
    def curve_slope(curve: SpotCurve, short_maturity: Decimal=Decimal('2'), long_maturity: Decimal=Decimal('10')) -> Decimal:
        """Calculate curve slope between two maturities"""
        short_rate = curve.get_rate(short_maturity)
        long_rate = curve.get_rate(long_maturity)
        return long_rate - short_rate

    @staticmethod
    def curve_curvature(curve: SpotCurve, short_maturity: Decimal=Decimal('2'), medium_maturity: Decimal=Decimal('5'), long_maturity: Decimal=Decimal('10')) -> Decimal:
        """Calculate curve curvature (butterfly)"""
        short_rate = curve.get_rate(short_maturity)
        medium_rate = curve.get_rate(medium_maturity)
        long_rate = curve.get_rate(long_maturity)
        return Decimal('2') * medium_rate - short_rate - long_rate

    @staticmethod
    def level_slope_curvature_decomposition(curve: SpotCurve) -> Tuple[Decimal, Decimal, Decimal]:
        """Decompose curve into level, slope, and curvature factors"""
        r2 = curve.get_rate(Decimal('2'))
        r5 = curve.get_rate(Decimal('5'))
        r10 = curve.get_rate(Decimal('10'))
        level = (r2 + r5 + r10) / Decimal('3')
        slope = r10 - r2
        curvature = Decimal('2') * r5 - r2 - r10
        return (level, slope, curvature)

    @staticmethod
    def duration_matched_curve_shift(curve: SpotCurve, target_duration: Decimal, shift_amount: Decimal) -> SpotCurve:
        """Apply duration-matched curve shift"""
        duration_scaling = target_duration / Decimal('5')
        scaled_shift = shift_amount * duration_scaling
        return curve.shift_curve(scaled_shift, 'parallel')

@staticmethod
def curve_slope(curve: SpotCurve, short_maturity: Decimal=Decimal('2'), long_maturity: Decimal=Decimal('10')) -> Decimal:
    """Calculate curve slope between two maturities"""
    short_rate = curve.get_rate(short_maturity)
    long_rate = curve.get_rate(long_maturity)
    return long_rate - short_rate

@staticmethod
def curve_curvature(curve: SpotCurve, short_maturity: Decimal=Decimal('2'), medium_maturity: Decimal=Decimal('5'), long_maturity: Decimal=Decimal('10')) -> Decimal:
    """Calculate curve curvature (butterfly)"""
    short_rate = curve.get_rate(short_maturity)
    medium_rate = curve.get_rate(medium_maturity)
    long_rate = curve.get_rate(long_maturity)
    return Decimal('2') * medium_rate - short_rate - long_rate

@staticmethod
def level_slope_curvature_decomposition(curve: SpotCurve) -> Tuple[Decimal, Decimal, Decimal]:
    """Decompose curve into level, slope, and curvature factors"""
    r2 = curve.get_rate(Decimal('2'))
    r5 = curve.get_rate(Decimal('5'))
    r10 = curve.get_rate(Decimal('10'))
    level = (r2 + r5 + r10) / Decimal('3')
    slope = r10 - r2
    curvature = Decimal('2') * r5 - r2 - r10
    return (level, slope, curvature)

@staticmethod
def duration_matched_curve_shift(curve: SpotCurve, target_duration: Decimal, shift_amount: Decimal) -> SpotCurve:
    """Apply duration-matched curve shift"""
    duration_scaling = target_duration / Decimal('5')
    scaled_shift = shift_amount * duration_scaling
    return curve.shift_curve(scaled_shift, 'parallel')

def create_flat_curve(rate: Decimal, maturities: List[Decimal], currency: Currency=Currency.USD) -> SpotCurve:
    """Create flat yield curve with constant rate"""
    rates = [rate] * len(maturities)
    yield_curve = YieldCurve(curve_date=date.today(), maturities=maturities, rates=rates, currency=currency, curve_type='spot')
    return SpotCurve(yield_curve)

class TermStructureTheories:
    """Implementation of classical term structure theories"""

    @staticmethod
    def pure_expectations_theory(forward_rates: List[Decimal], maturities: List[Decimal]) -> Dict[str, Decimal]:
        """Analyze yield curve under Pure Expectations Theory"""
        if len(forward_rates) != len(maturities):
            raise ValueError('Forward rates and maturities must have same length')
        results = {}
        for i, maturity in enumerate(maturities):
            if i == 0:
                spot_rate = forward_rates[i]
            else:
                product = Decimal('1')
                for j in range(i + 1):
                    product *= Decimal('1') + forward_rates[j]
                spot_rate = product ** (Decimal('1') / Decimal(str(i + 1))) - Decimal('1')
            results[f'spot_rate_{maturity}Y'] = spot_rate
            results[f'forward_rate_{maturity}Y'] = forward_rates[i]
        results['liquidity_premiums'] = [Decimal('0')] * len(maturities)
        results['theory'] = 'Pure Expectations Theory'
        results['risk_premium_assumption'] = 'Zero risk premiums'
        return results

    @staticmethod
    def liquidity_preference_theory(forward_rates: List[Decimal], maturities: List[Decimal], liquidity_premiums: List[Decimal]) -> Dict[str, Decimal]:
        """Analyze yield curve under Liquidity Preference Theory"""
        if len(forward_rates) != len(maturities) or len(liquidity_premiums) != len(maturities):
            raise ValueError('All input lists must have same length')
        results = {}
        expected_rates = []
        for i in range(len(forward_rates)):
            expected_rate = forward_rates[i] - liquidity_premiums[i]
            expected_rates.append(expected_rate)
        for i, maturity in enumerate(maturities):
            if i == 0:
                spot_rate = forward_rates[i]
            else:
                product = Decimal('1')
                for j in range(i + 1):
                    product *= Decimal('1') + forward_rates[j]
                spot_rate = product ** (Decimal('1') / Decimal(str(i + 1))) - Decimal('1')
            results[f'spot_rate_{maturity}Y'] = spot_rate
            results[f'expected_rate_{maturity}Y'] = expected_rates[i]
            results[f'liquidity_premium_{maturity}Y'] = liquidity_premiums[i]
        results['theory'] = 'Liquidity Preference Theory'
        results['risk_premium_assumption'] = 'Positive, increasing liquidity premiums'
        return results

    @staticmethod
    def market_segmentation_theory(supply_demand_factors: Dict[Decimal, Dict[str, Decimal]]) -> Dict[str, Decimal]:
        """Analyze yield curve under Market Segmentation Theory"""
        results = {}
        results['theory'] = 'Market Segmentation Theory'
        for maturity, factors in supply_demand_factors.items():
            supply = factors.get('supply', Decimal('1'))
            demand = factors.get('demand', Decimal('1'))
            base_rate = factors.get('base_rate', Decimal('0.03'))
            supply_demand_ratio = supply / demand if demand > 0 else Decimal('1')
            rate_adjustment = (supply_demand_ratio - Decimal('1')) * Decimal('0.01')
            adjusted_rate = base_rate + rate_adjustment
            results[f'rate_{maturity}Y'] = adjusted_rate
            results[f'supply_demand_ratio_{maturity}Y'] = supply_demand_ratio
            results[f'rate_adjustment_{maturity}Y'] = rate_adjustment
        results['arbitrage_assumption'] = 'Limited arbitrage between maturity segments'
        return results

    @staticmethod
    def preferred_habitat_theory(forward_rates: List[Decimal], maturities: List[Decimal], habitat_premiums: List[Decimal]) -> Dict[str, Decimal]:
        """Analyze yield curve under Preferred Habitat Theory"""
        if len(forward_rates) != len(maturities) or len(habitat_premiums) != len(maturities):
            raise ValueError('All input lists must have same length')
        results = {}
        expected_rates = []
        for i in range(len(forward_rates)):
            expected_rate = forward_rates[i] - habitat_premiums[i]
            expected_rates.append(expected_rate)
        for i, maturity in enumerate(maturities):
            if i == 0:
                spot_rate = forward_rates[i]
            else:
                product = Decimal('1')
                for j in range(i + 1):
                    product *= Decimal('1') + forward_rates[j]
                spot_rate = product ** (Decimal('1') / Decimal(str(i + 1))) - Decimal('1')
            results[f'spot_rate_{maturity}Y'] = spot_rate
            results[f'expected_rate_{maturity}Y'] = expected_rates[i]
            results[f'habitat_premium_{maturity}Y'] = habitat_premiums[i]
        results['theory'] = 'Preferred Habitat Theory'
        results['risk_premium_assumption'] = 'Risk premiums can be positive or negative'
        return results

@staticmethod
def market_segmentation_theory(supply_demand_factors: Dict[Decimal, Dict[str, Decimal]]) -> Dict[str, Decimal]:
    """Analyze yield curve under Market Segmentation Theory"""
    results = {}
    results['theory'] = 'Market Segmentation Theory'
    for maturity, factors in supply_demand_factors.items():
        supply = factors.get('supply', Decimal('1'))
        demand = factors.get('demand', Decimal('1'))
        base_rate = factors.get('base_rate', Decimal('0.03'))
        supply_demand_ratio = supply / demand if demand > 0 else Decimal('1')
        rate_adjustment = (supply_demand_ratio - Decimal('1')) * Decimal('0.01')
        adjusted_rate = base_rate + rate_adjustment
        results[f'rate_{maturity}Y'] = adjusted_rate
        results[f'supply_demand_ratio_{maturity}Y'] = supply_demand_ratio
        results[f'rate_adjustment_{maturity}Y'] = rate_adjustment
    results['arbitrage_assumption'] = 'Limited arbitrage between maturity segments'
    return results

class YieldCurveFactors:
    """Yield curve factor analysis and decomposition"""

    @staticmethod
    def level_slope_curvature_factors(spot_curve: SpotCurve, key_maturities: List[Decimal]=None) -> Dict[str, Decimal]:
        """Decompose yield curve into level, slope, and curvature factors"""
        if key_maturities is None:
            key_maturities = [Decimal('2'), Decimal('5'), Decimal('10')]
        if len(key_maturities) < 3:
            raise ValueError('Need at least 3 maturities for LSC decomposition')
        rates = [spot_curve.get_rate(maturity) for maturity in key_maturities]
        level = sum(rates) / Decimal(str(len(rates)))
        slope = rates[-1] - rates[0]
        if len(rates) >= 3:
            curvature = Decimal('2') * rates[1] - rates[0] - rates[-1]
        else:
            curvature = Decimal('0')
        factor_loadings = YieldCurveFactors._calculate_factor_loadings(spot_curve, key_maturities)
        return {'level_factor': level, 'slope_factor': slope, 'curvature_factor': curvature, 'factor_loadings': factor_loadings, 'explained_variance': {'level': Decimal('0.85'), 'slope': Decimal('0.12'), 'curvature': Decimal('0.03')}}

    @staticmethod
    def _calculate_factor_loadings(spot_curve: SpotCurve, key_maturities: List[Decimal]) -> Dict[str, List[Decimal]]:
        """Calculate factor loadings for level, slope, curvature"""
        maturities = spot_curve.curve.maturities
        n = len(maturities)
        level_loadings = [Decimal('1') / Decimal(str(n)) ** Decimal('0.5')] * n
        slope_loadings = []
        for i, maturity in enumerate(maturities):
            loading = Decimal('-1') + Decimal('2') * Decimal(str(i)) / Decimal(str(n - 1))
            slope_loadings.append(loading)
        curvature_loadings = []
        for i, maturity in enumerate(maturities):
            x = Decimal(str(i)) / Decimal(str(n - 1))
            loading = Decimal('2') * x * (Decimal('1') - x)
            curvature_loadings.append(loading)
        return {'level': level_loadings, 'slope': slope_loadings, 'curvature': curvature_loadings}

    @staticmethod
    def principal_component_analysis(historical_curves: List[SpotCurve]) -> Dict[str, any]:
        """Simplified PCA analysis of yield curve movements"""
        if len(historical_curves) < 2:
            raise ValueError('Need at least 2 historical curves for PCA')
        common_maturities = historical_curves[0].curve.maturities
        rate_matrix = []
        for curve in historical_curves:
            rates = [curve.get_rate(maturity) for maturity in common_maturities]
            rate_matrix.append(rates)
        n_curves = len(rate_matrix)
        n_maturities = len(common_maturities)
        mean_rates = []
        for j in range(n_maturities):
            mean_rate = sum((rate_matrix[i][j] for i in range(n_curves))) / Decimal(str(n_curves))
            mean_rates.append(mean_rate)
        rate_changes = []
        for i in range(n_curves):
            changes = [rate_matrix[i][j] - mean_rates[j] for j in range(n_maturities)]
            rate_changes.append(changes)
        pc1_loadings = [Decimal('1') / Decimal(str(n_maturities)) ** Decimal('0.5')] * n_maturities
        pc2_loadings = []
        for j in range(n_maturities):
            loading = Decimal('-1') + Decimal('2') * Decimal(str(j)) / Decimal(str(n_maturities - 1))
            pc2_loadings.append(loading)
        pc3_loadings = []
        for j in range(n_maturities):
            x = Decimal(str(j)) / Decimal(str(n_maturities - 1))
            loading = Decimal('2') * x * (Decimal('1') - x)
            pc3_loadings.append(loading)
        return {'principal_components': {'PC1_loadings': pc1_loadings, 'PC2_loadings': pc2_loadings, 'PC3_loadings': pc3_loadings}, 'explained_variance': [Decimal('0.85'), Decimal('0.12'), Decimal('0.03')], 'interpretation': ['Level', 'Slope', 'Curvature'], 'mean_rates': mean_rates, 'maturities': common_maturities}

@staticmethod
def level_slope_curvature_factors(spot_curve: SpotCurve, key_maturities: List[Decimal]=None) -> Dict[str, Decimal]:
    """Decompose yield curve into level, slope, and curvature factors"""
    if key_maturities is None:
        key_maturities = [Decimal('2'), Decimal('5'), Decimal('10')]
    if len(key_maturities) < 3:
        raise ValueError('Need at least 3 maturities for LSC decomposition')
    rates = [spot_curve.get_rate(maturity) for maturity in key_maturities]
    level = sum(rates) / Decimal(str(len(rates)))
    slope = rates[-1] - rates[0]
    if len(rates) >= 3:
        curvature = Decimal('2') * rates[1] - rates[0] - rates[-1]
    else:
        curvature = Decimal('0')
    factor_loadings = YieldCurveFactors._calculate_factor_loadings(spot_curve, key_maturities)
    return {'level_factor': level, 'slope_factor': slope, 'curvature_factor': curvature, 'factor_loadings': factor_loadings, 'explained_variance': {'level': Decimal('0.85'), 'slope': Decimal('0.12'), 'curvature': Decimal('0.03')}}

@staticmethod
def principal_component_analysis(historical_curves: List[SpotCurve]) -> Dict[str, any]:
    """Simplified PCA analysis of yield curve movements"""
    if len(historical_curves) < 2:
        raise ValueError('Need at least 2 historical curves for PCA')
    common_maturities = historical_curves[0].curve.maturities
    rate_matrix = []
    for curve in historical_curves:
        rates = [curve.get_rate(maturity) for maturity in common_maturities]
        rate_matrix.append(rates)
    n_curves = len(rate_matrix)
    n_maturities = len(common_maturities)
    mean_rates = []
    for j in range(n_maturities):
        mean_rate = sum((rate_matrix[i][j] for i in range(n_curves))) / Decimal(str(n_curves))
        mean_rates.append(mean_rate)
    rate_changes = []
    for i in range(n_curves):
        changes = [rate_matrix[i][j] - mean_rates[j] for j in range(n_maturities)]
        rate_changes.append(changes)
    pc1_loadings = [Decimal('1') / Decimal(str(n_maturities)) ** Decimal('0.5')] * n_maturities
    pc2_loadings = []
    for j in range(n_maturities):
        loading = Decimal('-1') + Decimal('2') * Decimal(str(j)) / Decimal(str(n_maturities - 1))
        pc2_loadings.append(loading)
    pc3_loadings = []
    for j in range(n_maturities):
        x = Decimal(str(j)) / Decimal(str(n_maturities - 1))
        loading = Decimal('2') * x * (Decimal('1') - x)
        pc3_loadings.append(loading)
    return {'principal_components': {'PC1_loadings': pc1_loadings, 'PC2_loadings': pc2_loadings, 'PC3_loadings': pc3_loadings}, 'explained_variance': [Decimal('0.85'), Decimal('0.12'), Decimal('0.03')], 'interpretation': ['Level', 'Slope', 'Curvature'], 'mean_rates': mean_rates, 'maturities': common_maturities}

class VolatilityStructure:
    """Term structure of volatility analysis"""

    @staticmethod
    def yield_volatility_structure(historical_yields: Dict[Decimal, List[Decimal]], window_size: int=252) -> Dict[Decimal, Dict[str, Decimal]]:
        """Calculate volatility structure across maturities"""
        volatility_structure = {}
        for maturity, yield_series in historical_yields.items():
            if len(yield_series) < window_size:
                continue
            returns = []
            for i in range(1, len(yield_series)):
                return_val = yield_series[i] - yield_series[i - 1]
                returns.append(return_val)
            volatilities = VolatilityStructure._calculate_rolling_volatility(returns, window_size)
            if volatilities:
                avg_volatility = sum(volatilities) / Decimal(str(len(volatilities)))
                max_volatility = max(volatilities)
                min_volatility = min(volatilities)
                volatility_structure[maturity] = {'average_volatility': avg_volatility, 'maximum_volatility': max_volatility, 'minimum_volatility': min_volatility, 'current_volatility': volatilities[-1] if volatilities else Decimal('0')}
        return volatility_structure

    @staticmethod
    def _calculate_rolling_volatility(returns: List[Decimal], window: int) -> List[Decimal]:
        """Calculate rolling volatility"""
        volatilities = []
        for i in range(window, len(returns) + 1):
            window_returns = returns[i - window:i]
            mean_return = sum(window_returns) / Decimal(str(len(window_returns)))
            variance = sum(((r - mean_return) ** 2 for r in window_returns)) / Decimal(str(len(window_returns) - 1))
            volatility = variance ** Decimal('0.5') * Decimal('252') ** Decimal('0.5')
            volatilities.append(volatility)
        return volatilities

    @staticmethod
    def volatility_smile_analysis(option_data: Dict[Decimal, Decimal]) -> Dict[str, Decimal]:
        """Analyze volatility smile/skew patterns"""
        if len(option_data) < 3:
            return {'error': 'Insufficient data for smile analysis'}
        strikes = sorted(option_data.keys())
        volatilities = [option_data[strike] for strike in strikes]
        atm_index = len(strikes) // 2
        atm_vol = volatilities[atm_index]
        if len(strikes) >= 3:
            low_strike_idx = len(strikes) // 4
            high_strike_idx = 3 * len(strikes) // 4
            skew_25d = volatilities[low_strike_idx] - volatilities[high_strike_idx]
        else:
            skew_25d = Decimal('0')
        if len(strikes) >= 3:
            butterfly = (volatilities[0] + volatilities[-1]) / Decimal('2') - atm_vol
        else:
            butterfly = Decimal('0')
        return {'atm_volatility': atm_vol, 'volatility_skew_25d': skew_25d, 'volatility_butterfly': butterfly, 'min_volatility': min(volatilities), 'max_volatility': max(volatilities), 'volatility_range': max(volatilities) - min(volatilities)}

    @staticmethod
    def term_structure_volatility_models(forward_rates: List[Decimal], volatilities: List[Decimal], model_type: str='ho_lee') -> Dict[str, any]:
        """Implement term structure volatility models"""
        if len(forward_rates) != len(volatilities):
            raise ValueError('Forward rates and volatilities must have same length')
        if model_type == 'ho_lee':
            return VolatilityStructure._ho_lee_model(forward_rates, volatilities)
        elif model_type == 'hull_white':
            return VolatilityStructure._hull_white_model(forward_rates, volatilities)
        elif model_type == 'black_karasinski':
            return VolatilityStructure._black_karasinski_model(forward_rates, volatilities)
        else:
            raise ValueError(f'Unknown model type: {model_type}')

    @staticmethod
    def _ho_lee_model(forward_rates: List[Decimal], volatilities: List[Decimal]) -> Dict[str, any]:
        """Ho-Lee model: dr = θ(t)dt + σdW"""
        avg_volatility = sum(volatilities) / Decimal(str(len(volatilities)))
        drift_function = []
        for i, rate in enumerate(forward_rates):
            if i == 0:
                drift = rate
            else:
                drift = forward_rates[i] - forward_rates[i - 1]
            drift_function.append(drift)
        return {'model': 'Ho-Lee', 'constant_volatility': avg_volatility, 'drift_function': drift_function, 'mean_reversion': Decimal('0'), 'characteristics': 'Normal rates, constant volatility'}

    @staticmethod
    def _hull_white_model(forward_rates: List[Decimal], volatilities: List[Decimal]) -> Dict[str, any]:
        """Hull-White model: dr = [θ(t) - ar]dt + σdW"""
        avg_volatility = sum(volatilities) / Decimal(str(len(volatilities)))
        mean_reversion = Decimal('0.1')
        long_term_mean = sum(forward_rates) / Decimal(str(len(forward_rates)))
        return {'model': 'Hull-White', 'volatility': avg_volatility, 'mean_reversion_speed': mean_reversion, 'long_term_mean': long_term_mean, 'characteristics': 'Normal rates, mean-reverting'}

    @staticmethod
    def _black_karasinski_model(forward_rates: List[Decimal], volatilities: List[Decimal]) -> Dict[str, any]:
        """Black-Karasinski model: d(ln r) = [θ(t) - a ln r]dt + σdW"""
        avg_volatility = sum(volatilities) / Decimal(str(len(volatilities)))
        log_rates = [Decimal(str(math.log(float(rate)))) for rate in forward_rates if rate > 0]
        if log_rates:
            avg_log_rate = sum(log_rates) / Decimal(str(len(log_rates)))
            mean_reversion = Decimal('0.15')
        else:
            avg_log_rate = Decimal('0')
            mean_reversion = Decimal('0')
        return {'model': 'Black-Karasinski', 'volatility': avg_volatility, 'mean_reversion_speed': mean_reversion, 'mean_log_rate': avg_log_rate, 'characteristics': 'Log-normal rates, mean-reverting'}

@staticmethod
def _hull_white_model(forward_rates: List[Decimal], volatilities: List[Decimal]) -> Dict[str, any]:
    """Hull-White model: dr = [θ(t) - ar]dt + σdW"""
    avg_volatility = sum(volatilities) / Decimal(str(len(volatilities)))
    mean_reversion = Decimal('0.1')
    long_term_mean = sum(forward_rates) / Decimal(str(len(forward_rates)))
    return {'model': 'Hull-White', 'volatility': avg_volatility, 'mean_reversion_speed': mean_reversion, 'long_term_mean': long_term_mean, 'characteristics': 'Normal rates, mean-reverting'}

@staticmethod
def _black_karasinski_model(forward_rates: List[Decimal], volatilities: List[Decimal]) -> Dict[str, any]:
    """Black-Karasinski model: d(ln r) = [θ(t) - a ln r]dt + σdW"""
    avg_volatility = sum(volatilities) / Decimal(str(len(volatilities)))
    log_rates = [Decimal(str(math.log(float(rate)))) for rate in forward_rates if rate > 0]
    if log_rates:
        avg_log_rate = sum(log_rates) / Decimal(str(len(log_rates)))
        mean_reversion = Decimal('0.15')
    else:
        avg_log_rate = Decimal('0')
        mean_reversion = Decimal('0')
    return {'model': 'Black-Karasinski', 'volatility': avg_volatility, 'mean_reversion_speed': mean_reversion, 'mean_log_rate': avg_log_rate, 'characteristics': 'Log-normal rates, mean-reverting'}

class RidingTheYieldCurve:
    """Yield curve riding strategies and analysis"""

    @staticmethod
    def rolling_yield_analysis(bond_maturity: Decimal, holding_period: Decimal, spot_curve: SpotCurve) -> Dict[str, Decimal]:
        """Analyze rolling yield for bond investment"""
        ValidationUtils.validate_positive(bond_maturity, 'Bond maturity')
        ValidationUtils.validate_positive(holding_period, 'Holding period')
        if holding_period >= bond_maturity:
            raise ValueError('Holding period must be less than bond maturity')
        current_yield = spot_curve.get_rate(bond_maturity)
        future_maturity = bond_maturity - holding_period
        if future_maturity > 0:
            future_yield = spot_curve.get_rate(future_maturity)
        else:
            future_yield = Decimal('0')
        current_price = Decimal('100')
        if future_maturity > 0:
            future_price = current_price * (Decimal('1') + current_yield) / (Decimal('1') + future_yield)
        else:
            future_price = Decimal('100')
        coupon_income = current_yield * holding_period * current_price
        capital_gain = future_price - current_price
        total_return = coupon_income + capital_gain
        if holding_period > 0:
            rolling_yield = total_return / (current_price * holding_period)
        else:
            rolling_yield = Decimal('0')
        return {'current_yield': current_yield, 'future_yield': future_yield, 'yield_change': future_yield - current_yield, 'current_price': current_price, 'future_price': future_price, 'capital_gain': capital_gain, 'coupon_income': coupon_income, 'total_return': total_return, 'rolling_yield': rolling_yield, 'excess_return': rolling_yield - current_yield}

    @staticmethod
    def optimal_maturity_selection(target_holding_period: Decimal, spot_curve: SpotCurve, maturity_range: Tuple[Decimal, Decimal]=(Decimal('1'), Decimal('30'))) -> Dict[str, Decimal]:
        """Find optimal bond maturity for yield curve riding"""
        ValidationUtils.validate_positive(target_holding_period, 'Target holding period')
        min_maturity, max_maturity = maturity_range
        test_maturities = []
        current_mat = min_maturity
        while current_mat <= max_maturity:
            if current_mat > target_holding_period:
                test_maturities.append(current_mat)
            current_mat += Decimal('0.5')
        best_maturity = None
        best_rolling_yield = Decimal('-999')
        results = {}
        for maturity in test_maturities:
            try:
                analysis = RidingTheYieldCurve.rolling_yield_analysis(maturity, target_holding_period, spot_curve)
                rolling_yield = analysis['rolling_yield']
                results[f'maturity_{maturity}Y'] = {'rolling_yield': rolling_yield, 'excess_return': analysis['excess_return'], 'yield_change': analysis['yield_change']}
                if rolling_yield > best_rolling_yield:
                    best_rolling_yield = rolling_yield
                    best_maturity = maturity
            except Exception:
                continue
        return {'optimal_maturity': best_maturity, 'optimal_rolling_yield': best_rolling_yield, 'target_holding_period': target_holding_period, 'maturity_analysis': results}

@staticmethod
def rolling_yield_analysis(bond_maturity: Decimal, holding_period: Decimal, spot_curve: SpotCurve) -> Dict[str, Decimal]:
    """Analyze rolling yield for bond investment"""
    ValidationUtils.validate_positive(bond_maturity, 'Bond maturity')
    ValidationUtils.validate_positive(holding_period, 'Holding period')
    if holding_period >= bond_maturity:
        raise ValueError('Holding period must be less than bond maturity')
    current_yield = spot_curve.get_rate(bond_maturity)
    future_maturity = bond_maturity - holding_period
    if future_maturity > 0:
        future_yield = spot_curve.get_rate(future_maturity)
    else:
        future_yield = Decimal('0')
    current_price = Decimal('100')
    if future_maturity > 0:
        future_price = current_price * (Decimal('1') + current_yield) / (Decimal('1') + future_yield)
    else:
        future_price = Decimal('100')
    coupon_income = current_yield * holding_period * current_price
    capital_gain = future_price - current_price
    total_return = coupon_income + capital_gain
    if holding_period > 0:
        rolling_yield = total_return / (current_price * holding_period)
    else:
        rolling_yield = Decimal('0')
    return {'current_yield': current_yield, 'future_yield': future_yield, 'yield_change': future_yield - current_yield, 'current_price': current_price, 'future_price': future_price, 'capital_gain': capital_gain, 'coupon_income': coupon_income, 'total_return': total_return, 'rolling_yield': rolling_yield, 'excess_return': rolling_yield - current_yield}

@staticmethod
def optimal_maturity_selection(target_holding_period: Decimal, spot_curve: SpotCurve, maturity_range: Tuple[Decimal, Decimal]=(Decimal('1'), Decimal('30'))) -> Dict[str, Decimal]:
    """Find optimal bond maturity for yield curve riding"""
    ValidationUtils.validate_positive(target_holding_period, 'Target holding period')
    min_maturity, max_maturity = maturity_range
    test_maturities = []
    current_mat = min_maturity
    while current_mat <= max_maturity:
        if current_mat > target_holding_period:
            test_maturities.append(current_mat)
        current_mat += Decimal('0.5')
    best_maturity = None
    best_rolling_yield = Decimal('-999')
    results = {}
    for maturity in test_maturities:
        try:
            analysis = RidingTheYieldCurve.rolling_yield_analysis(maturity, target_holding_period, spot_curve)
            rolling_yield = analysis['rolling_yield']
            results[f'maturity_{maturity}Y'] = {'rolling_yield': rolling_yield, 'excess_return': analysis['excess_return'], 'yield_change': analysis['yield_change']}
            if rolling_yield > best_rolling_yield:
                best_rolling_yield = rolling_yield
                best_maturity = maturity
        except Exception:
            continue
    return {'optimal_maturity': best_maturity, 'optimal_rolling_yield': best_rolling_yield, 'target_holding_period': target_holding_period, 'maturity_analysis': results}

def compare_term_structure_theories(spot_curve: SpotCurve, forward_curve: ForwardCurve) -> Dict[str, Dict]:
    """Compare different term structure theories"""
    maturities = [Decimal('1'), Decimal('2'), Decimal('5'), Decimal('10')]
    forward_rates = [forward_curve.get_forward_rate(Decimal('0'), mat) for mat in maturities]
    liquidity_premiums = [Decimal('0.001') * mat for mat in maturities]
    habitat_premiums = [Decimal('0.0005') * (Decimal('1') if i % 2 == 0 else Decimal('-1')) for i, mat in enumerate(maturities)]
    theories = {'pure_expectations': TermStructureTheories.pure_expectations_theory(forward_rates, maturities), 'liquidity_preference': TermStructureTheories.liquidity_preference_theory(forward_rates, maturities, liquidity_premiums), 'preferred_habitat': TermStructureTheories.preferred_habitat_theory(forward_rates, maturities, habitat_premiums)}
    return theories

def yield_curve_scenario_analysis(base_curve: SpotCurve, scenarios: Dict[str, Dict[str, Decimal]]) -> Dict[str, Dict]:
    """Analyze yield curve under different scenarios"""
    results = {}
    base_factors = YieldCurveFactors.level_slope_curvature_factors(base_curve)
    results['base_case'] = base_factors
    for scenario_name, shifts in scenarios.items():
        shift_type = shifts.get('type', 'parallel')
        shift_amount = shifts.get('amount', Decimal('0.01'))
        shifted_curve = base_curve.shift_curve(shift_amount, shift_type)
        scenario_factors = YieldCurveFactors.level_slope_curvature_factors(shifted_curve)
        results[scenario_name] = {'factors': scenario_factors, 'shift_type': shift_type, 'shift_amount': shift_amount}
    return results

class PerformanceCalculations:
    """Performance and risk-adjusted return calculations"""

    @staticmethod
    def sharpe_ratio(returns: Union[np.ndarray, pd.Series], risk_free_rate: float=MathConstants.DEFAULT_RISK_FREE_RATE, annualize: bool=True) -> float:
        """Calculate Sharpe ratio"""
        if not validate_returns(returns):
            raise ValueError(ERROR_MESSAGES['insufficient_data'])
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate / MathConstants.TRADING_DAYS_YEAR
        mean_excess = np.mean(excess_returns)
        std_excess = np.std(excess_returns, ddof=1)
        if std_excess == 0:
            return 0.0
        sharpe = mean_excess / std_excess
        if annualize:
            sharpe *= MathConstants.SQRT_TRADING_DAYS
        return sharpe

    @staticmethod
    def treynor_ratio(returns: Union[np.ndarray, pd.Series], beta: float, risk_free_rate: float=MathConstants.DEFAULT_RISK_FREE_RATE, annualize: bool=True) -> float:
        """Calculate Treynor ratio"""
        if not validate_returns(returns):
            raise ValueError(ERROR_MESSAGES['insufficient_data'])
        returns_array = np.array(returns)
        mean_return = np.mean(returns_array)
        if annualize:
            mean_return *= MathConstants.TRADING_DAYS_YEAR
            risk_free_rate_annual = risk_free_rate
        else:
            risk_free_rate_annual = risk_free_rate / MathConstants.TRADING_DAYS_YEAR
        if beta == 0:
            return 0.0
        return (mean_return - risk_free_rate_annual) / beta

    @staticmethod
    def information_ratio(portfolio_returns: Union[np.ndarray, pd.Series], benchmark_returns: Union[np.ndarray, pd.Series]) -> float:
        """Calculate information ratio"""
        excess_returns = np.array(portfolio_returns) - np.array(benchmark_returns)
        if len(excess_returns) < 2:
            raise ValueError(ERROR_MESSAGES['insufficient_data'])
        mean_excess = np.mean(excess_returns)
        std_excess = np.std(excess_returns, ddof=1)
        if std_excess == 0:
            return 0.0
        return mean_excess / std_excess * MathConstants.SQRT_TRADING_DAYS

    @staticmethod
    def jensen_alpha(portfolio_returns: Union[np.ndarray, pd.Series], market_returns: Union[np.ndarray, pd.Series], beta: float, risk_free_rate: float=MathConstants.DEFAULT_RISK_FREE_RATE) -> float:
        """Calculate Jensen's alpha"""
        portfolio_mean = np.mean(portfolio_returns) * MathConstants.TRADING_DAYS_YEAR
        market_mean = np.mean(market_returns) * MathConstants.TRADING_DAYS_YEAR
        expected_return = risk_free_rate + beta * (market_mean - risk_free_rate)
        alpha = portfolio_mean - expected_return
        return alpha

    @staticmethod
    def m_squared(portfolio_returns: Union[np.ndarray, pd.Series], market_returns: Union[np.ndarray, pd.Series], risk_free_rate: float=MathConstants.DEFAULT_RISK_FREE_RATE) -> float:
        """Calculate M-squared (M²) measure"""
        portfolio_sharpe = PerformanceCalculations.sharpe_ratio(portfolio_returns, risk_free_rate)
        market_sharpe = PerformanceCalculations.sharpe_ratio(market_returns, risk_free_rate)
        market_std = np.std(market_returns, ddof=1) * MathConstants.SQRT_TRADING_DAYS
        return (portfolio_sharpe - market_sharpe) * market_std

    @staticmethod
    def sortino_ratio(returns: Union[np.ndarray, pd.Series], target_return: float=0.0, risk_free_rate: float=MathConstants.DEFAULT_RISK_FREE_RATE, annualize: bool=True) -> float:
        """Calculate Sortino ratio"""
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate / MathConstants.TRADING_DAYS_YEAR
        mean_excess = np.mean(excess_returns)
        downside_dev = StatisticalCalculations.calculate_downside_deviation(returns_array, target_return, annualize=False)
        if downside_dev == 0:
            return 0.0
        sortino = mean_excess / downside_dev
        if annualize:
            sortino *= MathConstants.SQRT_TRADING_DAYS
        return sortino

@staticmethod
def m_squared(portfolio_returns: Union[np.ndarray, pd.Series], market_returns: Union[np.ndarray, pd.Series], risk_free_rate: float=MathConstants.DEFAULT_RISK_FREE_RATE) -> float:
    """Calculate M-squared (M²) measure"""
    portfolio_sharpe = PerformanceCalculations.sharpe_ratio(portfolio_returns, risk_free_rate)
    market_sharpe = PerformanceCalculations.sharpe_ratio(market_returns, risk_free_rate)
    market_std = np.std(market_returns, ddof=1) * MathConstants.SQRT_TRADING_DAYS
    return (portfolio_sharpe - market_sharpe) * market_std

class ValuationMultiples:
    """Cyclical effects on valuation multiples"""

    @staticmethod
    def multiple_analysis() -> Dict:
        """Analyze cyclical effects on valuation multiples"""
        return {'pe_ratio_cycles': {'expansion': 'Rising P/E as growth expectations improve', 'peak': 'Peak P/E but vulnerable to disappointment', 'contraction': 'Falling P/E as earnings decline', 'trough': 'Low P/E but earnings depressed'}, 'ev_ebitda_cycles': {'advantages': 'Less affected by depreciation and financial structure', 'cycle_behavior': 'Similar pattern to P/E but less volatile', 'sector_utility': 'Particularly useful for capital-intensive sectors'}, 'price_to_book': {'cycle_stability': 'More stable through cycles', 'financial_sectors': 'Key metric for banks and insurers', 'asset_quality': 'Reflects asset quality and franchise value'}}

    @staticmethod
    def calculate_normalized_multiples(current_earnings: float, normalized_earnings: float, current_price: float) -> Dict:
        """Calculate normalized valuation multiples"""
        current_pe = current_price / current_earnings if current_earnings > 0 else float('inf')
        normalized_pe = current_price / normalized_earnings if normalized_earnings > 0 else float('inf')
        return {'current_pe': current_pe, 'normalized_pe': normalized_pe, 'valuation_assessment': {'current_basis': 'Expensive' if current_pe > 20 else 'Fair' if current_pe > 15 else 'Cheap', 'normalized_basis': 'Expensive' if normalized_pe > 18 else 'Fair' if normalized_pe > 12 else 'Cheap'}, 'cycle_adjustment': normalized_pe - current_pe}

@staticmethod
def calculate_normalized_multiples(current_earnings: float, normalized_earnings: float, current_price: float) -> Dict:
    """Calculate normalized valuation multiples"""
    current_pe = current_price / current_earnings if current_earnings > 0 else float('inf')
    normalized_pe = current_price / normalized_earnings if normalized_earnings > 0 else float('inf')
    return {'current_pe': current_pe, 'normalized_pe': normalized_pe, 'valuation_assessment': {'current_basis': 'Expensive' if current_pe > 20 else 'Fair' if current_pe > 15 else 'Cheap', 'normalized_basis': 'Expensive' if normalized_pe > 18 else 'Fair' if normalized_pe > 12 else 'Cheap'}, 'cycle_adjustment': normalized_pe - current_pe}

class RiskManagement:
    """Main risk management interface"""

    def __init__(self, parameters: RiskParameters=DEFAULT_RISK_PARAMS):
        self.parameters = parameters
        self.governance = RiskGovernance()
        self.risk_budgeting = None

    def comprehensive_risk_analysis(self, returns_data: Union[np.ndarray, Dict[str, np.ndarray]], weights: Optional[np.ndarray]=None, portfolio_value: float=1000000) -> Dict:
        """Perform comprehensive risk analysis"""
        if isinstance(returns_data, dict):
            returns_matrix = np.array([returns_data[asset] for asset in returns_data.keys()]).T
            if weights is None:
                weights = np.ones(len(returns_data)) / len(returns_data)
            portfolio_returns = np.dot(returns_matrix, weights)
            asset_names = list(returns_data.keys())
        else:
            portfolio_returns = np.array(returns_data)
            returns_matrix = portfolio_returns.reshape(-1, 1)
            weights = np.array([1.0])
            asset_names = ['Portfolio']
        results = {'basic_risk_metrics': self._calculate_basic_risk_metrics(portfolio_returns), 'var_analysis': self._comprehensive_var_analysis(portfolio_returns), 'stress_testing': self._perform_stress_testing(portfolio_returns), 'risk_decomposition': None}
        if len(asset_names) > 1:
            results['risk_decomposition'] = VaRCalculations.component_var(portfolio_returns, returns_matrix, weights)
        results['dollar_metrics'] = self._convert_to_dollar_metrics(results, portfolio_value)
        return results

    def _calculate_basic_risk_metrics(self, returns: np.ndarray) -> Dict:
        """Calculate basic risk metrics"""
        return {'volatility_daily': np.std(returns, ddof=1), 'volatility_annual': np.std(returns, ddof=1) * np.sqrt(MathConstants.TRADING_DAYS_YEAR), 'downside_deviation': StatisticalCalculations.calculate_downside_deviation(returns), 'max_drawdown': self._calculate_max_drawdown(returns), 'skewness': stats.skew(returns), 'kurtosis': stats.kurtosis(returns, fisher=False), 'jarque_bera_test': stats.jarque_bera(returns)}

    def _comprehensive_var_analysis(self, returns: np.ndarray) -> Dict:
        """Comprehensive VaR analysis with multiple methods"""
        var_results = {}
        for confidence_level in self.parameters.var_confidence_levels:
            var_results[f'var_{int(confidence_level * 100)}'] = {'parametric_normal': VaRCalculations.parametric_var(returns, confidence_level, distribution='normal'), 'parametric_t': VaRCalculations.parametric_var(returns, confidence_level, distribution='t_distribution'), 'historical': {'var': RiskCalculations.value_at_risk_historical(returns, confidence_level), 'cvar': RiskCalculations.conditional_value_at_risk(returns, confidence_level)}, 'monte_carlo': VaRCalculations.monte_carlo_var(returns, confidence_level, num_simulations=self.parameters.monte_carlo_simulations)}
        return var_results

    def _perform_stress_testing(self, returns: np.ndarray) -> Dict:
        """Perform comprehensive stress testing"""
        return ScenarioAnalysis.stress_testing(returns, self.parameters.stress_scenarios)

    def _calculate_max_drawdown(self, returns: np.ndarray) -> Dict:
        """Calculate maximum drawdown statistics"""
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_dd = np.min(drawdown)
        max_dd_idx = np.argmin(drawdown)
        peak_idx = np.argmax(running_max[:max_dd_idx + 1]) if max_dd_idx > 0 else 0
        return {'max_drawdown': max_dd, 'peak_to_trough_days': max_dd_idx - peak_idx, 'drawdown_series': drawdown}

    def _convert_to_dollar_metrics(self, results: Dict, portfolio_value: float) -> Dict:
        """Convert percentage metrics to dollar amounts"""
        dollar_metrics = {}
        if 'var_analysis' in results:
            for var_level, var_data in results['var_analysis'].items():
                dollar_metrics[var_level] = {}
                if 'historical' in var_data:
                    dollar_metrics[var_level]['historical_var'] = var_data['historical']['var'] * portfolio_value
                    dollar_metrics[var_level]['historical_cvar'] = var_data['historical']['cvar'] * portfolio_value
                if 'parametric_normal' in var_data:
                    dollar_metrics[var_level]['parametric_var'] = var_data['parametric_normal']['var'] * portfolio_value
        return dollar_metrics

def _comprehensive_var_analysis(self, returns: np.ndarray) -> Dict:
    """Comprehensive VaR analysis with multiple methods"""
    var_results = {}
    for confidence_level in self.parameters.var_confidence_levels:
        var_results[f'var_{int(confidence_level * 100)}'] = {'parametric_normal': VaRCalculations.parametric_var(returns, confidence_level, distribution='normal'), 'parametric_t': VaRCalculations.parametric_var(returns, confidence_level, distribution='t_distribution'), 'historical': {'var': RiskCalculations.value_at_risk_historical(returns, confidence_level), 'cvar': RiskCalculations.conditional_value_at_risk(returns, confidence_level)}, 'monte_carlo': VaRCalculations.monte_carlo_var(returns, confidence_level, num_simulations=self.parameters.monte_carlo_simulations)}
    return var_results

class DataProcessor:
    """
    Universal financial data processor supporting multiple data sources and formats.
    Ensures CFA-compliant standardization and validation.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_standard_mappings()

    def _initialize_standard_mappings(self):
        """Initialize standard account mappings for different reporting standards"""
        self.income_statement_mapping = {'revenue': ['revenue', 'sales', 'net_sales', 'total_revenue', 'net_revenue'], 'cost_of_sales': ['cost_of_sales', 'cost_of_goods_sold', 'cogs', 'cost_of_revenue'], 'gross_profit': ['gross_profit', 'gross_income'], 'operating_expenses': ['operating_expenses', 'total_operating_expenses'], 'selling_expenses': ['selling_expenses', 'sales_expenses', 'marketing_expenses'], 'administrative_expenses': ['administrative_expenses', 'admin_expenses', 'general_admin'], 'rd_expenses': ['research_development', 'rd_expenses', 'r_and_d'], 'depreciation': ['depreciation', 'depreciation_amortization', 'da_expense'], 'operating_income': ['operating_income', 'ebit', 'operating_profit'], 'interest_expense': ['interest_expense', 'interest_cost', 'finance_costs'], 'interest_income': ['interest_income', 'interest_revenue'], 'other_income': ['other_income', 'other_revenue', 'non_operating_income'], 'pretax_income': ['pretax_income', 'ebt', 'income_before_tax'], 'tax_expense': ['tax_expense', 'income_tax', 'provision_for_taxes'], 'net_income': ['net_income', 'net_profit', 'profit_after_tax'], 'discontinued_operations': ['discontinued_operations', 'discontinued_ops'], 'extraordinary_items': ['extraordinary_items', 'exceptional_items'], 'basic_eps': ['basic_eps', 'earnings_per_share_basic'], 'diluted_eps': ['diluted_eps', 'earnings_per_share_diluted'], 'shares_outstanding_basic': ['shares_outstanding_basic', 'basic_shares'], 'shares_outstanding_diluted': ['shares_outstanding_diluted', 'diluted_shares']}
        self.balance_sheet_mapping = {'cash_equivalents': ['cash', 'cash_equivalents', 'cash_and_equivalents'], 'short_term_investments': ['short_term_investments', 'marketable_securities'], 'accounts_receivable': ['accounts_receivable', 'receivables', 'trade_receivables'], 'inventory': ['inventory', 'inventories'], 'prepaid_expenses': ['prepaid_expenses', 'prepaid_assets'], 'current_assets': ['current_assets', 'total_current_assets'], 'ppe_gross': ['ppe_gross', 'property_plant_equipment_gross'], 'accumulated_depreciation': ['accumulated_depreciation', 'accum_depreciation'], 'ppe_net': ['ppe_net', 'property_plant_equipment_net'], 'intangible_assets': ['intangible_assets', 'intangibles'], 'goodwill': ['goodwill'], 'long_term_investments': ['long_term_investments', 'investments'], 'total_assets': ['total_assets', 'assets'], 'accounts_payable': ['accounts_payable', 'payables', 'trade_payables'], 'short_term_debt': ['short_term_debt', 'current_debt'], 'accrued_liabilities': ['accrued_liabilities', 'accrued_expenses'], 'current_liabilities': ['current_liabilities', 'total_current_liabilities'], 'long_term_debt': ['long_term_debt', 'non_current_debt'], 'deferred_tax_liability': ['deferred_tax_liability', 'deferred_tax_liab'], 'other_liabilities': ['other_liabilities', 'other_non_current_liab'], 'total_liabilities': ['total_liabilities', 'liabilities'], 'common_stock': ['common_stock', 'share_capital'], 'retained_earnings': ['retained_earnings'], 'accumulated_oci': ['accumulated_oci', 'other_comprehensive_income'], 'treasury_stock': ['treasury_stock', 'treasury_shares'], 'total_equity': ['total_equity', 'shareholders_equity', 'stockholders_equity']}
        self.cash_flow_mapping = {'net_income_cf': ['net_income', 'profit_after_tax'], 'depreciation_cf': ['depreciation', 'depreciation_amortization'], 'amortization_cf': ['amortization'], 'stock_compensation': ['stock_based_compensation', 'share_based_comp'], 'deferred_tax': ['deferred_tax', 'deferred_tax_expense'], 'working_capital_change': ['working_capital_change', 'change_working_capital'], 'accounts_receivable_change': ['accounts_receivable_change'], 'inventory_change': ['inventory_change'], 'accounts_payable_change': ['accounts_payable_change'], 'operating_cash_flow': ['operating_cash_flow', 'cash_from_operations'], 'capex': ['capital_expenditures', 'capex', 'ppe_investments'], 'acquisitions': ['acquisitions', 'business_acquisitions'], 'asset_sales': ['asset_sales', 'asset_disposals'], 'investment_purchases': ['investment_purchases', 'securities_purchased'], 'investment_sales': ['investment_sales', 'securities_sold'], 'investing_cash_flow': ['investing_cash_flow', 'cash_from_investing'], 'debt_issued': ['debt_issued', 'debt_proceeds'], 'debt_repaid': ['debt_repaid', 'debt_repayments'], 'equity_issued': ['equity_issued', 'stock_issued'], 'equity_repurchased': ['equity_repurchased', 'stock_repurchased'], 'dividends_paid': ['dividends_paid', 'dividend_payments'], 'financing_cash_flow': ['financing_cash_flow', 'cash_from_financing'], 'net_cash_change': ['net_cash_change', 'net_change_cash'], 'cash_beginning': ['cash_beginning_period', 'beginning_cash'], 'cash_ending': ['cash_ending_period', 'ending_cash']}

    def process_data(self, data: Union[Dict, pd.DataFrame, str], source_type: DataSource, company_info: CompanyInfo, period_info: FinancialPeriod) -> FinancialStatements:
        """
        Main entry point for processing financial data from any source

        Args:
            data: Raw financial data
            source_type: Type of data source
            company_info: Company identification information
            period_info: Financial period information

        Returns:
            FinancialStatements: Standardized financial statement object
        """
        try:
            raw_data = self._load_data(data, source_type)
            self._validate_raw_data(raw_data)
            standardized_data = self._standardize_accounts(raw_data)
            statements = FinancialStatements(company_info=company_info, period_info=period_info)
            statements.income_statement = self._extract_income_statement(standardized_data)
            statements.balance_sheet = self._extract_balance_sheet(standardized_data)
            statements.cash_flow = self._extract_cash_flow(standardized_data)
            statements.equity_statement = self._extract_equity_statement(standardized_data)
            statements.notes = self._extract_notes(standardized_data)
            statements.data_quality = self._assess_data_quality(statements)
            self._validate_financial_statements(statements)
            self.logger.info(f'Successfully processed data for {company_info.ticker} - {period_info.period_end}')
            return statements
        except Exception as e:
            self.logger.error(f'Error processing data: {str(e)}')
            raise

    def _load_data(self, data: Union[Dict, pd.DataFrame, str], source_type: DataSource) -> Dict:
        """Load data from various sources"""
        if source_type == DataSource.CSV:
            if isinstance(data, str):
                df = pd.read_csv(data)
            else:
                df = data
            return df.to_dict('records')[0] if len(df) == 1 else df.to_dict('list')
        elif source_type == DataSource.EXCEL:
            if isinstance(data, str):
                df = pd.read_excel(data)
            else:
                df = data
            return df.to_dict('records')[0] if len(df) == 1 else df.to_dict('list')
        elif source_type == DataSource.JSON:
            if isinstance(data, str):
                import json
                with open(data, 'r') as f:
                    return json.load(f)
            return data
        elif source_type in [DataSource.API, DataSource.TERMINAL, DataSource.MANUAL]:
            return data if isinstance(data, dict) else data.to_dict()
        else:
            raise ValueError(f'Unsupported source type: {source_type}')

    def _standardize_accounts(self, raw_data: Dict) -> Dict:
        """Standardize account names using mapping dictionaries"""
        standardized = {}
        raw_lower = {k.lower().replace(' ', '_').replace('-', '_'): v for k, v in raw_data.items()}
        all_mappings = {**self.income_statement_mapping, **self.balance_sheet_mapping, **self.cash_flow_mapping}
        for standard_name, possible_names in all_mappings.items():
            for possible_name in possible_names:
                if possible_name.lower() in raw_lower:
                    standardized[standard_name] = raw_lower[possible_name.lower()]
                    break
        for orig_key, value in raw_lower.items():
            if not any((orig_key in mapping for mapping in all_mappings.values())):
                standardized[orig_key] = value
        return standardized

    def _extract_income_statement(self, data: Dict) -> Dict[str, float]:
        """Extract and organize income statement items"""
        income_items = {}
        for key in self.income_statement_mapping.keys():
            if key in data:
                income_items[key] = float(data[key]) if data[key] is not None else 0.0
        if 'gross_profit' not in income_items and 'revenue' in income_items and ('cost_of_sales' in income_items):
            income_items['gross_profit'] = income_items['revenue'] - income_items['cost_of_sales']
        if 'operating_income' not in income_items and 'gross_profit' in income_items and ('operating_expenses' in income_items):
            income_items['operating_income'] = income_items['gross_profit'] - income_items['operating_expenses']
        return income_items

    def _extract_balance_sheet(self, data: Dict) -> Dict[str, float]:
        """Extract and organize balance sheet items"""
        balance_items = {}
        for key in self.balance_sheet_mapping.keys():
            if key in data:
                balance_items[key] = float(data[key]) if data[key] is not None else 0.0
        return balance_items

    def _extract_cash_flow(self, data: Dict) -> Dict[str, float]:
        """Extract and organize cash flow statement items"""
        cf_items = {}
        for key in self.cash_flow_mapping.keys():
            if key in data:
                cf_items[key] = float(data[key]) if data[key] is not None else 0.0
        return cf_items

    def _extract_equity_statement(self, data: Dict) -> Dict[str, float]:
        """Extract equity statement information"""
        equity_items = {}
        equity_keys = ['common_stock', 'retained_earnings', 'accumulated_oci', 'treasury_stock']
        for key in equity_keys:
            if key in data:
                equity_items[key] = float(data[key]) if data[key] is not None else 0.0
        return equity_items

    def _extract_notes(self, data: Dict) -> Dict[str, Any]:
        """Extract notes and supplementary information"""
        notes = {}
        note_keywords = ['accounting_policy', 'segment', 'geographic', 'related_party', 'contingency', 'commitment', 'subsequent_event']
        for key, value in data.items():
            if any((keyword in key.lower() for keyword in note_keywords)):
                notes[key] = value
        return notes

    def _validate_raw_data(self, data: Dict):
        """Validate raw data structure and completeness"""
        if not data:
            raise ValueError('Empty data provided')
        required_fields = ['revenue', 'total_assets', 'total_equity']
        missing_fields = []
        data_lower = {k.lower(): v for k, v in data.items()}
        for field in required_fields:
            field_found = False
            if field in self.income_statement_mapping:
                for possible_name in self.income_statement_mapping[field]:
                    if possible_name.lower() in data_lower:
                        field_found = True
                        break
            elif field in self.balance_sheet_mapping:
                for possible_name in self.balance_sheet_mapping[field]:
                    if possible_name.lower() in data_lower:
                        field_found = True
                        break
            if not field_found:
                missing_fields.append(field)
        if missing_fields:
            self.logger.warning(f'Missing recommended fields: {missing_fields}')

    def _validate_financial_statements(self, statements: FinancialStatements):
        """Validate financial statement integrity and relationships"""
        errors = []
        warnings = []
        if statements.balance_sheet:
            assets = statements.balance_sheet.get('total_assets', 0)
            liabilities = statements.balance_sheet.get('total_liabilities', 0)
            equity = statements.balance_sheet.get('total_equity', 0)
            if abs(assets - (liabilities + equity)) > 0.01:
                errors.append(f"Balance sheet doesn't balance: Assets({assets}) != Liabilities({liabilities}) + Equity({equity})")
        if statements.cash_flow:
            net_change = statements.cash_flow.get('net_cash_change', 0)
            beginning = statements.cash_flow.get('cash_beginning', 0)
            ending = statements.cash_flow.get('cash_ending', 0)
            if abs(net_change - (ending - beginning)) > 0.01:
                warnings.append("Cash flow net change doesn't match beginning/ending cash difference")
        if statements.income_statement:
            net_income = statements.income_statement.get('net_income', 0)
            basic_eps = statements.income_statement.get('basic_eps', 0)
            basic_shares = statements.income_statement.get('shares_outstanding_basic', 0)
            if basic_eps and basic_shares and (abs(basic_eps - net_income / basic_shares) > 0.01):
                warnings.append('Basic EPS calculation inconsistent with net income and shares outstanding')
        statements.data_quality['validation_errors'] = errors
        statements.data_quality['validation_warnings'] = warnings
        if errors:
            raise ValueError(f'Financial statement validation failed: {errors}')

    def _assess_data_quality(self, statements: FinancialStatements) -> Dict[str, Any]:
        """Assess data quality and completeness"""
        quality_metrics = {'completeness_score': 0.0, 'consistency_score': 0.0, 'missing_fields': [], 'data_issues': []}
        total_expected_fields = len(self.income_statement_mapping) + len(self.balance_sheet_mapping) + len(self.cash_flow_mapping)
        total_present_fields = len(statements.income_statement) + len(statements.balance_sheet) + len(statements.cash_flow)
        quality_metrics['completeness_score'] = min(total_present_fields / total_expected_fields, 1.0)
        critical_fields = ['revenue', 'net_income', 'total_assets', 'total_equity', 'operating_cash_flow']
        for field in critical_fields:
            if field not in statements.income_statement and field not in statements.balance_sheet and (field not in statements.cash_flow):
                quality_metrics['missing_fields'].append(field)
        consistency_checks = 0
        passed_checks = 0
        if statements.balance_sheet.get('current_assets', 0) <= statements.balance_sheet.get('total_assets', 0):
            passed_checks += 1
        consistency_checks += 1
        if statements.income_statement.get('revenue', 0) > 0:
            passed_checks += 1
        consistency_checks += 1
        quality_metrics['consistency_score'] = passed_checks / consistency_checks if consistency_checks > 0 else 0.0
        return quality_metrics

    def convert_currency(self, statements: FinancialStatements, target_currency: str, exchange_rates: Dict[str, float]) -> FinancialStatements:
        """Convert financial statements to target currency"""
        pass

    def adjust_for_inflation(self, statements: FinancialStatements, inflation_rate: float) -> FinancialStatements:
        """Adjust financial statements for inflation (hyperinflationary economies)"""
        pass

def _extract_equity_statement(self, data: Dict) -> Dict[str, float]:
    """Extract equity statement information"""
    equity_items = {}
    equity_keys = ['common_stock', 'retained_earnings', 'accumulated_oci', 'treasury_stock']
    for key in equity_keys:
        if key in data:
            equity_items[key] = float(data[key]) if data[key] is not None else 0.0
    return equity_items

class BaseAnalyzer(ABC):
    """
    Abstract base class for all financial statement analyzers.
    Implements CFA Institute analysis framework and best practices.
    """

    def __init__(self, enable_logging: bool=True):
        """Initialize base analyzer with common functionality"""
        self.logger = logging.getLogger(self.__class__.__name__) if enable_logging else None
        self._initialize_benchmarks()
        self._initialize_formulas()

    def _initialize_benchmarks(self):
        """Initialize industry benchmarks and thresholds"""
        self.liquidity_benchmarks = {'current_ratio': {'excellent': 2.0, 'good': 1.5, 'adequate': 1.2, 'poor': 1.0}, 'quick_ratio': {'excellent': 1.5, 'good': 1.0, 'adequate': 0.8, 'poor': 0.5}, 'cash_ratio': {'excellent': 0.5, 'good': 0.3, 'adequate': 0.2, 'poor': 0.1}}
        self.activity_benchmarks = {'asset_turnover': {'excellent': 2.0, 'good': 1.5, 'adequate': 1.0, 'poor': 0.5}, 'inventory_turnover': {'excellent': 12.0, 'good': 8.0, 'adequate': 6.0, 'poor': 4.0}, 'receivables_turnover': {'excellent': 12.0, 'good': 8.0, 'adequate': 6.0, 'poor': 4.0}}
        self.solvency_benchmarks = {'debt_to_equity': {'excellent': 0.3, 'good': 0.5, 'adequate': 1.0, 'poor': 2.0}, 'debt_to_assets': {'excellent': 0.2, 'good': 0.3, 'adequate': 0.5, 'poor': 0.7}, 'interest_coverage': {'excellent': 10.0, 'good': 5.0, 'adequate': 2.5, 'poor': 1.5}}
        self.profitability_benchmarks = {'gross_margin': {'excellent': 0.4, 'good': 0.3, 'adequate': 0.2, 'poor': 0.1}, 'operating_margin': {'excellent': 0.2, 'good': 0.15, 'adequate': 0.1, 'poor': 0.05}, 'net_margin': {'excellent': 0.15, 'good': 0.1, 'adequate': 0.05, 'poor': 0.02}, 'roe': {'excellent': 0.2, 'good': 0.15, 'adequate': 0.1, 'poor': 0.05}, 'roa': {'excellent': 0.15, 'good': 0.1, 'adequate': 0.05, 'poor': 0.02}}
        self.quality_thresholds = {'earnings_quality': {'high': 80, 'moderate': 60, 'low': 40}, 'cash_flow_quality': {'high': 80, 'moderate': 60, 'low': 40}, 'balance_sheet_quality': {'high': 80, 'moderate': 60, 'low': 40}}

    def _initialize_formulas(self):
        """Initialize standard financial formulas and calculations"""
        self.formula_registry = {}

    @abstractmethod
    def analyze(self, statements: FinancialStatements, comparative_data: Optional[List[FinancialStatements]]=None, industry_data: Optional[Dict]=None) -> List[AnalysisResult]:
        """
        Main analysis method - must be implemented by subclasses

        Args:
            statements: Current period financial statements
            comparative_data: Historical data for trend analysis
            industry_data: Industry benchmarks and peer data

        Returns:
            List of analysis results
        """
        pass

    @abstractmethod
    def get_key_metrics(self, statements: FinancialStatements) -> Dict[str, float]:
        """Return key metrics calculated by this analyzer"""
        pass

    def validate_data_sufficiency(self, statements: FinancialStatements, required_fields: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate that required data fields are present for analysis

        Args:
            statements: Financial statements to validate
            required_fields: List of required field names

        Returns:
            Tuple of (is_sufficient, missing_fields)
        """
        missing_fields = []
        all_data = {**statements.income_statement, **statements.balance_sheet, **statements.cash_flow}
        for field in required_fields:
            if field not in all_data or all_data[field] is None:
                missing_fields.append(field)
        is_sufficient = len(missing_fields) == 0
        if not is_sufficient and self.logger:
            self.logger.warning(f'Missing required fields for analysis: {missing_fields}')
        return (is_sufficient, missing_fields)

    def calculate_trend(self, values: List[float], periods: List[str]) -> ComparativeAnalysis:
        """
        Calculate trend analysis for a series of values

        Args:
            values: List of metric values over time
            periods: List of period identifiers

        Returns:
            ComparativeAnalysis object with trend information
        """
        if len(values) < 2:
            return ComparativeAnalysis(periods=periods, values=values, trend_analysis='Insufficient data for trend analysis', volatility_measure=0.0)
        if len(values) > 1:
            if values[0] != 0:
                if len(values) == 2:
                    growth_rate = values[-1] / values[0] - 1
                else:
                    n_periods = len(values) - 1
                    growth_rate = (values[-1] / values[0]) ** (1 / n_periods) - 1
            else:
                growth_rate = None
        else:
            growth_rate = None
        mean_value = np.mean(values)
        std_value = np.std(values)
        volatility = std_value / mean_value if mean_value != 0 else 0
        if len(values) >= 3:
            recent_trend = np.polyfit(range(len(values)), values, 1)[0]
            if recent_trend > 0.05 * mean_value:
                trend_description = 'Strong upward trend'
            elif recent_trend > 0.02 * mean_value:
                trend_description = 'Moderate upward trend'
            elif recent_trend < -0.05 * mean_value:
                trend_description = 'Strong downward trend'
            elif recent_trend < -0.02 * mean_value:
                trend_description = 'Moderate downward trend'
            else:
                trend_description = 'Stable trend'
        elif values[-1] > values[0]:
            trend_description = 'Improving'
        elif values[-1] < values[0]:
            trend_description = 'Declining'
        else:
            trend_description = 'Stable'
        return ComparativeAnalysis(periods=periods, values=values, trend_analysis=trend_description, volatility_measure=volatility, growth_rate=growth_rate)

    def assess_risk_level(self, metric_value: float, benchmark_dict: Dict[str, float], higher_is_better: bool=True) -> RiskLevel:
        """
        Assess risk level based on metric value and benchmarks

        Args:
            metric_value: The calculated metric value
            benchmark_dict: Dictionary with benchmark thresholds
            higher_is_better: Whether higher values indicate better performance

        Returns:
            RiskLevel enum value
        """
        if higher_is_better:
            if metric_value >= benchmark_dict.get('excellent', float('inf')):
                return RiskLevel.LOW
            elif metric_value >= benchmark_dict.get('good', float('inf')):
                return RiskLevel.LOW
            elif metric_value >= benchmark_dict.get('adequate', float('inf')):
                return RiskLevel.MODERATE
            else:
                return RiskLevel.HIGH
        elif metric_value <= benchmark_dict.get('excellent', 0):
            return RiskLevel.LOW
        elif metric_value <= benchmark_dict.get('good', 0):
            return RiskLevel.LOW
        elif metric_value <= benchmark_dict.get('adequate', float('inf')):
            return RiskLevel.MODERATE
        else:
            return RiskLevel.HIGH

    def generate_interpretation(self, metric_name: str, value: float, risk_level: RiskLevel, analysis_type: AnalysisType) -> str:
        """
        Generate standardized interpretation text for metrics

        Args:
            metric_name: Name of the metric
            value: Calculated value
            risk_level: Assessed risk level
            analysis_type: Type of analysis

        Returns:
            Interpretation string
        """
        risk_descriptions = {RiskLevel.LOW: 'strong', RiskLevel.MODERATE: 'adequate', RiskLevel.HIGH: 'weak', RiskLevel.VERY_HIGH: 'very weak'}
        base_interpretation = f'The {metric_name} of {value:.3f} indicates {risk_descriptions[risk_level]} {analysis_type.value} performance.'
        if analysis_type == AnalysisType.LIQUIDITY:
            if risk_level == RiskLevel.LOW:
                base_interpretation += ' The company appears well-positioned to meet short-term obligations.'
            elif risk_level == RiskLevel.HIGH:
                base_interpretation += ' The company may face challenges meeting short-term obligations.'
        elif analysis_type == AnalysisType.PROFITABILITY:
            if risk_level == RiskLevel.LOW:
                base_interpretation += ' The company demonstrates effective management and competitive positioning.'
            elif risk_level == RiskLevel.HIGH:
                base_interpretation += ' The company may need to improve operational efficiency or pricing strategies.'
        elif analysis_type == AnalysisType.SOLVENCY:
            if risk_level == RiskLevel.LOW:
                base_interpretation += ' The company maintains conservative financial leverage.'
            elif risk_level == RiskLevel.HIGH:
                base_interpretation += ' The company carries significant financial risk due to high leverage.'
        return base_interpretation

    def compare_to_industry(self, metric_value: float, industry_data: Optional[Dict]) -> Optional[str]:
        """
        Compare metric to industry benchmarks

        Args:
            metric_value: Company metric value
            industry_data: Industry benchmark data

        Returns:
            Comparison interpretation or None if no data available
        """
        if not industry_data:
            return None
        industry_median = industry_data.get('median')
        industry_q1 = industry_data.get('q1')
        industry_q3 = industry_data.get('q3')
        if not all([industry_median, industry_q1, industry_q3]):
            return None
        if metric_value >= industry_q3:
            return f'Above industry 75th percentile (Industry median: {industry_median:.3f})'
        elif metric_value >= industry_median:
            return f'Above industry median (Industry median: {industry_median:.3f})'
        elif metric_value >= industry_q1:
            return f'Below industry median but above 25th percentile (Industry median: {industry_median:.3f})'
        else:
            return f'Below industry 25th percentile (Industry median: {industry_median:.3f})'

    def calculate_percentile_rank(self, value: float, peer_values: List[float]) -> float:
        """Calculate percentile rank against peer group"""
        if not peer_values:
            return None
        rank = sum((1 for x in peer_values if x < value))
        percentile = rank / len(peer_values) * 100
        return percentile

    def assess_data_quality(self, statements: FinancialStatements, required_fields: List[str]) -> QualityAssessment:
        """
        Assess the quality of financial data for analysis

        Args:
            statements: Financial statements to assess
            required_fields: Fields required for specific analysis

        Returns:
            QualityAssessment object
        """
        quality_issues = []
        warning_signs = []
        quality_drivers = []
        all_data = {**statements.income_statement, **statements.balance_sheet, **statements.cash_flow}
        missing_critical = [field for field in required_fields if field not in all_data]
        if missing_critical:
            quality_issues.append(f'Missing critical fields: {missing_critical}')
        negative_checks = {'revenue': statements.income_statement.get('revenue', 0), 'total_assets': statements.balance_sheet.get('total_assets', 0), 'cash_equivalents': statements.balance_sheet.get('cash_equivalents', 0)}
        for field, value in negative_checks.items():
            if value < 0:
                warning_signs.append(f'Negative {field}: {value}')
        assets = statements.balance_sheet.get('total_assets', 0)
        liabilities = statements.balance_sheet.get('total_liabilities', 0)
        equity = statements.balance_sheet.get('total_equity', 0)
        if abs(assets - (liabilities + equity)) > 0.01:
            quality_issues.append('Balance sheet equation does not balance')
        else:
            quality_drivers.append('Balance sheet equation balances correctly')
        current_assets = statements.balance_sheet.get('current_assets', 0)
        if current_assets > assets:
            warning_signs.append('Current assets exceed total assets')
        if statements.period_info.audit_status == 'audited':
            quality_drivers.append('Financial statements are audited')
        elif statements.period_info.audit_status == 'unaudited':
            warning_signs.append('Financial statements are unaudited')
        earnings_quality = max(0, 100 - len(quality_issues) * 20 - len(warning_signs) * 10)
        balance_sheet_quality = max(0, 100 - len(quality_issues) * 15 - len(warning_signs) * 8)
        cash_flow_quality = max(0, 100 - len(quality_issues) * 25 - len(warning_signs) * 12)
        overall_score = np.mean([earnings_quality, balance_sheet_quality, cash_flow_quality])
        return QualityAssessment(overall_score=overall_score, earnings_quality=earnings_quality, balance_sheet_quality=balance_sheet_quality, cash_flow_quality=cash_flow_quality, red_flags=quality_issues, warning_signs=warning_signs, quality_drivers=quality_drivers)

    def safe_divide(self, numerator: float, denominator: float, default: float=0.0) -> float:
        """
        Safely perform division with handling for zero denominators

        Args:
            numerator: Numerator value
            denominator: Denominator value
            default: Default value to return if denominator is zero

        Returns:
            Division result or default value
        """
        if denominator == 0 or denominator is None:
            return default
        return numerator / denominator

    def format_percentage(self, value: float, decimal_places: int=1) -> str:
        """Format decimal as percentage string"""
        return f'{value * 100:.{decimal_places}f}%'

    def format_ratio(self, value: float, decimal_places: int=2) -> str:
        """Format ratio with specified decimal places"""
        return f'{value:.{decimal_places}f}'

    def get_analysis_limitations(self, statements: FinancialStatements) -> List[str]:
        """
        Identify general limitations that apply to the analysis

        Args:
            statements: Financial statements being analyzed

        Returns:
            List of limitation descriptions
        """
        limitations = []
        if statements.company_info.reporting_standard == ReportingStandard.LOCAL_GAAP:
            limitations.append('Analysis based on local GAAP may not be comparable to IFRS or US GAAP companies')
        period_end = statements.period_info.period_end
        days_old = (datetime.now().date() - period_end).days
        if days_old > 365:
            limitations.append(f'Financial data is {days_old} days old and may not reflect current conditions')
        if statements.period_info.period_type != 'annual':
            limitations.append('Analysis based on interim data may not reflect full-year performance')
        if statements.period_info.audit_status == 'unaudited':
            limitations.append('Unaudited financial statements may contain errors or adjustments')
        if statements.data_quality.get('completeness_score', 1.0) < 0.8:
            limitations.append('Incomplete financial data may affect analysis accuracy')
        return limitations

    def generate_recommendations(self, analysis_results: List[AnalysisResult]) -> List[str]:
        """
        Generate actionable recommendations based on analysis results

        Args:
            analysis_results: List of analysis results

        Returns:
            List of recommendation strings
        """
        recommendations = []
        high_risk_areas = [result for result in analysis_results if result.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]]
        if high_risk_areas:
            for area in high_risk_areas:
                if area.analysis_type == AnalysisType.LIQUIDITY:
                    recommendations.append('Consider improving working capital management or securing additional credit facilities')
                elif area.analysis_type == AnalysisType.SOLVENCY:
                    recommendations.append('Focus on debt reduction and improving interest coverage ratios')
                elif area.analysis_type == AnalysisType.PROFITABILITY:
                    recommendations.append('Review cost structure and pricing strategies to improve profitability')
                elif area.analysis_type == AnalysisType.ACTIVITY:
                    recommendations.append('Optimize asset utilization and working capital efficiency')
        declining_trends = [result for result in analysis_results if result.trend == TrendDirection.DETERIORATING]
        if declining_trends:
            recommendations.append('Monitor declining performance trends and develop corrective action plans')
        quality_issues = [result for result in analysis_results if result.quality_score and result.quality_score < 60]
        if quality_issues:
            recommendations.append('Improve financial reporting quality and transparency')
        return list(set(recommendations))

def assess_risk_level(self, metric_value: float, benchmark_dict: Dict[str, float], higher_is_better: bool=True) -> RiskLevel:
    """
        Assess risk level based on metric value and benchmarks

        Args:
            metric_value: The calculated metric value
            benchmark_dict: Dictionary with benchmark thresholds
            higher_is_better: Whether higher values indicate better performance

        Returns:
            RiskLevel enum value
        """
    if higher_is_better:
        if metric_value >= benchmark_dict.get('excellent', float('inf')):
            return RiskLevel.LOW
        elif metric_value >= benchmark_dict.get('good', float('inf')):
            return RiskLevel.LOW
        elif metric_value >= benchmark_dict.get('adequate', float('inf')):
            return RiskLevel.MODERATE
        else:
            return RiskLevel.HIGH
    elif metric_value <= benchmark_dict.get('excellent', 0):
        return RiskLevel.LOW
    elif metric_value <= benchmark_dict.get('good', 0):
        return RiskLevel.LOW
    elif metric_value <= benchmark_dict.get('adequate', float('inf')):
        return RiskLevel.MODERATE
    else:
        return RiskLevel.HIGH

class EconomicsBase(ABC):
    """
    Abstract base class for all economics analysis components.
    Ensures consistent interface and precision across modules.
    """

    def __init__(self, precision: int=8, base_currency: str='USD'):
        self.precision = precision
        self.base_currency = base_currency
        self.validator = DataValidator()
        self._results_cache = {}

    def to_decimal(self, value: Union[float, int, str]) -> Decimal:
        """Convert value to high-precision Decimal"""
        try:
            return Decimal(str(value)).quantize(Decimal('0.' + '0' * self.precision), rounding=ROUND_HALF_UP)
        except Exception as e:
            raise CalculationError(f'Cannot convert {value} to Decimal: {e}')

    def validate_inputs(self, **kwargs) -> bool:
        """Validate input parameters"""
        return self.validator.validate_parameters(**kwargs)

    @abstractmethod
    def calculate(self, *args, **kwargs) -> Dict[str, Any]:
        """Main calculation method - must be implemented by subclasses"""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Return component metadata"""
        return {'class': self.__class__.__name__, 'precision': self.precision, 'base_currency': self.base_currency, 'timestamp': datetime.now().isoformat()}

def to_decimal(self, value: Union[float, int, str]) -> Decimal:
    """Convert value to high-precision Decimal"""
    try:
        return Decimal(str(value)).quantize(Decimal('0.' + '0' * self.precision), rounding=ROUND_HALF_UP)
    except Exception as e:
        raise CalculationError(f'Cannot convert {value} to Decimal: {e}')

class CalculationUtils:
    """
    Utility functions for common economic calculations.
    Provides mathematical precision and error handling.
    """

    @staticmethod
    def compound_growth_rate(initial: Decimal, final: Decimal, periods: Decimal) -> Decimal:
        """Calculate compound annual growth rate"""
        if initial <= 0 or final <= 0 or periods <= 0:
            raise CalculationError('All values must be positive for CAGR calculation')
        return (final / initial) ** (Decimal('1') / periods) - Decimal('1')

    @staticmethod
    def present_value(future_value: Decimal, rate: Decimal, periods: Decimal) -> Decimal:
        """Calculate present value"""
        if periods <= 0:
            raise CalculationError('Periods must be positive')
        return future_value / (Decimal('1') + rate) ** periods

    @staticmethod
    def future_value(present_value: Decimal, rate: Decimal, periods: Decimal) -> Decimal:
        """Calculate future value"""
        if periods <= 0:
            raise CalculationError('Periods must be positive')
        return present_value * (Decimal('1') + rate) ** periods

    @staticmethod
    def effective_rate(nominal_rate: Decimal, compounding_frequency: int) -> Decimal:
        """Calculate effective annual rate"""
        if compounding_frequency <= 0:
            raise CalculationError('Compounding frequency must be positive')
        return (Decimal('1') + nominal_rate / Decimal(str(compounding_frequency))) ** Decimal(str(compounding_frequency)) - Decimal('1')

    @staticmethod
    def geometric_mean(values: List[Decimal]) -> Decimal:
        """Calculate geometric mean"""
        if not values or any((v <= 0 for v in values)):
            raise CalculationError('All values must be positive for geometric mean')
        product = Decimal('1')
        for value in values:
            product *= value
        return product ** (Decimal('1') / Decimal(str(len(values))))

    @staticmethod
    def standard_deviation(values: List[Decimal]) -> Decimal:
        """Calculate sample standard deviation"""
        if len(values) < 2:
            raise CalculationError('At least 2 values required for standard deviation')
        mean = sum(values) / Decimal(str(len(values)))
        variance = sum(((x - mean) ** 2 for x in values)) / Decimal(str(len(values) - 1))
        return variance.sqrt()

@staticmethod
def compound_growth_rate(initial: Decimal, final: Decimal, periods: Decimal) -> Decimal:
    """Calculate compound annual growth rate"""
    if initial <= 0 or final <= 0 or periods <= 0:
        raise CalculationError('All values must be positive for CAGR calculation')
    return (final / initial) ** (Decimal('1') / periods) - Decimal('1')

@staticmethod
def present_value(future_value: Decimal, rate: Decimal, periods: Decimal) -> Decimal:
    """Calculate present value"""
    if periods <= 0:
        raise CalculationError('Periods must be positive')
    return future_value / (Decimal('1') + rate) ** periods

@staticmethod
def future_value(present_value: Decimal, rate: Decimal, periods: Decimal) -> Decimal:
    """Calculate future value"""
    if periods <= 0:
        raise CalculationError('Periods must be positive')
    return present_value * (Decimal('1') + rate) ** periods

@staticmethod
def effective_rate(nominal_rate: Decimal, compounding_frequency: int) -> Decimal:
    """Calculate effective annual rate"""
    if compounding_frequency <= 0:
        raise CalculationError('Compounding frequency must be positive')
    return (Decimal('1') + nominal_rate / Decimal(str(compounding_frequency))) ** Decimal(str(compounding_frequency)) - Decimal('1')

@staticmethod
def geometric_mean(values: List[Decimal]) -> Decimal:
    """Calculate geometric mean"""
    if not values or any((v <= 0 for v in values)):
        raise CalculationError('All values must be positive for geometric mean')
    product = Decimal('1')
    for value in values:
        product *= value
    return product ** (Decimal('1') / Decimal(str(len(values))))

class EconomicsConfig:
    """Global configuration for economics module"""

    def __init__(self):
        self.precision = 8
        self.base_currency = 'USD'
        self.data_validation_enabled = True
        self.error_tolerance = Decimal('1e-6')
        self.default_confidence_interval = Decimal('0.95')
        self.cache_enabled = True
        self.logging_level = logging.INFO

    def update_config(self, **kwargs):
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f'Unknown configuration parameter: {key}')

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {'precision': self.precision, 'base_currency': self.base_currency, 'data_validation_enabled': self.data_validation_enabled, 'error_tolerance': str(self.error_tolerance), 'default_confidence_interval': str(self.default_confidence_interval), 'cache_enabled': self.cache_enabled, 'logging_level': self.logging_level}

def __init__(self):
    self.precision = 8
    self.base_currency = 'USD'
    self.data_validation_enabled = True
    self.error_tolerance = Decimal('1e-6')
    self.default_confidence_interval = Decimal('0.95')
    self.cache_enabled = True
    self.logging_level = logging.INFO

class ArbitrageDetector(EconomicsBase):
    """Triangular arbitrage detection and profit calculation"""

    def detect_triangular_arbitrage(self, currency_quotes: Dict[str, Dict[str, Decimal]], base_currency: str=None) -> Dict[str, Any]:
        """Detect triangular arbitrage opportunities"""
        base = base_currency or self.base_currency
        opportunities = []
        currencies = list(currency_quotes.keys())
        for i, curr1 in enumerate(currencies):
            for j, curr2 in enumerate(currencies[i + 1:], i + 1):
                for k, curr3 in enumerate(currencies[j + 1:], j + 1):
                    opportunity = self._check_triangle(curr1, curr2, curr3, currency_quotes)
                    if opportunity['arbitrage_exists']:
                        opportunities.append(opportunity)
        return {'opportunities': opportunities, 'total_opportunities': len(opportunities), 'base_currency': base, 'quotes_analyzed': len(currencies), 'timestamp': datetime.now().isoformat()}

    def _check_triangle(self, curr1: str, curr2: str, curr3: str, quotes: Dict[str, Dict[str, Decimal]]) -> Dict[str, Any]:
        """Check specific triangular arbitrage opportunity"""
        try:
            pair1 = f'{curr1}/{curr2}'
            pair2 = f'{curr2}/{curr3}'
            pair3 = f'{curr3}/{curr1}'
            if pair1 in quotes and pair2 in quotes and (pair3 in quotes):
                rate1 = quotes[pair1]['ask']
                rate2 = quotes[pair2]['ask']
                rate3 = quotes[pair3]['bid']
                forward_result = rate1 * rate2 * rate3
                rate1_rev = quotes[pair3]['ask']
                rate2_rev = self.to_decimal(1) / quotes[pair2]['bid']
                rate3_rev = self.to_decimal(1) / quotes[pair1]['bid']
                reverse_result = rate1_rev * rate2_rev * rate3_rev
                arbitrage_forward = forward_result > self.to_decimal(1)
                arbitrage_reverse = reverse_result > self.to_decimal(1)
                if arbitrage_forward or arbitrage_reverse:
                    best_path = 'forward' if forward_result > reverse_result else 'reverse'
                    profit_factor = max(forward_result, reverse_result)
                    return {'currencies': [curr1, curr2, curr3], 'arbitrage_exists': True, 'best_path': best_path, 'profit_factor': profit_factor, 'profit_percentage': (profit_factor - self.to_decimal(1)) * self.to_decimal(100), 'forward_result': forward_result, 'reverse_result': reverse_result}
            return {'currencies': [curr1, curr2, curr3], 'arbitrage_exists': False, 'profit_factor': self.to_decimal(0), 'profit_percentage': self.to_decimal(0)}
        except Exception as e:
            raise CalculationError(f'Error calculating triangular arbitrage: {e}')

    def calculate_arbitrage_profit(self, opportunity: Dict[str, Any], investment_amount: Decimal) -> Dict[str, Decimal]:
        """Calculate profit from arbitrage opportunity"""
        if not opportunity['arbitrage_exists']:
            raise ValidationError('No arbitrage opportunity exists')
        profit_factor = opportunity['profit_factor']
        gross_profit = investment_amount * (profit_factor - self.to_decimal(1))
        transaction_cost_rate = self.to_decimal(0.001)
        num_transactions = self.to_decimal(3)
        transaction_costs = investment_amount * transaction_cost_rate * num_transactions
        net_profit = gross_profit - transaction_costs
        net_profit_percentage = net_profit / investment_amount * self.to_decimal(100)
        return {'investment_amount': investment_amount, 'gross_profit': gross_profit, 'transaction_costs': transaction_costs, 'net_profit': net_profit, 'net_profit_percentage': net_profit_percentage, 'profit_factor': profit_factor, 'viable': net_profit > self.to_decimal(0)}

    def calculate(self, **kwargs) -> Dict[str, Any]:
        """Main arbitrage calculation"""
        if 'currency_quotes' in kwargs:
            return self.detect_triangular_arbitrage(kwargs['currency_quotes'], kwargs.get('base_currency'))
        elif 'opportunity' in kwargs and 'investment_amount' in kwargs:
            return self.calculate_arbitrage_profit(kwargs['opportunity'], self.to_decimal(kwargs['investment_amount']))
        else:
            raise ValidationError('Missing required parameters for arbitrage calculation')

def _check_triangle(self, curr1: str, curr2: str, curr3: str, quotes: Dict[str, Dict[str, Decimal]]) -> Dict[str, Any]:
    """Check specific triangular arbitrage opportunity"""
    try:
        pair1 = f'{curr1}/{curr2}'
        pair2 = f'{curr2}/{curr3}'
        pair3 = f'{curr3}/{curr1}'
        if pair1 in quotes and pair2 in quotes and (pair3 in quotes):
            rate1 = quotes[pair1]['ask']
            rate2 = quotes[pair2]['ask']
            rate3 = quotes[pair3]['bid']
            forward_result = rate1 * rate2 * rate3
            rate1_rev = quotes[pair3]['ask']
            rate2_rev = self.to_decimal(1) / quotes[pair2]['bid']
            rate3_rev = self.to_decimal(1) / quotes[pair1]['bid']
            reverse_result = rate1_rev * rate2_rev * rate3_rev
            arbitrage_forward = forward_result > self.to_decimal(1)
            arbitrage_reverse = reverse_result > self.to_decimal(1)
            if arbitrage_forward or arbitrage_reverse:
                best_path = 'forward' if forward_result > reverse_result else 'reverse'
                profit_factor = max(forward_result, reverse_result)
                return {'currencies': [curr1, curr2, curr3], 'arbitrage_exists': True, 'best_path': best_path, 'profit_factor': profit_factor, 'profit_percentage': (profit_factor - self.to_decimal(1)) * self.to_decimal(100), 'forward_result': forward_result, 'reverse_result': reverse_result}
        return {'currencies': [curr1, curr2, curr3], 'arbitrage_exists': False, 'profit_factor': self.to_decimal(0), 'profit_percentage': self.to_decimal(0)}
    except Exception as e:
        raise CalculationError(f'Error calculating triangular arbitrage: {e}')

class ReportGenerator(EconomicsBase):
    """Generate comprehensive analysis reports"""

    def __init__(self, precision: int=8):
        super().__init__(precision)
        self.viz_engine = VisualizationEngine(precision)

    def generate_analysis_report(self, analysis_results: Dict[str, Any], report_title: str='Economic Analysis Report') -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        report = {'title': report_title, 'generated_at': datetime.now().isoformat(), 'summary': self._generate_executive_summary(analysis_results), 'sections': {}, 'visualizations': [], 'recommendations': self._generate_recommendations(analysis_results)}
        for analysis_type, results in analysis_results.items():
            if 'error' in str(results):
                continue
            section = self._create_analysis_section(analysis_type, results)
            if section:
                report['sections'][analysis_type] = section
        return report

    def _generate_executive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary from analysis results"""
        summary = {'key_findings': [], 'risk_assessment': 'Not Available', 'outlook': 'Neutral', 'confidence_level': 'Medium'}
        for analysis_type, analysis_results in results.items():
            if isinstance(analysis_results, dict) and 'error' not in analysis_results:
                if 'correlation' in analysis_type.lower():
                    high_corr = analysis_results.get('highest_correlations', [])
                    if high_corr:
                        summary['key_findings'].append(f'Highest correlation: {high_corr[0]['variable_1']} - {high_corr[0]['variable_2']} ({float(high_corr[0]['correlation']):.3f})')
                elif 'forecast' in analysis_type.lower():
                    forecasts = analysis_results.get('forecasts', {})
                    if forecasts:
                        best_method = analysis_results.get('evaluation', {}).get('best_method', 'Unknown')
                        summary['key_findings'].append(f'Best forecasting method: {best_method}')
                elif 'monte_carlo' in analysis_type.lower():
                    risk_metrics = analysis_results.get('risk_metrics', {})
                    if risk_metrics:
                        var_95 = risk_metrics.get('var_95')
                        if var_95:
                            summary['key_findings'].append(f'95% VaR: {float(var_95):.2f}')
        return summary

    def _create_analysis_section(self, analysis_type: str, results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create report section for specific analysis type"""
        section = {'title': analysis_type.replace('_', ' ').title(), 'content': {}, 'key_metrics': {}, 'interpretation': ''}
        if 'statistical' in analysis_type:
            stats = results.get('basic_statistics', {})
            section['key_metrics'] = {'Mean': stats.get('mean'), 'Std Dev': stats.get('standard_deviation'), 'Skewness': stats.get('skewness'), 'Kurtosis': stats.get('kurtosis')}
            section['interpretation'] = self._interpret_statistics(stats)
        elif 'correlation' in analysis_type:
            section['key_metrics'] = {'Mean Correlation': results.get('summary_statistics', {}).get('mean_correlation'), 'Max Correlation': results.get('summary_statistics', {}).get('max_correlation'), 'Significant Pairs': len(results.get('significant_correlations', []))}
        elif 'forecast' in analysis_type:
            evaluation = results.get('evaluation', {})
            if evaluation:
                best_method = evaluation.get('best_method', 'Unknown')
                section['key_metrics'] = {'Best Method': best_method, 'Forecast Periods': results.get('forecast_periods', 0)}
        section['content'] = results
        return section

    def _interpret_statistics(self, stats: Dict[str, Any]) -> str:
        """Generate interpretation of statistical results"""
        interpretations = []
        skewness = stats.get('skewness')
        if skewness:
            skew_val = float(skewness)
            if abs(skew_val) < 0.5:
                interpretations.append('Distribution is approximately symmetric')
            elif skew_val > 0.5:
                interpretations.append('Distribution is positively skewed (right tail)')
            else:
                interpretations.append('Distribution is negatively skewed (left tail)')
        kurtosis = stats.get('kurtosis')
        if kurtosis:
            kurt_val = float(kurtosis)
            if kurt_val > 3:
                interpretations.append('Distribution has heavy tails (leptokurtic)')
            elif kurt_val < 3:
                interpretations.append('Distribution has light tails (platykurtic)')
        return '. '.join(interpretations) + '.' if interpretations else 'No specific interpretation available.'

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        for analysis_type, analysis_results in results.items():
            if isinstance(analysis_results, dict) and 'error' not in analysis_results:
                if 'risk' in analysis_type.lower():
                    recommendations.append('Monitor risk metrics regularly and adjust exposure accordingly')
                elif 'correlation' in analysis_type.lower():
                    recommendations.append('Consider correlation relationships for portfolio diversification')
                elif 'forecast' in analysis_type.lower():
                    recommendations.append('Use multiple forecasting methods and update predictions regularly')
        if not recommendations:
            recommendations = ['Continue monitoring economic indicators and market conditions']
        return recommendations

def _interpret_statistics(self, stats: Dict[str, Any]) -> str:
    """Generate interpretation of statistical results"""
    interpretations = []
    skewness = stats.get('skewness')
    if skewness:
        skew_val = float(skewness)
        if abs(skew_val) < 0.5:
            interpretations.append('Distribution is approximately symmetric')
        elif skew_val > 0.5:
            interpretations.append('Distribution is positively skewed (right tail)')
        else:
            interpretations.append('Distribution is negatively skewed (left tail)')
    kurtosis = stats.get('kurtosis')
    if kurtosis:
        kurt_val = float(kurtosis)
        if kurt_val > 3:
            interpretations.append('Distribution has heavy tails (leptokurtic)')
        elif kurt_val < 3:
            interpretations.append('Distribution has light tails (platykurtic)')
    return '. '.join(interpretations) + '.' if interpretations else 'No specific interpretation available.'

class PrivateEquityAnalyzer(AlternativeInvestmentBase):
    """
    Private Equity investment analysis and valuation
    CFA Standards: IRR, MOIC, DPI, RVPI calculations and due diligence
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.fund_life = getattr(parameters, 'fund_life', Constants.PE_TYPICAL_FUND_LIFE)
        self.vintage_year = getattr(parameters, 'vintage_year', None)
        self.commitment = getattr(parameters, 'commitment', None)
        self.called_capital = Decimal('0')
        self.distributed_capital = Decimal('0')
        self.current_nav = Decimal('0')

    def add_commitment(self, commitment_amount: Decimal, vintage_year: int) -> None:
        """Record fund commitment"""
        self.commitment = commitment_amount
        self.vintage_year = vintage_year

    def process_capital_call(self, amount: Decimal, call_date: str, description: str=None) -> None:
        """Process capital call from fund"""
        cash_flow = CashFlow(date=call_date, amount=-abs(amount), cf_type='capital_call', description=description or f'Capital call - {call_date}')
        self.add_cash_flows([cash_flow])
        self.called_capital += abs(amount)

    def process_distribution(self, amount: Decimal, dist_date: str, distribution_type: str='distribution') -> None:
        """Process distribution from fund"""
        cash_flow = CashFlow(date=dist_date, amount=amount, cf_type=distribution_type, description=f'{distribution_type} - {dist_date}')
        self.add_cash_flows([cash_flow])
        self.distributed_capital += amount

    def update_nav(self, nav_value: Decimal, nav_date: str) -> None:
        """Update current Net Asset Value"""
        self.current_nav = nav_value
        market_data = MarketData(timestamp=nav_date, price=nav_value, volume=None)
        self.add_market_data([market_data])

    def calculate_nav(self) -> Decimal:
        """Calculate current NAV"""
        return self.current_nav

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """
        Calculate key PE metrics following CFA standards
        """
        if not self.cash_flows:
            return {'error': 'No cash flows available'}
        metrics = {}
        cf_for_irr = self.cash_flows.copy()
        if self.current_nav > 0:
            latest_date = max((cf.date for cf in self.cash_flows)) if self.cash_flows else datetime.now().strftime('%Y-%m-%d')
            cf_for_irr.append(CashFlow(date=latest_date, amount=self.current_nav, cf_type='nav', description='Current NAV'))
        irr = self.math.irr(cf_for_irr)
        metrics['irr'] = float(irr) if irr else None
        moic = self.math.moic(cf_for_irr)
        metrics['moic'] = float(moic) if moic else None
        dpi = self.math.dpi(self.cash_flows)
        metrics['dpi'] = float(dpi)
        rvpi = self.math.rvpi(self.cash_flows, self.current_nav)
        metrics['rvpi'] = float(rvpi)
        tvpi = dpi + rvpi
        metrics['tvpi'] = float(tvpi)
        if self.commitment:
            called_ratio = self.called_capital / self.commitment
            metrics['called_capital_ratio'] = float(called_ratio)
            metrics['uncalled_commitment'] = float(self.commitment - self.called_capital)
        metrics['called_capital'] = float(self.called_capital)
        metrics['distributed_capital'] = float(self.distributed_capital)
        metrics['current_nav'] = float(self.current_nav)
        if self.vintage_year:
            current_year = datetime.now().year
            fund_age = current_year - self.vintage_year
            metrics['fund_age'] = fund_age
            metrics['vintage_year'] = self.vintage_year
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive PE valuation summary"""
        key_metrics = self.calculate_key_metrics()
        valuation = {'investment_overview': {'asset_class': self.parameters.asset_class.value, 'fund_name': self.parameters.name, 'vintage_year': self.vintage_year, 'commitment': float(self.commitment) if self.commitment else None}, 'capital_account': {'total_commitment': float(self.commitment) if self.commitment else None, 'called_capital': float(self.called_capital), 'uncalled_commitment': float(self.commitment - self.called_capital) if self.commitment else None, 'distributed_capital': float(self.distributed_capital), 'current_nav': float(self.current_nav)}, 'performance_metrics': key_metrics, 'cash_flow_summary': {'number_of_capital_calls': len([cf for cf in self.cash_flows if cf.cf_type == 'capital_call']), 'number_of_distributions': len([cf for cf in self.cash_flows if cf.cf_type == 'distribution']), 'total_cash_flows': len(self.cash_flows)}}
        return valuation

    def benchmark_comparison(self, benchmark_irr: Decimal, benchmark_moic: Decimal) -> Dict[str, Any]:
        """Compare performance against benchmark"""
        metrics = self.calculate_key_metrics()
        if not metrics.get('irr') or not metrics.get('moic'):
            return {'error': 'Insufficient data for benchmark comparison'}
        fund_irr = Decimal(str(metrics['irr']))
        fund_moic = Decimal(str(metrics['moic']))
        comparison = {'fund_performance': {'irr': float(fund_irr), 'moic': float(fund_moic)}, 'benchmark_performance': {'irr': float(benchmark_irr), 'moic': float(benchmark_moic)}, 'relative_performance': {'irr_difference': float(fund_irr - benchmark_irr), 'moic_difference': float(fund_moic - benchmark_moic), 'irr_outperformance': fund_irr > benchmark_irr, 'moic_outperformance': fund_moic > benchmark_moic}}
        return comparison

def valuation_summary(self) -> Dict[str, Any]:
    """Comprehensive PE valuation summary"""
    key_metrics = self.calculate_key_metrics()
    valuation = {'investment_overview': {'asset_class': self.parameters.asset_class.value, 'fund_name': self.parameters.name, 'vintage_year': self.vintage_year, 'commitment': float(self.commitment) if self.commitment else None}, 'capital_account': {'total_commitment': float(self.commitment) if self.commitment else None, 'called_capital': float(self.called_capital), 'uncalled_commitment': float(self.commitment - self.called_capital) if self.commitment else None, 'distributed_capital': float(self.distributed_capital), 'current_nav': float(self.current_nav)}, 'performance_metrics': key_metrics, 'cash_flow_summary': {'number_of_capital_calls': len([cf for cf in self.cash_flows if cf.cf_type == 'capital_call']), 'number_of_distributions': len([cf for cf in self.cash_flows if cf.cf_type == 'distribution']), 'total_cash_flows': len(self.cash_flows)}}
    return valuation

def benchmark_comparison(self, benchmark_irr: Decimal, benchmark_moic: Decimal) -> Dict[str, Any]:
    """Compare performance against benchmark"""
    metrics = self.calculate_key_metrics()
    if not metrics.get('irr') or not metrics.get('moic'):
        return {'error': 'Insufficient data for benchmark comparison'}
    fund_irr = Decimal(str(metrics['irr']))
    fund_moic = Decimal(str(metrics['moic']))
    comparison = {'fund_performance': {'irr': float(fund_irr), 'moic': float(fund_moic)}, 'benchmark_performance': {'irr': float(benchmark_irr), 'moic': float(benchmark_moic)}, 'relative_performance': {'irr_difference': float(fund_irr - benchmark_irr), 'moic_difference': float(fund_moic - benchmark_moic), 'irr_outperformance': fund_irr > benchmark_irr, 'moic_outperformance': fund_moic > benchmark_moic}}
    return comparison

class PrivateDebtAnalyzer(AlternativeInvestmentBase):
    """
    Private Debt investment analysis and risk assessment
    CFA Standards: Credit analysis, yield calculations, duration
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.principal_amount = getattr(parameters, 'principal_amount', None)
        self.coupon_rate = getattr(parameters, 'coupon_rate', None)
        self.maturity_date = getattr(parameters, 'maturity_date', None)
        self.credit_rating = getattr(parameters, 'credit_rating', None)
        self.seniority = getattr(parameters, 'seniority', 'senior')
        self.current_price = Decimal('100')

    def calculate_current_yield(self) -> Decimal:
        """Calculate current yield"""
        if not self.coupon_rate or self.current_price == 0:
            return Decimal('0')
        annual_coupon = self.principal_amount * self.coupon_rate if self.principal_amount else self.coupon_rate
        return annual_coupon / self.current_price

    def calculate_yield_to_maturity(self, current_price: Decimal=None) -> Optional[Decimal]:
        """
        Calculate Yield to Maturity using approximation method
        CFA Standard: YTM calculation for bonds
        """
        if not all([self.coupon_rate, self.maturity_date, self.principal_amount]):
            return None
        price = current_price or self.current_price
        maturity = datetime.strptime(self.maturity_date, '%Y-%m-%d')
        years_to_maturity = (maturity - datetime.now()).days / 365.25
        if years_to_maturity <= 0:
            return self.coupon_rate
        face_value = Decimal('100')
        annual_coupon = self.coupon_rate * face_value
        numerator = annual_coupon + (face_value - price) / Decimal(str(years_to_maturity))
        denominator = (face_value + price) / Decimal('2')
        ytm = numerator / denominator
        return ytm

    def calculate_duration(self, ytm: Decimal=None) -> Dict[str, Decimal]:
        """
        Calculate Macaulay and Modified Duration
        CFA Standard: Duration as price sensitivity measure
        """
        if not all([self.coupon_rate, self.maturity_date]):
            return {}
        if ytm is None:
            ytm = self.calculate_yield_to_maturity()
            if ytm is None:
                return {}
        maturity = datetime.strptime(self.maturity_date, '%Y-%m-%d')
        years_to_maturity = (maturity - datetime.now()).days / 365.25
        if years_to_maturity <= 0:
            return {}
        coupon_rate = self.coupon_rate
        periods = int(years_to_maturity)
        pv_weighted_time = Decimal('0')
        total_pv = Decimal('0')
        for t in range(1, periods + 1):
            if t < periods:
                cash_flow = coupon_rate * Decimal('100')
            else:
                cash_flow = coupon_rate * Decimal('100') + Decimal('100')
            pv = cash_flow / (Decimal('1') + ytm) ** t
            pv_weighted_time += pv * Decimal(str(t))
            total_pv += pv
        macaulay_duration = pv_weighted_time / total_pv if total_pv > 0 else Decimal('0')
        modified_duration = macaulay_duration / (Decimal('1') + ytm)
        return {'macaulay_duration': macaulay_duration, 'modified_duration': modified_duration, 'years_to_maturity': Decimal(str(years_to_maturity))}

    def credit_risk_assessment(self) -> Dict[str, Any]:
        """
        Assess credit risk characteristics
        CFA Standard: Credit analysis framework
        """
        assessment = {'credit_profile': {'credit_rating': self.credit_rating, 'seniority': self.seniority, 'principal_amount': float(self.principal_amount) if self.principal_amount else None, 'coupon_rate': float(self.coupon_rate) if self.coupon_rate else None, 'maturity_date': self.maturity_date}}
        if self.coupon_rate:
            risk_free_rate = Config.RISK_FREE_RATE
            credit_spread = self.coupon_rate - risk_free_rate
            assessment['credit_spread'] = float(credit_spread)
            assessment['credit_spread_bps'] = float(credit_spread * Constants.BASIS_POINTS)
        risk_factors = {'senior': {'recovery_rate': 0.8, 'risk_weight': 1.0}, 'mezzanine': {'recovery_rate': 0.5, 'risk_weight': 1.5}, 'subordinated': {'recovery_rate': 0.2, 'risk_weight': 2.0}}
        if self.seniority in risk_factors:
            assessment['risk_characteristics'] = risk_factors[self.seniority]
        return assessment

    def calculate_nav(self) -> Decimal:
        """Calculate current NAV based on market price"""
        if self.principal_amount:
            return self.principal_amount * (self.current_price / Decimal('100'))
        return self.current_price

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key private debt metrics"""
        metrics = {}
        current_yield = self.calculate_current_yield()
        ytm = self.calculate_yield_to_maturity()
        metrics['current_yield'] = float(current_yield)
        if ytm:
            metrics['yield_to_maturity'] = float(ytm)
        duration_metrics = self.calculate_duration(ytm)
        for key, value in duration_metrics.items():
            metrics[key] = float(value)
        credit_assessment = self.credit_risk_assessment()
        metrics.update(credit_assessment)
        metrics['current_price'] = float(self.current_price)
        metrics['nav'] = float(self.calculate_nav())
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive private debt valuation"""
        return {'debt_overview': {'asset_class': self.parameters.asset_class.value, 'instrument_name': self.parameters.name, 'principal_amount': float(self.principal_amount) if self.principal_amount else None, 'seniority': self.seniority, 'credit_rating': self.credit_rating}, 'performance_metrics': self.calculate_key_metrics(), 'risk_assessment': self.credit_risk_assessment()}

    def interest_rate_sensitivity(self, rate_change_bps: int) -> Dict[str, Decimal]:
        """
        Calculate price sensitivity to interest rate changes
        CFA Standard: Duration-based price sensitivity
        """
        duration_metrics = self.calculate_duration()
        if 'modified_duration' not in duration_metrics:
            return {'error': 'Cannot calculate duration'}
        modified_duration = duration_metrics['modified_duration']
        rate_change = Decimal(str(rate_change_bps)) / Constants.BASIS_POINTS
        price_change_pct = -modified_duration * rate_change
        new_price = self.current_price * (Decimal('1') + price_change_pct)
        return {'rate_change_bps': Decimal(str(rate_change_bps)), 'price_change_percent': price_change_pct, 'new_price': new_price, 'price_change_amount': new_price - self.current_price}

def calculate_current_yield(self) -> Decimal:
    """Calculate current yield"""
    if not self.coupon_rate or self.current_price == 0:
        return Decimal('0')
    annual_coupon = self.principal_amount * self.coupon_rate if self.principal_amount else self.coupon_rate
    return annual_coupon / self.current_price

def credit_risk_assessment(self) -> Dict[str, Any]:
    """
        Assess credit risk characteristics
        CFA Standard: Credit analysis framework
        """
    assessment = {'credit_profile': {'credit_rating': self.credit_rating, 'seniority': self.seniority, 'principal_amount': float(self.principal_amount) if self.principal_amount else None, 'coupon_rate': float(self.coupon_rate) if self.coupon_rate else None, 'maturity_date': self.maturity_date}}
    if self.coupon_rate:
        risk_free_rate = Config.RISK_FREE_RATE
        credit_spread = self.coupon_rate - risk_free_rate
        assessment['credit_spread'] = float(credit_spread)
        assessment['credit_spread_bps'] = float(credit_spread * Constants.BASIS_POINTS)
    risk_factors = {'senior': {'recovery_rate': 0.8, 'risk_weight': 1.0}, 'mezzanine': {'recovery_rate': 0.5, 'risk_weight': 1.5}, 'subordinated': {'recovery_rate': 0.2, 'risk_weight': 2.0}}
    if self.seniority in risk_factors:
        assessment['risk_characteristics'] = risk_factors[self.seniority]
    return assessment

def calculate_nav(self) -> Decimal:
    """Calculate current NAV based on market price"""
    if self.principal_amount:
        return self.principal_amount * (self.current_price / Decimal('100'))
    return self.current_price

def calculate_key_metrics(self) -> Dict[str, Any]:
    """Calculate key private debt metrics"""
    metrics = {}
    current_yield = self.calculate_current_yield()
    ytm = self.calculate_yield_to_maturity()
    metrics['current_yield'] = float(current_yield)
    if ytm:
        metrics['yield_to_maturity'] = float(ytm)
    duration_metrics = self.calculate_duration(ytm)
    for key, value in duration_metrics.items():
        metrics[key] = float(value)
    credit_assessment = self.credit_risk_assessment()
    metrics.update(credit_assessment)
    metrics['current_price'] = float(self.current_price)
    metrics['nav'] = float(self.calculate_nav())
    return metrics

def valuation_summary(self) -> Dict[str, Any]:
    """Comprehensive private debt valuation"""
    return {'debt_overview': {'asset_class': self.parameters.asset_class.value, 'instrument_name': self.parameters.name, 'principal_amount': float(self.principal_amount) if self.principal_amount else None, 'seniority': self.seniority, 'credit_rating': self.credit_rating}, 'performance_metrics': self.calculate_key_metrics(), 'risk_assessment': self.credit_risk_assessment()}

def interest_rate_sensitivity(self, rate_change_bps: int) -> Dict[str, Decimal]:
    """
        Calculate price sensitivity to interest rate changes
        CFA Standard: Duration-based price sensitivity
        """
    duration_metrics = self.calculate_duration()
    if 'modified_duration' not in duration_metrics:
        return {'error': 'Cannot calculate duration'}
    modified_duration = duration_metrics['modified_duration']
    rate_change = Decimal(str(rate_change_bps)) / Constants.BASIS_POINTS
    price_change_pct = -modified_duration * rate_change
    new_price = self.current_price * (Decimal('1') + price_change_pct)
    return {'rate_change_bps': Decimal(str(rate_change_bps)), 'price_change_percent': price_change_pct, 'new_price': new_price, 'price_change_amount': new_price - self.current_price}

class PrivateCapitalPortfolio:
    """
    Portfolio-level analysis for private capital investments
    CFA Standards: Portfolio construction and diversification
    """

    def __init__(self):
        self.pe_investments: List[PrivateEquityAnalyzer] = []
        self.pd_investments: List[PrivateDebtAnalyzer] = []

    def add_pe_investment(self, pe_investment: PrivateEquityAnalyzer) -> None:
        """Add private equity investment to portfolio"""
        self.pe_investments.append(pe_investment)

    def add_pd_investment(self, pd_investment: PrivateDebtAnalyzer) -> None:
        """Add private debt investment to portfolio"""
        self.pd_investments.append(pd_investment)

    def portfolio_summary(self) -> Dict[str, Any]:
        """Generate comprehensive portfolio summary"""
        total_nav = Decimal('0')
        total_commitments = Decimal('0')
        total_called = Decimal('0')
        total_distributed = Decimal('0')
        pe_navs = []
        pe_irrs = []
        pe_moics = []
        for pe in self.pe_investments:
            nav = pe.calculate_nav()
            total_nav += nav
            pe_navs.append(nav)
            if pe.commitment:
                total_commitments += pe.commitment
            total_called += pe.called_capital
            total_distributed += pe.distributed_capital
            metrics = pe.calculate_key_metrics()
            if metrics.get('irr'):
                pe_irrs.append(Decimal(str(metrics['irr'])))
            if metrics.get('moic'):
                pe_moics.append(Decimal(str(metrics['moic'])))
        pd_navs = []
        pd_yields = []
        for pd in self.pd_investments:
            nav = pd.calculate_nav()
            total_nav += nav
            pd_navs.append(nav)
            metrics = pd.calculate_key_metrics()
            if metrics.get('yield_to_maturity'):
                pd_yields.append(Decimal(str(metrics['yield_to_maturity'])))
        summary = {'portfolio_overview': {'total_nav': float(total_nav), 'total_commitments': float(total_commitments), 'total_called_capital': float(total_called), 'total_distributions': float(total_distributed), 'number_pe_investments': len(self.pe_investments), 'number_pd_investments': len(self.pd_investments)}, 'pe_portfolio': {'average_irr': float(sum(pe_irrs) / len(pe_irrs)) if pe_irrs else None, 'average_moic': float(sum(pe_moics) / len(pe_moics)) if pe_moics else None, 'total_pe_nav': float(sum(pe_navs))}, 'pd_portfolio': {'average_yield': float(sum(pd_yields) / len(pd_yields)) if pd_yields else None, 'total_pd_nav': float(sum(pd_navs))}}
        if total_nav > 0:
            pe_allocation = sum(pe_navs) / total_nav
            pd_allocation = sum(pd_navs) / total_nav
            summary['allocation'] = {'pe_weight': float(pe_allocation), 'pd_weight': float(pd_allocation)}
        return summary

    def diversification_analysis(self) -> Dict[str, Any]:
        """Analyze portfolio diversification"""
        analysis = {'vintage_year_diversification': {}, 'strategy_diversification': {}, 'geographic_diversification': {}}
        vintage_years = {}
        for pe in self.pe_investments:
            if pe.vintage_year:
                year = pe.vintage_year
                if year not in vintage_years:
                    vintage_years[year] = []
                vintage_years[year].append(pe.calculate_nav())
        analysis['vintage_year_diversification'] = {year: {'count': len(investments), 'total_nav': float(sum(investments))} for year, investments in vintage_years.items()}
        return analysis

def portfolio_summary(self) -> Dict[str, Any]:
    """Generate comprehensive portfolio summary"""
    total_nav = Decimal('0')
    total_commitments = Decimal('0')
    total_called = Decimal('0')
    total_distributed = Decimal('0')
    pe_navs = []
    pe_irrs = []
    pe_moics = []
    for pe in self.pe_investments:
        nav = pe.calculate_nav()
        total_nav += nav
        pe_navs.append(nav)
        if pe.commitment:
            total_commitments += pe.commitment
        total_called += pe.called_capital
        total_distributed += pe.distributed_capital
        metrics = pe.calculate_key_metrics()
        if metrics.get('irr'):
            pe_irrs.append(Decimal(str(metrics['irr'])))
        if metrics.get('moic'):
            pe_moics.append(Decimal(str(metrics['moic'])))
    pd_navs = []
    pd_yields = []
    for pd in self.pd_investments:
        nav = pd.calculate_nav()
        total_nav += nav
        pd_navs.append(nav)
        metrics = pd.calculate_key_metrics()
        if metrics.get('yield_to_maturity'):
            pd_yields.append(Decimal(str(metrics['yield_to_maturity'])))
    summary = {'portfolio_overview': {'total_nav': float(total_nav), 'total_commitments': float(total_commitments), 'total_called_capital': float(total_called), 'total_distributions': float(total_distributed), 'number_pe_investments': len(self.pe_investments), 'number_pd_investments': len(self.pd_investments)}, 'pe_portfolio': {'average_irr': float(sum(pe_irrs) / len(pe_irrs)) if pe_irrs else None, 'average_moic': float(sum(pe_moics) / len(pe_moics)) if pe_moics else None, 'total_pe_nav': float(sum(pe_navs))}, 'pd_portfolio': {'average_yield': float(sum(pd_yields) / len(pd_yields)) if pd_yields else None, 'total_pd_nav': float(sum(pd_navs))}}
    if total_nav > 0:
        pe_allocation = sum(pe_navs) / total_nav
        pd_allocation = sum(pd_navs) / total_nav
        summary['allocation'] = {'pe_weight': float(pe_allocation), 'pd_weight': float(pd_allocation)}
    return summary

def diversification_analysis(self) -> Dict[str, Any]:
    """Analyze portfolio diversification"""
    analysis = {'vintage_year_diversification': {}, 'strategy_diversification': {}, 'geographic_diversification': {}}
    vintage_years = {}
    for pe in self.pe_investments:
        if pe.vintage_year:
            year = pe.vintage_year
            if year not in vintage_years:
                vintage_years[year] = []
            vintage_years[year].append(pe.calculate_nav())
    analysis['vintage_year_diversification'] = {year: {'count': len(investments), 'total_nav': float(sum(investments))} for year, investments in vintage_years.items()}
    return analysis

class HedgeFundAnalyzer(AlternativeInvestmentBase):
    """
    Comprehensive hedge fund analysis across all strategies
    CFA Standards: Performance analysis, risk metrics, factor models
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.strategy = getattr(parameters, 'strategy', HedgeFundStrategy.LONG_SHORT_EQUITY)
        self.gross_exposure = getattr(parameters, 'gross_exposure', None)
        self.net_exposure = getattr(parameters, 'net_exposure', None)
        self.leverage = getattr(parameters, 'leverage', Decimal('1.0'))
        self.high_water_mark = getattr(parameters, 'high_water_mark', Decimal('100'))
        self.hurdle_rate = getattr(parameters, 'hurdle_rate', Config.HF_HURDLE_RATE_DEFAULT)
        self.redemption_frequency = getattr(parameters, 'redemption_frequency', 'quarterly')
        self.lock_up_period = getattr(parameters, 'lock_up_period', 12)

    def calculate_strategy_metrics(self) -> Dict[str, Any]:
        """
        Calculate strategy-specific metrics based on hedge fund type
        CFA Standards: Strategy classification and risk metrics
        """
        metrics = {}
        returns = self.calculate_simple_returns()
        if not returns:
            return {'error': 'Insufficient return data'}
        metrics.update(self._calculate_base_metrics(returns))
        if self.strategy in [HedgeFundStrategy.LONG_SHORT_EQUITY, HedgeFundStrategy.EQUITY_MARKET_NEUTRAL, HedgeFundStrategy.DEDICATED_SHORT_BIAS]:
            metrics.update(self._analyze_equity_related_strategy(returns))
        elif self.strategy in [HedgeFundStrategy.MERGER_ARBITRAGE, HedgeFundStrategy.DISTRESSED_SECURITIES, HedgeFundStrategy.ACTIVIST]:
            metrics.update(self._analyze_event_driven_strategy(returns))
        elif self.strategy in [HedgeFundStrategy.FIXED_INCOME_ARBITRAGE, HedgeFundStrategy.CONVERTIBLE_ARBITRAGE, HedgeFundStrategy.VOLATILITY_ARBITRAGE]:
            metrics.update(self._analyze_relative_value_strategy(returns))
        elif self.strategy in [HedgeFundStrategy.GLOBAL_MACRO, HedgeFundStrategy.CTA_MANAGED_FUTURES]:
            metrics.update(self._analyze_opportunistic_strategy(returns))
        return metrics

    def _calculate_base_metrics(self, returns: List[Decimal]) -> Dict[str, Any]:
        """Calculate base metrics common to all hedge fund strategies"""
        metrics = {}
        total_return = sum(returns)
        avg_return = total_return / len(returns)
        volatility = self.calculate_volatility(returns, annualized=False)
        metrics['total_return'] = float(total_return)
        metrics['average_return'] = float(avg_return)
        metrics['volatility'] = float(volatility)
        sharpe = self.math.sharpe_ratio(returns)
        sortino = self.math.sortino_ratio(returns)
        metrics['sharpe_ratio'] = float(sharpe)
        metrics['sortino_ratio'] = float(sortino)
        prices = [md.price for md in self.market_data]
        if prices:
            max_dd, peak_idx, trough_idx = self.math.maximum_drawdown(prices)
            metrics['maximum_drawdown'] = float(max_dd)
        if self.gross_exposure and self.net_exposure:
            metrics['gross_exposure'] = float(self.gross_exposure)
            metrics['net_exposure'] = float(self.net_exposure)
            metrics['leverage'] = float(self.leverage)
        return metrics

    def _analyze_equity_related_strategy(self, returns: List[Decimal]) -> Dict[str, Any]:
        """Analyze equity-related hedge fund strategies"""
        metrics = {}
        if self.strategy == HedgeFundStrategy.LONG_SHORT_EQUITY:
            if self.gross_exposure and self.net_exposure:
                long_exposure = (self.gross_exposure + self.net_exposure) / Decimal('2')
                short_exposure = (self.gross_exposure - self.net_exposure) / Decimal('2')
                metrics['long_exposure'] = float(long_exposure)
                metrics['short_exposure'] = float(short_exposure)
                metrics['long_short_ratio'] = float(long_exposure / short_exposure) if short_exposure != 0 else None
        elif self.strategy == HedgeFundStrategy.EQUITY_MARKET_NEUTRAL:
            metrics['target_beta'] = 0.0
            metrics['expected_market_correlation'] = 'Low'
        elif self.strategy == HedgeFundStrategy.DEDICATED_SHORT_BIAS:
            metrics['short_bias'] = True
            metrics['expected_market_correlation'] = 'Negative'
        return metrics

    def _analyze_event_driven_strategy(self, returns: List[Decimal]) -> Dict[str, Any]:
        """Analyze event-driven hedge fund strategies"""
        metrics = {}
        if self.strategy == HedgeFundStrategy.MERGER_ARBITRAGE:
            metrics['return_profile'] = 'steady_positive_with_tail_risk'
            metrics['market_correlation'] = 'low_in_normal_times'
        elif self.strategy == HedgeFundStrategy.DISTRESSED_SECURITIES:
            metrics['return_profile'] = 'illiquid_with_high_returns'
            metrics['credit_sensitivity'] = 'high'
        elif self.strategy == HedgeFundStrategy.ACTIVIST:
            metrics['holding_period'] = 'long_term'
            metrics['concentration'] = 'high'
        win_rate = self._calculate_win_rate(returns)
        metrics['win_rate'] = win_rate
        return metrics

    def _analyze_relative_value_strategy(self, returns: List[Decimal]) -> Dict[str, Any]:
        """Analyze relative value hedge fund strategies"""
        metrics = {}
        if self.strategy == HedgeFundStrategy.FIXED_INCOME_ARBITRAGE:
            metrics['duration_risk'] = 'managed'
            metrics['credit_risk'] = 'varies'
            metrics['leverage_typical'] = 'high'
        elif self.strategy == HedgeFundStrategy.CONVERTIBLE_ARBITRAGE:
            metrics['delta_hedging'] = True
            metrics['volatility_exposure'] = 'positive'
        elif self.strategy == HedgeFundStrategy.VOLATILITY_ARBITRAGE:
            metrics['volatility_exposure'] = 'primary_driver'
            metrics['gamma_trading'] = True
        consistency_ratio = self._calculate_consistency_ratio(returns)
        metrics['consistency_ratio'] = consistency_ratio
        return metrics

    def _analyze_opportunistic_strategy(self, returns: List[Decimal]) -> Dict[str, Any]:
        """Analyze opportunistic hedge fund strategies"""
        metrics = {}
        if self.strategy == HedgeFundStrategy.GLOBAL_MACRO:
            metrics['investment_universe'] = 'global'
            metrics['asset_classes'] = 'multiple'
            metrics['leverage'] = 'variable'
        elif self.strategy == HedgeFundStrategy.CTA_MANAGED_FUTURES:
            metrics['approach'] = 'systematic_trend_following'
            metrics['diversification'] = 'high'
            metrics['crisis_alpha'] = 'potential'
        volatility = self.calculate_volatility(returns)
        metrics['return_volatility'] = float(volatility)
        return metrics

    def _calculate_win_rate(self, returns: List[Decimal]) -> float:
        """Calculate percentage of positive return periods"""
        if not returns:
            return 0.0
        positive_periods = sum((1 for r in returns if r > 0))
        return positive_periods / len(returns)

    def _calculate_consistency_ratio(self, returns: List[Decimal]) -> float:
        """Calculate return consistency (lower volatility relative to mean)"""
        if len(returns) < 2:
            return 0.0
        mean_return = sum(returns) / len(returns)
        volatility = self.calculate_volatility(returns, annualized=False)
        if volatility == 0:
            return float('inf')
        return float(abs(mean_return) / volatility)

    def fee_calculation(self, gross_returns: List[Decimal], nav_values: List[Decimal]) -> Dict[str, Any]:
        """
        Calculate hedge fund fees with high water mark
        CFA Standard: 2 and 20 fee structure with high water mark
        """
        if not all([gross_returns, nav_values, self.parameters.management_fee]):
            return {'error': 'Insufficient data for fee calculation'}
        management_fee_rate = self.parameters.management_fee
        performance_fee_rate = self.parameters.performance_fee or Decimal('0.20')
        total_mgmt_fees = Decimal('0')
        total_perf_fees = Decimal('0')
        net_returns = []
        current_hwm = self.high_water_mark
        for i, (gross_ret, nav) in enumerate(zip(gross_returns, nav_values)):
            beginning_nav = nav_values[i - 1] if i > 0 else nav
            mgmt_fee = beginning_nav * management_fee_rate / Constants.MONTHS_IN_YEAR
            total_mgmt_fees += mgmt_fee
            perf_fee = Decimal('0')
            nav_after_mgmt_fee = nav - mgmt_fee
            if nav_after_mgmt_fee > current_hwm:
                hurdle_amount = beginning_nav * self.hurdle_rate / Constants.MONTHS_IN_YEAR
                if nav_after_mgmt_fee > beginning_nav + hurdle_amount:
                    excess_return = nav_after_mgmt_fee - max(current_hwm, beginning_nav + hurdle_amount)
                    perf_fee = excess_return * performance_fee_rate
                    current_hwm = nav_after_mgmt_fee
            total_perf_fees += perf_fee
            net_nav = nav_after_mgmt_fee - perf_fee
            net_return = (net_nav - beginning_nav) / beginning_nav if beginning_nav > 0 else Decimal('0')
            net_returns.append(net_return)
        return {'total_management_fees': float(total_mgmt_fees), 'total_performance_fees': float(total_perf_fees), 'total_fees': float(total_mgmt_fees + total_perf_fees), 'net_returns': [float(r) for r in net_returns], 'final_high_water_mark': float(current_hwm), 'fee_drag': float((sum(gross_returns) - sum(net_returns)) / sum(gross_returns)) if sum(gross_returns) != 0 else 0}

    def factor_model_analysis(self, market_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]]=None) -> Dict[str, Any]:
        """
        Multi-factor model analysis for hedge fund returns
        CFA Standard: Factor model decomposition
        """
        fund_returns = self.calculate_simple_returns()
        if not fund_returns or not market_returns:
            return {'error': 'Insufficient return data'}
        if len(fund_returns) != len(market_returns):
            return {'error': 'Return series length mismatch'}
        analysis = {}
        market_beta = self._calculate_beta(fund_returns, market_returns)
        market_alpha = self._calculate_alpha(fund_returns, market_returns, market_beta)
        analysis['market_beta'] = float(market_beta)
        analysis['market_alpha'] = float(market_alpha)
        if factor_returns:
            factor_exposures = self._multi_factor_regression(fund_returns, market_returns, factor_returns)
            analysis['factor_exposures'] = factor_exposures
        strategy_factors = self._get_strategy_factors()
        analysis['relevant_factors'] = strategy_factors
        return analysis

    def _calculate_beta(self, fund_returns: List[Decimal], market_returns: List[Decimal]) -> Decimal:
        """Calculate beta relative to market"""
        if len(fund_returns) != len(market_returns) or len(fund_returns) < 2:
            return Decimal('1')
        fund_mean = sum(fund_returns) / len(fund_returns)
        market_mean = sum(market_returns) / len(market_returns)
        covariance = sum(((f - fund_mean) * (m - market_mean) for f, m in zip(fund_returns, market_returns))) / (len(fund_returns) - 1)
        market_variance = sum(((m - market_mean) ** 2 for m in market_returns)) / (len(market_returns) - 1)
        if market_variance == 0:
            return Decimal('1')
        return Decimal(str(covariance)) / Decimal(str(market_variance))

    def _calculate_alpha(self, fund_returns: List[Decimal], market_returns: List[Decimal], beta: Decimal) -> Decimal:
        """Calculate Jensen's alpha"""
        fund_mean = sum(fund_returns) / len(fund_returns)
        market_mean = sum(market_returns) / len(market_returns)
        risk_free = Config.RISK_FREE_RATE / Constants.MONTHS_IN_YEAR
        alpha = fund_mean - risk_free - beta * (market_mean - risk_free)
        return alpha

    def _multi_factor_regression(self, fund_returns: List[Decimal], market_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]]) -> Dict[str, float]:
        """Perform multi-factor regression analysis"""
        try:
            y = np.array([float(r) for r in fund_returns])
            factors = [market_returns]
            factor_names = ['market']
            for factor_name, returns in factor_returns.items():
                if len(returns) == len(fund_returns):
                    factors.append(returns)
                    factor_names.append(factor_name)
            X = np.array([[float(factors[j][i]) for j in range(len(factors))] for i in range(len(fund_returns))])
            X = np.column_stack([np.ones(len(y)), X])
            coefficients = np.linalg.lstsq(X, y, rcond=None)[0]
            exposures = {'alpha': float(coefficients[0])}
            for i, factor_name in enumerate(factor_names):
                exposures[f'{factor_name}_beta'] = float(coefficients[i + 1])
            y_pred = X @ coefficients
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else 0
            exposures['r_squared'] = float(r_squared)
            return exposures
        except Exception as e:
            logger.error(f'Error in multi-factor regression: {str(e)}')
            return {}

    def _get_strategy_factors(self) -> List[str]:
        """Get relevant factors for each strategy type"""
        strategy_factors = {HedgeFundStrategy.LONG_SHORT_EQUITY: ['market', 'size', 'value', 'momentum'], HedgeFundStrategy.EQUITY_MARKET_NEUTRAL: ['size', 'value', 'momentum', 'quality'], HedgeFundStrategy.MERGER_ARBITRAGE: ['volatility', 'credit_spreads'], HedgeFundStrategy.DISTRESSED_SECURITIES: ['credit_spreads', 'high_yield'], HedgeFundStrategy.FIXED_INCOME_ARBITRAGE: ['term_structure', 'credit_spreads'], HedgeFundStrategy.CONVERTIBLE_ARBITRAGE: ['volatility', 'credit_spreads', 'equity'], HedgeFundStrategy.GLOBAL_MACRO: ['currencies', 'commodities', 'bonds', 'equity'], HedgeFundStrategy.CTA_MANAGED_FUTURES: ['momentum', 'commodities', 'currencies']}
        return strategy_factors.get(self.strategy, ['market'])

    def liquidity_analysis(self) -> Dict[str, Any]:
        """
        Analyze hedge fund liquidity characteristics
        CFA Standard: Liquidity risk assessment
        """
        analysis = {'redemption_frequency': self.redemption_frequency, 'lock_up_period_months': self.lock_up_period, 'strategy': self.strategy.value}
        liquidity_profiles = {HedgeFundStrategy.EQUITY_MARKET_NEUTRAL: 'high', HedgeFundStrategy.LONG_SHORT_EQUITY: 'medium_high', HedgeFundStrategy.MERGER_ARBITRAGE: 'medium', HedgeFundStrategy.CONVERTIBLE_ARBITRAGE: 'medium', HedgeFundStrategy.DISTRESSED_SECURITIES: 'low', HedgeFundStrategy.ACTIVIST: 'low', HedgeFundStrategy.GLOBAL_MACRO: 'high', HedgeFundStrategy.CTA_MANAGED_FUTURES: 'high'}
        analysis['expected_liquidity'] = liquidity_profiles.get(self.strategy, 'medium')
        risk_scores = {'daily': 1, 'weekly': 2, 'monthly': 3, 'quarterly': 4, 'annual': 5}
        analysis['liquidity_risk_score'] = risk_scores.get(self.redemption_frequency, 3)
        return analysis

    def calculate_nav(self) -> Decimal:
        """Calculate hedge fund NAV"""
        latest_price = self.get_latest_price()
        return latest_price or Decimal('100')

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive hedge fund metrics"""
        metrics = {}
        strategy_metrics = self.calculate_strategy_metrics()
        metrics.update(strategy_metrics)
        liquidity_metrics = self.liquidity_analysis()
        metrics.update(liquidity_metrics)
        metrics['strategy'] = self.strategy.value
        metrics['leverage'] = float(self.leverage)
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive hedge fund analysis summary"""
        return {'fund_overview': {'strategy': self.strategy.value, 'management_fee': float(self.parameters.management_fee) if self.parameters.management_fee else None, 'performance_fee': float(self.parameters.performance_fee) if self.parameters.performance_fee else None, 'hurdle_rate': float(self.hurdle_rate), 'high_water_mark': float(self.high_water_mark), 'leverage': float(self.leverage)}, 'performance_analysis': self.calculate_key_metrics(), 'liquidity_profile': self.liquidity_analysis()}

def _calculate_base_metrics(self, returns: List[Decimal]) -> Dict[str, Any]:
    """Calculate base metrics common to all hedge fund strategies"""
    metrics = {}
    total_return = sum(returns)
    avg_return = total_return / len(returns)
    volatility = self.calculate_volatility(returns, annualized=False)
    metrics['total_return'] = float(total_return)
    metrics['average_return'] = float(avg_return)
    metrics['volatility'] = float(volatility)
    sharpe = self.math.sharpe_ratio(returns)
    sortino = self.math.sortino_ratio(returns)
    metrics['sharpe_ratio'] = float(sharpe)
    metrics['sortino_ratio'] = float(sortino)
    prices = [md.price for md in self.market_data]
    if prices:
        max_dd, peak_idx, trough_idx = self.math.maximum_drawdown(prices)
        metrics['maximum_drawdown'] = float(max_dd)
    if self.gross_exposure and self.net_exposure:
        metrics['gross_exposure'] = float(self.gross_exposure)
        metrics['net_exposure'] = float(self.net_exposure)
        metrics['leverage'] = float(self.leverage)
    return metrics

def _analyze_equity_related_strategy(self, returns: List[Decimal]) -> Dict[str, Any]:
    """Analyze equity-related hedge fund strategies"""
    metrics = {}
    if self.strategy == HedgeFundStrategy.LONG_SHORT_EQUITY:
        if self.gross_exposure and self.net_exposure:
            long_exposure = (self.gross_exposure + self.net_exposure) / Decimal('2')
            short_exposure = (self.gross_exposure - self.net_exposure) / Decimal('2')
            metrics['long_exposure'] = float(long_exposure)
            metrics['short_exposure'] = float(short_exposure)
            metrics['long_short_ratio'] = float(long_exposure / short_exposure) if short_exposure != 0 else None
    elif self.strategy == HedgeFundStrategy.EQUITY_MARKET_NEUTRAL:
        metrics['target_beta'] = 0.0
        metrics['expected_market_correlation'] = 'Low'
    elif self.strategy == HedgeFundStrategy.DEDICATED_SHORT_BIAS:
        metrics['short_bias'] = True
        metrics['expected_market_correlation'] = 'Negative'
    return metrics

def _analyze_opportunistic_strategy(self, returns: List[Decimal]) -> Dict[str, Any]:
    """Analyze opportunistic hedge fund strategies"""
    metrics = {}
    if self.strategy == HedgeFundStrategy.GLOBAL_MACRO:
        metrics['investment_universe'] = 'global'
        metrics['asset_classes'] = 'multiple'
        metrics['leverage'] = 'variable'
    elif self.strategy == HedgeFundStrategy.CTA_MANAGED_FUTURES:
        metrics['approach'] = 'systematic_trend_following'
        metrics['diversification'] = 'high'
        metrics['crisis_alpha'] = 'potential'
    volatility = self.calculate_volatility(returns)
    metrics['return_volatility'] = float(volatility)
    return metrics

def _calculate_consistency_ratio(self, returns: List[Decimal]) -> float:
    """Calculate return consistency (lower volatility relative to mean)"""
    if len(returns) < 2:
        return 0.0
    mean_return = sum(returns) / len(returns)
    volatility = self.calculate_volatility(returns, annualized=False)
    if volatility == 0:
        return float('inf')
    return float(abs(mean_return) / volatility)

def factor_model_analysis(self, market_returns: List[Decimal], factor_returns: Dict[str, List[Decimal]]=None) -> Dict[str, Any]:
    """
        Multi-factor model analysis for hedge fund returns
        CFA Standard: Factor model decomposition
        """
    fund_returns = self.calculate_simple_returns()
    if not fund_returns or not market_returns:
        return {'error': 'Insufficient return data'}
    if len(fund_returns) != len(market_returns):
        return {'error': 'Return series length mismatch'}
    analysis = {}
    market_beta = self._calculate_beta(fund_returns, market_returns)
    market_alpha = self._calculate_alpha(fund_returns, market_returns, market_beta)
    analysis['market_beta'] = float(market_beta)
    analysis['market_alpha'] = float(market_alpha)
    if factor_returns:
        factor_exposures = self._multi_factor_regression(fund_returns, market_returns, factor_returns)
        analysis['factor_exposures'] = factor_exposures
    strategy_factors = self._get_strategy_factors()
    analysis['relevant_factors'] = strategy_factors
    return analysis

def calculate_nav(self) -> Decimal:
    """Calculate hedge fund NAV"""
    latest_price = self.get_latest_price()
    return latest_price or Decimal('100')

def calculate_key_metrics(self) -> Dict[str, Any]:
    """Calculate comprehensive hedge fund metrics"""
    metrics = {}
    strategy_metrics = self.calculate_strategy_metrics()
    metrics.update(strategy_metrics)
    liquidity_metrics = self.liquidity_analysis()
    metrics.update(liquidity_metrics)
    metrics['strategy'] = self.strategy.value
    metrics['leverage'] = float(self.leverage)
    return metrics

def valuation_summary(self) -> Dict[str, Any]:
    """Comprehensive hedge fund analysis summary"""
    return {'fund_overview': {'strategy': self.strategy.value, 'management_fee': float(self.parameters.management_fee) if self.parameters.management_fee else None, 'performance_fee': float(self.parameters.performance_fee) if self.parameters.performance_fee else None, 'hurdle_rate': float(self.hurdle_rate), 'high_water_mark': float(self.high_water_mark), 'leverage': float(self.leverage)}, 'performance_analysis': self.calculate_key_metrics(), 'liquidity_profile': self.liquidity_analysis()}

class HedgeFundPortfolio:
    """
    Portfolio-level hedge fund analysis
    CFA Standards: Multi-manager allocation and diversification
    """

    def __init__(self):
        self.hedge_funds: List[HedgeFundAnalyzer] = []

    def add_hedge_fund(self, hedge_fund: HedgeFundAnalyzer) -> None:
        """Add hedge fund to portfolio"""
        self.hedge_funds.append(hedge_fund)

    def strategy_diversification(self) -> Dict[str, Any]:
        """Analyze strategy diversification across portfolio"""
        strategy_allocation = {}
        total_nav = Decimal('0')
        for hf in self.hedge_funds:
            strategy = hf.strategy.value
            nav = hf.calculate_nav()
            if strategy not in strategy_allocation:
                strategy_allocation[strategy] = {'count': 0, 'total_nav': Decimal('0')}
            strategy_allocation[strategy]['count'] += 1
            strategy_allocation[strategy]['total_nav'] += nav
            total_nav += nav
        for strategy in strategy_allocation:
            allocation = strategy_allocation[strategy]
            allocation['weight'] = float(allocation['total_nav'] / total_nav) if total_nav > 0 else 0
            allocation['total_nav'] = float(allocation['total_nav'])
        return {'strategy_allocation': strategy_allocation, 'total_portfolio_nav': float(total_nav), 'number_of_strategies': len(strategy_allocation), 'number_of_funds': len(self.hedge_funds)}

    def portfolio_correlation_analysis(self) -> Dict[str, Any]:
        """Analyze correlations between hedge fund strategies"""
        if len(self.hedge_funds) < 2:
            return {'error': 'Need at least 2 hedge funds for correlation analysis'}
        fund_returns = {}
        for i, hf in enumerate(self.hedge_funds):
            returns = hf.calculate_simple_returns()
            if returns:
                fund_returns[f'fund_{i}_{hf.strategy.value}'] = returns
        if len(fund_returns) < 2:
            return {'error': 'Insufficient return data'}
        correlations = {}
        fund_names = list(fund_returns.keys())
        for i, fund1 in enumerate(fund_names):
            for j, fund2 in enumerate(fund_names[i + 1:], i + 1):
                returns1 = fund_returns[fund1]
                returns2 = fund_returns[fund2]
                if len(returns1) == len(returns2) and len(returns1) > 1:
                    correlation = self._calculate_correlation(returns1, returns2)
                    correlations[f'{fund1}_vs_{fund2}'] = float(correlation)
        return {'pairwise_correlations': correlations, 'funds_analyzed': fund_names}

    def _calculate_correlation(self, returns1: List[Decimal], returns2: List[Decimal]) -> Decimal:
        """Calculate correlation between two return series"""
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

def strategy_diversification(self) -> Dict[str, Any]:
    """Analyze strategy diversification across portfolio"""
    strategy_allocation = {}
    total_nav = Decimal('0')
    for hf in self.hedge_funds:
        strategy = hf.strategy.value
        nav = hf.calculate_nav()
        if strategy not in strategy_allocation:
            strategy_allocation[strategy] = {'count': 0, 'total_nav': Decimal('0')}
        strategy_allocation[strategy]['count'] += 1
        strategy_allocation[strategy]['total_nav'] += nav
        total_nav += nav
    for strategy in strategy_allocation:
        allocation = strategy_allocation[strategy]
        allocation['weight'] = float(allocation['total_nav'] / total_nav) if total_nav > 0 else 0
        allocation['total_nav'] = float(allocation['total_nav'])
    return {'strategy_allocation': strategy_allocation, 'total_portfolio_nav': float(total_nav), 'number_of_strategies': len(strategy_allocation), 'number_of_funds': len(self.hedge_funds)}

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

class Config:
    """Main configuration class"""
    PRICE_TOLERANCE = Decimal('0.0001')
    MAX_LEVERAGE = Decimal('10.0')
    MIN_PRICE = Decimal('0.0001')
    ANNUALIZATION_FACTOR = Constants.DAYS_IN_YEAR
    RISK_FREE_RATE = Constants.DEFAULT_RISK_FREE_RATE
    PE_IRR_TOLERANCE = Decimal('0.000001')
    PE_IRR_MAX_ITERATIONS = 1000
    RE_CAP_RATE_MIN = Decimal('0.01')
    RE_CAP_RATE_MAX = Decimal('0.20')
    COMMODITY_ROLL_DAYS = 5
    HF_HIGH_WATER_MARK_DEFAULT = True
    HF_HURDLE_RATE_DEFAULT = Decimal('0.08')
    CRYPTO_VOLATILITY_FLOOR = Decimal('0.10')
    MAX_CONCENTRATION = Decimal('0.50')
    MIN_WEIGHT = Decimal('0.001')
    DECIMAL_PLACES = 4
    PERCENTAGE_DECIMAL_PLACES = 2

    @classmethod
    def get_asset_defaults(cls, asset_class: AssetClass) -> Dict[str, Any]:
        """Get default parameters for asset class"""
        defaults = {AssetClass.PRIVATE_EQUITY: {'management_fee': Decimal('0.02'), 'performance_fee': Decimal('0.20'), 'lock_up_period': 120, 'minimum_investment': Decimal('1000000')}, AssetClass.PRIVATE_DEBT: {'management_fee': Decimal('0.015'), 'performance_fee': Decimal('0.10'), 'lock_up_period': 60, 'minimum_investment': Decimal('250000')}, AssetClass.REAL_ESTATE: {'management_fee': Decimal('0.01'), 'performance_fee': Decimal('0.15'), 'minimum_investment': Decimal('50000')}, AssetClass.HEDGE_FUND: {'management_fee': Decimal('0.02'), 'performance_fee': Decimal('0.20'), 'hurdle_rate': Decimal('0.08'), 'high_water_mark': True, 'minimum_investment': Decimal('100000')}, AssetClass.COMMODITIES: {'management_fee': Decimal('0.005'), 'minimum_investment': Decimal('10000')}, AssetClass.DIGITAL_ASSETS: {'management_fee': Decimal('0.01'), 'minimum_investment': Decimal('1000')}}
        return defaults.get(asset_class, {})

@classmethod
def get_asset_defaults(cls, asset_class: AssetClass) -> Dict[str, Any]:
    """Get default parameters for asset class"""
    defaults = {AssetClass.PRIVATE_EQUITY: {'management_fee': Decimal('0.02'), 'performance_fee': Decimal('0.20'), 'lock_up_period': 120, 'minimum_investment': Decimal('1000000')}, AssetClass.PRIVATE_DEBT: {'management_fee': Decimal('0.015'), 'performance_fee': Decimal('0.10'), 'lock_up_period': 60, 'minimum_investment': Decimal('250000')}, AssetClass.REAL_ESTATE: {'management_fee': Decimal('0.01'), 'performance_fee': Decimal('0.15'), 'minimum_investment': Decimal('50000')}, AssetClass.HEDGE_FUND: {'management_fee': Decimal('0.02'), 'performance_fee': Decimal('0.20'), 'hurdle_rate': Decimal('0.08'), 'high_water_mark': True, 'minimum_investment': Decimal('100000')}, AssetClass.COMMODITIES: {'management_fee': Decimal('0.005'), 'minimum_investment': Decimal('10000')}, AssetClass.DIGITAL_ASSETS: {'management_fee': Decimal('0.01'), 'minimum_investment': Decimal('1000')}}
    return defaults.get(asset_class, {})

class ValidationRules:
    """Validation rules for different asset classes"""

    @staticmethod
    def validate_performance_fee(fee: Decimal, asset_class: AssetClass) -> bool:
        """Validate performance fee ranges"""
        if asset_class == AssetClass.PRIVATE_EQUITY:
            return Decimal('0.15') <= fee <= Decimal('0.30')
        elif asset_class == AssetClass.HEDGE_FUND:
            return Decimal('0.10') <= fee <= Decimal('0.50')
        elif asset_class == AssetClass.REAL_ESTATE:
            return Decimal('0.05') <= fee <= Decimal('0.25')
        return True

    @staticmethod
    def validate_management_fee(fee: Decimal, asset_class: AssetClass) -> bool:
        """Validate management fee ranges"""
        return Decimal('0.001') <= fee <= Decimal('0.05')

    @staticmethod
    def validate_return(return_value: Decimal) -> bool:
        """Validate return values"""
        return Decimal('-0.99') <= return_value <= Decimal('10.0')

    @staticmethod
    def validate_volatility(vol: Decimal) -> bool:
        """Validate volatility values"""
        return Decimal('0.001') <= vol <= Decimal('5.0')

@staticmethod
def validate_performance_fee(fee: Decimal, asset_class: AssetClass) -> bool:
    """Validate performance fee ranges"""
    if asset_class == AssetClass.PRIVATE_EQUITY:
        return Decimal('0.15') <= fee <= Decimal('0.30')
    elif asset_class == AssetClass.HEDGE_FUND:
        return Decimal('0.10') <= fee <= Decimal('0.50')
    elif asset_class == AssetClass.REAL_ESTATE:
        return Decimal('0.05') <= fee <= Decimal('0.25')
    return True

@staticmethod
def validate_management_fee(fee: Decimal, asset_class: AssetClass) -> bool:
    """Validate management fee ranges"""
    return Decimal('0.001') <= fee <= Decimal('0.05')

@staticmethod
def validate_return(return_value: Decimal) -> bool:
    """Validate return values"""
    return Decimal('-0.99') <= return_value <= Decimal('10.0')

@staticmethod
def validate_volatility(vol: Decimal) -> bool:
    """Validate volatility values"""
    return Decimal('0.001') <= vol <= Decimal('5.0')

class DigitalAssetAnalyzer(AlternativeInvestmentBase):
    """
    Digital Asset investment analysis and valuation
    CFA Standards: Risk assessment, correlation analysis, portfolio integration
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.asset_type = getattr(parameters, 'asset_type', 'cryptocurrency')
        self.blockchain = getattr(parameters, 'blockchain', 'bitcoin')
        self.market_cap = getattr(parameters, 'market_cap', None)
        self.circulating_supply = getattr(parameters, 'circulating_supply', None)
        self.total_supply = getattr(parameters, 'total_supply', None)
        self.trading_volume_24h = getattr(parameters, 'trading_volume_24h', None)
        self.staking_yield = getattr(parameters, 'staking_yield', None)
        self.protocol_revenue = getattr(parameters, 'protocol_revenue', None)

    def fundamental_metrics(self) -> Dict[str, Any]:
        """
        Calculate fundamental valuation metrics for digital assets
        CFA Standard: Fundamental analysis adaptation for digital assets
        """
        metrics = {}
        if self.market_cap and self.circulating_supply:
            price_per_token = self.market_cap / self.circulating_supply
            metrics['price_per_token'] = float(price_per_token)
            metrics['market_cap'] = float(self.market_cap)
            metrics['circulating_supply'] = float(self.circulating_supply)
        if self.total_supply and self.circulating_supply:
            inflation_rate = (self.total_supply - self.circulating_supply) / self.circulating_supply
            metrics['potential_inflation'] = float(inflation_rate)
        if self.trading_volume_24h and self.market_cap:
            volume_to_mcap = self.trading_volume_24h / self.market_cap
            metrics['volume_to_market_cap'] = float(volume_to_mcap)
            if volume_to_mcap > Decimal('0.1'):
                liquidity_tier = 'high'
            elif volume_to_mcap > Decimal('0.01'):
                liquidity_tier = 'medium'
            else:
                liquidity_tier = 'low'
            metrics['liquidity_tier'] = liquidity_tier
        if self.staking_yield:
            metrics['staking_yield_annual'] = float(self.staking_yield)
            crypto_vol = self.config.CRYPTO_VOLATILITY_FLOOR
            if self.market_data:
                returns = self.calculate_simple_returns()
                if returns:
                    actual_vol = self.calculate_volatility(returns)
                    crypto_vol = max(actual_vol, crypto_vol)
            risk_adjusted_yield = self.staking_yield / crypto_vol
            metrics['risk_adjusted_staking_yield'] = float(risk_adjusted_yield)
        if self.protocol_revenue and self.market_cap:
            revenue_multiple = self.market_cap / self.protocol_revenue
            metrics['price_to_protocol_revenue'] = float(revenue_multiple)
        return metrics

    def volatility_analysis(self) -> Dict[str, Any]:
        """
        Comprehensive volatility analysis for digital assets
        CFA Standard: Risk measurement adapted for high volatility assets
        """
        returns = self.calculate_simple_returns()
        if not returns:
            return {'error': 'Insufficient price data for volatility analysis'}
        analysis = {}
        daily_vol = self.calculate_volatility(returns, annualized=False)
        annualized_vol = daily_vol * Constants.DAYS_IN_YEAR.sqrt()
        analysis['daily_volatility'] = float(daily_vol)
        analysis['annualized_volatility'] = float(annualized_vol)
        return_magnitudes = [abs(r) for r in returns]
        sorted_magnitudes = sorted(return_magnitudes)
        if len(sorted_magnitudes) >= 10:
            p90_vol = sorted_magnitudes[int(0.9 * len(sorted_magnitudes))]
            p95_vol = sorted_magnitudes[int(0.95 * len(sorted_magnitudes))]
            p99_vol = sorted_magnitudes[int(0.99 * len(sorted_magnitudes))]
            analysis['90th_percentile_move'] = float(p90_vol)
            analysis['95th_percentile_move'] = float(p95_vol)
            analysis['99th_percentile_move'] = float(p99_vol)
        vol_clustering = self._detect_volatility_clustering(returns)
        analysis['volatility_clustering'] = vol_clustering
        traditional_equity_vol = Decimal('0.16')
        vol_multiple = annualized_vol / traditional_equity_vol
        analysis['volatility_vs_equity'] = float(vol_multiple)
        return analysis

    def _detect_volatility_clustering(self, returns: List[Decimal]) -> Dict[str, Any]:
        """Detect volatility clustering patterns"""
        if len(returns) < 20:
            return {'insufficient_data': True}
        window = min(10, len(returns) // 4)
        rolling_vols = []
        for i in range(window, len(returns)):
            window_returns = returns[i - window:i]
            window_vol = self.calculate_volatility(window_returns, annualized=False)
            rolling_vols.append(window_vol)
        if len(rolling_vols) < 2:
            return {'insufficient_data': True}
        vol_changes = []
        for i in range(1, len(rolling_vols)):
            vol_change = (rolling_vols[i] - rolling_vols[i - 1]) / rolling_vols[i - 1]
            vol_changes.append(vol_change)
        clustering_score = len([v for v in vol_changes if abs(v) < Decimal('0.1')]) / len(vol_changes)
        return {'clustering_score': float(clustering_score), 'interpretation': 'High' if clustering_score > 0.6 else 'Medium' if clustering_score > 0.4 else 'Low'}

    def correlation_analysis(self, benchmark_returns: List[Decimal], traditional_assets: Dict[str, List[Decimal]]=None) -> Dict[str, Any]:
        """
        Analyze correlations with traditional assets and crypto market
        CFA Standard: Diversification benefit analysis
        """
        crypto_returns = self.calculate_simple_returns()
        if not crypto_returns or not benchmark_returns:
            return {'error': 'Insufficient return data'}
        if len(crypto_returns) != len(benchmark_returns):
            return {'error': 'Return series length mismatch'}
        analysis = {}
        crypto_correlation = self._calculate_correlation(crypto_returns, benchmark_returns)
        analysis['crypto_market_correlation'] = float(crypto_correlation)
        crypto_beta = self._calculate_beta(crypto_returns, benchmark_returns)
        analysis['crypto_market_beta'] = float(crypto_beta)
        if traditional_assets:
            traditional_correlations = {}
            for asset_name, asset_returns in traditional_assets.items():
                if len(asset_returns) == len(crypto_returns):
                    correlation = self._calculate_correlation(crypto_returns, asset_returns)
                    traditional_correlations[asset_name] = float(correlation)
            analysis['traditional_asset_correlations'] = traditional_correlations
            if traditional_correlations:
                avg_traditional_corr = sum(traditional_correlations.values()) / len(traditional_correlations)
                analysis['average_traditional_correlation'] = avg_traditional_corr
                if avg_traditional_corr < 0.3:
                    diversification_benefit = 'High'
                elif avg_traditional_corr < 0.6:
                    diversification_benefit = 'Medium'
                else:
                    diversification_benefit = 'Low'
                analysis['diversification_benefit'] = diversification_benefit
        return analysis

    def _calculate_correlation(self, returns1: List[Decimal], returns2: List[Decimal]) -> Decimal:
        """Calculate correlation coefficient between two return series"""
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

    def _calculate_beta(self, asset_returns: List[Decimal], market_returns: List[Decimal]) -> Decimal:
        """Calculate beta relative to market"""
        if len(asset_returns) != len(market_returns) or len(asset_returns) < 2:
            return Decimal('1')
        asset_mean = sum(asset_returns) / len(asset_returns)
        market_mean = sum(market_returns) / len(market_returns)
        covariance = sum(((a - asset_mean) * (m - market_mean) for a, m in zip(asset_returns, market_returns))) / (len(asset_returns) - 1)
        market_variance = sum(((m - market_mean) ** 2 for m in market_returns)) / (len(market_returns) - 1)
        if market_variance == 0:
            return Decimal('1')
        return Decimal(str(covariance)) / Decimal(str(market_variance))

    def defi_protocol_analysis(self) -> Dict[str, Any]:
        """
        Analyze DeFi protocol fundamentals
        CFA Standard: Business model analysis for DeFi protocols
        """
        if self.asset_type != 'defi_token':
            return {'not_applicable': 'Analysis specific to DeFi tokens'}
        analysis = {}
        if self.protocol_revenue and self.market_cap:
            p_revenue = self.market_cap / self.protocol_revenue
            analysis['price_to_revenue'] = float(p_revenue)
            revenue_yield = self.protocol_revenue / self.market_cap
            analysis['revenue_yield'] = float(revenue_yield)
        utility_factors = {'governance_rights': True, 'fee_discounts': None, 'staking_rewards': self.staking_yield is not None, 'protocol_fees_capture': self.protocol_revenue is not None}
        analysis['token_utility'] = utility_factors
        utility_score = sum((1 for v in utility_factors.values() if v is True))
        analysis['utility_score'] = utility_score
        analysis['max_utility_score'] = len(utility_factors)
        return analysis

    def risk_assessment(self) -> Dict[str, Any]:
        """
        Comprehensive risk assessment for digital assets
        CFA Standard: Risk identification and measurement
        """
        risk_assessment = {}
        risk_assessment['technology_risk'] = {'smart_contract_risk': self.asset_type in ['defi_token'], 'blockchain_risk': self.blockchain, 'upgrade_risk': True}
        risk_assessment['regulatory_risk'] = {'classification_uncertainty': True, 'geographic_restrictions': 'varies_by_jurisdiction', 'compliance_requirements': 'evolving'}
        returns = self.calculate_simple_returns()
        if returns:
            vol_analysis = self.volatility_analysis()
            if 'annualized_volatility' in vol_analysis:
                annual_vol = vol_analysis['annualized_volatility']
                if annual_vol > 1.0:
                    risk_tier = 'Very High'
                elif annual_vol > 0.5:
                    risk_tier = 'High'
                elif annual_vol > 0.3:
                    risk_tier = 'Medium-High'
                else:
                    risk_tier = 'Medium'
                risk_assessment['market_risk_tier'] = risk_tier
        if self.trading_volume_24h and self.market_cap:
            volume_ratio = self.trading_volume_24h / self.market_cap
            if volume_ratio < Decimal('0.001'):
                liquidity_risk = 'High'
            elif volume_ratio < Decimal('0.01'):
                liquidity_risk = 'Medium'
            else:
                liquidity_risk = 'Low'
            risk_assessment['liquidity_risk'] = liquidity_risk
        if self.circulating_supply and self.total_supply:
            supply_concentration = (self.total_supply - self.circulating_supply) / self.total_supply
            risk_assessment['supply_concentration_risk'] = float(supply_concentration)
        return risk_assessment

    def portfolio_integration_analysis(self, portfolio_returns: List[Decimal], target_allocation: Decimal=Decimal('0.05')) -> Dict[str, Any]:
        """
        Analyze impact of adding digital asset to traditional portfolio
        CFA Standard: Portfolio optimization with alternative assets
        """
        crypto_returns = self.calculate_simple_returns()
        if not crypto_returns or not portfolio_returns:
            return {'error': 'Insufficient return data'}
        if len(crypto_returns) != len(portfolio_returns):
            return {'error': 'Return series length mismatch'}
        integration_analysis = {}
        portfolio_correlation = self._calculate_correlation(crypto_returns, portfolio_returns)
        integration_analysis['portfolio_correlation'] = float(portfolio_correlation)
        crypto_weight = target_allocation
        portfolio_weight = Decimal('1') - crypto_weight
        crypto_mean = sum(crypto_returns) / len(crypto_returns)
        portfolio_mean = sum(portfolio_returns) / len(portfolio_returns)
        combined_expected_return = crypto_weight * crypto_mean + portfolio_weight * portfolio_mean
        integration_analysis['expected_return_with_crypto'] = float(combined_expected_return)
        crypto_vol = self.calculate_volatility(crypto_returns, annualized=False)
        portfolio_vol = self._calculate_volatility(portfolio_returns)
        combined_variance = crypto_weight ** 2 * crypto_vol ** 2 + portfolio_weight ** 2 * portfolio_vol ** 2 + 2 * crypto_weight * portfolio_weight * portfolio_correlation * crypto_vol * portfolio_vol
        combined_volatility = combined_variance.sqrt()
        integration_analysis['expected_volatility_with_crypto'] = float(combined_volatility)
        risk_free_rate = Config.RISK_FREE_RATE / Constants.MONTHS_IN_YEAR
        original_sharpe = (portfolio_mean - risk_free_rate) / portfolio_vol if portfolio_vol > 0 else Decimal('0')
        combined_sharpe = (combined_expected_return - risk_free_rate) / combined_volatility if combined_volatility > 0 else Decimal('0')
        integration_analysis['original_sharpe_ratio'] = float(original_sharpe)
        integration_analysis['combined_sharpe_ratio'] = float(combined_sharpe)
        integration_analysis['sharpe_improvement'] = float(combined_sharpe - original_sharpe)
        diversification_ratio = combined_volatility / (crypto_weight * crypto_vol + portfolio_weight * portfolio_vol)
        integration_analysis['diversification_ratio'] = float(diversification_ratio)
        return integration_analysis

    def _calculate_volatility(self, returns: List[Decimal]) -> Decimal:
        """Calculate volatility of returns"""
        if len(returns) < 2:
            return Decimal('0')
        mean_return = sum(returns) / len(returns)
        variance = sum(((r - mean_return) ** 2 for r in returns)) / (len(returns) - 1)
        return variance.sqrt()

    def calculate_nav(self) -> Decimal:
        """Calculate digital asset NAV"""
        latest_price = self.get_latest_price()
        if latest_price:
            return latest_price
        if self.market_cap and self.circulating_supply:
            return self.market_cap / self.circulating_supply
        return Decimal('0')

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive digital asset metrics"""
        metrics = {}
        fundamental_metrics = self.fundamental_metrics()
        metrics.update(fundamental_metrics)
        vol_analysis = self.volatility_analysis()
        if 'error' not in vol_analysis:
            metrics.update(vol_analysis)
        risk_metrics = self.risk_assessment()
        metrics.update(risk_metrics)
        if self.asset_type == 'defi_token':
            defi_metrics = self.defi_protocol_analysis()
            if 'not_applicable' not in defi_metrics:
                metrics.update(defi_metrics)
        metrics['asset_type'] = self.asset_type
        metrics['blockchain'] = self.blockchain
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive digital asset valuation summary"""
        return {'asset_overview': {'asset_type': self.asset_type, 'blockchain': self.blockchain, 'market_cap': float(self.market_cap) if self.market_cap else None, 'circulating_supply': float(self.circulating_supply) if self.circulating_supply else None, 'trading_volume_24h': float(self.trading_volume_24h) if self.trading_volume_24h else None}, 'fundamental_analysis': self.fundamental_metrics(), 'risk_analysis': self.risk_assessment(), 'performance_metrics': self.calculate_key_metrics()}

def fundamental_metrics(self) -> Dict[str, Any]:
    """
        Calculate fundamental valuation metrics for digital assets
        CFA Standard: Fundamental analysis adaptation for digital assets
        """
    metrics = {}
    if self.market_cap and self.circulating_supply:
        price_per_token = self.market_cap / self.circulating_supply
        metrics['price_per_token'] = float(price_per_token)
        metrics['market_cap'] = float(self.market_cap)
        metrics['circulating_supply'] = float(self.circulating_supply)
    if self.total_supply and self.circulating_supply:
        inflation_rate = (self.total_supply - self.circulating_supply) / self.circulating_supply
        metrics['potential_inflation'] = float(inflation_rate)
    if self.trading_volume_24h and self.market_cap:
        volume_to_mcap = self.trading_volume_24h / self.market_cap
        metrics['volume_to_market_cap'] = float(volume_to_mcap)
        if volume_to_mcap > Decimal('0.1'):
            liquidity_tier = 'high'
        elif volume_to_mcap > Decimal('0.01'):
            liquidity_tier = 'medium'
        else:
            liquidity_tier = 'low'
        metrics['liquidity_tier'] = liquidity_tier
    if self.staking_yield:
        metrics['staking_yield_annual'] = float(self.staking_yield)
        crypto_vol = self.config.CRYPTO_VOLATILITY_FLOOR
        if self.market_data:
            returns = self.calculate_simple_returns()
            if returns:
                actual_vol = self.calculate_volatility(returns)
                crypto_vol = max(actual_vol, crypto_vol)
        risk_adjusted_yield = self.staking_yield / crypto_vol
        metrics['risk_adjusted_staking_yield'] = float(risk_adjusted_yield)
    if self.protocol_revenue and self.market_cap:
        revenue_multiple = self.market_cap / self.protocol_revenue
        metrics['price_to_protocol_revenue'] = float(revenue_multiple)
    return metrics

def _detect_volatility_clustering(self, returns: List[Decimal]) -> Dict[str, Any]:
    """Detect volatility clustering patterns"""
    if len(returns) < 20:
        return {'insufficient_data': True}
    window = min(10, len(returns) // 4)
    rolling_vols = []
    for i in range(window, len(returns)):
        window_returns = returns[i - window:i]
        window_vol = self.calculate_volatility(window_returns, annualized=False)
        rolling_vols.append(window_vol)
    if len(rolling_vols) < 2:
        return {'insufficient_data': True}
    vol_changes = []
    for i in range(1, len(rolling_vols)):
        vol_change = (rolling_vols[i] - rolling_vols[i - 1]) / rolling_vols[i - 1]
        vol_changes.append(vol_change)
    clustering_score = len([v for v in vol_changes if abs(v) < Decimal('0.1')]) / len(vol_changes)
    return {'clustering_score': float(clustering_score), 'interpretation': 'High' if clustering_score > 0.6 else 'Medium' if clustering_score > 0.4 else 'Low'}

def risk_assessment(self) -> Dict[str, Any]:
    """
        Comprehensive risk assessment for digital assets
        CFA Standard: Risk identification and measurement
        """
    risk_assessment = {}
    risk_assessment['technology_risk'] = {'smart_contract_risk': self.asset_type in ['defi_token'], 'blockchain_risk': self.blockchain, 'upgrade_risk': True}
    risk_assessment['regulatory_risk'] = {'classification_uncertainty': True, 'geographic_restrictions': 'varies_by_jurisdiction', 'compliance_requirements': 'evolving'}
    returns = self.calculate_simple_returns()
    if returns:
        vol_analysis = self.volatility_analysis()
        if 'annualized_volatility' in vol_analysis:
            annual_vol = vol_analysis['annualized_volatility']
            if annual_vol > 1.0:
                risk_tier = 'Very High'
            elif annual_vol > 0.5:
                risk_tier = 'High'
            elif annual_vol > 0.3:
                risk_tier = 'Medium-High'
            else:
                risk_tier = 'Medium'
            risk_assessment['market_risk_tier'] = risk_tier
    if self.trading_volume_24h and self.market_cap:
        volume_ratio = self.trading_volume_24h / self.market_cap
        if volume_ratio < Decimal('0.001'):
            liquidity_risk = 'High'
        elif volume_ratio < Decimal('0.01'):
            liquidity_risk = 'Medium'
        else:
            liquidity_risk = 'Low'
        risk_assessment['liquidity_risk'] = liquidity_risk
    if self.circulating_supply and self.total_supply:
        supply_concentration = (self.total_supply - self.circulating_supply) / self.total_supply
        risk_assessment['supply_concentration_risk'] = float(supply_concentration)
    return risk_assessment

def calculate_nav(self) -> Decimal:
    """Calculate digital asset NAV"""
    latest_price = self.get_latest_price()
    if latest_price:
        return latest_price
    if self.market_cap and self.circulating_supply:
        return self.market_cap / self.circulating_supply
    return Decimal('0')

def calculate_key_metrics(self) -> Dict[str, Any]:
    """Calculate comprehensive digital asset metrics"""
    metrics = {}
    fundamental_metrics = self.fundamental_metrics()
    metrics.update(fundamental_metrics)
    vol_analysis = self.volatility_analysis()
    if 'error' not in vol_analysis:
        metrics.update(vol_analysis)
    risk_metrics = self.risk_assessment()
    metrics.update(risk_metrics)
    if self.asset_type == 'defi_token':
        defi_metrics = self.defi_protocol_analysis()
        if 'not_applicable' not in defi_metrics:
            metrics.update(defi_metrics)
    metrics['asset_type'] = self.asset_type
    metrics['blockchain'] = self.blockchain
    return metrics

def valuation_summary(self) -> Dict[str, Any]:
    """Comprehensive digital asset valuation summary"""
    return {'asset_overview': {'asset_type': self.asset_type, 'blockchain': self.blockchain, 'market_cap': float(self.market_cap) if self.market_cap else None, 'circulating_supply': float(self.circulating_supply) if self.circulating_supply else None, 'trading_volume_24h': float(self.trading_volume_24h) if self.trading_volume_24h else None}, 'fundamental_analysis': self.fundamental_metrics(), 'risk_analysis': self.risk_assessment(), 'performance_metrics': self.calculate_key_metrics()}

class DigitalAssetPortfolio:
    """
    Portfolio-level digital asset analysis
    CFA Standards: Portfolio construction and risk management
    """

    def __init__(self):
        self.digital_assets: List[DigitalAssetAnalyzer] = []

    def add_digital_asset(self, asset: DigitalAssetAnalyzer) -> None:
        """Add digital asset to portfolio"""
        self.digital_assets.append(asset)

    def portfolio_diversification(self) -> Dict[str, Any]:
        """Analyze portfolio diversification across digital asset types"""
        type_allocation = {}
        blockchain_allocation = {}
        total_nav = Decimal('0')
        for asset in self.digital_assets:
            asset_type = asset.asset_type
            blockchain = asset.blockchain
            nav = asset.calculate_nav()
            if asset_type not in type_allocation:
                type_allocation[asset_type] = {'count': 0, 'total_nav': Decimal('0')}
            type_allocation[asset_type]['count'] += 1
            type_allocation[asset_type]['total_nav'] += nav
            if blockchain not in blockchain_allocation:
                blockchain_allocation[blockchain] = {'count': 0, 'total_nav': Decimal('0')}
            blockchain_allocation[blockchain]['count'] += 1
            blockchain_allocation[blockchain]['total_nav'] += nav
            total_nav += nav
        for allocation_dict in [type_allocation, blockchain_allocation]:
            for key in allocation_dict:
                allocation = allocation_dict[key]
                allocation['weight'] = float(allocation['total_nav'] / total_nav) if total_nav > 0 else 0
                allocation['total_nav'] = float(allocation['total_nav'])
        return {'asset_type_allocation': type_allocation, 'blockchain_allocation': blockchain_allocation, 'total_portfolio_nav': float(total_nav), 'number_of_assets': len(self.digital_assets)}

    def portfolio_risk_metrics(self) -> Dict[str, Any]:
        """Calculate portfolio-level risk metrics"""
        all_returns = []
        weights = []
        total_nav = sum((asset.calculate_nav() for asset in self.digital_assets))
        for asset in self.digital_assets:
            asset_returns = asset.calculate_simple_returns()
            if asset_returns:
                all_returns.append(asset_returns)
                weight = asset.calculate_nav() / total_nav if total_nav > 0 else Decimal('0')
                weights.append(weight)
        if not all_returns:
            return {'error': 'No return data available'}
        if not weights:
            weights = [Decimal('1') / len(all_returns)] * len(all_returns)
        min_length = min((len(returns) for returns in all_returns))
        portfolio_returns = []
        for i in range(min_length):
            period_return = sum((weight * returns[i] for weight, returns in zip(weights, all_returns)))
            portfolio_returns.append(period_return)
        if not portfolio_returns:
            return {'error': 'Cannot calculate portfolio returns'}
        portfolio_vol = self._calculate_portfolio_volatility(portfolio_returns)
        portfolio_var = self._calculate_var(portfolio_returns)
        return {'portfolio_volatility': float(portfolio_vol), 'portfolio_var_95': float(portfolio_var), 'number_of_periods': len(portfolio_returns), 'correlation_weighted_risk': 'high'}

    def _calculate_portfolio_volatility(self, returns: List[Decimal]) -> Decimal:
        """Calculate portfolio volatility"""
        if len(returns) < 2:
            return Decimal('0')
        mean_return = sum(returns) / len(returns)
        variance = sum(((r - mean_return) ** 2 for r in returns)) / (len(returns) - 1)
        daily_vol = variance.sqrt()
        return daily_vol * Constants.DAYS_IN_YEAR.sqrt()

    def _calculate_var(self, returns: List[Decimal], confidence: Decimal=Decimal('0.05')) -> Decimal:
        """Calculate Value at Risk"""
        if not returns:
            return Decimal('0')
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * confidence)
        if var_index >= len(sorted_returns):
            var_index = len(sorted_returns) - 1
        return abs(sorted_returns[var_index])

def portfolio_diversification(self) -> Dict[str, Any]:
    """Analyze portfolio diversification across digital asset types"""
    type_allocation = {}
    blockchain_allocation = {}
    total_nav = Decimal('0')
    for asset in self.digital_assets:
        asset_type = asset.asset_type
        blockchain = asset.blockchain
        nav = asset.calculate_nav()
        if asset_type not in type_allocation:
            type_allocation[asset_type] = {'count': 0, 'total_nav': Decimal('0')}
        type_allocation[asset_type]['count'] += 1
        type_allocation[asset_type]['total_nav'] += nav
        if blockchain not in blockchain_allocation:
            blockchain_allocation[blockchain] = {'count': 0, 'total_nav': Decimal('0')}
        blockchain_allocation[blockchain]['count'] += 1
        blockchain_allocation[blockchain]['total_nav'] += nav
        total_nav += nav
    for allocation_dict in [type_allocation, blockchain_allocation]:
        for key in allocation_dict:
            allocation = allocation_dict[key]
            allocation['weight'] = float(allocation['total_nav'] / total_nav) if total_nav > 0 else 0
            allocation['total_nav'] = float(allocation['total_nav'])
    return {'asset_type_allocation': type_allocation, 'blockchain_allocation': blockchain_allocation, 'total_portfolio_nav': float(total_nav), 'number_of_assets': len(self.digital_assets)}

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

def _analyze_volume_patterns(self, volumes: List[Decimal]) -> Dict[str, Any]:
    """Analyze trading volume patterns for liquidity assessment"""
    if not volumes:
        return {}
    avg_volume = sum(volumes) / len(volumes)
    volume_volatility = self._calculate_volatility(volumes)
    volume_stability = 1 - volume_volatility / avg_volume if avg_volume > 0 else 0
    return {'average_volume': float(avg_volume), 'volume_volatility': float(volume_volatility), 'volume_stability': float(volume_stability)}

def _analyze_bid_ask_spreads(self, spreads: List[Decimal]) -> Dict[str, Any]:
    """Analyze bid-ask spreads for liquidity assessment"""
    if not spreads:
        return {}
    avg_spread = sum(spreads) / len(spreads)
    spread_volatility = self._calculate_volatility(spreads)
    return {'average_spread': float(avg_spread), 'spread_volatility': float(spread_volatility), 'spread_stability': float(1 - spread_volatility / avg_spread) if avg_spread > 0 else 0}

def _calculate_drawdown_statistics(self, drawdowns: List[Decimal]) -> Dict[str, Any]:
    """Calculate comprehensive drawdown statistics"""
    if not drawdowns:
        return {}
    max_dd = max(drawdowns)
    avg_dd = sum(drawdowns) / len(drawdowns)
    periods_in_drawdown = sum((1 for dd in drawdowns if dd > 0))
    drawdown_frequency = periods_in_drawdown / len(drawdowns)
    return {'maximum_drawdown': float(max_dd), 'average_drawdown': float(avg_dd), 'drawdown_frequency': float(drawdown_frequency), 'periods_in_drawdown': periods_in_drawdown, 'total_periods': len(drawdowns)}

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

class PortfolioRiskAnalyzer:
    """
    Portfolio-level risk analysis across multiple alternative investments
    CFA Standards: Portfolio risk management and optimization
    """

    def __init__(self):
        self.risk_analyzer = RiskAnalyzer()

    def portfolio_var_analysis(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal]) -> Dict[str, Any]:
        """
        Calculate portfolio VaR considering correlations
        CFA Standard: Portfolio VaR with correlation matrix
        """
        if not asset_returns or not portfolio_weights:
            return {'error': 'Asset returns and weights required'}
        total_weight = sum(portfolio_weights.values())
        if abs(total_weight - Decimal('1')) > Decimal('0.01'):
            return {'error': f'Weights sum to {total_weight}, should be 1.0'}
        portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
        if not portfolio_returns:
            return {'error': 'Cannot calculate portfolio returns'}
        portfolio_var = self.risk_analyzer.value_at_risk_analysis(portfolio_returns)
        component_var = self._calculate_component_var(asset_returns, portfolio_weights)
        return {'portfolio_var': portfolio_var, 'component_var': component_var, 'portfolio_statistics': {'mean_return': float(sum(portfolio_returns) / len(portfolio_returns)), 'volatility': float(self.risk_analyzer._calculate_volatility(portfolio_returns)), 'number_of_assets': len(portfolio_weights)}}

    def risk_budget_analysis(self, asset_returns: Dict[str, List[Decimal]], target_risk_budgets: Dict[str, Decimal]) -> Dict[str, Any]:
        """
        Analyze risk budgeting and contribution
        CFA Standard: Risk budgeting framework
        """
        risk_analysis = {}
        asset_volatilities = {}
        for asset, returns in asset_returns.items():
            vol = self.risk_analyzer._calculate_volatility(returns)
            asset_volatilities[asset] = vol
        correlation_matrix = self.risk_analyzer._calculate_correlation_matrix(asset_returns)
        risk_contributions = self._calculate_risk_contributions_detailed(asset_volatilities, correlation_matrix, target_risk_budgets)
        risk_analysis['risk_contributions'] = risk_contributions
        risk_analysis['target_risk_budgets'] = {k: float(v) for k, v in target_risk_budgets.items()}
        risk_analysis['asset_volatilities'] = {k: float(v) for k, v in asset_volatilities.items()}
        return risk_analysis

    def portfolio_stress_testing(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal], stress_scenarios: Dict[str, Dict[str, Decimal]]) -> Dict[str, Any]:
        """
        Comprehensive portfolio stress testing
        CFA Standard: Portfolio stress testing across scenarios
        """
        stress_results = {}
        portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
        baseline_metrics = {'mean_return': float(sum(portfolio_returns) / len(portfolio_returns)), 'volatility': float(self.risk_analyzer._calculate_volatility(portfolio_returns))}
        stress_results['baseline_metrics'] = baseline_metrics
        scenario_impacts = {}
        for scenario_name, scenario_shocks in stress_scenarios.items():
            scenario_impact = self._apply_portfolio_stress_scenario(asset_returns, portfolio_weights, scenario_shocks)
            scenario_impacts[scenario_name] = scenario_impact
        stress_results['scenario_impacts'] = scenario_impacts
        worst_case = self._identify_worst_case_scenario(scenario_impacts)
        stress_results['worst_case_scenario'] = worst_case
        return stress_results

    def liquidity_risk_portfolio(self, asset_liquidity_scores: Dict[str, float], portfolio_weights: Dict[str, Decimal]) -> Dict[str, Any]:
        """
        Analyze portfolio-level liquidity risk
        CFA Standard: Portfolio liquidity management
        """
        liquidity_analysis = {}
        weighted_liquidity = Decimal('0')
        for asset, weight in portfolio_weights.items():
            if asset in asset_liquidity_scores:
                liquidity_score = Decimal(str(asset_liquidity_scores[asset]))
                weighted_liquidity += weight * liquidity_score
        liquidity_analysis['weighted_average_liquidity'] = float(weighted_liquidity)
        liquidity_buckets = {'high': Decimal('0'), 'medium': Decimal('0'), 'low': Decimal('0')}
        for asset, weight in portfolio_weights.items():
            if asset in asset_liquidity_scores:
                score = asset_liquidity_scores[asset]
                if score >= 70:
                    liquidity_buckets['high'] += weight
                elif score >= 40:
                    liquidity_buckets['medium'] += weight
                else:
                    liquidity_buckets['low'] += weight
        liquidity_analysis['liquidity_buckets'] = {k: float(v) for k, v in liquidity_buckets.items()}
        if weighted_liquidity >= 70:
            risk_level = 'Low'
        elif weighted_liquidity >= 50:
            risk_level = 'Medium'
        else:
            risk_level = 'High'
        liquidity_analysis['portfolio_liquidity_risk'] = risk_level
        return liquidity_analysis

    def concentration_risk_analysis(self, portfolio_weights: Dict[str, Decimal], asset_classifications: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyze concentration risk across multiple dimensions
        CFA Standard: Concentration risk management
        """
        concentration_analysis = {}
        max_weight = max(portfolio_weights.values())
        concentration_analysis['maximum_single_asset_weight'] = float(max_weight)
        asset_class_weights = {}
        for asset, weight in portfolio_weights.items():
            if asset in asset_classifications:
                asset_class = asset_classifications[asset].get('asset_class', 'unknown')
                if asset_class not in asset_class_weights:
                    asset_class_weights[asset_class] = Decimal('0')
                asset_class_weights[asset_class] += weight
        concentration_analysis['asset_class_concentration'] = {k: float(v) for k, v in asset_class_weights.items()}
        geographic_weights = {}
        for asset, weight in portfolio_weights.items():
            if asset in asset_classifications:
                geography = asset_classifications[asset].get('geography', 'unknown')
                if geography not in geographic_weights:
                    geographic_weights[geography] = Decimal('0')
                geographic_weights[geography] += weight
        concentration_analysis['geographic_concentration'] = {k: float(v) for k, v in geographic_weights.items()}
        concentration_score = self._calculate_concentration_score(max_weight, asset_class_weights, geographic_weights)
        concentration_analysis['concentration_risk_score'] = concentration_score
        return concentration_analysis

    def _calculate_portfolio_returns(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal]) -> List[Decimal]:
        """Calculate portfolio returns given weights"""
        min_length = min((len(returns) for returns in asset_returns.values() if returns))
        if min_length == 0:
            return []
        portfolio_returns = []
        for i in range(min_length):
            period_return = Decimal('0')
            for asset, weight in portfolio_weights.items():
                if asset in asset_returns and i < len(asset_returns[asset]):
                    period_return += weight * asset_returns[asset][i]
            portfolio_returns.append(period_return)
        return portfolio_returns

    def _calculate_component_var(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal]) -> Dict[str, Any]:
        """Calculate component VaR for each asset"""
        component_vars = {}
        portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
        if not portfolio_returns:
            return component_vars
        portfolio_var_95 = self.risk_analyzer.math.var_historical(portfolio_returns, Decimal('0.05'))
        for asset, weight in portfolio_weights.items():
            if asset in asset_returns:
                asset_return_series = asset_returns[asset][:len(portfolio_returns)]
                if asset_return_series:
                    correlation = self.risk_analyzer._calculate_correlation(asset_return_series, portfolio_returns)
                    asset_vol = self.risk_analyzer._calculate_volatility(asset_return_series)
                    portfolio_vol = self.risk_analyzer._calculate_volatility(portfolio_returns)
                    if portfolio_vol > 0:
                        component_var = weight * correlation * (asset_vol / portfolio_vol) * portfolio_var_95
                        component_vars[asset] = float(component_var)
        return component_vars

    def _calculate_risk_contributions_detailed(self, asset_volatilities: Dict[str, Decimal], correlation_matrix: Dict[str, Dict[str, float]], target_risk_budgets: Dict[str, Decimal]) -> Dict[str, Any]:
        """Calculate detailed risk contributions"""
        risk_contributions = {}
        assets = list(asset_volatilities.keys())
        for asset in assets:
            asset_vol = asset_volatilities[asset]
            correlations = []
            for other_asset in assets:
                if other_asset != asset and other_asset in correlation_matrix.get(asset, {}):
                    correlations.append(correlation_matrix[asset][other_asset])
            avg_correlation = sum(correlations) / len(correlations) if correlations else 0
            target_budget = target_risk_budgets.get(asset, Decimal('0'))
            risk_contribution = float(asset_vol * target_budget * Decimal(str(avg_correlation)))
            risk_contributions[asset] = {'risk_contribution': risk_contribution, 'target_budget': float(target_budget), 'asset_volatility': float(asset_vol), 'average_correlation': avg_correlation}
        return risk_contributions

    def _apply_portfolio_stress_scenario(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal], scenario_shocks: Dict[str, Decimal]) -> Dict[str, Any]:
        """Apply stress scenario to portfolio"""
        scenario_impact = {}
        portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
        baseline_return = sum(portfolio_returns) / len(portfolio_returns) if portfolio_returns else Decimal('0')
        stressed_return = Decimal('0')
        for asset, weight in portfolio_weights.items():
            asset_shock = scenario_shocks.get(asset, Decimal('0'))
            if asset in asset_returns and asset_returns[asset]:
                asset_baseline = sum(asset_returns[asset]) / len(asset_returns[asset])
                stressed_asset_return = asset_baseline + asset_shock
            else:
                stressed_asset_return = asset_shock
            stressed_return += weight * stressed_asset_return
        impact = stressed_return - baseline_return
        scenario_impact['baseline_return'] = float(baseline_return)
        scenario_impact['stressed_return'] = float(stressed_return)
        scenario_impact['impact'] = float(impact)
        scenario_impact['impact_percentage'] = float(impact / baseline_return * 100) if baseline_return != 0 else 0
        return scenario_impact

    def _identify_worst_case_scenario(self, scenario_impacts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Identify worst case scenario from stress testing"""
        worst_case = {}
        worst_impact = 0
        worst_scenario = None
        for scenario_name, impact_data in scenario_impacts.items():
            if isinstance(impact_data, dict) and 'impact' in impact_data:
                impact = impact_data['impact']
                if impact < worst_impact:
                    worst_impact = impact
                    worst_scenario = scenario_name
        if worst_scenario:
            worst_case['worst_scenario_name'] = worst_scenario
            worst_case['worst_impact'] = worst_impact
            worst_case['worst_scenario_details'] = scenario_impacts[worst_scenario]
        return worst_case

    def _calculate_concentration_score(self, max_single_weight: Decimal, asset_class_weights: Dict[str, Decimal], geographic_weights: Dict[str, Decimal]) -> Dict[str, Any]:
        """Calculate concentration risk score"""
        score_components = {}
        single_asset_score = float(max_single_weight * 100)
        score_components['single_asset_concentration'] = single_asset_score
        if asset_class_weights:
            hhi_asset_class = sum((weight ** 2 for weight in asset_class_weights.values()))
            asset_class_score = float(hhi_asset_class * 100)
            score_components['asset_class_concentration'] = asset_class_score
        if geographic_weights:
            hhi_geographic = sum((weight ** 2 for weight in geographic_weights.values()))
            geographic_score = float(hhi_geographic * 100)
            score_components['geographic_concentration'] = geographic_score
        scores = list(score_components.values())
        composite_score = sum(scores) / len(scores) if scores else 0
        if composite_score < 30:
            risk_level = 'Low'
        elif composite_score < 60:
            risk_level = 'Medium'
        else:
            risk_level = 'High'
        return {'composite_concentration_score': composite_score, 'concentration_risk_level': risk_level, 'score_components': score_components}

def portfolio_var_analysis(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal]) -> Dict[str, Any]:
    """
        Calculate portfolio VaR considering correlations
        CFA Standard: Portfolio VaR with correlation matrix
        """
    if not asset_returns or not portfolio_weights:
        return {'error': 'Asset returns and weights required'}
    total_weight = sum(portfolio_weights.values())
    if abs(total_weight - Decimal('1')) > Decimal('0.01'):
        return {'error': f'Weights sum to {total_weight}, should be 1.0'}
    portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
    if not portfolio_returns:
        return {'error': 'Cannot calculate portfolio returns'}
    portfolio_var = self.risk_analyzer.value_at_risk_analysis(portfolio_returns)
    component_var = self._calculate_component_var(asset_returns, portfolio_weights)
    return {'portfolio_var': portfolio_var, 'component_var': component_var, 'portfolio_statistics': {'mean_return': float(sum(portfolio_returns) / len(portfolio_returns)), 'volatility': float(self.risk_analyzer._calculate_volatility(portfolio_returns)), 'number_of_assets': len(portfolio_weights)}}

def portfolio_stress_testing(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal], stress_scenarios: Dict[str, Dict[str, Decimal]]) -> Dict[str, Any]:
    """
        Comprehensive portfolio stress testing
        CFA Standard: Portfolio stress testing across scenarios
        """
    stress_results = {}
    portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
    baseline_metrics = {'mean_return': float(sum(portfolio_returns) / len(portfolio_returns)), 'volatility': float(self.risk_analyzer._calculate_volatility(portfolio_returns))}
    stress_results['baseline_metrics'] = baseline_metrics
    scenario_impacts = {}
    for scenario_name, scenario_shocks in stress_scenarios.items():
        scenario_impact = self._apply_portfolio_stress_scenario(asset_returns, portfolio_weights, scenario_shocks)
        scenario_impacts[scenario_name] = scenario_impact
    stress_results['scenario_impacts'] = scenario_impacts
    worst_case = self._identify_worst_case_scenario(scenario_impacts)
    stress_results['worst_case_scenario'] = worst_case
    return stress_results

def liquidity_risk_portfolio(self, asset_liquidity_scores: Dict[str, float], portfolio_weights: Dict[str, Decimal]) -> Dict[str, Any]:
    """
        Analyze portfolio-level liquidity risk
        CFA Standard: Portfolio liquidity management
        """
    liquidity_analysis = {}
    weighted_liquidity = Decimal('0')
    for asset, weight in portfolio_weights.items():
        if asset in asset_liquidity_scores:
            liquidity_score = Decimal(str(asset_liquidity_scores[asset]))
            weighted_liquidity += weight * liquidity_score
    liquidity_analysis['weighted_average_liquidity'] = float(weighted_liquidity)
    liquidity_buckets = {'high': Decimal('0'), 'medium': Decimal('0'), 'low': Decimal('0')}
    for asset, weight in portfolio_weights.items():
        if asset in asset_liquidity_scores:
            score = asset_liquidity_scores[asset]
            if score >= 70:
                liquidity_buckets['high'] += weight
            elif score >= 40:
                liquidity_buckets['medium'] += weight
            else:
                liquidity_buckets['low'] += weight
    liquidity_analysis['liquidity_buckets'] = {k: float(v) for k, v in liquidity_buckets.items()}
    if weighted_liquidity >= 70:
        risk_level = 'Low'
    elif weighted_liquidity >= 50:
        risk_level = 'Medium'
    else:
        risk_level = 'High'
    liquidity_analysis['portfolio_liquidity_risk'] = risk_level
    return liquidity_analysis

def _calculate_component_var(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal]) -> Dict[str, Any]:
    """Calculate component VaR for each asset"""
    component_vars = {}
    portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
    if not portfolio_returns:
        return component_vars
    portfolio_var_95 = self.risk_analyzer.math.var_historical(portfolio_returns, Decimal('0.05'))
    for asset, weight in portfolio_weights.items():
        if asset in asset_returns:
            asset_return_series = asset_returns[asset][:len(portfolio_returns)]
            if asset_return_series:
                correlation = self.risk_analyzer._calculate_correlation(asset_return_series, portfolio_returns)
                asset_vol = self.risk_analyzer._calculate_volatility(asset_return_series)
                portfolio_vol = self.risk_analyzer._calculate_volatility(portfolio_returns)
                if portfolio_vol > 0:
                    component_var = weight * correlation * (asset_vol / portfolio_vol) * portfolio_var_95
                    component_vars[asset] = float(component_var)
    return component_vars

def _apply_portfolio_stress_scenario(self, asset_returns: Dict[str, List[Decimal]], portfolio_weights: Dict[str, Decimal], scenario_shocks: Dict[str, Decimal]) -> Dict[str, Any]:
    """Apply stress scenario to portfolio"""
    scenario_impact = {}
    portfolio_returns = self._calculate_portfolio_returns(asset_returns, portfolio_weights)
    baseline_return = sum(portfolio_returns) / len(portfolio_returns) if portfolio_returns else Decimal('0')
    stressed_return = Decimal('0')
    for asset, weight in portfolio_weights.items():
        asset_shock = scenario_shocks.get(asset, Decimal('0'))
        if asset in asset_returns and asset_returns[asset]:
            asset_baseline = sum(asset_returns[asset]) / len(asset_returns[asset])
            stressed_asset_return = asset_baseline + asset_shock
        else:
            stressed_asset_return = asset_shock
        stressed_return += weight * stressed_asset_return
    impact = stressed_return - baseline_return
    scenario_impact['baseline_return'] = float(baseline_return)
    scenario_impact['stressed_return'] = float(stressed_return)
    scenario_impact['impact'] = float(impact)
    scenario_impact['impact_percentage'] = float(impact / baseline_return * 100) if baseline_return != 0 else 0
    return scenario_impact

class CommodityAnalyzer(AlternativeInvestmentBase):
    """
    Commodity investment analysis and derivatives
    CFA Standards: Contango/backwardation, roll yield, futures pricing
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.commodity_sector = getattr(parameters, 'commodity_sector', CommoditySector.ENERGY)
        self.spot_price = getattr(parameters, 'spot_price', None)
        self.futures_prices = getattr(parameters, 'futures_prices', {})
        self.storage_cost = getattr(parameters, 'storage_cost', Constants.COMMODITY_STORAGE_COST_TYPICAL)
        self.convenience_yield = getattr(parameters, 'convenience_yield', Decimal('0'))
        self.contract_size = getattr(parameters, 'contract_size', Decimal('1'))

    def calculate_futures_basis(self, futures_price: Decimal, expiry_months: int) -> Dict[str, Decimal]:
        """
        Calculate futures basis and determine market structure
        CFA Standard: Basis = Futures Price - Spot Price
        """
        if not self.spot_price:
            return {'error': 'Spot price required'}
        basis = futures_price - self.spot_price
        basis_percentage = basis / self.spot_price
        if basis > 0:
            market_structure = 'contango'
        elif basis < 0:
            market_structure = 'backwardation'
        else:
            market_structure = 'neutral'
        years_to_expiry = Decimal(str(expiry_months)) / Constants.MONTHS_IN_YEAR
        annualized_basis = basis_percentage / years_to_expiry if years_to_expiry > 0 else Decimal('0')
        return {'basis': basis, 'basis_percentage': basis_percentage, 'annualized_basis': annualized_basis, 'market_structure': market_structure, 'years_to_expiry': years_to_expiry}

    def theoretical_futures_price(self, time_to_expiry_years: Decimal, risk_free_rate: Decimal=None) -> Decimal:
        """
        Calculate theoretical futures price
        CFA Standard: F = S * e^((r + storage - convenience) * T)
        """
        if not self.spot_price:
            return Decimal('0')
        if risk_free_rate is None:
            risk_free_rate = Config.RISK_FREE_RATE
        cost_of_carry = risk_free_rate + self.storage_cost - self.convenience_yield
        theoretical_price = self.spot_price * (Decimal('1') + cost_of_carry * time_to_expiry_years)
        return theoretical_price

    def roll_yield_analysis(self, front_month_price: Decimal, next_month_price: Decimal, days_to_roll: int) -> Dict[str, Decimal]:
        """
        Calculate roll yield for commodity futures
        CFA Standard: Roll yield from rolling futures positions
        """
        if days_to_roll <= 0:
            return {'error': 'Invalid roll period'}
        price_difference = next_month_price - front_month_price
        roll_yield = price_difference / front_month_price
        days_in_year = float(Constants.DAYS_IN_YEAR)
        annualized_roll_yield = roll_yield * (Decimal(str(days_in_year)) / Decimal(str(days_to_roll)))
        return {'roll_yield': roll_yield, 'annualized_roll_yield': annualized_roll_yield, 'price_difference': price_difference, 'days_to_roll': days_to_roll}

    def commodity_total_return(self, spot_returns: List[Decimal], roll_yields: List[Decimal], collateral_returns: List[Decimal]) -> Dict[str, Decimal]:
        """
        Calculate total return components for commodity investment
        CFA Standard: Total Return = Spot Return + Roll Yield + Collateral Return
        """
        if not all([spot_returns, roll_yields, collateral_returns]):
            return {'error': 'All return components required'}
        if not len(spot_returns) == len(roll_yields) == len(collateral_returns):
            return {'error': 'Return series must have equal length'}
        total_returns = []
        spot_component = Decimal('0')
        roll_component = Decimal('0')
        collateral_component = Decimal('0')
        for spot, roll, collateral in zip(spot_returns, roll_yields, collateral_returns):
            total_return = spot + roll + collateral
            total_returns.append(total_return)
            spot_component += spot
            roll_component += roll
            collateral_component += collateral
        periods = len(spot_returns)
        return {'total_return': sum(total_returns), 'average_total_return': sum(total_returns) / periods, 'spot_contribution': spot_component / periods, 'roll_contribution': roll_component / periods, 'collateral_contribution': collateral_component / periods, 'periods': periods}

    def volatility_analysis(self, price_history: List[Decimal]) -> Dict[str, Decimal]:
        """Analyze commodity price volatility"""
        if len(price_history) < 2:
            return {'error': 'Insufficient price history'}
        returns = []
        for i in range(1, len(price_history)):
            ret = (price_history[i] - price_history[i - 1]) / price_history[i - 1]
            returns.append(ret)
        mean_return = sum(returns) / len(returns)
        variance = sum(((r - mean_return) ** 2 for r in returns)) / (len(returns) - 1)
        volatility = variance.sqrt()
        annualized_vol = volatility * Constants.BUSINESS_DAYS_IN_YEAR.sqrt()
        return {'daily_volatility': volatility, 'annualized_volatility': annualized_vol, 'mean_daily_return': mean_return, 'number_of_observations': len(returns)}

    def calculate_nav(self) -> Decimal:
        """Calculate commodity position NAV"""
        if self.spot_price:
            return self.spot_price * self.contract_size
        latest_price = self.get_latest_price()
        if latest_price:
            return latest_price * self.contract_size
        return Decimal('0')

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key commodity metrics"""
        metrics = {}
        if self.spot_price:
            metrics['spot_price'] = float(self.spot_price)
        if self.futures_prices:
            sorted_futures = sorted(self.futures_prices.items())
            metrics['futures_curve'] = {str(exp): float(price) for exp, price in sorted_futures}
            if len(sorted_futures) >= 2:
                front_exp, front_price = sorted_futures[0]
                next_exp, next_price = sorted_futures[1]
                basis_analysis = self.calculate_futures_basis(front_price, 1)
                metrics.update(basis_analysis)
                roll_analysis = self.roll_yield_analysis(front_price, next_price, 30)
                if 'error' not in roll_analysis:
                    metrics.update(roll_analysis)
        prices = [md.price for md in self.market_data]
        if prices:
            vol_analysis = self.volatility_analysis(prices)
            if 'error' not in vol_analysis:
                metrics.update(vol_analysis)
        metrics['commodity_sector'] = self.commodity_sector.value
        metrics['storage_cost'] = float(self.storage_cost)
        metrics['convenience_yield'] = float(self.convenience_yield)
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive commodity valuation summary"""
        return {'commodity_overview': {'sector': self.commodity_sector.value, 'spot_price': float(self.spot_price) if self.spot_price else None, 'contract_size': float(self.contract_size), 'storage_cost': float(self.storage_cost), 'convenience_yield': float(self.convenience_yield)}, 'market_analysis': self.calculate_key_metrics(), 'futures_curve': self.futures_prices}

def calculate_futures_basis(self, futures_price: Decimal, expiry_months: int) -> Dict[str, Decimal]:
    """
        Calculate futures basis and determine market structure
        CFA Standard: Basis = Futures Price - Spot Price
        """
    if not self.spot_price:
        return {'error': 'Spot price required'}
    basis = futures_price - self.spot_price
    basis_percentage = basis / self.spot_price
    if basis > 0:
        market_structure = 'contango'
    elif basis < 0:
        market_structure = 'backwardation'
    else:
        market_structure = 'neutral'
    years_to_expiry = Decimal(str(expiry_months)) / Constants.MONTHS_IN_YEAR
    annualized_basis = basis_percentage / years_to_expiry if years_to_expiry > 0 else Decimal('0')
    return {'basis': basis, 'basis_percentage': basis_percentage, 'annualized_basis': annualized_basis, 'market_structure': market_structure, 'years_to_expiry': years_to_expiry}

def theoretical_futures_price(self, time_to_expiry_years: Decimal, risk_free_rate: Decimal=None) -> Decimal:
    """
        Calculate theoretical futures price
        CFA Standard: F = S * e^((r + storage - convenience) * T)
        """
    if not self.spot_price:
        return Decimal('0')
    if risk_free_rate is None:
        risk_free_rate = Config.RISK_FREE_RATE
    cost_of_carry = risk_free_rate + self.storage_cost - self.convenience_yield
    theoretical_price = self.spot_price * (Decimal('1') + cost_of_carry * time_to_expiry_years)
    return theoretical_price

def roll_yield_analysis(self, front_month_price: Decimal, next_month_price: Decimal, days_to_roll: int) -> Dict[str, Decimal]:
    """
        Calculate roll yield for commodity futures
        CFA Standard: Roll yield from rolling futures positions
        """
    if days_to_roll <= 0:
        return {'error': 'Invalid roll period'}
    price_difference = next_month_price - front_month_price
    roll_yield = price_difference / front_month_price
    days_in_year = float(Constants.DAYS_IN_YEAR)
    annualized_roll_yield = roll_yield * (Decimal(str(days_in_year)) / Decimal(str(days_to_roll)))
    return {'roll_yield': roll_yield, 'annualized_roll_yield': annualized_roll_yield, 'price_difference': price_difference, 'days_to_roll': days_to_roll}

def calculate_nav(self) -> Decimal:
    """Calculate commodity position NAV"""
    if self.spot_price:
        return self.spot_price * self.contract_size
    latest_price = self.get_latest_price()
    if latest_price:
        return latest_price * self.contract_size
    return Decimal('0')

def calculate_key_metrics(self) -> Dict[str, Any]:
    """Calculate key commodity metrics"""
    metrics = {}
    if self.spot_price:
        metrics['spot_price'] = float(self.spot_price)
    if self.futures_prices:
        sorted_futures = sorted(self.futures_prices.items())
        metrics['futures_curve'] = {str(exp): float(price) for exp, price in sorted_futures}
        if len(sorted_futures) >= 2:
            front_exp, front_price = sorted_futures[0]
            next_exp, next_price = sorted_futures[1]
            basis_analysis = self.calculate_futures_basis(front_price, 1)
            metrics.update(basis_analysis)
            roll_analysis = self.roll_yield_analysis(front_price, next_price, 30)
            if 'error' not in roll_analysis:
                metrics.update(roll_analysis)
    prices = [md.price for md in self.market_data]
    if prices:
        vol_analysis = self.volatility_analysis(prices)
        if 'error' not in vol_analysis:
            metrics.update(vol_analysis)
    metrics['commodity_sector'] = self.commodity_sector.value
    metrics['storage_cost'] = float(self.storage_cost)
    metrics['convenience_yield'] = float(self.convenience_yield)
    return metrics

def valuation_summary(self) -> Dict[str, Any]:
    """Comprehensive commodity valuation summary"""
    return {'commodity_overview': {'sector': self.commodity_sector.value, 'spot_price': float(self.spot_price) if self.spot_price else None, 'contract_size': float(self.contract_size), 'storage_cost': float(self.storage_cost), 'convenience_yield': float(self.convenience_yield)}, 'market_analysis': self.calculate_key_metrics(), 'futures_curve': self.futures_prices}

class LandInvestmentAnalyzer(AlternativeInvestmentBase):
    """
    Land investment analysis - Timberland, Farmland, Raw Land
    CFA Standards: Natural resource valuation methods
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.land_type = getattr(parameters, 'land_type', 'timberland')
        self.acres = getattr(parameters, 'acres', None)
        self.acquisition_price_per_acre = getattr(parameters, 'acquisition_price_per_acre', None)
        self.annual_revenue_per_acre = getattr(parameters, 'annual_revenue_per_acre', None)
        self.operating_expenses_per_acre = getattr(parameters, 'operating_expenses_per_acre', None)
        self.appreciation_rate = getattr(parameters, 'appreciation_rate', Decimal('0.03'))
        self.timber_volume = getattr(parameters, 'timber_volume', None)
        self.growth_rate = getattr(parameters, 'growth_rate', Decimal('0.04'))
        self.harvest_cycle = getattr(parameters, 'harvest_cycle', 25)
        self.crop_yield = getattr(parameters, 'crop_yield', None)
        self.commodity_price = getattr(parameters, 'commodity_price', None)

    def timberland_valuation(self) -> Dict[str, Decimal]:
        """
        Timberland valuation using biological asset model
        CFA Standard: DCF with biological growth consideration
        """
        if self.land_type != 'timberland' or not all([self.timber_volume, self.acres]):
            return {'error': 'Timberland parameters required'}
        discount_rate = Config.RISK_FREE_RATE + Decimal('0.04')
        land_value = Decimal('0')
        if self.acquisition_price_per_acre:
            land_value = self.acquisition_price_per_acre * self.acres
        current_timber_value = self.timber_volume * self.acres
        total_timber_value = Decimal('0')
        years_to_project = 50
        for cycle in range(1, years_to_project // self.harvest_cycle + 1):
            harvest_year = cycle * self.harvest_cycle
            harvest_volume = current_timber_value * (Decimal('1') + self.growth_rate) ** harvest_year
            timber_price_per_unit = Decimal('100')
            harvest_revenue = harvest_volume * timber_price_per_unit
            pv_harvest = harvest_revenue / (Decimal('1') + discount_rate) ** harvest_year
            total_timber_value += pv_harvest
        annual_income = (self.annual_revenue_per_acre or Decimal('0')) * self.acres
        annual_expenses = (self.operating_expenses_per_acre or Decimal('0')) * self.acres
        net_annual_income = annual_income - annual_expenses
        if net_annual_income > 0:
            pv_annual_income = net_annual_income / discount_rate
        else:
            pv_annual_income = Decimal('0')
        total_value = land_value + total_timber_value + pv_annual_income
        return {'total_timberland_value': total_value, 'land_value': land_value, 'timber_value': total_timber_value, 'annual_income_value': pv_annual_income, 'value_per_acre': total_value / self.acres if self.acres > 0 else Decimal('0')}

    def farmland_valuation(self) -> Dict[str, Decimal]:
        """
        Farmland valuation based on productive capacity
        CFA Standard: Income approach for agricultural land
        """
        if self.land_type != 'farmland' or not self.acres:
            return {'error': 'Farmland parameters required'}
        annual_gross_income = Decimal('0')
        if self.crop_yield and self.commodity_price:
            annual_gross_income = self.crop_yield * self.commodity_price * self.acres
        elif self.annual_revenue_per_acre:
            annual_gross_income = self.annual_revenue_per_acre * self.acres
        annual_expenses = (self.operating_expenses_per_acre or Decimal('0')) * self.acres
        net_operating_income = annual_gross_income - annual_expenses
        cap_rate = Decimal('0.05')
        income_value = net_operating_income / cap_rate if cap_rate > 0 else Decimal('0')
        market_value = Decimal('0')
        if self.acquisition_price_per_acre:
            years_held = 1
            appreciated_price = self.acquisition_price_per_acre * (Decimal('1') + self.appreciation_rate) ** years_held
            market_value = appreciated_price * self.acres
        farmland_value = max(income_value, market_value)
        return {'farmland_value': farmland_value, 'income_value': income_value, 'market_value': market_value, 'annual_noi': net_operating_income, 'value_per_acre': farmland_value / self.acres if self.acres > 0 else Decimal('0'), 'cap_rate': cap_rate}

    def raw_land_valuation(self) -> Dict[str, Decimal]:
        """
        Raw land valuation for development potential
        """
        if self.land_type != 'raw_land' or not self.acres:
            return {'error': 'Raw land parameters required'}
        current_value_per_acre = self.acquisition_price_per_acre or Decimal('1000')
        projection_years = 10
        future_value_per_acre = current_value_per_acre * (Decimal('1') + self.appreciation_rate) ** projection_years
        discount_rate = Config.RISK_FREE_RATE + Decimal('0.06')
        present_value_per_acre = future_value_per_acre / (Decimal('1') + discount_rate) ** projection_years
        total_value = present_value_per_acre * self.acres
        return {'raw_land_value': total_value, 'current_value_per_acre': current_value_per_acre, 'projected_value_per_acre': future_value_per_acre, 'present_value_per_acre': present_value_per_acre, 'total_acres': self.acres}

    def calculate_nav(self) -> Decimal:
        """Calculate land investment NAV"""
        if self.land_type == 'timberland':
            valuation = self.timberland_valuation()
            return valuation.get('total_timberland_value', Decimal('0'))
        elif self.land_type == 'farmland':
            valuation = self.farmland_valuation()
            return valuation.get('farmland_value', Decimal('0'))
        elif self.land_type == 'raw_land':
            valuation = self.raw_land_valuation()
            return valuation.get('raw_land_value', Decimal('0'))
        return Decimal('0')

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key land investment metrics"""
        metrics = {'land_type': self.land_type, 'total_acres': float(self.acres) if self.acres else None, 'appreciation_rate': float(self.appreciation_rate)}
        if self.land_type == 'timberland':
            valuation = self.timberland_valuation()
        elif self.land_type == 'farmland':
            valuation = self.farmland_valuation()
        elif self.land_type == 'raw_land':
            valuation = self.raw_land_valuation()
        else:
            valuation = {}
        for key, value in valuation.items():
            if isinstance(value, Decimal):
                metrics[key] = float(value)
            else:
                metrics[key] = value
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive land investment summary"""
        return {'land_overview': {'land_type': self.land_type, 'total_acres': float(self.acres) if self.acres else None, 'acquisition_price_per_acre': float(self.acquisition_price_per_acre) if self.acquisition_price_per_acre else None}, 'valuation_analysis': self.calculate_key_metrics()}

def farmland_valuation(self) -> Dict[str, Decimal]:
    """
        Farmland valuation based on productive capacity
        CFA Standard: Income approach for agricultural land
        """
    if self.land_type != 'farmland' or not self.acres:
        return {'error': 'Farmland parameters required'}
    annual_gross_income = Decimal('0')
    if self.crop_yield and self.commodity_price:
        annual_gross_income = self.crop_yield * self.commodity_price * self.acres
    elif self.annual_revenue_per_acre:
        annual_gross_income = self.annual_revenue_per_acre * self.acres
    annual_expenses = (self.operating_expenses_per_acre or Decimal('0')) * self.acres
    net_operating_income = annual_gross_income - annual_expenses
    cap_rate = Decimal('0.05')
    income_value = net_operating_income / cap_rate if cap_rate > 0 else Decimal('0')
    market_value = Decimal('0')
    if self.acquisition_price_per_acre:
        years_held = 1
        appreciated_price = self.acquisition_price_per_acre * (Decimal('1') + self.appreciation_rate) ** years_held
        market_value = appreciated_price * self.acres
    farmland_value = max(income_value, market_value)
    return {'farmland_value': farmland_value, 'income_value': income_value, 'market_value': market_value, 'annual_noi': net_operating_income, 'value_per_acre': farmland_value / self.acres if self.acres > 0 else Decimal('0'), 'cap_rate': cap_rate}

def raw_land_valuation(self) -> Dict[str, Decimal]:
    """
        Raw land valuation for development potential
        """
    if self.land_type != 'raw_land' or not self.acres:
        return {'error': 'Raw land parameters required'}
    current_value_per_acre = self.acquisition_price_per_acre or Decimal('1000')
    projection_years = 10
    future_value_per_acre = current_value_per_acre * (Decimal('1') + self.appreciation_rate) ** projection_years
    discount_rate = Config.RISK_FREE_RATE + Decimal('0.06')
    present_value_per_acre = future_value_per_acre / (Decimal('1') + discount_rate) ** projection_years
    total_value = present_value_per_acre * self.acres
    return {'raw_land_value': total_value, 'current_value_per_acre': current_value_per_acre, 'projected_value_per_acre': future_value_per_acre, 'present_value_per_acre': present_value_per_acre, 'total_acres': self.acres}

def valuation_summary(self) -> Dict[str, Any]:
    """Comprehensive land investment summary"""
    return {'land_overview': {'land_type': self.land_type, 'total_acres': float(self.acres) if self.acres else None, 'acquisition_price_per_acre': float(self.acquisition_price_per_acre) if self.acquisition_price_per_acre else None}, 'valuation_analysis': self.calculate_key_metrics()}

class EnergyInvestmentAnalyzer(AlternativeInvestmentBase):
    """
    Energy investment analysis - Oil & Gas, Renewables
    CFA Standards: Energy project finance and valuation
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.energy_type = getattr(parameters, 'energy_type', 'oil_gas')
        self.proved_reserves = getattr(parameters, 'proved_reserves', None)
        self.daily_production = getattr(parameters, 'daily_production', None)
        self.decline_rate = getattr(parameters, 'decline_rate', Decimal('0.15'))
        self.operating_cost_per_unit = getattr(parameters, 'operating_cost_per_unit', None)
        self.commodity_price = getattr(parameters, 'commodity_price', None)
        self.capacity_factor = getattr(parameters, 'capacity_factor', Decimal('0.35'))
        self.power_purchase_agreement = getattr(parameters, 'ppa_price', None)
        self.asset_life = getattr(parameters, 'asset_life', 25)

    def oil_gas_valuation(self) -> Dict[str, Decimal]:
        """
        Oil & Gas asset valuation using decline curve analysis
        CFA Standard: DCF with production decline
        """
        if self.energy_type != 'oil_gas':
            return {'error': 'Oil & Gas parameters required'}
        if not all([self.daily_production, self.commodity_price]):
            return {'error': 'Production and price data required'}
        discount_rate = Config.RISK_FREE_RATE + Decimal('0.08')
        projection_years = 20
        total_pv = Decimal('0')
        daily_prod = self.daily_production
        opex_per_unit = self.operating_cost_per_unit or Decimal('0')
        for year in range(1, projection_years + 1):
            annual_production = daily_prod * Constants.DAYS_IN_YEAR
            annual_revenue = annual_production * self.commodity_price
            annual_opex = annual_production * opex_per_unit
            annual_cash_flow = annual_revenue - annual_opex
            pv = annual_cash_flow / (Decimal('1') + discount_rate) ** year
            total_pv += pv
            daily_prod *= Decimal('1') - self.decline_rate
        return {'oil_gas_value': total_pv, 'initial_daily_production': self.daily_production, 'commodity_price': self.commodity_price, 'decline_rate': self.decline_rate, 'projection_years': projection_years}

    def renewable_energy_valuation(self) -> Dict[str, Decimal]:
        """
        Renewable energy project valuation
        CFA Standard: Project finance DCF
        """
        if self.energy_type != 'renewable':
            return {'error': 'Renewable energy parameters required'}
        if not all([self.proved_reserves, self.capacity_factor]):
            return {'error': 'Capacity and capacity factor required'}
        discount_rate = Config.RISK_FREE_RATE + Decimal('0.05')
        capacity_mw = self.proved_reserves
        hours_per_year = Decimal('8760')
        annual_mwh = capacity_mw * hours_per_year * self.capacity_factor
        ppa_price = self.power_purchase_agreement or Decimal('50')
        annual_revenue = annual_mwh * ppa_price
        annual_opex = capacity_mw * Decimal('25000')
        annual_cash_flow = annual_revenue - annual_opex
        total_pv = Decimal('0')
        for year in range(1, self.asset_life + 1):
            pv = annual_cash_flow / (Decimal('1') + discount_rate) ** year
            total_pv += pv
        return {'renewable_value': total_pv, 'capacity_mw': capacity_mw, 'annual_mwh': annual_mwh, 'annual_revenue': annual_revenue, 'annual_cash_flow': annual_cash_flow, 'asset_life': self.asset_life}

    def calculate_nav(self) -> Decimal:
        """Calculate energy investment NAV"""
        if self.energy_type == 'oil_gas':
            valuation = self.oil_gas_valuation()
            return valuation.get('oil_gas_value', Decimal('0'))
        elif self.energy_type == 'renewable':
            valuation = self.renewable_energy_valuation()
            return valuation.get('renewable_value', Decimal('0'))
        return Decimal('0')

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key energy investment metrics"""
        metrics = {'energy_type': self.energy_type}
        if self.energy_type == 'oil_gas':
            valuation = self.oil_gas_valuation()
            metrics.update({k: float(v) if isinstance(v, Decimal) else v for k, v in valuation.items()})
        elif self.energy_type == 'renewable':
            valuation = self.renewable_energy_valuation()
            metrics.update({k: float(v) if isinstance(v, Decimal) else v for k, v in valuation.items()})
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive energy investment summary"""
        return {'energy_overview': {'energy_type': self.energy_type, 'proved_reserves': float(self.proved_reserves) if self.proved_reserves else None, 'daily_production': float(self.daily_production) if self.daily_production else None}, 'valuation_analysis': self.calculate_key_metrics()}

def valuation_summary(self) -> Dict[str, Any]:
    """Comprehensive energy investment summary"""
    return {'energy_overview': {'energy_type': self.energy_type, 'proved_reserves': float(self.proved_reserves) if self.proved_reserves else None, 'daily_production': float(self.daily_production) if self.daily_production else None}, 'valuation_analysis': self.calculate_key_metrics()}

class RealEstateAnalyzer(AlternativeInvestmentBase):
    """
    Real Estate investment analysis and valuation
    CFA Standards: DCF, Direct Capitalization, Sales Comparison approaches
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.property_type = getattr(parameters, 'property_type', RealEstateType.OFFICE)
        self.acquisition_price = getattr(parameters, 'acquisition_price', None)
        self.current_market_value = getattr(parameters, 'current_market_value', None)
        self.gross_rental_income = getattr(parameters, 'gross_rental_income', None)
        self.operating_expenses = getattr(parameters, 'operating_expenses', None)
        self.vacancy_rate = getattr(parameters, 'vacancy_rate', Decimal('0.05'))
        self.cap_rate = getattr(parameters, 'cap_rate', None)

    def calculate_noi(self) -> Decimal:
        """
        Calculate Net Operating Income
        CFA Standard: NOI = Gross Rental Income - Operating Expenses - Vacancy Loss
        """
        if not self.gross_rental_income:
            return Decimal('0')
        effective_gross_income = self.gross_rental_income * (Decimal('1') - self.vacancy_rate)
        operating_expenses = self.operating_expenses or Decimal('0')
        noi = effective_gross_income - operating_expenses
        return max(noi, Decimal('0'))

    def calculate_cap_rate(self, market_value: Decimal=None) -> Optional[Decimal]:
        """
        Calculate Capitalization Rate
        CFA Standard: Cap Rate = NOI / Property Value
        """
        noi = self.calculate_noi()
        value = market_value or self.current_market_value or self.acquisition_price
        if not value or value == 0 or noi <= 0:
            return None
        cap_rate = noi / value
        if self.config.RE_CAP_RATE_MIN <= cap_rate <= self.config.RE_CAP_RATE_MAX:
            return cap_rate
        logger.warning(f'Calculated cap rate {cap_rate} outside normal range')
        return cap_rate

    def direct_capitalization_value(self, market_cap_rate: Decimal) -> Decimal:
        """
        Direct Capitalization valuation approach
        CFA Standard: Property Value = NOI / Cap Rate
        """
        noi = self.calculate_noi()
        if market_cap_rate <= 0:
            raise ValueError('Cap rate must be positive')
        return noi / market_cap_rate

    def dcf_valuation(self, projection_years: int=10, terminal_cap_rate: Decimal=None, discount_rate: Decimal=None) -> Dict[str, Decimal]:
        """
        Discounted Cash Flow valuation
        CFA Standard: DCF approach for income-producing real estate
        """
        if not self.gross_rental_income:
            return {'error': 'Gross rental income required for DCF'}
        if discount_rate is None:
            discount_rate = self.config.RISK_FREE_RATE + Decimal('0.04')
        if terminal_cap_rate is None:
            terminal_cap_rate = self.calculate_cap_rate() or Decimal('0.06')
        current_noi = self.calculate_noi()
        annual_growth_rate = Decimal('0.03')
        projected_cfs = []
        for year in range(1, projection_years + 1):
            projected_noi = current_noi * (Decimal('1') + annual_growth_rate) ** year
            projected_cfs.append(projected_noi)
        terminal_noi = projected_cfs[-1] * (Decimal('1') + annual_growth_rate)
        terminal_value = terminal_noi / terminal_cap_rate
        pv_cash_flows = Decimal('0')
        for year, cf in enumerate(projected_cfs, 1):
            pv = cf / (Decimal('1') + discount_rate) ** year
            pv_cash_flows += pv
        pv_terminal = terminal_value / (Decimal('1') + discount_rate) ** projection_years
        total_property_value = pv_cash_flows + pv_terminal
        return {'dcf_value': total_property_value, 'pv_cash_flows': pv_cash_flows, 'pv_terminal_value': pv_terminal, 'terminal_value': terminal_value, 'implied_cap_rate': current_noi / total_property_value if total_property_value > 0 else Decimal('0')}

    def calculate_real_estate_ratios(self) -> Dict[str, Decimal]:
        """Calculate key real estate financial ratios"""
        ratios = {}
        noi = self.calculate_noi()
        if self.gross_rental_income and self.operating_expenses:
            effective_gross = self.gross_rental_income * (Decimal('1') - self.vacancy_rate)
            expense_ratio = self.operating_expenses / effective_gross
            ratios['operating_expense_ratio'] = expense_ratio
        if self.gross_rental_income:
            effective_gross = self.gross_rental_income * (Decimal('1') - self.vacancy_rate)
            noi_margin = noi / effective_gross if effective_gross > 0 else Decimal('0')
            ratios['noi_margin'] = noi_margin
        occupancy_rate = Decimal('1') - self.vacancy_rate
        ratios['occupancy_rate'] = occupancy_rate
        return ratios

    def calculate_nav(self) -> Decimal:
        """Calculate current NAV based on market value or DCF"""
        if self.current_market_value:
            return self.current_market_value
        dcf_result = self.dcf_valuation()
        if isinstance(dcf_result, dict) and 'dcf_value' in dcf_result:
            return dcf_result['dcf_value']
        return self.acquisition_price or Decimal('0')

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key real estate metrics"""
        metrics = {}
        noi = self.calculate_noi()
        metrics['noi'] = float(noi)
        cap_rate = self.calculate_cap_rate()
        if cap_rate:
            metrics['cap_rate'] = float(cap_rate)
        ratios = self.calculate_real_estate_ratios()
        for key, value in ratios.items():
            metrics[key] = float(value)
        dcf_result = self.dcf_valuation()
        if isinstance(dcf_result, dict) and 'dcf_value' in dcf_result:
            metrics['dcf_valuation'] = float(dcf_result['dcf_value'])
            metrics['implied_cap_rate'] = float(dcf_result['implied_cap_rate'])
        if self.acquisition_price and self.current_market_value:
            total_return = (self.current_market_value - self.acquisition_price) / self.acquisition_price
            metrics['capital_appreciation'] = float(total_return)
        if self.current_market_value or self.acquisition_price:
            property_value = self.current_market_value or self.acquisition_price
            income_yield = noi / property_value if property_value > 0 else Decimal('0')
            metrics['income_yield'] = float(income_yield)
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive real estate valuation summary"""
        return {'property_overview': {'property_type': self.property_type.value, 'acquisition_price': float(self.acquisition_price) if self.acquisition_price else None, 'current_market_value': float(self.current_market_value) if self.current_market_value else None, 'gross_rental_income': float(self.gross_rental_income) if self.gross_rental_income else None, 'vacancy_rate': float(self.vacancy_rate)}, 'financial_metrics': self.calculate_key_metrics(), 'valuation_approaches': {'direct_cap': float(self.direct_capitalization_value(self.cap_rate)) if self.cap_rate else None, 'dcf': self.dcf_valuation()}}

def calculate_noi(self) -> Decimal:
    """
        Calculate Net Operating Income
        CFA Standard: NOI = Gross Rental Income - Operating Expenses - Vacancy Loss
        """
    if not self.gross_rental_income:
        return Decimal('0')
    effective_gross_income = self.gross_rental_income * (Decimal('1') - self.vacancy_rate)
    operating_expenses = self.operating_expenses or Decimal('0')
    noi = effective_gross_income - operating_expenses
    return max(noi, Decimal('0'))

def calculate_cap_rate(self, market_value: Decimal=None) -> Optional[Decimal]:
    """
        Calculate Capitalization Rate
        CFA Standard: Cap Rate = NOI / Property Value
        """
    noi = self.calculate_noi()
    value = market_value or self.current_market_value or self.acquisition_price
    if not value or value == 0 or noi <= 0:
        return None
    cap_rate = noi / value
    if self.config.RE_CAP_RATE_MIN <= cap_rate <= self.config.RE_CAP_RATE_MAX:
        return cap_rate
    logger.warning(f'Calculated cap rate {cap_rate} outside normal range')
    return cap_rate

def direct_capitalization_value(self, market_cap_rate: Decimal) -> Decimal:
    """
        Direct Capitalization valuation approach
        CFA Standard: Property Value = NOI / Cap Rate
        """
    noi = self.calculate_noi()
    if market_cap_rate <= 0:
        raise ValueError('Cap rate must be positive')
    return noi / market_cap_rate

def dcf_valuation(self, projection_years: int=10, terminal_cap_rate: Decimal=None, discount_rate: Decimal=None) -> Dict[str, Decimal]:
    """
        Discounted Cash Flow valuation
        CFA Standard: DCF approach for income-producing real estate
        """
    if not self.gross_rental_income:
        return {'error': 'Gross rental income required for DCF'}
    if discount_rate is None:
        discount_rate = self.config.RISK_FREE_RATE + Decimal('0.04')
    if terminal_cap_rate is None:
        terminal_cap_rate = self.calculate_cap_rate() or Decimal('0.06')
    current_noi = self.calculate_noi()
    annual_growth_rate = Decimal('0.03')
    projected_cfs = []
    for year in range(1, projection_years + 1):
        projected_noi = current_noi * (Decimal('1') + annual_growth_rate) ** year
        projected_cfs.append(projected_noi)
    terminal_noi = projected_cfs[-1] * (Decimal('1') + annual_growth_rate)
    terminal_value = terminal_noi / terminal_cap_rate
    pv_cash_flows = Decimal('0')
    for year, cf in enumerate(projected_cfs, 1):
        pv = cf / (Decimal('1') + discount_rate) ** year
        pv_cash_flows += pv
    pv_terminal = terminal_value / (Decimal('1') + discount_rate) ** projection_years
    total_property_value = pv_cash_flows + pv_terminal
    return {'dcf_value': total_property_value, 'pv_cash_flows': pv_cash_flows, 'pv_terminal_value': pv_terminal, 'terminal_value': terminal_value, 'implied_cap_rate': current_noi / total_property_value if total_property_value > 0 else Decimal('0')}

def calculate_real_estate_ratios(self) -> Dict[str, Decimal]:
    """Calculate key real estate financial ratios"""
    ratios = {}
    noi = self.calculate_noi()
    if self.gross_rental_income and self.operating_expenses:
        effective_gross = self.gross_rental_income * (Decimal('1') - self.vacancy_rate)
        expense_ratio = self.operating_expenses / effective_gross
        ratios['operating_expense_ratio'] = expense_ratio
    if self.gross_rental_income:
        effective_gross = self.gross_rental_income * (Decimal('1') - self.vacancy_rate)
        noi_margin = noi / effective_gross if effective_gross > 0 else Decimal('0')
        ratios['noi_margin'] = noi_margin
    occupancy_rate = Decimal('1') - self.vacancy_rate
    ratios['occupancy_rate'] = occupancy_rate
    return ratios

def calculate_nav(self) -> Decimal:
    """Calculate current NAV based on market value or DCF"""
    if self.current_market_value:
        return self.current_market_value
    dcf_result = self.dcf_valuation()
    if isinstance(dcf_result, dict) and 'dcf_value' in dcf_result:
        return dcf_result['dcf_value']
    return self.acquisition_price or Decimal('0')

def calculate_key_metrics(self) -> Dict[str, Any]:
    """Calculate key real estate metrics"""
    metrics = {}
    noi = self.calculate_noi()
    metrics['noi'] = float(noi)
    cap_rate = self.calculate_cap_rate()
    if cap_rate:
        metrics['cap_rate'] = float(cap_rate)
    ratios = self.calculate_real_estate_ratios()
    for key, value in ratios.items():
        metrics[key] = float(value)
    dcf_result = self.dcf_valuation()
    if isinstance(dcf_result, dict) and 'dcf_value' in dcf_result:
        metrics['dcf_valuation'] = float(dcf_result['dcf_value'])
        metrics['implied_cap_rate'] = float(dcf_result['implied_cap_rate'])
    if self.acquisition_price and self.current_market_value:
        total_return = (self.current_market_value - self.acquisition_price) / self.acquisition_price
        metrics['capital_appreciation'] = float(total_return)
    if self.current_market_value or self.acquisition_price:
        property_value = self.current_market_value or self.acquisition_price
        income_yield = noi / property_value if property_value > 0 else Decimal('0')
        metrics['income_yield'] = float(income_yield)
    return metrics

def valuation_summary(self) -> Dict[str, Any]:
    """Comprehensive real estate valuation summary"""
    return {'property_overview': {'property_type': self.property_type.value, 'acquisition_price': float(self.acquisition_price) if self.acquisition_price else None, 'current_market_value': float(self.current_market_value) if self.current_market_value else None, 'gross_rental_income': float(self.gross_rental_income) if self.gross_rental_income else None, 'vacancy_rate': float(self.vacancy_rate)}, 'financial_metrics': self.calculate_key_metrics(), 'valuation_approaches': {'direct_cap': float(self.direct_capitalization_value(self.cap_rate)) if self.cap_rate else None, 'dcf': self.dcf_valuation()}}

class REITAnalyzer(AlternativeInvestmentBase):
    """
    Real Estate Investment Trust (REIT) analysis
    CFA Standards: NAV, FFO, AFFO calculations and valuation
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.shares_outstanding = getattr(parameters, 'shares_outstanding', None)
        self.total_assets = getattr(parameters, 'total_assets', None)
        self.total_debt = getattr(parameters, 'total_debt', None)
        self.property_value = getattr(parameters, 'property_value', None)
        self.net_income = getattr(parameters, 'net_income', None)
        self.depreciation = getattr(parameters, 'depreciation', None)
        self.amortization = getattr(parameters, 'amortization', None)
        self.gains_on_sales = getattr(parameters, 'gains_on_sales', Decimal('0'))
        self.recurring_capex = getattr(parameters, 'recurring_capex', None)
        self.leasing_costs = getattr(parameters, 'leasing_costs', None)

    def calculate_ffo(self) -> Optional[Decimal]:
        """
        Calculate Funds From Operations
        CFA Standard: FFO = Net Income + Depreciation + Amortization - Gains on Sales
        """
        if not all([self.net_income, self.depreciation]):
            return None
        ffo = self.net_income + self.depreciation
        if self.amortization:
            ffo += self.amortization
        if self.gains_on_sales:
            ffo -= self.gains_on_sales
        return ffo

    def calculate_affo(self) -> Optional[Decimal]:
        """
        Calculate Adjusted Funds From Operations
        CFA Standard: AFFO = FFO - Recurring Capital Expenditures - Leasing Costs
        """
        ffo = self.calculate_ffo()
        if ffo is None:
            return None
        affo = ffo
        if self.recurring_capex:
            affo -= self.recurring_capex
        if self.leasing_costs:
            affo -= self.leasing_costs
        return affo

    def calculate_nav_per_share(self, property_values: Dict[str, Decimal]=None) -> Optional[Decimal]:
        """
        Calculate Net Asset Value per Share
        CFA Standard: NAVPS = (Total Property Value - Total Debt) / Shares Outstanding
        """
        if not self.shares_outstanding:
            return None
        total_property_value = self.property_value
        if property_values:
            total_property_value = sum(property_values.values())
        if not total_property_value:
            total_property_value = self.total_assets or Decimal('0')
        total_debt = self.total_debt or Decimal('0')
        equity_value = total_property_value - total_debt
        navps = equity_value / self.shares_outstanding
        return navps

    def reit_valuation_ratios(self, current_share_price: Decimal) -> Dict[str, Optional[Decimal]]:
        """Calculate key REIT valuation ratios"""
        ratios = {}
        ffo = self.calculate_ffo()
        if ffo and self.shares_outstanding:
            ffo_per_share = ffo / self.shares_outstanding
            if ffo_per_share > 0:
                ratios['price_to_ffo'] = current_share_price / ffo_per_share
                ratios['ffo_per_share'] = ffo_per_share
        affo = self.calculate_affo()
        if affo and self.shares_outstanding:
            affo_per_share = affo / self.shares_outstanding
            if affo_per_share > 0:
                ratios['price_to_affo'] = current_share_price / affo_per_share
                ratios['affo_per_share'] = affo_per_share
        navps = self.calculate_nav_per_share()
        if navps:
            ratios['price_to_nav'] = current_share_price / navps
            ratios['nav_per_share'] = navps
        if self.total_debt and self.property_value:
            equity_value = self.property_value - self.total_debt
            if equity_value > 0:
                ratios['debt_to_equity'] = self.total_debt / equity_value
        return ratios

    def dividend_analysis(self, annual_dividend: Decimal, current_price: Decimal) -> Dict[str, Decimal]:
        """Analyze REIT dividend metrics"""
        analysis = {}
        dividend_yield = annual_dividend / current_price
        analysis['dividend_yield'] = dividend_yield
        ffo = self.calculate_ffo()
        if ffo and self.shares_outstanding:
            total_dividends = annual_dividend * self.shares_outstanding
            ffo_payout_ratio = total_dividends / ffo
            analysis['ffo_payout_ratio'] = ffo_payout_ratio
        affo = self.calculate_affo()
        if affo and self.shares_outstanding:
            total_dividends = annual_dividend * self.shares_outstanding
            affo_payout_ratio = total_dividends / affo
            analysis['affo_payout_ratio'] = affo_payout_ratio
        return analysis

    def calculate_nav(self) -> Decimal:
        """Calculate REIT NAV"""
        navps = self.calculate_nav_per_share()
        if navps and self.shares_outstanding:
            return navps * self.shares_outstanding
        property_val = self.property_value or self.total_assets or Decimal('0')
        debt = self.total_debt or Decimal('0')
        return property_val - debt

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key REIT metrics"""
        metrics = {}
        ffo = self.calculate_ffo()
        if ffo:
            metrics['ffo'] = float(ffo)
            if self.shares_outstanding:
                metrics['ffo_per_share'] = float(ffo / self.shares_outstanding)
        affo = self.calculate_affo()
        if affo:
            metrics['affo'] = float(affo)
            if self.shares_outstanding:
                metrics['affo_per_share'] = float(affo / self.shares_outstanding)
        navps = self.calculate_nav_per_share()
        if navps:
            metrics['nav_per_share'] = float(navps)
        if self.total_debt and self.total_assets:
            debt_ratio = self.total_debt / self.total_assets
            metrics['debt_to_assets'] = float(debt_ratio)
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive REIT valuation summary"""
        return {'reit_overview': {'shares_outstanding': float(self.shares_outstanding) if self.shares_outstanding else None, 'total_assets': float(self.total_assets) if self.total_assets else None, 'total_debt': float(self.total_debt) if self.total_debt else None, 'property_value': float(self.property_value) if self.property_value else None}, 'operating_metrics': self.calculate_key_metrics(), 'valuation_metrics': {'ffo': float(self.calculate_ffo()) if self.calculate_ffo() else None, 'affo': float(self.calculate_affo()) if self.calculate_affo() else None, 'nav_per_share': float(self.calculate_nav_per_share()) if self.calculate_nav_per_share() else None}}

def calculate_affo(self) -> Optional[Decimal]:
    """
        Calculate Adjusted Funds From Operations
        CFA Standard: AFFO = FFO - Recurring Capital Expenditures - Leasing Costs
        """
    ffo = self.calculate_ffo()
    if ffo is None:
        return None
    affo = ffo
    if self.recurring_capex:
        affo -= self.recurring_capex
    if self.leasing_costs:
        affo -= self.leasing_costs
    return affo

def reit_valuation_ratios(self, current_share_price: Decimal) -> Dict[str, Optional[Decimal]]:
    """Calculate key REIT valuation ratios"""
    ratios = {}
    ffo = self.calculate_ffo()
    if ffo and self.shares_outstanding:
        ffo_per_share = ffo / self.shares_outstanding
        if ffo_per_share > 0:
            ratios['price_to_ffo'] = current_share_price / ffo_per_share
            ratios['ffo_per_share'] = ffo_per_share
    affo = self.calculate_affo()
    if affo and self.shares_outstanding:
        affo_per_share = affo / self.shares_outstanding
        if affo_per_share > 0:
            ratios['price_to_affo'] = current_share_price / affo_per_share
            ratios['affo_per_share'] = affo_per_share
    navps = self.calculate_nav_per_share()
    if navps:
        ratios['price_to_nav'] = current_share_price / navps
        ratios['nav_per_share'] = navps
    if self.total_debt and self.property_value:
        equity_value = self.property_value - self.total_debt
        if equity_value > 0:
            ratios['debt_to_equity'] = self.total_debt / equity_value
    return ratios

def dividend_analysis(self, annual_dividend: Decimal, current_price: Decimal) -> Dict[str, Decimal]:
    """Analyze REIT dividend metrics"""
    analysis = {}
    dividend_yield = annual_dividend / current_price
    analysis['dividend_yield'] = dividend_yield
    ffo = self.calculate_ffo()
    if ffo and self.shares_outstanding:
        total_dividends = annual_dividend * self.shares_outstanding
        ffo_payout_ratio = total_dividends / ffo
        analysis['ffo_payout_ratio'] = ffo_payout_ratio
    affo = self.calculate_affo()
    if affo and self.shares_outstanding:
        total_dividends = annual_dividend * self.shares_outstanding
        affo_payout_ratio = total_dividends / affo
        analysis['affo_payout_ratio'] = affo_payout_ratio
    return analysis

def calculate_nav(self) -> Decimal:
    """Calculate REIT NAV"""
    navps = self.calculate_nav_per_share()
    if navps and self.shares_outstanding:
        return navps * self.shares_outstanding
    property_val = self.property_value or self.total_assets or Decimal('0')
    debt = self.total_debt or Decimal('0')
    return property_val - debt

def calculate_key_metrics(self) -> Dict[str, Any]:
    """Calculate key REIT metrics"""
    metrics = {}
    ffo = self.calculate_ffo()
    if ffo:
        metrics['ffo'] = float(ffo)
        if self.shares_outstanding:
            metrics['ffo_per_share'] = float(ffo / self.shares_outstanding)
    affo = self.calculate_affo()
    if affo:
        metrics['affo'] = float(affo)
        if self.shares_outstanding:
            metrics['affo_per_share'] = float(affo / self.shares_outstanding)
    navps = self.calculate_nav_per_share()
    if navps:
        metrics['nav_per_share'] = float(navps)
    if self.total_debt and self.total_assets:
        debt_ratio = self.total_debt / self.total_assets
        metrics['debt_to_assets'] = float(debt_ratio)
    return metrics

def valuation_summary(self) -> Dict[str, Any]:
    """Comprehensive REIT valuation summary"""
    return {'reit_overview': {'shares_outstanding': float(self.shares_outstanding) if self.shares_outstanding else None, 'total_assets': float(self.total_assets) if self.total_assets else None, 'total_debt': float(self.total_debt) if self.total_debt else None, 'property_value': float(self.property_value) if self.property_value else None}, 'operating_metrics': self.calculate_key_metrics(), 'valuation_metrics': {'ffo': float(self.calculate_ffo()) if self.calculate_ffo() else None, 'affo': float(self.calculate_affo()) if self.calculate_affo() else None, 'nav_per_share': float(self.calculate_nav_per_share()) if self.calculate_nav_per_share() else None}}

class InfrastructureAnalyzer(AlternativeInvestmentBase):
    """
    Infrastructure investment analysis
    CFA Standards: Project finance, regulated utility analysis
    """

    def __init__(self, parameters: AssetParameters):
        super().__init__(parameters)
        self.infrastructure_type = getattr(parameters, 'infrastructure_type', 'transportation')
        self.regulatory_framework = getattr(parameters, 'regulatory_framework', 'regulated')
        self.concession_period = getattr(parameters, 'concession_period', None)
        self.revenue_model = getattr(parameters, 'revenue_model', 'user_pays')
        self.annual_revenue = getattr(parameters, 'annual_revenue', None)
        self.operating_costs = getattr(parameters, 'operating_costs', None)
        self.maintenance_capex = getattr(parameters, 'maintenance_capex', None)
        self.inflation_indexation = getattr(parameters, 'inflation_indexation', True)

    def project_cash_flows(self, projection_years: int=None) -> List[Dict[str, Decimal]]:
        """
        Project infrastructure cash flows
        CFA Standard: DCF for infrastructure projects
        """
        if projection_years is None:
            projection_years = self.concession_period or 25
        if not self.annual_revenue:
            return []
        cash_flows = []
        inflation_rate = Decimal('0.025')
        for year in range(1, projection_years + 1):
            if self.inflation_indexation:
                revenue = self.annual_revenue * (Decimal('1') + inflation_rate) ** (year - 1)
                opex = (self.operating_costs or Decimal('0')) * (Decimal('1') + inflation_rate) ** (year - 1)
                maintenance = (self.maintenance_capex or Decimal('0')) * (Decimal('1') + inflation_rate) ** (year - 1)
            else:
                revenue = self.annual_revenue
                opex = self.operating_costs or Decimal('0')
                maintenance = self.maintenance_capex or Decimal('0')
            ebitda = revenue - opex
            free_cash_flow = ebitda - maintenance
            cash_flows.append({'year': year, 'revenue': revenue, 'operating_costs': opex, 'maintenance_capex': maintenance, 'ebitda': ebitda, 'free_cash_flow': free_cash_flow})
        return cash_flows

    def infrastructure_valuation(self, discount_rate: Decimal=None) -> Dict[str, Decimal]:
        """
        Value infrastructure investment using DCF
        """
        if discount_rate is None:
            discount_rate = self.config.RISK_FREE_RATE + Decimal('0.03')
        projected_cfs = self.project_cash_flows()
        if not projected_cfs:
            return {'error': 'Cannot project cash flows'}
        present_value = Decimal('0')
        for cf in projected_cfs:
            year = cf['year']
            fcf = cf['free_cash_flow']
            pv = fcf / (Decimal('1') + discount_rate) ** year
            present_value += pv
        return {'enterprise_value': present_value, 'discount_rate': discount_rate, 'projection_years': len(projected_cfs), 'terminal_year_fcf': projected_cfs[-1]['free_cash_flow'] if projected_cfs else Decimal('0')}

    def regulatory_risk_assessment(self) -> Dict[str, Any]:
        """Assess regulatory risk factors"""
        risk_factors = {'regulatory_framework': self.regulatory_framework, 'concession_period': self.concession_period, 'revenue_model': self.revenue_model, 'inflation_protection': self.inflation_indexation}
        risk_score = 0
        if self.regulatory_framework == 'regulated':
            risk_score += 1
        elif self.regulatory_framework == 'merchant':
            risk_score += 3
        if self.revenue_model == 'availability':
            risk_score += 1
        elif self.revenue_model == 'user_pays':
            risk_score += 2
        if not self.inflation_indexation:
            risk_score += 1
        risk_factors['risk_score'] = risk_score
        risk_factors['risk_level'] = 'Low' if risk_score <= 3 else 'Medium' if risk_score <= 5 else 'High'
        return risk_factors

    def calculate_nav(self) -> Decimal:
        """Calculate infrastructure NAV using DCF"""
        valuation = self.infrastructure_valuation()
        if isinstance(valuation, dict) and 'enterprise_value' in valuation:
            return valuation['enterprise_value']
        return Decimal('0')

    def calculate_key_metrics(self) -> Dict[str, Any]:
        """Calculate key infrastructure metrics"""
        metrics = {}
        valuation = self.infrastructure_valuation()
        if isinstance(valuation, dict):
            for key, value in valuation.items():
                if isinstance(value, Decimal):
                    metrics[key] = float(value)
                else:
                    metrics[key] = value
        if self.annual_revenue and self.operating_costs:
            ebitda_margin = (self.annual_revenue - self.operating_costs) / self.annual_revenue
            metrics['ebitda_margin'] = float(ebitda_margin)
        risk_assessment = self.regulatory_risk_assessment()
        metrics.update(risk_assessment)
        return metrics

    def valuation_summary(self) -> Dict[str, Any]:
        """Comprehensive infrastructure valuation summary"""
        return {'infrastructure_overview': {'infrastructure_type': self.infrastructure_type, 'regulatory_framework': self.regulatory_framework, 'revenue_model': self.revenue_model, 'concession_period': self.concession_period, 'inflation_indexation': self.inflation_indexation}, 'financial_projections': self.project_cash_flows(), 'valuation_analysis': self.infrastructure_valuation(), 'risk_assessment': self.regulatory_risk_assessment()}

def infrastructure_valuation(self, discount_rate: Decimal=None) -> Dict[str, Decimal]:
    """
        Value infrastructure investment using DCF
        """
    if discount_rate is None:
        discount_rate = self.config.RISK_FREE_RATE + Decimal('0.03')
    projected_cfs = self.project_cash_flows()
    if not projected_cfs:
        return {'error': 'Cannot project cash flows'}
    present_value = Decimal('0')
    for cf in projected_cfs:
        year = cf['year']
        fcf = cf['free_cash_flow']
        pv = fcf / (Decimal('1') + discount_rate) ** year
        present_value += pv
    return {'enterprise_value': present_value, 'discount_rate': discount_rate, 'projection_years': len(projected_cfs), 'terminal_year_fcf': projected_cfs[-1]['free_cash_flow'] if projected_cfs else Decimal('0')}

def calculate_nav(self) -> Decimal:
    """Calculate infrastructure NAV using DCF"""
    valuation = self.infrastructure_valuation()
    if isinstance(valuation, dict) and 'enterprise_value' in valuation:
        return valuation['enterprise_value']
    return Decimal('0')

def calculate_key_metrics(self) -> Dict[str, Any]:
    """Calculate key infrastructure metrics"""
    metrics = {}
    valuation = self.infrastructure_valuation()
    if isinstance(valuation, dict):
        for key, value in valuation.items():
            if isinstance(value, Decimal):
                metrics[key] = float(value)
            else:
                metrics[key] = value
    if self.annual_revenue and self.operating_costs:
        ebitda_margin = (self.annual_revenue - self.operating_costs) / self.annual_revenue
        metrics['ebitda_margin'] = float(ebitda_margin)
    risk_assessment = self.regulatory_risk_assessment()
    metrics.update(risk_assessment)
    return metrics

def valuation_summary(self) -> Dict[str, Any]:
    """Comprehensive infrastructure valuation summary"""
    return {'infrastructure_overview': {'infrastructure_type': self.infrastructure_type, 'regulatory_framework': self.regulatory_framework, 'revenue_model': self.revenue_model, 'concession_period': self.concession_period, 'inflation_indexation': self.inflation_indexation}, 'financial_projections': self.project_cash_flows(), 'valuation_analysis': self.infrastructure_valuation(), 'risk_assessment': self.regulatory_risk_assessment()}

class RealEstatePortfolio:
    """
    Portfolio-level real estate analysis
    CFA Standards: Portfolio diversification and risk management
    """

    def __init__(self):
        self.real_estate_investments: List[RealEstateAnalyzer] = []
        self.reit_investments: List[REITAnalyzer] = []
        self.infrastructure_investments: List[InfrastructureAnalyzer] = []

    def add_real_estate(self, investment: RealEstateAnalyzer) -> None:
        """Add direct real estate investment"""
        self.real_estate_investments.append(investment)

    def add_reit(self, reit: REITAnalyzer) -> None:
        """Add REIT investment"""
        self.reit_investments.append(reit)

    def add_infrastructure(self, infrastructure: InfrastructureAnalyzer) -> None:
        """Add infrastructure investment"""
        self.infrastructure_investments.append(infrastructure)

    def portfolio_summary(self) -> Dict[str, Any]:
        """Generate comprehensive real estate portfolio summary"""
        total_nav = Decimal('0')
        re_navs = [inv.calculate_nav() for inv in self.real_estate_investments]
        re_total = sum(re_navs)
        total_nav += re_total
        reit_navs = [reit.calculate_nav() for reit in self.reit_investments]
        reit_total = sum(reit_navs)
        total_nav += reit_total
        infra_navs = [infra.calculate_nav() for infra in self.infrastructure_investments]
        infra_total = sum(infra_navs)
        total_nav += infra_total
        summary = {'portfolio_overview': {'total_portfolio_nav': float(total_nav), 'direct_real_estate_count': len(self.real_estate_investments), 'reit_count': len(self.reit_investments), 'infrastructure_count': len(self.infrastructure_investments)}, 'allocation': {'direct_real_estate': {'nav': float(re_total), 'weight': float(re_total / total_nav) if total_nav > 0 else 0}, 'reits': {'nav': float(reit_total), 'weight': float(reit_total / total_nav) if total_nav > 0 else 0}, 'infrastructure': {'nav': float(infra_total), 'weight': float(infra_total / total_nav) if total_nav > 0 else 0}}}
        return summary

    def geographic_diversification(self) -> Dict[str, Any]:
        """Analyze geographic diversification"""
        regions = {}
        for inv in self.real_estate_investments:
            region = getattr(inv.parameters, 'region', 'Unknown')
            if region not in regions:
                regions[region] = []
            regions[region].append(inv.calculate_nav())
        diversification = {}
        total_value = sum((sum(navs) for navs in regions.values()))
        for region, navs in regions.items():
            region_value = sum(navs)
            diversification[region] = {'count': len(navs), 'total_value': float(region_value), 'weight': float(region_value / total_value) if total_value > 0 else 0}
        return diversification

def portfolio_summary(self) -> Dict[str, Any]:
    """Generate comprehensive real estate portfolio summary"""
    total_nav = Decimal('0')
    re_navs = [inv.calculate_nav() for inv in self.real_estate_investments]
    re_total = sum(re_navs)
    total_nav += re_total
    reit_navs = [reit.calculate_nav() for reit in self.reit_investments]
    reit_total = sum(reit_navs)
    total_nav += reit_total
    infra_navs = [infra.calculate_nav() for infra in self.infrastructure_investments]
    infra_total = sum(infra_navs)
    total_nav += infra_total
    summary = {'portfolio_overview': {'total_portfolio_nav': float(total_nav), 'direct_real_estate_count': len(self.real_estate_investments), 'reit_count': len(self.reit_investments), 'infrastructure_count': len(self.infrastructure_investments)}, 'allocation': {'direct_real_estate': {'nav': float(re_total), 'weight': float(re_total / total_nav) if total_nav > 0 else 0}, 'reits': {'nav': float(reit_total), 'weight': float(reit_total / total_nav) if total_nav > 0 else 0}, 'infrastructure': {'nav': float(infra_total), 'weight': float(infra_total / total_nav) if total_nav > 0 else 0}}}
    return summary

def geographic_diversification(self) -> Dict[str, Any]:
    """Analyze geographic diversification"""
    regions = {}
    for inv in self.real_estate_investments:
        region = getattr(inv.parameters, 'region', 'Unknown')
        if region not in regions:
            regions[region] = []
        regions[region].append(inv.calculate_nav())
    diversification = {}
    total_value = sum((sum(navs) for navs in regions.values()))
    for region, navs in regions.items():
        region_value = sum(navs)
        diversification[region] = {'count': len(navs), 'total_value': float(region_value), 'weight': float(region_value / total_value) if total_value > 0 else 0}
    return diversification

class FinancialMath:
    """Core financial mathematics functions following CFA standards"""

    @staticmethod
    def irr(cash_flows: List[CashFlow], guess: Decimal=Decimal('0.10')) -> Optional[Decimal]:
        """
        Calculate Internal Rate of Return using Newton-Raphson method
        CFA Standard: IRR is the discount rate that makes NPV = 0

        Args:
            cash_flows: List of CashFlow objects
            guess: Initial guess for IRR

        Returns:
            IRR as decimal (e.g., 0.15 for 15%)
        """
        if not cash_flows:
            return None
        sorted_cfs = sorted(cash_flows, key=lambda x: x.date)
        dates = [datetime.strptime(cf.date, '%Y-%m-%d') for cf in sorted_cfs]
        amounts = [float(cf.amount) for cf in sorted_cfs]
        base_date = dates[0]
        days = [(d - base_date).days for d in dates]

        def npv(rate):
            return sum((amount / (1 + rate) ** (day / 365.25) for amount, day in zip(amounts, days)))

        def npv_derivative(rate):
            return sum((-amount * (day / 365.25) / (1 + rate) ** (day / 365.25 + 1) for amount, day in zip(amounts, days)))
        rate = float(guess)
        for _ in range(Config.PE_IRR_MAX_ITERATIONS):
            npv_val = npv(rate)
            if abs(npv_val) < float(Config.PE_IRR_TOLERANCE):
                return Decimal(str(rate))
            npv_deriv = npv_derivative(rate)
            if abs(npv_deriv) < 1e-12:
                break
            rate = rate - npv_val / npv_deriv
        return None

    @staticmethod
    def npv(cash_flows: List[CashFlow], discount_rate: Decimal) -> Decimal:
        """
        Calculate Net Present Value
        CFA Standard: NPV = Σ(CF_t / (1+r)^t)

        Args:
            cash_flows: List of CashFlow objects
            discount_rate: Discount rate as decimal

        Returns:
            NPV value
        """
        if not cash_flows:
            return Decimal('0')
        sorted_cfs = sorted(cash_flows, key=lambda x: x.date)
        base_date = datetime.strptime(sorted_cfs[0].date, '%Y-%m-%d')
        npv_value = Decimal('0')
        for cf in sorted_cfs:
            cf_date = datetime.strptime(cf.date, '%Y-%m-%d')
            years = Decimal(str((cf_date - base_date).days)) / Constants.DAYS_IN_YEAR
            present_value = cf.amount / (Decimal('1') + discount_rate) ** years
            npv_value += present_value
        return npv_value

    @staticmethod
    def moic(cash_flows: List[CashFlow]) -> Optional[Decimal]:
        """
        Calculate Multiple of Invested Capital
        CFA Standard: MOIC = Total Distributions / Total Contributions

        Args:
            cash_flows: List of CashFlow objects

        Returns:
            MOIC as decimal multiple
        """
        total_invested = Decimal('0')
        total_distributed = Decimal('0')
        for cf in cash_flows:
            if cf.amount < 0:
                total_invested += abs(cf.amount)
            elif cf.amount > 0:
                total_distributed += cf.amount
        if total_invested == 0:
            return None
        return total_distributed / total_invested

    @staticmethod
    def dpi(cash_flows: List[CashFlow]) -> Decimal:
        """
        Calculate Distributions to Paid-In Capital
        CFA Standard: DPI = Cumulative Distributions / Paid-In Capital

        Args:
            cash_flows: List of CashFlow objects

        Returns:
            DPI ratio
        """
        total_paid_in = Decimal('0')
        total_distributions = Decimal('0')
        for cf in cash_flows:
            if cf.cf_type in ['capital_call', 'investment'] or cf.amount < 0:
                total_paid_in += abs(cf.amount)
            elif cf.cf_type == 'distribution' or cf.amount > 0:
                total_distributions += cf.amount
        if total_paid_in == 0:
            return Decimal('0')
        return total_distributions / total_paid_in

    @staticmethod
    def rvpi(cash_flows: List[CashFlow], current_nav: Decimal) -> Decimal:
        """
        Calculate Residual Value to Paid-In Capital
        CFA Standard: RVPI = Net Asset Value / Paid-In Capital

        Args:
            cash_flows: List of CashFlow objects
            current_nav: Current Net Asset Value

        Returns:
            RVPI ratio
        """
        total_paid_in = Decimal('0')
        for cf in cash_flows:
            if cf.cf_type in ['capital_call', 'investment'] or cf.amount < 0:
                total_paid_in += abs(cf.amount)
        if total_paid_in == 0:
            return Decimal('0')
        return current_nav / total_paid_in

    @staticmethod
    def sharpe_ratio(returns: List[Decimal], risk_free_rate: Decimal=None) -> Decimal:
        """
        Calculate Sharpe Ratio
        CFA Standard: (Portfolio Return - Risk-Free Rate) / Portfolio Standard Deviation

        Args:
            returns: List of period returns
            risk_free_rate: Risk-free rate for the period

        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return Decimal('0')
        if risk_free_rate is None:
            risk_free_rate = Config.RISK_FREE_RATE / Constants.MONTHS_IN_YEAR
        excess_returns = [r - risk_free_rate for r in returns]
        mean_excess = sum(excess_returns) / len(excess_returns)
        if len(excess_returns) == 1:
            return Decimal('0')
        variance = sum(((r - mean_excess) ** 2 for r in excess_returns)) / (len(excess_returns) - 1)
        std_dev = variance.sqrt()
        if std_dev == 0:
            return Decimal('0')
        return mean_excess / std_dev

    @staticmethod
    def sortino_ratio(returns: List[Decimal], target_return: Decimal=Decimal('0')) -> Decimal:
        """
        Calculate Sortino Ratio
        CFA Standard: (Portfolio Return - Target Return) / Downside Deviation

        Args:
            returns: List of period returns
            target_return: Target or minimum acceptable return

        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            return Decimal('0')
        excess_returns = [r - target_return for r in returns]
        mean_excess = sum(excess_returns) / len(excess_returns)
        downside_returns = [r for r in excess_returns if r < 0]
        if not downside_returns:
            return Decimal('999')
        downside_variance = sum((r ** 2 for r in downside_returns)) / len(returns)
        downside_deviation = downside_variance.sqrt()
        if downside_deviation == 0:
            return Decimal('0')
        return mean_excess / downside_deviation

    @staticmethod
    def maximum_drawdown(prices: List[Decimal]) -> Tuple[Decimal, int, int]:
        """
        Calculate Maximum Drawdown
        CFA Standard: Maximum peak-to-trough decline

        Args:
            prices: List of price values

        Returns:
            Tuple of (max_drawdown, peak_index, trough_index)
        """
        if len(prices) < 2:
            return (Decimal('0'), 0, 0)
        max_dd = Decimal('0')
        peak_idx = 0
        trough_idx = 0
        current_peak = prices[0]
        current_peak_idx = 0
        for i, price in enumerate(prices):
            if price > current_peak:
                current_peak = price
                current_peak_idx = i
            drawdown = (current_peak - price) / current_peak
            if drawdown > max_dd:
                max_dd = drawdown
                peak_idx = current_peak_idx
                trough_idx = i
        return (max_dd, peak_idx, trough_idx)

    @staticmethod
    def var_historical(returns: List[Decimal], confidence_level: Decimal=Decimal('0.05')) -> Decimal:
        """
        Calculate Historical Value at Risk
        CFA Standard: Historical simulation method

        Args:
            returns: List of historical returns
            confidence_level: Confidence level (e.g., 0.05 for 95% VaR)

        Returns:
            VaR value (positive number representing loss)
        """
        if not returns:
            return Decimal('0')
        sorted_returns = sorted(returns)
        index = int(len(sorted_returns) * confidence_level)
        if index >= len(sorted_returns):
            index = len(sorted_returns) - 1
        return abs(sorted_returns[index])

    @staticmethod
    def calmar_ratio(annual_return: Decimal, max_drawdown: Decimal) -> Decimal:
        """
        Calculate Calmar Ratio
        CFA Standard: Annual Return / Maximum Drawdown

        Args:
            annual_return: Annualized return
            max_drawdown: Maximum drawdown

        Returns:
            Calmar ratio
        """
        if max_drawdown == 0:
            return Decimal('999')
        return annual_return / max_drawdown

@staticmethod
def irr(cash_flows: List[CashFlow], guess: Decimal=Decimal('0.10')) -> Optional[Decimal]:
    """
        Calculate Internal Rate of Return using Newton-Raphson method
        CFA Standard: IRR is the discount rate that makes NPV = 0

        Args:
            cash_flows: List of CashFlow objects
            guess: Initial guess for IRR

        Returns:
            IRR as decimal (e.g., 0.15 for 15%)
        """
    if not cash_flows:
        return None
    sorted_cfs = sorted(cash_flows, key=lambda x: x.date)
    dates = [datetime.strptime(cf.date, '%Y-%m-%d') for cf in sorted_cfs]
    amounts = [float(cf.amount) for cf in sorted_cfs]
    base_date = dates[0]
    days = [(d - base_date).days for d in dates]

    def npv(rate):
        return sum((amount / (1 + rate) ** (day / 365.25) for amount, day in zip(amounts, days)))

    def npv_derivative(rate):
        return sum((-amount * (day / 365.25) / (1 + rate) ** (day / 365.25 + 1) for amount, day in zip(amounts, days)))
    rate = float(guess)
    for _ in range(Config.PE_IRR_MAX_ITERATIONS):
        npv_val = npv(rate)
        if abs(npv_val) < float(Config.PE_IRR_TOLERANCE):
            return Decimal(str(rate))
        npv_deriv = npv_derivative(rate)
        if abs(npv_deriv) < 1e-12:
            break
        rate = rate - npv_val / npv_deriv
    return None

@staticmethod
def moic(cash_flows: List[CashFlow]) -> Optional[Decimal]:
    """
        Calculate Multiple of Invested Capital
        CFA Standard: MOIC = Total Distributions / Total Contributions

        Args:
            cash_flows: List of CashFlow objects

        Returns:
            MOIC as decimal multiple
        """
    total_invested = Decimal('0')
    total_distributed = Decimal('0')
    for cf in cash_flows:
        if cf.amount < 0:
            total_invested += abs(cf.amount)
        elif cf.amount > 0:
            total_distributed += cf.amount
    if total_invested == 0:
        return None
    return total_distributed / total_invested

@staticmethod
def dpi(cash_flows: List[CashFlow]) -> Decimal:
    """
        Calculate Distributions to Paid-In Capital
        CFA Standard: DPI = Cumulative Distributions / Paid-In Capital

        Args:
            cash_flows: List of CashFlow objects

        Returns:
            DPI ratio
        """
    total_paid_in = Decimal('0')
    total_distributions = Decimal('0')
    for cf in cash_flows:
        if cf.cf_type in ['capital_call', 'investment'] or cf.amount < 0:
            total_paid_in += abs(cf.amount)
        elif cf.cf_type == 'distribution' or cf.amount > 0:
            total_distributions += cf.amount
    if total_paid_in == 0:
        return Decimal('0')
    return total_distributions / total_paid_in

@staticmethod
def rvpi(cash_flows: List[CashFlow], current_nav: Decimal) -> Decimal:
    """
        Calculate Residual Value to Paid-In Capital
        CFA Standard: RVPI = Net Asset Value / Paid-In Capital

        Args:
            cash_flows: List of CashFlow objects
            current_nav: Current Net Asset Value

        Returns:
            RVPI ratio
        """
    total_paid_in = Decimal('0')
    for cf in cash_flows:
        if cf.cf_type in ['capital_call', 'investment'] or cf.amount < 0:
            total_paid_in += abs(cf.amount)
    if total_paid_in == 0:
        return Decimal('0')
    return current_nav / total_paid_in

@staticmethod
def calmar_ratio(annual_return: Decimal, max_drawdown: Decimal) -> Decimal:
    """
        Calculate Calmar Ratio
        CFA Standard: Annual Return / Maximum Drawdown

        Args:
            annual_return: Annualized return
            max_drawdown: Maximum drawdown

        Returns:
            Calmar ratio
        """
    if max_drawdown == 0:
        return Decimal('999')
    return annual_return / max_drawdown

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

class IncomeApproachValuator(BaseValuationModel):
    """Income approach valuation for private companies"""

    def __init__(self):
        super().__init__('Income Approach', 'Income-based private company valuation')
        self.valuation_method = ValuationMethod.PRIVATE_INCOME

    def validate_inputs(self, **kwargs) -> bool:
        """Validate income approach inputs"""
        normalized_earnings = kwargs.get('normalized_earnings')
        discount_rate = kwargs.get('discount_rate')
        if normalized_earnings is None or discount_rate is None:
            raise ValidationError('Normalized earnings and discount rate required')
        ModelValidator.validate_percentage(discount_rate, 'Discount rate')
        return True

    def calculate_capitalized_earnings_value(self, normalized_earnings: float, capitalization_rate: float, growth_rate: float=0) -> float:
        """Calculate value using capitalized earnings method"""
        if capitalization_rate <= growth_rate:
            raise ValidationError('Capitalization rate must be greater than growth rate')
        if growth_rate == 0:
            return normalized_earnings / capitalization_rate
        else:
            next_year_earnings = normalized_earnings * (1 + growth_rate)
            return next_year_earnings / (capitalization_rate - growth_rate)

    def calculate_dcf_value(self, projected_cash_flows: List[float], discount_rate: float, terminal_value: float=None, terminal_growth: float=None) -> Dict[str, float]:
        """Calculate DCF value for private company"""
        pv_cash_flows = 0
        for i, cf in enumerate(projected_cash_flows):
            pv_cf = CalculationEngine.present_value(cf, discount_rate, i + 1)
            pv_cash_flows += pv_cf
        if terminal_value is None and terminal_growth is not None:
            if len(projected_cash_flows) > 0:
                final_cf = projected_cash_flows[-1]
                terminal_cf = final_cf * (1 + terminal_growth)
                terminal_value = terminal_cf / (discount_rate - terminal_growth)
            else:
                terminal_value = 0
        elif terminal_value is None:
            terminal_value = 0
        pv_terminal = CalculationEngine.present_value(terminal_value, discount_rate, len(projected_cash_flows))
        enterprise_value = pv_cash_flows + pv_terminal
        return {'pv_cash_flows': pv_cash_flows, 'terminal_value': terminal_value, 'pv_terminal': pv_terminal, 'enterprise_value': enterprise_value}

    def calculate_excess_earnings_value(self, normalized_earnings: float, tangible_assets: float, required_return_assets: float, required_return_intangibles: float) -> Dict[str, float]:
        """Calculate value using excess earnings method"""
        tangible_asset_return = tangible_assets * required_return_assets
        excess_earnings = normalized_earnings - tangible_asset_return
        if excess_earnings > 0:
            intangible_value = excess_earnings / required_return_intangibles
        else:
            intangible_value = 0
        total_value = tangible_assets + intangible_value
        return {'tangible_asset_value': tangible_assets, 'tangible_asset_return': tangible_asset_return, 'excess_earnings': excess_earnings, 'intangible_value': intangible_value, 'total_business_value': total_value}

    def calculate_adjusted_present_value(self, unlevered_cash_flows: List[float], unlevered_discount_rate: float, tax_shield_values: List[float], tax_shield_discount_rate: float) -> Dict[str, float]:
        """Calculate APV for private companies with complex capital structures"""
        pv_unlevered_cf = sum((CalculationEngine.present_value(cf, unlevered_discount_rate, i + 1) for i, cf in enumerate(unlevered_cash_flows)))
        pv_tax_shields = sum((CalculationEngine.present_value(ts, tax_shield_discount_rate, i + 1) for i, ts in enumerate(tax_shield_values)))
        total_firm_value = pv_unlevered_cf + pv_tax_shields
        return {'unlevered_firm_value': pv_unlevered_cf, 'tax_shield_value': pv_tax_shields, 'total_firm_value': total_firm_value}

def validate_inputs(self, **kwargs) -> bool:
    """Validate income approach inputs"""
    normalized_earnings = kwargs.get('normalized_earnings')
    discount_rate = kwargs.get('discount_rate')
    if normalized_earnings is None or discount_rate is None:
        raise ValidationError('Normalized earnings and discount rate required')
    ModelValidator.validate_percentage(discount_rate, 'Discount rate')
    return True

def calculate_dcf_value(self, projected_cash_flows: List[float], discount_rate: float, terminal_value: float=None, terminal_growth: float=None) -> Dict[str, float]:
    """Calculate DCF value for private company"""
    pv_cash_flows = 0
    for i, cf in enumerate(projected_cash_flows):
        pv_cf = CalculationEngine.present_value(cf, discount_rate, i + 1)
        pv_cash_flows += pv_cf
    if terminal_value is None and terminal_growth is not None:
        if len(projected_cash_flows) > 0:
            final_cf = projected_cash_flows[-1]
            terminal_cf = final_cf * (1 + terminal_growth)
            terminal_value = terminal_cf / (discount_rate - terminal_growth)
        else:
            terminal_value = 0
    elif terminal_value is None:
        terminal_value = 0
    pv_terminal = CalculationEngine.present_value(terminal_value, discount_rate, len(projected_cash_flows))
    enterprise_value = pv_cash_flows + pv_terminal
    return {'pv_cash_flows': pv_cash_flows, 'terminal_value': terminal_value, 'pv_terminal': pv_terminal, 'enterprise_value': enterprise_value}

def calculate_adjusted_present_value(self, unlevered_cash_flows: List[float], unlevered_discount_rate: float, tax_shield_values: List[float], tax_shield_discount_rate: float) -> Dict[str, float]:
    """Calculate APV for private companies with complex capital structures"""
    pv_unlevered_cf = sum((CalculationEngine.present_value(cf, unlevered_discount_rate, i + 1) for i, cf in enumerate(unlevered_cash_flows)))
    pv_tax_shields = sum((CalculationEngine.present_value(ts, tax_shield_discount_rate, i + 1) for i, ts in enumerate(tax_shield_values)))
    total_firm_value = pv_unlevered_cf + pv_tax_shields
    return {'unlevered_firm_value': pv_unlevered_cf, 'tax_shield_value': pv_tax_shields, 'total_firm_value': total_firm_value}

class EconomicValueAddedModel(BaseValuationModel):
    """Economic Value Added (EVA) Model"""

    def __init__(self):
        super().__init__('EVA Model', 'Economic Value Added valuation')
        self.valuation_method = ValuationMethod.RESIDUAL_INCOME

    def calculate_eva(self, nopat: float, invested_capital: float, wacc: float) -> float:
        """Calculate Economic Value Added"""
        return CalculationEngine.economic_value_added(nopat, invested_capital, wacc)

    def calculate_nopat(self, ebit: float, tax_rate: float) -> float:
        """Calculate Net Operating Profit After Tax"""
        return ebit * (1 - tax_rate)

    def calculate_invested_capital(self, total_assets: float, non_interest_bearing_liabilities: float) -> float:
        """Calculate invested capital"""
        return total_assets - non_interest_bearing_liabilities

    def calculate_eva_from_components(self, ebit: float, tax_rate: float, total_assets: float, non_interest_bearing_liabilities: float, wacc: float) -> float:
        """Calculate EVA from financial statement components"""
        nopat = self.calculate_nopat(ebit, tax_rate)
        invested_capital = self.calculate_invested_capital(total_assets, non_interest_bearing_liabilities)
        return self.calculate_eva(nopat, invested_capital, wacc)

    def calculate_market_value_added(self, market_value: float, invested_capital: float) -> float:
        """Calculate Market Value Added (MVA)"""
        return market_value - invested_capital

    def eva_valuation(self, current_invested_capital: float, projected_evas: List[float], wacc: float, terminal_eva: float=None, terminal_growth: float=None) -> Dict[str, float]:
        """Calculate firm value using EVA approach"""
        pv_evas = 0
        for year, eva in enumerate(projected_evas, 1):
            pv_eva = CalculationEngine.present_value(eva, wacc, year)
            pv_evas += pv_eva
        if terminal_eva is not None:
            if terminal_growth is None:
                terminal_growth = 0
            if terminal_growth >= wacc:
                raise ValidationError('Terminal growth must be less than WACC for EVA terminal value')
            next_eva = terminal_eva * (1 + terminal_growth)
            terminal_value = next_eva / (wacc - terminal_growth)
            pv_terminal = CalculationEngine.present_value(terminal_value, wacc, len(projected_evas))
        else:
            pv_terminal = 0
        firm_value = current_invested_capital + pv_evas + pv_terminal
        return {'current_invested_capital': current_invested_capital, 'pv_projected_evas': pv_evas, 'pv_terminal_evas': pv_terminal, 'total_firm_value': firm_value}

def eva_valuation(self, current_invested_capital: float, projected_evas: List[float], wacc: float, terminal_eva: float=None, terminal_growth: float=None) -> Dict[str, float]:
    """Calculate firm value using EVA approach"""
    pv_evas = 0
    for year, eva in enumerate(projected_evas, 1):
        pv_eva = CalculationEngine.present_value(eva, wacc, year)
        pv_evas += pv_eva
    if terminal_eva is not None:
        if terminal_growth is None:
            terminal_growth = 0
        if terminal_growth >= wacc:
            raise ValidationError('Terminal growth must be less than WACC for EVA terminal value')
        next_eva = terminal_eva * (1 + terminal_growth)
        terminal_value = next_eva / (wacc - terminal_growth)
        pv_terminal = CalculationEngine.present_value(terminal_value, wacc, len(projected_evas))
    else:
        pv_terminal = 0
    firm_value = current_invested_capital + pv_evas + pv_terminal
    return {'current_invested_capital': current_invested_capital, 'pv_projected_evas': pv_evas, 'pv_terminal_evas': pv_terminal, 'total_firm_value': firm_value}

class BinomialPricingEngine(PricingEngine):
    """Multi-period binomial tree pricing engine"""

    def __init__(self, steps: int=50):
        self.steps = steps

    def price(self, instrument: VanillaOption, market_data: MarketData) -> PricingResult:
        """Price option using binomial tree"""
        if not self.validate_inputs(instrument, market_data):
            raise ValidationError('Invalid inputs for binomial pricing')
        S = market_data.spot_price
        K = instrument.strike_price
        T = instrument.time_to_expiry()
        r = market_data.risk_free_rate
        q = market_data.dividend_yield
        sigma = market_data.volatility
        if T <= 0:
            return PricingResult(fair_value=instrument.calculate_payoff(S))
        dt = T / self.steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        prob_up = (np.exp((r - q) * dt) - d) / (u - d)
        stock_tree = np.zeros((self.steps + 1, self.steps + 1))
        option_tree = np.zeros((self.steps + 1, self.steps + 1))
        for j in range(self.steps + 1):
            stock_tree[self.steps, j] = S * u ** (self.steps - j) * d ** j
        for j in range(self.steps + 1):
            option_tree[self.steps, j] = instrument.calculate_payoff(stock_tree[self.steps, j])
        for i in range(self.steps - 1, -1, -1):
            for j in range(i + 1):
                stock_tree[i, j] = S * u ** (i - j) * d ** j
                european_value = (prob_up * option_tree[i + 1, j] + (1 - prob_up) * option_tree[i + 1, j + 1]) * np.exp(-r * dt)
                if instrument.exercise_style == ExerciseStyle.AMERICAN:
                    exercise_value = instrument.calculate_payoff(stock_tree[i, j])
                    option_tree[i, j] = max(european_value, exercise_value)
                else:
                    option_tree[i, j] = european_value
        fair_value = option_tree[0, 0] * instrument.notional
        intrinsic = instrument.intrinsic_value(S)
        return PricingResult(fair_value=fair_value, intrinsic_value=intrinsic, time_value=fair_value - intrinsic, calculation_details={'model': 'Binomial Tree', 'steps': self.steps, 'u': u, 'd': d, 'prob_up': prob_up, 'dt': dt})

    def validate_inputs(self, instrument: VanillaOption, market_data: MarketData) -> bool:
        """Validate inputs for binomial pricing"""
        try:
            ModelValidator.validate_positive(market_data.spot_price, 'spot_price')
            ModelValidator.validate_positive(instrument.strike_price, 'strike_price')
            ModelValidator.validate_volatility(market_data.volatility)
            ModelValidator.validate_rate(market_data.risk_free_rate, 'risk_free_rate')
            return True
        except ValidationError:
            return False

def validate_inputs(self, instrument: VanillaOption, market_data: MarketData) -> bool:
    """Validate inputs for binomial pricing"""
    try:
        ModelValidator.validate_positive(market_data.spot_price, 'spot_price')
        ModelValidator.validate_positive(instrument.strike_price, 'strike_price')
        ModelValidator.validate_volatility(market_data.volatility)
        ModelValidator.validate_rate(market_data.risk_free_rate, 'risk_free_rate')
        return True
    except ValidationError:
        return False

class BlackScholesPricingEngine(PricingEngine):
    """Black-Scholes-Merton pricing engine with Greeks"""

    def price(self, instrument: VanillaOption, market_data: MarketData) -> PricingResult:
        """Price European option using Black-Scholes-Merton"""
        if not self.validate_inputs(instrument, market_data):
            raise ValidationError('Invalid inputs for Black-Scholes pricing')
        if instrument.exercise_style != ExerciseStyle.EUROPEAN:
            raise ValueError('Black-Scholes only valid for European options')
        result = instrument._black_scholes_price(market_data)
        greeks = self.calculate_greeks(instrument, market_data)
        result.greeks = greeks.__dict__
        return result

    def calculate_greeks(self, instrument: VanillaOption, market_data: MarketData) -> OptionGreeks:
        """Calculate all option Greeks"""
        S = market_data.spot_price
        K = instrument.strike_price
        T = instrument.time_to_expiry()
        r = market_data.risk_free_rate
        q = market_data.dividend_yield
        sigma = market_data.volatility
        if T <= 0:
            return OptionGreeks()
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        n_d1 = norm.pdf(d1)
        N_d1 = norm.cdf(d1)
        N_d2 = norm.cdf(d2)
        greeks = OptionGreeks()
        if instrument.option_type == OptionType.CALL:
            greeks.delta = np.exp(-q * T) * N_d1
            greeks.theta = (-S * n_d1 * sigma * np.exp(-q * T) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * N_d2 + q * S * np.exp(-q * T) * N_d1) / 365
            greeks.rho = K * T * np.exp(-r * T) * N_d2 / 100
        else:
            greeks.delta = -np.exp(-q * T) * norm.cdf(-d1)
            greeks.theta = (-S * n_d1 * sigma * np.exp(-q * T) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2) - q * S * np.exp(-q * T) * norm.cdf(-d1)) / 365
            greeks.rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        greeks.gamma = n_d1 * np.exp(-q * T) / (S * sigma * np.sqrt(T))
        greeks.vega = S * n_d1 * np.sqrt(T) * np.exp(-q * T) / 100
        greeks.vanna = -greeks.vega * d2 / sigma
        greeks.volga = greeks.vega * d1 * d2 / sigma
        greeks.charm = (q * np.exp(-q * T) * norm.cdf(d1 if instrument.option_type == OptionType.CALL else -d1) - np.exp(-q * T) * n_d1 * (2 * (r - q) * T - d2 * sigma * np.sqrt(T)) / (2 * T * sigma * np.sqrt(T))) / 365
        return greeks

    def validate_inputs(self, instrument: VanillaOption, market_data: MarketData) -> bool:
        """Validate inputs for Black-Scholes pricing"""
        try:
            ModelValidator.validate_positive(market_data.spot_price, 'spot_price')
            ModelValidator.validate_positive(instrument.strike_price, 'strike_price')
            ModelValidator.validate_volatility(market_data.volatility)
            ModelValidator.validate_rate(market_data.risk_free_rate, 'risk_free_rate')
            ModelValidator.validate_non_negative(market_data.dividend_yield, 'dividend_yield')
            if instrument.time_to_expiry() < 0:
                return False
            return True
        except ValidationError:
            return False

def validate_inputs(self, instrument: VanillaOption, market_data: MarketData) -> bool:
    """Validate inputs for Black-Scholes pricing"""
    try:
        ModelValidator.validate_positive(market_data.spot_price, 'spot_price')
        ModelValidator.validate_positive(instrument.strike_price, 'strike_price')
        ModelValidator.validate_volatility(market_data.volatility)
        ModelValidator.validate_rate(market_data.risk_free_rate, 'risk_free_rate')
        ModelValidator.validate_non_negative(market_data.dividend_yield, 'dividend_yield')
        if instrument.time_to_expiry() < 0:
            return False
        return True
    except ValidationError:
        return False

class BlackModelPricingEngine(PricingEngine):
    """Black model for options on futures and forwards"""

    def price(self, instrument: VanillaOption, market_data: MarketData) -> PricingResult:
        """Price option on futures using Black model"""
        if not self.validate_inputs(instrument, market_data):
            raise ValidationError('Invalid inputs for Black model pricing')
        F = market_data.forward_price or market_data.spot_price
        K = instrument.strike_price
        T = instrument.time_to_expiry()
        r = market_data.risk_free_rate
        sigma = market_data.volatility
        if T <= 0:
            return PricingResult(fair_value=instrument.calculate_payoff(F))
        d1 = (np.log(F / K) + 0.5 * sigma ** 2 * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        if instrument.option_type == OptionType.CALL:
            price = np.exp(-r * T) * (F * norm.cdf(d1) - K * norm.cdf(d2))
        else:
            price = np.exp(-r * T) * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
        price *= instrument.notional
        return PricingResult(fair_value=price, calculation_details={'model': 'Black Model', 'forward_price': F, 'd1': d1, 'd2': d2})

    def validate_inputs(self, instrument: VanillaOption, market_data: MarketData) -> bool:
        """Validate inputs for Black model"""
        try:
            forward_price = market_data.forward_price or market_data.spot_price
            ModelValidator.validate_positive(forward_price, 'forward_price')
            ModelValidator.validate_positive(instrument.strike_price, 'strike_price')
            ModelValidator.validate_volatility(market_data.volatility)
            ModelValidator.validate_rate(market_data.risk_free_rate, 'risk_free_rate')
            return True
        except ValidationError:
            return False

def validate_inputs(self, instrument: VanillaOption, market_data: MarketData) -> bool:
    """Validate inputs for Black model"""
    try:
        forward_price = market_data.forward_price or market_data.spot_price
        ModelValidator.validate_positive(forward_price, 'forward_price')
        ModelValidator.validate_positive(instrument.strike_price, 'strike_price')
        ModelValidator.validate_volatility(market_data.volatility)
        ModelValidator.validate_rate(market_data.risk_free_rate, 'risk_free_rate')
        return True
    except ValidationError:
        return False

@dataclass
class CarryModel:
    """Carry arbitrage model parameters"""
    spot_price: float
    risk_free_rate: float
    dividend_yield: float = 0.0
    storage_cost: float = 0.0
    convenience_yield: float = 0.0
    repo_rate: Optional[float] = None
    borrow_cost: Optional[float] = None

    def __post_init__(self):
        ModelValidator.validate_positive(self.spot_price, 'spot_price')
        ModelValidator.validate_rate(self.risk_free_rate, 'risk_free_rate')
        ModelValidator.validate_non_negative(self.dividend_yield, 'dividend_yield')
        ModelValidator.validate_non_negative(self.storage_cost, 'storage_cost')
        ModelValidator.validate_non_negative(self.convenience_yield, 'convenience_yield')

    @property
    def net_carry_rate(self) -> float:
        """Calculate net carry rate"""
        carry_rate = self.risk_free_rate - self.dividend_yield + self.storage_cost - self.convenience_yield
        if self.repo_rate is not None:
            carry_rate = self.repo_rate - self.dividend_yield + self.storage_cost - self.convenience_yield
        if self.borrow_cost is not None:
            carry_rate += self.borrow_cost
        return carry_rate

def __post_init__(self):
    ModelValidator.validate_positive(self.spot_price, 'spot_price')
    ModelValidator.validate_rate(self.risk_free_rate, 'risk_free_rate')
    ModelValidator.validate_non_negative(self.dividend_yield, 'dividend_yield')
    ModelValidator.validate_non_negative(self.storage_cost, 'storage_cost')
    ModelValidator.validate_non_negative(self.convenience_yield, 'convenience_yield')

class InterestRateSwap:
    """Interest Rate Swap implementation"""

    def __init__(self, notional: float, fixed_rate: float, floating_rate_index: str, start_date: datetime, end_date: datetime, payment_frequency: float=0.25, day_count: DayCountConvention=DayCountConvention.ACT_360, currency: str='USD'):
        self.notional = notional
        self.fixed_rate = fixed_rate
        self.floating_rate_index = floating_rate_index
        self.start_date = start_date
        self.end_date = end_date
        self.payment_frequency = payment_frequency
        self.day_count = day_count
        self.currency = currency
        ModelValidator.validate_positive(notional, 'notional')
        ModelValidator.validate_rate(fixed_rate, 'fixed_rate')

    def fair_value(self, yield_curve: CurveData, pay_fixed: bool=True) -> PricingResult:
        """Calculate swap fair value using yield curve"""
        payment_dates = self._generate_payment_dates()
        fixed_leg_pv = 0.0
        for payment_date in payment_dates:
            time_to_payment = calculate_time_fraction(datetime.now(), payment_date, self.day_count)
            discount_rate = yield_curve.interpolate_rate(time_to_payment)
            discount_factor = np.exp(-discount_rate * time_to_payment)
            period_length = self.payment_frequency
            fixed_payment = self.fixed_rate * period_length * self.notional
            fixed_leg_pv += fixed_payment * discount_factor
        floating_leg_pv = self.notional * (1 - np.exp(-yield_curve.interpolate_rate(calculate_time_fraction(datetime.now(), self.end_date, self.day_count)) * calculate_time_fraction(datetime.now(), self.end_date, self.day_count)))
        if pay_fixed:
            fair_value = floating_leg_pv - fixed_leg_pv
        else:
            fair_value = fixed_leg_pv - floating_leg_pv
        return PricingResult(fair_value=fair_value, calculation_details={'fixed_leg_pv': fixed_leg_pv, 'floating_leg_pv': floating_leg_pv, 'pay_fixed': pay_fixed, 'payment_dates': len(payment_dates)})

    def _generate_payment_dates(self) -> List[datetime]:
        """Generate payment dates for swap"""
        payment_dates = []
        current_date = self.start_date
        while current_date < self.end_date:
            days_to_add = int(self.payment_frequency * 365.25)
            next_date = current_date.replace(day=current_date.day + days_to_add)
            if next_date <= self.end_date:
                payment_dates.append(next_date)
            current_date = next_date
        return payment_dates

    def par_rate(self, yield_curve: CurveData) -> float:
        """Calculate par swap rate (market swap rate)"""
        payment_dates = self._generate_payment_dates()
        annuity_factor = 0.0
        for payment_date in payment_dates:
            time_to_payment = calculate_time_fraction(datetime.now(), payment_date, self.day_count)
            discount_rate = yield_curve.interpolate_rate(time_to_payment)
            discount_factor = np.exp(-discount_rate * time_to_payment)
            annuity_factor += discount_factor * self.payment_frequency
        final_time = calculate_time_fraction(datetime.now(), self.end_date, self.day_count)
        final_discount_factor = np.exp(-yield_curve.interpolate_rate(final_time) * final_time)
        par_rate = (1 - final_discount_factor) / annuity_factor
        return par_rate

def __init__(self, notional: float, fixed_rate: float, floating_rate_index: str, start_date: datetime, end_date: datetime, payment_frequency: float=0.25, day_count: DayCountConvention=DayCountConvention.ACT_360, currency: str='USD'):
    self.notional = notional
    self.fixed_rate = fixed_rate
    self.floating_rate_index = floating_rate_index
    self.start_date = start_date
    self.end_date = end_date
    self.payment_frequency = payment_frequency
    self.day_count = day_count
    self.currency = currency
    ModelValidator.validate_positive(notional, 'notional')
    ModelValidator.validate_rate(fixed_rate, 'fixed_rate')

class CurrencySwap:
    """Currency Swap implementation"""

    def __init__(self, notional_domestic: float, notional_foreign: float, fixed_rate_domestic: float, fixed_rate_foreign: float, start_date: datetime, end_date: datetime, domestic_currency: str='USD', foreign_currency: str='EUR', payment_frequency: float=0.5):
        self.notional_domestic = notional_domestic
        self.notional_foreign = notional_foreign
        self.fixed_rate_domestic = fixed_rate_domestic
        self.fixed_rate_foreign = fixed_rate_foreign
        self.start_date = start_date
        self.end_date = end_date
        self.domestic_currency = domestic_currency
        self.foreign_currency = foreign_currency
        self.payment_frequency = payment_frequency
        ModelValidator.validate_positive(notional_domestic, 'domestic_notional')
        ModelValidator.validate_positive(notional_foreign, 'foreign_notional')

    def fair_value(self, domestic_curve: CurveData, foreign_curve: CurveData, fx_rate: float) -> PricingResult:
        """Calculate currency swap fair value"""
        domestic_leg_pv = self._calculate_leg_pv(self.notional_domestic, self.fixed_rate_domestic, domestic_curve)
        foreign_leg_pv_foreign = self._calculate_leg_pv(self.notional_foreign, self.fixed_rate_foreign, foreign_curve)
        foreign_leg_pv_domestic = foreign_leg_pv_foreign * fx_rate
        fair_value = foreign_leg_pv_domestic - domestic_leg_pv
        return PricingResult(fair_value=fair_value, calculation_details={'domestic_leg_pv': domestic_leg_pv, 'foreign_leg_pv_foreign': foreign_leg_pv_foreign, 'foreign_leg_pv_domestic': foreign_leg_pv_domestic, 'fx_rate': fx_rate})

    def _calculate_leg_pv(self, notional: float, fixed_rate: float, yield_curve: CurveData) -> float:
        """Calculate present value of one leg"""
        total_time = calculate_time_fraction(self.start_date, self.end_date, DayCountConvention.ACT_365)
        num_payments = int(total_time / self.payment_frequency)
        leg_pv = 0.0
        for i in range(1, num_payments + 1):
            payment_time = i * self.payment_frequency
            discount_rate = yield_curve.interpolate_rate(payment_time)
            discount_factor = np.exp(-discount_rate * payment_time)
            coupon_payment = fixed_rate * self.payment_frequency * notional
            leg_pv += coupon_payment * discount_factor
        final_discount_rate = yield_curve.interpolate_rate(total_time)
        final_discount_factor = np.exp(-final_discount_rate * total_time)
        leg_pv += notional * final_discount_factor
        return leg_pv

def __init__(self, notional_domestic: float, notional_foreign: float, fixed_rate_domestic: float, fixed_rate_foreign: float, start_date: datetime, end_date: datetime, domestic_currency: str='USD', foreign_currency: str='EUR', payment_frequency: float=0.5):
    self.notional_domestic = notional_domestic
    self.notional_foreign = notional_foreign
    self.fixed_rate_domestic = fixed_rate_domestic
    self.fixed_rate_foreign = fixed_rate_foreign
    self.start_date = start_date
    self.end_date = end_date
    self.domestic_currency = domestic_currency
    self.foreign_currency = foreign_currency
    self.payment_frequency = payment_frequency
    ModelValidator.validate_positive(notional_domestic, 'domestic_notional')
    ModelValidator.validate_positive(notional_foreign, 'foreign_notional')

class EquitySwap:
    """Equity Swap implementation"""

    def __init__(self, notional: float, equity_leg_return: str, fixed_rate: Optional[float]=None, floating_rate_spread: float=0.0, start_date: datetime=None, end_date: datetime=None, payment_frequency: float=0.25):
        self.notional = notional
        self.equity_leg_return = equity_leg_return
        self.fixed_rate = fixed_rate
        self.floating_rate_spread = floating_rate_spread
        self.start_date = start_date or datetime.now()
        self.end_date = end_date
        self.payment_frequency = payment_frequency
        ModelValidator.validate_positive(notional, 'notional')

    def calculate_equity_leg_payment(self, initial_price: float, final_price: float, dividends: float=0.0) -> float:
        """Calculate equity leg payment"""
        price_return = (final_price - initial_price) / initial_price
        if self.equity_leg_return == 'total_return':
            total_return = price_return + dividends / initial_price
            return self.notional * total_return
        else:
            return self.notional * price_return

    def calculate_fixed_leg_payment(self, period_length: float) -> float:
        """Calculate fixed leg payment"""
        if self.fixed_rate is None:
            raise ValueError('Fixed rate not specified for equity swap')
        return self.notional * self.fixed_rate * period_length

    def fair_value(self, market_data: MarketData, expected_equity_return: float) -> PricingResult:
        """Calculate equity swap fair value"""
        time_to_expiry = calculate_time_fraction(self.start_date, self.end_date, DayCountConvention.ACT_365)
        expected_equity_pv = self.notional * expected_equity_return * np.exp(-market_data.risk_free_rate * time_to_expiry)
        if self.fixed_rate is not None:
            total_fixed_payments = self.fixed_rate * time_to_expiry * self.notional
            fixed_leg_pv = total_fixed_payments * np.exp(-market_data.risk_free_rate * time_to_expiry)
        else:
            fixed_leg_pv = self.notional * (market_data.risk_free_rate + self.floating_rate_spread) * time_to_expiry
            fixed_leg_pv *= np.exp(-market_data.risk_free_rate * time_to_expiry)
        fair_value = expected_equity_pv - fixed_leg_pv
        return PricingResult(fair_value=fair_value, calculation_details={'expected_equity_pv': expected_equity_pv, 'fixed_leg_pv': fixed_leg_pv, 'expected_equity_return': expected_equity_return, 'time_to_expiry': time_to_expiry})

def __init__(self, notional: float, equity_leg_return: str, fixed_rate: Optional[float]=None, floating_rate_spread: float=0.0, start_date: datetime=None, end_date: datetime=None, payment_frequency: float=0.25):
    self.notional = notional
    self.equity_leg_return = equity_leg_return
    self.fixed_rate = fixed_rate
    self.floating_rate_spread = floating_rate_spread
    self.start_date = start_date or datetime.now()
    self.end_date = end_date
    self.payment_frequency = payment_frequency
    ModelValidator.validate_positive(notional, 'notional')

class ForwardCommitmentPricingEngine(PricingEngine):
    """Unified pricing engine for forward commitments"""

    def __init__(self):
        self.carry_calculator = CarryArbitrageCalculator()

    def price(self, instrument: ForwardCommitment, market_data: MarketData) -> PricingResult:
        """Price forward commitment based on type"""
        if not self.validate_inputs(instrument, market_data):
            raise ValidationError('Invalid inputs for forward commitment pricing')
        if isinstance(instrument, EquityForward):
            return instrument.fair_value(market_data)
        elif isinstance(instrument, InterestRateForward):
            return instrument.fair_value(market_data)
        elif isinstance(instrument, FixedIncomeForward):
            return instrument.fair_value(market_data)
        else:
            raise ValueError(f'Unsupported forward commitment type: {type(instrument)}')

    def validate_inputs(self, instrument: ForwardCommitment, market_data: MarketData) -> bool:
        """Validate inputs for forward commitment pricing"""
        try:
            ModelValidator.validate_positive(market_data.spot_price, 'spot_price')
            ModelValidator.validate_rate(market_data.risk_free_rate, 'risk_free_rate')
            ModelValidator.validate_non_negative(market_data.dividend_yield, 'dividend_yield')
            if instrument.is_expired():
                logger.warning('Forward commitment has expired')
                return False
            return True
        except ValidationError:
            return False

def validate_inputs(self, instrument: ForwardCommitment, market_data: MarketData) -> bool:
    """Validate inputs for forward commitment pricing"""
    try:
        ModelValidator.validate_positive(market_data.spot_price, 'spot_price')
        ModelValidator.validate_rate(market_data.risk_free_rate, 'risk_free_rate')
        ModelValidator.validate_non_negative(market_data.dividend_yield, 'dividend_yield')
        if instrument.is_expired():
            logger.warning('Forward commitment has expired')
            return False
        return True
    except ValidationError:
        return False

class ConversionStrategy:
    """Conversion arbitrage strategy implementation"""

    def __init__(self, spot_price: float, strike_price: float, call_price: float, put_price: float, risk_free_rate: float, time_to_expiry: float, dividend_yield: float=0.0):
        self.spot_price = spot_price
        self.strike_price = strike_price
        self.call_price = call_price
        self.put_price = put_price
        self.risk_free_rate = risk_free_rate
        self.time_to_expiry = time_to_expiry
        self.dividend_yield = dividend_yield
        ModelValidator.validate_positive(spot_price, 'spot_price')
        ModelValidator.validate_positive(strike_price, 'strike_price')
        ModelValidator.validate_positive(call_price, 'call_price')
        ModelValidator.validate_positive(put_price, 'put_price')

    def detect_arbitrage(self) -> Optional[ArbitrageOpportunity]:
        """Detect conversion arbitrage opportunity"""
        pv_strike = self.strike_price * np.exp(-self.risk_free_rate * self.time_to_expiry)
        pv_spot = self.spot_price * np.exp(-self.dividend_yield * self.time_to_expiry)
        synthetic_call = self.put_price + pv_spot - pv_strike
        price_difference = self.call_price - synthetic_call
        if abs(price_difference) > Constants.EPSILON:
            if price_difference > 0:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.CONVERSION, direction=ArbitrageDirection.SELL_EXPENSIVE_BUY_CHEAP, profit_potential=abs(price_difference), confidence_level=0.95, instruments_involved=['call', 'put', 'stock', 'bond'], trade_details={'sell_call': self.call_price, 'buy_put': self.put_price, 'buy_stock': self.spot_price, 'sell_bond': pv_strike, 'net_profit': price_difference, 'synthetic_call_price': synthetic_call, 'actual_call_price': self.call_price}, risk_factors=['early_exercise', 'dividend_risk', 'interest_rate_risk'], execution_complexity='medium')
            else:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.REVERSAL, direction=ArbitrageDirection.BUY_CHEAP_SELL_EXPENSIVE, profit_potential=abs(price_difference), confidence_level=0.95, instruments_involved=['call', 'put', 'stock', 'bond'], trade_details={'buy_call': self.call_price, 'sell_put': self.put_price, 'sell_stock': self.spot_price, 'buy_bond': pv_strike, 'net_profit': abs(price_difference), 'synthetic_call_price': synthetic_call, 'actual_call_price': self.call_price}, risk_factors=['early_exercise', 'dividend_risk', 'interest_rate_risk'], execution_complexity='medium')
        return None

def __init__(self, spot_price: float, strike_price: float, call_price: float, put_price: float, risk_free_rate: float, time_to_expiry: float, dividend_yield: float=0.0):
    self.spot_price = spot_price
    self.strike_price = strike_price
    self.call_price = call_price
    self.put_price = put_price
    self.risk_free_rate = risk_free_rate
    self.time_to_expiry = time_to_expiry
    self.dividend_yield = dividend_yield
    ModelValidator.validate_positive(spot_price, 'spot_price')
    ModelValidator.validate_positive(strike_price, 'strike_price')
    ModelValidator.validate_positive(call_price, 'call_price')
    ModelValidator.validate_positive(put_price, 'put_price')

class ReversalStrategy:
    """Reversal arbitrage strategy implementation"""

    def __init__(self, spot_price: float, strike_price: float, call_price: float, put_price: float, risk_free_rate: float, time_to_expiry: float, dividend_yield: float=0.0):
        self.spot_price = spot_price
        self.strike_price = strike_price
        self.call_price = call_price
        self.put_price = put_price
        self.risk_free_rate = risk_free_rate
        self.time_to_expiry = time_to_expiry
        self.dividend_yield = dividend_yield
        ModelValidator.validate_positive(spot_price, 'spot_price')
        ModelValidator.validate_positive(strike_price, 'strike_price')
        ModelValidator.validate_positive(call_price, 'call_price')
        ModelValidator.validate_positive(put_price, 'put_price')

    def detect_arbitrage(self) -> Optional[ArbitrageOpportunity]:
        """Detect reversal arbitrage opportunity"""
        pv_strike = self.strike_price * np.exp(-self.risk_free_rate * self.time_to_expiry)
        pv_spot = self.spot_price * np.exp(-self.dividend_yield * self.time_to_expiry)
        synthetic_put = self.call_price + pv_strike - pv_spot
        price_difference = self.put_price - synthetic_put
        if abs(price_difference) > Constants.EPSILON:
            if price_difference > 0:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.REVERSAL, direction=ArbitrageDirection.SELL_EXPENSIVE_BUY_CHEAP, profit_potential=abs(price_difference), confidence_level=0.95, instruments_involved=['call', 'put', 'stock', 'bond'], trade_details={'buy_call': self.call_price, 'sell_put': self.put_price, 'sell_stock': self.spot_price, 'buy_bond': pv_strike, 'net_profit': price_difference, 'synthetic_put_price': synthetic_put, 'actual_put_price': self.put_price}, risk_factors=['early_exercise', 'dividend_risk', 'interest_rate_risk'], execution_complexity='medium')
            else:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.CONVERSION, direction=ArbitrageDirection.BUY_CHEAP_SELL_EXPENSIVE, profit_potential=abs(price_difference), confidence_level=0.95, instruments_involved=['call', 'put', 'stock', 'bond'], trade_details={'sell_call': self.call_price, 'buy_put': self.put_price, 'buy_stock': self.spot_price, 'sell_bond': pv_strike, 'net_profit': abs(price_difference), 'synthetic_put_price': synthetic_put, 'actual_put_price': self.put_price}, risk_factors=['early_exercise', 'dividend_risk', 'interest_rate_risk'], execution_complexity='medium')
        return None

def __init__(self, spot_price: float, strike_price: float, call_price: float, put_price: float, risk_free_rate: float, time_to_expiry: float, dividend_yield: float=0.0):
    self.spot_price = spot_price
    self.strike_price = strike_price
    self.call_price = call_price
    self.put_price = put_price
    self.risk_free_rate = risk_free_rate
    self.time_to_expiry = time_to_expiry
    self.dividend_yield = dividend_yield
    ModelValidator.validate_positive(spot_price, 'spot_price')
    ModelValidator.validate_positive(strike_price, 'strike_price')
    ModelValidator.validate_positive(call_price, 'call_price')
    ModelValidator.validate_positive(put_price, 'put_price')

class CarryArbitrageDetector:
    """Detect carry arbitrage opportunities in forwards/futures"""

    def __init__(self, spot_price: float, forward_price: float, risk_free_rate: float, time_to_expiry: float, dividend_yield: float=0.0, storage_cost: float=0.0, convenience_yield: float=0.0):
        self.spot_price = spot_price
        self.forward_price = forward_price
        self.risk_free_rate = risk_free_rate
        self.time_to_expiry = time_to_expiry
        self.dividend_yield = dividend_yield
        self.storage_cost = storage_cost
        self.convenience_yield = convenience_yield
        ModelValidator.validate_positive(spot_price, 'spot_price')
        ModelValidator.validate_positive(forward_price, 'forward_price')

    def detect_arbitrage(self) -> Optional[ArbitrageOpportunity]:
        """Detect carry arbitrage opportunity"""
        carry_rate = self.risk_free_rate - self.dividend_yield + self.storage_cost - self.convenience_yield
        theoretical_forward = self.spot_price * np.exp(carry_rate * self.time_to_expiry)
        price_difference = self.forward_price - theoretical_forward
        if abs(price_difference) > Constants.EPSILON:
            arbitrage_profit = abs(price_difference) * np.exp(-self.risk_free_rate * self.time_to_expiry)
            if price_difference > 0:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.CARRY_ARBITRAGE, direction=ArbitrageDirection.SELL_EXPENSIVE_BUY_CHEAP, profit_potential=arbitrage_profit, confidence_level=0.9, instruments_involved=['forward', 'underlying', 'bond'], trade_details={'sell_forward': self.forward_price, 'buy_underlying': self.spot_price, 'borrow_funds': self.spot_price, 'theoretical_forward': theoretical_forward, 'price_difference': price_difference, 'carry_rate': carry_rate, 'dividend_yield': self.dividend_yield, 'storage_cost': self.storage_cost, 'convenience_yield': self.convenience_yield}, risk_factors=['storage_costs', 'convenience_yield', 'dividend_changes', 'interest_rate_risk'], execution_complexity='medium')
            else:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.CARRY_ARBITRAGE, direction=ArbitrageDirection.BUY_CHEAP_SELL_EXPENSIVE, profit_potential=arbitrage_profit, confidence_level=0.9, instruments_involved=['forward', 'underlying', 'bond'], trade_details={'buy_forward': self.forward_price, 'sell_underlying': self.spot_price, 'invest_proceeds': self.spot_price, 'theoretical_forward': theoretical_forward, 'price_difference': price_difference, 'carry_rate': carry_rate, 'dividend_yield': self.dividend_yield, 'storage_cost': self.storage_cost, 'convenience_yield': self.convenience_yield}, risk_factors=['storage_costs', 'convenience_yield', 'dividend_changes', 'interest_rate_risk'], execution_complexity='medium')
        return None

def __init__(self, spot_price: float, forward_price: float, risk_free_rate: float, time_to_expiry: float, dividend_yield: float=0.0, storage_cost: float=0.0, convenience_yield: float=0.0):
    self.spot_price = spot_price
    self.forward_price = forward_price
    self.risk_free_rate = risk_free_rate
    self.time_to_expiry = time_to_expiry
    self.dividend_yield = dividend_yield
    self.storage_cost = storage_cost
    self.convenience_yield = convenience_yield
    ModelValidator.validate_positive(spot_price, 'spot_price')
    ModelValidator.validate_positive(forward_price, 'forward_price')

class VolatilityArbitrageDetector:
    """Detect volatility arbitrage opportunities"""

    def __init__(self, market_vol: float, implied_vol: float, option: VanillaOption, market_data: MarketData, confidence_threshold: float=0.05):
        self.market_vol = market_vol
        self.implied_vol = implied_vol
        self.option = option
        self.market_data = market_data
        self.confidence_threshold = confidence_threshold
        ModelValidator.validate_volatility(market_vol)
        ModelValidator.validate_volatility(implied_vol)

    def detect_arbitrage(self) -> Optional[ArbitrageOpportunity]:
        """Detect volatility arbitrage based on vol differential"""
        vol_difference = self.implied_vol - self.market_vol
        vol_spread_pct = abs(vol_difference) / self.market_vol
        if vol_spread_pct > self.confidence_threshold:
            market_data_market_vol = MarketData(spot_price=self.market_data.spot_price, risk_free_rate=self.market_data.risk_free_rate, dividend_yield=self.market_data.dividend_yield, volatility=self.market_vol, time_to_expiry=self.market_data.time_to_expiry)
            engine = BlackScholesPricingEngine()
            market_vol_price = engine.price(self.option, market_data_market_vol).fair_value
            market_data_implied_vol = MarketData(spot_price=self.market_data.spot_price, risk_free_rate=self.market_data.risk_free_rate, dividend_yield=self.market_data.dividend_yield, volatility=self.implied_vol, time_to_expiry=self.market_data.time_to_expiry)
            implied_vol_price = engine.price(self.option, market_data_implied_vol).fair_value
            price_difference = implied_vol_price - market_vol_price
            if vol_difference > 0:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.VOLATILITY_ARBITRAGE, direction=ArbitrageDirection.SELL_EXPENSIVE_BUY_CHEAP, profit_potential=abs(price_difference), confidence_level=min(0.95, vol_spread_pct * 5), instruments_involved=['option', 'underlying'], trade_details={'sell_option': implied_vol_price, 'market_vol': self.market_vol, 'implied_vol': self.implied_vol, 'vol_difference': vol_difference, 'price_difference': price_difference, 'strategy': 'sell_option_delta_hedge', 'vol_spread_pct': vol_spread_pct, 'market_vol_price': market_vol_price, 'implied_vol_price': implied_vol_price}, risk_factors=['gamma_risk', 'vol_risk', 'time_decay', 'model_risk'], execution_complexity='high')
            else:
                return ArbitrageOpportunity(arbitrage_type=ArbitrageType.VOLATILITY_ARBITRAGE, direction=ArbitrageDirection.BUY_CHEAP_SELL_EXPENSIVE, profit_potential=abs(price_difference), confidence_level=min(0.95, vol_spread_pct * 5), instruments_involved=['option', 'underlying'], trade_details={'buy_option': implied_vol_price, 'market_vol': self.market_vol, 'implied_vol': self.implied_vol, 'vol_difference': vol_difference, 'price_difference': price_difference, 'strategy': 'buy_option_delta_hedge', 'vol_spread_pct': vol_spread_pct, 'market_vol_price': market_vol_price, 'implied_vol_price': implied_vol_price}, risk_factors=['gamma_risk', 'vol_risk', 'time_decay', 'model_risk'], execution_complexity='high')
        return None

def __init__(self, market_vol: float, implied_vol: float, option: VanillaOption, market_data: MarketData, confidence_threshold: float=0.05):
    self.market_vol = market_vol
    self.implied_vol = implied_vol
    self.option = option
    self.market_data = market_data
    self.confidence_threshold = confidence_threshold
    ModelValidator.validate_volatility(market_vol)
    ModelValidator.validate_volatility(implied_vol)

@dataclass
class YieldCurvePoint:
    """Single point on yield curve"""
    maturity: float
    rate: float
    instrument_type: str = 'government'

    def __post_init__(self):
        ModelValidator.validate_non_negative(self.maturity, 'maturity')
        ModelValidator.validate_rate(self.rate, 'interest rate')

def __post_init__(self):
    ModelValidator.validate_non_negative(self.maturity, 'maturity')
    ModelValidator.validate_rate(self.rate, 'interest rate')

@dataclass
class VolatilitySurfacePoint:
    """Single point on volatility surface"""
    strike: float
    time_to_expiry: float
    implied_volatility: float
    delta: Optional[float] = None

    def __post_init__(self):
        ModelValidator.validate_positive(self.strike, 'strike')
        ModelValidator.validate_non_negative(self.time_to_expiry, 'time_to_expiry')
        ModelValidator.validate_volatility(self.implied_volatility)

def __post_init__(self):
    ModelValidator.validate_positive(self.strike, 'strike')
    ModelValidator.validate_non_negative(self.time_to_expiry, 'time_to_expiry')
    ModelValidator.validate_volatility(self.implied_volatility)

@dataclass
class MarketSnapshot:
    """Complete market data snapshot for pricing"""
    timestamp: datetime
    spot_price: float
    risk_free_rate: float
    dividend_yield: float = 0.0
    repo_rate: Optional[float] = None
    borrow_cost: Optional[float] = None
    yield_curve: Optional[List[YieldCurvePoint]] = None
    volatility_surface: Optional[List[VolatilitySurfacePoint]] = None
    bid_ask_spread: Optional[float] = None

    def __post_init__(self):
        ModelValidator.validate_positive(self.spot_price, 'spot_price')
        ModelValidator.validate_rate(self.risk_free_rate, 'risk_free_rate')
        ModelValidator.validate_non_negative(self.dividend_yield, 'dividend_yield')

def __post_init__(self):
    ModelValidator.validate_positive(self.spot_price, 'spot_price')
    ModelValidator.validate_rate(self.risk_free_rate, 'risk_free_rate')
    ModelValidator.validate_non_negative(self.dividend_yield, 'dividend_yield')

class ManualDataProvider(MarketDataProvider):
    """Manual data input provider for custom scenarios"""

    def __init__(self):
        super().__init__(DataProvider.MANUAL)
        self.data_cache = {}
        self.connection_status = True

    def connect(self, **kwargs) -> bool:
        self.connection_status = True
        return True

    def disconnect(self) -> bool:
        self.connection_status = False
        return True

    def set_spot_price(self, symbol: str, price: float):
        """Manually set spot price"""
        ModelValidator.validate_positive(price, f'spot price for {symbol}')
        self.data_cache[f'spot_{symbol}'] = price
        self.last_update = datetime.now()

    def set_risk_free_rate(self, rate: float, currency: str='USD', maturity: float=0.25):
        """Manually set risk-free rate"""
        ModelValidator.validate_rate(rate, f'risk-free rate for {currency}')
        self.data_cache[f'rf_{currency}_{maturity}'] = rate
        self.last_update = datetime.now()

    def set_dividend_yield(self, symbol: str, yield_rate: float):
        """Manually set dividend yield"""
        ModelValidator.validate_non_negative(yield_rate, f'dividend yield for {symbol}')
        self.data_cache[f'div_{symbol}'] = yield_rate
        self.last_update = datetime.now()

    def set_volatility(self, symbol: str, volatility: float, maturity: float=None, strike: float=None):
        """Manually set volatility"""
        ModelValidator.validate_volatility(volatility)
        key = f'vol_{symbol}'
        if maturity is not None:
            key += f'_{maturity}'
        if strike is not None:
            key += f'_{strike}'
        self.data_cache[key] = volatility
        self.last_update = datetime.now()

    def get_spot_price(self, symbol: str) -> float:
        key = f'spot_{symbol}'
        if key not in self.data_cache:
            raise ValueError(f'No spot price data for symbol: {symbol}')
        return self.data_cache[key]

    def get_risk_free_rate(self, currency: str='USD', maturity: float=0.25) -> float:
        key = f'rf_{currency}_{maturity}'
        if key not in self.data_cache:
            default_key = f'rf_{currency}_0.25'
            if default_key in self.data_cache:
                return self.data_cache[default_key]
            return 0.02
        return self.data_cache[key]

    def get_dividend_yield(self, symbol: str) -> float:
        key = f'div_{symbol}'
        return self.data_cache.get(key, 0.0)

    def get_volatility(self, symbol: str, maturity: float, strike: float=None) -> float:
        key = f'vol_{symbol}_{maturity}'
        if strike is not None:
            key += f'_{strike}'
        if key in self.data_cache:
            return self.data_cache[key]
        key_no_strike = f'vol_{symbol}_{maturity}'
        if key_no_strike in self.data_cache:
            return self.data_cache[key_no_strike]
        generic_key = f'vol_{symbol}'
        if generic_key in self.data_cache:
            return self.data_cache[generic_key]
        return 0.2

    def get_yield_curve(self, currency: str, curve_type: str='government') -> CurveData:
        """Get yield curve (simplified for manual input)"""
        curve = CurveData(curve_date=datetime.now(), curve_type=curve_type, currency=currency, day_count=DayCountConvention.ACT_365)
        default_rates = [(0.25, 0.02), (0.5, 0.022), (1.0, 0.025), (2.0, 0.028), (5.0, 0.032), (10.0, 0.035), (30.0, 0.038)]
        for maturity, rate in default_rates:
            rf_rate = self.get_risk_free_rate(currency, maturity)
            curve.add_point(maturity, rf_rate)
        return curve

def set_spot_price(self, symbol: str, price: float):
    """Manually set spot price"""
    ModelValidator.validate_positive(price, f'spot price for {symbol}')
    self.data_cache[f'spot_{symbol}'] = price
    self.last_update = datetime.now()

def set_risk_free_rate(self, rate: float, currency: str='USD', maturity: float=0.25):
    """Manually set risk-free rate"""
    ModelValidator.validate_rate(rate, f'risk-free rate for {currency}')
    self.data_cache[f'rf_{currency}_{maturity}'] = rate
    self.last_update = datetime.now()

def set_dividend_yield(self, symbol: str, yield_rate: float):
    """Manually set dividend yield"""
    ModelValidator.validate_non_negative(yield_rate, f'dividend yield for {symbol}')
    self.data_cache[f'div_{symbol}'] = yield_rate
    self.last_update = datetime.now()

def set_volatility(self, symbol: str, volatility: float, maturity: float=None, strike: float=None):
    """Manually set volatility"""
    ModelValidator.validate_volatility(volatility)
    key = f'vol_{symbol}'
    if maturity is not None:
        key += f'_{maturity}'
    if strike is not None:
        key += f'_{strike}'
    self.data_cache[key] = volatility
    self.last_update = datetime.now()

class WatchlistTab(BaseTab):
    """Bloomberg Terminal style Watchlist tab - Enhanced with DuckDB storage"""

    def __init__(self, main_app=None):
        logger.info('Initializing WatchlistTab')
        with operation('WatchlistTab initialization'):
            super().__init__(main_app)
            self.main_app = main_app
            self._init_colors()
            self.watchlist: Dict[str, Dict[str, Any]] = {}
            self.auto_update = True
            self.refresh_running = False
            self.selected_ticker: Optional[str] = None
            self._last_update_time = 0.0
            self._update_lock = threading.RLock()
            self._price_cache: Dict[str, Tuple[float, float]] = {}
            self._display_update_pending = False
            self.instance_id = str(id(self))
            self.db_path = self.get_config_directory() / 'watchlist' / DB_FILE
            self.db_connection = None
            self._initialize_database()
            self._initialize_data()
        logger.info('WatchlistTab initialization completed', context={'instance_id': self.instance_id})

    def get_config_directory(self) -> Path:
        """Get platform-specific config directory - uses .fincept folder"""
        config_dir = Path.home() / '.fincept' / 'watchlist'
        return config_dir

    def _init_colors(self):
        """Initialize Bloomberg color scheme - cached for performance"""
        self.BLOOMBERG_ORANGE = [255, 165, 0]
        self.BLOOMBERG_WHITE = [255, 255, 255]
        self.BLOOMBERG_RED = [255, 0, 0]
        self.BLOOMBERG_GREEN = [0, 200, 0]
        self.BLOOMBERG_YELLOW = [255, 255, 0]
        self.BLOOMBERG_GRAY = [120, 120, 120]

    def _initialize_database(self):
        """Initialize DuckDB database and create tables"""
        try:
            with operation('Database initialization'):
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                self.db_connection = duckdb.connect(str(self.db_path))
                self.db_connection.execute("\n                    CREATE TABLE IF NOT EXISTS watchlist (\n                        ticker VARCHAR PRIMARY KEY,\n                        quantity DOUBLE NOT NULL,\n                        avg_price DOUBLE NOT NULL,\n                        alert_price DOUBLE,\n                        current_price DOUBLE DEFAULT 0,\n                        change_1d DOUBLE DEFAULT 0,\n                        change_pct_1d DOUBLE DEFAULT 0,\n                        change_pct_7d DOUBLE DEFAULT 0,\n                        change_pct_30d DOUBLE DEFAULT 0,\n                        last_updated VARCHAR DEFAULT '',\n                        total_value DOUBLE DEFAULT 0,\n                        unrealized_pnl DOUBLE DEFAULT 0,\n                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n                    )\n                ")
                self.db_connection.execute('\n                    CREATE TABLE IF NOT EXISTS settings (\n                        key VARCHAR PRIMARY KEY,\n                        value VARCHAR,\n                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n                    )\n                ')
                self.db_connection.execute('\n                    CREATE TABLE IF NOT EXISTS price_history (\n                        ticker VARCHAR,\n                        price DOUBLE,\n                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                        PRIMARY KEY (ticker, timestamp)\n                    )\n                ')
                logger.info('Database initialized successfully', context={'db_path': str(self.db_path)})
        except Exception as e:
            logger.error('Failed to initialize database', context={'error': str(e), 'db_path': str(self.db_path)}, exc_info=True)
            raise

    def _initialize_data(self):
        """Initialize watchlist data from database"""
        with operation('Data initialization'):
            self.load_watchlist_from_database()

    def get_label(self) -> str:
        return 'Watchlist'

    def _round_currency(self, value: float) -> float:
        """Round currency values to 2 decimal places consistently"""
        if value is None:
            return 0.0
        return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    def _round_percentage(self, value: float) -> float:
        """Round percentage values to 4 decimal places for precision"""
        if value is None:
            return 0.0
        return float(Decimal(str(value)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))

    def _safe_float(self, value, default=0.0) -> float:
        """Safely convert value to float with default fallback"""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def load_watchlist_from_database(self):
        """Load watchlist from DuckDB database with proper precision and validation"""
        try:
            with operation('Load watchlist from database'):
                if not self.db_connection:
                    logger.error('Database connection not available')
                    return
                result = self.db_connection.execute('SELECT * FROM watchlist').fetchall()
                columns = [desc[0] for desc in self.db_connection.description]
                self.watchlist.clear()
                if result:
                    for row in result:
                        row_dict = dict(zip(columns, row))
                        ticker = row_dict['ticker']
                        quantity = self._safe_float(row_dict.get('quantity'), 0.0)
                        avg_price = self._safe_float(row_dict.get('avg_price'), 0.0)
                        alert_price = self._safe_float(row_dict.get('alert_price')) if row_dict.get('alert_price') is not None else None
                        current_price = self._safe_float(row_dict.get('current_price'))
                        if current_price == 0.0 and avg_price > 0.0:
                            current_price = avg_price
                        change_1d = self._safe_float(row_dict.get('change_1d'), 0.0)
                        change_pct_1d = self._safe_float(row_dict.get('change_pct_1d'), 0.0)
                        change_pct_7d = self._safe_float(row_dict.get('change_pct_7d'), 0.0)
                        change_pct_30d = self._safe_float(row_dict.get('change_pct_30d'), 0.0)
                        last_updated = row_dict.get('last_updated') or ''
                        if isinstance(last_updated, datetime.datetime):
                            last_updated = last_updated.strftime('%H:%M:%S')
                        total_value = self._round_currency(current_price * quantity) if quantity > 0 else 0.0
                        unrealized_pnl = self._round_currency((current_price - avg_price) * quantity) if abs(avg_price) > 1e-10 and quantity > 0 else 0.0
                        if quantity <= 0:
                            logger.warning(f'Invalid quantity for {ticker}: {quantity}, skipping')
                            continue
                        if avg_price < 0:
                            logger.warning(f'Invalid avg_price for {ticker}: {avg_price}, skipping')
                            continue
                        self.watchlist[ticker] = {'quantity': quantity, 'avg_price': self._round_currency(avg_price), 'alert_price': self._round_currency(alert_price) if alert_price is not None else None, 'current_price': self._round_currency(current_price), 'change_1d': self._round_currency(change_1d), 'change_pct_1d': self._round_percentage(change_pct_1d), 'change_pct_7d': self._round_percentage(change_pct_7d), 'change_pct_30d': self._round_percentage(change_pct_30d), 'last_updated': str(last_updated), 'total_value': total_value, 'unrealized_pnl': unrealized_pnl}
                    logger.info('Watchlist loaded from database', context={'positions': len(self.watchlist)})
                else:
                    logger.info('No watchlist data found in database, initializing with sample data')
                    self.initialize_sample_watchlist()
        except Exception as e:
            logger.error('Error loading watchlist from database', context={'error': str(e)}, exc_info=True)
            self.initialize_sample_watchlist()

    @monitor_performance
    def save_watchlist_to_database(self):
        """Save watchlist data to DuckDB database"""
        try:
            if not self.db_connection:
                logger.error('Database connection not available')
                return
            with operation('Save watchlist to database'):
                current_timestamp = datetime.datetime.now()
                self.db_connection.execute('DELETE FROM watchlist')
                if self.watchlist:
                    data_rows = []
                    for ticker, data in self.watchlist.items():
                        data_rows.append((ticker, data['quantity'], data['avg_price'], data.get('alert_price'), data['current_price'], data['change_1d'], data['change_pct_1d'], data['change_pct_7d'], data['change_pct_30d'], data['last_updated'], data['total_value'], data['unrealized_pnl'], current_timestamp, current_timestamp))
                    self.db_connection.executemany('\n                        INSERT INTO watchlist (\n                            ticker, quantity, avg_price, alert_price, current_price,\n                            change_1d, change_pct_1d, change_pct_7d, change_pct_30d,\n                            last_updated, total_value, unrealized_pnl, created_at, updated_at\n                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                    ', data_rows)
                    logger.debug('Watchlist saved to database', context={'positions': len(self.watchlist)})
        except Exception as e:
            logger.error('Error saving watchlist to database', context={'error': str(e)}, exc_info=True)

    def get_setting(self, key: str, default: Any=None) -> Any:
        """Get setting value from database"""
        try:
            if not self.db_connection:
                return default
            result = self.db_connection.execute('SELECT value FROM settings WHERE key = ?', [key]).fetchone()
            return result[0] if result else default
        except Exception as e:
            logger.error('Error getting setting', context={'key': key, 'error': str(e)})
            return default

    def set_setting(self, key: str, value: str):
        """Set setting value in database"""
        try:
            if not self.db_connection:
                return
            self.db_connection.execute('\n                INSERT OR REPLACE INTO settings (key, value, updated_at) \n                VALUES (?, ?, CURRENT_TIMESTAMP)\n            ', [key, value])
        except Exception as e:
            logger.error('Error setting value', context={'key': key, 'error': str(e)})

    def _create_status_bar(self):
        """Create status bar"""
        try:
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_text('WATCHLIST STATUS:', color=self.BLOOMBERG_GRAY)
                dpg.add_text('ACTIVE', color=self.BLOOMBERG_GREEN)
                dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                dpg.add_text('POSITIONS:', color=self.BLOOMBERG_GRAY)
                dpg.add_text(f'{len(self.watchlist)}', color=self.BLOOMBERG_YELLOW, tag=self.get_tag('status_positions'))
                dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                dpg.add_text('AUTO-UPDATE:', color=self.BLOOMBERG_GRAY)
                status_text = 'ON' if self.auto_update else 'OFF'
                status_color = self.BLOOMBERG_GREEN if self.auto_update else self.BLOOMBERG_RED
                dpg.add_text(status_text, color=status_color, tag=self.get_tag('auto_status'))
                dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                dpg.add_text('SELECTED:', color=self.BLOOMBERG_GRAY)
                dpg.add_text('None', color=self.BLOOMBERG_GRAY, tag=self.get_tag('selected_ticker_text'))
        except Exception as e:
            logger.error('Error creating status bar', context={'error': str(e)}, exc_info=True)

    def reset_watchlist(self, sender, app_data):
        """Reset watchlist to default"""
        try:
            with operation('Reset watchlist'):
                self.watchlist.clear()
                if self.db_connection:
                    self.db_connection.execute('DELETE FROM watchlist')
                    self.db_connection.execute('DELETE FROM settings')
                    self.db_connection.execute('DELETE FROM price_history')
                self.initialize_sample_watchlist()
                self.update_display()
                self.calculate_portfolio_metrics.cache_clear()
                logger.info('Watchlist reset to default')
        except Exception as e:
            logger.error('Error resetting watchlist', context={'error': str(e)}, exc_info=True)

    def portfolio_report(self, sender, app_data):
        """Generate portfolio report"""
        try:
            with operation('Generate portfolio report'):
                total_value, total_pnl, day_pnl = self.calculate_portfolio_metrics()
                report = ['\n=== PORTFOLIO REPORT ===', f'Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', f'Total Positions: {len(self.watchlist)}', f'Total Value: ${total_value:,.2f}', f'Unrealized P&L: ${total_pnl:+,.2f}', f'Day P&L: ${day_pnl:+,.2f}', '========================\n']
                report_text = '\n'.join(report)
                print(report_text)
                logger.info('Portfolio report generated', context={'total_value': total_value, 'positions': len(self.watchlist)})
        except Exception as e:
            logger.error('Error generating portfolio report', context={'error': str(e)}, exc_info=True)

    def redirect_to_equity_research(self, ticker: str):
        """Redirect to Equity Research tab with selected ticker - MINIMAL IMPLEMENTATION"""
        try:
            logger.info('Redirecting to Equity Research tab', context={'ticker': ticker})
            if self.main_app and hasattr(self.main_app, 'switch_to_tab_with_ticker'):
                success = self.main_app.switch_to_tab_with_ticker('Equity Research', ticker)
                if success:
                    logger.info(f'Successfully redirected to Equity Research with {ticker}')
                else:
                    logger.warning(f'Failed to redirect to Equity Research with {ticker}')
            else:
                logger.warning('Cannot redirect: main_app not properly configured')
        except Exception as e:
            logger.error('Error redirecting to Equity Research tab', context={'ticker': ticker, 'error': str(e)}, exc_info=True)

    @monitor_performance
    def add_ticker_to_watchlist(self, ticker: str, quantity: float, avg_price: float, alert_price: Optional[float]):
        """Add a ticker to the watchlist with optimized data structure"""
        try:
            with self._update_lock:
                current_price = avg_price if avg_price > 0 else 100.0
                current_time = datetime.datetime.now().strftime('%H:%M:%S')
                total_value = current_price * quantity
                unrealized_pnl = (current_price - avg_price) * quantity if avg_price > 0 else 0
                self.watchlist[ticker] = {'quantity': quantity, 'avg_price': avg_price, 'alert_price': alert_price, 'current_price': current_price, 'change_1d': random.uniform(-5, 5), 'change_pct_1d': random.uniform(-3, 3), 'change_pct_7d': random.uniform(-8, 8), 'change_pct_30d': random.uniform(-20, 20), 'last_updated': current_time, 'total_value': round(total_value, 2), 'unrealized_pnl': round(unrealized_pnl, 2)}
                self.calculate_portfolio_metrics.cache_clear()
                self.save_watchlist_to_database()
                self.update_display()
                if HAS_YFINANCE:
                    threading.Thread(target=self.fetch_single_price, args=(ticker,), daemon=True).start()
        except Exception as e:
            logger.error('Error adding ticker to watchlist', context={'ticker': ticker, 'error': str(e)}, exc_info=True)

    def remove_ticker_from_watchlist(self, ticker: str):
        """Remove a ticker from the watchlist"""
        try:
            with self._update_lock:
                if ticker in self.watchlist:
                    del self.watchlist[ticker]
                if self.db_connection:
                    self.db_connection.execute('DELETE FROM watchlist WHERE ticker = ?', [ticker])
                self.calculate_portfolio_metrics.cache_clear()
                self.update_display()
                self.selected_ticker = None
                selected_tag = self.get_tag('selected_ticker_text')
                if dpg.does_item_exist(selected_tag):
                    dpg.set_value(selected_tag, 'None')
                logger.info('Ticker removed from watchlist', context={'ticker': ticker})
        except Exception as e:
            logger.error('Error removing ticker from watchlist', context={'ticker': ticker, 'error': str(e)}, exc_info=True)

    def fetch_single_price(self, ticker: str):
        """Fetch price for a single ticker with caching and retry logic"""
        if not HAS_YFINANCE:
            return
        current_time = time.time()
        if ticker in self._price_cache:
            cached_price, cached_time = self._price_cache[ticker]
            if current_time - cached_time < 60:
                return
        retries = 0
        while retries < MAX_RETRIES:
            try:
                with operation(f'Fetch price for {ticker}'):
                    stock = yf.Ticker(ticker)
                    data = stock.history(period='30d', interval='1d')
                    if data.empty:
                        raise ValueError('No data available')
                    last_price = float(data['Close'].iloc[-1])
                    self._price_cache[ticker] = (last_price, current_time)
                    if self.db_connection:
                        self.db_connection.execute('\n                            INSERT INTO price_history (ticker, price, timestamp) \n                            VALUES (?, ?, CURRENT_TIMESTAMP)\n                        ', [ticker, last_price])
                    if len(data) >= 2:
                        prev_price = float(data['Close'].iloc[-2])
                        change = last_price - prev_price
                        change_pct = change / prev_price * 100 if abs(prev_price) > 1e-10 else 0.0
                        change_pct = self._round_percentage(change_pct)
                    else:
                        change = 0.0
                        change_pct = 0.0
                    with self._update_lock:
                        if ticker in self.watchlist:
                            data_entry = self.watchlist[ticker]
                            avg_price = data_entry['avg_price']
                            quantity = data_entry['quantity']
                            data_entry.update({'current_price': round(last_price, 2), 'change_1d': round(change, 2), 'change_pct_1d': round(change_pct, 2), 'last_updated': datetime.datetime.now().strftime('%H:%M:%S'), 'total_value': round(last_price * quantity, 2), 'unrealized_pnl': self._round_currency((last_price - avg_price) * quantity) if abs(avg_price) > 1e-10 else 0.0})
                            if not self._display_update_pending:
                                self._display_update_pending = True
                                threading.Timer(0.5, self._batch_update_display).start()
                    logger.debug('Price fetched successfully', context={'ticker': ticker, 'price': last_price})
                    return
            except Exception as e:
                retries += 1
                logger.warning(f'Error fetching price for {ticker} (attempt {retries})', context={'error': str(e)})
                if retries < MAX_RETRIES:
                    time.sleep(REQUEST_DELAY * retries)
        logger.error(f'Failed to fetch price for {ticker} after {MAX_RETRIES} attempts')

    def _batch_update_display(self):
        """Batch update display to reduce UI refresh frequency"""
        try:
            self._display_update_pending = False
            self.calculate_portfolio_metrics.cache_clear()
            self.update_display()
        except Exception as e:
            logger.error('Error in batch display update', context={'error': str(e)})

    @monitor_performance
    def refresh_all_prices_sync(self):
        """Refresh all prices synchronously with rate limiting"""
        if not self.watchlist:
            return
        try:
            with operation('Refresh all prices'):
                tickers = list(self.watchlist.keys())
                logger.info('Starting price refresh', context={'ticker_count': len(tickers)})
                for i, ticker in enumerate(tickers):
                    self.fetch_single_price(ticker)
                    if i < len(tickers) - 1:
                        time.sleep(REQUEST_DELAY)
                self.save_watchlist_to_database()
                logger.info('Price refresh completed')
        except Exception as e:
            logger.error('Error refreshing all prices', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def update_watchlist_data(self):
        """Update watchlist data with simulated changes - fixed precision"""
        try:
            with self._update_lock:
                current_time = datetime.datetime.now().strftime('%H:%M:%S')
                ticker_count = len(self.watchlist)
                if ticker_count == 0:
                    return
                change_factors = [1 + random.uniform(-PRICE_CHANGE_LIMIT, PRICE_CHANGE_LIMIT) for _ in range(ticker_count)]
                for i, ticker in enumerate(self.watchlist):
                    data = self.watchlist[ticker]
                    old_price = data['current_price']
                    new_price = self._round_currency(old_price * change_factors[i])
                    new_change_1d = self._round_currency(new_price - old_price)
                    new_change_pct_1d = 0.0
                    if abs(old_price) > 1e-10:
                        new_change_pct_1d = self._round_percentage(new_change_1d / old_price * 100)
                    quantity = data['quantity']
                    avg_price = data['avg_price']
                    new_total_value = self._round_currency(new_price * quantity)
                    new_unrealized_pnl = 0.0
                    if abs(avg_price) > 1e-10:
                        new_unrealized_pnl = self._round_currency((new_price - avg_price) * quantity)
                    base_change = new_change_pct_1d
                    weekly_factor = random.uniform(3.0, 7.0)
                    monthly_factor = random.uniform(8.0, 15.0)
                    new_change_pct_7d = self._round_percentage(base_change * weekly_factor + random.uniform(-2, 2))
                    new_change_pct_30d = self._round_percentage(base_change * monthly_factor + random.uniform(-5, 5))
                    self.watchlist[ticker].update({'current_price': new_price, 'change_1d': new_change_1d, 'change_pct_1d': new_change_pct_1d, 'change_pct_7d': new_change_pct_7d, 'change_pct_30d': new_change_pct_30d, 'last_updated': current_time, 'total_value': new_total_value, 'unrealized_pnl': new_unrealized_pnl})
                self._update_time_displays(current_time)
                logger.debug('Watchlist data updated with precision', context={'ticker_count': ticker_count})
        except Exception as e:
            logger.error('Error updating watchlist data', context={'error': str(e)}, exc_info=True)

    def _update_time_displays(self, current_time: str):
        """Update time displays efficiently"""
        time_tags = [('last_update_time', current_time), ('watchlist_time', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))]
        for tag_name, time_value in time_tags:
            tag = self.get_tag(tag_name)
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, time_value)

    @monitor_performance
    def update_display(self):
        """Update all display elements with optimizations"""
        try:
            with operation('Update display'):
                self.populate_watchlist_table()
                total_value, total_pnl, day_pnl = self.calculate_portfolio_metrics()
                metrics_updates = [('total_value_text', f'TOTAL VALUE: ${total_value:,.2f}', self.BLOOMBERG_WHITE), ('total_pnl_text', f'UNREALIZED P&L: ${total_pnl:+,.2f}', self.BLOOMBERG_GREEN if total_pnl >= 0 else self.BLOOMBERG_RED), ('day_pnl_text', f'DAY P&L: ${day_pnl:+,.2f}', self.BLOOMBERG_GREEN if day_pnl >= 0 else self.BLOOMBERG_RED), ('positions_count', f'POSITIONS: {len(self.watchlist)}', self.BLOOMBERG_YELLOW), ('status_positions', f'{len(self.watchlist)}', self.BLOOMBERG_YELLOW)]
                for tag_name, text, color in metrics_updates:
                    tag = self.get_tag(tag_name)
                    if dpg.does_item_exist(tag):
                        dpg.set_value(tag, text)
                        if color:
                            dpg.configure_item(tag, color=color)
                self.update_top_holdings(total_value)
        except Exception as e:
            logger.error('Error updating display', context={'error': str(e)}, exc_info=True)

    def start_auto_update(self):
        """Start auto-update thread with improved error handling"""

        def update_loop():
            logger.info('Auto-update loop started')
            while self.auto_update:
                try:
                    time.sleep(UPDATE_INTERVAL)
                    if not self.auto_update:
                        break
                    current_time = time.time()
                    if current_time - self._last_update_time < UPDATE_INTERVAL - 0.5:
                        continue
                    self._last_update_time = current_time
                    if HAS_YFINANCE:
                        self.refresh_all_prices_sync()
                    else:
                        self.update_watchlist_data()
                        self.update_display()
                except Exception as e:
                    logger.error('Error in auto-update loop', context={'error': str(e)}, exc_info=True)
                    time.sleep(UPDATE_INTERVAL)
            logger.info('Auto-update loop stopped')
        if self.auto_update and (not self.refresh_running):
            self.refresh_running = True
            update_thread = threading.Thread(target=update_loop, daemon=True, name=f'WatchlistUpdate-{self.instance_id}')
            update_thread.start()
            logger.info('Auto-update thread started', context={'thread_name': update_thread.name})

    @monitor_performance
    def cleanup(self):
        """Clean up resources with comprehensive error handling"""
        try:
            logger.info('Starting watchlist tab cleanup')
            self.auto_update = False
            self.refresh_running = False
            self.save_watchlist_to_database()
            if self.db_connection:
                self.db_connection.close()
                self.db_connection = None
            self.get_tag.cache_clear()
            self.calculate_portfolio_metrics.cache_clear()
            self._price_cache.clear()
            self.cleanup_existing_items()
            with self._update_lock:
                self.watchlist.clear()
                self.selected_ticker = None
            logger.info('Watchlist tab cleanup completed successfully')
        except Exception as e:
            logger.error('Error during cleanup', context={'error': str(e)}, exc_info=True)

    def initialize_sample_watchlist(self):
        """Initialize with optimized sample watchlist data"""
        sample_stocks = {'AAPL': {'quantity': 100, 'avg_price': 150.25}, 'MSFT': {'quantity': 50, 'avg_price': 305.8}, 'GOOGL': {'quantity': 25, 'avg_price': 2650.4}, 'TSLA': {'quantity': 75, 'avg_price': 220.15}, 'AMZN': {'quantity': 30, 'avg_price': 3280.75}, 'NVDA': {'quantity': 40, 'avg_price': 450.6}, 'META': {'quantity': 60, 'avg_price': 315.9}, 'NFLX': {'quantity': 20, 'avg_price': 485.3}}
        random_changes = [random.uniform(-0.15, 0.15) for _ in range(len(sample_stocks))]
        random_1d = [random.uniform(-0.03, 0.03) for _ in range(len(sample_stocks))]
        random_7d = [random.uniform(-8, 8) for _ in range(len(sample_stocks))]
        random_30d = [random.uniform(-20, 20) for _ in range(len(sample_stocks))]
        current_time = datetime.datetime.now().strftime('%H:%M:%S')
        for i, (ticker, data) in enumerate(sample_stocks.items()):
            avg_price = data['avg_price']
            current_price = avg_price * (1 + random_changes[i])
            change_1d = current_price * random_1d[i]
            change_pct_1d = change_1d / current_price * 100
            quantity = data['quantity']
            self.watchlist[ticker] = {'quantity': quantity, 'avg_price': avg_price, 'alert_price': None, 'current_price': round(current_price, 2), 'change_1d': round(change_1d, 2), 'change_pct_1d': round(change_pct_1d, 2), 'change_pct_7d': round(random_7d[i], 2), 'change_pct_30d': round(random_30d[i], 2), 'last_updated': current_time, 'total_value': round(current_price * quantity, 2), 'unrealized_pnl': round((current_price - avg_price) * quantity, 2)}
        self.save_watchlist_to_database()

    @lru_cache(maxsize=128)
    def get_tag(self, base_name: str) -> str:
        """Generate unique tag for this instance - cached for performance"""
        return f'{base_name}_{self.instance_id}'

    def create_content(self):
        """Create Bloomberg-style watchlist terminal layout"""
        logger.info('Creating watchlist UI content')
        try:
            with operation('UI Content Creation'):
                self.cleanup_existing_items()
                self._create_header()
                self._create_control_panel()
                self._create_main_area()
                self._create_status_bar()
                if self.auto_update:
                    self.start_auto_update()
            logger.info('Watchlist UI content created successfully')
        except Exception as e:
            logger.error('Error creating watchlist content', context={'error': str(e)}, exc_info=True)
            dpg.add_text('WATCHLIST TERMINAL', color=self.BLOOMBERG_ORANGE)
            dpg.add_text(f'Error loading watchlist: {e}')

    def _create_header(self):
        """Create top header bar"""
        with dpg.group(horizontal=True):
            dpg.add_text('FINCEPT', color=self.BLOOMBERG_ORANGE)
            dpg.add_text('WATCHLIST TERMINAL', color=self.BLOOMBERG_WHITE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_input_text(default_value='', hint='Add Symbol', width=150, tag=self.get_tag('add_symbol_input'), uppercase=True)
            dpg.add_input_text(default_value='', hint='Qty', width=80, tag=self.get_tag('add_qty_input'), decimal=True)
            dpg.add_input_text(default_value='', hint='Avg Price', width=100, tag=self.get_tag('add_price_input'), decimal=True)
            dpg.add_input_text(default_value='', hint='Alert Price', width=100, tag=self.get_tag('add_alert_input'), decimal=True)
            dpg.add_button(label='ADD', width=60, callback=self.add_to_watchlist_callback)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), tag=self.get_tag('watchlist_time'))
        dpg.add_separator()

    def _create_control_panel(self):
        """Create control panel"""
        with dpg.group(horizontal=True):
            dpg.add_button(label='REFRESH', width=80, callback=self.refresh_all_callback)
            dpg.add_button(label='REMOVE', width=80, callback=self.remove_ticker_callback)
            dpg.add_button(label='AUTO ON', tag=self.get_tag('auto_toggle_btn'), width=80, callback=self.toggle_auto_update)
            dpg.add_button(label='CHART', width=80, callback=self.show_chart_callback)
            dpg.add_button(label='INFO', width=80, callback=self.show_info_callback)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('LAST UPDATE:', color=self.BLOOMBERG_GRAY)
            dpg.add_text(datetime.datetime.now().strftime('%H:%M:%S'), tag=self.get_tag('last_update_time'), color=self.BLOOMBERG_WHITE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('LIVE', color=self.BLOOMBERG_GREEN)
        dpg.add_separator()

    def _create_main_area(self):
        """Create main area with watchlist and summary panels"""
        with dpg.group(horizontal=True):
            self.create_watchlist_panel()
            self.create_summary_panel()

    def cleanup_existing_items(self):
        """Clean up any existing items that might cause tag conflicts"""
        cleanup_tags = ['add_symbol_input', 'add_qty_input', 'add_price_input', 'add_alert_input', 'watchlist_time', 'auto_toggle_btn', 'last_update_time', 'watchlist_table', 'total_value_text', 'total_pnl_text', 'day_pnl_text', 'positions_count', 'top_holdings_group', 'status_positions', 'auto_status', 'selected_ticker_text']
        for tag in cleanup_tags:
            unique_tag = self.get_tag(tag)
            if dpg.does_item_exist(unique_tag):
                try:
                    dpg.delete_item(unique_tag)
                except Exception as e:
                    logger.debug('Failed to delete item', context={'tag': unique_tag, 'error': str(e)})

    def create_watchlist_panel(self):
        """Create watchlist table panel"""
        with dpg.child_window(width=1000, height=550, border=True):
            dpg.add_text('PORTFOLIO WATCHLIST', color=self.BLOOMBERG_ORANGE)
            dpg.add_separator()
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, scrollY=True, height=480, tag=self.get_tag('watchlist_table')):
                columns = [('Symbol', 80), ('Qty', 70), ('Avg Price', 90), ('Current', 90), ('Chg', 70), ('Chg%', 70), ('7D%', 70), ('30D%', 70), ('Total Value', 110), ('P&L', 90), ('Alert', 80)]
                for label, width in columns:
                    dpg.add_table_column(label=label, width_fixed=True, init_width_or_weight=width)
                self.populate_watchlist_table()

    def view_selected_details_callback(self, sender, app_data):
        """Callback for view selected details button"""
        if not self.selected_ticker:
            logger.warning('View details failed: no ticker selected')
            return
        self.redirect_to_equity_research(self.selected_ticker)

    def create_summary_panel(self):
        """Create portfolio summary panel"""
        with dpg.child_window(width=450, height=550, border=True):
            dpg.add_text('PORTFOLIO SUMMARY', color=self.BLOOMBERG_ORANGE)
            dpg.add_separator()
            total_value, total_pnl, day_pnl = self.calculate_portfolio_metrics()
            dpg.add_text(f'TOTAL VALUE: ${total_value:,.2f}', color=self.BLOOMBERG_WHITE, tag=self.get_tag('total_value_text'))
            pnl_color = self.BLOOMBERG_GREEN if total_pnl >= 0 else self.BLOOMBERG_RED
            dpg.add_text(f'UNREALIZED P&L: ${total_pnl:+,.2f}', color=pnl_color, tag=self.get_tag('total_pnl_text'))
            day_color = self.BLOOMBERG_GREEN if day_pnl >= 0 else self.BLOOMBERG_RED
            dpg.add_text(f'DAY P&L: ${day_pnl:+,.2f}', color=day_color, tag=self.get_tag('day_pnl_text'))
            dpg.add_text(f'POSITIONS: {len(self.watchlist)}', color=self.BLOOMBERG_YELLOW, tag=self.get_tag('positions_count'))
            dpg.add_separator()
            dpg.add_text('TOP HOLDINGS', color=self.BLOOMBERG_YELLOW)
            with dpg.group(tag=self.get_tag('top_holdings_group')):
                self.update_top_holdings(total_value)
            dpg.add_separator()
            dpg.add_text('MARKET ALERTS', color=self.BLOOMBERG_YELLOW)
            dpg.add_text('System: Ready', color=self.BLOOMBERG_GREEN)
            if HAS_YFINANCE:
                dpg.add_text('Data: Live Feed', color=self.BLOOMBERG_GREEN)
            else:
                dpg.add_text('Data: Simulated', color=self.BLOOMBERG_ORANGE)
            dpg.add_text('Status: Active', color=self.BLOOMBERG_WHITE)
            dpg.add_separator()
            dpg.add_text('QUICK ACTIONS', color=self.BLOOMBERG_YELLOW)
            dpg.add_button(label='VIEW SELECTED DETAILS', width=-1, callback=self.view_selected_details_callback)
            dpg.add_spacer(height=5)
            dpg.add_button(label='EXPORT PORTFOLIO', width=-1, callback=self.export_portfolio)
            dpg.add_spacer(height=5)
            dpg.add_button(label='RESET WATCHLIST', width=-1, callback=self.reset_watchlist)
            dpg.add_spacer(height=5)
            dpg.add_button(label='PORTFOLIO REPORT', width=-1, callback=self.portfolio_report)

    def update_top_holdings(self, total_value: float):
        """Update top holdings display with performance optimization - FIXED"""
        try:
            holdings_tag = self.get_tag('top_holdings_group')
            if not dpg.does_item_exist(holdings_tag):
                logger.warning(f'Holdings group does not exist: {holdings_tag}')
                return
            try:
                children = dpg.get_item_children(holdings_tag, slot=1)
                if children:
                    for child in children:
                        try:
                            if dpg.does_item_exist(child):
                                dpg.delete_item(child)
                        except Exception as delete_error:
                            logger.debug(f'Failed to delete child item {child}: {delete_error}')
            except Exception as clear_error:
                logger.debug(f'Error clearing holdings: {clear_error}')
            if total_value > 0 and self.watchlist:
                try:
                    sorted_holdings = sorted(self.watchlist.items(), key=lambda x: x[1]['total_value'], reverse=True)[:6]
                    for ticker, data in sorted_holdings:
                        try:
                            if not dpg.does_item_exist(holdings_tag):
                                logger.warning(f'Holdings group disappeared: {holdings_tag}')
                                break
                            percentage = data['total_value'] / total_value * 100
                            dpg.add_text(f'{ticker}: ${data['total_value']:,.0f} ({percentage:.1f}%)', color=self.BLOOMBERG_WHITE, parent=holdings_tag)
                        except Exception as add_error:
                            logger.debug(f'Failed to add holding text for {ticker}: {add_error}')
                            continue
                except Exception as sort_error:
                    logger.error(f'Error sorting holdings: {sort_error}')
        except Exception as e:
            logger.error(f'Error in update_top_holdings: {e}', exc_info=True)

    def create_status_bar(self):
        """Create status bar"""
        with dpg.group(horizontal=True):
            dpg.add_text('WATCHLIST STATUS:', color=self.BLOOMBERG_GRAY)
            dpg.add_text('ACTIVE', color=self.BLOOMBERG_GREEN)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('POSITIONS:', color=self.BLOOMBERG_GRAY)
            dpg.add_text(f'{len(self.watchlist)}', color=self.BLOOMBERG_YELLOW, tag=self.get_tag('status_positions'))
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('AUTO-UPDATE:', color=self.BLOOMBERG_GRAY)
            status_text = 'ON' if self.auto_update else 'OFF'
            status_color = self.BLOOMBERG_GREEN if self.auto_update else self.BLOOMBERG_RED
            dpg.add_text(status_text, color=status_color, tag=self.get_tag('auto_status'))
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('SELECTED:', color=self.BLOOMBERG_GRAY)
            dpg.add_text('None', color=self.BLOOMBERG_GRAY, tag=self.get_tag('selected_ticker_text'))

    @monitor_performance
    def populate_watchlist_table(self):
        """Populate the watchlist table with current data - optimized with clickable symbols"""
        table_tag = None
        try:
            table_tag = self.get_tag('watchlist_table')
            if not dpg.does_item_exist(table_tag):
                logger.warning('Watchlist table does not exist', context={'table_tag': table_tag})
                return
            try:
                dpg.get_item_info(table_tag)
            except Exception as info_error:
                logger.warning(f'Table tag invalid: {table_tag}, error: {info_error}')
                return
            try:
                children = dpg.get_item_children(table_tag, slot=1)
                if children:
                    for child in children:
                        try:
                            if dpg.does_item_exist(child):
                                dpg.delete_item(child)
                        except Exception as delete_error:
                            logger.debug('Failed to delete table child', context={'child': child, 'error': str(delete_error)})
            except Exception as clear_error:
                logger.debug(f'Error clearing table: {clear_error}')
            sorted_tickers = sorted(self.watchlist.keys())
            for ticker in sorted_tickers:
                try:
                    if not dpg.does_item_exist(table_tag):
                        logger.warning(f'Table disappeared during population: {table_tag}')
                        break
                    data = self.watchlist[ticker]
                    with dpg.table_row(parent=table_tag):
                        try:
                            symbol_selectable = dpg.add_selectable(label=ticker, span_columns=False, callback=self.on_ticker_selected, user_data=ticker)
                            try:
                                with dpg.tooltip(symbol_selectable):
                                    dpg.add_text(f'Click {ticker} to view detailed analysis')
                                    dpg.add_text('→ Opens in Equity Research tab', color=self.BLOOMBERG_YELLOW)
                            except Exception as tooltip_error:
                                logger.debug(f'Failed to add tooltip for {ticker}: {tooltip_error}')
                        except Exception as symbol_error:
                            logger.debug(f'Failed to add symbol selectable for {ticker}: {symbol_error}')
                            try:
                                dpg.add_text(ticker, color=self.BLOOMBERG_WHITE)
                            except Exception as fallback_error:
                                logger.debug(f'Failed to add fallback text for {ticker}: {fallback_error}')
                        try:
                            dpg.add_text(f'{data['quantity']:,}', color=self.BLOOMBERG_WHITE)
                        except Exception as qty_error:
                            logger.debug(f'Failed to add quantity for {ticker}: {qty_error}')
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                        try:
                            dpg.add_text(f'${data['avg_price']:.2f}', color=self.BLOOMBERG_GRAY)
                        except Exception as avg_error:
                            logger.debug(f'Failed to add avg_price for {ticker}: {avg_error}')
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                        try:
                            dpg.add_text(f'${data['current_price']:.2f}', color=self.BLOOMBERG_WHITE)
                        except Exception as price_error:
                            logger.debug(f'Failed to add current_price for {ticker}: {price_error}')
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                        try:
                            change_color = self.BLOOMBERG_GREEN if data['change_1d'] >= 0 else self.BLOOMBERG_RED
                            dpg.add_text(f'${data['change_1d']:+.2f}', color=change_color)
                        except Exception as change_error:
                            logger.debug(f'Failed to add change_1d for {ticker}: {change_error}')
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                        try:
                            pct_color = self.BLOOMBERG_GREEN if data['change_pct_1d'] >= 0 else self.BLOOMBERG_RED
                            dpg.add_text(f'{data['change_pct_1d']:+.2f}%', color=pct_color)
                        except Exception as pct_error:
                            logger.debug(f'Failed to add change_pct_1d for {ticker}: {pct_error}')
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                        try:
                            pct_7d_color = self.BLOOMBERG_GREEN if data['change_pct_7d'] >= 0 else self.BLOOMBERG_RED
                            dpg.add_text(f'{data['change_pct_7d']:+.2f}%', color=pct_7d_color)
                        except Exception as pct_7d_error:
                            logger.debug(f'Failed to add change_pct_7d for {ticker}: {pct_7d_error}')
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                        try:
                            pct_30d_color = self.BLOOMBERG_GREEN if data['change_pct_30d'] >= 0 else self.BLOOMBERG_RED
                            dpg.add_text(f'{data['change_pct_30d']:+.2f}%', color=pct_30d_color)
                        except Exception as pct_30d_error:
                            logger.debug(f'Failed to add change_pct_30d for {ticker}: {pct_30d_error}')
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                        try:
                            dpg.add_text(f'${data['total_value']:,.2f}', color=self.BLOOMBERG_WHITE)
                        except Exception as total_error:
                            logger.debug(f'Failed to add total_value for {ticker}: {total_error}')
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                        try:
                            pnl_color = self.BLOOMBERG_GREEN if data['unrealized_pnl'] >= 0 else self.BLOOMBERG_RED
                            dpg.add_text(f'${data['unrealized_pnl']:+,.2f}', color=pnl_color)
                        except Exception as pnl_error:
                            logger.debug(f'Failed to add unrealized_pnl for {ticker}: {pnl_error}')
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                        try:
                            alert_text = f'${data['alert_price']:.2f}' if data['alert_price'] else ''
                            dpg.add_text(alert_text, color=self.BLOOMBERG_YELLOW)
                        except Exception as alert_error:
                            logger.debug(f'Failed to add alert_price for {ticker}: {alert_error}')
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                except Exception as row_error:
                    logger.debug(f'Error adding row for {ticker}: {row_error}')
                    try:
                        if dpg.does_item_exist(table_tag):
                            with dpg.table_row(parent=table_tag):
                                dpg.add_text(f'ERROR: {ticker}', color=self.BLOOMBERG_RED)
                                for _ in range(10):
                                    dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                    except Exception as error_row_error:
                        logger.debug(f'Failed to create error row for {ticker}: {error_row_error}')
                    continue
            logger.debug('Watchlist table populated successfully', context={'ticker_count': len(sorted_tickers)})
        except Exception as e:
            logger.error('Error populating watchlist table', context={'error': str(e)}, exc_info=True)
            if table_tag and dpg.does_item_exist(table_tag):
                try:
                    with dpg.table_row(parent=table_tag):
                        dpg.add_text('CRITICAL ERROR', color=self.BLOOMBERG_RED)
                        for _ in range(10):
                            dpg.add_text('--', color=self.BLOOMBERG_GRAY)
                except Exception as fallback_error:
                    logger.error('Failed to create critical error row', context={'error': str(fallback_error)})

    def on_ticker_selected(self, sender, app_data, user_data):
        """Handle ticker selection with proper data passing"""
        ticker = user_data
        if ticker:
            logger.debug(f'Ticker selected via callback: {ticker}')
            self.select_ticker(ticker)
        else:
            logger.warning('No ticker data received in callback')

    @lru_cache(maxsize=1)
    def calculate_portfolio_metrics(self) -> Tuple[float, float, float]:
        """Calculate portfolio summary metrics with high precision"""
        try:
            if not self.watchlist:
                return (0.0, 0.0, 0.0)
            total_value_decimal = Decimal('0')
            total_pnl_decimal = Decimal('0')
            day_pnl_decimal = Decimal('0')
            for ticker, data in self.watchlist.items():
                current_price = Decimal(str(data['current_price']))
                avg_price = Decimal(str(data['avg_price']))
                quantity = Decimal(str(data['quantity']))
                change_1d = Decimal(str(data['change_1d']))
                position_value = current_price * quantity
                position_pnl = (current_price - avg_price) * quantity
                position_day_pnl = change_1d * quantity
                total_value_decimal += position_value
                total_pnl_decimal += position_pnl
                day_pnl_decimal += position_day_pnl
            total_value = self._round_currency(float(total_value_decimal))
            total_pnl = self._round_currency(float(total_pnl_decimal))
            day_pnl = self._round_currency(float(day_pnl_decimal))
            return (total_value, total_pnl, day_pnl)
        except Exception as e:
            logger.error('Error calculating portfolio metrics', context={'error': str(e)})
            return (0.0, 0.0, 0.0)

    def select_ticker(self, ticker: str):
        """Select a ticker from the table and redirect to Equity Research tab"""
        self.selected_ticker = ticker
        selected_tag = self.get_tag('selected_ticker_text')
        if dpg.does_item_exist(selected_tag):
            dpg.set_value(selected_tag, ticker)
        logger.debug('Ticker selected', context={'ticker': ticker})
        self.redirect_to_equity_research(ticker)

    def add_to_watchlist_callback(self, sender, app_data):
        """Callback for add to watchlist button"""
        try:
            with operation('Add ticker to watchlist'):
                ticker = dpg.get_value(self.get_tag('add_symbol_input')).strip().upper()
                quantity_str = dpg.get_value(self.get_tag('add_qty_input')).strip()
                avg_price_str = dpg.get_value(self.get_tag('add_price_input')).strip()
                alert_str = dpg.get_value(self.get_tag('add_alert_input')).strip()
                if not ticker:
                    logger.warning('Add ticker failed: empty ticker symbol')
                    return
                if ticker in self.watchlist:
                    logger.warning('Add ticker failed: ticker already exists', context={'ticker': ticker})
                    return
                try:
                    quantity = float(quantity_str) if quantity_str else 1.0
                    avg_price = float(avg_price_str) if avg_price_str else 100.0
                    alert_price = float(alert_str) if alert_str else None
                except ValueError:
                    logger.warning('Add ticker failed: invalid numeric values')
                    return
                self.add_ticker_to_watchlist(ticker, quantity, avg_price, alert_price)
                for tag in ['add_symbol_input', 'add_qty_input', 'add_price_input', 'add_alert_input']:
                    dpg.set_value(self.get_tag(tag), '')
                logger.info('Ticker added to watchlist', context={'ticker': ticker, 'quantity': quantity})
        except Exception as e:
            logger.error('Error in add_to_watchlist_callback', context={'error': str(e)}, exc_info=True)

    def remove_ticker_callback(self, sender, app_data):
        """Callback for remove ticker button"""
        if not self.selected_ticker:
            logger.warning('Remove ticker failed: no ticker selected')
            return
        with operation('Remove ticker from watchlist'):
            self.remove_ticker_from_watchlist(self.selected_ticker)

    def refresh_all_callback(self, sender, app_data):
        """Callback for refresh all button"""
        logger.info('Manual refresh requested')
        with operation('Manual refresh all'):
            if HAS_YFINANCE:
                threading.Thread(target=self.refresh_all_prices_sync, daemon=True).start()
            else:
                self.update_watchlist_data()
                self.update_display()

    def toggle_auto_update(self, sender, app_data):
        """Toggle auto-update on/off"""
        self.auto_update = not self.auto_update
        auto_btn_tag = self.get_tag('auto_toggle_btn')
        if dpg.does_item_exist(auto_btn_tag):
            dpg.set_item_label(auto_btn_tag, 'AUTO ON' if self.auto_update else 'AUTO OFF')
        auto_status_tag = self.get_tag('auto_status')
        if dpg.does_item_exist(auto_status_tag):
            status_text = 'ON' if self.auto_update else 'OFF'
            status_color = self.BLOOMBERG_GREEN if self.auto_update else self.BLOOMBERG_RED
            dpg.set_value(auto_status_tag, status_text)
            dpg.configure_item(auto_status_tag, color=status_color)
        if self.auto_update and (not self.refresh_running):
            self.start_auto_update()
        elif not self.auto_update:
            self.refresh_running = False
        logger.info('Auto-update toggled', context={'enabled': self.auto_update})

    def show_chart_callback(self, sender, app_data):
        """Callback for show chart button"""
        if not self.selected_ticker:
            logger.warning('Chart request failed: no ticker selected')
            return
        logger.info('Chart requested', context={'ticker': self.selected_ticker})

    def show_info_callback(self, sender, app_data):
        """Callback for show info button"""
        if not self.selected_ticker:
            logger.warning('Info request failed: no ticker selected')
            return
        logger.info('Info requested', context={'ticker': self.selected_ticker})

    @monitor_performance
    def export_portfolio(self, sender, app_data):
        """Export portfolio to DuckDB file or CSV"""
        try:
            with operation('Export portfolio'):
                if not self.db_connection:
                    logger.error('Database connection not available for export')
                    return
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_filename = f'portfolio_export_{timestamp}.csv'
                export_query = "\n                    COPY (\n                        SELECT \n                            ticker,\n                            quantity,\n                            avg_price,\n                            current_price,\n                            (current_price - avg_price) * quantity as unrealized_pnl,\n                            current_price * quantity as total_value,\n                            change_pct_1d,\n                            change_pct_7d,\n                            change_pct_30d,\n                            last_updated,\n                            created_at\n                        FROM watchlist\n                        ORDER BY total_value DESC\n                    ) TO ? WITH (HEADER, DELIMITER ',')\n                "
                self.db_connection.execute(export_query, [csv_filename])
                total_value, total_pnl, day_pnl = self.calculate_portfolio_metrics()
                summary_filename = f'portfolio_summary_{timestamp}.txt'
                with open(summary_filename, 'w') as f:
                    f.write('=== PORTFOLIO EXPORT SUMMARY ===\n')
                    f.write(f'Export Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
                    f.write(f'Total Positions: {len(self.watchlist)}\n')
                    f.write(f'Total Value: ${total_value:,.2f}\n')
                    f.write(f'Unrealized P&L: ${total_pnl:+,.2f}\n')
                    f.write(f'Day P&L: ${day_pnl:+,.2f}\n')
                    f.write('================================\n')
                    f.write(f'Detailed data exported to: {csv_filename}\n')
                logger.info('Portfolio exported successfully', context={'csv_file': csv_filename, 'summary_file': summary_filename})
        except Exception as e:
            logger.error('Error exporting portfolio', context={'error': str(e)}, exc_info=True)

    def resize_components(self, left_width, center_width, right_width, top_height, bottom_height, cell_height):
        """Handle resize events - optimized to do minimal work"""
        pass

def _round_currency(self, value: float) -> float:
    """Round currency values to 2 decimal places consistently"""
    if value is None:
        return 0.0
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def _round_percentage(self, value: float) -> float:
    """Round percentage values to 4 decimal places for precision"""
    if value is None:
        return 0.0
    return float(Decimal(str(value)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))

def _safe_float(self, value, default=0.0) -> float:
    """Safely convert value to float with default fallback"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

class PortfolioBusinessLogic:
    """Business logic for Portfolio Management - separated from UI"""

    def __init__(self):
        self.price_cache = {}
        self.last_price_update = {}
        self.price_fetch_errors = {}
        self.daily_change_cache = {}
        self.previous_close_cache = {}
        self.refresh_thread = None
        self.refresh_running = False
        self.price_update_interval = 3600
        self.initial_price_fetch_done = False
        self.portfolios = self.load_portfolios()
        self.current_portfolio = None
        self.country_suffixes = self._get_country_suffixes()
        self._portfolio_value_cache = {}
        self._portfolio_investment_cache = {}
        self._cache_timeout = 30
        self._last_cache_update = {}
        self.csv_data = None
        self.csv_headers = []
        self.column_mapping = {}
        self.csv_preview_data = []
        self.csv_file_path = None
        self.initialize_sample_data()
        self.fetch_initial_prices()

    def _get_country_suffixes(self):
        """Get country suffix mapping - cached"""
        return {'India': '.NS', 'United States': '', 'United Kingdom': '.L', 'Germany': '.DE', 'Japan': '.T', 'Australia': '.AX', 'Canada': '.TO', 'France': '.PA', 'Hong Kong': '.HK', 'South Korea': '.KS'}

    def initialize_sample_data(self):
        """Initialize sample portfolio data for demonstration"""
        if not self.portfolios:
            self.portfolios = {'Tech Growth': {'AAPL': {'quantity': 50, 'avg_price': 150.25, 'last_added': '2024-01-15'}, 'MSFT': {'quantity': 30, 'avg_price': 280.75, 'last_added': '2024-01-10'}, 'GOOGL': {'quantity': 25, 'avg_price': 125.5, 'last_added': '2024-01-05'}, 'NVDA': {'quantity': 20, 'avg_price': 450.3, 'last_added': '2024-01-20'}}, 'Dividend Income': {'JNJ': {'quantity': 100, 'avg_price': 160.8, 'last_added': '2024-01-12'}, 'PG': {'quantity': 75, 'avg_price': 145.2, 'last_added': '2024-01-08'}, 'KO': {'quantity': 150, 'avg_price': 58.9, 'last_added': '2024-01-18'}}}
            self.save_portfolios()

    @monitor_performance
    def fetch_initial_prices(self):
        """Fetch initial prices for all stocks in portfolios"""
        threading.Thread(target=self._fetch_initial_prices_worker, daemon=True).start()

    def _fetch_initial_prices_worker(self):
        """Background worker to fetch initial prices"""
        try:
            with operation('initial_price_fetch'):
                logger.info('Fetching initial stock prices...')
                all_symbols = set()
                for portfolio in self.portfolios.values():
                    for symbol in portfolio.keys():
                        all_symbols.add(symbol)
                if not all_symbols:
                    logger.info('No stocks found in portfolios')
                    self.initial_price_fetch_done = True
                    return
                self._fetch_prices_batch(list(all_symbols))
                self.initial_price_fetch_done = True
                logger.info(f'Initial price fetch completed for {len(all_symbols)} symbols', context={'symbols_count': len(all_symbols)})
        except Exception as e:
            logger.error(f'Error in initial price fetch: {e}', exc_info=True)
            self.initial_price_fetch_done = True

    @monitor_performance
    def _fetch_prices_batch(self, symbols):
        """Fetch prices for a batch of symbols - optimized"""
        max_workers = min(10, len(symbols))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {executor.submit(self._fetch_single_price, symbol): symbol for symbol in symbols}
            for future in as_completed(future_to_symbol, timeout=60):
                symbol = future_to_symbol[future]
                try:
                    price = future.result(timeout=30)
                    if price is not None:
                        self.price_cache[symbol] = price
                        self.last_price_update[symbol] = datetime.datetime.now()
                        self.price_fetch_errors.pop(symbol, None)
                        logger.debug(f'Price updated: {symbol} = ${price:.2f}')
                    else:
                        self.price_fetch_errors[symbol] = 'No price data available'
                        logger.warning(f'No price data available for {symbol}')
                except Exception as e:
                    self.price_fetch_errors[symbol] = str(e)
                    logger.error(f'Error fetching price for {symbol}: {e}')
                time.sleep(0.1)

    def _fetch_single_price(self, symbol):
        """Fetch price and daily change data for a single symbol using yfinance - optimized"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price_fields = ['regularMarketPrice', 'currentPrice', 'previousClose', 'regularMarketPreviousClose']
            current_price = None
            previous_close = None
            for field in price_fields:
                if field in info and info[field] is not None:
                    current_price = float(info[field])
                    if current_price > 0:
                        break
            prev_close_fields = ['regularMarketPreviousClose', 'previousClose']
            for field in prev_close_fields:
                if field in info and info[field] is not None:
                    previous_close = float(info[field])
                    if previous_close > 0:
                        break
            if current_price is None or previous_close is None:
                hist = ticker.history(period='2d', interval='1d')
                if not hist.empty and len(hist) >= 2:
                    if current_price is None:
                        current_price = float(hist['Close'].iloc[-1])
                    if previous_close is None:
                        previous_close = float(hist['Close'].iloc[-2])
                elif not hist.empty:
                    if current_price is None:
                        current_price = float(hist['Close'].iloc[-1])
                    if previous_close is None:
                        previous_close = current_price
            if current_price is not None and previous_close is not None and (previous_close > 0):
                daily_change = current_price - previous_close
                daily_change_pct = daily_change / previous_close * 100
                self.previous_close_cache[symbol] = previous_close
                self.daily_change_cache[symbol] = {'change': daily_change, 'change_pct': daily_change_pct}
                return current_price
            return current_price
        except Exception as e:
            logger.error(f'Error fetching price for {symbol}: {e}')
            return None

    @lru_cache(maxsize=128)
    def get_daily_change(self, symbol):
        """Get today's change for a symbol - cached"""
        if symbol in self.daily_change_cache:
            return self.daily_change_cache[symbol]
        current_price = self.get_current_price(symbol)
        previous_close = self.previous_close_cache.get(symbol)
        if current_price and previous_close and (previous_close > 0):
            daily_change = current_price - previous_close
            daily_change_pct = daily_change / previous_close * 100
            return {'change': daily_change, 'change_pct': daily_change_pct}
        return {'change': 0.0, 'change_pct': 0.0}

    def calculate_portfolio_daily_change(self, portfolio_name):
        """Calculate total daily change for a portfolio - cached"""
        cache_key = f'daily_change_{portfolio_name}'
        current_time = time.time()
        if cache_key in self._last_cache_update and current_time - self._last_cache_update[cache_key] < self._cache_timeout:
            if cache_key in self._portfolio_value_cache:
                return self._portfolio_value_cache[cache_key]
        portfolio = self.portfolios.get(portfolio_name, {})
        total_change = 0.0
        total_previous_value = 0.0
        for symbol, data in portfolio.items():
            if isinstance(data, dict):
                quantity = data.get('quantity', 0)
                current_price = self.get_current_price(symbol)
                previous_close = self.previous_close_cache.get(symbol, current_price)
                current_value = quantity * current_price
                previous_value = quantity * previous_close
                holding_change = current_value - previous_value
                total_change += holding_change
                total_previous_value += previous_value
        change_pct = total_change / total_previous_value * 100 if total_previous_value > 0 else 0.0
        result = {'change': total_change, 'change_pct': change_pct}
        self._portfolio_value_cache[cache_key] = result
        self._last_cache_update[cache_key] = current_time
        return result

    def calculate_total_daily_change(self):
        """Calculate total daily change across all portfolios - cached"""
        cache_key = 'total_daily_change'
        current_time = time.time()
        if cache_key in self._last_cache_update and current_time - self._last_cache_update[cache_key] < self._cache_timeout:
            if cache_key in self._portfolio_value_cache:
                return self._portfolio_value_cache[cache_key]
        total_change = 0.0
        total_previous_value = 0.0
        for portfolio_name in self.portfolios.keys():
            portfolio_change = self.calculate_portfolio_daily_change(portfolio_name)
            portfolio_current_value = self.calculate_portfolio_value(portfolio_name)
            portfolio_previous_value = portfolio_current_value - portfolio_change['change']
            total_change += portfolio_change['change']
            total_previous_value += portfolio_previous_value
        change_pct = total_change / total_previous_value * 100 if total_previous_value > 0 else 0.0
        result = {'change': total_change, 'change_pct': change_pct}
        self._portfolio_value_cache[cache_key] = result
        self._last_cache_update[cache_key] = current_time
        return result

    @lru_cache(maxsize=256)
    def get_current_price(self, symbol):
        """Get current price from cache or return fallback price - cached"""
        if symbol in self.price_cache:
            return self.price_cache[symbol]
        if symbol in self.price_fetch_errors:
            for portfolio in self.portfolios.values():
                if symbol in portfolio and isinstance(portfolio[symbol], dict):
                    avg_price = portfolio[symbol].get('avg_price', 100)
                    logger.warning(f'Using avg_price ${avg_price:.2f} for {symbol} (fetch error)')
                    return avg_price
        logger.debug(f'Using default price $100.00 for {symbol}')
        return 100.0

    def calculate_portfolio_value(self, portfolio_name):
        """Calculate current portfolio value - cached"""
        cache_key = f'value_{portfolio_name}'
        current_time = time.time()
        if cache_key in self._last_cache_update and current_time - self._last_cache_update[cache_key] < self._cache_timeout:
            if cache_key in self._portfolio_value_cache:
                return self._portfolio_value_cache[cache_key]
        portfolio = self.portfolios.get(portfolio_name, {})
        total_value = 0
        for symbol, data in portfolio.items():
            if isinstance(data, dict):
                quantity = data.get('quantity', 0)
                current_price = self.get_current_price(symbol)
                total_value += quantity * current_price
        self._portfolio_value_cache[cache_key] = total_value
        self._last_cache_update[cache_key] = current_time
        return total_value

    def calculate_portfolio_investment(self, portfolio_name):
        """Calculate total portfolio investment - cached"""
        cache_key = f'investment_{portfolio_name}'
        current_time = time.time()
        if cache_key in self._last_cache_update and current_time - self._last_cache_update[cache_key] < self._cache_timeout:
            if cache_key in self._portfolio_investment_cache:
                return self._portfolio_investment_cache[cache_key]
        portfolio = self.portfolios.get(portfolio_name, {})
        total_investment = 0
        for symbol, data in portfolio.items():
            if isinstance(data, dict):
                quantity = data.get('quantity', 0)
                avg_price = data.get('avg_price', 0)
                total_investment += quantity * avg_price
        self._portfolio_investment_cache[cache_key] = total_investment
        self._last_cache_update[cache_key] = current_time
        return total_investment

    def get_portfolio_summary(self):
        """Get comprehensive portfolio summary"""
        total_portfolios = len(self.portfolios)
        total_investment = sum((self.calculate_portfolio_investment(name) for name in self.portfolios.keys()))
        total_value = sum((self.calculate_portfolio_value(name) for name in self.portfolios.keys()))
        total_pnl = total_value - total_investment
        total_pnl_pct = total_pnl / total_investment * 100 if total_investment > 0 else 0
        total_daily_change = self.calculate_total_daily_change()
        today_change = total_daily_change['change']
        today_change_pct = total_daily_change['change_pct']
        return {'total_portfolios': total_portfolios, 'total_investment': total_investment, 'total_value': total_value, 'total_pnl': total_pnl, 'total_pnl_pct': total_pnl_pct, 'today_change': today_change, 'today_change_pct': today_change_pct}

    def get_portfolio_breakdown(self):
        """Get detailed breakdown of all portfolios"""
        breakdown = []
        total_value = sum((self.calculate_portfolio_value(name) for name in self.portfolios.keys()))
        for portfolio_name, stocks in self.portfolios.items():
            portfolio_investment = self.calculate_portfolio_investment(portfolio_name)
            portfolio_value = self.calculate_portfolio_value(portfolio_name)
            portfolio_pnl = portfolio_value - portfolio_investment
            portfolio_pnl_pct = portfolio_pnl / portfolio_investment * 100 if portfolio_investment > 0 else 0
            allocation_pct = portfolio_value / total_value * 100 if total_value > 0 else 0
            portfolio_daily_change = self.calculate_portfolio_daily_change(portfolio_name)
            today_change = portfolio_daily_change['change']
            today_change_pct = portfolio_daily_change['change_pct']
            breakdown.append({'name': portfolio_name, 'stocks_count': len(stocks), 'investment': portfolio_investment, 'value': portfolio_value, 'pnl': portfolio_pnl, 'pnl_pct': portfolio_pnl_pct, 'today_change': today_change, 'today_change_pct': today_change_pct, 'allocation_pct': allocation_pct})
        return breakdown

    def get_portfolio_holdings(self, portfolio_name):
        """Get detailed holdings for a specific portfolio"""
        if portfolio_name not in self.portfolios:
            return []
        portfolio = self.portfolios[portfolio_name]
        portfolio_value = self.calculate_portfolio_value(portfolio_name)
        holdings = []
        for symbol, data in portfolio.items():
            if isinstance(data, dict):
                quantity = data.get('quantity', 0)
                avg_price = data.get('avg_price', 0)
                original_symbol = data.get('original_symbol', symbol)
                current_price = self.get_current_price(symbol)
                market_value = quantity * current_price
                investment = quantity * avg_price
                gain_loss = market_value - investment
                gain_loss_pct = gain_loss / investment * 100 if investment > 0 else 0
                weight_pct = market_value / portfolio_value * 100 if portfolio_value > 0 else 0
                holdings.append({'symbol': symbol, 'original_symbol': original_symbol, 'quantity': quantity, 'avg_price': avg_price, 'current_price': current_price, 'market_value': market_value, 'investment': investment, 'gain_loss': gain_loss, 'gain_loss_pct': gain_loss_pct, 'weight_pct': weight_pct})
        return holdings

    def create_portfolio(self, name, description=''):
        """Create a new portfolio"""
        if not name:
            raise ValueError('Please enter a portfolio name.')
        if name in self.portfolios:
            raise ValueError('Portfolio name already exists.')
        self.portfolios[name] = {}
        self.save_portfolios()
        self._clear_portfolio_cache()
        return True

    def create_portfolio_with_stock(self, name, symbol, quantity, price, description=''):
        """Create portfolio and add first stock"""
        if not name:
            raise ValueError('Please enter a portfolio name.')
        if name in self.portfolios:
            raise ValueError('Portfolio name already exists.')
        if symbol and quantity is not None and (price is not None):
            try:
                quantity = float(quantity)
                price = float(price)
                self.portfolios[name] = {symbol: {'quantity': quantity, 'avg_price': price, 'last_added': datetime.datetime.now().strftime('%Y-%m-%d')}}
                threading.Thread(target=lambda: self._fetch_single_price_and_update(symbol), daemon=True).start()
            except ValueError:
                raise ValueError('Invalid quantity or price values.')
        else:
            self.portfolios[name] = {}
        self.save_portfolios()
        self._clear_portfolio_cache()
        return True

    def add_stock_to_portfolio(self, portfolio_name, symbol, quantity, price):
        """Add stock to existing portfolio"""
        if not portfolio_name or portfolio_name not in self.portfolios:
            raise ValueError('Invalid portfolio selected.')
        if not symbol or quantity is None or price is None:
            raise ValueError('Please fill in all fields.')
        try:
            quantity = float(quantity)
            price = float(price)
        except ValueError:
            raise ValueError('Invalid quantity or price values.')
        if symbol in self.portfolios[portfolio_name]:
            existing = self.portfolios[portfolio_name][symbol]
            current_qty = existing['quantity']
            current_avg = existing['avg_price']
            new_qty = current_qty + quantity
            new_avg = (current_avg * current_qty + price * quantity) / new_qty
            self.portfolios[portfolio_name][symbol] = {'quantity': new_qty, 'avg_price': round(new_avg, 2), 'last_added': datetime.datetime.now().strftime('%Y-%m-%d')}
        else:
            self.portfolios[portfolio_name][symbol] = {'quantity': quantity, 'avg_price': price, 'last_added': datetime.datetime.now().strftime('%Y-%m-%d')}
        self.price_cache[symbol] = price * (1 + random.uniform(-0.05, 0.05))
        self.save_portfolios()
        self._clear_portfolio_cache()
        threading.Thread(target=lambda: self._fetch_single_price_and_update(symbol), daemon=True).start()
        return True

    def remove_stock_from_portfolio(self, portfolio_name, symbol):
        """Remove stock from portfolio"""
        if not portfolio_name or portfolio_name not in self.portfolios:
            raise ValueError('Portfolio not found')
        if symbol not in self.portfolios[portfolio_name]:
            raise ValueError('Stock not found in portfolio')
        del self.portfolios[portfolio_name][symbol]
        self.save_portfolios()
        self._clear_portfolio_cache()
        return True

    def delete_portfolio(self, portfolio_name):
        """Delete the specified portfolio"""
        if portfolio_name not in self.portfolios:
            raise ValueError('Portfolio not found')
        del self.portfolios[portfolio_name]
        self.save_portfolios()
        self._clear_portfolio_cache()
        if self.current_portfolio == portfolio_name:
            self.current_portfolio = None
        return True

    @monitor_performance
    def select_csv_file(self):
        """Open file dialog to select CSV file - optimized"""
        try:
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(title='Select Portfolio CSV File', filetypes=[('CSV files', '*.csv'), ('All files', '*.*')])
            root.destroy()
            if file_path:
                self.csv_file_path = file_path
                filename = os.path.basename(file_path)
                return filename
            else:
                return None
        except Exception as e:
            logger.error(f'Error selecting CSV file: {e}', exc_info=True)
            raise Exception('Error selecting file')

    @monitor_performance
    def analyze_csv_file(self):
        """Analyze the selected CSV file and return column info"""
        try:
            if not hasattr(self, 'csv_file_path'):
                raise ValueError('Please select a CSV file first')
            with operation('csv_analysis'):
                with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                    sample = file.read(1024)
                    file.seek(0)
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
                    reader = csv.reader(file, delimiter=delimiter)
                    rows = list(reader)
                if not rows:
                    raise ValueError('CSV file is empty')
                self.csv_headers = rows[0]
                self.csv_data = rows[1:] if len(rows) > 1 else []
                return {'headers': self.csv_headers, 'row_count': len(self.csv_data), 'columns_count': len(self.csv_headers)}
        except Exception as e:
            logger.error(f'Error analyzing CSV: {e}', exc_info=True)
            raise Exception(f'Error analyzing CSV: {str(e)}')

    @lru_cache(maxsize=64)
    def auto_detect_column(self, field_type):
        """Auto-detect CSV column based on common naming patterns - cached"""
        field_patterns = {'symbol': ['symbol', 'instrument', 'stock', 'ticker', 'scrip', 'name'], 'quantity': ['quantity', 'qty', 'shares', 'units', 'holding'], 'avg_price': ['avg', 'average', 'cost', 'price', 'purchase', 'buy'], 'current_price': ['ltp', 'current', 'market', 'last', 'trading'], 'investment': ['invested', 'investment', 'total_cost', 'amount'], 'current_value': ['current_value', 'market_value', 'value', 'cur'], 'pnl': ['pnl', 'p&l', 'profit', 'loss', 'gain', 'net']}
        patterns = field_patterns.get(field_type, [])
        for header in self.csv_headers:
            header_lower = header.lower().replace(' ', '_').replace('.', '').replace('-', '_')
            for pattern in patterns:
                if pattern in header_lower:
                    return header
        return ''

    @monitor_performance
    def preview_import(self, column_mapping, country_suffix):
        """Preview the import with current column mapping"""
        try:
            with operation('import_preview'):
                required_mappings = ['symbol', 'quantity', 'avg_price']
                self.column_mapping = {}
                for field in required_mappings:
                    mapped_column = column_mapping.get(field)
                    if not mapped_column:
                        raise ValueError(f'Please map the required field: {field}')
                    self.column_mapping[field] = mapped_column
                optional_mappings = ['current_price', 'investment', 'current_value', 'pnl']
                for field in optional_mappings:
                    mapped_column = column_mapping.get(field)
                    if mapped_column:
                        self.column_mapping[field] = mapped_column
                self.csv_preview_data = []
                for row in self.csv_data[:10]:
                    if len(row) >= len(self.csv_headers):
                        row_dict = dict(zip(self.csv_headers, row))
                        symbol = str(row_dict.get(self.column_mapping['symbol'], '')).strip()
                        if not symbol:
                            continue
                        if country_suffix and (not symbol.endswith(country_suffix)):
                            symbol_yf = symbol + country_suffix
                        else:
                            symbol_yf = symbol
                        try:
                            quantity = float(row_dict.get(self.column_mapping['quantity'], 0))
                            avg_price = float(row_dict.get(self.column_mapping['avg_price'], 0))
                        except (ValueError, TypeError):
                            continue
                        preview_item = {'original_symbol': symbol, 'yfinance_symbol': symbol_yf, 'quantity': quantity, 'avg_price': avg_price}
                        self.csv_preview_data.append(preview_item)
                return {'preview_data': self.csv_preview_data, 'valid_rows': len(self.csv_preview_data), 'total_investment': sum((item['quantity'] * item['avg_price'] for item in self.csv_preview_data))}
        except Exception as e:
            logger.error(f'Error creating preview: {e}', exc_info=True)
            raise Exception(f'Error creating preview: {str(e)}')

    @monitor_performance
    def import_csv_portfolio(self, portfolio_name):
        """Import the CSV data as a new portfolio"""
        try:
            with operation('csv_portfolio_import'):
                if not portfolio_name.strip():
                    raise ValueError('Please enter a portfolio name')
                if portfolio_name in self.portfolios:
                    raise ValueError('Portfolio name already exists')
                if not self.csv_preview_data:
                    raise ValueError('No preview data available. Please analyze CSV first')
                new_portfolio = {}
                for item in self.csv_preview_data:
                    symbol = item['yfinance_symbol']
                    new_portfolio[symbol] = {'quantity': item['quantity'], 'avg_price': item['avg_price'], 'last_added': datetime.datetime.now().strftime('%Y-%m-%d'), 'original_symbol': item['original_symbol']}
                    self.price_cache[symbol] = item['avg_price'] * (1 + random.uniform(-0.05, 0.05))
                self.portfolios[portfolio_name] = new_portfolio
                self.save_portfolios()
                self._clear_portfolio_cache()
                imported_symbols = list(new_portfolio.keys())
                threading.Thread(target=lambda: self._fetch_prices_batch(imported_symbols), daemon=True).start()
                self.csv_data = None
                self.csv_headers = []
                self.column_mapping = {}
                self.csv_preview_data = []
                return {'portfolio_name': portfolio_name, 'stocks_imported': len(new_portfolio), 'success': True}
        except Exception as e:
            logger.error(f'Error importing portfolio: {e}', exc_info=True)
            raise Exception(f'Error importing portfolio: {str(e)}')

    def _clear_portfolio_cache(self):
        """Clear portfolio calculation cache"""
        self._portfolio_value_cache.clear()
        self._portfolio_investment_cache.clear()
        self._last_cache_update.clear()
        self.get_current_price.cache_clear()
        self.get_daily_change.cache_clear()

    def _fetch_single_price_and_update(self, symbol):
        """Fetch price for a single symbol and update cache - optimized"""
        try:
            with operation('fetch_single_price', context={'symbol': symbol}):
                price = self._fetch_single_price(symbol)
                if price is not None:
                    self.price_cache[symbol] = price
                    self.last_price_update[symbol] = datetime.datetime.now()
                    logger.debug(f'Updated price for {symbol}: ${price:.2f}')
                    self._clear_portfolio_cache()
                else:
                    logger.warning(f'Could not fetch price for {symbol}')
        except Exception as e:
            logger.error(f'Error fetching price for {symbol}: {e}')

    def start_price_refresh_thread(self):
        """Start the auto price refresh thread"""
        if not self.refresh_running:
            self.refresh_running = True
            self.refresh_thread = threading.Thread(target=self._price_refresh_loop, daemon=True)
            self.refresh_thread.start()
            logger.info('Started hourly price refresh thread')

    def _price_refresh_loop(self):
        """Background thread for price refresh - runs every hour - optimized"""
        while self.refresh_running:
            try:
                while not self.initial_price_fetch_done and self.refresh_running:
                    time.sleep(10)
                if not self.refresh_running:
                    break
                for _ in range(0, self.price_update_interval, 10):
                    if not self.refresh_running:
                        break
                    time.sleep(10)
                if self.refresh_running:
                    logger.info('Hourly price update starting...')
                    self.refresh_all_prices_background()
            except Exception as e:
                logger.error(f'Error in price refresh loop: {e}')
                time.sleep(300)

    @monitor_performance
    def refresh_all_prices_background(self):
        """Refresh all prices in background - optimized"""
        try:
            with operation('refresh_all_prices'):
                all_symbols = set()
                for portfolio in self.portfolios.values():
                    for symbol in portfolio.keys():
                        all_symbols.add(symbol)
                if not all_symbols:
                    return
                logger.info(f'Refreshing prices for {len(all_symbols)} symbols...', context={'symbols_count': len(all_symbols)})
                self._fetch_prices_batch(list(all_symbols))
                self._clear_portfolio_cache()
                logger.info('Price refresh completed')
                return True
        except Exception as e:
            logger.error(f'Error refreshing prices: {e}')
            return False

    def refresh_all_prices_now(self):
        """Refresh all prices immediately"""
        threading.Thread(target=self.refresh_all_prices_background, daemon=True).start()
        return True

    @monitor_performance
    def export_portfolio_data(self):
        """Export portfolio data - optimized"""
        try:
            with operation('export_portfolio_data'):
                export_data = []
                export_data.append(['Portfolio', 'Symbol', 'Original_Symbol', 'Quantity', 'Avg_Price', 'Current_Price', 'Investment', 'Current_Value', 'P&L', 'P&L_%'])
                for portfolio_name, stocks in self.portfolios.items():
                    for symbol, data in stocks.items():
                        if isinstance(data, dict):
                            quantity = data.get('quantity', 0)
                            avg_price = data.get('avg_price', 0)
                            original_symbol = data.get('original_symbol', symbol)
                            current_price = self.get_current_price(symbol)
                            investment = quantity * avg_price
                            current_value = quantity * current_price
                            pnl = current_value - investment
                            pnl_pct = pnl / investment * 100 if investment > 0 else 0
                            export_data.append([portfolio_name, symbol, original_symbol, quantity, avg_price, current_price, investment, current_value, pnl, pnl_pct])
                export_filename = f'portfolio_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv'
                with open(export_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(export_data)
                return export_filename
        except Exception as e:
            logger.error(f'Error exporting portfolio data: {e}', exc_info=True)
            raise Exception('Error exporting portfolio data')

    @monitor_performance
    def load_portfolios(self):
        """Load portfolios from settings file - optimized"""
        if PORTFOLIO_CONFIG_FILE.exists():
            try:
                with operation('load_portfolios'):
                    with open(PORTFOLIO_CONFIG_FILE, 'r') as file:
                        settings = json.load(file)
                        portfolios = settings.get('portfolios', {})
                        if 'watchlist' in portfolios:
                            del portfolios['watchlist']
                        return portfolios
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f'Error loading portfolios: Corrupted portfolio_settings.json file - {e}')
                return {}
        return {}

    @monitor_performance
    def save_portfolios(self):
        """Save portfolios to settings file - optimized"""
        try:
            with operation('save_portfolios'):
                settings = {}
                if PORTFOLIO_CONFIG_FILE.exists():
                    try:
                        with open(PORTFOLIO_CONFIG_FILE, 'r') as file:
                            settings = json.load(file)
                    except json.JSONDecodeError:
                        settings = {}
                if 'portfolios' not in settings:
                    settings['portfolios'] = {}
                for portfolio_name, portfolio_data in self.portfolios.items():
                    settings['portfolios'][portfolio_name] = portfolio_data
                temp_file = str(PORTFOLIO_CONFIG_FILE) + '.tmp'
                with open(temp_file, 'w') as file:
                    json.dump(settings, file, indent=4)
                import shutil
                shutil.move(temp_file, str(PORTFOLIO_CONFIG_FILE))
                logger.debug('Portfolios saved successfully')
        except Exception as e:
            logger.error(f'Error saving portfolios: {e}', exc_info=True)
            raise Exception(f'Error saving portfolios: {e}')

    @monitor_performance
    def cleanup(self):
        """Clean up portfolio business logic resources - optimized"""
        try:
            with operation('portfolio_business_cleanup'):
                logger.info('🧹 Cleaning up portfolio business logic...')
                self.refresh_running = False
                if hasattr(self, 'portfolios'):
                    self.save_portfolios()
                self.portfolios.clear()
                self.current_portfolio = None
                self.price_cache.clear()
                self.last_price_update.clear()
                self.price_fetch_errors.clear()
                self.daily_change_cache.clear()
                self.previous_close_cache.clear()
                self.csv_data = None
                self.csv_headers = []
                self.column_mapping = {}
                self.csv_preview_data = []
                self._clear_portfolio_cache()
                self.get_current_price.cache_clear()
                self.get_daily_change.cache_clear()
                self.auto_detect_column.cache_clear()
                logger.info('Portfolio business logic cleanup complete')
        except Exception as e:
            logger.error(f'Error in portfolio business cleanup: {e}', exc_info=True)

def initialize_sample_data(self):
    """Initialize sample portfolio data for demonstration"""
    if not self.portfolios:
        self.portfolios = {'Tech Growth': {'AAPL': {'quantity': 50, 'avg_price': 150.25, 'last_added': '2024-01-15'}, 'MSFT': {'quantity': 30, 'avg_price': 280.75, 'last_added': '2024-01-10'}, 'GOOGL': {'quantity': 25, 'avg_price': 125.5, 'last_added': '2024-01-05'}, 'NVDA': {'quantity': 20, 'avg_price': 450.3, 'last_added': '2024-01-20'}}, 'Dividend Income': {'JNJ': {'quantity': 100, 'avg_price': 160.8, 'last_added': '2024-01-12'}, 'PG': {'quantity': 75, 'avg_price': 145.2, 'last_added': '2024-01-08'}, 'KO': {'quantity': 150, 'avg_price': 58.9, 'last_added': '2024-01-18'}}}
        self.save_portfolios()

def create_portfolio(self, name, description=''):
    """Create a new portfolio"""
    if not name:
        raise ValueError('Please enter a portfolio name.')
    if name in self.portfolios:
        raise ValueError('Portfolio name already exists.')
    self.portfolios[name] = {}
    self.save_portfolios()
    self._clear_portfolio_cache()
    return True

def create_portfolio_with_stock(self, name, symbol, quantity, price, description=''):
    """Create portfolio and add first stock"""
    if not name:
        raise ValueError('Please enter a portfolio name.')
    if name in self.portfolios:
        raise ValueError('Portfolio name already exists.')
    if symbol and quantity is not None and (price is not None):
        try:
            quantity = float(quantity)
            price = float(price)
            self.portfolios[name] = {symbol: {'quantity': quantity, 'avg_price': price, 'last_added': datetime.datetime.now().strftime('%Y-%m-%d')}}
            threading.Thread(target=lambda: self._fetch_single_price_and_update(symbol), daemon=True).start()
        except ValueError:
            raise ValueError('Invalid quantity or price values.')
    else:
        self.portfolios[name] = {}
    self.save_portfolios()
    self._clear_portfolio_cache()
    return True

def add_stock_to_portfolio(self, portfolio_name, symbol, quantity, price):
    """Add stock to existing portfolio"""
    if not portfolio_name or portfolio_name not in self.portfolios:
        raise ValueError('Invalid portfolio selected.')
    if not symbol or quantity is None or price is None:
        raise ValueError('Please fill in all fields.')
    try:
        quantity = float(quantity)
        price = float(price)
    except ValueError:
        raise ValueError('Invalid quantity or price values.')
    if symbol in self.portfolios[portfolio_name]:
        existing = self.portfolios[portfolio_name][symbol]
        current_qty = existing['quantity']
        current_avg = existing['avg_price']
        new_qty = current_qty + quantity
        new_avg = (current_avg * current_qty + price * quantity) / new_qty
        self.portfolios[portfolio_name][symbol] = {'quantity': new_qty, 'avg_price': round(new_avg, 2), 'last_added': datetime.datetime.now().strftime('%Y-%m-%d')}
    else:
        self.portfolios[portfolio_name][symbol] = {'quantity': quantity, 'avg_price': price, 'last_added': datetime.datetime.now().strftime('%Y-%m-%d')}
    self.price_cache[symbol] = price * (1 + random.uniform(-0.05, 0.05))
    self.save_portfolios()
    self._clear_portfolio_cache()
    threading.Thread(target=lambda: self._fetch_single_price_and_update(symbol), daemon=True).start()
    return True

def remove_stock_from_portfolio(self, portfolio_name, symbol):
    """Remove stock from portfolio"""
    if not portfolio_name or portfolio_name not in self.portfolios:
        raise ValueError('Portfolio not found')
    if symbol not in self.portfolios[portfolio_name]:
        raise ValueError('Stock not found in portfolio')
    del self.portfolios[portfolio_name][symbol]
    self.save_portfolios()
    self._clear_portfolio_cache()
    return True

def delete_portfolio(self, portfolio_name):
    """Delete the specified portfolio"""
    if portfolio_name not in self.portfolios:
        raise ValueError('Portfolio not found')
    del self.portfolios[portfolio_name]
    self.save_portfolios()
    self._clear_portfolio_cache()
    if self.current_portfolio == portfolio_name:
        self.current_portfolio = None
    return True

class AlpacaWrapper:
    """Complete wrapper for Alpaca trading and data operations"""

    def __init__(self, api_key: str=None, secret_key: str=None, paper: bool=True):
        self.api_key = api_key or os.getenv('ALPACA_API_KEY')
        self.secret_key = secret_key or os.getenv('ALPACA_SECRET_KEY')
        if not self.api_key or not self.secret_key:
            raise ValueError('API keys must be provided or set as environment variables')
        self.paper = paper
        try:
            self.trading_client = TradingClient(self.api_key, self.secret_key, paper=paper)
            self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
            self.stream = StockDataStream(self.api_key, self.secret_key)
            logger.info(f'Initialized Alpaca clients (Paper: {paper})')
        except Exception as e:
            logger.error(f'Failed to initialize Alpaca clients: {e}')
            raise

    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f'Failed to get market status: {e}')
            return False

    def get_market_clock(self) -> Dict:
        """Get detailed market status"""
        try:
            clock = self.trading_client.get_clock()
            return {'is_open': clock.is_open, 'timestamp': clock.timestamp, 'next_open': clock.next_open, 'next_close': clock.next_close}
        except Exception as e:
            logger.error(f'Failed to get market clock: {e}')
            return {}

    def get_account(self) -> Dict:
        """Get account information"""
        try:
            account = self.trading_client.get_account()
            return {'equity': float(account.equity), 'buying_power': float(account.buying_power), 'cash': float(account.cash), 'portfolio_value': float(account.portfolio_value), 'day_trade_count': int(account.daytrade_count), 'pattern_day_trader': account.pattern_day_trader}
        except Exception as e:
            logger.error(f'Failed to get account info: {e}')
            return {}

    def get_positions(self) -> pd.DataFrame:
        """Get all positions as DataFrame"""
        try:
            positions = self.trading_client.get_all_positions()
            if not positions:
                return pd.DataFrame()
            data = []
            for pos in positions:
                data.append({'symbol': pos.symbol, 'qty': float(pos.qty), 'market_value': float(pos.market_value), 'cost_basis': float(pos.cost_basis), 'unrealized_pl': float(pos.unrealized_pl), 'unrealized_plpc': float(pos.unrealized_plpc), 'avg_entry_price': float(pos.avg_entry_price), 'side': pos.side})
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f'Failed to get positions: {e}')
            return pd.DataFrame()

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get specific position"""
        try:
            pos = self.trading_client.get_open_position(symbol)
            return {'symbol': pos.symbol, 'qty': float(pos.qty), 'market_value': float(pos.market_value), 'avg_entry_price': float(pos.avg_entry_price), 'unrealized_pl': float(pos.unrealized_pl), 'unrealized_plpc': float(pos.unrealized_plpc), 'cost_basis': float(pos.cost_basis)}
        except Exception as e:
            logger.warning(f'No position found for {symbol}: {e}')
            return None

    def buy(self, symbol: str, qty: Union[int, float], order_type: str='market', limit_price: float=None, stop_price: float=None, extended_hours: bool=False) -> Optional[str]:
        """Place buy order"""
        return self._place_order(symbol, qty, OrderSide.BUY, order_type, limit_price, stop_price, extended_hours)

    def sell(self, symbol: str, qty: Union[int, float], order_type: str='market', limit_price: float=None, stop_price: float=None, extended_hours: bool=False) -> Optional[str]:
        """Place sell order"""
        return self._place_order(symbol, qty, OrderSide.SELL, order_type, limit_price, stop_price, extended_hours)

    def _place_order(self, symbol: str, qty: Union[int, float], side: OrderSide, order_type: str, limit_price: float=None, stop_price: float=None, extended_hours: bool=False) -> Optional[str]:
        """Internal order placement with improved error handling"""
        try:
            if not extended_hours and (not self.is_market_open()):
                logger.warning('Market is closed. Use extended_hours=True for after-hours trading')
            order_type = order_type.lower()
            if order_type == 'market':
                request = MarketOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.DAY, extended_hours=extended_hours)
            elif order_type == 'limit':
                if limit_price is None:
                    raise ValueError('limit_price required for limit orders')
                request = LimitOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.DAY, limit_price=limit_price, extended_hours=extended_hours)
            elif order_type == 'stop':
                if stop_price is None:
                    raise ValueError('stop_price required for stop orders')
                request = StopOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.DAY, stop_price=stop_price)
            elif order_type == 'stop_limit':
                if limit_price is None or stop_price is None:
                    raise ValueError('Both limit_price and stop_price required for stop-limit orders')
                request = StopLimitOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.DAY, limit_price=limit_price, stop_price=stop_price)
            else:
                raise ValueError(f'Unsupported order type: {order_type}')
            order = self.trading_client.submit_order(request)
            logger.info(f'Order placed: {order.id} - {side.value} {qty} {symbol}')
            return order.id
        except Exception as e:
            logger.error(f'Failed to place order: {e}')
            return None

    def place_trailing_stop(self, symbol: str, qty: Union[int, float], side: OrderSide, trail_percent: float=None, trail_price: float=None) -> Optional[str]:
        """Place trailing stop order"""
        try:
            if trail_percent is None and trail_price is None:
                raise ValueError('Either trail_percent or trail_price must be specified')
            request = TrailingStopOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.GTC, trail_percent=trail_percent, trail_price=trail_price)
            order = self.trading_client.submit_order(request)
            logger.info(f'Trailing stop order placed: {order.id}')
            return order.id
        except Exception as e:
            logger.error(f'Failed to place trailing stop order: {e}')
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel order by ID"""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f'Order cancelled: {order_id}')
            return True
        except Exception as e:
            logger.error(f'Failed to cancel order {order_id}: {e}')
            return False

    def cancel_all_orders(self) -> bool:
        """Cancel all open orders"""
        try:
            self.trading_client.cancel_orders()
            logger.info('All orders cancelled')
            return True
        except Exception as e:
            logger.error(f'Failed to cancel all orders: {e}')
            return False

    def get_orders(self, status: str='all', symbols: List[str]=None, limit: int=100) -> pd.DataFrame:
        """Get order history with improved filtering"""
        try:
            status_map = {'all': QueryOrderStatus.ALL, 'open': QueryOrderStatus.OPEN, 'closed': QueryOrderStatus.CLOSED, 'filled': QueryOrderStatus.CLOSED, 'cancelled': QueryOrderStatus.CANCELED}
            req = GetOrdersRequest(status=status_map.get(status.lower(), QueryOrderStatus.ALL), symbols=symbols, limit=limit)
            orders = self.trading_client.get_orders(req)
            if not orders:
                return pd.DataFrame()
            data = []
            for order in orders:
                data.append({'id': order.id, 'symbol': order.symbol, 'qty': float(order.qty), 'side': order.side.value, 'order_type': order.order_type.value, 'status': order.status.value, 'created_at': order.created_at, 'filled_price': float(order.filled_avg_price) if order.filled_avg_price else None, 'filled_qty': float(order.filled_qty) if order.filled_qty else 0, 'limit_price': float(order.limit_price) if order.limit_price else None, 'stop_price': float(order.stop_price) if order.stop_price else None})
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f'Failed to get orders: {e}')
            return pd.DataFrame()

    def close_position(self, symbol: str, qty: Optional[Union[int, float]]=None) -> bool:
        """Close specific position (all or partial)"""
        try:
            if qty:
                from alpaca.trading.requests import ClosePositionRequest
                self.trading_client.close_position(symbol, close_options=ClosePositionRequest(qty=str(qty)))
            else:
                self.trading_client.close_position(symbol)
            logger.info(f'Position closed for {symbol}')
            return True
        except Exception as e:
            logger.error(f'Failed to close position for {symbol}: {e}')
            return False

    def close_all_positions(self) -> bool:
        """Close all positions"""
        try:
            self.trading_client.close_all_positions(cancel_orders=True)
            logger.info('All positions closed')
            return True
        except Exception as e:
            logger.error(f'Failed to close all positions: {e}')
            return False

    def get_bars(self, symbols: Union[str, List[str]], timeframe: str='1Day', start: datetime=None, end: datetime=None, limit: int=1000) -> pd.DataFrame:
        """Get historical bar data with improved timeframe handling"""
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            if start is None:
                start = datetime.now() - timedelta(days=365)
            tf_map = {'1Min': TimeFrame(1, TimeFrameUnit.Minute), '5Min': TimeFrame(5, TimeFrameUnit.Minute), '15Min': TimeFrame(15, TimeFrameUnit.Minute), '30Min': TimeFrame(30, TimeFrameUnit.Minute), '1Hour': TimeFrame(1, TimeFrameUnit.Hour), '4Hour': TimeFrame(4, TimeFrameUnit.Hour), '1Day': TimeFrame(1, TimeFrameUnit.Day), '1Week': TimeFrame(1, TimeFrameUnit.Week), '1Month': TimeFrame(1, TimeFrameUnit.Month)}
            timeframe_obj = tf_map.get(timeframe)
            if timeframe_obj is None:
                raise ValueError(f'Unsupported timeframe: {timeframe}')
            request = StockBarsRequest(symbol_or_symbols=symbols, timeframe=timeframe_obj, start=start, end=end, limit=limit)
            bars = self.data_client.get_stock_bars(request)
            return bars.df
        except Exception as e:
            logger.error(f'Failed to get bars: {e}')
            return pd.DataFrame()

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for symbol"""
        try:
            bars = self.data_client.get_stock_latest_bar([symbol])
            return float(bars[symbol].close)
        except Exception as e:
            logger.error(f'Failed to get latest price for {symbol}: {e}')
            return None

    def get_latest_quote(self, symbol: str) -> Optional[Dict]:
        """Get latest bid/ask quote"""
        try:
            quote = self.data_client.get_stock_latest_quote([symbol])
            q = quote[symbol]
            return {'symbol': symbol, 'bid': float(q.bid_price), 'ask': float(q.ask_price), 'bid_size': int(q.bid_size), 'ask_size': int(q.ask_size), 'timestamp': q.timestamp}
        except Exception as e:
            logger.error(f'Failed to get latest quote for {symbol}: {e}')
            return None

    def get_quotes(self, symbols: Union[str, List[str]], start: datetime=None, limit: int=1000) -> pd.DataFrame:
        """Get historical quote data"""
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            if start is None:
                start = datetime.now() - timedelta(days=1)
            request = StockQuotesRequest(symbol_or_symbols=symbols, start=start, limit=limit)
            quotes = self.data_client.get_stock_quotes(request)
            return quotes.df
        except Exception as e:
            logger.error(f'Failed to get quotes: {e}')
            return pd.DataFrame()

    def get_trades(self, symbols: Union[str, List[str]], start: datetime=None, limit: int=1000) -> pd.DataFrame:
        """Get historical trade data"""
        try:
            if isinstance(symbols, str):
                symbols = [symbols]
            if start is None:
                start = datetime.now() - timedelta(days=1)
            request = StockTradesRequest(symbol_or_symbols=symbols, start=start, limit=limit)
            trades = self.data_client.get_stock_trades(request)
            return trades.df
        except Exception as e:
            logger.error(f'Failed to get trades: {e}')
            return pd.DataFrame()

    def get_portfolio_history(self, period: str='1M', timeframe: str='1D') -> pd.DataFrame:
        """Get portfolio performance history"""
        try:
            history = self.trading_client.get_portfolio_history(period=period, timeframe=timeframe)
            data = {'timestamp': history.timestamp, 'equity': history.equity, 'profit_loss': history.profit_loss, 'profit_loss_pct': history.profit_loss_pct}
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            return df.set_index('timestamp')
        except Exception as e:
            logger.error(f'Failed to get portfolio history: {e}')
            return pd.DataFrame()

    def start_stream(self, symbols: List[str], on_bar=None, on_trade=None, on_quote=None):
        """Start real-time data stream"""
        try:
            if on_bar:
                self.stream.subscribe_bars(on_bar, *symbols)
            if on_trade:
                self.stream.subscribe_trades(on_trade, *symbols)
            if on_quote:
                self.stream.subscribe_quotes(on_quote, *symbols)
            logger.info(f'Starting stream for {symbols}')
            self.stream.run()
        except Exception as e:
            logger.error(f'Failed to start stream: {e}')

    def stop_stream(self):
        """Stop real-time data stream"""
        try:
            self.stream.stop()
            logger.info('Stream stopped')
        except Exception as e:
            logger.error(f'Failed to stop stream: {e}')

    def get_watchlist(self, watchlist_id: str=None) -> pd.DataFrame:
        """Get watchlist"""
        try:
            if watchlist_id:
                watchlist = self.trading_client.get_watchlist_by_id(watchlist_id)
            else:
                watchlists = self.trading_client.get_watchlists()
                if not watchlists:
                    return pd.DataFrame()
                watchlist = watchlists[0]
            symbols = [asset.symbol for asset in watchlist.assets]
            return pd.DataFrame({'symbol': symbols})
        except Exception as e:
            logger.error(f'Failed to get watchlist: {e}')
            return pd.DataFrame()

def get_account(self) -> Dict:
    """Get account information"""
    try:
        account = self.trading_client.get_account()
        return {'equity': float(account.equity), 'buying_power': float(account.buying_power), 'cash': float(account.cash), 'portfolio_value': float(account.portfolio_value), 'day_trade_count': int(account.daytrade_count), 'pattern_day_trader': account.pattern_day_trader}
    except Exception as e:
        logger.error(f'Failed to get account info: {e}')
        return {}

def get_positions(self) -> pd.DataFrame:
    """Get all positions as DataFrame"""
    try:
        positions = self.trading_client.get_all_positions()
        if not positions:
            return pd.DataFrame()
        data = []
        for pos in positions:
            data.append({'symbol': pos.symbol, 'qty': float(pos.qty), 'market_value': float(pos.market_value), 'cost_basis': float(pos.cost_basis), 'unrealized_pl': float(pos.unrealized_pl), 'unrealized_plpc': float(pos.unrealized_plpc), 'avg_entry_price': float(pos.avg_entry_price), 'side': pos.side})
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f'Failed to get positions: {e}')
        return pd.DataFrame()

def get_position(self, symbol: str) -> Optional[Dict]:
    """Get specific position"""
    try:
        pos = self.trading_client.get_open_position(symbol)
        return {'symbol': pos.symbol, 'qty': float(pos.qty), 'market_value': float(pos.market_value), 'avg_entry_price': float(pos.avg_entry_price), 'unrealized_pl': float(pos.unrealized_pl), 'unrealized_plpc': float(pos.unrealized_plpc), 'cost_basis': float(pos.cost_basis)}
    except Exception as e:
        logger.warning(f'No position found for {symbol}: {e}')
        return None

def get_latest_price(self, symbol: str) -> Optional[float]:
    """Get latest price for symbol"""
    try:
        bars = self.data_client.get_stock_latest_bar([symbol])
        return float(bars[symbol].close)
    except Exception as e:
        logger.error(f'Failed to get latest price for {symbol}: {e}')
        return None

def get_latest_quote(self, symbol: str) -> Optional[Dict]:
    """Get latest bid/ask quote"""
    try:
        quote = self.data_client.get_stock_latest_quote([symbol])
        q = quote[symbol]
        return {'symbol': symbol, 'bid': float(q.bid_price), 'ask': float(q.ask_price), 'bid_size': int(q.bid_size), 'ask_size': int(q.ask_size), 'timestamp': q.timestamp}
    except Exception as e:
        logger.error(f'Failed to get latest quote for {symbol}: {e}')
        return None

def safe_format(value, format_type='number', decimal_places=2):
    """Safely format values to avoid errors"""
    if value is None or value == 'N/A' or value == '':
        return 'N/A'
    try:
        if format_type == 'percentage':
            return f'{float(value):.{decimal_places}%}'
        elif format_type == 'number':
            return f'{float(value):,.{decimal_places}f}'
        elif format_type == 'currency':
            return f'${float(value):,.0f}'
        else:
            return str(value)
    except:
        return str(value) if value is not None else 'N/A'

