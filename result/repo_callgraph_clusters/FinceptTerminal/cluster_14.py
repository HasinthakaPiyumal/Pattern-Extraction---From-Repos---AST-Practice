# Cluster 14

class SECDataUI:
    """DearPyGUI Interface for SEC Data"""

    def __init__(self):
        self.api = SECDataAPI()
        self.current_data = None

    def setup_ui(self):
        """Setup the main UI"""
        dpg.create_context()
        with dpg.window(label='SEC Data Terminal', tag='main_window'):
            dpg.add_text('🟢 Using Working SEC Headers', color=(0, 255, 0))
            dpg.add_separator()
            with dpg.tab_bar():
                with dpg.tab(label='CIK Map'):
                    dpg.add_text('Convert Symbol to CIK')
                    dpg.add_input_text(label='Symbol', tag='cik_symbol', default_value='TSLA')
                    dpg.add_button(label='Get CIK', callback=self.get_cik_callback)
                    dpg.add_text('', tag='cik_result')
                with dpg.tab(label='Company Filings'):
                    dpg.add_text('Get SEC Filings for Company')
                    dpg.add_input_text(label='Symbol', tag='filing_symbol', default_value='TSLA')
                    dpg.add_input_text(label='Form Type (optional)', tag='filing_form', default_value='10-K,10-Q')
                    dpg.add_input_int(label='Limit', tag='filing_limit', default_value=10)
                    dpg.add_button(label='Get Filings', callback=self.get_filings_callback)
                    with dpg.child_window(height=300, tag='filings_table'):
                        dpg.add_text('Filings will appear here...')
                with dpg.tab(label='Company Facts'):
                    dpg.add_text('Compare Company Facts')
                    dpg.add_input_text(label='Symbol (optional)', tag='facts_symbol', default_value='TSLA')
                    dpg.add_input_text(label='Fact', tag='facts_fact', default_value='Revenues')
                    dpg.add_input_int(label='Year (optional)', tag='facts_year', default_value=0)
                    dpg.add_button(label='Get Facts', callback=self.get_facts_callback)
                    with dpg.child_window(height=300, tag='facts_table'):
                        dpg.add_text('Facts will appear here...')
                with dpg.tab(label='Fails to Deliver'):
                    dpg.add_text('Get Fails-to-Deliver Data')
                    dpg.add_input_text(label='Symbol', tag='ftd_symbol', default_value='TSLA')
                    dpg.add_input_int(label='Reports Limit', tag='ftd_limit', default_value=12)
                    dpg.add_button(label='Get FTD Data', callback=self.get_ftd_callback)
                    with dpg.child_window(height=300, tag='ftd_table'):
                        dpg.add_text('FTD data will appear here...')
                with dpg.tab(label='Equity Search'):
                    dpg.add_text('Search Companies')
                    dpg.add_input_text(label='Search Query', tag='search_query', default_value='Tesla')
                    dpg.add_checkbox(label='Search Funds', tag='search_funds', default_value=False)
                    dpg.add_button(label='Search', callback=self.search_callback)
                    with dpg.child_window(height=300, tag='search_table'):
                        dpg.add_text('Search results will appear here...')
        dpg.create_viewport(title='SEC Data Terminal', width=1000, height=700)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window('main_window', True)

    def get_cik_callback(self):
        """Callback for CIK mapping"""
        symbol = dpg.get_value('cik_symbol')

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.api.get_cik_map(symbol))
                if 'error' in result:
                    dpg.set_value('cik_result', f'Error: {result['error']}')
                else:
                    dpg.set_value('cik_result', f'Symbol: {result['symbol']} -> CIK: {result['cik']}')
            finally:
                loop.close()
        import threading
        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

    def get_filings_callback(self):
        """Callback for company filings"""
        symbol = dpg.get_value('filing_symbol')
        form_type = dpg.get_value('filing_form') or None
        limit = dpg.get_value('filing_limit')

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.api.get_company_filings(symbol=symbol, form_type=form_type, limit=limit))
                dpg.delete_item('filings_table', children_only=True)
                if 'error' in result:
                    dpg.add_text(f'Error: {result['error']}', parent='filings_table')
                else:
                    dpg.add_text(f'Company: {result['company_name']} (CIK: {result['cik']})', parent='filings_table')
                    dpg.add_separator(parent='filings_table')
                    filings = result['filings'][:10]
                    for filing in filings:
                        filing_text = f'Form: {filing.get('form', 'N/A')} | Date: {filing.get('filingDate', 'N/A')} | Document: {filing.get('primaryDocument', 'N/A')}'
                        dpg.add_text(filing_text, parent='filings_table')
            finally:
                loop.close()
        import threading
        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

    def get_facts_callback(self):
        """Callback for company facts"""
        symbol = dpg.get_value('facts_symbol') or None
        fact = dpg.get_value('facts_fact')
        year = dpg.get_value('facts_year') or None

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.api.get_compare_company_facts(symbol=symbol, fact=fact, year=year))
                dpg.delete_item('facts_table', children_only=True)
                if 'error' in result:
                    dpg.add_text(f'Error: {result['error']}', parent='facts_table')
                else:
                    metadata = result['metadata']
                    dpg.add_text(f'Fact: {metadata.get('fact', 'N/A')}', parent='facts_table')
                    if 'company' in metadata:
                        dpg.add_text(f'Company: {metadata['company']}', parent='facts_table')
                    dpg.add_separator(parent='facts_table')
                    data = result['data'][:15]
                    for item in data:
                        if symbol:
                            fact_text = f'Value: {item.get('val', 'N/A')} | Period: {item.get('end', 'N/A')} | Filed: {item.get('filed', 'N/A')}'
                        else:
                            fact_text = f'Company: {item.get('symbol', 'N/A')} | Value: {item.get('val', 'N/A')}'
                        dpg.add_text(fact_text, parent='facts_table')
            finally:
                loop.close()
        import threading
        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

    def get_ftd_callback(self):
        """Callback for FTD data"""
        symbol = dpg.get_value('ftd_symbol')
        limit = dpg.get_value('ftd_limit')

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.api.get_equity_ftd(symbol, limit))
                dpg.delete_item('ftd_table', children_only=True)
                if 'error' in result:
                    dpg.add_text(f'Error: {result['error']}', parent='ftd_table')
                else:
                    dpg.add_text(f'Symbol: {result['symbol']} | Total Records: {result['count']}', parent='ftd_table')
                    dpg.add_separator(parent='ftd_table')
                    data = result['data'][:20]
                    for item in data:
                        ftd_text = f'Date: {item.get('date', 'N/A')} | Quantity: {item.get('quantity', 'N/A')} | Price: ${item.get('price', 'N/A')}'
                        dpg.add_text(ftd_text, parent='ftd_table')
            finally:
                loop.close()
        import threading
        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

    def search_callback(self):
        """Callback for equity search"""
        query = dpg.get_value('search_query')
        is_fund = dpg.get_value('search_funds')

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.api.get_equity_search(query, is_fund))
                dpg.delete_item('search_table', children_only=True)
                if 'error' in result:
                    dpg.add_text(f'Error: {result['error']}', parent='search_table')
                else:
                    dpg.add_text(f"Query: '{result['query']}' | Results: {result['count']}", parent='search_table')
                    dpg.add_separator(parent='search_table')
                    data = result['data'][:15]
                    for item in data:
                        if is_fund:
                            search_text = f'Symbol: {item.get('symbol', 'N/A')} | CIK: {item.get('cik', 'N/A')}'
                        else:
                            search_text = f'Symbol: {item.get('symbol', 'N/A')} | Name: {item.get('name', 'N/A')} | CIK: {item.get('cik', 'N/A')}'
                        dpg.add_text(search_text, parent='search_table')
            finally:
                loop.close()
        import threading
        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

    def run(self):
        """Run the application"""
        self.setup_ui()
        dpg.start_dearpygui()
        dpg.destroy_context()

def __init__(self):
    self.api = SECDataAPI()
    self.current_data = None

