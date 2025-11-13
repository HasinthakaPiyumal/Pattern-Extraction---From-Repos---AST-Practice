# Cluster 206

class SECDataAPI:
    """SEC Data API Wrapper for first 5 endpoints"""

    def __init__(self):
        self.cache_dir = './cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        self.working_headers = {'User-Agent': 'my real company name definitelynot@fakecompany.com', 'Accept-Encoding': 'gzip, deflate'}

    async def _make_request(self, url: str, headers: dict=None, use_cache: bool=True) -> Union[dict, str]:
        """Make HTTP request with optional caching"""
        if headers is None:
            headers = self.working_headers
        print(f'Making request to: {url}')
        try:
            if use_cache and CACHE_AVAILABLE:
                async with CachedSession(cache=SQLiteBackend(f'{self.cache_dir}/http_cache', expire_after=3600 * 24)) as session:
                    try:
                        async with session.get(url, headers=headers) as response:
                            print(f'Response status: {response.status}')
                            response.raise_for_status()
                            content_type = response.headers.get('Content-Type', '')
                            print(f'Content-Type: {content_type}')
                            if 'application/json' in content_type:
                                result = await response.json()
                                print(f'JSON Response keys: {(list(result.keys()) if isinstance(result, dict) else 'Not a dict')}')
                                print(f'JSON Response sample: {str(result)[:200]}...')
                                return result
                            else:
                                text_result = await response.text()
                                print(f'Text Response length: {len(text_result)}')
                                return text_result
                    finally:
                        await session.close()
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        print(f'Response status: {response.status}')
                        response.raise_for_status()
                        content_type = response.headers.get('Content-Type', '')
                        print(f'Content-Type: {content_type}')
                        if 'application/json' in content_type:
                            result = await response.json()
                            print(f'JSON Response keys: {(list(result.keys()) if isinstance(result, dict) else 'Not a dict')}')
                            print(f'JSON Response sample: {str(result)[:200]}...')
                            return result
                        else:
                            text_result = await response.text()
                            print(f'Text Response length: {len(text_result)}')
                            return text_result
        except aiohttp.ClientResponseError as e:
            print(f'HTTP Error {e.status}: {e.message} for URL: {url}')
            raise Exception(f'HTTP {e.status}: {e.message}')
        except Exception as e:
            print(f'Request failed for {url}: {str(e)}')
            raise

    async def get_cik_map(self, symbol: str, use_cache: bool=True) -> dict:
        """Convert symbol to CIK number"""
        try:
            print(f'Looking up CIK for symbol: {symbol}')
            cik = await symbol_map(symbol.upper(), use_cache)
            print(f'Found CIK: {cik}')
            return {'symbol': symbol.upper(), 'cik': cik if cik else 'Not Found'}
        except Exception as e:
            print(f'Error in get_cik_map: {str(e)}')
            return {'error': str(e)}

    async def get_company_filings(self, symbol: str=None, cik: str=None, form_type: str=None, limit: int=100, use_cache: bool=True) -> dict:
        """Get company SEC filings"""
        try:
            print(f'Getting filings for symbol: {symbol}, cik: {cik}')
            if symbol and (not cik):
                cik = await symbol_map(symbol.upper(), use_cache)
                print(f'Mapped symbol {symbol} to CIK: {cik}')
                if not cik:
                    return {'error': f'CIK not found for symbol {symbol}'}
            if not cik:
                return {'error': 'CIK or symbol must be provided'}
            cik_clean = str(cik).lstrip('0')
            cik_padded = cik_clean.zfill(10)
            print(f'CIK clean: {cik_clean}, CIK padded: {cik_padded}')
            url = f'https://data.sec.gov/submissions/CIK{cik_padded}.json'
            response = await self._make_request(url, use_cache=use_cache)
            if isinstance(response, dict) and 'filings' in response:
                filings = pd.DataFrame(response['filings']['recent'])
                print(f'Found {len(filings)} total filings')
                if form_type:
                    form_types = form_type.replace('_', ' ').split(',')
                    filings = filings[filings['form'].str.contains('|'.join(form_types), case=False, na=False)]
                    print(f'After form type filter: {len(filings)} filings')
                if limit:
                    filings = filings.head(limit)
                base_url = f'https://www.sec.gov/Archives/edgar/data/{cik_clean}/'
                filings['report_url'] = base_url + filings['accessionNumber'].str.replace('-', '') + '/' + filings['primaryDocument']
                return {'company_name': response.get('name', ''), 'cik': cik_padded, 'filings': filings.to_dict('records')}
            print(f'Response structure: {type(response)}, keys: {(response.keys() if isinstance(response, dict) else 'Not dict')}')
            return {'error': 'No filings data found'}
        except Exception as e:
            print(f'Error in get_company_filings: {str(e)}')
            return {'error': str(e)}

    async def get_compare_company_facts(self, symbol: str=None, fact: str='Revenues', year: int=None, use_cache: bool=True) -> dict:
        """Get company facts for comparison"""
        try:
            print(f'Getting facts for symbol: {symbol}, fact: {fact}, year: {year}')
            if not symbol:
                current_year = datetime.now().year if not year else year
                quarter = (datetime.now().month - 1) // 3 + 1
                urls_to_try = [f'https://data.sec.gov/api/xbrl/frames/us-gaap/{fact}/USD/CY{current_year}Q{quarter}.json', f'https://data.sec.gov/api/xbrl/frames/us-gaap/{fact}/USD/CY{current_year}.json', f'https://data.sec.gov/api/xbrl/frames/us-gaap/{fact}/USD/CY{current_year}Q{quarter}I.json']
                response = None
                for i, url in enumerate(urls_to_try):
                    try:
                        print(f'Trying URL {i + 1}/3: {url}')
                        response = await self._make_request(url, use_cache=use_cache)
                        if isinstance(response, dict) and 'data' in response:
                            print(f'Success with URL {i + 1}')
                            break
                    except Exception as e:
                        print(f'Failed URL {i + 1}: {str(e)}')
                        continue
                if response and isinstance(response, dict) and ('data' in response):
                    companies = await get_all_companies(use_cache)
                    cik_to_symbol = companies.set_index('cik')['symbol'].to_dict()
                    data = response['data']
                    for item in data:
                        item['symbol'] = cik_to_symbol.get(str(int(item['cik'])), '')
                        item['fact'] = fact
                    print(f'Found {len(data)} companies with {fact} data')
                    return {'metadata': {'fact': fact, 'year': current_year, 'quarter': quarter, 'label': response.get('label', ''), 'count': len(data)}, 'data': sorted(data, key=lambda x: x.get('val', 0), reverse=True)[:50]}
            else:
                cik = await symbol_map(symbol.upper(), use_cache)
                print(f'Mapped {symbol} to CIK: {cik}')
                if not cik:
                    return {'error': f'CIK not found for symbol {symbol}'}
                cik_clean = str(cik).lstrip('0')
                cik_padded = cik_clean.zfill(10)
                print(f'Using CIK: {cik_padded}')
                url = f'https://data.sec.gov/api/xbrl/companyconcept/CIK{cik_padded}/us-gaap/{fact}.json'
                response = await self._make_request(url, use_cache=use_cache)
                if isinstance(response, dict) and 'units' in response:
                    units = response['units']
                    all_data = []
                    print(f'Found units: {list(units.keys())}')
                    for unit, values in units.items():
                        for item in values:
                            item.update({'unit': unit, 'symbol': symbol.upper(), 'cik': cik_padded, 'fact': response.get('label', fact)})
                            all_data.append(item)
                    if year:
                        all_data = [d for d in all_data if str(d.get('fy')) == str(year)]
                        print(f'After year filter: {len(all_data)} records')
                    return {'metadata': {'company': response.get('entityName', ''), 'cik': cik_padded, 'symbol': symbol.upper(), 'fact': response.get('label', fact)}, 'data': sorted(all_data, key=lambda x: x.get('filed', ''), reverse=True)}
                else:
                    print(f'Response keys: {(response.keys() if isinstance(response, dict) else 'Not dict')}')
            return {'error': 'No data found'}
        except Exception as e:
            print(f'Error in get_compare_company_facts: {str(e)}')
            return {'error': str(e)}

    async def get_equity_ftd(self, symbol: str, limit: int=24, use_cache: bool=True) -> dict:
        """Get fails-to-deliver data for a symbol"""
        try:
            urls_data = await get_ftd_urls()
            urls = list(urls_data.values())
            if limit > 0:
                urls = urls[:limit]
            results = []
            for url in urls:
                data = await download_zip_file(url, symbol.upper(), use_cache)
                results.extend(data)
            if not results:
                return {'error': f'No FTD data found for {symbol}'}
            results = sorted(results, key=lambda d: d.get('date', ''), reverse=True)
            return {'symbol': symbol.upper(), 'count': len(results), 'data': results}
        except Exception as e:
            return {'error': str(e)}

    async def get_equity_search(self, query: str, is_fund: bool=False, use_cache: bool=True) -> dict:
        """Search for companies by name/symbol"""
        try:
            if is_fund:
                companies = await get_mf_and_etf_map(use_cache)
                results = companies[companies['cik'].str.contains(query, case=False, na=False) | companies['seriesId'].str.contains(query, case=False, na=False) | companies['classId'].str.contains(query, case=False, na=False) | companies['symbol'].str.contains(query, case=False, na=False)]
            else:
                companies = await get_all_companies(use_cache)
                results = companies[companies['name'].str.contains(query, case=False, na=False) | companies['symbol'].str.contains(query, case=False, na=False) | companies['cik'].str.contains(query, case=False, na=False)]
            return {'query': query, 'is_fund': is_fund, 'count': len(results), 'data': results.to_dict('records')}
        except Exception as e:
            return {'error': str(e)}

def __init__(self):
    self.cache_dir = './cache'
    os.makedirs(self.cache_dir, exist_ok=True)
    self.working_headers = {'User-Agent': 'my real company name definitelynot@fakecompany.com', 'Accept-Encoding': 'gzip, deflate'}

