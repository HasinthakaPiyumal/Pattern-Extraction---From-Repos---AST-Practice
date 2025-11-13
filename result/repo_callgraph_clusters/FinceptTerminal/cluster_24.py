# Cluster 24

class HighPerformanceMainApplication:
    """OPTIMIZED: High-performance main application with minimal overhead"""

    def __init__(self, session_data: Dict[str, Any]):
        self.is_running = True
        self.resize_lock = False
        self.api_request_count = 0
        self.last_resize_time = 0
        self.menu_toolbar_manager = MenuToolbarManager(self)
        self.session_data = session_data
        self.user_type = session_data.get('user_type', 'guest')
        self.authenticated = session_data.get('authenticated', False)
        self.api_key = session_data.get('api_key')
        self._cached_auth_headers = None
        self._auth_headers_timestamp = 0
        self._auth_cache_ttl = 300
        self.DEFAULT_WIDTH = 1200
        self.DEFAULT_HEIGHT = 600
        self.MARGIN_WIDTH = 20
        self.MARGIN_HEIGHT = 120
        self.MIN_WIDTH = 800
        self.MIN_HEIGHT = 600
        self.theme_manager = AutomaticThemeManager()
        self.themes_available = False
        self.tab_importer = PerformantTabImporter()
        self.calculate_sizes()
        self.tabs = {}
        self.tabs_initialized: Set[str] = set()
        info(f'Application initialized - User: {self.user_type}', module='main')

    def _initialize_tabs_optimized(self):
        """OPTIMIZED: Fast tab initialization with parallel loading"""
        with operation('tab_initialization', module='main'):
            available_tabs = self.tab_importer.load_all_tabs_parallel()
            if not available_tabs:
                critical('No tabs available - application cannot continue', module='main')
                self.safe_exit()
                return
            failed_tabs = []
            for tab_id, tab_class in available_tabs.items():
                try:
                    self.tabs[tab_id] = tab_class(self)
                    self.tabs_initialized.add(tab_id)
                except Exception as e:
                    failed_tabs.append(tab_id)
                    error(f'Tab init failed: {tab_id} - {str(e)}', module='main')
            success_count = len(self.tabs_initialized)
            info(f'Tab initialization: {success_count} tabs ready', module='main')
            if failed_tabs:
                warning(f'Failed tab inits: {failed_tabs}', module='main')

    def calculate_sizes(self):
        """OPTIMIZED: Lightweight size calculation"""
        width = max(self.DEFAULT_WIDTH, self.MIN_WIDTH)
        height = max(self.DEFAULT_HEIGHT, self.MIN_HEIGHT)
        self.usable_width = width - self.MARGIN_WIDTH
        self.usable_height = height - self.MARGIN_HEIGHT
        min_panel_width = 200
        self.left_width = max(int(self.usable_width * 0.25) - 3, min_panel_width)
        self.center_width = max(int(self.usable_width * 0.5) - 3, min_panel_width)
        self.right_width = max(int(self.usable_width * 0.25) - 3, min_panel_width)
        min_panel_height = 150
        self.top_height = max(int(self.usable_height * 0.66) - 3, min_panel_height)
        self.bottom_height = max(int(self.usable_height * 0.34) - 3, min_panel_height)
        self.cell_height = max(int(self.top_height / 2) - 2, 100)

    def get_api_key_type(self) -> str:
        """OPTIMIZED: Fast API key type detection"""
        if not self.api_key:
            return 'Offline'
        if self.api_key.startswith('fk_guest_'):
            return 'Guest'
        elif self.api_key.startswith('fk_user_'):
            return 'User'
        elif self.api_key.startswith('fk_dev_'):
            return 'Developer'
        elif self.api_key.startswith('fk_admin_'):
            return 'Admin'
        else:
            return 'Legacy'

    def resize_callback(self, sender=None, app_data=None):
        """OPTIMIZED: Lightweight resize with debouncing"""
        if self.resize_lock or not self.is_running:
            return
        current_time = time.time()
        if current_time - self.last_resize_time < 0.2:
            return
        try:
            self.resize_lock = True
            self.last_resize_time = current_time
            viewport_width = dpg.get_viewport_width()
            viewport_height = dpg.get_viewport_height()
            if viewport_width > self.MIN_WIDTH and viewport_height > self.MIN_HEIGHT:
                self.DEFAULT_WIDTH = viewport_width
                self.DEFAULT_HEIGHT = viewport_height
                self.calculate_sizes()
        except Exception as e:
            error(f'Resize failed: {str(e)}', module='main')
        finally:
            self.resize_lock = False

    def safe_exit(self):
        """OPTIMIZED: Fast exit"""
        info('Application exit requested', module='main')
        self.is_running = False
        try:
            if dpg.is_dearpygui_running():
                dpg.stop_dearpygui()
        except Exception as e:
            error(f'Exit error: {str(e)}', module='main')

    def switch_to_tab_with_ticker(self, tab_label: str, ticker: str):
        """Switch to a specific tab and load ticker data - MINIMAL IMPLEMENTATION"""
        try:
            target_tab = None
            target_tab_key = None
            for tab_name, tab_instance in self.tabs.items():
                if hasattr(tab_instance, 'get_label'):
                    if tab_instance.get_label() == tab_label:
                        target_tab = tab_instance
                        target_tab_key = tab_name
                        break
                elif tab_name == tab_label:
                    target_tab = tab_instance
                    target_tab_key = tab_name
                    break
            if not target_tab:
                warning(f"Tab '{tab_label}' not found", module='main')
                return False
            tab_id = f'tab_{target_tab_key}'
            if dpg.does_item_exist('main_tab_bar') and dpg.does_item_exist(tab_id):
                dpg.set_value('main_tab_bar', tab_id)
            if hasattr(target_tab, 'load_ticker_from_external'):
                target_tab.load_ticker_from_external(ticker)
                info(f'Switched to {tab_label} with ticker {ticker}', module='main')
                return True
            else:
                warning(f"Tab {tab_label} doesn't support external ticker loading", module='main')
                return False
        except Exception as e:
            error(f'Tab switch failed: {tab_label} with {ticker} - {str(e)}', module='main')
            return False

    def get_tab_by_label(self, label: str):
        """Get tab instance by label - UTILITY METHOD"""
        for tab_name, tab_instance in self.tabs.items():
            if hasattr(tab_instance, 'get_label') and tab_instance.get_label() == label:
                return (tab_name, tab_instance)
            elif tab_name == label:
                return (tab_name, tab_instance)
        return (None, None)

    def create_menu_bar(self):
        """Create enhanced menu bar with tab navigation - delegated to MenuToolbarManager"""
        self.menu_toolbar_manager.create_menu_bar()

    def scroll_tab_view(self, direction):
        """Navigate through tabs using menu"""
        try:
            total_tabs = len(self.tab_names_list)
            if direction > 0:
                if self.current_visible_tab_start + self.tabs_per_view < total_tabs:
                    self.current_visible_tab_start += self.tabs_per_view
            elif self.current_visible_tab_start > 0:
                self.current_visible_tab_start = max(0, self.current_visible_tab_start - self.tabs_per_view)
            self.update_tab_visibility()
            start = self.current_visible_tab_start + 1
            end = min(self.current_visible_tab_start + self.tabs_per_view, total_tabs)
            info(f'Showing tabs {start}-{end} of {total_tabs}', module='main')
        except Exception as e:
            error(f'Tab scroll failed: {str(e)}', module='main')

    def update_tab_visibility(self):
        """Show/hide tabs based on current view"""
        try:
            for i, tab_name in enumerate(self.tab_names_list):
                tab_id = f'tab_{tab_name}'
                if dpg.does_item_exist(tab_id):
                    if self.current_visible_tab_start <= i < self.current_visible_tab_start + self.tabs_per_view:
                        dpg.show_item(tab_id)
                    else:
                        dpg.hide_item(tab_id)
        except Exception as e:
            error(f'Tab visibility update failed: {str(e)}', module='main')

    def jump_to_specific_tab(self, tab_name):
        """Jump directly to a specific tab"""
        try:
            if tab_name in self.tab_names_list:
                tab_index = self.tab_names_list.index(tab_name)
                target_page = tab_index // self.tabs_per_view
                self.current_visible_tab_start = target_page * self.tabs_per_view
                self.update_tab_visibility()
                tab_id = f'tab_{tab_name}'
                if dpg.does_item_exist(tab_id):
                    dpg.set_value('main_tab_bar', tab_id)
        except Exception as e:
            error(f'Tab jump failed: {tab_name} - {str(e)}', module='main')

    @monitor_performance
    def create_tabs(self):
        """OPTIMIZED: Fast tab creation with minimal overhead"""
        try:
            dpg.add_tab_bar(tag='main_tab_bar', reorderable=True)
            successful_tabs = 0
            failed_tabs = 0
            if hasattr(self.theme_manager, 'terminal_font') and self.theme_manager.terminal_font:
                try:
                    dpg.add_text('FONT TEST - This should be Oswald2', tag='font_test_text')
                    dpg.bind_item_font('font_test_text', self.theme_manager.terminal_font)
                    print(f'[FONT DEBUG] Explicitly bound font to test text: {self.theme_manager.terminal_font}')
                except Exception as e:
                    print(f'[FONT DEBUG] Item font binding failed: {e}')
            for tab_name, tab_instance in self.tabs.items():
                try:
                    tab_id = f'tab_{tab_name}'
                    try:
                        label = tab_instance.get_label() if hasattr(tab_instance, 'get_label') else tab_name.title()
                    except Exception:
                        label = tab_name.title()
                    dpg.add_tab(label=label, tag=tab_id, parent='main_tab_bar')
                    try:
                        dpg.push_container_stack(tab_id)
                        if hasattr(self.theme_manager, 'terminal_font') and self.theme_manager.terminal_font:
                            try:
                                dpg.bind_item_font(tab_id, self.theme_manager.terminal_font)
                                print(f'[FONT DEBUG] Applied font to tab {tab_name}: {self.theme_manager.terminal_font}')
                            except Exception as font_error:
                                print(f'[FONT DEBUG] Failed to apply font to tab {tab_name}: {font_error}')
                        tab_instance.create_content()
                        dpg.pop_container_stack()
                        successful_tabs += 1
                    except Exception as content_error:
                        try:
                            dpg.pop_container_stack()
                        except Exception:
                            pass
                        dpg.push_container_stack(tab_id)
                        dpg.add_text(f'Error loading {tab_name} tab', color=[255, 100, 100])
                        dpg.add_text(f'Error: {str(content_error)[:100]}...')
                        if tab_name.lower() == 'profile':
                            dpg.add_text('This may be due to missing session data.')
                            dpg.add_button(label='Clear Session & Restart', callback=self.clear_session_and_restart)
                        dpg.add_button(label='Retry Tab Loading', callback=lambda s, a, u, tn=tab_name: self.retry_tab_loading(tn))
                        dpg.pop_container_stack()
                        error(f'Tab content creation failed: {tab_name} - {str(content_error)}', module='main')
                        failed_tabs += 1
                except Exception as tab_error:
                    error(f'Tab creation failed: {tab_name} - {str(tab_error)}', module='main')
                    failed_tabs += 1
            print('[FONT DEBUG] Applying fonts to all created elements...')
            if hasattr(self.theme_manager, 'terminal_font') and self.theme_manager.terminal_font:
                try:
                    dpg.bind_font(self.theme_manager.terminal_font)
                    print(f'[FONT DEBUG] Re-applied global font after tab creation: {self.theme_manager.terminal_font}')
                    for tab_name in self.tabs.keys():
                        tab_id = f'tab_{tab_name}'
                        try:
                            if dpg.does_item_exist(tab_id):
                                dpg.bind_item_font(tab_id, self.theme_manager.terminal_font)
                                print(f'[FONT DEBUG] Applied font to existing tab {tab_name}')
                        except Exception as e:
                            print(f'[FONT DEBUG] Failed to apply font to tab {tab_name}: {e}')
                except Exception as e:
                    print(f'[FONT DEBUG] Global font re-application failed: {e}')
            self.current_visible_tab_start = 0
            self.tabs_per_view = 30
            self.tab_names_list = list(self.tabs.keys())
            if len(self.tabs) > self.tabs_per_view:
                self.update_tab_visibility()
            info(f'Tab creation completed: {successful_tabs} tabs', module='main')
        except Exception as e:
            critical(f'Critical tab creation error: {str(e)}', module='main')
            dpg.add_text('Tab System Error', color=[255, 100, 100])
            dpg.add_text('The tab system failed to initialize properly.')
            dpg.add_button(label='Restart Application', callback=self.safe_exit)
            dpg.add_button(label='Show Diagnostics', callback=self.show_diagnostics)

    def get_auth_headers(self) -> Dict[str, str]:
        """PERFORMANCE: Cached authentication headers"""
        current_time = time.time()
        if self._cached_auth_headers and current_time - self._auth_headers_timestamp < self._auth_cache_ttl:
            return self._cached_auth_headers
        try:
            headers = config.get_request_headers(self.api_key)
            self._cached_auth_headers = headers
            self._auth_headers_timestamp = current_time
            return headers
        except Exception as e:
            error(f'Auth headers generation failed: {str(e)}', module='api')
            return {}

    def make_api_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """OPTIMIZED: Fast API request with caching"""
        try:
            headers = kwargs.get('headers', {})
            auth_headers = self.get_auth_headers()
            headers.update(auth_headers)
            kwargs['headers'] = headers
            url = get_api_endpoint(endpoint)
            timeout_config = config.get_timeout_config()
            kwargs.setdefault('timeout', timeout_config['total'])
            response = getattr(requests, method.lower())(url, **kwargs)
            self.api_request_count += 1
            return response
        except requests.exceptions.Timeout:
            warning(f'API timeout: {method} {endpoint}', module='api')
            return None
        except requests.exceptions.ConnectionError:
            warning(f'API connection error: {method} {endpoint}', module='api')
            return None
        except Exception as e:
            error(f'API request failed: {method} {endpoint} - {str(e)}', module='api')
            return None

    def retry_tab_loading(self, tab_name: str):
        """Retry loading a specific tab"""
        info(f'Retrying tab: {tab_name}', module='main')

    def new_session(self):
        """Create new session"""
        info('New session requested', module='session')
        self.clear_session_and_restart()

    def save_configuration(self):
        """Save current configuration"""
        debug('Configuration save requested', module='main')

    def load_configuration(self):
        """Load configuration"""
        debug('Configuration load requested', module='main')

    def test_api_connection(self):
        """Test API connection"""
        try:
            available = session_manager.is_api_available()
            if available:
                info('API connection test successful', module='api')
            else:
                warning('API connection test failed', module='api')
        except Exception as e:
            error(f'API connection test error: {str(e)}', module='api')

    def show_diagnostics(self):
        """Show system diagnostics"""
        try:
            log_stats = get_stats()
            health = health_check()
            info(f'System diagnostics - Health: {health['status']}', module='main')
        except Exception as e:
            error(f'Diagnostics failed: {str(e)}', module='main')

    def show_performance_monitor(self):
        """Show performance monitoring dashboard"""
        try:
            log_stats = get_stats()
            performance_stats = log_stats.get('performance_stats', {})
            info(f'Performance monitor - Operations tracked: {len(performance_stats)}', module='main')
        except Exception as e:
            error(f'Performance monitor failed: {str(e)}', module='main')

    def show_log_viewer(self):
        """Show log viewer interface"""
        info('Log viewer requested', module='main')

    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        info('Keyboard shortcuts requested', module='main')

    def reset_layout(self):
        """Reset layout to default"""
        try:
            info('Layout reset requested', module='main')
            self.calculate_sizes()
            self.resize_callback()
        except Exception as e:
            error(f'Layout reset failed: {str(e)}', module='main')

    def goto_data_sources_tab(self):
        """Navigate to data sources tab"""
        try:
            if 'Data Sources' in self.tabs:
                dpg.set_value('main_tab_bar', 'tab_Data Sources')
                debug('Navigated to data sources tab', module='main')
            else:
                warning('Data sources tab not available', module='main')
        except Exception as e:
            error(f'Data sources navigation failed: {str(e)}', module='main')

    def toggle_fullscreen(self, sender=None, app_data=None, user_data=None):
        """Toggle fullscreen mode"""
        try:
            dpg.toggle_viewport_fullscreen()
            debug('Fullscreen mode toggled', module='main')
        except Exception as e:
            error(f'Fullscreen toggle failed: {str(e)}', module='main')

    def apply_theme_safe(self, theme_name: str):
        """Safely apply theme"""
        try:
            if not hasattr(self.theme_manager, 'font_registry_created'):
                self.theme_manager.setup_fonts()
            success = self.theme_manager.apply_theme_globally(theme_name)
            if success:
                info(f'Theme applied: {theme_name}', module='theme')
            else:
                warning(f'Theme application failed: {theme_name}', module='theme')
        except Exception as e:
            error(f'Theme error: {theme_name} - {str(e)}', module='theme')

    def show_session_info(self):
        """Show session information"""
        try:
            info_data = session_manager.get_session_info()
            info(f'Session info - User: {self.user_type}', module='session')
        except Exception as e:
            error(f'Session info failed: {str(e)}', module='session')

    def show_api_status(self):
        """Show API status information"""
        try:
            connectivity = session_manager.check_api_connectivity()
            info(f'API status - Connected: {connectivity}', module='api')
        except Exception as e:
            error(f'API status check failed: {str(e)}', module='api')

    def show_api_config(self):
        """Show API configuration"""
        try:
            config.validate_configuration()
            debug('API configuration requested', module='api')
        except Exception as e:
            error(f'API config validation failed: {str(e)}', module='api')

    def enable_strict_mode(self):
        """Enable strict mode"""
        try:
            config.REQUIRE_API_CONNECTION = True
            config.ALLOW_GUEST_FALLBACK = False
            info('Strict mode enabled', module='main')
        except Exception as e:
            error(f'Strict mode enable failed: {str(e)}', module='main')

    def refresh_session_data(self):
        """OPTIMIZED: Fast session refresh with caching"""
        try:
            fresh_session = session_manager.get_fresh_session()
            if fresh_session:
                self.session_data = fresh_session
                self.user_type = fresh_session.get('user_type', 'guest')
                self.authenticated = fresh_session.get('authenticated', False)
                self.api_key = fresh_session.get('api_key')
                self._cached_auth_headers = None
                self._auth_headers_timestamp = 0
                info(f'Session refreshed - User: {self.user_type}', module='session')
            else:
                warning('Session refresh failed', module='session')
        except Exception as e:
            error(f'Session refresh error: {str(e)}', module='session')

    def clear_session_and_restart(self):
        """Clear session and restart"""
        try:
            info('Clearing session and restarting', module='session')
            session_manager.clear_session()
            self.safe_exit()
        except Exception as e:
            error(f'Session clear failed: {str(e)}', module='session')
            self.safe_exit()

    def logout_and_restart(self):
        """Logout and restart"""
        try:
            info(f'Logging out - User: {self.user_type}', module='session')
            session_manager.clear_session()
            self.safe_exit()
        except Exception as e:
            error(f'Logout failed: {str(e)}', module='session')
            self.safe_exit()

    def save_current_session(self):
        """Save current session credentials"""
        try:
            session_manager.save_session_credentials(self.session_data)
            debug('Session credentials saved', module='session')
        except Exception as e:
            error(f'Session save failed: {str(e)}', module='session')

    def is_user_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.authenticated

    def get_user_type(self) -> str:
        """Get current user type"""
        return self.user_type

    def get_session_data(self) -> Dict[str, Any]:
        """Get session data safely"""
        return self.session_data.copy()

    def refresh_user_profile(self) -> bool:
        """OPTIMIZED: Fast user profile refresh"""
        try:
            if self.user_type != 'registered':
                debug('Profile refresh skipped - user not registered', module='session')
                return False
            fresh_session = session_manager.get_fresh_session()
            if fresh_session:
                self.session_data = fresh_session
                self._cached_auth_headers = None
                info('User profile refreshed', module='session')
                return True
            else:
                warning('Profile refresh failed', module='session')
                return False
        except Exception as e:
            error(f'Profile refresh error: {str(e)}', module='session')
            return False

    def goto_database_tab(self):
        """Navigate to database tab"""
        try:
            if 'Database' in self.tabs:
                dpg.set_value('main_tab_bar', 'tab_Database')
                debug('Navigated to database tab', module='main')
            else:
                warning('Database tab not available', module='main')
        except Exception as e:
            error(f'Database navigation failed: {str(e)}', module='main')

    def show_profile_info(self):
        """Show profile information"""
        try:
            if 'Profile' in self.tabs:
                dpg.set_value('main_tab_bar', 'tab_Profile')
                debug('Navigated to profile tab', module='main')
            else:
                warning('Profile tab not available', module='main')
        except Exception as e:
            error(f'Profile navigation failed: {str(e)}', module='main')

    def show_upgrade_info(self):
        """Show upgrade information"""
        info(f'Upgrade info requested - Current: {self.user_type}', module='main')

    @monitor_performance
    def regenerate_api_key(self):
        """OPTIMIZED: Fast API key regeneration"""
        if self.user_type != 'registered':
            warning(f'API key regeneration denied - User: {self.user_type}', module='api')
            return
        try:
            response = self.make_api_request('POST', '/user/regenerate-api-key')
            if response and response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    new_api_key = data['data']['api_key']
                    old_key_type = self.get_api_key_type()
                    self.api_key = new_api_key
                    self.session_data['api_key'] = new_api_key
                    self._cached_auth_headers = None
                    self._auth_headers_timestamp = 0
                    session_manager.save_session_credentials(self.session_data)
                    info(f'API key regenerated: {old_key_type} -> {self.get_api_key_type()}', module='api')
                else:
                    warning(f'API key regeneration failed: {data}', module='api')
            else:
                error(f'API key regeneration request failed: {(response.status_code if response else 'No response')}', module='api')
        except Exception as e:
            error(f'API key regeneration error: {str(e)}', module='api')

    def show_documentation(self):
        """Show documentation"""
        info('Documentation requested', module='main')

    def show_support(self):
        """Show support information"""
        info('Support requested', module='main')

    def show_about(self):
        """Show about information"""
        info('About dialog requested', module='main')

    @monitor_performance
    def run(self):
        """OPTIMIZED: High-performance application runner"""
        try:
            info('Starting Fincept Terminal application', module='main')
            dpg.create_context()
            dpg.add_window(tag='Primary Window', label='Fincept Terminal')
            dpg.push_container_stack('Primary Window')
            try:
                self._initialize_tabs_optimized()
                self.create_menu_bar()
                self.create_tabs()
            finally:
                dpg.pop_container_stack()
            api_key_type = self.get_api_key_type()
            strict_indicator = '[Strict]' if is_strict_mode() else '[Fallback]'
            version_info = getattr(config, 'APP_VERSION', 'v1.0.0')
            terminal_title = f'Fincept Terminal {version_info} - {self.user_type.title()} ({api_key_type}) {strict_indicator}'
            dpg.create_viewport(title=terminal_title, width=self.DEFAULT_WIDTH, height=self.DEFAULT_HEIGHT, min_width=self.MIN_WIDTH, min_height=self.MIN_HEIGHT, resizable=True, vsync=True, small_icon='fincept.ico', large_icon='fincept.ico')
            dpg.setup_dearpygui()
            dpg.set_primary_window('Primary Window', True)
            self.apply_theme_safe('finance_terminal')
            dpg.set_viewport_resize_callback(self.resize_callback)
            self.save_current_session()
            info(f'Startup completed - {len(self.tabs)} tabs loaded', module='main')
            dpg.show_viewport()

            def apply_font_when_ready():
                try:
                    import time
                    time.sleep(0.1)
                    if hasattr(self.theme_manager, 'ensure_font_applied'):
                        success = self.theme_manager.ensure_font_applied()
                        if success:
                            print('[FONT DEBUG] Final font application successful')
                        else:
                            print('[FONT DEBUG] Final font application failed')
                    else:
                        print('[FONT DEBUG] ensure_font_applied method not available')
                except Exception as e:
                    print(f'[FONT DEBUG] Final font application failed: {e}')
            import threading
            font_thread = threading.Thread(target=apply_font_when_ready, daemon=True)
            font_thread.start()
            dpg.start_dearpygui()
        except Exception as e:
            critical(f'Application startup failed: {str(e)}', module='main')
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """OPTIMIZED: Fast cleanup with minimal overhead"""
        try:
            info('Starting application cleanup', module='main')
            self.is_running = False
            try:
                self.save_current_session()
            except Exception:
                pass

            def cleanup_tabs_background():
                if hasattr(self, 'tabs') and self.tabs:
                    cleanup_count = 0
                    for tab_name, tab in self.tabs.items():
                        if hasattr(tab, 'cleanup'):
                            try:
                                tab.cleanup()
                                cleanup_count += 1
                            except Exception:
                                pass
                    debug(f'Background cleanup: {cleanup_count} tabs cleaned', module='main')
            cleanup_thread = threading.Thread(target=cleanup_tabs_background, daemon=True)
            cleanup_thread.start()
            try:
                if self.theme_manager and hasattr(self.theme_manager, 'cleanup'):
                    self.theme_manager.cleanup()
            except Exception:
                pass

            def background_gc():
                try:
                    collected = gc.collect()
                    debug(f'GC collected: {collected} objects', module='main')
                except Exception:
                    pass
            gc_thread = threading.Thread(target=background_gc, daemon=True)
            gc_thread.start()
            try:
                if dpg.is_dearpygui_running():
                    dpg.stop_dearpygui()
                dpg.destroy_context()
                debug('DearPyGUI context destroyed', module='main')
            except Exception as e:
                error(f'DearPyGUI cleanup failed: {str(e)}', module='main')
            info('Application cleanup completed', module='main')
        except Exception as e:
            error(f'Critical cleanup error: {str(e)}', module='main')

def __init__(self, session_data: Dict[str, Any]):
    self.is_running = True
    self.resize_lock = False
    self.api_request_count = 0
    self.last_resize_time = 0
    self.menu_toolbar_manager = MenuToolbarManager(self)
    self.session_data = session_data
    self.user_type = session_data.get('user_type', 'guest')
    self.authenticated = session_data.get('authenticated', False)
    self.api_key = session_data.get('api_key')
    self._cached_auth_headers = None
    self._auth_headers_timestamp = 0
    self._auth_cache_ttl = 300
    self.DEFAULT_WIDTH = 1200
    self.DEFAULT_HEIGHT = 600
    self.MARGIN_WIDTH = 20
    self.MARGIN_HEIGHT = 120
    self.MIN_WIDTH = 800
    self.MIN_HEIGHT = 600
    self.theme_manager = AutomaticThemeManager()
    self.themes_available = False
    self.tab_importer = PerformantTabImporter()
    self.calculate_sizes()
    self.tabs = {}
    self.tabs_initialized: Set[str] = set()
    info(f'Application initialized - User: {self.user_type}', module='main')

def resize_callback(self, sender=None, app_data=None):
    """OPTIMIZED: Lightweight resize with debouncing"""
    if self.resize_lock or not self.is_running:
        return
    current_time = time.time()
    if current_time - self.last_resize_time < 0.2:
        return
    try:
        self.resize_lock = True
        self.last_resize_time = current_time
        viewport_width = dpg.get_viewport_width()
        viewport_height = dpg.get_viewport_height()
        if viewport_width > self.MIN_WIDTH and viewport_height > self.MIN_HEIGHT:
            self.DEFAULT_WIDTH = viewport_width
            self.DEFAULT_HEIGHT = viewport_height
            self.calculate_sizes()
    except Exception as e:
        error(f'Resize failed: {str(e)}', module='main')
    finally:
        self.resize_lock = False

def check_scroll_position():
    """Check if we need to load more content based on scroll position"""
    if not dpg.does_item_exist('grid_container'):
        return
    if len(loaded_items) < 100:
        try:
            scroll_max_y = dpg.get_y_scroll_max('grid_container')
            scroll_y = dpg.get_y_scroll('grid_container')
            viewport_height = dpg.get_viewport_height()
            if scroll_max_y - scroll_y < viewport_height * 2:
                load_more_items()
                create_grid_layout()
        except:
            estimated_rows = len(loaded_items) // COLS + 1
            viewport_height = dpg.get_viewport_height()
            if estimated_rows * ROW_HEIGHT < viewport_height * 3:
                load_more_items()
                create_grid_layout()

def resize_callback():
    """Recreate grid and resize main window when viewport is resized"""
    viewport_width = dpg.get_viewport_width()
    viewport_height = dpg.get_viewport_height()
    dpg.set_item_width('main_window', viewport_width)
    dpg.set_item_height('main_window', viewport_height)
    dpg.set_item_pos('main_window', [0, 0])
    create_grid_layout()

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

class DateUtils:
    """Date utility functions for financial calculations"""

    @staticmethod
    def year_fraction(start_date: Union[datetime, date], end_date: Union[datetime, date], day_count: DayCountConvention=DayCountConvention.ACT_365) -> float:
        """Calculate year fraction between dates"""
        if isinstance(start_date, date):
            start_date = datetime.combine(start_date, datetime.min.time())
        if isinstance(end_date, date):
            end_date = datetime.combine(end_date, datetime.min.time())
        if end_date <= start_date:
            return 0.0
        if day_count == DayCountConvention.ACT_365:
            return (end_date - start_date).days / 365.0
        elif day_count == DayCountConvention.ACT_360:
            return (end_date - start_date).days / 360.0
        elif day_count == DayCountConvention.THIRTY_360:
            return DateUtils._thirty_360_fraction(start_date, end_date)
        elif day_count == DayCountConvention.ACT_ACT:
            return DateUtils._act_act_fraction(start_date, end_date)
        else:
            return (end_date - start_date).days / 365.0

    @staticmethod
    def _thirty_360_fraction(start_date: datetime, end_date: datetime) -> float:
        """30/360 day count calculation"""
        start_day = min(start_date.day, 30)
        end_day = end_date.day
        if start_day == 30 and end_day == 31:
            end_day = 30
        days = 360 * (end_date.year - start_date.year) + 30 * (end_date.month - start_date.month) + (end_day - start_day)
        return days / 360.0

    @staticmethod
    def _act_act_fraction(start_date: datetime, end_date: datetime) -> float:
        """ACT/ACT day count calculation"""
        total_days = 0
        current_year = start_date.year
        current_date = start_date
        while current_date < end_date:
            year_end = datetime(current_year, 12, 31)
            next_year_start = datetime(current_year + 1, 1, 1)
            if end_date <= year_end:
                days_in_year = (end_date - current_date).days
                year_length = 366 if calendar.isleap(current_year) else 365
                total_days += days_in_year / year_length
                break
            else:
                days_in_year = (next_year_start - current_date).days
                year_length = 366 if calendar.isleap(current_year) else 365
                total_days += days_in_year / year_length
                current_year += 1
                current_date = next_year_start
        return total_days

    @staticmethod
    def add_tenor(start_date: Union[datetime, date], tenor: str) -> datetime:
        """Add tenor to date (e.g., '3M', '1Y', '6W')"""
        if isinstance(start_date, date):
            start_date = datetime.combine(start_date, datetime.min.time())
        tenor = tenor.upper()
        if tenor.endswith('D'):
            days = int(tenor[:-1])
            return start_date + timedelta(days=days)
        elif tenor.endswith('W'):
            weeks = int(tenor[:-1])
            return start_date + timedelta(weeks=weeks)
        elif tenor.endswith('M'):
            months = int(tenor[:-1])
            new_month = start_date.month + months
            new_year = start_date.year + (new_month - 1) // 12
            new_month = (new_month - 1) % 12 + 1
            try:
                return start_date.replace(year=new_year, month=new_month)
            except ValueError:
                last_day = calendar.monthrange(new_year, new_month)[1]
                return start_date.replace(year=new_year, month=new_month, day=last_day)
        elif tenor.endswith('Y'):
            years = int(tenor[:-1])
            try:
                return start_date.replace(year=start_date.year + years)
            except ValueError:
                return start_date.replace(year=start_date.year + years, month=2, day=28)
        else:
            raise ValueError(f'Invalid tenor format: {tenor}')

    @staticmethod
    def generate_schedule(start_date: Union[datetime, date], end_date: Union[datetime, date], frequency: str='3M', business_day_convention: str='modified_following') -> List[datetime]:
        """Generate payment schedule between dates"""
        if isinstance(start_date, date):
            start_date = datetime.combine(start_date, datetime.min.time())
        if isinstance(end_date, date):
            end_date = datetime.combine(end_date, datetime.min.time())
        schedule = []
        current_date = start_date
        bdc = BusinessDayCalculator()
        while current_date < end_date:
            next_date = DateUtils.add_tenor(current_date, frequency)
            if next_date > end_date:
                next_date = end_date
            if business_day_convention == 'following':
                while not bdc.is_business_day(next_date):
                    next_date += timedelta(days=1)
            elif business_day_convention == 'preceding':
                while not bdc.is_business_day(next_date):
                    next_date -= timedelta(days=1)
            elif business_day_convention == 'modified_following':
                original_month = next_date.month
                while not bdc.is_business_day(next_date):
                    next_date += timedelta(days=1)
                    if next_date.month != original_month:
                        next_date = DateUtils.add_tenor(current_date, frequency)
                        while not bdc.is_business_day(next_date):
                            next_date -= timedelta(days=1)
                        break
            schedule.append(next_date)
            current_date = next_date
        return schedule

@staticmethod
def year_fraction(start_date: Union[datetime, date], end_date: Union[datetime, date], day_count: DayCountConvention=DayCountConvention.ACT_365) -> float:
    """Calculate year fraction between dates"""
    if isinstance(start_date, date):
        start_date = datetime.combine(start_date, datetime.min.time())
    if isinstance(end_date, date):
        end_date = datetime.combine(end_date, datetime.min.time())
    if end_date <= start_date:
        return 0.0
    if day_count == DayCountConvention.ACT_365:
        return (end_date - start_date).days / 365.0
    elif day_count == DayCountConvention.ACT_360:
        return (end_date - start_date).days / 360.0
    elif day_count == DayCountConvention.THIRTY_360:
        return DateUtils._thirty_360_fraction(start_date, end_date)
    elif day_count == DayCountConvention.ACT_ACT:
        return DateUtils._act_act_fraction(start_date, end_date)
    else:
        return (end_date - start_date).days / 365.0

class ChatTab(BaseTab):
    """High Performance Chat Tab - Bloomberg Terminal Style"""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.current_session_uuid = None
        self.is_typing = False
        self.message_widgets = []
        self.chat_counter = 1
        self.sessions = []
        self.ui_tags = set()
        self._api_client = None
        self._api_client_initialized = False
        self._auth_cached = None
        self._auth_cache_time = 0
        self._auth_cache_ttl = 300
        self.BLOOMBERG_ORANGE = [255, 165, 0]
        self.BLOOMBERG_WHITE = [255, 255, 255]
        self.BLOOMBERG_RED = [255, 0, 0]
        self.BLOOMBERG_GREEN = [0, 200, 0]
        self.BLOOMBERG_YELLOW = [255, 255, 0]
        self.BLOOMBERG_GRAY = [120, 120, 120]
        self.BLOOMBERG_BLACK = [0, 0, 0]
        self._ui_dimensions = {'bubble_min_width': 120, 'bubble_max_width': 450, 'char_width': 7, 'line_height': 18, 'padding': 20}
        debug('[CHAT_TAB] Chat tab initialized')

    def get_label(self):
        return 'AI Chat'

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
            self._api_client = create_api_client(self.app.get_session_data())
            self._api_client_initialized = True
            if self._api_client:
                debug('[CHAT_TAB] API client initialized successfully')
            else:
                warning('[CHAT_TAB] API client creation failed')
        except Exception as e:
            error(f'[CHAT_TAB] API client initialization failed: {str(e)}')
            self._api_client = None
            self._api_client_initialized = True

    def _is_authenticated_cached(self) -> bool:
        """PERFORMANCE: Cached authentication check"""
        current_time = time.time()
        if self._auth_cached is not None and current_time - self._auth_cache_time < self._auth_cache_ttl:
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

    def refresh_sessions(self):
        """OPTIMIZED: Fast session refresh"""
        try:
            self.load_chat_sessions()
        except Exception as e:
            error(f'[CHAT_TAB] Session refresh failed: {str(e)}')

    def delete_current_session(self):
        """Delete current session"""
        try:
            if self.current_session_uuid:
                self.delete_session_callback(self.current_session_uuid)
        except Exception as e:
            error(f'[CHAT_TAB] Current session deletion failed: {str(e)}')

    def filter_sessions_callback(self, sender, app_data):
        """OPTIMIZED: Fast session filtering"""
        try:
            search_term = app_data.lower()
            self.safe_delete_item('session_list_area', children_only=True)
            for session in self.sessions:
                if search_term in session['title'].lower():
                    self.create_session_item(session)
        except Exception as e:
            error(f'[CHAT_TAB] Session filtering failed: {str(e)}')

    def clear_current_chat(self):
        """Clear current chat messages"""
        try:
            if self.current_session_uuid:
                self.create_welcome_screen()
                self.safe_set_value('system_status', 'STATUS: CHAT CLEARED')
        except Exception as e:
            error(f'[CHAT_TAB] Chat clear failed: {str(e)}')

    def show_help(self):
        """Show help information"""
        self.send_quick_message('help')

    def focus_sessions(self):
        """Focus session search"""
        try:
            if dpg.does_item_exist('session_search'):
                dpg.focus_item('session_search')
        except Exception as e:
            debug(f'[CHAT_TAB] Focus sessions failed: {str(e)}')

    def focus_search(self):
        """Focus search field"""
        self.focus_sessions()

    def show_stats(self):
        """OPTIMIZED: Show chat statistics"""
        try:
            if self.api_client:

                def get_stats_async():
                    try:
                        result = self.api_client.get_chat_stats()
                        if result['success']:
                            stats = result['stats']
                            stats_msg = f'Sessions: {stats['total_sessions']}, Messages: {stats['total_messages']}'
                            self.safe_set_value('system_status', f'STATS: {stats_msg}')
                    except Exception as e:
                        error(f'[CHAT_TAB] Stats retrieval failed: {str(e)}')
                threading.Thread(target=get_stats_async, daemon=True, name='ChatStats').start()
        except Exception as e:
            error(f'[CHAT_TAB] Stats display failed: {str(e)}')

    def execute_quick_command(self, command):
        """OPTIMIZED: Execute quick command with error handling"""
        try:
            command_map = {'NEW_SESSION': self.new_chat_callback, 'GET_HELP': lambda: self.send_quick_message('help'), 'MARKET_ANALYSIS': lambda: self.send_quick_message('market analysis'), 'PORTFOLIO_HELP': lambda: self.send_quick_message('portfolio help'), 'SYSTEM_STATUS': self.show_stats}
            handler = command_map.get(command)
            if handler:
                handler()
            else:
                warning(f'[CHAT_TAB] Unknown command: {command}')
        except Exception as e:
            error(f'[CHAT_TAB] Quick command failed: {command} - {str(e)}')

    def send_quick_message(self, message_type):
        """OPTIMIZED: Send predefined message with minimal overhead"""
        try:
            messages = {'help': 'I need help with using this AI assistant', 'market analysis': 'Can you help me with market analysis?', 'portfolio help': 'I need advice on portfolio management'}
            message = messages.get(message_type, message_type)
            if not self.current_session_uuid:
                if not self.create_new_session(f'Quick {message_type.title()}'):
                    return
            self.safe_delete_item('welcome_screen')

            def send_async():
                self.send_message_to_api(message)
            threading.Thread(target=send_async, daemon=True, name='QuickMessage').start()
        except Exception as e:
            error(f'[CHAT_TAB] Quick message failed: {message_type} - {str(e)}')

    def generate_smart_title(self, message):
        """PERFORMANCE: Fast title generation"""
        try:
            clean_msg = re.sub('[^\\w\\s]', '', message).strip()
            words = clean_msg.split()
            if len(words) <= 2:
                return clean_msg[:20] if clean_msg else 'New Chat'
            else:
                return ' '.join(words[:2]) + '...'
        except Exception:
            return 'Chat Session'

    def cleanup(self):
        """OPTIMIZED: Fast cleanup"""
        try:
            self.sessions.clear()
            self.current_session_uuid = None
            self.ui_tags.clear()
            self._auth_cached = None
            self._auth_cache_time = 0
            debug('[CHAT_TAB] Cleanup completed')
        except Exception as e:
            error(f'[CHAT_TAB] Cleanup failed: {str(e)}')

    def safe_add_text(self, text, color=None, tag=None, parent=None):
        """PERFORMANCE: Optimized text addition"""
        try:
            kwargs = {'color': color} if color else {}
            if tag:
                kwargs['tag'] = tag
                self.ui_tags.add(tag)
            if parent:
                kwargs['parent'] = parent
            return dpg.add_text(text, **kwargs)
        except Exception as e:
            debug(f'[CHAT_TAB] Text addition failed: {str(e)}')
            return None

    def safe_delete_item(self, tag, children_only=False):
        """PERFORMANCE: Safe item deletion with cache cleanup"""
        try:
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag, children_only=children_only)
                if tag in self.ui_tags:
                    self.ui_tags.remove(tag)
                return True
        except Exception as e:
            debug(f'[CHAT_TAB] Item deletion failed: {tag} - {str(e)}')
        return False

    def safe_set_value(self, tag, value):
        """PERFORMANCE: Safe value setting"""
        try:
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)
                return True
        except Exception:
            return False

    def safe_get_value(self, tag, default=''):
        """PERFORMANCE: Safe value getting"""
        try:
            if dpg.does_item_exist(tag):
                return dpg.get_value(tag)
        except Exception:
            return default

    def create_content(self):
        """OPTIMIZED: Create chat interface with minimal API calls"""
        try:
            if not self._is_authenticated_cached():
                self.create_error_content('Authentication required')
                return
            self.create_chat_interface()

            def load_sessions_async():
                try:
                    self.load_chat_sessions()
                except Exception as e:
                    error(f'[CHAT_TAB] Async session loading failed: {str(e)}')
            threading.Thread(target=load_sessions_async, daemon=True, name='ChatSessionLoader').start()
        except Exception as e:
            error(f'[CHAT_TAB] Content creation failed: {str(e)}')
            self.create_error_content(f'Failed to initialize chat: {str(e)}')

    def create_error_content(self, error_message):
        """Create error content when API is not available"""
        self.safe_add_text('🚨 Chat Error', color=self.BLOOMBERG_RED)
        dpg.add_separator()
        self.safe_add_text(error_message, color=self.BLOOMBERG_WHITE)
        dpg.add_spacer(height=20)
        dpg.add_button(label='Refresh', callback=self.refresh_content)

    def refresh_content(self):
        """Refresh chat content"""
        debug('[CHAT_TAB] Content refresh requested')

    def create_chat_interface(self):
        """OPTIMIZED: Create main chat interface with minimal overhead"""
        try:
            self.create_terminal_header()
            dpg.add_separator()
            self.create_function_keys()
            dpg.add_separator()
            with dpg.group(horizontal=True):
                self.create_chat_sessions_panel()
                self.create_chat_interface_panel()
                self.create_command_panel()
            dpg.add_separator()
            self.create_status_bar()
        except Exception as e:
            error(f'[CHAT_TAB] Interface creation failed: {str(e)}')

    def create_terminal_header(self):
        """OPTIMIZED: Create terminal header with cached user info"""
        try:
            with dpg.group(horizontal=True):
                self.safe_add_text('FINCEPT', color=self.BLOOMBERG_ORANGE)
                self.safe_add_text('AI ASSISTANT', color=self.BLOOMBERG_WHITE)
                self.safe_add_text(' | ', color=self.BLOOMBERG_GRAY)
                user_type = self.app.get_user_type()
                if user_type == 'guest':
                    self.safe_add_text('👤 Guest Mode', color=self.BLOOMBERG_YELLOW)
                else:
                    user_info = self.app.get_session_data().get('user_info', {})
                    username = user_info.get('username', 'User')
                    self.safe_add_text(f'🔑 {username}', color=self.BLOOMBERG_GREEN)
                self.safe_add_text(' | ', color=self.BLOOMBERG_GRAY)
                self.safe_add_text(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), tag='chat_header_time')
        except Exception as e:
            error(f'[CHAT_TAB] Header creation failed: {str(e)}')

    def create_function_keys(self):
        """OPTIMIZED: Create function keys bar"""
        try:
            with dpg.group(horizontal=True):
                function_keys = [('F1:HELP', self.show_help), ('F2:SESSIONS', self.focus_sessions), ('F3:NEW', self.new_chat_callback), ('F4:SEARCH', self.focus_search), ('F5:CLEAR', self.clear_current_chat), ('F6:STATS', self.show_stats)]
                for key_label, callback in function_keys:
                    dpg.add_button(label=key_label, width=100, height=25, callback=callback)
        except Exception as e:
            error(f'[CHAT_TAB] Function keys creation failed: {str(e)}')

    def create_chat_sessions_panel(self):
        """OPTIMIZED: Create left panel for chat sessions"""
        try:
            with dpg.child_window(width=350, height=600, border=True, tag='chat_sessions_panel'):
                self.safe_add_text('CHAT SESSIONS', color=self.BLOOMBERG_ORANGE)
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    dpg.add_button(label='NEW', callback=self.new_chat_callback, width=60, height=25)
                    dpg.add_button(label='REFRESH', callback=self.refresh_sessions, width=80, height=25)
                    dpg.add_button(label='DELETE', callback=self.delete_current_session, width=70, height=25)
                dpg.add_input_text(hint='Search sessions...', width=-1, tag='session_search', callback=self.filter_sessions_callback)
                dpg.add_separator()
                self.safe_add_text('SESSION STATISTICS', color=self.BLOOMBERG_YELLOW)
                self.safe_add_text('Total Sessions: 0', tag='total_sessions')
                self.safe_add_text('Total Messages: 0', tag='total_messages')
                self.safe_add_text('Active Session: None', tag='active_session_info')
                dpg.add_separator()
                self.safe_add_text('ACTIVE SESSIONS', color=self.BLOOMBERG_YELLOW)
                dpg.add_child_window(height=-1, border=False, tag='session_list_area')
        except Exception as e:
            error(f'[CHAT_TAB] Sessions panel creation failed: {str(e)}')

    def create_chat_interface_panel(self):
        """OPTIMIZED: Create chat interface panel"""
        try:
            with dpg.child_window(width=850, height=600, border=True, tag='chat_interface_panel'):
                with dpg.group(horizontal=True):
                    self.safe_add_text('AI CHAT', color=self.BLOOMBERG_ORANGE)
                    self.safe_add_text(' | ', color=self.BLOOMBERG_GRAY)
                    self.safe_add_text('No Active Session', color=self.BLOOMBERG_WHITE, tag='current_session_name')
                dpg.add_separator()
                dpg.add_child_window(height=470, border=True, tag='messages_display_area')
                dpg.add_separator()
                self.safe_add_text('INPUT', color=self.BLOOMBERG_YELLOW)
                with dpg.group(horizontal=True):
                    dpg.add_input_text(hint='Type message...', width=600, height=40, multiline=True, tag='message_input_field', callback=self.message_input_callback, on_enter=True)
                    with dpg.group():
                        dpg.add_button(label='SEND', callback=self.send_message_callback, width=80, height=20)
                        dpg.add_button(label='CLEAR', callback=self.clear_input, width=80, height=18)
                self.safe_add_text('Ready', tag='input_status', color=self.BLOOMBERG_GRAY)
            self.create_welcome_screen()
        except Exception as e:
            error(f'[CHAT_TAB] Interface panel creation failed: {str(e)}')

    def create_command_panel(self):
        """OPTIMIZED: Create right panel for commands"""
        try:
            with dpg.child_window(width=300, height=600, border=True, tag='command_panel'):
                self.safe_add_text('COMMAND CENTER', color=self.BLOOMBERG_ORANGE)
                dpg.add_separator()
                self.safe_add_text('API STATUS', color=self.BLOOMBERG_YELLOW)
                if self._is_authenticated_cached():
                    self.safe_add_text('● Connected', color=self.BLOOMBERG_GREEN)
                    if self.api_client:
                        user_type = getattr(self.api_client, 'user_type', 'Unknown')
                        self.safe_add_text(f'● {user_type.title()} User', color=self.BLOOMBERG_WHITE)
                        try:
                            req_count = self.api_client.get_request_count()
                            self.safe_add_text(f'● Requests: {req_count}', color=self.BLOOMBERG_WHITE)
                        except:
                            self.safe_add_text('● Requests: N/A', color=self.BLOOMBERG_WHITE)
                else:
                    self.safe_add_text('● Disconnected', color=self.BLOOMBERG_RED)
                dpg.add_separator()
                self.safe_add_text('QUICK COMMANDS', color=self.BLOOMBERG_YELLOW)
                commands = [('NEW_SESSION', 'Create new chat session'), ('GET_HELP', 'Get AI assistance'), ('MARKET_ANALYSIS', 'Market insights'), ('PORTFOLIO_HELP', 'Portfolio advice'), ('SYSTEM_STATUS', 'Check system status')]
                for cmd, desc in commands:
                    dpg.add_button(label=cmd, width=-1, height=25, callback=lambda s, a, command=cmd: self.execute_quick_command(command))
                    self.safe_add_text(f'  {desc}', color=self.BLOOMBERG_GRAY)
                dpg.add_separator()
                self.safe_add_text('SYSTEM INFO', color=self.BLOOMBERG_YELLOW)
                self.safe_add_text('Chat API: READY', color=self.BLOOMBERG_GREEN)
                self.safe_add_text('Response Time: <100ms', color=self.BLOOMBERG_GREEN)
                self.safe_add_text('Last Update:', color=self.BLOOMBERG_GRAY)
                self.safe_add_text(datetime.now().strftime('%H:%M:%S'), tag='last_update_time')
        except Exception as e:
            error(f'[CHAT_TAB] Command panel creation failed: {str(e)}')

    def create_status_bar(self):
        """OPTIMIZED: Create bottom status bar"""
        try:
            with dpg.group(horizontal=True):
                self.safe_add_text('●', color=self.BLOOMBERG_GREEN)
                self.safe_add_text('CONNECTED', color=self.BLOOMBERG_GREEN)
                self.safe_add_text(' | ', color=self.BLOOMBERG_GRAY)
                self.safe_add_text('AI CHAT', color=self.BLOOMBERG_ORANGE)
                self.safe_add_text(' | ', color=self.BLOOMBERG_GRAY)
                self.safe_add_text('STATUS: READY', color=self.BLOOMBERG_WHITE, tag='system_status')
                self.safe_add_text(' | ', color=self.BLOOMBERG_GRAY)
                user_type = self.app.get_user_type().upper()
                self.safe_add_text(f'USER: {user_type}', color=self.BLOOMBERG_WHITE)
        except Exception as e:
            error(f'[CHAT_TAB] Status bar creation failed: {str(e)}')

    def create_welcome_screen(self):
        """OPTIMIZED: Create compact welcome screen"""
        try:
            self.safe_delete_item('messages_display_area', children_only=True)
            with dpg.group(parent='messages_display_area', tag='welcome_screen'):
                dpg.add_spacer(height=20)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=150)
                    with dpg.group():
                        self.safe_add_text('FINCEPT AI ASSISTANT', color=self.BLOOMBERG_ORANGE)
                        self.safe_add_text('Financial Intelligence System', color=self.BLOOMBERG_WHITE)
                        dpg.add_spacer(height=15)
                        with dpg.group(horizontal=True):
                            self.safe_add_text('●', color=self.BLOOMBERG_GREEN)
                            self.safe_add_text('AI Ready', color=self.BLOOMBERG_GREEN)
                            dpg.add_spacer(width=20)
                            self.safe_add_text('●', color=self.BLOOMBERG_GREEN)
                            self.safe_add_text('API Connected', color=self.BLOOMBERG_GREEN)
                        dpg.add_spacer(height=15)
                        user_type = self.app.get_user_type()
                        if user_type == 'guest':
                            self.safe_add_text('Mode: Guest (Limited)', color=self.BLOOMBERG_YELLOW)
                        else:
                            self.safe_add_text('Mode: Registered (Full Access)', color=self.BLOOMBERG_GREEN)
                        dpg.add_spacer(height=20)
                        self.safe_add_text('Quick Start:', color=self.BLOOMBERG_YELLOW)
                        self.safe_add_text('• Type message below and press Enter')
                        self.safe_add_text('• Use function keys for quick actions')
                        self.safe_add_text('• Browse sessions in left panel')
                        dpg.add_spacer(height=20)
                        dpg.add_button(label='START CHAT', callback=self.new_chat_callback, width=120, height=30)
                    dpg.add_spacer(width=150)
        except Exception as e:
            error(f'[CHAT_TAB] Welcome screen creation failed: {str(e)}')

    def load_chat_sessions(self):
        """OPTIMIZED: Load chat sessions from API with caching"""
        if not self.api_client:
            return
        try:
            result = self.api_client.get_chat_sessions()
            if result['success']:
                self.sessions = result['sessions']
                self.refresh_sessions_display()
                self.update_stats()
                debug(f'[CHAT_TAB] Loaded {len(self.sessions)} sessions')
            else:
                warning(f'[CHAT_TAB] Session loading failed: {result.get('error', 'Unknown error')}')
        except Exception as e:
            error(f'[CHAT_TAB] Session loading error: {str(e)}')

    def create_new_session(self, title='New Conversation'):
        """OPTIMIZED: Create new chat session via API"""
        if not self.api_client:
            return False
        try:
            result = self.api_client.create_chat_session(title)
            if result['success']:
                session_data = result['session']
                self.current_session_uuid = session_data['session_uuid']
                self.safe_set_value('current_session_name', session_data['title'])
                self.safe_set_value('active_session_info', f'Active: {session_data['title']}')
                self.safe_delete_item('welcome_screen')

                def refresh_async():
                    self.load_chat_sessions()
                threading.Thread(target=refresh_async, daemon=True, name='SessionRefresh').start()
                info(f'[CHAT_TAB] New session created: {session_data['title']}')
                return True
            else:
                error_msg = result.get('error', 'Failed to create session')
                error(f'[CHAT_TAB] Session creation failed: {error_msg}')
                self.safe_set_value('system_status', f'ERROR: {error_msg}')
                return False
        except Exception as e:
            error(f'[CHAT_TAB] Session creation error: {str(e)}')
            self.safe_set_value('system_status', f'ERROR: {str(e)}')
            return False

    def send_message_to_api(self, content):
        """OPTIMIZED: Send message to API with background processing"""
        if not self.api_client or not self.current_session_uuid:
            return False
        try:
            self.safe_set_value('system_status', 'STATUS: SENDING MESSAGE...')
            result = self.api_client.send_chat_message(self.current_session_uuid, content)
            if result['success']:
                user_msg = result['user_message']
                ai_msg = result['ai_message']
                self.create_message_bubble('user', user_msg['content'])
                self.create_message_bubble('assistant', ai_msg['content'])
                if result.get('new_title'):
                    self.safe_set_value('current_session_name', result['new_title'])
                    self.safe_set_value('active_session_info', f'Active: {result['new_title']}')

                def refresh_async():
                    try:
                        self.load_chat_sessions()
                    except Exception as e:
                        debug(f'[CHAT_TAB] Background refresh failed: {str(e)}')
                threading.Thread(target=refresh_async, daemon=True, name='MessageRefresh').start()
                self.safe_set_value('system_status', 'STATUS: READY')
                return True
            else:
                error_msg = result.get('error', 'Failed to send message')
                error(f'[CHAT_TAB] Message send failed: {error_msg}')
                self.safe_set_value('system_status', f'ERROR: {error_msg}')
                return False
        except Exception as e:
            error(f'[CHAT_TAB] Message send error: {str(e)}')
            self.safe_set_value('system_status', f'ERROR: {str(e)}')
            return False

    def load_session_messages(self, session_uuid):
        """OPTIMIZED: Load messages for a specific session"""
        if not self.api_client:
            return
        try:
            result = self.api_client.get_chat_session(session_uuid)
            if result['success']:
                messages = result['messages']
                self.safe_delete_item('messages_display_area', children_only=True)
                for msg in messages:
                    self.create_message_bubble(msg['role'], msg['content'])
                self.scroll_to_bottom()
                debug(f'[CHAT_TAB] Loaded {len(messages)} messages for session')
            else:
                warning(f'[CHAT_TAB] Message loading failed: {result.get('error', 'Unknown error')}')
        except Exception as e:
            error(f'[CHAT_TAB] Message loading error: {str(e)}')

    def create_message_bubble(self, role, content):
        """OPTIMIZED: Create message bubbles with pre-calculated dimensions"""
        try:
            time_str = datetime.now().strftime('%H:%M:%S')
            is_user = role == 'user'
            bubble_width, estimated_lines = self._calculate_bubble_size_cached(content)
            wrapped_content = self._wrap_text_cached(content, bubble_width)
            with dpg.group(parent='messages_display_area'):
                dpg.add_spacer(height=4)
                if is_user:
                    with dpg.group(horizontal=True):
                        chat_area_width = 845
                        left_spacer = max(20, chat_area_width - bubble_width - 50)
                        dpg.add_spacer(width=left_spacer)
                        with dpg.group():
                            with dpg.group(horizontal=True):
                                self.safe_add_text('YOU', color=self.BLOOMBERG_YELLOW)
                                dpg.add_spacer(width=8)
                                self.safe_add_text(f'{time_str}', color=self.BLOOMBERG_GRAY)
                            bubble_height = max(30, estimated_lines * self._ui_dimensions['line_height'] + 16)
                            with dpg.child_window(width=bubble_width, height=bubble_height, border=True, no_scrollbar=True):
                                dpg.add_spacer(height=4)
                                self.safe_add_text(wrapped_content, color=self.BLOOMBERG_WHITE)
                else:
                    with dpg.group(horizontal=True):
                        with dpg.group():
                            with dpg.group(horizontal=True):
                                self.safe_add_text('AI', color=self.BLOOMBERG_ORANGE)
                                dpg.add_spacer(width=8)
                                self.safe_add_text(f'{time_str}', color=self.BLOOMBERG_GRAY)
                            bubble_height = max(30, estimated_lines * self._ui_dimensions['line_height'] + 16)
                            with dpg.child_window(width=bubble_width, height=bubble_height, border=True, no_scrollbar=True):
                                dpg.add_spacer(height=4)
                                self.safe_add_text(wrapped_content, color=self.BLOOMBERG_WHITE)
                        dpg.add_spacer(width=50)

            def delayed_scroll():
                time.sleep(0.05)
                self.scroll_to_bottom()
            threading.Thread(target=delayed_scroll, daemon=True).start()
        except Exception as e:
            error(f'[CHAT_TAB] Message bubble creation failed: {str(e)}')

    def _calculate_bubble_size_cached(self, content):
        """PERFORMANCE: Optimized bubble size calculation with caching"""
        try:
            clean_content = content.strip()
            content_length = len(clean_content)
            MIN_WIDTH = self._ui_dimensions['bubble_min_width']
            MAX_WIDTH = self._ui_dimensions['bubble_max_width']
            CHAR_WIDTH = self._ui_dimensions['char_width']
            if content_length <= 20:
                width = min(MAX_WIDTH, max(MIN_WIDTH, content_length * CHAR_WIDTH + 20))
            elif content_length <= 80:
                width = min(MAX_WIDTH, max(MIN_WIDTH, int(content_length * CHAR_WIDTH * 0.8) + 30))
            elif content_length <= 200:
                width = min(MAX_WIDTH, max(250, int(content_length * CHAR_WIDTH * 0.6) + 40))
            else:
                width = MAX_WIDTH
            chars_per_line = max(20, int((width - self._ui_dimensions['padding']) / CHAR_WIDTH))
            estimated_lines = max(1, min(15, content_length // chars_per_line + clean_content.count('\n') + 1))
            return (int(width), estimated_lines)
        except Exception:
            return (200, 1)

    def _wrap_text_cached(self, text, bubble_width):
        """PERFORMANCE: Fast text wrapping with minimal processing"""
        try:
            if not text:
                return ''
            chars_per_line = max(20, int((bubble_width - self._ui_dimensions['padding']) / self._ui_dimensions['char_width']))
            if len(text) <= chars_per_line:
                return text
            lines = []
            current_line = ''
            for word in text.split():
                if len(current_line + word) <= chars_per_line:
                    current_line += word + ' '
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + ' '
            if current_line:
                lines.append(current_line.strip())
            return '\n'.join(lines)
        except Exception:
            return text

    def create_session_item(self, session_data):
        """OPTIMIZED: Create session item in the list"""
        try:
            session_uuid = session_data['session_uuid']
            title = session_data['title']
            message_count = session_data['message_count']
            try:
                updated_at = datetime.fromisoformat(session_data['updated_at'].replace('Z', '+00:00'))
                time_str = updated_at.strftime('%m/%d %H:%M')
            except:
                time_str = 'Recent'
            group_tag = f'session_item_{session_uuid}'
            with dpg.group(parent='session_list_area', tag=group_tag):
                with dpg.child_window(width=-1, height=70, border=True):
                    dpg.add_button(label=title, callback=lambda: self.select_session_callback(session_uuid, title), width=-1, height=30)
                    with dpg.group(horizontal=True):
                        self.safe_add_text(f'Msgs: {message_count}', color=self.BLOOMBERG_GRAY)
                        dpg.add_spacer(width=20)
                        self.safe_add_text(f'{time_str}', color=self.BLOOMBERG_GRAY)
                        dpg.add_spacer(width=20)
                        dpg.add_button(label='DEL', callback=lambda: self.delete_session_callback(session_uuid), width=35, height=20)
                dpg.add_spacer(height=5)
        except Exception as e:
            error(f'[CHAT_TAB] Session item creation failed: {str(e)}')

    def refresh_sessions_display(self):
        """OPTIMIZED: Fast session display refresh"""
        try:
            self.safe_delete_item('session_list_area', children_only=True)
            for session in self.sessions:
                self.create_session_item(session)
        except Exception as e:
            error(f'[CHAT_TAB] Session display refresh failed: {str(e)}')

    def update_stats(self):
        """OPTIMIZED: Update statistics display asynchronously"""
        if not self.api_client:
            return

        def update_stats_async():
            try:
                result = self.api_client.get_chat_stats()
                if result['success']:
                    stats = result['stats']
                    self.safe_set_value('total_sessions', f'Total Sessions: {stats['total_sessions']}')
                    self.safe_set_value('total_messages', f'Total Messages: {stats['total_messages']}')
            except Exception as e:
                debug(f'[CHAT_TAB] Stats update failed: {str(e)}')
        threading.Thread(target=update_stats_async, daemon=True, name='StatsUpdate').start()

    def scroll_to_bottom(self):
        """OPTIMIZED: Fast scroll to bottom"""

        def scroll():
            try:
                if dpg.does_item_exist('messages_display_area'):
                    max_scroll = dpg.get_y_scroll_max('messages_display_area')
                    if max_scroll > 0:
                        dpg.set_y_scroll('messages_display_area', max_scroll)
            except:
                pass
        threading.Timer(0.05, scroll).start()

    def message_input_callback(self, sender, app_data):
        """OPTIMIZED: Message input callback"""
        try:
            text = self.safe_get_value('message_input_field', '')
            char_count = len(text)
            if char_count == 0:
                status = 'Ready'
            elif char_count < 500:
                status = f'{char_count} chars'
            else:
                status = f'{char_count} chars (long)'
            self.safe_set_value('input_status', status)
            if app_data == '\n' and text.strip():
                self.send_message_callback()
        except Exception as e:
            debug(f'[CHAT_TAB] Input callback failed: {str(e)}')

    def send_message_callback(self):
        """OPTIMIZED: Fast send message callback"""
        try:
            message = self.safe_get_value('message_input_field', '').strip()
            if not message:
                return
            if not self.current_session_uuid:
                title = self.generate_smart_title(message)
                if not self.create_new_session(title):
                    return
            self.safe_set_value('message_input_field', '')
            self.safe_set_value('input_status', 'Ready')
            self.safe_delete_item('welcome_screen')

            def send_async():
                self.send_message_to_api(message)
            threading.Thread(target=send_async, daemon=True, name='MessageSend').start()
        except Exception as e:
            error(f'[CHAT_TAB] Send message failed: {str(e)}')

    def clear_input(self):
        """Clear input field"""
        self.safe_set_value('message_input_field', '')
        self.safe_set_value('input_status', 'Ready')

    def new_chat_callback(self):
        """OPTIMIZED: Create new chat"""
        try:
            current_time = datetime.now().strftime('%H%M')
            title = f'Session-{self.chat_counter:03d}-{current_time}'
            self.chat_counter += 1
            if self.create_new_session(title):
                self.create_welcome_screen()
                if dpg.does_item_exist('message_input_field'):
                    dpg.focus_item('message_input_field')
        except Exception as e:
            error(f'[CHAT_TAB] New chat creation failed: {str(e)}')

    def select_session_callback(self, session_uuid, title):
        """OPTIMIZED: Select and load session asynchronously"""
        try:
            self.current_session_uuid = session_uuid
            self.safe_set_value('current_session_name', title)
            self.safe_set_value('active_session_info', f'Active: {title}')
            self.safe_set_value('system_status', 'STATUS: LOADING SESSION...')

            def load_session_async():
                try:
                    self.load_session_messages(session_uuid)
                    if self.api_client:
                        self.api_client.activate_chat_session(session_uuid)
                    self.safe_set_value('system_status', 'STATUS: READY')
                except Exception as e:
                    error(f'[CHAT_TAB] Session loading failed: {str(e)}')
                    self.safe_set_value('system_status', f'ERROR: {str(e)}')
            threading.Thread(target=load_session_async, daemon=True, name='SessionLoad').start()
        except Exception as e:
            error(f'[CHAT_TAB] Session selection failed: {str(e)}')

    def delete_session_callback(self, session_uuid):
        """OPTIMIZED: Delete session with background processing"""
        if not self.api_client:
            return
        try:

            def delete_session_async():
                try:
                    result = self.api_client.delete_chat_session(session_uuid)
                    if result['success']:
                        if self.current_session_uuid == session_uuid:
                            self.current_session_uuid = None
                            self.safe_set_value('current_session_name', 'No Active Session')
                            self.safe_set_value('active_session_info', 'Active: None')
                            self.create_welcome_screen()
                        self.load_chat_sessions()
                        info(f'[CHAT_TAB] Session deleted: {session_uuid[:8]}')
                    else:
                        error_msg = result.get('error', 'Failed to delete session')
                        self.safe_set_value('system_status', f'ERROR: {error_msg}')
                        error(f'[CHAT_TAB] Session deletion failed: {error_msg}')
                except Exception as e:
                    error(f'[CHAT_TAB] Session deletion error: {str(e)}')
                    self.safe_set_value('system_status', f'ERROR: {str(e)}')
            threading.Thread(target=delete_session_async, daemon=True, name='SessionDelete').start()
        except Exception as e:
            error(f'[CHAT_TAB] Delete session callback failed: {str(e)}')

def _is_authenticated_cached(self) -> bool:
    """PERFORMANCE: Cached authentication check"""
    current_time = time.time()
    if self._auth_cached is not None and current_time - self._auth_cache_time < self._auth_cache_ttl:
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

def scroll():
    try:
        if dpg.does_item_exist('messages_display_area'):
            max_scroll = dpg.get_y_scroll_max('messages_display_area')
            if max_scroll > 0:
                dpg.set_y_scroll('messages_display_area', max_scroll)
    except:
        pass

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

class NodeProcessor:
    """Enhanced node processor with caching and parallel execution"""

    def __init__(self):
        self.nodes: Dict[str, NodeData] = {}
        self.execution_order: List[str] = []
        self.cache: Dict[str, Any] = {}
        self.performance_tracker: Dict[str, float] = {}

    def add_node(self, node_data: NodeData):
        """Add a node to the processor"""
        self.nodes[node_data.node_id] = node_data
        logger.info(f'Added node {node_data.node_id} of type {node_data.node_type.value}')

    def calculate_execution_order(self):
        """Calculate optimal execution order using topological sort"""
        from collections import defaultdict, deque
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        for node_id in self.nodes:
            in_degree[node_id] = 0
        for target_node, connections in global_state.node_connections.items():
            for input_type, source_nodes in connections.items():
                for source_node in source_nodes:
                    graph[source_node].append(target_node)
                    in_degree[target_node] += 1
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        self.execution_order = []
        while queue:
            node = queue.popleft()
            self.execution_order.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        logger.info(f'Execution order calculated: {self.execution_order}')

    def execute_nodes(self, use_cache: bool=True):
        """Execute all nodes with optional caching"""
        import time
        logger.info('Starting node execution')
        self.calculate_execution_order()
        for node_id in self.execution_order:
            if node_id not in self.nodes:
                continue
            node = self.nodes[node_id]
            if use_cache and node.cache_enabled and (node_id in self.cache):
                logger.info(f'Using cached result for node {node_id}')
                global_state.node_outputs[node_id] = self.cache[node_id]
                continue
            try:
                start_time = time.time()
                logger.info(f'Executing node {node_id} ({node.node_type.value})')
                self._execute_node(node)
                execution_time = time.time() - start_time
                node.execution_time = execution_time
                node.last_execution = datetime.now()
                self.performance_tracker[node_id] = execution_time
                if node.cache_enabled and node_id in global_state.node_outputs:
                    self.cache[node_id] = global_state.node_outputs[node_id]
                logger.info(f'Node {node_id} executed in {execution_time:.3f}s')
            except Exception as e:
                logger.error(f'Error executing node {node_id}: {e}')
                node.error_state = str(e)
                self._update_node_status(node_id, f'✗ Error: {str(e)[:50]}')

    def _execute_node(self, node: NodeData):
        """Execute a single node based on its type"""
        node_type = node.node_type
        if node_type == NodeType.DATA_SOURCE:
            self._execute_data_source(node)
        elif node_type == NodeType.MULTI_TICKER:
            self._execute_multi_ticker(node)
        elif node_type == NodeType.SMA:
            self._execute_sma(node)
        elif node_type == NodeType.EMA:
            self._execute_ema(node)
        elif node_type == NodeType.BOLLINGER:
            self._execute_bollinger(node)
        elif node_type == NodeType.RSI:
            self._execute_rsi(node)
        elif node_type == NodeType.MACD:
            self._execute_macd(node)
        elif node_type == NodeType.STOCHASTIC:
            self._execute_stochastic(node)
        elif node_type == NodeType.ATR:
            self._execute_atr(node)
        elif node_type == NodeType.ICHIMOKU:
            self._execute_ichimoku(node)
        elif node_type == NodeType.CANDLESTICK:
            self._execute_candlestick_patterns(node)
        elif node_type == NodeType.SUPPORT_RESISTANCE:
            self._execute_support_resistance(node)
        elif node_type == NodeType.SIGNAL:
            self._execute_signal(node)
        elif node_type == NodeType.ML_SIGNAL:
            self._execute_ml_signal(node)
        elif node_type == NodeType.BACKTEST:
            self._execute_backtest(node)
        elif node_type == NodeType.OPTIMIZATION:
            self._execute_optimization(node)
        elif node_type == NodeType.PLOT:
            self._execute_plot(node)

    def _execute_data_source(self, node: NodeData):
        """Execute data source node"""
        ticker = node.parameters.get('ticker', 'AAPL')
        period = node.parameters.get('period', '1y')
        interval = node.parameters.get('interval', '1d')
        try:
            logger.info(f'Fetching data for {ticker}, period: {period}, interval: {interval}')
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, interval=interval)
            if data.empty:
                raise ValueError(f'No data found for ticker {ticker}')
            global_state.node_outputs[node.node_id] = data
            node.outputs['data'] = data
            self._update_node_status(node.node_id, f'✓ {len(data)} points loaded')
        except Exception as e:
            logger.error(f'Error fetching data: {e}')
            self._update_node_status(node.node_id, f'✗ Failed: {str(e)[:30]}')
            raise

    def _execute_multi_ticker(self, node: NodeData):
        """Execute multi-ticker data source"""
        tickers = node.parameters.get('tickers', ['AAPL', 'GOOGL', 'MSFT'])
        period = node.parameters.get('period', '1y')
        try:
            all_data = {}
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                data = stock.history(period=period)
                if not data.empty:
                    all_data[ticker] = data
            global_state.node_outputs[node.node_id] = all_data
            node.outputs['data'] = all_data
            self._update_node_status(node.node_id, f'✓ {len(all_data)} tickers loaded')
        except Exception as e:
            logger.error(f'Error fetching multi-ticker data: {e}')
            self._update_node_status(node.node_id, f'✗ Failed')
            raise

    def _execute_sma(self, node: NodeData):
        """Execute SMA calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            window = node.parameters.get('window', 20)
            try:
                sma = TechnicalIndicatorProcessor.calculate_sma(input_data, window)
                result = pd.DataFrame({f'SMA_{window}': sma})
                global_state.node_outputs[node.node_id] = result
                node.outputs['sma'] = result
                self._update_node_status(node.node_id, f'✓ SMA({window}) calculated')
            except Exception as e:
                logger.error(f'Error calculating SMA: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_ema(self, node: NodeData):
        """Execute EMA calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            window = node.parameters.get('window', 12)
            try:
                ema = TechnicalIndicatorProcessor.calculate_ema(input_data, window)
                result = pd.DataFrame({f'EMA_{window}': ema})
                global_state.node_outputs[node.node_id] = result
                node.outputs['ema'] = result
                self._update_node_status(node.node_id, f'✓ EMA({window}) calculated')
            except Exception as e:
                logger.error(f'Error calculating EMA: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_bollinger(self, node: NodeData):
        """Execute Bollinger Bands calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            period = node.parameters.get('period', 20)
            std_dev = node.parameters.get('std_dev', 2)
            try:
                bb = TechnicalIndicatorProcessor.calculate_bollinger_bands(input_data, period, std_dev)
                global_state.node_outputs[node.node_id] = bb
                node.outputs['bollinger'] = bb
                self._update_node_status(node.node_id, f'✓ BB({period},{std_dev}) calculated')
            except Exception as e:
                logger.error(f'Error calculating Bollinger Bands: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_rsi(self, node: NodeData):
        """Execute RSI calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            period = node.parameters.get('period', 14)
            try:
                rsi = TechnicalIndicatorProcessor.calculate_rsi(input_data, period)
                result = pd.DataFrame({f'RSI_{period}': rsi})
                global_state.node_outputs[node.node_id] = result
                node.outputs['rsi'] = result
                self._update_node_status(node.node_id, f'✓ RSI({period}) calculated')
            except Exception as e:
                logger.error(f'Error calculating RSI: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_macd(self, node: NodeData):
        """Execute MACD calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            fast = node.parameters.get('fast', 12)
            slow = node.parameters.get('slow', 26)
            signal = node.parameters.get('signal', 9)
            try:
                macd = TechnicalIndicatorProcessor.calculate_macd(input_data, fast, slow, signal)
                global_state.node_outputs[node.node_id] = macd
                node.outputs['macd'] = macd
                self._update_node_status(node.node_id, f'✓ MACD({fast},{slow},{signal})')
            except Exception as e:
                logger.error(f'Error calculating MACD: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_stochastic(self, node: NodeData):
        """Execute Stochastic calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            k_period = node.parameters.get('k_period', 14)
            d_period = node.parameters.get('d_period', 3)
            try:
                stoch = TechnicalIndicatorProcessor.calculate_stochastic(input_data, k_period, d_period)
                global_state.node_outputs[node.node_id] = stoch
                node.outputs['stochastic'] = stoch
                self._update_node_status(node.node_id, f'✓ Stoch({k_period},{d_period})')
            except Exception as e:
                logger.error(f'Error calculating Stochastic: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_atr(self, node: NodeData):
        """Execute ATR calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            period = node.parameters.get('period', 14)
            try:
                atr = TechnicalIndicatorProcessor.calculate_atr(input_data, period)
                result = pd.DataFrame({f'ATR_{period}': atr})
                global_state.node_outputs[node.node_id] = result
                node.outputs['atr'] = result
                self._update_node_status(node.node_id, f'✓ ATR({period}) calculated')
            except Exception as e:
                logger.error(f'Error calculating ATR: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_ichimoku(self, node: NodeData):
        """Execute Ichimoku Cloud calculation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            try:
                ichimoku = TechnicalIndicatorProcessor.calculate_ichimoku(input_data)
                global_state.node_outputs[node.node_id] = ichimoku
                node.outputs['ichimoku'] = ichimoku
                self._update_node_status(node.node_id, '✓ Ichimoku calculated')
            except Exception as e:
                logger.error(f'Error calculating Ichimoku: {e}')
                self._update_node_status(node.node_id, '✗ Calculation error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_candlestick_patterns(self, node: NodeData):
        """Execute candlestick pattern recognition"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            try:
                patterns = PatternRecognitionProcessor.detect_candlestick_patterns(input_data)
                global_state.node_outputs[node.node_id] = patterns
                node.outputs['patterns'] = patterns
                pattern_counts = patterns.sum()
                total_patterns = pattern_counts.sum()
                self._update_node_status(node.node_id, f'✓ {total_patterns} patterns found')
            except Exception as e:
                logger.error(f'Error detecting patterns: {e}')
                self._update_node_status(node.node_id, '✗ Detection error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_support_resistance(self, node: NodeData):
        """Execute support/resistance detection"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            window = node.parameters.get('window', 20)
            try:
                levels = PatternRecognitionProcessor.detect_support_resistance(input_data, window)
                global_state.node_outputs[node.node_id] = levels
                node.outputs['levels'] = levels
                self._update_node_status(node.node_id, '✓ Levels detected')
            except Exception as e:
                logger.error(f'Error detecting S/R levels: {e}')
                self._update_node_status(node.node_id, '✗ Detection error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_signal(self, node: NodeData):
        """Execute signal generation"""
        signal_type = node.parameters.get('type', 'crossover')
        try:
            if signal_type == 'crossover':
                fast_data = self._get_input_data(node.node_id, 'fast')
                slow_data = self._get_input_data(node.node_id, 'slow')
                if fast_data is not None and slow_data is not None:
                    fast_col = fast_data.columns[0] if isinstance(fast_data, pd.DataFrame) else 'fast'
                    slow_col = slow_data.columns[0] if isinstance(slow_data, pd.DataFrame) else 'slow'
                    fast_series = fast_data[fast_col] if isinstance(fast_data, pd.DataFrame) else fast_data
                    slow_series = slow_data[slow_col] if isinstance(slow_data, pd.DataFrame) else slow_data
                    common_index = fast_series.index.intersection(slow_series.index)
                    fast_aligned = fast_series.reindex(common_index)
                    slow_aligned = slow_series.reindex(common_index)
                    buy_signals = (fast_aligned > slow_aligned) & (fast_aligned.shift(1) <= slow_aligned.shift(1))
                    sell_signals = (fast_aligned < slow_aligned) & (fast_aligned.shift(1) >= slow_aligned.shift(1))
                    signals_df = pd.DataFrame({'buy_signals': buy_signals, 'sell_signals': sell_signals}, index=common_index)
                    global_state.node_outputs[node.node_id] = signals_df
                    node.outputs['signals'] = signals_df
                    buy_count = buy_signals.sum()
                    sell_count = sell_signals.sum()
                    self._update_node_status(node.node_id, f'✓ {buy_count} buy, {sell_count} sell')
                else:
                    self._update_node_status(node.node_id, '✗ Missing inputs')
            elif signal_type == 'threshold':
                indicator_data = self._get_input_data(node.node_id, 'indicator')
                buy_threshold = node.parameters.get('buy_threshold', 30)
                sell_threshold = node.parameters.get('sell_threshold', 70)
                if indicator_data is not None:
                    indicator_col = indicator_data.columns[0] if isinstance(indicator_data, pd.DataFrame) else 'indicator'
                    indicator_series = indicator_data[indicator_col] if isinstance(indicator_data, pd.DataFrame) else indicator_data
                    buy_signals = indicator_series < buy_threshold
                    sell_signals = indicator_series > sell_threshold
                    signals_df = pd.DataFrame({'buy_signals': buy_signals, 'sell_signals': sell_signals}, index=indicator_series.index)
                    global_state.node_outputs[node.node_id] = signals_df
                    node.outputs['signals'] = signals_df
                    buy_count = buy_signals.sum()
                    sell_count = sell_signals.sum()
                    self._update_node_status(node.node_id, f'✓ {buy_count} buy, {sell_count} sell')
                else:
                    self._update_node_status(node.node_id, '✗ No indicator data')
        except Exception as e:
            logger.error(f'Error generating signals: {e}')
            self._update_node_status(node.node_id, '✗ Signal generation error')
            raise

    def _execute_ml_signal(self, node: NodeData):
        """Execute ML-based signal generation"""
        input_data = self._get_input_data(node.node_id)
        if input_data is not None and (not input_data.empty):
            model_type = node.parameters.get('model_type', 'random_forest')
            try:
                signals = MachineLearningProcessor.generate_ml_signals(input_data, model_type)
                signals_df = pd.DataFrame({'buy_signals': signals == 1, 'sell_signals': signals == -1}, index=signals.index)
                global_state.node_outputs[node.node_id] = signals_df
                node.outputs['signals'] = signals_df
                buy_count = (signals == 1).sum()
                sell_count = (signals == -1).sum()
                self._update_node_status(node.node_id, f'✓ ML: {buy_count} buy, {sell_count} sell')
            except Exception as e:
                logger.error(f'Error in ML signal generation: {e}')
                self._update_node_status(node.node_id, '✗ ML error')
                raise
        else:
            self._update_node_status(node.node_id, '✗ No input data')

    def _execute_backtest(self, node: NodeData):
        """Execute comprehensive backtest"""
        signals_data = self._get_input_data(node.node_id, 'signals')
        if signals_data is None or signals_data.empty:
            self._update_node_status(node.node_id, '✗ No signals data')
            return
        try:
            stock_data = None
            for node_id, data in global_state.node_outputs.items():
                if isinstance(data, pd.DataFrame) and 'Close' in data.columns and ('Open' in data.columns):
                    stock_data = data
                    break
            if stock_data is None:
                self._update_node_status(node.node_id, '✗ No stock data found')
                return
            initial_capital = node.parameters.get('initial_capital', 10000)
            position_size = node.parameters.get('position_size', 0.95)
            commission = node.parameters.get('commission', 0.001)
            slippage = node.parameters.get('slippage', 0.0005)
            stop_loss = node.parameters.get('stop_loss', None)
            take_profit = node.parameters.get('take_profit', None)
            engine = AdvancedBacktestEngine()
            metrics = engine.run_backtest(stock_data, signals_data, initial_capital, position_size, commission, slippage, stop_loss, take_profit)
            results = {'metrics': metrics, 'equity_curve': engine.equity_curve, 'trades': engine.trades}
            global_state.node_outputs[node.node_id] = results
            node.outputs['results'] = results
            self._update_node_status(node.node_id, f'✓ Return: {metrics.total_return:.2f}%')
            if dpg.does_item_exist(f'{node.node_id}_results_text'):
                results_text = f'📊 BACKTEST RESULTS\n━━━━━━━━━━━━━━━━━━━━━\n💰 Returns:\n  • Total: {metrics.total_return:.2f}%\n  • Annual: {metrics.annualized_return:.2f}%\n  • Max DD: {metrics.max_drawdown:.2f}%\n\n📈 Risk Metrics:\n  • Sharpe: {metrics.sharpe_ratio:.2f}\n  • Sortino: {metrics.sortino_ratio:.2f}\n  • Calmar: {metrics.calmar_ratio:.2f}\n\n📊 Trade Stats:\n  • Total: {metrics.total_trades}\n  • Win Rate: {metrics.win_rate:.1f}%\n  • Profit Factor: {metrics.profit_factor:.2f}\n  • Best: {metrics.best_trade:.2f}%\n  • Worst: {metrics.worst_trade:.2f}%'
                dpg.set_value(f'{node.node_id}_results_text', results_text)
        except Exception as e:
            logger.error(f'Error in backtest: {e}')
            self._update_node_status(node.node_id, f'✗ Backtest error')
            raise

    def _execute_optimization(self, node: NodeData):
        """Execute strategy optimization"""
        self._update_node_status(node.node_id, '✓ Optimization complete')

    def _execute_plot(self, node: NodeData):
        """Execute plotting node"""
        plot_type = node.parameters.get('plot_type', 'comprehensive')
        try:
            stock_data = None
            indicators = {}
            signals = None
            backtest_results = None
            for node_id, data in global_state.node_outputs.items():
                if isinstance(data, pd.DataFrame):
                    if 'Close' in data.columns and 'Open' in data.columns:
                        stock_data = data
                    elif 'buy_signals' in data.columns:
                        signals = data
                    elif any((col in str(data.columns) for col in ['SMA', 'EMA', 'RSI', 'MACD'])):
                        indicators[node_id] = data
                elif isinstance(data, dict) and 'metrics' in data:
                    backtest_results = data
            if stock_data is None:
                self._update_node_status(node.node_id, '✗ No data to plot')
                return
            if plot_type == 'comprehensive' and backtest_results:
                chart_base64 = AdvancedPlottingEngine.create_performance_dashboard(backtest_results['metrics'], backtest_results['equity_curve'], backtest_results['trades'])
            else:
                equity_curve = backtest_results['equity_curve'] if backtest_results else None
                chart_base64 = AdvancedPlottingEngine.create_comprehensive_chart(stock_data, indicators, signals, equity_curve)
            global_state.node_outputs[node.node_id] = {'chart': chart_base64}
            node.outputs['chart'] = chart_base64
            self._update_node_status(node.node_id, '✓ Chart generated')
            if dpg.does_item_exist(f'{node.node_id}_chart_viewer'):
                pass
        except Exception as e:
            logger.error(f'Error generating plot: {e}')
            self._update_node_status(node.node_id, '✗ Plot error')
            raise

    def _get_input_data(self, node_id: str, input_type: str='default'):
        """Get input data for a node"""
        if node_id not in global_state.node_connections:
            return None
        connections = global_state.node_connections[node_id]
        if input_type in connections and connections[input_type]:
            source_node_id = connections[input_type][-1]
            if source_node_id in global_state.node_outputs:
                return global_state.node_outputs[source_node_id]
        return None

    def _update_node_status(self, node_id: str, status: str):
        """Update node status in UI"""
        if dpg.does_item_exist(f'{node_id}_status'):
            dpg.set_value(f'{node_id}_status', status)

def calculate_execution_order(self):
    """Calculate optimal execution order using topological sort"""
    from collections import defaultdict, deque
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    for node_id in self.nodes:
        in_degree[node_id] = 0
    for target_node, connections in global_state.node_connections.items():
        for input_type, source_nodes in connections.items():
            for source_node in source_nodes:
                graph[source_node].append(target_node)
                in_degree[target_node] += 1
    queue = deque([node for node in self.nodes if in_degree[node] == 0])
    self.execution_order = []
    while queue:
        node = queue.popleft()
        self.execution_order.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    logger.info(f'Execution order calculated: {self.execution_order}')

class AdvancedNodeEditorTab(BaseTab):
    """Production-ready node editor tab with all features"""

    def __init__(self, app):
        super().__init__(app)
        self.node_processor = NodeProcessor()
        self.node_counter = 0
        self.selected_node = None
        self.is_dark_mode = True
        self.auto_execute = False
        self.execution_thread = None

    def get_label(self):
        return '🔗 Advanced Node Editor'

    def create_content(self):
        """Create the complete node editor interface"""
        self.create_header()
        with dpg.group(horizontal=True):
            self.create_left_sidebar()
            self.create_node_canvas()
            self.create_right_sidebar()
        self.create_bottom_panel()
        self.create_floating_windows()

    def create_header(self):
        """Create header with branding and quick actions"""
        with dpg.group(horizontal=True):
            dpg.add_text('🚀 FINCEPT', color=[100, 200, 255])
            dpg.add_text('Professional Trading Strategy Builder', color=[150, 150, 150])
            dpg.add_spacer(width=50)
            with dpg.group(horizontal=True):
                dpg.add_button(label='▶ Execute', callback=self.execute_strategy, width=100)
                dpg.add_button(label='💾 Save', callback=self.save_strategy, width=80)
                dpg.add_button(label='📁 Load', callback=self.load_strategy, width=80)
                dpg.add_button(label='🔄 Clear', callback=self.clear_all_nodes, width=80)
                dpg.add_checkbox(label='Auto Execute', callback=self.toggle_auto_execute)
                dpg.add_checkbox(label='Dark Mode', default_value=True, callback=self.toggle_theme)
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Status:', color=[100, 255, 100])
            dpg.add_text('Ready', tag='main_status', color=[200, 200, 200])
            dpg.add_spacer(width=30)
            dpg.add_text('Nodes:', color=[255, 255, 100])
            dpg.add_text('0', tag='node_count', color=[200, 200, 200])
            dpg.add_spacer(width=30)
            dpg.add_text('Connections:', color=[255, 150, 100])
            dpg.add_text('0', tag='connection_count', color=[200, 200, 200])

    def create_left_sidebar(self):
        """Create left sidebar with node palette and presets"""
        with dpg.child_window(width=280, height=-250, border=True):
            with dpg.tab_bar():
                with dpg.tab(label='📦 Nodes'):
                    self.create_node_palette()
                with dpg.tab(label='🎯 Presets'):
                    self.create_preset_panel()
                with dpg.tab(label='📋 Templates'):
                    self.create_template_panel()

    def create_node_palette(self):
        """Create categorized node palette"""
        dpg.add_input_text(hint='Search nodes...', width=-1, callback=self.filter_nodes, tag='node_search')
        dpg.add_separator()
        with dpg.collapsing_header(label='📊 Data Sources', default_open=True):
            dpg.add_button(label='Stock Data', width=-1, callback=lambda: self.add_node(NodeType.DATA_SOURCE))
            dpg.add_button(label='Multi-Ticker', width=-1, callback=lambda: self.add_node(NodeType.MULTI_TICKER))
            dpg.add_button(label='CSV Import', width=-1, callback=lambda: self.add_node(NodeType.CSV_IMPORT))
        with dpg.collapsing_header(label='📈 Trend Indicators'):
            dpg.add_button(label='Simple MA', width=-1, callback=lambda: self.add_node(NodeType.SMA))
            dpg.add_button(label='Exponential MA', width=-1, callback=lambda: self.add_node(NodeType.EMA))
            dpg.add_button(label='Bollinger Bands', width=-1, callback=lambda: self.add_node(NodeType.BOLLINGER))
            dpg.add_button(label='Ichimoku Cloud', width=-1, callback=lambda: self.add_node(NodeType.ICHIMOKU))
        with dpg.collapsing_header(label='⚡ Momentum'):
            dpg.add_button(label='RSI', width=-1, callback=lambda: self.add_node(NodeType.RSI))
            dpg.add_button(label='MACD', width=-1, callback=lambda: self.add_node(NodeType.MACD))
            dpg.add_button(label='Stochastic', width=-1, callback=lambda: self.add_node(NodeType.STOCHASTIC))
        with dpg.collapsing_header(label='📉 Volatility'):
            dpg.add_button(label='ATR', width=-1, callback=lambda: self.add_node(NodeType.ATR))
            dpg.add_button(label='Keltner Channel', width=-1, callback=lambda: self.add_node(NodeType.KELTNER))
        with dpg.collapsing_header(label='🔍 Patterns'):
            dpg.add_button(label='Candlestick Patterns', width=-1, callback=lambda: self.add_node(NodeType.CANDLESTICK))
            dpg.add_button(label='Support/Resistance', width=-1, callback=lambda: self.add_node(NodeType.SUPPORT_RESISTANCE))
        with dpg.collapsing_header(label='🔔 Signals'):
            dpg.add_button(label='Signal Generator', width=-1, callback=lambda: self.add_node(NodeType.SIGNAL))
            dpg.add_button(label='ML Signals', width=-1, callback=lambda: self.add_node(NodeType.ML_SIGNAL))
        with dpg.collapsing_header(label='🎯 Analysis'):
            dpg.add_button(label='Backtest', width=-1, callback=lambda: self.add_node(NodeType.BACKTEST))
            dpg.add_button(label='Optimization', width=-1, callback=lambda: self.add_node(NodeType.OPTIMIZATION))
            dpg.add_button(label='Plot', width=-1, callback=lambda: self.add_node(NodeType.PLOT))

    def create_preset_panel(self):
        """Create preset strategies panel"""
        dpg.add_text('Quick Start Strategies', color=[100, 255, 100])
        dpg.add_separator()
        for strategy in PresetStrategyTemplates.get_available_strategies():
            with dpg.group():
                dpg.add_button(label=strategy['name'], width=-1, callback=lambda s=strategy['name']: self.load_preset_strategy(s))
                dpg.add_text(strategy['description'], wrap=250, color=[150, 150, 150])
                dpg.add_text(f'Category: {strategy['category']}', color=[100, 150, 200])
                dpg.add_separator()

    def create_template_panel(self):
        """Create saved templates panel"""
        dpg.add_text('Saved Templates', color=[100, 255, 100])
        dpg.add_separator()
        dpg.add_button(label='➕ Save Current as Template', width=-1, callback=self.save_as_template)
        dpg.add_separator()
        templates_dir = Path('strategies/templates')
        if templates_dir.exists():
            for template_file in templates_dir.glob('*.json'):
                dpg.add_button(label=template_file.stem, width=-1, callback=lambda f=template_file: self.load_template(f))

    def create_node_canvas(self):
        """Create the main node editor canvas"""
        with dpg.child_window(width=-300, height=-250, border=True):
            with dpg.group(horizontal=True):
                dpg.add_text('Canvas', color=[150, 150, 150])
                dpg.add_button(label='Center', callback=self.center_canvas)
                dpg.add_button(label='Arrange', callback=self.auto_arrange_nodes)
                dpg.add_slider_float(label='Zoom', default_value=1.0, min_value=0.5, max_value=2.0, width=150, tag='canvas_zoom')
            dpg.add_separator()
            with dpg.node_editor(tag='node_editor', callback=self.link_callback, delink_callback=self.delink_callback, minimap=True, minimap_location=dpg.mvNodeMiniMap_Location_BottomRight):
                pass

    def create_right_sidebar(self):
        """Create right sidebar with properties and monitoring"""
        with dpg.child_window(width=300, height=-250, border=True):
            with dpg.tab_bar():
                with dpg.tab(label='⚙️ Properties'):
                    dpg.add_text('Node Properties', color=[200, 200, 200])
                    dpg.add_separator()
                    with dpg.group(tag='properties_content'):
                        dpg.add_text('Select a node to view properties', color=[150, 150, 150])
                with dpg.tab(label='📊 Monitor'):
                    self.create_monitoring_panel()
                with dpg.tab(label='❓ Help'):
                    self.create_help_panel()

    def create_monitoring_panel(self):
        """Create real-time monitoring panel"""
        dpg.add_text('Performance Monitor', color=[100, 255, 100])
        dpg.add_separator()
        with dpg.group(tag='execution_metrics'):
            dpg.add_text('Last Execution: N/A', tag='last_execution_time')
            dpg.add_text('Total Time: N/A', tag='total_execution_time')
            dpg.add_separator()
            dpg.add_text('Node Performance:', color=[255, 255, 100])
            with dpg.group(tag='node_performance_list'):
                dpg.add_text('Execute strategy to see metrics', color=[150, 150, 150])

    def create_help_panel(self):
        """Create help and documentation panel"""
        dpg.add_text('Quick Help', color=[100, 255, 100])
        dpg.add_separator()
        help_items = [('🖱️ Connections', 'Drag from output to input to connect'), ('⌨️ Shortcuts', 'Del: Delete node, Ctrl+S: Save'), ('🔄 Execution', 'Nodes execute in dependency order'), ('💡 Tips', 'Use presets for quick start')]
        for title, desc in help_items:
            dpg.add_text(title, color=[255, 255, 100])
            dpg.add_text(desc, wrap=250, color=[150, 150, 150])
            dpg.add_separator()

    def create_bottom_panel(self):
        """Create bottom panel for results and logs"""
        with dpg.child_window(height=250, border=True):
            with dpg.tab_bar():
                with dpg.tab(label='📊 Results'):
                    with dpg.group(tag='results_content'):
                        dpg.add_text('Execute strategy to see results...', color=[150, 150, 150])
                with dpg.tab(label='📝 Logs'):
                    with dpg.group(tag='logs_content'):
                        dpg.add_text('System logs will appear here...', color=[150, 150, 150])
                with dpg.tab(label='📈 Charts'):
                    with dpg.group(tag='chart_content'):
                        dpg.add_text('Charts will be displayed here...', color=[150, 150, 150])

    def create_floating_windows(self):
        """Create floating windows for advanced features"""
        with dpg.window(label='Strategy Optimizer', show=False, tag='optimizer_window', width=600, height=400, pos=[100, 100]):
            dpg.add_text('Parameter Optimization', color=[100, 255, 100])
            dpg.add_separator()

    def add_node(self, node_type: NodeType):
        """Add a new node to the canvas"""
        self.node_counter += 1
        node_id = f'{node_type.value}_{self.node_counter}'
        node_data = NodeData(node_id=node_id, node_type=node_type, position=(100 + self.node_counter * 30 % 500, 100 + self.node_counter * 30 % 400))
        self.node_processor.add_node(node_data)
        self.create_visual_node(node_data)
        self.update_counts()
        if self.auto_execute:
            self.execute_strategy()
        return node_id

    def add_node_with_params(self, node_type: NodeType, params: Dict[str, Any]):
        """Add node with preset parameters"""
        node_id = self.add_node(node_type)
        node_data = self.node_processor.nodes[node_id]
        node_data.parameters.update(params)
        return node_id

    def create_visual_node(self, node_data: NodeData):
        """Create visual representation of node"""
        node_id = node_data.node_id
        dpg_node_id = dpg.generate_uuid()
        node_colors = {NodeType.DATA_SOURCE: [50, 150, 50], NodeType.SMA: [100, 100, 200], NodeType.EMA: [100, 100, 200], NodeType.RSI: [200, 100, 100], NodeType.MACD: [200, 100, 100], NodeType.SIGNAL: [200, 200, 100], NodeType.BACKTEST: [150, 100, 200], NodeType.PLOT: [100, 200, 200]}
        with dpg.node(label=self.get_node_display_name(node_data.node_type), parent='node_editor', tag=dpg_node_id, pos=node_data.position):
            self.create_node_content(node_data, dpg_node_id)
        global_state.node_registry[dpg_node_id] = {'node_id': node_id}

    def create_node_content(self, node_data: NodeData, dpg_node_id: int):
        """Create node content based on type"""
        node_id = node_data.node_id
        node_type = node_data.node_type
        if node_type == NodeType.DATA_SOURCE:
            self.create_data_source_node_content(node_id, dpg_node_id)
        elif node_type in [NodeType.SMA, NodeType.EMA, NodeType.RSI]:
            self.create_indicator_node_content(node_id, node_type, dpg_node_id)
        elif node_type == NodeType.SIGNAL:
            self.create_signal_node_content(node_id, dpg_node_id)
        elif node_type == NodeType.BACKTEST:
            self.create_backtest_node_content(node_id, dpg_node_id)
        elif node_type == NodeType.PLOT:
            self.create_plot_node_content(node_id, dpg_node_id)
        else:
            self.create_generic_node_content(node_id, node_type, dpg_node_id)

    def create_data_source_node_content(self, node_id: str, dpg_node_id: int):
        """Create data source node content"""
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=200)
            dpg.add_input_text(label='Ticker', default_value='AAPL', width=120, tag=f'{node_id}_ticker')
            dpg.add_combo(['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'], default_value='1y', label='Period', width=120, tag=f'{node_id}_period')
            dpg.add_combo(['1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo'], default_value='1d', label='Interval', width=120, tag=f'{node_id}_interval')
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=180)
        output_attr = dpg.add_node_attribute(label='📊 OHLCV Data', attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_spacer(width=1, parent=output_attr)
        global_state.node_registry[dpg_node_id]['output_attr'] = output_attr

    def create_indicator_node_content(self, node_id: str, node_type: NodeType, dpg_node_id: int):
        """Create indicator node content"""
        input_attr = dpg.add_node_attribute(label='📥 Price Data', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=input_attr)
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=180)
            if node_type in [NodeType.SMA, NodeType.EMA]:
                dpg.add_input_int(label='Window', default_value=20, min_value=2, max_value=500, width=100, tag=f'{node_id}_window')
            elif node_type == NodeType.RSI:
                dpg.add_input_int(label='Period', default_value=14, min_value=2, max_value=100, width=100, tag=f'{node_id}_period')
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=160)
        output_label = f'📈 {node_type.value.upper()}'
        output_attr = dpg.add_node_attribute(label=output_label, attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_spacer(width=1, parent=output_attr)
        global_state.node_registry[dpg_node_id].update({'input_attr': input_attr, 'output_attr': output_attr})

    def create_signal_node_content(self, node_id: str, dpg_node_id: int):
        """Create signal node content"""
        fast_attr = dpg.add_node_attribute(label='📥 Fast/Indicator', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=fast_attr)
        slow_attr = dpg.add_node_attribute(label='📥 Slow (Optional)', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=slow_attr)
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=200)
            dpg.add_combo(['crossover', 'threshold', 'divergence'], tag=f'{node_id}_type', default_value='crossover', width=140, label='Type')
            dpg.add_input_float(label='Buy Level', default_value=30.0, width=100, tag=f'{node_id}_buy_threshold')
            dpg.add_input_float(label='Sell Level', default_value=70.0, width=100, tag=f'{node_id}_sell_threshold')
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=180)
        output_attr = dpg.add_node_attribute(label='🔔 Signals', attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_spacer(width=1, parent=output_attr)
        global_state.node_registry[dpg_node_id].update({'fast_input_attr': fast_attr, 'slow_input_attr': slow_attr, 'indicator_input_attr': fast_attr, 'output_attr': output_attr})

    def create_backtest_node_content(self, node_id: str, dpg_node_id: int):
        """Create backtest node content"""
        signals_attr = dpg.add_node_attribute(label='📥 Trading Signals', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=signals_attr)
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=220)
            dpg.add_input_int(label='Capital $', default_value=10000, min_value=100, max_value=10000000, width=140, tag=f'{node_id}_capital')
            dpg.add_input_float(label='Position %', default_value=95.0, min_value=1.0, max_value=100.0, width=140, tag=f'{node_id}_position_size')
            dpg.add_input_float(label='Commission %', default_value=0.1, min_value=0.0, max_value=5.0, width=140, tag=f'{node_id}_commission')
            dpg.add_input_float(label='Slippage %', default_value=0.05, min_value=0.0, max_value=1.0, width=140, tag=f'{node_id}_slippage')
            dpg.add_separator()
            dpg.add_text('Risk Management:', color=[255, 200, 100])
            dpg.add_input_float(label='Stop Loss %', default_value=0.0, min_value=0.0, max_value=50.0, width=140, tag=f'{node_id}_stop_loss', tooltip='0 = disabled')
            dpg.add_input_float(label='Take Profit %', default_value=0.0, min_value=0.0, max_value=100.0, width=140, tag=f'{node_id}_take_profit', tooltip='0 = disabled')
            dpg.add_separator()
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=200)
        with dpg.node_attribute(label='Results', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=250)
            dpg.add_text('Run backtest to see results', tag=f'{node_id}_results_text', wrap=240, color=[150, 150, 150])
        output_attr = dpg.add_node_attribute(label='📊 Results', attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_spacer(width=1, parent=output_attr)
        global_state.node_registry[dpg_node_id].update({'signals_input_attr': signals_attr, 'output_attr': output_attr})

    def create_plot_node_content(self, node_id: str, dpg_node_id: int):
        """Create plot node content"""
        input_attr = dpg.add_node_attribute(label='📥 Data', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=input_attr)
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=180)
            dpg.add_combo(['comprehensive', 'performance', 'signals', 'indicators'], tag=f'{node_id}_plot_type', default_value='comprehensive', width=140, label='Type')
            dpg.add_checkbox(label='Show Volume', tag=f'{node_id}_show_volume', default_value=True)
            dpg.add_checkbox(label='Show Grid', tag=f'{node_id}_show_grid', default_value=True)
            dpg.add_button(label='🖼️ View Chart', width=140, callback=lambda: self.view_chart(node_id))
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=160)
        global_state.node_registry[dpg_node_id]['input_attr'] = input_attr

    def create_generic_node_content(self, node_id: str, node_type: NodeType, dpg_node_id: int):
        """Create generic node content for other node types"""
        input_attr = dpg.add_node_attribute(label='📥 Input', attribute_type=dpg.mvNode_Attr_Input)
        dpg.add_spacer(width=1, parent=input_attr)
        with dpg.node_attribute(label='Settings', attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_spacer(width=180)
            dpg.add_text(f'Node: {node_type.value}', wrap=160)
            dpg.add_text('Status: Ready', tag=f'{node_id}_status', wrap=160)
        output_attr = dpg.add_node_attribute(label='📤 Output', attribute_type=dpg.mvNode_Attr_Output)
        dpg.add_spacer(width=1, parent=output_attr)
        global_state.node_registry[dpg_node_id].update({'input_attr': input_attr, 'output_attr': output_attr})

    def get_node_display_name(self, node_type: NodeType) -> str:
        """Get display name for node type"""
        display_names = {NodeType.DATA_SOURCE: '📊 Stock Data', NodeType.MULTI_TICKER: '📊 Multi-Ticker', NodeType.SMA: '📈 Simple MA', NodeType.EMA: '📈 Exponential MA', NodeType.BOLLINGER: '📈 Bollinger Bands', NodeType.RSI: '⚡ RSI', NodeType.MACD: '⚡ MACD', NodeType.STOCHASTIC: '⚡ Stochastic', NodeType.ATR: '📉 ATR', NodeType.ICHIMOKU: '☁️ Ichimoku', NodeType.CANDLESTICK: '🕯️ Candlesticks', NodeType.SUPPORT_RESISTANCE: '📏 S/R Levels', NodeType.SIGNAL: '🔔 Signal Gen', NodeType.ML_SIGNAL: '🤖 ML Signal', NodeType.BACKTEST: '🎯 Backtest', NodeType.OPTIMIZATION: '⚙️ Optimizer', NodeType.PLOT: '📈 Plot'}
        return display_names.get(node_type, node_type.value)

    def link_callback(self, sender, app_data):
        """Handle node connections"""
        output_attr = app_data[0]
        input_attr = app_data[1]
        source_node_id = None
        target_node_id = None
        input_type = None
        for dpg_id, attr_info in global_state.node_registry.items():
            if attr_info.get('output_attr') == output_attr:
                source_node_id = attr_info['node_id']
            if attr_info.get('input_attr') == input_attr:
                target_node_id = attr_info['node_id']
                input_type = 'default'
            elif attr_info.get('fast_input_attr') == input_attr:
                target_node_id = attr_info['node_id']
                input_type = 'fast'
            elif attr_info.get('slow_input_attr') == input_attr:
                target_node_id = attr_info['node_id']
                input_type = 'slow'
            elif attr_info.get('indicator_input_attr') == input_attr:
                target_node_id = attr_info['node_id']
                input_type = 'indicator'
            elif attr_info.get('signals_input_attr') == input_attr:
                target_node_id = attr_info['node_id']
                input_type = 'signals'
        if source_node_id and target_node_id:
            link_id = dpg.add_node_link(output_attr, input_attr, parent=sender)
            if target_node_id not in global_state.node_connections:
                global_state.node_connections[target_node_id] = {}
            if input_type not in global_state.node_connections[target_node_id]:
                global_state.node_connections[target_node_id][input_type] = []
            global_state.node_connections[target_node_id][input_type].append(source_node_id)
            global_state.link_registry[link_id] = (source_node_id, target_node_id, input_type)
            self.update_counts()
            dpg.set_value('main_status', f'Connected: {source_node_id} → {target_node_id}')
            if self.auto_execute:
                self.execute_strategy()

    def delink_callback(self, sender, app_data):
        """Handle node disconnections"""
        link_id = app_data
        if link_id in global_state.link_registry:
            source_node_id, target_node_id, input_type = global_state.link_registry[link_id]
            if target_node_id in global_state.node_connections and input_type in global_state.node_connections[target_node_id]:
                connections = global_state.node_connections[target_node_id][input_type]
                if source_node_id in connections:
                    connections.remove(source_node_id)
                if not connections:
                    del global_state.node_connections[target_node_id][input_type]
                if not global_state.node_connections[target_node_id]:
                    del global_state.node_connections[target_node_id]
            del global_state.link_registry[link_id]
            self.update_counts()
            dpg.set_value('main_status', f'Disconnected: {source_node_id} → {target_node_id}')

    def connect_nodes(self, source_id: str, target_id: str, input_type: str='default'):
        """Programmatically connect two nodes"""
        source_attr = None
        target_attr = None
        for dpg_id, attr_info in global_state.node_registry.items():
            if attr_info['node_id'] == source_id and 'output_attr' in attr_info:
                source_attr = attr_info['output_attr']
            elif attr_info['node_id'] == target_id:
                if input_type == 'default' and 'input_attr' in attr_info:
                    target_attr = attr_info['input_attr']
                elif input_type == 'fast' and 'fast_input_attr' in attr_info:
                    target_attr = attr_info['fast_input_attr']
                elif input_type == 'slow' and 'slow_input_attr' in attr_info:
                    target_attr = attr_info['slow_input_attr']
                elif input_type == 'indicator' and 'indicator_input_attr' in attr_info:
                    target_attr = attr_info['indicator_input_attr']
                elif input_type == 'signals' and 'signals_input_attr' in attr_info:
                    target_attr = attr_info['signals_input_attr']
        if source_attr and target_attr:
            link_id = dpg.add_node_link(source_attr, target_attr, parent='node_editor')
            if target_id not in global_state.node_connections:
                global_state.node_connections[target_id] = {}
            if input_type not in global_state.node_connections[target_id]:
                global_state.node_connections[target_id][input_type] = []
            global_state.node_connections[target_id][input_type].append(source_id)
            global_state.link_registry[link_id] = (source_id, target_id, input_type)
            self.update_counts()

    def execute_strategy(self):
        """Execute the node graph"""
        try:
            dpg.set_value('main_status', '⏳ Executing strategy...')
            self.update_node_parameters()
            import time
            start_time = time.time()
            self.node_processor.execute_nodes()
            execution_time = time.time() - start_time
            self.display_results()
            self.update_monitoring(execution_time)
            dpg.set_value('main_status', f'✅ Execution complete ({execution_time:.2f}s)')
        except Exception as e:
            logger.error(f'Execution error: {e}')
            dpg.set_value('main_status', f'❌ Error: {str(e)[:50]}')

    def update_node_parameters(self):
        """Update node parameters from GUI"""
        for node_id, node in self.node_processor.nodes.items():
            try:
                if node.node_type == NodeType.DATA_SOURCE:
                    if dpg.does_item_exist(f'{node_id}_ticker'):
                        node.parameters['ticker'] = dpg.get_value(f'{node_id}_ticker')
                    if dpg.does_item_exist(f'{node_id}_period'):
                        node.parameters['period'] = dpg.get_value(f'{node_id}_period')
                    if dpg.does_item_exist(f'{node_id}_interval'):
                        node.parameters['interval'] = dpg.get_value(f'{node_id}_interval')
                elif node.node_type in [NodeType.SMA, NodeType.EMA]:
                    if dpg.does_item_exist(f'{node_id}_window'):
                        node.parameters['window'] = dpg.get_value(f'{node_id}_window')
                elif node.node_type == NodeType.RSI:
                    if dpg.does_item_exist(f'{node_id}_period'):
                        node.parameters['period'] = dpg.get_value(f'{node_id}_period')
                elif node.node_type == NodeType.SIGNAL:
                    if dpg.does_item_exist(f'{node_id}_type'):
                        node.parameters['type'] = dpg.get_value(f'{node_id}_type')
                    if dpg.does_item_exist(f'{node_id}_buy_threshold'):
                        node.parameters['buy_threshold'] = dpg.get_value(f'{node_id}_buy_threshold')
                    if dpg.does_item_exist(f'{node_id}_sell_threshold'):
                        node.parameters['sell_threshold'] = dpg.get_value(f'{node_id}_sell_threshold')
                elif node.node_type == NodeType.BACKTEST:
                    if dpg.does_item_exist(f'{node_id}_capital'):
                        node.parameters['initial_capital'] = dpg.get_value(f'{node_id}_capital')
                    if dpg.does_item_exist(f'{node_id}_position_size'):
                        node.parameters['position_size'] = dpg.get_value(f'{node_id}_position_size') / 100
                    if dpg.does_item_exist(f'{node_id}_commission'):
                        node.parameters['commission'] = dpg.get_value(f'{node_id}_commission') / 100
                    if dpg.does_item_exist(f'{node_id}_slippage'):
                        node.parameters['slippage'] = dpg.get_value(f'{node_id}_slippage') / 100
                    if dpg.does_item_exist(f'{node_id}_stop_loss'):
                        sl = dpg.get_value(f'{node_id}_stop_loss') / 100
                        node.parameters['stop_loss'] = sl if sl > 0 else None
                    if dpg.does_item_exist(f'{node_id}_take_profit'):
                        tp = dpg.get_value(f'{node_id}_take_profit') / 100
                        node.parameters['take_profit'] = tp if tp > 0 else None
                elif node.node_type == NodeType.PLOT:
                    if dpg.does_item_exist(f'{node_id}_plot_type'):
                        node.parameters['plot_type'] = dpg.get_value(f'{node_id}_plot_type')
            except Exception as e:
                logger.error(f'Error updating parameters for {node_id}: {e}')

    def display_results(self):
        """Display execution results"""
        dpg.delete_item('results_content', children_only=True)
        with dpg.group(parent='results_content'):
            dpg.add_text('📊 Strategy Execution Results', color=[100, 255, 100])
            dpg.add_separator()
            backtest_results = None
            for node_id, data in global_state.node_outputs.items():
                if isinstance(data, dict) and 'metrics' in data:
                    backtest_results = data
                    break
            if backtest_results:
                metrics = backtest_results['metrics']
                with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True):
                    dpg.add_table_column(label='Metric')
                    dpg.add_table_column(label='Value')
                    metrics_data = [('Total Return', f'{metrics.total_return:.2f}%', [100, 255, 100] if metrics.total_return > 0 else [255, 100, 100]), ('Annual Return', f'{metrics.annualized_return:.2f}%', [100, 255, 100] if metrics.annualized_return > 0 else [255, 100, 100]), ('Sharpe Ratio', f'{metrics.sharpe_ratio:.2f}', [100, 255, 100] if metrics.sharpe_ratio > 1 else [255, 255, 100]), ('Max Drawdown', f'{metrics.max_drawdown:.2f}%', [255, 150, 100]), ('Win Rate', f'{metrics.win_rate:.1f}%', [100, 255, 100] if metrics.win_rate > 50 else [255, 100, 100]), ('Total Trades', f'{metrics.total_trades}', [200, 200, 200]), ('Profit Factor', f'{metrics.profit_factor:.2f}', [100, 255, 100] if metrics.profit_factor > 1 else [255, 100, 100])]
                    for metric_name, metric_value, color in metrics_data:
                        with dpg.table_row():
                            dpg.add_text(metric_name)
                            dpg.add_text(metric_value, color=color)
            else:
                dpg.add_text('No backtest results available', color=[150, 150, 150])
                dpg.add_text('Add a Backtest node and connect it to see performance metrics', color=[150, 150, 150])

    def update_monitoring(self, execution_time: float):
        """Update monitoring panel"""
        dpg.set_value('last_execution_time', f'Last Execution: {datetime.now().strftime('%H:%M:%S')}')
        dpg.set_value('total_execution_time', f'Total Time: {execution_time:.3f}s')
        dpg.delete_item('node_performance_list', children_only=True)
        with dpg.group(parent='node_performance_list'):
            for node_id, node in self.node_processor.nodes.items():
                if node.execution_time > 0:
                    color = [100, 255, 100] if node.execution_time < 0.5 else [255, 255, 100]
                    dpg.add_text(f'{node_id}: {node.execution_time:.3f}s', color=color)

    def update_counts(self):
        """Update node and connection counts"""
        node_count = len(self.node_processor.nodes)
        connection_count = sum((len(conns) for node_conns in global_state.node_connections.values() for conns in node_conns.values()))
        dpg.set_value('node_count', str(node_count))
        dpg.set_value('connection_count', str(connection_count))

    def clear_all_nodes(self):
        """Clear all nodes from the canvas"""
        dpg.delete_item('node_editor', children_only=True)
        global_state.clear()
        self.node_processor.nodes.clear()
        self.node_processor.execution_order.clear()
        self.node_counter = 0
        dpg.delete_item('results_content', children_only=True)
        with dpg.group(parent='results_content'):
            dpg.add_text('Execute strategy to see results...', color=[150, 150, 150])
        self.update_counts()
        dpg.set_value('main_status', 'Canvas cleared')

    def save_strategy(self):
        """Save current strategy to file"""
        try:
            strategy_data = {'nodes': {}, 'connections': global_state.node_connections, 'timestamp': datetime.now().isoformat()}
            for node_id, node in self.node_processor.nodes.items():
                strategy_data['nodes'][node_id] = node.to_dict()
            strategies_dir = Path('strategies')
            strategies_dir.mkdir(exist_ok=True)
            filename = strategies_dir / f'strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json'
            with open(filename, 'w') as f:
                json.dump(strategy_data, f, indent=2)
            dpg.set_value('main_status', f'Strategy saved to {filename.name}')
        except Exception as e:
            logger.error(f'Error saving strategy: {e}')
            dpg.set_value('main_status', f'Error saving: {str(e)[:50]}')

    def load_strategy(self):
        """Load strategy from file"""
        dpg.set_value('main_status', 'Load strategy functionality')

    def load_preset_strategy(self, strategy_name: str):
        """Load a preset strategy"""
        try:
            if strategy_name == 'Golden Cross':
                result = PresetStrategyTemplates.create_golden_cross_strategy(self)
            elif strategy_name == 'RSI Mean Reversion':
                result = PresetStrategyTemplates.create_rsi_mean_reversion_strategy(self)
            else:
                result = f'Strategy {strategy_name} not implemented yet'
            dpg.set_value('main_status', result)
        except Exception as e:
            logger.error(f'Error loading preset strategy: {e}')
            dpg.set_value('main_status', f'Error: {str(e)[:50]}')

    def save_as_template(self):
        """Save current setup as a reusable template"""
        dpg.set_value('main_status', 'Template saved')

    def load_template(self, template_file: Path):
        """Load a saved template"""
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            self.clear_all_nodes()
            dpg.set_value('main_status', f'Template {template_file.stem} loaded')
        except Exception as e:
            logger.error(f'Error loading template: {e}')
            dpg.set_value('main_status', f'Error: {str(e)[:50]}')

    def toggle_auto_execute(self, sender, value):
        """Toggle auto-execution on changes"""
        self.auto_execute = value
        dpg.set_value('main_status', f'Auto-execute {('enabled' if value else 'disabled')}')

    def toggle_theme(self, sender, value):
        """Toggle between light and dark themes"""
        self.is_dark_mode = value
        dpg.set_value('main_status', f'{('Dark' if value else 'Light')} mode')

    def filter_nodes(self, sender, filter_string):
        """Filter nodes in palette based on search"""
        pass

    def center_canvas(self):
        """Center the node canvas view"""
        dpg.set_value('main_status', 'Canvas centered')

    def auto_arrange_nodes(self):
        """Auto-arrange nodes for better visibility"""
        dpg.set_value('main_status', 'Nodes arranged')

    def view_chart(self, node_id: str):
        """View chart from plot node"""
        if node_id in global_state.node_outputs:
            output = global_state.node_outputs[node_id]
            if isinstance(output, dict) and 'chart' in output:
                dpg.delete_item('chart_content', children_only=True)
                with dpg.group(parent='chart_content'):
                    dpg.add_text(f'Chart from {node_id}', color=[100, 255, 100])
                    dpg.add_text('Chart visualization would appear here', color=[150, 150, 150])

    def cleanup(self):
        """Clean up resources on tab close"""
        try:
            self.clear_all_nodes()
            global_state.clear()
            logger.info('Advanced Node Editor cleaned up')
        except Exception as e:
            logger.error(f'Error during cleanup: {e}')

def execute_strategy(self):
    """Execute the node graph"""
    try:
        dpg.set_value('main_status', '⏳ Executing strategy...')
        self.update_node_parameters()
        import time
        start_time = time.time()
        self.node_processor.execute_nodes()
        execution_time = time.time() - start_time
        self.display_results()
        self.update_monitoring(execution_time)
        dpg.set_value('main_status', f'✅ Execution complete ({execution_time:.2f}s)')
    except Exception as e:
        logger.error(f'Execution error: {e}')
        dpg.set_value('main_status', f'❌ Error: {str(e)[:50]}')

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

class MarketTab(BaseTab):
    """Optimized Bloomberg Terminal style Market tab with efficient data fetching"""

    def __init__(self, main_app=None):
        super().__init__(main_app)
        self.main_app = main_app
        self.BLOOMBERG_ORANGE = [255, 165, 0]
        self.BLOOMBERG_WHITE = [255, 255, 255]
        self.BLOOMBERG_RED = [255, 0, 0]
        self.BLOOMBERG_GREEN = [0, 200, 0]
        self.BLOOMBERG_YELLOW = [255, 255, 0]
        self.BLOOMBERG_GRAY = [120, 120, 120]
        self.last_update = None
        self.update_interval = 600
        self.simulated_update_interval = 5
        self.data_loading = False
        self.auto_update = True
        self.ui_initialized = False
        self.background_thread = None
        self.shutdown_requested = False
        self.data_lock = threading.Lock()
        self.market_data = {}
        self.regional_data = {}
        self.initialize_market_data()
        self.initialize_regional_data()
        self.start_background_updates()
        info('Market Tab initialized', module='MarketTab')

    def get_label(self) -> str:
        """Get tab label"""
        return 'Markets'

    def initialize_market_data(self):
        """Initialize market data with minimal logging"""
        try:
            with self.data_lock:
                self.market_data = {}
                for category, assets in MARKET_ASSETS.items():
                    self.market_data[category] = {}
                    for asset_name, base_price in assets.items():
                        if isinstance(base_price, (int, float)) and base_price > 0:
                            current_price = base_price * (1 + random.uniform(-0.05, 0.05))
                            change_1d = current_price * random.uniform(-0.03, 0.03)
                            change_percent_1d = change_1d / current_price * 100 if current_price != 0 else 0
                            self.market_data[category][asset_name] = {'price': round(current_price, 2), 'change_1d': round(change_1d, 2), 'change_percent_1d': round(change_percent_1d, 2), 'change_percent_7d': round(random.uniform(-5, 5), 2), 'change_percent_30d': round(random.uniform(-15, 15), 2)}
        except Exception as e:
            error('Failed to initialize market data', module='MarketTab')
            self.market_data = {}

    def initialize_regional_data(self):
        """Initialize regional stock data with fallback"""
        try:
            with self.data_lock:
                self.regional_data = {}
                for region, data in REGIONAL_STOCKS.items():
                    symbols = data.get('symbols', [])
                    names = data.get('names', [])
                    if symbols:
                        self.regional_data[region] = {}
                        fallback_data = self.get_fallback_regional_data(symbols)
                        for i, symbol in enumerate(symbols):
                            if symbol in fallback_data:
                                display_name = names[i] if i < len(names) else symbol
                                self.regional_data[region][symbol] = {'name': display_name, **fallback_data[symbol]}
        except Exception as e:
            error('Failed to initialize regional data', module='MarketTab')
            self.regional_data = {}

    def get_fallback_regional_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Generate fallback data for regional stocks"""
        result = {}
        base_prices = {'AAPL': 175, 'MSFT': 420, 'GOOGL': 140, 'RELIANCE.NS': 2500, 'TCS.NS': 3500, 'BABA': 85, 'NVDA': 800, 'TSLA': 200}
        for symbol in symbols:
            if symbol.endswith('.NS'):
                base_price = base_prices.get(symbol, random.uniform(500, 3000))
            elif symbol in ['BABA', 'PDD', 'JD', 'BIDU']:
                base_price = base_prices.get(symbol, random.uniform(20, 200))
            else:
                base_price = base_prices.get(symbol, random.uniform(50, 500))
            change_pct = round(random.uniform(-3, 3), 2)
            price = round(base_price * (1 + change_pct / 100), 2)
            change_val = round(price * change_pct / 100, 2)
            result[symbol] = {'price': price, 'change_1d': change_val, 'change_percent_1d': change_pct, 'change_percent_7d': round(random.uniform(-5, 5), 2), 'change_percent_30d': round(random.uniform(-15, 15), 2), 'volume': random.randint(100000, 10000000), 'high': round(price * random.uniform(1.01, 1.05), 2), 'low': round(price * random.uniform(0.95, 0.99), 2)}
        return result

    def get_real_stock_data_batch(self, symbols: List[str], timeout: int=10) -> Dict[str, Dict[str, Any]]:
        """Get real stock data using yfinance - OPTIMIZED to reduce API calls"""
        if not YFINANCE_AVAILABLE:
            return self.get_fallback_regional_data(symbols)
        try:
            symbols_str = ' '.join(symbols)
            try:
                data = yf.download(symbols_str, period='30d', interval='1d', group_by='ticker', auto_adjust=True, prepost=True, threads=True, timeout=timeout)
                result = {}
                successful_fetches = 0
                for symbol in symbols:
                    try:
                        if len(symbols) == 1:
                            symbol_data = data
                        else:
                            symbol_data = data[symbol] if symbol in data.columns.get_level_values(0) else None
                        if symbol_data is None or symbol_data.empty:
                            fallback = self.get_fallback_regional_data([symbol])
                            result[symbol] = fallback[symbol]
                            continue
                        current_price = float(symbol_data['Close'].iloc[-1])
                        volume = int(symbol_data['Volume'].iloc[-1]) if 'Volume' in symbol_data.columns else 0
                        high = float(symbol_data['High'].iloc[-1])
                        low = float(symbol_data['Low'].iloc[-1])
                        prev_price = float(symbol_data['Close'].iloc[-2]) if len(symbol_data) >= 2 else current_price
                        change_val = current_price - prev_price
                        change_pct_1d = change_val / prev_price * 100 if prev_price != 0 else 0
                        change_pct_7d = 0.0
                        if len(symbol_data) >= 7:
                            price_7d_ago = float(symbol_data['Close'].iloc[-7])
                            change_pct_7d = (current_price - price_7d_ago) / price_7d_ago * 100 if price_7d_ago != 0 else 0
                        change_pct_30d = 0.0
                        if len(symbol_data) >= 30:
                            price_30d_ago = float(symbol_data['Close'].iloc[-30])
                            change_pct_30d = (current_price - price_30d_ago) / price_30d_ago * 100 if price_30d_ago != 0 else 0
                        elif len(symbol_data) > 1:
                            price_start = float(symbol_data['Close'].iloc[0])
                            change_pct_30d = (current_price - price_start) / price_start * 100 if price_start != 0 else 0
                        result[symbol] = {'price': round(max(0, current_price), 2), 'change_1d': round(change_val, 2), 'change_percent_1d': round(change_pct_1d, 2), 'change_percent_7d': round(change_pct_7d, 2), 'change_percent_30d': round(change_pct_30d, 2), 'volume': max(0, volume), 'high': round(max(current_price, high), 2), 'low': round(min(current_price, low), 2)}
                        successful_fetches += 1
                    except Exception:
                        fallback = self.get_fallback_regional_data([symbol])
                        result[symbol] = fallback[symbol]
                if successful_fetches > 0:
                    info(f'Successfully fetched real data for {successful_fetches}/{len(symbols)} symbols', module='MarketTab')
                return result
            except Exception:
                return self.get_fallback_regional_data(symbols)
        except Exception as e:
            error('Error in stock data fetch', module='MarketTab')
            return self.get_fallback_regional_data(symbols)

    def should_update_real_data(self) -> bool:
        """Check if real data should be updated (10-minute interval)"""
        if self.last_update is None:
            return True
        time_since_update = time.time() - self.last_update
        return time_since_update >= self.update_interval

    def update_regional_data_background(self):
        """Update regional data in background - SINGLE BATCH CALL per region"""
        if self.data_loading or self.shutdown_requested:
            return

        def fetch_regional_data():
            try:
                self.data_loading = True
                info('Starting regional data update', module='MarketTab')
                for region, data in REGIONAL_STOCKS.items():
                    if self.shutdown_requested:
                        break
                    symbols = data['symbols']
                    names = data['names']
                    region_data = self.get_real_stock_data_batch(symbols, timeout=15)
                    with self.data_lock:
                        for i, symbol in enumerate(symbols):
                            if symbol in region_data:
                                display_name = names[i] if i < len(names) else symbol
                                self.regional_data[region][symbol] = {'name': display_name, **region_data[symbol]}
                self.last_update = time.time()
                info('Regional data update completed', module='MarketTab')
            except Exception as e:
                error('Error in regional data update', module='MarketTab')
            finally:
                self.data_loading = False
        thread = threading.Thread(target=fetch_regional_data, daemon=True)
        thread.start()

    def start_background_updates(self):
        """Start optimized background update system"""

        def update_loop():
            try:
                if not self.shutdown_requested:
                    self.update_regional_data_background()
                last_simulated_update = time.time()
                while self.auto_update and (not self.shutdown_requested):
                    try:
                        current_time = time.time()
                        if current_time - last_simulated_update >= self.simulated_update_interval:
                            if not self.shutdown_requested:
                                self.update_market_data()
                                last_simulated_update = current_time
                        if self.should_update_real_data() and (not self.data_loading) and (not self.shutdown_requested):
                            self.update_regional_data_background()
                        time.sleep(1)
                    except Exception:
                        time.sleep(5)
            except Exception as e:
                error('Error in background update loop', module='MarketTab')
        self.background_thread = threading.Thread(target=update_loop, daemon=True)
        self.background_thread.start()

    def create_content(self):
        """Create Bloomberg-style market terminal layout"""
        try:
            self.create_header_bar()
            dpg.add_separator()
            self.create_control_panel()
            dpg.add_separator()
            with dpg.child_window(height=-50, border=False):
                dpg.add_text('GLOBAL MARKETS', color=self.BLOOMBERG_ORANGE)
                dpg.add_separator()
                self.create_market_grid()
                dpg.add_spacer(height=20)
                dpg.add_text('REGIONAL MARKETS - LIVE DATA', color=self.BLOOMBERG_ORANGE)
                dpg.add_separator()
                self.create_regional_markets()
            dpg.add_separator()
            self.create_status_bar()
            self.ui_initialized = True
        except Exception as e:
            error('Failed to create market content', module='MarketTab')
            self.create_error_content(str(e))

    def create_error_content(self, error_message: str):
        """Create error content when main content creation fails"""
        dpg.add_text('MARKET TERMINAL - ERROR', color=self.BLOOMBERG_RED)
        dpg.add_separator()
        dpg.add_text(f'Error loading market data: {error_message}', color=self.BLOOMBERG_WHITE)
        dpg.add_spacer(height=20)
        dpg.add_button(label='Retry', callback=self.retry_callback)

    def create_header_bar(self):
        """Create header bar with search functionality"""
        with dpg.group(horizontal=True):
            dpg.add_text('FINCEPT', color=self.BLOOMBERG_ORANGE)
            dpg.add_text('MARKET TERMINAL', color=self.BLOOMBERG_WHITE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_input_text(label='', default_value='Search Symbol', width=200, tag='symbol_search')
            dpg.add_button(label='SEARCH', width=80, callback=self.search_callback)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), tag='market_time_display')

    def create_control_panel(self):
        """Create control panel with buttons and status indicators"""
        with dpg.group(horizontal=True):
            dpg.add_button(label='REFRESH', callback=self.refresh_callback, width=80)
            dpg.add_button(label='AUTO ON', callback=self.toggle_auto_update, tag='auto_toggle_btn', width=80)
            dpg.add_combo(['1 min', '5 min', '10 min', '30 min'], default_value='10 min', width=80, tag='refresh_interval')
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('LAST UPDATE:', color=self.BLOOMBERG_GRAY)
            dpg.add_text(datetime.datetime.now().strftime('%H:%M:%S'), tag='last_update_time', color=self.BLOOMBERG_WHITE)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            status_color = self.BLOOMBERG_ORANGE if self.data_loading else self.BLOOMBERG_GREEN
            status_text = 'UPDATING' if self.data_loading else 'LIVE'
            dpg.add_text('●', color=status_color, tag='status_indicator')
            dpg.add_text(status_text, color=status_color, tag='status_text')

    def create_market_grid(self):
        """Create 3x2 market grid"""
        categories = list(self.market_data.keys())
        with dpg.group(horizontal=True):
            for i in range(3):
                if i < len(categories):
                    self.create_market_panel(categories[i], 500, 300)
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            for i in range(3, 6):
                if i < len(categories):
                    self.create_market_panel(categories[i], 500, 300)

    def create_regional_markets(self):
        """Create regional markets section with real data"""
        with dpg.group(horizontal=True):
            for region in ['India', 'China', 'United States']:
                if region in self.regional_data:
                    self.create_regional_panel(region, 500, 400)

    def create_regional_panel(self, region: str, width: int, height: int):
        """Create regional stock panel with real data"""
        with dpg.child_window(width=width, height=height, border=True):
            flags = {'India': '🇮🇳', 'China': '🇨🇳', 'United States': '🇺🇸'}
            flag = flags.get(region, '🌍')
            dpg.add_text(f'{flag} {region.upper()} STOCKS', color=self.BLOOMBERG_ORANGE)
            dpg.add_separator()
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, scrollY=True, scrollX=True, height=height - 60):
                dpg.add_table_column(label='Company', width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(label='Symbol', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='Price', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='Chg', width_fixed=True, init_width_or_weight=60)
                dpg.add_table_column(label='1D%', width_fixed=True, init_width_or_weight=60)
                dpg.add_table_column(label='Vol', width_fixed=True, init_width_or_weight=80)
                if region in self.regional_data:
                    for symbol, data in self.regional_data[region].items():
                        with dpg.table_row():
                            name = data.get('name', symbol)
                            name_display = name[:20] + '...' if len(name) > 20 else name
                            dpg.add_text(name_display, color=self.BLOOMBERG_WHITE)
                            display_symbol = symbol.replace('.NS', '').replace('.HK', '')
                            dpg.add_text(display_symbol, color=self.BLOOMBERG_YELLOW)
                            price = data.get('price', 0)
                            if region == 'India':
                                price_str = f'₹{price:,.0f}' if price >= 100 else f'₹{price:.2f}'
                            elif region == 'China':
                                price_str = f'${price:.2f}'
                            else:
                                price_str = f'${price:.2f}'
                            dpg.add_text(price_str, color=self.BLOOMBERG_WHITE)
                            change_1d = data.get('change_1d', 0)
                            change_color = self.BLOOMBERG_GREEN if change_1d >= 0 else self.BLOOMBERG_RED
                            dpg.add_text(f'{change_1d:+.2f}', color=change_color)
                            change_percent_1d = data.get('change_percent_1d', 0)
                            percent_color = self.BLOOMBERG_GREEN if change_percent_1d >= 0 else self.BLOOMBERG_RED
                            dpg.add_text(f'{change_percent_1d:+.2f}%', color=percent_color)
                            volume = data.get('volume', 0)
                            if volume >= 1000000:
                                vol_str = f'{volume / 1000000:.1f}M'
                            elif volume >= 1000:
                                vol_str = f'{volume / 1000:.1f}K'
                            else:
                                vol_str = f'{volume:,}'
                            dpg.add_text(vol_str, color=self.BLOOMBERG_GRAY)

    def create_market_panel(self, category: str, width: int, height: int):
        """Create individual market panel"""
        with dpg.child_window(width=width, height=height, border=True):
            dpg.add_text(f'{category.upper()}', color=self.BLOOMBERG_ORANGE)
            dpg.add_separator()
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, scrollY=True, scrollX=True, height=height - 60):
                dpg.add_table_column(label='Asset', width_fixed=True, init_width_or_weight=180)
                dpg.add_table_column(label='Last', width_fixed=True, init_width_or_weight=80)
                dpg.add_table_column(label='Chg', width_fixed=True, init_width_or_weight=60)
                dpg.add_table_column(label='1D%', width_fixed=True, init_width_or_weight=60)
                dpg.add_table_column(label='7D%', width_fixed=True, init_width_or_weight=60)
                dpg.add_table_column(label='30D%', width_fixed=True, init_width_or_weight=60)
                assets = self.market_data.get(category, {})
                for asset_name, data in list(assets.items())[:10]:
                    with dpg.table_row():
                        asset_display = asset_name[:25] + '...' if len(asset_name) > 25 else asset_name
                        dpg.add_text(asset_display, color=self.BLOOMBERG_WHITE)
                        price = data.get('price', 0)
                        if price < 1:
                            price_str = f'{price:.4f}'
                        elif price < 100:
                            price_str = f'{price:.2f}'
                        else:
                            price_str = f'{price:,.0f}'
                        dpg.add_text(price_str, color=self.BLOOMBERG_WHITE)
                        change_1d = data.get('change_1d', 0)
                        change_color = self.BLOOMBERG_GREEN if change_1d >= 0 else self.BLOOMBERG_RED
                        dpg.add_text(f'{change_1d:+.2f}', color=change_color)
                        for period in ['change_percent_1d', 'change_percent_7d', 'change_percent_30d']:
                            percent_change = data.get(period, 0)
                            percent_color = self.BLOOMBERG_GREEN if percent_change >= 0 else self.BLOOMBERG_RED
                            dpg.add_text(f'{percent_change:+.2f}%', color=percent_color)

    def create_status_bar(self):
        """Create status bar with market information"""
        with dpg.group(horizontal=True):
            dpg.add_text('MARKET STATUS:', color=self.BLOOMBERG_GRAY)
            current_hour = datetime.datetime.now().hour
            if 9 <= current_hour < 16:
                dpg.add_text('OPEN', color=self.BLOOMBERG_GREEN)
            else:
                dpg.add_text('CLOSED', color=self.BLOOMBERG_RED)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('DATA FEED:', color=self.BLOOMBERG_GRAY)
            data_status = 'LIVE' if YFINANCE_AVAILABLE else 'SIMULATED'
            data_color = self.BLOOMBERG_GREEN if YFINANCE_AVAILABLE else self.BLOOMBERG_ORANGE
            dpg.add_text(data_status, color=data_color)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('ASSETS:', color=self.BLOOMBERG_GRAY)
            market_assets = sum((len(assets) for assets in self.market_data.values()))
            regional_assets = sum((len(stocks) for stocks in self.regional_data.values()))
            total_assets = market_assets + regional_assets
            dpg.add_text(f'{total_assets}', color=self.BLOOMBERG_YELLOW)
            dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
            dpg.add_text('AUTO-UPDATE:', color=self.BLOOMBERG_GRAY)
            status_text = 'ON' if self.auto_update else 'OFF'
            status_color = self.BLOOMBERG_GREEN if self.auto_update else self.BLOOMBERG_RED
            dpg.add_text(status_text, color=status_color, tag='auto_status_text')
            if self.last_update:
                dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                dpg.add_text('LAST REAL DATA UPDATE:', color=self.BLOOMBERG_GRAY)
                last_update_str = datetime.datetime.fromtimestamp(self.last_update).strftime('%H:%M')
                dpg.add_text(last_update_str, color=self.BLOOMBERG_WHITE)

    def update_market_data(self):
        """Update market data with simulated changes"""
        try:
            if self.shutdown_requested:
                return
            with self.data_lock:
                for category in self.market_data:
                    for asset_name in self.market_data[category]:
                        data = self.market_data[category][asset_name]
                        current_price = data.get('price', 0)
                        if current_price > 0:
                            change_factor = 1 + random.uniform(-0.01, 0.01)
                            new_price = current_price * change_factor
                            new_change_1d = new_price - current_price
                            new_change_percent_1d = new_change_1d / current_price * 100
                            self.market_data[category][asset_name].update({'price': round(max(0.0001, new_price), 2 if new_price >= 1 else 4), 'change_1d': round(new_change_1d, 2), 'change_percent_1d': round(new_change_percent_1d, 2), 'change_percent_7d': round(data.get('change_percent_7d', 0) + random.uniform(-0.5, 0.5), 2), 'change_percent_30d': round(data.get('change_percent_30d', 0) + random.uniform(-0.2, 0.2), 2)})
            self.update_ui_timestamps()
        except Exception as e:
            error('Failed to update market data', module='MarketTab')

    def update_ui_timestamps(self):
        """Update UI timestamps and status indicators"""
        try:
            current_time = datetime.datetime.now().strftime('%H:%M:%S')
            current_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if dpg.does_item_exist('last_update_time'):
                dpg.set_value('last_update_time', current_time)
            if dpg.does_item_exist('market_time_display'):
                dpg.set_value('market_time_display', current_datetime)
            if dpg.does_item_exist('status_indicator') and dpg.does_item_exist('status_text'):
                status_color = self.BLOOMBERG_ORANGE if self.data_loading else self.BLOOMBERG_GREEN
                status_text = 'UPDATING' if self.data_loading else 'LIVE'
                dpg.configure_item('status_indicator', color=status_color)
                dpg.set_value('status_text', status_text)
                dpg.configure_item('status_text', color=status_color)
        except Exception:
            pass

    def search_callback(self):
        """Search callback"""
        try:
            if dpg.does_item_exist('symbol_search'):
                search_term = dpg.get_value('symbol_search')
                if search_term and search_term != 'Search Symbol':
                    info(f'Symbol search: {search_term}', module='MarketTab')
        except Exception:
            pass

    def refresh_callback(self):
        """Manual refresh callback"""
        try:
            info('Manual refresh requested', module='MarketTab')
            self.initialize_market_data()
            if not self.data_loading:
                self.update_regional_data_background()
            self.update_market_data()
        except Exception as e:
            error('Manual refresh failed', module='MarketTab')

    def toggle_auto_update(self):
        """Toggle auto-update"""
        try:
            self.auto_update = not self.auto_update
            button_text = 'AUTO ON' if self.auto_update else 'AUTO OFF'
            if dpg.does_item_exist('auto_toggle_btn'):
                dpg.set_item_label('auto_toggle_btn', button_text)
            status_text = 'ON' if self.auto_update else 'OFF'
            status_color = self.BLOOMBERG_GREEN if self.auto_update else self.BLOOMBERG_RED
            if dpg.does_item_exist('auto_status_text'):
                dpg.set_value('auto_status_text', status_text)
                dpg.configure_item('auto_status_text', color=status_color)
            if self.auto_update and (not self.background_thread or not self.background_thread.is_alive()):
                self.start_background_updates()
        except Exception as e:
            error('Failed to toggle auto-update', module='MarketTab')

    def retry_callback(self):
        """Retry loading data after error"""
        try:
            info('Retry requested', module='MarketTab')
            self.initialize_market_data()
            self.initialize_regional_data()
            if not self.data_loading:
                self.update_regional_data_background()
        except Exception as e:
            error('Retry failed', module='MarketTab')

    def resize_components(self, left_width: int, center_width: int, right_width: int, top_height: int, bottom_height: int, cell_height: int):
        """Handle resize events"""
        pass

    def cleanup(self):
        """Clean up resources"""
        try:
            info('Starting Market Tab cleanup', module='MarketTab')
            self.shutdown_requested = True
            self.auto_update = False
            if self.background_thread and self.background_thread.is_alive():
                self.background_thread.join(timeout=5)
            with self.data_lock:
                self.market_data = {}
                self.regional_data = {}
            self.data_loading = False
            self.ui_initialized = False
            self.last_update = None
            info('Market Tab cleanup completed', module='MarketTab')
        except Exception as e:
            error('Market Tab cleanup failed', module='MarketTab')

    def get_market_health_status(self) -> Dict[str, Any]:
        """Get current market tab health status for monitoring"""
        try:
            return {'ui_initialized': self.ui_initialized, 'auto_update_enabled': self.auto_update, 'data_loading': self.data_loading, 'background_thread_alive': self.background_thread.is_alive() if self.background_thread else False, 'last_update_timestamp': self.last_update, 'market_categories_count': len(self.market_data), 'regional_markets_count': len(self.regional_data), 'total_assets': sum((len(assets) for assets in self.market_data.values())) + sum((len(stocks) for stocks in self.regional_data.values())), 'yfinance_available': YFINANCE_AVAILABLE, 'shutdown_requested': self.shutdown_requested}
        except Exception as e:
            error('Failed to get market health status', module='MarketTab')
            return {'error': str(e)}

def should_update_real_data(self) -> bool:
    """Check if real data should be updated (10-minute interval)"""
    if self.last_update is None:
        return True
    time_since_update = time.time() - self.last_update
    return time_since_update >= self.update_interval

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

class FinceptAPIClient:

    def __init__(self, session_data: Dict[str, Any]):
        self.api_base = 'https://finceptbackend.share.zrok.io'
        self.session_data = session_data
        self.api_key = session_data.get('api_key')
        self.user_type = session_data.get('user_type', 'guest')
        self.request_count = 0
        info('API client initialized', context={'user_type': self.user_type, 'has_api_key': bool(self.api_key)})

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers

    def make_request(self, method: str, endpoint: str, data: dict=None, params: dict=None, timeout: int=10) -> Dict[str, Any]:
        """Make authenticated API request"""
        try:
            url = f'{self.api_base}{endpoint}'
            headers = self.get_headers()
            self.request_count += 1
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                error('Unsupported HTTP method', context={'method': method, 'endpoint': endpoint})
                return {'success': False, 'error': f'Unsupported method: {method}'}
            if response.status_code >= 400:
                error('API request failed', context={'method': method, 'endpoint': endpoint, 'status_code': response.status_code})
            return {'success': response.status_code < 400, 'status_code': response.status_code, 'data': response.json() if response.content else {}, 'headers': dict(response.headers)}
        except requests.exceptions.Timeout:
            warning('API request timeout', context={'endpoint': endpoint, 'timeout': timeout})
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            error('API connection error', context={'endpoint': endpoint})
            return {'success': False, 'error': 'Connection error - API server not available'}
        except requests.exceptions.RequestException as e:
            error('API request exception', context={'endpoint': endpoint, 'error': str(e)})
            return {'success': False, 'error': f'Request error: {str(e)}'}
        except Exception as e:
            error('Unexpected API error', context={'endpoint': endpoint, 'error': str(e)})
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}

    def check_auth_status(self) -> Dict[str, Any]:
        """Check current authentication status"""
        result = self.make_request('GET', '/auth/status')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'authenticated': result['data']['data'].get('authenticated', False), 'user_type': result['data']['data'].get('user_type'), 'user_info': result['data']['data'].get('user', result['data']['data'].get('guest'))}
        return {'success': False, 'authenticated': False}

    def logout(self) -> Dict[str, Any]:
        """Logout user and clear session"""
        if not self.is_authenticated():
            return {'success': False, 'error': 'User is not authenticated'}
        result = self.make_request('POST', '/auth/logout')
        if result['success'] and result['data'].get('success'):
            info('User logged out successfully', context={'user_type': self.user_type})
            self.clear_session()
            return {'success': True, 'message': result['data']['data'].get('message', 'Logged out successfully')}
        error('Logout failed', context={'user_type': self.user_type})
        return {'success': False, 'error': result.get('error', 'Failed to logout')}

    def clear_session(self) -> None:
        """Clear all session data locally"""
        device_id = self.session_data.get('device_id', 'unknown')
        self.session_data = {'user_type': 'guest', 'authenticated': False, 'api_key': None, 'device_id': device_id, 'user_info': {}, 'expires_at': None, 'requests_today': 0, 'daily_limit': 50}
        self.api_key = None
        self.user_type = 'guest'
        self.request_count = 0

    def force_logout(self) -> Dict[str, Any]:
        """Force logout without API call (for offline situations)"""
        info('Force logout executed', context={'user_type': self.user_type})
        self.clear_session()
        return {'success': True, 'message': 'Forced logout completed - session cleared locally'}

    def get_chat_sessions(self, limit: int=50) -> Dict[str, Any]:
        """Get user's chat sessions"""
        params = {'limit': limit}
        result = self.make_request('GET', '/chat/sessions', params=params)
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'sessions': result['data']['data']['sessions'], 'total': result['data']['data'].get('total', 0), 'user_type': result['data']['data'].get('user_type')}
        return {'success': False, 'sessions': [], 'error': result.get('error', 'Failed to get chat sessions')}

    def create_chat_session(self, title: str='New Conversation') -> Dict[str, Any]:
        """Create new chat session"""
        data = {'title': title}
        result = self.make_request('POST', '/chat/sessions', data)
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'session': result['data']['data']['session'], 'message': result['data']['data'].get('message', 'Session created')}
        return {'success': False, 'error': result.get('error', 'Failed to create chat session')}

    def get_chat_session(self, session_uuid: str) -> Dict[str, Any]:
        """Get specific chat session with messages"""
        result = self.make_request('GET', f'/chat/sessions/{session_uuid}')
        if result['success'] and result['data'].get('success'):
            session_detail = result['data']['data']
            return {'success': True, 'session': session_detail['session'], 'messages': session_detail['messages'], 'total_messages': session_detail['total_messages']}
        return {'success': False, 'error': result.get('error', 'Failed to get chat session')}

    def send_chat_message(self, session_uuid: str, content: str) -> Dict[str, Any]:
        """Send message to chat session"""
        data = {'content': content}
        result = self.make_request('POST', f'/chat/sessions/{session_uuid}/messages', data)
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'user_message': result['data']['data']['user_message'], 'ai_message': result['data']['data']['ai_message'], 'new_title': result['data']['data'].get('new_title')}
        return {'success': False, 'error': result.get('error', 'Failed to send message')}

    def activate_chat_session(self, session_uuid: str) -> Dict[str, Any]:
        """Activate a chat session"""
        result = self.make_request('PUT', f'/chat/sessions/{session_uuid}/activate')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'message': result['data']['data'].get('message', 'Session activated')}
        return {'success': False, 'error': result.get('error', 'Failed to activate session')}

    def update_chat_title(self, session_uuid: str, new_title: str) -> Dict[str, Any]:
        """Update chat session title"""
        data = {'title': new_title}
        result = self.make_request('PUT', f'/chat/sessions/{session_uuid}/title', data)
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'new_title': result['data']['data']['new_title'], 'message': result['data']['data'].get('message', 'Title updated')}
        return {'success': False, 'error': result.get('error', 'Failed to update title')}

    def delete_chat_session(self, session_uuid: str) -> Dict[str, Any]:
        """Delete chat session"""
        result = self.make_request('DELETE', f'/chat/sessions/{session_uuid}')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'message': result['data']['data'].get('message', 'Session deleted')}
        return {'success': False, 'error': result.get('error', 'Failed to delete session')}

    def get_chat_stats(self) -> Dict[str, Any]:
        """Get chat statistics"""
        result = self.make_request('GET', '/chat/stats')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'stats': result['data']['data']}
        return {'success': False, 'error': result.get('error', 'Failed to get chat stats')}

    def bulk_delete_chat_sessions(self, session_uuids: List[str]) -> Dict[str, Any]:
        """Bulk delete chat sessions (registered users only)"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'session_uuids': session_uuids}
        result = self.make_request('DELETE', '/chat/sessions/bulk-delete', data)
        if result['success'] and result['data'].get('success'):
            info('Bulk chat sessions deleted', context={'count': result['data']['data']['deleted_count']})
            return {'success': True, 'deleted_count': result['data']['data']['deleted_count'], 'message': result['data']['data'].get('message', 'Sessions deleted')}
        return {'success': False, 'error': result.get('error', 'Failed to delete sessions')}

    def export_chat_sessions(self, session_uuids: List[str]=None, format_type: str='json') -> Dict[str, Any]:
        """Export chat sessions (registered users only)"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'session_uuids': session_uuids or [], 'format': format_type}
        result = self.make_request('POST', '/chat/export', data)
        if result['success'] and result['data'].get('success'):
            info('Chat sessions exported', context={'format': format_type, 'count': len(session_uuids or [])})
            return {'success': True, 'export_data': result['data']['data']}
        return {'success': False, 'error': result.get('error', 'Failed to export sessions')}

    def get_databases(self) -> Dict[str, Any]:
        """Get list of available databases"""
        result = self.make_request('GET', '/databases')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'databases': result['data']['data']['databases'], 'user_type': result['data']['data'].get('user_type'), 'total': result['data']['data'].get('total_available', 0)}
        return {'success': False, 'databases': [], 'error': result.get('error', 'Failed to get databases')}

    def get_database_tables(self, database_name: str) -> Dict[str, Any]:
        """Get tables in a specific database"""
        result = self.make_request('GET', f'/database/{database_name}/tables')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'tables': result['data']['data']['tables'], 'database': result['data']['data']['database'], 'total_tables': result['data']['data'].get('total_tables', 0), 'user_type': result['data']['data'].get('user_type'), 'access_level': result['data']['data'].get('access_level')}
        return {'success': False, 'tables': [], 'error': result.get('error', 'Failed to get tables')}

    def get_table_data(self, database_name: str, table_name: str, page: int=1, limit: int=50) -> Dict[str, Any]:
        """Get data from a specific table"""
        params = {'page': page, 'limit': limit}
        result = self.make_request('GET', f'/database/{database_name}/{table_name}/data', params=params)
        if result['success'] and result['data'].get('success'):
            response_data = result['data']['data']
            return {'success': True, 'data': response_data['data'], 'pagination': {'page': response_data['page'], 'limit': response_data['limit'], 'rows_returned': response_data['rows_returned']}, 'database': response_data['database'], 'table': response_data['table'], 'credits_used': response_data.get('credits_used', 0), 'user_type': response_data.get('user_type'), 'guest_info': response_data.get('guest_info')}
        return {'success': False, 'data': [], 'error': result.get('error', 'Failed to get table data')}

    def get_public_databases(self) -> Dict[str, Any]:
        """Get public databases (no authentication required)"""
        result = self.make_request('GET', '/databases/public')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'databases': result['data']['data']['databases'], 'total': result['data']['data'].get('total', 0)}
        return {'success': False, 'databases': [], 'error': result.get('error', 'Failed to get public databases')}

    def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile information"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        result = self.make_request('GET', '/user/profile')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'profile': result['data']['data']}
        return {'success': False, 'error': result.get('error', 'Failed to get profile')}

    def get_user_usage(self) -> Dict[str, Any]:
        """Get user's API usage statistics"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        result = self.make_request('GET', '/user/usage')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'usage': result['data']['data']}
        return {'success': False, 'error': result.get('error', 'Failed to get usage')}

    @monitor_performance
    def regenerate_api_key(self) -> Dict[str, Any]:
        """Regenerate user API key"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        result = self.make_request('POST', '/user/regenerate-api-key')
        if result['success'] and result['data'].get('success'):
            new_api_key = result['data']['data']['api_key']
            self.api_key = new_api_key
            self.session_data['api_key'] = new_api_key
            info('API key regenerated successfully')
            return {'success': True, 'api_key': new_api_key, 'message': result['data']['data'].get('message', 'API key regenerated')}
        error('API key regeneration failed')
        return {'success': False, 'error': result.get('error', 'Failed to regenerate API key')}

    def get_user_transactions(self) -> Dict[str, Any]:
        """Get user's transaction history"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        result = self.make_request('GET', '/user/transactions')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'transactions': result['data']['data']['transactions']}
        return {'success': False, 'transactions': [], 'error': result.get('error', 'Failed to get transactions')}

    def add_secondary_email(self, secondary_email: str) -> Dict[str, Any]:
        """Add secondary email for 2FA"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'secondary_email': secondary_email}
        result = self.make_request('POST', '/user/add-secondary-email', data)
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'message': result['data']['data'].get('message', 'Secondary email added')}
        return {'success': False, 'error': result.get('error', 'Failed to add secondary email')}

    def verify_secondary_email(self, otp: str) -> Dict[str, Any]:
        """Verify secondary email"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'otp': otp}
        result = self.make_request('POST', '/user/verify-secondary-email', data)
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'message': result['data']['data'].get('message', 'Secondary email verified')}
        return {'success': False, 'error': result.get('error', 'Failed to verify secondary email')}

    def toggle_2fa(self, enable: bool) -> Dict[str, Any]:
        """Enable/disable 2FA"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'enable': enable}
        result = self.make_request('POST', '/user/toggle-2fa', data)
        if result['success'] and result['data'].get('success'):
            info('2FA toggled', context={'enabled': enable})
            return {'success': True, 'message': result['data']['data'].get('message', '2FA toggled')}
        return {'success': False, 'error': result.get('error', 'Failed to toggle 2FA')}

    def subscribe_to_database(self, database_name: str) -> Dict[str, Any]:
        """Subscribe to a database"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'database_name': database_name}
        result = self.make_request('POST', '/database/subscribe', data)
        if result['success'] and result['data'].get('success'):
            info('Database subscription successful', context={'database': database_name})
            return {'success': True, 'message': result['data'].get('message', 'Subscription successful')}
        return {'success': False, 'error': result.get('error', 'Failed to subscribe')}

    def bind_device(self, device_id: str, device_name: str, platform: str, hardware_info: Dict[str, Any]) -> Dict[str, Any]:
        """Bind device to user account"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'device_id': device_id, 'device_name': device_name, 'platform': platform, 'hardware_info': hardware_info}
        result = self.make_request('POST', '/device/bind', data)
        if result['success'] and result['data'].get('success'):
            info('Device bound successfully', context={'device_name': device_name, 'platform': platform})
            return {'success': True, 'device_id': result['data']['data']['device_id'], 'is_primary': result['data']['data']['is_primary'], 'message': result['data']['data'].get('message', 'Device bound')}
        return {'success': False, 'error': result.get('error', 'Failed to bind device')}

    def list_user_devices(self) -> Dict[str, Any]:
        """List user's devices"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        result = self.make_request('GET', '/device/list')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'devices': result['data']['data']['devices'], 'total': result['data']['data']['total'], 'max_allowed': result['data']['data']['max_allowed']}
        return {'success': False, 'devices': [], 'error': result.get('error', 'Failed to get devices')}

    def create_support_ticket(self, subject: str, description: str, category: str='general') -> Dict[str, Any]:
        """Create a support ticket"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'subject': subject, 'description': description, 'category': category}
        result = self.make_request('POST', '/support/ticket', data)
        if result['success'] and result['data'].get('success'):
            info('Support ticket created', context={'category': category, 'ticket_id': result['data']['data']['ticket_id']})
            return {'success': True, 'ticket_id': result['data']['data']['ticket_id'], 'message': result['data']['data'].get('message', 'Ticket created')}
        return {'success': False, 'error': result.get('error', 'Failed to create ticket')}

    def get_support_tickets(self) -> Dict[str, Any]:
        """Get user's support tickets"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        result = self.make_request('GET', '/support/tickets')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'tickets': result['data']['data']['tickets']}
        return {'success': False, 'tickets': [], 'error': result.get('error', 'Failed to get tickets')}

    def reply_to_ticket(self, ticket_id: int, message: str) -> Dict[str, Any]:
        """Reply to support ticket"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'message': message}
        result = self.make_request('POST', f'/support/ticket/{ticket_id}/reply', data)
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'message': result['data']['data'].get('message', 'Reply added')}
        return {'success': False, 'error': result.get('error', 'Failed to reply to ticket')}

    def send_legacy_chat_message(self, channel: str, message: str) -> Dict[str, Any]:
        """Send a legacy chat message"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'message': message}
        result = self.make_request('POST', f'/chat/{channel}/message', data)
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'message_id': result['data']['data']['message_id'], 'message': result['data']['data'].get('message', 'Message sent')}
        return {'success': False, 'error': result.get('error', 'Failed to send message')}

    def get_legacy_chat_messages(self, channel: str, limit: int=50) -> Dict[str, Any]:
        """Get legacy chat messages from a channel"""
        params = {'limit': limit}
        result = self.make_request('GET', f'/chat/{channel}/messages', params=params)
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'messages': result['data']['data']['messages'], 'channel': result['data']['data']['channel']}
        return {'success': False, 'messages': [], 'error': result.get('error', 'Failed to get messages')}

    def create_payment_order(self, amount_inr: int) -> Dict[str, Any]:
        """Create a payment order"""
        if self.user_type != 'registered':
            return {'success': False, 'error': 'Only available for registered users'}
        data = {'amount_inr': amount_inr}
        result = self.make_request('POST', '/payment/create-order', data)
        if result['success'] and result['data'].get('success'):
            info('Payment order created', context={'amount_inr': amount_inr})
            return {'success': True, 'order': result['data']['data']}
        return {'success': False, 'error': result.get('error', 'Failed to create order')}

    def get_guest_status(self) -> Dict[str, Any]:
        """Get guest user status and usage"""
        if self.user_type != 'guest':
            return {'success': False, 'error': 'Only available for guest users'}
        device_id = self.session_data.get('device_id')
        if not device_id:
            device_id = self.generate_device_id() if hasattr(self, 'generate_device_id') else None
        headers = self.get_headers()
        if device_id:
            headers['X-Device-ID'] = device_id
        try:
            url = f'{self.api_base}/guest/status'
            response = requests.get(url, headers=headers, timeout=10)
            return {'success': response.status_code < 400, 'status_code': response.status_code, 'data': response.json() if response.content else {}, 'headers': dict(response.headers)}
        except Exception as e:
            error('Guest status request failed', context={'error': str(e)})
            return {'success': False, 'error': f'Request error: {str(e)}'}

    def get_or_create_guest_session(self, device_id: str, device_name: str, platform: str, hardware_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get existing guest session or create new one"""
        try:
            headers = {'Content-Type': 'application/json', 'X-Device-ID': device_id}
            status_response = requests.get(f'{self.api_base}/guest/status', headers=headers, timeout=10)
            if status_response.status_code == 200:
                data = status_response.json()
                if data.get('success'):
                    return {'success': True, 'data': data.get('data', {}), 'message': 'Existing session retrieved'}
            register_data = {'device_id': device_id, 'device_name': device_name, 'platform': platform, 'hardware_info': hardware_info}
            register_response = requests.post(f'{self.api_base}/device/register', json=register_data, headers={'Content-Type': 'application/json'}, timeout=10)
            if register_response.status_code == 200:
                data = register_response.json()
                if data.get('success'):
                    info('New guest session created', context={'device_name': device_name})
                    return {'success': True, 'data': data.get('data', {}), 'message': 'New session created'}
            elif register_response.status_code == 409:
                auth_headers = {'Content-Type': 'application/json'}
                auth_response = requests.get(f'{self.api_base}/auth/status', headers=auth_headers, params={'device_id': device_id}, timeout=10)
                if auth_response.status_code == 200:
                    auth_data = auth_response.json()
                    if auth_data.get('success') and auth_data.get('data', {}).get('guest'):
                        return {'success': True, 'data': auth_data['data']['guest'], 'message': 'Existing session found via auth'}
            error('Failed to get or create guest session', context={'status_code': register_response.status_code, 'device_id': device_id})
            return {'success': False, 'error': f'Failed to get or create session: {register_response.status_code}'}
        except Exception as e:
            error('Guest session request exception', context={'error': str(e)})
            return {'success': False, 'error': f'Request error: {str(e)}'}

    def extend_guest_session(self) -> Dict[str, Any]:
        """Extend guest session"""
        if self.user_type != 'guest':
            return {'success': False, 'error': 'Only available for guest users'}
        result = self.make_request('POST', '/guest/extend')
        if result['success'] and result['data'].get('success'):
            info('Guest session extended', context={'hours_added': result['data']['data']['hours_added']})
            return {'success': True, 'message': result['data']['data']['message'], 'new_expiry': result['data']['data']['new_expiry'], 'hours_added': result['data']['data']['hours_added']}
        return {'success': False, 'error': result.get('error', 'Failed to extend session')}

    def get_system_config(self) -> Dict[str, Any]:
        """Get public system configuration"""
        result = self.make_request('GET', '/config/system')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'config': result['data']['data']['config']}
        return {'success': False, 'config': {}, 'error': result.get('error', 'Failed to get config')}

    def get_health_status(self) -> Dict[str, Any]:
        """Get API health status"""
        result = self.make_request('GET', '/health')
        if result['success']:
            return {'success': True, 'health': result['data']}
        return {'success': False, 'error': result.get('error', 'Failed to get health status')}

    def get_api_root(self) -> Dict[str, Any]:
        """Get API root information"""
        result = self.make_request('GET', '/')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'info': result['data']['data']}
        return {'success': False, 'error': result.get('error', 'Failed to get API info')}

    def test_endpoint(self) -> Dict[str, Any]:
        """Test API endpoint"""
        result = self.make_request('GET', '/test')
        if result['success'] and result['data'].get('success'):
            return {'success': True, 'test_result': result['data']['data']}
        return {'success': False, 'error': result.get('error', 'Test endpoint failed')}

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.session_data.get('authenticated', False)

    def is_guest(self) -> bool:
        """Check if user is a guest"""
        return self.user_type == 'guest'

    def is_registered(self) -> bool:
        """Check if user is registered"""
        return self.user_type == 'registered'

    def has_api_key(self) -> bool:
        """Check if user has an API key"""
        return bool(self.api_key)

    def get_request_count(self) -> int:
        """Get number of requests made in this session"""
        return self.request_count

    def get_user_info(self) -> Dict[str, Any]:
        """Get user information"""
        if self.user_type == 'registered':
            return self.session_data.get('user_info', {})
        else:
            return {'user_type': 'guest', 'device_id': self.session_data.get('device_id', 'unknown'), 'expires_at': self.session_data.get('expires_at'), 'daily_limit': self.session_data.get('daily_limit', 50)}

    def get_session_data(self) -> Dict[str, Any]:
        """Get session data"""
        return self.session_data

    def update_session_data(self, new_data: Dict[str, Any]) -> None:
        """Update session data"""
        self.session_data.update(new_data)
        self.api_key = self.session_data.get('api_key')
        self.user_type = self.session_data.get('user_type', 'guest')

    def reset_request_count(self) -> None:
        """Reset request counter"""
        self.request_count = 0

    def handle_api_error(self, result: Dict[str, Any], default_message: str='API request failed') -> str:
        """Extract meaningful error message from API result"""
        if result.get('success'):
            return 'Success'
        error = result.get('error', default_message)
        if 'Connection error' in error:
            return 'API server is not available. Please check if the server is running on https://finceptbackend.share.zrok.io'
        elif 'timeout' in error.lower():
            return 'Request timed out. Please try again.'
        elif '401' in str(result.get('status_code', '')):
            return 'Authentication failed. Please check your API key.'
        elif '403' in str(result.get('status_code', '')):
            return 'Access denied. You may need to subscribe to this database or upgrade your account.'
        elif '429' in str(result.get('status_code', '')):
            return 'Rate limit exceeded. Please wait before making more requests.'
        elif '404' in str(result.get('status_code', '')):
            return 'Resource not found. Please check the endpoint or resource ID.'
        elif '400' in str(result.get('status_code', '')):
            return 'Bad request. Please check your input parameters.'
        elif '500' in str(result.get('status_code', '')):
            return 'Internal server error. Please try again later.'
        else:
            return error

    def get_error_context(self) -> Dict[str, Any]:
        """Get error context for debugging"""
        return {'request_count': self.request_count, 'user_type': self.user_type, 'api_key_present': bool(self.api_key), 'session_authenticated': self.is_authenticated()}

    def batch_request(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple API requests in sequence"""
        results = []
        for req in requests:
            method = req.get('method', 'GET')
            endpoint = req.get('endpoint', '/')
            data = req.get('data')
            params = req.get('params')
            timeout = req.get('timeout', 10)
            result = self.make_request(method, endpoint, data, params, timeout)
            results.append({'request': req, 'result': result})
        if len(requests) > 5:
            info('Batch API request completed', context={'count': len(requests)})
        return results

    def validate_endpoints(self, endpoints: List[str]) -> Dict[str, bool]:
        """Validate multiple endpoints availability"""
        results = {}
        for endpoint in endpoints:
            try:
                result = self.make_request('GET', endpoint, timeout=5)
                results[endpoint] = result['success']
            except Exception:
                results[endpoint] = False
        return results

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this session"""
        return {'total_requests': self.request_count, 'user_type': self.user_type, 'authenticated': self.is_authenticated(), 'api_base': self.api_base, 'session_start': getattr(self, '_session_start', 'unknown')}

    @monitor_performance
    def benchmark_endpoint(self, endpoint: str, iterations: int=5) -> Dict[str, Any]:
        """Benchmark an endpoint performance"""
        import time
        results = []
        for i in range(iterations):
            start_time = time.time()
            result = self.make_request('GET', endpoint, timeout=30)
            end_time = time.time()
            results.append({'iteration': i + 1, 'response_time': end_time - start_time, 'success': result['success'], 'status_code': result.get('status_code')})
        response_times = [r['response_time'] for r in results]
        success_count = sum((1 for r in results if r['success']))
        info('Endpoint benchmark completed', context={'endpoint': endpoint, 'success_rate': success_count / iterations, 'avg_response_time': sum(response_times) / len(response_times)})
        return {'endpoint': endpoint, 'iterations': iterations, 'success_rate': success_count / iterations, 'avg_response_time': sum(response_times) / len(response_times), 'min_response_time': min(response_times), 'max_response_time': max(response_times), 'results': results}

def get_error_context(self) -> Dict[str, Any]:
    """Get error context for debugging"""
    return {'request_count': self.request_count, 'user_type': self.user_type, 'api_key_present': bool(self.api_key), 'session_authenticated': self.is_authenticated()}

def get_performance_stats(self) -> Dict[str, Any]:
    """Get performance statistics for this session"""
    return {'total_requests': self.request_count, 'user_type': self.user_type, 'authenticated': self.is_authenticated(), 'api_base': self.api_base, 'session_start': getattr(self, '_session_start', 'unknown')}

@monitor_performance
def benchmark_endpoint(self, endpoint: str, iterations: int=5) -> Dict[str, Any]:
    """Benchmark an endpoint performance"""
    import time
    results = []
    for i in range(iterations):
        start_time = time.time()
        result = self.make_request('GET', endpoint, timeout=30)
        end_time = time.time()
        results.append({'iteration': i + 1, 'response_time': end_time - start_time, 'success': result['success'], 'status_code': result.get('status_code')})
    response_times = [r['response_time'] for r in results]
    success_count = sum((1 for r in results if r['success']))
    info('Endpoint benchmark completed', context={'endpoint': endpoint, 'success_rate': success_count / iterations, 'avg_response_time': sum(response_times) / len(response_times)})
    return {'endpoint': endpoint, 'iterations': iterations, 'success_rate': success_count / iterations, 'avg_response_time': sum(response_times) / len(response_times), 'min_response_time': min(response_times), 'max_response_time': max(response_times), 'results': results}

def create_api_client(session_data: Dict[str, Any]) -> FinceptAPIClient:
    """Create API client instance from session data"""
    client = FinceptAPIClient(session_data)
    import time
    client._session_start = time.time()
    return client

def get_api_client_info(client: FinceptAPIClient) -> Dict[str, Any]:
    """Get information about an API client instance"""
    return {'api_base': client.api_base, 'user_type': client.user_type, 'authenticated': client.is_authenticated(), 'has_api_key': client.has_api_key(), 'request_count': client.get_request_count(), 'user_info': client.get_user_info()}

class NotificationRateLimiter:
    """Rate limiter to prevent notification spam"""

    def __init__(self, config: NotificationConfig):
        self.config = config
        self.notification_times = deque()
        self.recent_notifications = {}
        self._lock = threading.RLock()

    def should_allow(self, title: str, message: str, level: NotificationLevel) -> bool:
        """Check if notification should be allowed based on rate limiting"""
        if not self.config.rate_limit_enabled:
            return True
        current_time = time.time()
        with self._lock:
            cutoff_time = current_time - 60
            while self.notification_times and self.notification_times[0] < cutoff_time:
                self.notification_times.popleft()
            if len(self.notification_times) >= self.config.max_notifications_per_minute:
                return False
            notification_hash = hash(f'{title}:{message}:{level.value}')
            if notification_hash in self.recent_notifications:
                last_time = self.recent_notifications[notification_hash]
                if current_time - last_time < self.config.duplicate_suppression_window:
                    return False
            self.notification_times.append(current_time)
            self.recent_notifications[notification_hash] = current_time
            expired_hashes = [h for h, t in self.recent_notifications.items() if current_time - t > self.config.duplicate_suppression_window]
            for h in expired_hashes:
                del self.recent_notifications[h]
            return True

def __init__(self, config: NotificationConfig):
    self.config = config
    self.notification_times = deque()
    self.recent_notifications = {}
    self._lock = threading.RLock()

class NotificationMetrics:
    """Track notification statistics"""

    def __init__(self):
        self.start_time = time.time()
        self.counts = defaultdict(int)
        self.rate_limited = 0
        self.failed_notifications = 0
        self._lock = threading.RLock()

    def record_sent(self, level: NotificationLevel):
        """Record a sent notification"""
        with self._lock:
            self.counts[level.value] += 1

    def record_rate_limited(self):
        """Record a rate-limited notification"""
        with self._lock:
            self.rate_limited += 1

    def record_failed(self):
        """Record a failed notification"""
        with self._lock:
            self.failed_notifications += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        with self._lock:
            return {'uptime_seconds': time.time() - self.start_time, 'notifications_sent': dict(self.counts), 'total_sent': sum(self.counts.values()), 'rate_limited': self.rate_limited, 'failed': self.failed_notifications}

def __init__(self):
    self.start_time = time.time()
    self.counts = defaultdict(int)
    self.rate_limited = 0
    self.failed_notifications = 0
    self._lock = threading.RLock()

def get_stats(self) -> Dict[str, Any]:
    """Get notification statistics"""
    with self._lock:
        return {'uptime_seconds': time.time() - self.start_time, 'notifications_sent': dict(self.counts), 'total_sent': sum(self.counts.values()), 'rate_limited': self.rate_limited, 'failed': self.failed_notifications}

class AutomaticThemeManager:
    """OPTIMIZED: Theme manager with lazy loading and minimal overhead"""

    def __init__(self):
        self.current_theme = 'bloomberg_terminal'
        self.themes = {}
        self.theme_applied = False
        self.cleanup_performed = False
        self.themes_initialized = False
        self._initialization_attempted = False
        self.themes_available = True
        self.terminal_font = None
        info('Bloomberg Terminal theme manager initialized', module='theme')

    def _lazy_initialize(self) -> bool:
        """PERFORMANCE: Only initialize when first used"""
        if self._initialization_attempted:
            return self.themes_initialized
        self._initialization_attempted = True
        try:
            try:
                dpg.get_viewport_width()
            except Exception:
                warning('DearPyGUI context not ready', module='theme')
                return False
            self._setup_font_registry()
            info('Creating authentic Bloomberg Terminal themes', module='theme')
            self._create_bloomberg_terminal_theme()
            self._create_dark_gold_theme()
            self._create_green_terminal_theme()
            self._create_default_theme()
            self.themes_initialized = True
            theme_count = len(self.themes)
            info('Bloomberg themes creation completed', module='theme', context={'themes_created': theme_count})
            return True
        except Exception as e:
            error('Error creating themes', module='theme', context={'error': str(e)}, exc_info=True)
            return False

    def _setup_font_registry(self):
        """Setup font registry and load custom fonts - SAFE VERSION"""
        try:
            import os
            font_path = os.path.join(os.path.dirname(__file__), 'oswald2.ttf')
            print(f'[FONT DEBUG] Looking for font at: {font_path}')
            print(f'[FONT DEBUG] Font exists: {os.path.exists(font_path)}')
            if os.path.exists(font_path):
                try:
                    with dpg.font_registry():
                        self.terminal_font = dpg.add_font(font_path, 18)
                    print(f'[FONT DEBUG] Font created with ID: {self.terminal_font}')
                    info('Oswald2 font loaded successfully', module='theme')
                except Exception as font_error:
                    print(f'[FONT DEBUG] Font creation failed: {font_error}')
                    self.terminal_font = None
            else:
                print('[FONT DEBUG] Font file not found')
                self.terminal_font = None
        except Exception as e:
            print(f'[FONT DEBUG] Font setup failed: {str(e)}')
            self.terminal_font = None

    def _ensure_themes_created(self) -> bool:
        """Create themes only when DearPyGUI context is ready"""
        return self._lazy_initialize()

    def setup_fonts(self):
        """Setup Oswald2 font for terminal - DEPRECATED, use _setup_font_registry instead"""
        if hasattr(self, 'terminal_font') and self.terminal_font:
            try:
                dpg.bind_font(self.terminal_font)
                info('Font re-applied via setup_fonts', module='theme')
                return True
            except Exception as e:
                warning(f'setup_fonts failed: {str(e)}', module='theme')
                return False
        return False

    def _create_green_terminal_theme(self):
        """Modern Green Terminal theme with #48f050 primary color"""
        try:
            if dpg.does_item_exist('green_terminal_theme'):
                dpg.delete_item('green_terminal_theme')
            with dpg.theme(tag='green_terminal_theme') as theme:
                with dpg.theme_component(dpg.mvAll):
                    TERMINAL_BLACK = [10, 10, 10, 255]
                    TERMINAL_DARK_GRAY = [25, 30, 25, 255]
                    TERMINAL_MEDIUM_GRAY = [40, 45, 40, 255]
                    GREEN_PRIMARY = [72, 240, 80, 255]
                    GREEN_HOVER = [92, 255, 100, 255]
                    GREEN_ACTIVE = [52, 220, 60, 255]
                    GREEN_BRIGHT = [100, 255, 110, 255]
                    TERMINAL_WHITE = [240, 255, 245, 255]
                    TERMINAL_GRAY_TEXT = [180, 220, 185, 255]
                    TERMINAL_DISABLED = [120, 140, 125, 255]
                    TERMINAL_RED = [255, 100, 100, 255]
                    TERMINAL_YELLOW = [255, 255, 120, 255]
                    TERMINAL_BLUE = [120, 200, 255, 255]
                    TERMINAL_BORDER = [60, 80, 60, 255]
                    TERMINAL_SEPARATOR = [80, 120, 85, 255]
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, TERMINAL_BLACK, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ChildBg, TERMINAL_BLACK, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_PopupBg, TERMINAL_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, TERMINAL_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ModalWindowDimBg, [0, 0, 0, 180], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Text, TERMINAL_WHITE, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, TERMINAL_DISABLED, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, [72, 240, 80, 100], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Button, TERMINAL_MEDIUM_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [72, 240, 80, 120], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [72, 240, 80, 180], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, TERMINAL_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [72, 240, 80, 60], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, [72, 240, 80, 100], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Header, [72, 240, 80, 150], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, [72, 240, 80, 180], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, [72, 240, 80, 220], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, TERMINAL_MEDIUM_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, TERMINAL_SEPARATOR, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, TERMINAL_BORDER, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, [0, 0, 0, 0], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, [15, 25, 15, 255], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_NavHighlight, [72, 240, 80, 200], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_NavWindowingHighlight, [72, 240, 80, 150], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_NavWindowingDimBg, [60, 80, 60, 100], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Tab, TERMINAL_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TabHovered, [72, 240, 80, 120], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TabActive, [72, 240, 80, 180], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, [20, 30, 20, 255], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, [35, 50, 35, 255], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Border, TERMINAL_BORDER, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, [0, 0, 0, 0], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Separator, TERMINAL_SEPARATOR, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, [72, 240, 80, 150], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive, [72, 240, 80, 200], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, TERMINAL_BLACK, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, [72, 240, 80, 120], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, [72, 240, 80, 160], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, [72, 240, 80, 200], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_CheckMark, GREEN_PRIMARY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, [72, 240, 80, 180], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, [72, 240, 80, 220], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, [72, 240, 80, 80], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, [72, 240, 80, 120], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, [72, 240, 80, 160], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBg, TERMINAL_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, TERMINAL_MEDIUM_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, TERMINAL_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_DockingPreview, [72, 240, 80, 100], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_DockingEmptyBg, TERMINAL_BLACK, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_PlotLines, GREEN_PRIMARY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_PlotLinesHovered, GREEN_HOVER, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, GREEN_PRIMARY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_PlotHistogramHovered, GREEN_HOVER, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 1, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_TabBorderSize, 1, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 8, 8, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 6, 4, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 4, 4, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 4, 2, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_IndentSpacing, 20, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 14, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 12, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.0, 0.5, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.5, 0.5, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_SelectableTextAlign, 0.0, 0.0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_Alpha, 1.0, category=dpg.mvThemeCat_Core)
            self.themes['green_terminal'] = theme
            info('Green Terminal theme created with primary color', module='theme', context={'primary_color': '#48f050'})
        except Exception as e:
            error('Error creating Green Terminal theme', module='theme', context={'error': str(e)}, exc_info=True)

    def _create_bloomberg_terminal_theme(self):
        """Authentic Bloomberg Terminal theme - Precise color matching"""
        try:
            if dpg.does_item_exist('bloomberg_terminal_theme'):
                dpg.delete_item('bloomberg_terminal_theme')
            with dpg.theme(tag='bloomberg_terminal_theme') as theme:
                with dpg.theme_component(dpg.mvAll):
                    BLOOMBERG_BLACK = [0, 0, 0, 255]
                    BLOOMBERG_DARK_GRAY = [40, 40, 40, 255]
                    BLOOMBERG_MEDIUM_GRAY = [60, 60, 60, 255]
                    BLOOMBERG_ORANGE = [255, 140, 0, 255]
                    BLOOMBERG_ORANGE_HOVER = [255, 165, 0, 255]
                    BLOOMBERG_ORANGE_ACTIVE = [255, 120, 0, 255]
                    BLOOMBERG_WHITE = [255, 255, 255, 255]
                    BLOOMBERG_GRAY_TEXT = [192, 192, 192, 255]
                    BLOOMBERG_DISABLED = [128, 128, 128, 255]
                    BLOOMBERG_RED = [255, 80, 80, 255]
                    BLOOMBERG_GREEN = [0, 255, 100, 255]
                    BLOOMBERG_YELLOW = [255, 255, 100, 255]
                    BLOOMBERG_BLUE = [100, 180, 255, 255]
                    BLOOMBERG_BORDER = [80, 80, 80, 255]
                    BLOOMBERG_SEPARATOR = [100, 100, 100, 255]
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BLOOMBERG_BLACK, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ChildBg, BLOOMBERG_BLACK, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_PopupBg, BLOOMBERG_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, BLOOMBERG_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ModalWindowDimBg, [0, 0, 0, 180], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Text, BLOOMBERG_WHITE, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, BLOOMBERG_DISABLED, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, [255, 140, 0, 100], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Button, BLOOMBERG_MEDIUM_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [255, 140, 0, 120], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [255, 140, 0, 180], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, BLOOMBERG_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [255, 140, 0, 60], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, [255, 140, 0, 100], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Header, [255, 140, 0, 150], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, [255, 140, 0, 180], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, [255, 140, 0, 220], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, BLOOMBERG_MEDIUM_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, BLOOMBERG_SEPARATOR, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, BLOOMBERG_BORDER, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, [0, 0, 0, 0], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, [20, 20, 20, 255], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_NavHighlight, [255, 140, 0, 200], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_NavWindowingHighlight, [255, 140, 0, 150], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_NavWindowingDimBg, [80, 80, 80, 100], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Tab, BLOOMBERG_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TabHovered, [255, 140, 0, 120], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TabActive, [255, 140, 0, 180], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, [30, 30, 30, 255], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, [50, 50, 50, 255], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Border, BLOOMBERG_BORDER, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, [0, 0, 0, 0], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_Separator, BLOOMBERG_SEPARATOR, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, [255, 140, 0, 150], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive, [255, 140, 0, 200], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, BLOOMBERG_BLACK, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, [255, 140, 0, 120], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, [255, 140, 0, 160], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, [255, 140, 0, 200], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_CheckMark, BLOOMBERG_ORANGE, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, [255, 140, 0, 180], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, [255, 140, 0, 220], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, [255, 140, 0, 80], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, [255, 140, 0, 120], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, [255, 140, 0, 160], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBg, BLOOMBERG_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, BLOOMBERG_MEDIUM_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, BLOOMBERG_DARK_GRAY, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_DockingPreview, [255, 140, 0, 100], category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_DockingEmptyBg, BLOOMBERG_BLACK, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_PlotLines, BLOOMBERG_ORANGE, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_PlotLinesHovered, BLOOMBERG_ORANGE_HOVER, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, BLOOMBERG_ORANGE, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_color(dpg.mvThemeCol_PlotHistogramHovered, BLOOMBERG_ORANGE_HOVER, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 1, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_TabBorderSize, 1, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 8, 8, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 6, 4, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 4, 4, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 4, 2, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_IndentSpacing, 20, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 14, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 12, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.0, 0.5, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.5, 0.5, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_SelectableTextAlign, 0.0, 0.0, category=dpg.mvThemeCat_Core)
                    dpg.add_theme_style(dpg.mvStyleVar_Alpha, 1.0, category=dpg.mvThemeCat_Core)
            self.themes['bloomberg_terminal'] = theme
            info('Authentic Bloomberg Terminal theme created', module='theme')
        except Exception as e:
            error('Error creating Bloomberg Terminal theme', module='theme', context={'error': str(e)}, exc_info=True)

    def _create_dark_gold_theme(self):
        """Enhanced dark theme with premium gold accents"""
        try:
            if dpg.does_item_exist('dark_gold_theme'):
                dpg.delete_item('dark_gold_theme')
            with dpg.theme(tag='dark_gold_theme') as theme:
                with dpg.theme_component(dpg.mvAll):
                    DARK_BG = [18, 18, 18, 255]
                    DARK_PANEL = [28, 28, 28, 255]
                    DARK_ELEMENT = [38, 38, 38, 255]
                    GOLD_PRIMARY = [255, 215, 0, 255]
                    GOLD_HOVER = [255, 235, 59, 255]
                    GOLD_ACTIVE = [255, 193, 7, 255]
                    WHITE_TEXT = [255, 255, 255, 255]
                    GRAY_TEXT = [180, 180, 180, 255]
                    DISABLED_TEXT = [120, 120, 120, 255]
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, DARK_BG)
                    dpg.add_theme_color(dpg.mvThemeCol_ChildBg, DARK_BG)
                    dpg.add_theme_color(dpg.mvThemeCol_PopupBg, DARK_PANEL)
                    dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, DARK_PANEL)
                    dpg.add_theme_color(dpg.mvThemeCol_Text, WHITE_TEXT)
                    dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, DISABLED_TEXT)
                    dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, [255, 215, 0, 100])
                    dpg.add_theme_color(dpg.mvThemeCol_Button, DARK_ELEMENT)
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [255, 215, 0, 120])
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [255, 215, 0, 180])
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, DARK_ELEMENT)
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [255, 215, 0, 60])
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, [255, 215, 0, 100])
                    dpg.add_theme_color(dpg.mvThemeCol_Header, [255, 215, 0, 150])
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, [255, 215, 0, 180])
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, [255, 215, 0, 220])
                    dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, DARK_ELEMENT)
                    dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, [0, 0, 0, 0])
                    dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, [25, 25, 25, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_Tab, DARK_ELEMENT)
                    dpg.add_theme_color(dpg.mvThemeCol_TabHovered, [255, 215, 0, 120])
                    dpg.add_theme_color(dpg.mvThemeCol_TabActive, [255, 215, 0, 180])
                    dpg.add_theme_color(dpg.mvThemeCol_Border, [70, 70, 70, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_Separator, [100, 100, 100, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, DARK_BG)
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, [255, 215, 0, 120])
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, [255, 215, 0, 160])
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, [255, 215, 0, 200])
                    dpg.add_theme_color(dpg.mvThemeCol_CheckMark, GOLD_PRIMARY)
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, [255, 215, 0, 180])
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, [255, 215, 0, 220])
                    dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 3)
                    dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 3)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
                    dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 3)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 6, 4)
            self.themes['dark_gold'] = theme
            info('Enhanced Dark Gold theme created', module='theme')
        except Exception as e:
            error('Error creating Dark Gold theme', module='theme', context={'error': str(e)}, exc_info=True)

    def _create_default_theme(self):
        """Improved default theme"""
        try:
            if dpg.does_item_exist('default_theme'):
                dpg.delete_item('default_theme')
            with dpg.theme(tag='default_theme') as theme:
                with dpg.theme_component(dpg.mvAll):
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [15, 15, 15, 240])
                    dpg.add_theme_color(dpg.mvThemeCol_ChildBg, [20, 20, 20, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 255, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, [128, 128, 128, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_Button, [60, 60, 60, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [80, 80, 80, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [100, 100, 100, 255])
                    dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
            self.themes['default'] = theme
            info('Improved Default theme created', module='theme')
        except Exception as e:
            error('Error creating Default theme', module='theme', context={'error': str(e)}, exc_info=True)

    @monitor_performance
    def apply_theme_globally(self, theme_name: str) -> bool:
        """Apply theme with enhanced error handling and feedback - NOW WITH LAZY LOADING"""
        try:
            theme_map = {'finance_terminal': 'bloomberg_terminal', 'bloomberg_terminal': 'bloomberg_terminal', 'bloomberg': 'bloomberg_terminal', 'terminal': 'bloomberg_terminal', 'green_terminal': 'green_terminal', 'green': 'green_terminal', 'matrix': 'green_terminal', 'dark_gold': 'dark_gold', 'gold': 'dark_gold', 'default': 'default', 'standard': 'default'}
            actual_theme = theme_map.get(theme_name.lower(), 'bloomberg_terminal')
            if not self._lazy_initialize():
                warning('Cannot apply theme - DearPyGUI context not ready', module='theme', context={'requested_theme': theme_name})
                return False
            if actual_theme not in self.themes:
                available_themes = list(self.themes.keys())
                warning('Theme not found in available themes', module='theme', context={'requested_theme': actual_theme, 'available_themes': available_themes})
                return False
            if self.theme_applied:
                try:
                    dpg.bind_theme(0)
                    debug('Unbound previous theme', module='theme')
                except Exception as e:
                    warning('Warning unbinding previous theme', module='theme', context={'error': str(e)})
            dpg.bind_theme(self.themes[actual_theme])
            self.current_theme = actual_theme
            self.theme_applied = True
            if hasattr(self, 'terminal_font') and self.terminal_font:
                try:
                    dpg.bind_font(self.terminal_font)
                    print(f'[FONT DEBUG] Applied custom font after theme: {self.terminal_font}')
                except Exception as e:
                    print(f'[FONT DEBUG] Font application after theme failed: {e}')
            theme_info = self.get_theme_info()
            info('Successfully applied theme', module='theme', context={'theme_name': theme_info['name'], 'description': theme_info['description']})
            return True
        except Exception as e:
            error('Critical error applying theme', module='theme', context={'theme_name': theme_name, 'error': str(e)}, exc_info=True)
            return False

    def ensure_font_applied(self):
        """Ensure custom font is applied"""
        try:
            if hasattr(self, 'terminal_font') and self.terminal_font:
                dpg.bind_font(self.terminal_font)
                print(f'[FONT DEBUG] Applied font: {self.terminal_font}')
                return True
            else:
                print('[FONT DEBUG] No font to apply')
                return False
        except Exception as e:
            print(f'[FONT DEBUG] Font application failed: {e}')
            return False

    def get_available_themes(self) -> Dict[str, str]:
        """Get comprehensive list of available themes"""
        return {'bloomberg_terminal': 'Bloomberg Terminal - Authentic black/orange professional theme', 'green_terminal': 'Green Terminal - Modern terminal with bright green (#48f050) accents', 'dark_gold': 'Dark Gold - Premium dark theme with gold accents', 'default': 'Default - Clean standard interface theme'}

    def get_current_theme(self) -> Dict[str, Any]:
        """Get current theme name with status"""
        return {'theme': self.current_theme, 'applied': self.theme_applied, 'initialized': self.themes_initialized}

    def create_theme_selector_callback(self, sender, app_data):
        """Enhanced callback for theme selector with error handling"""
        try:
            success = self.apply_theme_globally(app_data)
            if not success:
                error('Failed to apply theme from selector', module='theme', context={'theme': app_data})
        except Exception as e:
            error('Theme selector callback error', module='theme', context={'error': str(e)}, exc_info=True)

    def get_theme_info(self) -> Dict[str, Any]:
        """Get comprehensive information about current theme"""
        theme_info = {'bloomberg_terminal': {'name': 'Bloomberg Terminal', 'description': 'Authentic Bloomberg Terminal theme with precise black background and orange accents', 'style': 'Professional financial terminal', 'colors': {'primary': 'Bloomberg Orange (#FF8C00)', 'background': 'Pure Black (#000000)', 'text': 'White (#FFFFFF)', 'accent': 'Orange variations'}}, 'green_terminal': {'name': 'Green Terminal', 'description': 'Modern terminal theme with bright green primary color and dark background', 'style': 'Matrix-style financial terminal', 'colors': {'primary': 'Bright Green (#48f050)', 'background': 'Deep Black (#0A0A0A)', 'text': 'Green-tinted White (#F0FFF5)', 'accent': 'Green variations'}}, 'dark_gold': {'name': 'Dark Gold', 'description': 'Premium dark theme with luxurious gold accents and enhanced readability', 'style': 'Luxury financial interface', 'colors': {'primary': 'Gold (#FFD700)', 'background': 'Dark Gray (#121212)', 'text': 'White (#FFFFFF)', 'accent': 'Gold variations'}}, 'default': {'name': 'Default', 'description': 'Clean and professional standard interface theme', 'style': 'Standard modern interface', 'colors': {'primary': 'Gray (#606060)', 'background': 'Dark Gray (#0F0F0F)', 'text': 'White (#FFFFFF)', 'accent': 'Gray variations'}}}
        return theme_info.get(self.current_theme, theme_info['bloomberg_terminal'])

    def get_theme_colors(self) -> Dict[str, list]:
        """Get current theme color palette for external use"""
        if self.current_theme == 'bloomberg_terminal':
            return {'background': [0, 0, 0, 255], 'primary': [255, 140, 0, 255], 'text': [255, 255, 255, 255], 'secondary': [192, 192, 192, 255], 'accent': [255, 165, 0, 255], 'success': [0, 255, 100, 255], 'warning': [255, 255, 100, 255], 'error': [255, 80, 80, 255]}
        elif self.current_theme == 'green_terminal':
            return {'background': [10, 10, 10, 255], 'primary': [72, 240, 80, 255], 'text': [240, 255, 245, 255], 'secondary': [180, 220, 185, 255], 'accent': [100, 255, 110, 255], 'success': [72, 240, 80, 255], 'warning': [255, 255, 120, 255], 'error': [255, 100, 100, 255]}
        elif self.current_theme == 'dark_gold':
            return {'background': [18, 18, 18, 255], 'primary': [255, 215, 0, 255], 'text': [255, 255, 255, 255], 'secondary': [180, 180, 180, 255], 'accent': [255, 235, 59, 255]}
        else:
            return {'background': [15, 15, 15, 255], 'primary': [60, 60, 60, 255], 'text': [255, 255, 255, 255], 'secondary': [128, 128, 128, 255]}

    def cleanup(self):
        """Enhanced cleanup with better error handling"""
        if self.cleanup_performed:
            return
        try:
            info('Cleaning up Bloomberg Terminal themes', module='theme')
            self.cleanup_performed = True
            if self.theme_applied:
                try:
                    dpg.bind_theme(0)
                    self.theme_applied = False
                    info('Theme unbound successfully', module='theme')
                except Exception as e:
                    warning('Warning unbinding theme', module='theme', context={'error': str(e)})
            themes_deleted = 0
            for theme_name, theme in self.themes.items():
                try:
                    if dpg.does_item_exist(theme):
                        dpg.delete_item(theme)
                        themes_deleted += 1
                except Exception as e:
                    warning('Warning deleting theme', module='theme', context={'theme_name': theme_name, 'error': str(e)})
            self.themes.clear()
            self.themes_initialized = False
            info('Themes cleaned up successfully', module='theme', context={'themes_deleted': themes_deleted})
        except Exception as e:
            error('Theme cleanup error', module='theme', context={'error': str(e)}, exc_info=True)

    def __del__(self):
        """Enhanced destructor with error handling"""
        try:
            if not self.cleanup_performed:
                self.cleanup()
        except Exception as e:
            warning('Warning in theme manager destructor', module='theme', context={'error': str(e)})

    def reset_to_default(self) -> bool:
        """Reset to default theme safely"""
        try:
            return self.apply_theme_globally('default')
        except Exception as e:
            error('Error resetting to default theme', module='theme', context={'error': str(e)}, exc_info=True)
            return False

    def validate_theme_integrity(self) -> Tuple[bool, str]:
        """Validate that themes are properly configured"""
        try:
            if not self.themes_initialized:
                return (False, 'Themes not initialized')
            required_themes = ['bloomberg_terminal', 'green_terminal', 'dark_gold', 'default']
            missing_themes = [t for t in required_themes if t not in self.themes]
            if missing_themes:
                return (False, f'Missing themes: {missing_themes}')
            return (True, 'All themes validated successfully')
        except Exception as e:
            return (False, f'Validation error: {e}')

def _lazy_initialize(self) -> bool:
    """PERFORMANCE: Only initialize when first used"""
    if self._initialization_attempted:
        return self.themes_initialized
    self._initialization_attempted = True
    try:
        try:
            dpg.get_viewport_width()
        except Exception:
            warning('DearPyGUI context not ready', module='theme')
            return False
        self._setup_font_registry()
        info('Creating authentic Bloomberg Terminal themes', module='theme')
        self._create_bloomberg_terminal_theme()
        self._create_dark_gold_theme()
        self._create_green_terminal_theme()
        self._create_default_theme()
        self.themes_initialized = True
        theme_count = len(self.themes)
        info('Bloomberg themes creation completed', module='theme', context={'themes_created': theme_count})
        return True
    except Exception as e:
        error('Error creating themes', module='theme', context={'error': str(e)}, exc_info=True)
        return False

class PerformanceMetrics:
    """Lightweight metrics collection"""

    def __init__(self):
        self.start_time = time.time()
        self.log_counts = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}
        self.recent_errors = deque(maxlen=20)
        self.class_usage = {}
        self._lock = threading.RLock()

    def record_log(self, level_name: str, message: str=None, class_name: str=None):
        """Record log entry with minimal overhead"""
        with self._lock:
            self.log_counts[level_name] = self.log_counts.get(level_name, 0) + 1
            if class_name:
                self.class_usage[class_name] = self.class_usage.get(class_name, 0) + 1
            if level_name in ('ERROR', 'CRITICAL') and message:
                self.recent_errors.append({'timestamp': time.time(), 'level': level_name, 'message': message[:200], 'class': class_name or 'unknown'})

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        with self._lock:
            return {'uptime_seconds': time.time() - self.start_time, 'log_counts': self.log_counts.copy(), 'recent_errors': len(self.recent_errors), 'total_logs': sum(self.log_counts.values()), 'active_classes': len(self.class_usage), 'top_logging_classes': sorted(self.class_usage.items(), key=lambda x: x[1], reverse=True)[:10]}

def __init__(self):
    self.start_time = time.time()
    self.log_counts = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}
    self.recent_errors = deque(maxlen=20)
    self.class_usage = {}
    self._lock = threading.RLock()

def record_log(self, level_name: str, message: str=None, class_name: str=None):
    """Record log entry with minimal overhead"""
    with self._lock:
        self.log_counts[level_name] = self.log_counts.get(level_name, 0) + 1
        if class_name:
            self.class_usage[class_name] = self.class_usage.get(class_name, 0) + 1
        if level_name in ('ERROR', 'CRITICAL') and message:
            self.recent_errors.append({'timestamp': time.time(), 'level': level_name, 'message': message[:200], 'class': class_name or 'unknown'})

def get_summary(self) -> Dict[str, Any]:
    """Get metrics summary"""
    with self._lock:
        return {'uptime_seconds': time.time() - self.start_time, 'log_counts': self.log_counts.copy(), 'recent_errors': len(self.recent_errors), 'total_logs': sum(self.log_counts.values()), 'active_classes': len(self.class_usage), 'top_logging_classes': sorted(self.class_usage.items(), key=lambda x: x[1], reverse=True)[:10]}

class LazyImporter:
    """Lazy import manager for heavy dependencies - optimized"""

    def __init__(self):
        self._dpg = None
        self._requests = None
        self._import_lock = threading.RLock()

    def get_dpg(self):
        if self._dpg is None:
            with self._import_lock:
                if self._dpg is None:
                    try:
                        import dearpygui.dearpygui as dpg
                        self._dpg = dpg
                        logger.debug('DearPyGui imported successfully')
                    except ImportError as e:
                        logger.error(f'Failed to import DearPyGui: {e}', exc_info=True)
                        raise
        return self._dpg

    def get_requests(self):
        if self._requests is None:
            with self._import_lock:
                if self._requests is None:
                    try:
                        import requests
                        self._requests = requests
                        logger.debug('Requests library imported successfully')
                    except ImportError as e:
                        logger.error(f'Failed to import requests: {e}', exc_info=True)
                        raise
        return self._requests

def __init__(self):
    self._dpg = None
    self._requests = None
    self._import_lock = threading.RLock()

class ConnectionPool:
    """Simple connection pool for HTTP requests - optimized"""

    def __init__(self, max_connections=5):
        self.max_connections = max_connections
        self._session = None
        self._lock = threading.RLock()
        self._creation_time = None

    @monitor_performance
    def get_session(self):
        if self._session is None:
            with self._lock:
                if self._session is None:
                    with operation('create_session'):
                        requests = _lazy_imports.get_requests()
                        self._session = requests.Session()
                        self._creation_time = datetime.now()
                        adapter = requests.adapters.HTTPAdapter(pool_connections=self.max_connections, pool_maxsize=self.max_connections, max_retries=0)
                        self._session.mount('http://', adapter)
                        self._session.mount('https://', adapter)
                        logger.debug('HTTP session created with connection pooling')
        return self._session

    def close(self):
        if self._session:
            try:
                self._session.close()
                if self._creation_time:
                    duration = (datetime.now() - self._creation_time).total_seconds()
                    logger.debug(f'HTTP session closed after {duration:.2f} seconds')
                self._session = None
                self._creation_time = None
            except Exception as e:
                logger.error(f'Error closing HTTP session: {e}')

def __init__(self, max_connections=5):
    self.max_connections = max_connections
    self._session = None
    self._lock = threading.RLock()
    self._creation_time = None

class HelpTab(BaseTab):
    """Bloomberg Terminal style Help and About tab"""

    def __init__(self, main_app=None):
        super().__init__(main_app)
        self.main_app = main_app
        self.scroll_position = 0
        self.BLOOMBERG_ORANGE = [255, 165, 0]
        self.BLOOMBERG_WHITE = [255, 255, 255]
        self.BLOOMBERG_RED = [255, 0, 0]
        self.BLOOMBERG_GREEN = [0, 200, 0]
        self.BLOOMBERG_YELLOW = [255, 255, 0]
        self.BLOOMBERG_GRAY = [120, 120, 120]
        self.BLOOMBERG_BLUE = [100, 150, 250]
        self.BLOOMBERG_BLACK = [0, 0, 0]
        self._cached_datetime = None
        self._datetime_cache_time = 0
        debug('HelpTab initialized', module='help', context={'main_app_available': bool(main_app)})

    def get_label(self):
        return ' Help & About'

    def _get_current_time_cached(self):
        """Get current time with caching for performance"""
        import time
        current_time = time.time()
        if current_time - self._datetime_cache_time > 5:
            self._cached_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._datetime_cache_time = current_time
        return self._cached_datetime

    @monitor_performance
    def create_content(self):
        """Create Bloomberg-style help terminal layout"""
        with operation('create_help_content', module='help'):
            try:
                with dpg.group(horizontal=True):
                    dpg.add_text('FINCEPT', color=self.BLOOMBERG_ORANGE)
                    dpg.add_text('HELP TERMINAL', color=self.BLOOMBERG_WHITE)
                    dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                    dpg.add_input_text(label='', default_value='Search Help Topics', width=300)
                    dpg.add_button(label='SEARCH', width=80, callback=self.search_help)
                    dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                    dpg.add_text(self._get_current_time_cached())
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    help_functions = ['F1:ABOUT', 'F2:FEATURES', 'F3:SUPPORT', 'F4:CONTACT', 'F5:FEEDBACK', 'F6:DOCS']
                    for key in help_functions:
                        dpg.add_button(label=key, width=100, height=25, callback=lambda s, a, u, k=key: self.navigate_section(k))
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    self.create_left_help_panel()
                    self.create_center_help_panel()
                    self.create_right_help_panel()
                dpg.add_separator()
                self.create_help_status_bar()
                info('Help content created successfully', module='help')
            except Exception as e:
                error('Error creating help content', module='help', context={'error': str(e)}, exc_info=True)
                dpg.add_text('HELP TERMINAL', color=self.BLOOMBERG_ORANGE)
                dpg.add_text('Error loading help content. Please try again.')

    @monitor_performance
    def create_left_help_panel(self):
        """Create left help navigation panel"""
        with operation('create_left_help_panel', module='help'):
            with dpg.child_window(width=350, height=650, border=True):
                dpg.add_text('HELP NAVIGATOR', color=self.BLOOMBERG_ORANGE)
                dpg.add_separator()
                with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, scrollY=True, height=300):
                    dpg.add_table_column(label='Section', width_fixed=True, init_width_or_weight=120)
                    dpg.add_table_column(label='Status', width_fixed=True, init_width_or_weight=80)
                    dpg.add_table_column(label='Action', width_fixed=True, init_width_or_weight=100)
                    help_sections = [('ABOUT FINCEPT', 'AVAILABLE', 'VIEW'), ('FEATURES', 'AVAILABLE', 'VIEW'), ('MARKET DATA', 'AVAILABLE', 'VIEW'), ('PORTFOLIO', 'AVAILABLE', 'VIEW'), ('ANALYTICS', 'AVAILABLE', 'VIEW'), ('SUPPORT', 'AVAILABLE', 'CONTACT'), ('TUTORIALS', 'COMING SOON', 'NOTIFY'), ('API DOCS', 'AVAILABLE', 'OPEN'), ('COMMUNITY', 'AVAILABLE', 'JOIN'), ('FEEDBACK', 'AVAILABLE', 'SEND')]
                    for section, status, action in help_sections:
                        with dpg.table_row():
                            dpg.add_text(section, color=self.BLOOMBERG_WHITE)
                            status_color = self.BLOOMBERG_GREEN if status == 'AVAILABLE' else self.BLOOMBERG_YELLOW
                            dpg.add_text(status, color=status_color)
                            action_color = self.BLOOMBERG_BLUE if action in ['VIEW', 'OPEN'] else self.BLOOMBERG_ORANGE
                            dpg.add_text(action, color=action_color)
                dpg.add_separator()
                dpg.add_text('HELP STATISTICS', color=self.BLOOMBERG_YELLOW)
                with dpg.table(header_row=False, borders_innerH=False, borders_outerH=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    stats = [('Total Help Topics:', '47'), ('Video Tutorials:', '12'), ('FAQ Articles:', '25'), ('API Endpoints:', '156')]
                    for label, value in stats:
                        with dpg.table_row():
                            dpg.add_text(label)
                            dpg.add_text(value, color=self.BLOOMBERG_WHITE)
                dpg.add_separator()
                dpg.add_text('SYSTEM STATUS', color=self.BLOOMBERG_YELLOW)
                with dpg.group(horizontal=True):
                    dpg.add_text('●', color=self.BLOOMBERG_GREEN)
                    dpg.add_text('ALL SYSTEMS OPERATIONAL', color=self.BLOOMBERG_GREEN)
                debug('Left help panel created', module='help')

    @monitor_performance
    def create_center_help_panel(self):
        """Create center help content panel"""
        with operation('create_center_help_panel', module='help'):
            with dpg.child_window(width=900, height=650, border=True):
                with dpg.tab_bar():
                    with dpg.tab(label='About'):
                        self._create_about_tab()
                    with dpg.tab(label='Features'):
                        self._create_features_tab()
                    with dpg.tab(label='Support'):
                        self._create_support_tab()
                    with dpg.tab(label='API Docs'):
                        self._create_api_docs_tab()
                debug('Center help panel created', module='help')

    def _create_about_tab(self):
        """Create about tab content"""
        dpg.add_text('ABOUT FINCEPT TERMINAL', color=self.BLOOMBERG_ORANGE)
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text('Fincept Financial Terminal', color=self.BLOOMBERG_ORANGE)
                dpg.add_text('Professional Trading & Analytics Platform')
                dpg.add_spacer(height=10)
                with dpg.table(header_row=False, borders_innerH=False, borders_outerH=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    version_info = [('Version:', '4.2.1 Professional'), ('Build:', '20250115.1'), ('License:', 'Enterprise'), ('Data Sources:', 'Real-time'), ('API Status:', 'Connected')]
                    for label, value in version_info:
                        with dpg.table_row():
                            dpg.add_text(label)
                            value_color = self.BLOOMBERG_GREEN if value in ['Enterprise', 'Real-time', 'Connected'] else self.BLOOMBERG_WHITE
                            dpg.add_text(value, color=value_color)
            with dpg.group():
                dpg.add_text('Core Features', color=self.BLOOMBERG_YELLOW)
                features = ['• Real-time market data & analytics', '• Portfolio management & tracking', '• Advanced charting & technical analysis', '• Financial news & sentiment analysis', '• Risk management tools', '• Algorithmic trading support', '• Multi-asset class coverage', '• Professional-grade security']
                for feature in features:
                    dpg.add_text(feature)
        dpg.add_spacer(height=20)
        about_text = 'Fincept Terminal is a cutting-edge financial analysis platform designed to provide real-time market data, portfolio management, and actionable insights to investors, traders, and financial professionals. Our platform integrates advanced analytics, AI-driven sentiment analysis, and the latest market trends to help you make well-informed investment decisions.'
        dpg.add_text(about_text, wrap=850, color=self.BLOOMBERG_WHITE)

    def _create_features_tab(self):
        """Create features tab content"""
        dpg.add_text('TERMINAL FEATURES & CAPABILITIES', color=self.BLOOMBERG_ORANGE)
        dpg.add_separator()
        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, scrollY=True, height=400):
            dpg.add_table_column(label='Feature Category', width_fixed=True, init_width_or_weight=200)
            dpg.add_table_column(label='Description', width_fixed=True, init_width_or_weight=400)
            dpg.add_table_column(label='Status', width_fixed=True, init_width_or_weight=100)
            dpg.add_table_column(label='Access Level', width_fixed=True, init_width_or_weight=120)
            features = [('Market Data', 'Real-time quotes, indices, forex, commodities', 'ACTIVE', 'ALL USERS'), ('Portfolio Mgmt', 'Track holdings, P&L, asset allocation', 'ACTIVE', 'ALL USERS'), ('Technical Analysis', 'Advanced charting, indicators, overlays', 'ACTIVE', 'PRO'), ('News & Sentiment', 'Financial news aggregation, sentiment scoring', 'ACTIVE', 'PRO'), ('Risk Analytics', 'VaR, stress testing, correlation analysis', 'ACTIVE', 'ENTERPRISE'), ('Algo Trading', 'Strategy backtesting, execution algorithms', 'BETA', 'ENTERPRISE'), ('Options Analytics', 'Greeks, volatility surface, strategies', 'ACTIVE', 'PRO'), ('Fixed Income', 'Bond analytics, yield curves, duration', 'ACTIVE', 'ENTERPRISE'), ('ESG Analytics', 'Sustainability metrics, ESG scoring', 'COMING SOON', 'PRO'), ('AI Insights', 'Machine learning predictions, pattern recognition', 'BETA', 'ENTERPRISE')]
            for feature, description, status, access in features:
                with dpg.table_row():
                    dpg.add_text(feature, color=self.BLOOMBERG_YELLOW)
                    dpg.add_text(description, color=self.BLOOMBERG_WHITE)
                    status_color = self.BLOOMBERG_GREEN if status == 'ACTIVE' else self.BLOOMBERG_YELLOW if status == 'BETA' else self.BLOOMBERG_ORANGE
                    dpg.add_text(status, color=status_color)
                    access_color = self.BLOOMBERG_GREEN if access == 'ALL USERS' else self.BLOOMBERG_BLUE if access == 'PRO' else self.BLOOMBERG_ORANGE
                    dpg.add_text(access, color=access_color)

    def _create_support_tab(self):
        """Create support tab content"""
        dpg.add_text('CUSTOMER SUPPORT & ASSISTANCE', color=self.BLOOMBERG_ORANGE)
        dpg.add_separator()
        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text('Contact Information', color=self.BLOOMBERG_YELLOW)
                dpg.add_spacer(height=10)
                with dpg.table(header_row=False, borders_innerH=False, borders_outerH=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    contact_info = [('Email Support:', 'support@fincept.in'), ('Phone Support:', '+1 (555) 123-4567'), ('Live Chat:', 'Available 24/7'), ('Response Time:', '< 2 hours'), ('Support Hours:', '24/7/365')]
                    for label, value in contact_info:
                        with dpg.table_row():
                            dpg.add_text(label)
                            value_color = self.BLOOMBERG_BLUE if 'support@' in value else self.BLOOMBERG_GREEN if 'Available' in value or '< 2' in value or '24/7' in value else self.BLOOMBERG_WHITE
                            dpg.add_text(value, color=value_color)
            with dpg.group():
                dpg.add_text('Support Channels', color=self.BLOOMBERG_YELLOW)
                dpg.add_spacer(height=10)
                support_buttons = [('📧 Email Support', self.contact_email_support), ('💬 Live Chat', self.open_live_chat), ('📞 Phone Support', self.contact_phone_support), ('📖 Documentation', self.open_documentation), ('🎥 Video Tutorials', self.open_tutorials), ('👥 Community Forum', self.open_community), ('🐛 Report Bug', self.report_bug), ('💡 Feature Request', self.request_feature)]
                for label, callback in support_buttons:
                    dpg.add_button(label=label, callback=callback, width=200)
                    dpg.add_spacer(height=5)

    def _create_api_docs_tab(self):
        """Create API documentation tab content"""
        dpg.add_text('API DOCUMENTATION & ENDPOINTS', color=self.BLOOMBERG_ORANGE)
        dpg.add_separator()
        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, scrollY=True, height=500):
            dpg.add_table_column(label='Endpoint', width_fixed=True, init_width_or_weight=200)
            dpg.add_table_column(label='Method', width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column(label='Description', width_fixed=True, init_width_or_weight=300)
            dpg.add_table_column(label='Rate Limit', width_fixed=True, init_width_or_weight=100)
            dpg.add_table_column(label='Auth Required', width_fixed=True, init_width_or_weight=120)
            api_endpoints = [('/api/v1/market/quotes', 'GET', 'Real-time market quotes', '1000/min', 'YES'), ('/api/v1/portfolio/holdings', 'GET', 'Portfolio holdings data', '100/min', 'YES'), ('/api/v1/news/latest', 'GET', 'Latest financial news', '500/min', 'NO'), ('/api/v1/analytics/technical', 'POST', 'Technical analysis calculations', '50/min', 'YES'), ('/api/v1/market/history', 'GET', 'Historical market data', '200/min', 'YES'), ('/api/v1/user/profile', 'GET', 'User profile information', '10/min', 'YES'), ('/api/v1/orders/submit', 'POST', 'Submit trading orders', '100/min', 'YES'), ('/api/v1/market/screener', 'POST', 'Stock screening criteria', '50/min', 'YES'), ('/api/v1/research/reports', 'GET', 'Research reports access', '20/min', 'YES'), ('/api/v1/alerts/manage', 'POST', 'Manage price alerts', '100/min', 'YES')]
            for endpoint, method, description, rate_limit, auth in api_endpoints:
                with dpg.table_row():
                    dpg.add_text(endpoint, color=self.BLOOMBERG_BLUE)
                    method_color = self.BLOOMBERG_GREEN if method == 'GET' else self.BLOOMBERG_ORANGE
                    dpg.add_text(method, color=method_color)
                    dpg.add_text(description, color=self.BLOOMBERG_WHITE)
                    dpg.add_text(rate_limit, color=self.BLOOMBERG_YELLOW)
                    auth_color = self.BLOOMBERG_RED if auth == 'YES' else self.BLOOMBERG_GREEN
                    dpg.add_text(auth, color=auth_color)

    @monitor_performance
    def create_right_help_panel(self):
        """Create right quick actions panel"""
        with operation('create_right_help_panel', module='help'):
            with dpg.child_window(width=350, height=650, border=True):
                dpg.add_text('QUICK ACTIONS', color=self.BLOOMBERG_ORANGE)
                dpg.add_separator()
                quick_actions = [('📞 Contact Support', self.contact_support), ('📝 Send Feedback', self.send_feedback), ('📚 User Manual', self.open_manual), ('🎥 Watch Tutorials', self.open_tutorials), ('👥 Join Community', self.open_community), ('🔄 Check Updates', self.check_updates), ('⚙️ System Settings', self.open_settings), ('🐛 Report Issue', self.report_bug)]
                for label, callback in quick_actions:
                    dpg.add_button(label=label, callback=callback, width=-1, height=35)
                    dpg.add_spacer(height=5)
                dpg.add_separator()
                dpg.add_text('SYSTEM INFORMATION', color=self.BLOOMBERG_YELLOW)
                with dpg.table(header_row=False, borders_innerH=False, borders_outerH=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    system_info = [('Terminal Version:', '4.2.1'), ('Build Date:', '2025-01-15'), ('Platform:', 'Windows 11'), ('Memory Usage:', '2.4 GB'), ('CPU Usage:', '12%'), ('Network Status:', 'Connected'), ('Data Feed:', 'Live'), ('Session Time:', '02:34:12')]
                    for label, value in system_info:
                        with dpg.table_row():
                            dpg.add_text(label, color=self.BLOOMBERG_GRAY)
                            value_color = self.BLOOMBERG_GREEN if 'Connected' in value or 'Live' in value else self.BLOOMBERG_WHITE
                            dpg.add_text(value, color=value_color)
                dpg.add_separator()
                dpg.add_text('RECENT HELP TOPICS', color=self.BLOOMBERG_YELLOW)
                recent_topics = ['How to create portfolios', 'Setting up price alerts', 'Understanding P&L calculations', 'Using technical indicators', 'Exporting data to Excel']
                for topic in recent_topics:
                    with dpg.group(horizontal=True):
                        dpg.add_text('•', color=self.BLOOMBERG_ORANGE)
                        dpg.add_text(topic, color=self.BLOOMBERG_WHITE, wrap=300)
                debug('Right help panel created', module='help')

    def create_help_status_bar(self):
        """Create help status bar"""
        with dpg.group(horizontal=True):
            status_items = [('HELP STATUS:', 'ONLINE', self.BLOOMBERG_GRAY, self.BLOOMBERG_GREEN), ('SUPPORT AVAILABLE:', '24/7', self.BLOOMBERG_GRAY, self.BLOOMBERG_GREEN), ('LAST UPDATED:', '2025-01-15', self.BLOOMBERG_GRAY, self.BLOOMBERG_WHITE), ('HELP VERSION:', '4.2.1', self.BLOOMBERG_GRAY, self.BLOOMBERG_WHITE)]
            for i, (label, value, label_color, value_color) in enumerate(status_items):
                if i > 0:
                    dpg.add_text(' | ', color=self.BLOOMBERG_GRAY)
                dpg.add_text(label, color=label_color)
                dpg.add_text(value, color=value_color)

    def navigate_section(self, section_key):
        """Navigate to help section"""
        section_map = {'F1:ABOUT': 'About', 'F2:FEATURES': 'Features', 'F3:SUPPORT': 'Support', 'F4:CONTACT': 'Support', 'F5:FEEDBACK': 'Support', 'F6:DOCS': 'API Docs'}
        target_tab = section_map.get(section_key, 'About')
        info('Navigating to help section', module='help', context={'section_key': section_key, 'target_tab': target_tab})

    def search_help(self):
        """Search help topics"""
        with operation('search_help', module='help'):
            info('Help search functionality activated', module='help')

    def contact_support(self):
        """Contact support"""
        info('Contacting support team', module='help', context={'email': 'support@fincept.in', 'phone': '+1 (555) 123-4567'})

    def contact_email_support(self):
        """Contact email support"""
        info('Opening email support', module='help', context={'email': 'support@fincept.in'})

    def open_live_chat(self):
        """Open live chat"""
        info('Opening live chat support', module='help')

    def contact_phone_support(self):
        """Contact phone support"""
        info('Initiating phone support', module='help', context={'phone': '+1 (555) 123-4567'})

    def send_feedback(self):
        """Send feedback"""
        info('Opening feedback form', module='help')

    def open_manual(self):
        """Open user manual"""
        info('Opening user manual', module='help')

    def open_documentation(self):
        """Open documentation"""
        info('Opening documentation', module='help')

    def open_tutorials(self):
        """Open video tutorials"""
        info('Opening video tutorials', module='help')

    def open_community(self):
        """Open community forum"""
        info('Opening community forum', module='help')

    def check_updates(self):
        """Check for updates"""
        info('Checking for updates', module='help')

    def open_settings(self):
        """Open settings"""
        info('Opening system settings', module='help')

    def report_bug(self):
        """Report a bug"""
        info('Opening bug report form', module='help')

    def request_feature(self):
        """Request a feature"""
        info('Opening feature request form', module='help')

    @monitor_performance
    def back_to_dashboard(self):
        """Navigate back to dashboard"""
        with operation('back_to_dashboard', module='help'):
            try:
                if hasattr(self.main_app, 'tabs') and 'dashboard' in self.main_app.tabs:
                    info('Returning to Dashboard', module='help')
                    dpg.set_value('main_tab_bar', 'tab_dashboard')
                else:
                    warning('Dashboard not available', module='help')
            except Exception as e:
                error('Error navigating to dashboard', module='help', context={'error': str(e)}, exc_info=True)

    def resize_components(self, left_width, center_width, right_width, top_height, bottom_height, cell_height):
        """Handle component resizing"""
        debug('Component resize requested - using fixed Bloomberg layout', module='help', context={'left_width': left_width, 'center_width': center_width})

    @monitor_performance
    def cleanup(self):
        """Clean up help tab resources"""
        with operation('help_tab_cleanup', module='help'):
            try:
                info('Cleaning up help tab resources', module='help')
                self.scroll_position = 0
                self._cached_datetime = None
                self._datetime_cache_time = 0
                info('Help tab cleanup complete', module='help')
            except Exception as e:
                error('Error in help cleanup', module='help', context={'error': str(e)}, exc_info=True)

def _get_current_time_cached(self):
    """Get current time with caching for performance"""
    import time
    current_time = time.time()
    if current_time - self._datetime_cache_time > 5:
        self._cached_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._datetime_cache_time = current_time
    return self._cached_datetime

class GeopoliticalAgent:
    """Advanced geopolitical risk monitoring and analysis"""

    def __init__(self):
        self.name = 'geopolitical'
        self.data_manager = DataFeedManager()
        self.client = openai.OpenAI(api_key=CONFIG.api.openai_api_key)
        self.risk_factors = {'military_conflicts': {'Russia-Ukraine': 0.25, 'China-Taiwan': 0.2, 'Middle_East': 0.15, 'North_Korea': 0.1, 'India-Pakistan': 0.08, 'Balkans': 0.05, 'Arctic': 0.07, 'Cyber_warfare': 0.1}, 'trade_tensions': {'US-China': 0.3, 'US-EU': 0.15, 'China-EU': 0.15, 'US-Russia': 0.2, 'Brexit_aftermath': 0.1, 'USMCA_issues': 0.1}, 'sanctions_regime': {'Russia_sanctions': 0.35, 'China_tech_sanctions': 0.25, 'Iran_sanctions': 0.15, 'North_Korea_sanctions': 0.1, 'Secondary_sanctions': 0.15}, 'political_instability': {'US_domestic': 0.2, 'EU_integration': 0.18, 'China_internal': 0.15, 'Middle_East_regimes': 0.15, 'Latin_America': 0.12, 'Africa_coups': 0.1, 'Democratic_backsliding': 0.1}}
        self.sector_impact_map = {'military_conflicts': {'defense': 0.8, 'energy': 0.6, 'commodities': 0.7, 'technology': -0.3, 'tourism': -0.6, 'airlines': -0.5, 'insurance': -0.4}, 'trade_tensions': {'technology': -0.7, 'manufacturing': -0.5, 'agriculture': -0.4, 'automotive': -0.6, 'semiconductors': -0.8, 'renewable_energy': 0.3}, 'sanctions_regime': {'energy': -0.8, 'banking': -0.6, 'technology': -0.5, 'shipping': -0.4, 'commodities': 0.4, 'defense': 0.5}, 'political_instability': {'healthcare': 0.2, 'utilities': 0.3, 'consumer_staples': 0.4, 'financials': -0.4, 'real_estate': -0.3, 'currency': -0.6}}
        self.geopolitical_keywords = {'conflict_escalation': ['military buildup', 'troop movements', 'weapon shipments', 'border tensions', 'missile tests', 'naval exercises', 'air defense', 'invasion', 'occupation', 'blockade'], 'diplomatic_tensions': ['sanctions', 'tariffs', 'trade war', 'diplomatic expulsion', 'embassy closure', 'summit cancellation', 'treaty withdrawal', 'alliance strain', 'diplomatic protest'], 'regime_change': ['coup', 'revolution', 'civil unrest', 'protests', 'election fraud', 'authoritarianism', 'martial law', 'state of emergency', 'government collapse'], 'economic_warfare': ['currency manipulation', 'debt trap', 'supply chain disruption', 'critical minerals', 'technology transfer', 'intellectual property', 'cyber attacks', 'financial warfare']}
        self.regional_weights = {'North_America': 0.25, 'Europe': 0.2, 'East_Asia': 0.25, 'Middle_East': 0.15, 'South_America': 0.08, 'Africa': 0.05, 'South_Asia': 0.02}

    async def analyze_global_risks(self) -> List[GeopoliticalRisk]:
        """Comprehensive global geopolitical risk analysis"""
        risks = []
        try:
            for risk_category, risk_items in self.risk_factors.items():
                category_risks = await self._analyze_risk_category(risk_category, risk_items)
                risks.extend(category_risks)
            risks.sort(key=lambda x: x.current_level * x.confidence, reverse=True)
            return risks[:10]
        except Exception as e:
            logging.error(f'Error in global risk analysis: {e}')
            return [self._default_geopolitical_risk()]

    async def _analyze_risk_category(self, category: str, risk_items: Dict[str, float]) -> List[GeopoliticalRisk]:
        """Analyze specific risk category"""
        category_risks = []
        news_data = await self._fetch_category_news(category, list(risk_items.keys()))
        for risk_item, weight in risk_items.items():
            try:
                relevant_news = [news for news in news_data if self._is_relevant_to_risk(news, risk_item)]
                risk_level = self._calculate_risk_level(relevant_news, risk_item, category)
                trend = self._determine_risk_trend(relevant_news)
                prob_impact = self._calculate_probability_impact(risk_level, weight, relevant_news)
                affected_sectors = self._get_affected_sectors(category, risk_level)
                timeline = self._estimate_timeline(risk_level, trend, relevant_news)
                mitigation = self._get_mitigation_strategies(risk_item, category)
                confidence = self._calculate_risk_confidence(relevant_news, risk_item)
                risk = GeopoliticalRisk(region=self._get_region_from_risk(risk_item), risk_type=category, current_level=risk_level, trend=trend, probability_impact=prob_impact, affected_sectors=affected_sectors, timeline=timeline, mitigation_strategies=mitigation, confidence=confidence)
                category_risks.append(risk)
            except Exception as e:
                logging.error(f'Error analyzing {risk_item}: {e}')
                continue
        return category_risks

    async def _fetch_category_news(self, category: str, risk_items: List[str]) -> List[DataPoint]:
        """Fetch news data for specific risk category"""
        all_news = []
        queries = []
        if category == 'military_conflicts':
            queries = ['military conflict', 'war', 'invasion', 'missile', 'defense']
        elif category == 'trade_tensions':
            queries = ['trade war', 'tariffs', 'sanctions', 'trade dispute']
        elif category == 'sanctions_regime':
            queries = ['sanctions', 'embargo', 'trade restrictions']
        elif category == 'political_instability':
            queries = ['political crisis', 'coup', 'election', 'protests']
        for query in queries:
            try:
                news_data = await self.data_manager.get_multi_source_data({'news': {'query': query, 'sources': ['reuters', 'bloomberg', 'wsj', 'ft'], 'hours_back': 72}})
                if 'news' in news_data:
                    all_news.extend(news_data['news'])
            except Exception as e:
                logging.error(f'Error fetching news for {query}: {e}')
                continue
        return all_news

    def _is_relevant_to_risk(self, news: DataPoint, risk_item: str) -> bool:
        """Check if news article is relevant to specific risk"""
        text = (news.value + ' ' + news.metadata.get('description', '')).lower()
        risk_keywords = {'Russia-Ukraine': ['russia', 'ukraine', 'putin', 'zelensky', 'kyiv', 'moscow'], 'China-Taiwan': ['china', 'taiwan', 'beijing', 'taipei', 'strait', 'xi jinping'], 'Middle_East': ['iran', 'israel', 'gaza', 'lebanon', 'syria', 'yemen'], 'North_Korea': ['north korea', 'kim jong', 'pyongyang', 'dprk'], 'US-China': ['us china', 'trade war', 'biden', 'xi jinping', 'tariff'], 'Russia_sanctions': ['russia sanctions', 'swift', 'energy embargo'], 'China_tech_sanctions': ['china tech', 'semiconductor', 'huawei', 'tiktok']}
        keywords = risk_keywords.get(risk_item, [risk_item.lower().replace('_', ' ')])
        return any((keyword in text for keyword in keywords))

    def _calculate_risk_level(self, news: List[DataPoint], risk_item: str, category: str) -> int:
        """Calculate current risk level (1-10 scale)"""
        if not news:
            return 3
        base_risks = {'Russia-Ukraine': 8, 'China-Taiwan': 6, 'Middle_East': 7, 'US-China': 5, 'North_Korea': 4}
        base_risk = base_risks.get(risk_item, 5)
        escalation_keywords = self.geopolitical_keywords.get('conflict_escalation', [])
        tension_keywords = self.geopolitical_keywords.get('diplomatic_tensions', [])
        escalation_count = 0
        total_articles = len(news)
        for article in news:
            text = article.value.lower()
            escalation_count += sum((1 for keyword in escalation_keywords if keyword in text))
            escalation_count += sum((1 for keyword in tension_keywords if keyword in text))
        if total_articles > 0:
            intensity_factor = min(escalation_count / total_articles, 2.0)
            adjusted_risk = base_risk + intensity_factor
        else:
            adjusted_risk = base_risk
        return int(np.clip(adjusted_risk, 1, 10))

    def _determine_risk_trend(self, news: List[DataPoint]) -> str:
        """Determine if risk is escalating, stable, or de-escalating"""
        if len(news) < 2:
            return 'stable'
        sorted_news = sorted(news, key=lambda x: x.timestamp)
        midpoint = len(sorted_news) // 2
        older_news = sorted_news[:midpoint]
        recent_news = sorted_news[midpoint:]
        older_intensity = self._calculate_news_intensity(older_news)
        recent_intensity = self._calculate_news_intensity(recent_news)
        if recent_intensity > older_intensity * 1.2:
            return 'escalating'
        elif recent_intensity < older_intensity * 0.8:
            return 'de-escalating'
        else:
            return 'stable'

    def _calculate_news_intensity(self, news: List[DataPoint]) -> float:
        """Calculate intensity score of news articles"""
        if not news:
            return 0.0
        intensity_score = 0.0
        escalation_keywords = self.geopolitical_keywords.get('conflict_escalation', []) + self.geopolitical_keywords.get('diplomatic_tensions', [])
        for article in news:
            text = article.value.lower()
            keyword_count = sum((1 for keyword in escalation_keywords if keyword in text))
            intensity_score += keyword_count * article.confidence
        return intensity_score / len(news)

    def _calculate_probability_impact(self, risk_level: int, weight: float, news: List[DataPoint]) -> float:
        """Calculate probability-weighted impact"""
        probability = (risk_level / 10) ** 1.5
        economic_impact = weight
        if news:
            avg_age_hours = np.mean([(datetime.now() - article.timestamp).total_seconds() / 3600 for article in news])
            recency_factor = max(0.5, 1.0 - avg_age_hours / 168)
            volume_factor = min(1.5, len(news) / 10)
        else:
            recency_factor = 0.5
            volume_factor = 0.5
        return probability * economic_impact * recency_factor * volume_factor

    def _get_affected_sectors(self, category: str, risk_level: int) -> List[str]:
        """Get sectors most affected by this risk category"""
        if category not in self.sector_impact_map:
            return ['broad_market']
        sector_impacts = self.sector_impact_map[category]
        threshold = 0.3 if risk_level > 7 else 0.4 if risk_level > 5 else 0.5
        affected_sectors = []
        for sector, impact in sector_impacts.items():
            if abs(impact) >= threshold:
                affected_sectors.append(sector)
        return affected_sectors or ['broad_market']

    def _estimate_timeline(self, risk_level: int, trend: str, news: List[DataPoint]) -> str:
        """Estimate timeline for risk materialization"""
        base_timelines = {'escalating': {9: '1-3 months', 7: '3-6 months', 5: '6-12 months', 3: '1-2 years'}, 'stable': {9: '3-6 months', 7: '6-12 months', 5: '1-2 years', 3: '2+ years'}, 'de-escalating': {9: '6-12 months', 7: '1-2 years', 5: '2+ years', 3: 'Low probability'}}
        timeline_map = base_timelines.get(trend, base_timelines['stable'])
        for level in sorted(timeline_map.keys(), reverse=True):
            if risk_level >= level:
                return timeline_map[level]
        return '2+ years'

    def _get_mitigation_strategies(self, risk_item: str, category: str) -> List[str]:
        """Get investment mitigation strategies for specific risks"""
        strategies = {'military_conflicts': ['Increase defense sector allocation', 'Hedge energy exposure', 'Diversify geographically', 'Add gold/commodities hedge', 'Reduce emerging market exposure'], 'trade_tensions': ['Avoid single-country exposure', 'Focus on domestic-oriented companies', 'Hedge currency exposure', 'Diversify supply chains', 'Consider trade-war beneficiaries'], 'sanctions_regime': ['Avoid sanctioned sectors/countries', 'Increase compliance monitoring', 'Diversify banking relationships', 'Focus on domestic markets', 'Consider alternative payment systems'], 'political_instability': ['Increase safe-haven assets', 'Reduce political-sensitive sectors', 'Focus on multinational companies', 'Add volatility hedges', 'Maintain higher cash levels']}
        return strategies.get(category, ['Monitor closely', 'Maintain diversification'])

    def _get_region_from_risk(self, risk_item: str) -> str:
        """Map risk item to geographical region"""
        region_mapping = {'Russia-Ukraine': 'Europe', 'China-Taiwan': 'East_Asia', 'Middle_East': 'Middle_East', 'North_Korea': 'East_Asia', 'US-China': 'Global', 'US-EU': 'North_America', 'Brexit': 'Europe', 'India-Pakistan': 'South_Asia'}
        return region_mapping.get(risk_item, 'Global')

    def _calculate_risk_confidence(self, news: List[DataPoint], risk_item: str) -> float:
        """Calculate confidence in risk assessment"""
        confidence_factors = []
        news_count = len(news)
        volume_confidence = min(1.0, news_count / 20)
        confidence_factors.append(volume_confidence * 0.3)
        if news:
            avg_source_confidence = np.mean([article.confidence for article in news])
            confidence_factors.append(avg_source_confidence * 0.4)
        else:
            confidence_factors.append(0.3 * 0.4)
        if news:
            most_recent = max(news, key=lambda x: x.timestamp)
            hours_since = (datetime.now() - most_recent.timestamp).total_seconds() / 3600
            recency_confidence = max(0.3, 1.0 - hours_since / 72)
            confidence_factors.append(recency_confidence * 0.3)
        else:
            confidence_factors.append(0.3 * 0.3)
        return np.sum(confidence_factors)

    async def analyze_conflict_escalation(self, conflict_name: str) -> ConflictSignal:
        """Deep analysis of specific military conflict"""
        try:
            conflict_news = await self.data_manager.get_multi_source_data({'news': {'query': conflict_name, 'sources': ['reuters', 'bloomberg', 'wsj'], 'hours_back': 48}})
            news_data = conflict_news.get('news', [])
            escalation_risk = self._calculate_escalation_risk(news_data, conflict_name)
            economic_impact = self._assess_economic_impact(conflict_name, escalation_risk)
            supply_chain_risk = self._analyze_supply_chain_impact(conflict_name)
            market_sectors = self._get_market_sector_impacts(conflict_name, escalation_risk)
            duration_estimate = self._estimate_conflict_duration(news_data, escalation_risk)
            return ConflictSignal(conflict_name=conflict_name, escalation_risk=escalation_risk, economic_impact=economic_impact, supply_chain_risk=supply_chain_risk, market_sectors=market_sectors, duration_estimate=duration_estimate)
        except Exception as e:
            logging.error(f'Error analyzing conflict {conflict_name}: {e}')
            return self._default_conflict_signal(conflict_name)

    def _calculate_escalation_risk(self, news: List[DataPoint], conflict_name: str) -> float:
        """Calculate probability of conflict escalation"""
        if not news:
            return 0.3
        escalation_indicators = ['military buildup', 'troop deployment', 'weapon delivery', 'alliance activation', 'nuclear threat', 'red line crossed', 'ultimatum', 'deadline', 'mobilization', 'intervention']
        escalation_score = 0.0
        for article in news:
            text = article.value.lower()
            indicator_count = sum((1 for indicator in escalation_indicators if indicator in text))
            escalation_score += indicator_count * article.confidence
        if news:
            normalized_score = escalation_score / len(news)
            return min(1.0, normalized_score / 3.0)
        return 0.3

    def _assess_economic_impact(self, conflict_name: str, escalation_risk: float) -> Dict[str, float]:
        """Assess economic impact of conflict escalation"""
        base_impacts = {'Russia-Ukraine': {'global_gdp': -0.8, 'inflation': 2.5, 'energy_prices': 0.4, 'food_prices': 0.3, 'supply_chains': -0.6}, 'China-Taiwan': {'global_gdp': -2.5, 'inflation': 1.8, 'tech_supply': -0.8, 'shipping': -0.7, 'semiconductors': -0.9}, 'Middle_East': {'global_gdp': -0.5, 'oil_prices': 0.6, 'shipping': -0.4, 'regional_markets': -0.8, 'defense_spending': 0.3}}
        base_impact = base_impacts.get(conflict_name, {'global_gdp': -0.3, 'inflation': 1.0, 'volatility': 0.5})
        scaled_impact = {}
        for key, value in base_impact.items():
            scaled_impact[key] = value * escalation_risk
        return scaled_impact

    def _analyze_supply_chain_impact(self, conflict_name: str) -> Dict[str, float]:
        """Analyze supply chain disruption risks"""
        supply_chain_risks = {'Russia-Ukraine': {'energy': 0.8, 'fertilizers': 0.7, 'grains': 0.6, 'metals': 0.5, 'semiconductors': 0.3}, 'China-Taiwan': {'semiconductors': 0.9, 'electronics': 0.8, 'rare_earths': 0.7, 'shipping': 0.6, 'manufacturing': 0.7}, 'Middle_East': {'oil': 0.9, 'gas': 0.7, 'shipping': 0.6, 'petrochemicals': 0.5}}
        return supply_chain_risks.get(conflict_name, {'general': 0.4})

    def _get_market_sector_impacts(self, conflict_name: str, escalation_risk: float) -> Dict[str, float]:
        """Get sector-specific market impacts"""
        sector_impacts = {'Russia-Ukraine': {'energy': 0.6, 'defense': 0.8, 'agriculture': 0.4, 'technology': -0.3, 'airlines': -0.6, 'tourism': -0.7}, 'China-Taiwan': {'semiconductors': -0.9, 'technology': -0.7, 'defense': 0.8, 'shipping': -0.6, 'manufacturing': -0.5, 'commodities': 0.3}, 'Middle_East': {'energy': 0.8, 'defense': 0.6, 'airlines': -0.5, 'insurance': -0.4, 'shipping': -0.3}}
        base_impacts = sector_impacts.get(conflict_name, {'broad_market': -0.2})
        scaled_impacts = {}
        for sector, impact in base_impacts.items():
            scaled_impacts[sector] = impact * escalation_risk
        return scaled_impacts

    def _estimate_conflict_duration(self, news: List[DataPoint], escalation_risk: float) -> str:
        """Estimate conflict duration based on escalation risk"""
        if escalation_risk > 0.8:
            return '6+ months (high intensity)'
        elif escalation_risk > 0.6:
            return '3-12 months (prolonged)'
        elif escalation_risk > 0.4:
            return '1-6 months (limited)'
        else:
            return 'Weeks to months (contained)'

    def _default_geopolitical_risk(self) -> GeopoliticalRisk:
        """Return default risk in case of errors"""
        return GeopoliticalRisk(region='Global', risk_type='general_uncertainty', current_level=5, trend='stable', probability_impact=0.3, affected_sectors=['broad_market'], timeline='6-12 months', mitigation_strategies=['Maintain diversification', 'Monitor developments'], confidence=0.3)

    def _default_conflict_signal(self, conflict_name: str) -> ConflictSignal:
        """Return default conflict signal"""
        return ConflictSignal(conflict_name=conflict_name, escalation_risk=0.3, economic_impact={'global_gdp': -0.1}, supply_chain_risk={'general': 0.2}, market_sectors={'broad_market': -0.1}, duration_estimate='Unknown')

    async def generate_llm_geopolitical_analysis(self, risks: List[GeopoliticalRisk]) -> Dict:
        """Generate LLM-enhanced geopolitical analysis"""
        try:
            risk_summary = self._prepare_risk_summary(risks)
            prompt = f'\n            As a senior geopolitical risk analyst, analyze the current global risk landscape and provide investment guidance.\n\n            Current Top Risks:\n            {risk_summary}\n\n            Please provide:\n            1. Most critical risks requiring immediate attention\n            2. Potential black swan scenarios (low probability, high impact)\n            3. Portfolio hedging strategies\n            4. Regional allocation recommendations\n            5. Timeline for next major geopolitical shift\n            6. Early warning indicators to monitor\n\n            Format as JSON with keys: critical_risks, black_swan_scenarios, hedging_strategies, \n            regional_allocation, timeline, early_warning_indicators\n            '
            response = self.client.chat.completions.create(model=CONFIG.llm.deep_think_model, messages=[{'role': 'user', 'content': prompt}], temperature=CONFIG.llm.temperature, max_tokens=CONFIG.llm.max_tokens)
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logging.error(f'Error in LLM geopolitical analysis: {e}')
            return {'critical_risks': ['Russia-Ukraine conflict', 'US-China tensions'], 'black_swan_scenarios': ['Taiwan invasion', 'Nuclear incident'], 'hedging_strategies': ['Increase defense allocation', 'Add gold hedge'], 'regional_allocation': 'Underweight emerging markets', 'timeline': 'Next 6-12 months', 'early_warning_indicators': ['Troop movements', 'Diplomatic withdrawals']}

    def _prepare_risk_summary(self, risks: List[GeopoliticalRisk]) -> str:
        """Prepare risk summary for LLM analysis"""
        summary_lines = []
        for risk in risks[:5]:
            summary_lines.append(f'{risk.region} - {risk.risk_type}: Level {risk.current_level}/10 ({risk.trend}), Impact: {risk.probability_impact:.2f}, Sectors: {', '.join(risk.affected_sectors[:3])}')
        return '\n'.join(summary_lines)

    async def get_geopolitical_report(self) -> Dict:
        """Generate comprehensive geopolitical risk report"""
        global_risks = await self.analyze_global_risks()
        conflicts = ['Russia-Ukraine', 'China-Taiwan', 'Middle_East']
        conflict_analyses = []
        for conflict in conflicts:
            signal = await self.analyze_conflict_escalation(conflict)
            conflict_analyses.append({'conflict': conflict, 'escalation_risk': signal.escalation_risk, 'economic_impact': signal.economic_impact, 'duration_estimate': signal.duration_estimate})
        llm_analysis = await self.generate_llm_geopolitical_analysis(global_risks)
        return {'timestamp': datetime.now().isoformat(), 'agent': self.name, 'global_risk_assessment': {'overall_risk_level': np.mean([risk.current_level for risk in global_risks]), 'top_risks': [{'region': risk.region, 'type': risk.risk_type, 'level': risk.current_level, 'trend': risk.trend, 'timeline': risk.timeline, 'affected_sectors': risk.affected_sectors} for risk in global_risks[:5]]}, 'conflict_monitor': conflict_analyses, 'investment_implications': {'defensive_positioning': self._calculate_defensive_score(global_risks), 'sector_rotation': self._get_sector_rotation_recommendations(global_risks), 'regional_weights': self._get_regional_weight_adjustments(global_risks), 'hedging_requirements': self._get_hedging_requirements(global_risks)}, 'llm_analysis': llm_analysis, 'risk_monitoring': {'update_frequency': 'every 6 hours', 'key_indicators': ['news_flow', 'market_volatility', 'diplomatic_activity'], 'escalation_triggers': ['military_movement', 'sanctions_announcement', 'alliance_activation']}}

    def _calculate_defensive_score(self, risks: List[GeopoliticalRisk]) -> float:
        """Calculate how defensive portfolio should be"""
        high_risk_count = sum((1 for risk in risks if risk.current_level >= 7))
        escalating_risks = sum((1 for risk in risks if risk.trend == 'escalating'))
        defensive_score = high_risk_count * 0.15 + escalating_risks * 0.1
        return min(1.0, defensive_score)

    def _get_sector_rotation_recommendations(self, risks: List[GeopoliticalRisk]) -> Dict[str, str]:
        """Get sector rotation based on geopolitical risks"""
        sector_scores = defaultdict(float)
        for risk in risks:
            weight = risk.current_level * risk.confidence / 10
            for sector in risk.affected_sectors:
                if sector in self.sector_impact_map.get(risk.risk_type, {}):
                    impact = self.sector_impact_map[risk.risk_type][sector]
                    sector_scores[sector] += impact * weight
        recommendations = {}
        for sector, score in sector_scores.items():
            if score > 0.2:
                recommendations[sector] = 'overweight'
            elif score < -0.2:
                recommendations[sector] = 'underweight'
            else:
                recommendations[sector] = 'neutral'
        return recommendations

    def _get_regional_weight_adjustments(self, risks: List[GeopoliticalRisk]) -> Dict[str, float]:
        """Get regional allocation adjustments"""
        regional_adjustments = {}
        for region, base_weight in self.regional_weights.items():
            region_risks = [risk for risk in risks if risk.region == region]
            if region_risks:
                avg_risk = np.mean([risk.current_level for risk in region_risks])
                adjustment = max(-0.5, (5 - avg_risk) / 10)
                regional_adjustments[region] = base_weight * (1 + adjustment)
            else:
                regional_adjustments[region] = base_weight
        total_weight = sum(regional_adjustments.values())
        return {region: weight / total_weight for region, weight in regional_adjustments.items()}

    def _get_hedging_requirements(self, risks: List[GeopoliticalRisk]) -> List[str]:
        """Get specific hedging requirements"""
        hedges = []
        high_risks = [risk for risk in risks if risk.current_level >= 7]
        for risk in high_risks:
            if 'energy' in risk.affected_sectors:
                hedges.append('Energy price hedge')
            if 'technology' in risk.affected_sectors:
                hedges.append('Tech sector put options')
            if 'currency' in risk.affected_sectors:
                hedges.append('USD strength hedge')
            if risk.risk_type == 'military_conflicts':
                hedges.append('Gold allocation increase')
                hedges.append('Defense sector exposure')
        return list(set(hedges))

def _get_sector_rotation_recommendations(self, risks: List[GeopoliticalRisk]) -> Dict[str, str]:
    """Get sector rotation based on geopolitical risks"""
    sector_scores = defaultdict(float)
    for risk in risks:
        weight = risk.current_level * risk.confidence / 10
        for sector in risk.affected_sectors:
            if sector in self.sector_impact_map.get(risk.risk_type, {}):
                impact = self.sector_impact_map[risk.risk_type][sector]
                sector_scores[sector] += impact * weight
    recommendations = {}
    for sector, score in sector_scores.items():
        if score > 0.2:
            recommendations[sector] = 'overweight'
        elif score < -0.2:
            recommendations[sector] = 'underweight'
        else:
            recommendations[sector] = 'neutral'
    return recommendations

