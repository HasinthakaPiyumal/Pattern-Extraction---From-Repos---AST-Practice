# Cluster 16

class AJSONDecoder(json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, object_hook=self.object_hook, **kwargs)

    def object_hook(self, obj):
        try:
            if '_type' not in obj:
                return obj
            type = obj['_type']
            if type == 'bytes':
                return base64.b64decode(obj['value'].encode('utf-8'))
            elif type == 'AImage':
                return AImage.FromJson(obj['value'])
            elif type == 'AImageLocation':
                return AImageLocation.FromJson(obj['value'])
            elif type == 'AVideo':
                return AVideo.FromJson(obj['value'])
            elif type == 'AVideoLocation':
                return AVideoLocation.FromJson(obj['value'])
            else:
                ModelType = pydantic.create_model(obj['_type'], **obj['value'])
                return ModelType().model_validate_json(obj['value'])
        except Exception as e:
            print('AJSONDecoder Exception. ', str(e))
            return obj

def __init__(self, *args, **kwargs):
    super().__init__(*args, object_hook=self.object_hook, **kwargs)

class AImage(BaseModel):
    data: Optional[bytes]
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

    def __init__(self, **params):
        super().__init__(**params)
        if self.data and (not all([self.format, self.width, self.height])):
            meta = self.GetMeta()
            self.format = meta['format']
            self.width = meta['width']
            self.height = meta['height']
        return

    def GetMeta(self):
        if self.data:
            image = Image.open(io.BytesIO(self.data))
            return {'width': image.width, 'height': image.height, 'format': image.format}
        else:
            return {'width': 0, 'height': 0, 'format': None}

    def __str__(self) -> str:
        return f'< AImage object in {self.format} format. >'

    @classmethod
    def FromJson(cls, data):
        return cls(data=base64.b64decode(data['data'].encode('utf-8')))

    def ToJson(self):
        return {'type': 'AImage', 'format': self.format, 'data': base64.b64encode(self.data).decode('utf-8') if self.data else self.data}

    def Convert(self, format: str):
        if format == self.format or not self.data:
            return self
        imageBytes = io.BytesIO()
        image = Image.open(io.BytesIO(self.data))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(imageBytes, format=format)
        return AImage(data=imageBytes.getvalue())

    def Standardize(self):
        return self.Convert(format='JPEG')

def __init__(self, **params):
    super().__init__(**params)
    if self.data and (not all([self.format, self.width, self.height])):
        meta = self.GetMeta()
        self.format = meta['format']
        self.width = meta['width']
        self.height = meta['height']
    return

class AVideo(BaseModel):
    data: Optional[bytes]
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None

    def __init__(self, **params):
        super().__init__(**params)
        if self.data and (not all([self.format, self.width, self.height, self.fps])):
            meta = self.GetMeta()
            self.format = meta['format']
            self.width = meta['width']
            self.height = meta['height']
            self.fps = meta['fps']
        return

    def GetMeta(self):
        ret = {'width': 0, 'height': 0, 'fps': 0, 'format': None}
        if self.data:
            video = av.open(io.BytesIO(self.data))
            stream = next((s for s in video.streams if s.type == 'video'), None)
            if stream is not None:
                ret = {'width': stream.codec_context.width, 'height': stream.codec_context.height, 'fps': stream.average_rate, 'format': video.format}
            video.close()
        return ret

    def __str__(self) -> str:
        return f'< AVideo object in {self.format} format. >'

    @classmethod
    def FromJson(cls, data):
        return cls(data=base64.b64decode(data['data'].encode('utf-8')))

    def ToJson(self):
        return {'type': 'AVideo', 'format': self.format, 'data': base64.b64encode(self.data).decode('utf-8') if self.data else self.data}

    def Standardize(self):
        return AVideo(data=ConvertVideoFormat(self.data, 'mp4')) if self.data else self

def __init__(self, **params):
    super().__init__(**params)
    if self.data and (not all([self.format, self.width, self.height, self.fps])):
        meta = self.GetMeta()
        self.format = meta['format']
        self.width = meta['width']
        self.height = meta['height']
        self.fps = meta['fps']
    return

class DatasetAIliceTrace(GeneratorBasedBuilder):
    VERSION = datasets.Version('1.0.0')

    def __init__(self, maxWindow: int, **kwargs):
        super().__init__(**kwargs)
        self.maxWindow = maxWindow
        return

    def _info(self):
        return DatasetInfo(description='AIlice trace dataset', features=Features({'conversations': Sequence({'role': Value('string'), 'msg': Value('string')})}), supervised_keys=None)

    def _split_generators(self, dl_manager):
        return [SplitGenerator(name=Split.TRAIN, gen_kwargs={'datasetDir': dl_manager.manual_dir, 'datasetType': 'train'}), SplitGenerator(name=Split.VALIDATION, gen_kwargs={'datasetDir': dl_manager.manual_dir, 'datasetType': 'validation'})]

    def _generate_examples(self, datasetDir, datasetType):
        idx = -1
        directoryPath = Path(datasetDir)
        for jsonFile in directoryPath.glob('*.json'):
            with jsonFile.open('r', encoding='utf-8') as f:
                data = json.load(f)
                convs = self.ExtractConversations(data)
                left, right = {'train': (0, int(0.8 * len(convs))), 'validation': (int(0.8 * len(convs)), len(convs))}[datasetType]
                for conv in convs[left:right]:
                    for convPiece in self.Split(conv):
                        idx += 1
                        yield (idx, {'conversations': convPiece})

    def ExtractConversations(self, trace):
        convs = []
        agentTrace = trace
        convs.append(agentTrace['conversations'])
        if 'subProcessors' in agentTrace:
            for subAgent in agentTrace['subProcessors']:
                convs += self.ExtractConversations(agentTrace['subProcessors'][subAgent])
        return convs

    def Split(self, conv):
        ret = [[]]
        currentLen = 0
        for c in conv:
            currentLen += len(f'{c['role']}: {c['msg']}')
            if currentLen // 4 >= self.maxWindow:
                ret.append([c])
                currentLen = 0
            else:
                ret[-1].append(c)
        return ret

def __init__(self, maxWindow: int, **kwargs):
    super().__init__(**kwargs)
    self.maxWindow = maxWindow
    return

class MyDataCollatorWithPadding(transformers.DataCollatorWithPadding):

    def __init__(self, tokenizer, padding=True, return_tensors='pt'):
        super().__init__(tokenizer, padding=padding, return_tensors=return_tensors)
        return

    def __call__(self, features):
        labels = [feature['labels'] for feature in features]
        maxLabelLength = max((len(label) for label in labels))
        paddedLabels = [F.pad(label, pad=(0, maxLabelLength - len(label)), value=self.tokenizer.pad_token_id) for label in labels]
        features = [{k: v for k, v in feature.items() if k != 'labels'} for feature in features]
        batch = super().__call__(features)
        batch['labels'] = torch.stack(paddedLabels)
        return batch

def __init__(self, tokenizer, padding=True, return_tensors='pt'):
    super().__init__(tokenizer, padding=padding, return_tensors=return_tensors)
    return

def __call__(self, features):
    labels = [feature['labels'] for feature in features]
    maxLabelLength = max((len(label) for label in labels))
    paddedLabels = [F.pad(label, pad=(0, maxLabelLength - len(label)), value=self.tokenizer.pad_token_id) for label in labels]
    features = [{k: v for k, v in feature.items() if k != 'labels'} for feature in features]
    batch = super().__call__(features)
    batch['labels'] = torch.stack(paddedLabels)
    return batch

class ADuckDuckGo:

    def __init__(self):
        self.baseURL = 'https://api.duckduckgo.com/'
        self.sessions = {}
        self.functions = {'SCROLLDOWN': '#scroll down the page: \nSCROLL-DOWN-DUCKDUCKGO<!|session: str|!>'}
        return

    def ModuleInfo(self):
        return {'NAME': 'duckduckgo', 'ACTIONS': {'DUCKDUCKGO': {'func': 'DuckDuckGo', 'prompt': 'Use duckduckgo to search internet content.', 'type': 'primary'}, 'SCROLL-DOWN-DUCKDUCKGO': {'func': 'ScrollDown', 'prompt': 'Scrolldown the results.', 'type': 'supportive'}}}

    def GetSessionID(self) -> str:
        id = f'session-{str(random.randint(0, 99999999))}'
        while id in self.sessions:
            id = f'session-{str(random.randint(0, 99999999))}'
        return id

    def DuckDuckGo(self, keywords: str) -> str:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(keywords, max_results=10)]
            ret = str(results) if len(results) > 0 else 'No search results were found. Please check if you used overly complex keywords or unsupported search syntax. Note that relaxing your search terms is an effective strategy when no valid search results are returned.'
        except Exception as e:
            print(f'Error during the request: {e}')
            ret = str(e)
        finally:
            loop.close()
        session = self.GetSessionID()
        self.sessions[session] = AScrollablePage(functions=self.functions)
        self.sessions[session].LoadPage(str(ret), 'TOP')
        return self.sessions[session]() + '\n\n' + f'Session name: "{session}"\n'

    def ScrollDown(self, session: str) -> str:
        return self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

def ScrollDown(self, session: str) -> str:
    return self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

class AGoogle:

    def __init__(self, api_key: str, cse_id: str):
        self.api_key = api_key
        self.cse_id = cse_id
        self.service = build('customsearch', 'v1', developerKey=self.api_key)
        self.sessions = {}
        self.functions = {'SCROLLDOWN': '#scroll down the page: \nSCROLL-DOWN-GOOGLE<!|session: str|!>'}
        return

    def ModuleInfo(self):
        return {'NAME': 'google', 'ACTIONS': {'GOOGLE': {'func': 'Google', 'prompt': 'Use Google to search the web.', 'type': 'primary'}, 'SCROLL-DOWN-GOOGLE': {'func': 'ScrollDown', 'prompt': 'Scroll down the search results.', 'type': 'supportive'}}}

    def GetSessionID(self) -> str:
        id = f'session-{str(random.randint(0, 99999999))}'
        while id in self.sessions:
            id = f'session-{str(random.randint(0, 99999999))}'
        return id

    def Google(self, keywords: str) -> str:
        try:
            res = self.service.cse().list(q=keywords, cx=self.cse_id).execute()
            results = res.get('items', [])
            ret = str(results) if len(results) > 0 else 'No search results were found. Please check if you used overly complex keywords or unsupported search syntax. Note that relaxing your search terms is an effective strategy when no valid search results are returned.'
        except Exception as e:
            print('Google Search exception: ', e)
            ret = f'Google Search exception: {str(e)}'
        session = self.GetSessionID()
        self.sessions[session] = AScrollablePage(functions=self.functions)
        self.sessions[session].LoadPage(str(ret), 'TOP')
        return self.sessions[session]() + '\n\n' + f'Session name: "{session}"\n'

    def ScrollDown(self, session: str) -> str:
        return self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

def ScrollDown(self, session: str) -> str:
    return self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

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

def __init__(self, functions: dict[str, str]):
    super(AWebBrowser, self).__init__(functions=functions)
    self.inited = False
    self.driver = None
    self.urls = {}
    self.prompt = '\nThe text with links are enclosed in square brackets to highlight it. If you need to open the page linked to a certain text, please call GET-LINK<!|text: str, session: str|!> function to get the url, and then call BROWSE<!|url: str, session: str|!>. Please note that the text parameter of GET-LINK must exactly match the content in the square brackets (excluding the square brackets themselves).\nThe forms on the webpage have been listed in text format, and you can use the EXECUTE-JS<!|js_code: str, session: str|!> function to operate the form, such as entering text, clicking buttons, etc. Use triple quotes on your code. Example: \n!EXECUTE-JS<!|"""\ndocument.querySelector(\'form.mini-search input[name="query"]\').value = "hello world";\ndocument.querySelector(\'form.mini-search\').submit();\n""", "arxiv_session"|!>\n'
    return

def ScrollDown(self) -> str:
    return super(AWebBrowser, self).ScrollDown() + self.prompt

def ScrollUp(self) -> str:
    return super(AWebBrowser, self).ScrollUp() + self.prompt

def SearchDown(self, query: str) -> str:
    return super(AWebBrowser, self).SearchDown(query) + self.prompt

def SearchUp(self, query: str) -> str:
    return super(AWebBrowser, self).SearchUp(query) + self.prompt

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

def __init__(self, pdfOutputDir: str, functions: dict[str, str]):
    super(APDFBrowser, self).__init__(functions=functions)
    self.pdfOutputDir = pdfOutputDir
    if 'pix2text' == OCROption:
        self.p2t = Pix2Text.from_config()
    return

class ATextBrowser(AScrollablePage):

    def __init__(self, functions: dict[str, str]):
        super(ATextBrowser, self).__init__(functions=functions)
        self.path = None
        self.prompt = '\nThe document is in editable mode. You can edit the content using the following functions:\n#Replace the matching content within the current page. When regexMode==True, you can use regular expressions to represent the pattern and replacement. This function is a simple wrapper for re.sub() in this mode. When regexMode==False, pattern and replacement represent literal strings. Use triple quotes to represent pattern and replacement.\nREPLACE<!|pattern: str, replacement: str, regexMode: bool, session: str|!> -> str\n#Replace all matching content in the entire document. The parameters are the same as REPLACE.\nREPLACE-ALL<!|pattern: str, replacement: str, regexMode: bool, session: str|!> -> str\n#Save the modified content to a file. If the dstPath parameter is an empty string, save it to the original file.\nSAVETO<!|dstPath: str, session: str|!> -> str\n\nExample:\n!REPLACE<!|"""Hello World!""", """Hello Python!""", False, "session_example"|!>\n!SAVETO<!|"", "session_example"|!>\n'
        return

    def Browse(self, url: str) -> str:
        parsedURL = urlparse(url)
        if parsedURL.scheme in ['file', ''] and '' == parsedURL.netloc:
            try:
                with open(parsedURL.path, 'r', encoding='utf-8') as f:
                    self.LoadPage(f.read(), 'TOP')
                    self.path = None
                    return self()
            except Exception as e:
                self.LoadPage(f'Exception: {str(e)}.', 'BOTTOM')
                return self()
        else:
            response = requests.get(url)
            if response.status_code != 200:
                return f'Error: can not download text file. HTTP err code: {response.status_code}'
            if 'text' not in response.headers.get('Content-Type', ''):
                return 'The url returned non-text content and cannot be browsed.'
            self.LoadPage(response.content, 'TOP')
            return self()

    def Edit(self, path: str) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.LoadPage(f.read(), 'TOP')
                self.path = path
                return self() + self.prompt
        except Exception as e:
            self.LoadPage(f'Exception: {str(e)}.', 'BOTTOM')
            return self()

    def Replace(self, pattern: str, replacement: str, regexMode: bool) -> str:
        if regexMode:
            textNew = re.sub(pattern, replacement, self(prompt=False))
        else:
            textNew = self(prompt=False).replace(pattern, replacement)
        msg = 'Pattern NOT FOUND in current visible page. Please check: 1. If the pattern you entered is correct, such as whether you forgot to properly escape characters within the quotes. 2. Ensure that the content to be replaced is within the currently visible page (you can use the SEARCHDOWN/SEARCHUP to locate it, or directly use the REPLACE-ALL to replace all matching content).\n\n'
        if self(prompt=False) != textNew or '' == pattern:
            msg = 'The matching contents has been replaced. \n\n'
        self.ReplaceText(textNew, replaceAll=False)
        return msg + self() + self.prompt

    def ReplaceAll(self, pattern: str, replacement: str, regexMode: bool) -> str:
        if regexMode:
            textNew = re.sub(pattern, replacement, self.txt)
        else:
            textNew = self.txt.replace(pattern, replacement)
        msg = 'Pattern NOT FOUND in the entire document. Please check if the pattern you entered is correct, such as whether you forgot to properly escape characters within the quotes.\n\n'
        if self.txt != textNew or '' == pattern:
            msg = 'The matching contents has been replaced. \n\n'
        self.ReplaceText(textNew, replaceAll=True)
        return msg + self() + self.prompt

    def SaveTo(self, dstPath: str) -> str:
        try:
            dstPath = self.path if dstPath.strip() == '' and self.path != None else dstPath
            d = os.path.dirname(dstPath)
            if d.strip() != '':
                os.makedirs(d, exist_ok=True)
            with open(dstPath, 'w') as f:
                f.write(self.txt)
            return f'File {dstPath} saved.'
        except Exception as e:
            return f'Failed to save file {dstPath}, Exception: {str(e)}'

    def GetFullText(self) -> str:
        return self.txt if self.txt != None else ''

    def ScrollDown(self) -> str:
        return super(ATextBrowser, self).ScrollDown() + (self.prompt if self.path else '')

    def ScrollUp(self) -> str:
        return super(ATextBrowser, self).ScrollUp() + (self.prompt if self.path else '')

    def SearchDown(self, query: str) -> str:
        return super(ATextBrowser, self).SearchDown(query) + (self.prompt if self.path else '')

    def SearchUp(self, query: str) -> str:
        return super(ATextBrowser, self).SearchUp(query) + (self.prompt if self.path else '')

    def Destroy(self):
        return

def __init__(self, functions: dict[str, str]):
    super(ATextBrowser, self).__init__(functions=functions)
    self.path = None
    self.prompt = '\nThe document is in editable mode. You can edit the content using the following functions:\n#Replace the matching content within the current page. When regexMode==True, you can use regular expressions to represent the pattern and replacement. This function is a simple wrapper for re.sub() in this mode. When regexMode==False, pattern and replacement represent literal strings. Use triple quotes to represent pattern and replacement.\nREPLACE<!|pattern: str, replacement: str, regexMode: bool, session: str|!> -> str\n#Replace all matching content in the entire document. The parameters are the same as REPLACE.\nREPLACE-ALL<!|pattern: str, replacement: str, regexMode: bool, session: str|!> -> str\n#Save the modified content to a file. If the dstPath parameter is an empty string, save it to the original file.\nSAVETO<!|dstPath: str, session: str|!> -> str\n\nExample:\n!REPLACE<!|"""Hello World!""", """Hello Python!""", False, "session_example"|!>\n!SAVETO<!|"", "session_example"|!>\n'
    return

def ScrollDown(self) -> str:
    return super(ATextBrowser, self).ScrollDown() + (self.prompt if self.path else '')

def ScrollUp(self) -> str:
    return super(ATextBrowser, self).ScrollUp() + (self.prompt if self.path else '')

def SearchDown(self, query: str) -> str:
    return super(ATextBrowser, self).SearchDown(query) + (self.prompt if self.path else '')

def SearchUp(self, query: str) -> str:
    return super(ATextBrowser, self).SearchUp(query) + (self.prompt if self.path else '')

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

def ScrollUp(self, session: str) -> str:
    with self.sessionsLock:
        return self.sessions[session]['pages'].ScrollUp() + '\n\n' + f'Session name: "{session}"\n'

class AArxiv:

    def __init__(self):
        self.sessions = {}
        self.functions = {'SCROLLDOWN': '#scroll down the page: \nSCROLL-DOWN-ARXIV<!|session: str|!>'}
        self.lock = threading.Lock()
        return

    def ModuleInfo(self):
        return {'NAME': 'arxiv', 'ACTIONS': {'ARXIV': {'func': 'ArxivSearch', 'prompt': 'Search arXiv for academic papers.\nParameters:\n- query (str): The search query. Construct queries with:\n    - Logical combinations: AND/OR/ANDNOT operators\n    - Field restrictions: Limit searches to specific fields using these options:\n        - \'ti\': Title\n        - \'au\': Author\n        - \'abs\': Abstract\n        - \'co\': Comment\n        - \'jr\': Journal Reference\n        - \'cat\': Subject Category\n        - \'rn\': Report Number\n        - \'id\': Id\n        - \'all\': All of the above\n\n- options (str): A JSON string with search parameters. Pass \'{}\' to use all default values.\n  - sort_by (optional, str): Sort criterion. Default: \'relevance\'. Options: \'relevance\', \'lastUpdatedDate\', \'submittedDate\'.\n  - sort_order (optional, str): Sort order. Default: \'descending\'. Options: \'ascending\', \'descending\'.\n  - max_results (optional, int): Number of results to return. Default: 10.\n  \nExamples:\nARXIV<!|query="transformer architecture", options=\'{"max_results": 5, "sort_by": "submittedDate"}\'|!>\nARXIV<!|query=\'cat:hep-ph ANDNOT ti:"quantum gravity"\', options=\'{"sort_by": "submittedDate", "sort_order": "descending", "max_results": 5}\'|!>', 'type': 'primary'}, 'SCROLL-DOWN-ARXIV': {'func': 'ScrollDown', 'prompt': 'Scroll down the results.', 'type': 'supportive'}}}

    def GetSessionID(self) -> str:
        with self.lock:
            id = f'session-{str(random.randint(0, 99999999))}'
            while id in self.sessions:
                id = f'session-{str(random.randint(0, 99999999))}'
            return id

    def ParseEntry(self, entry: arxiv.Result) -> dict:
        return {'arxiv_id': entry.entry_id.split('/')[-1], 'title': entry.title, 'authors': [author.name for author in entry.authors], 'summary': entry.summary.replace('\n', ' '), 'published_date': entry.published.isoformat(), 'pdf_url': entry.pdf_url}

    def FormatResults(self, results: list) -> str:
        if not results:
            return 'No search results were found. Please check if you used overly complex keywords or unsupported search syntax. Note that relaxing your search terms is an effective strategy when no valid search results are returned.'
        return '\n\n---\n\n'.join((f'Result {i + 1}:\n  ID: {r['arxiv_id']}\n  Title: {r['title']}\n  Authors: {', '.join(r['authors'])}\n  Summary: {r['summary']}\n  Published: {r['published_date']}\n  PDF URL: {r['pdf_url']}' for i, r in enumerate(results)))

    def ArxivSearch(self, query: str, options: str) -> str:
        try:
            try:
                opts = json.loads(options) if options else {}
            except json.JSONDecodeError:
                return 'Error: Invalid JSON format in options parameter.'
            sort_by = opts.get('sort_by', 'relevance')
            sort_order = opts.get('sort_order', 'descending')
            max_results = opts.get('max_results', 10)
            sort_criterion = {'relevance': arxiv.SortCriterion.Relevance, 'lastUpdatedDate': arxiv.SortCriterion.LastUpdatedDate, 'submittedDate': arxiv.SortCriterion.SubmittedDate}[sort_by]
            sort_order_enum = {'ascending': arxiv.SortOrder.Ascending, 'descending': arxiv.SortOrder.Descending}[sort_order]
            search = arxiv.Search(query=query, max_results=max_results, sort_by=sort_criterion, sort_order=sort_order_enum)
            ret = self.FormatResults([self.ParseEntry(r) for r in list(search.results())[:max_results]])
        except Exception as e:
            ret = f'arxiv exception: {str(e)}'
        session = self.GetSessionID()
        content = AScrollablePage(functions=self.functions)
        content.LoadPage(str(ret), 'TOP')
        with self.lock:
            self.sessions[session] = content
        return content() + '\n\n' + f'Session name: "{session}"\n'

    def ScrollDown(self, session: str) -> str:
        with self.lock:
            if session not in self.sessions:
                return 'Invalid session ID.'
            return self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

def ScrollDown(self, session: str) -> str:
    with self.lock:
        if session not in self.sessions:
            return 'Invalid session ID.'
        return self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

class AGoogle:

    def __init__(self):
        self.sessions = {}
        self.functions = {'SCROLLDOWN': '#scroll down the page: \nSCROLL-DOWN-GOOGLE<!|session: str|!>'}
        return

    def ModuleInfo(self):
        return {'NAME': 'google', 'ACTIONS': {'GOOGLE': {'func': 'Google', 'prompt': 'Use google to search internet content.', 'type': 'primary'}, 'SCROLL-DOWN-GOOGLE': {'func': 'ScrollDown', 'prompt': 'Scroll down the results.', 'type': 'supportive'}}}

    def GetSessionID(self) -> str:
        id = f'session-{str(random.randint(0, 99999999))}'
        while id in self.sessions:
            id = f'session-{str(random.randint(0, 99999999))}'
        return id

    def Google(self, keywords: str) -> str:
        try:
            res = search(keywords, num_results=20, advanced=True, sleep_interval=5)
            results = list(res)
            ret = str(results) if len(results) > 0 else 'No search results were found. Please check if you used overly complex keywords or unsupported search syntax. Note that relaxing your search terms is an effective strategy when no valid search results are returned.'
        except Exception as e:
            print('google excetption: ', e)
            ret = f'google excetption: {str(e)}'
        session = self.GetSessionID()
        self.sessions[session] = AScrollablePage(functions=self.functions)
        self.sessions[session].LoadPage(str(ret), 'TOP')
        return self.sessions[session]() + '\n\n' + f'Session name: "{session}"\n'

    def ScrollDown(self, session: str) -> str:
        return self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

def ScrollDown(self, session: str) -> str:
    return self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

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

def ScrollDown(self):
    return super(AWebBrowser, self).ScrollDown() + self.prompt

def ScrollUp(self):
    return super(AWebBrowser, self).ScrollUp() + self.prompt

def SearchDown(self, query):
    return super(AWebBrowser, self).SearchDown(query) + self.prompt

def SearchUp(self, query):
    return super(AWebBrowser, self).SearchUp(query) + self.prompt

class ABrowser:

    def __init__(self, pdfOutputDir: str):
        self.pdfOutputDir = pdfOutputDir
        self.sessions = {}
        self.functions = {'SCROLLDOWN': '#scroll down the page: \nSCROLL-DOWN-BROWSER<!|session: str|!>', 'SCROLLUP': '#scroll up the page: \nSCROLL-UP-BROWSER<!|session: str|!>', 'SEARCHDOWN': '#search the content downward and jumps the page to the next matching point(Just like the F3 key normally does): \nSEARCH-DOWN-BROWSER<!|query: str, session: str|!>', 'SEARCHUP': '#search the content upward and jumps the page to the next matching point: \nSEARCH-UP-BROWSER<!|query: str, session: str|!>'}
        self.prompt = 'The browser is running in headless mode, mouse and keyboard operations are not supported. All operations on the page must be accomplished using the functions listed after the page content.'
        return

    def ModuleInfo(self):
        return {'NAME': 'browser', 'ACTIONS': {'BROWSE': {'func': 'Browse', 'prompt': "Open any PDFs, web pages in headless mode to retrieve their content. The 'url' parameter can be either a URL or a local path. You need to give the page a name(the session parameter). You can reuse this session to open new url/path.", 'type': 'primary'}, 'BROWSE-EDIT': {'func': 'Edit', 'prompt': 'Browse and edit any text document (including code files with various extensions) in headless mode. You need to give the page a name(the session parameter). You can reuse this session to open new file.', 'type': 'primary'}, 'SCROLL-DOWN-BROWSER': {'func': 'ScrollDown', 'prompt': 'Scroll down the page.', 'type': 'supportive'}, 'SCROLL-UP-BROWSER': {'func': 'ScrollUp', 'prompt': 'Scroll up the page.', 'type': 'supportive'}, 'SEARCH-DOWN-BROWSER': {'func': 'SearchDown', 'prompt': 'Search content downward from the current location.', 'type': 'supportive'}, 'SEARCH-UP-BROWSER': {'func': 'SearchUp', 'prompt': 'Search content upward from the current location.', 'type': 'supportive'}, 'GET-LINK': {'func': 'GetLink', 'prompt': 'Get the url on the specified text fragment. The text needs to be one of those text fragments enclosed by square brackets on the page (excluding the square brackets themselves).', 'type': 'supportive'}, 'EXECUTE-JS': {'func': 'ExecuteJS', 'prompt': 'Execute js code on the current web page, especially suitable for form operations such as entering text, clicking buttons, etc. Use triple quotes on your code.', 'type': 'supportive'}, 'REPLACE': {'func': 'Replace', 'prompt': 'Replace the matching content within the current page. When regexMode==True, you can use regular expressions to represent the pattern and replacement. This function is a simple wrapper for re.sub() in this mode. When regexMode==False, pattern and replacement represent literal strings. Use triple quotes to represent pattern and replacement.', 'type': 'supportive'}, 'REPLACE-ALL': {'func': 'ReplaceAll', 'prompt': 'Replace all matching content in the entire document. When regexMode==True, you can use regular expressions to represent the pattern and replacement. This function is a simple wrapper for re.sub() in this mode. When regexMode==False, pattern and replacement represent literal strings. Use triple quotes to represent pattern and replacement.', 'type': 'supportive'}, 'SAVETO': {'func': 'SaveTo', 'prompt': 'Save the modified content to a file. If the dstPath parameter is an empty string, save it to the original file.', 'type': 'supportive'}}}

    def ParseURL(self, txt: str) -> str:
        extractor = URLExtract()
        urls = extractor.find_urls(txt)
        if 0 == len(urls):
            print('ParseURL: no url provided. ', txt)
            return None
        else:
            url = urls[0]
        return url

    def ParsePath(self, txt: str) -> str:
        pattern = '^(\\/.*|[^\\/].*)$'
        matches = re.findall(pattern, txt)
        if not matches:
            print('ParsePath: no path provided. ', txt)
            return None
        else:
            return matches[0].strip()

    def GetLocation(self, txt: str) -> tuple[str, str]:
        url = self.ParseURL(txt)
        if url is not None:
            return (self.ToHttps(url), None)
        path = self.ParsePath(txt)
        if path is not None:
            return (None, path)
        return (None, None)

    def ToHttps(self, url: str) -> str:
        if not urlparse(url).scheme:
            url = 'https://' + url
        return url

    def URLIsPDF(self, url: str) -> bool:
        response = requests.head(url, allow_redirects=True)
        contentType = response.headers.get('content-type')
        return 'pdf' in contentType if contentType else False

    def PathIsPDF(self, path: str) -> bool:
        return path[-4:] == '.pdf'

    def Browse(self, url: str, session: str) -> str:
        try:
            if session in self.sessions:
                self.sessions[session].Destroy()
                self.sessions.pop(session)
            url, path = self.GetLocation(url)
            if url is not None:
                if self.URLIsPDF(url):
                    self.sessions[session] = APDFBrowser(self.pdfOutputDir, functions=self.functions)
                    return self.prompt + '\n\n' + self.sessions[session].Browse(url) + '\n\n' + f'Session name: "{session}"\n'
                else:
                    self.sessions[session] = AWebBrowser(functions=self.functions)
                    return self.prompt + '\n\n' + self.sessions[session].Browse(url) + '\n\n' + f'Session name: "{session}"\n'
            elif path is not None:
                if os.path.isdir(path):
                    self.sessions[session] = AFileBrowser(functions=self.functions)
                    return self.prompt + '\n\n' + self.sessions[session].Browse(path) + '\n\n' + f'Session name: "{session}"\n'
                elif self.PathIsPDF(path):
                    self.sessions[session] = APDFBrowser(self.pdfOutputDir, functions=self.functions)
                    return self.prompt + '\n\n' + self.sessions[session].Browse(path) + '\n\n' + f'Session name: "{session}"\n'
                else:
                    self.sessions[session] = ATextBrowser(functions=self.functions)
                    return self.prompt + '\n\n' + self.sessions[session].Browse(path) + '\n\n' + f'Session name: "{session}"\n'
            else:
                return 'No URL/Path found in input string. Please check your input. '
        except Exception as e:
            print('EXCEPTION. e: ', str(e))
            return f'Browser Exception. please check your url input. EXCEPTION: {str(e)}\n{traceback.format_exc()}'

    def ExecuteJS(self, js_code: str, session: str) -> str:
        return self.sessions[session].ExecuteJS(js_code) if hasattr(self.sessions[session], 'ExecuteJS') else 'ExecuteJS not supported in current browser.'

    def Edit(self, path: str, session: str) -> str:
        try:
            if session in self.sessions:
                self.sessions[session].Destroy()
                self.sessions.pop(session)
            self.sessions[session] = ATextBrowser(functions=self.functions)
            return self.prompt + '\n\n' + self.sessions[session].Edit(path) + '\n\n' + f'Session name: "{session}"\n'
        except Exception as e:
            print('EXCEPTION. e: ', str(e))
            return f'Browser Exception. please check your path input. EXCEPTION: {str(e)}\n{traceback.format_exc()}'
        return

    def GetFullText(self, session: str) -> str:
        return self.sessions[session].GetFullText() if session in self.sessions else f'ERROR: Invalid session name: {session}'

    def ScrollDown(self, session: str) -> str:
        return self.prompt + '\n\n' + self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

    def ScrollUp(self, session: str) -> str:
        return self.prompt + '\n\n' + self.sessions[session].ScrollUp() + '\n\n' + f'Session name: "{session}"\n'

    def SearchDown(self, query: str, session: str) -> str:
        return self.prompt + '\n\n' + self.sessions[session].SearchDown(query=query) + '\n\n' + f'Session name: "{session}"\n'

    def SearchUp(self, query: str, session: str) -> str:
        return self.prompt + '\n\n' + self.sessions[session].SearchUp(query=query) + '\n\n' + f'Session name: "{session}"\n'

    def GetLink(self, text: str, session: str) -> str:
        return self.sessions[session].GetLink(text) if hasattr(self.sessions[session], 'GetLink') else 'GetLink not supported in current browser.'

    def Replace(self, pattern: str, replacement: str, regexMode: bool, session: str) -> str:
        return self.sessions[session].Replace(pattern, replacement, regexMode) if hasattr(self.sessions[session], 'Replace') else 'Replace not supported in current browser.'

    def ReplaceAll(self, pattern: str, replacement: str, regexMode: bool, session: str) -> str:
        return self.sessions[session].ReplaceAll(pattern, replacement, regexMode) if hasattr(self.sessions[session], 'ReplaceAll') else 'ReplaceAll not supported in current browser.'

    def SaveTo(self, dstPath: str, session: str) -> str:
        return self.sessions[session].SaveTo(dstPath) if hasattr(self.sessions[session], 'SaveTo') else 'SaveTo not supported in current browser.'

    def Destroy(self):
        for _, session in self.sessions.items():
            destroy = getattr(session, 'Destroy', None)
            if callable(destroy):
                destroy()
        self.sessions.clear()
        self.computer = None
        self.scripter = None
        return

def ScrollDown(self, session: str) -> str:
    return self.prompt + '\n\n' + self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

def ScrollUp(self, session: str) -> str:
    return self.prompt + '\n\n' + self.sessions[session].ScrollUp() + '\n\n' + f'Session name: "{session}"\n'

def SearchDown(self, query: str, session: str) -> str:
    return self.prompt + '\n\n' + self.sessions[session].SearchDown(query=query) + '\n\n' + f'Session name: "{session}"\n'

def SearchUp(self, query: str, session: str) -> str:
    return self.prompt + '\n\n' + self.sessions[session].SearchUp(query=query) + '\n\n' + f'Session name: "{session}"\n'

class AFileBrowser(AScrollablePage):

    def __init__(self, functions: dict[str, str]):
        super(AFileBrowser, self).__init__(functions=functions)
        return

    def Browse(self, path: str) -> str:
        if not (os.path.exists(path) and os.path.isdir(path)):
            return f'Specified directory {path} does NOT exist.'
        files = []
        dirs = []
        for filename in os.listdir(path):
            if os.path.isfile(os.path.join(path, filename)):
                files.append(filename)
            else:
                dirs.append(filename)
        self.LoadPage('Folders: ' + ' '.join(dirs) + '\n\nFiles: ' + ' '.join(files), 'BOTTOM')
        return self()

    def Destroy(self):
        return

def __init__(self, functions: dict[str, str]):
    super(AFileBrowser, self).__init__(functions=functions)
    return

