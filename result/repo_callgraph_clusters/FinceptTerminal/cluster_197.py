# Cluster 197

class FinnhubUtils:
    """Utility functions for common Finnhub operations"""

    @staticmethod
    def batch_quotes(client: FinnhubClient, symbols: List[str]) -> Dict[str, Dict]:
        """Get quotes for multiple symbols"""
        quotes = {}
        for symbol in symbols:
            try:
                quotes[symbol] = client.market.quote(symbol)
            except Exception as e:
                quotes[symbol] = {'error': str(e)}
        return quotes

    @staticmethod
    def portfolio_analysis(client: FinnhubClient, symbols: List[str]) -> Dict:
        """Get comprehensive data for a portfolio of symbols"""
        portfolio_data = {}
        for symbol in symbols:
            try:
                data = {'quote': client.market.quote(symbol), 'profile': client.company.company_profile2(symbol=symbol), 'financials': client.financials.basic_financials(symbol), 'recommendations': client.estimates.recommendation_trends(symbol)}
                portfolio_data[symbol] = data
            except Exception as e:
                portfolio_data[symbol] = {'error': str(e)}
        return portfolio_data

    @staticmethod
    def market_overview(client: FinnhubClient) -> Dict:
        """Get market overview data"""
        try:
            return {'market_news': client.news.market_news('general'), 'economic_calendar': client.calendar.economic_calendar(), 'ipo_calendar': client.calendar.ipo_calendar('2025-01-01', '2025-12-31')}
        except Exception as e:
            return {'error': str(e)}

@staticmethod
def market_overview(client: FinnhubClient) -> Dict:
    """Get market overview data"""
    try:
        return {'market_news': client.news.market_news('general'), 'economic_calendar': client.calendar.economic_calendar(), 'ipo_calendar': client.calendar.ipo_calendar('2025-01-01', '2025-12-31')}
    except Exception as e:
        return {'error': str(e)}

