# Cluster 45

class BrowserBase(BaseModule):
    """
    A tool for interacting with web browsers using Selenium.
    Allows agents to navigate to URLs, interact with elements, extract information,
    and more from web pages.
    
    Key Features:
    - Auto-initialization: Browser is automatically initialized when any method is first called
    - Auto-cleanup: Browser is automatically closed when the instance is destroyed
    - No manual initialization or cleanup required
    """
    timeout: int = Field(default=10, description='Default timeout in seconds for browser operations')
    browser_type: str = Field(default='chrome', description="Type of browser to use ('chrome', 'firefox', 'safari', 'edge')")
    headless: bool = Field(default=False, description='Whether to run the browser in headless mode')
    user_data_dir: Optional[str] = Field(default=None, description='User data directory for persistent browser sessions')

    def __init__(self, name: str='Browser Tool', browser_type: str='chrome', headless: bool=False, timeout: int=10, **kwargs):
        """
        Initialize the browser tool with Selenium WebDriver.
        
        Args:
            name (str): Name of the tool
            browser_type (str): Type of browser to use ('chrome', 'firefox', 'safari', 'edge')
            headless (bool): Whether to run the browser in headless mode
            timeout (int): Default timeout in seconds for browser operations
            **kwargs: Additional keyword arguments for parent class initialization
        """
        super().__init__(name=name, timeout=timeout, browser_type=browser_type, headless=headless, **kwargs)
        self.driver = None
        self.element_references = {}

    def _check_driver_initialized(self) -> Union[None, Dict[str, Any]]:
        """
        Check if the browser driver is initialized. If not, initialize it automatically.
        
        Returns:
            Union[None, Dict[str, Any]]: None if driver is initialized, error response if initialization fails
        """
        if not self.driver:
            init_result = self.initialize_browser()
            if init_result['status'] == 'error':
                return init_result
        return None

    def _get_selector_by_type(self, selector_type: str) -> Union[str, Dict[str, Any]]:
        """
        Get the Selenium By selector for the given selector type.
        
        Args:
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            
        Returns:
            Union[str, Dict[str, Any]]: The By selector or error response
        """
        by_type = SELECTOR_MAP.get(selector_type.lower())
        if not by_type:
            return {'status': 'error', 'message': f'Invalid selector type: {selector_type}'}
        return by_type

    def _wait_for_page_load(self, timeout: Optional[int]=None) -> bool:
        """
        Wait for the page to load completely.
        
        Args:
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            bool: True if page loaded, False if timed out
        """
        timeout = timeout or self.timeout
        try:
            WebDriverWait(self.driver, timeout).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            return True
        except TimeoutException:
            return False

    def _parse_element_reference(self, ref: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse an element reference into selector type and selector.
        
        Args:
            ref (str): Element reference ID from the page snapshot
            
        Returns:
            Tuple[Optional[str], Optional[str], Optional[str]]: 
                (selector_type, selector, error_message) - error_message is None if successful
        """
        if not self.element_references:
            return (None, None, 'No page snapshot available. Use browser_snapshot or navigate_to_url first.')
        stored_ref = self.element_references.get(ref)
        if not stored_ref:
            return (None, None, f"Element reference '{ref}' not found. Use browser_snapshot or navigate_to_url first.")
        if ':' in stored_ref:
            ref_parts = stored_ref.split(':', 1)
            if len(ref_parts) != 2:
                return (None, None, f'Invalid stored reference format: {stored_ref}')
            selector_type, selector = ref_parts
            return (selector_type, selector, None)
        return (None, None, f'Invalid stored reference format: {stored_ref}')

    def _find_element_with_wait(self, by_type: str, selector: str, timeout: Optional[int]=None, wait_condition=EC.presence_of_element_located) -> Tuple[Optional[Any], Optional[str]]:
        """
        Find an element on the page with wait condition.
        
        Args:
            by_type (str): Selenium By selector type
            selector (str): The selector string
            timeout (int, optional): Custom timeout for this operation
            wait_condition: The EC condition to wait for
            
        Returns:
            Tuple[Optional[Any], Optional[str]]: (element, error_message) - error_message is None if successful
        """
        timeout = timeout or self.timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(wait_condition((by_type, selector)))
            return (element, None)
        except TimeoutException:
            return (None, f'Element not found or condition not met with selector: {selector}')
        except Exception as e:
            logger.error(f'Error finding element {selector}: {str(e)}')
            return (None, str(e))

    def _handle_function_params(self, function_params: Optional[list], function_name: str, param_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract parameters from nested function_params format.
        
        Args:
            function_params (list, optional): Nested function parameters
            function_name (str): The function name to look for
            param_mapping (Dict[str, str]): Mapping of parameter names
            
        Returns:
            Dict[str, Any]: Extracted parameters
        """
        result = {}
        if not function_params:
            return result
        for param in function_params:
            fn_name = param.get('function_name', '')
            if fn_name == function_name or fn_name in param_mapping.get('alt_names', []):
                args = param.get('function_args', {})
                for param_name, result_name in param_mapping.items():
                    if param_name == 'alt_names':
                        continue
                    if param_name in args:
                        result[result_name] = args[param_name]
                break
        return result

    def initialize_browser(self, function_params: list=None) -> Dict[str, Any]:
        """
        Start or restart a browser session. This method is called automatically when needed.
        
        Note: This method is now called automatically by other browser methods when the browser
        is not initialized. Manual initialization is no longer required.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "initialize_browser", "function_args": {}}]
           
        Args:
            function_params (list, optional): Nested function parameters
        
        Returns:
            Dict[str, Any]: Status information about the browser initialization
        """
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning(f'Error closing existing browser session: {str(e)}')
            options = None
            if self.browser_type == 'chrome':
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-gpu-sandbox')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                if self.user_data_dir:
                    options.add_argument(f'--user-data-dir={self.user_data_dir}')
                    logger.info(f'Using user data directory: {self.user_data_dir}')
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            elif self.browser_type == 'firefox':
                from selenium.webdriver.firefox.options import Options
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                self.driver = webdriver.Firefox(options=options)
            elif self.browser_type == 'safari':
                self.driver = webdriver.Safari()
            elif self.browser_type == 'edge':
                from selenium.webdriver.edge.options import Options
                options = Options()
                if self.headless:
                    options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-gpu-sandbox')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                if self.user_data_dir:
                    options.add_argument(f'--user-data-dir={self.user_data_dir}')
                    logger.info(f'Using user data directory: {self.user_data_dir}')
                self.driver = webdriver.Edge(options=options)
            else:
                return {'status': 'error', 'message': f'Unsupported browser type: {self.browser_type}'}
            self.driver.set_page_load_timeout(self.timeout)
            return {'status': 'success', 'message': f'Browser {self.browser_type} initialized successfully'}
        except Exception as e:
            logger.error(f'Error initializing browser: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def navigate_to_url(self, url: str=None, timeout: int=None, function_params: list=None) -> Dict[str, Any]:
        """
        Navigate to a URL and capture a snapshot of the page. This provides element references used for interaction.
        
        This function supports multiple parameter styles:
        1. Standard style: url parameter
        2. Nested function_params style:
           function_params=[{"function_name": "navigate_to_url", "function_args": {"url": "..."}}]
        
        Args:
            url (str, optional): The complete URL (with https://) to navigate to
            timeout (int, optional): Custom timeout in seconds (default: 10)
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Information about the navigation result and page snapshot
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        if function_params and (not url):
            params = self._handle_function_params(function_params, 'navigate_to_url', {'url': 'url', 'timeout': 'timeout', 'alt_names': ['browser_navigate']})
            url = params.get('url')
            timeout = params.get('timeout', timeout)
        if not url:
            return {'status': 'error', 'message': 'URL parameter is required'}
        timeout = timeout or self.timeout
        try:
            self.driver.get(url)
            page_loaded = self._wait_for_page_load(timeout)
            if not page_loaded:
                logger.warning(f'Page load timeout for URL: {url}, but continuing with snapshot')
            snapshot_result = self.browser_snapshot()
            if snapshot_result['status'] == 'success':
                return {'status': 'success', 'url': url, 'title': self.driver.title, 'current_url': self.driver.current_url, 'snapshot': {'interactive_elements': snapshot_result.get('interactive_elements', [])}}
            else:
                return {'status': 'partial_success', 'url': url, 'title': self.driver.title, 'current_url': self.driver.current_url, 'snapshot_error': snapshot_result.get('message', 'Unknown error capturing snapshot')}
        except TimeoutException:
            return {'status': 'timeout', 'message': f'Timed out loading URL: {url}'}
        except Exception as e:
            logger.error(f'Error navigating to URL {url}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def find_element(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
        """
        Find an element on the current page and return information about it.
        
        Args:
            selector (str): The selector to find the element
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Information about the found element
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        timeout = timeout or self.timeout
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            element, error = self._find_element_with_wait(by_type, selector, timeout, EC.presence_of_element_located)
            if error:
                return {'status': 'not_found', 'message': f'Element not found with {selector_type}: {selector}'}
            element_properties = self._extract_element_properties(element, selector)
            return {'status': 'success', 'element': element_properties}
        except Exception as e:
            logger.error(f'Error finding element {selector}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def _extract_element_properties(self, element, selector: str) -> Dict[str, Any]:
        """
        Extract common properties from a WebElement.
        
        Args:
            element: The Selenium WebElement
            selector (str): The selector used to find the element (for error messages)
            
        Returns:
            Dict[str, Any]: Element properties
        """
        element_properties = {'text': element.text, 'tag_name': element.tag_name, 'is_displayed': element.is_displayed(), 'is_enabled': element.is_enabled()}
        for attr in ['href', 'id', 'class']:
            try:
                value = element.get_attribute(attr)
                if value:
                    element_properties[attr] = value
            except StaleElementReferenceException:
                logger.warning(f'Element became stale when trying to get {attr} attribute for {selector}')
            except Exception as e:
                logger.warning(f'Could not get {attr} attribute for {selector}: {str(e)}')
        return element_properties

    def find_multiple_elements(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
        """
        Find multiple elements on the current page and return information about them.
        
        Args:
            selector (str): The selector to find the elements
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Information about the found elements
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        timeout = timeout or self.timeout
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            element, error = self._find_element_with_wait(by_type, selector, timeout, EC.presence_of_element_located)
            if error:
                return {'status': 'not_found', 'message': f'No elements found with {selector_type}: {selector}'}
            elements = self.driver.find_elements(by_type, selector)
            elements_properties = []
            for idx, element in enumerate(elements):
                try:
                    element_properties = self._extract_element_properties(element, f'{selector}[{idx}]')
                    element_properties['index'] = idx
                    elements_properties.append(element_properties)
                except StaleElementReferenceException:
                    logger.warning(f'Element {idx} became stale while extracting properties')
                except Exception as e:
                    logger.warning(f'Error extracting properties for element {idx}: {str(e)}')
            return {'status': 'success', 'count': len(elements_properties), 'elements': elements_properties}
        except Exception as e:
            logger.error(f'Error finding elements {selector}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def click_element(self, selector: str, selector_type: str='css', timeout: int=None) -> Dict[str, Any]:
        """
        Click on an element on the current page.
        
        Args:
            selector (str): The selector to find the element
            selector_type (str): Type of selector ('css', 'xpath', 'id', 'class', 'name', 'tag')
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            Dict[str, Any]: Result of the click operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        timeout = timeout or self.timeout
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            element, error = self._find_element_with_wait(by_type, selector, timeout, EC.element_to_be_clickable)
            if error:
                return {'status': 'not_found', 'message': f'Element not clickable with {selector_type}: {selector}'}
            element.click()
            page_loaded = self._wait_for_page_load(timeout)
            if not page_loaded:
                return {'status': 'partial_success', 'message': 'Element clicked, but page load timed out', 'selector': selector, 'current_url': self.driver.current_url}
            return {'status': 'success', 'message': f'Clicked element with {selector_type}: {selector}', 'current_url': self.driver.current_url, 'title': self.driver.title}
        except Exception as e:
            logger.error(f'Error clicking element {selector}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def input_text(self, element: str=None, ref: str=None, text: str=None, submit: bool=False, slowly: bool=True, function_params: list=None) -> Dict[str, Any]:
        """
        Type text into a form field, search box, or other input element using a reference ID from a snapshot.
        
        This function only works with element references from a snapshot. Use browser_snapshot
        or navigate_to_url first to capture the page elements.
        
        This function supports multiple parameter styles:
        1. Standard style: element (description), ref (element ID), text
        2. Nested function_params style:
           function_params=[{"function_name": "browser_type", "function_args": {...}}]
        
        Args:
            element (str, optional): Human-readable description of the element (e.g., 'Search field', 'Username input')
            ref (str, optional): Element ID from the page snapshot (e.g., 'e0', 'e1', 'e2') - NOT a CSS selector
            text (str, optional): Text to input into the element
            submit (bool): Press Enter after typing to submit forms (default: false)
            slowly (bool): Type one character at a time to trigger JS events (default: true)
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Result of the text input operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        if function_params:
            params = self._handle_function_params(function_params, 'input_text', {'element': 'element', 'ref': 'ref', 'text': 'text', 'submit': 'submit', 'slowly': 'slowly', 'alt_names': ['browser_type']})
            element = params.get('element', element)
            ref = params.get('ref', ref)
            text = params.get('text', text)
            if 'submit' in params:
                submit = params['submit']
            if 'slowly' in params:
                slowly = params['slowly']
        if not ref or not text:
            return {'status': 'error', 'message': 'Both ref and text parameters are required'}
        selector_type, selector, error = self._parse_element_reference(ref)
        if error:
            return {'status': 'error', 'message': error}
        element_desc = element or ref
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            web_element, error = self._find_element_with_wait(by_type, selector, self.timeout, EC.element_to_be_clickable)
            if error:
                return {'status': 'not_found', 'message': f'Element not found: {element_desc}'}
            web_element.clear()
            if slowly:
                for char in text:
                    web_element.send_keys(char)
                    time.sleep(0.05)
            else:
                web_element.send_keys(text)
            if submit:
                from selenium.webdriver.common.keys import Keys
                web_element.send_keys(Keys.ENTER)
                page_loaded = self._wait_for_page_load(self.timeout)
                if not page_loaded:
                    self.browser_snapshot()
                    return {'status': 'partial_success', 'message': 'Text entered and submitted, but page load timed out', 'element': element_desc, 'text': text}
                snapshot_result = self.browser_snapshot()
                if snapshot_result['status'] != 'success':
                    logger.warning(f'Failed to capture snapshot after form submission: {snapshot_result.get('message')}')
            return {'status': 'success', 'message': f'Successfully input text into {element_desc}' + (' and submitted' if submit else ''), 'element': element_desc, 'text': text}
        except TimeoutException:
            return {'status': 'not_found', 'message': f'Element not found: {element_desc}'}
        except Exception as e:
            logger.error(f'Error inputting text to element {element_desc}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def get_page_content(self) -> Dict[str, Any]:
        """
        Get the current page title, URL and body content.
        
        Returns:
            Dict[str, Any]: Information about the current page
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            title = self.driver.title
            current_url = self.driver.current_url
            body_content = self.driver.execute_script('\n                var body = document.body;\n                return body ? body.outerHTML : "";\n            ')
            element_summary = self.driver.execute_script('\n                // Get common interactive elements\n                var summary = {\n                    links: [],\n                    buttons: [],\n                    inputs: [],\n                    forms: []\n                };\n                \n                // Get links\n                var links = document.querySelectorAll(\'a\');\n                for (var i = 0; i < Math.min(links.length, 20); i++) {\n                    var link = links[i];\n                    summary.links.push({\n                        text: link.textContent.trim().substring(0, 50),\n                        href: link.getAttribute(\'href\'),\n                        id: link.id,\n                        class: link.className\n                    });\n                }\n                \n                // Get buttons\n                var buttons = document.querySelectorAll(\'button, input[type="button"], input[type="submit"]\');\n                for (var i = 0; i < Math.min(buttons.length, 20); i++) {\n                    var button = buttons[i];\n                    summary.buttons.push({\n                        text: button.textContent ? button.textContent.trim().substring(0, 50) : button.value,\n                        id: button.id,\n                        class: button.className,\n                        type: button.type\n                    });\n                }\n                \n                // Get inputs\n                var inputs = document.querySelectorAll(\'input:not([type="button"]):not([type="submit"]), textarea, select\');\n                for (var i = 0; i < Math.min(inputs.length, 20); i++) {\n                    var input = inputs[i];\n                    summary.inputs.push({\n                        type: input.type,\n                        name: input.name,\n                        id: input.id,\n                        placeholder: input.placeholder\n                    });\n                }\n                \n                // Get forms\n                var forms = document.querySelectorAll(\'form\');\n                for (var i = 0; i < Math.min(forms.length, 10); i++) {\n                    var form = forms[i];\n                    summary.forms.push({\n                        id: form.id,\n                        action: form.action,\n                        method: form.method\n                    });\n                }\n                \n                return summary;\n            ')
            return {'status': 'success', 'title': title, 'url': current_url, 'body_content': body_content, 'element_summary': element_summary}
        except Exception as e:
            logger.error(f'Error getting page content: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def switch_to_frame(self, frame_reference: str, reference_type: str='index') -> Dict[str, Any]:
        """
        Switch to a frame on the page.
        
        Args:
            frame_reference (str): Reference to the frame (index, name, or ID)
            reference_type (str): Type of reference ('index', 'name', 'id', 'element')
            
        Returns:
            Dict[str, Any]: Result of the frame switch operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            if reference_type == 'index':
                try:
                    index = int(frame_reference)
                    self.driver.switch_to.frame(index)
                except ValueError:
                    return {'status': 'error', 'message': f'Invalid frame index: {frame_reference}'}
            elif reference_type == 'name' or reference_type == 'id':
                self.driver.switch_to.frame(frame_reference)
            elif reference_type == 'element':
                selector_parts = frame_reference.split(':', 1)
                if len(selector_parts) != 2:
                    return {'status': 'error', 'message': "Element reference must be in format 'selector_type:selector'"}
                selector_type, selector = selector_parts
                element_result = self.find_element(selector, selector_type)
                if element_result['status'] != 'success':
                    return {'status': 'error', 'message': f'Could not find frame element: {element_result['message']}'}
                selector_map = {'css': By.CSS_SELECTOR, 'xpath': By.XPATH, 'id': By.ID, 'class': By.CLASS_NAME, 'name': By.NAME, 'tag': By.TAG_NAME}
                by_type = selector_map.get(selector_type.lower())
                element = self.driver.find_element(by_type, selector)
                self.driver.switch_to.frame(element)
            else:
                return {'status': 'error', 'message': f'Invalid reference type: {reference_type}'}
            return {'status': 'success', 'message': f'Switched to frame using {reference_type}: {frame_reference}'}
        except Exception as e:
            logger.error(f'Error switching to frame {frame_reference}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def switch_to_window(self, window_reference: str, reference_type: str='index') -> Dict[str, Any]:
        """
        Switch to a window or tab.
        
        Args:
            window_reference (str): Reference to the window (index, handle, or title)
            reference_type (str): Type of reference ('index', 'handle', 'title')
            
        Returns:
            Dict[str, Any]: Result of the window switch operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            window_handles = self.driver.window_handles
            if not window_handles:
                return {'status': 'error', 'message': 'No window handles available'}
            if reference_type == 'index':
                try:
                    index = int(window_reference)
                    if index < 0 or index >= len(window_handles):
                        return {'status': 'error', 'message': f'Window index out of range: {index}'}
                    self.driver.switch_to.window(window_handles[index])
                except ValueError:
                    return {'status': 'error', 'message': f'Invalid window index: {window_reference}'}
            elif reference_type == 'handle':
                if window_reference not in window_handles:
                    return {'status': 'error', 'message': f'Window handle not found: {window_reference}'}
                self.driver.switch_to.window(window_reference)
            elif reference_type == 'title':
                current_handle = self.driver.current_window_handle
                window_found = False
                for handle in window_handles:
                    try:
                        self.driver.switch_to.window(handle)
                        if self.driver.title == window_reference:
                            window_found = True
                            break
                    except Exception:
                        pass
                if not window_found:
                    self.driver.switch_to.window(current_handle)
                    return {'status': 'error', 'message': f"No window with title '{window_reference}' found"}
            else:
                return {'status': 'error', 'message': f'Invalid reference type: {reference_type}'}
            return {'status': 'success', 'message': f'Switched to window using {reference_type}: {window_reference}', 'title': self.driver.title, 'url': self.driver.current_url}
        except Exception as e:
            logger.error(f'Error switching to window {window_reference}: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def select_dropdown_option(self, select_selector: str, option_value: str, select_by: str='value', selector_type: str='css') -> Dict[str, Any]:
        """
        Select an option from a dropdown
        select_by can be 'value', 'text', or 'index'
        
        Args:
            select_selector (str): The selector to find the dropdown element
            option_value (str): The value to select (depends on select_by)
            select_by (str): Method to select by ('value', 'text', 'index')
            selector_type (str): Type of selector for the dropdown
            
        Returns:
            Dict[str, Any]: Result of the selection operation
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            from selenium.webdriver.support.ui import Select
            by_type = self._get_selector_by_type(selector_type)
            if isinstance(by_type, dict):
                return by_type
            element, error = self._find_element_with_wait(by_type, select_selector, self.timeout, EC.presence_of_element_located)
            if error:
                return {'status': 'not_found', 'message': f'Dropdown element not found with {selector_type}: {select_selector}'}
            select = Select(element)
            if select_by.lower() == 'value':
                select.select_by_value(option_value)
            elif select_by.lower() == 'text':
                select.select_by_visible_text(option_value)
            elif select_by.lower() == 'index':
                try:
                    select.select_by_index(int(option_value))
                except ValueError:
                    return {'status': 'error', 'message': f'Invalid index value: {option_value}. Must be an integer.'}
            else:
                return {'status': 'error', 'message': f'Invalid select_by option: {select_by}'}
            return {'status': 'success', 'message': f'Selected option with {select_by}: {option_value}'}
        except Exception as e:
            logger.error(f'Error selecting dropdown option: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def close_browser(self) -> Dict[str, Any]:
        """
        Close the browser and end the session. Call this when you're done to free resources.
        
        Returns:
            Dict[str, Any]: Status of the browser closure
        """
        if not self.driver:
            return {'status': 'success', 'message': 'Browser already closed'}
        try:
            self.driver.quit()
            self.driver = None
            return {'status': 'success', 'message': 'Browser closed successfully'}
        except Exception as e:
            logger.error(f'Error closing browser: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def browser_click(self, element: str=None, ref: str=None, function_params: list=None) -> Dict[str, Any]:
        """
        Click on a button, link, or other clickable element using a reference ID from a snapshot.
        
        This function only works with element references from a snapshot. You MUST call browser_snapshot
        or navigate_to_url first to capture the page elements.
        
        Common usage pattern:
        1. First get a snapshot: browser_snapshot() or navigate_to_url()
        2. Find the element reference (e.g. 'e0', 'e1') from the snapshot's interactive_elements
        3. Use that reference to click: browser_click(element='Login button', ref='e0')
        
        This function supports multiple parameter styles:
        1. Standard style: element (description), ref (element ID)
        2. Nested function_params style:
           function_params=[{"function_name": "browser_click", "function_args": {...}}]
        
        Args:
            element (str, optional): Human-readable description of what you're clicking (e.g., 'Login button', 'Next page link')
            ref (str, optional): Element ID from the page snapshot (e.g., 'e0', 'e1', 'e2') - NOT a CSS selector
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: Result of the click operation with detailed feedback
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        if function_params and (not ref):
            params = self._handle_function_params(function_params, 'browser_click', {'element': 'element', 'ref': 'ref'})
            element = params.get('element', element)
            ref = params.get('ref', ref)
        if not ref:
            return {'status': 'error', 'message': 'Element reference (ref) parameter is required. You must first call browser_snapshot() or navigate_to_url() to get element references.', 'required_steps': ['1. Call browser_snapshot() or navigate_to_url() to get page elements', "2. Find the element reference (e.g. 'e0') in the response's interactive_elements", "3. Use that reference to click: browser_click(element='Button name', ref='e0')"]}
        if not self.element_references:
            return {'status': 'error', 'message': 'No element references found. You must first capture a page snapshot.', 'required_steps': ['1. Call browser_snapshot() or navigate_to_url() to capture the page state', '2. Use the element references returned in the snapshot']}
        selector_type, selector, error = self._parse_element_reference(ref)
        if error:
            return {'status': 'error', 'message': error, 'help': "Make sure you're using a valid element reference from a recent snapshot"}
        element_desc = element or ref
        by_type = self._get_selector_by_type(selector_type)
        if isinstance(by_type, dict):
            return by_type
        try:
            try:
                element_exists = self.driver.find_element(by_type, selector)
            except Exception:
                return {'status': 'not_found', 'message': f'Element not found: {element_desc}', 'suggestion': 'The page may have changed. Try getting a new snapshot with browser_snapshot()'}
            web_element, error = self._find_element_with_wait(by_type, selector, self.timeout, EC.element_to_be_clickable)
            if error:
                try:
                    is_visible = element_exists.is_displayed()
                    is_enabled = element_exists.is_enabled()
                    element_tag = element_exists.tag_name
                    element_classes = element_exists.get_attribute('class')
                    return {'status': 'not_clickable', 'message': f'Element found but not clickable: {element_desc}', 'element_state': {'visible': is_visible, 'enabled': is_enabled, 'tag': element_tag, 'classes': element_classes}, 'suggestion': 'The element might be disabled, hidden, or covered by another element'}
                except Exception:
                    return {'status': 'not_clickable', 'message': f'Element found but not clickable: {element_desc}', 'suggestion': 'The element might be disabled, hidden, or covered by another element'}
            web_element.click()
            page_loaded = self._wait_for_page_load(self.timeout)
            if not page_loaded:
                snapshot_result = self.browser_snapshot()
                return {'status': 'partial_success', 'message': 'Element clicked, but page load timed out', 'element': element_desc, 'current_url': self.driver.current_url, 'snapshot': snapshot_result if snapshot_result['status'] == 'success' else None, 'suggestion': 'The page might still be loading. You may want to wait and take another snapshot.'}
            snapshot_result = self.browser_snapshot()
            if snapshot_result['status'] == 'success':
                return {'status': 'success', 'message': f'Successfully clicked on {element_desc}', 'element': element_desc, 'current_url': self.driver.current_url, 'title': self.driver.title, 'snapshot': {'interactive_elements': snapshot_result.get('interactive_elements', [])}}
            else:
                return {'status': 'success', 'message': f'Successfully clicked on {element_desc} but snapshot failed', 'element': element_desc, 'current_url': self.driver.current_url, 'title': self.driver.title, 'snapshot_error': snapshot_result.get('message', 'Unknown error capturing snapshot'), 'suggestion': 'You may want to take another snapshot with browser_snapshot()'}
        except TimeoutException:
            return {'status': 'timeout', 'message': f'Timed out waiting for element to be clickable: {element_desc}', 'suggestion': 'The element might be taking too long to load or become clickable'}
        except Exception as e:
            logger.error(f'Error clicking element: {str(e)}')
            return {'status': 'error', 'message': str(e), 'element': element_desc, 'suggestion': 'Try getting a new snapshot of the page with browser_snapshot()'}

    def _classify_element_interactivity(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify an element's interactivity based on its properties.
        This method contains all rules for determining if an element is interactive or editable.
        
        Args:
            element_data (Dict[str, Any]): Element data including properties, attributes, etc.
            
        Returns:
            Dict[str, Any]: Element data with interactivity classifications added
        """
        element_data['interactable'] = False
        element_data['editable'] = False
        tag_name = element_data.get('properties', {}).get('tag', '').upper()
        role = element_data.get('attributes', {}).get('role', '').lower()
        is_disabled = element_data.get('attributes', {}).get('disabled') is not None or element_data.get('attributes', {}).get('aria-disabled') == 'true' or element_data.get('attributes', {}).get('aria-hidden') == 'true'
        is_visible = element_data.get('visible', True)
        if not is_disabled and is_visible:
            interactive_tags = {'A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'DETAILS', 'AUDIO', 'VIDEO', 'IFRAME', 'EMBED', 'OBJECT', 'SUMMARY', 'MENU'}
            interactive_roles = {'button', 'link', 'checkbox', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'option', 'radio', 'searchbox', 'slider', 'spinbutton', 'switch', 'tab', 'textbox', 'combobox', 'listbox', 'menu', 'menubar', 'radiogroup', 'tablist', 'toolbar', 'tree', 'treegrid'}
            has_interactive_attrs = any([element_data.get('attributes', {}).get(attr) is not None for attr in ['onclick', 'onkeydown', 'onkeyup', 'onmousedown', 'onmouseup', 'tabindex']])
            element_data['interactable'] = tag_name in interactive_tags or role in interactive_roles or has_interactive_attrs
            editable_input_types = {'text', 'search', 'email', 'number', 'tel', 'url', 'password'}
            editable_roles = {'textbox', 'searchbox', 'spinbutton'}
            element_data['editable'] = tag_name == 'INPUT' and element_data.get('attributes', {}).get('type', 'text').lower() in editable_input_types or tag_name == 'TEXTAREA' or element_data.get('attributes', {}).get('contenteditable') == 'true' or (role in editable_roles)
        return element_data

    def _process_accessibility_tree(self, accessibility_tree):
        """
        Process the accessibility tree to extract all elements and store their references.
        
        This method processes all elements in the page structure, assigns unique IDs,
        and stores their selectors for later interaction.
        
        Args:
            accessibility_tree (dict): The accessibility tree from JavaScript
            
        Returns:
            list: A list of all elements with their IDs and properties
        """
        all_elements = []

        def extract_elements(node, path='', index=0):
            if not node:
                return index
            current_path = path + '/' + (node.get('name') or node.get('role') or 'element')
            element_id = f'e{index}'
            element_info = {'id': element_id, 'description': current_path.strip('/'), 'purpose': node.get('semantic_info', {}).get('purpose', ''), 'label': node.get('semantic_info', {}).get('label', ''), 'category': node.get('semantic_info', {}).get('category', ''), 'isPrimary': node.get('semantic_info', {}).get('isPrimary', False), 'visible': node.get('visible', True), 'properties': node.get('properties', {}), 'attributes': node.get('attributes', {})}
            if 'all_refs' in node:
                self.element_references[element_id] = node['all_refs'][0]
            element_info = self._classify_element_interactivity(element_info)
            all_elements.append(element_info)
            index += 1
            for child in node.get('children', []):
                index = extract_elements(child, current_path, index)
            return index
        extract_elements(accessibility_tree)
        return all_elements

    def browser_snapshot(self, function_params: list=None) -> Dict[str, Any]:
        """
        Capture a fresh snapshot of the current page with all interactive elements. 
        Use after page state changes not caused by navigation or clicking.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "browser_snapshot", "function_args": {}}]
        
        Args:
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: The accessibility snapshot of the page with interactive elements
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            title = self.driver.title
            current_url = self.driver.current_url
            accessibility_tree = self.driver.execute_script("\n                function getAccessibilityTree(node, depth = 0, maxDepth = 10) {\n                    if (!node || depth > maxDepth) return null;\n                    \n                    let result = {\n                        role: node.role || node.tagName,\n                        name: node.name || '',\n                        type: node.type || '',\n                        value: node.value || '',\n                        description: node.description || '',\n                        properties: {},\n                        visible: isElementVisible(node)\n                    };\n                    \n                    // Helper function for element visibility\n                    function isElementVisible(element) {\n                        if (!element.getBoundingClientRect) return true;\n                        const style = window.getComputedStyle(element);\n                        const rect = element.getBoundingClientRect();\n                        \n                        // Check basic visibility\n                        const isVisible = style.display !== 'none' && \n                                        style.visibility !== 'hidden' && \n                                        style.opacity !== '0' &&\n                                        rect.width > 0 && \n                                        rect.height > 0;\n                                        \n                        // Check if element is in viewport\n                        const isInViewport = rect.top >= 0 &&\n                                           rect.left >= 0 &&\n                                           rect.bottom <= window.innerHeight &&\n                                           rect.right <= window.innerWidth;\n                                           \n                        return isVisible && isInViewport;\n                    }\n                    \n                    // Add text content\n                    if (node.textContent) {\n                        result.text_content = node.textContent.trim();\n                    }\n\n                    // Add identifier properties for references\n                    if (node.id) result.properties.id = node.id;\n                    if (node.className) result.properties.class = node.className;\n                    if (node.tagName) result.properties.tag = node.tagName.toLowerCase();\n                    \n                    // Add attributes\n                    if (node.attributes) {\n                        result.attributes = {};\n                        for (let attr of node.attributes) {\n                            result.attributes[attr.name] = attr.value;\n                        }\n                    }\n\n                    // Add custom ref property that combines selector types\n                    let refs = [];\n                    // Store all possible selectors, but don't use them as primary ref\n                    if (node.id) refs.push(`id:${node.id}`);\n                    if (node.className && typeof node.className === 'string') \n                        refs.push(`class:${node.className}`);\n                    if (node.tagName) refs.push(`tag:${node.tagName.toLowerCase()}`);\n                    \n                    // For inputs, add name attribute\n                    if (node.getAttribute && node.getAttribute('name')) {\n                        result.properties.name = node.getAttribute('name');\n                        refs.push(`name:${node.getAttribute('name')}`);\n                    }\n                    \n                    // Create XPath and CSS selectors\n                    try {\n                        // CSS selector\n                        let cssPath = getCssPath(node);\n                        if (cssPath) refs.push(`css:${cssPath}`);\n                        \n                        // XPath\n                        let xpath = getXPath(node);\n                        if (xpath) refs.push(`xpath:${xpath}`);\n                    } catch (e) {}\n                    \n                    // Store all refs but don't set primary ref here\n                    if (refs.length > 0) {\n                        result.all_refs = refs;\n                    }\n\n                    // Add semantic information about the element\n                    result.semantic_info = {\n                        // What the element represents\n                        purpose: (function() {\n                            if (node.tagName === 'INPUT') {\n                                if (node.type === 'submit') return 'submit button';\n                                if (node.type === 'search') return 'search box';\n                                if (node.type === 'text') return 'text input';\n                                return `${node.type || 'text'} input`;\n                            }\n                            if (node.tagName === 'BUTTON') return 'button';\n                            if (node.tagName === 'A') return 'link';\n                            if (node.tagName === 'SELECT') return 'dropdown';\n                            if (node.tagName === 'TEXTAREA') return 'text area';\n                            if (node.getAttribute('role')) return node.getAttribute('role');\n                            return 'interactive element';\n                        })(),\n                        \n                        // The visible or accessible text\n                        label: (function() {\n                            return node.getAttribute('aria-label') ||\n                                   node.getAttribute('title') ||\n                                   node.getAttribute('placeholder') ||\n                                   node.getAttribute('alt') ||\n                                   (node.tagName === 'INPUT' ? node.value : node.textContent.trim());\n                        })(),\n                        \n                        // Is this a primary action?\n                        isPrimary: !!(\n                            node.classList.contains('primary') ||\n                            node.getAttribute('aria-label')?.toLowerCase().includes('search') ||\n                            node.getAttribute('title')?.toLowerCase().includes('search') ||\n                            node.type === 'search' ||\n                            node.getAttribute('role') === 'main' ||\n                            node.id?.toLowerCase().includes('main') ||\n                            node.classList.contains('main')\n                        ),\n                        \n                        // Basic category\n                        category: (function() {\n                            if (node.type === 'search' || \n                                node.getAttribute('role') === 'searchbox') return 'search';\n                            if (node.type === 'submit' || \n                                node.tagName === 'BUTTON' ||\n                                node.getAttribute('role') === 'button') return 'action';\n                            if (node.tagName === 'A' ||\n                                node.getAttribute('role') === 'link') return 'navigation';\n                            if (node.tagName === 'INPUT' || \n                                node.tagName === 'TEXTAREA' ||\n                                node.getAttribute('role') === 'textbox') return 'input';\n                            if (node.tagName === 'SELECT' ||\n                                ['listbox', 'combobox'].includes(node.getAttribute('role'))) return 'selection';\n                            return 'interactive';\n                        })()\n                    };\n                    \n                    // Process children\n                    result.children = [];\n                    if (node.children) {\n                        for (let i = 0; i < node.children.length; i++) {\n                            const childTree = getAccessibilityTree(node.children[i], depth + 1, maxDepth);\n                            if (childTree) {\n                                result.children.push(childTree);\n                            }\n                        }\n                    }\n                    \n                    return result;\n                }\n                \n                return getAccessibilityTree(document.body);\n            ")
            all_elements = self._process_accessibility_tree(accessibility_tree)
            page_content = html2text.html2text(self.driver.page_source)
            return {'status': 'success', 'title': title, 'url': current_url, 'accessibility_tree': accessibility_tree, 'page_content': page_content, 'interactive_elements': [e for e in all_elements if e.get('interactable') or e.get('editable')]}
        except Exception as e:
            logger.error(f'Error generating accessibility snapshot: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def browser_console_messages(self, function_params: list=None) -> Dict[str, Any]:
        """
        Retrieve JavaScript console messages (logs, warnings, errors) from the browser for debugging.
        
        This function supports multiple parameter styles:
        1. Standard style: no parameters
        2. Nested function_params style:
           function_params=[{"function_name": "browser_console_messages", "function_args": {}}]
        
        Args:
            function_params (list, optional): Nested function parameters
            
        Returns:
            Dict[str, Any]: The console messages including logs, warnings and errors
        """
        driver_check = self._check_driver_initialized()
        if driver_check:
            return driver_check
        try:
            logs = self._collect_browser_logs()
            return {'status': 'success', 'console_messages': logs}
        except Exception as e:
            logger.error(f'Error retrieving console messages: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def _collect_browser_logs(self) -> List[Dict[str, Any]]:
        """
        Collect logs from both the browser driver and JavaScript console.
        
        Returns:
            List[Dict[str, Any]]: Combined logs from both sources
        """
        logs = []
        try:
            browser_logs = self.driver.get_log('browser')
            for log in browser_logs:
                level = log.get('level', '').upper()
                if level == 'SEVERE':
                    level = 'ERROR'
                elif level == 'INFO':
                    level = 'LOG'
                logs.append({'level': level, 'message': log.get('message', ''), 'timestamp': log.get('timestamp', '')})
        except Exception as log_error:
            logs.append({'level': 'WARNING', 'message': f'Could not retrieve browser logs: {str(log_error)}', 'timestamp': ''})
        try:
            self.driver.execute_script("\n                if (!window._consoleLogs) {\n                    window._consoleLogs = [];\n                    \n                    // Store original console methods\n                    const originalConsole = {\n                        log: console.log,\n                        info: console.info,\n                        warn: console.warn,\n                        error: console.error,\n                        debug: console.debug\n                    };\n                    \n                    // Helper function to add message with proper level\n                    function addMessage(level, args) {\n                        window._consoleLogs.push({\n                            level: level.toUpperCase(),\n                            message: Array.from(args).join(' '),\n                            timestamp: new Date().toISOString()\n                        });\n                    }\n                    \n                    // Override console methods to capture logs\n                    console.log = function() {\n                        addMessage('LOG', arguments);\n                        originalConsole.log.apply(console, arguments);\n                    };\n                    \n                    console.info = function() {\n                        addMessage('INFO', arguments);\n                        originalConsole.info.apply(console, arguments);\n                    };\n                    \n                    console.warn = function() {\n                        addMessage('WARN', arguments);\n                        originalConsole.warn.apply(console, arguments);\n                    };\n                    \n                    console.error = function() {\n                        addMessage('ERROR', arguments);\n                        originalConsole.error.apply(console, arguments);\n                    };\n                    \n                    console.debug = function() {\n                        addMessage('DEBUG', arguments);\n                        originalConsole.debug.apply(console, arguments);\n                    };\n                }\n            ")
            time.sleep(2)
            js_logs = self.driver.execute_script('return window._consoleLogs || [];')
            for log in js_logs:
                if log not in logs:
                    logs.append(log)
        except Exception as js_error:
            logs.append({'level': 'WARNING', 'message': f'Could not retrieve JavaScript console logs: {str(js_error)}', 'timestamp': ''})
        return logs

    def __del__(self):
        """
        Destructor to automatically close the browser when the instance is destroyed.
        """
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                logger.info('Browser automatically closed on cleanup')
            except Exception as e:
                logger.warning(f'Error during automatic browser cleanup: {str(e)}')

def _check_driver_initialized(self) -> Union[None, Dict[str, Any]]:
    """
        Check if the browser driver is initialized. If not, initialize it automatically.
        
        Returns:
            Union[None, Dict[str, Any]]: None if driver is initialized, error response if initialization fails
        """
    if not self.driver:
        init_result = self.initialize_browser()
        if init_result['status'] == 'error':
            return init_result
    return None

