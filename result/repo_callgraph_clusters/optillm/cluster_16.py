# Cluster 16

class OptILMClassifier(nn.Module):

    def __init__(self, base_model, num_labels):
        super().__init__()
        self.base_model = base_model
        self.effort_encoder = nn.Sequential(nn.Linear(1, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU())
        self.classifier = nn.Linear(base_model.config.hidden_size + 64, num_labels)

    def forward(self, input_ids, attention_mask, effort):
        outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0]
        effort_encoded = self.effort_encoder(effort.unsqueeze(1))
        combined_input = torch.cat((pooled_output, effort_encoded), dim=1)
        logits = self.classifier(combined_input)
        return logits

def __init__(self, base_model, num_labels):
    super().__init__()
    self.base_model = base_model
    self.effort_encoder = nn.Sequential(nn.Linear(1, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU())
    self.classifier = nn.Linear(base_model.config.hidden_size + 64, num_labels)

class MemoryEfficientAttention(nn.Module):
    """
    Memory-efficient attention using linear attention mechanism.
    Supports automatic fallback to optimized implementations when available.
    """

    def __init__(self, hidden_size: int, num_attention_heads: int, dropout: float=0.1):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_attention_heads = num_attention_heads
        self.head_dim = hidden_size // num_attention_heads
        self.scale = self.head_dim ** (-0.5)
        self.q_proj = nn.Linear(hidden_size, hidden_size)
        self.k_proj = nn.Linear(hidden_size, hidden_size)
        self.v_proj = nn.Linear(hidden_size, hidden_size)
        self.o_proj = nn.Linear(hidden_size, hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.optimized_attention = None
        try:
            from flash_attn import flash_attn_func
            self.optimized_attention = flash_attn_func
            print('Using Flash Attention')
        except ImportError:
            pass
        if self.optimized_attention is None:
            try:
                import xformers.ops as xops
                self.optimized_attention = xops.memory_efficient_attention
                print('Using xFormers attention')
            except ImportError:
                pass

    def _linear_attention(self, q: torch.Tensor, k: torch.Tensor, v: torch.Tensor, attention_mask: Optional[torch.Tensor]=None, causal: bool=False) -> torch.Tensor:
        """Implements linear attention for more memory efficiency"""
        q = q * self.scale
        if attention_mask is not None:
            if attention_mask.dtype == torch.bool:
                attention_mask = attention_mask.float()
            k = k * attention_mask.unsqueeze(-1)
        if causal:
            batch_size, num_heads, seq_length, head_dim = q.shape
            positions = torch.arange(seq_length, device=q.device)
            causal_mask = positions.view(1, 1, -1, 1) <= positions.view(1, 1, 1, -1)
            k = k * causal_mask.float()
        context = torch.matmul(k.transpose(-2, -1), v)
        out = torch.matmul(q, context)
        return out

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor]=None, causal: bool=False) -> torch.Tensor:
        batch_size, seq_length, _ = hidden_states.size()
        q = self.q_proj(hidden_states)
        k = self.k_proj(hidden_states)
        v = self.v_proj(hidden_states)
        q = q.view(batch_size, seq_length, self.num_attention_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_length, self.num_attention_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_length, self.num_attention_heads, self.head_dim).transpose(1, 2)
        if self.optimized_attention is not None and hidden_states.device.type == 'cuda':
            if attention_mask is not None:
                if attention_mask.dtype != torch.bool:
                    attention_mask = attention_mask > 0
                attention_mask = attention_mask.view(batch_size, 1, 1, seq_length)
            try:
                attn_output = self.optimized_attention(q, k, v, attn_mask=attention_mask, causal=causal, scale=self.scale)
            except Exception as e:
                print(f'Optimized attention failed, falling back to linear attention: {e}')
                attn_output = self._linear_attention(q, k, v, attention_mask, causal)
        else:
            attn_output = self._linear_attention(q, k, v, attention_mask, causal)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_length, self.hidden_size)
        attn_output = self.o_proj(attn_output)
        return attn_output

def __init__(self, hidden_size: int, num_attention_heads: int, dropout: float=0.1):
    super().__init__()
    self.hidden_size = hidden_size
    self.num_attention_heads = num_attention_heads
    self.head_dim = hidden_size // num_attention_heads
    self.scale = self.head_dim ** (-0.5)
    self.q_proj = nn.Linear(hidden_size, hidden_size)
    self.k_proj = nn.Linear(hidden_size, hidden_size)
    self.v_proj = nn.Linear(hidden_size, hidden_size)
    self.o_proj = nn.Linear(hidden_size, hidden_size)
    self.dropout = nn.Dropout(dropout)
    self.optimized_attention = None
    try:
        from flash_attn import flash_attn_func
        self.optimized_attention = flash_attn_func
        print('Using Flash Attention')
    except ImportError:
        pass
    if self.optimized_attention is None:
        try:
            import xformers.ops as xops
            self.optimized_attention = xops.memory_efficient_attention
            print('Using xFormers attention')
        except ImportError:
            pass

class CacheManager:
    """
    Singleton cache manager for models and tokenizers.
    Thread-safe but minimizes lock contention.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self, max_size: int=5):
        if self._initialized:
            return
        with self._lock:
            if not self._initialized:
                logger.info('Initializing CacheManager singleton')
                self.max_size = max_size
                self.model_cache = OrderedDict()
                self.tokenizer_cache = OrderedDict()
                self.adapter_cache = OrderedDict()
                self.model_adapter_map = {}
                self.cache_stats = defaultdict(lambda: {'hits': 0, 'misses': 0})
                self._initialized = True
                logger.info('CacheManager singleton initialized')

    def get_or_load_model(self, model_key: str, loader_fn) -> Tuple[Any, Any]:
        """Get or load model and tokenizer with minimal locking."""
        cached_model = cached_tokenizer = None
        cache_hit = False
        with self._lock:
            if model_key in self.model_cache and model_key in self.tokenizer_cache:
                cached_model = self.model_cache[model_key]
                cached_tokenizer = self.tokenizer_cache[model_key]
                self.model_cache.move_to_end(model_key)
                self.tokenizer_cache.move_to_end(model_key)
                self.cache_stats[model_key]['hits'] += 1
                cache_hit = True
                logger.debug(f'Cache hit for model: {model_key}')
        if cache_hit:
            return (cached_model, cached_tokenizer)
        logger.info(f'Loading model and tokenizer: {model_key}')
        model, tokenizer = loader_fn()
        with self._lock:
            if model_key in self.model_cache and model_key in self.tokenizer_cache:
                cached_model = self.model_cache[model_key]
                cached_tokenizer = self.tokenizer_cache[model_key]
                self.cache_stats[model_key]['hits'] += 1
                logger.debug(f'Using already cached model: {model_key}')
                return (cached_model, cached_tokenizer)
            self.model_cache[model_key] = model
            self.tokenizer_cache[model_key] = tokenizer
            self.cache_stats[model_key]['misses'] += 1
            self.model_adapter_map[model_key] = []
            self._cleanup_caches()
            logger.info(f'Successfully cached model and tokenizer: {model_key}')
            return (model, tokenizer)

    def get_or_load_adapter(self, model_key: str, adapter_key: str, loader_fn):
        """Get or load adapter with enhanced caching."""
        cache_key = f'{model_key}_{adapter_key}'
        with self._lock:
            if cache_key in self.adapter_cache:
                adapter = self.adapter_cache[cache_key]
                self.adapter_cache.move_to_end(cache_key)
                logger.debug(f'Cache hit for adapter: {cache_key}')
                return adapter
        adapter = loader_fn()
        with self._lock:
            self.adapter_cache[cache_key] = adapter
            if model_key not in self.model_adapter_map:
                self.model_adapter_map[model_key] = []
            if adapter_key not in self.model_adapter_map[model_key]:
                self.model_adapter_map[model_key].append(adapter_key)
            self._cleanup_caches()
            logger.info(f'Successfully cached adapter: {cache_key}')
            return adapter

    def get_model_adapters(self, model_key: str) -> List[str]:
        """Get list of adapter IDs loaded for a specific model."""
        with self._lock:
            return self.model_adapter_map.get(model_key, [])

    def _cleanup_caches(self):
        """Clean up caches if they exceed max size."""
        while len(self.model_cache) > self.max_size:
            model_key, model = self.model_cache.popitem(last=False)
            if hasattr(model, 'cpu'):
                model.cpu()
            if model_key in self.model_adapter_map:
                for adapter_id in self.model_adapter_map[model_key]:
                    cache_key = f'{model_key}_{adapter_id}'
                    if cache_key in self.adapter_cache:
                        self.adapter_cache.pop(cache_key)
                self.model_adapter_map.pop(model_key)
        while len(self.tokenizer_cache) > self.max_size:
            self.tokenizer_cache.popitem(last=False)
        valid_cache_keys = {f'{model_key}_{adapter_id}' for model_key, adapter_ids in self.model_adapter_map.items() for adapter_id in adapter_ids}
        orphaned_adapters = [key for key in self.adapter_cache.keys() if key not in valid_cache_keys]
        for key in orphaned_adapters:
            adapter = self.adapter_cache.pop(key)
            if hasattr(adapter, 'cpu'):
                adapter.cpu()
        torch.cuda.empty_cache()

    @classmethod
    def get_instance(cls, max_size: int=5) -> 'CacheManager':
        """Alternative way to get the singleton instance."""
        if cls._instance is None:
            return cls(max_size)
        return cls._instance

def __new__(cls, *args, **kwargs):
    if cls._instance is None:
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instance = instance
    return cls._instance

class GoogleSearcher:

    def __init__(self, headless: bool=False, timeout: int=30):
        self.timeout = timeout
        self.headless = headless
        self.driver = None
        self.setup_driver(headless)

    def setup_driver(self, headless: bool=False):
        """Setup Chrome driver with appropriate options"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            else:
                chrome_options.add_argument('--window-size=1280,800')
                chrome_options.add_argument('--window-position=100,100')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
        except Exception as e:
            raise Exception(f'Failed to setup Chrome driver: {str(e)}')

    def detect_captcha(self) -> bool:
        """Detect if CAPTCHA is present on the page"""
        try:
            page_source = self.driver.page_source.lower()
            captcha_indicators = ['recaptcha', 'captcha', 'are you a robot', 'not a robot', 'unusual traffic', 'automated requests', "verify you're human", "verify that you're not a robot"]
            for indicator in captcha_indicators:
                if indicator in page_source:
                    return True
            try:
                self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
                return True
            except:
                pass
            try:
                self.driver.find_element(By.ID, 'captcha')
                return True
            except:
                pass
            return False
        except:
            return False

    def wait_for_captcha_resolution(self, max_wait: int=300) -> bool:
        """Wait for CAPTCHA to be resolved with user confirmation"""
        print('🚨 CAPTCHA DETECTED! 🚨')
        print('Please solve the CAPTCHA in the browser window.')
        print('After solving the CAPTCHA, press ENTER here to continue...')
        if self.headless:
            print('ERROR: CAPTCHA detected in headless mode - cannot solve automatically')
            return False
        try:
            input('Press ENTER after you have solved the CAPTCHA: ')
        except KeyboardInterrupt:
            print('\\nSearch cancelled by user')
            return False
        print('Checking if CAPTCHA has been resolved...')
        time.sleep(2)
        for attempt in range(3):
            if not self.detect_captcha():
                print('✅ CAPTCHA resolved successfully!')
                return True
            else:
                print(f'CAPTCHA still detected (attempt {attempt + 1}/3)')
                if attempt < 2:
                    response = input("CAPTCHA still present. Try again? Press ENTER to continue or 'q' to quit: ")
                    if response.lower() == 'q':
                        return False
                    time.sleep(2)
        print('❌ CAPTCHA still not resolved after 3 attempts')
        return False

    def search(self, query: str, num_results: int=10, delay_seconds: Optional[int]=None) -> List[Dict[str, str]]:
        """Perform Google search and return results"""
        if not self.driver:
            raise Exception('Chrome driver not initialized')
        try:
            print(f'Searching for: {query}')
            if not self.headless:
                print('Browser window opened')
            self.driver.get('https://www.google.com')
            time.sleep(1)
            if self.detect_captcha():
                if not self.wait_for_captcha_resolution():
                    return []
            try:
                accept_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'I agree') or contains(text(), 'Agree')]")
                accept_button.click()
                time.sleep(1)
            except:
                pass
            try:
                search_box = None
                for selector in [(By.NAME, 'q'), (By.CSS_SELECTOR, "input[type='text']"), (By.CSS_SELECTOR, "textarea[name='q']")]:
                    try:
                        search_box = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(selector))
                        break
                    except:
                        continue
                if search_box:
                    actions = ActionChains(self.driver)
                    actions.move_to_element(search_box)
                    actions.click()
                    actions.pause(0.5)
                    search_box.clear()
                    actions.send_keys(query)
                    actions.pause(0.5)
                    actions.send_keys(Keys.RETURN)
                    actions.perform()
                    time.sleep(1)
                    if self.detect_captcha():
                        if not self.wait_for_captcha_resolution():
                            return []
                else:
                    raise Exception('Could not find search box')
            except:
                print('Using direct URL navigation...')
                search_url = f'https://www.google.com/search?q={quote_plus(query)}&num={num_results}'
                self.driver.get(search_url)
                time.sleep(1)
                if self.detect_captcha():
                    if not self.wait_for_captcha_resolution():
                        return []
            wait = WebDriverWait(self.driver, 10)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g, [data-sokoban-container], div[data-async-context]')))
            except TimeoutException:
                if self.detect_captcha():
                    if self.wait_for_captcha_resolution():
                        try:
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g')))
                        except:
                            print('No results found after CAPTCHA resolution')
                            return []
                    else:
                        return []
                else:
                    print('Timeout waiting for search results')
                    return []
            results = []
            if delay_seconds is None:
                delay_seconds = random.randint(4, 32)
            if delay_seconds > 0:
                print(f'Applying {delay_seconds} second delay after search...')
                time.sleep(delay_seconds)
            print('Extracting search results...')
            try:
                print('Waiting for search results to load...')
                WebDriverWait(self.driver, 10).until(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'div.g') or driver.find_element(By.ID, 'search') or driver.find_elements(By.CSS_SELECTOR, '[data-sokoban-container]'))
            except TimeoutException:
                print('Timeout waiting for search results. Checking for CAPTCHA...')
                if self.detect_captcha():
                    if not self.wait_for_captcha_resolution():
                        return []
                    try:
                        WebDriverWait(self.driver, 10).until(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'div.g'))
                    except:
                        print('Still no results after CAPTCHA resolution')
                        return []
                else:
                    print('No CAPTCHA detected, but timeout occurred - search may have failed')
                    return []
            print(f'Current URL: {self.driver.current_url}')
            print(f'Page title: {self.driver.title}')
            search_results = []
            search_results = self.driver.find_elements(By.CSS_SELECTOR, 'div.g')
            print(f'Found {len(search_results)} results with div.g')
            if not search_results:
                all_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-hveid]')
                print(f'Found {len(all_elements)} elements with data-hveid')
                for elem in all_elements:
                    try:
                        h3 = elem.find_element(By.TAG_NAME, 'h3')
                        link = elem.find_element(By.CSS_SELECTOR, 'a[href]')
                        if h3 and link:
                            search_results.append(elem)
                    except:
                        continue
                print(f'Filtered to {len(search_results)} valid result elements')
            if not search_results:
                print('No search results found with any method')
                print('Page source sample (first 500 chars):')
                print(self.driver.page_source[:500])
                return []
            results_to_process = min(len(search_results), num_results)
            print(f'Processing {results_to_process} results...')
            for i, result in enumerate(search_results[:results_to_process]):
                try:
                    if len(results) >= num_results:
                        break
                    try:
                        url = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                        title = result.find_element(By.CSS_SELECTOR, 'h3').text
                        if not url or 'google.com' in url:
                            continue
                        snippet = ''
                        try:
                            snippet_selectors = ['.VwiC3b', '.aCOpRe', '.IsZvec']
                            for selector in snippet_selectors:
                                try:
                                    snippet_elem = result.find_element(By.CSS_SELECTOR, selector)
                                    if snippet_elem and snippet_elem.text:
                                        snippet = snippet_elem.text
                                        break
                                except:
                                    pass
                        except:
                            pass
                        results.append({'title': title, 'url': url, 'snippet': snippet or 'No description available'})
                        print(f'Extracted result {len(results)}: {title[:50]}...')
                    except NoSuchElementException:
                        print(f'Failed to parse result {i + 1}')
                        continue
                except Exception as e:
                    continue
            seen_urls = set()
            unique_results = []
            for result in results:
                if result['url'] not in seen_urls:
                    seen_urls.add(result['url'])
                    unique_results.append(result)
            print(f'Successfully extracted {len(unique_results)} unique search results (from {len(results)} total)')
            return unique_results
        except TimeoutException as e:
            print(f"Search timeout for query '{query}': {str(e)}")
            return []
        except WebDriverException as e:
            error_msg = str(e).lower()
            if 'invalid session id' in error_msg or 'session deleted' in error_msg:
                print(f'WebDriver session invalid: {str(e)}')
                self.driver = None
            else:
                print(f'WebDriver error during search: {str(e)}')
            return []
        except Exception as e:
            print(f'Unexpected error during search: {str(e)}')
            return []

    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

def setup_driver(self, headless: bool=False):
    """Setup Chrome driver with appropriate options"""
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        else:
            chrome_options.add_argument('--window-size=1280,800')
            chrome_options.add_argument('--window-position=100,100')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(self.timeout)
    except Exception as e:
        raise Exception(f'Failed to setup Chrome driver: {str(e)}')

def detect_captcha(self) -> bool:
    """Detect if CAPTCHA is present on the page"""
    try:
        page_source = self.driver.page_source.lower()
        captcha_indicators = ['recaptcha', 'captcha', 'are you a robot', 'not a robot', 'unusual traffic', 'automated requests', "verify you're human", "verify that you're not a robot"]
        for indicator in captcha_indicators:
            if indicator in page_source:
                return True
        try:
            self.driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            return True
        except:
            pass
        try:
            self.driver.find_element(By.ID, 'captcha')
            return True
        except:
            pass
        return False
    except:
        return False

def wait_for_captcha_resolution(self, max_wait: int=300) -> bool:
    """Wait for CAPTCHA to be resolved with user confirmation"""
    print('🚨 CAPTCHA DETECTED! 🚨')
    print('Please solve the CAPTCHA in the browser window.')
    print('After solving the CAPTCHA, press ENTER here to continue...')
    if self.headless:
        print('ERROR: CAPTCHA detected in headless mode - cannot solve automatically')
        return False
    try:
        input('Press ENTER after you have solved the CAPTCHA: ')
    except KeyboardInterrupt:
        print('\\nSearch cancelled by user')
        return False
    print('Checking if CAPTCHA has been resolved...')
    time.sleep(2)
    for attempt in range(3):
        if not self.detect_captcha():
            print('✅ CAPTCHA resolved successfully!')
            return True
        else:
            print(f'CAPTCHA still detected (attempt {attempt + 1}/3)')
            if attempt < 2:
                response = input("CAPTCHA still present. Try again? Press ENTER to continue or 'q' to quit: ")
                if response.lower() == 'q':
                    return False
                time.sleep(2)
    print('❌ CAPTCHA still not resolved after 3 attempts')
    return False

def search(self, query: str, num_results: int=10, delay_seconds: Optional[int]=None) -> List[Dict[str, str]]:
    """Perform Google search and return results"""
    if not self.driver:
        raise Exception('Chrome driver not initialized')
    try:
        print(f'Searching for: {query}')
        if not self.headless:
            print('Browser window opened')
        self.driver.get('https://www.google.com')
        time.sleep(1)
        if self.detect_captcha():
            if not self.wait_for_captcha_resolution():
                return []
        try:
            accept_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'I agree') or contains(text(), 'Agree')]")
            accept_button.click()
            time.sleep(1)
        except:
            pass
        try:
            search_box = None
            for selector in [(By.NAME, 'q'), (By.CSS_SELECTOR, "input[type='text']"), (By.CSS_SELECTOR, "textarea[name='q']")]:
                try:
                    search_box = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(selector))
                    break
                except:
                    continue
            if search_box:
                actions = ActionChains(self.driver)
                actions.move_to_element(search_box)
                actions.click()
                actions.pause(0.5)
                search_box.clear()
                actions.send_keys(query)
                actions.pause(0.5)
                actions.send_keys(Keys.RETURN)
                actions.perform()
                time.sleep(1)
                if self.detect_captcha():
                    if not self.wait_for_captcha_resolution():
                        return []
            else:
                raise Exception('Could not find search box')
        except:
            print('Using direct URL navigation...')
            search_url = f'https://www.google.com/search?q={quote_plus(query)}&num={num_results}'
            self.driver.get(search_url)
            time.sleep(1)
            if self.detect_captcha():
                if not self.wait_for_captcha_resolution():
                    return []
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g, [data-sokoban-container], div[data-async-context]')))
        except TimeoutException:
            if self.detect_captcha():
                if self.wait_for_captcha_resolution():
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g')))
                    except:
                        print('No results found after CAPTCHA resolution')
                        return []
                else:
                    return []
            else:
                print('Timeout waiting for search results')
                return []
        results = []
        if delay_seconds is None:
            delay_seconds = random.randint(4, 32)
        if delay_seconds > 0:
            print(f'Applying {delay_seconds} second delay after search...')
            time.sleep(delay_seconds)
        print('Extracting search results...')
        try:
            print('Waiting for search results to load...')
            WebDriverWait(self.driver, 10).until(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'div.g') or driver.find_element(By.ID, 'search') or driver.find_elements(By.CSS_SELECTOR, '[data-sokoban-container]'))
        except TimeoutException:
            print('Timeout waiting for search results. Checking for CAPTCHA...')
            if self.detect_captcha():
                if not self.wait_for_captcha_resolution():
                    return []
                try:
                    WebDriverWait(self.driver, 10).until(lambda driver: driver.find_elements(By.CSS_SELECTOR, 'div.g'))
                except:
                    print('Still no results after CAPTCHA resolution')
                    return []
            else:
                print('No CAPTCHA detected, but timeout occurred - search may have failed')
                return []
        print(f'Current URL: {self.driver.current_url}')
        print(f'Page title: {self.driver.title}')
        search_results = []
        search_results = self.driver.find_elements(By.CSS_SELECTOR, 'div.g')
        print(f'Found {len(search_results)} results with div.g')
        if not search_results:
            all_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-hveid]')
            print(f'Found {len(all_elements)} elements with data-hveid')
            for elem in all_elements:
                try:
                    h3 = elem.find_element(By.TAG_NAME, 'h3')
                    link = elem.find_element(By.CSS_SELECTOR, 'a[href]')
                    if h3 and link:
                        search_results.append(elem)
                except:
                    continue
            print(f'Filtered to {len(search_results)} valid result elements')
        if not search_results:
            print('No search results found with any method')
            print('Page source sample (first 500 chars):')
            print(self.driver.page_source[:500])
            return []
        results_to_process = min(len(search_results), num_results)
        print(f'Processing {results_to_process} results...')
        for i, result in enumerate(search_results[:results_to_process]):
            try:
                if len(results) >= num_results:
                    break
                try:
                    url = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    title = result.find_element(By.CSS_SELECTOR, 'h3').text
                    if not url or 'google.com' in url:
                        continue
                    snippet = ''
                    try:
                        snippet_selectors = ['.VwiC3b', '.aCOpRe', '.IsZvec']
                        for selector in snippet_selectors:
                            try:
                                snippet_elem = result.find_element(By.CSS_SELECTOR, selector)
                                if snippet_elem and snippet_elem.text:
                                    snippet = snippet_elem.text
                                    break
                            except:
                                pass
                    except:
                        pass
                    results.append({'title': title, 'url': url, 'snippet': snippet or 'No description available'})
                    print(f'Extracted result {len(results)}: {title[:50]}...')
                except NoSuchElementException:
                    print(f'Failed to parse result {i + 1}')
                    continue
            except Exception as e:
                continue
        seen_urls = set()
        unique_results = []
        for result in results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        print(f'Successfully extracted {len(unique_results)} unique search results (from {len(results)} total)')
        return unique_results
    except TimeoutException as e:
        print(f"Search timeout for query '{query}': {str(e)}")
        return []
    except WebDriverException as e:
        error_msg = str(e).lower()
        if 'invalid session id' in error_msg or 'session deleted' in error_msg:
            print(f'WebDriver session invalid: {str(e)}')
            self.driver = None
        else:
            print(f'WebDriver error during search: {str(e)}')
        return []
    except Exception as e:
        print(f'Unexpected error during search: {str(e)}')
        return []

class OptILMClassifier(nn.Module):

    def __init__(self, base_model, num_labels):
        super().__init__()
        self.base_model = base_model
        self.effort_encoder = nn.Sequential(nn.Linear(1, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU())
        self.classifier = nn.Linear(base_model.config.hidden_size + 64, num_labels)

    def forward(self, input_ids, attention_mask, effort):
        outputs = self.base_model(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0]
        effort_encoded = self.effort_encoder(effort.unsqueeze(1))
        combined_input = torch.cat((pooled_output, effort_encoded), dim=1)
        logits = self.classifier(combined_input)
        return logits

def __init__(self, base_model, num_labels):
    super().__init__()
    self.base_model = base_model
    self.effort_encoder = nn.Sequential(nn.Linear(1, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU())
    self.classifier = nn.Linear(base_model.config.hidden_size + 64, num_labels)

def run(system_prompt: str, initial_query: str, client, model: str) -> Tuple[str, int]:
    memory = Memory()
    query, context = extract_query(initial_query)
    completion_tokens = 0
    chunk_size = 100000
    for i in range(0, len(context), chunk_size):
        chunk = context[i:i + chunk_size]
        key_info, tokens = extract_key_information(system_prompt, chunk, query, client, model)
        completion_tokens += tokens
        for info in key_info:
            memory.add(info)
    relevant_info = memory.get_relevant(query)
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': f"\n\nI asked my assistant to read and analyse the above content page by page to help you complete this task. These are margin notes left on each page:\n'''text\n{relevant_info}\n'''\nRead again the note(s), take a deep breath and answer the query.\n{query}\n"}]
    response = client.chat.completions.create(model=model, messages=messages)
    final_response = response.choices[0].message.content.strip()
    completion_tokens += response.usage.completion_tokens
    return (final_response, completion_tokens)

class Provider:
    """Wrapper for a provider configuration and client"""

    def __init__(self, config: Dict):
        self.name = config['name']
        self.base_url = config['base_url']
        self.api_key = config['api_key']
        self.weight = config.get('weight', 1)
        self.fallback_only = config.get('fallback_only', False)
        self.model_map = config.get('model_map', {})
        self._client = None
        self.is_healthy = True
        self.last_error = None
        self.latencies = []
        self.max_concurrent = config.get('max_concurrent', None)
        if self.max_concurrent is not None:
            self._semaphore = threading.Semaphore(self.max_concurrent)
            logger.info(f'Provider {self.name} limited to {self.max_concurrent} concurrent requests')
        else:
            self._semaphore = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if not self._client:
            if 'azure' in self.base_url.lower():
                self._client = AzureOpenAI(api_key=self.api_key, azure_endpoint=self.base_url, api_version='2024-02-01', max_retries=0)
            elif 'generativelanguage.googleapis.com' in self.base_url:
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=0)
            else:
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=0)
        return self._client

    def map_model(self, model: str) -> str:
        """Map requested model to provider-specific name"""
        return self.model_map.get(model, model)

    def track_latency(self, latency: float):
        """Track request latency"""
        self.latencies.append(latency)
        if len(self.latencies) > 10:
            self.latencies.pop(0)

    def avg_latency(self) -> float:
        """Get average latency"""
        if not self.latencies:
            return 0
        return sum(self.latencies) / len(self.latencies)

    def acquire_slot(self, timeout: Optional[float]=None) -> bool:
        """
        Try to acquire a slot for this provider.
        Returns True if acquired, False if timeout or no limit.
        """
        if self._semaphore is None:
            return True
        return self._semaphore.acquire(blocking=True, timeout=timeout)

    def release_slot(self):
        """Release a slot for this provider."""
        if self._semaphore is not None:
            self._semaphore.release()

    def available_slots(self) -> Optional[int]:
        """Get number of available slots, None if unlimited."""
        if self._semaphore is None:
            return None
        return self._semaphore._value

def acquire_slot(self, timeout: Optional[float]=None) -> bool:
    """
        Try to acquire a slot for this provider.
        Returns True if acquired, False if timeout or no limit.
        """
    if self._semaphore is None:
        return True
    return self._semaphore.acquire(blocking=True, timeout=timeout)

def release_slot(self):
    """Release a slot for this provider."""
    if self._semaphore is not None:
        self._semaphore.release()

class _Completions:

    def __init__(self, proxy_client):
        self.proxy_client = proxy_client
        self._system_message_support_cache = {}

    def _filter_kwargs(self, kwargs: dict) -> dict:
        """Filter out OptiLLM-specific parameters that shouldn't be sent to providers"""
        optillm_params = {'optillm_approach', 'proxy_wrap', 'wrapped_approach', 'wrap', 'mcts_simulations', 'mcts_exploration', 'mcts_depth', 'best_of_n', 'rstar_max_depth', 'rstar_num_rollouts', 'rstar_c'}
        return {k: v for k, v in kwargs.items() if k not in optillm_params}

    def _test_system_message_support(self, provider, model: str) -> bool:
        """Test if a model supports system messages"""
        cache_key = f'{provider.name}:{model}'
        if cache_key in self._system_message_support_cache:
            return self._system_message_support_cache[cache_key]
        try:
            test_response = provider.client.chat.completions.create(model=model, messages=[{'role': 'system', 'content': 'test'}, {'role': 'user', 'content': 'hi'}], max_tokens=1, temperature=0)
            self._system_message_support_cache[cache_key] = True
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if any((pattern in error_msg for pattern in ['developer instruction', 'system message', 'not enabled', 'not supported'])):
                logger.info(f'Provider {provider.name} model {model} does not support system messages')
                self._system_message_support_cache[cache_key] = False
                return False
            self._system_message_support_cache[cache_key] = True
            return True

    def _format_messages_for_provider(self, provider, model: str, messages: list) -> list:
        """Format messages based on provider's system message support"""
        has_system = any((msg.get('role') == 'system' for msg in messages))
        if not has_system:
            return messages
        supports_system = self._test_system_message_support(provider, model)
        if supports_system:
            return messages
        formatted_messages = []
        system_content = None
        for msg in messages:
            if msg.get('role') == 'system':
                system_content = msg.get('content', '')
            elif msg.get('role') == 'user':
                if system_content:
                    formatted_messages.append({'role': 'user', 'content': f'Instructions: {system_content}\n\nUser: {msg.get('content', '')}'})
                    system_content = None
                else:
                    formatted_messages.append(msg)
            else:
                formatted_messages.append(msg)
        return formatted_messages

    def _make_request_with_timeout(self, provider, request_kwargs):
        """Make a request with timeout handling"""
        try:
            response = provider.client.chat.completions.create(**request_kwargs)
            return response
        except Exception as e:
            if 'timeout' in str(e).lower() or 'timed out' in str(e).lower():
                raise TimeoutError(f'Request to {provider.name} timed out after {self.proxy_client.request_timeout}s')
            raise e

    def create(self, **kwargs):
        """Create completion with load balancing, failover, and timeout handling"""
        if not self.proxy_client._request_semaphore.acquire(blocking=True, timeout=self.proxy_client.queue_timeout):
            raise TimeoutError(f'Request queue timeout after {self.proxy_client.queue_timeout}s - server overloaded')
        try:
            model = kwargs.get('model', 'unknown')
            attempted_providers = set()
            errors = []
            healthy_providers = [p for p in self.proxy_client.active_providers if p.is_healthy]
            if not healthy_providers:
                logger.warning('No healthy providers, trying fallback providers')
                healthy_providers = self.proxy_client.fallback_providers
            while healthy_providers:
                available_providers = [p for p in healthy_providers if p not in attempted_providers]
                if not available_providers:
                    break
                provider = self.proxy_client.router.select(available_providers)
                logger.info(f'Router selected provider: {(provider.name if provider else 'None')}')
                if not provider:
                    break
                attempted_providers.add(provider)
                slot_timeout = 10.0
                if not provider.acquire_slot(timeout=slot_timeout):
                    logger.debug(f'Provider {provider.name} at max capacity, trying next provider')
                    errors.append((provider.name, 'At max concurrent requests'))
                    continue
                try:
                    request_kwargs = self._filter_kwargs(kwargs.copy())
                    mapped_model = provider.map_model(model)
                    request_kwargs['model'] = mapped_model
                    if 'messages' in request_kwargs:
                        request_kwargs['messages'] = self._format_messages_for_provider(provider, mapped_model, request_kwargs['messages'])
                    request_kwargs['timeout'] = self.proxy_client.request_timeout
                    start_time = time.time()
                    logger.debug(f'Routing to {provider.name} with {self.proxy_client.request_timeout}s timeout')
                    response = self._make_request_with_timeout(provider, request_kwargs)
                    latency = time.time() - start_time
                    if self.proxy_client.track_latency:
                        provider.track_latency(latency)
                    logger.info(f'Request succeeded via {provider.name} in {latency:.2f}s')
                    return response
                except TimeoutError as e:
                    logger.error(f'Provider {provider.name} timed out: {e}')
                    errors.append((provider.name, str(e)))
                    if self.proxy_client.track_errors:
                        provider.is_healthy = False
                        provider.last_error = f'Timeout: {str(e)}'
                except Exception as e:
                    logger.error(f'Provider {provider.name} failed: {e}')
                    errors.append((provider.name, str(e)))
                    if self.proxy_client.track_errors:
                        provider.is_healthy = False
                        provider.last_error = str(e)
                finally:
                    provider.release_slot()
                    logger.debug(f'Released slot for provider {provider.name}')
            if self.proxy_client.fallback_client:
                logger.warning('All proxy providers failed, using fallback client')
                try:
                    fallback_kwargs = self._filter_kwargs(kwargs.copy())
                    fallback_kwargs['timeout'] = self.proxy_client.request_timeout
                    return self.proxy_client.fallback_client.chat.completions.create(**fallback_kwargs)
                except Exception as e:
                    errors.append(('fallback_client', str(e)))
            error_msg = f'All providers failed. Errors: {errors}'
            logger.error(error_msg)
            raise Exception(error_msg)
        finally:
            self.proxy_client._request_semaphore.release()

def create(self, **kwargs):
    """Create completion with load balancing, failover, and timeout handling"""
    if not self.proxy_client._request_semaphore.acquire(blocking=True, timeout=self.proxy_client.queue_timeout):
        raise TimeoutError(f'Request queue timeout after {self.proxy_client.queue_timeout}s - server overloaded')
    try:
        model = kwargs.get('model', 'unknown')
        attempted_providers = set()
        errors = []
        healthy_providers = [p for p in self.proxy_client.active_providers if p.is_healthy]
        if not healthy_providers:
            logger.warning('No healthy providers, trying fallback providers')
            healthy_providers = self.proxy_client.fallback_providers
        while healthy_providers:
            available_providers = [p for p in healthy_providers if p not in attempted_providers]
            if not available_providers:
                break
            provider = self.proxy_client.router.select(available_providers)
            logger.info(f'Router selected provider: {(provider.name if provider else 'None')}')
            if not provider:
                break
            attempted_providers.add(provider)
            slot_timeout = 10.0
            if not provider.acquire_slot(timeout=slot_timeout):
                logger.debug(f'Provider {provider.name} at max capacity, trying next provider')
                errors.append((provider.name, 'At max concurrent requests'))
                continue
            try:
                request_kwargs = self._filter_kwargs(kwargs.copy())
                mapped_model = provider.map_model(model)
                request_kwargs['model'] = mapped_model
                if 'messages' in request_kwargs:
                    request_kwargs['messages'] = self._format_messages_for_provider(provider, mapped_model, request_kwargs['messages'])
                request_kwargs['timeout'] = self.proxy_client.request_timeout
                start_time = time.time()
                logger.debug(f'Routing to {provider.name} with {self.proxy_client.request_timeout}s timeout')
                response = self._make_request_with_timeout(provider, request_kwargs)
                latency = time.time() - start_time
                if self.proxy_client.track_latency:
                    provider.track_latency(latency)
                logger.info(f'Request succeeded via {provider.name} in {latency:.2f}s')
                return response
            except TimeoutError as e:
                logger.error(f'Provider {provider.name} timed out: {e}')
                errors.append((provider.name, str(e)))
                if self.proxy_client.track_errors:
                    provider.is_healthy = False
                    provider.last_error = f'Timeout: {str(e)}'
            except Exception as e:
                logger.error(f'Provider {provider.name} failed: {e}')
                errors.append((provider.name, str(e)))
                if self.proxy_client.track_errors:
                    provider.is_healthy = False
                    provider.last_error = str(e)
            finally:
                provider.release_slot()
                logger.debug(f'Released slot for provider {provider.name}')
        if self.proxy_client.fallback_client:
            logger.warning('All proxy providers failed, using fallback client')
            try:
                fallback_kwargs = self._filter_kwargs(kwargs.copy())
                fallback_kwargs['timeout'] = self.proxy_client.request_timeout
                return self.proxy_client.fallback_client.chat.completions.create(**fallback_kwargs)
            except Exception as e:
                errors.append(('fallback_client', str(e)))
        error_msg = f'All providers failed. Errors: {errors}'
        logger.error(error_msg)
        raise Exception(error_msg)
    finally:
        self.proxy_client._request_semaphore.release()

class CBLog(dict):
    """Object for logging the number of LLM calls and tokens used in the pipeline"""
    __allowed_keys__ = {'total_tokens', 'completion_tokens', 'llm_calls'}

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        if key not in self.__allowed_keys__:
            raise KeyError(f"Key '{key}' not allowed. Allowed keys: {self.__allowed_keys__}")
        if not isinstance(value, int):
            raise TypeError(f"Value for '{key}' must be int, got {type(value).__name__}")
        super().__setitem__(key, value)

    def update(self, other=None, **kwargs):
        updates = {}
        if other:
            if isinstance(other, dict):
                updates.update(other)
            else:
                updates.update(dict(other))
        updates.update(kwargs)
        for key, value in updates.items():
            if key not in self.__allowed_keys__:
                raise KeyError(f"Key '{key}' not allowed. Allowed keys: {self.__allowed_keys__}")
            if not isinstance(value, int):
                raise TypeError(f"Value for '{key}' must be int, got {type(value).__name__}")
            self[key] = self.get(key, 0) + value

def __init__(self, *args, **kwargs):
    super().__init__()
    self.update(*args, **kwargs)

class FailingTokenizer:

    def encode(self, text):
        raise Exception('Tokenizer failed')

def encode(self, text):
    raise Exception('Tokenizer failed')

class ControlledMockClient(MockOpenAIClient):

    def __init__(self):
        super().__init__(response_delay=0.01, reasoning_tokens=1000)
        self.response_index = 0
        self.controlled_responses = ['After careful analysis, I determine that the smallest constant c = 4. This can be proven by construction and bounds analysis.', 'The minimum value is c = 4. Therefore, the answer is 4.', 'Through systematic analysis, the constant c must equal 4. The final answer is c = 4.']

    def chat_completions_create(self, **kwargs):
        result = super().chat_completions_create(**kwargs)
        if self.response_index < len(self.controlled_responses):
            result.choices[0].message.content = self.controlled_responses[self.response_index]
            self.response_index += 1
        return result

def __init__(self):
    super().__init__(response_delay=0.01, reasoning_tokens=1000)
    self.response_index = 0
    self.controlled_responses = ['After careful analysis, I determine that the smallest constant c = 4. This can be proven by construction and bounds analysis.', 'The minimum value is c = 4. Therefore, the answer is 4.', 'Through systematic analysis, the constant c must equal 4. The final answer is c = 4.']

def chat_completions_create(self, **kwargs):
    result = super().chat_completions_create(**kwargs)
    if self.response_index < len(self.controlled_responses):
        result.choices[0].message.content = self.controlled_responses[self.response_index]
        self.response_index += 1
    return result

class FailingMockClient(MockOpenAIClient):

    def __init__(self):
        super().__init__(response_delay=0.01)
        self.failure_count = 0

    def chat_completions_create(self, **kwargs):
        self.failure_count += 1
        if self.failure_count % 3 == 0:
            raise Exception('Mock API failure')
        return super().chat_completions_create(**kwargs)

def __init__(self):
    super().__init__(response_delay=0.01)
    self.failure_count = 0

def chat_completions_create(self, **kwargs):
    self.failure_count += 1
    if self.failure_count % 3 == 0:
        raise Exception('Mock API failure')
    return super().chat_completions_create(**kwargs)

class EnhancedMockClient(MockOpenAIClient):

    def __init__(self):
        super().__init__(response_delay=0.1, reasoning_tokens=3000)
        self.problem_responses = {'Advanced Algebra': 'This requires systematic case analysis. Let me examine small values systematically. After checking cases x,y,z < 100, the equation x³ + y³ = z³ - 1 has solutions like (x,y,z) = (1,1,1) since 1³ + 1³ = 2 = 2³ - 6... Actually, let me recalculate: 1³ + 1³ = 2, and z³ - 1 = 2 means z³ = 3, so z ≈ 1.44. Let me check (2,2,2): 8 + 8 = 16 = 8 - 1 = 7? No. This is a difficult Diophantine equation requiring advanced techniques.', 'Number Theory': "I'll prove this by contradiction using Euclid's method. Assume there are only finitely many primes of the form 4k+3: p₁, p₂, ..., pₙ. Consider N = 4(p₁p₂...pₙ) + 3. Since N ≡ 3 (mod 4), at least one prime factor of N must be ≡ 3 (mod 4). But N is not divisible by any of p₁, p₂, ..., pₙ, so there must be another prime of the form 4k+3, contradicting our assumption. Therefore, there are infinitely many such primes.", 'Combinatorics': 'This is a stars and bars problem with constraints. We need to distribute 20 balls into 5 boxes with each box having at least 2 balls. First, place 2 balls in each box (using 10 balls). Now we need to distribute the remaining 10 balls into 5 boxes with no constraints. Using stars and bars: C(10+5-1, 5-1) = C(14,4) = 1001 ways.', 'Geometry': "This is a form of Weitzenböck's inequality. We can prove this using the relationship between area and sides. For a triangle with area S and sides a,b,c, we have S = √[s(s-a)(s-b)(s-c)] where s = (a+b+c)/2. We want to show a² + b² + c² ≥ 4√3 · S. This can be proven using the isoperimetric inequality and Jensen's inequality applied to the convex function f(x) = x²."}

    def chat_completions_create(self, **kwargs):
        result = super().chat_completions_create(**kwargs)
        messages = kwargs.get('messages', [])
        for message in messages:
            content = message.get('content', '')
            for prob_type, response in self.problem_responses.items():
                if any((keyword in content for keyword in prob_type.lower().split())):
                    result.choices[0].message.content = response
                    return result
        result.choices[0].message.content = 'This is a complex problem requiring careful analysis. Let me work through it step by step with rigorous reasoning.'
        return result

def __init__(self):
    super().__init__(response_delay=0.1, reasoning_tokens=3000)
    self.problem_responses = {'Advanced Algebra': 'This requires systematic case analysis. Let me examine small values systematically. After checking cases x,y,z < 100, the equation x³ + y³ = z³ - 1 has solutions like (x,y,z) = (1,1,1) since 1³ + 1³ = 2 = 2³ - 6... Actually, let me recalculate: 1³ + 1³ = 2, and z³ - 1 = 2 means z³ = 3, so z ≈ 1.44. Let me check (2,2,2): 8 + 8 = 16 = 8 - 1 = 7? No. This is a difficult Diophantine equation requiring advanced techniques.', 'Number Theory': "I'll prove this by contradiction using Euclid's method. Assume there are only finitely many primes of the form 4k+3: p₁, p₂, ..., pₙ. Consider N = 4(p₁p₂...pₙ) + 3. Since N ≡ 3 (mod 4), at least one prime factor of N must be ≡ 3 (mod 4). But N is not divisible by any of p₁, p₂, ..., pₙ, so there must be another prime of the form 4k+3, contradicting our assumption. Therefore, there are infinitely many such primes.", 'Combinatorics': 'This is a stars and bars problem with constraints. We need to distribute 20 balls into 5 boxes with each box having at least 2 balls. First, place 2 balls in each box (using 10 balls). Now we need to distribute the remaining 10 balls into 5 boxes with no constraints. Using stars and bars: C(10+5-1, 5-1) = C(14,4) = 1001 ways.', 'Geometry': "This is a form of Weitzenböck's inequality. We can prove this using the relationship between area and sides. For a triangle with area S and sides a,b,c, we have S = √[s(s-a)(s-b)(s-c)] where s = (a+b+c)/2. We want to show a² + b² + c² ≥ 4√3 · S. This can be proven using the isoperimetric inequality and Jensen's inequality applied to the convex function f(x) = x²."}

class MonitoringMockClient(MockOpenAIClient):

    def __init__(self):
        super().__init__(response_delay=0.05, reasoning_tokens=2500)
        self.detailed_responses = True

    def chat_completions_create(self, **kwargs):
        result = super().chat_completions_create(**kwargs)
        if 'verifying' in str(kwargs.get('messages', [])):
            result.choices[0].message.content = 'VERIFICATION: The solution appears CORRECT with high confidence. The reasoning is sound and the final answer is properly justified. Confidence: 9/10.'
        elif 'improving' in str(kwargs.get('messages', [])):
            result.choices[0].message.content = "IMPROVEMENT: The original solution can be enhanced by adding more rigorous justification. Here's the improved version with stronger mathematical foundations..."
        else:
            result.choices[0].message.content = "Let me solve this step by step. First, I'll analyze the problem structure. Then I'll apply appropriate mathematical techniques. The solution involves careful reasoning and verification. \\boxed{42}"
        return result

def __init__(self):
    super().__init__(response_delay=0.05, reasoning_tokens=2500)
    self.detailed_responses = True

def chat_completions_create(self, **kwargs):
    result = super().chat_completions_create(**kwargs)
    if 'verifying' in str(kwargs.get('messages', [])):
        result.choices[0].message.content = 'VERIFICATION: The solution appears CORRECT with high confidence. The reasoning is sound and the final answer is properly justified. Confidence: 9/10.'
    elif 'improving' in str(kwargs.get('messages', [])):
        result.choices[0].message.content = "IMPROVEMENT: The original solution can be enhanced by adding more rigorous justification. Here's the improved version with stronger mathematical foundations..."
    else:
        result.choices[0].message.content = "Let me solve this step by step. First, I'll analyze the problem structure. Then I'll apply appropriate mathematical techniques. The solution involves careful reasoning and verification. \\boxed{42}"
    return result

class ConsistentMockClient(MockOpenAIClient):

    def chat_completions_create(self, **kwargs):
        result = super().chat_completions_create(**kwargs)
        result.choices[0].message.content = 'The solution is x = 5. Final answer: 5'
        return result

def chat_completions_create(self, **kwargs):
    result = super().chat_completions_create(**kwargs)
    result.choices[0].message.content = 'The solution is x = 5. Final answer: 5'
    return result

class TestRequestBatcher(unittest.TestCase):
    """Test the core RequestBatcher functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.batcher = RequestBatcher(max_batch_size=4, max_wait_ms=100)
        self.test_responses = []

        def mock_processor(requests):
            """Mock batch processor that returns simple responses"""
            responses = []
            for i, req in enumerate(requests):
                responses.append({'id': f'test-{i}', 'object': 'chat.completion', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': f'Response to request {i}'}, 'finish_reason': 'stop'}], 'usage': {'completion_tokens': 10, 'total_tokens': 20}})
            return responses
        self.batcher.set_processor(mock_processor)

    def tearDown(self):
        """Clean up after tests"""
        self.batcher.shutdown()

    def test_single_request(self):
        """Test that single requests work correctly"""
        request_data = {'model': 'test-model', 'prompt': 'Hello'}
        response = self.batcher.add_request(request_data)
        self.assertIsInstance(response, dict)
        self.assertEqual(response['object'], 'chat.completion')
        self.assertEqual(response['choices'][0]['message']['content'], 'Response to request 0')

    def test_batch_formation(self):
        """Test that multiple requests form a batch"""

        def send_request(request_id):
            request_data = {'model': 'test-model', 'prompt': f'Request {request_id}'}
            return self.batcher.add_request(request_data)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(send_request, i) for i in range(3)]
            responses = [future.result() for future in futures]
        self.assertEqual(len(responses), 3)
        for i, response in enumerate(responses):
            self.assertIsInstance(response, dict)
            self.assertEqual(response['object'], 'chat.completion')

    def test_batch_timeout(self):
        """Test that partial batches process after timeout"""
        start_time = time.time()
        request_data = {'model': 'test-model', 'prompt': 'Single request'}
        response = self.batcher.add_request(request_data)
        elapsed_time = time.time() - start_time
        self.assertGreater(elapsed_time, 0.09)
        self.assertIsInstance(response, dict)

    def test_incompatible_requests(self):
        """Test that incompatible requests are properly handled"""
        request_data = {'model': 'test-model', 'stream': True}
        with self.assertRaises(BatchingError):
            self.batcher.add_request(request_data)

    def test_processor_error_handling(self):
        """Test that processor errors are handled correctly"""

        def failing_processor(requests):
            raise Exception('Processor failed')
        batcher = RequestBatcher(max_batch_size=2, max_wait_ms=50)
        batcher.set_processor(failing_processor)
        try:
            request_data = {'model': 'test-model', 'prompt': 'Test'}
            with self.assertRaises(BatchingError):
                batcher.add_request(request_data)
        finally:
            batcher.shutdown()

    def test_batch_stats(self):
        """Test that batch statistics are collected correctly"""
        for i in range(5):
            request_data = {'model': 'test-model', 'prompt': f'Request {i}'}
            self.batcher.add_request(request_data)
        stats = self.batcher.get_stats()
        self.assertGreater(stats['total_requests'], 0)
        self.assertGreater(stats['total_batches'], 0)
        self.assertGreater(stats['avg_batch_size'], 0)

def failing_processor(requests):
    raise Exception('Processor failed')

