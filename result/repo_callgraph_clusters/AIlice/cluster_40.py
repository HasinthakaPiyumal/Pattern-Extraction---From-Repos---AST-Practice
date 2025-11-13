# Cluster 40

class AWebBrowser(AScrollablePage):

    def __init__(self, functions: dict[str, str]):
        super(AWebBrowser, self).__init__(functions=functions)
        self.inited = False
        self.exit_stack = AsyncExitStack()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.urls = {}
        self.prompt = '\nThe text with links are enclosed in square brackets to highlight it. If you need to open the page linked to a certain text, please call GET-LINK<!|text: str, session: str|!> function to get the url, and then call BROWSE<!|url: str, session: str|!>. Please note that the text parameter of GET-LINK must exactly match the content in the square brackets (excluding the square brackets themselves).\nThe forms on the webpage have been listed in text format, and you can use the EXECUTE-JS<!|js_code: str, session: str|!> function to operate the form, such as entering text, clicking buttons, etc. Use triple quotes on your code. Example: \n!EXECUTE-JS<!|"""\ndocument.querySelector(\'form.mini-search input[name="query"]\').value = "hello world";\ndocument.querySelector(\'form.mini-search\').submit();\n""", "arxiv_session"|!>\n'
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.RunEventLoop, daemon=True)
        self.thread.start()

    def RunEventLoop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def RunCoroutine(self, coro, timeout=60):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=timeout)
        except Exception as e:
            if not future.done():
                future.cancel()
            raise e

    async def AsyncInit(self):
        if self.inited:
            return (True, '')
        try:
            self.playwright = await self.exit_stack.enter_async_context(async_playwright())
            browser_args = []
            if os.path.exists('/.dockerenv'):
                browser_args.append('--no-sandbox')
            browser_instance = await self.playwright.chromium.launch(headless=True, args=browser_args)
            self.browser = await self.exit_stack.enter_async_context(browser_instance)
            context_instance = await self.browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36', viewport={'width': 1280, 'height': 800})
            self.context = await self.exit_stack.enter_async_context(context_instance)
            await self.context.route('**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,otf,eot}', lambda route: route.abort())
            self.page = await self.context.new_page()
            self.inited = True
            return (True, '')
        except Exception as e:
            await self.exit_stack.aclose()
            return (False, f'Browser initialization failed: {str(e)}\n{traceback.format_exc()}')

    def Init(self):
        return self.RunCoroutine(self.AsyncInit())

    async def AsyncBrowse(self, url):
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return 'Invalid URL. Please provide a complete URL starting with http:// or https://'
        except Exception:
            return 'Invalid URL format. Please check the URL and try again.'
        succ, msg = await self.AsyncInit()
        if not succ:
            raise Exception(msg)
        await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await self.page.wait_for_timeout(2000)
        content = await self.AsyncHtmlToMarkdown()
        self.LoadPage(content, 'TOP')
        return self() + self.prompt

    def Browse(self, url):
        return self.RunCoroutine(self.AsyncBrowse(url))

    def GetFullText(self):
        return self.txt if self.txt is not None else ''

    def GetLink(self, text):
        if text in self.urls:
            return self.urls[text]
        else:
            import difflib
            prompt = 'Please note that the text you use to query the URL should be the part enclosed in square brackets (excluding the square brackets themselves), otherwise the search will not yield results.'
            similars = '\n'.join(['[' + key + '](' + self.urls[key] + ')' for key in difflib.get_close_matches(text, self.urls, n=3)])
            if similars == '':
                return 'No url found on specified text. \n' + prompt
            else:
                return f'No exact match found, the most similar URLs are as follows:\n {similars} \n{prompt}'

    def ScrollDown(self):
        return super(AWebBrowser, self).ScrollDown() + self.prompt

    def ScrollUp(self):
        return super(AWebBrowser, self).ScrollUp() + self.prompt

    def SearchDown(self, query):
        return super(AWebBrowser, self).SearchDown(query) + self.prompt

    def SearchUp(self, query):
        return super(AWebBrowser, self).SearchUp(query) + self.prompt

    async def AsyncExecuteJS(self, js_code):
        succ, msg = await self.AsyncInit()
        if not succ:
            return msg
        try:
            if not self.page or self.page.is_closed():
                return 'No active page. Please browse to a URL first.'
            result = await self.page.evaluate(js_code)
            await self.page.wait_for_timeout(2000)
            content = await self.AsyncHtmlToMarkdown()
            result_str = 'JavaScript executed successfully.' if result is None else str(result)
            self.LoadPage(f'JS execution returned: {result_str}\n\n---\n\nThe current page content is as follows:\n\n{content}', 'TOP')
            return self() + self.prompt
        except Exception as e:
            return f'Error executing JavaScript: {str(e)}\n{traceback.format_exc()}'

    def ExecuteJS(self, js_code):
        return self.RunCoroutine(self.AsyncExecuteJS(js_code))

    def EnsureUnique(self, text):
        if not text or text.isspace():
            text = 'Link'
        text = re.sub('\\s+', ' ', text).strip()
        if not text:
            text = 'Link'
        ret = text
        while ret in self.urls:
            ret = text + ' |' + str(random.randint(0, 10000000))
        return ret

    async def AsyncHtmlToMarkdown(self):
        """Convert HTML to Markdown using JavaScript for DOM processing and Python for frame handling"""
        self.urls = {}
        result = await self.AsyncProcessPageAndFrames(self.page)
        return result

    async def AsyncProcessPageAndFrames(self, page_or_frame):
        """Process a page or frame and all its child frames recursively"""
        result = await page_or_frame.evaluate('() => {\n            // Helper function to clean text\n            function cleanText(text) {\n                return text ? text.replace(/\\s+/g, \' \').trim() : \'\';\n            }\n            \n            // Helper function to ensure element is visible\n            function isVisible(element) {\n                if (!element) return false;\n                \n                // Check computed style\n                const style = window.getComputedStyle(element);\n                if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') {\n                    return false;\n                }\n                \n                // Check dimensions\n                const rect = element.getBoundingClientRect();\n                if (rect.width === 0 || rect.height === 0) {\n                    return false;\n                }\n                \n                return true;\n            }\n            \n            // Process a form element\n            function processForm(form) {\n                let formInfo = [\'\\n\\n```\', \'Form:\'];\n                \n                // Extract form attributes\n                [\'action\', \'method\', \'name\', \'id\', \'class\'].forEach(attr => {\n                    if (form[attr]) {\n                        formInfo.push(`- ${attr.charAt(0).toUpperCase() + attr.slice(1)}: ${form[attr]}`);\n                    }\n                });\n                \n                // Build selector\n                let selector = \'form\';\n                if (form.id) selector = `form#${form.id}`;\n                else if (form.name) selector = `form[name=\'${form.name}\']`;\n                else if (form.className) {\n                    const className = form.className.split(\' \')[0];\n                    if (className) selector = `form.${className}`;\n                }\n                \n                formInfo.push(`- Selector: ${selector}`);\n                formInfo.push(\'\\nFields:\');\n                \n                // Process form fields\n                const fields = form.querySelectorAll(\'input, select, textarea, button\');\n                let fieldCount = 0;\n                \n                fields.forEach(field => {\n                    if (!isVisible(field)) return;\n                    \n                    fieldCount++;\n                    formInfo.push(`${fieldCount}. ${field.nodeName.charAt(0).toUpperCase() + field.nodeName.slice(1).toLowerCase()}:`);\n                    \n                    [\'type\', \'name\', \'id\', \'placeholder\', \'required\'].forEach(attr => {\n                        if (field[attr]) {\n                            formInfo.push(`   - ${attr.charAt(0).toUpperCase() + attr.slice(1)}: ${field[attr]}`);\n                        }\n                    });\n                    \n                    // Build field selector\n                    let fieldSelector = \'\';\n                    if (field.id) fieldSelector = `#${field.id}`;\n                    else if (field.name) fieldSelector = `${field.nodeName.toLowerCase()}[name=\'${field.name}\']`;\n                    else fieldSelector = `${selector} ${field.nodeName.toLowerCase()}`;\n                    if (field.type && !field.id && !field.name) fieldSelector += `[type=\'${field.type}\']`;\n                    \n                    formInfo.push(`   - Selector: ${fieldSelector}`);\n                    \n                    if (field.value) {\n                        formInfo.push(`   - Value: "${field.value}"`);\n                    }\n                    \n                    if (field.nodeName.toLowerCase() === \'select\') {\n                        formInfo.push(\'   - Options:\');\n                        for (const option of field.options) {\n                            formInfo.push(`     * Value: "${option.value}", Text: "${option.text}", Selected: ${option.selected}`);\n                        }\n                    }\n                    \n                    if (field.nodeName.toLowerCase() === \'button\') {\n                        formInfo.push(`   - Text: "${cleanText(field.textContent)}"`);\n                    }\n                });\n                \n                formInfo.push(\'```\\n\\n\');\n                return formInfo.join(\'\\n\');\n            }\n            \n            // Generate a unique ID\n            function generateUniqueId(prefix) {\n                return prefix + \'_\' + Date.now() + \'_\' + Math.random().toString(36).substring(2, 15);\n            }\n            \n            // Store for URL mappings and iframe positions\n            const urlMappings = {};\n            const iframePositions = [];\n            \n            // Process a node recursively\n            function processNode(node, strip = true, depth = 0) {\n                if (!node) return \'\';\n                \n                // Skip invisible elements\n                if (node.nodeType === Node.ELEMENT_NODE && !isVisible(node)) {\n                    return \'\';\n                }\n                \n                // Skip comments\n                if (node.nodeType === Node.COMMENT_NODE) {\n                    return \'\';\n                }\n                \n                // Skip script, style, etc.\n                if (node.nodeType === Node.ELEMENT_NODE) {\n                    const tagName = node.nodeName.toLowerCase();\n                    if ([\'script\', \'style\', \'noscript\', \'svg\', \'path\', \'meta\', \'link\'].includes(tagName)) {\n                        return \'\';\n                    }\n                }\n                \n                // Text node\n                if (node.nodeType === Node.TEXT_NODE) {\n                    const text = node.textContent || \'\';\n                    return strip ? cleanText(text) : text;\n                }\n                \n                // Element node\n                const tagName = node.nodeName.toLowerCase();\n                let result = \'\';\n                \n                // Process by tag type\n                switch (tagName) {\n                    case \'form\':\n                        return processForm(node);\n                        \n                    case \'li\':\n                        let liContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent && childContent.trim()) {\n                                liContent += childContent;\n                            }\n                        }\n                        return `- ${liContent.trim()}\\n`;\n                        \n                    case \'p\':\n                        let pContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent && childContent.trim()) {\n                                pContent += childContent;\n                            }\n                        }\n                        return `\\n\\n${pContent}\\n\\n`;\n                        \n                    case \'pre\':\n                        let preContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, false, depth + 1);\n                            if (childContent) {\n                                preContent += childContent;\n                            }\n                        }\n                        return `\\n\\n\\`\\`\\`\\n${preContent}\\n\\`\\`\\`\\n\\n`;\n                        \n                    case \'code\':\n                        let codeContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, false, depth + 1);\n                            if (childContent) {\n                                codeContent += childContent;\n                            }\n                        }\n                        return `\\`${codeContent}\\``;\n                        \n                    case \'h1\': case \'h2\': case \'h3\': case \'h4\': case \'h5\': case \'h6\':\n                        const level = parseInt(tagName.charAt(1));\n                        let headingContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent) {\n                                headingContent += childContent;\n                            }\n                        }\n                        return `\\n\\n${\'#\'.repeat(level)} ${headingContent.trim()}\\n`;\n                        \n                    case \'a\':\n                        const href = node.getAttribute(\'href\') || \'\';\n                        let linkContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent) {\n                                linkContent += childContent;\n                            }\n                        }\n                        \n                        if (!linkContent) {\n                            linkContent = strip ? cleanText(node.textContent) : node.textContent;\n                        }\n                        \n                        if (linkContent && href) {\n                            // Create a unique ID for this link\n                            const linkId = generateUniqueId(\'link\');\n                            urlMappings[linkId] = {\n                                url: href,\n                                text: linkContent\n                            };\n                            return `[${linkContent}](${linkId})`;\n                        }\n                        return linkContent;\n                        \n                    case \'img\':\n                        const src = node.getAttribute(\'src\') || \'\';\n                        const alt = strip ? cleanText(node.getAttribute(\'alt\') || \'\') : (node.getAttribute(\'alt\') || \'\');\n                        \n                        if (src) {\n                            if (src.startsWith(\'data:\')) {\n                                return alt;\n                            }\n                            // Create a unique ID for this image\n                            const imgId = generateUniqueId(\'img\');\n                            urlMappings[imgId] = {\n                                url: src,\n                                text: alt || \'Image\'\n                            };\n                            return `\\n![${alt || \'Image\'}](${imgId})\\n`;\n                        }\n                        return alt;\n                        \n                    case \'video\':\n                        const videoSrc = node.getAttribute(\'src\') || \'\';\n                        if (videoSrc) {\n                            // Create a unique ID for this video\n                            const videoId = generateUniqueId(\'video\');\n                            urlMappings[videoId] = {\n                                url: videoSrc,\n                                text: \'Video\'\n                            };\n                            return `\\n\\n[Video](${videoId})\\n\\n`;\n                        }\n                        \n                        const sourceElement = node.querySelector(\'source\');\n                        if (sourceElement) {\n                            const sourceSrc = sourceElement.getAttribute(\'src\') || \'\';\n                            if (sourceSrc) {\n                                // Create a unique ID for this video source\n                                const sourceId = generateUniqueId(\'video\');\n                                urlMappings[sourceId] = {\n                                    url: sourceSrc,\n                                    text: \'Video\'\n                                };\n                                return `\\n\\n[Video](${sourceId})\\n\\n`;\n                            }\n                        }\n                        return \'\';\n                        \n                    case \'iframe\':\n                        const iframeSrc = node.getAttribute(\'src\') || \'\';\n                        if (iframeSrc) {\n                            // Create a placeholder for this iframe\n                            const iframeId = generateUniqueId(\'iframe\');\n                            const placeholder = `__IFRAME_PLACEHOLDER_${iframeId}__`;\n                            \n                            // Store iframe information for later processing\n                            iframePositions.push({\n                                id: iframeId,\n                                src: iframeSrc,\n                                placeholder: placeholder,\n                                name: node.getAttribute(\'name\') || node.getAttribute(\'id\') || \'Unnamed Frame\'\n                            });\n                            \n                            return placeholder;\n                        }\n                        return \'\';\n                        \n                    case \'ul\': case \'ol\':\n                        let listContent = \'\\n\\n\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent) {\n                                listContent += childContent;\n                            }\n                        }\n                        return listContent + \'\\n\\n\';\n                        \n                    case \'div\': case \'span\': case \'section\': case \'article\': case \'main\': case \'header\': case \'footer\':\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent) {\n                                result += childContent;\n                            }\n                        }\n                        break;\n                        \n                    default:\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent) {\n                                result += childContent;\n                            }\n                        }\n                }\n                \n                return result;\n            }\n            \n            // Process the document body\n            const body = document.body;\n            const markdown = processNode(body, true, 0);\n            \n            return {\n                markdown: markdown,\n                urls: urlMappings,\n                iframes: iframePositions\n            };\n        }')
        markdown = result['markdown']
        urls = result['urls']
        iframes = result['iframes']
        for id, url_info in urls.items():
            url = url_info['url']
            text = url_info['text']
            unique_text = self.EnsureUnique(text)
            self.urls[unique_text] = urljoin(self.page.url, url)
            markdown = markdown.replace(f'[{text}]({id})', f'[{unique_text}]')
            markdown = markdown.replace(f'![{text}]({id})', f'![{unique_text}]({urljoin(self.page.url, url)})')
        for iframe in iframes:
            iframe_src = iframe['src']
            placeholder = iframe['placeholder']
            if not iframe_src:
                continue
            iframe_content = ''
            iframe_url = urljoin(self.page.url, iframe_src)
            for frame in page_or_frame.frames if hasattr(page_or_frame, 'frames') else page_or_frame.child_frames:
                if frame.url == iframe_src or frame.url == iframe_url:
                    try:
                        iframe_content = await self.AsyncProcessPageAndFrames(frame)
                        break
                    except Exception as e:
                        print(f'Error processing iframe: {str(e)}')
            if not iframe_content:
                iframe_content = f'[Iframe: {iframe_src}]'
            else:
                iframe_name = iframe['name']
                iframe_content = f'\n\n--- Frame: {iframe_name} ({iframe_src}) ---\n\n{iframe_content}\n\n--- End of Frame ---\n\n'
            markdown = markdown.replace(placeholder, iframe_content)
        return markdown

    async def AsyncDestroy(self):
        try:
            await self.exit_stack.aclose()
            self.inited = False
            self.playwright = None
            self.browser = None
            self.context = None
            self.page = None
            self.urls = {}
            return (True, 'Resources destroyed successfully')
        except Exception as e:
            return (False, f'Error during cleanup: {str(e)}\n{traceback.format_exc()}')

    def Destroy(self):
        result = self.RunCoroutine(self.AsyncDestroy())

        def shutdown_loop():
            for task in asyncio.all_tasks(self.loop):
                if not task.done():
                    task.cancel()
            self.loop.call_later(1, self.loop.stop)
        self.loop.call_soon_threadsafe(shutdown_loop)
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            print('Warning: Event loop thread did not terminate within timeout')
        return result

def RunCoroutine(self, coro, timeout=60):
    future = asyncio.run_coroutine_threadsafe(coro, self.loop)
    try:
        return future.result(timeout=timeout)
    except Exception as e:
        if not future.done():
            future.cancel()
        raise e

def shutdown_loop():
    for task in asyncio.all_tasks(self.loop):
        if not task.done():
            task.cancel()
    self.loop.call_later(1, self.loop.stop)

def action_method(self, jsonParam: str) -> list:
    ret = asyncio.run_coroutine_threadsafe(async_action_method(self, jsonParam), loop).result()
    result = []
    for item in ret.content:
        if type(item) == mcp.types.TextContent:
            result.append(str(item))
        elif type(item) == mcp.types.ImageContent:
            result.append(AImage.FromJson({'data': item.data}))
        elif type(item) == mcp.types.EmbeddedResource:
            result.append('[Unsupported EmbeddedResource content]')
    return result

class AMCPWrapper:
    MODULE_INFO = {'NAME': serverParams.args[0] if serverParams is not None else serverUrl, 'ACTIONS': {}}

    def __init__(self, serverParams=None, serverUrl=None):
        self.serverParams = serverParams
        self.serverUrl = serverUrl
        self.exit_stack = None
        self.stdio = None
        self.write = None
        self.session = None
        asyncio.run_coroutine_threadsafe(self.initialize(), loop).result()
        return

    def __del__(self):
        if hasattr(self, 'exit_stack') and self.exit_stack:
            try:
                asyncio.run_coroutine_threadsafe(self.close(), loop).result()
            except Exception as e:
                print(f'Error closing resources: {e}')

    async def initialize(self):
        self.exit_stack = AsyncExitStack()
        if self.serverParams is not None:
            self.MODULE_INFO['NAME'] = self.serverParams.args[0]
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(self.serverParams))
            self.session = await self.exit_stack.enter_async_context(ClientSession(*stdio_transport))
        elif self.serverUrl is not None:
            self.MODULE_INFO['NAME'] = self.serverUrl
            streams = await self.exit_stack.enter_async_context(sse_client(url=self.serverUrl))
            self.session = await self.exit_stack.enter_async_context(ClientSession(*streams))
        await self.session.initialize()

    async def close(self):
        if self.exit_stack:
            await self.exit_stack.aclose()

    def ModuleInfo(self):
        return self.MODULE_INFO

def __init__(self, serverParams=None, serverUrl=None):
    self.serverParams = serverParams
    self.serverUrl = serverUrl
    self.exit_stack = None
    self.stdio = None
    self.write = None
    self.session = None
    asyncio.run_coroutine_threadsafe(self.initialize(), loop).result()
    return

def MakeWrapper(serverParams=None, serverUrl=None):

    class AMCPWrapper:
        MODULE_INFO = {'NAME': serverParams.args[0] if serverParams is not None else serverUrl, 'ACTIONS': {}}

        def __init__(self, serverParams=None, serverUrl=None):
            self.serverParams = serverParams
            self.serverUrl = serverUrl
            self.exit_stack = None
            self.stdio = None
            self.write = None
            self.session = None
            asyncio.run_coroutine_threadsafe(self.initialize(), loop).result()
            return

        def __del__(self):
            if hasattr(self, 'exit_stack') and self.exit_stack:
                try:
                    asyncio.run_coroutine_threadsafe(self.close(), loop).result()
                except Exception as e:
                    print(f'Error closing resources: {e}')

        async def initialize(self):
            self.exit_stack = AsyncExitStack()
            if self.serverParams is not None:
                self.MODULE_INFO['NAME'] = self.serverParams.args[0]
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(self.serverParams))
                self.session = await self.exit_stack.enter_async_context(ClientSession(*stdio_transport))
            elif self.serverUrl is not None:
                self.MODULE_INFO['NAME'] = self.serverUrl
                streams = await self.exit_stack.enter_async_context(sse_client(url=self.serverUrl))
                self.session = await self.exit_stack.enter_async_context(ClientSession(*streams))
            await self.session.initialize()

        async def close(self):
            if self.exit_stack:
                await self.exit_stack.aclose()

        def ModuleInfo(self):
            return self.MODULE_INFO
    maxRetries = 3
    for attempt in range(maxRetries):
        try:
            toolsInfo = asyncio.run_coroutine_threadsafe(LoadMeta(serverParams=serverParams, serverUrl=serverUrl), loop).result()
            break
        except Exception as e:
            if attempt == maxRetries - 1:
                raise
            print(f'Attempt {attempt + 1} failed: {e}, retrying...')
            time.sleep(1)
    actions = []
    for tool in toolsInfo.tools:
        print(tool)
        actions.append(tool.name)
        AddActionMethod(AMCPWrapper, tool.name, tool)
    return (AMCPWrapper, actions)

