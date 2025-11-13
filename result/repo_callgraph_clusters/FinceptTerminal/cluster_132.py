# Cluster 132

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

@property
def api_client(self):
    """PERFORMANCE: Lazy API client initialization"""
    if not self._api_client_initialized:
        self._initialize_api_client()
    return self._api_client

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

@property
def api_client(self):
    """PERFORMANCE: Lazy API client initialization"""
    if not self._api_client_initialized:
        self._initialize_api_client()
    return self._api_client

