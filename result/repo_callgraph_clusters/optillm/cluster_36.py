# Cluster 36

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

def close(self):
    """Close the browser driver"""
    if self.driver:
        self.driver.quit()
        self.driver = None

