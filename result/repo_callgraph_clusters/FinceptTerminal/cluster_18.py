# Cluster 18

def get_access_token() -> Dict[str, Any]:
    """
    Get OAuth2 access token using client credentials

    Returns:
        Dict with access token or error information
    """
    try:
        client_id = os.environ.get('SENTINELHUB_CLIENT_ID')
        client_secret = os.environ.get('SENTINELHUB_CLIENT_SECRET')
        if not client_id or not client_secret:
            return {'error': 'Missing Sentinel Hub credentials. Set SENTINELHUB_CLIENT_ID and SENTINELHUB_CLIENT_SECRET environment variables.'}
        auth_string = f'{client_id}:{client_secret}'
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/x-www-form-urlencoded'}
        data = 'grant_type=client_credentials'
        response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=TIMEOUT)
        response.raise_for_status()
        token_data = response.json()
        return {'access_token': token_data.get('access_token'), 'expires_in': token_data.get('expires_in'), 'token_type': token_data.get('token_type'), 'error': None}
    except requests.exceptions.HTTPError as e:
        error_msg = f'Authentication failed: {e.response.status_code}'
        if e.response.status_code == 401:
            error_msg = 'Invalid client credentials'
        elif e.response.status_code == 403:
            error_msg = 'Access forbidden'
        return {'error': f'{error_msg}: {str(e)}'}
    except requests.exceptions.Timeout:
        return {'error': 'Authentication timeout'}
    except requests.exceptions.ConnectionError:
        return {'error': 'Connection error during authentication'}
    except Exception as e:
        return {'error': f'Authentication error: {str(e)}'}

def _make_process_request(process_params: Dict[str, Any], save_to_file: bool=False) -> Dict[str, Any]:
    """
    Centralized request handler for Process API

    Args:
        process_params: Process parameters for the Process API
        save_to_file: Whether to save the image to a temporary file

    Returns:
        Dict with 'data', 'metadata', and 'error' keys
    """
    try:
        headers = get_auth_headers()
        if 'error' in headers:
            return {'data': {}, 'metadata': {}, 'error': headers['error']}
        process_headers = headers.copy()
        process_headers['Accept'] = 'image/*'
        response = requests.post(PROCESS_API_URL, headers=process_headers, json=process_params, timeout=TIMEOUT)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        if save_to_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(response.content)
                file_path = tmp_file.name
            return {'data': {'image_file': file_path, 'content_type': content_type, 'size_bytes': len(response.content)}, 'metadata': {'source': 'Sentinel Hub Process API', 'process_params': process_params, 'timestamp': datetime.utcnow().isoformat(), 'description': 'Processed satellite image saved to file'}, 'error': None}
        else:
            image_b64 = base64.b64encode(response.content).decode('utf-8')
            return {'data': {'image_base64': image_b64, 'content_type': content_type, 'size_bytes': len(response.content)}, 'metadata': {'source': 'Sentinel Hub Process API', 'process_params': process_params, 'timestamp': datetime.utcnow().isoformat(), 'description': 'Processed satellite image (base64 encoded)'}, 'error': None}
    except requests.exceptions.HTTPError as e:
        error_msg = f'Process API Error {e.response.status_code}'
        if e.response.status_code == 401:
            error_msg = 'Authentication expired - please check credentials'
        elif e.response.status_code == 400:
            error_msg = 'Invalid process parameters'
        elif e.response.status_code == 429:
            error_msg = 'Rate limit exceeded - please try again later'
        return {'data': {}, 'metadata': {}, 'error': f'{error_msg}: {str(e)}'}
    except requests.exceptions.Timeout:
        return {'data': {}, 'metadata': {}, 'error': 'Process API timeout - image processing took too long'}
    except Exception as e:
        return {'data': {}, 'metadata': {}, 'error': f'Process API error: {str(e)}'}

def explore_raw_data():
    """Explore the raw Databento data file"""
    try:
        raw_data_file = 'databento_raw_data.bin'
        records = []
        with open(raw_data_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    records.append({'line_number': line_num, 'raw_content': line})
        if not records:
            return {'success': False, 'error': 'No data found in the raw data file'}
        analysis = {'total_records': len(records), 'file_size_bytes': len(open(raw_data_file, 'rb').read()), 'sample_records': records[:5], 'last_few_records': records[-3:]}
        record_types = {}
        symbol_counts = {}
        action_types = {}
        side_types = {}
        price_ranges = []
        sample_size = min(100, len(records))
        parsed_records = []
        for i, record in enumerate(records[:sample_size]):
            content = record['raw_content']
            parsed = {'line_number': record['line_number'], 'raw_content': content}
            if 'Msg' in content:
                msg_type = re.search('(\\w+Msg)', content)
                if msg_type:
                    parsed['message_type'] = msg_type.group(1)
                    record_types[parsed['message_type']] = record_types.get(parsed['message_type'], 0) + 1
            symbol_match = re.search('symbol=([^\\s,\\)]+)', content)
            if symbol_match:
                symbol = symbol_match.group(1)
                parsed['symbol'] = symbol
                if symbol != 'None':
                    symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            action_match = re.search('action=([A-Za-z])', content)
            if action_match:
                action = action_match.group(1)
                parsed['action'] = action
                action_types[action] = action_types.get(action, 0) + 1
            side_match = re.search('side=([A-Za-z])', content)
            if side_match:
                side = side_match.group(1)
                parsed['side'] = side
                side_types[side] = side_types.get(side, 0) + 1
            price_match = re.search('price=([\\d.]+)', content)
            if price_match:
                price = float(price_match.group(1))
                parsed['price'] = price
                price_ranges.append(price)
            size_match = re.search('size=(\\d+)', content)
            if size_match:
                size = int(size_match.group(1))
                parsed['size'] = size
            ts_match = re.search('ts_event=(\\d+)', content)
            if ts_match:
                timestamp = int(ts_match.group(1))
                parsed['timestamp_ns'] = timestamp
                parsed['timestamp_readable'] = datetime.fromtimestamp(timestamp / 1000000000).strftime('%Y-%m-%d %H:%M:%S.%f')
            parsed_records.append(parsed)
        stats = {'record_types': record_types, 'unique_symbols': list(symbol_counts.keys()), 'symbol_counts': symbol_counts, 'action_types': action_types, 'side_types': side_types}
        if price_ranges:
            stats['price_statistics'] = {'min_price': min(price_ranges), 'max_price': max(price_ranges), 'avg_price': sum(price_ranges) / len(price_ranges), 'total_records_with_price': len(price_ranges)}
        timestamps = [r['timestamp_ns'] for r in parsed_records if 'timestamp_ns' in r]
        if timestamps:
            stats['time_range'] = {'start_time': datetime.fromtimestamp(min(timestamps) / 1000000000).strftime('%Y-%m-%d %H:%M:%S.%f'), 'end_time': datetime.fromtimestamp(max(timestamps) / 1000000000).strftime('%Y-%m-%d %H:%M:%S.%f'), 'duration_seconds': (max(timestamps) - min(timestamps)) / 1000000000}
        return {'success': True, 'file_analysis': analysis, 'parsed_records_sample': parsed_records[:10], 'statistics': stats, 'exploration_summary': f'File contains {len(records)} records with {len(record_types)} different message types'}
    except Exception as e:
        return {'success': False, 'error': str(e), 'message': 'Failed to explore raw data file'}

class VisualizationEngine(EconomicsBase):
    """Advanced visualization for economic analysis"""

    def __init__(self, precision: int=8):
        super().__init__(precision)
        self.default_figsize = (12, 8)
        self.color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    def plot_time_series(self, data: pd.DataFrame, title: str='Time Series Analysis', figsize: tuple=None) -> Dict[str, Any]:
        """Create professional time series plots"""
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValidationError('Data must have datetime index')
        figsize = figsize or self.default_figsize
        fig, axes = plt.subplots(2, 2, figsize=(figsize[0], figsize[1] * 1.2))
        fig.suptitle(title, fontsize=16, fontweight='bold')
        ax1 = axes[0, 0]
        for i, col in enumerate(data.columns[:5]):
            ax1.plot(data.index, data[col], label=col, color=self.color_palette[i % len(self.color_palette)], linewidth=2)
        ax1.set_title('Time Series Data')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax2 = axes[0, 1]
        returns = data.pct_change().dropna()
        if not returns.empty:
            ax2.plot(returns.index, returns.iloc[:, 0], color=self.color_palette[0], linewidth=1, alpha=0.7)
            ax2.set_title('Returns')
            ax2.grid(True, alpha=0.3)
        ax3 = axes[1, 0]
        if not returns.empty:
            ax3.hist(returns.iloc[:, 0].dropna(), bins=30, alpha=0.7, color=self.color_palette[0], edgecolor='black')
            ax3.set_title('Returns Distribution')
            ax3.set_xlabel('Returns')
            ax3.set_ylabel('Frequency')
        ax4 = axes[1, 1]
        try:
            from statsmodels.tsa.stattools import acf
            if len(data.iloc[:, 0].dropna()) > 20:
                lags = min(20, len(data) // 4)
                autocorr = acf(data.iloc[:, 0].dropna(), nlags=lags)
                ax4.bar(range(len(autocorr)), autocorr, alpha=0.7, color=self.color_palette[0])
                ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                ax4.set_title('Autocorrelation')
                ax4.set_xlabel('Lags')
        except ImportError:
            ax4.text(0.5, 0.5, 'Autocorrelation\nrequires statsmodels', ha='center', va='center', transform=ax4.transAxes)
        plt.tight_layout()
        return {'figure': fig, 'plot_type': 'time_series'}

    def plot_correlation_matrix(self, corr_matrix: pd.DataFrame, title: str='Correlation Matrix') -> Dict[str, Any]:
        """Create correlation heatmap"""
        fig, ax = plt.subplots(figsize=self.default_figsize)
        sns.heatmap(corr_matrix, annot=True, cmap='RdYlBu_r', center=0, square=True, fmt='.2f', cbar_kws={'label': 'Correlation'})
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        return {'figure': fig, 'plot_type': 'correlation_heatmap'}

    def plot_economic_indicators(self, data: Dict[str, pd.Series], title: str='Economic Indicators') -> Dict[str, Any]:
        """Plot multiple economic indicators with subplots"""
        n_indicators = len(data)
        if n_indicators == 0:
            raise ValidationError('No data provided')
        if n_indicators <= 2:
            rows, cols = (1, n_indicators)
        elif n_indicators <= 4:
            rows, cols = (2, 2)
        else:
            rows, cols = (3, 3)
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4))
        if n_indicators == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        fig.suptitle(title, fontsize=16, fontweight='bold')
        for i, (indicator, series) in enumerate(data.items()):
            if i >= len(axes):
                break
            ax = axes[i]
            ax.plot(series.index, series.values, color=self.color_palette[i % len(self.color_palette)], linewidth=2)
            ax.set_title(indicator)
            ax.grid(True, alpha=0.3)
            if len(series) > 2:
                z = np.polyfit(range(len(series)), series.values, 1)
                trend = np.poly1d(z)
                ax.plot(series.index, trend(range(len(series))), '--', alpha=0.7, color='red', linewidth=1)
        for i in range(n_indicators, len(axes)):
            axes[i].set_visible(False)
        plt.tight_layout()
        return {'figure': fig, 'plot_type': 'economic_indicators'}

    def plot_forecast(self, historical: pd.Series, forecast: List[float], confidence_intervals: Optional[Dict[str, List[float]]]=None, title: str='Forecast Analysis') -> Dict[str, Any]:
        """Plot forecast with confidence intervals"""
        fig, ax = plt.subplots(figsize=self.default_figsize)
        ax.plot(historical.index, historical.values, label='Historical', color=self.color_palette[0], linewidth=2)
        last_date = historical.index[-1]
        if isinstance(last_date, pd.Timestamp):
            freq = pd.infer_freq(historical.index) or 'D'
            forecast_index = pd.date_range(start=last_date + pd.Timedelta(freq), periods=len(forecast), freq=freq)
        else:
            forecast_index = range(len(historical), len(historical) + len(forecast))
        ax.plot(forecast_index, forecast, label='Forecast', color=self.color_palette[1], linewidth=2, linestyle='--')
        if confidence_intervals:
            lower = confidence_intervals.get('lower', [])
            upper = confidence_intervals.get('upper', [])
            if len(lower) == len(forecast) and len(upper) == len(forecast):
                ax.fill_between(forecast_index, lower, upper, alpha=0.3, color=self.color_palette[1], label='95% CI')
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return {'figure': fig, 'plot_type': 'forecast'}

def plot_time_series(self, data: pd.DataFrame, title: str='Time Series Analysis', figsize: tuple=None) -> Dict[str, Any]:
    """Create professional time series plots"""
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValidationError('Data must have datetime index')
    figsize = figsize or self.default_figsize
    fig, axes = plt.subplots(2, 2, figsize=(figsize[0], figsize[1] * 1.2))
    fig.suptitle(title, fontsize=16, fontweight='bold')
    ax1 = axes[0, 0]
    for i, col in enumerate(data.columns[:5]):
        ax1.plot(data.index, data[col], label=col, color=self.color_palette[i % len(self.color_palette)], linewidth=2)
    ax1.set_title('Time Series Data')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax2 = axes[0, 1]
    returns = data.pct_change().dropna()
    if not returns.empty:
        ax2.plot(returns.index, returns.iloc[:, 0], color=self.color_palette[0], linewidth=1, alpha=0.7)
        ax2.set_title('Returns')
        ax2.grid(True, alpha=0.3)
    ax3 = axes[1, 0]
    if not returns.empty:
        ax3.hist(returns.iloc[:, 0].dropna(), bins=30, alpha=0.7, color=self.color_palette[0], edgecolor='black')
        ax3.set_title('Returns Distribution')
        ax3.set_xlabel('Returns')
        ax3.set_ylabel('Frequency')
    ax4 = axes[1, 1]
    try:
        from statsmodels.tsa.stattools import acf
        if len(data.iloc[:, 0].dropna()) > 20:
            lags = min(20, len(data) // 4)
            autocorr = acf(data.iloc[:, 0].dropna(), nlags=lags)
            ax4.bar(range(len(autocorr)), autocorr, alpha=0.7, color=self.color_palette[0])
            ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax4.set_title('Autocorrelation')
            ax4.set_xlabel('Lags')
    except ImportError:
        ax4.text(0.5, 0.5, 'Autocorrelation\nrequires statsmodels', ha='center', va='center', transform=ax4.transAxes)
    plt.tight_layout()
    return {'figure': fig, 'plot_type': 'time_series'}

def plot_correlation_matrix(self, corr_matrix: pd.DataFrame, title: str='Correlation Matrix') -> Dict[str, Any]:
    """Create correlation heatmap"""
    fig, ax = plt.subplots(figsize=self.default_figsize)
    sns.heatmap(corr_matrix, annot=True, cmap='RdYlBu_r', center=0, square=True, fmt='.2f', cbar_kws={'label': 'Correlation'})
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    return {'figure': fig, 'plot_type': 'correlation_heatmap'}

def plot_economic_indicators(self, data: Dict[str, pd.Series], title: str='Economic Indicators') -> Dict[str, Any]:
    """Plot multiple economic indicators with subplots"""
    n_indicators = len(data)
    if n_indicators == 0:
        raise ValidationError('No data provided')
    if n_indicators <= 2:
        rows, cols = (1, n_indicators)
    elif n_indicators <= 4:
        rows, cols = (2, 2)
    else:
        rows, cols = (3, 3)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4))
    if n_indicators == 1:
        axes = [axes]
    elif rows == 1 or cols == 1:
        axes = axes.flatten()
    else:
        axes = axes.flatten()
    fig.suptitle(title, fontsize=16, fontweight='bold')
    for i, (indicator, series) in enumerate(data.items()):
        if i >= len(axes):
            break
        ax = axes[i]
        ax.plot(series.index, series.values, color=self.color_palette[i % len(self.color_palette)], linewidth=2)
        ax.set_title(indicator)
        ax.grid(True, alpha=0.3)
        if len(series) > 2:
            z = np.polyfit(range(len(series)), series.values, 1)
            trend = np.poly1d(z)
            ax.plot(series.index, trend(range(len(series))), '--', alpha=0.7, color='red', linewidth=1)
    for i in range(n_indicators, len(axes)):
        axes[i].set_visible(False)
    plt.tight_layout()
    return {'figure': fig, 'plot_type': 'economic_indicators'}

def plot_forecast(self, historical: pd.Series, forecast: List[float], confidence_intervals: Optional[Dict[str, List[float]]]=None, title: str='Forecast Analysis') -> Dict[str, Any]:
    """Plot forecast with confidence intervals"""
    fig, ax = plt.subplots(figsize=self.default_figsize)
    ax.plot(historical.index, historical.values, label='Historical', color=self.color_palette[0], linewidth=2)
    last_date = historical.index[-1]
    if isinstance(last_date, pd.Timestamp):
        freq = pd.infer_freq(historical.index) or 'D'
        forecast_index = pd.date_range(start=last_date + pd.Timedelta(freq), periods=len(forecast), freq=freq)
    else:
        forecast_index = range(len(historical), len(historical) + len(forecast))
    ax.plot(forecast_index, forecast, label='Forecast', color=self.color_palette[1], linewidth=2, linestyle='--')
    if confidence_intervals:
        lower = confidence_intervals.get('lower', [])
        upper = confidence_intervals.get('upper', [])
        if len(lower) == len(forecast) and len(upper) == len(forecast):
            ax.fill_between(forecast_index, lower, upper, alpha=0.3, color=self.color_palette[1], label='95% CI')
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return {'figure': fig, 'plot_type': 'forecast'}

class WikipediaTab(BaseTab):

    def __init__(self, app):
        super().__init__(app)
        self.ORANGE = [255, 165, 0]
        self.WHITE = [255, 255, 255]
        self.GREEN = [0, 200, 0]
        self.BLUE = [0, 128, 255]
        self.GRAY = [120, 120, 120]
        self.YELLOW = [255, 255, 0]
        self.RED = [255, 100, 100]
        self.loading = False
        self.loaded_images = {}
        self.current_article = None
        self.search_history = []
        self.bookmarked_articles = []
        self._search_cache = {}
        self._article_cache = {}
        wikipedia.set_lang('en')
        info('Wikipedia tab initialized', context={'language': 'en'})

    def get_label(self):
        return 'Wikipedia'

    def create_content(self):
        """Create Wikipedia interface content"""
        try:
            self.add_section_header('📚 Wikipedia Search & Research')
            self.create_status_panel()
            dpg.add_spacer(height=10)
            self.create_search_panel()
            dpg.add_spacer(height=15)
            self.create_main_layout()
            info('Wikipedia tab content created successfully')
        except Exception as e:
            error('Error creating Wikipedia tab content', context={'error': str(e)}, exc_info=True)
            dpg.add_text('Error loading Wikipedia interface', color=self.RED)
            dpg.add_button(label='Retry', callback=lambda: self.create_content())

    def create_status_panel(self):
        """Show Wikipedia status and statistics"""
        with dpg.group():
            dpg.add_text('📊 Wikipedia Status:', color=self.YELLOW)
            with dpg.group(horizontal=True):
                dpg.add_text('Language: English', color=self.GRAY)
                dpg.add_spacer(width=20)
                dpg.add_text('Articles Searched: 0', tag='search_count', color=self.GRAY)
                dpg.add_spacer(width=20)
                dpg.add_text('Current Article: None', tag='current_article_status', color=self.GRAY)
                dpg.add_spacer(width=20)
                dpg.add_text('Bookmarks: 0', tag='bookmark_count', color=self.GRAY)

    def create_search_panel(self):
        """Create search controls and options"""
        with dpg.group(horizontal=True):
            dpg.add_text('🔍 Search:', color=self.ORANGE)
            dpg.add_input_text(hint='Enter search term...', width=400, tag='wiki_search_input', callback=self.on_search_enter, on_enter=True)
            dpg.add_button(label='Search', width=80, callback=self.execute_search)
            dpg.add_button(label='Clear', width=60, callback=self.clear_search)
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            dpg.add_text('Quick:', color=self.YELLOW)
            for term in ['Technology', 'Science', 'History', 'Finance', 'Medicine', 'Geography']:
                dpg.add_button(label=term, width=80, callback=lambda s, a, t=term: self.quick_search(t))
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label='Auto-load images', tag='auto_load_images', default_value=True)
            dpg.add_spacer(width=20)
            dpg.add_combo(['English', 'Spanish', 'French', 'German', 'Italian'], default_value='English', tag='wiki_language', callback=self.on_language_changed, width=100)
            dpg.add_spacer(width=20)
            dpg.add_button(label='📖 History', callback=self.show_search_history)
            dpg.add_button(label='⭐ Bookmarks', callback=self.show_bookmarks)
            dpg.add_button(label='📤 Export', callback=self.export_article)

    def create_main_layout(self):
        """Create the main 20-60-20 layout"""
        usable_width, content_height = self.get_dimensions()
        results_width, article_width, suggestions_width = self.calculate_panel_widths()
        with dpg.group(horizontal=True):
            self.create_results_panel(results_width, content_height)
            dpg.add_spacer(width=2)
            self.create_article_panel(article_width, content_height)
            dpg.add_spacer(width=2)
            self.create_suggestions_panel(suggestions_width, content_height)

    def get_dimensions(self):
        """Get proper dimensions with padding consideration"""
        try:
            viewport_width = dpg.get_viewport_width()
            viewport_height = dpg.get_viewport_height()
        except:
            viewport_width = 1200
            viewport_height = 800
        usable_width = viewport_width - 40
        content_height = viewport_height - 200
        return (usable_width, content_height)

    def calculate_panel_widths(self):
        """Calculate exact panel widths to prevent overflow"""
        usable_width, _ = self.get_dimensions()
        border_space = 6
        gap_space = 4
        available_width = usable_width - border_space - gap_space
        results_width = int(available_width * 0.2)
        article_width = int(available_width * 0.6)
        suggestions_width = available_width - results_width - article_width
        return (results_width, article_width, suggestions_width)

    def create_results_panel(self, width, height):
        """Create search results panel"""
        with self.create_child_window(tag='results_panel', width=width, height=height):
            dpg.add_text('🔍 SEARCH RESULTS', color=self.ORANGE)
            dpg.add_separator()
            dpg.add_text('Enter search term to begin', tag='results_status', color=self.GRAY)
            dpg.add_child_window(height=-1, border=False, tag='results_list')

    def create_article_panel(self, width, height):
        """Create article content panel"""
        with self.create_child_window(tag='article_panel', width=width, height=height):
            dpg.add_text('📄 ARTICLE CONTENT', color=self.ORANGE)
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_text('Select an article from results', tag='article_title', color=self.WHITE)
                dpg.add_spacer(width=20)
                dpg.add_button(label='⭐', width=30, tag='bookmark_btn', callback=self.bookmark_article, show=False)
                dpg.add_button(label='🔗', width=30, tag='open_web_btn', callback=self.open_in_browser, show=False)
            dpg.add_separator()
            dpg.add_child_window(height=-1, border=False, tag='article_content')

    def create_suggestions_panel(self, width, height):
        """Create suggestions and tools panel"""
        with self.create_child_window(tag='suggestions_panel', width=width, height=height):
            dpg.add_text('🔗 RELATED & TOOLS', color=self.ORANGE)
            dpg.add_separator()
            dpg.add_text('📊 Article Stats:', color=self.YELLOW)
            dpg.add_text('Word count: 0', tag='word_count', color=self.GRAY)
            dpg.add_text('Read time: 0 min', tag='read_time', color=self.GRAY)
            dpg.add_text('Last updated: N/A', tag='last_updated', color=self.GRAY)
            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_text('Related articles will appear here', tag='suggestions_status', color=self.GRAY)
            dpg.add_child_window(height=-1, border=False, tag='suggestions_list')

    def on_search_enter(self, sender, app_data):
        """Handle search input enter key"""
        self.execute_search()

    def quick_search(self, term):
        """Execute quick search for predefined terms"""
        dpg.set_value('wiki_search_input', term)
        self.execute_search()
        debug(f'Quick search executed: {term}')

    def clear_search(self):
        """Clear search input and results"""
        dpg.set_value('wiki_search_input', '')
        dpg.delete_item('results_list', children_only=True)
        dpg.set_value('results_status', 'Search cleared')
        info('Search cleared')

    @monitor_performance
    def execute_search(self):
        """Execute Wikipedia search with threading and caching"""
        if self.loading:
            warning('Search already in progress')
            return
        search_term = dpg.get_value('wiki_search_input')
        if not search_term or not search_term.strip():
            dpg.set_value('results_status', '⚠️ Please enter a search term')
            return

        def search_thread():
            try:
                self.loading = True
                with operation('wikipedia_search', context={'search_term': search_term}):
                    dpg.set_value('results_status', f"🔍 Searching '{search_term}'...")
                    dpg.delete_item('results_list', children_only=True)
                    dpg.delete_item('suggestions_list', children_only=True)
                    dpg.set_value('suggestions_status', 'Search for an article first')
                    cache_key = search_term.lower()
                    if cache_key in self._search_cache:
                        cached_time, cached_results = self._search_cache[cache_key]
                        if datetime.now().timestamp() - cached_time < 600:
                            results = cached_results
                            info('Wikipedia search loaded from cache', context={'search_term': search_term, 'results_count': len(results)})
                        else:
                            del self._search_cache[cache_key]
                            results = None
                    else:
                        results = None
                    if results is None:
                        results = wikipedia.search(search_term, results=15)
                        self._search_cache[cache_key] = (datetime.now().timestamp(), results)
                    if search_term not in self.search_history:
                        self.search_history.append(search_term)
                        if len(self.search_history) > 20:
                            self.search_history.pop(0)
                    if results:
                        dpg.set_value('results_status', f'✅ Found {len(results)} results')
                        for i, result in enumerate(results):
                            self.create_result_item(result, i)
                        current_count = len(self.search_history)
                        dpg.set_value('search_count', f'Articles Searched: {current_count}')
                        info('Wikipedia search completed successfully', context={'search_term': search_term, 'results_count': len(results)})
                    else:
                        dpg.set_value('results_status', '❌ No results found')
                        info('Wikipedia search returned no results', context={'search_term': search_term})
            except wikipedia.exceptions.DisambiguationError as e:
                dpg.set_value('results_status', '🔀 Multiple matches found')
                dpg.delete_item('results_list', children_only=True)
                for i, option in enumerate(e.options[:15]):
                    self.create_result_item(option, i)
                info('Wikipedia disambiguation handled', context={'search_term': search_term, 'options_count': len(e.options[:15])})
            except Exception as e:
                error_msg = f'❌ Search error: {str(e)[:30]}'
                dpg.set_value('results_status', error_msg)
                error('Wikipedia search error', context={'search_term': search_term, 'error': str(e)}, exc_info=True)
            finally:
                self.loading = False
        threading.Thread(target=search_thread, daemon=True).start()
        info(f'Wikipedia search started', context={'search_term': search_term})

    def create_result_item(self, title, index):
        """Create search result item"""
        with dpg.group(parent='results_list'):
            display_title = f'{index + 1}. {title}'
            dpg.add_button(label=display_title, callback=lambda: self.load_article(title), width=-1, height=40)
            dpg.add_spacer(height=3)

    @monitor_performance
    def load_article(self, title):
        """Load Wikipedia article with comprehensive error handling and caching"""
        if self.loading:
            warning('Article loading already in progress')
            return

        def load_thread():
            try:
                self.loading = True
                self.current_article = title
                with operation('load_wikipedia_article', context={'title': title}):
                    dpg.set_value('article_title', f'📄 Loading {title}...')
                    dpg.delete_item('article_content', children_only=True)
                    dpg.set_value('current_article_status', f'Current Article: {title[:30]}...')
                    cache_key = title.lower()
                    if cache_key in self._article_cache:
                        cached_time, cached_page = self._article_cache[cache_key]
                        if datetime.now().timestamp() - cached_time < 1800:
                            page = cached_page
                            info('Wikipedia article loaded from cache', context={'title': title})
                        else:
                            del self._article_cache[cache_key]
                            page = None
                    else:
                        page = None
                    if page is None:
                        try:
                            page = wikipedia.page(title)
                        except wikipedia.exceptions.DisambiguationError as e:
                            page = wikipedia.page(e.options[0])
                            info('Wikipedia disambiguation resolved', context={'original_title': title, 'resolved_title': e.options[0]})
                        except wikipedia.exceptions.PageError:
                            search_results = wikipedia.search(title, results=1)
                            if search_results:
                                page = wikipedia.page(search_results[0])
                                info('Wikipedia page found via search', context={'original_title': title, 'found_title': search_results[0]})
                            else:
                                raise
                        self._article_cache[cache_key] = (datetime.now().timestamp(), page)
                    dpg.set_value('article_title', f'📄 {page.title}')
                    dpg.configure_item('bookmark_btn', show=True)
                    dpg.configure_item('open_web_btn', show=True)
                    self.current_page_url = page.url
                    dpg.delete_item('article_content', children_only=True)
                    with dpg.group(parent='article_content'):
                        dpg.add_text('📊 Article Information:', color=self.BLUE)
                        dpg.add_text(f'URL: {page.url}', color=self.WHITE, wrap=0)
                        content_length = len(page.content)
                        word_count = len(page.content.split())
                        read_time = max(1, word_count // 200)
                        dpg.set_value('word_count', f'Word count: {word_count:,}')
                        dpg.set_value('read_time', f'Read time: {read_time} min')
                        dpg.add_spacer(height=10)
                        if dpg.get_value('auto_load_images'):
                            self.load_main_image(page)
                        dpg.add_text('📝 SUMMARY', color=self.YELLOW)
                        try:
                            summary = wikipedia.summary(page.title, sentences=4)
                            dpg.add_text(summary, color=self.WHITE, wrap=0)
                        except:
                            dpg.add_text('Summary not available', color=self.GRAY)
                        dpg.add_spacer(height=15)
                        dpg.add_text('📖 FULL CONTENT', color=self.YELLOW)
                        self.process_content(page)
                        self.load_suggestions(page)
                    info('Wikipedia article loaded successfully', context={'title': page.title, 'word_count': word_count, 'read_time': read_time})
            except Exception as e:
                dpg.delete_item('article_content', children_only=True)
                with dpg.group(parent='article_content'):
                    dpg.add_text(f'❌ Error loading article: {str(e)}', color=self.RED)
                error('Error loading Wikipedia article', context={'title': title, 'error': str(e)}, exc_info=True)
            finally:
                self.loading = False
        threading.Thread(target=load_thread, daemon=True).start()
        info(f'Wikipedia article loading started', context={'title': title})

    def load_suggestions(self, page):
        """Load related articles and categories with error handling"""
        try:
            dpg.delete_item('suggestions_list', children_only=True)
            dpg.set_value('suggestions_status', 'Loading related content...')
            with dpg.group(parent='suggestions_list'):
                if hasattr(page, 'links') and page.links:
                    dpg.add_text('🔗 RELATED ARTICLES', color=self.GREEN)
                    dpg.add_separator()
                    for i, link in enumerate(page.links[:10]):
                        dpg.add_button(label=link, callback=lambda l=link: self.load_article(l), width=-1, height=35)
                        dpg.add_spacer(height=3)
                dpg.add_spacer(height=10)
                if hasattr(page, 'categories') and page.categories:
                    dpg.add_text('📂 CATEGORIES', color=self.YELLOW)
                    dpg.add_separator()
                    for category in page.categories[:8]:
                        cat_name = category.replace('Category:', '')
                        dpg.add_text(f'• {cat_name}', color=self.WHITE, wrap=0)
                        dpg.add_spacer(height=3)
            dpg.set_value('suggestions_status', '✅ Related content loaded')
            debug('Wikipedia suggestions loaded successfully', context={'links_count': len(page.links[:10]) if hasattr(page, 'links') and page.links else 0, 'categories_count': len(page.categories[:8]) if hasattr(page, 'categories') and page.categories else 0})
        except Exception as e:
            dpg.set_value('suggestions_status', '❌ No suggestions available')
            error('Error loading Wikipedia suggestions', context={'error': str(e)}, exc_info=True)

    def load_main_image(self, page):
        """Load and display main image with caching"""
        try:
            if hasattr(page, 'images') and page.images:
                for img_url in page.images[:3]:
                    if self.is_suitable_image(img_url):
                        dpg.add_text('🖼️ FEATURED IMAGE', color=self.GREEN)
                        _, article_width, _ = self.calculate_panel_widths()
                        max_img_width = min(400, article_width - 40)
                        self.load_and_display_image(img_url, max_img_width, 250)
                        dpg.add_spacer(height=10)
                        break
        except Exception as e:
            error('Error loading Wikipedia image', context={'error': str(e)}, exc_info=True)

    def is_suitable_image(self, img_url):
        """Check if image is suitable for display"""
        if not img_url:
            return False
        unsuitable = ['.svg', 'commons-logo', 'edit-icon', 'wikimedia', 'mediawiki']
        img_lower = img_url.lower()
        if any((pattern in img_lower for pattern in unsuitable)):
            return False
        return any((fmt in img_lower for fmt in ['.jpg', '.jpeg', '.png', '.gif', '.webp']))

    def load_and_display_image(self, img_url, max_width=400, max_height=250):
        """Load and display image with caching and error handling"""
        try:
            if img_url in self.loaded_images:
                texture_tag = self.loaded_images[img_url]
                if dpg.does_item_exist(texture_tag):
                    dpg.add_image(texture_tag)
                    return
            response = requests.get(img_url, timeout=5, stream=True)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content)).convert('RGBA')
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            img_array = np.array(img)
            img_flat = img_array.flatten().astype(np.float32) / 255.0
            texture_tag = f'wiki_img_texture_{len(self.loaded_images)}'
            if not dpg.does_item_exist('texture_registry'):
                dpg.add_texture_registry(tag='texture_registry')
            dpg.add_static_texture(width=img.width, height=img.height, default_value=img_flat, tag=texture_tag, parent='texture_registry')
            self.loaded_images[img_url] = texture_tag
            dpg.add_image(texture_tag)
            dpg.add_text(f'Size: {img.width}x{img.height}', color=self.GRAY)
            debug('Wikipedia image loaded successfully', context={'img_url': img_url[:100], 'size': f'{img.width}x{img.height}'})
        except Exception as e:
            dpg.add_text('❌ Failed to load image', color=self.RED)
            error('Error loading Wikipedia image', context={'img_url': img_url[:100], 'error': str(e)}, exc_info=True)

    def process_content(self, page):
        """Process and display article content with error handling"""
        try:
            content = page.content
            paragraphs = content.split('\n\n')
            displayed_count = 0
            for paragraph in paragraphs:
                if paragraph.strip() and displayed_count < 12:
                    if paragraph.startswith('==') and paragraph.endswith('=='):
                        section = paragraph.replace('=', '').strip()
                        dpg.add_spacer(height=10)
                        dpg.add_text(f'📋 {section.upper()}', color=self.ORANGE)
                        dpg.add_separator()
                    else:
                        clean = paragraph.strip()
                        if len(clean) > 30:
                            dpg.add_text(clean, color=self.WHITE, wrap=0)
                            dpg.add_spacer(height=8)
                            displayed_count += 1
                            if displayed_count >= 10:
                                dpg.add_text('... [Content truncated for display] ...', color=self.GRAY)
                                break
        except Exception as e:
            dpg.add_text('❌ Content not available', color=self.GRAY)
            error('Error processing Wikipedia content', context={'error': str(e)}, exc_info=True)

    def on_language_changed(self, sender, app_data):
        """Handle language change"""
        lang_map = {'English': 'en', 'Spanish': 'es', 'French': 'fr', 'German': 'de', 'Italian': 'it'}
        lang_code = lang_map.get(app_data, 'en')
        wikipedia.set_lang(lang_code)
        self._search_cache.clear()
        self._article_cache.clear()
        info(f'Wikipedia language changed', context={'language': app_data, 'code': lang_code})

    def bookmark_article(self):
        """Bookmark current article"""
        if self.current_article:
            if self.current_article not in self.bookmarked_articles:
                self.bookmarked_articles.append(self.current_article)
                dpg.set_value('bookmark_count', f'Bookmarks: {len(self.bookmarked_articles)}')
                info(f'Article bookmarked', context={'title': self.current_article})
            else:
                info(f'Article already bookmarked', context={'title': self.current_article})

    def open_in_browser(self):
        """Open current article in web browser"""
        if hasattr(self, 'current_page_url'):
            try:
                webbrowser.open(self.current_page_url)
                info(f'Article opened in browser', context={'url': self.current_page_url})
            except Exception as e:
                error('Failed to open article in browser', context={'url': self.current_page_url, 'error': str(e)}, exc_info=True)

    def show_search_history(self):
        """Show search history"""
        history_count = len(self.search_history)
        info('Search history requested', context={'history_count': history_count})

    def show_bookmarks(self):
        """Show bookmarked articles"""
        bookmarks_count = len(self.bookmarked_articles)
        info('Bookmarks requested', context={'bookmarks_count': bookmarks_count})

    def export_article(self):
        """Export current article"""
        if self.current_article:
            info(f'Article export requested', context={'title': self.current_article})

    def update_layout(self):
        """Update layout on window resize"""
        try:
            _, content_height = self.get_dimensions()
            results_width, article_width, suggestions_width = self.calculate_panel_widths()
            if dpg.does_item_exist('results_panel'):
                dpg.configure_item('results_panel', width=results_width, height=content_height)
            if dpg.does_item_exist('article_panel'):
                dpg.configure_item('article_panel', width=article_width, height=content_height)
            if dpg.does_item_exist('suggestions_panel'):
                dpg.configure_item('suggestions_panel', width=suggestions_width, height=content_height)
        except Exception as e:
            error('Error updating Wikipedia layout', context={'error': str(e)}, exc_info=True)

    def cleanup(self):
        """Clean up Wikipedia tab resources"""
        try:
            info('Starting Wikipedia tab cleanup')
            for texture_tag in self.loaded_images.values():
                if dpg.does_item_exist(texture_tag):
                    dpg.delete_item(texture_tag)
            self.loaded_images.clear()
            self._search_cache.clear()
            self._article_cache.clear()
            self.search_history.clear()
            self.bookmarked_articles.clear()
            self.current_article = None
            info('Wikipedia tab cleanup completed', context={'images_cleared': len(self.loaded_images), 'history_items': len(self.search_history), 'bookmarks': len(self.bookmarked_articles)})
        except Exception as e:
            error('Error during Wikipedia cleanup', context={'error': str(e)}, exc_info=True)

def load_and_display_image(self, img_url, max_width=400, max_height=250):
    """Load and display image with caching and error handling"""
    try:
        if img_url in self.loaded_images:
            texture_tag = self.loaded_images[img_url]
            if dpg.does_item_exist(texture_tag):
                dpg.add_image(texture_tag)
                return
        response = requests.get(img_url, timeout=5, stream=True)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content)).convert('RGBA')
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        img_array = np.array(img)
        img_flat = img_array.flatten().astype(np.float32) / 255.0
        texture_tag = f'wiki_img_texture_{len(self.loaded_images)}'
        if not dpg.does_item_exist('texture_registry'):
            dpg.add_texture_registry(tag='texture_registry')
        dpg.add_static_texture(width=img.width, height=img.height, default_value=img_flat, tag=texture_tag, parent='texture_registry')
        self.loaded_images[img_url] = texture_tag
        dpg.add_image(texture_tag)
        dpg.add_text(f'Size: {img.width}x{img.height}', color=self.GRAY)
        debug('Wikipedia image loaded successfully', context={'img_url': img_url[:100], 'size': f'{img.width}x{img.height}'})
    except Exception as e:
        dpg.add_text('❌ Failed to load image', color=self.RED)
        error('Error loading Wikipedia image', context={'img_url': img_url[:100], 'error': str(e)}, exc_info=True)

class AdvancedPlottingEngine:
    """Professional charting and visualization engine"""

    @staticmethod
    def create_comprehensive_chart(data: pd.DataFrame, indicators: Dict[str, pd.DataFrame], signals: Optional[pd.DataFrame]=None, equity_curve: Optional[pd.Series]=None) -> str:
        """Create comprehensive trading chart"""
        fig, axes = plt.subplots(4, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        ax1 = axes[0]
        ax1.plot(data.index, data['Close'], label='Close', color='black', linewidth=1.5)
        colors = ['blue', 'red', 'green', 'orange', 'purple']
        for i, (name, indicator_data) in enumerate(indicators.items()):
            if 'MA' in name or 'EMA' in name or 'SMA' in name:
                if isinstance(indicator_data, pd.DataFrame):
                    for col in indicator_data.columns[:1]:
                        ax1.plot(data.index, indicator_data[col], label=col, color=colors[i % len(colors)], alpha=0.7)
                elif isinstance(indicator_data, pd.Series):
                    ax1.plot(data.index, indicator_data, label=name, color=colors[i % len(colors)], alpha=0.7)
        if signals is not None and (not signals.empty):
            if 'buy_signals' in signals.columns:
                buy_points = data[signals['buy_signals']]
                ax1.scatter(buy_points.index, buy_points['Close'], color='green', marker='^', s=100, zorder=5, label='Buy')
            if 'sell_signals' in signals.columns:
                sell_points = data[signals['sell_signals']]
                ax1.scatter(sell_points.index, sell_points['Close'], color='red', marker='v', s=100, zorder=5, label='Sell')
        ax1.set_title('Price Chart with Indicators', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=10)
        ax1.legend(loc='upper left', fontsize=8)
        ax1.grid(True, alpha=0.3)
        ax2 = axes[1]
        volume_colors = ['green' if data['Close'].iloc[i] >= data['Open'].iloc[i] else 'red' for i in range(len(data))]
        ax2.bar(data.index, data['Volume'], color=volume_colors, alpha=0.5)
        ax2.set_ylabel('Volume', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax3 = axes[2]
        for name, indicator_data in indicators.items():
            if 'RSI' in name:
                if isinstance(indicator_data, pd.DataFrame):
                    ax3.plot(data.index, indicator_data.iloc[:, 0], label='RSI', color='purple')
                elif isinstance(indicator_data, pd.Series):
                    ax3.plot(data.index, indicator_data, label='RSI', color='purple')
                ax3.axhline(y=70, color='r', linestyle='--', alpha=0.5)
                ax3.axhline(y=30, color='g', linestyle='--', alpha=0.5)
                ax3.set_ylabel('RSI', fontsize=10)
                ax3.set_ylim(0, 100)
                ax3.grid(True, alpha=0.3)
                break
        ax4 = axes[3]
        if equity_curve is not None:
            ax4.plot(equity_curve.index, equity_curve.values, label='Portfolio Value', color='blue')
            ax4.fill_between(equity_curve.index, equity_curve.values, alpha=0.3)
            ax4.set_ylabel('Portfolio Value', fontsize=10)
            ax4.set_xlabel('Date', fontsize=10)
            ax4.grid(True, alpha=0.3)
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        return image_base64

    @staticmethod
    def create_performance_dashboard(metrics: PortfolioMetrics, equity_curve: pd.Series, trades: pd.DataFrame) -> str:
        """Create comprehensive performance dashboard"""
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(equity_curve.index, equity_curve.values, color='blue', linewidth=2)
        ax1.fill_between(equity_curve.index, equity_curve.values, alpha=0.3)
        ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax2 = fig.add_subplot(gs[1, :])
        rolling_max = equity_curve.expanding().max()
        drawdown = (equity_curve - rolling_max) / rolling_max * 100
        ax2.fill_between(drawdown.index, drawdown.values, color='red', alpha=0.3)
        ax2.plot(drawdown.index, drawdown.values, color='red', linewidth=1)
        ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax3 = fig.add_subplot(gs[2, 0])
        if not trades.empty and 'return' in trades.columns:
            returns = trades['return'].dropna() * 100
            ax3.hist(returns, bins=30, color='blue', alpha=0.7, edgecolor='black')
            ax3.axvline(x=0, color='red', linestyle='--')
            ax3.set_title('Returns Distribution', fontsize=12)
            ax3.set_xlabel('Return (%)', fontsize=10)
            ax3.set_ylabel('Frequency', fontsize=10)
        ax4 = fig.add_subplot(gs[2, 1])
        sizes = [metrics.winning_trades, metrics.losing_trades]
        labels = [f'Wins ({metrics.winning_trades})', f'Losses ({metrics.losing_trades})']
        colors = ['green', 'red']
        if sum(sizes) > 0:
            ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax4.set_title('Win/Loss Ratio', fontsize=12)
        ax5 = fig.add_subplot(gs[2, 2])
        if len(equity_curve) > 30:
            monthly_returns = equity_curve.resample('M').last().pct_change() * 100
            monthly_data = monthly_returns.values.reshape(-1, 1)
            im = ax5.imshow(monthly_data, cmap='RdYlGn', aspect='auto', vmin=-10, vmax=10)
            ax5.set_title('Monthly Returns', fontsize=12)
            ax5.set_ylabel('Month', fontsize=10)
            plt.colorbar(im, ax=ax5)
        ax6 = fig.add_subplot(gs[3, :])
        ax6.axis('tight')
        ax6.axis('off')
        metrics_data = [['Total Return', f'{metrics.total_return:.2f}%', 'Sharpe Ratio', f'{metrics.sharpe_ratio:.2f}'], ['Annual Return', f'{metrics.annualized_return:.2f}%', 'Sortino Ratio', f'{metrics.sortino_ratio:.2f}'], ['Max Drawdown', f'{metrics.max_drawdown:.2f}%', 'Calmar Ratio', f'{metrics.calmar_ratio:.2f}'], ['Win Rate', f'{metrics.win_rate:.2f}%', 'Profit Factor', f'{metrics.profit_factor:.2f}'], ['Total Trades', f'{metrics.total_trades}', 'Avg Win', f'{metrics.avg_win:.2f}%'], ['Best Trade', f'{metrics.best_trade:.2f}%', 'Worst Trade', f'{metrics.worst_trade:.2f}%']]
        table = ax6.table(cellText=metrics_data, cellLoc='center', loc='center', colWidths=[0.2, 0.3, 0.2, 0.3])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)
        for i in range(len(metrics_data)):
            for j in range(4):
                cell = table[i, j]
                if j % 2 == 0:
                    cell.set_facecolor('#E8E8E8')
                else:
                    cell.set_facecolor('#F5F5F5')
        plt.suptitle('Performance Dashboard', fontsize=16, fontweight='bold')
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        return image_base64

@staticmethod
def create_comprehensive_chart(data: pd.DataFrame, indicators: Dict[str, pd.DataFrame], signals: Optional[pd.DataFrame]=None, equity_curve: Optional[pd.Series]=None) -> str:
    """Create comprehensive trading chart"""
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1, 1, 1]})
    ax1 = axes[0]
    ax1.plot(data.index, data['Close'], label='Close', color='black', linewidth=1.5)
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    for i, (name, indicator_data) in enumerate(indicators.items()):
        if 'MA' in name or 'EMA' in name or 'SMA' in name:
            if isinstance(indicator_data, pd.DataFrame):
                for col in indicator_data.columns[:1]:
                    ax1.plot(data.index, indicator_data[col], label=col, color=colors[i % len(colors)], alpha=0.7)
            elif isinstance(indicator_data, pd.Series):
                ax1.plot(data.index, indicator_data, label=name, color=colors[i % len(colors)], alpha=0.7)
    if signals is not None and (not signals.empty):
        if 'buy_signals' in signals.columns:
            buy_points = data[signals['buy_signals']]
            ax1.scatter(buy_points.index, buy_points['Close'], color='green', marker='^', s=100, zorder=5, label='Buy')
        if 'sell_signals' in signals.columns:
            sell_points = data[signals['sell_signals']]
            ax1.scatter(sell_points.index, sell_points['Close'], color='red', marker='v', s=100, zorder=5, label='Sell')
    ax1.set_title('Price Chart with Indicators', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Price', fontsize=10)
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax2 = axes[1]
    volume_colors = ['green' if data['Close'].iloc[i] >= data['Open'].iloc[i] else 'red' for i in range(len(data))]
    ax2.bar(data.index, data['Volume'], color=volume_colors, alpha=0.5)
    ax2.set_ylabel('Volume', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax3 = axes[2]
    for name, indicator_data in indicators.items():
        if 'RSI' in name:
            if isinstance(indicator_data, pd.DataFrame):
                ax3.plot(data.index, indicator_data.iloc[:, 0], label='RSI', color='purple')
            elif isinstance(indicator_data, pd.Series):
                ax3.plot(data.index, indicator_data, label='RSI', color='purple')
            ax3.axhline(y=70, color='r', linestyle='--', alpha=0.5)
            ax3.axhline(y=30, color='g', linestyle='--', alpha=0.5)
            ax3.set_ylabel('RSI', fontsize=10)
            ax3.set_ylim(0, 100)
            ax3.grid(True, alpha=0.3)
            break
    ax4 = axes[3]
    if equity_curve is not None:
        ax4.plot(equity_curve.index, equity_curve.values, label='Portfolio Value', color='blue')
        ax4.fill_between(equity_curve.index, equity_curve.values, alpha=0.3)
        ax4.set_ylabel('Portfolio Value', fontsize=10)
        ax4.set_xlabel('Date', fontsize=10)
        ax4.grid(True, alpha=0.3)
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    return image_base64

@staticmethod
def create_performance_dashboard(metrics: PortfolioMetrics, equity_curve: pd.Series, trades: pd.DataFrame) -> str:
    """Create comprehensive performance dashboard"""
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(equity_curve.index, equity_curve.values, color='blue', linewidth=2)
    ax1.fill_between(equity_curve.index, equity_curve.values, alpha=0.3)
    ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax2 = fig.add_subplot(gs[1, :])
    rolling_max = equity_curve.expanding().max()
    drawdown = (equity_curve - rolling_max) / rolling_max * 100
    ax2.fill_between(drawdown.index, drawdown.values, color='red', alpha=0.3)
    ax2.plot(drawdown.index, drawdown.values, color='red', linewidth=1)
    ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Drawdown (%)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax3 = fig.add_subplot(gs[2, 0])
    if not trades.empty and 'return' in trades.columns:
        returns = trades['return'].dropna() * 100
        ax3.hist(returns, bins=30, color='blue', alpha=0.7, edgecolor='black')
        ax3.axvline(x=0, color='red', linestyle='--')
        ax3.set_title('Returns Distribution', fontsize=12)
        ax3.set_xlabel('Return (%)', fontsize=10)
        ax3.set_ylabel('Frequency', fontsize=10)
    ax4 = fig.add_subplot(gs[2, 1])
    sizes = [metrics.winning_trades, metrics.losing_trades]
    labels = [f'Wins ({metrics.winning_trades})', f'Losses ({metrics.losing_trades})']
    colors = ['green', 'red']
    if sum(sizes) > 0:
        ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax4.set_title('Win/Loss Ratio', fontsize=12)
    ax5 = fig.add_subplot(gs[2, 2])
    if len(equity_curve) > 30:
        monthly_returns = equity_curve.resample('M').last().pct_change() * 100
        monthly_data = monthly_returns.values.reshape(-1, 1)
        im = ax5.imshow(monthly_data, cmap='RdYlGn', aspect='auto', vmin=-10, vmax=10)
        ax5.set_title('Monthly Returns', fontsize=12)
        ax5.set_ylabel('Month', fontsize=10)
        plt.colorbar(im, ax=ax5)
    ax6 = fig.add_subplot(gs[3, :])
    ax6.axis('tight')
    ax6.axis('off')
    metrics_data = [['Total Return', f'{metrics.total_return:.2f}%', 'Sharpe Ratio', f'{metrics.sharpe_ratio:.2f}'], ['Annual Return', f'{metrics.annualized_return:.2f}%', 'Sortino Ratio', f'{metrics.sortino_ratio:.2f}'], ['Max Drawdown', f'{metrics.max_drawdown:.2f}%', 'Calmar Ratio', f'{metrics.calmar_ratio:.2f}'], ['Win Rate', f'{metrics.win_rate:.2f}%', 'Profit Factor', f'{metrics.profit_factor:.2f}'], ['Total Trades', f'{metrics.total_trades}', 'Avg Win', f'{metrics.avg_win:.2f}%'], ['Best Trade', f'{metrics.best_trade:.2f}%', 'Worst Trade', f'{metrics.worst_trade:.2f}%']]
    table = ax6.table(cellText=metrics_data, cellLoc='center', loc='center', colWidths=[0.2, 0.3, 0.2, 0.3])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    for i in range(len(metrics_data)):
        for j in range(4):
            cell = table[i, j]
            if j % 2 == 0:
                cell.set_facecolor('#E8E8E8')
            else:
                cell.set_facecolor('#F5F5F5')
    plt.suptitle('Performance Dashboard', fontsize=16, fontweight='bold')
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    return image_base64

class DashboardTab(BaseTab):
    """Bloomberg Terminal style Dashboard tab - With Real Data (Fast Loading)"""

    def __init__(self, main_app=None):
        super().__init__(main_app)
        try:
            with logger.operation('dashboard_tab_initialization'):
                info('Initializing Dashboard Tab')
                self.main_app = main_app
                self.BLOOMBERG_ORANGE = [255, 165, 0]
                self.BLOOMBERG_WHITE = [255, 255, 255]
                self.BLOOMBERG_RED = [255, 0, 0]
                self.BLOOMBERG_GREEN = [0, 200, 0]
                self.BLOOMBERG_YELLOW = [255, 255, 0]
                self.BLOOMBERG_GRAY = [120, 120, 120]
                self.last_update = None
                self.update_interval = 3600
                self.data_loading = False
                self._lock = threading.Lock()
                self.initialize_data()
                self.start_background_updates()
                info('Dashboard Tab initialized successfully', context={'yfinance_available': YFINANCE_AVAILABLE, 'feedparser_available': FEEDPARSER_AVAILABLE})
        except Exception as e:
            error('Dashboard Tab initialization failed', context={'error': str(e)}, exc_info=True)
            raise

    def get_label(self):
        return 'Dashboard'

    def safe_float_conversion(self, value: Any, default: float=0.0) -> float:
        """Safely convert value to float with encoding handling"""
        try:
            if value is None:
                return default
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='ignore')
            elif isinstance(value, str):
                value = ''.join((c for c in value if c.isdigit() or c in '.-'))
            return float(value) if value else default
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            warning(f'Error converting value to float', context={'value': str(value), 'error': str(e)})
            return default

    def safe_int_conversion(self, value: Any, default: int=0) -> int:
        """Safely convert value to int with encoding handling"""
        try:
            if value is None:
                return default
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='ignore')
            elif isinstance(value, str):
                value = ''.join((c for c in value if c.isdigit()))
            return int(float(value)) if value else default
        except (ValueError, TypeError, UnicodeDecodeError) as e:
            warning(f'Error converting value to int', context={'value': str(value), 'error': str(e)})
            return default

    @monitor_performance
    def get_stock_data_optimized(self, symbols: List[str], timeout: int=10) -> Dict[str, Dict[str, Any]]:
        """Optimized stock data fetch using yfinance history method and concurrent processing"""
        if not YFINANCE_AVAILABLE:
            debug('yfinance not available, using fallback data')
            return self.get_fallback_stock_data(symbols)
        result = {}

        def fetch_single_stock(symbol: str) -> tuple[str, Dict[str, Any]]:
            """Fetch data for a single stock symbol"""
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d', interval='1d', timeout=timeout)
                if hist.empty or len(hist) < 2:
                    warning(f'Insufficient data for {symbol}, using fallback')
                    return (symbol, self.get_fallback_stock_data([symbol])[symbol])
                current_data = hist.iloc[-1]
                prev_data = hist.iloc[-2]
                current_price = self.safe_float_conversion(current_data['Close'])
                prev_price = self.safe_float_conversion(prev_data['Close'])
                volume = self.safe_int_conversion(current_data['Volume'])
                high = self.safe_float_conversion(current_data['High'])
                low = self.safe_float_conversion(current_data['Low'])
                open_price = self.safe_float_conversion(current_data['Open'])
                change_val = current_price - prev_price
                change_pct = change_val / prev_price * 100 if prev_price != 0 else 0
                stock_data = {'price': round(current_price, 2), 'change_pct': round(change_pct, 2), 'change_val': round(change_val, 2), 'volume': volume, 'high': round(high, 2), 'low': round(low, 2), 'open': round(open_price, 2)}
                debug(f'Successfully fetched data for {symbol}', context={'price': current_price, 'change_pct': change_pct})
                return (symbol, stock_data)
            except Exception as e:
                warning(f'Error fetching data for {symbol}', context={'error': str(e)})
                return (symbol, self.get_fallback_stock_data([symbol])[symbol])
        try:
            with logger.operation('concurrent_stock_fetch'):
                info(f'Fetching stock data for {len(symbols)} symbols concurrently')
                with ThreadPoolExecutor(max_workers=min(10, len(symbols))) as executor:
                    future_to_symbol = {executor.submit(fetch_single_stock, symbol): symbol for symbol in symbols}
                    successful_fetches = 0
                    failed_fetches = 0
                    for future in as_completed(future_to_symbol, timeout=timeout + 5):
                        try:
                            symbol, data = future.result(timeout=5)
                            result[symbol] = data
                            successful_fetches += 1
                        except Exception as e:
                            symbol = future_to_symbol[future]
                            error(f'Failed to get data for {symbol}', context={'error': str(e)})
                            result[symbol] = self.get_fallback_stock_data([symbol])[symbol]
                            failed_fetches += 1
                info('Concurrent stock fetch completed', context={'successful': successful_fetches, 'failed': failed_fetches, 'success_rate': f'{successful_fetches / (successful_fetches + failed_fetches) * 100:.1f}%'})
        except Exception as e:
            error('Error in concurrent stock data fetch', context={'error': str(e)}, exc_info=True)
            return self.get_fallback_stock_data(symbols)
        for symbol in symbols:
            if symbol not in result:
                result[symbol] = self.get_fallback_stock_data([symbol])[symbol]
        return result

    def get_fallback_stock_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Generate realistic fallback stock data with proper encoding handling"""
        import random
        result = {}
        base_prices = {'AAPL': 175, 'MSFT': 420, 'AMZN': 155, 'GOOGL': 140, 'META': 485, 'TSLA': 250, 'NVDA': 875, 'JPM': 155, 'V': 265, 'JNJ': 165, 'BAC': 35, 'PG': 160, 'MA': 465, 'UNH': 525, 'HD': 385, 'INTC': 45, 'VZ': 40, 'DIS': 110, 'PYPL': 65, 'NFLX': 485}
        for symbol in symbols:
            try:
                if isinstance(symbol, bytes):
                    symbol = symbol.decode('utf-8', errors='ignore')
                base_price = base_prices.get(symbol, 100)
                change_pct = round(random.uniform(-2.5, 2.5), 2)
                price = round(base_price * (1 + change_pct / 100), 2)
                change_val = round(price * change_pct / 100, 2)
                result[symbol] = {'price': price, 'change_pct': change_pct, 'change_val': change_val, 'volume': random.randint(1000000, 50000000), 'high': round(price * 1.03, 2), 'low': round(price * 0.97, 2), 'open': round(price * 0.995, 2)}
            except Exception as e:
                error(f'Error generating fallback data for {symbol}', context={'error': str(e)}, exc_info=True)
                result[symbol] = {'price': 100.0, 'change_pct': 0.0, 'change_val': 0.0, 'volume': 1000000, 'high': 103.0, 'low': 97.0, 'open': 99.5}
        return result

    @monitor_performance
    def get_indices_data_optimized(self, timeout: int=10) -> Dict[str, Dict[str, float]]:
        """Optimized index data fetch with better error handling"""
        if not YFINANCE_AVAILABLE:
            debug('yfinance not available, using fallback indices data')
            return self.get_fallback_indices_data()
        symbols = ['^GSPC', '^DJI', '^IXIC', '^FTSE', '^GDAXI', '^N225']
        names = ['S&P 500', 'DOW JONES', 'NASDAQ', 'FTSE 100', 'DAX', 'NIKKEI 225']
        result = {}

        def fetch_single_index(symbol: str, name: str) -> tuple[str, Dict[str, float]]:
            """Fetch data for a single index"""
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d', interval='1d', timeout=timeout)
                if hist.empty or len(hist) < 2:
                    warning(f'Insufficient data for index {name}', context={'symbol': symbol})
                    fallback = self.get_fallback_indices_data()
                    return (name, fallback[name])
                current_value = self.safe_float_conversion(hist['Close'].iloc[-1])
                prev_value = self.safe_float_conversion(hist['Close'].iloc[-2])
                change_pct = (current_value - prev_value) / prev_value * 100 if prev_value != 0 else 0
                debug(f'Successfully fetched index data for {name}', context={'value': current_value, 'change': change_pct})
                return (name, {'value': round(current_value, 2), 'change': round(change_pct, 2)})
            except Exception as e:
                error(f'Error fetching index {name}', context={'symbol': symbol, 'error': str(e)})
                fallback = self.get_fallback_indices_data()
                return (name, fallback[name])
        try:
            with logger.operation('concurrent_indices_fetch'):
                info(f'Fetching indices data concurrently')
                with ThreadPoolExecutor(max_workers=6) as executor:
                    future_to_name = {executor.submit(fetch_single_index, symbol, name): name for symbol, name in zip(symbols, names)}
                    successful_fetches = 0
                    failed_fetches = 0
                    for future in as_completed(future_to_name, timeout=timeout + 5):
                        try:
                            name, data = future.result(timeout=5)
                            result[name] = data
                            successful_fetches += 1
                        except Exception as e:
                            name = future_to_name[future]
                            error(f'Failed to get index data for {name}', context={'error': str(e)})
                            fallback = self.get_fallback_indices_data()
                            result[name] = fallback[name]
                            failed_fetches += 1
                info('Indices data fetch completed', context={'successful': successful_fetches, 'failed': failed_fetches})
        except Exception as e:
            error('Error in concurrent index data fetch', context={'error': str(e)}, exc_info=True)
            return self.get_fallback_indices_data()
        return result

    def get_fallback_indices_data(self) -> Dict[str, Dict[str, float]]:
        """Generate realistic fallback indices data"""
        import random
        return {'S&P 500': {'value': round(5200 + random.uniform(-50, 50), 2), 'change': round(random.uniform(-1, 1), 2)}, 'DOW JONES': {'value': round(38500 + random.uniform(-200, 200), 2), 'change': round(random.uniform(-1, 1), 2)}, 'NASDAQ': {'value': round(16400 + random.uniform(-100, 100), 2), 'change': round(random.uniform(-1.5, 1.5), 2)}, 'FTSE 100': {'value': round(7600 + random.uniform(-50, 50), 2), 'change': round(random.uniform(-1, 1), 2)}, 'DAX': {'value': round(18200 + random.uniform(-100, 100), 2), 'change': round(random.uniform(-1, 1), 2)}, 'NIKKEI 225': {'value': round(35800 + random.uniform(-200, 200), 2), 'change': round(random.uniform(-1, 1), 2)}}

    @monitor_performance
    def get_news_optimized(self, timeout: int=15) -> List[str]:
        """Optimized news fetch with better encoding handling"""
        if not FEEDPARSER_AVAILABLE:
            debug('feedparser not available, using fallback news')
            return self.get_fallback_news()
        try:
            with logger.operation('news_fetch'):
                info('Fetching news headlines from multiple sources')
                feeds = ['https://feeds.finance.yahoo.com/rss/2.0/headline', 'https://www.cnbc.com/id/100003114/device/rss/rss.html', 'https://feeds.marketwatch.com/marketwatch/topstories/']
                news_headlines = []

                def fetch_feed(feed_url: str) -> List[str]:
                    """Fetch headlines from a single feed"""
                    try:
                        debug(f'Fetching from feed: {feed_url}')
                        feed = feedparser.parse(feed_url)
                        headlines = []
                        if feed.entries:
                            for entry in feed.entries[:3]:
                                try:
                                    title = entry.title.strip()
                                    if isinstance(title, bytes):
                                        title = title.decode('utf-8', errors='ignore')
                                    title = title.encode('ascii', errors='ignore').decode('ascii')
                                    if len(title) > 80:
                                        title = title[:77] + '...'
                                    if title:
                                        headlines.append(title)
                                except Exception as e:
                                    warning(f'Error processing news entry', context={'error': str(e)})
                                    continue
                        debug(f'Fetched {len(headlines)} headlines from feed')
                        return headlines
                    except Exception as e:
                        warning(f'Error parsing feed', context={'feed_url': feed_url, 'error': str(e)})
                        return []
                for feed_url in feeds:
                    try:
                        headlines = fetch_feed(feed_url)
                        news_headlines.extend(headlines)
                        if len(news_headlines) >= 6:
                            break
                    except Exception as e:
                        error(f'Error fetching from feed', context={'feed_url': feed_url, 'error': str(e)})
                        continue
                if not news_headlines:
                    warning('No news headlines fetched, using fallback')
                    return self.get_fallback_news()
                info(f'Successfully fetched {len(news_headlines)} news headlines')
                return news_headlines[:6]
        except Exception as e:
            error('Error fetching news', context={'error': str(e)}, exc_info=True)
            return self.get_fallback_news()

    def get_fallback_news(self) -> List[str]:
        """Fallback news headlines"""
        return ['Market Update: Fed maintains current interest rates amid economic stability', 'Tech stocks show strong performance during Q4 earnings season', 'Oil prices stabilize following recent OPEC+ production decisions', 'Treasury yields remain elevated on persistent inflation concerns', 'Consumer spending data indicates continued economic resilience', 'Global markets react positively to central bank policy updates']

    def initialize_data(self):
        """Initialize with fallback data for immediate display"""
        try:
            with logger.operation('data_initialization'):
                info('Initializing dashboard data')
                self.tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V', 'JNJ', 'BAC', 'PG', 'MA', 'UNH', 'HD', 'INTC', 'VZ', 'DIS', 'PYPL', 'NFLX']
                with self._lock:
                    self.stock_data = self.get_fallback_stock_data(self.tickers)
                    self.indices = self.get_fallback_indices_data()
                    self.news_headlines = self.get_fallback_news()
                self.economic_indicators = {'US 10Y Treasury': {'value': 4.35, 'change': 0.05}, 'US GDP Growth': {'value': 2.8, 'change': 0.1}, 'US Unemployment': {'value': 3.6, 'change': -0.1}, 'EUR/USD': {'value': 1.084, 'change': -0.002}, 'Gold': {'value': 2312.8, 'change': 15.6}, 'WTI Crude': {'value': 78.35, 'change': -1.25}}
                info('Dashboard data initialized successfully', context={'stocks_count': len(self.stock_data), 'indices_count': len(self.indices), 'news_count': len(self.news_headlines)})
        except Exception as e:
            error('Failed to initialize dashboard data', context={'error': str(e)}, exc_info=True)

    def should_update_data(self) -> bool:
        """Check if data should be updated (every hour)"""
        if self.last_update is None:
            debug('No previous update, data refresh needed')
            return True
        time_since_update = time.time() - self.last_update
        should_update = time_since_update >= self.update_interval
        if should_update:
            debug(f'Update interval exceeded', context={'hours_since_update': time_since_update / 3600})
        return should_update

    @monitor_performance
    def update_data_background(self):
        """Update data in background thread with optimizations"""
        if self.data_loading:
            debug('Data update already in progress, skipping')
            return

        def fetch_all_data():
            try:
                with logger.operation('background_data_update'):
                    with self._lock:
                        self.data_loading = True
                    info('Starting optimized background data update')
                    stock_data = self.get_stock_data_optimized(self.tickers, timeout=15)
                    indices_data = self.get_indices_data_optimized(timeout=15)
                    news_data = self.get_news_optimized(timeout=15)
                    with self._lock:
                        self.stock_data.update(stock_data)
                        self.indices = indices_data
                        self.news_headlines = news_data
                        self.last_update = time.time()
                    info('Optimized background data update completed successfully')
            except Exception as e:
                error('Error in background data update', context={'error': str(e)}, exc_info=True)
            finally:
                with self._lock:
                    self.data_loading = False
        thread = threading.Thread(target=fetch_all_data, daemon=True, name='DashboardDataUpdater')
        thread.start()

    def start_background_updates(self):
        """Start the background update system with better scheduling"""
        try:
            info('Starting background update system')

            def update_loop():
                try:
                    time.sleep(2)
                    self.update_data_background()
                    while True:
                        time.sleep(300)
                        if self.should_update_data() and (not self.data_loading):
                            info('Starting scheduled hourly data update')
                            self.update_data_background()
                except Exception as e:
                    error('Error in background update loop', context={'error': str(e)}, exc_info=True)
            update_thread = threading.Thread(target=update_loop, daemon=True, name='DashboardUpdateLoop')
            update_thread.start()
            info('Background update system started successfully')
        except Exception as e:
            error('Failed to start background update system', context={'error': str(e)}, exc_info=True)

    def safe_text_display(self, text: Any) -> str:
        """Safely display text with encoding handling"""
        try:
            if isinstance(text, bytes):
                return text.decode('utf-8', errors='ignore')
            elif isinstance(text, (int, float)):
                return str(text)
            elif text is None:
                return ''
            else:
                return str(text).encode('ascii', errors='ignore').decode('ascii')
        except Exception as e:
            warning(f'Error displaying text', context={'error': str(e)})
            return 'N/A'

    @monitor_performance
    def create_content(self):
        """Create the Bloomberg Terminal layout with error handling"""
        try:
            with logger.operation('create_dashboard_content'):
                info('Creating dashboard tab content')
                with dpg.group(horizontal=True):
                    dpg.add_text('FINCEPT', color=self.BLOOMBERG_ORANGE)
                    dpg.add_text('PROFESSIONAL', color=self.BLOOMBERG_WHITE)
                    dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                    dpg.add_input_text(label='', default_value='Enter Command', width=300)
                    dpg.add_button(label='Search', width=80)
                    dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                    dpg.add_text(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    function_keys = ['F1:HELP', 'F2:MARKETS', 'F3:NEWS', 'F4:PORT', 'F5:MOVERS', 'F6:ECON']
                    for key in function_keys:
                        dpg.add_button(label=key, width=80, height=25)
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    self.create_left_panel()
                    self.create_center_panel()
                    self.create_right_panel()
                dpg.add_separator()
                self.create_bottom_section()
                info('Dashboard tab content created successfully')
        except Exception as e:
            error('Error in create_content', context={'error': str(e)}, exc_info=True)
            dpg.add_text('Bloomberg Terminal', color=self.BLOOMBERG_ORANGE)
            dpg.add_text('Terminal is loading... Please wait.')

    def create_left_panel(self):
        """Create left panel with market data"""
        with dpg.child_window(width=350, height=600, border=True):
            dpg.add_text('MARKET MONITOR', color=self.BLOOMBERG_ORANGE)
            dpg.add_separator()
            dpg.add_text('GLOBAL INDICES', color=self.BLOOMBERG_YELLOW)
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True):
                dpg.add_table_column(label='Index')
                dpg.add_table_column(label='Value')
                dpg.add_table_column(label='Change %')
                with self._lock:
                    for index, data in self.indices.items():
                        with dpg.table_row():
                            dpg.add_text(self.safe_text_display(index))
                            dpg.add_text(f'{data['value']:.2f}')
                            change_color = self.BLOOMBERG_GREEN if data['change'] > 0 else self.BLOOMBERG_RED
                            dpg.add_text(f'{data['change']:+.2f}%', color=change_color)
            dpg.add_separator()
            dpg.add_text('ECONOMIC INDICATORS', color=self.BLOOMBERG_YELLOW)
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True):
                dpg.add_table_column(label='Indicator')
                dpg.add_table_column(label='Value')
                dpg.add_table_column(label='Change')
                for indicator, data in self.economic_indicators.items():
                    with dpg.table_row():
                        dpg.add_text(self.safe_text_display(indicator))
                        dpg.add_text(f'{data['value']:.2f}')
                        change_color = self.BLOOMBERG_GREEN if data['change'] > 0 else self.BLOOMBERG_RED
                        dpg.add_text(f'{data['change']:+.2f}', color=change_color)
            dpg.add_separator()
            dpg.add_text('LATEST NEWS', color=self.BLOOMBERG_YELLOW)
            with self._lock:
                for headline in self.news_headlines[:4]:
                    time_str = datetime.datetime.now().strftime('%H:%M')
                    safe_headline = self.safe_text_display(headline)
                    if len(safe_headline) > 50:
                        safe_headline = safe_headline[:47] + '...'
                    dpg.add_text(f'{time_str} - {safe_headline}', wrap=340)

    def create_center_panel(self):
        """Create center panel with stock data"""
        with dpg.child_window(width=800, height=600, border=True):
            with dpg.tab_bar():
                with dpg.tab(label='Market Data'):
                    dpg.add_text('TOP STOCKS', color=self.BLOOMBERG_ORANGE)
                    with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, scrollY=True, height=300):
                        dpg.add_table_column(label='Ticker')
                        dpg.add_table_column(label='Last')
                        dpg.add_table_column(label='Chg')
                        dpg.add_table_column(label='Chg%')
                        dpg.add_table_column(label='Volume')
                        dpg.add_table_column(label='High')
                        dpg.add_table_column(label='Low')
                        with self._lock:
                            for ticker in self.tickers:
                                data = self.stock_data.get(ticker, {})
                                with dpg.table_row():
                                    dpg.add_text(self.safe_text_display(ticker))
                                    dpg.add_text(f'{data.get('price', 0):.2f}')
                                    change_color = self.BLOOMBERG_GREEN if data.get('change_pct', 0) > 0 else self.BLOOMBERG_RED
                                    dpg.add_text(f'{data.get('change_val', 0):+.2f}', color=change_color)
                                    dpg.add_text(f'{data.get('change_pct', 0):+.2f}%', color=change_color)
                                    dpg.add_text(f'{data.get('volume', 0):,}')
                                    dpg.add_text(f'{data.get('high', 0):.2f}')
                                    dpg.add_text(f'{data.get('low', 0):.2f}')
                    dpg.add_separator()
                    dpg.add_text('STOCK DETAILS', color=self.BLOOMBERG_ORANGE)
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(label='Ticker', default_value='AAPL', width=150)
                        dpg.add_button(label='Load')
                    with dpg.group(horizontal=True):
                        with dpg.group():
                            dpg.add_text('Apple Inc (AAPL US Equity)', color=self.BLOOMBERG_ORANGE)
                            dpg.add_text('Technology - Consumer Electronics')
                            with self._lock:
                                aapl_data = self.stock_data.get('AAPL', {})
                                dpg.add_text(f'Last Price: {aapl_data.get('price', 0):.2f}')
                                change_color = self.BLOOMBERG_GREEN if aapl_data.get('change_pct', 0) > 0 else self.BLOOMBERG_RED
                                dpg.add_text(f'Change: {aapl_data.get('change_val', 0):+.2f} ({aapl_data.get('change_pct', 0):+.2f}%)', color=change_color)
                                dpg.add_text(f'Volume: {aapl_data.get('volume', 0):,}')
                        with dpg.group():
                            with self._lock:
                                aapl_data = self.stock_data.get('AAPL', {})
                                dpg.add_text(f'High: {aapl_data.get('high', 0):.2f}')
                                dpg.add_text(f'Low: {aapl_data.get('low', 0):.2f}')
                                dpg.add_text(f'Open: {aapl_data.get('open', 0):.2f}')
                            dpg.add_text('P/E Ratio: 28.5')
                            dpg.add_text('Market Cap: $2.8T')
                with dpg.tab(label='Charts'):
                    dpg.add_text('ADVANCED CHARTS', color=self.BLOOMBERG_ORANGE)
                    with dpg.group(horizontal=True):
                        dpg.add_combo(['AAPL', 'MSFT', 'GOOGL', 'AMZN'], default_value='AAPL', width=150)
                        dpg.add_combo(['1D', '5D', '1M', '3M'], default_value='1M', width=100)
                        dpg.add_button(label='Update Chart')
                    with dpg.plot(height=300, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label='Time')
                        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Price')
                        x_data = list(range(30))
                        with self._lock:
                            base_price = self.stock_data.get('AAPL', {}).get('price', 175)
                        y_data = [base_price + i * 0.5 for i in range(30)]
                        dpg.add_line_series(x_data, y_data, label='AAPL', parent=y_axis)
                    dpg.add_text('TECHNICAL INDICATORS', color=self.BLOOMBERG_ORANGE)
                    with dpg.group(horizontal=True):
                        with dpg.group():
                            dpg.add_text('Moving Averages', color=self.BLOOMBERG_YELLOW)
                            dpg.add_text('MA 20: 175.50 - Buy', color=self.BLOOMBERG_GREEN)
                            dpg.add_text('MA 50: 172.30 - Buy', color=self.BLOOMBERG_GREEN)
                            dpg.add_text('MA 200: 165.80 - Neutral', color=self.BLOOMBERG_WHITE)
                        with dpg.group():
                            dpg.add_text('Oscillators', color=self.BLOOMBERG_YELLOW)
                            dpg.add_text('RSI(14): 65.42 - Neutral', color=self.BLOOMBERG_WHITE)
                            dpg.add_text('MACD: 2.15 - Buy', color=self.BLOOMBERG_GREEN)
                            dpg.add_text('Stochastic: 75.30 - Sell', color=self.BLOOMBERG_RED)
                with dpg.tab(label='News'):
                    dpg.add_text('FINANCIAL NEWS', color=self.BLOOMBERG_ORANGE)
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(label='Search', width=300)
                        dpg.add_button(label='Go')
                    dpg.add_separator()
                    with self._lock:
                        for i, headline in enumerate(self.news_headlines):
                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                            safe_headline = self.safe_text_display(headline)
                            dpg.add_text(safe_headline, color=self.BLOOMBERG_ORANGE)
                            dpg.add_text(timestamp, color=self.BLOOMBERG_GRAY)
                            dpg.add_text('Market analysis and financial news content goes here...')
                            dpg.add_separator()

    def create_right_panel(self):
        """Create right panel with command line"""
        with dpg.child_window(width=350, height=600, border=True):
            dpg.add_text('COMMAND LINE', color=self.BLOOMBERG_ORANGE)
            dpg.add_separator()
            with dpg.child_window(height=200, border=True):
                dpg.add_text('> AAPL US Equity <GO>', color=self.BLOOMBERG_WHITE)
                dpg.add_text('  Loading AAPL US Equity...', color=self.BLOOMBERG_GRAY)
                dpg.add_text('> TOP <GO>', color=self.BLOOMBERG_WHITE)
                dpg.add_text('  Loading TOP news...', color=self.BLOOMBERG_GRAY)
                dpg.add_text('> WEI <GO>', color=self.BLOOMBERG_WHITE)
                dpg.add_text('  Loading World Equity Indices...', color=self.BLOOMBERG_GRAY)
            dpg.add_input_text(label='>', width=-1)
            dpg.add_text('<HELP> for commands. Press <GO> to execute.', color=self.BLOOMBERG_GRAY)
            dpg.add_separator()
            dpg.add_text('COMMON COMMANDS', color=self.BLOOMBERG_ORANGE)
            dpg.add_text('HELP - Show available commands')
            dpg.add_text('DES - Company description')
            dpg.add_text('GP - Price graph')
            dpg.add_text('TOP - Top news headlines')
            dpg.add_text('WEI - World equity indices')
            dpg.add_text('PORT - Portfolio overview')

    def create_bottom_section(self):
        """Create bottom news ticker and status bar"""
        dpg.add_text('LIVE NEWS TICKER', color=self.BLOOMBERG_ORANGE)
        with dpg.child_window(height=50, border=True):
            with self._lock:
                ticker_text = ' • '.join(self.news_headlines[:3]) if self.news_headlines else 'Loading live news...'
                safe_ticker_text = self.safe_text_display(ticker_text)
            dpg.add_text(safe_ticker_text)
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with self._lock:
                status_color = self.BLOOMBERG_ORANGE if self.data_loading else self.BLOOMBERG_GREEN
                status_text = 'UPDATING' if self.data_loading else 'CONNECTED'
            dpg.add_text('●', color=status_color)
            dpg.add_text(status_text, color=status_color)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('LIVE DATA', color=self.BLOOMBERG_ORANGE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            current_hour = datetime.datetime.now().hour
            if 9 <= current_hour < 16:
                dpg.add_text('MARKET OPEN', color=self.BLOOMBERG_GREEN)
            else:
                dpg.add_text('MARKET CLOSED', color=self.BLOOMBERG_RED)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('SERVER: NY-01', color=self.BLOOMBERG_WHITE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('USER: TRADER001', color=self.BLOOMBERG_WHITE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            with self._lock:
                if self.last_update:
                    last_update_str = datetime.datetime.fromtimestamp(self.last_update).strftime('%H:%M:%S')
                    dpg.add_text(f'LAST UPDATE: {last_update_str}', color=self.BLOOMBERG_WHITE)
                else:
                    dpg.add_text('LAST UPDATE: --:--:--', color=self.BLOOMBERG_WHITE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('LATENCY: 12ms', color=self.BLOOMBERG_GREEN)

    def resize_components(self, left_width, center_width, right_width, top_height, bottom_height, cell_height):
        """Resize components - simplified"""
        try:
            debug('Dashboard resize requested', context={'left_width': left_width, 'center_width': center_width, 'right_width': right_width})
        except Exception as e:
            warning('Resize handling failed', context={'error': str(e)})

    @monitor_performance
    def cleanup(self):
        """Clean up resources"""
        try:
            with logger.operation('dashboard_cleanup'):
                info('Starting Dashboard Tab cleanup')
                with self._lock:
                    self.stock_data = {}
                    self.indices = {}
                    self.news_headlines = []
                    self.data_loading = False
                info('Dashboard Tab cleanup completed successfully')
        except Exception as e:
            error('Dashboard Tab cleanup failed', context={'error': str(e)}, exc_info=True)

    def force_refresh(self):
        """Force refresh all data - useful for manual updates"""
        try:
            if not self.data_loading:
                info('Force refreshing data')
                self.update_data_background()
            else:
                info('Data update already in progress')
        except Exception as e:
            error('Force refresh failed', context={'error': str(e)}, exc_info=True)

    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status information"""
        try:
            current_time = datetime.datetime.now()
            current_hour = current_time.hour
            is_market_open = 9 <= current_hour < 16
            with self._lock:
                status = {'is_open': is_market_open, 'last_update': self.last_update, 'data_loading': self.data_loading, 'stocks_count': len(self.stock_data), 'indices_count': len(self.indices), 'news_count': len(self.news_headlines)}
            return status
        except Exception as e:
            error('Failed to get market status', context={'error': str(e)}, exc_info=True)
            return {'error': str(e)}

    def get_stock_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data for a specific symbol"""
        try:
            with self._lock:
                return self.stock_data.get(symbol.upper())
        except Exception as e:
            error(f'Failed to get stock data for symbol', context={'symbol': symbol, 'error': str(e)}, exc_info=True)
            return None

    def add_custom_ticker(self, symbol: str):
        """Add a custom ticker to the watch list"""
        try:
            symbol = symbol.upper()
            if symbol not in self.tickers:
                self.tickers.append(symbol)
                if not self.data_loading:
                    try:
                        new_data = self.get_stock_data_optimized([symbol], timeout=10)
                        with self._lock:
                            self.stock_data.update(new_data)
                        info(f'Added ticker to watch list', context={'symbol': symbol})
                    except Exception as e:
                        error(f'Error adding ticker', context={'symbol': symbol, 'error': str(e)}, exc_info=True)
        except Exception as e:
            error(f'Failed to add custom ticker', context={'symbol': symbol, 'error': str(e)}, exc_info=True)

    def remove_ticker(self, symbol: str):
        """Remove a ticker from the watch list"""
        try:
            symbol = symbol.upper()
            if symbol in self.tickers:
                self.tickers.remove(symbol)
                with self._lock:
                    if symbol in self.stock_data:
                        del self.stock_data[symbol]
                info(f'Removed ticker from watch list', context={'symbol': symbol})
        except Exception as e:
            error(f'Failed to remove ticker', context={'symbol': symbol, 'error': str(e)}, exc_info=True)

    def export_data_to_json(self) -> str:
        """Export current data to JSON format"""
        try:
            with logger.operation('data_export'):
                info('Exporting dashboard data to JSON')
                with self._lock:
                    export_data = {'timestamp': datetime.datetime.now().isoformat(), 'stock_data': self.stock_data, 'indices': self.indices, 'news_headlines': self.news_headlines, 'economic_indicators': self.economic_indicators}
                json_data = json.dumps(export_data, indent=2)
                info('Dashboard data exported successfully', context={'data_size': len(json_data)})
                return json_data
        except Exception as e:
            error('Error exporting data', context={'error': str(e)}, exc_info=True)
            return '{}'

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        try:
            with self._lock:
                gainers = [ticker for ticker, data in self.stock_data.items() if data.get('change_pct', 0) > 0]
                losers = [ticker for ticker, data in self.stock_data.items() if data.get('change_pct', 0) < 0]
                total_volume = sum((data.get('volume', 0) for data in self.stock_data.values()))
                stats = {'total_stocks': len(self.stock_data), 'gainers': len(gainers), 'losers': len(losers), 'unchanged': len(self.stock_data) - len(gainers) - len(losers), 'total_volume': total_volume, 'top_gainer': max(self.stock_data.items(), key=lambda x: x[1].get('change_pct', 0))[0] if self.stock_data else None, 'top_loser': min(self.stock_data.items(), key=lambda x: x[1].get('change_pct', 0))[0] if self.stock_data else None}
            debug('Performance stats calculated', context=stats)
            return stats
        except Exception as e:
            error('Failed to get performance stats', context={'error': str(e)}, exc_info=True)
            return {'error': str(e)}

def fetch_feed(feed_url: str) -> List[str]:
    """Fetch headlines from a single feed"""
    try:
        debug(f'Fetching from feed: {feed_url}')
        feed = feedparser.parse(feed_url)
        headlines = []
        if feed.entries:
            for entry in feed.entries[:3]:
                try:
                    title = entry.title.strip()
                    if isinstance(title, bytes):
                        title = title.decode('utf-8', errors='ignore')
                    title = title.encode('ascii', errors='ignore').decode('ascii')
                    if len(title) > 80:
                        title = title[:77] + '...'
                    if title:
                        headlines.append(title)
                except Exception as e:
                    warning(f'Error processing news entry', context={'error': str(e)})
                    continue
        debug(f'Fetched {len(headlines)} headlines from feed')
        return headlines
    except Exception as e:
        warning(f'Error parsing feed', context={'feed_url': feed_url, 'error': str(e)})
        return []

def safe_text_display(self, text: Any) -> str:
    """Safely display text with encoding handling"""
    try:
        if isinstance(text, bytes):
            return text.decode('utf-8', errors='ignore')
        elif isinstance(text, (int, float)):
            return str(text)
        elif text is None:
            return ''
        else:
            return str(text).encode('ascii', errors='ignore').decode('ascii')
    except Exception as e:
        warning(f'Error displaying text', context={'error': str(e)})
        return 'N/A'

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

@monitor_performance
def plot_efficient_frontier(self, mu: pd.Series, S: pd.DataFrame, num_points: int=100, save_path: str=None, show_assets: bool=True, show_cml: bool=True) -> str:
    """
    Plot the efficient frontier

    Args:
        mu: Expected returns
        S: Covariance matrix
        num_points: Number of points on frontier
        save_path: Path to save plot
        show_assets: Whether to show individual assets
        show_cml: Whether to show Capital Market Line

    Returns:
        Path to saved plot or base64 string
    """
    try:
        with operation('plot_efficient_frontier'):
            frontier_data = self.calculate_efficient_frontier(mu, S, num_points)
            plt.figure(figsize=(12, 8))
            plt.scatter(frontier_data['volatilities'], frontier_data['returns'], c=frontier_data['returns'], cmap='viridis', alpha=0.6, s=50)
            plt.colorbar(label='Expected Return')
            if show_assets:
                asset_volatility = np.sqrt(np.diag(S))
                plt.scatter(asset_volatility, mu, alpha=0.8, s=100, c='red', marker='o')
                for i, asset in enumerate(mu.index):
                    plt.annotate(asset, (asset_volatility[i], mu[i]), xytext=(5, 5), textcoords='offset points')
            max_sharpe = frontier_data['max_sharpe']
            plt.scatter(max_sharpe['volatility'], max_sharpe['return'], marker='*', s=500, c='gold', edgecolors='black', label=f'Max Sharpe (SR={max_sharpe['sharpe_ratio']:.3f})')
            if show_cml:
                max_vol = max(frontier_data['volatilities'])
                cml_x = np.linspace(0, max_vol, 100)
                cml_slope = (max_sharpe['return'] - self.risk_free_rate) / max_sharpe['volatility']
                cml_y = self.risk_free_rate + cml_slope * cml_x
                plt.plot(cml_x, cml_y, 'r--', alpha=0.7, label='Capital Market Line')
            plt.xlabel('Volatility (Risk)')
            plt.ylabel('Expected Return')
            plt.title('Efficient Frontier')
            plt.legend()
            plt.grid(True, alpha=0.3)
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                import io
                import base64
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                buffer.seek(0)
                plot_data = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                return plot_data
    except Exception as e:
        logger.error(f'Error plotting efficient frontier: {e}')
        raise

@monitor_performance
def plot_correlation_matrix(self, prices: pd.DataFrame, method: str='pearson', save_path: str=None) -> str:
    """
    Plot correlation matrix of assets

    Args:
        prices: Price data
        method: Correlation method ('pearson', 'spearman', 'kendall')
        save_path: Path to save plot

    Returns:
        Path to saved plot or base64 string
    """
    try:
        with operation('plot_correlation_matrix'):
            returns = prices.pct_change().dropna()
            correlation_matrix = returns.corr(method=method)
            plt.figure(figsize=(12, 10))
            mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
            sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap='coolwarm', center=0, square=True, linewidths=0.5, cbar_kws={'shrink': 0.8})
            plt.title(f'Asset Correlation Matrix ({method.title()})')
            plt.tight_layout()
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                import io
                import base64
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                buffer.seek(0)
                plot_data = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                return plot_data
    except Exception as e:
        logger.error(f'Error plotting correlation matrix: {e}')
        raise

@monitor_performance
def plot_weights_comparison(self, weights_dict: Dict[str, Dict[str, float]], save_path: str=None) -> str:
    """
    Plot comparison of different portfolio weights

    Args:
        weights_dict: Dictionary of {method_name: weights}
        save_path: Path to save plot

    Returns:
        Path to saved plot or base64 string
    """
    try:
        with operation('plot_weights_comparison'):
            df_weights = pd.DataFrame(weights_dict).fillna(0)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            df_weights.T.plot(kind='bar', stacked=True, ax=ax1, colormap='tab20', alpha=0.8)
            ax1.set_title('Portfolio Weights Comparison (Stacked)')
            ax1.set_ylabel('Weight')
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.grid(True, alpha=0.3)
            df_weights.plot(kind='bar', ax=ax2, alpha=0.8, colormap='tab10')
            ax2.set_title('Portfolio Weights Comparison (Side-by-side)')
            ax2.set_ylabel('Weight')
            ax2.set_xlabel('Assets')
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax2.grid(True, alpha=0.3)
            plt.tight_layout()
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                import io
                import base64
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                buffer.seek(0)
                plot_data = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                return plot_data
    except Exception as e:
        logger.error(f'Error plotting weights comparison: {e}')
        raise

class YFinanceDataTab:
    """Bloomberg Terminal YFinance Data Tab with performance optimizations and new logger"""

    def __init__(self, main_app=None):
        self.main_app = main_app
        self.current_ticker = None
        self.stock_data = None
        self.history_data = None
        self.financials_data = {}
        self.is_loading = False
        self.BLOOMBERG_ORANGE = (255, 165, 0)
        self.BLOOMBERG_WHITE = (255, 255, 255)
        self.BLOOMBERG_RED = (255, 0, 0)
        self.BLOOMBERG_GREEN = (0, 200, 0)
        self.BLOOMBERG_YELLOW = (255, 255, 0)
        self.BLOOMBERG_GRAY = (120, 120, 120)
        self.BLOOMBERG_BLUE = (0, 128, 255)
        self._data_cache = {}
        self._chart_cache = {}
        self._search_cache = {}
        self._last_update_time = None
        self.dropdown_items = []
        self.dropdown_created = False
        self.search_timer = None
        self.equities_data = None
        self.equities_df = None
        self.finance_db_available = False
        self.initialize_equities_database()
        try:
            self.theme_manager = AutomaticThemeManager()
            debug('Theme manager initialized successfully')
        except Exception as e:
            warning('Theme manager initialization failed', context={'error': str(e)})
            self.theme_manager = None
        log_info('YFinanceDataTab initialized')

    def get_label(self):
        return 'Equity Research'

    def get_config_directory(self) -> Path:
        """Get platform-specific config directory - uses .fincept folder"""
        config_dir = Path.home() / '.fincept' / 'cache'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def initialize_equities_database(self):
        """Initialize the global equities database with proper DataFrame handling"""
        try:
            try:
                import financedatabase as fd
                log_info('Loading complete equities database...')
                equities = fd.Equities()
                equity_data = equities.select(exclude_exchanges=False)
                if isinstance(equity_data, dict):
                    self.equities_df = pd.DataFrame.from_dict(equity_data, orient='index')
                elif isinstance(equity_data, pd.DataFrame):
                    self.equities_df = equity_data
                else:
                    self.equities_df = pd.DataFrame(equity_data)
                self.equities_data = equity_data
                self.finance_db_available = True
                self._create_search_index()
                log_info(f'✅ Loaded {len(self.equities_df)} equities from {(self.equities_df['exchange'].nunique() if 'exchange' in self.equities_df.columns else 'multiple')} exchanges')
            except ImportError:
                warning('financedatabase not available. Install with: pip install financedatabase')
                self.finance_db_available = False
                self.equities_data = None
                self.equities_df = None
            except Exception as e:
                error('Error initializing equities database', context={'error': str(e)}, exc_info=True)
                self.finance_db_available = False
                self.equities_data = None
                self.equities_df = None
        except Exception as outer_e:
            error('Outer error in initialize_equities_database', context={'error': str(outer_e)}, exc_info=True)
            self.finance_db_available = False
            self.equities_data = None
            self.equities_df = None

    def _create_search_index(self):
        """Create optimized search index for faster lookups"""
        try:
            if self.equities_df is None or self.equities_df.empty:
                return
            search_data = []
            for idx, row in self.equities_df.iterrows():
                symbol = str(idx).upper()
                name = str(row.get('name', '')).lower()
                sector = str(row.get('sector', 'N/A'))
                country = str(row.get('country', 'N/A'))
                exchange = str(row.get('exchange', 'N/A'))
                search_entry = {'symbol': symbol, 'symbol_lower': symbol.lower(), 'name_lower': name, 'display_name': str(row.get('name', 'N/A'))[:35], 'sector': sector[:15], 'country': country[:10], 'exchange': exchange[:10]}
                search_data.append(search_entry)
            self._search_index = search_data
            debug(f'Search index created with {len(search_data)} entries')
        except Exception as e:
            error('Error creating search index', context={'error': str(e)}, exc_info=True)
            self._search_index = []

    def load_ticker_from_external(self, ticker: str):
        """Load ticker data when called from external source (like watchlist) - MINIMAL IMPLEMENTATION"""
        try:
            with operation('load_ticker_from_external', context={'ticker': ticker}):
                log_info('Loading ticker from external source', context={'ticker': ticker})
                if dpg.does_item_exist('ticker_search_input'):
                    dpg.set_value('ticker_search_input', ticker)
                self.safe_set_value('search_status_text', f'🔄 Loading {ticker} from Watchlist...')
                self.current_ticker = ticker.upper()
                threading.Thread(target=self._load_external_ticker_data, args=(ticker.upper(),), daemon=True).start()
        except Exception as e:
            error('Error loading ticker from external source', context={'ticker': ticker, 'error': str(e)}, exc_info=True)

    def _load_external_ticker_data(self, ticker: str):
        """Helper method to load ticker data from external source"""
        try:
            self.is_loading = True
            self.safe_configure_item('search_button', enabled=False)
            self.load_complete_stock_data(ticker)
            current_status = dpg.get_value('search_status_text') if dpg.does_item_exist('search_status_text') else ''
            if '✅' in current_status and 'loaded successfully' in current_status:
                self.safe_set_value('search_status_text', current_status + ' (from Watchlist)')
        except Exception as e:
            error('Error in external ticker data loading', context={'ticker': ticker, 'error': str(e)}, exc_info=True)
        finally:
            self.is_loading = False
            self.safe_configure_item('search_button', enabled=True)

    def safe_add_text(self, text, **kwargs):
        """Safely add text with encoding error handling and performance optimization"""
        try:
            if text is None:
                text = 'N/A'
            elif not isinstance(text, str):
                text = str(text)
            text = text.encode('ascii', 'ignore').decode('ascii')
            replacements = {'…': '...', '–': '-', '—': '-', '"': '"', '"': '"', ': "\'",\n                ': "'", '€': 'EUR', '£': 'GBP', '¥': 'JPY'}
            for old, new in replacements.items():
                text = text.replace(old, new)
            if not text.strip():
                text = 'N/A'
            if 'color' in kwargs:
                color = kwargs['color']
                if isinstance(color, list):
                    if len(color) >= 3:
                        kwargs['color'] = (int(color[0]), int(color[1]), int(color[2]))
                    else:
                        kwargs['color'] = (255, 255, 255)
                elif isinstance(color, tuple):
                    if len(color) >= 3:
                        kwargs['color'] = (int(color[0]), int(color[1]), int(color[2]))
                    else:
                        kwargs['color'] = (255, 255, 255)
                elif isinstance(color, (int, float)):
                    val = int(color)
                    kwargs['color'] = (val, val, val)
                else:
                    kwargs['color'] = (255, 255, 255)
            if 'tag' in kwargs:
                tag = kwargs['tag']
                if dpg.does_item_exist(tag):
                    import time
                    kwargs['tag'] = f'{tag}_{int(time.time() * 1000000) % 1000000}'
            return dpg.add_text(text, **kwargs)
        except Exception as e:
            error('Text add error', context={'error': str(e), 'text_preview': str(text)[:50] if text else 'None'}, exc_info=True)
            try:
                fallback_kwargs = {k: v for k, v in kwargs.items() if k not in ['color']}
                return dpg.add_text('Data Error', color=(255, 0, 0), **fallback_kwargs)
            except Exception as fallback_error:
                error('Fallback text add failed', context={'error': str(fallback_error)})
                return None

    def safe_configure_item(self, tag, **kwargs):
        """Safely configure item with error handling"""
        try:
            if dpg.does_item_exist(tag):
                if 'color' in kwargs:
                    color = kwargs['color']
                    if isinstance(color, list):
                        if len(color) >= 3:
                            kwargs['color'] = (int(color[0]), int(color[1]), int(color[2]))
                        else:
                            kwargs['color'] = (255, 255, 255)
                    elif isinstance(color, tuple):
                        if len(color) >= 3:
                            kwargs['color'] = (int(color[0]), int(color[1]), int(color[2]))
                        else:
                            kwargs['color'] = (255, 255, 255)
                dpg.configure_item(tag, **kwargs)
            else:
                debug(f'Item {tag} does not exist for configuration')
        except Exception as e:
            debug(f'Error configuring item {tag}', context={'error': str(e)})

    def safe_set_value(self, tag, value):
        """Safely set value with encoding handling and performance optimization"""
        try:
            if isinstance(value, str):
                value = ''.join((c for c in value if ord(c) < 128))
                replacements = {'…': '...', '–': '-', '—': '-'}
                for old, new in replacements.items():
                    value = value.replace(old, new)
            elif not isinstance(value, (int, float, bool)):
                value = str(value)
                value = ''.join((c for c in value if ord(c) < 128))
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)
            else:
                debug(f'Tag {tag} does not exist for value setting')
        except Exception as e:
            error('Set value error', context={'tag': tag, 'error': str(e)}, exc_info=True)
            try:
                if dpg.does_item_exist(tag):
                    dpg.set_value(tag, 'ERROR')
            except:
                pass

    @monitor_performance
    def create_content(self):
        """Create the complete YFinance data interface"""
        with operation('create_yfinance_content'):
            try:
                self.create_header_section()
                with dpg.child_window(height=-30, border=False, tag='main_content_area'):
                    self.create_company_overview_section()
                    dpg.add_spacer(height=15)
                    self.create_market_data_section()
                    dpg.add_spacer(height=15)
                    self.create_price_and_returns_section()
                    dpg.add_spacer(height=15)
                    self.create_financial_statements_section()
                    self.create_financial_charts_section()
                self.create_status_bar()
                self.start_time_updater()
                threading.Timer(1.0, self.load_default_ticker).start()
                log_info('YFinance content created successfully')
            except Exception as e:
                error('Error creating YFinance content', context={'error': str(e)}, exc_info=True)
                self.safe_add_text(f'ERROR: {e}', color=self.BLOOMBERG_RED)

    def load_default_ticker(self):
        """Load AAPL ticker by default"""
        with operation('load_default_ticker'):
            try:
                dpg.set_value('ticker_search_input', 'AAPL')
                self.handle_search()
                debug('Default ticker AAPL loaded')
            except Exception as e:
                error('Error loading default ticker', context={'error': str(e)}, exc_info=True)

    def create_header_section(self):
        """Create header with enhanced search functionality"""
        try:
            import time
            unique_suffix = int(time.time() * 1000) % 1000
            with dpg.group(horizontal=True):
                self.safe_add_text('FINCEPT', color=(255, 165, 0), tag=f'fincept_label_{unique_suffix}')
                self.safe_add_text('MARKET DATA', color=(255, 255, 255), tag=f'market_data_label_{unique_suffix}')
                self.safe_add_text(' | ', color=(120, 120, 120))
                self.safe_add_text('TICKER:', color=(255, 255, 0), tag=f'ticker_label_{unique_suffix}')
                dpg.add_input_text(width=200, hint='Search global equities...', tag='ticker_search_input', callback=self.search_callback, on_enter=True, default_value='AAPL')
                dpg.add_button(label='SEARCH', callback=self.handle_search, width=70, height=25, tag='search_button')
                dpg.add_button(label='CLEAR', callback=self.clear_search, width=60, height=25, tag=f'clear_button_{unique_suffix}')
                self.safe_add_text(' | ', color=(120, 120, 120))
                if self.finance_db_available and self.equities_df is not None:
                    self.safe_add_text('🌍', color=(0, 200, 0), tag=f'db_icon_{unique_suffix}')
                    self.safe_add_text(f'{len(self.equities_df):,} symbols', color=(0, 200, 0), tag=f'db_count_{unique_suffix}')
                else:
                    self.safe_add_text('❌', color=(255, 0, 0), tag=f'db_error_icon_{unique_suffix}')
                    self.safe_add_text('Local DB only', color=(255, 0, 0), tag=f'db_error_text_{unique_suffix}')
                self.safe_add_text(' | ', color=(120, 120, 120))
                self.safe_add_text('TIME:', color=(255, 255, 0), tag=f'time_label_{unique_suffix}')
                self.safe_add_text(datetime.now().strftime('%H:%M:%S'), tag='header_time', color=(255, 255, 255))
            dpg.add_separator()
            with dpg.group(horizontal=True):
                self.safe_add_text('', tag='search_status_text', color=(255, 255, 0))
            with dpg.group(tag='current_stock_display', show=False):
                with dpg.group(horizontal=True):
                    self.safe_add_text('CURRENT:', color=(255, 255, 0), tag=f'current_label_{unique_suffix}')
                    self.safe_add_text('', tag='current_stock_name', color=(255, 255, 255))
                    self.safe_add_text(' | ', color=(120, 120, 120))
                    self.safe_add_text('PRICE:', color=(255, 255, 0), tag=f'price_label_{unique_suffix}')
                    self.safe_add_text('', tag='current_stock_price', color=(0, 200, 0))
                    self.safe_add_text('', tag='current_stock_change', color=(0, 200, 0))
                dpg.add_separator()
        except Exception as e:
            error('Error creating header', context={'error': str(e)}, exc_info=True)

    def create_company_overview_section(self):
        """Create company overview section"""
        try:
            with dpg.collapsing_header(label='COMPANY OVERVIEW', default_open=True, tag='company_overview_header'):
                with dpg.group(horizontal=True):
                    sections = [('COMPANY INFORMATION', 380, 220, 'company_info_text', [173, 216, 230], 360), ('BUSINESS SUMMARY', 500, 220, 'business_summary_text', [144, 238, 144], 480), ('KEY METRICS', 320, 220, 'key_metrics_text', [240, 128, 128], None)]
                    for title, width, height, tag, color, wrap in sections:
                        with dpg.child_window(width=width, height=height, border=True):
                            self.safe_add_text(title, color=self.BLOOMBERG_ORANGE)
                            dpg.add_separator()
                            text_kwargs = {'color': color, 'tag': tag}
                            if wrap:
                                text_kwargs['wrap'] = wrap
                            self.safe_add_text('Loading AAPL data...', **text_kwargs)
        except Exception as e:
            error('Error creating company overview', context={'error': str(e)}, exc_info=True)

    def create_market_data_section(self):
        """Create market data section"""
        try:
            with dpg.collapsing_header(label='MARKET DATA & PERFORMANCE', default_open=True, tag='market_data_header'):
                with dpg.group(horizontal=True):
                    sections = [('PRICE DATA', 300, 200, 'price_data_text', [224, 255, 255]), ('TRADING METRICS', 300, 200, 'trading_metrics_text', [255, 255, 224]), ('VALUATION METRICS', 300, 200, 'valuation_metrics_text', [255, 182, 193]), ('EXECUTIVE TEAM', 400, 200, 'executives_text', self.BLOOMBERG_YELLOW)]
                    for title, width, height, tag, color in sections:
                        with dpg.child_window(width=width, height=height, border=True):
                            self.safe_add_text(title, color=self.BLOOMBERG_ORANGE)
                            dpg.add_separator()
                            self.safe_add_text('Loading AAPL data...', color=color, tag=tag)
        except Exception as e:
            error('Error creating market data', context={'error': str(e)}, exc_info=True)

    def create_price_and_returns_section(self):
        """Create price chart and returns section"""
        try:
            with dpg.collapsing_header(label='PRICE CHART & RETURNS', default_open=True, tag='price_returns_header'):
                with dpg.group(horizontal=True):
                    self.safe_add_text('PERIOD:', color=self.BLOOMBERG_YELLOW)
                    dpg.add_combo(['1D', '5D', '1M', '3M', '6M', '1Y', '2Y'], default_value='3M', width=100, tag='chart_period_combo', callback=self.update_price_chart)
                    dpg.add_button(label='UPDATE CHART', callback=self.update_price_chart, width=100, height=25)
                    self.safe_add_text('CHART TYPE:', color=self.BLOOMBERG_YELLOW)
                    dpg.add_combo(['Line Chart', 'Candlestick'], default_value='Candlestick', width=120, tag='chart_type_combo', callback=self.update_price_chart)
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    with dpg.child_window(width=800, height=400, border=True):
                        self.safe_add_text('PRICE CHART', color=self.BLOOMBERG_ORANGE)
                        dpg.add_separator()
                        with dpg.group(tag='chart_container'):
                            self.safe_add_text('Loading AAPL chart data...', color=self.BLOOMBERG_YELLOW, tag='chart_placeholder')
                    with dpg.child_window(width=400, height=400, border=True):
                        self.safe_add_text('HISTORICAL RETURNS', color=self.BLOOMBERG_ORANGE)
                        dpg.add_separator()
                        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, tag='returns_performance_table'):
                            dpg.add_table_column(label='Period', width_fixed=True, init_width_or_weight=80)
                            dpg.add_table_column(label='Return', width_fixed=True, init_width_or_weight=100)
                            dpg.add_table_column(label='Status', width_fixed=True, init_width_or_weight=80)
                            periods = ['1D', '7D', '15D', '30D', '60D', '90D', '180D', '365D']
                            for i, period in enumerate(periods):
                                with dpg.table_row(tag=f'return_row_{i}'):
                                    self.safe_add_text(period, color=self.BLOOMBERG_YELLOW)
                                    self.safe_add_text('Loading...', tag=f'return_value_{i}', color=self.BLOOMBERG_YELLOW)
                                    self.safe_add_text('--', tag=f'return_status_{i}', color=self.BLOOMBERG_GRAY)
        except Exception as e:
            error('Error creating price/returns section', context={'error': str(e)}, exc_info=True)

    def create_financial_statements_section(self):
        """Create financial statements section"""
        try:
            with dpg.collapsing_header(label='FINANCIAL STATEMENTS', default_open=True, tag='financials_header'):
                with dpg.tab_bar(tag='financial_statements_tabs'):
                    tabs = [('INCOME STATEMENT', 'income_statement_container', 'income_statement_placeholder'), ('BALANCE SHEET', 'balance_sheet_container', 'balance_sheet_placeholder'), ('CASH FLOW STATEMENT', 'cash_flow_container', 'cash_flow_placeholder')]
                    for tab_label, container_tag, placeholder_tag in tabs:
                        with dpg.tab(label=tab_label):
                            with dpg.child_window(height=400, border=True, horizontal_scrollbar=True, tag=container_tag):
                                self.safe_add_text(f'{tab_label} DATA', color=self.BLOOMBERG_ORANGE)
                                dpg.add_separator()
                                self.safe_add_text('Loading AAPL financial data...', color=self.BLOOMBERG_YELLOW, tag=placeholder_tag)
        except Exception as e:
            error('Error creating financial statements', context={'error': str(e)}, exc_info=True)

    def create_financial_charts_section(self):
        """Create financial analysis charts section"""
        try:
            with dpg.collapsing_header(label='FINANCIAL ANALYSIS CHARTS', default_open=True, tag='financial_charts_header'):
                with dpg.group(horizontal=True):
                    self.safe_add_text('CHART CONTROLS:', color=self.BLOOMBERG_ORANGE)
                    self.safe_add_text(' | ', color=self.BLOOMBERG_GRAY)
                    self.safe_add_text('YEARS:', color=self.BLOOMBERG_YELLOW)
                    dpg.add_combo(['Last 2 Years', 'Last 3 Years', 'Last 4 Years', 'All Years'], default_value='Last 4 Years', width=120, tag='chart_years_combo', callback=self.update_financial_charts)
                    dpg.add_button(label='UPDATE CHARTS', callback=self.update_financial_charts, width=120, height=25)
                dpg.add_spacer(height=10)
                chart_sections = [[('REVENUE & PROFITABILITY TRENDS', 'revenue_chart_container', 600), ('BALANCE SHEET TRENDS', 'balance_chart_container', 600)], [('CASH FLOW ANALYSIS', 'cashflow_chart_container', 600), ('FINANCIAL RATIOS & MARGINS', 'ratios_chart_container', 600)]]
                for row in chart_sections:
                    with dpg.group(horizontal=True):
                        for title, container_tag, width in row:
                            with dpg.child_window(width=width, height=350, border=True):
                                self.safe_add_text(title, color=self.BLOOMBERG_ORANGE)
                                dpg.add_separator()
                                with dpg.group(tag=container_tag):
                                    self.safe_add_text('Loading AAPL financial charts...', color=self.BLOOMBERG_YELLOW)
                    if row == chart_sections[0]:
                        dpg.add_spacer(height=15)
        except Exception as e:
            error('Error creating financial charts', context={'error': str(e)}, exc_info=True)

    def create_status_bar(self):
        """Create status bar with fixed color parameters"""
        try:
            dpg.add_separator()
            with dpg.group(horizontal=True):
                import time
                unique_suffix = int(time.time() * 1000) % 1000
                self.safe_add_text('●', color=(0, 200, 0), tag=f'status_dot_{unique_suffix}')
                self.safe_add_text('DATA SERVICE ONLINE', color=(0, 200, 0), tag=f'data_service_{unique_suffix}')
                self.safe_add_text(' | ', color=(120, 120, 120))
                self.safe_add_text('STATUS:', color=(255, 255, 0), tag=f'status_label_{unique_suffix}')
                self.safe_add_text('INITIALIZING', color=(255, 255, 0), tag='main_status_text')
                self.safe_add_text(' | ', color=(120, 120, 120))
                self.safe_add_text('LAST UPDATE:', color=(255, 255, 0), tag=f'update_label_{unique_suffix}')
                self.safe_add_text('LOADING', color=(255, 255, 255), tag='last_update_time')
        except Exception as e:
            error('Error creating status bar', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def handle_search(self, sender=None, app_data=None):
        """Handle search functionality with enhanced global search"""
        with operation('handle_search'):
            try:
                ticker = dpg.get_value('ticker_search_input').strip().upper()
                if not ticker:
                    self.safe_set_value('search_status_text', '❌ Enter ticker symbol')
                    return
                if self.is_loading:
                    self.safe_set_value('search_status_text', '⏳ Loading in progress...')
                    return
                self.hide_dropdown()
                cache_key = f'{ticker}_basic_data'
                if cache_key in self._data_cache:
                    cached_time = self._data_cache[cache_key].get('timestamp', 0)
                    if time.time() - cached_time < 300:
                        debug('Using cached data', context={'ticker': ticker})
                        self.stock_data = self._data_cache[cache_key]['data']
                        self.update_all_data_sections(self.stock_data)
                        self.safe_set_value('search_status_text', f'✅ {ticker} (cached)')
                        return
                self.is_loading = True
                self.current_ticker = ticker
                self.safe_set_value('search_status_text', f'📈 Loading {ticker}...')
                self.safe_configure_item('search_button', enabled=False)
                log_info('Direct stock search initiated', context={'ticker': ticker})
                threading.Thread(target=self.load_complete_stock_data, args=(ticker,), daemon=True).start()
            except Exception as e:
                error('Error handling search', context={'error': str(e)}, exc_info=True)
                self.safe_set_value('search_status_text', '❌ Search error')

    def search_equities(self, query):
        """Fast search through global equities database using optimized index"""
        if not self.finance_db_available or not hasattr(self, '_search_index') or (not self._search_index):
            return [f'{query.upper()} | Search in progress... | N/A (Local)']
        query = query.lower().strip()
        if len(query) < 1:
            return []
        cache_key = f'search_{query}'
        if cache_key in self._search_cache:
            cached_time = self._search_cache[cache_key].get('timestamp', 0)
            if time.time() - cached_time < 60:
                return self._search_cache[cache_key]['results']
        results = []
        count = 0
        try:
            for entry in self._search_index:
                if count >= 8:
                    break
                if query in entry['symbol_lower'] or query in entry['name_lower']:
                    result_line = f'{entry['symbol']} | {entry['display_name']} | {entry['sector']} ({entry['country']}-{entry['exchange']})'
                    results.append(result_line)
                    count += 1
            if len(query) >= 1 and query.replace('.', '').replace('-', '').isalnum():
                direct_option = f'{query.upper()} | Direct Search | Manual Entry (Direct)'
                if direct_option not in results:
                    results.insert(0, direct_option)
            self._search_cache[cache_key] = {'results': results, 'timestamp': time.time()}
            return results if results else [f'{query.upper()} | No matches found | Try direct search']
        except Exception as e:
            error('Error searching equities', context={'error': str(e)}, exc_info=True)
            return [f'{query.upper()} | Search error | Try direct entry']

    def delayed_search(self):
        """Perform search with delay to avoid excessive API calls"""
        try:
            search_text = dpg.get_value('ticker_search_input').strip()
            if len(search_text) < 1:
                self.hide_dropdown()
                self.safe_set_value('search_status_text', '')
                return
            self.safe_set_value('search_status_text', '🔍 Searching global database...')
            matches = self.search_equities(search_text)
            self.dropdown_items = matches
            self.show_dropdown()
            status_msg = f'✅ {len(matches)} results found' if matches else '❌ No results'
            self.safe_set_value('search_status_text', status_msg)
        except Exception as e:
            error('Error in delayed search', context={'error': str(e)}, exc_info=True)
            self.safe_set_value('search_status_text', '❌ Search error')

    def search_callback(self, sender=None, app_data=None):
        """Handle search input with debouncing"""
        try:
            if self.search_timer and self.search_timer.is_alive():
                self.search_timer.cancel()
            self.search_timer = threading.Timer(0.2, self.delayed_search)
            self.search_timer.start()
        except Exception as e:
            error('Error in search callback', context={'error': str(e)}, exc_info=True)

    def show_dropdown(self):
        """Show search results dropdown"""
        try:
            if not self.dropdown_created:
                with dpg.window(label='##search_dropdown', tag='search_dropdown_window', no_title_bar=True, no_resize=True, no_move=True, no_collapse=True, no_close=True, show=False, modal=False, popup=True):
                    pass
                self.dropdown_created = True
            dpg.delete_item('search_dropdown_window', children_only=True)
            for i, item in enumerate(self.dropdown_items[:8]):
                dpg.add_button(label=item, parent='search_dropdown_window', callback=self.select_search_item, user_data=item, width=650, height=30)
            if dpg.does_item_exist('ticker_search_input'):
                input_pos = dpg.get_item_pos('ticker_search_input')
                dpg.set_item_pos('search_dropdown_window', [input_pos[0], input_pos[1] + 35])
                dpg.show_item('search_dropdown_window')
        except Exception as e:
            error('Error showing dropdown', context={'error': str(e)}, exc_info=True)

    def hide_dropdown(self):
        """Hide search dropdown"""
        try:
            if dpg.does_item_exist('search_dropdown_window'):
                dpg.hide_item('search_dropdown_window')
        except Exception as e:
            debug('Error hiding dropdown', context={'error': str(e)})

    def select_search_item(self, sender, app_data, user_data):
        """Handle selection from dropdown"""
        try:
            symbol = user_data.split(' | ')[0].strip()
            dpg.set_value('ticker_search_input', symbol)
            self.hide_dropdown()
            self.safe_set_value('search_status_text', f'Selected: {symbol}')
            self.current_ticker = symbol
            log_info('Symbol selected from search', context={'symbol': symbol})
            threading.Thread(target=self.load_complete_stock_data, args=(symbol,), daemon=True).start()
        except Exception as e:
            error('Error selecting search item', context={'error': str(e)}, exc_info=True)

    def clear_search(self):
        """Clear search input and hide dropdown"""
        try:
            dpg.set_value('ticker_search_input', '')
            self.safe_set_value('search_status_text', '')
            self.hide_dropdown()
        except Exception as e:
            error('Error clearing search', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def load_complete_stock_data(self, ticker):
        """Load complete stock data including financials with performance optimizations"""
        with operation('load_complete_stock_data', context={'ticker': ticker}):
            try:
                stock = yf.Ticker(ticker)
                self.safe_set_value('search_status_text', f'📊 Loading {ticker} info...')
                info_start_time = time.time()
                info = stock.info
                info_load_time = time.time() - info_start_time
                if not info or len(info) < 5:
                    raise Exception('Invalid ticker or no data available')
                self.stock_data = info
                cache_key = f'{ticker}_basic_data'
                self._data_cache[cache_key] = {'data': info, 'timestamp': time.time()}
                self.safe_set_value('search_status_text', f'📈 Loading {ticker} price history...')
                history_start_time = time.time()
                history = stock.history(period='2y')
                history_load_time = time.time() - history_start_time
                if history.empty:
                    raise Exception('No historical data available')
                self.history_data = history
                self.update_all_data_sections(info)
                self.safe_set_value('search_status_text', f'💰 Loading {ticker} financials...')
                financials_start_time = time.time()
                self.load_financial_data(stock)
                financials_load_time = time.time() - financials_start_time
                self.safe_set_value('search_status_text', f'✅ {ticker} loaded successfully')
                self.safe_set_value('last_update_time', datetime.now().strftime('%H:%M:%S'))
                self._last_update_time = time.time()
                from fincept_terminal.utils.Logging.logger import info as log_info
                log_info('Stock data loaded successfully', context={'ticker': ticker, 'info_load_time_ms': f'{info_load_time * 1000:.1f}', 'history_load_time_ms': f'{history_load_time * 1000:.1f}', 'financials_load_time_ms': f'{financials_load_time * 1000:.1f}'})
            except Exception as e:
                error_msg = str(e)[:50] + '...' if len(str(e)) > 50 else str(e)
                self.safe_set_value('search_status_text', f'❌ Error: {error_msg}')
                error('Error loading stock data', context={'ticker': ticker, 'error': str(e)}, exc_info=True)
            finally:
                self.is_loading = False
                self.safe_configure_item('search_button', enabled=True)

    def update_all_data_sections(self, info):
        """Update all data sections with stock info"""
        with operation('update_all_data_sections'):
            try:
                dpg.show_item('current_stock_display')
                company_name = info.get('shortName', info.get('longName', 'Unknown Company'))
                self.safe_set_value('current_stock_name', f'{self.current_ticker} - {company_name}')
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                previous_close = info.get('previousClose', info.get('regularMarketPreviousClose', 0))
                if current_price and previous_close:
                    change = current_price - previous_close
                    change_pct = change / previous_close * 100 if previous_close != 0 else 0
                    price_color = self.BLOOMBERG_GREEN if change >= 0 else self.BLOOMBERG_RED
                    self.safe_set_value('current_stock_price', f'${current_price:.2f}')
                    dpg.configure_item('current_stock_price', color=price_color)
                    change_text = f'{change:+.2f} ({change_pct:+.2f}%)'
                    self.safe_set_value('current_stock_change', change_text)
                    dpg.configure_item('current_stock_change', color=price_color)
                self.update_company_information(info)
                self.update_market_data_info(info)
                self.update_price_chart()
                self.update_returns_table()
                debug('All data sections updated successfully')
            except Exception as e:
                error('Error updating data sections', context={'error': str(e)}, exc_info=True)

    def update_company_information(self, info):
        """Update company information section with optimized formatting"""
        try:

            def safe_format(value, format_type='str'):
                try:
                    if value is None or pd.isna(value):
                        return 'N/A'
                    if format_type == 'int':
                        return f'{int(value):,}'
                    elif format_type == 'currency':
                        return f'${float(value):,.0f}' if value != 0 else '$0'
                    elif format_type == 'percentage':
                        return f'{float(value) * 100:.2f}%' if value != 0 else '0.00%'
                    elif format_type == 'float':
                        return f'{float(value):.2f}' if value != 0 else '0.00'
                    else:
                        return str(value)
                except:
                    return 'N/A'
            employees = safe_format(info.get('fullTimeEmployees'), 'int')
            company_info_items = [('Company', info.get('longName', 'N/A')), ('Sector', info.get('sector', 'N/A')), ('Industry', info.get('industry', 'N/A')), ('Country', info.get('country', 'N/A')), ('Website', info.get('website', 'N/A')), ('Phone', info.get('phone', 'N/A')), ('Employees', employees), ('Exchange', info.get('exchange', 'N/A')), ('Currency', info.get('currency', 'N/A')), ('Address', f'{info.get('address1', 'N/A')}, {info.get('city', 'N/A')}')]
            company_info = '\n'.join((f'{label}: {value}' for label, value in company_info_items))
            self.safe_set_value('company_info_text', company_info)
            dpg.configure_item('company_info_text', color=[173, 216, 230])
            business_summary = info.get('longBusinessSummary', 'No business summary available.')
            if len(business_summary) > 1200:
                business_summary = business_summary[:1200] + '...'
            self.safe_set_value('business_summary_text', business_summary)
            dpg.configure_item('business_summary_text', color=[144, 238, 144])
            key_metrics_items = [('Market Cap', safe_format(info.get('marketCap'), 'currency')), ('Enterprise Value', safe_format(info.get('enterpriseValue'), 'currency')), ('P/E Ratio', safe_format(info.get('trailingPE'), 'float')), ('Forward P/E', safe_format(info.get('forwardPE'), 'float')), ('PEG Ratio', safe_format(info.get('pegRatio'), 'float')), ('Price/Sales', safe_format(info.get('priceToSalesTrailing12Months'), 'float')), ('Price/Book', safe_format(info.get('priceToBook'), 'float')), ('Beta', safe_format(info.get('beta'), 'float')), ('ROE', safe_format(info.get('returnOnEquity'), 'percentage')), ('ROA', safe_format(info.get('returnOnAssets'), 'percentage')), ('Debt/Equity', safe_format(info.get('debtToEquity'), 'float')), ('Profit Margin', safe_format(info.get('profitMargins'), 'percentage'))]
            key_metrics = '\n'.join((f'{label}: {value}' for label, value in key_metrics_items))
            self.safe_set_value('key_metrics_text', key_metrics)
            dpg.configure_item('key_metrics_text', color=[240, 128, 128])
        except Exception as e:
            error('Error updating company information', context={'error': str(e)}, exc_info=True)

    def update_market_data_info(self, info):
        """Update market data information with optimized formatting"""
        try:

            def safe_format_value(value, is_currency=True, is_percentage=False):
                try:
                    if value is None or pd.isna(value):
                        return 'N/A'
                    if is_percentage:
                        return f'{float(value) * 100:.2f}%'
                    elif is_currency:
                        return f'${float(value):,.2f}'
                    else:
                        return f'{float(value):,}'
                except:
                    return 'N/A'
            price_data_items = [('Current Price', safe_format_value(info.get('currentPrice'))), ('Previous Close', safe_format_value(info.get('previousClose'))), ('Open', safe_format_value(info.get('open'))), ('Day Low', safe_format_value(info.get('dayLow'))), ('Day High', safe_format_value(info.get('dayHigh'))), ('52W Low', safe_format_value(info.get('fiftyTwoWeekLow'))), ('52W High', safe_format_value(info.get('fiftyTwoWeekHigh'))), ('Volume', safe_format_value(info.get('volume'), False)), ('Avg Volume', safe_format_value(info.get('averageVolume'), False))]
            price_data = '\n'.join((f'{label}: {value}' for label, value in price_data_items))
            self.safe_set_value('price_data_text', price_data)
            dpg.configure_item('price_data_text', color=[224, 255, 255])
            trading_metrics_items = [('Market Cap', safe_format_value(info.get('marketCap'))), ('Beta', safe_format_value(info.get('beta'))), ('Dividend Rate', safe_format_value(info.get('dividendRate'))), ('Dividend Yield', safe_format_value(info.get('dividendYield'), False, True)), ('Shares Outstanding', safe_format_value(info.get('sharesOutstanding'), False)), ('Float Shares', safe_format_value(info.get('floatShares'), False))]
            trading_metrics = '\n'.join((f'{label}: {value}' for label, value in trading_metrics_items))
            self.safe_set_value('trading_metrics_text', trading_metrics)
            dpg.configure_item('trading_metrics_text', color=[255, 255, 224])
            valuation_metrics_items = [('P/E Ratio (TTM)', safe_format_value(info.get('trailingPE'), False)), ('Forward P/E', safe_format_value(info.get('forwardPE'), False)), ('PEG Ratio', safe_format_value(info.get('pegRatio'), False)), ('Price/Sales (TTM)', safe_format_value(info.get('priceToSalesTrailing12Months'), False)), ('Price/Book', safe_format_value(info.get('priceToBook'), False)), ('Book Value', safe_format_value(info.get('bookValue'))), ('Target Price', safe_format_value(info.get('targetMeanPrice')))]
            valuation_metrics = '\n'.join((f'{label}: {value}' for label, value in valuation_metrics_items))
            self.safe_set_value('valuation_metrics_text', valuation_metrics)
            dpg.configure_item('valuation_metrics_text', color=[255, 182, 193])
            executives = info.get('companyOfficers', [])
            if executives:
                exec_text = ''
                for i, exec in enumerate(executives[:6]):
                    name = exec.get('name', 'Unknown')
                    title = exec.get('title', 'Unknown Title')
                    age = exec.get('age', '')
                    total_pay = exec.get('totalPay', 0)
                    exec_text += f'• {name}'
                    if age:
                        exec_text += f' (Age: {age})'
                    exec_text += f'\n  {title}'
                    if total_pay and total_pay > 0:
                        exec_text += f'\n  Compensation: ${total_pay:,.0f}'
                    exec_text += '\n\n'
                self.safe_set_value('executives_text', exec_text)
                dpg.configure_item('executives_text', color=self.BLOOMBERG_YELLOW)
            else:
                self.safe_set_value('executives_text', 'No executive information available.')
                dpg.configure_item('executives_text', color=self.BLOOMBERG_YELLOW)
        except Exception as e:
            error('Error updating market data', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def update_price_chart(self, sender=None, app_data=None):
        """Update price chart with historical data and caching"""
        with operation('update_price_chart'):
            try:
                if self.history_data is None or self.history_data.empty:
                    return
                if dpg.does_item_exist('chart_container'):
                    dpg.delete_item('chart_container', children_only=True)
                    period = dpg.get_value('chart_period_combo') if dpg.does_item_exist('chart_period_combo') else '3M'
                    chart_type = dpg.get_value('chart_type_combo') if dpg.does_item_exist('chart_type_combo') else 'Candlestick'
                    cache_key = f'{self.current_ticker}_{period}_{chart_type}_chart'
                    if cache_key in self._chart_cache:
                        cached_time = self._chart_cache[cache_key].get('timestamp', 0)
                        if time.time() - cached_time < 300:
                            debug('Using cached chart data', context={'ticker': self.current_ticker, 'period': period})
                    period_mapping = {'1D': 1, '5D': 5, '1M': 22, '3M': 66, '6M': 132, '1Y': 252, '2Y': len(self.history_data)}
                    data = self.history_data.tail(period_mapping.get(period, 66))
                    if data.empty:
                        self.safe_add_text('No data available for selected period', color=self.BLOOMBERG_RED, parent='chart_container')
                        return
                    with dpg.plot(height=350, width=-1, parent='chart_container', tag='main_price_chart'):
                        dpg.add_plot_legend()
                        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label='Time')
                        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Price ($)')
                        if chart_type == 'Candlestick':
                            dates = list(range(len(data)))
                            opens = data['Open'].tolist()
                            highs = data['High'].tolist()
                            lows = data['Low'].tolist()
                            closes = data['Close'].tolist()
                            dpg.add_candle_series(dates, opens, closes, lows, highs, label='OHLC', parent=y_axis, bull_color=[0, 255, 0, 255], bear_color=[255, 0, 0, 255], weight=0.75, tooltip=True)
                        else:
                            dates = list(range(len(data)))
                            closes = data['Close'].tolist()
                            if len(closes) >= 20:
                                ma20 = pd.Series(closes).rolling(window=20, min_periods=1).mean().tolist()
                                dpg.add_line_series(dates, ma20, label='MA20', parent=y_axis)
                            if len(closes) >= 50:
                                ma50 = pd.Series(closes).rolling(window=50, min_periods=1).mean().tolist()
                                dpg.add_line_series(dates, ma50, label='MA50', parent=y_axis)
                            dpg.add_line_series(dates, closes, label='Close Price', parent=y_axis)
                        if not data.empty:
                            price_min = min(data['Low'].min(), data['Close'].min()) * 0.98
                            price_max = max(data['High'].max(), data['Close'].max()) * 1.02
                            dpg.set_axis_limits(y_axis, price_min, price_max)
                        self._chart_cache[cache_key] = {'timestamp': time.time(), 'data': data.copy()}
                debug('Price chart updated successfully', context={'period': period, 'chart_type': chart_type})
            except Exception as e:
                error('Error updating price chart', context={'error': str(e)}, exc_info=True)
                if dpg.does_item_exist('chart_container'):
                    dpg.delete_item('chart_container', children_only=True)
                    self.safe_add_text(f'Chart Error: {str(e)[:50]}...', color=self.BLOOMBERG_RED, parent='chart_container')

    def update_returns_table(self):
        """Update historical returns table with performance optimization"""
        try:
            if self.history_data is None or self.history_data.empty:
                return
            current_price = self.history_data['Close'].iloc[-1]
            periods = [1, 7, 15, 30, 60, 90, 180, 365]
            for i, days in enumerate(periods):
                try:
                    if len(self.history_data) > days:
                        past_price = self.history_data['Close'].iloc[-(days + 1)]
                        return_pct = (current_price - past_price) / past_price * 100
                        if return_pct > 0:
                            color = self.BLOOMBERG_GREEN
                            status = '▲'
                        elif return_pct < 0:
                            color = self.BLOOMBERG_RED
                            status = '▼'
                        else:
                            color = self.BLOOMBERG_WHITE
                            status = '='
                        self.safe_set_value(f'return_value_{i}', f'{return_pct:+.2f}%')
                        dpg.configure_item(f'return_value_{i}', color=color)
                        self.safe_set_value(f'return_status_{i}', status)
                        dpg.configure_item(f'return_status_{i}', color=color)
                    else:
                        self.safe_set_value(f'return_value_{i}', 'N/A')
                        dpg.configure_item(f'return_value_{i}', color=self.BLOOMBERG_GRAY)
                        self.safe_set_value(f'return_status_{i}', '--')
                        dpg.configure_item(f'return_status_{i}', color=self.BLOOMBERG_GRAY)
                except Exception as e:
                    self.safe_set_value(f'return_value_{i}', 'Error')
                    dpg.configure_item(f'return_value_{i}', color=self.BLOOMBERG_RED)
        except Exception as e:
            error('Error updating returns table', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def load_financial_data(self, stock):
        """Load and display financial statements with performance optimization"""
        with operation('load_financial_data'):
            try:
                financials_mapping = {'income_statement': ('financials', self.create_financial_table, 'income_statement_container', 'Income Statement'), 'balance_sheet': ('balance_sheet', self.create_financial_table, 'balance_sheet_container', 'Balance Sheet'), 'cash_flow': ('cashflow', self.create_financial_table, 'cash_flow_container', 'Cash Flow Statement')}
                for key, (attr_name, create_func, container, title) in financials_mapping.items():
                    try:
                        df = getattr(stock, attr_name)
                        self.financials_data[key] = df
                        create_func(df, container, title)
                    except Exception as e:
                        warning(f'Could not load {title}', context={'error': str(e)})
                        placeholder_tag = f'{container.replace('_container', '_placeholder')}'
                        self.safe_set_value(placeholder_tag, f'Error loading {title.lower()}: {str(e)[:50]}...')
                self.update_financial_charts()
                debug('Financial data loaded successfully', context={'statements_loaded': len([k for k, v in self.financials_data.items() if v is not None])})
            except Exception as e:
                error('Error loading financial data', context={'error': str(e)}, exc_info=True)
                error_placeholders = ['income_statement_placeholder', 'balance_sheet_placeholder', 'cash_flow_placeholder']
                for placeholder in error_placeholders:
                    self.safe_set_value(placeholder, f'Error loading financial data: {str(e)[:50]}...')

    def create_financial_table(self, df, container_tag, title):
        """Create financial statement table with performance optimization"""
        try:
            if df is None or df.empty:
                return
            dpg.delete_item(container_tag, children_only=True)
            self.safe_add_text(f'{title.upper()} DATA', color=self.BLOOMBERG_ORANGE, parent=container_tag)
            dpg.add_separator(parent=container_tag)
            with dpg.table(parent=container_tag, header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, scrollY=True, scrollX=True, height=330):
                dpg.add_table_column(label='Line Item', width_fixed=True, init_width_or_weight=250)
                years = df.columns[:4] if len(df.columns) > 4 else df.columns
                for year in years:
                    year_str = year.strftime('%Y') if hasattr(year, 'strftime') else str(year)[:4]
                    dpg.add_table_column(label=year_str, width_fixed=True, init_width_or_weight=130)
                for idx in df.index[:20]:
                    with dpg.table_row():
                        self.safe_add_text(str(idx), color=self.BLOOMBERG_YELLOW)
                        for year in years:
                            try:
                                value = df.loc[idx, year]
                                if pd.isna(value):
                                    self.safe_add_text('N/A', color=self.BLOOMBERG_GRAY)
                                else:
                                    formatted_value = self._format_financial_value(value)
                                    self.safe_add_text(formatted_value, color=self.BLOOMBERG_WHITE)
                            except Exception:
                                self.safe_add_text('Error', color=self.BLOOMBERG_RED)
        except Exception as e:
            error('Error creating financial table', context={'title': title, 'error': str(e)}, exc_info=True)

    def _format_financial_value(self, value):
        """Efficiently format financial values"""
        try:
            abs_value = abs(value)
            if abs_value >= 1000000000000.0:
                return f'${value / 1000000000000.0:.2f}T'
            elif abs_value >= 1000000000.0:
                return f'${value / 1000000000.0:.2f}B'
            elif abs_value >= 1000000.0:
                return f'${value / 1000000.0:.2f}M'
            elif abs_value >= 1000.0:
                return f'${value / 1000.0:.2f}K'
            else:
                return f'${value:.2f}'
        except:
            return 'N/A'

    @monitor_performance
    def update_financial_charts(self, sender=None, app_data=None):
        """Update all financial analysis charts with performance optimization"""
        with operation('update_financial_charts'):
            try:
                if not self.financials_data:
                    return
                years_selection = dpg.get_value('chart_years_combo') if dpg.does_item_exist('chart_years_combo') else 'Last 4 Years'
                chart_updates = [('revenue_profitability', self.create_revenue_profitability_chart), ('balance_sheet_trends', self.create_balance_sheet_trends_chart), ('cash_flow_analysis', self.create_cash_flow_analysis_chart), ('financial_ratios', self.create_financial_ratios_chart)]
                for chart_name, update_func in chart_updates:
                    try:
                        update_func(years_selection)
                    except Exception as e:
                        warning(f'Could not update {chart_name} chart', context={'error': str(e)})
                debug('Financial charts updated', context={'years_selection': years_selection})
            except Exception as e:
                error('Error updating financial charts', context={'error': str(e)}, exc_info=True)

    def create_revenue_profitability_chart(self, years_selection):
        """Create revenue and profitability trends chart"""
        try:
            income_stmt = self.financials_data.get('income_statement')
            if income_stmt is None or income_stmt.empty:
                return
            dpg.delete_item('revenue_chart_container', children_only=True)
            years_mapping = {'Last 2 Years': 2, 'Last 3 Years': 3, 'Last 4 Years': 4}
            num_years = years_mapping.get(years_selection, len(income_stmt.columns))
            years_cols = income_stmt.columns[:num_years]
            with dpg.plot(height=300, width=-1, parent='revenue_chart_container'):
                dpg.add_plot_legend()
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label='Year')
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Amount (Billions)')
                data_series = [(['Total Revenue', 'Revenue', 'Net Sales', 'Total Revenues'], 'Revenue (B)'), (['Net Income', 'Net Income Common Stockholders'], 'Net Income (B)')]
                for items_list, label in data_series:
                    for revenue_item in items_list:
                        if revenue_item in income_stmt.index:
                            self._add_financial_series(income_stmt, revenue_item, years_cols, label, y_axis)
                            break
        except Exception as e:
            error('Error creating revenue chart', context={'error': str(e)}, exc_info=True)

    def _add_financial_series(self, df, item_name, years_cols, label, y_axis):
        """Helper method to add financial data series to chart"""
        try:
            item_data = df.loc[item_name]
            years = []
            values = []
            for year in years_cols:
                if year in item_data.index:
                    value = item_data[year]
                    if pd.notna(value) and value != 0:
                        year_num = year.year if hasattr(year, 'year') else int(str(year)[:4])
                        years.append(year_num)
                        values.append(value / 1000000000.0)
            if years and values:
                sorted_data = sorted(zip(years, values))
                years, values = zip(*sorted_data)
                dpg.add_line_series(list(years), list(values), label=label, parent=y_axis)
        except Exception as e:
            debug('Could not add financial series', context={'item': item_name, 'error': str(e)})

    def create_balance_sheet_trends_chart(self, years_selection):
        """Create balance sheet trends chart"""
        try:
            balance_sheet = self.financials_data.get('balance_sheet')
            if balance_sheet is None or balance_sheet.empty:
                return
            dpg.delete_item('balance_chart_container', children_only=True)
            years_mapping = {'Last 2 Years': 2, 'Last 3 Years': 3, 'Last 4 Years': 4}
            num_years = years_mapping.get(years_selection, len(balance_sheet.columns))
            years_cols = balance_sheet.columns[:num_years]
            with dpg.plot(height=300, width=-1, parent='balance_chart_container'):
                dpg.add_plot_legend()
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label='Year')
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Amount (Billions)')
                bs_items = [('Total Assets', 'Total Assets (B)'), ('Total Stockholder Equity', 'Stockholder Equity (B)'), ('Total Debt', 'Total Debt (B)')]
                for item_name, label in bs_items:
                    if item_name in balance_sheet.index:
                        self._add_financial_series(balance_sheet, item_name, years_cols, label, y_axis)
        except Exception as e:
            error('Error creating balance sheet chart', context={'error': str(e)}, exc_info=True)

    def create_cash_flow_analysis_chart(self, years_selection):
        """Create cash flow analysis chart"""
        try:
            cash_flow = self.financials_data.get('cash_flow')
            if cash_flow is None or cash_flow.empty:
                return
            dpg.delete_item('cashflow_chart_container', children_only=True)
            years_mapping = {'Last 2 Years': 2, 'Last 3 Years': 3, 'Last 4 Years': 4}
            num_years = years_mapping.get(years_selection, len(cash_flow.columns))
            years_cols = cash_flow.columns[:num_years]
            with dpg.plot(height=300, width=-1, parent='cashflow_chart_container'):
                dpg.add_plot_legend()
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label='Year')
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Cash Flow (Billions)')
                cf_items = [('Operating Cash Flow', 'Operating CF (B)'), ('Free Cash Flow', 'Free CF (B)'), ('Investing Cash Flow', 'Investing CF (B)'), ('Financing Cash Flow', 'Financing CF (B)')]
                for item_name, label in cf_items:
                    if item_name in cash_flow.index:
                        self._add_financial_series(cash_flow, item_name, years_cols, label, y_axis)
        except Exception as e:
            error('Error creating cash flow chart', context={'error': str(e)}, exc_info=True)

    def create_financial_ratios_chart(self, years_selection):
        """Create financial ratios and margins chart"""
        try:
            income_stmt = self.financials_data.get('income_statement')
            balance_sheet = self.financials_data.get('balance_sheet')
            if income_stmt is None or balance_sheet is None or income_stmt.empty or balance_sheet.empty:
                return
            dpg.delete_item('ratios_chart_container', children_only=True)
            years_mapping = {'Last 2 Years': 2, 'Last 3 Years': 3, 'Last 4 Years': 4}
            num_years = years_mapping.get(years_selection, min(len(income_stmt.columns), len(balance_sheet.columns)))
            income_years = income_stmt.columns[:num_years]
            balance_years = balance_sheet.columns[:num_years]
            with dpg.plot(height=300, width=-1, parent='ratios_chart_container'):
                dpg.add_plot_legend()
                x_axis = dpg.add_plot_axis(dpg.mvXAxis, label='Year')
                y_axis = dpg.add_plot_axis(dpg.mvYAxis, label='Percentage (%)')
                self._calculate_and_plot_roe(income_stmt, balance_sheet, income_years, balance_years, y_axis)
                self._calculate_and_plot_profit_margin(income_stmt, income_years, y_axis)
        except Exception as e:
            error('Error creating ratios chart', context={'error': str(e)}, exc_info=True)

    def _calculate_and_plot_roe(self, income_stmt, balance_sheet, income_years, balance_years, y_axis):
        """Calculate and plot Return on Equity"""
        try:
            net_income_items = ['Net Income', 'Net Income Common Stockholders']
            equity_items = ['Total Stockholder Equity', 'Stockholder Equity']
            net_income_data = None
            equity_data = None
            for item in net_income_items:
                if item in income_stmt.index:
                    net_income_data = income_stmt.loc[item]
                    break
            for item in equity_items:
                if item in balance_sheet.index:
                    equity_data = balance_sheet.loc[item]
                    break
            if net_income_data is not None and equity_data is not None:
                years = []
                roe_values = []
                for year in income_years:
                    if year in balance_years:
                        ni = net_income_data[year] if year in net_income_data.index else None
                        eq = equity_data[year] if year in equity_data.index else None
                        if pd.notna(ni) and pd.notna(eq) and (eq != 0):
                            roe = ni / eq * 100
                            year_num = year.year if hasattr(year, 'year') else int(str(year)[:4])
                            years.append(year_num)
                            roe_values.append(roe)
                if years and roe_values:
                    sorted_data = sorted(zip(years, roe_values))
                    years, roe_values = zip(*sorted_data)
                    dpg.add_line_series(list(years), list(roe_values), label='ROE (%)', parent=y_axis)
        except Exception as e:
            debug('Could not calculate ROE', context={'error': str(e)})

    def _calculate_and_plot_profit_margin(self, income_stmt, income_years, y_axis):
        """Calculate and plot Profit Margin"""
        try:
            net_income_items = ['Net Income', 'Net Income Common Stockholders']
            revenue_items = ['Total Revenue', 'Revenue', 'Net Sales']
            net_income_data = None
            revenue_data = None
            for item in net_income_items:
                if item in income_stmt.index:
                    net_income_data = income_stmt.loc[item]
                    break
            for item in revenue_items:
                if item in income_stmt.index:
                    revenue_data = income_stmt.loc[item]
                    break
            if net_income_data is not None and revenue_data is not None:
                years = []
                margin_values = []
                for year in income_years:
                    ni = net_income_data[year] if year in net_income_data.index else None
                    rev = revenue_data[year] if year in revenue_data.index else None
                    if pd.notna(ni) and pd.notna(rev) and (rev != 0):
                        margin = ni / rev * 100
                        year_num = year.year if hasattr(year, 'year') else int(str(year)[:4])
                        years.append(year_num)
                        margin_values.append(margin)
                if years and margin_values:
                    sorted_data = sorted(zip(years, margin_values))
                    years, margin_values = zip(*sorted_data)
                    dpg.add_line_series(list(years), list(margin_values), label='Profit Margin (%)', parent=y_axis)
        except Exception as e:
            debug('Could not calculate profit margin', context={'error': str(e)})

    def start_time_updater(self):
        """Start background time updater"""

        def time_updater():
            while True:
                try:
                    current_time = datetime.now().strftime('%H:%M:%S')
                    if dpg.does_item_exist('header_time'):
                        dpg.set_value('header_time', current_time)
                    time.sleep(1)
                except:
                    break
        threading.Thread(target=time_updater, daemon=True).start()

    @monitor_performance
    def cleanup(self):
        """Cleanup resources with performance optimization"""
        with operation('yfinance_tab_cleanup'):
            try:
                if self.search_timer and self.search_timer.is_alive():
                    self.search_timer.cancel()
                self.hide_dropdown()
                self._data_cache.clear()
                self._chart_cache.clear()
                self._search_cache.clear()
                if hasattr(self, '_search_index'):
                    del self._search_index
                self.financials_data.clear()
                if hasattr(self, 'history_data') and self.history_data is not None:
                    del self.history_data
                if hasattr(self, 'stock_data') and self.stock_data is not None:
                    del self.stock_data
                if hasattr(self, 'equities_data') and self.equities_data is not None:
                    del self.equities_data
                if hasattr(self, 'equities_df') and self.equities_df is not None:
                    del self.equities_df
                log_info('YFinance Data Tab cleanup completed')
            except Exception as e:
                error('Error during cleanup', context={'error': str(e)}, exc_info=True)

def safe_add_text(self, text, **kwargs):
    """Safely add text with encoding error handling and performance optimization"""
    try:
        if text is None:
            text = 'N/A'
        elif not isinstance(text, str):
            text = str(text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        replacements = {'…': '...', '–': '-', '—': '-', '"': '"', '"': '"', ': "\'",\n                ': "'", '€': 'EUR', '£': 'GBP', '¥': 'JPY'}
        for old, new in replacements.items():
            text = text.replace(old, new)
        if not text.strip():
            text = 'N/A'
        if 'color' in kwargs:
            color = kwargs['color']
            if isinstance(color, list):
                if len(color) >= 3:
                    kwargs['color'] = (int(color[0]), int(color[1]), int(color[2]))
                else:
                    kwargs['color'] = (255, 255, 255)
            elif isinstance(color, tuple):
                if len(color) >= 3:
                    kwargs['color'] = (int(color[0]), int(color[1]), int(color[2]))
                else:
                    kwargs['color'] = (255, 255, 255)
            elif isinstance(color, (int, float)):
                val = int(color)
                kwargs['color'] = (val, val, val)
            else:
                kwargs['color'] = (255, 255, 255)
        if 'tag' in kwargs:
            tag = kwargs['tag']
            if dpg.does_item_exist(tag):
                import time
                kwargs['tag'] = f'{tag}_{int(time.time() * 1000000) % 1000000}'
        return dpg.add_text(text, **kwargs)
    except Exception as e:
        error('Text add error', context={'error': str(e), 'text_preview': str(text)[:50] if text else 'None'}, exc_info=True)
        try:
            fallback_kwargs = {k: v for k, v in kwargs.items() if k not in ['color']}
            return dpg.add_text('Data Error', color=(255, 0, 0), **fallback_kwargs)
        except Exception as fallback_error:
            error('Fallback text add failed', context={'error': str(fallback_error)})
            return None

class MaritimeMapTab(BaseTab):
    """Maritime Maps tab that controls separate PyQt process"""

    def __init__(self, app):
        super().__init__(app)
        self.map_process = None
        self.markers_file = 'maritime_markers.json'
        self.commands_file = 'map_commands.json'
        self.status_file = 'map_status.json'
        self.markers_data = self.load_markers()
        self.pyqt_available = self.check_pyqt()

    def get_label(self):
        return 'Maps'

    def check_pyqt(self):
        """Check if PyQt5 is available"""
        try:
            import PyQt5
            logger.info('PyQt5 found and available')
            return True
        except ImportError:
            logger.warning('PyQt5 not available - some features will be disabled')
            return False

    def load_markers(self):
        """Load markers from file"""
        try:
            if os.path.exists(self.markers_file):
                with open(self.markers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.debug(f'Loaded {len(data)} markers from file')
                    return data
            else:
                logger.debug('No existing markers file found, starting with empty list')
                return []
        except Exception as e:
            logger.error(f'Failed to load markers: {e}', exc_info=True)
            return []

    def save_markers(self):
        """Save markers to file"""
        try:
            with open(self.markers_file, 'w', encoding='utf-8') as f:
                json.dump(self.markers_data, f, indent=2, ensure_ascii=False)
            logger.debug(f'Saved {len(self.markers_data)} markers to file')
        except Exception as e:
            logger.error(f'Failed to save markers: {e}', exc_info=True)

    def send_command(self, command):
        """Send command to PyQt process"""
        with operation('send_command', command=command):
            try:
                commands = {'commands': [command]}
                if os.path.exists(self.commands_file):
                    try:
                        with open(self.commands_file, 'r', encoding='utf-8') as f:
                            existing = json.load(f)
                            existing.get('commands', []).append(command)
                            commands = existing
                    except Exception as e:
                        logger.warning(f'Could not load existing commands file: {e}')
                with open(self.commands_file, 'w', encoding='utf-8') as f:
                    json.dump(commands, f, ensure_ascii=False)
                logger.debug(f'Command sent successfully: {command}')
            except Exception as e:
                logger.error(f"Failed to send command '{command}': {e}", exc_info=True)
                raise

    def get_map_status(self):
        """Get status from PyQt process"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    status = data.get('status', 'unknown')
                    logger.debug(f'Retrieved map status: {status}')
                    return status
            else:
                logger.debug('Status file not found')
                return 'unknown'
        except Exception as e:
            logger.error(f'Failed to get map status: {e}', exc_info=True)
            return 'unknown'

    def safe_add_text(self, text, **kwargs):
        """Safely add text with error handling"""
        try:
            if not isinstance(text, str):
                text = str(text)
            text = text.encode('ascii', 'replace').decode('ascii')
            return dpg.add_text(text, **kwargs)
        except Exception as e:
            logger.error(f"Failed to add text '{text}': {e}", exc_info=True)
            try:
                return dpg.add_text('Text Error', **kwargs)
            except Exception as fallback_e:
                logger.critical(f'Fallback text creation also failed: {fallback_e}')
                return None

    @monitor_performance
    def create_content(self):
        """Create maritime maps dashboard content"""
        with operation('create_content'):
            try:
                self.add_section_header('FINCEPT MARITIME MAPS')
                with self.create_child_window(tag='map_control', width=-1, height=120):
                    self.add_section_header('Map Control')
                    with dpg.group(horizontal=True):
                        if self.pyqt_available:
                            dpg.add_button(label='LAUNCH MAP', callback=self.launch_map, width=150, height=35, tag='launch_btn')
                            dpg.add_button(label='CLOSE MAP', callback=self.close_map, width=120, height=35)
                        else:
                            self.safe_add_text('PyQt5 Required', color=[255, 100, 100])
                            self.safe_add_text('Run: pip install PyQt5 PyQtWebEngine', color=[255, 200, 100])
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        self.safe_add_text('Status:', color=[255, 255, 255])
                        status = 'Ready' if self.pyqt_available else 'PyQt5 Missing'
                        color = [100, 255, 100] if self.pyqt_available else [255, 100, 100]
                        self.safe_add_text(status, color=color, tag='status_text')
                        dpg.add_spacer(width=50)
                        self.safe_add_text('Markers:', color=[255, 255, 255])
                        self.safe_add_text(str(len(self.markers_data)), color=[255, 200, 100], tag='marker_count')
                dpg.add_spacer(height=10)
                with self.create_child_window(tag='marker_controls', width=-1, height=150):
                    self.add_section_header('Add Markers')
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(hint='Marker Title', width=150, tag='marker_title')
                        dpg.add_combo(items=['Ship', 'Port', 'Industry', 'Bank', 'Exchange'], default_value='Ship', width=100, tag='marker_type', callback=self.on_marker_type_changed)
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_input_float(label='Lat', default_value=19.076, format='%.4f', width=100, tag='lat_input')
                        dpg.add_input_float(label='Lng', default_value=72.8777, format='%.4f', width=100, tag='lng_input')
                        dpg.add_button(label='ADD', callback=self.add_marker, width=60)
                    dpg.add_spacer(height=5)
                    presets = ['Mumbai Port', 'Shanghai Port', 'Singapore Port', 'Hong Kong Port']
                    with dpg.group(horizontal=True):
                        dpg.add_combo(items=presets, default_value='Mumbai Port', width=150, tag='preset_combo')
                        dpg.add_button(label='ADD PRESET', callback=self.add_preset, width=100)
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    with self.create_child_window(tag='features', width=300, height=200):
                        self.add_section_header('Map Features')
                        dpg.add_button(label='Toggle Routes', callback=self.toggle_routes, width=150)
                        dpg.add_spacer(height=5)
                        dpg.add_button(label='Toggle Ships', callback=self.toggle_ships, width=150)
                        dpg.add_spacer(height=5)
                        dpg.add_button(label='Clear All', callback=self.clear_all, width=150)
                        dpg.add_spacer(height=15)
                        self.safe_add_text('Quick Add:')
                        dpg.add_button(label='Indian Ports', callback=self.add_indian_ports, width=150)
                        dpg.add_spacer(height=3)
                        dpg.add_button(label='Financial Centers', callback=self.add_financial, width=150)
                    with self.create_child_window(tag='markers_list', width=460, height=200):
                        self.add_section_header('Current Markers')
                        try:
                            with dpg.table(header_row=True, resizable=True, tag='markers_table'):
                                dpg.add_table_column(label='Title', width_fixed=True, init_width_or_weight=150)
                                dpg.add_table_column(label='Type', width_fixed=True, init_width_or_weight=80)
                                dpg.add_table_column(label='Coordinates', width_fixed=True, init_width_or_weight=120)
                            self.update_markers_table()
                        except Exception as e:
                            logger.error(f'Failed to create markers table: {e}', exc_info=True)
                            self.safe_add_text('Table Error - Check Console')
                logger.info('Maritime maps content created successfully')
            except Exception as e:
                logger.error(f'Failed to create content: {e}', exc_info=True)
                try:
                    self.safe_add_text(f'Error loading Maps tab: {str(e)}', color=[255, 100, 100])
                except Exception as fallback_e:
                    logger.critical(f'Could not even create error message: {fallback_e}')

    def launch_map(self, *args, **kwargs):
        """Launch PyQt map process - Flexible callback signature"""
        with operation('launch_map'):
            if not self.pyqt_available:
                self.update_status('PyQt5 not available')
                return
            try:
                if self.map_process is None or self.map_process.poll() is not None:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    map_script = os.path.join(current_dir, 'leaflet_map_ui.py')
                    if not os.path.exists(map_script):
                        logger.error(f'Map script not found at: {map_script}')
                        self.update_status('Map script not found')
                        return
                    logger.info(f'Launching map process: {map_script}')
                    self.map_process = subprocess.Popen([sys.executable, map_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.update_status('Launching map...')
                    try:
                        if dpg.does_item_exist('launch_btn'):
                            dpg.set_item_label('launch_btn', 'MAP RUNNING')
                    except Exception as e:
                        logger.warning(f'Could not update button label: {e}')
                    logger.info('Map process launched successfully')
                else:
                    logger.info('Map process already running')
                    self.update_status('Map already running')
            except Exception as e:
                logger.error(f'Failed to launch map: {e}', exc_info=True)
                self.update_status(f'Launch error: {str(e)}')

    def close_map(self, *args, **kwargs):
        """Close PyQt map process - Flexible callback signature"""
        with operation('close_map'):
            try:
                if self.map_process and self.map_process.poll() is None:
                    logger.info('Terminating map process')
                    self.map_process.terminate()
                    self.map_process = None
                    self.update_status('Map closed')
                    try:
                        if dpg.does_item_exist('launch_btn'):
                            dpg.set_item_label('launch_btn', 'LAUNCH MAP')
                    except Exception as e:
                        logger.warning(f'Could not update button label: {e}')
                else:
                    logger.info('No map process to close')
                    self.update_status('Map not running')
            except Exception as e:
                logger.error(f'Failed to close map: {e}', exc_info=True)
                self.update_status(f'Close error: {str(e)}')

    def on_marker_type_changed(self, *args, **kwargs):
        """Handle marker type change in DearPyGUI - Flexible callback signature"""
        try:
            app_data = args[1] if len(args) > 1 else kwargs.get('app_data', 'Ship')
            marker_type = app_data if app_data is not None else 'Ship'
            logger.debug(f'Marker type changed to: {marker_type}')
            self.send_marker_type(marker_type)
            self.update_status(f'Marker type: {marker_type}')
        except Exception as e:
            logger.error(f'Failed to handle marker type change: {e}', exc_info=True)

    def send_marker_type(self, marker_type):
        """Send marker type change to PyQt process"""
        try:
            command = f'set_marker_type:{marker_type}'
            self.send_command(command)
            logger.debug(f'Marker type command sent: {command}')
        except Exception as e:
            logger.error(f"Failed to send marker type '{marker_type}': {e}", exc_info=True)

    def add_marker(self, *args, **kwargs):
        """Add marker from inputs - Flexible callback signature"""
        with operation('add_marker'):
            try:
                title = dpg.get_value('marker_title') or 'New Marker'
                marker_type = dpg.get_value('marker_type') or 'Ship'
                lat = dpg.get_value('lat_input') or 0.0
                lng = dpg.get_value('lng_input') or 0.0
                marker_data = {'lat': float(lat), 'lng': float(lng), 'title': str(title), 'type': str(marker_type)}
                logger.info(f'Adding marker: {title} at ({lat}, {lng}) of type {marker_type}')
                self.markers_data.append(marker_data)
                self.save_markers()
                self.update_markers_table()
                self.update_marker_count()
                self.update_status(f'Added: {title}')
                if dpg.does_item_exist('marker_title'):
                    dpg.set_value('marker_title', '')
            except Exception as e:
                logger.error(f'Failed to add marker: {e}', exc_info=True)
                self.update_status(f'Add error: {str(e)}')

    def add_preset(self, *args, **kwargs):
        """Add preset location - Flexible callback signature"""
        preset_coords = {'Mumbai Port': (19.076, 72.8777, 'Port'), 'Shanghai Port': (31.2304, 121.4737, 'Port'), 'Singapore Port': (1.3521, 103.8198, 'Port'), 'Hong Kong Port': (22.3193, 114.1694, 'Port')}
        with operation('add_preset'):
            try:
                selected = dpg.get_value('preset_combo') or 'Mumbai Port'
                if selected in preset_coords:
                    lat, lng, marker_type = preset_coords[selected]
                    marker_data = {'lat': float(lat), 'lng': float(lng), 'title': str(selected), 'type': str(marker_type)}
                    logger.info(f'Adding preset marker: {selected}')
                    self.markers_data.append(marker_data)
                    self.save_markers()
                    self.update_markers_table()
                    self.update_marker_count()
                    self.update_status(f'Added: {selected}')
                else:
                    logger.warning(f'Unknown preset selected: {selected}')
            except Exception as e:
                logger.error(f'Failed to add preset: {e}', exc_info=True)
                self.update_status(f'Preset error: {str(e)}')

    def add_indian_ports(self, *args, **kwargs):
        """Add Indian ports - Flexible callback signature"""
        ports = [(19.076, 72.8777, 'Mumbai Port', 'Port'), (22.5726, 88.3639, 'Kolkata Port', 'Port'), (13.0827, 80.2707, 'Chennai Port', 'Port'), (9.9312, 76.2673, 'Cochin Port', 'Port')]
        logger.info('Adding Indian ports preset')
        self.add_multiple_markers(ports, 'Indian ports')

    def add_financial(self, *args, **kwargs):
        """Add financial centers - Flexible callback signature"""
        centers = [(19.1136, 72.8697, 'Mumbai Financial District', 'Bank'), (28.5355, 77.391, 'Delhi Financial District', 'Bank'), (1.2797, 103.8565, 'Singapore Financial Center', 'Bank')]
        logger.info('Adding financial centers preset')
        self.add_multiple_markers(centers, 'Financial centers')

    def add_multiple_markers(self, markers_list, description):
        """Add multiple markers"""
        with operation('add_multiple_markers', description=description, count=len(markers_list)):
            try:
                added = 0
                for lat, lng, title, marker_type in markers_list:
                    marker_data = {'lat': float(lat), 'lng': float(lng), 'title': str(title), 'type': str(marker_type)}
                    self.markers_data.append(marker_data)
                    added += 1
                if added > 0:
                    self.save_markers()
                    self.update_markers_table()
                    self.update_marker_count()
                    self.update_status(f'Added {added} {description}')
                    logger.info(f'Successfully added {added} {description}')
                else:
                    logger.warning(f'No markers were added for {description}')
            except Exception as e:
                logger.error(f'Failed to add {description}: {e}', exc_info=True)
                self.update_status(f'Bulk add error: {str(e)}')

    def toggle_routes(self, *args, **kwargs):
        """Toggle trade routes - Flexible callback signature"""
        try:
            logger.debug('Toggling trade routes')
            self.send_command('toggle_routes')
            self.update_status('Routes toggled')
        except Exception as e:
            logger.error(f'Failed to toggle routes: {e}', exc_info=True)
            self.update_status(f'Routes error: {str(e)}')

    def toggle_ships(self, *args, **kwargs):
        """Toggle live ships - Flexible callback signature"""
        try:
            logger.debug('Toggling live ships')
            self.send_command('toggle_ships')
            self.update_status('Ships toggled')
        except Exception as e:
            logger.error(f'Failed to toggle ships: {e}', exc_info=True)
            self.update_status(f'Ships error: {str(e)}')

    def clear_all(self, *args, **kwargs):
        """Clear all markers - Flexible callback signature"""
        with operation('clear_all'):
            try:
                logger.info(f'Clearing all {len(self.markers_data)} markers')
                self.markers_data = []
                self.save_markers()
                self.send_command('clear_all')
                self.update_markers_table()
                self.update_marker_count()
                self.update_status('Cleared all')
            except Exception as e:
                logger.error(f'Failed to clear all markers: {e}', exc_info=True)
                self.update_status(f'Clear error: {str(e)}')

    def update_markers_table(self):
        """Update markers table"""
        with operation('update_markers_table'):
            try:
                if not dpg.does_item_exist('markers_table'):
                    logger.warning('Markers table does not exist')
                    return
                try:
                    children = dpg.get_item_children('markers_table', slot=1)
                    if children:
                        for child in children:
                            try:
                                dpg.delete_item(child)
                            except Exception as e:
                                logger.debug(f'Could not delete table child {child}: {e}')
                except Exception as e:
                    logger.debug(f'Error clearing table children: {e}')
                markers_shown = self.markers_data[-6:]
                logger.debug(f'Updating table with {len(markers_shown)} markers')
                for marker in markers_shown:
                    try:
                        with dpg.table_row(parent='markers_table'):
                            title = str(marker.get('title', 'Unknown'))
                            title = title[:20] + '...' if len(title) > 20 else title
                            self.safe_add_text(title)
                            self.safe_add_text(str(marker.get('type', 'Unknown')))
                            self.safe_add_text(f'{marker.get('lat', 0):.2f}, {marker.get('lng', 0):.2f}')
                    except Exception as e:
                        logger.warning(f'Failed to add table row for marker: {e}')
                logger.debug('Markers table updated successfully')
            except Exception as e:
                logger.error(f'Failed to update markers table: {e}', exc_info=True)

    def update_marker_count(self):
        """Update marker count"""
        try:
            count = len(self.markers_data)
            if dpg.does_item_exist('marker_count'):
                dpg.set_value('marker_count', str(count))
                logger.debug(f'Updated marker count to {count}')
        except Exception as e:
            logger.error(f'Failed to update marker count: {e}', exc_info=True)

    def update_status(self, message):
        """Update status"""
        try:
            message = str(message).encode('ascii', 'replace').decode('ascii')
            if dpg.does_item_exist('status_text'):
                dpg.set_value('status_text', message)
            logger.info(f'Status: {message}')
        except Exception as e:
            logger.error(f"Failed to update status with message '{message}': {e}", exc_info=True)

    def cleanup(self):
        """Cleanup resources"""
        with operation('cleanup'):
            try:
                if self.map_process:
                    logger.info('Terminating map process during cleanup')
                    self.map_process.terminate()
                files_to_clean = [self.commands_file, self.status_file]
                for file_path in files_to_clean:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.debug(f'Cleaned up file: {file_path}')
                    except Exception as e:
                        logger.warning(f'Could not remove file {file_path}: {e}')
                logger.info('Maritime Maps tab cleanup completed')
            except Exception as e:
                logger.error(f'Error during cleanup: {e}', exc_info=True)

def safe_add_text(self, text, **kwargs):
    """Safely add text with error handling"""
    try:
        if not isinstance(text, str):
            text = str(text)
        text = text.encode('ascii', 'replace').decode('ascii')
        return dpg.add_text(text, **kwargs)
    except Exception as e:
        logger.error(f"Failed to add text '{text}': {e}", exc_info=True)
        try:
            return dpg.add_text('Text Error', **kwargs)
        except Exception as fallback_e:
            logger.critical(f'Fallback text creation also failed: {fallback_e}')
            return None

class SplashAuth:
    """Splash screen with optimized performance and preserved security"""

    def __init__(self, is_first_time_user=False):
        self.current_screen = 'welcome'
        self.is_first_time_user = is_first_time_user
        self.session_data = {'user_type': None, 'api_key': None, 'device_id': None, 'user_info': {}, 'authenticated': False, 'expires_at': None}
        self.context_created = False
        self.pending_email = None
        self._connection_pool = ConnectionPool()
        self._ui_cache = UICache()
        self._device_id_cache = None
        self._hardware_info_cache = None
        self._api_status_cache = {'status': None, 'expires': None}
        self._executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix='SplashAuth')
        self._auth_lock = threading.RLock()
        self._precompute_device_info()
        logger.info('Splash Auth initialized with optimizations', context={'api_url': config.get_api_url(), 'strict_mode': is_strict_mode(), 'first_time_user': is_first_time_user})

    def _precompute_device_info(self):
        """Pre-compute device information in background - optimized"""

        def _compute():
            try:
                with operation('precompute_device_info'):
                    self._device_id_cache = self._generate_device_id_internal()
                    self._hardware_info_cache = self._get_hardware_info_internal()
                    logger.debug('Device information precomputed successfully')
            except Exception as e:
                logger.error('Failed to precompute device info', context={'error': str(e)}, exc_info=True)
        self._executor.submit(_compute)

    @lru_cache(maxsize=1)
    def _generate_device_id_internal(self) -> str:
        """Generate unique device ID - cached and optimized"""
        try:
            with operation('generate_device_id'):
                mac_address = ':'.join(['{:02x}'.format(uuid.getnode() >> elements & 255) for elements in range(0, 2 * 6, 2)][::-1])
                system_info = f'{platform.system()}-{platform.node()}-{mac_address}'
                device_hash = hashlib.sha256(system_info.encode()).hexdigest()
                device_id = f'desktop_{device_hash[:16]}'
                logger.debug(f'Device ID generated: {device_id}')
                return device_id
        except Exception as e:
            logger.warning(f'Error generating device ID, using fallback: {e}')
            fallback_id = f'desktop_{uuid.uuid4().hex[:16]}'
            logger.debug(f'Fallback device ID: {fallback_id}')
            return fallback_id

    @lru_cache(maxsize=1)
    def _get_hardware_info_internal(self) -> Dict[str, Any]:
        """Get hardware fingerprint - cached and optimized"""
        try:
            with operation('get_hardware_info'):
                hardware_info = {'system': platform.system(), 'release': platform.release(), 'machine': platform.machine(), 'processor': platform.processor(), 'node': platform.node(), 'timestamp': datetime.now().isoformat()}
                logger.debug('Hardware information collected', context={'system': hardware_info['system']})
                return hardware_info
        except Exception as e:
            logger.error(f'Error collecting hardware info: {e}', exc_info=True)
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def generate_device_id(self) -> str:
        """Get cached device ID - optimized"""
        if self._device_id_cache is None:
            self._device_id_cache = self._generate_device_id_internal()
        return self._device_id_cache

    def get_hardware_info(self) -> Dict[str, Any]:
        """Get cached hardware info - optimized"""
        if self._hardware_info_cache is None:
            self._hardware_info_cache = self._get_hardware_info_internal()
        return self._hardware_info_cache

    def _is_api_cache_valid(self) -> bool:
        """Check if API status cache is still valid"""
        if self._api_status_cache['expires'] is None:
            return False
        return datetime.now() < self._api_status_cache['expires']

    @monitor_performance
    def check_api_connectivity(self) -> bool:
        """Check API connectivity with caching - optimized"""
        if self._is_api_cache_valid():
            return self._api_status_cache['status']
        try:
            with operation('api_connectivity_check'):
                logger.info('Checking API connectivity...')
                session = self._connection_pool.get_session()
                response = session.get(get_api_endpoint('/health'), timeout=config.CONNECTION_TIMEOUT)
                status = response.status_code == 200
                self._api_status_cache = {'status': status, 'expires': datetime.now() + timedelta(seconds=30)}
                if status:
                    logger.info('API server is available', context={'api_url': config.get_api_url()})
                else:
                    logger.warning(f'API server returned status {response.status_code}')
                return status
        except Exception as e:
            logger.error('API connectivity error', context={'error': str(e)}, exc_info=True)
            self._api_status_cache = {'status': False, 'expires': datetime.now() + timedelta(seconds=10)}
            return False

    def _get_dpg(self):
        """Get DearPyGui with lazy loading"""
        return _lazy_imports.get_dpg()

    def _create_ui_component(self, component_type: str, **kwargs) -> Any:
        """Create UI component with caching - optimized"""
        cache_key = f'{component_type}_{hash(str(sorted(kwargs.items())))}'
        if cache_key in self._ui_cache.components:
            return self._ui_cache.components[cache_key]
        try:
            dpg = self._get_dpg()
            component = getattr(dpg, component_type)(**kwargs)
            self._ui_cache.components[cache_key] = component
            return component
        except Exception as e:
            logger.error(f'Error creating UI component {component_type}: {e}')
            return None

    @monitor_performance
    def show_api_error_screen(self):
        """Show API connection error screen - optimized"""
        try:
            with operation('show_api_error_screen'):
                self.clear_content()
                dpg = self._get_dpg()
                parent = 'content_container'
                self.safe_add_spacer(30, parent)
                with dpg.group(horizontal=True, parent=parent):
                    dpg.add_spacer(width=100)
                    dpg.add_text('🚫 API Connection Error', color=[255, 100, 100])
                self.safe_add_spacer(30, parent)
                with dpg.child_window(width=460, height=350, border=True, parent=parent):
                    dpg.add_spacer(height=30)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Cannot connect to Fincept API server', color=[255, 150, 150])
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text(f'API URL: {config.get_api_url()}', color=[200, 200, 200])
                    dpg.add_spacer(height=15)
                    error_messages = ['• Check if the API server is running', '• Verify the API URL is correct', '• Check your internet connection', '• Ensure firewall is not blocking the connection']
                    for msg in error_messages:
                        with dpg.group(horizontal=True):
                            dpg.add_spacer(width=50)
                            dpg.add_text(msg, color=[200, 200, 200])
                        dpg.add_spacer(height=5)
                    dpg.add_spacer(height=30)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_button(label='🔄 Retry Connection', width=150, callback=self.retry_api_connection)
                        dpg.add_spacer(width=20)
                        dpg.add_button(label='❌ Exit', width=100, callback=self.close_splash_error)
                logger.debug('API error screen displayed')
        except Exception as e:
            logger.error(f'Error showing API error screen: {e}', exc_info=True)

    def retry_api_connection(self, *args, **kwargs):
        """Retry API connection with cache invalidation - optimized"""
        try:
            with operation('retry_api_connection'):
                self._api_status_cache = {'status': None, 'expires': None}
                logger.info('Retrying API connection...')
                if self.check_api_connectivity():
                    logger.info('API connection successful on retry')
                    self.create_welcome_screen()
                else:
                    logger.warning('API connection failed on retry')
                    self.show_api_error_screen()
        except Exception as e:
            logger.error(f'Error during API retry: {e}', exc_info=True)

    def close_splash_error(self, *args, **kwargs):
        """Close splash with error"""
        try:
            logger.info('Closing splash due to API error')
            dpg = self._get_dpg()
            dpg.stop_dearpygui()
        except Exception as e:
            logger.error(f'Error closing splash: {e}', exc_info=True)

    @monitor_performance
    def show_splash(self) -> Dict[str, Any]:
        """Show splash screen with performance optimizations"""
        try:
            with operation('show_splash'):
                logger.info('Creating splash screen with optimizations', context={'first_time_user': self.is_first_time_user})
                dpg = self._get_dpg()
                if not self.context_created:
                    dpg.create_context()
                    self.context_created = True
                    logger.debug('DearPyGui context created')
                api_future = None
                if is_strict_mode():
                    api_future = self._executor.submit(self.check_api_connectivity)
                    logger.debug('API connectivity check started in background')
                with dpg.window(tag='splash_window', label='Fincept Authentication', width=500, height=600, no_resize=True, no_move=True, no_collapse=True, no_close=True):
                    with dpg.group(tag='content_container'):
                        if is_strict_mode() and api_future:
                            try:
                                api_available = api_future.result(timeout=config.CONNECTION_TIMEOUT)
                                if not api_available:
                                    logger.warning('API not available in strict mode')
                                    self.show_api_error_screen()
                                else:
                                    logger.info('API available, showing welcome screen')
                                    self.create_welcome_screen()
                            except Exception as e:
                                logger.error(f'Error checking API availability: {e}', exc_info=True)
                                self.show_api_error_screen()
                        else:
                            self.create_welcome_screen()
                title = 'Fincept Terminal - Welcome!' if self.is_first_time_user else 'Fincept Terminal - Authentication'
                dpg.create_viewport(title=title, width=520, height=640, resizable=False)
                dpg.setup_dearpygui()
                dpg.set_primary_window('splash_window', True)
                logger.info('Splash screen created successfully')
                dpg.show_viewport()
                dpg.start_dearpygui()
        except Exception as e:
            logger.error('Splash screen error', context={'error': str(e)}, exc_info=True)
            if is_strict_mode():
                return {'authenticated': False, 'error': f'Splash initialization failed: {str(e)}'}
            else:
                logger.warning('Using secure fallback for guest access')
                return {'user_type': 'guest', 'authenticated': True, 'device_id': self.generate_device_id(), 'api_key': None, 'user_info': {}, 'expires_at': None}
        return self.session_data

    @monitor_performance
    def clear_content(self):
        """Safely clear content with batching - optimized"""
        try:
            with operation('clear_content'):
                dpg = self._get_dpg()
                if dpg.does_item_exist('content_container'):
                    children = dpg.get_item_children('content_container', 1)
                    delete_count = 0
                    for child in children:
                        if dpg.does_item_exist(child):
                            dpg.delete_item(child)
                            delete_count += 1
                    logger.debug(f'Cleared {delete_count} UI elements from content container')
        except Exception as e:
            logger.error('Error clearing content', context={'error': str(e)}, exc_info=True)

    def safe_add_spacer(self, height=10, parent='content_container'):
        """Safely add spacer - optimized with error handling"""
        try:
            dpg = self._get_dpg()
            if dpg.does_item_exist(parent):
                dpg.add_spacer(height=height, parent=parent)
        except Exception as e:
            logger.debug('Could not add spacer', context={'height': height, 'error': str(e)})

    @monitor_performance
    def create_welcome_screen(self):
        """Create welcome screen with optimized rendering"""
        try:
            with operation('create_welcome_screen'):
                self.clear_content()
                dpg = self._get_dpg()
                parent = 'content_container'
                self.safe_add_spacer(20, parent)
                with dpg.group(horizontal=True, parent=parent):
                    dpg.add_spacer(width=80)
                    dpg.add_text('🚀 FINCEPT', color=[255, 215, 0])
                with dpg.group(horizontal=True, parent=parent):
                    dpg.add_spacer(width=120)
                    dpg.add_text('FINANCIAL TERMINAL', color=[200, 200, 200])
                self.safe_add_spacer(10, parent)
                if self.is_first_time_user:
                    with dpg.group(horizontal=True, parent=parent):
                        dpg.add_spacer(width=140)
                        dpg.add_text('👋 Welcome to Fincept!', color=[100, 255, 100])
                else:
                    with dpg.group(horizontal=True, parent=parent):
                        dpg.add_spacer(width=120)
                        dpg.add_text('🔄 Session Expired - Please Sign In', color=[255, 255, 100])
                self.safe_add_spacer(20, parent)
                with dpg.group(horizontal=True, parent=parent):
                    dpg.add_spacer(width=60)
                    dpg.add_text(f'🌐 API: {config.get_api_url()}', color=[100, 255, 100])
                self.safe_add_spacer(30, parent)
                self.create_auth_cards(parent)
                self.safe_add_spacer(30, parent)
                with dpg.group(horizontal=True, parent=parent):
                    dpg.add_spacer(width=150)
                    mode_text = 'First Time' if self.is_first_time_user else 'Returning User'
                    dpg.add_text(f'API v{config.API_VERSION} - {mode_text}', color=[100, 100, 100])
                logger.debug('Welcome screen created successfully')
        except Exception as e:
            logger.error(f'Error creating welcome screen: {e}', exc_info=True)

    def create_auth_cards(self, parent):
        """Create authentication cards with optimized layout"""
        try:
            if self.is_first_time_user:
                self.create_guest_card(parent, emphasized=True)
                self.safe_add_spacer(15, parent)
                self.create_signin_card(parent, emphasized=False)
                self.safe_add_spacer(15, parent)
                self.create_signup_card(parent, emphasized=False)
            else:
                self.create_signin_card(parent, emphasized=True)
                self.safe_add_spacer(15, parent)
                self.create_guest_card(parent, emphasized=False)
                self.safe_add_spacer(15, parent)
                self.create_signup_card(parent, emphasized=False)
            logger.debug('Authentication cards created')
        except Exception as e:
            logger.error(f'Error creating auth cards: {e}', exc_info=True)

    def create_signin_card(self, parent, emphasized=False):
        """Create sign in card - optimized"""
        try:
            dpg = self._get_dpg()
            with dpg.child_window(width=460, height=100, border=True, parent=parent):
                if emphasized:
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=15)
                        dpg.add_text('🔑 RECOMMENDED', color=[100, 255, 100])
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=15)
                    dpg.add_text('🔐 Sign In', color=[100, 255, 100])
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=15)
                    text = 'Welcome back! Access your account' if not self.is_first_time_user else 'Access your account with permanent API key'
                    dpg.add_text(text, color=[200, 200, 200])
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=350)
                    dpg.add_button(label='Sign In', width=100, callback=self.go_to_login)
        except Exception as e:
            logger.error(f'Error creating signin card: {e}', exc_info=True)

    def create_guest_card(self, parent, emphasized=False):
        """Create guest card - optimized"""
        try:
            dpg = self._get_dpg()
            with dpg.child_window(width=460, height=100, border=True, parent=parent):
                if emphasized:
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=15)
                        dpg.add_text('⭐ QUICK START', color=[255, 255, 100])
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=15)
                    dpg.add_text('🎯 Guest Access', color=[255, 255, 100])
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=15)
                    text = '🚀 Try Fincept instantly! No signup required' if self.is_first_time_user else '50 requests/day with temporary API key'
                    dpg.add_text(text, color=[200, 200, 200])
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=280)
                    button_text = '🚀 Try Now!' if self.is_first_time_user else 'Continue as Guest'
                    button_width = 170 if self.is_first_time_user else 150
                    dpg.add_button(label=button_text, width=button_width, callback=self.setup_guest_access)
        except Exception as e:
            logger.error(f'Error creating guest card: {e}', exc_info=True)

    def create_signup_card(self, parent, emphasized=False):
        """Create signup card - optimized"""
        try:
            dpg = self._get_dpg()
            with dpg.child_window(width=460, height=100, border=True, parent=parent):
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=15)
                    dpg.add_text('✨ Create Account', color=[100, 150, 255])
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=15)
                    text = '🎁 Join Fincept for unlimited access'
                    dpg.add_text(text, color=[200, 200, 200])
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=340)
                    dpg.add_button(label='Sign Up', width=110, callback=self.go_to_signup)
        except Exception as e:
            logger.error(f'Error creating signup card: {e}', exc_info=True)

    @monitor_performance
    def create_login_screen(self):
        """Create login screen with optimized layout"""
        try:
            with operation('create_login_screen'):
                self.clear_content()
                dpg = self._get_dpg()
                parent = 'content_container'
                self.safe_add_spacer(30, parent)
                with dpg.group(horizontal=True, parent=parent):
                    dpg.add_spacer(width=180)
                    dpg.add_text('🔐 Sign In', color=[100, 255, 100])
                self.safe_add_spacer(30, parent)
                with dpg.child_window(width=460, height=350, border=True, parent=parent):
                    dpg.add_spacer(height=30)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Email Address:')
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_input_text(tag='login_email', width=400, hint='Enter your email')
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Password:')
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_input_text(tag='login_password', width=400, password=True, hint='Enter password')
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('', tag='login_status', color=[255, 100, 100])
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_button(label='🔐 Sign In', width=120, callback=self.attempt_login)
                        dpg.add_spacer(width=20)
                        dpg.add_button(label='⬅️ Back', width=120, callback=self.go_to_welcome)
                logger.debug('Login screen created successfully')
        except Exception as e:
            logger.error(f'Error creating login screen: {e}', exc_info=True)

    @monitor_performance
    def create_signup_screen(self):
        """Create signup screen - optimized"""
        try:
            with operation('create_signup_screen'):
                self.clear_content()
                dpg = self._get_dpg()
                parent = 'content_container'
                self.safe_add_spacer(20, parent)
                with dpg.group(horizontal=True, parent=parent):
                    dpg.add_spacer(width=170)
                    dpg.add_text('✨ Create Account', color=[100, 150, 255])
                self.safe_add_spacer(20, parent)
                with dpg.child_window(width=460, height=450, border=True, parent=parent):
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Username:')
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_input_text(tag='signup_username', width=400, hint='Choose username')
                    dpg.add_spacer(height=15)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Email Address:')
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_input_text(tag='signup_email', width=400, hint='Enter email')
                    dpg.add_spacer(height=15)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Password:')
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_input_text(tag='signup_password', width=400, password=True, hint='Create password')
                    dpg.add_spacer(height=15)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Confirm Password:')
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_input_text(tag='signup_confirm_password', width=400, password=True, hint='Confirm password')
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('', tag='signup_status', color=[255, 100, 100])
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_button(label='✨ Create Account', width=140, callback=self.attempt_signup)
                        dpg.add_spacer(width=20)
                        dpg.add_button(label='⬅️ Back', width=120, callback=self.go_to_welcome)
                logger.debug('Signup screen created successfully')
        except Exception as e:
            logger.error(f'Error creating signup screen: {e}', exc_info=True)

    @monitor_performance
    def create_otp_screen(self):
        """Create OTP verification screen - optimized"""
        try:
            with operation('create_otp_screen'):
                self.clear_content()
                dpg = self._get_dpg()
                parent = 'content_container'
                self.safe_add_spacer(50, parent)
                with dpg.group(horizontal=True, parent=parent):
                    dpg.add_spacer(width=160)
                    dpg.add_text('📧 Email Verification', color=[255, 255, 100])
                self.safe_add_spacer(30, parent)
                with dpg.child_window(width=460, height=300, border=True, parent=parent):
                    dpg.add_spacer(height=30)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Enter the 6-digit code sent to your email:', color=[200, 200, 200])
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Verification Code:')
                    dpg.add_spacer(height=10)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=130)
                        dpg.add_input_text(tag='otp_code', width=200, hint='6-digit code')
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('', tag='otp_status', color=[255, 100, 100])
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=80)
                        dpg.add_button(label='✅ Verify Code', width=120, callback=self.verify_otp)
                        dpg.add_spacer(width=20)
                        dpg.add_button(label='⬅️ Back', width=120, callback=self.go_to_signup)
                logger.debug('OTP screen created successfully')
        except Exception as e:
            logger.error(f'Error creating OTP screen: {e}', exc_info=True)

    @monitor_performance
    def create_guest_setup_screen(self):
        """Create guest setup screen - optimized"""
        try:
            with operation('create_guest_setup_screen'):
                self.clear_content()
                dpg = self._get_dpg()
                parent = 'content_container'
                self.safe_add_spacer(40, parent)
                with dpg.group(horizontal=True, parent=parent):
                    dpg.add_spacer(width=130)
                    dpg.add_text('🎯 Setting up Guest Access', color=[255, 255, 100])
                self.safe_add_spacer(30, parent)
                with dpg.child_window(width=460, height=350, border=True, parent=parent):
                    dpg.add_spacer(height=30)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Guest Features:', color=[100, 255, 100])
                    dpg.add_spacer(height=15)
                    features = ['📈 Financial market data access', '💹 Real-time stock prices & forex', '🔢 50 API requests per day', '⏰ 24-hour access period', '🔑 Temporary API key authentication']
                    for feature in features:
                        with dpg.group(horizontal=True):
                            dpg.add_spacer(width=50)
                            dpg.add_text(feature, color=[200, 255, 200])
                        dpg.add_spacer(height=5)
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=30)
                        dpg.add_text('Status: Creating guest API key...', tag='guest_status', color=[255, 255, 100])
                    dpg.add_spacer(height=20)
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=130)
                        dpg.add_button(label='🚀 Continue to Terminal', width=200, callback=self.complete_guest_setup, show=False, tag='guest_continue_btn')
                self._executor.submit(self.create_guest_session)
                logger.debug('Guest setup screen created successfully')
        except Exception as e:
            logger.error(f'Error creating guest setup screen: {e}', exc_info=True)

    def go_to_welcome(self, *args, **kwargs):
        logger.debug('Navigating to welcome screen')
        self.current_screen = 'welcome'
        self.create_welcome_screen()

    def go_to_login(self, *args, **kwargs):
        logger.debug('Navigating to login screen')
        self.current_screen = 'login'
        self.create_login_screen()

    def go_to_signup(self, *args, **kwargs):
        logger.debug('Navigating to signup screen')
        self.current_screen = 'signup'
        self.create_signup_screen()

    @monitor_performance
    def _make_api_request(self, method: str, endpoint: str, data: Optional[Dict]=None, headers: Optional[Dict]=None, timeout: Optional[int]=None) -> Tuple[bool, Dict]:
        """Optimized API request with connection pooling"""
        try:
            with operation('api_request', context={'method': method, 'endpoint': endpoint}):
                session = self._connection_pool.get_session()
                timeout = timeout or config.REQUEST_TIMEOUT
                request_start = time.time()
                if method.upper() == 'GET':
                    response = session.get(get_api_endpoint(endpoint), headers=headers, timeout=timeout)
                elif method.upper() == 'POST':
                    response = session.post(get_api_endpoint(endpoint), json=data, headers=headers, timeout=timeout)
                else:
                    logger.error(f'Unsupported HTTP method: {method}')
                    return (False, {'error': 'Unsupported HTTP method'})
                request_duration = time.time() - request_start
                if response.status_code == 200:
                    logger.debug(f'API request successful', context={'method': method, 'endpoint': endpoint, 'duration_ms': f'{request_duration * 1000:.2f}', 'status_code': response.status_code})
                    return (True, response.json())
                else:
                    logger.warning(f'API request failed', context={'method': method, 'endpoint': endpoint, 'status_code': response.status_code, 'duration_ms': f'{request_duration * 1000:.2f}'})
                    return (False, {'error': f'HTTP {response.status_code}', 'status_code': response.status_code})
        except Exception as e:
            logger.error(f'API request exception', context={'method': method, 'endpoint': endpoint, 'error': str(e)}, exc_info=True)
            return (False, {'error': str(e)})

    @monitor_performance
    def attempt_login(self, *args, **kwargs):
        """Attempt user login with optimized API calls"""
        with self._auth_lock:
            try:
                with operation('login_attempt'):
                    dpg = self._get_dpg()
                    email = dpg.get_value('login_email') if dpg.does_item_exist('login_email') else ''
                    password = dpg.get_value('login_password') if dpg.does_item_exist('login_password') else ''
                    if not email or not password:
                        self.update_status('login_status', 'Please fill in all fields')
                        return
                    logger.info('Attempting user login', context={'email': email})
                    self.update_status('login_status', '🔐 Signing in...')
                    success, response_data = self._make_api_request('POST', '/auth/login', {'email': email, 'password': password})
                    if success and response_data.get('success'):
                        data = response_data.get('data', {})
                        self.session_data.update({'user_type': 'registered', 'api_key': data.get('api_key'), 'authenticated': True, 'device_id': self.generate_device_id()})
                        self._executor.submit(self.fetch_user_profile)
                        self.update_status('login_status', '✅ Login successful! Opening terminal...')
                        logger.info('User login successful', context={'user_type': 'registered'})
                        threading.Timer(1.0, self.close_splash_success).start()
                    else:
                        error_msg = response_data.get('message', 'Login failed')
                        self.update_status('login_status', f'❌ {error_msg}')
                        logger.warning(f'Login failed: {error_msg}')
            except Exception as e:
                error_msg = f'❌ Error: {str(e)}'
                self.update_status('login_status', error_msg)
                logger.error('Login error', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def attempt_signup(self, *args, **kwargs):
        """Attempt user registration with optimized validation"""
        with self._auth_lock:
            try:
                with operation('signup_attempt'):
                    dpg = self._get_dpg()
                    username = dpg.get_value('signup_username') if dpg.does_item_exist('signup_username') else ''
                    email = dpg.get_value('signup_email') if dpg.does_item_exist('signup_email') else ''
                    password = dpg.get_value('signup_password') if dpg.does_item_exist('signup_password') else ''
                    confirm_password = dpg.get_value('signup_confirm_password') if dpg.does_item_exist('signup_confirm_password') else ''
                    if not all([username, email, password, confirm_password]):
                        self.update_status('signup_status', 'Please fill in all fields')
                        return
                    if password != confirm_password:
                        self.update_status('signup_status', 'Passwords do not match')
                        return
                    if len(password) < 6:
                        self.update_status('signup_status', 'Password must be at least 6 characters')
                        return
                    logger.info('Attempting user registration', context={'username': username, 'email': email})
                    self.update_status('signup_status', '✨ Creating account...')
                    success, response_data = self._make_api_request('POST', '/auth/register', {'username': username, 'email': email, 'password': password})
                    if success and response_data.get('success'):
                        self.pending_email = email
                        self.current_screen = 'otp_verify'
                        self.create_otp_screen()
                        logger.info('Registration successful, OTP sent', context={'email': email})
                    else:
                        error_msg = response_data.get('message', 'Registration failed')
                        self.update_status('signup_status', f'❌ {error_msg}')
                        logger.warning(f'Registration failed: {error_msg}')
            except Exception as e:
                error_msg = f'❌ Error: {str(e)}'
                self.update_status('signup_status', error_msg)
                logger.error('Signup error', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def verify_otp(self, *args, **kwargs):
        """Verify OTP code with optimized validation"""
        with self._auth_lock:
            try:
                with operation('otp_verification'):
                    dpg = self._get_dpg()
                    otp_code = dpg.get_value('otp_code') if dpg.does_item_exist('otp_code') else ''
                    if not otp_code or len(otp_code) != 6 or (not otp_code.isdigit()):
                        self.update_status('otp_status', 'Please enter valid 6-digit code')
                        return
                    logger.info('Verifying OTP code', context={'email': self.pending_email})
                    self.update_status('otp_status', '📧 Verifying...')
                    success, response_data = self._make_api_request('POST', '/auth/verify-otp', {'email': self.pending_email, 'otp': otp_code})
                    if success and response_data.get('success'):
                        data = response_data.get('data', {})
                        self.session_data.update({'user_type': 'registered', 'api_key': data.get('api_key'), 'authenticated': True, 'device_id': self.generate_device_id()})
                        self._executor.submit(self.fetch_user_profile)
                        self.update_status('otp_status', '✅ Success! Opening terminal...')
                        logger.info('OTP verification successful')
                        threading.Timer(1.0, self.close_splash_success).start()
                    else:
                        error_msg = response_data.get('message', 'Verification failed')
                        self.update_status('otp_status', f'❌ {error_msg}')
                        logger.warning(f'OTP verification failed: {error_msg}')
            except Exception as e:
                error_msg = f'❌ Error: {str(e)}'
                self.update_status('otp_status', error_msg)
                logger.error('OTP verification error', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def setup_guest_access(self, *args, **kwargs):
        """Setup guest access with background processing"""
        try:
            with operation('setup_guest_access'):
                logger.info('Setting up guest access')
                self.current_screen = 'guest_setup'
                self.create_guest_setup_screen()
        except Exception as e:
            logger.error('Error setting up guest access', context={'error': str(e)}, exc_info=True)
            if is_strict_mode():
                self.update_status('guest_status', f'❌ Guest setup failed: {str(e)}')
            else:
                logger.warning('Using secure fallback for guest access')
                self.session_data.update({'user_type': 'guest', 'device_id': self.generate_device_id(), 'authenticated': True, 'api_key': None})
                self.close_splash_success()

    @monitor_performance
    def create_guest_session(self):
        """Create guest session with optimized API integration"""
        try:
            with operation('create_guest_session'):
                device_id = self.generate_device_id()
                hardware_info = self.get_hardware_info()
                logger.info('Creating guest session', context={'device_id': device_id})

                def update_ui_safe(message):
                    try:
                        self.update_status('guest_status', message)
                    except:
                        logger.debug('Could not update UI status (UI may be destroyed)')
                update_ui_safe('🌐 Checking for existing session...')
                from fincept_terminal.utils.APIClient.api_client import FinceptAPIClient
                temp_session = {'user_type': 'guest', 'device_id': device_id}
                api_client = FinceptAPIClient(temp_session)
                result = api_client.get_or_create_guest_session(device_id=device_id, device_name=f'Fincept Terminal - {platform.system()}', platform='desktop', hardware_info=hardware_info)
                if result['success']:
                    guest_data = result.get('data', {})
                    message = result.get('message', 'Session ready')
                    with self._auth_lock:
                        self.session_data.update({'user_type': 'guest', 'device_id': device_id, 'api_key': guest_data.get('api_key') or guest_data.get('temp_api_key'), 'authenticated': True, 'expires_at': guest_data.get('expires_at'), 'daily_limit': guest_data.get('daily_limit', 50), 'requests_today': guest_data.get('requests_today', 0)})
                    update_ui_safe(f'✅ {message}!')
                    logger.info('Guest session created successfully', context={'api_key_present': bool(self.session_data.get('api_key')), 'daily_limit': guest_data.get('daily_limit', 50)})
                    try:
                        dpg = self._get_dpg()
                        if dpg.does_item_exist('guest_continue_btn'):
                            dpg.show_item('guest_continue_btn')
                    except:
                        logger.debug('Could not show continue button')
                else:
                    error_msg = result.get('error', 'Unknown error')
                    update_ui_safe(f'❌ Session setup failed: {error_msg}')
                    logger.error('Guest session setup failed', context={'error': error_msg, 'device_id': device_id})
        except Exception as e:
            try:
                self.update_status('guest_status', f'❌ Guest creation failed: {str(e)}')
            except:
                pass
            logger.error('Guest session creation error', context={'error': str(e)}, exc_info=True)

    def complete_guest_setup(self, *args, **kwargs):
        """Complete guest setup"""
        logger.info('Completing guest setup')
        self.close_splash_success()

    @monitor_performance
    def fetch_user_profile(self):
        """Fetch user profile with optimized API call"""
        try:
            with operation('fetch_user_profile'):
                if not self.session_data.get('api_key'):
                    logger.warning('No API key available for profile fetch')
                    return
                success, response_data = self._make_api_request('GET', '/user/profile', headers={'X-API-Key': self.session_data['api_key']})
                if success and response_data.get('success'):
                    with self._auth_lock:
                        self.session_data['user_info'] = response_data.get('data', {})
                    logger.info('User profile fetched from API')
                else:
                    logger.warning('Failed to fetch user profile from API')
        except Exception as e:
            logger.error('Failed to fetch profile from API', context={'error': str(e)}, exc_info=True)

    def update_status(self, tag: str, message: str):
        """Thread-safe status update - optimized"""
        try:
            dpg = self._get_dpg()
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, message)
        except Exception as e:
            logger.debug('Could not update status', context={'tag': tag, 'message': message, 'error': str(e)})

    def close_splash_success(self):
        """Close splash successfully with cleanup"""
        try:
            logger.info('Closing splash screen successfully', context={'user_type': self.session_data.get('user_type')})
            dpg = self._get_dpg()
            dpg.stop_dearpygui()
        except Exception as e:
            logger.error('Error closing splash', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def cleanup(self):
        """Enhanced cleanup with resource management - optimized"""
        try:
            with operation('splash_cleanup'):
                logger.info('🧹 Cleaning up splash screen...')
                if hasattr(self, '_executor'):
                    try:
                        self._executor.shutdown(wait=True, timeout=5.0)
                        logger.debug('Thread pool shutdown completed')
                    except Exception as e:
                        logger.warning(f'Thread pool shutdown error: {e}')
                if hasattr(self, '_connection_pool'):
                    try:
                        self._connection_pool.close()
                        logger.debug('Connection pool closed')
                    except Exception as e:
                        logger.warning(f'Connection pool cleanup error: {e}')
                if hasattr(self, '_ui_cache'):
                    self._ui_cache.components.clear()
                    logger.debug('UI cache cleared')
                try:
                    self._generate_device_id_internal.cache_clear()
                    self._get_hardware_info_internal.cache_clear()
                    logger.debug('LRU caches cleared')
                except:
                    pass
                if self.context_created:
                    try:
                        dpg = self._get_dpg()
                        dpg.destroy_context()
                        self.context_created = False
                        logger.debug('DearPyGui context destroyed')
                    except Exception as e:
                        logger.warning(f'DPG context cleanup error: {e}')
                logger.info('Splash screen cleanup completed')
        except Exception as e:
            logger.error('Cleanup error', context={'error': str(e)}, exc_info=True)

    def __del__(self):
        """Destructor with resource cleanup"""
        try:
            self.cleanup()
        except:
            pass

@lru_cache(maxsize=1)
def _generate_device_id_internal(self) -> str:
    """Generate unique device ID - cached and optimized"""
    try:
        with operation('generate_device_id'):
            mac_address = ':'.join(['{:02x}'.format(uuid.getnode() >> elements & 255) for elements in range(0, 2 * 6, 2)][::-1])
            system_info = f'{platform.system()}-{platform.node()}-{mac_address}'
            device_hash = hashlib.sha256(system_info.encode()).hexdigest()
            device_id = f'desktop_{device_hash[:16]}'
            logger.debug(f'Device ID generated: {device_id}')
            return device_id
    except Exception as e:
        logger.warning(f'Error generating device ID, using fallback: {e}')
        fallback_id = f'desktop_{uuid.uuid4().hex[:16]}'
        logger.debug(f'Fallback device ID: {fallback_id}')
        return fallback_id

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

def generate_key(self, source: str, params: Dict) -> str:
    """Generate cache key from parameters"""
    param_str = json.dumps(params, sort_keys=True)
    return f'{source}:{hashlib.md5(param_str.encode()).hexdigest()}'

class FyersTab(BaseTab):
    """Optimized Fyers Trading Tab for stock data streaming and API integration"""

    def __init__(self, app):
        super().__init__(app)
        self.tag_prefix = f'fyers_{id(self)}_'
        self.config_dir = self._get_config_directory()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.credentials = {'client_id': '', 'pin': '', 'app_id': '', 'app_type': '', 'app_secret': '', 'totp_secret_key': '', 'redirect_uri': 'https://trade.fyers.in/api-login/redirect-uri/index.html'}
        self.BASE_URL = 'https://api-t2.fyers.in/vagator/v2'
        self.BASE_URL_2 = 'https://api-t1.fyers.in/api/v3'
        self._lock = threading.RLock()
        self.access_token = None
        self.is_connected = False
        self.websocket_client = None
        self.streaming_data = []
        self.max_streaming_rows = 1000
        self.previous_prices = {}
        self.is_paused = False
        self.session_start_time = None
        self.message_count = 0
        self.last_message_time = None
        self.current_symbols = ['NSE:SBIN-EQ', 'NSE:ADANIENT-EQ']
        self.current_data_type = 'DepthUpdate'
        self._last_table_update = None
        self._last_stats_update = None
        self.update_throttle_interval = 0.5
        self.load_access_token_on_startup()
        info('FyersTab initialized', context={'config_dir': str(self.config_dir)})

    def _get_config_directory(self) -> Path:
        """Get platform-specific config directory - uses .fincept folder"""
        config_dir = Path.home() / '.fincept' / 'fyers'
        return config_dir

    def get_label(self):
        return ' Fyers Trading'

    def get_tag(self, tag_name: str) -> str:
        """Generate unique tag with prefix"""
        return f'{self.tag_prefix}{tag_name}'

    def safe_add_item(self, add_func, *args, **kwargs):
        """Safely add DearPyGUI item with tag checking"""
        if 'tag' in kwargs:
            tag = kwargs['tag']
            if dpg.does_item_exist(tag):
                try:
                    dpg.delete_item(tag)
                except:
                    pass
        return add_func(*args, **kwargs)

    def safe_set_value(self, tag: str, value: Any):
        """Safely set value with existence check"""
        try:
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)
        except Exception as e:
            warning(f'Error setting value for {tag}: {e}')

    def safe_configure_item(self, tag: str, **kwargs):
        """Safely configure item with existence check"""
        try:
            if dpg.does_item_exist(tag):
                dpg.configure_item(tag, **kwargs)
        except Exception as e:
            warning(f'Error configuring item {tag}: {e}')

    @monitor_performance
    def create_content(self):
        """Create the Fyers trading interface with error handling"""
        with operation('create_fyers_content'):
            try:
                self.cleanup_existing_items()
                self.add_section_header(' Fyers Trading Platform')
                if not FYERS_AVAILABLE:
                    dpg.add_text(' Fyers API not available!')
                    dpg.add_text('Install with: pip install fyers-apiv3')
                    dpg.add_text('Command: pip install fyers-apiv3')
                    return
                self.create_auth_panel()
                dpg.add_spacer(height=10)
                self.create_streaming_panel()
                dpg.add_spacer(height=10)
                self.create_data_viewer()
                info('Fyers tab content created successfully')
            except Exception as e:
                error('Error creating Fyers tab content', context={'error': str(e)}, exc_info=True)
                try:
                    dpg.add_text(f' Error creating interface: {str(e)}')
                    dpg.add_text('Please restart the application or check logs.')
                except:
                    pass

    def cleanup_existing_items(self):
        """Clean up any existing items with our tag prefix"""
        try:
            all_items = dpg.get_all_items()
            for item in all_items:
                try:
                    alias = dpg.get_item_alias(item)
                    if alias and alias.startswith(self.tag_prefix):
                        dpg.delete_item(item)
                except:
                    continue
        except Exception as e:
            warning(f'Warning during cleanup: {e}')

    def create_auth_panel(self):
        """Create authentication and token management panel"""
        with dpg.collapsing_header(label=' Authentication & Token Management', default_open=True):
            with dpg.group(horizontal=True):
                with self.create_child_window('credentials_panel', width=400, height=320):
                    dpg.add_text('Fyers API Credentials')
                    dpg.add_separator()
                    self.safe_add_item(dpg.add_input_text, label='Client ID', default_value=self.credentials['client_id'], tag=self.get_tag('fyers_client_id'), width=200)
                    self.safe_add_item(dpg.add_input_text, label='PIN', default_value=self.credentials['pin'], tag=self.get_tag('fyers_pin'), password=True, width=200)
                    self.safe_add_item(dpg.add_input_text, label='App ID', default_value=self.credentials['app_id'], tag=self.get_tag('fyers_app_id'), width=200)
                    self.safe_add_item(dpg.add_input_text, label='App Type', default_value=self.credentials['app_type'], tag=self.get_tag('fyers_app_type'), width=200)
                    self.safe_add_item(dpg.add_input_text, label='App Secret', default_value=self.credentials['app_secret'], tag=self.get_tag('fyers_app_secret'), password=True, width=200)
                    self.safe_add_item(dpg.add_input_text, label='TOTP Secret', default_value=self.credentials['totp_secret_key'], tag=self.get_tag('fyers_totp_secret'), password=True, width=200)
                    dpg.add_spacer(height=10)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label=' Generate Token', callback=self.generate_access_token, width=120)
                        dpg.add_button(label=' Load Token', callback=self.load_access_token, width=100)
                        dpg.add_button(label=' Save Config', callback=self.save_credentials, width=100)
                with self.create_child_window('auth_status_panel', width=390, height=320):
                    dpg.add_text('Authentication Status')
                    dpg.add_separator()
                    self.safe_add_item(dpg.add_text, 'Status: Not Authenticated', tag=self.get_tag('auth_status_text'), color=(255, 100, 100))
                    self.safe_add_item(dpg.add_text, 'Token: None', tag=self.get_tag('token_status'))
                    self.safe_add_item(dpg.add_text, 'Generated: Never', tag=self.get_tag('token_generated_time'))
                    self.safe_add_item(dpg.add_text, 'Valid Until: Unknown', tag=self.get_tag('token_validity'))
                    dpg.add_spacer(height=10)
                    dpg.add_text('Token File Status:')
                    self.safe_add_item(dpg.add_text, 'access_token.log: Not Found', tag=self.get_tag('token_file_status'))
                    dpg.add_spacer(height=10)
                    with dpg.child_window(height=120, tag=self.get_tag('auth_log')):
                        self.safe_add_item(dpg.add_text, 'Ready for authentication...', tag=self.get_tag('auth_log_text'), wrap=370)

    def create_streaming_panel(self):
        """Create WebSocket streaming control panel"""
        with dpg.collapsing_header(label=' Real-time Data Streaming', default_open=True):
            with dpg.group(horizontal=True):
                with self.create_child_window('connection_controls', width=300, height=280):
                    dpg.add_text('WebSocket Connection')
                    dpg.add_separator()
                    self.safe_add_item(dpg.add_text, 'Status: Disconnected', tag=self.get_tag('ws_status_text'), color=(255, 100, 100))
                    self.safe_add_item(dpg.add_text, 'Data Type: None', tag=self.get_tag('ws_data_type'))
                    self.safe_add_item(dpg.add_text, 'Symbols: None', tag=self.get_tag('ws_symbols'))
                    self.safe_add_item(dpg.add_text, 'Messages Received: 0', tag=self.get_tag('ws_message_count'))
                    dpg.add_spacer(height=10)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label=' Connect', callback=self.connect_websocket, width=90)
                        dpg.add_button(label=' Disconnect', callback=self.disconnect_websocket, width=90)
                    dpg.add_spacer(height=10)
                    dpg.add_text('Connection Health:')
                    self.safe_add_item(dpg.add_text, 'Ping: Unknown', tag=self.get_tag('ws_ping'))
                    self.safe_add_item(dpg.add_text, 'Reconnects: 0', tag=self.get_tag('ws_reconnects'))
                with self.create_child_window('streaming_settings', width=250, height=280):
                    dpg.add_text('Streaming Settings')
                    dpg.add_separator()
                    dpg.add_text('Data Type:')
                    self.safe_add_item(dpg.add_combo, ['SymbolUpdate', 'DepthUpdate'], default_value=self.current_data_type, tag=self.get_tag('stream_data_type'), width=-1)
                    dpg.add_spacer(height=10)
                    dpg.add_text('Stock Symbols:')
                    self.safe_add_item(dpg.add_input_text, hint='NSE:SBIN-EQ,NSE:ADANIENT-EQ', default_value=','.join(self.current_symbols), tag=self.get_tag('stream_symbols'), width=-1, multiline=True, height=80)
                    dpg.add_spacer(height=10)
                    dpg.add_button(label=' Update Subscription', callback=self.update_subscription, width=-1)
                    dpg.add_spacer(height=10)
                    dpg.add_text('Quick Symbols:')
                    with dpg.group(horizontal=True):
                        dpg.add_button(label='NIFTY50', callback=lambda: self.set_quick_symbols('nifty50'), width=60)
                        dpg.add_button(label='BANKNIFTY', callback=lambda: self.set_quick_symbols('banknifty'), width=80)
                with self.create_child_window('streaming_stats', width=240, height=280):
                    dpg.add_text('Streaming Statistics')
                    dpg.add_separator()
                    self.safe_add_item(dpg.add_text, 'Session Time: 00:00:00', tag=self.get_tag('session_time'))
                    self.safe_add_item(dpg.add_text, 'Data Points: 0', tag=self.get_tag('data_points_count'))
                    self.safe_add_item(dpg.add_text, 'Last Update: Never', tag=self.get_tag('last_update_time'))
                    self.safe_add_item(dpg.add_text, 'Data Rate: 0 msg/sec', tag=self.get_tag('data_rate'))
                    dpg.add_spacer(height=10)
                    dpg.add_text('Max Display Rows:')
                    self.safe_add_item(dpg.add_combo, [100, 500, 1000, 2000], default_value=1000, tag=self.get_tag('max_display_rows'), callback=self.on_max_rows_changed, width=-1)
                    dpg.add_spacer(height=10)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label='Clear', callback=self.clear_streaming_data, width=60)
                        dpg.add_button(label='Stats', callback=self.show_detailed_stats, width=60)

    def create_data_viewer(self):
        """Create real-time data viewer"""
        with dpg.collapsing_header(label='Live Data Feed', default_open=True):
            with dpg.group(horizontal=True):
                with dpg.group():
                    with dpg.group(horizontal=True):
                        self.safe_add_item(dpg.add_button, label='Pause', tag=self.get_tag('pause_button'), callback=self.toggle_pause, width=80)
                        dpg.add_button(label='Export', callback=self.export_data, width=80)
                        dpg.add_button(label='Refresh', callback=self.force_refresh_table, width=80)
                        dpg.add_text('Auto-scroll:')
                        self.safe_add_item(dpg.add_checkbox, tag=self.get_tag('auto_scroll'), default_value=True)
                    with dpg.group(horizontal=True):
                        dpg.add_text('Filter Symbol:')
                        self.safe_add_item(dpg.add_input_text, tag=self.get_tag('symbol_filter'), width=120, callback=self.on_symbol_filter_changed)
                        dpg.add_text('Update Rate:')
                        self.safe_add_item(dpg.add_combo, ['Real-time', '1 sec', '2 sec', '5 sec'], default_value='Real-time', tag=self.get_tag('update_rate'), callback=self.on_update_rate_changed, width=100)
            dpg.add_spacer(height=5)
            with self.create_child_window('live_data_viewer', width=-1, height=450):
                self.safe_add_item(dpg.add_text, 'Connect to WebSocket to see live data...', tag=self.get_tag('data_viewer_status'))
                with dpg.group(tag=self.get_tag('live_data_table_container')):
                    pass

    def load_access_token_on_startup(self):
        """Load access token on startup if available"""
        with operation('load_token_on_startup'):
            try:
                token_path = self.config_dir / 'access_token.log'
                if token_path.exists():
                    with open(token_path, 'r', encoding='utf-8') as f:
                        tokens = [line.strip() for line in f if line.strip()]
                    if tokens:
                        self.access_token = tokens[-1]
                        info('Access token loaded on startup', context={'token_file': str(token_path)})
            except Exception as e:
                warning('Could not load token on startup', context={'error': str(e)})

    @monitor_performance
    def save_credentials(self):
        """Save credentials to config file"""
        with operation('save_credentials'):
            try:
                config = {'client_id': dpg.get_value(self.get_tag('fyers_client_id')), 'app_id': dpg.get_value(self.get_tag('fyers_app_id')), 'app_type': dpg.get_value(self.get_tag('fyers_app_type')), 'redirect_uri': self.credentials['redirect_uri']}
                config_path = self.config_dir / 'fyers_config.json'
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                self.update_auth_log('Credentials saved to fyers_config.json')
                info('Fyers credentials saved', context={'config_path': str(config_path)})
            except Exception as e:
                error_msg = f'Error saving credentials: {str(e)}'
                self.update_auth_log(error_msg)
                error('Failed to save credentials', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def generate_access_token(self):
        """Generate new access token using Fyers authentication flow"""

        def auth_thread():
            with operation('generate_access_token'):
                try:
                    with self._lock:
                        self.update_auth_log(' Starting authentication process...')
                        credentials = {'client_id': dpg.get_value(self.get_tag('fyers_client_id')), 'pin': dpg.get_value(self.get_tag('fyers_pin')), 'app_id': dpg.get_value(self.get_tag('fyers_app_id')), 'app_type': dpg.get_value(self.get_tag('fyers_app_type')), 'app_secret': dpg.get_value(self.get_tag('fyers_app_secret')), 'totp_secret': dpg.get_value(self.get_tag('fyers_totp_secret'))}
                        missing_fields = [k for k, v in credentials.items() if not v.strip()]
                        if missing_fields:
                            self.update_auth_log(f' Missing fields: {', '.join(missing_fields)}')
                            return
                        request_key = None
                        totp = None
                        status, request_key = self.verify_client_id(credentials['client_id'])
                        if status != 1:
                            self.update_auth_log(f'Client ID verification failed: {request_key}')
                            return
                        self.update_auth_log(' Client ID verified')
                        status, totp = self.generate_totp(credentials['totp_secret'])
                        if status != 1:
                            self.update_auth_log(f'TOTP generation failed: {totp}')
                            return
                        self.update_auth_log(' TOTP generated')
                        status, request_key = self.verify_totp(request_key, totp)
                        if status != 1:
                            self.update_auth_log(f'TOTP verification failed: {request_key}')
                            return
                        self.update_auth_log('TOTP verified')
                        status, fyers_access_token = self.verify_pin(request_key, credentials['pin'])
                        if status != 1:
                            self.update_auth_log(f'PIN verification failed: {fyers_access_token}')
                            return
                        self.update_auth_log('PIN verified')
                        status, auth_code = self.get_token(credentials['client_id'], credentials['app_id'], self.credentials['redirect_uri'], credentials['app_type'], fyers_access_token)
                        if status != 1:
                            self.update_auth_log(f'Token generation failed: {auth_code}')
                            return
                        self.update_auth_log('Auth code received')
                        status, v3_access = self.validate_authcode(auth_code, credentials['app_id'], credentials['app_type'], credentials['app_secret'])
                        if status != 1:
                            self.update_auth_log(f'Auth code validation failed: {v3_access}')
                            return
                        self.update_auth_log('Access token validated')
                        self.access_token = f'{credentials['app_id']}-{credentials['app_type']}:{v3_access}'
                        self.save_access_token()
                        self.update_auth_status()
                        self.update_auth_log(' Authentication completed successfully!')
                        info('Fyers authentication completed successfully')
                except Exception as e:
                    error_msg = f'Authentication error: {str(e)}'
                    self.update_auth_log(error_msg)
                    error('Authentication failed', context={'error': str(e)}, exc_info=True)
        threading.Thread(target=auth_thread, daemon=True).start()

    def load_access_token(self):
        """Load access token from file"""
        with operation('load_access_token'):
            try:
                token_path = self.config_dir / 'access_token.log'
                if not token_path.exists():
                    self.update_auth_log('access_token.log file not found')
                    return
                with open(token_path, 'r', encoding='utf-8') as f:
                    tokens = [line.strip() for line in f if line.strip()]
                if not tokens:
                    self.update_auth_log('No tokens found in access_token.log')
                    return
                with self._lock:
                    self.access_token = tokens[-1]
                self.update_auth_status()
                self.update_auth_log('Access token loaded from file')
                info('Access token loaded from file', context={'token_file': str(token_path)})
            except Exception as e:
                error_msg = f' Error loading token: {str(e)}'
                self.update_auth_log(error_msg)
                error('Failed to load token', context={'error': str(e)}, exc_info=True)

    def save_access_token(self):
        """Save access token to file"""
        try:
            token_path = self.config_dir / 'access_token.log'
            with open(token_path, 'a', encoding='utf-8') as f:
                f.write(f'{self.access_token}\n')
            self.update_auth_log(' Token saved to access_token.log')
            info('Token saved', context={'token_file': str(token_path)})
        except Exception as e:
            error_msg = f' Error saving token: {str(e)}'
            self.update_auth_log(error_msg)
            error('Failed to save token', context={'error': str(e)}, exc_info=True)

    def verify_client_id(self, client_id: str) -> Tuple[int, str]:
        """Verify client ID with Fyers API"""
        try:
            payload = {'fy_id': client_id, 'app_id': '2'}
            resp = requests.post(url=f'{self.BASE_URL}/send_login_otp', json=payload, timeout=30)
            if resp.status_code != 200:
                return [-1, f'HTTP {resp.status_code}: {resp.text}']
            data = resp.json()
            debug('Client ID verified successfully', context={'client_id': client_id})
            return [1, data['request_key']]
        except requests.exceptions.Timeout:
            return [-1, 'Request timeout']
        except requests.exceptions.RequestException as e:
            return [-1, f'Network error: {str(e)}']
        except Exception as e:
            return [-1, str(e)]

    def generate_totp(self, secret: str) -> Tuple[int, str]:
        """Generate TOTP code"""
        try:
            if not secret.strip():
                return [-1, 'TOTP secret is empty']
            totp = pyotp.TOTP(secret).now()
            debug('TOTP generated successfully')
            return [1, totp]
        except Exception as e:
            return [-1, f'TOTP generation error: {str(e)}']

    def verify_totp(self, request_key: str, totp: str) -> Tuple[int, str]:
        """Verify TOTP with Fyers API"""
        try:
            payload = {'request_key': request_key, 'otp': totp}
            resp = requests.post(url=f'{self.BASE_URL}/verify_otp', json=payload, timeout=30)
            if resp.status_code != 200:
                return [-1, f'HTTP {resp.status_code}: {resp.text}']
            data = resp.json()
            debug('TOTP verified successfully')
            return [1, data['request_key']]
        except requests.exceptions.Timeout:
            return [-1, 'Request timeout']
        except requests.exceptions.RequestException as e:
            return [-1, f'Network error: {str(e)}']
        except Exception as e:
            return [-1, str(e)]

    def verify_pin(self, request_key: str, pin: str) -> Tuple[int, str]:
        """Verify PIN with Fyers API"""
        try:
            payload = {'request_key': request_key, 'identity_type': 'pin', 'identifier': pin}
            resp = requests.post(url=f'{self.BASE_URL}/verify_pin', json=payload, timeout=30)
            if resp.status_code != 200:
                return [-1, f'HTTP {resp.status_code}: {resp.text}']
            data = resp.json()
            debug('PIN verified successfully')
            return [1, data['data']['access_token']]
        except requests.exceptions.Timeout:
            return [-1, 'Request timeout']
        except requests.exceptions.RequestException as e:
            return [-1, f'Network error: {str(e)}']
        except Exception as e:
            return [-1, str(e)]

    def get_token(self, client_id: str, app_id: str, redirect_uri: str, app_type: str, access_token: str) -> Tuple[int, str]:
        """Get authorization token"""
        try:
            payload = {'fyers_id': client_id, 'app_id': app_id, 'redirect_uri': redirect_uri, 'appType': app_type, 'code_challenge': '', 'state': 'sample_state', 'scope': '', 'nonce': '', 'response_type': 'code', 'create_cookie': True}
            headers = {'Authorization': f'Bearer {access_token}'}
            resp = requests.post(url=f'{self.BASE_URL_2}/token', json=payload, headers=headers, timeout=30)
            if resp.status_code != 308:
                return [-1, f'HTTP {resp.status_code}: {resp.text}']
            data = resp.json()
            url = data['Url']
            auth_code = parse.parse_qs(parse.urlparse(url).query)['auth_code'][0]
            debug('Authorization token received successfully')
            return [1, auth_code]
        except requests.exceptions.Timeout:
            return [-1, 'Request timeout']
        except requests.exceptions.RequestException as e:
            return [-1, f'Network error: {str(e)}']
        except Exception as e:
            return [-1, str(e)]

    def validate_authcode(self, auth_code: str, app_id: str, app_type: str, app_secret: str) -> Tuple[int, str]:
        """Validate authorization code"""
        try:
            app_id_hash = hashlib.sha256(f'{app_id}-{app_type}:{app_secret}'.encode()).hexdigest()
            payload = {'grant_type': 'authorization_code', 'appIdHash': app_id_hash, 'code': auth_code}
            resp = requests.post(url=f'{self.BASE_URL_2}/validate-authcode', json=payload, timeout=30)
            if resp.status_code != 200:
                return [-1, f'HTTP {resp.status_code}: {resp.text}']
            data = resp.json()
            debug('Authorization code validated successfully')
            return [1, data['access_token']]
        except requests.exceptions.Timeout:
            return [-1, 'Request timeout']
        except requests.exceptions.RequestException as e:
            return [-1, f'Network error: {str(e)}']
        except Exception as e:
            return [-1, str(e)]

    @monitor_performance
    def connect_websocket(self):
        """Connect to Fyers WebSocket with enhanced error handling"""
        if not self.access_token:
            self.update_auth_log(' No access token available. Generate token first.')
            return

        def connect_thread():
            with operation('connect_websocket'):
                try:
                    with self._lock:
                        if self.is_connected:
                            self.update_auth_log(' Already connected to WebSocket')
                            return
                    self.update_auth_log(' Connecting to WebSocket...')
                    self.websocket_client = data_ws.FyersDataSocket(access_token=self.access_token, log_path='', litemode=False, write_to_file=False, reconnect=True, on_connect=self.on_websocket_open, on_close=self.on_websocket_close, on_error=self.on_websocket_error, on_message=self.on_websocket_message)
                    with self._lock:
                        self.session_start_time = datetime.datetime.now()
                        self.message_count = 0
                    self.websocket_client.connect()
                    info('WebSocket connection initiated')
                except Exception as e:
                    error_msg = f' WebSocket connection failed: {str(e)}'
                    self.update_auth_log(error_msg)
                    error('WebSocket connection failed', context={'error': str(e)}, exc_info=True)
        threading.Thread(target=connect_thread, daemon=True).start()

    def disconnect_websocket(self):
        """Enhanced WebSocket disconnection"""
        with operation('disconnect_websocket'):
            try:
                self.update_auth_log(' Disconnecting WebSocket...')
                with self._lock:
                    self.is_connected = False
                    self.is_paused = True
                if self.websocket_client:
                    disconnect_methods = [('disconnect', lambda: self.websocket_client.disconnect()), ('close', lambda: self.websocket_client.close()), ('stop', lambda: self.websocket_client.stop())]
                    for method_name, method_func in disconnect_methods:
                        try:
                            if hasattr(self.websocket_client, method_name):
                                method_func()
                                self.update_auth_log(f' Called {method_name}() method')
                        except Exception as e:
                            warning(f'Warning calling {method_name}: {e}')
                    self.websocket_client = None
                    self.update_auth_log(' WebSocket client reference cleared')
                self.safe_set_value(self.get_tag('ws_status_text'), 'Status: Disconnected')
                self.safe_configure_item(self.get_tag('ws_status_text'), color=(255, 100, 100))
                self.safe_set_value(self.get_tag('ws_data_type'), 'Data Type: None')
                self.safe_set_value(self.get_tag('ws_symbols'), 'Symbols: None')
                self.safe_set_value(self.get_tag('ws_message_count'), 'Messages Received: 0')
                self.safe_set_value(self.get_tag('pause_button'), ' Paused')
                self.update_auth_log(' WebSocket disconnected successfully')
                info('WebSocket disconnected')
            except Exception as e:
                error_msg = f' Disconnect error: {str(e)}'
                self.update_auth_log(error_msg)
                error('WebSocket disconnect error', context={'error': str(e)}, exc_info=True)
                with self._lock:
                    self.is_connected = False
                    self.is_paused = True
                self.safe_set_value(self.get_tag('ws_status_text'), 'Status: Force Disconnected')
                self.safe_configure_item(self.get_tag('ws_status_text'), color=(255, 100, 100))

    def on_websocket_open(self):
        """WebSocket open callback with enhanced setup"""
        try:
            with self._lock:
                self.is_connected = True
                self.is_paused = False
                self.session_start_time = datetime.datetime.now()
            self.safe_set_value(self.get_tag('ws_status_text'), 'Status: Connected')
            self.safe_configure_item(self.get_tag('ws_status_text'), color=(100, 255, 100))
            self.safe_set_value(self.get_tag('pause_button'), ' Pause')
            data_type = dpg.get_value(self.get_tag('stream_data_type'))
            symbols_text = dpg.get_value(self.get_tag('stream_symbols'))
            symbols = [s.strip() for s in symbols_text.split(',') if s.strip()]
            if symbols and self.websocket_client:
                self.websocket_client.subscribe(symbols=symbols, data_type=data_type)
                self.safe_set_value(self.get_tag('ws_data_type'), f'Data Type: {data_type}')
                self.safe_set_value(self.get_tag('ws_symbols'), f'Symbols: {', '.join(symbols)}')
                with self._lock:
                    self.current_symbols = symbols
                    self.current_data_type = data_type
                self.websocket_client.keep_running()
            self.update_auth_log(' WebSocket connected and subscribed')
            info('WebSocket connected successfully', context={'symbols': len(symbols), 'data_type': data_type})
        except Exception as e:
            error_msg = f' WebSocket open callback error: {str(e)}'
            self.update_auth_log(error_msg)
            error('WebSocket open callback error', context={'error': str(e)}, exc_info=True)

    def on_websocket_close(self, code):
        """WebSocket close callback"""
        try:
            with self._lock:
                self.is_connected = False
                self.is_paused = True
            self.safe_set_value(self.get_tag('ws_status_text'), 'Status: Disconnected')
            self.safe_configure_item(self.get_tag('ws_status_text'), color=(255, 100, 100))
            self.safe_set_value(self.get_tag('pause_button'), ' Paused')
            error_msg = f' WebSocket closed (code: {code})'
            self.update_auth_log(error_msg)
            warning('WebSocket closed', context={'code': code})
        except Exception as e:
            error('Error in WebSocket close callback', context={'error': str(e)}, exc_info=True)

    def on_websocket_error(self, error):
        """WebSocket error callback"""
        error_msg = f' WebSocket error: {str(error)}'
        self.update_auth_log(error_msg)
        error('WebSocket error', context={'error': str(error)})

    def on_websocket_message(self, message):
        """Enhanced WebSocket message callback with filtering and throttling"""
        try:
            with self._lock:
                if self.is_paused or not self.is_connected:
                    return
                self.message_count += 1
                self.last_message_time = datetime.datetime.now()
            symbol_filter = dpg.get_value(self.get_tag('symbol_filter'))
            if symbol_filter and symbol_filter.strip():
                message_symbol = message.get('symbol', '').upper()
                if symbol_filter.upper() not in message_symbol:
                    return
            timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
            data_row = {'timestamp': timestamp, 'symbol': self.safe_encode_text(message.get('symbol', 'Unknown')), 'type': self.safe_encode_text(message.get('type', 'Unknown')), 'data': message}
            with self._lock:
                self.streaming_data.append(data_row)
                try:
                    max_rows = dpg.get_value(self.get_tag('max_display_rows'))
                    if isinstance(max_rows, str):
                        max_rows = int(max_rows)
                    elif max_rows is None:
                        max_rows = 1000
                except (ValueError, TypeError):
                    max_rows = 1000
                if len(self.streaming_data) > max_rows:
                    self.streaming_data = self.streaming_data[-max_rows:]
            should_update = self.should_update_ui()
            if should_update and dpg.get_value(self.get_tag('auto_scroll')) and (not self.is_paused):
                self.update_streaming_stats()
                self.update_data_table()
        except Exception as e:
            error_msg = f' Message processing error: {str(e)}'
            self.update_auth_log(error_msg)
            error('Message processing error', context={'error': str(e)}, exc_info=True)

    def safe_encode_text(self, text: Any) -> str:
        """Safely encode text with proper handling"""
        try:
            if isinstance(text, bytes):
                return text.decode('utf-8', errors='ignore')
            elif isinstance(text, (int, float)):
                return str(text)
            elif text is None:
                return ''
            else:
                return str(text).encode('ascii', errors='ignore').decode('ascii')
        except Exception:
            return 'N/A'

    def should_update_ui(self) -> bool:
        """Determine if UI should be updated based on throttling settings"""
        current_time = datetime.datetime.now()
        try:
            update_rate = dpg.get_value(self.get_tag('update_rate'))
            if update_rate == 'Real-time':
                throttle_seconds = 0.1
            elif update_rate == '1 sec':
                throttle_seconds = 1.0
            elif update_rate == '2 sec':
                throttle_seconds = 2.0
            elif update_rate == '5 sec':
                throttle_seconds = 5.0
            else:
                throttle_seconds = 0.5
        except:
            throttle_seconds = 0.5
        if self._last_table_update is None:
            self._last_table_update = current_time
            return True
        time_diff = (current_time - self._last_table_update).total_seconds()
        if time_diff >= throttle_seconds:
            self._last_table_update = current_time
            return True
        return False

    def update_auth_status(self):
        """Update authentication status in UI with safe operations"""
        try:
            if self.access_token:
                self.safe_set_value(self.get_tag('auth_status_text'), 'Status: Authenticated')
                self.safe_configure_item(self.get_tag('auth_status_text'), color=(100, 255, 100))
                token_display = f'Token: {self.access_token[:20]}...' if len(self.access_token) > 20 else f'Token: {self.access_token}'
                self.safe_set_value(self.get_tag('token_status'), token_display)
                self.safe_set_value(self.get_tag('token_generated_time'), f'Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')
                self.safe_set_value(self.get_tag('token_validity'), 'Valid Until: End of trading day')
            token_file_path = self.config_dir / 'access_token.log'
            token_file_status = f'access_token.log: Found' if token_file_path.exists() else f'access_token.log: Not Found'
            self.safe_set_value(self.get_tag('token_file_status'), token_file_status)
        except Exception as e:
            error('Error updating auth status', context={'error': str(e)}, exc_info=True)

    def update_streaming_stats(self):
        """Update streaming statistics with enhanced calculations"""
        try:
            with self._lock:
                data_count = len(self.streaming_data)
                current_time = datetime.datetime.now()
                self.safe_set_value(self.get_tag('data_points_count'), f'Data Points: {data_count}')
                self.safe_set_value(self.get_tag('last_update_time'), f'Last Update: {current_time.strftime('%H:%M:%S')}')
                if self.session_start_time:
                    session_duration = current_time - self.session_start_time
                    hours, remainder = divmod(session_duration.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    session_time_str = f'Session Time: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}'
                    self.safe_set_value(self.get_tag('session_time'), session_time_str)
                if self.session_start_time and self.message_count > 0:
                    elapsed_seconds = (current_time - self.session_start_time).total_seconds()
                    if elapsed_seconds > 0:
                        rate = self.message_count / elapsed_seconds
                        self.safe_set_value(self.get_tag('data_rate'), f'Data Rate: {rate:.1f} msg/sec')
                self.safe_set_value(self.get_tag('ws_message_count'), f'Messages Received: {self.message_count}')
        except Exception as e:
            error('Error updating streaming stats', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def update_data_table(self):
        """Enhanced data table update with better performance and error handling"""
        with operation('update_data_table'):
            try:
                if not dpg.get_value(self.get_tag('auto_scroll')) or self.is_paused:
                    return
                with self._lock:
                    if not self.streaming_data:
                        return
                    recent_data = self.streaming_data[-100:] if len(self.streaming_data) > 100 else self.streaming_data
                if not recent_data:
                    return
                container_tag = self.get_tag('live_data_table_container')
                if dpg.does_item_exist(container_tag):
                    dpg.delete_item(container_tag, children_only=True)
                    all_keys = set()
                    for row in recent_data[-10:]:
                        if isinstance(row['data'], dict):
                            all_keys.update(row['data'].keys())
                    sorted_keys = sorted(list(all_keys))
                    table_tag = self.get_tag('live_data_table')
                    if dpg.does_item_exist(table_tag):
                        dpg.delete_item(table_tag)
                    with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, parent=container_tag, scrollY=True, scrollX=True, height=400, tag=table_tag):
                        dpg.add_table_column(label='Time', width_fixed=True, init_width_or_weight=80)
                        dpg.add_table_column(label='Symbol', width_fixed=True, init_width_or_weight=120)
                        dpg.add_table_column(label='Type', width_fixed=True, init_width_or_weight=60)
                        priority_fields = ['ltp', 'volume', 'bid_price1', 'ask_price1', 'high_price', 'low_price']
                        added_fields = set()
                        for field in priority_fields:
                            if field in sorted_keys:
                                dpg.add_table_column(label=field, width_fixed=True, init_width_or_weight=100)
                                added_fields.add(field)
                        for key in sorted_keys:
                            if key not in ['symbol', 'type'] and key not in added_fields:
                                dpg.add_table_column(label=key, width_fixed=True, init_width_or_weight=100)
                                added_fields.add(key)
                        display_data = list(reversed(recent_data[-50:]))
                        for row in display_data:
                            with dpg.table_row():
                                dpg.add_text(row['timestamp'])
                                dpg.add_text(row['symbol'])
                                dpg.add_text(row['type'])
                                if isinstance(row['data'], dict):
                                    for field in priority_fields:
                                        if field in added_fields:
                                            self.add_table_cell(row, field)
                                    for key in sorted_keys:
                                        if key not in ['symbol', 'type'] and key not in priority_fields:
                                            if key in added_fields:
                                                self.add_table_cell(row, key)
                                else:
                                    for _ in added_fields:
                                        dpg.add_text('')
            except Exception as e:
                error('Error updating data table', context={'error': str(e)}, exc_info=True)
                try:
                    container_tag = self.get_tag('live_data_table_container')
                    if dpg.does_item_exist(container_tag):
                        dpg.delete_item(container_tag, children_only=True)
                        dpg.add_text(f'Table update error: {str(e)}', parent=container_tag)
                except:
                    pass

    def add_table_cell(self, row: Dict[str, Any], field: str):
        """Add a table cell with proper formatting and color coding"""
        try:
            value = row['data'].get(field, '')
            if value is None:
                dpg.add_text('NULL')
            else:
                try:
                    if isinstance(value, float):
                        display_value = f'{value:.2f}'
                        color = self.get_price_color(row['symbol'], field, value)
                    elif isinstance(value, int):
                        display_value = f'{value:,}'
                        color = self.get_price_color(row['symbol'], field, value)
                    else:
                        display_value = str(value)
                        color = None
                    if color:
                        dpg.add_text(display_value, color=color)
                    else:
                        dpg.add_text(display_value)
                except Exception:
                    dpg.add_text(str(value))
        except Exception:
            dpg.add_text('')

    def update_auth_log(self, message: str):
        """Update authentication log with safe operations"""
        try:
            log_tag = self.get_tag('auth_log_text')
            if dpg.does_item_exist(log_tag):
                current_log = dpg.get_value(log_tag)
                timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                new_message = f'[{timestamp}] {message}'
                new_log = f'{new_message}\n{current_log}'
                lines = new_log.split('\n')[:15]
                dpg.set_value(log_tag, '\n'.join(lines))
        except Exception as e:
            warning(f'Error updating auth log: {e}')

    def get_price_color(self, symbol: str, field: str, current_value: Any) -> Optional[Tuple[int, int, int]]:
        """Get color for price fields based on movement with enhanced field detection"""
        price_fields = {'ltp', 'ask_price1', 'ask_price2', 'ask_price3', 'ask_price4', 'ask_price5', 'bid_price1', 'bid_price2', 'bid_price3', 'bid_price4', 'bid_price5', 'high_price', 'low_price', 'open_price', 'prev_close_price', 'avg_trade_price', 'last_traded_price', 'close_price', 'price'}
        if field not in price_fields or not isinstance(current_value, (int, float)):
            return None
        key = f'{symbol}_{field}'
        with self._lock:
            previous_value = self.previous_prices.get(key)
            self.previous_prices[key] = current_value
        if previous_value is None:
            return None
        try:
            if current_value > previous_value:
                return (100, 255, 100)
            elif current_value < previous_value:
                return (255, 100, 100)
            else:
                return None
        except:
            return None

    def update_subscription(self):
        """Enhanced WebSocket subscription update"""
        if not self.is_connected or not self.websocket_client:
            self.update_auth_log(' Not connected to WebSocket')
            return
        with operation('update_subscription'):
            try:
                data_type = dpg.get_value(self.get_tag('stream_data_type'))
                symbols_text = dpg.get_value(self.get_tag('stream_symbols'))
                symbols = [s.strip().upper() for s in symbols_text.split(',') if s.strip()]
                if not symbols:
                    self.update_auth_log(' No symbols provided')
                    return
                self.update_auth_log(f' Updating subscription to {len(symbols)} symbols...')
                with self._lock:
                    if hasattr(self.websocket_client, 'unsubscribe') and self.current_symbols:
                        try:
                            self.websocket_client.unsubscribe(symbols=self.current_symbols, data_type=self.current_data_type)
                            self.update_auth_log(' Unsubscribed from previous symbols')
                        except Exception as e:
                            self.update_auth_log(f' Unsubscribe warning: {str(e)}')
                    self.websocket_client.subscribe(symbols=symbols, data_type=data_type)
                    self.current_symbols = symbols
                    self.current_data_type = data_type
                self.safe_set_value(self.get_tag('ws_data_type'), f'Data Type: {data_type}')
                self.safe_set_value(self.get_tag('ws_symbols'), f'Symbols: {', '.join(symbols)}')
                self.update_auth_log(f' Subscription updated: {data_type} for {len(symbols)} symbols')
                info('Subscription updated', context={'symbols_count': len(symbols), 'data_type': data_type})
            except Exception as e:
                error_msg = f' Subscription update failed: {str(e)}'
                self.update_auth_log(error_msg)
                error('Subscription update failed', context={'error': str(e)}, exc_info=True)

    def set_quick_symbols(self, symbol_set: str):
        """Set predefined symbol sets for quick access"""
        try:
            if symbol_set == 'nifty50':
                symbols = ['NSE:RELIANCE-EQ', 'NSE:TCS-EQ', 'NSE:HDFCBANK-EQ', 'NSE:INFY-EQ', 'NSE:HINDUNILVR-EQ', 'NSE:ICICIBANK-EQ', 'NSE:KOTAKBANK-EQ', 'NSE:SBIN-EQ', 'NSE:BHARTIARTL-EQ', 'NSE:ITC-EQ']
            elif symbol_set == 'banknifty':
                symbols = ['NSE:HDFCBANK-EQ', 'NSE:ICICIBANK-EQ', 'NSE:KOTAKBANK-EQ', 'NSE:SBIN-EQ', 'NSE:AXISBANK-EQ', 'NSE:INDUSINDBK-EQ', 'NSE:PNB-EQ', 'NSE:BANKBARODA-EQ']
            else:
                symbols = self.current_symbols
            symbols_text = ','.join(symbols)
            self.safe_set_value(self.get_tag('stream_symbols'), symbols_text)
            self.update_auth_log(f' Set {symbol_set.upper()} symbols')
            info('Quick symbols set', context={'symbol_set': symbol_set, 'count': len(symbols)})
        except Exception as e:
            error_msg = f' Error setting quick symbols: {str(e)}'
            self.update_auth_log(error_msg)
            error('Failed to set quick symbols', context={'error': str(e)}, exc_info=True)

    def on_max_rows_changed(self, sender, app_data):
        """Handle max rows change with safe conversion"""
        try:
            if isinstance(app_data, str):
                max_rows = int(app_data)
            else:
                max_rows = app_data
            with self._lock:
                self.max_streaming_rows = max_rows
                if len(self.streaming_data) > max_rows:
                    self.streaming_data = self.streaming_data[-max_rows:]
            self.update_data_table()
            info('Max rows changed', context={'max_rows': max_rows})
        except (ValueError, TypeError):
            self.max_streaming_rows = 1000
            warning('Invalid max rows value, using default 1000')

    def on_symbol_filter_changed(self, sender, app_data):
        """Handle symbol filter changes"""
        try:
            filter_value = app_data.strip().upper() if app_data else ''
            if filter_value:
                self.update_auth_log(f' Symbol filter set to: {filter_value}')
            else:
                self.update_auth_log(' Symbol filter cleared')
            if dpg.get_value(self.get_tag('auto_scroll')):
                self.update_data_table()
            debug('Symbol filter changed', context={'filter': filter_value})
        except Exception as e:
            error('Error in symbol filter change', context={'error': str(e)}, exc_info=True)

    def on_update_rate_changed(self, sender, app_data):
        """Handle update rate changes"""
        try:
            self.update_auth_log(f' Update rate changed to: {app_data}')
            info('Update rate changed', context={'rate': app_data})
        except Exception as e:
            error('Error in update rate change', context={'error': str(e)}, exc_info=True)

    def clear_streaming_data(self):
        """Clear all streaming data with enhanced cleanup"""
        with operation('clear_streaming_data'):
            try:
                with self._lock:
                    self.streaming_data.clear()
                    self.previous_prices.clear()
                    self.message_count = 0
                container_tag = self.get_tag('live_data_table_container')
                if dpg.does_item_exist(container_tag):
                    dpg.delete_item(container_tag, children_only=True)
                    dpg.add_text('Data cleared. Waiting for new messages...', parent=container_tag)
                self.update_auth_log(' All streaming data cleared')
                info('Streaming data cleared')
            except Exception as e:
                error_msg = f' Error clearing data: {str(e)}'
                self.update_auth_log(error_msg)
                error('Failed to clear streaming data', context={'error': str(e)}, exc_info=True)

    def toggle_pause(self):
        """Enhanced pause/resume functionality"""
        try:
            with self._lock:
                self.is_paused = not self.is_paused
            if self.is_paused:
                self.safe_set_value(self.get_tag('pause_button'), ' Resume')
                self.update_auth_log(' Data streaming paused')
            else:
                self.safe_set_value(self.get_tag('pause_button'), ' Pause')
                self.update_auth_log(' Data streaming resumed')
                if self.streaming_data:
                    self.update_data_table()
            info(f'Streaming {('paused' if self.is_paused else 'resumed')}')
        except Exception as e:
            error_msg = f' Error toggling pause: {str(e)}'
            self.update_auth_log(error_msg)
            error('Failed to toggle pause', context={'error': str(e)}, exc_info=True)

    def force_refresh_table(self):
        """Force refresh the data table"""
        try:
            self.update_data_table()
            self.update_auth_log(' Table refreshed manually')
            info('Table manually refreshed')
        except Exception as e:
            error_msg = f' Error refreshing table: {str(e)}'
            self.update_auth_log(error_msg)
            error('Failed to refresh table', context={'error': str(e)}, exc_info=True)

    def show_detailed_stats(self):
        """Show detailed streaming statistics"""
        try:
            with self._lock:
                total_messages = self.message_count
                data_count = len(self.streaming_data)
                unique_symbols = len(set((row['symbol'] for row in self.streaming_data)))
            stats_message = f' Detailed Statistics:\n• Total Messages: {total_messages:,}\n• Data Points Stored: {data_count:,}\n• Unique Symbols: {unique_symbols}\n• Memory Usage: ~{len(str(self.streaming_data)) / 1024:.1f} KB'
            self.update_auth_log(stats_message)
            info('Detailed stats shown', context={'messages': total_messages, 'data_points': data_count, 'symbols': unique_symbols})
        except Exception as e:
            error_msg = f' Error showing stats: {str(e)}'
            self.update_auth_log(error_msg)
            error('Failed to show stats', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def export_data(self):
        """Enhanced export functionality with multiple formats"""
        with operation('export_data'):
            try:
                with self._lock:
                    if not self.streaming_data:
                        self.update_auth_log(' No data to export')
                        return
                    data_to_export = self.streaming_data.copy()
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_filename = f'fyers_stream_{timestamp}.csv'
                csv_path = self.config_dir / csv_filename
                self.export_to_csv(data_to_export, csv_path)
                json_filename = f'fyers_stream_{timestamp}.json'
                json_path = self.config_dir / json_filename
                self.export_to_json(data_to_export, json_path)
                export_msg = f' Exported {len(data_to_export)} records to {csv_filename} and {json_filename}'
                self.update_auth_log(export_msg)
                info('Data exported successfully', context={'records': len(data_to_export), 'csv_file': str(csv_path), 'json_file': str(json_path)})
            except Exception as e:
                error_msg = f' Export failed: {str(e)}'
                self.update_auth_log(error_msg)
                error('Data export failed', context={'error': str(e)}, exc_info=True)

    def export_to_csv(self, data: List[Dict], filepath: Path):
        """Export data to CSV format"""
        try:
            all_keys = set(['timestamp', 'symbol', 'type'])
            for row in data:
                if isinstance(row['data'], dict):
                    all_keys.update(row['data'].keys())
            sorted_keys = sorted(list(all_keys))
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=sorted_keys)
                writer.writeheader()
                for row in data:
                    export_row = {'timestamp': row['timestamp'], 'symbol': row['symbol'], 'type': row['type']}
                    if isinstance(row['data'], dict):
                        for key, value in row['data'].items():
                            if key not in ['symbol', 'type']:
                                export_row[key] = value
                    writer.writerow(export_row)
            debug('CSV export completed', context={'filepath': str(filepath), 'rows': len(data)})
        except Exception as e:
            raise Exception(f'CSV export error: {str(e)}')

    def export_to_json(self, data: List[Dict], filepath: Path):
        """Export data to JSON format"""
        try:
            export_data = {'metadata': {'export_time': datetime.datetime.now().isoformat(), 'total_records': len(data), 'symbols': list(set((row['symbol'] for row in data))), 'data_types': list(set((row['type'] for row in data))), 'time_range': {'start': data[0]['timestamp'] if data else None, 'end': data[-1]['timestamp'] if data else None}}, 'data': data}
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
            debug('JSON export completed', context={'filepath': str(filepath), 'records': len(data)})
        except Exception as e:
            raise Exception(f'JSON export error: {str(e)}')

    def get_connection_health(self) -> Dict[str, Any]:
        """Get current connection health status"""
        try:
            with self._lock:
                current_time = datetime.datetime.now()
                health_status = {'is_connected': self.is_connected, 'is_paused': self.is_paused, 'has_token': bool(self.access_token), 'session_duration': None, 'message_count': self.message_count, 'data_points': len(self.streaming_data), 'last_message': None, 'symbols_count': len(self.current_symbols), 'websocket_client': self.websocket_client is not None}
                if self.session_start_time:
                    duration = current_time - self.session_start_time
                    health_status['session_duration'] = duration.total_seconds()
                if self.last_message_time:
                    time_since_last = current_time - self.last_message_time
                    health_status['last_message'] = time_since_last.total_seconds()
                return health_status
        except Exception as e:
            error('Error getting connection health', context={'error': str(e)}, exc_info=True)
            return {'error': str(e)}

    def reconnect_websocket(self):
        """Reconnect WebSocket with enhanced logic"""
        with operation('reconnect_websocket'):
            try:
                self.update_auth_log(' Attempting to reconnect WebSocket...')
                if self.is_connected:
                    self.disconnect_websocket()
                    time.sleep(2)
                self.connect_websocket()
                info('WebSocket reconnection attempted')
            except Exception as e:
                error_msg = f' Reconnection failed: {str(e)}'
                self.update_auth_log(error_msg)
                error('WebSocket reconnection failed', context={'error': str(e)}, exc_info=True)

    def validate_symbols(self, symbols: List[str]) -> Tuple[List[str], List[str]]:
        """Validate symbol format and return valid/invalid lists"""
        valid_symbols = []
        invalid_symbols = []
        for symbol in symbols:
            symbol = symbol.strip().upper()
            if not symbol:
                continue
            if ':' in symbol and '-EQ' in symbol:
                parts = symbol.split(':')
                if len(parts) == 2 and parts[0] in ['NSE', 'BSE']:
                    valid_symbols.append(symbol)
                else:
                    invalid_symbols.append(symbol)
            else:
                invalid_symbols.append(symbol)
        return (valid_symbols, invalid_symbols)

    def auto_save_config(self):
        """Auto-save current configuration"""
        try:
            config = {'last_symbols': self.current_symbols, 'last_data_type': self.current_data_type, 'max_rows': self.max_streaming_rows, 'auto_scroll': dpg.get_value(self.get_tag('auto_scroll')) if dpg.does_item_exist(self.get_tag('auto_scroll')) else True, 'update_rate': dpg.get_value(self.get_tag('update_rate')) if dpg.does_item_exist(self.get_tag('update_rate')) else 'Real-time'}
            config_path = self.config_dir / 'fyers_session_config.json'
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            info('Session configuration auto-saved', context={'config_path': str(config_path)})
        except Exception as e:
            warning('Could not auto-save config', context={'error': str(e)})

    def load_session_config(self):
        """Load saved session configuration"""
        try:
            config_path = self.config_dir / 'fyers_session_config.json'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if 'last_symbols' in config:
                    self.current_symbols = config['last_symbols']
                if 'last_data_type' in config:
                    self.current_data_type = config['last_data_type']
                if 'max_rows' in config:
                    self.max_streaming_rows = config['max_rows']
                info('Session configuration loaded', context={'config_path': str(config_path)})
                return True
        except Exception as e:
            warning('Could not load session config', context={'error': str(e)})
        return False

    @monitor_performance
    def cleanup(self):
        """Enhanced cleanup with auto-save"""
        with operation('fyers_tab_cleanup'):
            try:
                self.auto_save_config()
                if self.websocket_client:
                    try:
                        self.disconnect_websocket()
                    except Exception as e:
                        warning('Warning during WebSocket cleanup', context={'error': str(e)})
                with self._lock:
                    self.streaming_data.clear()
                    self.previous_prices.clear()
                self.cleanup_existing_items()
                info('Fyers tab cleaned up successfully')
            except Exception as e:
                error('Error during cleanup', context={'error': str(e)}, exc_info=True)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        try:
            with self._lock:
                current_time = datetime.datetime.now()
                metrics = {'memory_usage_kb': len(str(self.streaming_data)) / 1024, 'total_messages': self.message_count, 'stored_data_points': len(self.streaming_data), 'unique_symbols': len(set((row['symbol'] for row in self.streaming_data))), 'avg_message_size': len(str(self.streaming_data)) / max(len(self.streaming_data), 1), 'is_healthy': self.is_connected and (not self.is_paused), 'uptime_seconds': None}
                if self.session_start_time:
                    uptime = current_time - self.session_start_time
                    metrics['uptime_seconds'] = uptime.total_seconds()
                    if uptime.total_seconds() > 0:
                        metrics['messages_per_second'] = self.message_count / uptime.total_seconds()
                return metrics
        except Exception as e:
            error('Error getting performance metrics', context={'error': str(e)}, exc_info=True)
            return {'error': str(e)}

    def format_number(self, value: Any) -> str:
        """Format numbers for display"""
        try:
            if isinstance(value, float):
                if value >= 1000000:
                    return f'{value / 1000000:.2f}M'
                elif value >= 1000:
                    return f'{value / 1000:.2f}K'
                else:
                    return f'{value:.2f}'
            elif isinstance(value, int):
                if value >= 1000000:
                    return f'{value / 1000000:.1f}M'
                elif value >= 1000:
                    return f'{value / 1000:.1f}K'
                else:
                    return f'{value:,}'
            else:
                return str(value)
        except:
            return str(value)

    def get_symbol_stats(self, symbol: str) -> Dict[str, Any]:
        """Get statistics for a specific symbol"""
        try:
            with self._lock:
                symbol_data = [row for row in self.streaming_data if row['symbol'] == symbol]
            if not symbol_data:
                return {'error': 'No data found for symbol'}
            stats = {'total_updates': len(symbol_data), 'first_seen': symbol_data[0]['timestamp'], 'last_seen': symbol_data[-1]['timestamp'], 'data_types': list(set((row['type'] for row in symbol_data)))}
            prices = []
            for row in symbol_data:
                if isinstance(row['data'], dict) and 'ltp' in row['data']:
                    try:
                        prices.append(float(row['data']['ltp']))
                    except:
                        continue
            if prices:
                stats.update({'price_high': max(prices), 'price_low': min(prices), 'price_avg': sum(prices) / len(prices), 'price_current': prices[-1], 'price_change': prices[-1] - prices[0] if len(prices) > 1 else 0})
            return stats
        except Exception as e:
            return {'error': str(e)}

    def emergency_stop(self):
        """Emergency stop all operations"""
        try:
            warning('Emergency stop initiated')
            with self._lock:
                self.is_connected = False
                self.is_paused = True
            if self.websocket_client:
                self.websocket_client = None
            self.safe_set_value(self.get_tag('ws_status_text'), 'Status: Emergency Stopped')
            self.safe_configure_item(self.get_tag('ws_status_text'), color=(255, 0, 0))
            self.update_auth_log('Emergency stop - All operations halted')
            error('Emergency stop executed')
        except Exception as e:
            error('Error during emergency stop', context={'error': str(e)}, exc_info=True)

def validate_authcode(self, auth_code: str, app_id: str, app_type: str, app_secret: str) -> Tuple[int, str]:
    """Validate authorization code"""
    try:
        app_id_hash = hashlib.sha256(f'{app_id}-{app_type}:{app_secret}'.encode()).hexdigest()
        payload = {'grant_type': 'authorization_code', 'appIdHash': app_id_hash, 'code': auth_code}
        resp = requests.post(url=f'{self.BASE_URL_2}/validate-authcode', json=payload, timeout=30)
        if resp.status_code != 200:
            return [-1, f'HTTP {resp.status_code}: {resp.text}']
        data = resp.json()
        debug('Authorization code validated successfully')
        return [1, data['access_token']]
    except requests.exceptions.Timeout:
        return [-1, 'Request timeout']
    except requests.exceptions.RequestException as e:
        return [-1, f'Network error: {str(e)}']
    except Exception as e:
        return [-1, str(e)]

def safe_encode_text(self, text: Any) -> str:
    """Safely encode text with proper handling"""
    try:
        if isinstance(text, bytes):
            return text.decode('utf-8', errors='ignore')
        elif isinstance(text, (int, float)):
            return str(text)
        elif text is None:
            return ''
        else:
            return str(text).encode('ascii', errors='ignore').decode('ascii')
    except Exception:
        return 'N/A'

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: int) -> str:
    payload = {'user_id': user_id, 'exp': datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, 'your-secret-key', algorithm='HS256')

def verify_token(credentials: HTTPAuthorizationCredentials=Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, 'your-secret-key', algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')

