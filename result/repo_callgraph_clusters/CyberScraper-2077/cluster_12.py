# Cluster 12

class WebExtractor:

    def __init__(self, model_name: str='gpt-4o-mini', model_kwargs: Dict[str, Any]=None, proxy: Optional[str]=None, scraper_config: ScraperConfig=None, tor_config: TorConfig=None):
        model_kwargs = model_kwargs or {}
        if isinstance(model_name, str) and model_name.startswith('ollama:'):
            self.model = OllamaModelManager.get_model(model_name[7:])
        elif isinstance(model_name, OllamaModel):
            self.model = model_name
        elif model_name.startswith('gemini-'):
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            self.model = ChatGoogleGenerativeAI(model=model_name, **model_kwargs)
        else:
            self.model = Models.get_model(model_name, **model_kwargs)
        self.model_name = model_name
        self.scraper_config = scraper_config or ScraperConfig()
        self.playwright_scraper = PlaywrightScraper(config=self.scraper_config)
        self.html_scraper = HTMLScraper()
        self.json_scraper = JSONScraper()
        self.proxy_manager = ProxyManager(proxy)
        self.markdown_formatter = MarkdownFormatter()
        self.current_url = None
        self.current_content = None
        self.preprocessed_content = None
        self.conversation_history: List[str] = []
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=32000, chunk_overlap=200, length_function=self.num_tokens_from_string)
        self.max_tokens = 128000 if model_name == 'gpt-4o-mini' else 16385
        self.query_cache = {}
        self.content_hash = None
        self.tor_config = tor_config or TorConfig()
        self.tor_scraper = TorScraper(self.tor_config)

    @staticmethod
    def num_tokens_from_string(string: str) -> int:
        encoding = tiktoken.encoding_for_model('gpt-4o-mini')
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def _hash_content(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def get_website_name(self, url: str) -> str:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.split('.')[0].capitalize()

    @lru_cache(maxsize=100)
    async def _cached_api_call(self, content_hash: str, query: str) -> str:
        prompt_template = get_prompt_for_model(self.model_name)
        full_prompt = prompt_template.format(webpage_content=self.preprocessed_content, query=query)
        if isinstance(self.model, OllamaModel):
            return await self.model.generate(prompt=full_prompt)
        else:
            chain = prompt_template | self.model
            response = await chain.ainvoke({'webpage_content': self.preprocessed_content, 'query': query})
            return response.content

    async def process_query(self, user_input: str, progress_callback=None) -> str:
        if user_input.lower().startswith('http'):
            parts = user_input.split(maxsplit=3)
            url = parts[0]
            pages = parts[1] if len(parts) > 1 and (not parts[1].startswith('-')) else None
            url_pattern = parts[2] if len(parts) > 2 and (not parts[2].startswith('-')) else None
            handle_captcha = '-captcha' in user_input.lower()
            website_name = self.get_website_name(url)
            if progress_callback:
                progress_callback(f'Fetching content from {website_name}...')
            response = await self._fetch_url(url, pages, url_pattern, handle_captcha, progress_callback)
        elif not self.current_content:
            response = 'Please provide a URL first before asking for information.'
        else:
            if progress_callback:
                progress_callback('Extracting information...')
            response = await self._extract_info(user_input)
        self.conversation_history.append(f'Human: {user_input}')
        self.conversation_history.append(f'AI: {response}')
        return response

    async def _fetch_url(self, url: str, pages: Optional[str]=None, url_pattern: Optional[str]=None, handle_captcha: bool=False, progress_callback=None) -> str:
        self.current_url = url
        try:
            if TorScraper.is_onion_url(url):
                if progress_callback:
                    progress_callback('Fetching content through Tor network...')
                content = await self.tor_scraper.fetch_content(url)
                self.current_content = content
            else:
                if progress_callback:
                    progress_callback(f'Fetching content from {url}')
                contents = await self.playwright_scraper.fetch_content(url, proxy=None, pages=pages, url_pattern=url_pattern, handle_captcha=handle_captcha)
                self.current_content = '\n'.join(contents)
            if progress_callback:
                progress_callback('Preprocessing content...')
            self.preprocessed_content = self._preprocess_content(self.current_content)
            new_hash = self._hash_content(self.preprocessed_content)
            if self.content_hash != new_hash:
                self.content_hash = new_hash
                self.query_cache.clear()
            source_type = 'Tor network' if TorScraper.is_onion_url(url) else 'regular web'
            return f"I've fetched and preprocessed the content from {self.current_url} via {source_type}" + (f' (pages: {pages})' if pages else '') + '. What would you like to know about it?'
        except TorException as e:
            return f'Error accessing onion service: {str(e)}'
        except Exception as e:
            return f'Error fetching content: {str(e)}'

    def _preprocess_content(self, content: str) -> str:
        soup = BeautifulSoup(content, 'html.parser')
        for script in soup(['script', 'style']):
            script.decompose()
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        for tag in soup(['header', 'footer', 'nav', 'aside']):
            tag.decompose()
        for tag in soup.find_all():
            if len(tag.get_text(strip=True)) == 0:
                tag.extract()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
        text = '\n'.join((chunk for chunk in chunks if chunk))
        return text

    async def _extract_info(self, query: str) -> str:
        if not self.preprocessed_content:
            return 'Please provide a URL first before asking for information.'
        content_hash = self._hash_content(self.preprocessed_content)
        if self.content_hash != content_hash:
            self.content_hash = content_hash
            self.query_cache.clear()
        cache_key = (content_hash, query)
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        content_tokens = self.num_tokens_from_string(self.preprocessed_content)
        if content_tokens <= self.max_tokens - 1000:
            extracted_data = await self._cached_api_call(content_hash, query)
        else:
            chunks = self.optimized_text_splitter(self.preprocessed_content)
            all_extracted_data = []
            for i, chunk in enumerate(chunks):
                chunk_data = await self._cached_api_call(self._hash_content(chunk), query)
                all_extracted_data.append(chunk_data)
            extracted_data = self._merge_json_chunks(all_extracted_data)
        formatted_result = self._format_result(extracted_data, query)
        self.query_cache[cache_key] = formatted_result
        return formatted_result

    def _format_result(self, extracted_data: str, query: str) -> Union[str, Tuple[str, pd.DataFrame], BytesIO]:
        try:
            json_data = json.loads(extracted_data)
            if 'json' in query.lower():
                return self._format_as_json(json.dumps(json_data))
            elif 'csv' in query.lower():
                csv_string, df = self._format_as_csv(json.dumps(json_data))
                return (f'```csv\n{csv_string}\n```', df)
            elif 'excel' in query.lower():
                return self._format_as_excel(json.dumps(json_data))
            elif 'sql' in query.lower():
                return self._format_as_sql(json.dumps(json_data))
            elif 'html' in query.lower():
                return self._format_as_html(json.dumps(json_data))
            elif isinstance(json_data, list) and all((isinstance(item, dict) for item in json_data)):
                csv_string, df = self._format_as_csv(json.dumps(json_data))
                return (f'```csv\n{csv_string}\n```', df)
            else:
                return self._format_as_json(json.dumps(json_data))
        except json.JSONDecodeError:
            return self._format_as_text(extracted_data)

    def optimized_text_splitter(self, text: str) -> List[str]:
        return self.text_splitter.split_text(text)

    def _merge_json_chunks(self, chunks: List[str]) -> str:
        merged_data = []
        for chunk in chunks:
            try:
                data = json.loads(chunk)
                if isinstance(data, list):
                    merged_data.extend(data)
                else:
                    merged_data.append(data)
            except json.JSONDecodeError:
                print(f'Error decoding JSON chunk: {chunk[:100]}...')
        return json.dumps(merged_data)

    def _format_as_json(self, data: str) -> str:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        try:
            parsed_data = json.loads(data)
            return f'```json\n{json.dumps(parsed_data, indent=2)}\n```'
        except json.JSONDecodeError:
            return f'Error: Invalid JSON data. Raw data: {data[:500]}...'

    def _format_as_csv(self, data: str) -> Tuple[str, pd.DataFrame]:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        else:
            code_block_pattern = '```\\s*([\\s\\S]*?)\\s*```'
            match = re.search(code_block_pattern, data)
            if match:
                data = match.group(1)
        try:
            parsed_data = json.loads(data)
            if not parsed_data:
                return ('No data to convert to CSV.', pd.DataFrame())
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=parsed_data[0].keys())
            writer.writeheader()
            writer.writerows(parsed_data)
            csv_string = output.getvalue()
            df = pd.DataFrame(parsed_data)
            return (csv_string, df)
        except json.JSONDecodeError as e:
            error_msg = f'Error: Invalid JSON data. Raw data: {data[:500]}...'
            return (error_msg, pd.DataFrame())
        except Exception as e:
            error_msg = f'Error: Failed to convert data to CSV. {str(e)}'
            return (error_msg, pd.DataFrame())

    def _format_as_excel(self, data: str) -> Tuple[BytesIO, pd.DataFrame]:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        try:
            parsed_data = json.loads(data)
            if not parsed_data:
                return (BytesIO(b'No data to convert to Excel.'), pd.DataFrame())
            df = pd.DataFrame(parsed_data)
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            excel_buffer.seek(0)
            return (excel_buffer, df)
        except json.JSONDecodeError:
            error_msg = f'Error: Invalid JSON data. Raw data: {data[:500]}...'
            return (BytesIO(error_msg.encode()), pd.DataFrame())
        except Exception as e:
            error_msg = f'Error: Failed to convert data to Excel. {str(e)}'
            return (BytesIO(error_msg.encode()), pd.DataFrame())

    def _format_as_sql(self, data: str) -> str:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        try:
            parsed_data = json.loads(data)
            if not parsed_data:
                return 'No data to convert to SQL.'
            fields = ', '.join([f'{k} TEXT' for k in parsed_data[0].keys()])
            sql = f'CREATE TABLE extracted_data ({fields});\n'
            for row in parsed_data:
                escaped_values = [str(v).replace("'", "''") for v in row.values()]
                values = ', '.join([f"'{v}'" for v in escaped_values])
                sql += f'INSERT INTO extracted_data VALUES ({values});\n'
            return f'```sql\n{sql}\n```'
        except json.JSONDecodeError:
            return f'Error: Invalid JSON data. Raw data: {data[:500]}...'

    def _format_as_html(self, data: str) -> str:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        try:
            parsed_data = json.loads(data)
            if not parsed_data:
                return 'No data to convert to HTML.'
            html = '<table>\n<tr>\n'
            html += ''.join([f'<th>{k}</th>' for k in parsed_data[0].keys()])
            html += '</tr>\n'
            for row in parsed_data:
                html += '<tr>\n'
                html += ''.join([f'<td>{v}</td>' for v in row.values()])
                html += '</tr>\n'
            html += '</table>'
            return f'```html\n{html}\n```'
        except json.JSONDecodeError:
            return f'Error: Invalid JSON data. Raw data: {data[:500]}...'

    def _format_as_text(self, data: str) -> str:
        json_pattern = '```json\\s*([\\s\\S]*?)\\s*```'
        match = re.search(json_pattern, data)
        if match:
            data = match.group(1)
        try:
            parsed_data = json.loads(data)
            return '\n'.join([', '.join([f'{k}: {v}' for k, v in item.items()]) for item in parsed_data])
        except json.JSONDecodeError:
            return data

    def format_to_markdown(self, text: str) -> str:
        return self.markdown_formatter.to_markdown(text)

    def format_from_markdown(self, markdown_text: str) -> str:
        return self.markdown_formatter.from_markdown(markdown_text)

    @staticmethod
    async def list_ollama_models() -> List[str]:
        return await OllamaModel.list_models()

def _format_result(self, extracted_data: str, query: str) -> Union[str, Tuple[str, pd.DataFrame], BytesIO]:
    try:
        json_data = json.loads(extracted_data)
        if 'json' in query.lower():
            return self._format_as_json(json.dumps(json_data))
        elif 'csv' in query.lower():
            csv_string, df = self._format_as_csv(json.dumps(json_data))
            return (f'```csv\n{csv_string}\n```', df)
        elif 'excel' in query.lower():
            return self._format_as_excel(json.dumps(json_data))
        elif 'sql' in query.lower():
            return self._format_as_sql(json.dumps(json_data))
        elif 'html' in query.lower():
            return self._format_as_html(json.dumps(json_data))
        elif isinstance(json_data, list) and all((isinstance(item, dict) for item in json_data)):
            csv_string, df = self._format_as_csv(json.dumps(json_data))
            return (f'```csv\n{csv_string}\n```', df)
        else:
            return self._format_as_json(json.dumps(json_data))
    except json.JSONDecodeError:
        return self._format_as_text(extracted_data)

def _merge_json_chunks(self, chunks: List[str]) -> str:
    merged_data = []
    for chunk in chunks:
        try:
            data = json.loads(chunk)
            if isinstance(data, list):
                merged_data.extend(data)
            else:
                merged_data.append(data)
        except json.JSONDecodeError:
            print(f'Error decoding JSON chunk: {chunk[:100]}...')
    return json.dumps(merged_data)

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

def clean_data_for_sheets(df):

    def clean_value(val):
        if pd.isna(val):
            return ''
        if isinstance(val, (int, float)):
            return str(val)
        return str(val).replace('\n', ' ').replace('\r', '')
    for col in df.columns:
        df[col] = df[col].map(clean_value)
    if 'comments' in df.columns:
        df['comments'] = df['comments'].astype(str)
    return df

