# Cluster 5

class KMsgQue:

    def __init__(self):
        self.colorMap = {'CONTEXT': 'blue', 'USER': 'green', 'ASSISTANT': 'green', 'SYSTEM': 'yellow', 'OUTPUT': 'green'}
        self.depth = -1
        self.buffer = []
        self.queue = queue.Queue()
        return

    def ParseChannel(self, channel: str) -> tuple[str]:
        if channel in ['<', '>']:
            return (channel, '')
        l = channel.find('_')
        channelType, agentName = (channel[:l], channel[l + 1:])
        return (channelType, agentName)

    def SinkPrint(self, channel: str, txt: str=None, action: str=''):
        channelType, agentName = self.ParseChannel(channel)
        if 'open' == action:
            print(colored(channel + ': ', self.colorMap[channelType]), txt, end='', flush=True)
        elif 'append' == action:
            print(txt, end='', flush=True)
        elif 'close' == action:
            print(txt, end='', flush=True)
            print('')
        else:
            print(colored(channel + ': ', self.colorMap[channelType]), txt)
        return

    def SinkBuffer(self, channel: str, txt: str=None, action: str=''):
        if '>' == channel:
            if -1 == self.depth:
                self.queue.put({'message': '', 'role': '', 'action': '', 'msgType': ''})
        elif '<' == channel:
            return
        else:
            self.queue.put({'message': txt, 'role': channel, 'action': action, 'msgType': 'internal' if self.depth > 0 or self.ParseChannel(channel)[0] == 'SYSTEM' else 'user-ailice'})
        return

    def Load(self, messages: list):
        self.buffer = copy.deepcopy(messages)
        return

    def Get(self, timeout=None, getBuffer=False):
        if getBuffer:
            return copy.deepcopy(self.buffer)
        else:
            msg = self.queue.get(timeout=timeout)
            msg['isRoundEnd'] = self.depth == -1 and msg['role'] == ''
            if not msg['isRoundEnd']:
                self.buffer.append(msg)
            return msg

    def Receiver(self, channel: str, txt: str=None, action: str=''):
        braketMap = {'<': 1, '>': -1}
        self.depth += braketMap[channel] if channel in braketMap else 0
        channelType, _ = self.ParseChannel(channel)
        if channelType in ['ASSISTANT', 'SYSTEM']:
            self.SinkPrint(channel=channel, txt=txt, action=action)
        if channelType in ['ASSISTANT', 'SYSTEM', '>'] or ('USER' == channelType and self.depth == 0):
            self.SinkBuffer(channel=channel, txt=txt, action=action)
        return

def ParseChannel(self, channel: str) -> tuple[str]:
    if channel in ['<', '>']:
        return (channel, '')
    l = channel.find('_')
    channelType, agentName = (channel[:l], channel[l + 1:])
    return (channelType, agentName)

class ALogger:

    def __init__(self, speech):
        self.colorMap = {'CONTEXT': 'blue', 'USER': 'green', 'ASSISTANT': 'green', 'SYSTEM': 'yellow', 'OUTPUT': 'green'}
        self.depth = -1
        self.speech = speech
        self.queue = queue.Queue()
        return

    def ParseChannel(self, channel: str) -> tuple[str]:
        if channel in ['<', '>']:
            return (channel, '')
        l = channel.find('_')
        channelType, agentName = (channel[:l], channel[l + 1:])
        return (channelType, agentName)

    def SinkPrint(self, channel: str, txt: str=None, action: str=''):
        channelType, agentName = self.ParseChannel(channel)
        if 'open' == action:
            print(colored(channel + ': ', self.colorMap[channelType]), txt, end='', flush=True)
        elif 'append' == action:
            print(txt, end='', flush=True)
        elif 'close' == action:
            print(txt, end='', flush=True)
            print('')
        else:
            print(colored(channel + ': ', self.colorMap[channelType]), txt)
        return

    def SinkSpeech(self, channel: str, txt: str=None, action: str=''):
        if self.speech:
            self.speech.Speak(txt)
        return

    def SinkQueue(self, channel: str, txt: str=None, action: str=''):
        self.queue.put((channel, txt, action))
        return

    def Receiver(self, channel: str, txt: str=None, action: str=''):
        braketMap = {'<': 1, '>': -1}
        self.depth += braketMap[channel] if channel in braketMap else 0
        channelType, _ = self.ParseChannel(channel)
        if channelType in ['ASSISTANT', 'SYSTEM']:
            self.SinkPrint(channel=channel, txt=txt, action=action)
        if config.speechOn and (channelType in ['ASSISTANT'] and 0 == self.depth):
            self.SinkSpeech(channel=channel, txt=txt, action=action)
        if channelType in ['ASSISTANT', 'SYSTEM', '<', '>'] or 0 >= self.depth:
            self.SinkQueue(channel=channel, txt=txt, action=action)
        return

def ParseChannel(self, channel: str) -> tuple[str]:
    if channel in ['<', '>']:
        return (channel, '')
    l = channel.find('_')
    channelType, agentName = (channel[:l], channel[l + 1:])
    return (channelType, agentName)

class AWebBrowser(AScrollablePage):

    def __init__(self, functions: dict[str, str]):
        super(AWebBrowser, self).__init__(functions=functions)
        self.inited = False
        self.driver = None
        self.urls = {}
        self.prompt = '\nThe text with links are enclosed in square brackets to highlight it. If you need to open the page linked to a certain text, please call GET-LINK<!|text: str, session: str|!> function to get the url, and then call BROWSE<!|url: str, session: str|!>. Please note that the text parameter of GET-LINK must exactly match the content in the square brackets (excluding the square brackets themselves).\nThe forms on the webpage have been listed in text format, and you can use the EXECUTE-JS<!|js_code: str, session: str|!> function to operate the form, such as entering text, clicking buttons, etc. Use triple quotes on your code. Example: \n!EXECUTE-JS<!|"""\ndocument.querySelector(\'form.mini-search input[name="query"]\').value = "hello world";\ndocument.querySelector(\'form.mini-search\').submit();\n""", "arxiv_session"|!>\n'
        return

    def Init(self):
        if self.inited:
            return (True, '')
        try:
            self.options = webdriver.ChromeOptions()
            self.options.add_argument('--headless')
            if os.path.exists('/.dockerenv'):
                self.options.add_argument('--no-sandbox')
            self.options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36')
            self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
            self.options.add_argument('--disable-blink-features=AutomationControlled')
            self.driver = webdriver.Chrome(options=self.options)
            self.inited = True
            return (True, '')
        except Exception as e:
            return (False, f'webdriver init FAILED. It may be caused by chrome not being installed correctly. please install chrome manually, or let AIlice do it for you. Exception details: {str(e)}\n{traceback.format_exc()}')

    def Browse(self, url: str) -> str:
        succ, msg = self.Init()
        if not succ:
            return msg
        self.driver.get(url)
        WebDriverWait(self.driver, 30).until(lambda d: d.execute_script("return document.readyState == 'complete'"))
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        body = soup.find('body')
        self.LoadPage(self.ProcessNode(body), 'TOP')
        return self() + self.prompt

    def GetFullText(self) -> str:
        return self.txt if self.txt != None else ''

    def GetLink(self, text: str) -> str:
        if text in self.urls:
            return self.urls[text]
        else:
            prompt = 'Please note that the text you use to query the URL should be the part enclosed in square brackets (excluding the square brackets themselves), otherwise the search will not yield results.'
            similars = '\n'.join(['[' + key + '](' + self.urls[key] + ')' for key in difflib.get_close_matches(text, self.urls, n=3)])
            if '' == similars:
                return 'No url found on specified text. \n' + prompt
            else:
                return f'No exact match found, the most similar URLs are as follows:\n {similars} \n{prompt}'

    def ScrollDown(self) -> str:
        return super(AWebBrowser, self).ScrollDown() + self.prompt

    def ScrollUp(self) -> str:
        return super(AWebBrowser, self).ScrollUp() + self.prompt

    def SearchDown(self, query: str) -> str:
        return super(AWebBrowser, self).SearchDown(query) + self.prompt

    def SearchUp(self, query: str) -> str:
        return super(AWebBrowser, self).SearchUp(query) + self.prompt

    def ExecuteJS(self, js_code: dict):
        try:
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            result = self.driver.execute_script(js_code)
            WebDriverWait(self.driver, 30).until(lambda d: d.execute_script("return document.readyState == 'complete'"))
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            body = soup.find('body')
            self.LoadPage(self.ProcessNode(body), 'TOP')
            result = 'JavaScript executed successfully.' if result is None else result
            return f'JS execution returned: {result} \n\nThe current page content is as follows:\n\n{self() + self.prompt}'
        except Exception as e:
            return f'Error executing JavaScript: {str(e)}'

    def EnsureUnique(self, txt: str) -> str:
        ret = txt
        while ret in self.urls:
            ret = txt + '   |' + str(random.randint(0, 10000000))
        return ret

    def IsBase64Image(self, string):
        if string.startswith('data:image'):
            if ';base64,' not in string:
                return False
            string = string.split(';base64,')[1]
        try:
            valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
            return all((c in valid_chars for c in string))
        except Exception:
            return False

    def ProcessNode(self, node, strip=True) -> str:
        ret = ''
        if node is None:
            return ''
        if node.name is None:
            if isinstance(node, Comment):
                return ''
            else:
                return (node.string.strip() if strip else node.string) if node.string else ''
        elif node.name == 'form':
            return f'\n\n```\n{self.ProcessForm(node)}\n```\n\n'
        elif node.name == 'li':
            li = ''
            for child in node.children:
                li += self.ProcessNode(child)
            ret = f'- {li}\n'
        elif node.name == 'p':
            ret += '\n\n'
            for child in node.children:
                ret += self.ProcessNode(child)
        elif node.name == 'pre':
            for child in node.children:
                ret += self.ProcessNode(child, strip=False)
        elif node.name == 'code':
            ret = f'\n\n```\n{''.join([self.ProcessNode(child, strip=False) for child in node.children])}\n```\n\n'
        elif node.name in ['span', 'div']:
            for child in node.children:
                ret += self.ProcessNode(child)
        elif node.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(node.name[1])
            for child in node.children:
                ret += self.ProcessNode(child)
            ret = '\n\n' + '#' * level + ' ' + ret + '\n'
        elif node.name == 'a':
            href = node.get('href', '')
            text = ''
            for child in node.children:
                text += self.ProcessNode(child)
            if '' != text and '' != href:
                href = urljoin(self.driver.current_url, node.get('href', ''))
                textUni = self.EnsureUnique(text)
                self.urls[textUni] = href
                ret = f'[{textUni}]'
            else:
                ret = text
        elif node.name == 'img':
            src = node.get('src', '')
            alt = node.get('alt', '').strip() if strip else node.get('alt', '')
            if '' != src:
                textUni = self.EnsureUnique(alt)
                url = urljoin(self.driver.current_url, src)
                if not self.IsBase64Image(url):
                    self.urls[textUni] = url
                    ret = f'\n![{textUni}]({url})\n'
            else:
                ret = alt
        elif node.name == 'video':
            videoURL = None
            if node.has_attr('src'):
                videoURL = node.get('src', '')
            else:
                for source in node.find_all('source'):
                    videoURL = source.get('src', '')
                    if videoURL:
                        break
            if videoURL:
                ret = f'\n\n[Video]({urljoin(self.driver.current_url, videoURL)})\n\n'
        elif node.name in ['ul', 'ol']:
            ret += '\n\n'
            for child in node.children:
                ret += self.ProcessNode(child)
            ret += '\n\n'
        elif node.name in ['script', 'style', 'noscript']:
            ret = ''
        elif node.name in ['iframe']:
            try:
                iframeElement = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, f'iframe[src="{node.get('src')}"]')))
            except selenium.common.exceptions.TimeoutException as e:
                return ret
            self.driver.switch_to.frame(iframeElement)
            iframeContent = self.driver.page_source
            self.driver.switch_to.parent_frame()
            soup = BeautifulSoup(iframeContent, 'html.parser')
            body = soup.find('body')
            ret += self.ProcessNode(body)
        else:
            for child in node.children:
                ret += self.ProcessNode(child)
        return ret

    def ProcessForm(self, form_node):
        form_info = []
        form_info.append(f'Form:')
        form_info.append(f'- Action: {form_node.get('action', '')}')
        form_info.append(f'- Method: {form_node.get('method', 'GET')}')
        if form_node.get('name'):
            form_info.append(f'- Name: {form_node['name']}')
        if form_node.get('id'):
            form_info.append(f'- ID: {form_node['id']}')
        form_info.append('\nFields:')
        for i, field in enumerate(form_node.find_all(['input', 'select', 'textarea', 'button']), 1):
            form_info.append(f'{i}. {field.name.capitalize()}:')
            for attr in ['type', 'name', 'id', 'placeholder', 'required']:
                if field.get(attr):
                    form_info.append(f'   - {attr.capitalize()}: {field[attr]}')
            if field.name == 'select':
                form_info.append('   - Options:')
                for option in field.find_all('option'):
                    form_info.append(f'     * Value: {option.get('value', '')}, Text: {option.text.strip()}')
            if field.name == 'button' and field.text:
                form_info.append(f'   - Text: {field.text.strip()}')
        return '\n'.join(form_info)

    def Destroy(self):
        self.inited = False
        self.driver.quit()
        self.driver = None
        self.urls = {}
        return

def Browse(self, url: str) -> str:
    succ, msg = self.Init()
    if not succ:
        return msg
    self.driver.get(url)
    WebDriverWait(self.driver, 30).until(lambda d: d.execute_script("return document.readyState == 'complete'"))
    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
    body = soup.find('body')
    self.LoadPage(self.ProcessNode(body), 'TOP')
    return self() + self.prompt

def ExecuteJS(self, js_code: dict):
    try:
        WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        result = self.driver.execute_script(js_code)
        WebDriverWait(self.driver, 30).until(lambda d: d.execute_script("return document.readyState == 'complete'"))
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        body = soup.find('body')
        self.LoadPage(self.ProcessNode(body), 'TOP')
        result = 'JavaScript executed successfully.' if result is None else result
        return f'JS execution returned: {result} \n\nThe current page content is as follows:\n\n{self() + self.prompt}'
    except Exception as e:
        return f'Error executing JavaScript: {str(e)}'

def ProcessNode(self, node, strip=True) -> str:
    ret = ''
    if node is None:
        return ''
    if node.name is None:
        if isinstance(node, Comment):
            return ''
        else:
            return (node.string.strip() if strip else node.string) if node.string else ''
    elif node.name == 'form':
        return f'\n\n```\n{self.ProcessForm(node)}\n```\n\n'
    elif node.name == 'li':
        li = ''
        for child in node.children:
            li += self.ProcessNode(child)
        ret = f'- {li}\n'
    elif node.name == 'p':
        ret += '\n\n'
        for child in node.children:
            ret += self.ProcessNode(child)
    elif node.name == 'pre':
        for child in node.children:
            ret += self.ProcessNode(child, strip=False)
    elif node.name == 'code':
        ret = f'\n\n```\n{''.join([self.ProcessNode(child, strip=False) for child in node.children])}\n```\n\n'
    elif node.name in ['span', 'div']:
        for child in node.children:
            ret += self.ProcessNode(child)
    elif node.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        level = int(node.name[1])
        for child in node.children:
            ret += self.ProcessNode(child)
        ret = '\n\n' + '#' * level + ' ' + ret + '\n'
    elif node.name == 'a':
        href = node.get('href', '')
        text = ''
        for child in node.children:
            text += self.ProcessNode(child)
        if '' != text and '' != href:
            href = urljoin(self.driver.current_url, node.get('href', ''))
            textUni = self.EnsureUnique(text)
            self.urls[textUni] = href
            ret = f'[{textUni}]'
        else:
            ret = text
    elif node.name == 'img':
        src = node.get('src', '')
        alt = node.get('alt', '').strip() if strip else node.get('alt', '')
        if '' != src:
            textUni = self.EnsureUnique(alt)
            url = urljoin(self.driver.current_url, src)
            if not self.IsBase64Image(url):
                self.urls[textUni] = url
                ret = f'\n![{textUni}]({url})\n'
        else:
            ret = alt
    elif node.name == 'video':
        videoURL = None
        if node.has_attr('src'):
            videoURL = node.get('src', '')
        else:
            for source in node.find_all('source'):
                videoURL = source.get('src', '')
                if videoURL:
                    break
        if videoURL:
            ret = f'\n\n[Video]({urljoin(self.driver.current_url, videoURL)})\n\n'
    elif node.name in ['ul', 'ol']:
        ret += '\n\n'
        for child in node.children:
            ret += self.ProcessNode(child)
        ret += '\n\n'
    elif node.name in ['script', 'style', 'noscript']:
        ret = ''
    elif node.name in ['iframe']:
        try:
            iframeElement = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, f'iframe[src="{node.get('src')}"]')))
        except selenium.common.exceptions.TimeoutException as e:
            return ret
        self.driver.switch_to.frame(iframeElement)
        iframeContent = self.driver.page_source
        self.driver.switch_to.parent_frame()
        soup = BeautifulSoup(iframeContent, 'html.parser')
        body = soup.find('body')
        ret += self.ProcessNode(body)
    else:
        for child in node.children:
            ret += self.ProcessNode(child)
    return ret

class APDFBrowser(AScrollablePage):

    def __init__(self, pdfOutputDir: str, functions: dict[str, str]):
        super(APDFBrowser, self).__init__(functions=functions)
        self.pdfOutputDir = pdfOutputDir
        if 'pix2text' == OCROption:
            self.p2t = Pix2Text.from_config()
        return

    def OCRPix2Text(self, pdfPath: str, outDir: str) -> str:
        return self.p2t.recognize_pdf(pdfPath).to_markdown(outDir)

    def OCRMarker(self, pdfPath: str, outDir: str) -> str:
        result = subprocess.run(['marker_single', f'{pdfPath}', '--output_dir', f'{outDir}', '--output_format', 'markdown'])
        if result.returncode != 0:
            raise Exception(str(result.stdout) + '\n\n' + str(result.stderr))
        pdfName = Path(pdfPath).stem
        with open(Path(outDir) / pdfName / f'{pdfName}.md', 'r') as f:
            ret = f.read()
        ret = re.sub('!\\[([^\\]]*)\\]\\(([^)]+)\\)', lambda match: f'![{match.group(1)}]({str(os.path.join(outDir, pdfName, match.group(2)))})', ret)
        with open(Path(outDir) / pdfName / f'{pdfName}.md', 'w') as f:
            f.write(ret)
        return ret

    def Browse(self, url: str) -> str:
        if 'None' == OCROption:
            self.LoadPage(f'python packages marker-pdf or pix2text not found. Please install one of them before using PDF OCR.', 'BOTTOM')
            return self()
        try:
            fullName = url.split('/')[-1]
            fileName = fullName[:fullName.rfind('.')]
            outDir = f'{self.pdfOutputDir}/{fileName}'
            os.makedirs(outDir, exist_ok=True)
            pdfPath = f'{outDir}/{fullName}'
            if os.path.exists(url):
                shutil.copy(url, pdfPath)
            else:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(pdfPath, 'wb') as pdf_file:
                        pdf_file.write(response.content)
                else:
                    print('can not download pdf file. HTTP err code:', response.status_code)
            if 'marker' == OCROption:
                result = self.OCRMarker(pdfPath, outDir)
            elif 'pix2text' == OCROption:
                result = self.OCRPix2Text(pdfPath, outDir)
            self.LoadPage(result, 'TOP')
        except Exception as e:
            self.LoadPage(f'PDF OCR Exception: {str(e)}.', 'BOTTOM')
        return self()

    def GetFullText(self) -> str:
        return self.txt if self.txt != None else ''

    def Destroy(self):
        return

def Browse(self, url: str) -> str:
    if 'None' == OCROption:
        self.LoadPage(f'python packages marker-pdf or pix2text not found. Please install one of them before using PDF OCR.', 'BOTTOM')
        return self()
    try:
        fullName = url.split('/')[-1]
        fileName = fullName[:fullName.rfind('.')]
        outDir = f'{self.pdfOutputDir}/{fileName}'
        os.makedirs(outDir, exist_ok=True)
        pdfPath = f'{outDir}/{fullName}'
        if os.path.exists(url):
            shutil.copy(url, pdfPath)
        else:
            response = requests.get(url)
            if response.status_code == 200:
                with open(pdfPath, 'wb') as pdf_file:
                    pdf_file.write(response.content)
            else:
                print('can not download pdf file. HTTP err code:', response.status_code)
        if 'marker' == OCROption:
            result = self.OCRMarker(pdfPath, outDir)
        elif 'pix2text' == OCROption:
            result = self.OCRPix2Text(pdfPath, outDir)
        self.LoadPage(result, 'TOP')
    except Exception as e:
        self.LoadPage(f'PDF OCR Exception: {str(e)}.', 'BOTTOM')
    return self()

class AScripter:

    def __init__(self, incontainer=False):
        self.incontainer = incontainer
        self.sessions = {}
        self.sessionsLock = threading.Lock()
        self.reader = threading.Thread(target=self.OutputReader, args=())
        self.reader.start()
        self.functions = {'SCROLLUP': '#scroll up the page: \nSCROLL-UP-TERM<!|session: str|!>'}
        return

    def ModuleInfo(self):
        return {'NAME': 'scripter', 'ACTIONS': {'PLATFORM-INFO': {'func': 'PlatformInfo', 'prompt': 'Get the platform information of the current code execution environment.', 'type': 'primary'}, 'BASH': {'func': 'RunBash', 'prompt': 'Create a bash execution environment and execute a bash script. A timeout error will occur for programs that have not been completed for a long time. Different calls to a BASH function are independent of each other. The state from previous calls, such as custom environment variables and the current directory, will not affect subsequent calls. Note that this means you might need to redefine some environment variables or re-enter certain directories in each BASH call.', 'type': 'primary'}, 'PYTHON': {'func': 'RunPython', 'prompt': 'Execute python code. Please note that you need to copy the complete code here, and you must not use references.', 'type': 'primary'}, 'CHECK-OUTPUT': {'func': 'CheckOutput', 'prompt': 'Obtain script execution output result.', 'type': 'supportive'}, 'SCROLL-UP-TERM': {'func': 'ScrollUp', 'prompt': 'Scroll up the results.', 'type': 'supportive'}, 'SAVE-TO-FILE': {'func': 'Save2File', 'prompt': 'Save text or code to file.', 'type': 'primary'}}}

    def GetSessionID(self) -> str:
        id = f'session-{str(random.randint(0, 99999999))}'
        while id in self.sessions:
            id = f'session-{str(random.randint(0, 99999999))}'
        return id

    def RunCMD(self, session: str, cmd: list[str], timeout: int=30):
        env = os.environ.copy()
        env['A_IN_CONTAINER'] = '1' if self.incontainer else '0'
        self.sessions[session]['proc'] = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        if os.name != 'nt':
            os.set_blocking(self.sessions[session]['proc'].stdout.fileno(), False)
        self.Wait(process=self.sessions[session]['proc'], timeout=timeout)
        return

    def Wait(self, process, timeout):
        t0 = time.time()
        while time.time() < t0 + timeout:
            if process.poll() is not None:
                return
            time.sleep(0.5)

    def CheckProcOutput(self, session: str) -> tuple[str, bool]:
        process = self.sessions[session]['proc']
        output = ''
        completed = False
        if process.poll() is not None:
            for i in range(2):
                remainingOutput = ''
                try:
                    remainingOutput = process.stdout.read()
                    break
                except TypeError as e:
                    time.sleep(1)
                    remainingOutput += str(e) if 1 == i else ''
                    continue
            if remainingOutput:
                output += remainingOutput
            completed = True
        else:
            while True:
                line = process.stdout.readline()
                if line:
                    output += line
                else:
                    break
        return (output, completed)

    def UpdateSession(self, session: str):
        try:
            output, completed = self.CheckProcOutput(session=session)
            self.sessions[session]['completed'] = completed
            self.sessions[session]['output'] += output
            p = '\nThe program takes longer to complete. You can use WAIT to wait for a while and then use CHECK-OUTPUT function to get new output.' if not completed else '\nExecution completed.'
        except Exception as e:
            p = f'Exception when check the output of program execution: {str(e)}\n {traceback.format_exc()}'
            print(p)
        finally:
            self.sessions[session]['pages'].LoadPage(self.sessions[session]['output'] + '\n\n---\n\n' + p, 'BOTTOM')

    def OutputReader(self):
        while True:
            with self.sessionsLock:
                for session in self.sessions:
                    if self.sessions[session]['completed']:
                        continue
                    self.UpdateSession(session)
            time.sleep(1.0)
        return

    def CheckOutput(self, session: str) -> str:
        with self.sessionsLock:
            return self.sessions[session]['pages']() + '\n\n' + f'Session name: "{session}"\n'

    def PlatformInfo(self) -> str:
        info = platform.uname()
        currentPath = os.getcwd()
        contents = os.listdir(currentPath)
        newline = '\n'
        return f'system: {info.system}, release: {info.release}, version: {info.version}, machine: {info.machine} current path: {currentPath} contents of current path: {(newline.join(contents) if len(contents) <= 32 else newline.join(contents[:32]) + '....[The tail content has been ignored. You can use BASH function to execute system commands to view the remaining content]')}'

    def RunBash(self, code: str) -> str:
        with self.sessionsLock:
            try:
                session = self.GetSessionID()
                self.sessions[session] = {'proc': None, 'pages': AScrollablePage(functions=self.functions), 'output': '', 'lock': threading.Lock()}
                self.RunCMD(session, ['bash', '-c', code])
            except Exception as e:
                self.sessions[session]['output'] += f'Exception: {str(e)}\n {traceback.format_exc()}'
            self.UpdateSession(session)
            return f'{self.sessions[session]['pages']()}\nNote that each BASH function execution is independent, so if you want to use the state from the current execution (current directory / custom environment variables, etc.) in subsequent BASH functions, you need to redefine them.\n\n\nSession name: "{session}"\n'

    def RunPython(self, code: str) -> str:
        with self.sessionsLock:
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp:
                temp.write(code)
                temp.flush()
                try:
                    session = self.GetSessionID()
                    self.sessions[session] = {'proc': None, 'pages': AScrollablePage(functions=self.functions), 'output': '', 'lock': threading.Lock()}
                    self.RunCMD(session, ['python3', '-u', temp.name])
                except Exception as e:
                    self.sessions[session]['output'] += f'Exception: {str(e)}\n {traceback.format_exc()}'
            self.UpdateSession(session)
            return self.sessions[session]['pages']() + '\n\n' + f'Session name: "{session}"\n'

    def ScrollUp(self, session: str) -> str:
        with self.sessionsLock:
            return self.sessions[session]['pages'].ScrollUp() + '\n\n' + f'Session name: "{session}"\n'

    def Save2File(self, filePath: str, code: str) -> str:
        try:
            dirPath = os.path.dirname(filePath)
            if '' != dirPath:
                os.makedirs(dirPath, exist_ok=True)
            with open(filePath, 'w') as f:
                f.write(code)
            return f'The file contents has been written.'
        except Exception as e:
            return f'Exception encountered while writing to file. EXCEPTION: {str(e)}'

def RunCMD(self, session: str, cmd: list[str], timeout: int=30):
    env = os.environ.copy()
    env['A_IN_CONTAINER'] = '1' if self.incontainer else '0'
    self.sessions[session]['proc'] = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
    if os.name != 'nt':
        os.set_blocking(self.sessions[session]['proc'].stdout.fileno(), False)
    self.Wait(process=self.sessions[session]['proc'], timeout=timeout)
    return

class AScrollablePage:

    def __init__(self, functions: dict[str, str]):
        self.txt = None
        self.indivisibles = []
        self.currentIdx = None
        self.currentEnd = None
        self.functions = functions
        return

    def Clamp(self, x: int) -> int:
        r = 0 if x < 0 else x
        r = len(self.txt) if r > len(self.txt) else r
        return r

    def BoundCorrection(self, edge: int) -> int:
        for l, r in self.indivisibles:
            if l < edge and edge < r:
                return (l, r)
        return (edge, edge)

    def CalcWindow(self, pos: int, posType: str) -> tuple[int, int]:
        pos = self.Clamp(pos)
        delta = {'start': 0, 'mid': -STEP // 2, 'end': -STEP}
        start = pos + delta[posType]
        end = start + STEP
        start = self.Clamp(start)
        end = self.Clamp(end)
        lBound, rBound = (self.BoundCorrection(start), self.BoundCorrection(end))
        if 'start' == posType:
            return (start, rBound[0] if rBound[0] > start else rBound[1])
        elif 'end' == posType:
            return (lBound[1] if lBound[1] < end else lBound[0], end)
        elif 'mid' == posType:
            return (lBound[1], rBound[0]) if lBound[1] < rBound[0] else (lBound[0], rBound[1])

    def ConstructPrompt(self) -> str:
        ret = 'To avoid excessive consumption of context space due to lengthy content, we have paginated the entire content. This is just one page, to browse more content, please use the following function(s) for page navigation.\n'
        funcs = []
        if 'SCROLLDOWN' in self.functions and self.currentEnd < len(self.txt):
            funcs.append(self.functions['SCROLLDOWN'])
        if 'SCROLLUP' in self.functions and self.currentIdx > 0:
            funcs.append(self.functions['SCROLLUP'])
        if 'SEARCHDOWN' in self.functions and self.currentEnd < len(self.txt):
            funcs.append(self.functions['SEARCHDOWN'])
        if 'SEARCHUP' in self.functions and self.currentIdx > 0:
            funcs.append(self.functions['SEARCHUP'])
        pos = self.currentIdx
        prior = float(pos) / float(len(self.txt)) * 100 if len(self.txt) > 0 else 0.0
        remaining = float(len(self.txt) - self.currentEnd) / float(len(self.txt)) * 100 if len(self.txt) > 0 else 0.0
        return f'Prior: {prior:.1f}% / Remaining: {remaining:.1f}% \n\n' + (ret + '\n'.join(funcs) if len(funcs) > 0 else '')

    def LoadPage(self, txt: str, initPosition: str):
        self.txt = txt
        self.indivisibles = [(match.start(), match.end()) for match in re.finditer('!\\[([^\\]]*)\\]\\(([^)]+)\\)', self.txt)]
        self.currentIdx, self.currentEnd = {'TOP': self.CalcWindow(0, 'start'), 'BOTTOM': self.CalcWindow(len(txt), 'end')}[initPosition]
        return

    def ScrollDown(self) -> str:
        self.currentIdx, self.currentEnd = self.CalcWindow(self.currentEnd, 'start')
        return self()

    def ScrollUp(self) -> str:
        self.currentIdx, self.currentEnd = self.CalcWindow(self.currentIdx, 'end')
        return self()

    def SearchDown(self, query: str) -> str:
        loc = self.txt.lower().find(query.lower(), self.currentIdx)
        self.currentIdx, self.currentEnd = self.CalcWindow(loc, 'mid') if -1 != loc else (self.currentIdx, self.currentEnd)
        return self() if -1 != loc else 'NOT FOUND. \nSince this is an exact match search for text fragments, you can try using shorter query phrases to increase the success rate.'

    def SearchUp(self, query: str) -> str:
        loc = self.txt.lower().rfind(query.lower(), 0, self.currentIdx)
        self.currentIdx, self.currentEnd = self.CalcWindow(loc, 'mid') if -1 != loc else (self.currentIdx, self.currentEnd)
        return self() if -1 != loc else 'NOT FOUND. \nSince this is an exact match search for text fragments, you can try using shorter query phrases to increase the success rate.'

    def ReplaceText(self, replacement: str, replaceAll: bool=False):
        if replaceAll:
            self.txt = replacement
        else:
            self.txt = self.txt[:self.currentIdx] + replacement + self.txt[self.currentEnd:]
        return

    def __call__(self, prompt: bool=True) -> str:
        ret = self.txt[self.currentIdx:self.currentEnd]
        return f'\n\n---\n\n{ret}\n\n---\n\n{self.ConstructPrompt()}' if prompt else ret

def ScrollDown(self) -> str:
    self.currentIdx, self.currentEnd = self.CalcWindow(self.currentEnd, 'start')
    return self()

def ScrollUp(self) -> str:
    self.currentIdx, self.currentEnd = self.CalcWindow(self.currentIdx, 'end')
    return self()

def SearchDown(self, query: str) -> str:
    loc = self.txt.lower().find(query.lower(), self.currentIdx)
    self.currentIdx, self.currentEnd = self.CalcWindow(loc, 'mid') if -1 != loc else (self.currentIdx, self.currentEnd)
    return self() if -1 != loc else 'NOT FOUND. \nSince this is an exact match search for text fragments, you can try using shorter query phrases to increase the success rate.'

def SearchUp(self, query: str) -> str:
    loc = self.txt.lower().rfind(query.lower(), 0, self.currentIdx)
    self.currentIdx, self.currentEnd = self.CalcWindow(loc, 'mid') if -1 != loc else (self.currentIdx, self.currentEnd)
    return self() if -1 != loc else 'NOT FOUND. \nSince this is an exact match search for text fragments, you can try using shorter query phrases to increase the success rate.'

class ALLMPool:

    def __init__(self, config):
        self.pool = dict()
        self.config = config
        return

    def ParseID(self, id):
        split = id.find(':')
        return (id[:split], id[split + 1:])

    def Init(self, llmIDs: list[str]):
        MODEL_WRAPPER_MAP = {'AModelChatGPT': AModelChatGPT, 'AModelMistral': AModelMistral, 'AModelAnthropic': AModelAnthropic}
        if 0 == len(requirements):
            MODEL_WRAPPER_MAP['AModelCausalLM'] = AModelCausalLM
            MODEL_WRAPPER_MAP['AModelLLAMA'] = AModelCausalLM
        llmIDs = list(set([id for k, id in self.config.agentModelConfig.items()] + [id for id in llmIDs if '' != id])) if '' in llmIDs else llmIDs
        for id in llmIDs:
            modelType, modelName = self.ParseID(id)
            if 0 != len(requirements) and self.config.models[modelType]['modelWrapper'] in ['AModelCausalLM', 'AModelLLAMA']:
                print(f'The specified modelID {id} requires the installation of the following dependencies: {str(requirements)}. Please execute the following command to install: pip install {' '.join(requirements)}')
                sys.exit(0)
            if id not in self.pool:
                self.pool[id] = MODEL_WRAPPER_MAP[self.config.models[modelType]['modelWrapper']](modelType=modelType, modelName=modelName, config=self.config)
        return

    def GetModel(self, modelID: str, agentType: str):
        if '' == modelID:
            if 'DEFAULT' not in self.config.agentModelConfig:
                print('You did not configure a default modelID (agentModelConfig["DEFAULT"]), which makes config.json invalid and unable to start. Please update your configuration.')
                sys.exit(0)
            modelID = self.config.agentModelConfig.get(agentType, self.config.agentModelConfig['DEFAULT'])
        return self.pool[modelID]

def ParseID(self, id):
    split = id.find(':')
    return (id[:split], id[split + 1:])

