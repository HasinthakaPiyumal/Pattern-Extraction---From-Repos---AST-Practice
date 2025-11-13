# Cluster 194

class CompanyData(FinnhubBase):
    """Company information and profiles"""

    def symbol_lookup(self, q: str, exchange: str=None) -> Dict:
        """Search for best-matching symbols"""
        return self._get('/search', q=q, exchange=exchange)

    def stock_symbols(self, exchange: str, mic: str=None, security_type: str=None, currency: str=None) -> Dict:
        """List supported stocks"""
        return self._get('/stock/symbol', exchange=exchange, mic=mic, securityType=security_type, currency=currency)

    def market_status(self, exchange: str) -> Dict:
        """Get current market status"""
        return self._get('/stock/market-status', exchange=exchange)

    def market_holiday(self, exchange: str) -> Dict:
        """Get market holidays"""
        return self._get('/stock/market-holiday', exchange=exchange)

    def company_profile(self, symbol: str=None, isin: str=None, cusip: str=None) -> Dict:
        """Get company profile (Premium)"""
        return self._get('/stock/profile', symbol=symbol, isin=isin, cusip=cusip)

    def company_profile2(self, symbol: str=None, isin: str=None, cusip: str=None) -> Dict:
        """Get company profile (Basic)"""
        return self._get('/stock/profile2', symbol=symbol, isin=isin, cusip=cusip)

    def company_executive(self, symbol: str) -> Dict:
        """Get company executives (Premium)"""
        return self._get('/stock/executive', symbol=symbol)

    def company_peers(self, symbol: str, grouping: str=None) -> Dict:
        """Get company peers"""
        return self._get('/stock/peers', symbol=symbol, grouping=grouping)

def symbol_lookup(self, q: str, exchange: str=None) -> Dict:
    """Search for best-matching symbols"""
    return self._get('/search', q=q, exchange=exchange)

def stock_symbols(self, exchange: str, mic: str=None, security_type: str=None, currency: str=None) -> Dict:
    """List supported stocks"""
    return self._get('/stock/symbol', exchange=exchange, mic=mic, securityType=security_type, currency=currency)

def market_status(self, exchange: str) -> Dict:
    """Get current market status"""
    return self._get('/stock/market-status', exchange=exchange)

def market_holiday(self, exchange: str) -> Dict:
    """Get market holidays"""
    return self._get('/stock/market-holiday', exchange=exchange)

def company_profile(self, symbol: str=None, isin: str=None, cusip: str=None) -> Dict:
    """Get company profile (Premium)"""
    return self._get('/stock/profile', symbol=symbol, isin=isin, cusip=cusip)

def company_profile2(self, symbol: str=None, isin: str=None, cusip: str=None) -> Dict:
    """Get company profile (Basic)"""
    return self._get('/stock/profile2', symbol=symbol, isin=isin, cusip=cusip)

def company_executive(self, symbol: str) -> Dict:
    """Get company executives (Premium)"""
    return self._get('/stock/executive', symbol=symbol)

def company_peers(self, symbol: str, grouping: str=None) -> Dict:
    """Get company peers"""
    return self._get('/stock/peers', symbol=symbol, grouping=grouping)

class NewsData(FinnhubBase):
    """News and press releases"""

    def market_news(self, category: str, min_id: int=None) -> Dict:
        """Get latest market news"""
        return self._get('/news', category=category, minId=min_id)

    def company_news(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get company news"""
        return self._get('/company-news', symbol=symbol, **{'from': from_date, 'to': to_date})

    def press_releases(self, symbol: str, from_date: str=None, to_date: str=None) -> Dict:
        """Get press releases (Premium)"""
        params = {'symbol': symbol}
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        return self._get('/press-releases', **params)

    def news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment (Premium)"""
        return self._get('/news-sentiment', symbol=symbol)

def market_news(self, category: str, min_id: int=None) -> Dict:
    """Get latest market news"""
    return self._get('/news', category=category, minId=min_id)

def company_news(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get company news"""
    return self._get('/company-news', symbol=symbol, **{'from': from_date, 'to': to_date})

def press_releases(self, symbol: str, from_date: str=None, to_date: str=None) -> Dict:
    """Get press releases (Premium)"""
    params = {'symbol': symbol}
    if from_date:
        params['from'] = from_date
    if to_date:
        params['to'] = to_date
    return self._get('/press-releases', **params)

def news_sentiment(self, symbol: str) -> Dict:
    """Get news sentiment (Premium)"""
    return self._get('/news-sentiment', symbol=symbol)

class FinancialData(FinnhubBase):
    """Financial statements and metrics"""

    def basic_financials(self, symbol: str, metric: str='all') -> Dict:
        """Get basic financials"""
        return self._get('/stock/metric', symbol=symbol, metric=metric)

    def ownership(self, symbol: str, limit: int=None) -> Dict:
        """Get ownership data (Premium)"""
        return self._get('/stock/ownership', symbol=symbol, limit=limit)

    def fund_ownership(self, symbol: str, limit: int=None) -> Dict:
        """Get fund ownership (Premium)"""
        return self._get('/stock/fund-ownership', symbol=symbol, limit=limit)

    def financials(self, symbol: str, statement: str, freq: str) -> Dict:
        """Get financial statements (Premium)"""
        return self._get('/stock/financials', symbol=symbol, statement=statement, freq=freq)

    def financials_reported(self, symbol: str=None, cik: str=None, access_number: str=None, freq: str=None, from_date: str=None, to_date: str=None) -> Dict:
        """Get financials as reported"""
        return self._get('/stock/financials-reported', symbol=symbol, cik=cik, accessNumber=access_number, freq=freq, **{'from': from_date, 'to': to_date})

    def revenue_breakdown(self, symbol: str=None, cik: str=None) -> Dict:
        """Get revenue breakdown (Premium)"""
        return self._get('/stock/revenue-breakdown', symbol=symbol, cik=cik)

    def revenue_breakdown2(self, symbol: str) -> Dict:
        """Get revenue breakdown & KPI (Premium)"""
        return self._get('/stock/revenue-breakdown2', symbol=symbol)

def basic_financials(self, symbol: str, metric: str='all') -> Dict:
    """Get basic financials"""
    return self._get('/stock/metric', symbol=symbol, metric=metric)

def ownership(self, symbol: str, limit: int=None) -> Dict:
    """Get ownership data (Premium)"""
    return self._get('/stock/ownership', symbol=symbol, limit=limit)

def fund_ownership(self, symbol: str, limit: int=None) -> Dict:
    """Get fund ownership (Premium)"""
    return self._get('/stock/fund-ownership', symbol=symbol, limit=limit)

def financials(self, symbol: str, statement: str, freq: str) -> Dict:
    """Get financial statements (Premium)"""
    return self._get('/stock/financials', symbol=symbol, statement=statement, freq=freq)

def financials_reported(self, symbol: str=None, cik: str=None, access_number: str=None, freq: str=None, from_date: str=None, to_date: str=None) -> Dict:
    """Get financials as reported"""
    return self._get('/stock/financials-reported', symbol=symbol, cik=cik, accessNumber=access_number, freq=freq, **{'from': from_date, 'to': to_date})

def revenue_breakdown(self, symbol: str=None, cik: str=None) -> Dict:
    """Get revenue breakdown (Premium)"""
    return self._get('/stock/revenue-breakdown', symbol=symbol, cik=cik)

def revenue_breakdown2(self, symbol: str) -> Dict:
    """Get revenue breakdown & KPI (Premium)"""
    return self._get('/stock/revenue-breakdown2', symbol=symbol)

class SECData(FinnhubBase):
    """SEC and regulatory data"""

    def sec_filings(self, symbol: str=None, cik: str=None, access_number: str=None, form: str=None, from_date: str=None, to_date: str=None) -> Dict:
        """Get SEC filings"""
        return self._get('/stock/filings', symbol=symbol, cik=cik, accessNumber=access_number, form=form, **{'from': from_date, 'to': to_date})

    def sec_sentiment(self, access_number: str) -> Dict:
        """Get SEC sentiment analysis (Premium)"""
        return self._get('/stock/filings-sentiment', accessNumber=access_number)

    def similarity_index(self, symbol: str=None, cik: str=None, freq: str='annual') -> Dict:
        """Get similarity index (Premium)"""
        return self._get('/stock/similarity-index', symbol=symbol, cik=cik, freq=freq)

    def international_filings(self, symbol: str=None, country: str=None, from_date: str=None, to_date: str=None) -> Dict:
        """Get international filings (Premium)"""
        return self._get('/stock/international-filings', symbol=symbol, country=country, **{'from': from_date, 'to': to_date})

def sec_filings(self, symbol: str=None, cik: str=None, access_number: str=None, form: str=None, from_date: str=None, to_date: str=None) -> Dict:
    """Get SEC filings"""
    return self._get('/stock/filings', symbol=symbol, cik=cik, accessNumber=access_number, form=form, **{'from': from_date, 'to': to_date})

def sec_sentiment(self, access_number: str) -> Dict:
    """Get SEC sentiment analysis (Premium)"""
    return self._get('/stock/filings-sentiment', accessNumber=access_number)

def similarity_index(self, symbol: str=None, cik: str=None, freq: str='annual') -> Dict:
    """Get similarity index (Premium)"""
    return self._get('/stock/similarity-index', symbol=symbol, cik=cik, freq=freq)

def international_filings(self, symbol: str=None, country: str=None, from_date: str=None, to_date: str=None) -> Dict:
    """Get international filings (Premium)"""
    return self._get('/stock/international-filings', symbol=symbol, country=country, **{'from': from_date, 'to': to_date})

class MarketData(FinnhubBase):
    """Market data and trading information"""

    def quote(self, symbol: str) -> Dict:
        """Get real-time quote"""
        return self._get('/quote', symbol=symbol)

    def stock_candles(self, symbol: str, resolution: str, from_ts: int, to_ts: int) -> Dict:
        """Get stock candles (Premium)"""
        return self._get('/stock/candle', symbol=symbol, resolution=resolution, **{'from': from_ts, 'to': to_ts})

    def tick_data(self, symbol: str, date: str, limit: int, skip: int) -> Dict:
        """Get tick data (Premium)"""
        return self._get('/stock/tick', symbol=symbol, date=date, limit=limit, skip=skip)

    def historical_nbbo(self, symbol: str, date: str, limit: int, skip: int) -> Dict:
        """Get historical NBBO (Premium)"""
        return self._get('/stock/bbo', symbol=symbol, date=date, limit=limit, skip=skip)

    def last_bid_ask(self, symbol: str) -> Dict:
        """Get last bid-ask (Premium)"""
        return self._get('/stock/bidask', symbol=symbol)

    def stock_splits(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get stock splits (Premium)"""
        return self._get('/stock/split', symbol=symbol, **{'from': from_date, 'to': to_date})

    def dividends(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get dividends (Premium)"""
        return self._get('/stock/dividend', symbol=symbol, **{'from': from_date, 'to': to_date})

    def dividends2(self, symbol: str) -> Dict:
        """Get dividends basic (Premium)"""
        return self._get('/stock/dividend2', symbol=symbol)

def quote(self, symbol: str) -> Dict:
    """Get real-time quote"""
    return self._get('/quote', symbol=symbol)

def stock_candles(self, symbol: str, resolution: str, from_ts: int, to_ts: int) -> Dict:
    """Get stock candles (Premium)"""
    return self._get('/stock/candle', symbol=symbol, resolution=resolution, **{'from': from_ts, 'to': to_ts})

def tick_data(self, symbol: str, date: str, limit: int, skip: int) -> Dict:
    """Get tick data (Premium)"""
    return self._get('/stock/tick', symbol=symbol, date=date, limit=limit, skip=skip)

def historical_nbbo(self, symbol: str, date: str, limit: int, skip: int) -> Dict:
    """Get historical NBBO (Premium)"""
    return self._get('/stock/bbo', symbol=symbol, date=date, limit=limit, skip=skip)

def last_bid_ask(self, symbol: str) -> Dict:
    """Get last bid-ask (Premium)"""
    return self._get('/stock/bidask', symbol=symbol)

def stock_splits(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get stock splits (Premium)"""
    return self._get('/stock/split', symbol=symbol, **{'from': from_date, 'to': to_date})

def dividends(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get dividends (Premium)"""
    return self._get('/stock/dividend', symbol=symbol, **{'from': from_date, 'to': to_date})

def dividends2(self, symbol: str) -> Dict:
    """Get dividends basic (Premium)"""
    return self._get('/stock/dividend2', symbol=symbol)

class EstimatesData(FinnhubBase):
    """Estimates and analyst data"""

    def recommendation_trends(self, symbol: str) -> Dict:
        """Get recommendation trends"""
        return self._get('/stock/recommendation', symbol=symbol)

    def price_target(self, symbol: str) -> Dict:
        """Get price target (Premium)"""
        return self._get('/stock/price-target', symbol=symbol)

    def upgrade_downgrade(self, symbol: str=None, from_date: str=None, to_date: str=None) -> Dict:
        """Get upgrades/downgrades (Premium)"""
        return self._get('/stock/upgrade-downgrade', symbol=symbol, **{'from': from_date, 'to': to_date})

    def revenue_estimates(self, symbol: str, freq: str='quarterly') -> Dict:
        """Get revenue estimates (Premium)"""
        return self._get('/stock/revenue-estimate', symbol=symbol, freq=freq)

    def eps_estimates(self, symbol: str, freq: str='quarterly') -> Dict:
        """Get EPS estimates (Premium)"""
        return self._get('/stock/eps-estimate', symbol=symbol, freq=freq)

    def ebitda_estimates(self, symbol: str, freq: str='quarterly') -> Dict:
        """Get EBITDA estimates (Premium)"""
        return self._get('/stock/ebitda-estimate', symbol=symbol, freq=freq)

    def ebit_estimates(self, symbol: str, freq: str='quarterly') -> Dict:
        """Get EBIT estimates (Premium)"""
        return self._get('/stock/ebit-estimate', symbol=symbol, freq=freq)

    def earnings_surprises(self, symbol: str, limit: int=None) -> Dict:
        """Get earnings surprises"""
        return self._get('/stock/earnings', symbol=symbol, limit=limit)

def recommendation_trends(self, symbol: str) -> Dict:
    """Get recommendation trends"""
    return self._get('/stock/recommendation', symbol=symbol)

def price_target(self, symbol: str) -> Dict:
    """Get price target (Premium)"""
    return self._get('/stock/price-target', symbol=symbol)

def upgrade_downgrade(self, symbol: str=None, from_date: str=None, to_date: str=None) -> Dict:
    """Get upgrades/downgrades (Premium)"""
    return self._get('/stock/upgrade-downgrade', symbol=symbol, **{'from': from_date, 'to': to_date})

def revenue_estimates(self, symbol: str, freq: str='quarterly') -> Dict:
    """Get revenue estimates (Premium)"""
    return self._get('/stock/revenue-estimate', symbol=symbol, freq=freq)

def eps_estimates(self, symbol: str, freq: str='quarterly') -> Dict:
    """Get EPS estimates (Premium)"""
    return self._get('/stock/eps-estimate', symbol=symbol, freq=freq)

def ebitda_estimates(self, symbol: str, freq: str='quarterly') -> Dict:
    """Get EBITDA estimates (Premium)"""
    return self._get('/stock/ebitda-estimate', symbol=symbol, freq=freq)

def ebit_estimates(self, symbol: str, freq: str='quarterly') -> Dict:
    """Get EBIT estimates (Premium)"""
    return self._get('/stock/ebit-estimate', symbol=symbol, freq=freq)

def earnings_surprises(self, symbol: str, limit: int=None) -> Dict:
    """Get earnings surprises"""
    return self._get('/stock/earnings', symbol=symbol, limit=limit)

class CalendarData(FinnhubBase):
    """Calendar events"""

    def ipo_calendar(self, from_date: str, to_date: str) -> Dict:
        """Get IPO calendar"""
        return self._get('/calendar/ipo', **{'from': from_date, 'to': to_date})

    def earnings_calendar(self, from_date: str=None, to_date: str=None, symbol: str=None, international: bool=False) -> Dict:
        """Get earnings calendar"""
        return self._get('/calendar/earnings', **{'from': from_date, 'to': to_date}, symbol=symbol, international=international)

    def economic_calendar(self, from_date: str=None, to_date: str=None) -> Dict:
        """Get economic calendar (Premium)"""
        return self._get('/calendar/economic', **{'from': from_date, 'to': to_date})

def ipo_calendar(self, from_date: str, to_date: str) -> Dict:
    """Get IPO calendar"""
    return self._get('/calendar/ipo', **{'from': from_date, 'to': to_date})

def earnings_calendar(self, from_date: str=None, to_date: str=None, symbol: str=None, international: bool=False) -> Dict:
    """Get earnings calendar"""
    return self._get('/calendar/earnings', **{'from': from_date, 'to': to_date}, symbol=symbol, international=international)

def economic_calendar(self, from_date: str=None, to_date: str=None) -> Dict:
    """Get economic calendar (Premium)"""
    return self._get('/calendar/economic', **{'from': from_date, 'to': to_date})

class MetricsData(FinnhubBase):
    """Performance metrics and analytics"""

    def sector_metrics(self, region: str) -> Dict:
        """Get sector metrics (Premium)"""
        return self._get('/sector/metrics', region=region)

    def price_metrics(self, symbol: str, date: str=None) -> Dict:
        """Get price metrics (Premium)"""
        return self._get('/stock/price-metric', symbol=symbol, date=date)

    def symbol_change(self, from_date: str, to_date: str) -> Dict:
        """Get symbol changes (Premium)"""
        return self._get('/ca/symbol-change', **{'from': from_date, 'to': to_date})

    def isin_change(self, from_date: str, to_date: str) -> Dict:
        """Get ISIN changes (Premium)"""
        return self._get('/ca/isin-change', **{'from': from_date, 'to': to_date})

    def historical_market_cap(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get historical market cap (Premium)"""
        return self._get('/stock/historical-market-cap', symbol=symbol, **{'from': from_date, 'to': to_date})

    def historical_employee_count(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get historical employee count (Premium)"""
        return self._get('/stock/historical-employee-count', symbol=symbol, **{'from': from_date, 'to': to_date})

def sector_metrics(self, region: str) -> Dict:
    """Get sector metrics (Premium)"""
    return self._get('/sector/metrics', region=region)

def price_metrics(self, symbol: str, date: str=None) -> Dict:
    """Get price metrics (Premium)"""
    return self._get('/stock/price-metric', symbol=symbol, date=date)

def symbol_change(self, from_date: str, to_date: str) -> Dict:
    """Get symbol changes (Premium)"""
    return self._get('/ca/symbol-change', **{'from': from_date, 'to': to_date})

def isin_change(self, from_date: str, to_date: str) -> Dict:
    """Get ISIN changes (Premium)"""
    return self._get('/ca/isin-change', **{'from': from_date, 'to': to_date})

def historical_market_cap(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get historical market cap (Premium)"""
    return self._get('/stock/historical-market-cap', symbol=symbol, **{'from': from_date, 'to': to_date})

def historical_employee_count(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get historical employee count (Premium)"""
    return self._get('/stock/historical-employee-count', symbol=symbol, **{'from': from_date, 'to': to_date})

class InstitutionalData(FinnhubBase):
    """Institutional and insider data"""

    def institutional_profile(self, cik: str=None) -> Dict:
        """Get institutional profile (Premium)"""
        return self._get('/institutional/profile', cik=cik)

    def institutional_portfolio(self, cik: str, from_date: str, to_date: str) -> Dict:
        """Get institutional portfolio (Premium)"""
        return self._get('/institutional/portfolio', cik=cik, **{'from': from_date, 'to': to_date})

    def institutional_ownership(self, symbol: str=None, cusip: str=None, from_date: str=None, to_date: str=None) -> Dict:
        """Get institutional ownership (Premium)"""
        return self._get('/institutional/ownership', symbol=symbol, cusip=cusip, **{'from': from_date, 'to': to_date})

    def insider_transactions(self, symbol: str=None, from_date: str=None, to_date: str=None) -> Dict:
        """Get insider transactions"""
        return self._get('/stock/insider-transactions', symbol=symbol, **{'from': from_date, 'to': to_date})

    def insider_sentiment(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get insider sentiment"""
        return self._get('/stock/insider-sentiment', symbol=symbol, **{'from': from_date, 'to': to_date})

def institutional_profile(self, cik: str=None) -> Dict:
    """Get institutional profile (Premium)"""
    return self._get('/institutional/profile', cik=cik)

def institutional_portfolio(self, cik: str, from_date: str, to_date: str) -> Dict:
    """Get institutional portfolio (Premium)"""
    return self._get('/institutional/portfolio', cik=cik, **{'from': from_date, 'to': to_date})

def institutional_ownership(self, symbol: str=None, cusip: str=None, from_date: str=None, to_date: str=None) -> Dict:
    """Get institutional ownership (Premium)"""
    return self._get('/institutional/ownership', symbol=symbol, cusip=cusip, **{'from': from_date, 'to': to_date})

def insider_transactions(self, symbol: str=None, from_date: str=None, to_date: str=None) -> Dict:
    """Get insider transactions"""
    return self._get('/stock/insider-transactions', symbol=symbol, **{'from': from_date, 'to': to_date})

def insider_sentiment(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get insider sentiment"""
    return self._get('/stock/insider-sentiment', symbol=symbol, **{'from': from_date, 'to': to_date})

class ETFMutualFunds(FinnhubBase):
    """ETFs and Mutual Funds data"""

    def indices_constituents(self, symbol: str) -> Dict:
        """Get indices constituents (Premium)"""
        return self._get('/index/constituents', symbol=symbol)

    def historical_constituents(self, symbol: str) -> Dict:
        """Get historical constituents (Premium)"""
        return self._get('/index/historical-constituents', symbol=symbol)

    def etf_profile(self, symbol: str=None, isin: str=None) -> Dict:
        """Get ETF profile (Premium)"""
        return self._get('/etf/profile', symbol=symbol, isin=isin)

    def etf_holdings(self, symbol: str=None, isin: str=None, skip: int=None, date: str=None) -> Dict:
        """Get ETF holdings (Premium)"""
        return self._get('/etf/holdings', symbol=symbol, isin=isin, skip=skip, date=date)

    def etf_sector_exposure(self, symbol: str=None, isin: str=None) -> Dict:
        """Get ETF sector exposure (Premium)"""
        return self._get('/etf/sector', symbol=symbol, isin=isin)

    def etf_country_exposure(self, symbol: str=None, isin: str=None) -> Dict:
        """Get ETF country exposure (Premium)"""
        return self._get('/etf/country', symbol=symbol, isin=isin)

    def mutual_fund_profile(self, symbol: str=None, isin: str=None) -> Dict:
        """Get mutual fund profile (Premium)"""
        return self._get('/mutual-fund/profile', symbol=symbol, isin=isin)

    def mutual_fund_holdings(self, symbol: str=None, isin: str=None, skip: int=None) -> Dict:
        """Get mutual fund holdings (Premium)"""
        return self._get('/mutual-fund/holdings', symbol=symbol, isin=isin, skip=skip)

    def mutual_fund_sector_exposure(self, symbol: str=None, isin: str=None) -> Dict:
        """Get mutual fund sector exposure (Premium)"""
        return self._get('/mutual-fund/sector', symbol=symbol, isin=isin)

    def mutual_fund_country_exposure(self, symbol: str=None, isin: str=None) -> Dict:
        """Get mutual fund country exposure (Premium)"""
        return self._get('/mutual-fund/country', symbol=symbol, isin=isin)

    def mutual_fund_eet(self, isin: str) -> Dict:
        """Get mutual fund EET (Premium)"""
        return self._get('/mutual-fund/eet', isin=isin)

    def mutual_fund_eet_pai(self, isin: str) -> Dict:
        """Get mutual fund EET PAI (Premium)"""
        return self._get('/mutual-fund/eet-pai', isin=isin)

def indices_constituents(self, symbol: str) -> Dict:
    """Get indices constituents (Premium)"""
    return self._get('/index/constituents', symbol=symbol)

def historical_constituents(self, symbol: str) -> Dict:
    """Get historical constituents (Premium)"""
    return self._get('/index/historical-constituents', symbol=symbol)

def etf_profile(self, symbol: str=None, isin: str=None) -> Dict:
    """Get ETF profile (Premium)"""
    return self._get('/etf/profile', symbol=symbol, isin=isin)

def etf_holdings(self, symbol: str=None, isin: str=None, skip: int=None, date: str=None) -> Dict:
    """Get ETF holdings (Premium)"""
    return self._get('/etf/holdings', symbol=symbol, isin=isin, skip=skip, date=date)

def etf_sector_exposure(self, symbol: str=None, isin: str=None) -> Dict:
    """Get ETF sector exposure (Premium)"""
    return self._get('/etf/sector', symbol=symbol, isin=isin)

def etf_country_exposure(self, symbol: str=None, isin: str=None) -> Dict:
    """Get ETF country exposure (Premium)"""
    return self._get('/etf/country', symbol=symbol, isin=isin)

def mutual_fund_profile(self, symbol: str=None, isin: str=None) -> Dict:
    """Get mutual fund profile (Premium)"""
    return self._get('/mutual-fund/profile', symbol=symbol, isin=isin)

def mutual_fund_holdings(self, symbol: str=None, isin: str=None, skip: int=None) -> Dict:
    """Get mutual fund holdings (Premium)"""
    return self._get('/mutual-fund/holdings', symbol=symbol, isin=isin, skip=skip)

def mutual_fund_sector_exposure(self, symbol: str=None, isin: str=None) -> Dict:
    """Get mutual fund sector exposure (Premium)"""
    return self._get('/mutual-fund/sector', symbol=symbol, isin=isin)

def mutual_fund_country_exposure(self, symbol: str=None, isin: str=None) -> Dict:
    """Get mutual fund country exposure (Premium)"""
    return self._get('/mutual-fund/country', symbol=symbol, isin=isin)

def mutual_fund_eet(self, isin: str) -> Dict:
    """Get mutual fund EET (Premium)"""
    return self._get('/mutual-fund/eet', isin=isin)

def mutual_fund_eet_pai(self, isin: str) -> Dict:
    """Get mutual fund EET PAI (Premium)"""
    return self._get('/mutual-fund/eet-pai', isin=isin)

class BondsData(FinnhubBase):
    """Bonds data"""

    def bond_profile(self, isin: str=None, cusip: str=None, figi: str=None) -> Dict:
        """Get bond profile (Premium)"""
        return self._get('/bond/profile', isin=isin, cusip=cusip, figi=figi)

    def bond_price(self, isin: str, from_ts: int, to_ts: int) -> Dict:
        """Get bond price data (Premium)"""
        return self._get('/bond/price', isin=isin, **{'from': from_ts, 'to': to_ts})

    def bond_tick(self, isin: str, date: str, limit: int, skip: int, exchange: str) -> Dict:
        """Get bond tick data (Premium)"""
        return self._get('/bond/tick', isin=isin, date=date, limit=limit, skip=skip, exchange=exchange)

    def bond_yield_curve(self, code: str) -> Dict:
        """Get bond yield curve (Premium)"""
        return self._get('/bond/yield-curve', code=code)

def bond_profile(self, isin: str=None, cusip: str=None, figi: str=None) -> Dict:
    """Get bond profile (Premium)"""
    return self._get('/bond/profile', isin=isin, cusip=cusip, figi=figi)

def bond_price(self, isin: str, from_ts: int, to_ts: int) -> Dict:
    """Get bond price data (Premium)"""
    return self._get('/bond/price', isin=isin, **{'from': from_ts, 'to': to_ts})

def bond_tick(self, isin: str, date: str, limit: int, skip: int, exchange: str) -> Dict:
    """Get bond tick data (Premium)"""
    return self._get('/bond/tick', isin=isin, date=date, limit=limit, skip=skip, exchange=exchange)

def bond_yield_curve(self, code: str) -> Dict:
    """Get bond yield curve (Premium)"""
    return self._get('/bond/yield-curve', code=code)

class ForexData(FinnhubBase):
    """Forex data"""

    def forex_exchanges(self) -> Dict:
        """Get forex exchanges"""
        return self._get('/forex/exchange')

    def forex_symbols(self, exchange: str) -> Dict:
        """Get forex symbols"""
        return self._get('/forex/symbol', exchange=exchange)

    def forex_candles(self, symbol: str, resolution: str, from_ts: int, to_ts: int) -> Dict:
        """Get forex candles (Premium)"""
        return self._get('/forex/candle', symbol=symbol, resolution=resolution, **{'from': from_ts, 'to': to_ts})

    def forex_rates(self, base: str='EUR', date: str=None) -> Dict:
        """Get all forex rates (Premium)"""
        return self._get('/forex/rates', base=base, date=date)

def forex_exchanges(self) -> Dict:
    """Get forex exchanges"""
    return self._get('/forex/exchange')

def forex_symbols(self, exchange: str) -> Dict:
    """Get forex symbols"""
    return self._get('/forex/symbol', exchange=exchange)

def forex_candles(self, symbol: str, resolution: str, from_ts: int, to_ts: int) -> Dict:
    """Get forex candles (Premium)"""
    return self._get('/forex/candle', symbol=symbol, resolution=resolution, **{'from': from_ts, 'to': to_ts})

def forex_rates(self, base: str='EUR', date: str=None) -> Dict:
    """Get all forex rates (Premium)"""
    return self._get('/forex/rates', base=base, date=date)

class CryptoData(FinnhubBase):
    """Cryptocurrency data"""

    def crypto_exchanges(self) -> Dict:
        """Get crypto exchanges"""
        return self._get('/crypto/exchange')

    def crypto_symbols(self, exchange: str) -> Dict:
        """Get crypto symbols"""
        return self._get('/crypto/symbol', exchange=exchange)

    def crypto_profile(self, symbol: str) -> Dict:
        """Get crypto profile (Premium)"""
        return self._get('/crypto/profile', symbol=symbol)

    def crypto_candles(self, symbol: str, resolution: str, from_ts: int, to_ts: int) -> Dict:
        """Get crypto candles (Premium)"""
        return self._get('/crypto/candle', symbol=symbol, resolution=resolution, **{'from': from_ts, 'to': to_ts})

def crypto_exchanges(self) -> Dict:
    """Get crypto exchanges"""
    return self._get('/crypto/exchange')

def crypto_symbols(self, exchange: str) -> Dict:
    """Get crypto symbols"""
    return self._get('/crypto/symbol', exchange=exchange)

def crypto_profile(self, symbol: str) -> Dict:
    """Get crypto profile (Premium)"""
    return self._get('/crypto/profile', symbol=symbol)

def crypto_candles(self, symbol: str, resolution: str, from_ts: int, to_ts: int) -> Dict:
    """Get crypto candles (Premium)"""
    return self._get('/crypto/candle', symbol=symbol, resolution=resolution, **{'from': from_ts, 'to': to_ts})

class TechnicalAnalysis(FinnhubBase):
    """Technical analysis tools"""

    def pattern_recognition(self, symbol: str, resolution: str) -> Dict:
        """Get pattern recognition (Premium)"""
        return self._get('/scan/pattern', symbol=symbol, resolution=resolution)

    def support_resistance(self, symbol: str, resolution: str) -> Dict:
        """Get support/resistance levels (Premium)"""
        return self._get('/scan/support-resistance', symbol=symbol, resolution=resolution)

    def aggregate_indicators(self, symbol: str, resolution: str) -> Dict:
        """Get aggregate indicators (Premium)"""
        return self._get('/scan/technical-indicator', symbol=symbol, resolution=resolution)

    def technical_indicators(self, symbol: str, resolution: str, from_ts: int, to_ts: int, indicator: str, **indicator_fields) -> Dict:
        """Get technical indicators (Premium)"""
        params = {'symbol': symbol, 'resolution': resolution, 'from': from_ts, 'to': to_ts, 'indicator': indicator}
        params.update(indicator_fields)
        return self._get('/indicator', **params)

def pattern_recognition(self, symbol: str, resolution: str) -> Dict:
    """Get pattern recognition (Premium)"""
    return self._get('/scan/pattern', symbol=symbol, resolution=resolution)

def support_resistance(self, symbol: str, resolution: str) -> Dict:
    """Get support/resistance levels (Premium)"""
    return self._get('/scan/support-resistance', symbol=symbol, resolution=resolution)

def aggregate_indicators(self, symbol: str, resolution: str) -> Dict:
    """Get aggregate indicators (Premium)"""
    return self._get('/scan/technical-indicator', symbol=symbol, resolution=resolution)

class AlternativeData(FinnhubBase):
    """Alternative data sources"""

    def transcripts_list(self, symbol: str=None) -> Dict:
        """Get transcripts list (Premium)"""
        return self._get('/stock/transcripts/list', symbol=symbol)

    def transcripts(self, id: str) -> Dict:
        """Get earnings call transcripts (Premium)"""
        return self._get('/stock/transcripts', id=id)

    def earnings_call_live(self, from_date: str=None, to_date: str=None, symbol: str=None) -> Dict:
        """Get earnings call audio live (Premium)"""
        return self._get('/stock/earnings-call-live', **{'from': from_date, 'to': to_date}, symbol=symbol)

    def company_presentation(self, symbol: str) -> Dict:
        """Get company presentation (Premium)"""
        return self._get('/stock/presentation', symbol=symbol)

    def social_sentiment(self, symbol: str, from_date: str=None, to_date: str=None) -> Dict:
        """Get social sentiment (Premium)"""
        return self._get('/stock/social-sentiment', symbol=symbol, **{'from': from_date, 'to': to_date})

    def investment_themes(self, theme: str) -> Dict:
        """Get investment themes (Premium)"""
        return self._get('/stock/investment-theme', theme=theme)

    def supply_chain(self, symbol: str) -> Dict:
        """Get supply chain relationships (Premium)"""
        return self._get('/stock/supply-chain', symbol=symbol)

def transcripts_list(self, symbol: str=None) -> Dict:
    """Get transcripts list (Premium)"""
    return self._get('/stock/transcripts/list', symbol=symbol)

def transcripts(self, id: str) -> Dict:
    """Get earnings call transcripts (Premium)"""
    return self._get('/stock/transcripts', id=id)

def earnings_call_live(self, from_date: str=None, to_date: str=None, symbol: str=None) -> Dict:
    """Get earnings call audio live (Premium)"""
    return self._get('/stock/earnings-call-live', **{'from': from_date, 'to': to_date}, symbol=symbol)

def company_presentation(self, symbol: str) -> Dict:
    """Get company presentation (Premium)"""
    return self._get('/stock/presentation', symbol=symbol)

def social_sentiment(self, symbol: str, from_date: str=None, to_date: str=None) -> Dict:
    """Get social sentiment (Premium)"""
    return self._get('/stock/social-sentiment', symbol=symbol, **{'from': from_date, 'to': to_date})

def investment_themes(self, theme: str) -> Dict:
    """Get investment themes (Premium)"""
    return self._get('/stock/investment-theme', theme=theme)

def supply_chain(self, symbol: str) -> Dict:
    """Get supply chain relationships (Premium)"""
    return self._get('/stock/supply-chain', symbol=symbol)

class ESGSustainability(FinnhubBase):
    """ESG and sustainability data"""

    def esg_scores(self, symbol: str) -> Dict:
        """Get ESG scores (Premium)"""
        return self._get('/stock/esg', symbol=symbol)

    def historical_esg_scores(self, symbol: str) -> Dict:
        """Get historical ESG scores (Premium)"""
        return self._get('/stock/historical-esg', symbol=symbol)

    def earnings_quality_score(self, symbol: str, freq: str) -> Dict:
        """Get earnings quality score (Premium)"""
        return self._get('/stock/earnings-quality-score', symbol=symbol, freq=freq)

def esg_scores(self, symbol: str) -> Dict:
    """Get ESG scores (Premium)"""
    return self._get('/stock/esg', symbol=symbol)

def historical_esg_scores(self, symbol: str) -> Dict:
    """Get historical ESG scores (Premium)"""
    return self._get('/stock/historical-esg', symbol=symbol)

def earnings_quality_score(self, symbol: str, freq: str) -> Dict:
    """Get earnings quality score (Premium)"""
    return self._get('/stock/earnings-quality-score', symbol=symbol, freq=freq)

class GovernmentData(FinnhubBase):
    """Government and regulatory data"""

    def uspto_patents(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get USPTO patents"""
        return self._get('/stock/uspto-patent', symbol=symbol, **{'from': from_date, 'to': to_date})

    def visa_applications(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get H1-B visa applications"""
        return self._get('/stock/visa-application', symbol=symbol, **{'from': from_date, 'to': to_date})

    def lobbying_activities(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get senate lobbying activities"""
        return self._get('/stock/lobbying', symbol=symbol, **{'from': from_date, 'to': to_date})

    def usa_spending(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get USA spending data"""
        return self._get('/stock/usa-spending', symbol=symbol, **{'from': from_date, 'to': to_date})

    def congressional_trading(self, symbol: str, from_date: str, to_date: str) -> Dict:
        """Get congressional trading (Premium)"""
        return self._get('/stock/congressional-trading', symbol=symbol, **{'from': from_date, 'to': to_date})

    def bank_branches(self, symbol: str) -> Dict:
        """Get bank branch list (Premium)"""
        return self._get('/bank-branch', symbol=symbol)

    def fda_calendar(self) -> Dict:
        """Get FDA committee calendar"""
        return self._get('/fda-advisory-committee-calendar')

def uspto_patents(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get USPTO patents"""
    return self._get('/stock/uspto-patent', symbol=symbol, **{'from': from_date, 'to': to_date})

def visa_applications(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get H1-B visa applications"""
    return self._get('/stock/visa-application', symbol=symbol, **{'from': from_date, 'to': to_date})

def lobbying_activities(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get senate lobbying activities"""
    return self._get('/stock/lobbying', symbol=symbol, **{'from': from_date, 'to': to_date})

def usa_spending(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get USA spending data"""
    return self._get('/stock/usa-spending', symbol=symbol, **{'from': from_date, 'to': to_date})

def congressional_trading(self, symbol: str, from_date: str, to_date: str) -> Dict:
    """Get congressional trading (Premium)"""
    return self._get('/stock/congressional-trading', symbol=symbol, **{'from': from_date, 'to': to_date})

def bank_branches(self, symbol: str) -> Dict:
    """Get bank branch list (Premium)"""
    return self._get('/bank-branch', symbol=symbol)

def fda_calendar(self) -> Dict:
    """Get FDA committee calendar"""
    return self._get('/fda-advisory-committee-calendar')

class GlobalFilings(FinnhubBase):
    """Global filings and search"""

    def global_filings_search(self, query: str, **kwargs) -> Dict:
        """Search global filings (Premium)"""
        data = {'query': query}
        data.update(kwargs)
        return self._post('/global-filings/search', data=data)

    def search_in_filing(self, filing_id: str, query: str) -> Dict:
        """Search in filing (Premium)"""
        data = {'filingId': filing_id, 'query': query}
        return self._post('/global-filings/search-in-filing', data=data)

    def search_filter(self, field: str, source: str=None) -> Dict:
        """Get search filters (Premium)"""
        return self._get('/global-filings/filter', field=field, source=source)

    def download_filings(self, document_id: str) -> Dict:
        """Download filings (Premium)"""
        return self._get('/global-filings/download', documentId=document_id)

def search_filter(self, field: str, source: str=None) -> Dict:
    """Get search filters (Premium)"""
    return self._get('/global-filings/filter', field=field, source=source)

def download_filings(self, document_id: str) -> Dict:
    """Download filings (Premium)"""
    return self._get('/global-filings/download', documentId=document_id)

class EconomicData(FinnhubBase):
    """Economic data"""

    def country_metadata(self) -> Dict:
        """Get country metadata"""
        return self._get('/country')

    def economic_codes(self) -> Dict:
        """Get economic codes (Premium)"""
        return self._get('/economic/code')

    def economic_data(self, code: str) -> Dict:
        """Get economic data (Premium)"""
        return self._get('/economic', code=code)

def country_metadata(self) -> Dict:
    """Get country metadata"""
    return self._get('/country')

def economic_codes(self) -> Dict:
    """Get economic codes (Premium)"""
    return self._get('/economic/code')

def economic_data(self, code: str) -> Dict:
    """Get economic data (Premium)"""
    return self._get('/economic', code=code)

