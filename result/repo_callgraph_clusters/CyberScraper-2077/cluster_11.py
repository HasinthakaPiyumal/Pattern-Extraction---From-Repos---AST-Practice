# Cluster 11

def main():
    st.set_page_config(page_title='CyberScraper 2077', page_icon='app/icons/radiation.png', layout='wide')
    load_css()
    handle_oauth_callback()
    user_avatar_path = 'app/icons/man.png'
    ai_avatar_path = 'app/icons/skull.png'
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = load_chat_history()
    if 'current_chat_id' not in st.session_state or st.session_state.current_chat_id not in st.session_state.chat_history:
        if st.session_state.chat_history:
            st.session_state.current_chat_id = next(iter(st.session_state.chat_history))
        else:
            new_chat_id = str(datetime.now().timestamp())
            st.session_state.chat_history[new_chat_id] = {'messages': [], 'date': datetime.now().strftime('%Y-%m-%d')}
            st.session_state.current_chat_id = new_chat_id
            save_chat_history(st.session_state.chat_history)
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = 'gpt-4o-mini'
    if 'web_scraper_chat' not in st.session_state:
        st.session_state.web_scraper_chat = None
    with st.sidebar:
        st.title('Conversation History')
        st.subheader('Select Model')
        default_models = ['gpt-4o-mini', 'gpt-3.5-turbo', 'gemini-1.5-flash', 'gemini-pro']
        ollama_models = st.session_state.get('ollama_models', [])
        all_models = default_models + [f'ollama:{model}' for model in ollama_models]
        selected_model = st.selectbox('Choose a model', all_models, index=all_models.index(st.session_state.selected_model) if st.session_state.selected_model in all_models else 0)
        if selected_model != st.session_state.selected_model:
            st.session_state.selected_model = selected_model
            st.session_state.web_scraper_chat = None
            st.rerun()
        if not os.getenv('OPENAI_API_KEY') and any((model.startswith(('gpt-', 'text-')) for model in all_models)):
            st.warning('OpenAI API Key is not set. Some models may not be available.')
        if not os.getenv('GOOGLE_API_KEY') and any((model.startswith('gemini-') for model in all_models)):
            st.warning('Google API Key is not set. Gemini models may not be available.')
        st.session_state.use_current_browser = st.checkbox('Use Current Browser (No Docker)', value=False, help="Works Natively, Doesn't Work with Docker. if a website is blocking your browser, you can use this option to use the current browser instead of opening a new one.")
        if st.button('Refresh Ollama Models'):
            with st.spinner('Fetching Ollama models...'):
                st.session_state.ollama_models = asyncio.run(list_ollama_models())
            st.success(f'Found {len(st.session_state.ollama_models)} Ollama models')
            st.rerun()
        if st.button('+ 🗨️ New Chat', key='new_chat', use_container_width=True):
            new_chat_id = str(datetime.now().timestamp())
            st.session_state.chat_history[new_chat_id] = {'messages': [], 'date': datetime.now().strftime('%Y-%m-%d'), 'name': '🗨️ New Chat'}
            st.session_state.current_chat_id = new_chat_id
            st.session_state.web_scraper_chat = None
            save_chat_history(st.session_state.chat_history)
            st.rerun()
        grouped_chats = {}
        for chat_id, chat_data in st.session_state.chat_history.items():
            date_group = get_date_group(chat_data['date'])
            if date_group not in grouped_chats:
                grouped_chats[date_group] = []
            grouped_chats[date_group].append((chat_id, chat_data))
        for date_group, chats in grouped_chats.items():
            st.markdown(f"<div class='date-group'>{date_group}</div>", unsafe_allow_html=True)
            for chat_id, chat_data in chats:
                button_label = chat_data.get('name', '🗨️ Unnamed Chat')
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    if st.button(button_label, key=f'history_{chat_id}', use_container_width=True):
                        st.session_state.current_chat_id = chat_id
                        messages = chat_data['messages']
                        last_url = get_last_url_from_chat(messages)
                        if last_url and (not st.session_state.web_scraper_chat):
                            st.session_state.web_scraper_chat = initialize_web_scraper_chat(last_url)
                        st.rerun()
                with col2:
                    if st.button('🗑️', key=f'delete_{chat_id}'):
                        del st.session_state.chat_history[chat_id]
                        save_chat_history(st.session_state.chat_history)
                        if st.session_state.current_chat_id == chat_id:
                            if st.session_state.chat_history:
                                st.session_state.current_chat_id = next(iter(st.session_state.chat_history))
                            else:
                                st.session_state.current_chat_id = None
                            st.session_state.web_scraper_chat = None
                        st.rerun()
    st.markdown('\n        <h1 style="text-align: center; font-size: 30px; color: #333;">CyberScraper 2077</h1>\n        ', unsafe_allow_html=True)
    display_info_icons()
    if st.session_state.current_chat_id not in st.session_state.chat_history:
        if st.session_state.chat_history:
            st.session_state.current_chat_id = next(iter(st.session_state.chat_history))
        else:
            new_chat_id = str(datetime.now().timestamp())
            st.session_state.chat_history[new_chat_id] = {'messages': [], 'date': datetime.now().strftime('%Y-%m-%d')}
            st.session_state.current_chat_id = new_chat_id
            save_chat_history(st.session_state.chat_history)
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for index, message in enumerate(st.session_state.chat_history[st.session_state.current_chat_id]['messages']):
            if message['role'] == 'user':
                st.markdown(render_message('user', message['content'], user_avatar_path), unsafe_allow_html=True)
            else:
                with st.container():
                    st.markdown(render_message('assistant', '', ai_avatar_path), unsafe_allow_html=True)
                    display_message_with_sheets_upload(message, index)
        st.markdown('</div>', unsafe_allow_html=True)
    prompt = st.chat_input('Enter the URL to scrape or ask a question regarding the data', key='user_input')
    if prompt:
        st.session_state.chat_history[st.session_state.current_chat_id]['messages'].append({'role': 'user', 'content': prompt})
        if not st.session_state.web_scraper_chat:
            st.session_state.web_scraper_chat = initialize_web_scraper_chat()
        if prompt.lower().startswith('http'):
            website_name = get_website_name(prompt)
            st.session_state.chat_history[st.session_state.current_chat_id]['name'] = website_name
            st.info(f'Scraping {website_name}... This may take a moment.')
        with st.chat_message('assistant'):
            try:
                full_response = loading_animation(safe_process_message, st.session_state.web_scraper_chat, prompt)
                if isinstance(full_response, str) and (not full_response.startswith('Error:')):
                    st.success('Scraping completed successfully!')
                st.write('Debug: Full response type:', type(full_response))
                if full_response is not None:
                    if isinstance(full_response, tuple) and len(full_response) == 2 and isinstance(full_response[1], BytesIO):
                        st.session_state.chat_history[st.session_state.current_chat_id]['messages'].append({'role': 'assistant', 'content': full_response[0]})
                    else:
                        st.session_state.chat_history[st.session_state.current_chat_id]['messages'].append({'role': 'assistant', 'content': full_response})
                    save_chat_history(st.session_state.chat_history)
            except Exception as e:
                st.error(f'An unexpected error occurred: {str(e)}')
            save_chat_history(st.session_state.chat_history)
            st.rerun()
    st.markdown('\n        <p style="text-align: center; font-size: 12px; color: #666666;">CyberScraper 2077 can make mistakes sometimes. Report any issues to the developers.</p>\n        ', unsafe_allow_html=True)

class PlaywrightScraper(BaseScraper):

    def __init__(self, config: ScraperConfig=ScraperConfig()):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG if config.debug else logging.INFO)
        self.config = config
        self.chrome_process = None
        self.temp_user_data_dir = None

    async def fetch_content(self, url: str, proxy: Optional[str]=None, pages: Optional[str]=None, url_pattern: Optional[str]=None, handle_captcha: bool=False) -> List[str]:
        async with async_playwright() as p:
            if self.config.use_current_browser:
                browser = await self.launch_and_connect_to_chrome(p)
            else:
                browser = await self.launch_browser(p, proxy, handle_captcha)
            try:
                context = await self.create_context(browser, proxy)
                page = await context.new_page()
                if self.config.use_stealth:
                    await self.apply_stealth_settings(page)
                await self.set_browser_features(page)
                if handle_captcha:
                    await self.handle_captcha(page, url)
                contents = await self.scrape_multiple_pages(page, url, pages, url_pattern)
            except Exception as e:
                self.logger.error(f'Error during scraping: {str(e)}')
                contents = [f'Error: {str(e)}']
            finally:
                if not self.config.use_current_browser:
                    await browser.close()
                    self.logger.info('Browser closed after scraping.')
        return contents

    async def handle_captcha(self, page: Page, url: str):
        self.logger.info('Waiting for user to solve CAPTCHA...')
        await page.goto(url, wait_until=self.config.wait_for, timeout=self.config.timeout)
        print('Please solve the CAPTCHA in the browser window.')
        print('Once solved, press Enter in this console to continue...')
        input()
        await page.wait_for_load_state('networkidle')
        self.logger.info('CAPTCHA handling completed.')

    async def launch_and_connect_to_chrome(self, playwright):
        if self.chrome_process is None:
            self.temp_user_data_dir = tempfile.mkdtemp(prefix='chrome_debug_profile_')
            chrome_executable = self.get_chrome_executable()
            command = [chrome_executable, f'--user-data-dir={self.temp_user_data_dir}', '--remote-debugging-port=9222', '--no-first-run', '--no-default-browser-check']
            self.chrome_process = subprocess.Popen(command)
            self.logger.info('Launched Chrome with remote debugging.')
        for _ in range(30):
            try:
                browser = await playwright.chromium.connect_over_cdp('http://localhost:9222')
                self.logger.info('Successfully connected to Chrome.')
                return browser
            except Exception as e:
                self.logger.debug(f'Connection attempt failed: {str(e)}')
                await asyncio.sleep(1)
        raise Exception('Failed to connect to Chrome after 30 seconds')

    def get_chrome_executable(self):
        system = platform.system()
        if system == 'Darwin':
            return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        elif system == 'Linux':
            return 'google-chrome'
        else:
            raise NotImplementedError(f'Unsupported operating system: {system}')

    def __del__(self):
        if self.chrome_process:
            self.chrome_process.terminate()
            self.chrome_process.wait()
            self.logger.info('Chrome process terminated.')
        if self.temp_user_data_dir:
            import shutil
            shutil.rmtree(self.temp_user_data_dir, ignore_errors=True)
            self.logger.info(f'Temporary user data directory removed: {self.temp_user_data_dir}')

    async def connect_to_current_browser(self, playwright):
        system = platform.system()
        if system == 'Darwin':
            subprocess.Popen(['open', '-a', 'Google Chrome', '--args', '--remote-debugging-port=9222'])
        elif system == 'Linux':
            subprocess.Popen(['google-chrome', '--remote-debugging-port=9222'])
        elif system == 'Windows':
            subprocess.Popen(['start', 'chrome', '--remote-debugging-port=9222'], shell=True)
        else:
            raise NotImplementedError(f'Connecting to current browser is not implemented for {system}')
        self.logger.info('Waiting for browser to start...')
        for _ in range(30):
            try:
                browser = await playwright.chromium.connect_over_cdp('http://localhost:9222')
                self.logger.info('Successfully connected to the browser.')
                return browser
            except Exception as e:
                self.logger.debug(f'Connection attempt failed: {str(e)}')
                await asyncio.sleep(1)
        raise Exception('Failed to connect to the current browser after 30 seconds')

    async def launch_browser(self, playwright, proxy: Optional[str]=None, handle_captcha: bool=False) -> Browser:
        return await playwright.chromium.launch(headless=self.config.headless and (not handle_captcha), args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-infobars', '--window-position=0,0', '--ignore-certifcate-errors', '--ignore-certifcate-errors-spki-list'], proxy={'server': proxy} if proxy else None)

    async def create_context(self, browser: Browser, proxy: Optional[str]=None) -> BrowserContext:
        return await browser.new_context(viewport={'width': 1920, 'height': 1080}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', proxy={'server': proxy} if proxy else None, java_script_enabled=True, ignore_https_errors=True)

    async def apply_stealth_settings(self, page: Page):
        await page.evaluate("\n            () => {\n                Object.defineProperty(navigator, 'webdriver', {\n                    get: () => undefined\n                });\n\n                Object.defineProperty(navigator, 'languages', {\n                    get: () => ['en-US', 'en']\n                });\n\n                Object.defineProperty(navigator, 'plugins', {\n                    get: () => [1, 2, 3, 4, 5]\n                });\n\n                const originalQuery = window.navigator.permissions.query;\n                window.navigator.permissions.query = (parameters) => (\n                    parameters.name === 'notifications' ?\n                        Promise.resolve({ state: Notification.permission }) :\n                        originalQuery(parameters)\n                );\n            }\n        ")

    async def set_browser_features(self, page: Page):
        if self.config.use_custom_headers:
            await page.set_extra_http_headers({'Accept-Language': 'en-US,en;q=0.9', 'Accept-Encoding': 'gzip, deflate, br', 'Referer': 'https://www.google.com/', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-User': '?1', 'Upgrade-Insecure-Requests': '1'})

    async def scrape_multiple_pages(self, page: Page, base_url: str, pages: Optional[str]=None, url_pattern: Optional[str]=None) -> List[str]:
        contents = []
        if not url_pattern:
            url_pattern = self.detect_url_pattern(base_url)
        if not url_pattern and (not pages):
            self.logger.info(f'Scraping single page: {base_url}')
            content = await self.navigate_and_get_content(page, base_url)
            contents.append(content)
        else:
            page_numbers = self.parse_page_numbers(pages) if pages else [1]
            for page_num in page_numbers:
                current_url = self.apply_url_pattern(base_url, url_pattern, page_num) if url_pattern else base_url
                self.logger.info(f'Scraping page {page_num}: {current_url}')
                content = await self.navigate_and_get_content(page, current_url)
                contents.append(content)
                if page_num < len(page_numbers):
                    await asyncio.sleep(random.uniform(1, 2))
        return contents

    async def navigate_and_get_content(self, page: Page, url: str) -> str:
        try:
            self.logger.info(f'Navigating to {url}')
            await page.goto(url, wait_until=self.config.wait_for, timeout=self.config.timeout)
            self.logger.info(f'Successfully loaded {url}')
            await asyncio.sleep(self.config.delay_after_load)
            self.logger.info('Extracting page content')
            content = await page.content()
            self.logger.info(f'Successfully extracted content (length: {len(content)})')
            return content
        except Exception as e:
            self.logger.error(f'Error navigating to {url}: {str(e)}')
            return f'Error: Failed to load {url}. {str(e)}'

    async def bypass_cloudflare(self, page: Page, url: str) -> str:
        max_retries = 3
        for _ in range(max_retries):
            await page.reload(wait_until=self.config.wait_for, timeout=self.config.timeout)
            if self.config.simulate_human:
                await self.simulate_human_behavior(page)
            else:
                await asyncio.sleep(2)
            content = await page.content()
            if 'Cloudflare' not in content or 'ray ID' not in content.lower():
                self.logger.info('Successfully bypassed Cloudflare')
                return content
            self.logger.info('Cloudflare still detected, retrying...')
        self.logger.warning('Failed to bypass Cloudflare after multiple attempts')
        return content

    async def simulate_human_behavior(self, page: Page):
        await page.evaluate('window.scrollBy(0, window.innerHeight / 2)')
        await asyncio.sleep(random.uniform(0.5, 1))
        for _ in range(2):
            x = random.randint(100, 500)
            y = random.randint(100, 500)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
        elements = await page.query_selector_all('a, button, input, select')
        if elements:
            random_element = random.choice(elements)
            await random_element.hover()
            await asyncio.sleep(random.uniform(0.3, 0.7))

    def detect_url_pattern(self, url: str) -> Optional[str]:
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        for param, value in query.items():
            if value and value[0].isdigit():
                return f'{param}={{{param}}}'
        path_parts = parsed_url.path.split('/')
        for i, part in enumerate(path_parts):
            if part.isdigit():
                path_parts[i] = '{page}'
                return '/'.join(path_parts)
        return None

    def apply_url_pattern(self, base_url: str, pattern: str, page_num: int) -> str:
        parsed_url = urlparse(base_url)
        if '=' in pattern:
            query = parse_qs(parsed_url.query)
            param, value = pattern.split('=')
            query[param] = [value.format(**{param: page_num})]
            return urlunparse(parsed_url._replace(query=urlencode(query, doseq=True)))
        elif '{page}' in pattern:
            return urlunparse(parsed_url._replace(path=pattern.format(page=page_num)))
        else:
            return base_url

    def parse_page_numbers(self, pages: Optional[str]) -> List[int]:
        if not pages:
            return [1]
        page_numbers = []
        for part in pages.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                page_numbers.extend(range(start, end + 1))
            else:
                page_numbers.append(int(part))
        return sorted(set(page_numbers))

    async def extract(self, content: str) -> Dict[str, Any]:
        return {'raw_content': content}

def __del__(self):
    if self.chrome_process:
        self.chrome_process.terminate()
        self.chrome_process.wait()
        self.logger.info('Chrome process terminated.')
    if self.temp_user_data_dir:
        import shutil
        shutil.rmtree(self.temp_user_data_dir, ignore_errors=True)
        self.logger.info(f'Temporary user data directory removed: {self.temp_user_data_dir}')

