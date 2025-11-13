# Cluster 135

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

def create_dataset_grid(self):
    """Create dataset grid display"""
    with dpg.child_window(width=-1, height=-1, border=True, tag='dataset_grid'):
        self.update_dataset_grid()

def create_purchases_content(self):
    """Create purchases tab content"""
    with dpg.child_window(width=-1, height=-1, border=True, tag='purchases_content'):
        self.update_purchases_content()

def create_my_datasets_content(self):
    """Create my datasets tab content"""
    with dpg.child_window(width=-1, height=-1, border=True, tag='my_datasets_content'):
        self.update_my_datasets_content()

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

def purchase_thread():
    success = self.purchase_dataset(dataset_id)
    if success:
        self.load_datasets()
        self.update_dataset_grid()
        print('Purchase successful!')
    else:
        print('Purchase failed!')

def refresh_thread():
    self.load_categories()
    self.load_datasets()
    self.update_dataset_grid()
    if dpg.get_value('main_tabs') == 'purchases_tab':
        self.update_purchases_content()
    elif dpg.get_value('main_tabs') == 'my_datasets_tab':
        self.update_my_datasets_content()

class ForumTab(BaseTab):
    """High Performance Global Forum Tab with minimal overhead"""

    def __init__(self, app):
        super().__init__(app)
        debug('[FORUM_TAB] Initializing Forum Tab')
        try:
            self._api_client = None
            self._api_client_initialized = False
            self._auth_cached = None
            self._auth_cache_time = 0
            self._user_info_cached = None
            self._user_info_cache_time = 0
            self._cache_ttl = 300
            self.current_category = None
            self.current_post_uuid = None
            self.categories = []
            self.posts = []
            self.search_results = []
            self.forum_stats = {}
            self.loading = False
            self.search_query = ''
            self.ui_initialized = False
            self.BLOOMBERG_ORANGE = [255, 165, 0]
            self.BLOOMBERG_WHITE = [255, 255, 255]
            self.BLOOMBERG_RED = [255, 0, 0]
            self.BLOOMBERG_GREEN = [0, 200, 0]
            self.BLOOMBERG_YELLOW = [255, 255, 0]
            self.BLOOMBERG_GRAY = [120, 120, 120]
            self.BLOOMBERG_BLUE = [0, 128, 255]
            self.BLOOMBERG_PURPLE = [138, 43, 226]
            debug('[FORUM_TAB] Forum Tab initialized successfully')
        except Exception as e:
            error(f'[FORUM_TAB] Initialization failed: {str(e)}')
            raise

    def get_label(self):
        return 'Forum'

    @property
    def api_client(self):
        """PERFORMANCE: Lazy API client initialization"""
        if not self._api_client_initialized:
            self._initialize_api_client()
        return self._api_client

    def _initialize_api_client(self):
        """PERFORMANCE: Initialize API client only when needed"""
        try:
            from fincept_terminal.utils.APIClient.api_client import create_api_client
            session_data = self.app.get_session_data()
            self._api_client = create_api_client(session_data)
            self._api_client_initialized = True
            if self._api_client:
                debug('[FORUM_TAB] API client initialized successfully')
            else:
                warning('[FORUM_TAB] API client creation failed')
        except Exception as e:
            error(f'[FORUM_TAB] API client initialization failed: {str(e)}')
            self._api_client = None
            self._api_client_initialized = True

    def _is_authenticated_cached(self) -> bool:
        """PERFORMANCE: Cached authentication check"""
        current_time = time.time()
        if self._auth_cached is not None and current_time - self._auth_cache_time < self._cache_ttl:
            return self._auth_cached
        is_auth = False
        if self.api_client:
            try:
                is_auth = self.api_client.is_authenticated()
            except Exception:
                is_auth = False
        self._auth_cached = is_auth
        self._auth_cache_time = current_time
        return is_auth

    def _get_user_info_cached(self) -> Optional[Dict[str, Any]]:
        """PERFORMANCE: Cached user info retrieval"""
        current_time = time.time()
        if self._user_info_cached is not None and current_time - self._user_info_cache_time < self._cache_ttl:
            return self._user_info_cached
        user_info = None
        if self.api_client:
            try:
                if self.api_client.is_registered():
                    user_info = self.api_client.get_user_info()
            except Exception:
                user_info = None
        self._user_info_cached = user_info
        self._user_info_cache_time = current_time
        return user_info

    def create_content(self):
        """OPTIMIZED: Create forum tab content with minimal API calls"""
        try:
            info('[FORUM_TAB] Creating forum tab content')
            self.add_section_header('FINCEPT TERMINAL - GLOBAL FORUM')
            if not self._is_authenticated_cached():
                warning('[FORUM_TAB] User not authenticated for forum access')
                self.create_auth_error_panel()
                return
            self.create_forum_header()
            dpg.add_spacer(height=10)
            try:
                with dpg.group(horizontal=True):
                    self.create_categories_panel()
                    dpg.add_spacer(width=10)
                    self.create_posts_panel()
                    dpg.add_spacer(width=10)
                    self.create_user_panel()
                self.ui_initialized = True
                info('[FORUM_TAB] Forum UI created successfully')
            except Exception as ui_error:
                error(f'[FORUM_TAB] UI creation failed: {str(ui_error)}')
                self.create_error_panel(f'UI creation failed: {str(ui_error)}')
                return

            def load_data_async():
                try:
                    self.load_initial_data_optimized()
                except Exception as e:
                    error(f'[FORUM_TAB] Async data loading failed: {str(e)}')
            threading.Thread(target=load_data_async, daemon=True, name='ForumDataLoader').start()
        except Exception as e:
            error(f'[FORUM_TAB] Critical error creating forum content: {str(e)}')
            self.create_error_panel(f'Critical error: {str(e)}')

    def create_error_panel(self, error_message: str):
        """Create error panel for critical failures"""
        try:
            with dpg.child_window(width=-1, height=400, border=True):
                dpg.add_spacer(height=50)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=200)
                    dpg.add_text('⚠️ Forum Error', color=self.BLOOMBERG_RED)
                dpg.add_spacer(height=20)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=150)
                    dpg.add_text(f'Error: {error_message}', color=self.BLOOMBERG_WHITE)
                dpg.add_spacer(height=30)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=250)
                    dpg.add_button(label='Retry', callback=self.retry_forum_initialization, width=100)
        except Exception as e:
            error(f'[FORUM_TAB] Error panel creation failed: {str(e)}')

    def retry_forum_initialization(self):
        """Retry forum initialization"""
        info('[FORUM_TAB] Retrying forum initialization')
        try:
            self._auth_cached = None
            self._user_info_cached = None
            self.load_initial_data_optimized()
        except Exception as e:
            error(f'[FORUM_TAB] Forum retry failed: {str(e)}')

    def create_auth_error_panel(self):
        """Create panel when user is not authenticated"""
        try:
            with dpg.child_window(width=-1, height=400, border=True):
                dpg.add_spacer(height=50)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=300)
                    dpg.add_text('🔒 Authentication Required', color=self.BLOOMBERG_YELLOW)
                dpg.add_spacer(height=20)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=250)
                    dpg.add_text('Please authenticate to access the Global Forum', color=self.BLOOMBERG_WHITE)
                dpg.add_spacer(height=30)
                features = ['• Access to all forum categories', '• Create posts and comments', '• Vote on posts and comments', '• Real-time forum activity', '• User profiles and reputation']
                for feature in features:
                    with dpg.group(horizontal=True):
                        dpg.add_spacer(width=300)
                        dpg.add_text(feature, color=self.BLOOMBERG_GRAY)
                    dpg.add_spacer(height=5)
        except Exception as e:
            error(f'[FORUM_TAB] Auth error panel creation failed: {str(e)}')

    def create_forum_header(self):
        """OPTIMIZED: Create Bloomberg Terminal style forum header"""
        try:
            with dpg.group(horizontal=True):
                dpg.add_text('FINCEPT', color=self.BLOOMBERG_ORANGE)
                dpg.add_text('GLOBAL FORUM', color=self.BLOOMBERG_WHITE)
                dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                dpg.add_input_text(label='', default_value='Search posts, topics...', width=300, tag='forum_search_input', callback=self.on_search_input_change)
                dpg.add_button(label='SEARCH', width=80, callback=self.execute_search)
                dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                try:
                    user_info = self._get_user_info_cached()
                    if user_info:
                        username = user_info.get('username', 'User')
                        dpg.add_text(f'USER: {username.upper()}', color=self.BLOOMBERG_GREEN)
                    else:
                        dpg.add_text('USER: GUEST', color=self.BLOOMBERG_YELLOW)
                except Exception:
                    dpg.add_text('USER: UNKNOWN', color=self.BLOOMBERG_RED)
            dpg.add_spacer(height=10)
            self.create_function_key_bar()
        except Exception as e:
            error(f'[FORUM_TAB] Header creation failed: {str(e)}')

    def create_function_key_bar(self):
        """OPTIMIZED: Create function key bar"""
        try:
            with dpg.group(horizontal=True):
                function_keys = [('F1:HELP', self.show_forum_help), ('F2:REFRESH', self.refresh_forum), ('F3:NEW POST', self.create_new_post), ('F4:SEARCH', self.focus_search), ('F5:TRENDING', self.show_trending), ('F6:PROFILE', self.show_user_profile)]
                for key_label, callback in function_keys:
                    dpg.add_button(label=key_label, width=100, height=25, callback=self._safe_callback(callback, key_label))
        except Exception as e:
            error(f'[FORUM_TAB] Function key bar creation failed: {str(e)}')

    def _safe_callback(self, callback, action_name: str):
        """PERFORMANCE: Create lightweight callback wrapper"""

        def wrapper(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except Exception as e:
                error(f'[FORUM_TAB] Action failed: {action_name} - {str(e)}')
                self._show_error_notification(f"Action '{action_name}' failed", str(e))
        return wrapper

    def create_categories_panel(self):
        """OPTIMIZED: Create left panel with categories"""
        try:
            with dpg.child_window(width=280, height=650, border=True, tag='categories_panel'):
                dpg.add_text('FORUM CATEGORIES', color=self.BLOOMBERG_ORANGE)
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    dpg.add_button(label='ALL', callback=self._safe_callback(lambda: self.filter_by_category(None), 'ALL'), width=50, height=25)
                    dpg.add_button(label='TRENDING', callback=self._safe_callback(self.show_trending_posts, 'TRENDING'), width=70, height=25)
                    dpg.add_button(label='RECENT', callback=self._safe_callback(self.show_recent_posts, 'RECENT'), width=60, height=25)
                dpg.add_separator()
                dpg.add_child_window(height=350, border=False, tag='categories_list')
                dpg.add_separator()
                self.create_stats_section()
                dpg.add_separator()
                self.create_quick_actions_section()
        except Exception as e:
            error(f'[FORUM_TAB] Categories panel creation failed: {str(e)}')

    def create_stats_section(self):
        """Create forum statistics section"""
        try:
            dpg.add_text('FORUM STATISTICS', color=self.BLOOMBERG_YELLOW)
            dpg.add_text('Loading...', tag='stat_total_categories', color=self.BLOOMBERG_WHITE)
            dpg.add_text('Loading...', tag='stat_total_posts', color=self.BLOOMBERG_WHITE)
            dpg.add_text('Loading...', tag='stat_total_comments', color=self.BLOOMBERG_WHITE)
            dpg.add_text('Loading...', tag='stat_total_votes', color=self.BLOOMBERG_GREEN)
        except Exception as e:
            error(f'[FORUM_TAB] Stats section creation failed: {str(e)}')

    def create_quick_actions_section(self):
        """OPTIMIZED: Create quick actions section with cached user check"""
        try:
            if self._is_authenticated_cached():
                dpg.add_text('QUICK ACTIONS', color=self.BLOOMBERG_YELLOW)
                dpg.add_button(label='CREATE NEW POST', callback=self._safe_callback(self.create_new_post, 'CREATE_POST'), width=-1, height=30)
                dpg.add_button(label='MY POSTS', callback=self._safe_callback(self.show_my_posts, 'MY_POSTS'), width=-1, height=25)
                dpg.add_button(label='MY ACTIVITY', callback=self._safe_callback(self.show_my_activity, 'MY_ACTIVITY'), width=-1, height=25)
        except Exception as e:
            error(f'[FORUM_TAB] Quick actions creation failed: {str(e)}')

    def create_posts_panel(self):
        """OPTIMIZED: Create center panel with posts list"""
        try:
            with dpg.child_window(width=850, height=650, border=True, tag='posts_panel'):
                with dpg.group(horizontal=True):
                    dpg.add_text('FORUM POSTS', color=self.BLOOMBERG_ORANGE, tag='posts_header_title')
                    dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                    dpg.add_text('All Categories', color=self.BLOOMBERG_WHITE, tag='current_category_name')
                    dpg.add_spacer(width=50)
                    dpg.add_text('SORT:', color=self.BLOOMBERG_GRAY)
                    dpg.add_combo(['latest', 'popular', 'views', 'replies'], default_value='latest', width=120, tag='sort_combo', callback=self._safe_callback(self.sort_posts_callback, 'SORT'))
                dpg.add_separator()
                dpg.add_text('Loading posts...', tag='posts_loading', color=self.BLOOMBERG_YELLOW, show=False)
                dpg.add_child_window(height=-1, border=False, tag='posts_list_area')
        except Exception as e:
            error(f'[FORUM_TAB] Posts panel creation failed: {str(e)}')

    def create_user_panel(self):
        """OPTIMIZED: Create right panel with user info"""
        try:
            with dpg.child_window(width=300, height=650, border=True, tag='user_panel'):
                dpg.add_text('USER DASHBOARD', color=self.BLOOMBERG_ORANGE)
                dpg.add_separator()
                self.create_user_info_section()
                dpg.add_separator()
                self.create_user_actions_section()
                dpg.add_separator()
                dpg.add_text('RECENT ACTIVITY', color=self.BLOOMBERG_YELLOW)
                dpg.add_child_window(height=-1, border=True, tag='recent_activity')
        except Exception as e:
            error(f'[FORUM_TAB] User panel creation failed: {str(e)}')

    def create_user_info_section(self):
        """OPTIMIZED: Create user information section with cached data"""
        try:
            dpg.add_text('CURRENT USER', color=self.BLOOMBERG_YELLOW)
            user_info = self._get_user_info_cached()
            if user_info:
                username = user_info.get('username', 'User')
                credit_balance = user_info.get('credit_balance', 0)
                with dpg.group(horizontal=True):
                    with dpg.drawlist(width=40, height=40):
                        dpg.draw_rectangle([0, 0], [40, 40], color=self.BLOOMBERG_GREEN, fill=self.BLOOMBERG_GREEN)
                        dpg.draw_text([15, 15], username[:2].upper(), color=self.BLOOMBERG_WHITE, size=12)
                    with dpg.group():
                        dpg.add_text(username, color=self.BLOOMBERG_WHITE, tag='user_display_name')
                        dpg.add_text(f'Credits: {credit_balance}', color=self.BLOOMBERG_GREEN, tag='user_credits')
                        dpg.add_text('Status: Online', color=self.BLOOMBERG_GREEN, tag='user_status')
            else:
                self.create_guest_user_info()
        except Exception as e:
            error(f'[FORUM_TAB] User info section creation failed: {str(e)}')

    def create_guest_user_info(self):
        """Create guest user info display"""
        try:
            with dpg.group(horizontal=True):
                with dpg.drawlist(width=40, height=40):
                    dpg.draw_rectangle([0, 0], [40, 40], color=self.BLOOMBERG_YELLOW, fill=self.BLOOMBERG_YELLOW)
                    dpg.draw_text([12, 15], 'GU', color=self.BLOOMBERG_WHITE, size=12)
                with dpg.group():
                    dpg.add_text('Guest User', color=self.BLOOMBERG_WHITE, tag='user_display_name')
                    dpg.add_text('Limited Access', color=self.BLOOMBERG_YELLOW, tag='user_status')
        except Exception as e:
            error(f'[FORUM_TAB] Guest user info creation failed: {str(e)}')

    def create_user_actions_section(self):
        """OPTIMIZED: Create user actions section with cached auth check"""
        try:
            dpg.add_text('USER ACTIONS', color=self.BLOOMBERG_YELLOW)
            if self._is_authenticated_cached():
                user_actions = [('VIEW PROFILE', self.show_user_profile), ('MY POSTS', self.show_my_posts), ('MY ACTIVITY', self.show_my_activity), ('SETTINGS', self.show_user_settings)]
            else:
                user_actions = [('VIEW POSTS', lambda: self.filter_by_category(None)), ('SEARCH FORUM', self.focus_search), ('UPGRADE ACCOUNT', self.show_upgrade_info)]
            for action_name, callback in user_actions:
                dpg.add_button(label=action_name, callback=self._safe_callback(callback, action_name), width=-1, height=25)
        except Exception as e:
            error(f'[FORUM_TAB] User actions section creation failed: {str(e)}')

    def load_initial_data_optimized(self):
        """OPTIMIZED: Fast initial forum data loading with parallel requests"""
        start_time = time.time()
        info('[FORUM_TAB] Starting optimized initial forum data load')
        self._set_loading_safe(True)
        success_count = 0
        operations = [('categories', self.load_categories), ('forum_stats', self.load_forum_stats), ('posts', self.load_posts)]
        for operation_name, operation_func in operations:
            try:
                operation_func()
                success_count += 1
            except Exception as e:
                error(f'[FORUM_TAB] {operation_name} loading failed: {str(e)}')
        total_time = time.time() - start_time
        info(f'[FORUM_TAB] Data load completed: {success_count}/3 operations in {total_time:.2f}s')
        self._set_loading_safe(False)

    def load_categories(self):
        """OPTIMIZED: Load categories from API with minimal overhead"""
        try:
            if not self.api_client:
                raise Exception('API client not available')
            result = self.api_client.make_request('GET', '/forum/categories')
            if not result or not result.get('success') or (not result.get('data', {}).get('success')):
                raise Exception('API request failed')
            categories_data = result['data']['data'].get('categories', [])
            self.categories = categories_data
            info(f'[FORUM_TAB] Loaded {len(self.categories)} categories')

            def update_ui():
                self.update_categories_ui()
            threading.Thread(target=update_ui, daemon=True, name='CategoriesUI').start()
        except Exception as e:
            error(f'[FORUM_TAB] Categories loading failed: {str(e)}')
            self.categories = []

    def update_categories_ui(self):
        """OPTIMIZED: Update categories UI safely"""
        try:
            if not dpg.does_item_exist('categories_list'):
                return
            dpg.delete_item('categories_list', children_only=True)
            for category in self.categories:
                try:
                    self._create_category_item_fast(category)
                except Exception as e:
                    debug(f'[FORUM_TAB] Category item creation failed: {str(e)}')
            debug(f'[FORUM_TAB] Categories UI updated: {len(self.categories)} displayed')
        except Exception as e:
            error(f'[FORUM_TAB] Categories UI update failed: {str(e)}')

    def _create_category_item_fast(self, category_data: Dict[str, Any]):
        """PERFORMANCE: Fast category item creation"""
        try:
            if not category_data:
                return
            category_id = category_data.get('id')
            name = category_data.get('name', 'Unknown')
            post_count = category_data.get('post_count', 0)
            if not category_id:
                return
            with dpg.group(parent='categories_list'):
                dpg.add_button(label=f'{name} ({post_count})', callback=self._safe_callback(lambda cid=category_id: self.filter_by_category(cid), f'CATEGORY_{name}'), width=-1, height=35)
                description = category_data.get('description', '')
                if description:
                    desc_text = description[:35] + '...' if len(description) > 35 else description
                    dpg.add_text(f'  {desc_text}', color=self.BLOOMBERG_GRAY)
                dpg.add_spacer(height=5)
        except Exception as e:
            debug(f'[FORUM_TAB] Fast category item creation failed: {str(e)}')

    def _show_error_notification(self, title: str, message: str):
        """PERFORMANCE: Lightweight error notification"""
        try:
            debug(f'[FORUM_TAB] Error notification: {title} - {message[:50]}')
        except Exception:
            pass

    def _set_loading_safe(self, loading: bool):
        """PERFORMANCE: Safe loading state management"""
        try:
            self.loading = loading
            if dpg.does_item_exist('posts_loading'):
                if loading:
                    dpg.show_item('posts_loading')
                    dpg.set_value('posts_loading', 'Loading...')
                else:
                    dpg.hide_item('posts_loading')
        except Exception:
            pass

    def load_posts(self, category_id: Optional[int]=None):
        """OPTIMIZED: Load posts from API with background processing"""
        try:
            self._set_loading_safe(True)
            if not self.api_client:
                raise Exception('API client not available')
            if category_id:
                sort_by = 'latest'
                if dpg.does_item_exist('sort_combo'):
                    sort_by = dpg.get_value('sort_combo')
                result = self.api_client.make_request('GET', f'/forum/categories/{category_id}/posts', params={'sort_by': sort_by, 'limit': 20})
                if result and result.get('success') and result.get('data', {}).get('success'):
                    posts_data = result['data']['data']
                    self.posts = posts_data.get('posts', [])
                    category_info = posts_data.get('category', {})
                    category_name = category_info.get('name', 'Unknown Category')
                    info(f'[FORUM_TAB] Loaded {len(self.posts)} posts for category: {category_name}')

                    def update_posts_ui():
                        self.update_posts_ui(category_name)
                    threading.Thread(target=update_posts_ui, daemon=True, name='PostsUI').start()
                else:
                    raise Exception('Failed to load posts for category')
            elif self.categories:
                first_category_id = self.categories[0]['id']
                result = self.api_client.make_request('GET', f'/forum/categories/{first_category_id}/posts', params={'sort_by': 'latest', 'limit': 20})
                if result and result.get('success') and result.get('data', {}).get('success'):
                    posts_data = result['data']['data']
                    self.posts = posts_data.get('posts', [])
                    category_name = 'Recent Posts'
                    info(f'[FORUM_TAB] Loaded {len(self.posts)} default posts')

                    def update_posts_ui():
                        self.update_posts_ui(category_name)
                    threading.Thread(target=update_posts_ui, daemon=True, name='DefaultPostsUI').start()
                else:
                    raise Exception('Failed to load default posts')
            else:
                warning('[FORUM_TAB] No categories available for loading posts')
                self.posts = []
                self.update_posts_ui('No Categories')
        except Exception as e:
            error(f'[FORUM_TAB] Posts loading failed: {str(e)}')
            self._show_error_notification('Posts Load Failed', f'Failed to load posts: {str(e)}')
        finally:
            self._set_loading_safe(False)

    def update_posts_ui(self, category_name: str):
        """OPTIMIZED: Update posts UI with batched operations"""
        try:
            if not dpg.does_item_exist('posts_list_area'):
                return
            dpg.delete_item('posts_list_area', children_only=True)
            posts_created = 0
            for post in self.posts:
                try:
                    self._create_post_item_fast(post)
                    posts_created += 1
                except Exception as e:
                    debug(f'[FORUM_TAB] Post item creation failed: {str(e)}')
            if dpg.does_item_exist('current_category_name'):
                dpg.set_value('current_category_name', category_name)
            info(f'[FORUM_TAB] Posts UI updated: {posts_created} posts displayed for {category_name}')
        except Exception as e:
            error(f'[FORUM_TAB] Posts UI update failed: {str(e)}')

    def _create_post_item_fast(self, post_data: Dict[str, Any]):
        """PERFORMANCE: Fast post item creation with minimal validation"""
        try:
            if not post_data:
                return
            post_uuid = post_data.get('post_uuid', '')
            title = post_data.get('title', 'Untitled')
            content = post_data.get('content', '')
            author_display_name = post_data.get('author_display_name', 'Unknown')
            likes = post_data.get('likes', 0)
            dislikes = post_data.get('dislikes', 0)
            reply_count = post_data.get('reply_count', 0)
            views = post_data.get('views', 0)
            created_at = post_data.get('created_at', '')
            category_name = post_data.get('category_name', 'General')
            is_pinned = post_data.get('is_pinned', False)
            if not post_uuid:
                return
            vote_score = likes - dislikes
            with dpg.group(parent='posts_list_area'):
                with dpg.child_window(width=-1, height=120, border=True):
                    with dpg.group(horizontal=True):
                        if is_pinned:
                            dpg.add_text('📌', color=self.BLOOMBERG_ORANGE)
                        title_display = title[:50] + '...' if len(title) > 50 else title
                        dpg.add_button(label=title_display, callback=self._safe_callback(lambda uuid=post_uuid: self.view_post_details(uuid), f'VIEW_POST_{post_uuid[:8]}'), width=350, height=25)
                        dpg.add_text(f'[{category_name}]', color=self.BLOOMBERG_BLUE)
                    with dpg.group(horizontal=True):
                        dpg.add_text(f'👁 {views}', color=self.BLOOMBERG_GRAY)
                        dpg.add_spacer(width=15)
                        vote_color = self.BLOOMBERG_GREEN if vote_score > 0 else self.BLOOMBERG_RED if vote_score < 0 else self.BLOOMBERG_GRAY
                        dpg.add_text(f'👍 {vote_score}', color=vote_color)
                        dpg.add_spacer(width=15)
                        dpg.add_text(f'💬 {reply_count}', color=self.BLOOMBERG_BLUE)
                        dpg.add_spacer(width=15)
                        dpg.add_text(f'By: {author_display_name}', color=self.BLOOMBERG_WHITE)
                        dpg.add_spacer(width=15)
                        time_str = self._format_timestamp_fast(created_at)
                        dpg.add_text(time_str, color=self.BLOOMBERG_GRAY)
                    preview = content[:80] + '...' if len(content) > 80 else content
                    dpg.add_text(preview, color=self.BLOOMBERG_WHITE, wrap=600)
                    self._create_post_action_buttons_fast(post_uuid)
                dpg.add_spacer(height=5)
        except Exception as e:
            debug(f'[FORUM_TAB] Fast post item creation failed: {str(e)}')

    def _format_timestamp_fast(self, created_at: str) -> str:
        """PERFORMANCE: Fast timestamp formatting"""
        try:
            if not created_at:
                return 'Recent'
            if created_at.endswith('Z'):
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(created_at)
            return dt.strftime('%m/%d %H:%M')
        except Exception:
            return 'Recent'

    def _create_post_action_buttons_fast(self, post_uuid: str):
        """PERFORMANCE: Fast action buttons creation"""
        try:
            with dpg.group(horizontal=True):
                dpg.add_button(label='VIEW', callback=self._safe_callback(lambda: self.view_post_details(post_uuid), f'VIEW_{post_uuid[:8]}'), width=60, height=20)
                if self._is_authenticated_cached():
                    dpg.add_button(label='👍 UP', callback=self._safe_callback(lambda: self.vote_on_post(post_uuid, 'up'), f'UPVOTE_{post_uuid[:8]}'), width=70, height=20)
                    dpg.add_button(label='👎 DOWN', callback=self._safe_callback(lambda: self.vote_on_post(post_uuid, 'down'), f'DOWNVOTE_{post_uuid[:8]}'), width=70, height=20)
                    dpg.add_button(label='REPLY', callback=self._safe_callback(lambda: self.reply_to_post(post_uuid), f'REPLY_{post_uuid[:8]}'), width=60, height=20)
        except Exception as e:
            debug(f'[FORUM_TAB] Action buttons creation failed: {str(e)}')

    def vote_on_post(self, post_identifier: str, vote_type: str):
        """OPTIMIZED: Vote on post with background processing"""
        try:
            if not self._is_authenticated_cached():
                self._show_error_notification('Registration Required', 'You must be registered to vote on posts.')
                return
            if not post_identifier or len(post_identifier) < 10:
                self._show_error_notification('Error', 'Invalid post format.')
                return

            def vote_async():
                try:
                    if not self.api_client:
                        return
                    result = self.api_client.make_request('POST', f'/forum/posts/{post_identifier}/vote', data={'vote_type': vote_type})
                    if result and result.get('success') and result.get('data', {}).get('success'):
                        vote_data = result['data']['data']
                        vote_action = vote_data.get('action', 'added')
                        if vote_action == 'added':
                            info(f'[FORUM_TAB] Vote added: {vote_type} on {post_identifier[:8]}')
                        elif vote_action == 'removed':
                            info(f'[FORUM_TAB] Vote removed: {vote_type} on {post_identifier[:8]}')
                        elif vote_action == 'changed':
                            info(f'[FORUM_TAB] Vote changed on {post_identifier[:8]}')

                        def refresh_data():
                            try:
                                self.load_posts(self.current_category)
                                self.load_categories()
                            except Exception:
                                pass
                        threading.Thread(target=refresh_data, daemon=True, name='VoteRefresh').start()
                    else:
                        error_msg = 'Unknown error'
                        if result and isinstance(result.get('data'), dict):
                            error_msg = result['data'].get('message', 'Unknown error')
                        warning(f'[FORUM_TAB] Vote failed: {error_msg}')
                except Exception as vote_error:
                    error(f'[FORUM_TAB] Vote operation failed: {str(vote_error)}')
            threading.Thread(target=vote_async, daemon=True, name=f'Vote-{vote_type}').start()
        except Exception as e:
            error(f'[FORUM_TAB] Vote initiation failed: {str(e)}')

    def view_post_details(self, post_uuid: str):
        """OPTIMIZED: View post details with lightweight popup"""
        try:
            info(f'[FORUM_TAB] Viewing post details: {post_uuid[:8]}')
            if not post_uuid:
                return
            if not dpg.does_item_exist('post_detail_window'):
                with dpg.window(label='POST DETAILS', tag='post_detail_window', width=800, height=600, pos=[200, 100], modal=True):
                    dpg.add_text('Loading post details...', tag='post_detail_content', color=self.BLOOMBERG_YELLOW)
                    dpg.add_separator()
                    with dpg.group(horizontal=True):
                        dpg.add_button(label='CLOSE', callback=self._safe_callback(lambda: dpg.delete_item('post_detail_window'), 'CLOSE_POST_DETAILS'), width=100)
                        if self._is_authenticated_cached():
                            dpg.add_spacer(width=20)
                            dpg.add_input_text(hint='Add a comment...', width=400, tag='new_comment_input')
                            dpg.add_button(label='POST COMMENT', callback=self._safe_callback(lambda: self.add_comment(post_uuid), 'POST_COMMENT'), width=120)

            def load_details_async():
                try:
                    if not self.api_client:
                        return
                    result = self.api_client.make_request('GET', f'/forum/posts/{post_uuid}')
                    if result and result.get('success') and result.get('data', {}).get('success'):
                        post_data = result['data']['data']
                        post = post_data.get('post', {})
                        comments = post_data.get('comments', [])
                        content_text = self._format_post_details_fast(post, comments)
                        if dpg.does_item_exist('post_detail_content'):
                            dpg.set_value('post_detail_content', content_text)
                        info(f'[FORUM_TAB] Post details loaded: {len(comments)} comments')
                    elif dpg.does_item_exist('post_detail_content'):
                        dpg.set_value('post_detail_content', 'Error loading post details')
                except Exception as e:
                    error(f'[FORUM_TAB] Post details loading failed: {str(e)}')
                    if dpg.does_item_exist('post_detail_content'):
                        dpg.set_value('post_detail_content', f'Error: {str(e)}')
            threading.Thread(target=load_details_async, daemon=True, name='PostDetails').start()
            dpg.show_item('post_detail_window')
        except Exception as e:
            error(f'[FORUM_TAB] Post details view failed: {str(e)}')

    def _format_post_details_fast(self, post: Dict[str, Any], comments: List[Dict[str, Any]]) -> str:
        """PERFORMANCE: Fast post details formatting"""
        try:
            content_text = f'Title: {post.get('title', 'N/A')}\n\n'
            content_text += f'Author: {post.get('author_display_name', 'Unknown')}\n'
            content_text += f'Category: {post.get('category_name', 'General')}\n'
            content_text += f'Views: {post.get('views', 0)} | '
            content_text += f'Likes: {post.get('likes', 0)} | '
            content_text += f'Comments: {len(comments)}\n\n'
            content_text += f'Content:\n{post.get('content', 'N/A')}\n\n'
            if comments:
                content_text += 'Recent Comments:\n'
                for comment in comments[:5]:
                    author = comment.get('author_display_name', 'Unknown')
                    comment_content = comment.get('content', '')[:100]
                    content_text += f'- {author}: {comment_content}...\n'
            return content_text
        except Exception:
            return 'Error formatting post details'

    def load_forum_stats(self):
        """OPTIMIZED: Load forum statistics with background processing"""
        try:
            if not self.api_client:
                raise Exception('API client not available')

            def load_stats_async():
                try:
                    result = self.api_client.make_request('GET', '/forum/stats')
                    if result and result.get('success') and result.get('data', {}).get('success'):
                        stats = result['data']['data']
                        stats_updates = [('stat_total_categories', f'Categories: {stats.get('total_categories', 0)}'), ('stat_total_posts', f'Total Posts: {stats.get('total_posts', 0)}'), ('stat_total_comments', f'Total Comments: {stats.get('total_comments', 0)}'), ('stat_total_votes', f'Total Votes: {stats.get('total_votes', 0)}')]
                        for tag, text in stats_updates:
                            if dpg.does_item_exist(tag):
                                dpg.set_value(tag, text)
                        info(f'[FORUM_TAB] Forum statistics loaded: {stats.get('total_posts', 0)} posts')
                    else:
                        warning('[FORUM_TAB] Failed to load forum statistics')
                except Exception as e:
                    error(f'[FORUM_TAB] Stats loading failed: {str(e)}')
            threading.Thread(target=load_stats_async, daemon=True, name='ForumStats').start()
        except Exception as e:
            error(f'[FORUM_TAB] Forum stats loading failed: {str(e)}')

    def filter_by_category(self, category_id: Optional[int]):
        """OPTIMIZED: Filter posts by category with background loading"""
        try:
            info(f'[FORUM_TAB] Filtering posts by category: {category_id}')
            self.current_category = category_id

            def load_category_posts_async():
                self.load_posts(category_id)
            threading.Thread(target=load_category_posts_async, daemon=True, name=f'CategoryFilter-{category_id}').start()
        except Exception as e:
            error(f'[FORUM_TAB] Category filtering failed: {str(e)}')

    def execute_search(self):
        """OPTIMIZED: Execute forum search with background processing"""
        try:
            search_term = ''
            if dpg.does_item_exist('forum_search_input'):
                search_term = dpg.get_value('forum_search_input')
            if not search_term or search_term == 'Search posts, topics...':
                return
            info(f'[FORUM_TAB] Executing search: {search_term[:20]}')

            def search_async():
                try:
                    self._set_loading_safe(True)
                    if not self.api_client:
                        return
                    result = self.api_client.make_request('GET', '/forum/search', params={'q': search_term, 'post_type': 'all', 'limit': 20})
                    if result and result.get('success') and result.get('data', {}).get('success'):
                        search_data = result['data']['data']
                        results = search_data.get('results', {})
                        posts = results.get('posts', [])
                        info(f'[FORUM_TAB] Search completed: {len(posts)} results')
                        if dpg.does_item_exist('posts_list_area'):
                            dpg.delete_item('posts_list_area', children_only=True)
                        for post in posts:
                            try:
                                self._create_post_item_fast(post)
                            except Exception:
                                pass
                        if dpg.does_item_exist('current_category_name'):
                            dpg.set_value('current_category_name', f"Search: '{search_term}'")
                    else:
                        warning(f'[FORUM_TAB] Search request failed: {search_term}')
                except Exception as e:
                    error(f'[FORUM_TAB] Search operation failed: {str(e)}')
                finally:
                    self._set_loading_safe(False)
            threading.Thread(target=search_async, daemon=True, name='ForumSearch').start()
        except Exception as e:
            error(f'[FORUM_TAB] Search execution failed: {str(e)}')

    def on_search_input_change(self, sender, app_data):
        """Handle search input changes"""
        pass

    def sort_posts_callback(self, sender, app_data):
        """Handle post sorting"""
        try:

            def sort_async():
                self.load_posts(self.current_category)
            threading.Thread(target=sort_async, daemon=True, name='PostSort').start()
        except Exception as e:
            debug(f'[FORUM_TAB] Sort callback failed: {str(e)}')

    def reply_to_post(self, post_uuid: str):
        """Reply to a post"""
        self.view_post_details(post_uuid)

    def add_comment(self, post_uuid: str):
        """Add comment to post"""
        debug(f'[FORUM_TAB] Add comment requested: {post_uuid[:8]}')

    def show_forum_help(self):
        """Show forum help"""
        info('[FORUM_TAB] Forum help requested')

    def refresh_forum(self):
        """Refresh entire forum"""
        info('[FORUM_TAB] Forum refresh requested')

        def refresh_async():
            self.load_initial_data_optimized()
        threading.Thread(target=refresh_async, daemon=True, name='ForumRefresh').start()

    def create_new_post(self):
        """Create new post dialog"""
        info('[FORUM_TAB] New post creation requested')

    def focus_search(self):
        """Focus search field"""
        try:
            if dpg.does_item_exist('forum_search_input'):
                dpg.focus_item('forum_search_input')
                dpg.set_value('forum_search_input', '')
        except Exception as e:
            debug(f'[FORUM_TAB] Search focus failed: {str(e)}')

    def show_trending(self):
        """Show trending posts"""
        info('[FORUM_TAB] Trending posts requested')

    def show_trending_posts(self):
        """Show trending posts (button callback)"""
        self.show_trending()

    def show_recent_posts(self):
        """Show recent posts"""
        info('[FORUM_TAB] Recent posts requested')

    def show_user_profile(self):
        """Show user profile"""
        info('[FORUM_TAB] User profile requested')

    def show_my_posts(self):
        """Show current user's posts"""
        info("[FORUM_TAB] User's posts requested")

    def show_my_activity(self):
        """Show user activity"""
        info('[FORUM_TAB] User activity requested')

    def show_user_settings(self):
        """Show user settings"""
        info('[FORUM_TAB] User settings requested')

    def show_upgrade_info(self):
        """Show upgrade information for guests"""
        info('[FORUM_TAB] Upgrade information requested')

    def cleanup(self):
        """OPTIMIZED: Fast cleanup with minimal operations"""
        try:
            info('[FORUM_TAB] Cleaning up Forum Tab resources')
            self.categories.clear()
            self.posts.clear()
            self.search_results.clear()
            self.forum_stats.clear()
            self.current_category = None
            self.current_post_uuid = None
            self.loading = False
            self.ui_initialized = False
            self._auth_cached = None
            self._user_info_cached = None

            def close_dialogs_async():
                dialog_windows = ['post_detail_window', 'new_post_window', 'forum_help_window', 'user_profile_window', 'user_settings_window', 'upgrade_info_window']
                for window in dialog_windows:
                    try:
                        if dpg.does_item_exist(window):
                            dpg.delete_item(window)
                    except Exception:
                        pass
            threading.Thread(target=close_dialogs_async, daemon=True, name='ForumCleanup').start()
            info('[FORUM_TAB] Forum Tab cleanup completed')
        except Exception as e:
            error(f'[FORUM_TAB] Cleanup failed: {str(e)}')

    def resize_components(self, left_width: int, center_width: int, right_width: int, top_height: int, bottom_height: int, cell_height: int):
        """OPTIMIZED: Fast component resizing"""
        try:
            panel_updates = [('categories_panel', left_width), ('posts_panel', center_width), ('user_panel', right_width)]
            for panel_tag, width in panel_updates:
                try:
                    if dpg.does_item_exist(panel_tag):
                        dpg.configure_item(panel_tag, width=width)
                except Exception:
                    pass
            debug(f'[FORUM_TAB] Components resized: {left_width}x{center_width}x{right_width}')
        except Exception as e:
            debug(f'[FORUM_TAB] Component resizing failed: {str(e)}')

def refresh_data():
    try:
        self.load_posts(self.current_category)
        self.load_categories()
    except Exception:
        pass

def load_category_posts_async():
    self.load_posts(category_id)

def sort_async():
    self.load_posts(self.current_category)

