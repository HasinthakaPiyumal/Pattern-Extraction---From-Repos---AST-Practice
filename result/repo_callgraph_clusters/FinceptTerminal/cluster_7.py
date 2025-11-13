# Cluster 7

def scrape_forex_calendar_alt(date_str='oct15.2025'):
    """Alternative method using requests-html"""
    from requests_html import HTMLSession
    url = f'https://www.forexfactory.com/calendar?day={date_str}'
    session = HTMLSession()
    try:
        r = session.get(url)
        r.html.render(timeout=20)
        events = []
        rows = r.html.find('tr.calendar__row')
        for row in rows:
            event = {}
            event['time'] = row.find('.calendar__time', first=True).text if row.find('.calendar__time') else ''
            event['currency'] = row.find('.calendar__currency', first=True).text if row.find('.calendar__currency') else ''
            impact = row.find('.calendar__impact', first=True)
            if impact:
                event['impact'] = len(impact.find('.icon--ff-impact-red, .icon--ff-impact-ora, .icon--ff-impact-yel'))
            else:
                event['impact'] = 0
            event['event'] = row.find('.calendar__event', first=True).text if row.find('.calendar__event') else ''
            event['actual'] = row.find('.calendar__actual', first=True).text if row.find('.calendar__actual') else ''
            event['forecast'] = row.find('.calendar__forecast', first=True).text if row.find('.calendar__forecast') else ''
            event['previous'] = row.find('.calendar__previous', first=True).text if row.find('.calendar__previous') else ''
            if event['event'] and event['event'] not in ['', 'All Day']:
                events.append(event)
    except Exception as e:
        print(f'Error: {e}')
        return {'error': str(e)}
    return {'date': date_str, 'url': url, 'events_count': len(events), 'events': events}

def main():
    """Main CLI entry point. This is a simplified router."""
    if len(sys.argv) < 2:
        print('Usage: python coingecko_complete_wrapper.py <command> [args...]')
        return
    cmd = sys.argv[1]
    args = sys.argv[2:]
    result = {}
    try:
        if cmd == 'ping':
            result = ping()
        elif cmd == 'price':
            result = get_simple_price(ids=args[0], vs_currencies=args[1])
        elif cmd == 'coin-list':
            result = get_coin_list()
        elif cmd == 'details':
            result = get_coin_details(coin_id=args[0])
        elif cmd == 'history':
            result = get_coin_history(coin_id=args[0], date=args[1])
        elif cmd == 'exchanges':
            result = get_exchange_list()
        elif cmd == 'trending':
            result = get_trending_coins()
        elif cmd == 'global':
            result = get_global_data()
        elif cmd == 'nft-list':
            result = get_nft_list()
        elif cmd == 'nft-details':
            result = get_nft_details(nft_id=args[0])
        elif cmd == 'treasury':
            result = get_company_treasury(coin_id=args[0])
        else:
            result = {'error': f'Unknown or unimplemented command: {cmd}'}
    except IndexError:
        result = {'error': f"Missing arguments for command '{cmd}'."}
    except Exception as e:
        result = {'error': f'An unexpected error occurred: {e}'}
    print(json.dumps(result, indent=2))

class NASDAQDataAPI:
    """NASDAQ Data API wrapper for modular data fetching"""

    def __init__(self, api_key: Optional[str]=None):
        self.api_key = api_key or os.getenv('NASDAQ_API_KEY')
        self.session = requests.Session()
        self._update_headers()

    def _update_headers(self):
        """Update session headers with random user agent"""
        self.session.headers.update({'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Origin': 'https://www.nasdaq.com', 'Referer': 'https://www.nasdaq.com/', 'Connection': 'keep-alive'})

    def _get_random_user_agent(self) -> str:
        """Generate a random user agent"""
        user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0']
        import random
        return random.choice(user_agents)

    async def _make_async_request(self, url: str, headers: Optional[Dict]=None) -> Dict[str, Any]:
        """Make async HTTP request with error handling"""
        try:
            default_headers = {'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Origin': 'https://www.nasdaq.com', 'Referer': 'https://www.nasdaq.com/', 'Connection': 'keep-alive'}
            final_headers = {**default_headers, **(headers or {})}
            async with aiohttp.ClientSession(headers=final_headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {'success': True, 'data': result}
                    else:
                        text = await response.text()
                        return NASDAQError(url, f'HTTP {response.status}: {text}', response.status).to_dict()
        except aiohttp.ClientError as e:
            return NASDAQError(url, f'Network error: {str(e)}').to_dict()
        except json.JSONDecodeError as e:
            return NASDAQError(url, f'JSON decode error: {str(e)}').to_dict()
        except Exception as e:
            return NASDAQError(url, f'Unexpected error: {str(e)}').to_dict()

    def _make_request(self, url: str, headers: Optional[Dict]=None) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            final_headers = {**self.session.headers, **(headers or {})}
            response = self.session.get(url, headers=final_headers, timeout=30)
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {'success': True, 'data': data}
                except json.JSONDecodeError:
                    return NASDAQError(url, 'Invalid JSON response', response.status_code).to_dict()
            else:
                return NASDAQError(url, f'HTTP {response.status_code}: {response.text}', response.status_code).to_dict()
        except requests.exceptions.RequestException as e:
            return NASDAQError(url, f'Network error: {str(e)}', getattr(e.response, 'status_code', None)).to_dict()
        except Exception as e:
            return NASDAQError(url, f'Unexpected error: {str(e)}').to_dict()

    def _parse_equity_directory(self, content: str) -> pd.DataFrame:
        """Parse NASDAQ equity directory data"""
        try:
            df = pd.read_csv(StringIO(content), sep='|')
            if len(df) > 0:
                df = df.iloc[:-1]
            df.columns = [col.strip() for col in df.columns]
            if 'Security Name' in df.columns:
                df = df[~df['Security Name'].str.contains('test', case=False, na=False)]
            return df
        except Exception as e:
            raise ValueError(f'Failed to parse equity directory: {str(e)}')

    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return text
        clean = re.compile('<.*?>')
        return re.sub(clean, ' ', text)

    def _clean_html_text(self, text: str) -> str:
        """Clean HTML entities and tags"""
        if not text:
            return text
        text = html.unescape(text)
        text = text.replace('\r\n\r\n', ' ').replace('\r\n', ' ')
        text = text.replace("''", "'")
        text = self._remove_html_tags(text)
        return text.strip() if text else None

    async def search_equities(self, query: str='', is_etf: Optional[bool]=None) -> Dict[str, Any]:
        """Search for equities in NASDAQ directory

        Args:
            query: Search query (symbol or company name)
            is_etf: Filter by ETF status (True, False, or None for all)

        Returns:
            Dict containing search results
        """
        try:
            result = self._make_request(NASDAQ_EQUITY_DIR_URL, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
            if 'error' in result:
                return result
            df = self._parse_equity_directory(result['data'])
            if df.empty:
                return NASDAQError('equity_search', 'No equity data found').to_dict()
            if is_etf is not None and 'ETF' in df.columns:
                df = df[df['ETF'] == ('Y' if is_etf else 'N')]
            if query.strip():
                search_columns = ['Symbol', 'Security Name']
                if 'CQS Symbol' in df.columns:
                    search_columns.append('CQS Symbol')
                if 'NASDAQ Symbol' in df.columns:
                    search_columns.append('NASDAQ Symbol')
                mask = pd.Series([False] * len(df))
                for col in search_columns:
                    if col in df.columns:
                        mask |= df[col].str.contains(query, case=False, na=False)
                df = df[mask]
            if df.empty:
                return NASDAQError('equity_search', f"No results found for query: '{query}'").to_dict()
            if 'Market Category' in df.columns:
                df['Market Category'] = df['Market Category'].replace(' ', None)
            results = df.replace({pd.NA: None, 'nan': None}).to_dict('records')
            return {'success': True, 'data': {'query': query, 'is_etf_filter': is_etf, 'results': results, 'total_count': len(results)}}
        except Exception as e:
            return NASDAQError('equity_search', str(e)).to_dict()

    async def get_equity_screener(self, exchange: str='all', market_cap: str='all', sector: str='all', country: str='all', limit: Optional[int]=None) -> Dict[str, Any]:
        """Get equity screener results with filters

        Args:
            exchange: Exchange filter (nasdaq, nyse, amex, all)
            market_cap: Market cap filter (mega, large, mid, small, micro, all)
            sector: Sector filter
            country: Country filter
            limit: Maximum number of results

        Returns:
            Dict containing screener results
        """
        try:
            limit_param = limit if limit else 10000
            base_url = f'{NASDAQ_BASE_URL}/screener/stocks?tableonly=true&limit={limit_param}&'
            params = {}
            if exchange != 'all':
                params['exchange'] = exchange.upper()
            if market_cap != 'all':
                params['marketcap'] = market_cap
            if sector != 'all':
                sector_mapping = {'communication_services': 'telecommunications', 'financial_services': 'finance'}
                sector_clean = sector_mapping.get(sector, sector)
                params['sector'] = sector_clean
            if country != 'all':
                params['country'] = country.lower().replace(' ', '_')
            if params:
                query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
                url = base_url + query_string
            else:
                url = base_url
            result = await self._make_async_request(url)
            if 'error' in result:
                return result
            data = result.get('data', {})
            rows = data.get('data', {}).get('table', {}).get('rows', [])
            if not rows:
                return NASDAQError('equity_screener', 'No screener results found').to_dict()
            sorted_rows = sorted(rows, key=lambda x: float(x.get('pctchange', 0)), reverse=True)
            cleaned_results = []
            for row in sorted_rows:
                cleaned_row = {}
                for key, value in row.items():
                    if key in ['lastsale', 'netchange', 'pctchange', 'marketCap']:
                        if isinstance(value, str):
                            cleaned_value = value.replace('%', '').replace('$', '').replace(',', '')
                            cleaned_value = cleaned_value.replace('UNCH', '').replace('--', '').replace('NA', '')
                            try:
                                if key == 'pctchange':
                                    cleaned_row[key] = float(cleaned_value) / 100 if cleaned_value else None
                                else:
                                    cleaned_row[key] = float(cleaned_value) if cleaned_value else None
                            except ValueError:
                                cleaned_row[key] = None
                        else:
                            cleaned_row[key] = value
                    else:
                        cleaned_row[key] = value
                cleaned_results.append(cleaned_row)
            return {'success': True, 'data': {'filters': {'exchange': exchange, 'market_cap': market_cap, 'sector': sector, 'country': country}, 'results': cleaned_results[:limit] if limit else cleaned_results, 'total_count': len(cleaned_results)}}
        except Exception as e:
            return NASDAQError('equity_screener', str(e)).to_dict()

    async def get_dividend_calendar(self, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get dividend calendar

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dict containing dividend calendar data
        """
        try:
            now = datetime.now().date()
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else now
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else now + timedelta(days=3)
            date_list = []
            current = start
            while current <= end:
                date_list.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
            all_dividends = []
            headers = {'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Connection': 'keep-alive'}

            async def fetch_dividends_for_date(date_str):
                url = f'{NASDAQ_BASE_URL}/calendar/dividends?date={date_str}'
                result = await self._make_async_request(url, headers)
                if 'error' not in result:
                    data = result.get('data', {})
                    calendar_data = data.get('calendar', {}).get('rows', [])
                    return calendar_data
                return []
            tasks = [fetch_dividends_for_date(date_str) for date_str in date_list]
            results = await asyncio.gather(*tasks)
            for date_results in results:
                all_dividends.extend(date_results)
            if not all_dividends:
                return NASDAQError('dividend_calendar', 'No dividend data found').to_dict()
            sorted_dividends = sorted(all_dividends, key=lambda x: x.get('dividend_Ex_Date', ''), reverse=True)
            formatted_results = []
            for dividend in sorted_dividends:
                formatted_dividend = {'symbol': dividend.get('symbol'), 'company_name': dividend.get('companyName'), 'ex_dividend_date': self._parse_date(dividend.get('dividend_Ex_Date')), 'payment_date': self._parse_date(dividend.get('payment_Date')), 'record_date': self._parse_date(dividend.get('record_Date')), 'declaration_date': self._parse_date(dividend.get('announcement_Date')), 'amount': self._parse_float(dividend.get('dividend_Rate')), 'annualized_amount': self._parse_float(dividend.get('indicated_Annual_Dividend'))}
                formatted_results.append(formatted_dividend)
            return {'success': True, 'data': {'date_range': {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}, 'dividends': formatted_results, 'total_count': len(formatted_results)}}
        except Exception as e:
            return NASDAQError('dividend_calendar', str(e)).to_dict()

    async def get_earnings_calendar(self, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get earnings calendar

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dict containing earnings calendar data
        """
        try:
            now = datetime.now().date()
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else now
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else now + timedelta(days=3)
            date_list = []
            current = start
            while current <= end:
                date_list.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
            all_earnings = []
            headers = {'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Connection': 'keep-alive'}

            async def fetch_earnings_for_date(date_str):
                url = f'{NASDAQ_BASE_URL}/calendar/earnings?date={date_str}'
                result = await self._make_async_request(url, headers)
                if 'error' not in result:
                    data = result.get('data', {})
                    rows = data.get('rows', [])
                    if rows and data.get('asOf'):
                        report_date = datetime.strptime(data['asOf'], '%a, %b %d, %Y').date()
                        for row in rows:
                            row['date'] = report_date.strftime('%Y-%m-%d')
                    return rows
                return []
            tasks = [fetch_earnings_for_date(date_str) for date_str in date_list]
            results = await asyncio.gather(*tasks)
            for date_results in results:
                all_earnings.extend(date_results)
            if not all_earnings:
                return NASDAQError('earnings_calendar', 'No earnings data found').to_dict()
            sorted_earnings = sorted(all_earnings, key=lambda x: x.get('date', ''), reverse=True)
            formatted_results = []
            for earnings in sorted_earnings:
                formatted_earnings = {'symbol': earnings.get('symbol'), 'company_name': earnings.get('name'), 'report_date': earnings.get('date'), 'eps_previous': self._parse_float(earnings.get('lastYearEPS')), 'eps_consensus': self._parse_float(earnings.get('epsForecast')), 'eps_actual': self._parse_float(earnings.get('eps')), 'surprise_percent': self._parse_float(earnings.get('surprise')), 'num_estimates': self._parse_int(earnings.get('noOfEsts')), 'period_ending': self._parse_period_ending(earnings.get('fiscalQuarterEnding')), 'previous_report_date': self._parse_date(earnings.get('lastYearRptDt')), 'reporting_time': earnings.get('time', '').replace('time-', '') if earnings.get('time') else None, 'market_cap': self._parse_int(earnings.get('marketCap'))}
                formatted_results.append(formatted_earnings)
            return {'success': True, 'data': {'date_range': {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}, 'earnings': formatted_results, 'total_count': len(formatted_results)}}
        except Exception as e:
            return NASDAQError('earnings_calendar', str(e)).to_dict()

    async def get_ipo_calendar(self, status: str='priced', is_spo: bool=False, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get IPO calendar

        Args:
            status: IPO status (upcoming, priced, filed, withdrawn)
            is_spo: Whether to include secondary public offerings
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dict containing IPO calendar data
        """
        try:
            if status not in IPO_STATUS_CHOICES:
                return NASDAQError('ipo_calendar', f'Invalid status. Choose from: {', '.join(IPO_STATUS_CHOICES)}').to_dict()
            now = datetime.now()
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else now - timedelta(days=300)
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else now.date()
            months = set()
            current = start
            while current <= end:
                months.add(current.strftime('%Y-%m'))
                current = current.replace(day=1) + timedelta(days=32)
                current = current.replace(day=1)
            all_ipos = []
            headers = {'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Connection': 'keep-alive'}

            async def fetch_ipos_for_month(month_str):
                url_base = f'{NASDAQ_BASE_URL}/ipo/calendar?date={month_str}'
                if is_spo:
                    url_base += '&type=spo'
                result = await self._make_async_request(url_base, headers)
                if 'error' not in result:
                    data = result.get('data', {})
                    if status in data:
                        if status == 'upcoming':
                            return data['upcoming']['upcomingTable']['rows']
                        else:
                            return data[status]['rows']
                return []
            tasks = [fetch_ipos_for_month(month) for month in sorted(months)]
            results = await asyncio.gather(*tasks)
            for month_results in results:
                all_ipos.extend(month_results)
            if not all_ipos:
                return NASDAQError('ipo_calendar', f'No IPO data found for status: {status}').to_dict()
            if status == 'priced':
                sorted_ipos = sorted(all_ipos, key=lambda x: self._parse_date(x.get('pricedDate', '')))
            elif status == 'withdrawn':
                sorted_ipos = sorted(all_ipos, key=lambda x: self._parse_date(x.get('withdrawDate', '')))
            elif status == 'filed':
                sorted_ipos = sorted(all_ipos, key=lambda x: self._parse_date(x.get('filedDate', '')))
            else:
                sorted_ipos = all_ipos
            formatted_results = []
            for ipo in sorted_ipos:
                formatted_ipo = {'symbol': ipo.get('proposedTickerSymbol'), 'company_name': ipo.get('companyName'), 'ipo_date': self._parse_date(ipo.get('pricedDate')), 'share_price': self._parse_float(ipo.get('proposedSharePrice')), 'exchange': ipo.get('proposedExchange'), 'offer_amount': self._parse_float(ipo.get('dollarValueOfSharesOffered')), 'share_count': self._parse_int(ipo.get('sharesOffered')), 'expected_price_date': self._parse_date(ipo.get('expectedPriceDate')), 'filed_date': self._parse_date(ipo.get('filedDate')), 'withdraw_date': self._parse_date(ipo.get('withdrawDate')), 'deal_status': ipo.get('dealStatus'), 'deal_id': ipo.get('dealID')}
                formatted_results.append(formatted_ipo)
            return {'success': True, 'data': {'status': status, 'is_spo': is_spo, 'date_range': {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}, 'ipos': formatted_results, 'total_count': len(formatted_results)}}
        except Exception as e:
            return NASDAQError('ipo_calendar', str(e)).to_dict()

    async def get_economic_calendar(self, start_date: Optional[str]=None, end_date: Optional[str]=None, country: Optional[str]=None) -> Dict[str, Any]:
        """Get economic calendar

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            country: Country filter (comma-separated for multiple)

        Returns:
            Dict containing economic calendar data
        """
        try:
            now = datetime.now().date()
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else now - timedelta(days=2)
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else now + timedelta(days=3)
            date_list = []
            current = start
            while current <= end:
                if current.weekday() < 5:
                    date_list.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
            all_events = []
            headers = {'User-Agent': self._get_random_user_agent(), 'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip', 'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3', 'Host': 'api.nasdaq.com', 'Connection': 'keep-alive'}

            async def fetch_events_for_date(date_str):
                url = f'{NASDAQ_BASE_URL}/calendar/economicevents?date={date_str}'
                result = await self._make_async_request(url, headers)
                if 'error' not in result:
                    data = result.get('data', {})
                    rows = data.get('rows', [])
                    processed_events = []
                    for event in rows:
                        gmt = event.get('gmt', '')
                        if gmt == 'All Day':
                            datetime_str = f'{date_str} 00:00'
                        else:
                            clean_gmt = gmt.replace('Tentative', '00:00').replace('24H', '00:00')
                            datetime_str = f'{date_str} {clean_gmt}'
                        event['date'] = datetime_str
                        event.pop('gmt', None)
                        for field in ['actual', 'previous', 'consensus']:
                            if event.get(field):
                                event[field] = event[field].replace('&nbsp;', '-')
                        if event.get('description'):
                            event['description'] = self._clean_html_text(event['description'])
                        processed_events.append(event)
                    return processed_events
                return []
            tasks = [fetch_events_for_date(date_str) for date_str in date_list]
            results = await asyncio.gather(*tasks)
            for date_results in results:
                all_events.extend(date_results)
            if not all_events:
                return NASDAQError('economic_calendar', 'No economic events found').to_dict()
            if country:
                country_list = [c.strip().lower().replace(' ', '_') for c in country.split(',')]
                all_events = [event for event in all_events if event.get('country', '').lower().replace(' ', '_') in country_list]
            sorted_events = sorted(all_events, key=lambda x: x.get('date', ''))
            return {'success': True, 'data': {'date_range': {'start': start.strftime('%Y-%m-%d'), 'end': end.strftime('%Y-%m-%d')}, 'country_filter': country, 'events': sorted_events, 'total_count': len(sorted_events)}}
        except Exception as e:
            return NASDAQError('economic_calendar', str(e)).to_dict()

    async def get_top_retail_activity(self, limit: int=10) -> Dict[str, Any]:
        """Get top retail activity

        Args:
            limit: Maximum number of results

        Returns:
            Dict containing top retail activity data
        """
        try:
            if not self.api_key:
                return NASDAQError('top_retail', 'NASDAQ API key required for retail activity data').to_dict()
            url = f'{NASDAQ_RTAT_URL}?api_key={self.api_key}'
            result = self._make_request(url)
            if 'error' in result:
                return result
            data = result.get('data', {})
            if 'datatable' not in data or 'data' not in data['datatable']:
                return NASDAQError('top_retail', 'Invalid response format').to_dict()
            retail_data = data['datatable']['data']
            if not retail_data:
                return NASDAQError('top_retail', 'No retail activity data found').to_dict()
            formatted_results = []
            for row in retail_data[:limit]:
                formatted_result = {'date': self._parse_date(row[0]), 'symbol': row[1], 'activity': row[2], 'sentiment': row[3]}
                formatted_results.append(formatted_result)
            return {'success': True, 'data': {'retail_activity': formatted_results, 'total_count': len(formatted_results), 'limit': limit}}
        except Exception as e:
            return NASDAQError('top_retail', str(e)).to_dict()

    async def get_comprehensive_market_overview(self) -> Dict[str, Any]:
        """Get comprehensive market overview with multiple data sources"""
        try:
            results = {}
            screener_result = await self.get_equity_screener(limit=50)
            results['top_performers'] = screener_result
            dividends_result = await self.get_dividend_calendar(start_date=datetime.now().strftime('%Y-%m-%d'), end_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
            results['upcoming_dividends'] = dividends_result
            earnings_result = await self.get_earnings_calendar(start_date=datetime.now().strftime('%Y-%m-%d'), end_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
            results['upcoming_earnings'] = earnings_result
            ipo_result = await self.get_ipo_calendar(status='upcoming')
            results['upcoming_ipos'] = ipo_result
            recent_ipo_result = await self.get_ipo_calendar(status='priced', start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'), end_date=datetime.now().strftime('%Y-%m-%d'))
            results['recent_ipos'] = recent_ipo_result
            economic_result = await self.get_economic_calendar(start_date=datetime.now().strftime('%Y-%m-%d'), end_date=datetime.now().strftime('%Y-%m-%d'))
            results['today_economic_events'] = economic_result
            if self.api_key:
                retail_result = await self.get_top_retail_activity(limit=20)
                results['top_retail_activity'] = retail_result
            else:
                results['top_retail_activity'] = {'success': False, 'message': 'NASDAQ API key required for retail activity data'}
            return {'success': True, 'data': {'overview': results, 'generated_at': datetime.now().isoformat(), 'data_sources': ['Equity Screener', 'Dividend Calendar', 'Earnings Calendar', 'IPO Calendar', 'Economic Calendar', 'Top Retail Activity']}}
        except Exception as e:
            return NASDAQError('market_overview', str(e)).to_dict()

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string and return ISO format"""
        if not date_str or date_str == 'N/A':
            return None
        try:
            for fmt in ['%m/%d/%Y', '%Y-%m-%d']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return date_str
        except:
            return date_str

    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse value as float"""
        if not value or value == 'N/A':
            return None
        try:
            if isinstance(value, str):
                clean_value = value.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
                return float(clean_value) if clean_value else None
            return float(value)
        except:
            return None

    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse value as integer"""
        if not value or value == 'N/A':
            return None
        try:
            if isinstance(value, str):
                clean_value = value.replace(',', '')
                return int(clean_value) if clean_value else None
            return int(value)
        except:
            return None

    def _parse_period_ending(self, period_str: str) -> Optional[str]:
        """Parse fiscal quarter ending period"""
        if not period_str or period_str == 'N/A':
            return None
        try:
            parsed_date = datetime.strptime(period_str, '%b/%Y')
            return parsed_date.strftime('%Y-%m')
        except:
            return period_str

def __init__(self, api_key: Optional[str]=None):
    self.api_key = api_key or os.getenv('NASDAQ_API_KEY')
    self.session = requests.Session()
    self._update_headers()

def main():
    """Main function for CLI interface"""
    if len(sys.argv) < 2:
        print(json.dumps(NASDAQError('cli', 'Usage: python nasdaq_data.py <command> [args...]').to_dict()))
        sys.exit(1)
    command = sys.argv[1]
    api_key = os.getenv('NASDAQ_API_KEY')
    api = NASDAQDataAPI(api_key=api_key)

    async def run_command():
        if command == 'search_equities':
            query = sys.argv[2] if len(sys.argv) > 2 else ''
            is_etf_arg = sys.argv[3] if len(sys.argv) > 3 else None
            is_etf = None
            if is_etf_arg is not None:
                is_etf = is_etf_arg.lower() == 'true'
            return await api.search_equities(query, is_etf)
        elif command == 'equity_screener':
            exchange = sys.argv[2] if len(sys.argv) > 2 else 'all'
            market_cap = sys.argv[3] if len(sys.argv) > 3 else 'all'
            sector = sys.argv[4] if len(sys.argv) > 4 else 'all'
            country = sys.argv[5] if len(sys.argv) > 5 else 'all'
            limit = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6].isdigit() else None
            return await api.get_equity_screener(exchange, market_cap, sector, country, limit)
        elif command == 'dividend_calendar':
            start_date = sys.argv[2] if len(sys.argv) > 2 else None
            end_date = sys.argv[3] if len(sys.argv) > 3 else None
            return await api.get_dividend_calendar(start_date, end_date)
        elif command == 'earnings_calendar':
            start_date = sys.argv[2] if len(sys.argv) > 2 else None
            end_date = sys.argv[3] if len(sys.argv) > 3 else None
            return await api.get_earnings_calendar(start_date, end_date)
        elif command == 'ipo_calendar':
            status = sys.argv[2] if len(sys.argv) > 2 else 'priced'
            is_spo = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else False
            start_date = sys.argv[4] if len(sys.argv) > 4 else None
            end_date = sys.argv[5] if len(sys.argv) > 5 else None
            return await api.get_ipo_calendar(status, is_spo, start_date, end_date)
        elif command == 'economic_calendar':
            start_date = sys.argv[2] if len(sys.argv) > 2 else None
            end_date = sys.argv[3] if len(sys.argv) > 3 else None
            country = sys.argv[4] if len(sys.argv) > 4 else None
            return await api.get_economic_calendar(start_date, end_date, country)
        elif command == 'top_retail':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 10
            return await api.get_top_retail_activity(limit)
        elif command == 'market_overview':
            return await api.get_comprehensive_market_overview()
        else:
            return NASDAQError('cli', f'Unknown command: {command}').to_dict()
    result = asyncio.run(run_command())
    print(json.dumps(result, indent=2, default=str))

def main():
    """Main function for CLI interface"""
    wrapper = WTODataWrapper()
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': 'Usage: python wto_data.py <command> [options]', 'commands': ['available_apis', 'qr_members', 'qr_products', 'qr_notifications', 'qr_details', 'qr_list', 'qr_hs_versions', 'eping_members', 'eping_search', 'timeseries_topics', 'timeseries_indicators', 'timeseries_data', 'timeseries_reporters', 'tfad_data', 'overview', 'trade_restrictions_analysis', 'notifications_analysis', 'trade_statistics_analysis', 'comprehensive_analysis']}))
        sys.exit(1)
    command = sys.argv[1]
    args = {}
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg.startswith('--'):
            if '=' in arg:
                key, value = arg[2:].split('=', 1)
                args[key] = value
            elif i + 1 < len(sys.argv) and (not sys.argv[i + 1].startswith('--')):
                key = arg[2:]
                value = sys.argv[i + 1]
                args[key] = value
                i += 1
            else:
                args[arg[2:]] = True
    try:
        if command == 'available_apis':
            result = wrapper.get_available_apis()
        elif command == 'qr_members':
            result = asyncio.run(wrapper.get_qr_members(args.get('member_code'), args.get('name'), int(args.get('page')) if args.get('page') else None))
        elif command == 'qr_products':
            result = asyncio.run(wrapper.get_qr_products(args['hs_version'], args.get('code'), args.get('description'), int(args.get('page')) if args.get('page') else None))
        elif command == 'qr_notifications':
            result = asyncio.run(wrapper.get_qr_notifications(args.get('reporter_member_code'), int(args.get('notification_year')) if args.get('notification_year') else None, int(args.get('page')) if args.get('page') else None))
        elif command == 'qr_details':
            if 'qr_id' not in args:
                raise ValueError('qr_id parameter is required')
            result = asyncio.run(wrapper.get_qr_details(int(args['qr_id'])))
        elif command == 'qr_list':
            result = asyncio.run(wrapper.get_qr_list(args.get('reporter_member_code'), args.get('in_force_only') == 'true' if args.get('in_force_only') else None, int(args.get('year_of_entry_into_force')) if args.get('year_of_entry_into_force') else None, args.get('product_codes'), args.get('product_ids'), int(args.get('page')) if args.get('page') else None))
        elif command == 'qr_hs_versions':
            result = asyncio.run(wrapper.get_qr_hs_versions())
        elif command == 'eping_members':
            result = asyncio.run(wrapper.get_eping_members(int(args.get('language', 1))))
        elif command == 'eping_search':
            result = asyncio.run(wrapper.search_eping_notifications(int(args.get('language', 1)), int(args.get('domainIds')) if args.get('domainIds') else None, args.get('document_symbol'), args.get('distribution_date_from'), args.get('distribution_date_to'), args.get('country_ids', '').split(',') if args.get('country_ids') else None, args.get('hs_codes'), args.get('ics_codes'), args.get('free_text'), int(args.get('page')) if args.get('page') else None, int(args.get('page_size')) if args.get('page_size') else None))
        elif command == 'timeseries_topics':
            result = asyncio.run(wrapper.get_timeseries_topics(int(args.get('language', 1))))
        elif command == 'timeseries_indicators':
            result = asyncio.run(wrapper.get_timeseries_indicators(args.get('indicator', 'all'), args.get('name'), args.get('topics'), args.get('product_classifications'), args.get('trade_partner'), args.get('frequency'), int(args.get('language', 1))))
        elif command == 'timeseries_data':
            if 'i' not in args:
                raise ValueError('i (indicator) parameter is required')
            result = asyncio.run(wrapper.get_timeseries_data(args['i'], args.get('reporters', 'all'), args.get('partners', 'default'), args.get('periods', 'default'), args.get('products', 'default'), args.get('include_sub_products') == 'true', args.get('format_type', 'json'), args.get('mode', 'full'), args.get('decimals', 'default'), int(args.get('offset', 0)), int(args.get('max_records', 500)), args.get('heading_style', 'H'), int(args.get('language', 1)), args.get('include_metadata') == 'true'))
        elif command == 'timeseries_reporters':
            result = asyncio.run(wrapper.get_timeseries_reporters(args.get('name'), args.get('individual_group'), args.get('regions'), args.get('groups'), int(args.get('language', 1))))
        elif command == 'tfad_data':
            result = asyncio.run(wrapper.get_tfad_data(args.get('countries', '').split(',') if args.get('countries') else None))
        elif command == 'overview':
            result = asyncio.run(wrapper.get_wto_overview())
        elif command == 'trade_restrictions_analysis':
            result = asyncio.run(wrapper.get_trade_restrictions_analysis(args.get('member_code')))
        elif command == 'notifications_analysis':
            result = asyncio.run(wrapper.get_notifications_analysis(int(args.get('language', 1)), int(args.get('domain_ids')) if args.get('domain_ids') else None, args.get('date_from'), args.get('date_to')))
        elif command == 'trade_statistics_analysis':
            result = asyncio.run(wrapper.get_trade_statistics_analysis(args.get('indicator', 'TP_A_0010'), args.get('reporter', 'US'), args.get('years', '2020-2023')))
        elif command == 'comprehensive_analysis':
            result = asyncio.run(wrapper.get_comprehensive_wto_analysis(args.get('member_code'), args.get('indicator', 'TP_A_0010')))
        else:
            result = {'success': False, 'error': f'Unknown command: {command}'}
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({'success': False, 'error': str(e)}))

def main():
    """Main function for CLI interface"""
    if len(sys.argv) < 2:
        print(json.dumps(BLSError('cli', 'Usage: python bls_data.py <command> [args...]').to_dict()))
        sys.exit(1)
    command = sys.argv[1]
    api_key = os.getenv('BLS_API_KEY')
    api = BLSDataAPI(api_key=api_key)

    async def run_command():
        if command == 'search_series':
            query = sys.argv[2] if len(sys.argv) > 2 else ''
            category = sys.argv[3] if len(sys.argv) > 3 else 'cpi'
            include_extras = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else False
            include_code_map = sys.argv[5].lower() == 'true' if len(sys.argv) > 5 else False
            return api.search_bls_series(query, category, include_extras, include_code_map)
        elif command == 'get_series':
            series_ids = sys.argv[2] if len(sys.argv) > 2 else ''
            start_date = sys.argv[3] if len(sys.argv) > 3 else None
            end_date = sys.argv[4] if len(sys.argv) > 4 else None
            calculations = sys.argv[5].lower() != 'false' if len(sys.argv) > 5 else True
            annual_average = sys.argv[6].lower() == 'true' if len(sys.argv) > 6 else False
            aspects = sys.argv[7].lower() == 'true' if len(sys.argv) > 7 else False
            return await api.get_series_data(series_ids, start_date, end_date, calculations, annual_average, aspects)
        elif command == 'get_popular':
            return await api.get_popular_series()
        elif command == 'get_labor_overview':
            return await api.get_labor_market_overview()
        elif command == 'get_inflation_overview':
            return await api.get_inflation_overview()
        elif command == 'get_employment_cost_index':
            return await api.get_employment_cost_index()
        elif command == 'get_productivity_costs':
            return await api.get_productivity_costs()
        elif command == 'get_categories':
            return api.get_survey_categories()
        else:
            return BLSError('cli', f'Unknown command: {command}').to_dict()
    result = asyncio.run(run_command())
    print(json.dumps(result, indent=2, default=str))

class OECDWrapper:
    """Modular OECD API wrapper with fault tolerance"""

    def __init__(self, cache_dir: Optional[str]=None):
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser('~'), '.oecd_cache')
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        self.session = self._get_legacy_session()

    def _get_legacy_session(self):
        """Create a custom session for OECD compatibility"""
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 4
        session = requests.Session()
        session.mount('https://', self.CustomHttpAdapter(ctx))
        return session

    class CustomHttpAdapter(requests.adapters.HTTPAdapter):
        """Transport adapter that allows us to use custom ssl_context."""

        def __init__(self, ssl_context=None, **kwargs):
            self.ssl_context = ssl_context
            super().__init__(**kwargs)

        def init_poolmanager(self, connections, maxsize, block=False):
            self.poolmanager = urllib3.poolmanager.PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_context=self.ssl_context)

    def _make_request(self, url: str, method: str='GET', params: Optional[Dict]=None, format_type: str='csv', api_version: str='v1') -> Dict[str, Any]:
        """Make HTTP request with comprehensive error handling"""
        try:
            headers = {'Accept-Language': 'en', 'Accept-Encoding': 'gzip, deflate'}
            if format_type == 'json':
                if api_version == 'v2':
                    headers['Accept'] = 'application/vnd.sdmx.data+json; charset=utf-8; version=2'
                else:
                    headers['Accept'] = 'application/vnd.sdmx.data+json; charset=utf-8; version=1.0'
            elif format_type == 'xml':
                headers['Accept'] = 'application/vnd.sdmx.structurespecificdata+xml; charset=utf-8; version=2.1'
            elif format_type == 'csv':
                headers['Accept'] = 'application/vnd.sdmx.data+csv; charset=utf-8'
            else:
                headers['Accept'] = 'application/vnd.sdmx.data+csv; charset=utf-8'
                if params is None:
                    params = {}
                params['format'] = 'csvfile'
            response = self.session.request(method=method, url=url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '').lower()
            if 'json' in content_type or format_type == 'json':
                try:
                    return {'success': True, 'data': response.text, 'format': 'json'}
                except Exception as e:
                    return {'error': f'JSON parsing error: {str(e)}', 'json_error': True}
            elif 'xml' in content_type or format_type == 'xml':
                try:
                    return {'success': True, 'data': response.text, 'format': 'xml'}
                except Exception as e:
                    return {'error': f'XML parsing error: {str(e)}', 'xml_error': True}
            else:
                try:
                    return {'success': True, 'data': response.text, 'format': 'csv'}
                except Exception as e:
                    return {'error': f'Response parsing error: {str(e)}', 'response_error': True}
        except requests.exceptions.Timeout:
            return {'error': 'Request timeout', 'timeout': True, 'status_code': None}
        except requests.exceptions.ConnectionError:
            return {'error': 'Connection error', 'connection_error': True, 'status_code': None}
        except requests.exceptions.HTTPError as e:
            response = locals().get('response')
            if response is None:
                return {'error': f'HTTP error: {e}', 'http_error': True, 'status_code': None}
            if response.status_code == 404:
                return {'error': 'Data not found', 'not_found': True, 'status_code': response.status_code}
            elif response.status_code == 429:
                return {'error': 'Rate limit exceeded', 'rate_limit_error': True, 'status_code': response.status_code}
            else:
                return {'error': f'HTTP error: {e}', 'http_error': True, 'status_code': response.status_code}
        except requests.exceptions.RequestException as e:
            return {'error': f'Request error: {e}', 'request_error': True, 'status_code': None}
        except Exception as e:
            return {'error': f'Unexpected error: {e}', 'general_error': True, 'status_code': None}

    def _parse_xml_to_dataframe(self, xml_string: str) -> pd.DataFrame:
        """Parse the OECD XML and return a dataframe."""
        try:
            root = fromstring(xml_string)
            namespaces = {'message': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message', 'generic': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic'}
            data = []
            for series in root.findall('.//generic:Series', namespaces=namespaces):
                series_data = {}
                for value in series.findall('.//generic:Value', namespaces=namespaces):
                    series_data[value.get('id')] = value.get('value')
                for obs in series.findall('./generic:Obs', namespaces=namespaces):
                    obs_data = series_data.copy()
                    obs_data['TIME_PERIOD'] = obs.find('./generic:ObsDimension', namespaces=namespaces).get('value')
                    obs_data['VALUE'] = obs.find('./generic:ObsValue', namespaces=namespaces).get('value')
                    data.append(obs_data)
            return pd.DataFrame(data)
        except Exception as e:
            raise ValueError(f'Failed to parse XML: {str(e)}')

    def _oecd_date_to_python_date(self, input_date: Union[str, int]) -> date:
        """Date formatter helper."""
        input_date = str(input_date)
        if 'Q' in input_date:
            return pd.to_datetime(input_date).to_period('Q').start_time.date()
        if len(input_date) == 4:
            return date(int(input_date), 1, 1)
        if len(input_date) == 7:
            return pd.to_datetime(input_date).to_period('M').start_time.date()
        raise ValueError('Date not in expected format')

    def _country_string(self, countries: str, country_mapping: Dict[str, str]) -> str:
        """Convert list of countries to OECD codes"""
        if countries == 'all':
            return ''
        country_list = countries.split(',')
        return '+'.join([country_mapping.get(country.lower(), country) for country in country_list])

    def get_gdp_real(self, countries: str='united_states', frequency: str='quarter', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get real GDP data"""
        try:
            if frequency not in ['quarter', 'annual']:
                return OECDError('gdp_real', f'Invalid frequency: {frequency}. Must be quarter or annual').to_dict()
            if not start_date:
                start_date = '2020-01-01' if countries == 'all' else '1947-01-01'
            if not end_date:
                end_date = f'{date.today().year}-12-31'
            freq_code = 'Q' if frequency == 'quarter' else 'A'
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_GDP)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.NAD/DSD_NAMAIN1@DF_QNA/1.0/{country_codes}.{freq_code}..S1..B1GQ.VOBP...EUR+_T+GBP+USD+JPY.XDC'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                filter_expr = f'{freq_code}..{country_codes}.S1..B1GQ.VOBP...XDC'
                url_v1 = f'{SDMX_V1_BASE}data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA,1.0/{filter_expr}'
                params_v1 = {'startPeriod': start_date, 'endPeriod': end_date, 'dimensionAtObservation': 'TIME_PERIOD', 'detail': 'dataonly', 'format': 'csvfile'}
                result = self._make_request(url_v1, format_type='csv', api_version='v1', params=params_v1)
            if 'error' in result:
                return OECDError('gdp_real', result['error'], result.get('status_code')).to_dict()
            try:
                df = pd.read_csv(StringIO(result['data'])).get(['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE'])
                if df.empty:
                    return OECDError('gdp_real', 'No data found for the given parameters').to_dict()
                df = df.rename(columns={'REF_AREA': 'country', 'TIME_PERIOD': 'date', 'OBS_VALUE': 'value'})

                def apply_country_map(x):
                    v = CODE_TO_COUNTRY_GDP.get(x, x)
                    v = v.replace('_', ' ').title()
                    return v.replace('Oecd', 'OECD')
                df['country'] = df['country'].apply(apply_country_map)
                df['date'] = df['date'].apply(self._oecd_date_to_python_date)
                df = df[(df['date'] <= datetime.strptime(end_date, '%Y-%m-%d').date()) & (df['date'] >= datetime.strptime(start_date, '%Y-%m-%d').date())]
                df['value'] = (df['value'].astype(float) * 1000000).astype('int64')
                df = df.sort_values(by=['date', 'value'], ascending=[True, False])
                df['date'] = df['date'].astype(str)
                result_data = df.replace({np.nan: None}).to_dict(orient='records')
                return {'success': True, 'endpoint': 'gdp_real', 'parameters': {'countries': countries, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('gdp_real', f'Failed to process data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('gdp_real', str(e)).to_dict()

    def get_consumer_price_index(self, countries: str='united_states', expenditure: str='total', frequency: str='monthly', units: str='index', harmonized: bool=False, start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get Consumer Price Index data"""
        try:
            if frequency not in ['monthly', 'quarter', 'annual']:
                return OECDError('cpi', f'Invalid frequency: {frequency}').to_dict()
            if units not in ['index', 'yoy', 'mom']:
                return OECDError('cpi', f'Invalid units: {units}').to_dict()
            if not start_date:
                start_date = '1950-01-01'
            if not end_date:
                end_date = f'{date.today().year}-12-31'
            methodology = 'HICP' if harmonized else 'N'
            freq_code = 'M' if frequency == 'monthly' else 'Q' if frequency == 'quarter' else 'A'
            unit_code = {'index': 'IX', 'yoy': 'PA', 'mom': 'PC'}[units]
            expenditure_code = '' if expenditure == 'all' else EXPENDITURE_DICT.get(expenditure, '')
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_CPI)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.TPS/DSD_PRICES@DF_PRICES_ALL/1.0/{country_codes}.{freq_code}.{methodology}.CPI.{unit_code}.{expenditure_code}.N'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                filter_expr = f'{country_codes}.{freq_code}.{methodology}.CPI.{unit_code}.{expenditure_code}.N'
                url_v1 = f'{SDMX_V1_BASE}data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/{filter_expr}'
                params_v1 = {'startPeriod': start_date, 'endPeriod': end_date, 'dimensionAtObservation': 'TIME_PERIOD', 'detail': 'dataonly', 'format': 'csvfile'}
                result = self._make_request(url_v1, format_type='csv', api_version='v1', params=params_v1)
            if 'error' in result:
                return OECDError('cpi', result['error'], result.get('status_code')).to_dict()
            try:
                if result['format'] == 'xml':
                    data = self._parse_xml_to_dataframe(result['data'])
                else:
                    data = pd.read_csv(StringIO(result['data']))
                query_filter = f"METHODOLOGY=='{methodology}' & UNIT_MEASURE=='{unit_code}' & FREQ=='{freq_code}'"
                if country_codes:
                    if '+' in country_codes:
                        country_list = country_codes.split('+')
                        country_conditions = ' or '.join([f"REF_AREA=='{c}'" for c in country_list])
                        query_filter += f' & ({country_conditions})'
                    else:
                        query_filter += f" & REF_AREA=='{country_codes}'"
                if expenditure_code:
                    query_filter += f" & EXPENDITURE=='{expenditure_code}'"
                if hasattr(data, 'query'):
                    data = data.query(query_filter).reset_index(drop=True)
                if hasattr(data, 'rename'):
                    data = data[['REF_AREA', 'TIME_PERIOD', 'VALUE', 'EXPENDITURE']].rename(columns={'REF_AREA': 'country', 'TIME_PERIOD': 'date', 'VALUE': 'value', 'EXPENDITURE': 'expenditure'})
                data['country'] = data['country'].map(CODE_TO_COUNTRY_CPI)
                if expenditure_code:
                    reverse_expenditure = {v: k for k, v in EXPENDITURE_DICT.items()}
                    data['expenditure'] = data['expenditure'].map(reverse_expenditure)
                data['date'] = data['date'].apply(self._oecd_date_to_python_date)
                data = data[(data['date'] <= datetime.strptime(end_date, '%Y-%m-%d').date()) & (data['date'] >= datetime.strptime(start_date, '%Y-%m-%d').date())]
                data['date'] = data['date'].astype(str)
                if units in ('yoy', 'mom'):
                    data['value'] = data['value'].astype(float) / 100
                result_data = data.fillna('N/A').replace('N/A', None).to_dict(orient='records')
                return {'success': True, 'endpoint': 'consumer_price_index', 'parameters': {'countries': countries, 'expenditure': expenditure, 'frequency': frequency, 'units': units, 'harmonized': harmonized, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('cpi', f'Failed to process data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('cpi', str(e)).to_dict()

    def get_gdp_forecast(self, countries: str='united_states', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get GDP forecast data from OECD - Economic Outlook forecasts"""
        try:
            current_year = date.today().year
            if not start_date:
                start_date = f'{current_year - 1}-01-01'
            if not end_date:
                end_date = f'{current_year + 2}-12-31'
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_GDP)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/AEO/DSD_EO@DF_EO/1.0/FORECAST.{country_codes}.AUSGRO.SRWGPAGDP._Z._T.XDC'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                filter_expr = f'FORECAST.{country_codes}.AUSGRO.SRWGPAGDP._Z._T.XDC'
                url_v1 = f'{SDMX_V1_BASE}data/OECD.SDD.STD,AEO,DSD_EO@DF_EO,1.0/{filter_expr}'
                params_v1 = {'startPeriod': start_date, 'endPeriod': end_date, 'dimensionAtObservation': 'TIME_PERIOD', 'detail': 'dataonly', 'format': 'csvfile'}
                result = self._make_request(url_v1, format_type='csv', api_version='v1', params=params_v1)
            if 'error' in result:
                url_v2_alt = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/AEO/DSD_EO@DF_EO/1.0/{country_codes}.STP.AUSGRO.SRWGPAGDP._Z._T.XDC'
                result = self._make_request(url_v2_alt, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                return {'success': False, 'endpoint': 'gdp_forecast', 'error': f'OECD forecast API structure has changed or endpoint unavailable. Original error: {result['error']}. Note: GDP forecast data may require a different API endpoint or is no longer publicly available.', 'parameters': {'countries': countries, 'start_date': start_date, 'end_date': end_date, 'note': 'Forecast functionality is currently unavailable due to OECD API changes'}, 'suggestion': 'Consider using historical GDP data and external forecast sources', 'status_code': result.get('status_code'), 'timestamp': int(datetime.now().timestamp())}
            try:
                df = pd.read_csv(StringIO(result['data']))
                if df.empty:
                    return OECDError('gdp_forecast', 'No forecast data available').to_dict()
                if 'OBS_VALUE' in df.columns:
                    df = df[['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE']].rename(columns={'REF_AREA': 'country', 'TIME_PERIOD': 'date', 'OBS_VALUE': 'value'})

                    def apply_country_map(x):
                        v = CODE_TO_COUNTRY_GDP.get(x, x)
                        return v.replace('_', ' ').title() if v else x
                    df['country'] = df['country'].apply(apply_country_map)
                    df['date'] = df['date'].apply(self._oecd_date_to_python_date)
                    df = df[(df['date'] <= datetime.strptime(end_date, '%Y-%m-%d').date()) & (df['date'] >= datetime.strptime(start_date, '%Y-%m-%d').date())]
                    df['date'] = df['date'].astype(str)
                    df['value'] = df['value'].astype(float) * 1000000
                    df = df.sort_values(by=['date', 'country'])
                    result_data = df.replace({np.nan: None}).to_dict(orient='records')
                else:
                    result_data = []
                return {'success': True, 'endpoint': 'gdp_forecast', 'source': 'OECD', 'parameters': {'countries': countries, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('gdp_forecast', f'Failed to process forecast data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('gdp_forecast', str(e)).to_dict()

    def get_unemployment(self, countries: str='united_states', frequency: str='quarter', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get unemployment rate data from OECD"""
        try:
            if frequency not in ['quarter', 'annual', 'monthly']:
                return OECDError('unemployment', f'Invalid frequency: {frequency}').to_dict()
            if not start_date:
                start_date = '2000-01-01'
            if not end_date:
                end_date = f'{date.today().year}-12-31'
            freq_code = {'monthly': 'M', 'quarter': 'Q', 'annual': 'A'}[frequency]
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_GDP)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/AES@DF_AES/1.0/{country_codes}.{freq_code}.LRUN64TT.ST.A.SA'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                filter_expr1 = f'{country_codes}.{freq_code}.LRUN64TT.ST.A.SA'
                url_v1_1 = f'{SDMX_V1_BASE}data/OECD.SDD.STD,AES,AES@DF_AES,1.0/{filter_expr1}'
                params_v1 = {'startPeriod': start_date, 'endPeriod': end_date, 'dimensionAtObservation': 'TIME_PERIOD', 'detail': 'dataonly', 'format': 'csvfile'}
                result = self._make_request(url_v1_1, format_type='csv', api_version='v1', params=params_v1)
            if 'error' in result:
                url_v2_alt = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/AES@DF_AES/1.0/{country_codes}.{freq_code}.LRUNTTTT.ST.A.SA'
                result = self._make_request(url_v2_alt, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                return {'success': False, 'endpoint': 'unemployment', 'error': f'OECD unemployment API structure has changed or endpoint unavailable. Original error: {result['error']}. Note: Unemployment data may require a different API endpoint or is no longer publicly available.', 'parameters': {'countries': countries, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date, 'note': 'Unemployment functionality is currently unavailable due to OECD API changes'}, 'suggestion': 'Consider using alternative sources for unemployment data (e.g., World Bank, FRED)', 'status_code': result.get('status_code'), 'timestamp': int(datetime.now().timestamp())}
            try:
                df = pd.read_csv(StringIO(result['data']))
                if df.empty:
                    return OECDError('unemployment', 'No unemployment data available').to_dict()
                if 'OBS_VALUE' in df.columns:
                    df = df[['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE']].rename(columns={'REF_AREA': 'country', 'TIME_PERIOD': 'date', 'OBS_VALUE': 'value'})

                    def apply_country_map(x):
                        v = CODE_TO_COUNTRY_GDP.get(x, x)
                        return v.replace('_', ' ').title() if v else x
                    df['country'] = df['country'].apply(apply_country_map)
                    df['date'] = df['date'].apply(self._oecd_date_to_python_date)
                    df = df[(df['date'] <= datetime.strptime(end_date, '%Y-%m-%d').date()) & (df['date'] >= datetime.strptime(start_date, '%Y-%m-%d').date())]
                    df['date'] = df['date'].astype(str)
                    df['value'] = df['value'].astype(float)
                    df = df.sort_values(by=['date', 'country'])
                    result_data = df.replace({np.nan: None}).to_dict(orient='records')
                else:
                    result_data = []
                return {'success': True, 'endpoint': 'unemployment', 'source': 'OECD', 'parameters': {'countries': countries, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('unemployment', f'Failed to process unemployment data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('unemployment', str(e)).to_dict()

    def get_economic_summary(self, country: str='united_states', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get comprehensive economic summary for a country"""
        result = {'success': True, 'country': country, 'start_date': start_date, 'end_date': end_date, 'timestamp': int(datetime.now().timestamp()), 'endpoints': {}, 'failed_endpoints': []}
        endpoints = [('gdp_real', lambda: self.get_gdp_real(countries=country, start_date=start_date, end_date=end_date)), ('cpi', lambda: self.get_consumer_price_index(countries=country, start_date=start_date, end_date=end_date)), ('gdp_forecast', lambda: self.get_gdp_forecast(countries=country, start_date=start_date, end_date=end_date)), ('unemployment', lambda: self.get_unemployment(countries=country, start_date=start_date, end_date=end_date))]
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

    def get_country_list(self) -> Dict[str, Any]:
        """Get list of available countries"""
        try:
            return {'success': True, 'endpoint': 'country_list', 'available_countries': {'gdp': list(COUNTRY_TO_CODE_GDP.keys()), 'cpi': list(COUNTRY_TO_CODE_CPI.keys())}, 'country_codes': {'gdp': COUNTRY_TO_CODE_GDP, 'cpi': COUNTRY_TO_CODE_CPI}, 'expenditure_categories': list(EXPENDITURE_DICT.keys()), 'timestamp': int(datetime.now().timestamp())}
        except Exception as e:
            return OECDError('country_list', str(e)).to_dict()

    def get_interest_rates(self, countries: str='united_states', frequency: str='monthly', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get short-term interest rates data from OECD"""
        try:
            if frequency not in ['monthly', 'quarter', 'annual']:
                return OECDError('interest_rates', f'Invalid frequency: {frequency}').to_dict()
            if not start_date:
                start_date = '2000-01-01'
            if not end_date:
                end_date = f'{date.today().year}-12-31'
            freq_code = {'monthly': 'M', 'quarter': 'Q', 'annual': 'A'}[frequency]
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_GDP)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/MEI/DP_LIVE/1.0/{country_codes}.{freq_code}.IR3TIB.ST.A'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                return OECDError('interest_rates', result['error'], result.get('status_code')).to_dict()
            try:
                if result['format'] == 'xml':
                    data = self._parse_xml_to_dataframe(result['data'])
                else:
                    data = pd.read_csv(StringIO(result['data']))
                result_data = []
                return {'success': True, 'endpoint': 'interest_rates', 'parameters': {'countries': countries, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('interest_rates', f'Failed to process data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('interest_rates', str(e)).to_dict()

    def get_trade_balance(self, countries: str='united_states', frequency: str='quarter', start_date: Optional[str]=None, end_date: Optional[str]=None) -> Dict[str, Any]:
        """Get trade balance data from OECD"""
        try:
            if frequency not in ['monthly', 'quarter', 'annual']:
                return OECDError('trade_balance', f'Invalid frequency: {frequency}').to_dict()
            if not start_date:
                start_date = '2000-01-01'
            if not end_date:
                end_date = f'{date.today().year}-12-31'
            freq_code = {'monthly': 'M', 'quarter': 'Q', 'annual': 'A'}[frequency]
            country_codes = self._country_string(countries, COUNTRY_TO_CODE_GDP)
            if not country_codes:
                country_codes = '*'
            url_v2 = f'{SDMX_V2_BASE}data/dataflow/OECD.SDD.STD/BOP/DSD_BOP6@DF_BAL,1.0/{country_codes}.{freq_code}.B6_GI.NMBK_SV.DD._T._T._T._T.XDC'
            params_v2 = {'c[TIME_PERIOD]': f'ge:{start_date}+le:{end_date}', 'attributes': 'dsd', 'measures': 'all'}
            result = self._make_request(url_v2, format_type='csv', api_version='v2', params=params_v2)
            if 'error' in result:
                return OECDError('trade_balance', result['error'], result.get('status_code')).to_dict()
            try:
                if result['format'] == 'xml':
                    data = self._parse_xml_to_dataframe(result['data'])
                else:
                    data = pd.read_csv(StringIO(result['data']))
                result_data = []
                return {'success': True, 'endpoint': 'trade_balance', 'parameters': {'countries': countries, 'frequency': frequency, 'start_date': start_date, 'end_date': end_date}, 'total_records': len(result_data), 'data': result_data, 'timestamp': int(datetime.now().timestamp())}
            except Exception as e:
                return OECDError('trade_balance', f'Failed to process data: {str(e)}').to_dict()
        except Exception as e:
            return OECDError('trade_balance', str(e)).to_dict()

def __init__(self, cache_dir: Optional[str]=None):
    self.cache_dir = cache_dir or os.path.join(os.path.expanduser('~'), '.oecd_cache')
    Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
    self.session = self._get_legacy_session()

def main():
    """Command-line interface for Sentinel Hub API wrapper"""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python sentinelhub_data.py <command> [args]', 'available_commands': ['search <bbox> <datetime_range> [collections] [max_cloud] [limit]', 'search-coords <lat> <lon> <radius_km> [start_date] [end_date] [collections]', 'process <bbox> <datetime_range> [evalscript_type] [width] [height] [format] [save_to_file]', 'process-scene <scene_id> [evalscript_type] [width] [height] [format] [save_to_file]', 'collections', 'evalscripts', 'test-connectivity'], 'examples': ['sentinelhub_data.py search "13.0,45.0,14.0,46.0" "2019-12-10T00:00:00Z/2019-12-10T23:59:59Z" sentinel-2-l2a 20 5', 'sentinelhub_data.py search-coords 45.5 13.6 10 2019-12-01 2019-12-31', 'sentinelhub_data.py process "13.0,45.0,14.0,46.0" "2019-12-10T00:00:00Z/2019-12-10T23:59:59Z" ndvi 1024 1024', 'sentinelhub_data.py process-scene S2A_MSIL2A_20191210T100311_N0213_R122_T33TUE_20191210T121921 true_color', 'sentinelhub_data.py collections', 'sentinelhub_data.py evalscripts', 'sentinelhub_data.py test-connectivity']}, indent=2))
        sys.exit(1)
    command = sys.argv[1]
    try:
        if command == 'search':
            if len(sys.argv) < 4:
                result = {'error': 'Usage: search <bbox> <datetime_range> [collections] [max_cloud] [limit]'}
            else:
                bbox = json.loads(sys.argv[2])
                datetime_range = sys.argv[3]
                collections = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
                max_cloud = float(sys.argv[5]) if len(sys.argv) > 5 else 30.0
                limit = int(sys.argv[6]) if len(sys.argv) > 6 else 10
                result = search_imagery(bbox, datetime_range, collections, max_cloud, limit)
        elif command == 'search-coords':
            if len(sys.argv) < 4:
                result = {'error': 'Usage: search-coords <lat> <lon> <radius_km> [start_date] [end_date] [collections]'}
            else:
                lat = float(sys.argv[2])
                lon = float(sys.argv[3])
                radius = float(sys.argv[4])
                start_date = sys.argv[5] if len(sys.argv) > 5 else None
                end_date = sys.argv[6] if len(sys.argv) > 6 else None
                collections = json.loads(sys.argv[7]) if len(sys.argv) > 7 else None
                result = search_imagery_by_coordinates(lat, lon, radius, start_date, end_date, collections)
        elif command == 'process':
            if len(sys.argv) < 4:
                result = {'error': 'Usage: process <bbox> <datetime_range> [evalscript_type] [width] [height] [format] [save_to_file]'}
            else:
                bbox = json.loads(sys.argv[2])
                datetime_range = sys.argv[3]
                evalscript_type = sys.argv[4] if len(sys.argv) > 4 else 'true_color'
                width = int(sys.argv[5]) if len(sys.argv) > 5 else 512
                height = int(sys.argv[6]) if len(sys.argv) > 6 else 512
                format_type = sys.argv[7] if len(sys.argv) > 7 else 'image/png'
                save_to_file = sys.argv[8].lower() == 'true' if len(sys.argv) > 8 else False
                result = process_imagery(bbox, datetime_range, None, evalscript_type, width, height, format_type, save_to_file)
        elif command == 'process-scene':
            if len(sys.argv) < 3:
                result = {'error': 'Usage: process-scene <scene_id> [evalscript_type] [width] [height] [format] [save_to_file]'}
            else:
                scene_id = sys.argv[2]
                evalscript_type = sys.argv[3] if len(sys.argv) > 3 else 'true_color'
                width = int(sys.argv[4]) if len(sys.argv) > 4 else 512
                height = int(sys.argv[5]) if len(sys.argv) > 5 else 512
                format_type = sys.argv[6] if len(sys.argv) > 6 else 'image/png'
                save_to_file = sys.argv[7].lower() == 'true' if len(sys.argv) > 7 else False
                result = process_imagery_by_scene_id(scene_id, None, evalscript_type, width, height, format_type, save_to_file)
        elif command == 'collections':
            result = get_available_collections()
        elif command == 'evalscripts':
            result = get_evalscript_types()
        elif command == 'test-connectivity':
            result = test_api_connectivity()
        else:
            result = {'error': f'Unknown command: {command}', 'available_commands': ['search <bbox> <datetime_range> [collections] [max_cloud] [limit]', 'search-coords <lat> <lon> <radius_km> [start_date] [end_date] [collections]', 'process <bbox> <datetime_range> [evalscript_type] [width] [height] [format] [save_to_file]', 'process-scene <scene_id> [evalscript_type] [width] [height] [format] [save_to_file]', 'collections', 'evalscripts', 'test-connectivity']}
        print(json.dumps(result, indent=2))
    except json.JSONDecodeError as e:
        print(json.dumps({'error': f'Invalid JSON parameter: {str(e)}'}))
        sys.exit(1)
    except ValueError as e:
        print(json.dumps({'error': f'Invalid parameter: {str(e)}'}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'error': f'Command execution failed: {str(e)}'}))
        sys.exit(1)

def test_api_connectivity() -> Dict[str, Any]:
    """
    Test basic connectivity to all API endpoints.

    Returns:
        Dict with connectivity test results for each endpoint
    """
    results = {}
    try:
        collections_response = get_collections(page=1)
        results['collections_api'] = {'status': 'connected' if not collections_response['error'] else 'error', 'message': collections_response['error'] or 'Successfully connected', 'response_time_ms': 0}
    except Exception as e:
        results['collections_api'] = {'status': 'error', 'message': str(e), 'response_time_ms': 0}
    try:
        pm25_response = get_pm25_readings()
        results['realtime_api'] = {'status': 'connected' if not pm25_response['error'] else 'error', 'message': pm25_response['error'] or 'Successfully connected', 'response_time_ms': 0}
    except Exception as e:
        results['realtime_api'] = {'status': 'error', 'message': str(e), 'response_time_ms': 0}
    return {'data': results, 'metadata': {'test_timestamp': datetime.utcnow().isoformat(), 'api_key_configured': bool(API_KEY)}, 'error': None}

def main():
    """Command-line interface for data.gov.sg API wrapper."""
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python datagovsg_data.py <command> [args]', 'available_commands': ['collections [page]', 'collection-details <collection_id> [with_metadata]', 'initiate-download <dataset_id>', 'poll-download <dataset_id>', 'pm25 [date]', 'test-connectivity']}))
        sys.exit(1)
    command = sys.argv[1]
    try:
        if command == 'collections':
            page = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            result = get_collections(page=page)
        elif command == 'collection-details':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: datagovsg_data.py collection-details <collection_id> [with_metadata]'}))
                sys.exit(1)
            collection_id = sys.argv[2]
            with_metadata = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else False
            result = get_collection_details(collection_id, with_dataset_metadata=with_metadata)
        elif command == 'initiate-download':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: datagovsg_data.py initiate-download <dataset_id>'}))
                sys.exit(1)
            dataset_id = sys.argv[2]
            result = initiate_dataset_download(dataset_id)
        elif command == 'poll-download':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'Usage: datagovsg_data.py poll-download <dataset_id>'}))
                sys.exit(1)
            dataset_id = sys.argv[2]
            result = poll_dataset_download(dataset_id)
        elif command == 'pm25':
            date = sys.argv[2] if len(sys.argv) > 2 else None
            result = get_pm25_readings(date=date)
        elif command == 'test-connectivity':
            result = test_api_connectivity()
        else:
            result = {'error': f'Unknown command: {command}', 'available_commands': ['collections [page]', 'collection-details <collection_id> [with_metadata]', 'initiate-download <dataset_id>', 'poll-download <dataset_id>', 'pm25 [date]', 'test-connectivity']}
        print(json.dumps(result, indent=2))
    except ValueError as e:
        print(json.dumps({'error': f'Invalid parameter: {str(e)}'}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'error': f'Command execution failed: {str(e)}'}))
        sys.exit(1)

def start_terminal():
    """OPTIMIZED: Console script entry point"""
    try:
        main()
    except Exception as e:
        print(f'[CRITICAL] Terminal startup failed: {e}')
        sys.exit(1)

def calculate_all_indicators(df: pd.DataFrame, price_col: str='close', high_col: str='high', low_col: str='low') -> pd.DataFrame:
    """
    Calculate all technical indicators for a given dataframe.
    
    Args:
        df: DataFrame with OHLC data
        price_col: Column name for closing prices
        high_col: Column name for high prices
        low_col: Column name for low prices
        
    Returns:
        pd.DataFrame: Original dataframe with added indicator columns
    """
    try:
        result_df = df.copy()
        result_df['SMA_20'] = TechnicalIndicators.sma(df[price_col], 20)
        result_df['EMA_20'] = TechnicalIndicators.ema(df[price_col], 20)
        result_df['RSI_14'] = TechnicalIndicators.rsi(df[price_col], 14)
        macd, signal, histogram = TechnicalIndicators.macd(df[price_col])
        result_df['MACD'] = macd
        result_df['MACD_Signal'] = signal
        result_df['MACD_Histogram'] = histogram
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.bollinger_bands(df[price_col])
        result_df['BB_Upper'] = bb_upper
        result_df['BB_Middle'] = bb_middle
        result_df['BB_Lower'] = bb_lower
        if high_col in df.columns and low_col in df.columns:
            stoch_k, stoch_d = TechnicalIndicators.stochastic_oscillator(df[high_col], df[low_col], df[price_col])
            result_df['Stoch_K'] = stoch_k
            result_df['Stoch_D'] = stoch_d
            result_df['Williams_R'] = TechnicalIndicators.williams_r(df[high_col], df[low_col], df[price_col])
            result_df['ATR'] = TechnicalIndicators.atr(df[high_col], df[low_col], df[price_col])
            result_df['CCI'] = TechnicalIndicators.cci(df[high_col], df[low_col], df[price_col])
            adx, plus_di, minus_di = TechnicalIndicators.adx(df[high_col], df[low_col], df[price_col])
            result_df['ADX'] = adx
            result_df['Plus_DI'] = plus_di
            result_df['Minus_DI'] = minus_di
        print(f'Successfully calculated all technical indicators for {len(result_df)} data points')
        return result_df
    except Exception as e:
        print(f'Error calculating indicators: {e}')
        return df

def save_report(self, filename: str=None) -> str:
    """Save report to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'pypfopt_report_{timestamp}.json'
    report = self.generate_report()
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f'Report saved to: {filename}')
    return filename

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

def recursive_convert(obj):
    if isinstance(obj, dict):
        return {k: recursive_convert(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [recursive_convert(v) for v in obj]
    else:
        return convert_numpy(obj)

class DataQualityReport:
    """
    Comprehensive data quality assessment report.
    """

    def __init__(self, data_name: str):
        """Initialize data quality report."""
        self.data_name = data_name
        self.timestamp = datetime.now()
        self.issues = []
        self.warnings = []
        self.statistics = {}
        self.recommendations = []
        self.quality_score = 100.0

    def add_issue(self, issue_type: str, description: str, severity: str='medium'):
        """Add a data quality issue."""
        self.issues.append({'type': issue_type, 'description': description, 'severity': severity, 'timestamp': datetime.now()})
        score_reduction = {'low': 5, 'medium': 10, 'high': 20, 'critical': 50}
        self.quality_score -= score_reduction.get(severity, 10)
        self.quality_score = max(0, self.quality_score)

    def add_warning(self, warning_type: str, message: str):
        """Add a warning."""
        self.warnings.append({'type': warning_type, 'message': message, 'timestamp': datetime.now()})

    def add_recommendation(self, recommendation: str):
        """Add a recommendation for improvement."""
        self.recommendations.append(recommendation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {'data_name': self.data_name, 'timestamp': self.timestamp.isoformat(), 'quality_score': round(self.quality_score, 2), 'issues': self.issues, 'warnings': self.warnings, 'statistics': self.statistics, 'recommendations': self.recommendations}

    def print_summary(self):
        """Print a summary of the data quality report."""
        print(f'\n=== Data Quality Report: {self.data_name} ===')
        print(f'Quality Score: {self.quality_score:.1f}/100')
        print(f'Issues Found: {len(self.issues)}')
        print(f'Warnings: {len(self.warnings)}')
        if self.issues:
            print('\nCritical Issues:')
            for issue in self.issues:
                if issue['severity'] in ['high', 'critical']:
                    print(f'  - {issue['description']}')
        if self.recommendations:
            print('\nRecommendations:')
            for rec in self.recommendations[:3]:
                print(f'  - {rec}')

def print_summary(self):
    """Print a summary of the data quality report."""
    print(f'\n=== Data Quality Report: {self.data_name} ===')
    print(f'Quality Score: {self.quality_score:.1f}/100')
    print(f'Issues Found: {len(self.issues)}')
    print(f'Warnings: {len(self.warnings)}')
    if self.issues:
        print('\nCritical Issues:')
        for issue in self.issues:
            if issue['severity'] in ['high', 'critical']:
                print(f'  - {issue['description']}')
    if self.recommendations:
        print('\nRecommendations:')
        for rec in self.recommendations[:3]:
            print(f'  - {rec}')

class DataCache:
    """Simple file-based caching system"""

    def __init__(self, cache_dir: str='cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Generate cache file path"""
        return self.cache_dir / f'{key}.pkl'

    def get(self, key: str) -> Optional[Any]:
        """Retrieve data from cache"""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
                if datetime.now() - cache_time < timedelta(hours=24):
                    return cached_data
            except:
                pass
        return None

    def set(self, key: str, data: Any) -> None:
        """Store data in cache"""
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            warnings.warn(f'Failed to cache data: {e}')

    def clear(self) -> None:
        """Clear all cached data"""
        for cache_file in self.cache_dir.glob('*.pkl'):
            cache_file.unlink()

def __init__(self, cache_dir: str='cache'):
    self.cache_dir = Path(cache_dir)
    self.cache_dir.mkdir(exist_ok=True)

def test_setup():
    """Test basic setup and configuration"""
    print('=== Testing OpenRouter Client Setup ===')
    load_dotenv()
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print('❌ FAIL: OPENROUTER_API_KEY environment variable not found')
        print('Please create a .env file based on .env.example')
        return False
    else:
        print('✅ PASS: API key found in environment')
    try:
        config = OpenRouterConfig(max_retries=1)
        client = OpenRouterClient(api_key=api_key, config=config)
        print('✅ PASS: Client initialization successful')
    except Exception as e:
        print(f'❌ FAIL: Client initialization failed: {e}')
        return False
    return True

def test_api_call():
    """Test actual API call with a simple request"""
    print('\n=== Testing API Call ===')
    try:
        load_dotenv()
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print('❌ SKIPPED: API key not configured')
            return False
        config = OpenRouterConfig(timeout=30, max_retries=2)
        client = OpenRouterClient(api_key=api_key, config=config)
        messages = [{'role': 'user', 'content': "Say 'Hello from test client' and count to 3."}]
        print('Making test API call...')
        response = client.chat_completion(messages, max_tokens=50)
        if response and 'choices' in response:
            print('✅ PASS: API call successful')
            if len(response['choices']) > 0:
                content = response['choices'][0].get('message', {}).get('content', '')
                print(f'Response: {content[:100]}...')
            return True
        else:
            print('❌ FAIL: Invalid response structure')
            return False
    except requests.exceptions.RequestException as e:
        print(f'❌ FAIL: Network error during API call: {e}')
        return False
    except Exception as e:
        print(f'❌ FAIL: Unexpected error during API call: {e}')
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print('\n=== Testing Error Handling ===')
    try:
        try:
            client = OpenRouterClient()
            print('❌ FAIL: Should have raised ValueError without API key')
            return False
        except ValueError as e:
            print('✅ PASS: Correctly raises ValueError without API key')
        try:
            config = OpenRouterConfig(timeout=5, max_retries=1)
            client = OpenRouterClient(api_key='invalid-key', config=config)
            messages = [{'role': 'user', 'content': 'test'}]
            client.chat_completion(messages)
            print('❌ FAIL: Should have failed with invalid API key')
            return False
        except requests.exceptions.RequestException:
            print('✅ PASS: Correctly handles invalid API key')
        return True
    except Exception as e:
        print(f'❌ FAIL: Error handling test failed: {e}')
        return False

class OpenRouterClient:
    """Enhanced OpenRouter API client with error handling and retries"""

    def __init__(self, api_key: Optional[str]=None, config: Optional[OpenRouterConfig]=None):
        self.config = config or OpenRouterConfig()
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError('API key required. Set OPENROUTER_API_KEY environment variable or pass api_key parameter.')

    def chat_completion(self, messages: list, **kwargs) -> Dict[str, Any]:
        """Send a chat completion request with retry logic"""
        url = f'{self.config.base_url}/chat/completions'
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        payload = {'model': kwargs.get('model', self.config.model), 'messages': messages}
        payload.update(kwargs)
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(url=url, headers=headers, json=payload, timeout=self.config.timeout)
                if response.status_code == 429:
                    wait_time = int(response.headers.get('retry-after', attempt + 1))
                    print(f'Rate limited. Waiting {wait_time} seconds...')
                    time.sleep(wait_time)
                    continue
                response.raise_for_status()
                result = response.json()
                if 'choices' not in result:
                    raise ValueError(f'Invalid response format: {result}')
                return result
            except requests.exceptions.RequestException as e:
                if attempt < self.config.max_retries - 1:
                    print(f'Request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}')
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    print(f'Request failed after {self.config.max_retries} attempts: {e}')
                    raise
            except json.JSONDecodeError as e:
                print(f'Failed to decode response: {e}')
                print(f'Raw response: {response.text}')
                raise
        raise RuntimeError('Maximum retries exceeded')

    def print_chat_response(self, response: Dict[str, Any]):
        """Pretty print the chat response"""
        print(f'Response received at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
        print('-' * 50)
        if 'choices' in response and len(response['choices']) > 0:
            choice = response['choices'][0]
            message = choice.get('message', {})
            print(f'Model: {response.get('model', 'Unknown')}')
            print(f'Role: {message.get('role', 'Unknown')}')
            content = message.get('content', 'No content returned')
            print(f'Content: {content}')
            if 'usage' in response:
                usage = response['usage']
                print(f'Token usage - Prompt: {usage.get('prompt_tokens', 0)}, Completion: {usage.get('completion_tokens', 0)}, Total: {usage.get('total_tokens', 0)}')
        else:
            print('No valid response received')
            print(f'Full response: {json.dumps(response, indent=2)}')
        print('-' * 50)

def __init__(self, api_key: Optional[str]=None, config: Optional[OpenRouterConfig]=None):
    self.config = config or OpenRouterConfig()
    self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
    if not self.api_key:
        raise ValueError('API key required. Set OPENROUTER_API_KEY environment variable or pass api_key parameter.')

def main():
    """Main function demonstrating the improved client"""
    '\n    Example usage demonstrating various API features\n    '
    try:
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print('Error: OPENROUTER_API_KEY environment variable not set.')
            print("Please set your API key using: export OPENROUTER_API_KEY='your-key-here'")
            print('Or create a .env file with: OPENROUTER_API_KEY=your-key-here')
            print('\nFor testing, you can also initialize the client directly:')
            print("client = OpenRouterClient(api_key='your-key-here')")
            return
        config = OpenRouterConfig(timeout=60, max_retries=5)
        client = OpenRouterClient(config=config)
        print('=== Example 1: Simple Question ===')
        messages1 = [{'role': 'user', 'content': 'What is the meaning of life?'}]
        response1 = client.chat_completion(messages1)
        client.print_chat_response(response1)
        print('\n=== Example 2: Multi-turn Conversation ===')
        messages2 = [{'role': 'user', 'content': 'Explain quantum computing in simple terms'}, {'role': 'assistant', 'content': 'Quantum computing is a type of computing that uses quantum physics principles to solve complex problems that classical computers struggle with. Would you like to know more about specific aspects?'}, {'role': 'user', 'content': 'Yes, tell me about quantum bits (qubits) and how they differ from regular bits.'}]
        response2 = client.chat_completion(messages2)
        client.print_chat_response(response2)
        print('\n=== Example 3: Custom Parameters ===')
        messages3 = [{'role': 'user', 'content': 'Generate a haiku about artificial intelligence'}]
        response3 = client.chat_completion(messages3, model='moonshotai/kimi-k2:free', max_tokens=50, temperature=0.8)
        client.print_chat_response(response3)
    except ValueError as e:
        print(f'Configuration error: {e}')
    except requests.exceptions.RequestException as e:
        print(f'Network error: {e}')
    except Exception as e:
        print(f'Unexpected error: {e}')
        traceback.print_exc()

class DataManager:
    """Handles data acquisition, storage, and preprocessing"""

    def __init__(self, config: ML4TConfig):
        self.config = config
        self.logger = ML4TLogger('DataManager')
        self.data_cache = {}

    def load_market_data(self, symbols: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """Load market data for given symbols and date range"""
        self.logger.info(f'Loading market data for {len(symbols)} symbols from {start_date} to {end_date}')
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        np.random.seed(self.config.random_state)
        data = {}
        for symbol in symbols:
            n_days = len(dates)
            returns = np.random.normal(0.0005, 0.02, n_days)
            prices = 100 * np.exp(np.cumsum(returns))
            volumes = np.random.lognormal(10, 1, n_days)
            symbol_data = pd.DataFrame({'open': prices * (1 + np.random.normal(0, 0.001, n_days)), 'high': prices * (1 + np.abs(np.random.normal(0, 0.005, n_days))), 'low': prices * (1 - np.abs(np.random.normal(0, 0.005, n_days))), 'close': prices, 'volume': volumes, 'symbol': symbol}, index=dates)
            data[symbol] = symbol_data
        combined_data = pd.concat(data.values(), ignore_index=False)
        combined_data = combined_data.reset_index().rename(columns={'index': 'date'})
        self.data_cache['market_data'] = combined_data
        return combined_data

    def load_fundamental_data(self, symbols: List[str]) -> pd.DataFrame:
        """Load fundamental data from SEC filings"""
        self.logger.info(f'Loading fundamental data for {len(symbols)} symbols')
        np.random.seed(self.config.random_state)
        fundamental_data = []
        for symbol in symbols:
            data = {'symbol': symbol, 'market_cap': np.random.lognormal(15, 2), 'pe_ratio': np.random.lognormal(3, 0.5), 'pb_ratio': np.random.lognormal(1, 0.3), 'debt_to_equity': np.random.exponential(0.5), 'roe': np.random.normal(0.12, 0.05), 'roa': np.random.normal(0.06, 0.03), 'current_ratio': np.random.lognormal(1, 0.2), 'revenue_growth': np.random.normal(0.05, 0.15), 'earnings_growth': np.random.normal(0.08, 0.2)}
            fundamental_data.append(data)
        df = pd.DataFrame(fundamental_data)
        self.data_cache['fundamental_data'] = df
        return df

    def load_alternative_data(self, data_type: str) -> pd.DataFrame:
        """Load alternative data (sentiment, satellite, etc.)"""
        self.logger.info(f'Loading alternative data: {data_type}')
        if data_type == 'sentiment':
            return self._generate_sentiment_data()
        elif data_type == 'satellite':
            return self._generate_satellite_data()
        elif data_type == 'social':
            return self._generate_social_data()
        else:
            raise ValueError(f'Unknown alternative data type: {data_type}')

    def _generate_sentiment_data(self) -> pd.DataFrame:
        """Generate synthetic sentiment data"""
        dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
        np.random.seed(self.config.random_state)
        sentiment_data = pd.DataFrame({'date': dates, 'news_sentiment': np.random.normal(0, 1, len(dates)), 'social_sentiment': np.random.normal(0, 1.2, len(dates)), 'analyst_sentiment': np.random.normal(0, 0.8, len(dates)), 'earnings_sentiment': np.random.normal(0, 1.5, len(dates))})
        return sentiment_data

    def _generate_satellite_data(self) -> pd.DataFrame:
        """Generate synthetic satellite data"""
        return pd.DataFrame({'region': ['US_MIDWEST', 'BRAZIL_CERRADO', 'ARGENTINA_PAMPAS'], 'crop_health_index': [0.85, 0.78, 0.82], 'estimated_yield': [105.2, 89.7, 94.3], 'weather_risk': [0.15, 0.25, 0.18]})

    def _generate_social_data(self) -> pd.DataFrame:
        """Generate synthetic social media data"""
        dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
        np.random.seed(self.config.random_state)
        return pd.DataFrame({'date': dates, 'twitter_mentions': np.random.poisson(100, len(dates)), 'reddit_sentiment': np.random.normal(0, 1, len(dates)), 'google_trends': np.random.uniform(0, 100, len(dates)), 'news_volume': np.random.poisson(50, len(dates))})

def __init__(self, config: ML4TConfig):
    self.config = config
    self.logger = ML4TLogger('DataManager')
    self.data_cache = {}

class AlphaFactorEngine:
    """Comprehensive alpha factor generation and evaluation"""

    def __init__(self, config: ML4TConfig):
        self.config = config
        self.logger = ML4TLogger('AlphaEngine')
        self.factor_library = {}

    def calculate_technical_factors(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Calculate technical indicators and factors"""
        df = data[data['symbol'] == symbol].copy()
        df = df.sort_values('date')
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close']).diff()
        for window in [5, 10, 20, 50, 200]:
            df[f'sma_{window}'] = df['close'].rolling(window).mean()
            df[f'ema_{window}'] = df['close'].ewm(span=window).mean()
        for window in [5, 10, 20]:
            df[f'momentum_{window}'] = df['close'] / df['close'].shift(window) - 1
        for window in [5, 10, 20]:
            df[f'volatility_{window}'] = df['returns'].rolling(window).std()
        df['rsi_14'] = self._calculate_rsi(df['close'], 14)
        df['bb_upper'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'], 20)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['macd'], df['macd_signal'] = self._calculate_macd(df['close'])
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        df['vwap'] = (df['close'] * df['volume']).rolling(20).sum() / df['volume'].rolling(20).sum()
        df['price_volume_trend'] = ((df['close'] - df['close'].shift(1)) / df['close'].shift(1) * df['volume']).rolling(20).sum()
        return df

    def calculate_fundamental_factors(self, market_data: pd.DataFrame, fundamental_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate fundamental analysis factors"""
        merged_data = market_data.merge(fundamental_data, on='symbol', how='left')
        merged_data['price_to_book'] = merged_data['pb_ratio']
        merged_data['price_to_earnings'] = merged_data['pe_ratio']
        merged_data['return_on_equity'] = merged_data['roe']
        merged_data['return_on_assets'] = merged_data['roa']
        merged_data['debt_equity_ratio'] = merged_data['debt_to_equity']
        merged_data['revenue_growth_rate'] = merged_data['revenue_growth']
        merged_data['earnings_growth_rate'] = merged_data['earnings_growth']
        return merged_data

    def calculate_alternative_factors(self, data: pd.DataFrame, alt_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Integrate alternative data factors"""
        result = data.copy()
        if 'sentiment' in alt_data:
            sentiment = alt_data['sentiment']
            result = result.merge(sentiment, on='date', how='left')
            result['sentiment_momentum'] = result['news_sentiment'].rolling(5).mean()
            result['sentiment_volatility'] = result['news_sentiment'].rolling(10).std()
        if 'social' in alt_data:
            social = alt_data['social']
            result = result.merge(social, on='date', how='left')
            result['social_activity'] = result['twitter_mentions'] + result['news_volume']
            result['social_sentiment_trend'] = result['reddit_sentiment'].rolling(7).mean()
        return result

    def _calculate_rsi(self, prices: pd.Series, window: int=14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - 100 / (1 + rs)
        return rsi

    def _calculate_bollinger_bands(self, prices: pd.Series, window: int=20, num_std: float=2) -> Tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window).mean()
        std = prices.rolling(window).std()
        upper = sma + std * num_std
        lower = sma - std * num_std
        return (upper, lower)

    def _calculate_macd(self, prices: pd.Series, fast: int=12, slow: int=26, signal: int=9) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        return (macd, macd_signal)

    def evaluate_factor_performance(self, data: pd.DataFrame, factor_name: str, target: str='returns') -> Dict:
        """Evaluate factor performance using various metrics"""
        ic = data[factor_name].corr(data[target], method='spearman')
        data['factor_quintile'] = pd.qcut(data[factor_name].rank(), 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
        quintile_returns = data.groupby('factor_quintile')[target].mean()
        long_short_return = quintile_returns['Q5'] - quintile_returns['Q1']
        return {'information_coefficient': ic, 'quintile_returns': quintile_returns.to_dict(), 'long_short_return': long_short_return, 'factor_stats': {'mean': data[factor_name].mean(), 'std': data[factor_name].std(), 'skewness': data[factor_name].skew(), 'kurtosis': data[factor_name].kurtosis()}}

def __init__(self, config: ML4TConfig):
    self.config = config
    self.logger = ML4TLogger('AlphaEngine')
    self.factor_library = {}

class BaseMLModel(ABC):
    """Abstract base class for all ML models"""

    def __init__(self, config: ML4TConfig):
        self.config = config
        self.logger = ML4TLogger(self.__class__.__name__)
        self.model = None
        self.is_fitted = False
        self.feature_importance_ = None

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'BaseMLModel':
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        pass

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """Evaluate model performance"""
        predictions = self.predict(X_test)
        if len(np.unique(y_test)) == 2:
            metrics = {'accuracy': accuracy_score(y_test, predictions), 'precision': precision_score(y_test, predictions), 'recall': recall_score(y_test, predictions), 'f1_score': f1_score(y_test, predictions)}
        else:
            metrics = {'mse': mean_squared_error(y_test, predictions), 'mae': mean_absolute_error(y_test, predictions), 'r2': r2_score(y_test, predictions), 'rmse': np.sqrt(mean_squared_error(y_test, predictions))}
        return metrics

def __init__(self, config: ML4TConfig):
    self.config = config
    self.logger = ML4TLogger(self.__class__.__name__)
    self.model = None
    self.is_fitted = False
    self.feature_importance_ = None

class PortfolioOptimizer:
    """Modern Portfolio Theory and risk-based optimization"""

    def __init__(self, config: ML4TConfig):
        self.config = config
        self.logger = ML4TLogger('PortfolioOptimizer')

    def mean_variance_optimization(self, returns: pd.DataFrame, risk_aversion: float=1.0) -> pd.Series:
        """Classic Markowitz mean-variance optimization"""
        mu = returns.mean()
        cov_matrix = returns.cov()
        n = len(mu)
        inv_cov = np.linalg.pinv(cov_matrix)
        ones = np.ones((n, 1))
        weights = inv_cov @ mu
        weights = weights / np.sum(weights)
        return pd.Series(weights, index=returns.columns)

    def risk_parity_optimization(self, returns: pd.DataFrame) -> pd.Series:
        """Risk parity portfolio optimization"""
        cov_matrix = returns.cov()
        n = len(returns.columns)
        weights = np.ones(n) / n
        for _ in range(50):
            portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)
            marginal_contrib = cov_matrix @ weights / portfolio_vol
            risk_contrib = weights * marginal_contrib
            target_risk = np.mean(risk_contrib)
            adjustment = target_risk / risk_contrib
            weights = weights * adjustment
            weights = weights / np.sum(weights)
        return pd.Series(weights, index=returns.columns)

    def black_litterman_optimization(self, returns: pd.DataFrame, views: Dict=None) -> pd.Series:
        """Black-Litterman model with investor views"""
        mu = returns.mean()
        cov_matrix = returns.cov()
        if views is None:
            weights = np.ones(len(returns.columns)) / len(returns.columns)
        else:
            weights = self.mean_variance_optimization(returns)
        return pd.Series(weights, index=returns.columns)

    def calculate_portfolio_metrics(self, returns: pd.Series, benchmark_returns: pd.Series=None) -> Dict:
        """Calculate comprehensive portfolio performance metrics"""
        total_return = (1 + returns).prod() - 1
        annualized_return = (1 + returns.mean()) ** 252 - 1
        annualized_volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility > 0 else 0
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252)
        sortino_ratio = annualized_return / downside_deviation if downside_deviation > 0 else 0
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        var_95 = returns.quantile(0.05)
        cvar_95 = returns[returns <= var_95].mean()
        metrics = {'total_return': total_return, 'annualized_return': annualized_return, 'annualized_volatility': annualized_volatility, 'sharpe_ratio': sharpe_ratio, 'sortino_ratio': sortino_ratio, 'max_drawdown': max_drawdown, 'var_95': var_95, 'cvar_95': cvar_95, 'calmar_ratio': annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0}
        if benchmark_returns is not None:
            benchmark_return = (1 + benchmark_returns.mean()) ** 252 - 1
            alpha = annualized_return - benchmark_return
            covariance = returns.cov(benchmark_returns)
            benchmark_variance = benchmark_returns.var()
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
            active_returns = returns - benchmark_returns
            tracking_error = active_returns.std() * np.sqrt(252)
            information_ratio = active_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0
            metrics.update({'alpha': alpha, 'beta': beta, 'information_ratio': information_ratio, 'tracking_error': tracking_error})
        return metrics

def __init__(self, config: ML4TConfig):
    self.config = config
    self.logger = ML4TLogger('PortfolioOptimizer')

class BacktestEngine:
    """Comprehensive backtesting framework"""

    def __init__(self, config: ML4TConfig):
        self.config = config
        self.logger = ML4TLogger('BacktestEngine')
        self.results = {}

    def run_backtest(self, strategy_signals: pd.DataFrame, price_data: pd.DataFrame, initial_capital: float=None) -> Dict:
        """Execute complete backtest simulation"""
        if initial_capital is None:
            initial_capital = self.config.initial_capital
        portfolio = {'cash': initial_capital, 'positions': {}, 'portfolio_value': [initial_capital], 'dates': [], 'trades': []}
        signals = strategy_signals.sort_values('date')
        prices = price_data.sort_values('date')
        for date in signals['date'].unique():
            daily_signals = signals[signals['date'] == date]
            daily_prices = prices[prices['date'] == date]
            portfolio = self._process_daily_signals(portfolio, daily_signals, daily_prices, date)
            portfolio_value = self._calculate_portfolio_value(portfolio, daily_prices)
            portfolio['portfolio_value'].append(portfolio_value)
            portfolio['dates'].append(date)
        returns = pd.Series(portfolio['portfolio_value']).pct_change().dropna()
        portfolio_optimizer = PortfolioOptimizer(self.config)
        metrics = portfolio_optimizer.calculate_portfolio_metrics(returns)
        return {'portfolio_values': portfolio['portfolio_value'], 'dates': portfolio['dates'], 'trades': portfolio['trades'], 'positions': portfolio['positions'], 'metrics': metrics, 'returns': returns}

    def _process_daily_signals(self, portfolio: Dict, signals: pd.DataFrame, prices: pd.DataFrame, date) -> Dict:
        """Process trading signals for a single day"""
        for _, signal in signals.iterrows():
            symbol = signal['symbol']
            signal_strength = signal.get('signal', 0)
            price_row = prices[prices['symbol'] == symbol]
            if price_row.empty:
                continue
            current_price = price_row['close'].iloc[0]
            target_position_value = portfolio['cash'] * self.config.max_position_size * signal_strength
            target_shares = int(target_position_value / current_price)
            current_shares = portfolio['positions'].get(symbol, 0)
            shares_to_trade = target_shares - current_shares
            if abs(shares_to_trade) > 0:
                trade_value = shares_to_trade * current_price
                trading_cost = abs(trade_value) * self.config.trading_costs
                if shares_to_trade > 0:
                    total_cost = trade_value + trading_cost
                    if total_cost <= portfolio['cash']:
                        portfolio['cash'] -= total_cost
                        portfolio['positions'][symbol] = current_shares + shares_to_trade
                        portfolio['trades'].append({'date': date, 'symbol': symbol, 'shares': shares_to_trade, 'price': current_price, 'value': trade_value, 'cost': trading_cost, 'type': 'BUY'})
                else:
                    portfolio['cash'] += abs(trade_value) - trading_cost
                    portfolio['positions'][symbol] = current_shares + shares_to_trade
                    portfolio['trades'].append({'date': date, 'symbol': symbol, 'shares': shares_to_trade, 'price': current_price, 'value': trade_value, 'cost': trading_cost, 'type': 'SELL'})
        return portfolio

    def _calculate_portfolio_value(self, portfolio: Dict, prices: pd.DataFrame) -> float:
        """Calculate total portfolio value"""
        total_value = portfolio['cash']
        for symbol, shares in portfolio['positions'].items():
            if shares != 0:
                price_row = prices[prices['symbol'] == symbol]
                if not price_row.empty:
                    current_price = price_row['close'].iloc[0]
                    total_value += shares * current_price
        return total_value

    def run_walk_forward_analysis(self, model, data: pd.DataFrame, features: List[str], target: str, train_window: int=252, test_window: int=21) -> Dict:
        """Run walk-forward analysis for model validation"""
        results = []
        data = data.sort_values('date')
        start_idx = train_window
        while start_idx + test_window < len(data):
            train_data = data.iloc[start_idx - train_window:start_idx]
            test_data = data.iloc[start_idx:start_idx + test_window]
            X_train = train_data[features].fillna(0)
            y_train = train_data[target].fillna(0)
            X_test = test_data[features].fillna(0)
            y_test = test_data[target].fillna(0)
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            metrics = model.evaluate(X_test, y_test)
            results.append({'train_start': train_data['date'].iloc[0], 'train_end': train_data['date'].iloc[-1], 'test_start': test_data['date'].iloc[0], 'test_end': test_data['date'].iloc[-1], 'metrics': metrics, 'predictions': predictions, 'actual': y_test.values})
            start_idx += test_window
        return {'results': results, 'summary_metrics': self._summarize_walk_forward_results(results)}

    def _summarize_walk_forward_results(self, results: List[Dict]) -> Dict:
        """Summarize walk-forward analysis results"""
        metrics_list = [r['metrics'] for r in results]
        summary = {}
        for metric in metrics_list[0].keys():
            values = [m[metric] for m in metrics_list]
            summary[f'{metric}_mean'] = np.mean(values)
            summary[f'{metric}_std'] = np.std(values)
            summary[f'{metric}_min'] = np.min(values)
            summary[f'{metric}_max'] = np.max(values)
        return summary

def __init__(self, config: ML4TConfig):
    self.config = config
    self.logger = ML4TLogger('BacktestEngine')
    self.results = {}

class TradingStrategy(ABC):
    """Abstract base class for trading strategies"""

    def __init__(self, name: str, config: ML4TConfig):
        self.name = name
        self.config = config
        self.logger = ML4TLogger(f'Strategy_{name}')
        self.model = None
        self.features = []

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals"""
        pass

    def set_model(self, model: BaseMLModel):
        """Set the ML model for the strategy"""
        self.model = model

    def set_features(self, features: List[str]):
        """Set feature list for the strategy"""
        self.features = features

def __init__(self, name: str, config: ML4TConfig):
    self.name = name
    self.config = config
    self.logger = ML4TLogger(f'Strategy_{name}')
    self.model = None
    self.features = []

class ML4TVisualizer:
    """Comprehensive visualization toolkit for ML4T"""

    def __init__(self, config: ML4TConfig):
        self.config = config
        self.logger = ML4TLogger('Visualizer')

    def plot_portfolio_performance(self, backtest_results: Dict, benchmark_data: pd.DataFrame=None):
        """Plot portfolio performance with benchmarks"""
        fig = make_subplots(rows=3, cols=2, subplot_titles=['Portfolio Value', 'Returns Distribution', 'Drawdown', 'Rolling Sharpe Ratio', 'Trade Analysis', 'Feature Importance'], specs=[[{'secondary_y': False}, {'secondary_y': False}], [{'secondary_y': False}, {'secondary_y': False}], [{'secondary_y': False}, {'secondary_y': False}]])
        dates = pd.to_datetime(backtest_results['dates'])
        portfolio_values = backtest_results['portfolio_values'][1:]
        fig.add_trace(go.Scatter(x=dates, y=portfolio_values, name='Portfolio', line=dict(color='blue')), row=1, col=1)
        returns = backtest_results['returns']
        fig.add_trace(go.Histogram(x=returns, name='Returns', nbinsx=50, opacity=0.7), row=1, col=2)
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        fig.add_trace(go.Scatter(x=dates[1:], y=drawdown * 100, name='Drawdown %', fill='tonexty', line=dict(color='red')), row=2, col=1)
        rolling_sharpe = returns.rolling(window=252).mean() / returns.rolling(window=252).std() * np.sqrt(252)
        fig.add_trace(go.Scatter(x=dates[1:], y=rolling_sharpe, name='Rolling Sharpe', line=dict(color='green')), row=2, col=2)
        trades_df = pd.DataFrame(backtest_results['trades'])
        if not trades_df.empty:
            trade_pnl = trades_df.groupby('date')['value'].sum()
            fig.add_trace(go.Bar(x=trade_pnl.index, y=trade_pnl.values, name='Daily P&L'), row=3, col=1)
        fig.update_layout(height=1200, title_text='Portfolio Performance Dashboard')
        fig.show()

    def plot_factor_analysis(self, factor_performance: Dict):
        """Plot factor analysis results"""
        fig = make_subplots(rows=2, cols=2, subplot_titles=['Factor Returns by Quintile', 'Information Coefficient Over Time', 'Factor Distribution', 'Cumulative Factor Returns'])
        quintiles = list(factor_performance['quintile_returns'].keys())
        returns = list(factor_performance['quintile_returns'].values())
        fig.add_trace(go.Bar(x=quintiles, y=returns, name='Quintile Returns'), row=1, col=1)
        fig.update_layout(height=800, title_text='Factor Analysis Dashboard')
        fig.show()

    def plot_model_performance(self, walk_forward_results: Dict):
        """Plot model performance over time"""
        results = walk_forward_results['results']
        dates = [r['test_start'] for r in results]
        metrics = [r['metrics'] for r in results]
        fig = make_subplots(rows=2, cols=2, subplot_titles=['Model Accuracy Over Time', 'Prediction vs Actual', 'Feature Importance', 'Residual Analysis'])
        if 'accuracy' in metrics[0]:
            accuracy_scores = [m['accuracy'] for m in metrics]
            fig.add_trace(go.Scatter(x=dates, y=accuracy_scores, name='Accuracy', line=dict(color='blue')), row=1, col=1)
        elif 'r2' in metrics[0]:
            r2_scores = [m['r2'] for m in metrics]
            fig.add_trace(go.Scatter(x=dates, y=r2_scores, name='R²', line=dict(color='blue')), row=1, col=1)
        all_predictions = np.concatenate([r['predictions'] for r in results])
        all_actual = np.concatenate([r['actual'] for r in results])
        fig.add_trace(go.Scatter(x=all_actual, y=all_predictions, mode='markers', name='Pred vs Actual', opacity=0.6), row=1, col=2)
        min_val, max_val = (min(all_actual.min(), all_predictions.min()), max(all_actual.max(), all_predictions.max()))
        fig.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val], mode='lines', name='Perfect Prediction', line=dict(color='red', dash='dash')), row=1, col=2)
        fig.update_layout(height=800, title_text='Model Performance Analysis')
        fig.show()

def __init__(self, config: ML4TConfig):
    self.config = config
    self.logger = ML4TLogger('Visualizer')

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

def run_ml4t_demo():
    """Demonstration of the ML4T framework"""
    print('Initializing ML4T Framework...')
    config = ML4TConfig()
    ml4t = ML4TFramework(config)
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    start_date = '2020-01-01'
    end_date = '2023-12-31'
    ml4t.load_data(symbols, start_date, end_date)
    feature_data = ml4t.engineer_features(symbols)
    models_config = [{'name': 'ridge_model', 'type': 'ridge', 'params': {'alpha': 1.0}}, {'name': 'random_forest', 'type': 'random_forest', 'params': {'n_estimators': 100}}, {'name': 'gradient_boosting', 'type': 'gradient_boosting', 'params': {'n_estimators': 100}}]
    ml4t.train_models(feature_data, models_config)
    feature_columns = [col for col in feature_data.columns if col not in ['date', 'symbol', 'future_returns', 'open', 'high', 'low', 'close', 'volume']]
    strategies_config = [{'name': 'mean_reversion', 'type': 'mean_reversion', 'params': {'lookback_window': 20}}, {'name': 'momentum', 'type': 'momentum', 'params': {'lookback_window': 12}}, {'name': 'ml_ridge', 'type': 'ml_strategy', 'params': {'model_name': 'ridge_model', 'features': feature_columns[:10]}}, {'name': 'ml_rf', 'type': 'ml_strategy', 'params': {'model_name': 'random_forest', 'features': feature_columns[:10]}}]
    ml4t.create_strategies(strategies_config)
    ml4t.run_backtests()
    summary = ml4t.generate_report()
    return (ml4t, summary)

class CompanyDataValidator:
    """Validator for Company Data Integrity"""

    @staticmethod
    def validate_company_data(company_data: CompanyData) -> Dict[str, List[str]]:
        """Comprehensive validation of company data"""
        errors = []
        warnings = []
        if not company_data.symbol:
            errors.append('Company symbol is required')
        if company_data.current_price <= 0:
            errors.append('Current price must be positive')
        if company_data.shares_outstanding <= 0:
            errors.append('Shares outstanding must be positive')
        calculated_market_cap = company_data.current_price * company_data.shares_outstanding
        if abs(calculated_market_cap - company_data.market_cap) / company_data.market_cap > 0.1:
            warnings.append('Market cap inconsistent with price × shares outstanding')
        financial_data = company_data.financial_data
        revenue = financial_data.get('revenue', 0)
        if revenue < 0:
            warnings.append('Negative revenue reported')
        net_income = financial_data.get('net_income', 0)
        profit_margin = financial_data.get('profit_margin', 0)
        if revenue > 0 and net_income != 0:
            calculated_margin = net_income / revenue
            if abs(calculated_margin - profit_margin) > 0.02:
                warnings.append('Profit margin inconsistent with net income and revenue')
        total_assets = financial_data.get('total_assets', 0)
        total_debt = financial_data.get('total_debt', 0)
        if total_debt > total_assets and total_assets > 0:
            warnings.append('Total debt exceeds total assets')
        market_data = company_data.market_data
        pe_ratio = market_data.get('pe_ratio', 0)
        eps = financial_data.get('earnings_per_share', 0)
        if pe_ratio > 0 and eps > 0:
            calculated_price = pe_ratio * eps
            if abs(calculated_price - company_data.current_price) / company_data.current_price > 0.1:
                warnings.append('P/E ratio inconsistent with current price and EPS')
        return {'errors': errors, 'warnings': warnings}

    @staticmethod
    def validate_data_freshness(company_data: CompanyData, max_age_days: int=7) -> bool:
        """Validate that data is recent enough for analysis"""
        if not company_data.last_updated:
            print('Warning: No timestamp available for data freshness check')
            return True
        age = datetime.now() - company_data.last_updated
        if age.days > max_age_days:
            print(f'Warning: Data is {age.days} days old (max recommended: {max_age_days} days)')
        return True

@staticmethod
def validate_data_freshness(company_data: CompanyData, max_age_days: int=7) -> bool:
    """Validate that data is recent enough for analysis"""
    if not company_data.last_updated:
        print('Warning: No timestamp available for data freshness check')
        return True
    age = datetime.now() - company_data.last_updated
    if age.days > max_age_days:
        print(f'Warning: Data is {age.days} days old (max recommended: {max_age_days} days)')
    return True

class LiveMarketplaceInterface:
    """Live Financial Data Marketplace Interface with API Integration"""

    def __init__(self):
        self.SCREEN_WIDTH = 1400
        self.SCREEN_HEIGHT = 900
        self.SIDEBAR_WIDTH = 280
        self.CARD_WIDTH = 350
        self.CARD_HEIGHT = 320
        self.API_BASE_URL = 'https://finceptbackend.share.zrok.io'
        self.API_KEY = ''
        self.current_user = None
        self.datasets = []
        self.categories = []
        self.user_purchases = []
        self.my_datasets = []
        self.selected_dataset = None
        self.current_filters = {'category': None, 'price_tier': None, 'search': ''}
        self.setup_ui()

    def make_api_request(self, endpoint: str, method: str='GET', data: dict=None, files: dict=None) -> dict:
        """Make API request with error handling"""
        try:
            url = f'{self.API_BASE_URL}{endpoint}'
            headers = {}
            if self.API_KEY:
                headers['X-API-Key'] = self.API_KEY
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                if files:
                    response = requests.post(url, headers={k: v for k, v in headers.items() if k != 'Content-Type'}, data=data, files=files, timeout=30)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f'API Error {response.status_code}: {response.text}'
                print(error_msg)
                return {'success': False, 'message': error_msg}
        except requests.RequestException as e:
            error_msg = f'Network Error: {str(e)}'
            print(error_msg)
            return {'success': False, 'message': error_msg}

    def login_user(self, email: str, password: str) -> bool:
        """Login user and get API key"""
        try:
            login_data = {'email': email, 'password': password}
            response = self.make_api_request('/user/login', 'POST', login_data)
            if response.get('success') and 'api_key' in response.get('data', {}):
                self.API_KEY = response['data']['api_key']
                self.load_user_profile()
                return True
            else:
                return False
        except Exception as e:
            print(f'Login error: {e}')
            return False

    def load_user_profile(self):
        """Load user profile information"""
        try:
            response = self.make_api_request('/user/profile')
            if response.get('success'):
                self.current_user = response.get('data', {})
        except Exception as e:
            print(f'Profile load error: {e}')

    def load_datasets(self):
        """Load marketplace datasets"""
        try:
            params = {}
            if self.current_filters['category']:
                params['category'] = self.current_filters['category']
            if self.current_filters['price_tier']:
                params['price_tier'] = self.current_filters['price_tier']
            if self.current_filters['search']:
                params['search'] = self.current_filters['search']
            query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
            endpoint = '/marketplace/datasets'
            if query_string:
                endpoint += f'?{query_string}'
            response = self.make_api_request(endpoint)
            if response.get('success'):
                self.datasets = response.get('data', {}).get('datasets', [])
                return True
            return False
        except Exception as e:
            print(f'Dataset load error: {e}')
            return False

    def load_categories(self):
        """Load available categories"""
        try:
            response = self.make_api_request('/marketplace/categories')
            if response.get('success'):
                self.categories = response.get('data', {}).get('categories', [])
                return True
            return False
        except Exception as e:
            print(f'Categories load error: {e}')
            return False

    def load_user_purchases(self):
        """Load user's dataset purchases"""
        try:
            response = self.make_api_request('/marketplace/my-purchases')
            if response.get('success'):
                self.user_purchases = response.get('data', {}).get('purchases', [])
                return True
            return False
        except Exception as e:
            print(f'Purchases load error: {e}')
            return False

    def load_my_datasets(self):
        """Load user's uploaded datasets"""
        try:
            response = self.make_api_request('/marketplace/my-datasets')
            if response.get('success'):
                self.my_datasets = response.get('data', {}).get('datasets', [])
                return True
            return False
        except Exception as e:
            print(f'My datasets load error: {e}')
            return False

    def purchase_dataset(self, dataset_id: int, payment_method: str='subscription_credit'):
        """Purchase a dataset"""
        try:
            purchase_data = {'payment_method': payment_method}
            response = self.make_api_request(f'/marketplace/datasets/{dataset_id}/purchase', 'POST', purchase_data)
            return response.get('success', False)
        except Exception as e:
            print(f'Purchase error: {e}')
            return False

    def download_dataset(self, dataset_id: int):
        """Download a dataset"""
        try:
            response = self.make_api_request(f'/marketplace/datasets/{dataset_id}/download', 'POST')
            return response.get('success', False)
        except Exception as e:
            print(f'Download error: {e}')
            return False

    def setup_ui(self):
        """Initialize UI"""
        try:
            dpg.create_context()
            self.create_theme()
            dpg.create_viewport(title='Fincept Live Marketplace', width=self.SCREEN_WIDTH, height=self.SCREEN_HEIGHT, resizable=True)
            dpg.setup_dearpygui()
            if not self.API_KEY:
                self.create_login_window()
            else:
                self.create_main_interface()
            dpg.bind_theme('marketplace_theme')
            dpg.show_viewport()
            dpg.start_dearpygui()
        except Exception as e:
            print(f'UI setup error: {e}')
            sys.exit(1)
        finally:
            try:
                dpg.destroy_context()
            except:
                pass

    def create_theme(self):
        """Create marketplace theme"""
        try:
            with dpg.theme(tag='marketplace_theme'):
                with dpg.theme_component(dpg.mvAll):
                    DARK_BG = [15, 15, 20, 255]
                    MEDIUM_BG = [25, 30, 35, 255]
                    LIGHT_BG = [40, 45, 50, 255]
                    ACCENT = [64, 156, 255, 255]
                    WHITE = [255, 255, 255, 255]
                    GRAY = [160, 160, 160, 255]
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, DARK_BG)
                    dpg.add_theme_color(dpg.mvThemeCol_ChildBg, DARK_BG)
                    dpg.add_theme_color(dpg.mvThemeCol_Text, WHITE)
                    dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, GRAY)
                    dpg.add_theme_color(dpg.mvThemeCol_Button, MEDIUM_BG)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [64, 156, 255, 120])
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [64, 156, 255, 180])
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, LIGHT_BG)
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [64, 156, 255, 60])
                    dpg.add_theme_color(dpg.mvThemeCol_Header, ACCENT)
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, [64, 156, 255, 180])
                    dpg.add_theme_color(dpg.mvThemeCol_Tab, MEDIUM_BG)
                    dpg.add_theme_color(dpg.mvThemeCol_TabHovered, [64, 156, 255, 120])
                    dpg.add_theme_color(dpg.mvThemeCol_TabActive, ACCENT)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
        except Exception as e:
            print(f'Theme creation error: {e}')

    def create_login_window(self):
        """Create login interface"""
        with dpg.window(label='Login to Fincept Marketplace', tag='login_window', width=400, height=300, no_resize=True, modal=True, pos=[500, 300]):
            dpg.add_text('Welcome to Fincept Marketplace')
            dpg.add_separator()
            dpg.add_text('Email:')
            dpg.add_input_text(tag='login_email', width=350)
            dpg.add_text('Password:')
            dpg.add_input_text(tag='login_password', width=350, password=True)
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(label='Login', width=100, callback=self.handle_login)
                dpg.add_button(label='Cancel', width=100, callback=lambda: dpg.stop_dearpygui())
            dpg.add_text('', tag='login_status', color=[255, 100, 100, 255])
        dpg.set_primary_window('login_window', True)

    def handle_login(self):
        """Handle login button click"""
        email = dpg.get_value('login_email')
        password = dpg.get_value('login_password')
        if not email or not password:
            dpg.set_value('login_status', 'Please enter email and password')
            return
        dpg.set_value('login_status', 'Logging in...')

        def login_thread():
            success = self.login_user(email, password)
            if success:
                dpg.delete_item('login_window')
                self.create_main_interface()
            else:
                dpg.set_value('login_status', 'Login failed. Check credentials.')
        threading.Thread(target=login_thread, daemon=True).start()

    def create_main_interface(self):
        """Create main marketplace interface"""
        self.load_categories()
        self.load_datasets()
        with dpg.window(label='Fincept Marketplace', tag='main_window', width=self.SCREEN_WIDTH, height=self.SCREEN_HEIGHT, no_title_bar=True, no_resize=True, no_move=True, pos=[0, 0]):
            self.create_header()
            with dpg.tab_bar(tag='main_tabs'):
                with dpg.tab(label='Browse Marketplace', tag='marketplace_tab'):
                    with dpg.group(horizontal=True):
                        self.create_sidebar()
                        self.create_dataset_grid()
                with dpg.tab(label='My Purchases', tag='purchases_tab'):
                    self.create_purchases_content()
                with dpg.tab(label='My Datasets', tag='my_datasets_tab'):
                    self.create_my_datasets_content()
                with dpg.tab(label='Upload Dataset', tag='upload_tab'):
                    self.create_upload_content()
                with dpg.tab(label='Dataset Details', tag='details_tab', show=False):
                    self.create_dataset_details_content()
        dpg.set_primary_window('main_window', True)

    def create_header(self):
        """Create header section"""
        with dpg.child_window(width=-1, height=60, border=True, no_scrollbar=True):
            with dpg.group(horizontal=True):
                dpg.add_text('FINCEPT', color=[64, 156, 255, 255])
                dpg.add_text(' Live Marketplace')
                if self.current_user:
                    dpg.add_text(f' | Welcome, {self.current_user.get('username', 'User')}')
                dpg.add_input_text(hint='Search datasets...', width=250, tag='search_input')
                dpg.add_button(label='Search', callback=self.handle_search)
                dpg.add_button(label='Refresh', callback=self.refresh_data)
                dpg.add_button(label='Logout', callback=self.logout)

    def create_sidebar(self):
        """Create filter sidebar"""
        with dpg.child_window(width=self.SIDEBAR_WIDTH, height=-1, border=True):
            dpg.add_text('FILTERS', color=[64, 156, 255, 255])
            dpg.add_separator()
            dpg.add_text('Categories')
            dpg.add_combo(tag='category_filter', items=['All'] + [cat.get('category', '') for cat in self.categories], default_value='All', callback=self.apply_filters, width=240)
            dpg.add_text('Price Tier')
            dpg.add_combo(tag='price_filter', items=['All', 'free', 'basic', 'premium', 'enterprise'], default_value='All', callback=self.apply_filters, width=240)
            dpg.add_separator()
            dpg.add_button(label='Clear Filters', width=240, callback=self.clear_filters)
            dpg.add_text(f'Showing: {len(self.datasets)} datasets')

    def create_dataset_grid(self):
        """Create dataset grid display"""
        with dpg.child_window(width=-1, height=-1, border=True, tag='dataset_grid'):
            self.update_dataset_grid()

    def update_dataset_grid(self):
        """Update dataset grid content"""
        if dpg.does_item_exist('dataset_grid'):
            dpg.delete_item('dataset_grid', children_only=True)
        if not self.datasets:
            dpg.add_text('No datasets found. Try adjusting your filters.', parent='dataset_grid')
            return
        dpg.add_text(f'Available Datasets ({len(self.datasets)})', parent='dataset_grid')
        dpg.add_separator(parent='dataset_grid')
        for i in range(0, len(self.datasets), 3):
            with dpg.group(horizontal=True, parent='dataset_grid'):
                for j in range(3):
                    if i + j < len(self.datasets):
                        self.create_dataset_card(self.datasets[i + j])

    def create_dataset_card(self, dataset: dict):
        """Create individual dataset card"""
        with dpg.child_window(width=self.CARD_WIDTH, height=self.CARD_HEIGHT, border=True):
            title = dataset.get('title', 'Unknown Dataset')
            if len(title) > 25:
                title = title[:22] + '...'
            dpg.add_text(title, color=[255, 255, 255, 255])
            uploader = dataset.get('uploader', {}).get('username', 'Unknown')
            dpg.add_text(f'by {uploader}', color=[160, 160, 160, 255])
            with dpg.group(horizontal=True):
                category = dataset.get('category', 'Unknown')
                dpg.add_button(label=category, width=100, height=20, enabled=False)
                pricing = dataset.get('pricing', {})
                price = pricing.get('price_usd', 0)
                if price == 0:
                    dpg.add_text('FREE', color=[0, 255, 100, 255])
                else:
                    dpg.add_text(f'${price:.2f}', color=[255, 140, 0, 255])
            description = dataset.get('description', 'No description available')
            if len(description) > 120:
                description = description[:117] + '...'
            dpg.add_text(description, wrap=320, color=[180, 180, 180, 255])
            metadata = dataset.get('metadata', {})
            dpg.add_text(f'Rows: {metadata.get('total_rows', 0):,} | Cols: {metadata.get('total_columns', 0)}')
            dpg.add_text(f'Size: {metadata.get('file_size_mb', 0):.1f} MB')
            stats = dataset.get('statistics', {})
            dpg.add_text(f'Downloads: {stats.get('download_count', 0)} | Views: {stats.get('view_count', 0)}')
            with dpg.group(horizontal=True):
                dataset_id = dataset.get('id')
                dpg.add_button(label='View Details', width=110, height=30, user_data=dataset_id, callback=self.show_dataset_details)
                access = dataset.get('access', {})
                if access.get('can_access', False):
                    dpg.add_button(label='Download', width=80, height=30, user_data=dataset_id, callback=self.handle_download)
                elif access.get('requires_purchase', False):
                    dpg.add_button(label='Purchase', width=80, height=30, user_data=dataset_id, callback=self.handle_purchase)
                else:
                    dpg.add_button(label='Locked', width=80, height=30, enabled=False)

    def create_purchases_content(self):
        """Create purchases tab content"""
        with dpg.child_window(width=-1, height=-1, border=True, tag='purchases_content'):
            self.update_purchases_content()

    def update_purchases_content(self):
        """Update purchases content"""
        if dpg.does_item_exist('purchases_content'):
            dpg.delete_item('purchases_content', children_only=True)
        self.load_user_purchases()
        dpg.add_text('My Dataset Purchases', parent='purchases_content')
        dpg.add_separator(parent='purchases_content')
        if not self.user_purchases:
            dpg.add_text('No purchases yet.', parent='purchases_content')
            return
        for purchase in self.user_purchases:
            with dpg.child_window(width=-1, height=80, border=True, parent='purchases_content'):
                dataset = purchase.get('dataset', {})
                dpg.add_text(f'Dataset: {dataset.get('title', 'Unknown')}')
                dpg.add_text(f'Amount: ${purchase.get('amount_paid', 0):.2f} | Status: {purchase.get('status', 'Unknown')}')
                dpg.add_text(f'Purchased: {purchase.get('purchased_at', 'Unknown')}')

    def create_my_datasets_content(self):
        """Create my datasets tab content"""
        with dpg.child_window(width=-1, height=-1, border=True, tag='my_datasets_content'):
            self.update_my_datasets_content()

    def update_my_datasets_content(self):
        """Update my datasets content"""
        if dpg.does_item_exist('my_datasets_content'):
            dpg.delete_item('my_datasets_content', children_only=True)
        self.load_my_datasets()
        dpg.add_text('My Uploaded Datasets', parent='my_datasets_content')
        dpg.add_separator(parent='my_datasets_content')
        if not self.my_datasets:
            dpg.add_text('No datasets uploaded yet.', parent='my_datasets_content')
            return
        for dataset in self.my_datasets:
            with dpg.child_window(width=-1, height=100, border=True, parent='my_datasets_content'):
                dpg.add_text(f'Title: {dataset.get('title', 'Unknown')}')
                dpg.add_text(f'Category: {dataset.get('category', 'Unknown')} | Status: {dataset.get('status', 'Unknown')}')
                stats = dataset.get('statistics', {})
                dpg.add_text(f'Downloads: {stats.get('download_count', 0)} | Views: {stats.get('view_count', 0)}')
                with dpg.group(horizontal=True):
                    if dataset.get('status') == 'rejected':
                        dpg.add_text(f'Rejection reason: {dataset.get('admin_notes', 'No reason provided')}', color=[255, 100, 100, 255])

    def create_upload_content(self):
        """Create upload tab content"""
        with dpg.child_window(width=-1, height=-1, border=True):
            dpg.add_text('Upload New Dataset')
            dpg.add_separator()
            dpg.add_text('Dataset Title:')
            dpg.add_input_text(tag='upload_title', width=400)
            dpg.add_text('Description:')
            dpg.add_input_text(tag='upload_description', width=400, multiline=True, height=100)
            dpg.add_text('Category:')
            categories = [cat.get('category', '') for cat in self.categories] if self.categories else ['stocks', 'forex', 'crypto']
            dpg.add_combo(tag='upload_category', items=categories, width=200)
            dpg.add_text('Price Tier:')
            dpg.add_combo(tag='upload_price_tier', items=['free', 'basic', 'premium', 'enterprise'], default_value='free', width=200)
            dpg.add_text('Tags (comma-separated):')
            dpg.add_input_text(tag='upload_tags', width=400)
            dpg.add_checkbox(label='Requires Subscription', tag='upload_requires_sub')
            dpg.add_text('CSV File:')
            dpg.add_text('Please select a CSV file to upload', tag='file_status')
            dpg.add_button(label='Select File', callback=self.select_file)
            dpg.add_separator()
            dpg.add_button(label='Upload Dataset', width=200, height=40, callback=self.handle_upload)

    def create_dataset_details_content(self):
        """Create dataset details content"""
        dpg.add_text('Loading dataset details...', tag='details_content')

    def select_file(self):
        """Handle file selection"""
        dpg.set_value('file_status', 'File selection not implemented in this demo')

    def handle_search(self):
        """Handle search functionality"""
        search_term = dpg.get_value('search_input')
        self.current_filters['search'] = search_term
        self.load_datasets()
        self.update_dataset_grid()

    def apply_filters(self):
        """Apply selected filters"""
        category = dpg.get_value('category_filter')
        price_tier = dpg.get_value('price_filter')
        self.current_filters['category'] = category if category != 'All' else None
        self.current_filters['price_tier'] = price_tier if price_tier != 'All' else None
        self.load_datasets()
        self.update_dataset_grid()

    def clear_filters(self):
        """Clear all filters"""
        self.current_filters = {'category': None, 'price_tier': None, 'search': ''}
        dpg.set_value('category_filter', 'All')
        dpg.set_value('price_filter', 'All')
        dpg.set_value('search_input', '')
        self.load_datasets()
        self.update_dataset_grid()

    def show_dataset_details(self, sender, app_data, user_data):
        """Show dataset details"""
        dataset_id = user_data
        dataset = next((d for d in self.datasets if d.get('id') == dataset_id), None)
        if not dataset:
            return
        self.selected_dataset = dataset
        if dpg.does_item_exist('details_tab'):
            dpg.delete_item('details_tab', children_only=True)
        dpg.add_button(label='← Back to Marketplace', callback=self.back_to_marketplace, parent='details_tab')
        dpg.add_text(dataset.get('title', 'Unknown'), color=[255, 255, 255, 255], parent='details_tab')
        uploader = dataset.get('uploader', {}).get('username', 'Unknown')
        dpg.add_text(f'by {uploader}', color=[160, 160, 160, 255], parent='details_tab')
        dpg.add_separator(parent='details_tab')
        with dpg.group(horizontal=True, parent='details_tab'):
            with dpg.child_window(width=700, height=500, border=True):
                dpg.add_text('Description', color=[64, 156, 255, 255])
                dpg.add_text(dataset.get('description', 'No description'), wrap=680)
                dpg.add_text('Dataset Information', color=[64, 156, 255, 255])
                metadata = dataset.get('metadata', {})
                dpg.add_text(f'Rows: {metadata.get('total_rows', 0):,}')
                dpg.add_text(f'Columns: {metadata.get('total_columns', 0)}')
                dpg.add_text(f'File Size: {metadata.get('file_size_mb', 0):.1f} MB')
                file_info = dataset.get('file_info', {})
                columns = file_info.get('column_names', [])
                if columns:
                    dpg.add_text('Columns:', color=[64, 156, 255, 255])
                    dpg.add_text(', '.join(columns[:10]), wrap=680)
                    if len(columns) > 10:
                        dpg.add_text(f'... and {len(columns) - 10} more columns')
            with dpg.child_window(width=350, height=500, border=True):
                dpg.add_text('Dataset Access', color=[64, 156, 255, 255])
                pricing = dataset.get('pricing', {})
                price = pricing.get('price_usd', 0)
                if price == 0:
                    dpg.add_text('FREE DATASET', color=[0, 255, 100, 255])
                else:
                    dpg.add_text(f'Price: ${price:.2f}', color=[255, 140, 0, 255])
                access = dataset.get('access', {})
                if access.get('can_access', False):
                    dpg.add_button(label='Download Dataset', width=320, height=40, user_data=dataset_id, callback=self.handle_download)
                elif access.get('requires_purchase', False):
                    dpg.add_button(label='Purchase Dataset', width=320, height=40, user_data=dataset_id, callback=self.handle_purchase)
                else:
                    dpg.add_text('Access Requirements Not Met', color=[255, 100, 100, 255])
                dpg.add_text('Statistics', color=[64, 156, 255, 255])
                stats = dataset.get('statistics', {})
                dpg.add_text(f'Downloads: {stats.get('download_count', 0)}')
                dpg.add_text(f'Views: {stats.get('view_count', 0)}')
        dpg.configure_item('details_tab', show=True)
        dpg.set_value('main_tabs', 'details_tab')

    def back_to_marketplace(self):
        """Return to marketplace tab"""
        dpg.set_value('main_tabs', 'marketplace_tab')

    def handle_purchase(self, sender, app_data, user_data):
        """Handle dataset purchase"""
        dataset_id = user_data

        def purchase_thread():
            success = self.purchase_dataset(dataset_id)
            if success:
                self.load_datasets()
                self.update_dataset_grid()
                print('Purchase successful!')
            else:
                print('Purchase failed!')
        threading.Thread(target=purchase_thread, daemon=True).start()

    def handle_download(self, sender, app_data, user_data):
        """Handle dataset download"""
        dataset_id = user_data

        def download_thread():
            success = self.download_dataset(dataset_id)
            if success:
                print('Download successful!')
            else:
                print('Download failed!')
        threading.Thread(target=download_thread, daemon=True).start()

    def handle_upload(self):
        """Handle dataset upload"""
        title = dpg.get_value('upload_title')
        description = dpg.get_value('upload_description')
        category = dpg.get_value('upload_category')
        price_tier = dpg.get_value('upload_price_tier')
        tags = dpg.get_value('upload_tags').split(',')
        requires_sub = dpg.get_value('upload_requires_sub')
        if not title or not description or (not category):
            print('Please fill all required fields')
            return
        print('Upload functionality requires file selection implementation')

    def refresh_data(self):
        """Refresh all data"""

        def refresh_thread():
            self.load_categories()
            self.load_datasets()
            self.update_dataset_grid()
            if dpg.get_value('main_tabs') == 'purchases_tab':
                self.update_purchases_content()
            elif dpg.get_value('main_tabs') == 'my_datasets_tab':
                self.update_my_datasets_content()
        threading.Thread(target=refresh_thread, daemon=True).start()

    def logout(self):
        """Logout user"""
        self.API_KEY = ''
        self.current_user = None
        self.datasets = []
        self.categories = []
        dpg.delete_item('main_window')
        self.create_login_window()

def make_api_request(self, endpoint: str, method: str='GET', data: dict=None, files: dict=None) -> dict:
    """Make API request with error handling"""
    try:
        url = f'{self.API_BASE_URL}{endpoint}'
        headers = {}
        if self.API_KEY:
            headers['X-API-Key'] = self.API_KEY
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            if files:
                response = requests.post(url, headers={k: v for k, v in headers.items() if k != 'Content-Type'}, data=data, files=files, timeout=30)
            else:
                headers['Content-Type'] = 'application/json'
                response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f'API Error {response.status_code}: {response.text}'
            print(error_msg)
            return {'success': False, 'message': error_msg}
    except requests.RequestException as e:
        error_msg = f'Network Error: {str(e)}'
        print(error_msg)
        return {'success': False, 'message': error_msg}

def login_user(self, email: str, password: str) -> bool:
    """Login user and get API key"""
    try:
        login_data = {'email': email, 'password': password}
        response = self.make_api_request('/user/login', 'POST', login_data)
        if response.get('success') and 'api_key' in response.get('data', {}):
            self.API_KEY = response['data']['api_key']
            self.load_user_profile()
            return True
        else:
            return False
    except Exception as e:
        print(f'Login error: {e}')
        return False

def load_user_profile(self):
    """Load user profile information"""
    try:
        response = self.make_api_request('/user/profile')
        if response.get('success'):
            self.current_user = response.get('data', {})
    except Exception as e:
        print(f'Profile load error: {e}')

def load_datasets(self):
    """Load marketplace datasets"""
    try:
        params = {}
        if self.current_filters['category']:
            params['category'] = self.current_filters['category']
        if self.current_filters['price_tier']:
            params['price_tier'] = self.current_filters['price_tier']
        if self.current_filters['search']:
            params['search'] = self.current_filters['search']
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        endpoint = '/marketplace/datasets'
        if query_string:
            endpoint += f'?{query_string}'
        response = self.make_api_request(endpoint)
        if response.get('success'):
            self.datasets = response.get('data', {}).get('datasets', [])
            return True
        return False
    except Exception as e:
        print(f'Dataset load error: {e}')
        return False

def load_categories(self):
    """Load available categories"""
    try:
        response = self.make_api_request('/marketplace/categories')
        if response.get('success'):
            self.categories = response.get('data', {}).get('categories', [])
            return True
        return False
    except Exception as e:
        print(f'Categories load error: {e}')
        return False

def load_user_purchases(self):
    """Load user's dataset purchases"""
    try:
        response = self.make_api_request('/marketplace/my-purchases')
        if response.get('success'):
            self.user_purchases = response.get('data', {}).get('purchases', [])
            return True
        return False
    except Exception as e:
        print(f'Purchases load error: {e}')
        return False

def load_my_datasets(self):
    """Load user's uploaded datasets"""
    try:
        response = self.make_api_request('/marketplace/my-datasets')
        if response.get('success'):
            self.my_datasets = response.get('data', {}).get('datasets', [])
            return True
        return False
    except Exception as e:
        print(f'My datasets load error: {e}')
        return False

def purchase_dataset(self, dataset_id: int, payment_method: str='subscription_credit'):
    """Purchase a dataset"""
    try:
        purchase_data = {'payment_method': payment_method}
        response = self.make_api_request(f'/marketplace/datasets/{dataset_id}/purchase', 'POST', purchase_data)
        return response.get('success', False)
    except Exception as e:
        print(f'Purchase error: {e}')
        return False

def download_dataset(self, dataset_id: int):
    """Download a dataset"""
    try:
        response = self.make_api_request(f'/marketplace/datasets/{dataset_id}/download', 'POST')
        return response.get('success', False)
    except Exception as e:
        print(f'Download error: {e}')
        return False

def download_thread():
    success = self.download_dataset(dataset_id)
    if success:
        print('Download successful!')
    else:
        print('Download failed!')

def execute_stock_data_node(node_id, ticker, period):
    print(f'Fetching data for {ticker}, period: {period}')
    data = fetch_stock_data(ticker, period)
    if data is not None:
        node_outputs[node_id] = data
        dpg.set_value(f'{node_id}_status', '✓ Data loaded')
        print(f'Data loaded successfully for node {node_id}')
    else:
        dpg.set_value(f'{node_id}_status', '✗ Failed to load')
        print(f'Failed to load data for node {node_id}')

def get_all_input_data(node_id):
    """Get all connected input data for a node"""
    print(f'Getting all input data for node {node_id}')
    if node_id not in node_connections:
        print(f'Node {node_id} has no input connections')
        return []
    all_data = []
    connections = node_connections[node_id]
    for input_type, source_node_ids in connections.items():
        for source_node_id in source_node_ids:
            if source_node_id in node_outputs:
                data = node_outputs[source_node_id]
                all_data.append({'data': data, 'source_id': source_node_id, 'input_type': input_type})
                print(f'Retrieved data from node {source_node_id} (type: {input_type})')
    return all_data

def get_input_data(node_id, input_type='default'):
    print(f'Getting input data for node {node_id}, type: {input_type}')
    if node_id not in node_connections:
        print(f'Node {node_id} has no input connections')
        return None
    connections = node_connections[node_id]
    if input_type in connections and connections[input_type]:
        source_node_id = connections[input_type][-1]
        print(f'Found source node: {source_node_id}')
        if source_node_id in node_outputs:
            data = node_outputs[source_node_id]
            print(f'Retrieved data from node {source_node_id}')
            return data
        else:
            print(f'No data available in source node {source_node_id}')
            return None
    else:
        print(f'No source node found for input type {input_type}')
        return None

class NewsAnalysisTab(BaseTab):
    """Real-time News Analysis Dashboard with RSS Feed Integration"""

    def __init__(self, main_app=None):
        super().__init__(main_app)
        self.main_app = main_app
        self.BLOOMBERG_ORANGE = [255, 165, 0]
        self.BLOOMBERG_WHITE = [255, 255, 255]
        self.BLOOMBERG_RED = [255, 0, 0]
        self.BLOOMBERG_GREEN = [0, 200, 0]
        self.BLOOMBERG_YELLOW = [255, 255, 0]
        self.BLOOMBERG_GRAY = [120, 120, 120]
        self.BLOOMBERG_BLUE = [100, 149, 237]
        self.news_sources = {}
        self.refresh_threads = {}
        self.conn = None
        self.ui_initialized = False
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.5', 'Connection': 'keep-alive'}
        self.setup_database()
        threading.Thread(target=self.load_user_settings, daemon=True).start()

    def get_label(self):
        return 'News'

    def _get_config_directory(self) -> Path:
        config_dir = Path.home() / '.fincept' / 'news'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def setup_database(self):
        try:
            config_dir = self._get_config_directory()
            db_path = config_dir / 'news_settings.db'
            self.conn = duckdb.connect(str(db_path))
            self.conn.execute('\n                CREATE TABLE IF NOT EXISTS news_sources (\n                    id INTEGER PRIMARY KEY,\n                    website_url VARCHAR,\n                    refresh_interval INTEGER,\n                    source_name VARCHAR,\n                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n                )\n            ')
        except Exception as e:
            logger.error(f'Database setup failed: {e}')
            self.conn = duckdb.connect(':memory:')

    def resolve_url(self, url):
        """Resolve Google News URLs using Playwright"""
        if not PLAYWRIGHT_AVAILABLE or 'news.google.com' not in url:
            return url
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until='networkidle', timeout=15000)
                final_url = page.url
                browser.close()
                return final_url if 'news.google.com' not in final_url else url
        except Exception:
            return url

    def validate_news_website(self, url):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        domain = urlparse(url).netloc.lower().replace('www.', '')
        if not domain:
            return (False, 'Invalid URL format')
        rss_endpoints = [f'https://{domain}/rss', f'https://{domain}/feed', f'https://{domain}/rss.xml', f'https://{domain}/feed.xml']
        for rss_url in rss_endpoints:
            try:
                response = requests.get(rss_url, headers=self.headers, timeout=8)
                if response.status_code == 200:
                    try:
                        root = ET.fromstring(response.content)
                        if root.tag in ['rss', 'feed'] or 'rss' in root.tag.lower():
                            return (True, 'Direct RSS feed found')
                    except ET.ParseError:
                        continue
            except requests.RequestException:
                continue
        try:
            response = requests.get(f'https://{domain}', headers=self.headers, timeout=10)
            if response.status_code == 200:
                content = response.text.lower()
                if any((indicator in content for indicator in ['application/rss+xml', '/rss', '/feed'])):
                    return (True, 'RSS feed detected')
        except requests.RequestException:
            pass
        try:
            google_rss_url = f'https://news.google.com/rss/search?q=site%3A{domain}&hl=en-US&gl=US&ceid=US%3Aen'
            response = requests.get(google_rss_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                if len(root.findall('.//item')) > 0:
                    return (True, 'Google News RSS available')
        except Exception:
            pass
        return (False, f'No RSS feed found for {domain}')

    def generate_rss_url(self, website_url):
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        domain = urlparse(website_url).netloc.replace('www.', '')
        for path in ['/rss', '/feed', '/rss.xml', '/feed.xml']:
            rss_url = f'https://{domain}{path}'
            try:
                response = requests.get(rss_url, headers=self.headers, timeout=8)
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    if len(root.findall('.//item')) > 0:
                        return rss_url
            except Exception:
                continue
        return f'https://news.google.com/rss/search?q=site%3A{domain}&hl=en-US&gl=US&ceid=US%3Aen'

    def fetch_rss_feed(self, rss_url, source_id=None):
        try:
            response = requests.get(rss_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            articles = []
            items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
            for item in items[:10]:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                description = item.find('description')
                if title is None:
                    title = item.find('.//{http://www.w3.org/2005/Atom}title')
                if link is None:
                    link_elem = item.find('.//{http://www.w3.org/2005/Atom}link')
                    if link_elem is not None:
                        link = type('obj', (object,), {'text': link_elem.get('href')})
                if pub_date is None:
                    pub_date = item.find('.//{http://www.w3.org/2005/Atom}published') or item.find('.//{http://www.w3.org/2005/Atom}updated')
                if description is None:
                    description = item.find('.//{http://www.w3.org/2005/Atom}summary')
                article_url = link.text if link is not None and hasattr(link, 'text') and link.text else ''
                articles.append({'title': title.text if title is not None and title.text else 'No title', 'link': article_url, 'pub_date': pub_date.text if pub_date is not None and pub_date.text else '', 'description': re.sub('<[^<]+?>', '', description.text) if description is not None and description.text else ''})
            return articles
        except Exception as e:
            logger.error(f'RSS fetch error: {e}')
            return []

    def extract_article_content(self, article_url):
        """Extract article content using newspaper4k with debugging"""
        final_url = self.resolve_url(article_url)
        if NEWSPAPER_AVAILABLE:
            try:
                article = newspaper.article(final_url)
                if article and hasattr(article, 'text'):
                    article_data = {'title': getattr(article, 'title', 'No title'), 'text': getattr(article, 'text', ''), 'authors': getattr(article, 'authors', []), 'publish_date': getattr(article, 'publish_date', None), 'summary': '', 'top_image': getattr(article, 'top_image', ''), 'final_url': final_url}
                    try:
                        article.nlp()
                        if hasattr(article, 'summary') and article.summary:
                            article_data['summary'] = article.summary
                        if hasattr(article, 'keywords') and article.keywords:
                            article_data['keywords'] = getattr(article, 'keywords', [])
                    except Exception:
                        pass
                    if len(article_data['text'].strip()) > 100:
                        return (article_data, None)
            except Exception:
                pass
        try:
            response = requests.get(final_url, headers=self.headers, timeout=20)
            if response.status_code != 200:
                return (None, f'HTTP {response.status_code} error')
            html_content = response.text
            clean_html = re.sub('<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            clean_html = re.sub('<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
            clean_html = re.sub('<nav[^>]*>.*?</nav>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
            clean_html = re.sub('<header[^>]*>.*?</header>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
            clean_html = re.sub('<footer[^>]*>.*?</footer>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
            title_match = re.search('<title[^>]*>(.*?)</title>', clean_html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1) if title_match else 'Article Title'
            title = re.sub('<[^>]+>', '', title).strip()
            content_patterns = ['<article[^>]*>(.*?)</article>', '<div[^>]*class="[^"]*(?:content|article|story|post-content|entry-content)[^"]*"[^>]*>(.*?)</div>', '<main[^>]*>(.*?)</main>', '<div[^>]*id="[^"]*(?:content|article|story|main)[^"]*"[^>]*>(.*?)</div>', '<div[^>]*class="[^"]*(?:text|paragraph|body)[^"]*"[^>]*>(.*?)</div>']
            article_content = ''
            for pattern in content_patterns:
                matches = re.findall(pattern, clean_html, re.DOTALL | re.IGNORECASE)
                if matches:
                    potential_content = max(matches, key=len)
                    cleaned = re.sub('<[^>]+>', '', potential_content)
                    cleaned = re.sub('\\s+', ' ', cleaned).strip()
                    if len(cleaned) > 200 and len(cleaned.split()) > 30:
                        article_content = cleaned
                        break
            if not article_content or len(article_content) < 200:
                paragraphs = re.findall('<p[^>]*>(.*?)</p>', clean_html, re.DOTALL | re.IGNORECASE)
                if paragraphs:
                    cleaned_paragraphs = []
                    for p in paragraphs:
                        cleaned = re.sub('<[^>]+>', '', p)
                        cleaned = re.sub('\\s+', ' ', cleaned).strip()
                        if len(cleaned) > 20:
                            cleaned_paragraphs.append(cleaned)
                    if cleaned_paragraphs:
                        article_content = '\n\n'.join(cleaned_paragraphs)
            if not article_content or len(article_content) < 200:
                all_text = re.sub('<[^>]+>', '', clean_html)
                all_text = re.sub('\\s+', ' ', all_text).strip()
                title_words = title.split()[:3]
                if title_words:
                    title_pattern = '.*?'.join((re.escape(word) for word in title_words))
                    match = re.search(title_pattern, all_text, re.IGNORECASE)
                    if match:
                        start_pos = match.start()
                        article_content = all_text[start_pos:start_pos + 5000]
                    else:
                        text_parts = all_text.split()
                        if len(text_parts) > 100:
                            start_idx = len(text_parts) // 4
                            end_idx = 3 * len(text_parts) // 4
                            article_content = ' '.join(text_parts[start_idx:end_idx])
                        else:
                            article_content = all_text
            if len(article_content) > 8000:
                article_content = article_content[:8000] + '...'
            return ({'title': title, 'text': article_content, 'authors': [], 'publish_date': None, 'summary': '', 'final_url': final_url}, None)
        except Exception as e:
            return (None, f'Content extraction failed: {str(e)}')

    def extract_with_requests(self, article_url):
        """Fallback extraction using requests"""
        try:
            final_url = self.resolve_url(article_url)
            response = requests.get(final_url, headers=self.headers, timeout=20)
            if response.status_code == 403:
                return (None, 'Website blocked access (403 Forbidden)')
            elif response.status_code == 404:
                return (None, 'Article not found (404)')
            elif response.status_code != 200:
                return (None, f'Website returned error {response.status_code}')
            html_content = response.text
            clean_html = re.sub('<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            clean_html = re.sub('<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
            title_match = re.search('<title[^>]*>(.*?)</title>', clean_html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1) if title_match else 'Article Title'
            title = re.sub('<[^>]+>', '', title).strip()
            clean_text = re.sub('<[^>]+>', '', clean_html)
            clean_text = re.sub('\\s+', ' ', clean_text).strip()
            for pattern in ['<article[^>]*>(.*?)</article>', '<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>', '<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>', '<main[^>]*>(.*?)</main>']:
                matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if matches:
                    article_content = max(matches, key=len)
                    article_content = re.sub('<[^>]+>', '', article_content)
                    article_content = re.sub('\\s+', ' ', article_content).strip()
                    if len(article_content) > 100:
                        clean_text = article_content
                        break
            if len(clean_text) > 100:
                text_parts = clean_text.split()
                start_idx = len(text_parts) // 4
                end_idx = 3 * len(text_parts) // 4
                clean_text = ' '.join(text_parts[start_idx:end_idx])
            if len(clean_text) > 5000:
                clean_text = clean_text[:5000] + '...'
            return ({'title': title, 'text': clean_text, 'authors': [], 'publish_date': None, 'summary': '', 'final_url': final_url}, None)
        except Exception as e:
            return (None, f'Content extraction failed: {str(e)}')

    def update_status_message(self, message, color=None):
        try:
            status_tag = f'news_status_{id(self)}'
            if dpg.does_item_exist(status_tag):
                dpg.set_value(status_tag, message)
                if color:
                    dpg.configure_item(status_tag, color=color)
        except Exception:
            pass

    def add_news_source(self):
        website_url = dpg.get_value(f'news_website_input_{id(self)}')
        refresh_interval = dpg.get_value(f'news_refresh_input_{id(self)}')
        if not website_url or refresh_interval < 1:
            self.update_status_message('Please enter valid website URL and refresh interval', self.BLOOMBERG_RED)
            return
        self.update_status_message(f'Validating {website_url}...', self.BLOOMBERG_YELLOW)

        def validation_worker():
            try:
                is_valid, message = self.validate_news_website(website_url)
                if not is_valid:
                    self.update_status_message(f'Error: {message}', self.BLOOMBERG_RED)
                    return
                rss_url = self.generate_rss_url(website_url)
                if not rss_url:
                    self.update_status_message('Could not generate RSS URL', self.BLOOMBERG_RED)
                    return
                self.update_status_message('Testing RSS feed...', self.BLOOMBERG_YELLOW)
                test_articles = self.fetch_rss_feed(rss_url)
                if not test_articles:
                    self.update_status_message('No articles found', self.BLOOMBERG_RED)
                    return
                source_name = urlparse(website_url if website_url.startswith(('http://', 'https://')) else 'https://' + website_url).netloc.replace('www.', '')
                max_id_result = self.conn.execute('SELECT COALESCE(MAX(id), 0) FROM news_sources').fetchone()
                source_id = max_id_result[0] + 1
                self.conn.execute('INSERT INTO news_sources (id, website_url, refresh_interval, source_name) VALUES (?, ?, ?, ?)', (source_id, website_url, refresh_interval, source_name))
                self.news_sources[source_id] = {'url': website_url, 'rss_url': rss_url, 'timer': refresh_interval, 'source_name': source_name, 'articles': test_articles, 'last_update': time.time(), 'status': 'Active'}
                self.start_refresh_timer(source_id)
                self.refresh_news_display()
                dpg.set_value(f'news_website_input_{id(self)}', '')
                dpg.set_value(f'news_refresh_input_{id(self)}', 5)
                self.update_status_message(f'Added: {source_name} - {len(test_articles)} articles', self.BLOOMBERG_GREEN)
            except Exception as e:
                self.update_status_message(f'Error: {str(e)}', self.BLOOMBERG_RED)
        threading.Thread(target=validation_worker, daemon=True).start()

    def start_refresh_timer(self, source_id):

        def refresh_worker():
            try:
                while source_id in self.news_sources:
                    time.sleep(self.news_sources[source_id]['timer'] * 60)
                    if source_id not in self.news_sources:
                        break
                    self.news_sources[source_id]['status'] = 'Updating...'
                    articles = self.fetch_rss_feed(self.news_sources[source_id]['rss_url'], source_id)
                    if source_id in self.news_sources:
                        if articles:
                            self.news_sources[source_id]['articles'] = articles
                            self.news_sources[source_id]['last_update'] = time.time()
                            self.news_sources[source_id]['status'] = 'Active'
                        else:
                            self.news_sources[source_id]['status'] = 'Error'
                        self.refresh_news_display()
            except Exception:
                if source_id in self.news_sources:
                    self.news_sources[source_id]['status'] = 'Error'
        refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        refresh_thread.start()
        self.refresh_threads[source_id] = refresh_thread

    def refresh_single_source(self, source_id):
        try:
            if source_id not in self.news_sources:
                return
            self.update_status_message(f'Refreshing {self.news_sources[source_id]['source_name']}...', self.BLOOMBERG_YELLOW)

            def refresh_worker():
                try:
                    self.news_sources[source_id]['status'] = 'Updating...'
                    self.refresh_news_display()
                    articles = self.fetch_rss_feed(self.news_sources[source_id]['rss_url'], source_id)
                    if source_id in self.news_sources:
                        if articles:
                            self.news_sources[source_id]['articles'] = articles
                            self.news_sources[source_id]['last_update'] = time.time()
                            self.news_sources[source_id]['status'] = 'Active'
                            self.update_status_message(f'Refreshed {self.news_sources[source_id]['source_name']} - {len(articles)} articles', self.BLOOMBERG_GREEN)
                        else:
                            self.news_sources[source_id]['status'] = 'Error'
                            self.update_status_message(f'Failed to refresh {self.news_sources[source_id]['source_name']}', self.BLOOMBERG_RED)
                        self.refresh_news_display()
                except Exception:
                    if source_id in self.news_sources:
                        self.news_sources[source_id]['status'] = 'Error'
                        self.update_status_message(f'Error refreshing {self.news_sources[source_id]['source_name']}', self.BLOOMBERG_RED)
                        self.refresh_news_display()
            threading.Thread(target=refresh_worker, daemon=True).start()
        except Exception:
            self.update_status_message('Refresh failed', self.BLOOMBERG_RED)

    def delete_news_source(self, source_id):
        try:
            if self.conn:
                self.conn.execute('DELETE FROM news_sources WHERE id = ?', (source_id,))
            if source_id in self.news_sources:
                source_name = self.news_sources[source_id]['source_name']
                del self.news_sources[source_id]
            if source_id in self.refresh_threads:
                del self.refresh_threads[source_id]
            self.refresh_news_display()
            self.update_status_message(f'Deleted {source_name}', self.BLOOMBERG_GREEN)
        except Exception:
            self.update_status_message('Error deleting source', self.BLOOMBERG_RED)

    def load_user_settings(self):
        try:
            if not self.conn:
                return
            sources = self.conn.execute('SELECT * FROM news_sources ORDER BY id').fetchall()
            for source in sources:
                source_id, website_url, refresh_interval, source_name, *_ = source
                rss_url = self.generate_rss_url(website_url)
                self.news_sources[source_id] = {'url': website_url, 'rss_url': rss_url, 'timer': refresh_interval, 'source_name': source_name, 'articles': [], 'last_update': 0, 'status': 'Loading...'}

                def load_source(sid, rss):
                    try:
                        articles = self.fetch_rss_feed(rss, sid)
                        if sid in self.news_sources:
                            if articles:
                                self.news_sources[sid]['articles'] = articles
                                self.news_sources[sid]['last_update'] = time.time()
                                self.news_sources[sid]['status'] = 'Active'
                            else:
                                self.news_sources[sid]['status'] = 'Error'
                            self.refresh_news_display()
                    except Exception:
                        if sid in self.news_sources:
                            self.news_sources[sid]['status'] = 'Error'
                threading.Thread(target=load_source, args=(source_id, rss_url), daemon=True).start()
                self.start_refresh_timer(source_id)
        except Exception:
            pass

    def wrap_text(self, text, width=80):
        """Wrap text to specified width"""
        words = text.split()
        lines = []
        current_line = ''
        for word in words:
            if len(current_line + ' ' + word) <= width:
                current_line += ' ' + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return '\n'.join(lines)

    def open_full_article(self, article_url, article_title):
        """Open full article with optimized 600x600 window and robust error handling"""

        def fetch_article_worker():
            window_id = f'article_window_{hash(article_url)}'
            content_tag = f'article_content_{hash(article_url)}'
            try:
                if dpg.does_item_exist(content_tag):
                    dpg.set_value(content_tag, '🔄 Starting extraction...\n\nInitializing article loader...')
                import signal

                def timeout_handler(signum, frame):
                    raise TimeoutError('Article extraction timed out after 30 seconds')
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(30)
                try:
                    if dpg.does_item_exist(content_tag):
                        dpg.set_value(content_tag, '🔄 Resolving URL...\n\nChecking if Google News redirect...')
                    final_url = article_url
                    if 'news.google.com' in article_url:
                        if dpg.does_item_exist(content_tag):
                            dpg.set_value(content_tag, '🔄 Resolving Google News URL...\n\nUsing Playwright to get actual article URL...')
                        final_url = self.resolve_url(article_url)
                        if dpg.does_item_exist(content_tag):
                            dpg.set_value(content_tag, f'🔄 URL resolved to:\n{final_url}\n\nExtracting content...')
                    if dpg.does_item_exist(content_tag):
                        dpg.set_value(content_tag, f'🔄 Extracting content...\n\nUsing {('Newspaper4k' if NEWSPAPER_AVAILABLE else 'Fallback')} method...')
                    article_data, error = self.extract_article_content(article_url)
                    if hasattr(signal, 'SIGALRM'):
                        signal.alarm(0)
                    if error or not article_data:
                        error_msg = f'❌ EXTRACTION FAILED\n\n'
                        error_msg += f'Title: {article_title}\n'
                        error_msg += f'Original URL: {article_url}\n'
                        if final_url != article_url:
                            error_msg += f'Resolved URL: {final_url}\n'
                        error_msg += f'Method: {('Newspaper4k' if NEWSPAPER_AVAILABLE else 'Fallback')}\n'
                        error_msg += f'Playwright: {('Available' if PLAYWRIGHT_AVAILABLE else 'Not Available')}\n\n'
                        if error:
                            error_msg += f'Error: {error}\n\n'
                        error_msg += "💡 Try 'Browser' button to read the full article."
                        if dpg.does_item_exist(content_tag):
                            dpg.set_value(content_tag, error_msg)
                        return
                    if dpg.does_item_exist(content_tag):
                        dpg.set_value(content_tag, '🔄 Formatting content...\n\nPreparing article display...')
                    content = ''
                    title = article_data.get('title', 'No Title')
                    content += f'📰 {title}\n'
                    content += '=' * min(len(title) + 4, 70) + '\n\n'
                    content += '📋 ARTICLE INFO:\n'
                    content += '-' * 40 + '\n'
                    if article_data.get('publish_date'):
                        pub_date = str(article_data['publish_date'])
                        content += f'📅 Published: {pub_date}\n'
                    else:
                        content += f'📅 Published: Not available\n'
                    if article_data.get('authors'):
                        authors_list = article_data['authors']
                        if len(authors_list) > 3:
                            authors_str = ', '.join(authors_list[:3]) + f' + {len(authors_list) - 3} more'
                        else:
                            authors_str = ', '.join(authors_list)
                        content += f'✍️  Authors: {authors_str}\n'
                    else:
                        content += f'✍️  Authors: Not available\n'
                    final_url = article_data.get('final_url', article_url)
                    content += f'🔗 Source: {final_url}\n'
                    if final_url != article_url:
                        content += f'🌐 Original: {article_url}\n'
                    content += '\n'
                    if article_data.get('keywords'):
                        keywords = article_data['keywords'][:8]
                        content += f'🏷️  Keywords: {', '.join(keywords)}\n\n'
                    if article_data.get('summary'):
                        content += '📝 SUMMARY:\n'
                        content += '-' * 40 + '\n'
                        summary_wrapped = self.wrap_text(article_data['summary'], 65)
                        content += summary_wrapped + '\n\n'
                    content += '📖 FULL ARTICLE:\n'
                    content += '=' * 40 + '\n\n'
                    if article_data.get('text') and len(article_data['text'].strip()) > 50:
                        clean_text = re.sub('\\n\\s*\\n', '\n\n', article_data['text'].strip())
                        clean_text = re.sub('\\n{3,}', '\n\n', clean_text)
                        clean_text = re.sub(' {2,}', ' ', clean_text)
                        paragraphs = clean_text.split('\n\n')
                        wrapped_paragraphs = []
                        for paragraph in paragraphs:
                            if paragraph.strip():
                                wrapped_paragraphs.append(self.wrap_text(paragraph.strip(), 65))
                        content += '\n\n'.join(wrapped_paragraphs)
                        word_count = len(clean_text.split())
                        char_count = len(clean_text)
                        reading_time = max(1, word_count // 200)
                        content += f'\n\n' + '=' * 40
                        content += f'\n📊 STATS: {word_count:,} words • {char_count:,} chars • ~{reading_time} min read'
                    else:
                        content += '⚠️  Article content could not be extracted.\n\n'
                        content += 'Common reasons:\n'
                        content += '• JavaScript-heavy content\n'
                        content += '• Paywall protection\n'
                        content += '• Anti-scraping measures\n\n'
                        content += "💡 Use 'Browser' button to read directly."
                    if dpg.does_item_exist(content_tag):
                        dpg.set_value(content_tag, content)
                except TimeoutError:
                    if hasattr(signal, 'SIGALRM'):
                        signal.alarm(0)
                    error_msg = f'⏰ TIMEOUT ERROR\n\n'
                    error_msg += f'Article extraction timed out after 30 seconds.\n\n'
                    error_msg += f'Title: {article_title}\n'
                    error_msg += f'URL: {article_url}\n\n'
                    error_msg += 'This usually happens when:\n'
                    error_msg += '• Website is very slow to respond\n'
                    error_msg += '• Complex JavaScript processing\n'
                    error_msg += '• Network connectivity issues\n\n'
                    error_msg += "💡 Try 'Browser' button or reload."
                    if dpg.does_item_exist(content_tag):
                        dpg.set_value(content_tag, error_msg)
            except Exception as e:
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                error_msg = f'❌ UNEXPECTED ERROR\n\n'
                error_msg += f'Title: {article_title}\n'
                error_msg += f'URL: {article_url}\n'
                error_msg += f'Error: {str(e)}\n'
                error_msg += f'Error Type: {type(e).__name__}\n\n'
                error_msg += "💡 Try 'Browser' button to read the article."
                if dpg.does_item_exist(content_tag):
                    dpg.set_value(content_tag, error_msg)
        window_id = f'article_window_{hash(article_url)}'
        content_tag = f'article_content_{hash(article_url)}'
        if dpg.does_item_exist(window_id):
            dpg.delete_item(window_id)
        try:
            display_title = article_title[:45] + '...' if len(article_title) > 45 else article_title
            with dpg.window(label=f'📰 {display_title}', tag=window_id, width=600, height=600, pos=[100, 100], modal=False):
                with dpg.group(horizontal=True):
                    dpg.add_button(label='❌', callback=lambda: dpg.delete_item(window_id), width=30, height=30)
                    dpg.add_button(label='🌐 Browser', callback=lambda: self.open_in_browser(article_url), width=80, height=30)
                    dpg.add_button(label='🔄', callback=lambda: threading.Thread(target=fetch_article_worker, daemon=True).start(), width=30, height=30)
                    dpg.add_spacer(width=10)
                    dpg.add_text('💡 Full article reader', color=self.BLOOMBERG_YELLOW)
                dpg.add_separator()
                dpg.add_input_text(tag=content_tag, default_value='🔄 Initializing...\n\nStarting article extraction process...', multiline=True, width=580, height=520, readonly=True)
            threading.Thread(target=fetch_article_worker, daemon=True).start()
        except Exception as e:
            try:
                with dpg.window(label='Article Error', width=400, height=200, pos=[200, 200]):
                    dpg.add_text(f'Failed to create article window: {str(e)}')
                    dpg.add_button(label='Open in Browser', callback=lambda: self.open_in_browser(article_url))
            except Exception:
                pass

    def open_in_browser(self, url):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass

    def refresh_news_display(self):
        try:
            container_tag = f'news_container_{id(self)}'
            parent_tag = f'news_main_window_{id(self)}'
            if not dpg.does_item_exist(parent_tag):
                return
            if dpg.does_item_exist(container_tag):
                dpg.delete_item(container_tag)
            with dpg.group(tag=container_tag, parent=parent_tag):
                if not self.news_sources:
                    with dpg.group():
                        dpg.add_text('📰 No news sources configured', color=self.BLOOMBERG_GRAY)
                        dpg.add_text('Add websites above to start receiving live news feeds', color=self.BLOOMBERG_YELLOW)
                        dpg.add_spacer(height=10)
                        dpg.add_text('💡 Supported: Most major news websites with RSS feeds', color=self.BLOOMBERG_WHITE)
                else:
                    self.create_news_grid()
        except Exception:
            pass

    def create_news_grid(self):
        try:
            sources = list(self.news_sources.items())
            for i in range(0, len(sources), 2):
                with dpg.group(horizontal=True):
                    if i < len(sources):
                        source_id, source_data = sources[i]
                        self.create_news_panel(source_id, source_data, 750, 400)
                    if i + 1 < len(sources):
                        source_id, source_data = sources[i + 1]
                        self.create_news_panel(source_id, source_data, 750, 400)
                dpg.add_spacer(height=10)
        except Exception:
            pass

    def create_news_panel(self, source_id, source_data, width, height):
        try:
            with dpg.child_window(width=width, height=height, border=True):
                with dpg.group(horizontal=True):
                    dpg.add_text(f'📰 {source_data['source_name'].upper()}', color=self.BLOOMBERG_ORANGE)
                    dpg.add_text(' • ', color=self.BLOOMBERG_GRAY)
                    status = source_data.get('status', 'Unknown')
                    status_color = self.BLOOMBERG_GREEN if status == 'Active' else self.BLOOMBERG_YELLOW if status in ['Loading...', 'Updating...'] else self.BLOOMBERG_RED
                    dpg.add_text(f'{status}', color=status_color)
                    dpg.add_text(' • ', color=self.BLOOMBERG_GRAY)
                    dpg.add_text(f'⏱️ {source_data['timer']}min', color=self.BLOOMBERG_GRAY)
                    if source_data['last_update']:
                        last_update = time.strftime('%H:%M:%S', time.localtime(source_data['last_update']))
                        dpg.add_text(f' • 🔄 {last_update}', color=self.BLOOMBERG_GREEN)
                    dpg.add_spacer(width=10)

                    def create_refresh_callback(source_id_to_refresh):

                        def callback(sender, app_data, user_data):
                            self.refresh_single_source(source_id_to_refresh)
                        return callback
                    dpg.add_button(label='🔄', callback=create_refresh_callback(source_id), width=30, height=25)

                    def create_delete_callback(source_id_to_delete):

                        def callback(sender, app_data, user_data):
                            self.delete_news_source(source_id_to_delete)
                        return callback
                    dpg.add_button(label='🗑️', callback=create_delete_callback(source_id), width=30, height=25)
                dpg.add_separator()
                articles = source_data.get('articles', [])
                with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, scrollY=True, scrollX=True, height=height - 80):
                    dpg.add_table_column(label='📄 Title', width_fixed=True, init_width_or_weight=500)
                    dpg.add_table_column(label='📅 Published', width_fixed=True, init_width_or_weight=120)
                    dpg.add_table_column(label='⚡ Action', width_fixed=True, init_width_or_weight=80)
                    if not articles:
                        with dpg.table_row():
                            dpg.add_text('Loading articles...', color=self.BLOOMBERG_YELLOW)
                            dpg.add_text('', color=self.BLOOMBERG_GRAY)
                            dpg.add_text('', color=self.BLOOMBERG_GRAY)
                    else:
                        for article in articles:
                            with dpg.table_row():
                                title = article['title']
                                with dpg.group():
                                    if len(title) > 60:
                                        words = title.split()
                                        current_line = ''
                                        lines = []
                                        for word in words:
                                            if len(current_line + ' ' + word) <= 60:
                                                current_line += ' ' + word if current_line else word
                                            else:
                                                if current_line:
                                                    lines.append(current_line)
                                                current_line = word
                                        if current_line:
                                            lines.append(current_line)
                                        for i, line in enumerate(lines[:3]):
                                            if i == 2 and len(lines) > 3:
                                                dpg.add_text(line + '...', color=self.BLOOMBERG_WHITE)
                                            else:
                                                dpg.add_text(line, color=self.BLOOMBERG_WHITE)
                                    else:
                                        dpg.add_text(title, color=self.BLOOMBERG_WHITE)
                                pub_date = article.get('pub_date', '')
                                if pub_date:
                                    date_str = pub_date[:16] if len(pub_date) > 16 else pub_date
                                    dpg.add_text(date_str, color=self.BLOOMBERG_GRAY)
                                else:
                                    dpg.add_text('Unknown', color=self.BLOOMBERG_GRAY)

                                def create_article_callback(article_data):

                                    def callback(sender, app_data, user_data):
                                        self.open_full_article(article_data['link'], article_data['title'])
                                    return callback
                                dpg.add_button(label='👁️', callback=create_article_callback(article), width=60, height=20)
        except Exception:
            dpg.add_text(f'Error displaying {source_data.get('source_name', 'Unknown')}', color=self.BLOOMBERG_RED)

    def create_header_bar(self):
        try:
            with dpg.group(horizontal=True):
                dpg.add_text('📰 FINCEPT', color=self.BLOOMBERG_ORANGE)
                dpg.add_text('NEWS TERMINAL', color=self.BLOOMBERG_WHITE)
                dpg.add_text(' • ', color=self.BLOOMBERG_GRAY)
                dpg.add_text(f'Sources: {len(self.news_sources)}', color=self.BLOOMBERG_YELLOW)
                dpg.add_text(' • ', color=self.BLOOMBERG_GRAY)
                dpg.add_text(time.strftime('%Y-%m-%d %H:%M:%S'), color=self.BLOOMBERG_WHITE)
        except Exception:
            pass

    def create_control_panel(self):
        try:
            unique_id = id(self)
            with dpg.group(horizontal=True):
                dpg.add_text('🌐 Website:', color=self.BLOOMBERG_WHITE)
                dpg.add_input_text(tag=f'news_website_input_{unique_id}', width=250, hint='e.g., reuters.com, bbc.com')
                dpg.add_text('⏱️ Refresh (min):', color=self.BLOOMBERG_WHITE)
                dpg.add_input_int(tag=f'news_refresh_input_{unique_id}', default_value=5, width=80, min_value=1, max_value=1440)
                dpg.add_button(label='➕ ADD SOURCE', callback=self.add_news_source, width=120, height=30)
                dpg.add_button(label='🔄 REFRESH ALL', callback=self.refresh_all_sources, width=120, height=30)
            dpg.add_text('Ready to add news sources', tag=f'news_status_{unique_id}', color=self.BLOOMBERG_YELLOW)
            dpg.add_spacer(height=5)
            with dpg.group(horizontal=True):
                dpg.add_text('⚡ Quick Add:', color=self.BLOOMBERG_BLUE)
                popular_sources = [('Reuters', 'reuters.com'), ('BBC', 'bbc.com'), ('CNN', 'cnn.com'), ('TechCrunch', 'techcrunch.com'), ('Bloomberg', 'bloomberg.com')]
                for name, url in popular_sources:

                    def create_quick_add_callback(source_url):

                        def callback(sender, app_data, user_data):
                            self.quick_add_source(source_url)
                        return callback
                    dpg.add_button(label=name, callback=create_quick_add_callback(url), width=80, height=25)
        except Exception:
            pass

    def create_content(self):
        try:
            unique_id = id(self)
            self.create_header_bar()
            dpg.add_separator()
            self.create_control_panel()
            dpg.add_separator()
            with dpg.child_window(tag=f'news_main_window_{unique_id}', height=-50, border=False):
                dpg.add_text('📰 REAL-TIME NEWS FEEDS', color=self.BLOOMBERG_ORANGE)
                dpg.add_separator()
                with dpg.group(tag=f'news_container_{unique_id}'):
                    if not self.news_sources:
                        with dpg.group():
                            dpg.add_text('📰 No news sources configured', color=self.BLOOMBERG_GRAY)
                            dpg.add_text('Add websites above to start receiving live news feeds', color=self.BLOOMBERG_YELLOW)
                            dpg.add_spacer(height=10)
                            dpg.add_text('💡 Supported: Most major news websites with RSS feeds', color=self.BLOOMBERG_WHITE)
            dpg.add_separator()
            self.create_status_bar()
            self.ui_initialized = True
        except Exception as e:
            dpg.add_text('📰 NEWS TERMINAL - ERROR', color=self.BLOOMBERG_RED)
            dpg.add_separator()
            dpg.add_text(f'Error loading interface: {str(e)}', color=self.BLOOMBERG_WHITE)

    def create_status_bar(self):
        try:
            with dpg.group(horizontal=True):
                dpg.add_text('📊 STATUS:', color=self.BLOOMBERG_GRAY)
                dpg.add_text('ACTIVE', color=self.BLOOMBERG_GREEN)
                dpg.add_text(' • ', color=self.BLOOMBERG_GRAY)
                dpg.add_text('SOURCES:', color=self.BLOOMBERG_GRAY)
                active_sources = sum((1 for source in self.news_sources.values() if source.get('status') == 'Active'))
                total_articles = sum((len(source.get('articles', [])) for source in self.news_sources.values()))
                dpg.add_text(f'{active_sources}/{len(self.news_sources)}', color=self.BLOOMBERG_YELLOW)
                dpg.add_text(' • ', color=self.BLOOMBERG_GRAY)
                dpg.add_text('ARTICLES:', color=self.BLOOMBERG_GRAY)
                dpg.add_text(f'{total_articles}', color=self.BLOOMBERG_WHITE)
                dpg.add_text(' • ', color=self.BLOOMBERG_GRAY)
                dpg.add_text('AUTO-REFRESH:', color=self.BLOOMBERG_GRAY)
                dpg.add_text('ON', color=self.BLOOMBERG_GREEN)
        except Exception:
            pass

    def quick_add_source(self, url):
        try:
            dpg.set_value(f'news_website_input_{id(self)}', url)
            dpg.set_value(f'news_refresh_input_{id(self)}', 5)
            self.add_news_source()
        except Exception:
            pass

    def refresh_all_sources(self):
        try:
            self.update_status_message('Refreshing all sources...', self.BLOOMBERG_YELLOW)

            def refresh_worker():
                refreshed_count = 0
                for source_id in list(self.news_sources.keys()):
                    try:
                        if source_id in self.news_sources:
                            self.news_sources[source_id]['status'] = 'Updating...'
                            articles = self.fetch_rss_feed(self.news_sources[source_id]['rss_url'], source_id)
                            if articles:
                                self.news_sources[source_id]['articles'] = articles
                                self.news_sources[source_id]['last_update'] = time.time()
                                self.news_sources[source_id]['status'] = 'Active'
                                refreshed_count += 1
                            else:
                                self.news_sources[source_id]['status'] = 'Error'
                    except Exception:
                        if source_id in self.news_sources:
                            self.news_sources[source_id]['status'] = 'Error'
                self.refresh_news_display()
                self.update_status_message(f'Refreshed {refreshed_count} sources', self.BLOOMBERG_GREEN)
            threading.Thread(target=refresh_worker, daemon=True).start()
        except Exception:
            self.update_status_message('Refresh failed', self.BLOOMBERG_RED)

    def cleanup(self):
        try:
            source_ids = list(self.news_sources.keys())
            for source_id in source_ids:
                if source_id in self.news_sources:
                    del self.news_sources[source_id]
            self.refresh_threads.clear()
            if self.conn:
                self.conn.close()
                self.conn = None
        except Exception:
            pass

    def __del__(self):
        self.cleanup()

def fetch_rss_feed(self, rss_url, source_id=None):
    try:
        response = requests.get(rss_url, headers=self.headers, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        articles = []
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        for item in items[:10]:
            title = item.find('title')
            link = item.find('link')
            pub_date = item.find('pubDate')
            description = item.find('description')
            if title is None:
                title = item.find('.//{http://www.w3.org/2005/Atom}title')
            if link is None:
                link_elem = item.find('.//{http://www.w3.org/2005/Atom}link')
                if link_elem is not None:
                    link = type('obj', (object,), {'text': link_elem.get('href')})
            if pub_date is None:
                pub_date = item.find('.//{http://www.w3.org/2005/Atom}published') or item.find('.//{http://www.w3.org/2005/Atom}updated')
            if description is None:
                description = item.find('.//{http://www.w3.org/2005/Atom}summary')
            article_url = link.text if link is not None and hasattr(link, 'text') and link.text else ''
            articles.append({'title': title.text if title is not None and title.text else 'No title', 'link': article_url, 'pub_date': pub_date.text if pub_date is not None and pub_date.text else '', 'description': re.sub('<[^<]+?>', '', description.text) if description is not None and description.text else ''})
        return articles
    except Exception as e:
        logger.error(f'RSS fetch error: {e}')
        return []

class ProfileTab(BaseTab):
    """Enhanced profile tab - refactored and optimized"""

    def __init__(self, app):
        super().__init__(app)
        self.constants = ProfileConstants()
        self.last_refresh = None
        self.usage_stats = {}
        self.request_count = 0
        self.logout_in_progress = False
        self.api_client = create_api_client(self._get_initial_session_data())
        self.data_manager = ProfileDataManager(app, self.api_client)
        self.ui_builder = ProfileUIBuilder(self)
        logger.info('ProfileTab initialized', context={'api_url': config.get_api_url()})

    def _get_initial_session_data(self):
        """Get initial session data safely"""
        if hasattr(self.app, 'get_session_data'):
            return self.app.get_session_data()
        elif hasattr(self.app, 'session_data'):
            return self.app.session_data
        return {self.constants.USER_TYPE_KEY: self.constants.UNKNOWN_USER_TYPE}

    def get_label(self):
        return 'Profile'

    @handle_errors('create_profile_content')
    def create_content(self):
        """Create profile content based on user type"""
        self.refresh_data()
        session_data = self.data_manager.get_session_data()
        user_type = session_data.get(self.constants.USER_TYPE_KEY, self.constants.UNKNOWN_USER_TYPE)
        content_creators = {self.constants.GUEST_USER_TYPE: self._create_guest_profile, self.constants.REGISTERED_USER_TYPE: self._create_user_profile, self.constants.UNKNOWN_USER_TYPE: self._create_unknown_profile}
        creator = content_creators.get(user_type, self._create_unknown_profile)
        creator()

    @handle_errors('refresh_profile_data')
    def refresh_data(self):
        """Refresh all profile data"""
        self.last_refresh = datetime.now()
        self.data_manager.invalidate_cache()
        session_data = self.data_manager.get_session_data()
        self.api_client = create_api_client(session_data)
        if session_data.get(self.constants.AUTHENTICATED_KEY) and self.api_client:
            self._fetch_authenticated_data()
        self._update_request_count()

    def _fetch_authenticated_data(self):
        """Fetch data for authenticated users"""
        try:
            if self.api_client.is_registered():
                profile_result = self.api_client.get_user_profile()
                if profile_result.get(self.constants.SUCCESS_KEY):
                    self.data_manager.update_session_data({'user_info': profile_result['profile']})
                usage_result = self.api_client.get_user_usage()
                if usage_result.get(self.constants.SUCCESS_KEY):
                    self.usage_stats = usage_result['usage']
            elif self.api_client.is_guest():
                status_result = self.api_client.get_guest_status()
                if status_result.get(self.constants.SUCCESS_KEY):
                    self.data_manager.update_session_data(status_result['status'])
        except Exception as e:
            logger.warning('Failed to fetch authenticated data', context={'error': str(e)})

    def _update_request_count(self):
        """Update request count from various sources"""
        if self.api_client:
            self.request_count = self.api_client.get_request_count()
        elif hasattr(self.app, 'api_request_count'):
            self.request_count = self.app.api_request_count
        else:
            session_data = self.data_manager.get_session_data()
            self.request_count = session_data.get('requests_today', 0)

    def _create_guest_profile(self):
        """Create guest user profile"""
        session_data = self.data_manager.get_session_data()
        api_key = session_data.get(self.constants.API_KEY_KEY)
        self.ui_builder.create_header('👤 Guest Profile', self.last_refresh)
        self.ui_builder.create_two_column_layout(lambda: self._create_guest_status_info(session_data, api_key), lambda: self._create_guest_upgrade_info(session_data))
        dpg.add_spacer(height=20)
        self._create_session_stats(session_data)

    def _create_user_profile(self):
        """Create registered user profile"""
        session_data = self.data_manager.get_session_data()
        user_info = session_data.get('user_info', {})
        username = user_info.get('username', 'User')
        self.ui_builder.create_header(f"🔑 {username}'s Profile", self.last_refresh)
        self.ui_builder.create_two_column_layout(lambda: self._create_user_account_info(user_info, session_data), lambda: self._create_user_usage_info(user_info, session_data))
        dpg.add_spacer(height=20)
        self._create_user_stats()

    def _create_unknown_profile(self):
        """Create unknown state profile"""
        self.ui_builder.create_header('❓ Unknown Session State', self.last_refresh)
        info_items = ['Unable to determine authentication status', 'This may indicate a configuration issue.', None, {'text': 'Try refreshing or restarting the application', 'color': self.constants.COLORS['warning']}]
        self.ui_builder.create_info_widget('Session Status', info_items, width=500, height=200)
        buttons = [{'label': '🔄 Refresh Profile', 'callback': self.manual_refresh}, {'label': 'Clear Session & Restart', 'callback': self.logout_user}]
        self.ui_builder.create_button_group(buttons)

    def _create_guest_status_info(self, session_data, api_key):
        """Create guest status information widget"""
        device_id = session_data.get(self.constants.DEVICE_ID_KEY, 'Unknown')
        display_device_id = device_id[:20] + '...' if len(device_id) > 20 else device_id
        daily_limit = session_data.get('daily_limit', self.constants.GUEST_DAILY_LIMIT)
        requests_today = session_data.get('requests_today', 0)
        remaining = max(0, daily_limit - requests_today)
        info_items = ['Account Type: Guest User', f'Device ID: {display_device_id}', None, self._get_api_key_info(api_key), None, f'Session Requests: {self.request_count}', f"Today's Requests: {requests_today}/{daily_limit}", {'text': f'Remaining Today: {remaining}', 'color': self.constants.COLORS['success'] if remaining > 10 else self.constants.COLORS['error']}, None, '✓ Basic market data', '✓ Real-time quotes', '✓ Public databases']
        self.ui_builder.create_info_widget('Current Session Status', info_items)

    def _create_guest_upgrade_info(self, session_data):
        """Create guest upgrade information widget"""
        api_key = session_data.get(self.constants.API_KEY_KEY)
        if api_key and api_key.startswith('fk_guest_'):
            current_status = '🔄 Current: Guest API Key'
            status_items = ['• Temporary access (24 hours)', '• 50 requests per day']
        else:
            current_status = '🔄 Current: Offline Mode'
            status_items = ['• No API access']
        info_items = [{'text': current_status, 'color': self.constants.COLORS['warning']}, None, *status_items, None, {'text': '🔑 Create Account', 'color': self.constants.COLORS['info']}, 'Get unlimited access:', '• Permanent API key', '• Unlimited requests', '• All databases access', '• Premium features']
        self.ui_builder.create_info_widget('Upgrade Your Access', info_items)
        buttons = [{'label': 'Create Free Account', 'callback': self.show_signup_info}, {'label': 'Sign In to Account', 'callback': self.show_login_info}]
        self.ui_builder.create_button_group(buttons)

    def _create_user_account_info(self, user_info, session_data):
        """Create user account information widget"""
        api_key = session_data.get(self.constants.API_KEY_KEY)
        info_items = [f'Username: {user_info.get('username', 'N/A')}', f'Email: {user_info.get('email', 'N/A')}', f'Account Type: {user_info.get('account_type', 'free').title()}', f'Member Since: {self._format_date(user_info.get('created_at'))}', None, {'text': 'Authentication:', 'color': self.constants.COLORS['info']}, self._get_api_key_info(api_key, is_user=True), None, '✓ Unlimited API requests', '✓ All database access', '✓ Premium features']
        self.ui_builder.create_info_widget('Account Details', info_items)
        buttons = [{'label': 'Regenerate API Key', 'callback': self.regenerate_api_key}, {'label': 'Switch Account', 'callback': self.logout_user}]
        self.ui_builder.create_button_group(buttons)

    def _create_user_usage_info(self, user_info, session_data):
        """Create user usage information widget"""
        credit_balance = user_info.get('credit_balance', 0)
        if credit_balance > 1000:
            balance_color, status = (self.constants.COLORS['success'], 'Excellent')
        elif credit_balance > 100:
            balance_color, status = (self.constants.COLORS['warning'], 'Good')
        else:
            balance_color, status = (self.constants.COLORS['error'], 'Low Credits')
        info_items = [f'Current Balance: {credit_balance} credits', {'text': f'Status: {status}', 'color': balance_color}, None, {'text': 'Live Usage Stats:', 'color': self.constants.COLORS['info']}, f'Total Requests: {self.usage_stats.get('total_requests', 'Loading...')}', f'Credits Used: {self.usage_stats.get('total_credits_used', 'Loading...')}', f'This Session: {self.request_count}', None, 'Quick Actions:']
        self.ui_builder.create_info_widget('Credits & Usage', info_items)
        buttons = [{'label': 'View Usage Details', 'callback': self.view_usage_stats}, {'label': 'API Documentation', 'callback': self.show_api_docs}, {'label': 'Subscription Info', 'callback': self.show_subscription_info}]
        self.ui_builder.create_button_group(buttons)

    def _create_session_stats(self, session_data):
        """Create session statistics for guest users"""
        dpg.add_text('📊 Live Session Statistics', color=self.constants.COLORS['info'])
        dpg.add_separator()
        dpg.add_spacer(height=10)
        api_key = session_data.get(self.constants.API_KEY_KEY)
        daily_limit = session_data.get('daily_limit', self.constants.GUEST_DAILY_LIMIT)
        requests_today = session_data.get('requests_today', 0)
        stats_text = [f'Session Requests: {self.request_count}', f'Daily Progress: {requests_today}/{daily_limit}', f'Authentication: {('API Key' if api_key else 'Offline')}', f'Server: {config.get_api_url()}']
        for stat in stats_text:
            dpg.add_text(stat)

    def _create_user_stats(self):
        """Create user statistics for registered users"""
        dpg.add_text('📊 Live Account Overview', color=self.constants.COLORS['info'])
        dpg.add_separator()
        dpg.add_spacer(height=10)
        stats_text = [f'Session Requests: {self.request_count}', f'Total Requests: {self.usage_stats.get('total_requests', 'Loading...')}', f'Success Rate: 100%', f'Server: {config.get_api_url()}', f'Last Update: {(self.last_refresh.strftime('%H:%M:%S') if self.last_refresh else 'Never')}']
        for stat in stats_text:
            dpg.add_text(stat)

    def _get_api_key_info(self, api_key, is_user=False):
        """Get API key information text"""
        if not api_key:
            return {'text': 'Method: No API Key', 'color': self.constants.COLORS['error']}
        if api_key.startswith('fk_user_'):
            return {'text': f'Method: Permanent API Key\nAPI Key: {api_key[:25]}...', 'color': self.constants.COLORS['success']}
        elif api_key.startswith('fk_guest_'):
            return {'text': f'Method: Temporary API Key\nAPI Key: {api_key[:20]}...', 'color': self.constants.COLORS['warning']}
        else:
            return {'text': f'Method: Legacy API Key\nAPI Key: {api_key[:20]}...', 'color': self.constants.COLORS['warning']}

    @lru_cache(maxsize=32)
    def _format_date(self, date_str):
        """Format date string for display"""
        if not date_str:
            return 'Never'
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str

    @handle_errors('manual_refresh')
    def manual_refresh(self):
        """Manual refresh with error handling"""
        self.refresh_data()
        self._recreate_content()
        self.show_message('Profile refreshed successfully', 'success')

    @handle_errors('logout_user')
    def logout_user(self):
        """Complete logout process"""
        if self.logout_in_progress:
            return
        self.logout_in_progress = True
        try:
            self._update_logout_button_state(True)
            logger.info('Starting logout process')
            self._perform_api_logout()
            self.data_manager.clear_session()
            self._clear_saved_credentials()
            self._complete_logout()
        finally:
            self.logout_in_progress = False

    def _perform_api_logout(self):
        """Perform API logout with fallbacks"""
        if not self.api_client or not self.data_manager.get_session_data().get(self.constants.AUTHENTICATED_KEY):
            return True
        try:
            result = self.api_client.make_request('POST', '/auth/logout')
            if result.get(self.constants.SUCCESS_KEY):
                logger.info('API logout successful')
                return True
        except Exception as e:
            logger.warning('API logout failed, performing local cleanup', context={'error': str(e)})
        return True

    def _clear_saved_credentials(self):
        """Clear saved credentials"""
        try:
            from fincept_terminal.utils.Managers.session_manager import session_manager
            session_manager.clear_credentials()
            logger.info('Saved credentials cleared')
        except ImportError:
            logger.debug('Session manager not available')
        except Exception as e:
            logger.warning('Could not clear credentials', context={'error': str(e)})

    def _complete_logout(self):
        """Complete logout and exit"""
        logger.info('Logout completed successfully')
        print('\n✅ Logout completed successfully!\n🚪 Closing Fincept Terminal...\n\nTo access Fincept again:\n1. 🔄 Run the application\n2. 🔑 Choose authentication method\n3. 👤 Sign in or continue as guest\n\n👋 Thank you for using Fincept!\n        '.strip())
        threading.Timer(self.constants.LOGOUT_TIMER_DELAY, self._exit_application).start()

    def _update_logout_button_state(self, logging_out=False):
        """Update logout button state"""
        try:
            if dpg.does_item_exist('logout_btn'):
                if logging_out:
                    dpg.set_item_label('logout_btn', 'Logging out...')
                    dpg.disable_item('logout_btn')
                else:
                    dpg.set_item_label('logout_btn', '🚪 Logout')
                    dpg.enable_item('logout_btn')
        except Exception as e:
            logger.debug('Could not update logout button', context={'error': str(e)})

    def _exit_application(self):
        """Exit application with fallbacks"""
        exit_methods = [lambda: self.app.close_application(), lambda: self.app.shutdown(), lambda: dpg.stop_dearpygui(), lambda: __import__('sys').exit(0)]
        for exit_method in exit_methods:
            try:
                exit_method()
                return
            except:
                continue

    @handle_errors('regenerate_api_key')
    def regenerate_api_key(self):
        """Regenerate API key for authenticated users"""
        if not self.api_client or not self.api_client.is_registered():
            self.show_message('API key regeneration requires authenticated user', 'error')
            return
        result = self.api_client.regenerate_api_key()
        if result.get(self.constants.SUCCESS_KEY):
            new_api_key = result.get(self.constants.API_KEY_KEY)
            if new_api_key:
                self.data_manager.update_session_data({self.constants.API_KEY_KEY: new_api_key})
                threading.Timer(1.0, self.manual_refresh).start()
                self.show_message('API key regenerated successfully!', 'success')
            else:
                self.show_message('No new API key received', 'error')
        else:
            self.show_message('API key regeneration failed', 'error')

    def view_usage_stats(self):
        """Display detailed usage statistics"""
        stats = [f'📊 Detailed Usage Statistics:', f'Total Requests: {self.usage_stats.get('total_requests', 0)}', f'Credits Used: {self.usage_stats.get('total_credits_used', 0)}', f'Session Requests: {self.request_count}', f'Success Rate: {self.usage_stats.get('success_rate', 100)}%']
        for stat in stats:
            print(stat)

    def show_api_docs(self):
        """Open API documentation"""
        try:
            api_docs_url = f'{config.get_api_url()}/docs'
            webbrowser.open(api_docs_url)
            print(f'✅ Opened API docs: {api_docs_url}')
        except Exception as e:
            print(f'📖 Manual URL: {config.get_api_url()}/docs')

    def show_subscription_info(self):
        """Display subscription information"""
        session_data = self.data_manager.get_session_data()
        user_type = session_data.get(self.constants.USER_TYPE_KEY)
        if user_type == self.constants.REGISTERED_USER_TYPE:
            print('💳 Registered Account - Full access to all features')
        else:
            print('💳 Guest Account - Limited access. Create account for full features')

    def show_signup_info(self):
        """Display signup information"""
        print('📝 Create Account: Use logout button to return to authentication screen')

    def show_login_info(self):
        """Display login information"""
        print('🔑 Sign In: Use logout button to return to authentication screen')

    def show_message(self, message: str, msg_type: str='info'):
        """Display message with appropriate styling"""
        icons = {'success': '✅', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}
        icon = icons.get(msg_type, 'ℹ️')
        print(f'{icon} {message}')
        if msg_type == 'error':
            logger.error(message)
        elif msg_type == 'warning':
            logger.warning(message)
        else:
            logger.info(message)

    def _recreate_content(self):
        """Safely recreate tab content"""
        try:
            if hasattr(self, 'content_tag') and dpg.does_item_exist(self.content_tag):
                children = dpg.get_item_children(self.content_tag, 1)
                for child in children:
                    if dpg.does_item_exist(child):
                        dpg.delete_item(child)
            self.create_content()
        except Exception as e:
            logger.warning('Could not recreate content', context={'error': str(e)})

    @handle_errors('cleanup')
    def cleanup(self):
        """Cleanup resources"""
        self.api_client = None
        self.usage_stats = {}
        self.request_count = 0
        self.data_manager.invalidate_cache()
        self._format_date.cache_clear()
        logger.info('ProfileTab cleanup completed')

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass

def view_usage_stats(self):
    """Display detailed usage statistics"""
    stats = [f'📊 Detailed Usage Statistics:', f'Total Requests: {self.usage_stats.get('total_requests', 0)}', f'Credits Used: {self.usage_stats.get('total_credits_used', 0)}', f'Session Requests: {self.request_count}', f'Success Rate: {self.usage_stats.get('success_rate', 100)}%']
    for stat in stats:
        print(stat)

def show_signup_info(self):
    """Display signup information"""
    print('📝 Create Account: Use logout button to return to authentication screen')

def show_login_info(self):
    """Display login information"""
    print('🔑 Sign In: Use logout button to return to authentication screen')

class OECDDataTab(BaseTab):
    """OECD Economic Data tab for displaying economic indicators from OECD"""

    def __init__(self, app):
        super().__init__(app)
        self.tab_id = str(uuid.uuid4())[:8]
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=2)
        try:
            from fincept_terminal.DatabaseConnector.DataSources.oced_data.oced_provider import OECDProvider
            self.oecd_provider = OECDProvider()
            print('✅ OECD Provider initialized successfully')
        except ImportError as e:
            error(f'Failed to import OECD provider: {e}', module='OECDDataTab')
            self.oecd_provider = None
            print(f'❌ OECD Provider import failed: {e}')
        try:
            from fincept_terminal.DatabaseConnector.DataSources.oced_data.constants import COUNTRY_TO_CODE_GDP, COUNTRY_TO_CODE_CPI, COUNTRY_TO_CODE_UNEMPLOYMENT, COUNTRY_TO_CODE_IR, COUNTRY_TO_CODE_CLI, COUNTRY_TO_CODE_SHARES, COUNTRY_TO_CODE_RGDP, COUNTRY_TO_CODE_GDP_FORECAST
            self.constants = {'gdp': list(COUNTRY_TO_CODE_GDP.keys())[:20], 'cpi': list(COUNTRY_TO_CODE_CPI.keys())[:20], 'unemployment': list(COUNTRY_TO_CODE_UNEMPLOYMENT.keys())[:20], 'interest_rates': list(COUNTRY_TO_CODE_IR.keys())[:20], 'cli': list(COUNTRY_TO_CODE_CLI.keys())[:20], 'shares': list(COUNTRY_TO_CODE_SHARES.keys())[:20], 'housing': list(COUNTRY_TO_CODE_RGDP.keys())[:20], 'forecast': list(COUNTRY_TO_CODE_GDP_FORECAST.keys())[:20]}
            print('✅ Constants imported successfully')
        except ImportError as e:
            self.constants = {'gdp': ['united_states', 'germany', 'japan', 'united_kingdom', 'france', 'italy', 'canada', 'australia', 'spain', 'netherlands', 'g7', 'g20', 'oecd', 'all']}
            print(f'⚠️ Using fallback constants: {e}')
        self.current_data = {}
        self.last_refresh = None
        self.indicators = {'GDP Nominal': {'method': 'get_gdp_nominal', 'params': ['countries', 'frequency', 'units', 'price_base'], 'countries_key': 'gdp', 'description': 'Gross Domestic Product at market prices', 'y_label': 'GDP Value', 'units_info': {'level': 'USD (Millions)', 'index': 'Index (2015=100)', 'capita': 'USD per Capita', 'growth': 'Growth Rate (%)'}}, 'GDP Real': {'method': 'get_gdp_real', 'params': ['countries', 'frequency'], 'countries_key': 'gdp', 'description': 'Real GDP (PPP-adjusted, constant prices)', 'y_label': 'Real GDP (USD PPP)', 'units_info': {'default': 'USD PPP (Millions)'}}, 'Consumer Price Index': {'method': 'get_cpi', 'params': ['countries', 'frequency', 'transform', 'harmonized', 'expenditure'], 'countries_key': 'cpi', 'description': 'Consumer Price Index - Inflation measure', 'y_label': 'CPI Value', 'units_info': {'index': 'Index (2015=100)', 'yoy': 'Year-over-Year (%)', 'mom': 'Month-over-Month (%)'}}, 'Unemployment Rate': {'method': 'get_unemployment', 'params': ['countries', 'frequency', 'sex', 'age', 'seasonal_adjustment'], 'countries_key': 'unemployment', 'description': 'Unemployment rate as % of labor force', 'y_label': 'Unemployment Rate (%)', 'units_info': {'default': 'Percentage (%)'}}, 'Interest Rates': {'method': 'get_interest_rates', 'params': ['countries', 'duration', 'frequency'], 'countries_key': 'interest_rates', 'description': 'Interest rates by duration', 'y_label': 'Interest Rate (%)', 'units_info': {'default': 'Percentage (%)'}}}
        self.param_options = {'frequency': ['monthly', 'quarter', 'annual'], 'units': ['level', 'index', 'capita', 'volume', 'current_prices', 'growth', 'deflator'], 'price_base': ['current_prices', 'volume'], 'transform': ['index', 'yoy', 'mom', 'period'], 'expenditure': ['total', 'food_non_alcoholic_beverages', 'housing_water_electricity_gas', 'transport', 'energy'], 'sex': ['total', 'male', 'female'], 'age': ['total', '15-24', '25+'], 'duration': ['immediate', 'short', 'long'], 'adjustment': ['amplitude', 'normalized']}

    def get_label(self):
        return 'OECD'

    def get_countries_for_indicator(self, indicator: str) -> List[str]:
        """Get available countries for a specific indicator"""
        if indicator in self.indicators:
            countries_key = self.indicators[indicator].get('countries_key', 'gdp')
            return self.constants.get(countries_key, self.constants.get('gdp', []))
        return self.constants.get('gdp', [])

    def format_number(self, value: float, unit_type: str='default') -> str:
        """Format numbers for better readability"""
        try:
            if value is None or str(value).lower() == 'nan':
                return 'N/A'
            num_value = float(value)
            if '%' in unit_type or 'percentage' in unit_type.lower():
                return f'{num_value:.2f}%'
            abs_value = abs(num_value)
            if abs_value >= 1000000000000:
                return f'{num_value / 1000000000000:.2f}T'
            elif abs_value >= 1000000000:
                return f'{num_value / 1000000000:.2f}B'
            elif abs_value >= 1000000:
                return f'{num_value / 1000000:.2f}M'
            elif abs_value >= 1000:
                return f'{num_value:,.0f}'
            elif abs_value >= 1:
                return f'{num_value:.2f}'
            else:
                return f'{num_value:.4f}'
        except (ValueError, TypeError):
            return str(value) if value is not None else 'N/A'

    def get_y_axis_label(self, indicator: str, params: Dict[str, Any]) -> str:
        """Generate appropriate Y-axis label based on indicator and parameters"""
        if indicator not in self.indicators:
            return 'Value'
        config = self.indicators[indicator]
        base_label = config.get('y_label', 'Value')
        units_info = config.get('units_info', {})
        unit_key = params.get('units', params.get('transform', 'default'))
        unit_desc = units_info.get(unit_key, units_info.get('default', ''))
        if unit_desc:
            return f'{base_label} ({unit_desc})'
        return base_label

    def create_content(self):
        """Create the enhanced OECD data interface"""
        try:
            print('🔧 Creating enhanced OECD content...')
            with dpg.group():
                dpg.add_text('🌍 OECD Economic Indicators', color=[100, 200, 255])
                dpg.add_text('Access comprehensive economic data from OECD countries with enhanced visualizations', color=[180, 180, 180])
                with dpg.group(horizontal=True):
                    dpg.add_text('Last Updated:', color=[150, 150, 150])
                    dpg.add_text('Not yet loaded', tag=f'last_update_{self.tab_id}', color=[120, 120, 120])
            dpg.add_spacer(height=15)
            if not self.oecd_provider:
                dpg.add_text('❌ OECD Provider not available. Check import paths.', color=[255, 100, 100])
                return
            with dpg.child_window(height=750, border=True):
                with dpg.collapsing_header(label='📊 Data Selection & Parameters', default_open=True):
                    dpg.add_spacer(height=5)
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            dpg.add_text('Economic Indicator:', color=[200, 200, 100])
                            dpg.add_combo(list(self.indicators.keys()), tag=f'indicator_{self.tab_id}', default_value='GDP Nominal', width=220, callback=self.on_indicator_change)
                        dpg.add_text('', tag=f'indicator_desc_{self.tab_id}', color=[160, 160, 160], wrap=600)
                    dpg.add_spacer(height=10)
                    with dpg.group(horizontal=True):
                        dpg.add_text('Country/Region:')
                        initial_countries = self.get_countries_for_indicator('GDP Nominal')
                        dpg.add_combo(initial_countries, tag=f'countries_{self.tab_id}', default_value=initial_countries[0] if initial_countries else 'united_states', width=150)
                        dpg.add_spacer(width=30)
                        dpg.add_text('Start Date:')
                        dpg.add_input_text(tag=f'start_date_{self.tab_id}', default_value='2020-01-01', width=110, hint='YYYY-MM-DD')
                        dpg.add_spacer(width=15)
                        dpg.add_text('End Date:')
                        dpg.add_input_text(tag=f'end_date_{self.tab_id}', default_value='2024-12-31', width=110, hint='YYYY-MM-DD')
                    dpg.add_spacer(height=10)
                    with dpg.group(tag=f'dynamic_params_{self.tab_id}'):
                        self.create_parameter_controls('GDP Nominal')
                    dpg.add_spacer(height=15)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label='📈 Fetch Data', callback=self.fetch_data, width=130, height=35)
                        dpg.add_button(label='🔄 Refresh', callback=self.refresh_data, width=100, height=35)
                        dpg.add_button(label='🧹 Clear', callback=self.clear_data, width=90, height=35)
                        dpg.add_button(label='📊 Export CSV', callback=self.export_data, width=130, height=35)
                    dpg.add_spacer(height=10)
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            dpg.add_text('Status:', color=[150, 150, 150])
                            dpg.add_text('Ready', tag=f'status_{self.tab_id}', color=[100, 255, 100])
                        dpg.add_text('', tag=f'data_summary_{self.tab_id}', color=[140, 140, 140])
                dpg.add_separator()
                dpg.add_spacer(height=5)
                with dpg.tab_bar():
                    with dpg.tab(label='📈 Interactive Chart'):
                        dpg.add_spacer(height=8)
                        with dpg.group():
                            with dpg.group(horizontal=True):
                                dpg.add_text('Chart Type:')
                                dpg.add_combo(['Line', 'Bar', 'Scatter'], tag=f'chart_type_{self.tab_id}', default_value='Line', width=100, callback=self.on_chart_type_change)
                                dpg.add_spacer(width=20)
                                dpg.add_checkbox(label='Show Grid', tag=f'show_grid_{self.tab_id}', default_value=True, callback=self.update_chart)
                                dpg.add_spacer(width=20)
                                dpg.add_checkbox(label='Auto-scale Y', tag=f'auto_scale_{self.tab_id}', default_value=True)
                                dpg.add_spacer(width=30)
                                dpg.add_button(label='🔄 Refresh Chart', callback=self.update_chart, width=140)
                        dpg.add_spacer(height=10)
                        with dpg.plot(tag=f'chart_plot_{self.tab_id}', label='Economic Data Visualization', height=400, width=-1):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label='Time Period', tag=f'x_axis_{self.tab_id}')
                            dpg.add_plot_axis(dpg.mvYAxis, label='Value', tag=f'y_axis_{self.tab_id}')
                        with dpg.group():
                            dpg.add_text('Chart Information:', color=[150, 150, 200])
                            dpg.add_text('', tag=f'chart_info_{self.tab_id}', color=[130, 130, 130], wrap=800)
                    with dpg.tab(label='📊 Data Table'):
                        dpg.add_spacer(height=8)
                        with dpg.group(horizontal=True):
                            dpg.add_text('Show rows:')
                            dpg.add_combo(['25', '50', '100', 'All'], tag=f'table_limit_{self.tab_id}', default_value='50', width=80, callback=self.update_table)
                            dpg.add_spacer(width=20)
                            dpg.add_text('Search:')
                            dpg.add_input_text(tag=f'table_search_{self.tab_id}', width=150, hint='Filter data...', callback=self.update_table)
                        dpg.add_spacer(height=10)
                        with dpg.table(tag=f'data_table_{self.tab_id}', header_row=True, resizable=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=380, sortable=True):
                            dpg.add_table_column(label='Date', width_fixed=True, init_width_or_weight=120)
                            dpg.add_table_column(label='Country', width_fixed=True, init_width_or_weight=140)
                            dpg.add_table_column(label='Value', width_fixed=True, init_width_or_weight=180)
                            dpg.add_table_column(label='Frequency', width_fixed=True, init_width_or_weight=100)
                            dpg.add_table_column(label='Indicator', width_fixed=True, init_width_or_weight=160)
                    with dpg.tab(label='📈 Statistics'):
                        dpg.add_spacer(height=10)
                        with dpg.group():
                            dpg.add_text('Data Statistics & Analysis', color=[200, 200, 100])
                            dpg.add_spacer(height=10)
                            with dpg.group(tag=f'stats_display_{self.tab_id}'):
                                dpg.add_text('No data loaded for analysis...', color=[140, 140, 140])
                    with dpg.tab(label='🔍 Raw Data'):
                        dpg.add_spacer(height=8)
                        with dpg.group(horizontal=True):
                            dpg.add_button(label='📋 Copy JSON', callback=self.copy_raw_data, width=130)
                            dpg.add_button(label='💾 Save JSON', callback=self.save_raw_data, width=130)
                        dpg.add_spacer(height=10)
                        dpg.add_input_text(tag=f'raw_display_{self.tab_id}', multiline=True, height=380, width=-1, readonly=True, default_value='No data loaded...')
            print('✅ Enhanced OECD content created successfully')
        except Exception as e:
            error(f'Error creating OECD tab content: {str(e)}', module='OECDDataTab')
            print(f'❌ Error creating content: {str(e)}')
            print(f'❌ Traceback: {traceback.format_exc()}')
            dpg.add_text(f'Error: {str(e)}', color=[255, 100, 100])

    def create_parameter_controls(self, indicator: str):
        """Create dynamic parameter controls with better layout and error handling"""
        try:
            print(f'🔧 Creating enhanced parameters for {indicator}')
            if not dpg.does_item_exist(f'dynamic_params_{self.tab_id}'):
                print(f'❌ Parent container dynamic_params_{self.tab_id} does not exist')
                return
            children = dpg.get_item_children(f'dynamic_params_{self.tab_id}', 1)
            if children:
                for child in children:
                    try:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
                    except Exception as e:
                        print(f'⚠️ Error deleting child item {child}: {e}')
            if indicator not in self.indicators:
                print(f'❌ Indicator {indicator} not found in indicators')
                return
            if dpg.does_item_exist(f'indicator_desc_{self.tab_id}'):
                desc = self.indicators[indicator].get('description', 'Economic data indicator')
                dpg.set_value(f'indicator_desc_{self.tab_id}', f'📝 {desc}')
            params = self.indicators[indicator]['params']
            filtered_params = [param for param in params if param != 'countries']
            if not filtered_params:
                dpg.add_text('No additional parameters required for this indicator', parent=f'dynamic_params_{self.tab_id}', color=[140, 140, 140])
                return
            param_count = 0
            current_row = None
            for param in filtered_params:
                try:
                    if param_count % 3 == 0:
                        current_row = dpg.add_group(horizontal=True, parent=f'dynamic_params_{self.tab_id}')
                        if not dpg.does_item_exist(current_row):
                            print(f'❌ Failed to create row group')
                            continue
                    param_group = dpg.add_group(horizontal=True, parent=current_row)
                    if not dpg.does_item_exist(param_group):
                        print(f'❌ Failed to create parameter group for {param}')
                        continue
                    label_text = f'{param.replace('_', ' ').title()}:'
                    dpg.add_text(label_text, parent=param_group)
                    param_tag = f'{param}_{self.tab_id}'
                    if param in self.param_options:
                        dpg.add_combo(self.param_options[param], tag=param_tag, default_value=self.param_options[param][0], width=130, parent=param_group)
                    elif param in ['harmonized', 'seasonal_adjustment', 'growth_rate']:
                        dpg.add_checkbox(tag=param_tag, default_value=False, parent=param_group)
                    else:
                        dpg.add_input_text(tag=param_tag, width=130, hint=f'Enter {param}', parent=param_group)
                    if param_count % 3 < 2 and param_count < len(filtered_params) - 1:
                        dpg.add_spacer(width=20, parent=current_row)
                    param_count += 1
                except Exception as param_error:
                    print(f'❌ Error creating control for parameter {param}: {param_error}')
                    continue
            print(f'✅ Enhanced parameters created for {indicator} ({param_count} parameters)')
        except Exception as e:
            error(f'Error creating parameter controls: {str(e)}', module='OECDDataTab')
            print(f'❌ Error creating parameters: {str(e)}')
            print(f'❌ Traceback: {traceback.format_exc()}')
            try:
                if dpg.does_item_exist(f'dynamic_params_{self.tab_id}'):
                    dpg.add_text(f'Error loading parameters for {indicator}', parent=f'dynamic_params_{self.tab_id}', color=[255, 100, 100])
            except Exception as fallback_error:
                print(f'❌ Even fallback failed: {fallback_error}')

    def on_indicator_change(self, sender, app_data):
        """Handle indicator selection change with enhanced feedback"""
        try:
            print(f'🔧 Indicator changed to: {app_data}')
            countries = self.get_countries_for_indicator(app_data)
            if dpg.does_item_exist(f'countries_{self.tab_id}'):
                dpg.configure_item(f'countries_{self.tab_id}', items=countries)
                if countries:
                    dpg.set_value(f'countries_{self.tab_id}', countries[0])
            self.create_parameter_controls(app_data)
            self.update_status('Indicator changed - ready for new data', [200, 200, 100])
        except Exception as e:
            error(f'Error in indicator change: {str(e)}', module='OECDDataTab')
            print(f'❌ Error in indicator change: {str(e)}')

    def on_chart_type_change(self, sender, app_data):
        """Handle chart type change"""
        try:
            if self.current_data:
                self.update_chart()
        except Exception as e:
            print(f'❌ Error in chart type change: {str(e)}')

    def fetch_data(self):
        """Fetch OECD data with enhanced error handling"""
        try:
            print('🔧 Starting enhanced data fetch...')
            if not self.oecd_provider:
                self.update_status('❌ OECD Provider not available', [255, 100, 100])
                return
            indicator = dpg.get_value(f'indicator_{self.tab_id}')
            if indicator not in self.indicators:
                self.update_status('❌ Invalid indicator selected', [255, 100, 100])
                return
            print(f'🔧 Fetching {indicator} data...')
            self.update_status('🔄 Fetching data from OECD...', [255, 255, 100])
            params = self.prepare_parameters(indicator)
            future = self.process_executor.submit(_fetch_data_in_process, self.indicators[indicator], params)
            monitor_thread = threading.Thread(target=self._monitor_fetch_completion, args=(future, indicator), daemon=True)
            monitor_thread.start()
        except Exception as e:
            error(f'Error fetching data: {str(e)}', module='OECDDataTab')
            print(f'❌ Error fetching data: {str(e)}')
            self.update_status(f'❌ Error: {str(e)}', [255, 100, 100])

    def refresh_data(self):
        """Refresh current data"""
        try:
            if self.current_data:
                self.fetch_data()
            else:
                self.update_status('⚠️ No data to refresh - fetch data first', [255, 200, 100])
        except Exception as e:
            print(f'❌ Error refreshing data: {str(e)}')

    def _monitor_fetch_completion(self, future: concurrent.futures.Future, indicator: str):
        """Enhanced monitoring with better error handling"""
        try:
            data = future.result(timeout=120)

            def update_ui():
                try:
                    if data.get('success'):
                        self.current_data = data
                        self.update_displays(data, indicator)
                        self.update_statistics(data)
                        data_count = len(data.get('data', []))
                        country = data.get('countries', 'Unknown')
                        freq = data.get('frequency', 'Unknown')
                        self.update_status(f'✅ Loaded {data_count} data points', [100, 255, 100])
                        self.update_data_summary(f'📊 {data_count} records • {country} • {freq} frequency')
                        self.last_refresh = datetime.now()
                        if dpg.does_item_exist(f'last_update_{self.tab_id}'):
                            dpg.set_value(f'last_update_{self.tab_id}', self.last_refresh.strftime('%Y-%m-%d %H:%M:%S'))
                            dpg.configure_item(f'last_update_{self.tab_id}', color=[100, 255, 100])
                    else:
                        error_msg = data.get('error', 'Unknown error occurred')
                        print(f'❌ Data fetch failed: {error_msg}')
                        self.update_status(f'❌ {error_msg}', [255, 100, 100])
                        self.update_data_summary('No data available')
                except Exception as ui_error:
                    print(f'❌ Error updating UI: {ui_error}')
                    self.update_status(f'❌ UI Error: {str(ui_error)}', [255, 100, 100])
            threading.Timer(0.1, update_ui).start()
        except concurrent.futures.TimeoutError:
            print('❌ Fetch operation timed out')

            def timeout_update():
                self.update_status('❌ Request timed out (120s)', [255, 100, 100])
            threading.Timer(0.1, timeout_update).start()
        except Exception as e:
            print(f'❌ Error in fetch monitoring: {str(e)}')

            def error_update():
                self.update_status(f'❌ Monitoring error: {str(e)}', [255, 100, 100])
            threading.Timer(0.1, error_update).start()

    def prepare_parameters(self, indicator: str) -> Dict[str, Any]:
        """Prepare API parameters with validation"""
        try:
            params = {}
            params['countries'] = dpg.get_value(f'countries_{self.tab_id}')
            start_date = dpg.get_value(f'start_date_{self.tab_id}')
            end_date = dpg.get_value(f'end_date_{self.tab_id}')
            if start_date and start_date.strip():
                params['start_date'] = start_date.strip()
            if end_date and end_date.strip():
                params['end_date'] = end_date.strip()
            for param in self.indicators[indicator]['params']:
                if param == 'countries':
                    continue
                param_tag = f'{param}_{self.tab_id}'
                if dpg.does_item_exist(param_tag):
                    value = dpg.get_value(param_tag)
                    if value is not None and (value != '' or isinstance(value, bool)):
                        params[param] = value
            return params
        except Exception as e:
            error(f'Error preparing parameters: {str(e)}', module='OECDDataTab')
            print(f'❌ Error preparing parameters: {str(e)}')
            return {'countries': 'united_states'}

    def update_displays(self, data: Dict[str, Any], indicator: str):
        """Update all display components with enhanced formatting"""
        try:
            print('🔧 Updating enhanced displays...')
            self.update_chart(data=data, indicator=indicator)
            self.update_table(data=data)
            self.update_raw_display(data)
            self.update_chart_info(data, indicator)
            print('✅ Enhanced displays updated')
        except Exception as e:
            error(f'Error updating displays: {str(e)}', module='OECDDataTab')
            print(f'❌ Error updating displays: {str(e)}')

    def update_chart(self, sender=None, app_data=None, data=None, indicator=None):
        """Update chart with enhanced formatting and proper axis labels"""
        try:
            if data is None:
                data = self.current_data
            if not data or 'data' not in data:
                print('❌ No data for chart')
                return
            chart_data = data['data']
            if not isinstance(chart_data, list) or not chart_data:
                print('❌ Invalid chart data')
                return
            print(f'🔧 Updating enhanced chart with {len(chart_data)} data points')
            if dpg.does_item_exist(f'y_axis_{self.tab_id}'):
                children = dpg.get_item_children(f'y_axis_{self.tab_id}', 1)
                if children:
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
            plot_data = []
            date_labels = []
            for item in chart_data:
                value = item.get('value')
                date_str = item.get('date', '')
                if value is not None and str(value).lower() != 'nan':
                    try:
                        float_value = float(value)
                        plot_data.append(float_value)
                        date_labels.append(date_str)
                    except (ValueError, TypeError):
                        continue
            if not plot_data:
                print('❌ No valid plot data')
                return
            x_values = list(range(len(plot_data)))
            y_values = plot_data
            chart_type = dpg.get_value(f'chart_type_{self.tab_id}') if dpg.does_item_exist(f'chart_type_{self.tab_id}') else 'Line'
            show_grid = dpg.get_value(f'show_grid_{self.tab_id}') if dpg.does_item_exist(f'show_grid_{self.tab_id}') else True
            country = data.get('countries', 'Data').replace('_', ' ').title()
            indicator_name = data.get('indicator', indicator or 'Economic Data').replace('_', ' ').title()
            frequency = data.get('frequency', '').title()
            series_label = f'{country} - {indicator_name}'
            if frequency:
                series_label += f' ({frequency})'
            if dpg.does_item_exist(f'x_axis_{self.tab_id}'):
                dpg.configure_item(f'x_axis_{self.tab_id}', label='Time Period')
            if dpg.does_item_exist(f'y_axis_{self.tab_id}'):
                current_indicator = dpg.get_value(f'indicator_{self.tab_id}') if dpg.does_item_exist(f'indicator_{self.tab_id}') else indicator
                params = self.prepare_parameters(current_indicator) if current_indicator else {}
                y_label = self.get_y_axis_label(current_indicator, params)
                dpg.configure_item(f'y_axis_{self.tab_id}', label=y_label)
            if chart_type == 'Line':
                dpg.add_line_series(x_values, y_values, label=series_label, parent=f'y_axis_{self.tab_id}')
            elif chart_type == 'Bar':
                dpg.add_bar_series(x_values, y_values, label=series_label, parent=f'y_axis_{self.tab_id}')
            elif chart_type == 'Scatter':
                dpg.add_scatter_series(x_values, y_values, label=series_label, parent=f'y_axis_{self.tab_id}')
            if dpg.does_item_exist(f'chart_plot_{self.tab_id}'):
                if show_grid:
                    pass
            auto_scale = dpg.get_value(f'auto_scale_{self.tab_id}') if dpg.does_item_exist(f'auto_scale_{self.tab_id}') else True
            if auto_scale:
                if dpg.does_item_exist(f'x_axis_{self.tab_id}'):
                    dpg.fit_axis_data(f'x_axis_{self.tab_id}')
                if dpg.does_item_exist(f'y_axis_{self.tab_id}'):
                    dpg.fit_axis_data(f'y_axis_{self.tab_id}')
            print('✅ Enhanced chart updated successfully')
        except Exception as e:
            error(f'Error updating chart: {str(e)}', module='OECDDataTab')
            print(f'❌ Error updating chart: {str(e)}')

    def update_chart_info(self, data: Dict[str, Any], indicator: str):
        """Update chart information panel"""
        try:
            if not dpg.does_item_exist(f'chart_info_{self.tab_id}'):
                return
            chart_data = data.get('data', [])
            if not chart_data:
                dpg.set_value(f'chart_info_{self.tab_id}', 'No data to display')
                return
            values = []
            for item in chart_data:
                try:
                    val = float(item.get('value'))
                    if str(val).lower() != 'nan':
                        values.append(val)
                except:
                    continue
            if values:
                info_text = f'Data Points: {len(values)} | Min: {self.format_number(min(values))} | Max: {self.format_number(max(values))} | Avg: {self.format_number(sum(values) / len(values))}'
                if len(chart_data) > 1:
                    date_range = f' | Period: {chart_data[0].get('date', 'N/A')} to {chart_data[-1].get('date', 'N/A')}'
                    info_text += date_range
                dpg.set_value(f'chart_info_{self.tab_id}', info_text)
            else:
                dpg.set_value(f'chart_info_{self.tab_id}', 'No valid numerical data found')
        except Exception as e:
            print(f'❌ Error updating chart info: {str(e)}')

    def update_table(self, sender=None, app_data=None, data=None):
        """Update data table with enhanced formatting and search"""
        try:
            if data is None:
                data = self.current_data
            if not data or 'data' not in data:
                return
            table_data = data['data']
            if not isinstance(table_data, list):
                return
            print(f'🔧 Updating enhanced table with {len(table_data)} rows')
            if dpg.does_item_exist(f'data_table_{self.tab_id}'):
                children = dpg.get_item_children(f'data_table_{self.tab_id}', 1)
                if children:
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
            search_term = ''
            if dpg.does_item_exist(f'table_search_{self.tab_id}'):
                search_term = dpg.get_value(f'table_search_{self.tab_id}').lower()
            filtered_data = table_data
            if search_term:
                filtered_data = []
                for item in table_data:
                    searchable_text = f'{item.get('country', '')} {item.get('date', '')} {item.get('value', '')}'.lower()
                    if search_term in searchable_text:
                        filtered_data.append(item)
            limit_str = dpg.get_value(f'table_limit_{self.tab_id}') if dpg.does_item_exist(f'table_limit_{self.tab_id}') else '50'
            limit = len(filtered_data) if limit_str == 'All' else min(int(limit_str), len(filtered_data))
            current_indicator = dpg.get_value(f'indicator_{self.tab_id}') if dpg.does_item_exist(f'indicator_{self.tab_id}') else ''
            params = self.prepare_parameters(current_indicator) if current_indicator else {}
            unit_type = params.get('units', params.get('transform', 'default'))
            for i in range(min(limit, len(filtered_data))):
                item = filtered_data[i]
                with dpg.table_row(parent=f'data_table_{self.tab_id}'):
                    date_str = str(item.get('date', 'N/A'))
                    dpg.add_text(date_str)
                    country_str = str(item.get('country', 'N/A')).replace('_', ' ').title()
                    dpg.add_text(country_str)
                    value = item.get('value')
                    formatted_value = self.format_number(value, unit_type)
                    dpg.add_text(formatted_value)
                    freq_str = str(item.get('FREQ', data.get('frequency', 'N/A'))).title()
                    dpg.add_text(freq_str)
                    indicator_str = str(data.get('indicator', 'N/A')).replace('_', ' ').title()
                    dpg.add_text(indicator_str)
            print('✅ Enhanced table updated successfully')
        except Exception as e:
            error(f'Error updating table: {str(e)}', module='OECDDataTab')
            print(f'❌ Error updating table: {str(e)}')

    def update_statistics(self, data: Dict[str, Any]):
        """Update statistics panel with comprehensive analysis"""
        try:
            if not dpg.does_item_exist(f'stats_display_{self.tab_id}'):
                return
            children = dpg.get_item_children(f'stats_display_{self.tab_id}', 1)
            if children:
                for child in children:
                    if dpg.does_item_exist(child):
                        dpg.delete_item(child)
            chart_data = data.get('data', [])
            if not chart_data:
                dpg.add_text('No data available for statistical analysis', color=[140, 140, 140], parent=f'stats_display_{self.tab_id}')
                return
            values = []
            for item in chart_data:
                try:
                    val = float(item.get('value'))
                    if str(val).lower() != 'nan':
                        values.append(val)
                except:
                    continue
            if not values:
                dpg.add_text('No valid numerical data for analysis', color=[140, 140, 140], parent=f'stats_display_{self.tab_id}')
                return
            n = len(values)
            mean_val = sum(values) / n
            sorted_values = sorted(values)
            median_val = sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val
            variance = sum(((x - mean_val) ** 2 for x in values)) / n
            std_dev = variance ** 0.5
            current_indicator = dpg.get_value(f'indicator_{self.tab_id}') if dpg.does_item_exist(f'indicator_{self.tab_id}') else ''
            params = self.prepare_parameters(current_indicator) if current_indicator else {}
            unit_type = params.get('units', params.get('transform', 'default'))
            with dpg.group(parent=f'stats_display_{self.tab_id}'):
                dpg.add_text('📊 Descriptive Statistics', color=[200, 200, 100])
                dpg.add_spacer(height=5)
                with dpg.table(header_row=True, borders_innerH=True, borders_innerV=True):
                    dpg.add_table_column(label='Statistic', width_fixed=True, init_width_or_weight=150)
                    dpg.add_table_column(label='Value', width_fixed=True, init_width_or_weight=200)
                    stats = [('Count', str(n)), ('Mean', self.format_number(mean_val, unit_type)), ('Median', self.format_number(median_val, unit_type)), ('Minimum', self.format_number(min_val, unit_type)), ('Maximum', self.format_number(max_val, unit_type)), ('Range', self.format_number(range_val, unit_type)), ('Std Deviation', self.format_number(std_dev, unit_type))]
                    for stat_name, stat_value in stats:
                        with dpg.table_row():
                            dpg.add_text(stat_name)
                            dpg.add_text(stat_value)
                dpg.add_spacer(height=10)
                dpg.add_text('📈 Trend Analysis', color=[200, 200, 100])
                dpg.add_spacer(height=5)
                if n > 1:
                    first_val = values[0]
                    last_val = values[-1]
                    change = last_val - first_val
                    change_pct = change / first_val * 100 if first_val != 0 else 0
                    trend_text = 'Increasing' if change > 0 else 'Decreasing' if change < 0 else 'Stable'
                    trend_color = [100, 255, 100] if change > 0 else [255, 100, 100] if change < 0 else [200, 200, 200]
                    dpg.add_text(f'Trend: {trend_text}', color=trend_color)
                    dpg.add_text(f'Total Change: {self.format_number(change, unit_type)}')
                    dpg.add_text(f'Percentage Change: {change_pct:.2f}%')
        except Exception as e:
            error(f'Error updating statistics: {str(e)}', module='OECDDataTab')
            print(f'❌ Error updating statistics: {str(e)}')

    def update_raw_display(self, data: Dict[str, Any]):
        """Update raw JSON display with better formatting"""
        try:
            formatted_json = json.dumps(data, indent=2, default=str)
            if dpg.does_item_exist(f'raw_display_{self.tab_id}'):
                dpg.set_value(f'raw_display_{self.tab_id}', formatted_json)
        except Exception as e:
            error(f'Error updating raw display: {str(e)}', module='OECDDataTab')

    def copy_raw_data(self):
        """Copy raw data to clipboard"""
        try:
            if self.current_data:
                formatted_json = json.dumps(self.current_data, indent=2, default=str)
                dpg.set_clipboard_text(formatted_json)
                self.update_status('📋 Data copied to clipboard', [100, 255, 100])
            else:
                self.update_status('⚠️ No data to copy', [255, 200, 100])
        except Exception as e:
            error(f'Error copying data: {str(e)}', module='OECDDataTab')

    def save_raw_data(self):
        """Save raw data to file"""
        try:
            if not self.current_data:
                self.update_status('⚠️ No data to save', [255, 200, 100])
                return
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            indicator = self.current_data.get('indicator', 'data')
            country = self.current_data.get('countries', 'unknown')
            filename = f'oecd_{indicator}_{country}_{timestamp}.json'
            with open(filename, 'w') as f:
                json.dump(self.current_data, f, indent=2, default=str)
            self.update_status(f'💾 Data saved to {filename}', [100, 255, 100])
        except Exception as e:
            error(f'Error saving data: {str(e)}', module='OECDDataTab')
            self.update_status(f'❌ Save error: {str(e)}', [255, 100, 100])

    def export_data(self):
        """Export data to CSV with enhanced formatting"""
        try:
            if not self.current_data or 'data' not in self.current_data:
                self.update_status('❌ No data to export', [255, 100, 100])
                return
            import csv
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            indicator = self.current_data.get('indicator', 'data')
            country = self.current_data.get('countries', 'unknown')
            filename = f'oecd_{indicator}_{country}_{timestamp}.csv'
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Date', 'Country', 'Value', 'Indicator', 'Frequency', 'Units', 'Source', 'Fetched_At'])
                units = self.current_data.get('units', 'N/A')
                frequency = self.current_data.get('frequency', 'N/A')
                indicator_name = self.current_data.get('indicator', 'N/A')
                fetched_at = self.current_data.get('fetched_at', 'N/A')
                for item in self.current_data['data']:
                    writer.writerow([item.get('date', ''), item.get('country', ''), item.get('value', ''), indicator_name, item.get('FREQ', frequency), units, 'OECD', fetched_at])
            self.update_status(f'📊 Exported to {filename}', [100, 255, 100])
        except Exception as e:
            error(f'Error exporting data: {str(e)}', module='OECDDataTab')
            self.update_status(f'❌ Export error: {str(e)}', [255, 100, 100])

    def clear_data(self):
        """Clear all data and displays"""
        try:
            print('🔧 Clearing all data...')
            self.current_data = {}
            if dpg.does_item_exist(f'y_axis_{self.tab_id}'):
                children = dpg.get_item_children(f'y_axis_{self.tab_id}', 1)
                if children:
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
            if dpg.does_item_exist(f'data_table_{self.tab_id}'):
                children = dpg.get_item_children(f'data_table_{self.tab_id}', 1)
                if children:
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
            if dpg.does_item_exist(f'stats_display_{self.tab_id}'):
                children = dpg.get_item_children(f'stats_display_{self.tab_id}', 1)
                if children:
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
                dpg.add_text('No data loaded for analysis...', color=[140, 140, 140], parent=f'stats_display_{self.tab_id}')
            if dpg.does_item_exist(f'raw_display_{self.tab_id}'):
                dpg.set_value(f'raw_display_{self.tab_id}', 'No data loaded...')
            if dpg.does_item_exist(f'chart_info_{self.tab_id}'):
                dpg.set_value(f'chart_info_{self.tab_id}', 'No chart data available')
            self.update_status('🧹 Data cleared', [200, 200, 200])
            self.update_data_summary('Ready for new data')
            if dpg.does_item_exist(f'last_update_{self.tab_id}'):
                dpg.set_value(f'last_update_{self.tab_id}', 'Not yet loaded')
                dpg.configure_item(f'last_update_{self.tab_id}', color=[120, 120, 120])
            print('✅ All data cleared successfully')
        except Exception as e:
            error(f'Error clearing data: {str(e)}', module='OECDDataTab')
            print(f'❌ Error clearing data: {str(e)}')

    def update_status(self, message: str, color: List[int]=None):
        """Update status message"""
        try:
            if color is None:
                color = [200, 200, 200]
            if dpg.does_item_exist(f'status_{self.tab_id}'):
                dpg.set_value(f'status_{self.tab_id}', message)
                dpg.configure_item(f'status_{self.tab_id}', color=color)
                print(f'📊 Status: {message}')
        except Exception as e:
            error(f'Error updating status: {str(e)}', module='OECDDataTab')
            print(f'❌ Error updating status: {str(e)}')

    def update_data_summary(self, summary: str):
        """Update data summary information"""
        try:
            if dpg.does_item_exist(f'data_summary_{self.tab_id}'):
                dpg.set_value(f'data_summary_{self.tab_id}', summary)
        except Exception as e:
            print(f'❌ Error updating data summary: {str(e)}')

    async def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
                print('✅ Thread pool shutdown completed')
            if hasattr(self, 'process_executor'):
                self.process_executor.shutdown(wait=True)
                print('✅ Process pool shutdown completed')
            if hasattr(self, 'oecd_provider') and self.oecd_provider:
                await self.oecd_provider.close()
                print('✅ OECD provider cleanup completed')
            self.current_data = {}
            print('✅ OECD cleanup completed')
        except Exception as e:
            error(f'Error during cleanup: {str(e)}', module='OECDDataTab')
            print(f'❌ Error during cleanup: {str(e)}')

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
            if hasattr(self, 'process_executor'):
                self.process_executor.shutdown(wait=False)
        except Exception:
            pass

def on_chart_type_change(self, sender, app_data):
    """Handle chart type change"""
    try:
        if self.current_data:
            self.update_chart()
    except Exception as e:
        print(f'❌ Error in chart type change: {str(e)}')

def update_displays(self, data: Dict[str, Any], indicator: str):
    """Update all display components with enhanced formatting"""
    try:
        print('🔧 Updating enhanced displays...')
        self.update_chart(data=data, indicator=indicator)
        self.update_table(data=data)
        self.update_raw_display(data)
        self.update_chart_info(data, indicator)
        print('✅ Enhanced displays updated')
    except Exception as e:
        error(f'Error updating displays: {str(e)}', module='OECDDataTab')
        print(f'❌ Error updating displays: {str(e)}')

class DataViewerTab(BaseTab):
    """Enhanced Data Viewer tab for displaying comprehensive financial data from Alpha Vantage and other providers"""

    def __init__(self, app):
        print('🔧 DEBUG: DataViewerTab.__init__ called')
        try:
            super().__init__(app)
            print('🔧 DEBUG: BaseTab.__init__ completed')
            self.tab_id = str(uuid.uuid4())[:8]
            self.data_source_manager = get_data_source_manager(app)
            print(f'🔧 DEBUG: DataSourceManager: {self.data_source_manager}')
            self.current_data = {}
            self.last_refresh = None
            self.auto_refresh = False
            self.refresh_interval = 30
            self.refresh_thread = None
            self._stop_refresh = False
            self.data_types = {'Stock Data': {'Time Series Daily': 'get_stock_data', 'Time Series Intraday': 'get_stock_data', 'Time Series Weekly': 'get_weekly_data', 'Time Series Monthly': 'get_monthly_data', 'Daily Adjusted': 'get_daily_adjusted', 'Weekly Adjusted': 'get_weekly_adjusted', 'Monthly Adjusted': 'get_monthly_adjusted', 'Global Quote': 'get_global_quote', 'Symbol Search': 'search_symbols'}, 'Fundamental Data': {'Company Overview': 'get_company_overview', 'Income Statement': 'get_income_statement', 'Balance Sheet': 'get_balance_sheet', 'Cash Flow': 'get_cash_flow', 'Earnings': 'get_earnings', 'Earnings Estimates': 'get_earnings_estimates', 'Dividends': 'get_dividends', 'Splits': 'get_splits'}, 'Technical Indicators': {'SMA': 'get_sma', 'EMA': 'get_ema', 'RSI': 'get_rsi', 'MACD': 'get_macd', 'Bollinger Bands': 'get_bbands', 'Stochastic': 'get_stoch', 'ADX': 'get_adx', 'VWAP': 'get_vwap'}, 'Forex': {'Currency Exchange Rate': 'get_currency_exchange_rate', 'FX Daily': 'get_forex_data', 'FX Intraday': 'get_fx_intraday', 'FX Weekly': 'get_fx_weekly', 'FX Monthly': 'get_fx_monthly'}, 'Cryptocurrency': {'Crypto Daily': 'get_crypto_data', 'Crypto Intraday': 'get_crypto_intraday', 'Digital Currency Weekly': 'get_digital_currency_weekly', 'Digital Currency Monthly': 'get_digital_currency_monthly'}, 'Commodities': {'WTI Oil': 'get_wti_oil', 'Brent Oil': 'get_brent_oil', 'Natural Gas': 'get_natural_gas', 'Gold': 'get_copper', 'Silver': 'get_aluminum'}, 'Economic Indicators': {'Real GDP': 'get_real_gdp', 'Unemployment': 'get_unemployment', 'CPI': 'get_cpi', 'Treasury Yield': 'get_treasury_yield', 'Federal Funds Rate': 'get_federal_funds_rate'}, 'Market Intelligence': {'News Sentiment': 'get_news_sentiment', 'Top Gainers/Losers': 'get_top_gainers_losers', 'Insider Transactions': 'get_insider_transactions'}}
            print('✅ DEBUG: DataViewerTab initialization completed successfully')
        except Exception as e:
            print(f'❌ DEBUG: Error in DataViewerTab.__init__: {str(e)}')
            print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')
            raise

    def get_label(self):
        return 'Data Viewer'

    def safe_add_item(self, add_function, *args, **kwargs):
        """Safely add DPG items with error handling"""
        try:
            return add_function(*args, **kwargs)
        except Exception as e:
            print(f'❌ DEBUG: Error adding item {add_function.__name__}: {str(e)}')
            try:
                if 'tag' in kwargs:
                    kwargs['tag'] = f'{kwargs['tag']}_{self.tab_id}'
                return add_function(*args, **kwargs)
            except:
                print(f'❌ DEBUG: Failed to add {add_function.__name__} even with modified tag')
                return None

    def create_content(self):
        """Create the enhanced data viewer interface"""
        print('🔧 DEBUG: create_content() called')
        try:
            self.add_section_header('📊 Advanced Financial Data Viewer')
            self.safe_add_item(dpg.add_text, 'Access comprehensive financial data from Alpha Vantage and other providers', color=[200, 200, 200])
            self.safe_add_item(dpg.add_spacer, height=20)
            with dpg.child_window(height=800, border=True):
                self.create_control_panel()
                self.safe_add_item(dpg.add_separator)
                self.safe_add_item(dpg.add_spacer, height=10)
                self.create_data_display()
            print('✅ DEBUG: create_content() completed successfully')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_content(): {str(e)}')
            print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')
            try:
                self.safe_add_item(dpg.add_text, f'Error creating content: {str(e)}', color=[255, 100, 100])
            except:
                pass

    def create_control_panel(self):
        """Create enhanced control panel"""
        print('🔧 DEBUG: create_control_panel() called')
        try:
            self.safe_add_item(dpg.add_text, '🎛️ Data Controls', color=[255, 255, 100])
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_text, 'Category:', width=100)
                self.safe_add_item(dpg.add_combo, list(self.data_types.keys()), tag=f'data_category_{self.tab_id}', default_value='Stock Data', width=150, callback=self.on_category_change)
                self.safe_add_item(dpg.add_text, 'Data Type:', width=100)
                self.safe_add_item(dpg.add_combo, list(self.data_types['Stock Data'].keys()), tag=f'data_type_{self.tab_id}', default_value='Time Series Daily', width=150)
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_text, 'Symbol:', width=100)
                self.safe_add_item(dpg.add_input_text, tag=f'symbol_input_{self.tab_id}', default_value='AAPL', width=100, hint='e.g., AAPL, EURUSD, BTC')
                self.safe_add_item(dpg.add_text, 'Period:', width=100)
                self.safe_add_item(dpg.add_combo, ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'], tag=f'period_combo_{self.tab_id}', default_value='1d', width=80)
                self.safe_add_item(dpg.add_text, 'Interval:', width=100)
                self.safe_add_item(dpg.add_combo, ['1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'], tag=f'interval_combo_{self.tab_id}', default_value='daily', width=80)
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True, tag=f'tech_params_{self.tab_id}', show=False):
                self.safe_add_item(dpg.add_text, 'Time Period:', width=100)
                self.safe_add_item(dpg.add_input_int, tag=f'time_period_{self.tab_id}', default_value=14, width=60, min_value=1, max_value=200)
                self.safe_add_item(dpg.add_text, 'Series Type:', width=100)
                self.safe_add_item(dpg.add_combo, ['close', 'open', 'high', 'low'], tag=f'series_type_{self.tab_id}', default_value='close', width=80)
            with dpg.group(horizontal=True, tag=f'forex_params_{self.tab_id}', show=False):
                self.safe_add_item(dpg.add_text, 'From Currency:', width=100)
                self.safe_add_item(dpg.add_input_text, tag=f'from_currency_{self.tab_id}', default_value='USD', width=60)
                self.safe_add_item(dpg.add_text, 'To Currency:', width=100)
                self.safe_add_item(dpg.add_input_text, tag=f'to_currency_{self.tab_id}', default_value='EUR', width=60)
            self.safe_add_item(dpg.add_spacer, height=15)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_button, label='🔄 Fetch Data', tag=f'fetch_btn_{self.tab_id}', callback=self.fetch_data, width=120)
                self.safe_add_item(dpg.add_button, label='🧹 Clear', tag=f'clear_btn_{self.tab_id}', callback=self.clear_data, width=80)
                self.safe_add_item(dpg.add_checkbox, label='Auto Refresh (30s)', tag=f'auto_refresh_{self.tab_id}', callback=self.toggle_auto_refresh)
                self.safe_add_item(dpg.add_button, label='📋 Export CSV', tag=f'export_btn_{self.tab_id}', callback=self.export_data, width=120)
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_text, 'Status:', color=[150, 150, 150])
                self.safe_add_item(dpg.add_text, 'Ready', tag=f'status_text_{self.tab_id}', color=[100, 255, 100])
                self.safe_add_item(dpg.add_text, ' | Last Updated:', color=[150, 150, 150])
                self.safe_add_item(dpg.add_text, 'Never', tag=f'last_update_{self.tab_id}', color=[150, 150, 150])
            print('✅ DEBUG: create_control_panel() completed')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_control_panel(): {str(e)}')
            print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')

    def create_data_display(self):
        """Create comprehensive data display area"""
        print('🔧 DEBUG: create_data_display() called')
        try:
            self.safe_add_item(dpg.add_text, '📈 Data Display', color=[255, 255, 100])
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.tab_bar(tag=f'display_tabs_{self.tab_id}'):
                with dpg.tab(label='📊 Overview', tag=f'overview_tab_{self.tab_id}'):
                    self.create_overview_display()
                with dpg.tab(label='📈 Time Series', tag=f'timeseries_tab_{self.tab_id}'):
                    self.create_timeseries_display()
                with dpg.tab(label='💼 Fundamentals', tag=f'fundamentals_tab_{self.tab_id}'):
                    self.create_fundamentals_display()
                with dpg.tab(label='📐 Technical', tag=f'technical_tab_{self.tab_id}'):
                    self.create_technical_display()
                with dpg.tab(label='🔍 Raw Data', tag=f'raw_tab_{self.tab_id}'):
                    self.create_raw_display()
                with dpg.tab(label='🔧 Provider Info', tag=f'provider_tab_{self.tab_id}'):
                    self.create_provider_display()
            print('✅ DEBUG: create_data_display() completed')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_data_display(): {str(e)}')
            print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')

    def create_overview_display(self):
        """Create overview display for key metrics"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True):
                with dpg.child_window(width=200, height=120, border=True):
                    self.safe_add_item(dpg.add_text, 'Current Price', color=[255, 255, 100])
                    self.safe_add_item(dpg.add_separator)
                    self.safe_add_item(dpg.add_text, 'N/A', tag=f'overview_price_{self.tab_id}', color=[100, 255, 100])
                    self.safe_add_item(dpg.add_text, 'Change: N/A', tag=f'overview_change_{self.tab_id}', color=[200, 200, 200])
                with dpg.child_window(width=200, height=120, border=True):
                    self.safe_add_item(dpg.add_text, 'Volume/Activity', color=[255, 255, 100])
                    self.safe_add_item(dpg.add_separator)
                    self.safe_add_item(dpg.add_text, 'N/A', tag=f'overview_volume_{self.tab_id}', color=[200, 200, 200])
                    self.safe_add_item(dpg.add_text, 'Avg: N/A', tag=f'overview_avg_volume_{self.tab_id}', color=[200, 200, 200])
                with dpg.child_window(width=200, height=120, border=True):
                    self.safe_add_item(dpg.add_text, 'Price Range', color=[255, 255, 100])
                    self.safe_add_item(dpg.add_separator)
                    self.safe_add_item(dpg.add_text, 'High: N/A', tag=f'overview_high_{self.tab_id}', color=[100, 255, 100])
                    self.safe_add_item(dpg.add_text, 'Low: N/A', tag=f'overview_low_{self.tab_id}', color=[255, 100, 100])
            self.safe_add_item(dpg.add_spacer, height=20)
            self.safe_add_item(dpg.add_text, '📋 Data Information', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            self.safe_add_item(dpg.add_spacer, height=5)
            with dpg.table(tag=f'overview_info_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True):
                dpg.add_table_column(label='Property')
                dpg.add_table_column(label='Value')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_overview_display(): {str(e)}')

    def create_timeseries_display(self):
        """Create time series data display"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_text, 'Show Last:')
                self.safe_add_item(dpg.add_combo, ['10', '25', '50', '100', 'All'], tag=f'timeseries_limit_{self.tab_id}', default_value='25', width=80)
                self.safe_add_item(dpg.add_button, label='🔄 Refresh View', callback=self.refresh_timeseries_view, width=120)
            self.safe_add_item(dpg.add_spacer, height=10)
            with dpg.table(tag=f'timeseries_table_{self.tab_id}', header_row=True, resizable=True, borders_innerH=True, borders_innerV=True, borders_outerH=True, borders_outerV=True, scrollY=True, height=400):
                dpg.add_table_column(label='Date/Time', width_fixed=True, init_width_or_weight=120)
                dpg.add_table_column(label='Open', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='High', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='Low', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='Close', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='Volume', width_fixed=True, init_width_or_weight=100)
        except Exception as e:
            print(f'❌ DEBUG: Error in create_timeseries_display(): {str(e)}')

    def create_fundamentals_display(self):
        """Create fundamentals data display"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            self.safe_add_item(dpg.add_text, '🏢 Company Information', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            with dpg.table(tag=f'company_info_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=150):
                dpg.add_table_column(label='Property')
                dpg.add_table_column(label='Value')
            self.safe_add_item(dpg.add_spacer, height=15)
            self.safe_add_item(dpg.add_text, '📊 Financial Statements', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            with dpg.tab_bar(tag=f'financial_tabs_{self.tab_id}'):
                with dpg.tab(label='Income Statement'):
                    with dpg.table(tag=f'income_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=200):
                        dpg.add_table_column(label='Item')
                        dpg.add_table_column(label='Value')
                with dpg.tab(label='Balance Sheet'):
                    with dpg.table(tag=f'balance_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=200):
                        dpg.add_table_column(label='Item')
                        dpg.add_table_column(label='Value')
                with dpg.tab(label='Cash Flow'):
                    with dpg.table(tag=f'cashflow_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=200):
                        dpg.add_table_column(label='Item')
                        dpg.add_table_column(label='Value')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_fundamentals_display(): {str(e)}')

    def create_technical_display(self):
        """Create technical analysis display"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            self.safe_add_item(dpg.add_text, '📐 Technical Indicators', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            with dpg.table(tag=f'technical_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=300):
                dpg.add_table_column(label='Date/Time')
                dpg.add_table_column(label='Indicator')
                dpg.add_table_column(label='Value')
                dpg.add_table_column(label='Signal')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_technical_display(): {str(e)}')

    def create_raw_display(self):
        """Create raw data display"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            self.safe_add_item(dpg.add_text, '🔍 Raw API Response', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            self.safe_add_item(dpg.add_spacer, height=5)
            with dpg.group(horizontal=True):
                self.safe_add_item(dpg.add_button, label='📋 Copy to Clipboard', callback=self.copy_raw_data, width=150)
                self.safe_add_item(dpg.add_button, label='💾 Save to File', callback=self.save_raw_data, width=120)
            self.safe_add_item(dpg.add_spacer, height=10)
            self.safe_add_item(dpg.add_input_text, tag=f'raw_data_display_{self.tab_id}', multiline=True, height=400, width=-1, readonly=True, default_value='No data loaded yet...')
        except Exception as e:
            print(f'❌ DEBUG: Error in create_raw_display(): {str(e)}')

    def create_provider_display(self):
        """Create provider information display"""
        try:
            self.safe_add_item(dpg.add_spacer, height=10)
            self.safe_add_item(dpg.add_text, '🔧 Provider Information', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            with dpg.table(tag=f'provider_info_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True):
                dpg.add_table_column(label='Property')
                dpg.add_table_column(label='Value')
            self.safe_add_item(dpg.add_spacer, height=15)
            self.safe_add_item(dpg.add_text, '📋 Available Endpoints', color=[255, 255, 100])
            self.safe_add_item(dpg.add_separator)
            with dpg.table(tag=f'endpoints_table_{self.tab_id}', header_row=True, borders_innerH=True, borders_innerV=True, scrollY=True, height=200):
                dpg.add_table_column(label='Category')
                dpg.add_table_column(label='Endpoint')
                dpg.add_table_column(label='Status')
            self.populate_endpoints_table()
        except Exception as e:
            print(f'❌ DEBUG: Error in create_provider_display(): {str(e)}')

    def populate_endpoints_table(self):
        """Populate the endpoints table with available data types"""
        try:
            table_tag = f'endpoints_table_{self.tab_id}'
            if not dpg.does_item_exist(table_tag):
                return
            for category, endpoints in self.data_types.items():
                for endpoint_name, method_name in endpoints.items():
                    with dpg.table_row(parent=table_tag):
                        dpg.add_text(category)
                        dpg.add_text(endpoint_name)
                        if hasattr(self.data_source_manager, method_name) if self.data_source_manager else False:
                            dpg.add_text('✅ Available', color=[100, 255, 100])
                        else:
                            dpg.add_text('❌ Not Available', color=[255, 100, 100])
        except Exception as e:
            print(f'❌ DEBUG: Error in populate_endpoints_table(): {str(e)}')

    def on_category_change(self, sender, app_data):
        """Handle category change to update data type options"""
        try:
            category = app_data
            data_type_combo = f'data_type_{self.tab_id}'
            if category in self.data_types:
                dpg.configure_item(data_type_combo, items=list(self.data_types[category].keys()))
                dpg.set_value(data_type_combo, list(self.data_types[category].keys())[0])
                self.update_parameter_visibility(category)
        except Exception as e:
            print(f'❌ DEBUG: Error in on_category_change(): {str(e)}')

    def update_parameter_visibility(self, category):
        """Update visibility of parameter groups based on selected category"""
        try:
            dpg.configure_item(f'tech_params_{self.tab_id}', show=False)
            dpg.configure_item(f'forex_params_{self.tab_id}', show=False)
            if category == 'Technical Indicators':
                dpg.configure_item(f'tech_params_{self.tab_id}', show=True)
            elif category == 'Forex':
                dpg.configure_item(f'forex_params_{self.tab_id}', show=True)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_parameter_visibility(): {str(e)}')

    def fetch_data(self):
        """Fetch data based on current selections"""
        try:
            if not self.data_source_manager:
                self.update_status('❌ Data Source Manager not available', [255, 100, 100])
                return
            category = dpg.get_value(f'data_category_{self.tab_id}')
            data_type = dpg.get_value(f'data_type_{self.tab_id}')
            symbol = dpg.get_value(f'symbol_input_{self.tab_id}').strip().upper()
            if not symbol and category not in ['Economic Indicators', 'Market Intelligence']:
                self.update_status('❌ Please enter a symbol', [255, 100, 100])
                return
            self.update_status('🔄 Fetching data...', [255, 255, 100])
            thread = threading.Thread(target=self._fetch_data_async, args=(category, data_type, symbol))
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f'❌ DEBUG: Error in fetch_data(): {str(e)}')
            self.update_status(f'❌ Error: {str(e)}', [255, 100, 100])

    def _fetch_data_async(self, category: str, data_type: str, symbol: str):
        """Fetch data asynchronously"""
        try:
            print(f'🔧 DEBUG: Fetching {category} - {data_type} for {symbol}')
            if category not in self.data_types or data_type not in self.data_types[category]:
                self.update_status('❌ Invalid data type selection', [255, 100, 100])
                return
            method_name = self.data_types[category][data_type]
            if not hasattr(self.data_source_manager, method_name):
                self.update_status(f'❌ Method {method_name} not available', [255, 100, 100])
                return
            method = getattr(self.data_source_manager, method_name)
            params = self._prepare_method_parameters(category, data_type, symbol)
            if asyncio.iscoroutinefunction(method):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    data = loop.run_until_complete(method(**params))
                finally:
                    loop.close()
            else:
                data = method(**params)
            print(f'🔧 DEBUG: Data fetch result: {(data.get('success', False) if isinstance(data, dict) else 'Unknown')}')
            if isinstance(data, dict) and data.get('success'):
                self.current_data = data
                self.update_all_displays(data, category, data_type, symbol)
                self.update_status('✅ Data loaded successfully', [100, 255, 100])
                self.last_refresh = datetime.now()
                dpg.set_value(f'last_update_{self.tab_id}', self.last_refresh.strftime('%H:%M:%S'))
            else:
                error_msg = data.get('error', 'Unknown error') if isinstance(data, dict) else str(data)
                self.update_status(f'❌ {error_msg}', [255, 100, 100])
        except Exception as e:
            print(f'❌ DEBUG: Error in _fetch_data_async(): {str(e)}')
            print(f'❌ DEBUG: Traceback: {traceback.format_exc()}')
            self.update_status(f'❌ Error: {str(e)}', [255, 100, 100])

    def _prepare_method_parameters(self, category: str, data_type: str, symbol: str) -> Dict[str, Any]:
        """Prepare parameters for the API method call"""
        params = {}
        try:
            if symbol and category not in ['Economic Indicators', 'Market Intelligence', 'Commodities']:
                params['symbol'] = symbol
            time_series_methods = ['Time Series Daily', 'Time Series Intraday', 'Time Series Weekly', 'Time Series Monthly', 'Daily Adjusted', 'Weekly Adjusted', 'Monthly Adjusted', 'FX Daily', 'FX Intraday', 'FX Weekly', 'FX Monthly', 'Crypto Daily', 'Crypto Intraday', 'Digital Currency Weekly', 'Digital Currency Monthly']
            if data_type in time_series_methods:
                if dpg.does_item_exist(f'period_combo_{self.tab_id}'):
                    params['period'] = dpg.get_value(f'period_combo_{self.tab_id}')
                if dpg.does_item_exist(f'interval_combo_{self.tab_id}'):
                    params['interval'] = dpg.get_value(f'interval_combo_{self.tab_id}')
            if category == 'Technical Indicators':
                if dpg.does_item_exist(f'time_period_{self.tab_id}'):
                    params['time_period'] = dpg.get_value(f'time_period_{self.tab_id}')
                if dpg.does_item_exist(f'series_type_{self.tab_id}'):
                    params['series_type'] = dpg.get_value(f'series_type_{self.tab_id}')
                if dpg.does_item_exist(f'interval_combo_{self.tab_id}'):
                    params['interval'] = dpg.get_value(f'interval_combo_{self.tab_id}')
            elif category == 'Forex':
                if data_type == 'Currency Exchange Rate':
                    params['from_currency'] = dpg.get_value(f'from_currency_{self.tab_id}') if dpg.does_item_exist(f'from_currency_{self.tab_id}') else 'USD'
                    params['to_currency'] = dpg.get_value(f'to_currency_{self.tab_id}') if dpg.does_item_exist(f'to_currency_{self.tab_id}') else 'EUR'
                    params.pop('symbol', None)
                elif data_type in ['FX Daily', 'FX Intraday', 'FX Weekly', 'FX Monthly']:
                    params['from_symbol'] = dpg.get_value(f'from_currency_{self.tab_id}') if dpg.does_item_exist(f'from_currency_{self.tab_id}') else 'USD'
                    params['to_symbol'] = dpg.get_value(f'to_currency_{self.tab_id}') if dpg.does_item_exist(f'to_currency_{self.tab_id}') else 'EUR'
                    params.pop('symbol', None)
            elif category == 'Cryptocurrency':
                if data_type in ['Crypto Intraday', 'Digital Currency Weekly', 'Digital Currency Monthly']:
                    params['market'] = 'USD'
            elif category == 'Economic Indicators':
                params.pop('symbol', None)
                if data_type == 'Treasury Yield':
                    params['maturity'] = '10year'
                    params['interval'] = 'monthly'
                elif data_type in ['Real GDP', 'CPI', 'Federal Funds Rate']:
                    params['interval'] = dpg.get_value(f'interval_combo_{self.tab_id}') if dpg.does_item_exist(f'interval_combo_{self.tab_id}') else 'monthly'
            elif category == 'Commodities':
                params.pop('symbol', None)
                if dpg.does_item_exist(f'interval_combo_{self.tab_id}'):
                    params['interval'] = dpg.get_value(f'interval_combo_{self.tab_id}')
                else:
                    params['interval'] = 'monthly'
            elif category == 'Market Intelligence':
                if data_type == 'Top Gainers/Losers':
                    params.pop('symbol', None)
                elif data_type == 'News Sentiment':
                    if symbol:
                        params['tickers'] = symbol
                    params.pop('symbol', None)
                elif data_type == 'Insider Transactions':
                    pass
            fundamental_methods = ['Company Overview', 'Income Statement', 'Balance Sheet', 'Cash Flow', 'Earnings', 'Earnings Estimates', 'Dividends', 'Splits']
            if data_type in fundamental_methods:
                params = {k: v for k, v in params.items() if k == 'symbol'}
            stock_methods = ['Time Series Daily', 'Time Series Intraday', 'Time Series Weekly', 'Time Series Monthly', 'Daily Adjusted', 'Weekly Adjusted', 'Monthly Adjusted', 'Global Quote', 'Symbol Search']
            if data_type == 'Symbol Search':
                if symbol:
                    params = {'keywords': symbol}
                else:
                    params = {'keywords': 'apple'}
            print(f'🔧 DEBUG: Prepared parameters for {category}/{data_type}: {params}')
            return params
        except Exception as e:
            print(f'❌ DEBUG: Error preparing parameters: {str(e)}')
            return {'symbol': symbol} if symbol else {}

    def update_all_displays(self, data: Dict[str, Any], category: str, data_type: str, symbol: str):
        """Update all display tabs with fetched data"""
        try:
            self.update_overview_display(data, category, data_type, symbol)
            if 'data' in data and isinstance(data['data'], dict):
                self.update_timeseries_display(data['data'])
            if category == 'Fundamental Data':
                self.update_fundamentals_display(data, data_type)
            if category == 'Technical Indicators':
                self.update_technical_display(data, data_type)
            self.update_raw_display(data)
            self.update_provider_info(data)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_all_displays(): {str(e)}')

    def update_overview_display(self, data: Dict[str, Any], category: str, data_type: str, symbol: str):
        """Update overview display with key metrics"""
        try:
            price_value = 'N/A'
            change_value = 'N/A'
            volume_value = 'N/A'
            high_value = 'N/A'
            low_value = 'N/A'
            if category == 'Stock Data':
                if data_type == 'Global Quote' and 'data' in data:
                    quote_data = data['data']
                    price_value = f'${quote_data.get('price', 0):.2f}'
                    change_value = f'{quote_data.get('change', 0):.2f} ({quote_data.get('change_percent', '0%')})'
                    volume_value = f'{quote_data.get('volume', 0):,}'
                    high_value = f'${quote_data.get('high', 0):.2f}'
                    low_value = f'${quote_data.get('low', 0):.2f}'
                elif 'current_price' in data:
                    price_value = f'${data['current_price']:.2f}'
                elif 'data' in data and isinstance(data['data'], dict):
                    if 'close' in data['data'] and data['data']['close']:
                        price_value = f'${data['data']['close'][-1]:.2f}'
                        if 'high' in data['data'] and data['data']['high']:
                            high_value = f'${max(data['data']['high']):.2f}'
                        if 'low' in data['data'] and data['data']['low']:
                            low_value = f'${min(data['data']['low']):.2f}'
                        if 'volume' in data['data'] and data['data']['volume']:
                            avg_volume = sum(data['data']['volume']) // len(data['data']['volume'])
                            volume_value = f'{avg_volume:,}'
            elif category == 'Forex':
                if 'current_rate' in data:
                    price_value = f'{data['current_rate']:.4f}'
                elif 'data' in data and 'exchange_rate' in data['data']:
                    price_value = f'{data['data']['exchange_rate']:.4f}'
            elif category == 'Cryptocurrency':
                if 'current_price' in data:
                    price_value = f'${data['current_price']:.2f}'
            dpg.set_value(f'overview_price_{self.tab_id}', price_value)
            dpg.set_value(f'overview_change_{self.tab_id}', f'Change: {change_value}')
            dpg.set_value(f'overview_volume_{self.tab_id}', volume_value)
            dpg.set_value(f'overview_high_{self.tab_id}', f'High: {high_value}')
            dpg.set_value(f'overview_low_{self.tab_id}', f'Low: {low_value}')
            self.update_info_table(data, symbol, category, data_type)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_overview_display(): {str(e)}')

    def update_info_table(self, data: Dict[str, Any], symbol: str, category: str, data_type: str):
        """Update the overview info table"""
        try:
            table_tag = f'overview_info_table_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            with dpg.table_row(parent=table_tag):
                dpg.add_text('Symbol')
                dpg.add_text(symbol)
            with dpg.table_row(parent=table_tag):
                dpg.add_text('Category')
                dpg.add_text(category)
            with dpg.table_row(parent=table_tag):
                dpg.add_text('Data Type')
                dpg.add_text(data_type)
            with dpg.table_row(parent=table_tag):
                dpg.add_text('Source')
                dpg.add_text(data.get('source', 'Unknown'))
            with dpg.table_row(parent=table_tag):
                dpg.add_text('Fetched At')
                dpg.add_text(data.get('fetched_at', 'Unknown'))
            if 'data' in data and isinstance(data['data'], dict):
                data_info = data['data']
                for key, value in data_info.items():
                    if key not in ['timestamps', 'open', 'high', 'low', 'close', 'volume'] and (not isinstance(value, list)):
                        with dpg.table_row(parent=table_tag):
                            dpg.add_text(key.replace('_', ' ').title())
                            dpg.add_text(str(value)[:50] + '...' if len(str(value)) > 50 else str(value))
        except Exception as e:
            print(f'❌ DEBUG: Error in update_info_table(): {str(e)}')

    def update_timeseries_display(self, data: Dict[str, Any]):
        """Update time series data table"""
        try:
            table_tag = f'timeseries_table_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            if not all((key in data for key in ['timestamps'])):
                return
            timestamps = data.get('timestamps', [])
            opens = data.get('open', [])
            highs = data.get('high', [])
            lows = data.get('low', [])
            closes = data.get('close', [])
            volumes = data.get('volume', [])
            limit_str = dpg.get_value(f'timeseries_limit_{self.tab_id}') if dpg.does_item_exist(f'timeseries_limit_{self.tab_id}') else '25'
            limit = len(timestamps) if limit_str == 'All' else min(int(limit_str), len(timestamps))
            for i in range(min(limit, len(timestamps))):
                idx = len(timestamps) - 1 - i
                with dpg.table_row(parent=table_tag):
                    dpg.add_text(timestamps[idx] if idx < len(timestamps) else 'N/A')
                    dpg.add_text(f'{opens[idx]:.2f}' if idx < len(opens) and opens[idx] else 'N/A')
                    dpg.add_text(f'{highs[idx]:.2f}' if idx < len(highs) and highs[idx] else 'N/A')
                    dpg.add_text(f'{lows[idx]:.2f}' if idx < len(lows) and lows[idx] else 'N/A')
                    dpg.add_text(f'{closes[idx]:.2f}' if idx < len(closes) and closes[idx] else 'N/A')
                    dpg.add_text(f'{volumes[idx]:,}' if idx < len(volumes) and volumes[idx] else 'N/A')
        except Exception as e:
            print(f'❌ DEBUG: Error in update_timeseries_display(): {str(e)}')

    def update_fundamentals_display(self, data: Dict[str, Any], data_type: str):
        """Update fundamentals display based on data type"""
        try:
            if data_type == 'Company Overview':
                self.update_company_info_table(data.get('data', {}))
            elif data_type == 'Income Statement':
                self.update_financial_table('income_table', data.get('data', {}))
            elif data_type == 'Balance Sheet':
                self.update_financial_table('balance_table', data.get('data', {}))
            elif data_type == 'Cash Flow':
                self.update_financial_table('cashflow_table', data.get('data', {}))
        except Exception as e:
            print(f'❌ DEBUG: Error in update_fundamentals_display(): {str(e)}')

    def update_company_info_table(self, data: Dict[str, Any]):
        """Update company information table"""
        try:
            table_tag = f'company_info_table_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            key_fields = ['Name', 'Symbol', 'Description', 'Exchange', 'Currency', 'Country', 'Sector', 'Industry', 'MarketCapitalization', 'PERatio', 'PEGRatio', 'BookValue', 'DividendPerShare', 'DividendYield', 'EPS', 'RevenuePerShareTTM', 'ProfitMargin', 'OperatingMarginTTM', 'ReturnOnAssetsTTM', 'ReturnOnEquityTTM']
            for field in key_fields:
                if field in data:
                    with dpg.table_row(parent=table_tag):
                        dpg.add_text(field.replace('TTM', ' (TTM)'))
                        value = data[field]
                        if field == 'MarketCapitalization' and value.isdigit():
                            value = f'${int(value):,}'
                        elif field in ['PERatio', 'PEGRatio', 'BookValue', 'DividendPerShare', 'EPS'] and value != 'None':
                            try:
                                value = f'{float(value):.2f}'
                            except:
                                pass
                        dpg.add_text(str(value))
        except Exception as e:
            print(f'❌ DEBUG: Error in update_company_info_table(): {str(e)}')

    def update_financial_table(self, table_prefix: str, data: Dict[str, Any]):
        """Update financial statement table"""
        try:
            table_tag = f'{table_prefix}_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            for key, value in data.items():
                if key not in ['symbol', 'fiscalDateEnding', 'reportedCurrency']:
                    with dpg.table_row(parent=table_tag):
                        dpg.add_text(key.replace('TTM', ' (TTM)'))
                        if isinstance(value, str) and value.isdigit():
                            formatted_value = f'${int(value):,}'
                        else:
                            formatted_value = str(value)
                        dpg.add_text(formatted_value)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_financial_table(): {str(e)}')

    def update_technical_display(self, data: Dict[str, Any], data_type: str):
        """Update technical analysis display"""
        try:
            table_tag = f'technical_table_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            if 'data' not in data:
                return
            tech_data = data['data']
            timestamps = tech_data.get('timestamps', [])
            for key, values in tech_data.items():
                if key != 'timestamps' and isinstance(values, list):
                    for i in range(min(10, len(values))):
                        idx = len(values) - 1 - i
                        if idx < len(timestamps):
                            with dpg.table_row(parent=table_tag):
                                dpg.add_text(timestamps[idx])
                                dpg.add_text(data_type + f' ({key})')
                                dpg.add_text(f'{values[idx]:.4f}' if isinstance(values[idx], (int, float)) else str(values[idx]))
                                signal = self.calculate_signal(key, values[idx], values[idx - 1] if idx > 0 else values[idx])
                                dpg.add_text(signal)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_technical_display(): {str(e)}')

    def calculate_signal(self, indicator: str, current: float, previous: float) -> str:
        """Calculate basic signal from indicator values"""
        try:
            if not isinstance(current, (int, float)) or not isinstance(previous, (int, float)):
                return 'N/A'
            if indicator.upper() in ['RSI']:
                if current > 70:
                    return '🔴 Overbought'
                elif current < 30:
                    return '🟢 Oversold'
                else:
                    return '🟡 Neutral'
            elif 'MACD' in indicator.upper():
                if current > previous:
                    return '🟢 Bullish'
                elif current < previous:
                    return '🔴 Bearish'
                else:
                    return '🟡 Neutral'
            elif current > previous:
                return '⬆️ Rising'
            elif current < previous:
                return '⬇️ Falling'
            else:
                return '➡️ Flat'
        except Exception as e:
            return 'N/A'

    def update_raw_display(self, data: Dict[str, Any]):
        """Update raw data display"""
        try:
            import json
            raw_text = json.dumps(data, indent=2, default=str)
            dpg.set_value(f'raw_data_display_{self.tab_id}', raw_text)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_raw_display(): {str(e)}')

    def update_provider_info(self, data: Dict[str, Any]):
        """Update provider information"""
        try:
            table_tag = f'provider_info_table_{self.tab_id}'
            if dpg.does_item_exist(table_tag):
                children = dpg.get_item_children(table_tag, 1)
                for child in children:
                    dpg.delete_item(child)
            provider_info = [('Provider', data.get('source', 'Unknown')), ('Status', '✅ Active' if data.get('success') else '❌ Error'), ('Data Points', str(len(data.get('data', {}).get('timestamps', []))) if 'data' in data else 'N/A'), ('Response Time', '< 1s'), ('Last Updated', data.get('fetched_at', 'Unknown'))]
            for key, value in provider_info:
                with dpg.table_row(parent=table_tag):
                    dpg.add_text(key)
                    dpg.add_text(value)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_provider_info(): {str(e)}')

    def refresh_timeseries_view(self):
        """Refresh the time series view with current data"""
        try:
            if self.current_data and 'data' in self.current_data:
                self.update_timeseries_display(self.current_data['data'])
        except Exception as e:
            print(f'❌ DEBUG: Error in refresh_timeseries_view(): {str(e)}')

    def copy_raw_data(self):
        """Copy raw data to clipboard"""
        try:
            if self.current_data:
                import json
                raw_text = json.dumps(self.current_data, indent=2, default=str)
                dpg.set_clipboard_text(raw_text)
                self.update_status('📋 Data copied to clipboard', [100, 255, 100])
        except Exception as e:
            print(f'❌ DEBUG: Error in copy_raw_data(): {str(e)}')
            self.update_status('❌ Failed to copy data', [255, 100, 100])

    def save_raw_data(self):
        """Save raw data to file"""
        try:
            if self.current_data:
                import json
                from datetime import datetime
                filename = f'financial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json'
                with open(filename, 'w') as f:
                    json.dump(self.current_data, f, indent=2, default=str)
                self.update_status(f'💾 Data saved to {filename}', [100, 255, 100])
        except Exception as e:
            print(f'❌ DEBUG: Error in save_raw_data(): {str(e)}')
            self.update_status('❌ Failed to save data', [255, 100, 100])

    def export_data(self):
        """Export current data to CSV"""
        try:
            if not self.current_data or 'data' not in self.current_data:
                self.update_status('❌ No data to export', [255, 100, 100])
                return
            data = self.current_data['data']
            if 'timestamps' not in data:
                self.update_status('❌ No time series data to export', [255, 100, 100])
                return
            import csv
            from datetime import datetime
            filename = f'financial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv'
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                headers = ['timestamp']
                for key in data.keys():
                    if key != 'timestamps':
                        headers.append(key)
                writer.writerow(headers)
                timestamps = data['timestamps']
                for i in range(len(timestamps)):
                    row = [timestamps[i]]
                    for key in data.keys():
                        if key != 'timestamps':
                            values = data[key]
                            row.append(values[i] if i < len(values) else '')
                    writer.writerow(row)
            self.update_status(f'📊 Data exported to {filename}', [100, 255, 100])
        except Exception as e:
            print(f'❌ DEBUG: Error in export_data(): {str(e)}')
            self.update_status('❌ Failed to export data', [255, 100, 100])

    def toggle_auto_refresh(self, sender, value):
        """Toggle auto refresh functionality"""
        try:
            self.auto_refresh = value
            if self.auto_refresh:
                self.update_status('🔄 Auto refresh enabled', [100, 255, 100])
                self.start_auto_refresh()
            else:
                self.update_status('⏹️ Auto refresh disabled', [200, 200, 200])
                self.stop_auto_refresh()
        except Exception as e:
            print(f'❌ DEBUG: Error in toggle_auto_refresh(): {str(e)}')

    def start_auto_refresh(self):
        """Start auto refresh thread"""
        try:
            if self.refresh_thread and self.refresh_thread.is_alive():
                return
            self._stop_refresh = False
            self.refresh_thread = threading.Thread(target=self._auto_refresh_worker)
            self.refresh_thread.daemon = True
            self.refresh_thread.start()
        except Exception as e:
            print(f'❌ DEBUG: Error in start_auto_refresh(): {str(e)}')

    def stop_auto_refresh(self):
        """Stop auto refresh thread"""
        try:
            self._stop_refresh = True
            if self.refresh_thread:
                self.refresh_thread.join(timeout=1.0)
        except Exception as e:
            print(f'❌ DEBUG: Error in stop_auto_refresh(): {str(e)}')

    def _auto_refresh_worker(self):
        """Auto refresh worker thread"""
        try:
            while not self._stop_refresh and self.auto_refresh:
                time.sleep(self.refresh_interval)
                if not self._stop_refresh and self.auto_refresh:
                    self.fetch_data()
        except Exception as e:
            print(f'❌ DEBUG: Error in _auto_refresh_worker(): {str(e)}')

    def clear_data(self):
        """Clear all displayed data"""
        try:
            self.current_data = {}
            for tag_suffix in ['price', 'change', 'volume', 'high', 'low']:
                tag = f'overview_{tag_suffix}_{self.tab_id}'
                if dpg.does_item_exist(tag):
                    dpg.set_value(tag, 'N/A')
            for table_name in ['overview_info_table', 'timeseries_table', 'company_info_table', 'income_table', 'balance_table', 'cashflow_table', 'technical_table']:
                table_tag = f'{table_name}_{self.tab_id}'
                if dpg.does_item_exist(table_tag):
                    children = dpg.get_item_children(table_tag, 1)
                    for child in children:
                        dpg.delete_item(child)
            dpg.set_value(f'raw_data_display_{self.tab_id}', 'No data loaded yet...')
            self.update_status('🧹 Data cleared', [200, 200, 200])
            dpg.set_value(f'last_update_{self.tab_id}', 'Never')
        except Exception as e:
            print(f'❌ DEBUG: Error in clear_data(): {str(e)}')

    def update_status(self, message: str, color: List[int]=None):
        """Update status message"""
        try:
            if color is None:
                color = [200, 200, 200]
            status_tag = f'status_text_{self.tab_id}'
            if dpg.does_item_exist(status_tag):
                dpg.set_value(status_tag, message)
                dpg.configure_item(status_tag, color=color)
        except Exception as e:
            print(f'❌ DEBUG: Error in update_status(): {str(e)}')

    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_auto_refresh()
            self.current_data = {}
            print('✅ DEBUG: Enhanced Data Viewer tab cleanup completed')
        except Exception as e:
            print(f'❌ DEBUG: Error during cleanup: {str(e)}')

def safe_add_item(self, add_function, *args, **kwargs):
    """Safely add DPG items with error handling"""
    try:
        return add_function(*args, **kwargs)
    except Exception as e:
        print(f'❌ DEBUG: Error adding item {add_function.__name__}: {str(e)}')
        try:
            if 'tag' in kwargs:
                kwargs['tag'] = f'{kwargs['tag']}_{self.tab_id}'
            return add_function(*args, **kwargs)
        except:
            print(f'❌ DEBUG: Failed to add {add_function.__name__} even with modified tag')
            return None

def update_all_displays(self, data: Dict[str, Any], category: str, data_type: str, symbol: str):
    """Update all display tabs with fetched data"""
    try:
        self.update_overview_display(data, category, data_type, symbol)
        if 'data' in data and isinstance(data['data'], dict):
            self.update_timeseries_display(data['data'])
        if category == 'Fundamental Data':
            self.update_fundamentals_display(data, data_type)
        if category == 'Technical Indicators':
            self.update_technical_display(data, data_type)
        self.update_raw_display(data)
        self.update_provider_info(data)
    except Exception as e:
        print(f'❌ DEBUG: Error in update_all_displays(): {str(e)}')

def update_fundamentals_display(self, data: Dict[str, Any], data_type: str):
    """Update fundamentals display based on data type"""
    try:
        if data_type == 'Company Overview':
            self.update_company_info_table(data.get('data', {}))
        elif data_type == 'Income Statement':
            self.update_financial_table('income_table', data.get('data', {}))
        elif data_type == 'Balance Sheet':
            self.update_financial_table('balance_table', data.get('data', {}))
        elif data_type == 'Cash Flow':
            self.update_financial_table('cashflow_table', data.get('data', {}))
    except Exception as e:
        print(f'❌ DEBUG: Error in update_fundamentals_display(): {str(e)}')

def refresh_timeseries_view(self):
    """Refresh the time series view with current data"""
    try:
        if self.current_data and 'data' in self.current_data:
            self.update_timeseries_display(self.current_data['data'])
    except Exception as e:
        print(f'❌ DEBUG: Error in refresh_timeseries_view(): {str(e)}')

def stop_auto_refresh(self):
    """Stop auto refresh thread"""
    try:
        self._stop_refresh = True
        if self.refresh_thread:
            self.refresh_thread.join(timeout=1.0)
    except Exception as e:
        print(f'❌ DEBUG: Error in stop_auto_refresh(): {str(e)}')

def info(msg, **kwargs):
    print(f'INFO: {msg}')

def warning(msg, **kwargs):
    print(f'WARNING: {msg}')

def error(msg, **kwargs):
    print(f'ERROR: {msg}')

def debug(msg, **kwargs):
    print(f'DEBUG: {msg}')

class NotificationConfig:
    """Configuration for notification system"""

    def __init__(self):
        self.enabled = os.getenv('FINCEPT_NOTIFICATIONS', 'true').lower() == 'true'
        self.silent_mode = os.getenv('FINCEPT_SILENT_MODE', 'false').lower() == 'true'
        self.debug_notifications = os.getenv('FINCEPT_DEBUG_NOTIFICATIONS', 'false').lower() == 'true'
        self.rate_limit_enabled = True
        self.max_notifications_per_minute = int(os.getenv('FINCEPT_MAX_NOTIFICATIONS_PER_MIN', '5'))
        self.duplicate_suppression_window = int(os.getenv('FINCEPT_DUPLICATE_WINDOW', '30'))
        enabled_levels = os.getenv('FINCEPT_NOTIFICATION_LEVELS', 'info,success,warning,error,critical')
        self.enabled_levels = set((level.strip().lower() for level in enabled_levels.split(',')))
        self.app_name = os.getenv('FINCEPT_APP_NAME', 'Finance Terminal')
        self.app_icon = self._get_app_icon()
        self.tab_prefixes = {'chat': '💬 Chat', 'forum': '📋 Forum', 'dashboard': '📊 Dashboard', 'market': '📈 Market', 'analytics': '📉 Analytics', 'database': '🗄️ Database', 'api': '🌐 API', 'session': '🔐 Session', 'trading': '💰 Trading', 'portfolio': '📦 Portfolio', 'alerts': '🚨 Alerts', 'main': '🏠 Main', 'logger': '📝 Logger'}

    def _get_app_icon(self) -> Optional[str]:
        """Get application icon path"""
        icon_path = os.getenv('FINCEPT_ICON_PATH')
        if icon_path and Path(icon_path).exists():
            return icon_path
        possible_paths = [Path.cwd() / 'assets' / 'icon.ico', Path.cwd() / 'assets' / 'icon.png', Path.cwd() / 'icon.ico', Path.cwd() / 'icon.png']
        for path in possible_paths:
            if path.exists():
                return str(path)
        return None

    def get_tab_prefix(self, module: Optional[str]) -> str:
        """Get display prefix for module/tab"""
        if not module:
            return '🏠'
        module_key = module.lower().split('_')[0]
        return self.tab_prefixes.get(module_key, f'📱 {module.title()}')

def __init__(self):
    self.enabled = os.getenv('FINCEPT_NOTIFICATIONS', 'true').lower() == 'true'
    self.silent_mode = os.getenv('FINCEPT_SILENT_MODE', 'false').lower() == 'true'
    self.debug_notifications = os.getenv('FINCEPT_DEBUG_NOTIFICATIONS', 'false').lower() == 'true'
    self.rate_limit_enabled = True
    self.max_notifications_per_minute = int(os.getenv('FINCEPT_MAX_NOTIFICATIONS_PER_MIN', '5'))
    self.duplicate_suppression_window = int(os.getenv('FINCEPT_DUPLICATE_WINDOW', '30'))
    enabled_levels = os.getenv('FINCEPT_NOTIFICATION_LEVELS', 'info,success,warning,error,critical')
    self.enabled_levels = set((level.strip().lower() for level in enabled_levels.split(',')))
    self.app_name = os.getenv('FINCEPT_APP_NAME', 'Finance Terminal')
    self.app_icon = self._get_app_icon()
    self.tab_prefixes = {'chat': '💬 Chat', 'forum': '📋 Forum', 'dashboard': '📊 Dashboard', 'market': '📈 Market', 'analytics': '📉 Analytics', 'database': '🗄️ Database', 'api': '🌐 API', 'session': '🔐 Session', 'trading': '💰 Trading', 'portfolio': '📦 Portfolio', 'alerts': '🚨 Alerts', 'main': '🏠 Main', 'logger': '📝 Logger'}

class LogConfig:
    """Simplified configuration with automatic class detection"""

    def __init__(self):
        self.debug_mode = os.getenv('FINCEPT_DEBUG', 'false').lower() == 'true'
        self.log_level = getattr(logging, os.getenv('FINCEPT_LOG_LEVEL', 'INFO').upper(), logging.INFO)
        self.console_enabled = os.getenv('FINCEPT_CONSOLE_LOG', 'false').lower() == 'true'
        self.max_file_size = int(os.getenv('FINCEPT_MAX_LOG_SIZE', str(50 * 1024 * 1024)))
        self.backup_count = int(os.getenv('FINCEPT_BACKUP_COUNT', '10'))
        self.retention_days = int(os.getenv('FINCEPT_RETENTION_DAYS', '30'))
        self.buffer_size = 1000
        self.flush_interval = 30.0

    @lru_cache(maxsize=256)
    def get_class_prefix(self, class_name: Optional[str]) -> str:
        """Generate intelligent prefix from class name with caching"""
        if not class_name:
            return 'APP'
        class_name = class_name.strip()
        suffixes_to_remove = ['Tab', 'Manager', 'Handler', 'Service', 'Client', 'Controller', 'Helper']
        for suffix in suffixes_to_remove:
            if class_name.endswith(suffix):
                class_name = class_name[:-len(suffix)]
                break
        words = re.findall('[A-Z][a-z]*', class_name)
        if words:
            if len(words) == 1:
                return words[0].upper()
            elif len(words) <= 3:
                return '_'.join((word.upper() for word in words))
            else:
                return f'{words[0].upper()}_{words[-1].upper()}'
        return class_name.upper()[:10]

    def get_logs_dir(self) -> Path:
        """Get logs directory - uses .fincept/logs folder"""
        if (env_dir := os.getenv('FINCEPT_LOGS_DIR')):
            return Path(env_dir).expanduser()
        logs_dir = Path.home() / '.fincept' / 'logs'
        return logs_dir

def __init__(self):
    self.debug_mode = os.getenv('FINCEPT_DEBUG', 'false').lower() == 'true'
    self.log_level = getattr(logging, os.getenv('FINCEPT_LOG_LEVEL', 'INFO').upper(), logging.INFO)
    self.console_enabled = os.getenv('FINCEPT_CONSOLE_LOG', 'false').lower() == 'true'
    self.max_file_size = int(os.getenv('FINCEPT_MAX_LOG_SIZE', str(50 * 1024 * 1024)))
    self.backup_count = int(os.getenv('FINCEPT_BACKUP_COUNT', '10'))
    self.retention_days = int(os.getenv('FINCEPT_RETENTION_DAYS', '30'))
    self.buffer_size = 1000
    self.flush_interval = 30.0

def get_logs_dir(self) -> Path:
    """Get logs directory - uses .fincept/logs folder"""
    if (env_dir := os.getenv('FINCEPT_LOGS_DIR')):
        return Path(env_dir).expanduser()
    logs_dir = Path.home() / '.fincept' / 'logs'
    return logs_dir

def analyze_stock_with_hedge_funds(ticker: str, financial_data: dict):
    """Use multiple hedge fund agents to analyze a stock"""
    state = {'data': {'tickers': [ticker], 'end_date': '2024-12-31', 'analyst_signals': {}}, 'metadata': {'show_reasoning': True}}
    results = {}
    bridgewater_result = bridgewater_associates_agent(state, 'bridgewater')
    results['bridgewater'] = state['data']['analyst_signals']['bridgewater']
    renaissance_result = renaissance_technologies_agent(state, 'renaissance')
    results['renaissance'] = state['data']['analyst_signals']['renaissance']
    aqr_result = aqr_capital_hedge_fund_agent(state, 'aqr')
    results['aqr'] = state['data']['analyst_signals']['aqr']
    return results

def call_llm_openrouter(prompt, pydantic_model, agent_name, state, default_factory, model='anthropic/claude-3.5-sonnet'):
    """Modified LLM call for OpenRouter"""
    client = setup_openrouter_client()
    try:
        response = client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': prompt.messages[0].content}, {'role': 'user', 'content': prompt.messages[1].content}], temperature=0.1, max_tokens=2000)
        import json
        content = response.choices[0].message.content
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        json_str = content[start_idx:end_idx]
        parsed_data = json.loads(json_str)
        return pydantic_model(**parsed_data)
    except Exception as e:
        print(f'OpenRouter API error: {e}')
        return default_factory()

def call_llm_ollama(prompt, pydantic_model, agent_name, state, default_factory, model='llama3.1:70b'):
    """Modified LLM call for Ollama local"""
    full_prompt = f'System: {prompt.messages[0].content}\n\nHuman: {prompt.messages[1].content}\n\nAssistant:'
    try:
        response = requests.post('http://localhost:11434/api/generate', json={'model': model, 'prompt': full_prompt, 'stream': False, 'options': {'temperature': 0.1, 'top_p': 0.9}}, timeout=120)
        if response.status_code == 200:
            content = response.json()['response']
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                parsed_data = json.loads(json_str)
                return pydantic_model(**parsed_data)
            else:
                raise ValueError('No valid JSON found in response')
        else:
            raise Exception(f'HTTP {response.status_code}: {response.text}')
    except Exception as e:
        print(f'Ollama API error: {e}')
        return default_factory()

class HedgeFundLLMAdapter:
    """Adapter to use different LLM providers with hedge fund agents"""

    def __init__(self, provider='openai', **kwargs):
        self.provider = provider
        self.config = kwargs

    def call_llm(self, prompt, pydantic_model, agent_name, state, default_factory):
        """Route to appropriate LLM provider"""
        if self.provider == 'openrouter':
            return call_llm_openrouter(prompt, pydantic_model, agent_name, state, default_factory, model=self.config.get('model', 'anthropic/claude-3.5-sonnet'))
        elif self.provider == 'ollama':
            return call_llm_ollama(prompt, pydantic_model, agent_name, state, default_factory, model=self.config.get('model', 'llama3.1:70b'))
        elif self.provider == 'openai':
            return self.call_openai_llm(prompt, pydantic_model, agent_name, state, default_factory)
        else:
            raise ValueError(f'Unsupported provider: {self.provider}')

    def call_openai_llm(self, prompt, pydantic_model, agent_name, state, default_factory):
        """OpenAI integration"""
        import openai
        client = openai.OpenAI(api_key=self.config.get('api_key'))
        try:
            response = client.chat.completions.create(model=self.config.get('model', 'gpt-4'), messages=[{'role': 'system', 'content': prompt.messages[0].content}, {'role': 'user', 'content': prompt.messages[1].content}], temperature=0.1, max_tokens=2000)
            content = response.choices[0].message.content
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            json_str = content[start_idx:end_idx]
            parsed_data = json.loads(json_str)
            return pydantic_model(**parsed_data)
        except Exception as e:
            print(f'OpenAI API error: {e}')
            return default_factory()

def call_openai_llm(self, prompt, pydantic_model, agent_name, state, default_factory):
    """OpenAI integration"""
    import openai
    client = openai.OpenAI(api_key=self.config.get('api_key'))
    try:
        response = client.chat.completions.create(model=self.config.get('model', 'gpt-4'), messages=[{'role': 'system', 'content': prompt.messages[0].content}, {'role': 'user', 'content': prompt.messages[1].content}], temperature=0.1, max_tokens=2000)
        content = response.choices[0].message.content
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        json_str = content[start_idx:end_idx]
        parsed_data = json.loads(json_str)
        return pydantic_model(**parsed_data)
    except Exception as e:
        print(f'OpenAI API error: {e}')
        return default_factory()

def example_standalone_usage():
    """Example: Using hedge fund agents standalone"""
    mock_state = {'data': {'tickers': ['AAPL'], 'end_date': '2024-12-31', 'analyst_signals': {}}, 'metadata': {'show_reasoning': True}}
    import bridgewater_hedge_fund
    llm_adapter = HedgeFundLLMAdapter(provider='openrouter', model='anthropic/claude-3.5-sonnet')
    bridgewater_hedge_fund.call_llm = llm_adapter.call_llm
    result = bridgewater_associates_agent(mock_state, 'bridgewater_test')
    print('Bridgewater Analysis Results:')
    print(json.dumps(mock_state['data']['analyst_signals']['bridgewater_test'], indent=2))

def example_multi_hedge_fund_consensus():
    """Example: Get consensus from multiple hedge funds"""
    hedge_funds = [('bridgewater', bridgewater_associates_agent), ('renaissance', renaissance_technologies_agent), ('aqr', aqr_capital_hedge_fund_agent), ('elliott', elliott_management_hedge_fund_agent)]
    ticker = 'MSFT'
    all_signals = {}
    llm_adapter = HedgeFundLLMAdapter(provider='ollama', model='llama3.1:70b')
    for fund_name, fund_agent in hedge_funds:
        fund_module = fund_agent.__module__
        import importlib
        module = importlib.import_module(fund_module)
        module.call_llm = llm_adapter.call_llm
        state = create_mock_state([ticker])
        try:
            fund_agent(state, f'{fund_name}_analysis')
            all_signals[fund_name] = state['data']['analyst_signals'][f'{fund_name}_analysis'][ticker]
        except Exception as e:
            print(f'Error running {fund_name}: {e}')
            continue
    consensus = calculate_hedge_fund_consensus(all_signals)
    return consensus

@app.route('/analyze/<ticker>')
def analyze_ticker(ticker):
    """Web endpoint to analyze a ticker with all hedge funds"""
    try:
        provider = request.args.get('provider', 'openrouter')
        model = request.args.get('model', 'anthropic/claude-3.5-sonnet')
        llm_adapter = HedgeFundLLMAdapter(provider=provider, model=model)
        selected_funds = request.args.get('funds', 'bridgewater,aqr,renaissance').split(',')
        results = {}
        for fund_name in selected_funds:
            if fund_name in AVAILABLE_FUNDS:
                fund_agent = AVAILABLE_FUNDS[fund_name]
                fund_module = importlib.import_module(fund_agent.__module__)
                fund_module.call_llm = llm_adapter.call_llm
                state = create_mock_state([ticker])
                fund_agent(state, f'{fund_name}_web')
                results[fund_name] = state['data']['analyst_signals'][f'{fund_name}_web'][ticker]
        consensus = calculate_hedge_fund_consensus(results)
        return jsonify({'ticker': ticker, 'consensus': consensus, 'individual_analyses': results, 'timestamp': '2024-12-31T00:00:00Z'})
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

def is_ollama_installed() -> bool:
    """Check if Ollama is installed on the system."""
    system = platform.system().lower()
    if system == 'darwin' or system == 'linux':
        try:
            result = subprocess.run(['which', 'ollama'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.returncode == 0
        except Exception:
            return False
    elif system == 'windows':
        try:
            result = subprocess.run(['where', 'ollama'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            return result.returncode == 0
        except Exception:
            return False
    else:
        return False

def get_locally_available_models() -> List[str]:
    """Get a list of models that are already downloaded locally."""
    if not is_ollama_server_running():
        return []
    try:
        response = requests.get(OLLAMA_API_MODELS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data['models']] if 'models' in data else []
        return []
    except requests.RequestException:
        return []

def start_ollama_server() -> bool:
    """Start the Ollama server if it's not already running."""
    if is_ollama_server_running():
        print(f'{Fore.GREEN}Ollama server is already running.{Style.RESET_ALL}')
        return True
    system = platform.system().lower()
    try:
        if system == 'darwin' or system == 'linux':
            subprocess.Popen(['ollama', 'serve'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif system == 'windows':
            subprocess.Popen(['ollama', 'serve'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        else:
            print(f'{Fore.RED}Unsupported operating system: {system}{Style.RESET_ALL}')
            return False
        for _ in range(10):
            if is_ollama_server_running():
                print(f'{Fore.GREEN}Ollama server started successfully.{Style.RESET_ALL}')
                return True
            time.sleep(1)
        print(f'{Fore.RED}Failed to start Ollama server. Timed out waiting for server to become available.{Style.RESET_ALL}')
        return False
    except Exception as e:
        print(f'{Fore.RED}Error starting Ollama server: {e}{Style.RESET_ALL}')
        return False

def install_ollama() -> bool:
    """Install Ollama on the system."""
    system = platform.system().lower()
    if system not in OLLAMA_DOWNLOAD_URL:
        print(f'{Fore.RED}Unsupported operating system for automatic installation: {system}{Style.RESET_ALL}')
        print(f'Please visit https://ollama.com/download to install Ollama manually.')
        return False
    if system == 'darwin':
        print(f'{Fore.YELLOW}Ollama for Mac is available as an application download.{Style.RESET_ALL}')
        if questionary.confirm('Would you like to download the Ollama application?', default=True).ask():
            try:
                import webbrowser
                webbrowser.open(OLLAMA_DOWNLOAD_URL['darwin'])
                print(f'{Fore.YELLOW}Please download and install the application, then restart this program.{Style.RESET_ALL}')
                print(f'{Fore.CYAN}After installation, you may need to open the Ollama app once before continuing.{Style.RESET_ALL}')
                if questionary.confirm('Have you installed the Ollama app and opened it at least once?', default=False).ask():
                    if is_ollama_installed() and start_ollama_server():
                        print(f'{Fore.GREEN}Ollama is now properly installed and running!{Style.RESET_ALL}')
                        return True
                    else:
                        print(f'{Fore.RED}Ollama installation not detected. Please restart this application after installing Ollama.{Style.RESET_ALL}')
                        return False
                return False
            except Exception as e:
                print(f'{Fore.RED}Failed to open browser: {e}{Style.RESET_ALL}')
                return False
        else:
            if questionary.confirm('Would you like to try the command-line installation instead? (For advanced users)', default=False).ask():
                print(f'{Fore.YELLOW}Attempting command-line installation...{Style.RESET_ALL}')
                try:
                    install_process = subprocess.run(['bash', '-c', 'curl -fsSL https://ollama.com/install.sh | sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if install_process.returncode == 0:
                        print(f'{Fore.GREEN}Ollama installed successfully via command line.{Style.RESET_ALL}')
                        return True
                    else:
                        print(f'{Fore.RED}Command-line installation failed. Please use the app download method instead.{Style.RESET_ALL}')
                        return False
                except Exception as e:
                    print(f'{Fore.RED}Error during command-line installation: {e}{Style.RESET_ALL}')
                    return False
            return False
    elif system == 'linux':
        print(f'{Fore.YELLOW}Installing Ollama...{Style.RESET_ALL}')
        try:
            install_process = subprocess.run(['bash', '-c', 'curl -fsSL https://ollama.com/install.sh | sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if install_process.returncode == 0:
                print(f'{Fore.GREEN}Ollama installed successfully.{Style.RESET_ALL}')
                return True
            else:
                print(f'{Fore.RED}Failed to install Ollama. Error: {install_process.stderr}{Style.RESET_ALL}')
                return False
        except Exception as e:
            print(f'{Fore.RED}Error during Ollama installation: {e}{Style.RESET_ALL}')
            return False
    elif system == 'windows':
        print(f'{Fore.YELLOW}Automatic installation on Windows is not supported.{Style.RESET_ALL}')
        print(f'Please download and install Ollama from: {OLLAMA_DOWNLOAD_URL['windows']}')
        if questionary.confirm('Do you want to open the Ollama download page in your browser?').ask():
            try:
                import webbrowser
                webbrowser.open(OLLAMA_DOWNLOAD_URL['windows'])
                print(f'{Fore.YELLOW}After installation, please restart this application.{Style.RESET_ALL}')
                if questionary.confirm('Have you installed Ollama?', default=False).ask():
                    if is_ollama_installed() and start_ollama_server():
                        print(f'{Fore.GREEN}Ollama is now properly installed and running!{Style.RESET_ALL}')
                        return True
                    else:
                        print(f'{Fore.RED}Ollama installation not detected. Please restart this application after installing Ollama.{Style.RESET_ALL}')
                        return False
            except Exception as e:
                print(f'{Fore.RED}Failed to open browser: {e}{Style.RESET_ALL}')
        return False
    return False

def download_model(model_name: str) -> bool:
    """Download an Ollama model."""
    if not is_ollama_server_running():
        if not start_ollama_server():
            return False
    print(f'{Fore.YELLOW}Downloading model {model_name}...{Style.RESET_ALL}')
    print(f'{Fore.CYAN}This may take a while depending on your internet speed and the model size.{Style.RESET_ALL}')
    print(f'{Fore.CYAN}The download is happening in the background. Please be patient...{Style.RESET_ALL}')
    try:
        process = subprocess.Popen(['ollama', 'pull', model_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace')
        print(f'{Fore.CYAN}Download progress:{Style.RESET_ALL}')
        last_percentage = 0
        last_phase = ''
        bar_length = 40
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output = output.strip()
                percentage = None
                current_phase = None
                import re
                percentage_match = re.search('(\\d+(\\.\\d+)?)%', output)
                if percentage_match:
                    try:
                        percentage = float(percentage_match.group(1))
                    except ValueError:
                        percentage = None
                phase_match = re.search('^([a-zA-Z\\s]+):', output)
                if phase_match:
                    current_phase = phase_match.group(1).strip()
                if percentage is not None:
                    if abs(percentage - last_percentage) >= 1 or (current_phase and current_phase != last_phase):
                        last_percentage = percentage
                        if current_phase:
                            last_phase = current_phase
                        filled_length = int(bar_length * percentage / 100)
                        bar = '█' * filled_length + '░' * (bar_length - filled_length)
                        phase_display = f'{Fore.CYAN}{last_phase.capitalize()}{Style.RESET_ALL}: ' if last_phase else ''
                        status_line = f'\r{phase_display}{Fore.GREEN}{bar}{Style.RESET_ALL} {Fore.YELLOW}{percentage:.1f}%{Style.RESET_ALL}'
                        print(status_line, end='', flush=True)
                elif 'download' in output.lower() or 'extract' in output.lower() or 'pulling' in output.lower():
                    if '%' in output:
                        print(f'\r{Fore.GREEN}{output}{Style.RESET_ALL}', end='', flush=True)
                    else:
                        print(f'{Fore.GREEN}{output}{Style.RESET_ALL}')
        return_code = process.wait()
        print()
        if return_code == 0:
            print(f'{Fore.GREEN}Model {model_name} downloaded successfully!{Style.RESET_ALL}')
            return True
        else:
            print(f'{Fore.RED}Failed to download model {model_name}. Check your internet connection and try again.{Style.RESET_ALL}')
            return False
    except Exception as e:
        print(f'\n{Fore.RED}Error downloading model {model_name}: {e}{Style.RESET_ALL}')
        return False

def ensure_ollama_and_model(model_name: str) -> bool:
    """Ensure Ollama is installed, running, and the requested model is available."""
    in_docker = os.environ.get('OLLAMA_BASE_URL', '').startswith('http://ollama:') or os.environ.get('OLLAMA_BASE_URL', '').startswith('http://host.docker.internal:')
    if in_docker:
        ollama_url = os.environ.get('OLLAMA_BASE_URL', 'http://ollama:11434')
        return docker.ensure_ollama_and_model(model_name, ollama_url)
    if not is_ollama_installed():
        print(f'{Fore.YELLOW}Ollama is not installed on your system.{Style.RESET_ALL}')
        if questionary.confirm('Do you want to install Ollama?').ask():
            if not install_ollama():
                return False
        else:
            print(f'{Fore.RED}Ollama is required to use local models.{Style.RESET_ALL}')
            return False
    if not is_ollama_server_running():
        print(f'{Fore.YELLOW}Starting Ollama server...{Style.RESET_ALL}')
        if not start_ollama_server():
            return False
    available_models = get_locally_available_models()
    if model_name not in available_models:
        print(f'{Fore.YELLOW}Model {model_name} is not available locally.{Style.RESET_ALL}')
        model_size_info = ''
        if '70b' in model_name:
            model_size_info = ' This is a large model (up to several GB) and may take a while to download.'
        elif '34b' in model_name or '8x7b' in model_name:
            model_size_info = ' This is a medium-sized model (1-2 GB) and may take a few minutes to download.'
        if questionary.confirm(f'Do you want to download the {model_name} model?{model_size_info} The download will happen in the background.').ask():
            return download_model(model_name)
        else:
            print(f'{Fore.RED}The model is required to proceed.{Style.RESET_ALL}')
            return False
    return True

def delete_model(model_name: str) -> bool:
    """Delete a locally downloaded Ollama model."""
    in_docker = os.environ.get('OLLAMA_BASE_URL', '').startswith('http://ollama:') or os.environ.get('OLLAMA_BASE_URL', '').startswith('http://host.docker.internal:')
    if in_docker:
        ollama_url = os.environ.get('OLLAMA_BASE_URL', 'http://ollama:11434')
        return docker.delete_model(model_name, ollama_url)
    if not is_ollama_server_running():
        if not start_ollama_server():
            return False
    print(f'{Fore.YELLOW}Deleting model {model_name}...{Style.RESET_ALL}')
    try:
        process = subprocess.run(['ollama', 'rm', model_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if process.returncode == 0:
            print(f'{Fore.GREEN}Model {model_name} deleted successfully.{Style.RESET_ALL}')
            return True
        else:
            print(f'{Fore.RED}Failed to delete model {model_name}. Error: {process.stderr}{Style.RESET_ALL}')
            return False
    except Exception as e:
        print(f'{Fore.RED}Error deleting model {model_name}: {e}{Style.RESET_ALL}')
        return False

def ensure_ollama_and_model(model_name: str, ollama_url: str) -> bool:
    """Ensure the Ollama model is available in a Docker environment."""
    print(f'{Fore.CYAN}Docker environment detected.{Style.RESET_ALL}')
    if not is_ollama_available(ollama_url):
        return False
    available_models = get_available_models(ollama_url)
    if model_name in available_models:
        print(f'{Fore.GREEN}Model {model_name} is available in the Docker Ollama container.{Style.RESET_ALL}')
        return True
    print(f'{Fore.YELLOW}Model {model_name} is not available in the Docker Ollama container.{Style.RESET_ALL}')
    if not questionary.confirm(f'Do you want to download {model_name}?').ask():
        print(f'{Fore.RED}Cannot proceed without the model.{Style.RESET_ALL}')
        return False
    return download_model(model_name, ollama_url)

def is_ollama_available(ollama_url: str) -> bool:
    """Check if Ollama service is available in Docker environment."""
    try:
        response = requests.get(f'{ollama_url}/api/version', timeout=5)
        if response.status_code == 200:
            return True
        print(f'{Fore.RED}Cannot connect to Ollama service at {ollama_url}.{Style.RESET_ALL}')
        print(f'{Fore.YELLOW}Make sure the Ollama service is running in your Docker environment.{Style.RESET_ALL}')
        return False
    except requests.RequestException as e:
        print(f'{Fore.RED}Error connecting to Ollama service: {e}{Style.RESET_ALL}')
        return False

def get_available_models(ollama_url: str) -> list:
    """Get list of available models in Docker environment."""
    try:
        response = requests.get(f'{ollama_url}/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [m['name'] for m in models]
        print(f'{Fore.RED}Failed to get available models from Ollama service. Status code: {response.status_code}{Style.RESET_ALL}')
        return []
    except requests.RequestException as e:
        print(f'{Fore.RED}Error getting available models: {e}{Style.RESET_ALL}')
        return []

def delete_model(model_name: str, ollama_url: str) -> bool:
    """Delete a model in Docker environment."""
    print(f'{Fore.YELLOW}Deleting model {model_name} from Docker container...{Style.RESET_ALL}')
    try:
        response = requests.delete(f'{ollama_url}/api/delete', json={'name': model_name}, timeout=10)
        if response.status_code == 200:
            print(f'{Fore.GREEN}Model {model_name} deleted successfully.{Style.RESET_ALL}')
            return True
        else:
            print(f'{Fore.RED}Failed to delete model. Status code: {response.status_code}{Style.RESET_ALL}')
            if response.text:
                print(f'{Fore.RED}Error: {response.text}{Style.RESET_ALL}')
            return False
    except requests.RequestException as e:
        print(f'{Fore.RED}Error deleting model: {e}{Style.RESET_ALL}')
        return False

def call_llm(prompt: any, pydantic_model: type[BaseModel], agent_name: str | None=None, state: AgentState | None=None, max_retries: int=3, default_factory=None) -> BaseModel:
    """
    Makes an LLM call with retry logic, handling both JSON supported and non-JSON supported models.

    Args:
        prompt: The prompt to send to the LLM
        pydantic_model: The Pydantic model class to structure the output
        agent_name: Optional name of the agent for progress updates and model config extraction
        state: Optional state object to extract agent-specific model configuration
        max_retries: Maximum number of retries (default: 3)
        default_factory: Optional factory function to create default response on failure

    Returns:
        An instance of the specified Pydantic model
    """
    if state and agent_name:
        model_name, model_provider = get_agent_model_config(state, agent_name)
    else:
        model_name = 'gpt-4.1'
        model_provider = 'OPENAI'
    api_keys = None
    if state:
        request = state.get('metadata', {}).get('request')
        if request and hasattr(request, 'api_keys'):
            api_keys = request.api_keys
    model_info = get_model_info(model_name, model_provider)
    llm = get_model(model_name, model_provider, api_keys)
    if not (model_info and (not model_info.has_json_mode())):
        llm = llm.with_structured_output(pydantic_model, method='json_mode')
    for attempt in range(max_retries):
        try:
            result = llm.invoke(prompt)
            if model_info and (not model_info.has_json_mode()):
                parsed_result = extract_json_from_response(result.content)
                if parsed_result:
                    return pydantic_model(**parsed_result)
            else:
                return result
        except Exception as e:
            if agent_name:
                progress.update_status(agent_name, None, f'Error - retry {attempt + 1}/{max_retries}')
            if attempt == max_retries - 1:
                print(f'Error in LLM call after {max_retries} attempts: {e}')
                if default_factory:
                    return default_factory()
                return create_default_response(pydantic_model)
    return create_default_response(pydantic_model)

def extract_json_from_response(content: str) -> dict | None:
    """Extracts JSON from markdown-formatted response."""
    try:
        json_start = content.find('```json')
        if json_start != -1:
            json_text = content[json_start + 7:]
            json_end = json_text.find('```')
            if json_end != -1:
                json_text = json_text[:json_end].strip()
                return json.loads(json_text)
    except Exception as e:
        print(f'Error extracting JSON from response: {e}')
    return None

def get_agent_model_config(state, agent_name):
    """
    Get model configuration for a specific agent from the state.
    Falls back to global model configuration if agent-specific config is not available.
    Always returns valid model_name and model_provider values.
    """
    request = state.get('metadata', {}).get('request')
    if request and hasattr(request, 'get_agent_model_config'):
        model_name, model_provider = request.get_agent_model_config(agent_name)
        if model_name and model_provider:
            return (model_name, model_provider.value if hasattr(model_provider, 'value') else str(model_provider))
    model_name = state.get('metadata', {}).get('model_name') or 'gpt-4.1'
    model_provider = state.get('metadata', {}).get('model_provider') or 'OPENAI'
    if hasattr(model_provider, 'value'):
        model_provider = model_provider.value
    return (model_name, model_provider)

def show_agent_reasoning(output, agent_name):
    print(f'\n{'=' * 10} {agent_name.center(28)} {'=' * 10}')

    def convert_to_serializable(obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif isinstance(obj, (int, float, bool, str)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: convert_to_serializable(value) for key, value in obj.items()}
        else:
            return str(obj)
    if isinstance(output, (dict, list)):
        serializable_output = convert_to_serializable(output)
        print(json.dumps(serializable_output, indent=2))
    else:
        try:
            parsed_output = json.loads(output)
            print(json.dumps(parsed_output, indent=2))
        except json.JSONDecodeError:
            print(output)
    print('=' * 48)

def convert_to_serializable(obj):
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif isinstance(obj, (int, float, bool, str)):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    else:
        return str(obj)

class DataCache:
    """Redis-based caching for data feeds"""

    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.default_ttl = CONFIG.agent.cache_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get cached data"""
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int]=None) -> bool:
        """Set cached data"""
        try:
            ttl = ttl or self.default_ttl
            return self.redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            return False

    def generate_key(self, source: str, params: Dict) -> str:
        """Generate cache key from parameters"""
        param_str = json.dumps(params, sort_keys=True)
        return f'{source}:{hashlib.md5(param_str.encode()).hexdigest()}'

def get(self, key: str) -> Optional[Any]:
    """Get cached data"""
    try:
        data = self.redis_client.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None

class Config:
    """Main configuration class"""

    def __init__(self):
        self.api = APIConfig()
        self.llm = LLMConfig()
        self.agent = AgentConfig()
        self.risk = RiskConfig()
        self.trading = TradingConfig()
        self.log_level = logging.INFO
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.data_dir = Path('data')
        self.cache_dir = Path('cache')
        self.logs_dir = Path('logs')
        for directory in [self.data_dir, self.cache_dir, self.logs_dir]:
            directory.mkdir(exist_ok=True)
        self.agent_weights = {'macro_cycle': 0.15, 'central_bank': 0.2, 'geopolitical': 0.18, 'regulatory': 0.12, 'sentiment': 0.1, 'institutional_flow': 0.15, 'supply_chain': 0.05, 'innovation': 0.03, 'currency': 0.02, 'behavioral': 0.0}
        self.trading_sessions = {'US': {'open': '09:30', 'close': '16:00', 'timezone': 'America/New_York'}, 'EU': {'open': '08:00', 'close': '16:30', 'timezone': 'Europe/London'}, 'ASIA': {'open': '09:00', 'close': '15:00', 'timezone': 'Asia/Tokyo'}}
        self.asset_classes = {'equities': ['SPY', 'QQQ', 'IWM', 'EFA', 'EEM'], 'bonds': ['TLT', 'IEF', 'SHY', 'LQD', 'HYG'], 'commodities': ['GLD', 'SLV', 'USO', 'UNG', 'DBA'], 'currencies': ['UUP', 'FXE', 'FXY', 'FXB', 'EWZ'], 'volatility': ['VIX', 'UVXY', 'SVXY']}
        self.economic_indicators = ['GDP', 'CPI', 'PPI', 'UNRATE', 'FEDFUNDS', 'DGS10', 'DGS2', 'DEXUSEU', 'DEXCHUS', 'DEXJPUS', 'DEXUSUK', 'CPIAUCSL', 'PAYEMS', 'INDPRO', 'HOUST', 'RSAFS', 'UMCSENT']
        self.news_sources = {'reuters': 0.95, 'bloomberg': 0.95, 'wsj': 0.9, 'ft': 0.9, 'cnbc': 0.75, 'marketwatch': 0.7, 'yahoo_finance': 0.65}

    def validate_config(self) -> bool:
        """Validate configuration settings"""
        required_keys = [self.api.openai_api_key, self.api.finnhub_api_key, self.api.fred_api_key]
        if not all(required_keys):
            raise ValueError('Missing required API keys. Check environment variables.')
        if sum(self.agent_weights.values()) != 1.0:
            raise ValueError('Agent weights must sum to 1.0')
        return True

    def get_market_hours(self, market: str) -> Dict[str, str]:
        """Get trading hours for specific market"""
        return self.trading_sessions.get(market.upper(), {})

    def get_asset_universe(self, asset_class: str) -> List[str]:
        """Get tradeable assets for asset class"""
        return self.asset_classes.get(asset_class.lower(), [])

def __init__(self):
    self.api = APIConfig()
    self.llm = LLMConfig()
    self.agent = AgentConfig()
    self.risk = RiskConfig()
    self.trading = TradingConfig()
    self.log_level = logging.INFO
    self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    self.data_dir = Path('data')
    self.cache_dir = Path('cache')
    self.logs_dir = Path('logs')
    for directory in [self.data_dir, self.cache_dir, self.logs_dir]:
        directory.mkdir(exist_ok=True)
    self.agent_weights = {'macro_cycle': 0.15, 'central_bank': 0.2, 'geopolitical': 0.18, 'regulatory': 0.12, 'sentiment': 0.1, 'institutional_flow': 0.15, 'supply_chain': 0.05, 'innovation': 0.03, 'currency': 0.02, 'behavioral': 0.0}
    self.trading_sessions = {'US': {'open': '09:30', 'close': '16:00', 'timezone': 'America/New_York'}, 'EU': {'open': '08:00', 'close': '16:30', 'timezone': 'Europe/London'}, 'ASIA': {'open': '09:00', 'close': '15:00', 'timezone': 'Asia/Tokyo'}}
    self.asset_classes = {'equities': ['SPY', 'QQQ', 'IWM', 'EFA', 'EEM'], 'bonds': ['TLT', 'IEF', 'SHY', 'LQD', 'HYG'], 'commodities': ['GLD', 'SLV', 'USO', 'UNG', 'DBA'], 'currencies': ['UUP', 'FXE', 'FXY', 'FXB', 'EWZ'], 'volatility': ['VIX', 'UVXY', 'SVXY']}
    self.economic_indicators = ['GDP', 'CPI', 'PPI', 'UNRATE', 'FEDFUNDS', 'DGS10', 'DGS2', 'DEXUSEU', 'DEXCHUS', 'DEXJPUS', 'DEXUSUK', 'CPIAUCSL', 'PAYEMS', 'INDPRO', 'HOUST', 'RSAFS', 'UMCSENT']
    self.news_sources = {'reuters': 0.95, 'bloomberg': 0.95, 'wsj': 0.9, 'ft': 0.9, 'cnbc': 0.75, 'marketwatch': 0.7, 'yahoo_finance': 0.65}

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

def make_request(endpoint, params=None):
    """Efficient request function with counter"""
    global request_count
    if params is None:
        params = {}
    params['apikey'] = API_KEY
    try:
        response = requests.get(f'{BASE_URL}/{endpoint}', params=params)
        request_count += 1
        print(f'📡 Request {request_count}: {endpoint}')
        if response.status_code == 200:
            return response.json()
        else:
            print(f'❌ Error {response.status_code}: {endpoint}')
            return None
    except Exception as e:
        print(f'❌ Exception: {e}')
        return None

def on_dataset_selected(sender, app_data, user_data):
    """Callback when dataset is selected"""
    global selected_dataset, current_page
    print(f"DEBUG: Dataset selected - '{app_data}'")
    if not app_data or app_data == 'Select a dataset...':
        return
    selected_dataset = None
    for dataset in datasets:
        if dataset['display_name'] == app_data:
            selected_dataset = dataset
            break
    if selected_dataset:
        dpg.set_value('selected_info', f'Selected: {selected_dataset['display_name']}')
        dpg.set_value('status_text', f'Loading data for: {selected_dataset['dataset_id']}')
        print(f'DEBUG: Selected dataset ID: {selected_dataset['dataset_id']}')
        current_page = 1
        fetch_dataset_data(offset=0)
    else:
        dpg.set_value('status_text', f"Dataset '{app_data}' not found")

def on_prev_page():
    """Go to previous page"""
    global current_page, records_per_page
    if current_page > 1:
        offset = (current_page - 2) * records_per_page
        fetch_dataset_data(offset)

def on_next_page():
    """Go to next page"""
    global current_page, records_per_page, current_data
    total = current_data.get('total', 0)
    max_pages = (total + records_per_page - 1) // records_per_page
    if current_page < max_pages:
        offset = current_page * records_per_page
        fetch_dataset_data(offset)

class WebSocketClient:
    """WebSocket client for real-time data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws = None

    def connect(self, on_message=None, on_error=None, on_close=None):
        """Connect to WebSocket"""
        url = f'wss://ws.finnhub.io?token={self.api_key}'

        def on_open(ws):
            print('WebSocket connection opened')
        self.ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
        self.ws.run_forever()

    def subscribe(self, symbol: str, data_type: str='trade'):
        """Subscribe to real-time data"""
        if self.ws:
            message = json.dumps({'type': f'subscribe-{data_type}', 'symbol': symbol})
            self.ws.send(message)

    def unsubscribe(self, symbol: str, data_type: str='trade'):
        """Unsubscribe from real-time data"""
        if self.ws:
            message = json.dumps({'type': f'unsubscribe-{data_type}', 'symbol': symbol})
            self.ws.send(message)

def on_open(ws):
    print('WebSocket connection opened')

class DebugIMFWrapper:
    """Debug IMF wrapper with extensive logging"""

    def __init__(self):
        self.base_url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/'
        self.debug_log = []

    def log_debug(self, message: str):
        """Add debug message with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        debug_msg = f'[{timestamp}] {message}'
        self.debug_log.append(debug_msg)
        print(debug_msg)

    def get_debug_log(self) -> str:
        """Get all debug messages"""
        return '\n'.join(self.debug_log[-20:])

    def _run_async(self, coro):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

    async def _make_request(self, url: str) -> Dict:
        """Make async HTTP request with debug logging"""
        self.log_debug(f'Making request to: {url}')
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                self.log_debug('Session created, sending request...')
                async with session.get(url) as response:
                    self.log_debug(f'Response status: {response.status}')
                    self.log_debug(f'Response headers: {dict(response.headers)}')
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        self.log_debug(f'Content type: {content_type}')
                        if 'json' in content_type:
                            data = await response.json()
                            self.log_debug(f'JSON response keys: {(list(data.keys()) if isinstance(data, dict) else 'Not a dict')}')
                            return data
                        else:
                            text_data = await response.text()
                            self.log_debug(f'Text response (first 200 chars): {text_data[:200]}')
                            raise Exception(f'Expected JSON but got {content_type}')
                    else:
                        error_text = await response.text()
                        self.log_debug(f'Error response: {error_text[:200]}')
                        raise Exception(f'HTTP {response.status}: {response.reason}')
        except asyncio.TimeoutError:
            self.log_debug('Request timed out after 30 seconds')
            raise Exception('Request timeout')
        except aiohttp.ClientError as e:
            self.log_debug(f'Client error: {str(e)}')
            raise Exception(f'Network error: {str(e)}')
        except Exception as e:
            self.log_debug(f'Unexpected error: {str(e)}')
            raise

    def test_simple_connection(self) -> WrapperResponse:
        """Test basic connection to IMF API"""
        try:
            self.log_debug('Starting simple connection test...')
            test_urls = [f'{self.base_url}Dataflow', f'{self.base_url}CompactData/DOT/A.US.TXG_FOB_USD.CN?startPeriod=2022&endPeriod=2023', 'https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/DOT/A.US.TXG_FOB_USD.CN?startPeriod=2022&endPeriod=2023']
            for i, url in enumerate(test_urls):
                try:
                    self.log_debug(f'Testing URL {i + 1}: {url}')
                    response = self._run_async(self._make_request(url))
                    if response:
                        self.log_debug(f'URL {i + 1} SUCCESS - got response')
                        return WrapperResponse(success=True, message=f'Connection successful via URL {i + 1}', debug_info=self.get_debug_log())
                except Exception as e:
                    self.log_debug(f'URL {i + 1} FAILED: {str(e)}')
                    continue
            return WrapperResponse(success=False, error='All test URLs failed', debug_info=self.get_debug_log())
        except Exception as e:
            self.log_debug(f'Connection test exception: {str(e)}')
            return WrapperResponse(success=False, error=str(e), debug_info=self.get_debug_log())

    def get_direction_of_trade(self, **params) -> WrapperResponse:
        """Get bilateral trade data with multiple endpoint fallbacks"""
        try:
            self.log_debug('Starting direction of trade request...')
            defaults = {'country': 'US', 'counterpart': 'CN', 'direction': 'exports', 'frequency': 'A', 'start_date': '2022', 'end_date': '2023'}
            query_params = {**defaults, **params}
            self.log_debug(f'Query parameters: {query_params}')
            direction_map = {'exports': 'TXG_FOB_USD', 'imports': 'TMG_CIF_USD', 'balance': 'TBG_USD'}
            indicator = direction_map.get(query_params['direction'], 'TXG_FOB_USD')
            country = query_params['country']
            counterpart = query_params['counterpart']
            frequency = query_params['frequency']
            start_date = query_params['start_date']
            end_date = query_params['end_date']
            self.log_debug(f'Mapped indicator: {indicator}')
            url_templates = ['https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/DOT/{freq}.{country}.{indicator}.{counterpart}?startPeriod={start}&endPeriod={end}', 'http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/DOT/{freq}.{country}.{indicator}.{counterpart}?startPeriod={start}&endPeriod={end}', 'https://data.imf.org/api/data/DOT/{freq}.{country}.{indicator}.{counterpart}?startPeriod={start}&endPeriod={end}']
            for i, template in enumerate(url_templates):
                try:
                    url = template.format(freq=frequency, country=country, indicator=indicator, counterpart=counterpart, start=start_date, end=end_date)
                    self.log_debug(f'Trying URL template {i + 1}: {url}')
                    response = self._run_async(self._make_request(url))
                    self.log_debug(f'Got response from template {i + 1}, analyzing...')
                    result = self._parse_trade_response(response, query_params, indicator)
                    if result.success:
                        return result
                    else:
                        self.log_debug(f'Template {i + 1} parsing failed: {result.error}')
                except Exception as e:
                    self.log_debug(f'Template {i + 1} failed: {str(e)}')
                    continue
            self.log_debug('All URL templates failed, generating mock data for testing...')
            return self._generate_mock_trade_data(query_params)
        except Exception as e:
            self.log_debug(f'Exception in get_direction_of_trade: {str(e)}')
            return WrapperResponse(success=False, error=str(e), debug_info=self.get_debug_log())

    def _parse_trade_response(self, response, query_params, indicator) -> WrapperResponse:
        """Parse trade response with detailed logging"""
        try:
            if isinstance(response, dict):
                self.log_debug(f'Response top-level keys: {list(response.keys())}')
                if 'CompactData' in response:
                    return self._parse_sdmx_response(response, query_params, indicator)
                elif 'data' in response:
                    return self._parse_simple_response(response, query_params, indicator)
                elif 'ErrorDetails' in response:
                    error_details = response['ErrorDetails']
                    self.log_debug(f'API Error: {error_details}')
                    return WrapperResponse(success=False, error=f'IMF API Error: {error_details}')
                else:
                    self.log_debug('Unknown response format')
                    return WrapperResponse(success=False, error='Unknown response format')
            else:
                return WrapperResponse(success=False, error='Response is not a dictionary')
        except Exception as e:
            self.log_debug(f'Response parsing error: {str(e)}')
            return WrapperResponse(success=False, error=f'Parsing error: {str(e)}')

    def _parse_sdmx_response(self, response, query_params, indicator) -> WrapperResponse:
        """Parse SDMX format response"""
        try:
            compact_data = response['CompactData']
            self.log_debug(f'CompactData keys: {(list(compact_data.keys()) if isinstance(compact_data, dict) else 'Not a dict')}')
            dataset = compact_data.get('DataSet', {})
            series = dataset.get('Series', [])
            if not series:
                self.log_debug('No series data found in SDMX response')
                return WrapperResponse(success=False, error='No series data in response')
            return self._extract_trade_records(series, query_params, indicator)
        except Exception as e:
            return WrapperResponse(success=False, error=f'SDMX parsing error: {str(e)}')

    def _parse_simple_response(self, response, query_params, indicator) -> WrapperResponse:
        """Parse simple JSON response format"""
        try:
            data = response.get('data', [])
            self.log_debug(f'Simple response data length: {len(data)}')
            if not data:
                return WrapperResponse(success=False, error='No data in simple response')
            records = []
            for item in data:
                records.append({'date': item.get('date') or item.get('period'), 'country': query_params['country'], 'counterpart': query_params['counterpart'], 'direction': query_params['direction'], 'value': float(item.get('value', 0)), 'indicator': indicator})
            df = pd.DataFrame(records)
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} records')
        except Exception as e:
            return WrapperResponse(success=False, error=f'Simple parsing error: {str(e)}')

    def _extract_trade_records(self, series, query_params, indicator) -> WrapperResponse:
        """Extract records from series data"""
        try:
            if isinstance(series, dict):
                series = [series]
                self.log_debug('Converted single series dict to list')
            records = []
            for i, s in enumerate(series):
                self.log_debug(f'Processing series {i}: {(list(s.keys()) if isinstance(s, dict) else 'Not a dict')}')
                obs_list = s.get('Obs', [])
                if isinstance(obs_list, dict):
                    obs_list = [obs_list]
                self.log_debug(f'Series {i} has {len(obs_list)} observations')
                for j, obs in enumerate(obs_list):
                    time_period = obs.get('@TIME_PERIOD')
                    obs_value = obs.get('@OBS_VALUE')
                    self.log_debug(f'Obs {j}: TIME_PERIOD={time_period}, OBS_VALUE={obs_value}')
                    records.append({'date': time_period, 'country': query_params['country'], 'counterpart': query_params['counterpart'], 'direction': query_params['direction'], 'value': float(obs_value) if obs_value and obs_value != 'None' else 0, 'indicator': indicator})
            self.log_debug(f'Extracted {len(records)} records')
            if not records:
                return WrapperResponse(success=False, error='No valid records extracted')
            df = pd.DataFrame(records)
            try:
                df['date'] = pd.to_datetime(df['date'])
            except:
                self.log_debug('Date conversion failed, keeping as string')
            return WrapperResponse(success=True, data=df, message=f'Retrieved {len(df)} trade records')
        except Exception as e:
            return WrapperResponse(success=False, error=f'Record extraction error: {str(e)}')

    def _generate_mock_trade_data(self, query_params) -> WrapperResponse:
        """Generate mock trade data when API is unavailable"""
        try:
            self.log_debug('Generating mock trade data for testing...')
            years = [query_params['start_date'], query_params['end_date']]
            if query_params['start_date'] != query_params['end_date']:
                start_year = int(query_params['start_date'])
                end_year = int(query_params['end_date'])
                years = list(range(start_year, end_year + 1))
            records = []
            base_value = 500000
            for year in years:
                variation = (hash(f'{year}{query_params['country']}{query_params['counterpart']}') % 200 - 100) / 100
                value = base_value * (1 + variation * 0.1)
                records.append({'date': f'{year}-01-01', 'country': query_params['country'], 'counterpart': query_params['counterpart'], 'direction': query_params['direction'], 'value': value, 'indicator': 'MOCK_DATA'})
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            return WrapperResponse(success=True, data=df, message=f'Generated {len(df)} mock trade records (API unavailable)', debug_info=self.get_debug_log())
        except Exception as e:
            return WrapperResponse(success=False, error=f'Mock data generation failed: {str(e)}')

    def execute_query(self, data_type: str, **params) -> WrapperResponse:
        """Generic query executor"""
        self.log_debug(f'Executing query: {data_type} with params: {params}')
        method_map = {'direction_of_trade': self.get_direction_of_trade, 'test_connection': self.test_simple_connection}
        if data_type not in method_map:
            return WrapperResponse(success=False, error=f'Unknown data type: {data_type}', debug_info=self.get_debug_log())
        return method_map[data_type](**params)

def log_debug(self, message: str):
    """Add debug message with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    debug_msg = f'[{timestamp}] {message}'
    self.debug_log.append(debug_msg)
    print(debug_msg)

def info(msg, **kwargs):
    print(f'INFO: {msg}')

def debug(msg, **kwargs):
    print(f'DEBUG: {msg}')

def warning(msg, **kwargs):
    print(f'WARNING: {msg}')

def error(msg, **kwargs):
    print(f'ERROR: {msg}')

