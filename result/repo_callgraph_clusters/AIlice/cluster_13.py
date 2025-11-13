# Cluster 13

def GuessMediaType(pathOrUrl: str) -> str:
    mimetype, _ = mimetypes.guess_type(pathOrUrl)
    if None != mimetype:
        return mimetype
    r = requests.head(pathOrUrl)
    return r.headers.get('content-type')

class AComputer:

    def __init__(self):
        self.lock = threading.Lock()
        if 0 == len(requirements):
            self.clicks = {'click': pyautogui.click, 'double-click': pyautogui.doubleClick, 'right-click': pyautogui.rightClick, 'middle': pyautogui.middleClick}
            self.reader = easyocr.Reader(['en'])
        return

    def ModuleInfo(self):
        return {'NAME': 'computer', 'ACTIONS': {'SCREENSHOT': {'func': 'ScreenShot', 'prompt': 'Take a screenshot of the current screen.', 'type': 'primary'}, 'LOCATEANDCLICK': {'func': 'LocateAndClick', 'prompt': "Locate the control containing a piece of text on the screenshot and click on it. clickType is a string, and its value can only be one of 'click', 'double-click', 'right-click' or 'middle'.", 'type': 'primary'}, 'LOCATEANDSCROLL': {'func': 'LocateAndScroll', 'prompt': 'Move to the position marked by the text and scroll the mouse wheel.', 'type': 'primary'}, 'TYPEWRITE': {'func': 'TypeWrite', 'prompt': 'Simulate keyboard input for the string. Please ensure that the focus has been moved to the location where input is expected.', 'type': 'primary'}, 'READ-IMAGE': {'func': 'ReadImage', 'prompt': 'Read the content of an image file into a variable.', 'type': 'primary'}, 'WRITE-IMAGE': {'func': 'WriteImage', 'prompt': 'Write a variable of image type into a file.', 'type': 'primary'}}}

    def Locate(self, txt: str):
        image = ImageGrab.grab()
        results = self.reader.readtext(numpy.array(image.convert('L')), slope_ths=0.0, ycenter_ths=0.0, width_ths=0.0)
        for detection in results:
            bbox = detection[0]
            text = detection[1]
            if txt in text:
                x, y = (int((bbox[0][0] + bbox[2][0]) * 0.5), int((bbox[0][1] + bbox[2][1]) * 0.5))
                return (x, y, text)
        return None

    def ScreenShot(self) -> AImage:
        with self.lock:
            imageByte = io.BytesIO()
            ImageGrab.grab().save(imageByte, format='JPEG')
            return AImage(data=imageByte.getvalue())

    def LocateAndClick(self, txt: str, clickType: str) -> str:
        with self.lock:
            if 0 != len(requirements):
                return f'python package(s) {[x for x in requirements]} not found. Please install it before using this feature.'
            if clickType not in self.clicks:
                return f"LOCATEANDCLICK ERROR. clickType: {clickType} can only be one of 'click', 'double-click', 'right-click' or 'middle'."
            ret = self.Locate(txt)
            if None != ret:
                x, y, text = ret
                pyautogui.moveTo(x, y, duration=0.5)
                self.clicks[clickType]()
                return f"'''{text}''' at {x},{y} is clicked."
            else:
                return f"'''{txt}''' not found. It may be because the text has been segmented into different boxes by the OCR software. Please try a shorter and distinctive substring."

    def LocateAndScroll(self, txt: str, clicks: float) -> str:
        with self.lock:
            if 0 != len(requirements):
                return f'python package(s) {[x for x in requirements]} not found. Please install it before using this feature.'
            ret = self.Locate(txt)
            if None != ret:
                x, y, text = ret
                pyautogui.moveTo(x, y, duration=0.5)
                pyautogui.scroll(clicks)
                return f'The mouse wheel has scrolled {clicks} times.'
            else:
                return f"'''{txt}''' not found. It may be because the text has been segmented into different boxes by the OCR software. Please try a shorter and distinctive substring."

    def TypeWrite(self, txt: str) -> str:
        with self.lock:
            if 0 != len(requirements):
                return f'python package(s) {[x for x in requirements]} not found. Please install it before using this feature.'
            pyautogui.typewrite(txt)
            return f"'''{txt}''' the string has already been typed."

    def ReadImage(self, path: str) -> AImage:
        try:
            return AImageLocation(urlOrPath=path).Standardize()
        except Exception as e:
            print('ReadImage() excetption: ', e)
        return AImage(data=None)

    def WriteImage(self, image: AImage, path: str) -> str:
        try:
            Image.open(io.BytesIO(image.data)).save(path)
            return f'The image has been written to {path}.'
        except Exception as e:
            print('WriteImage() excetption: ', e)
            return f'WriteImage() excetption: {str(e)}'
        return

    def WriteFile(self, data: bytes, path: str) -> str:
        try:
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(path, 'wb') as file:
                file.write(data)
            return f'The file has been written to {path}.'
        except Exception as e:
            print('WriteFile() excetption: ', e)
            return f'WriteFile() excetption: {str(e)}'
        return

    def Proxy(self, href: str, method: str, headers: dict={}, body: dict={}, params: dict={}) -> typing.Generator:
        if os.path.exists(href):
            filePath = os.path.abspath(href)
            fileSize = os.path.getsize(filePath)
            fileName = os.path.basename(filePath)
            contentType, encoding = mimetypes.guess_type(filePath)
            if contentType is None:
                contentType = 'application/octet-stream'
            startByte = 0
            endByte = fileSize - 1
            statusCode = 200
            if headers and 'Range' in headers:
                rangeHeader = headers['Range']
                rangeMatch = re.match('bytes=(\\d+)-(\\d*)', rangeHeader)
                if rangeMatch:
                    startByte = int(rangeMatch.group(1))
                    if rangeMatch.group(2):
                        endByte = min(int(rangeMatch.group(2)), fileSize - 1)
                    statusCode = 206
            responseHeaders = {'Content-Type': contentType, 'Content-Length': str(endByte - startByte + 1), 'Accept-Ranges': 'bytes', 'Content-Disposition': f"""inline; filename="{urllib.parse.quote(fileName)}"; filename*=UTF-8''{urllib.parse.quote(fileName)}""", 'Last-Modified': datetime.datetime.fromtimestamp(os.stat(filePath).st_mtime, tz=datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}
            if statusCode == 206:
                responseHeaders['Content-Range'] = f'bytes {startByte}-{endByte}/{fileSize}'
            responseInfo = {'status_code': statusCode, 'headers': responseHeaders}
            yield responseInfo
            if method.upper() != 'HEAD':

                def content_generator():
                    with open(filePath, 'rb') as file:
                        if startByte > 0:
                            file.seek(startByte)
                        bytesToRead = endByte - startByte + 1
                        bytesRead = 0
                        while bytesRead < bytesToRead:
                            chunkSize = min(262144, bytesToRead - bytesRead)
                            chunk = file.read(chunkSize)
                            if not chunk:
                                break
                            bytesRead += len(chunk)
                            yield chunk
                yield from content_generator()
        else:
            req = requests.request(method=method, url=href, headers=headers, data=body, params=params, stream=True)
            responseInfo = {'status_code': req.status_code, 'headers': dict(req.headers)}
            yield responseInfo
            if method.upper() != 'HEAD':

                def content_generator():
                    try:
                        for chunk in req.iter_content(chunk_size=262144):
                            if chunk:
                                yield chunk
                    finally:
                        req.close()
                yield from content_generator()

def Proxy(self, href: str, method: str, headers: dict={}, body: dict={}, params: dict={}) -> typing.Generator:
    if os.path.exists(href):
        filePath = os.path.abspath(href)
        fileSize = os.path.getsize(filePath)
        fileName = os.path.basename(filePath)
        contentType, encoding = mimetypes.guess_type(filePath)
        if contentType is None:
            contentType = 'application/octet-stream'
        startByte = 0
        endByte = fileSize - 1
        statusCode = 200
        if headers and 'Range' in headers:
            rangeHeader = headers['Range']
            rangeMatch = re.match('bytes=(\\d+)-(\\d*)', rangeHeader)
            if rangeMatch:
                startByte = int(rangeMatch.group(1))
                if rangeMatch.group(2):
                    endByte = min(int(rangeMatch.group(2)), fileSize - 1)
                statusCode = 206
        responseHeaders = {'Content-Type': contentType, 'Content-Length': str(endByte - startByte + 1), 'Accept-Ranges': 'bytes', 'Content-Disposition': f"""inline; filename="{urllib.parse.quote(fileName)}"; filename*=UTF-8''{urllib.parse.quote(fileName)}""", 'Last-Modified': datetime.datetime.fromtimestamp(os.stat(filePath).st_mtime, tz=datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}
        if statusCode == 206:
            responseHeaders['Content-Range'] = f'bytes {startByte}-{endByte}/{fileSize}'
        responseInfo = {'status_code': statusCode, 'headers': responseHeaders}
        yield responseInfo
        if method.upper() != 'HEAD':

            def content_generator():
                with open(filePath, 'rb') as file:
                    if startByte > 0:
                        file.seek(startByte)
                    bytesToRead = endByte - startByte + 1
                    bytesRead = 0
                    while bytesRead < bytesToRead:
                        chunkSize = min(262144, bytesToRead - bytesRead)
                        chunk = file.read(chunkSize)
                        if not chunk:
                            break
                        bytesRead += len(chunk)
                        yield chunk
            yield from content_generator()
    else:
        req = requests.request(method=method, url=href, headers=headers, data=body, params=params, stream=True)
        responseInfo = {'status_code': req.status_code, 'headers': dict(req.headers)}
        yield responseInfo
        if method.upper() != 'HEAD':

            def content_generator():
                try:
                    for chunk in req.iter_content(chunk_size=262144):
                        if chunk:
                            yield chunk
                finally:
                    req.close()
            yield from content_generator()

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

def URLIsPDF(self, url: str) -> bool:
    response = requests.head(url, allow_redirects=True)
    contentType = response.headers.get('content-type')
    return 'pdf' in contentType if contentType else False

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

def LoadPage(self, txt: str, initPosition: str):
    self.txt = txt
    self.indivisibles = [(match.start(), match.end()) for match in re.finditer('!\\[([^\\]]*)\\]\\(([^)]+)\\)', self.txt)]
    self.currentIdx, self.currentEnd = {'TOP': self.CalcWindow(0, 'start'), 'BOTTOM': self.CalcWindow(len(txt), 'end')}[initPosition]
    return

def extract_answer(response: str) -> str:
    """
    Extract the final answer from the response.
    
    Args:
        response: The complete response string
    Returns:
        The extracted answer or empty string
    """
    match = re.search('FINAL ANSWER:\\s*(.*?)(?:\\n|$)', response, re.IGNORECASE | re.DOTALL)
    if not match:
        logging.warning(f"No 'FINAL ANSWER:' found in response: {response}")
        return ''
    return match.group(1).strip()

class AInterpreter:

    def __init__(self, messenger):
        self.actions = {}
        self.patterns = []
        self.env = {}
        self.messenger = messenger
        self.RegisterPattern('_STR', f'(?P<txt>({ARegexMap['str']}))', False)
        self.RegisterPattern('_INT', f'(?P<txt>({ARegexMap['int']}))', False)
        self.RegisterPattern('_FLOAT', f'(?P<txt>({ARegexMap['float']}))', False)
        self.RegisterPattern('_BOOL', f'(?P<txt>({ARegexMap['bool']}))', False)
        self.RegisterPattern('_VAR', VAR_DEF, True)
        self.RegisterPattern('_PRINT', GenerateRE4FunctionCalling('PRINT<!|txt: str|!> -> str', faultTolerance=True), True)
        self.RegisterAction('_PRINT', {'func': self.EvalPrint})
        self.RegisterPattern('_VAR_REF', f'(?P<varName>({ARegexMap['ref']}))', False)
        self.RegisterPattern('_EXPR_CAT', f'(?P<expr>({ARegexMap['expr_cat']}))', False)
        for dataType in typeInfo:
            if not typeInfo[dataType]['tag']:
                continue
            self.RegisterPattern(f'_EXPR_OBJ_{dataType.__name__}', GenerateRE4ObjectExpr([(fieldName, fieldInfo.annotation.__name__) for fieldName, fieldInfo in dataType.model_fields.items()], dataType.__name__, faultTolerance=True), False)
            self.RegisterAction(f'_EXPR_OBJ_{dataType.__name__}', {'func': self.CreateObjCB(dataType)})
        self.RegisterPattern('_EXPR_OBJ_DEFAULT', EXPR_OBJ, False)
        self.RegisterAction('_EXPR_OBJ_DEFAULT', {'func': self.EvalObjDefault, 'noEval': ['typeBra', 'typeKet']})
        return

    def RegisterAction(self, nodeType: str, action: dict):
        signature = inspect.signature(action['func'])
        if not all([param.annotation != inspect.Parameter.empty for param in signature.parameters.values()]):
            print('Need annotations in registered function. node type: ', nodeType)
            exit()
        self.actions[nodeType] = {k: v for k, v in action.items()}
        self.actions[nodeType]['signature'] = signature
        return

    def RegisterPattern(self, nodeType: str, pattern: str, isEntry: bool, noTrunc: bool=False, priority: int=0):
        p = {'nodeType': nodeType, 're': pattern, 'isEntry': isEntry, 'noTrunc': noTrunc, 'priority': priority}
        if pattern not in [p['re'] for p in self.patterns]:
            loc = 0
            for loc in range(0, len(self.patterns)):
                if self.patterns[loc]['priority'] > priority:
                    break
            self.patterns.insert(loc, p)
        return

    def CreateVar(self, content: Any, basename: str, dynamicSuffix: bool=True) -> str:
        if dynamicSuffix and basename not in self.env:
            varName = basename
        else:
            varName = f'{basename}_{type(content).__name__}_{str(random.randint(0, 999999))}'
        self.env[varName] = content
        return varName

    def EndChecker(self, txt: str) -> bool:
        endPatterns = [p['re'] for p in self.patterns if p['isEntry'] and (not p['noTrunc']) and (HasReturnValue(self.actions[p['nodeType']]) if p['nodeType'] in self.actions else False)]
        return any([bool(re.findall(pattern, txt, re.DOTALL)) for pattern in endPatterns]) or None != self.messenger.Get()

    def GetEntryPatterns(self) -> dict[str, str]:
        return [(p['nodeType'], p['re']) for p in self.patterns if p['isEntry']]

    def Parse(self, txt: str) -> tuple[str, dict[str, str]]:
        for p in self.patterns:
            m = re.fullmatch(p['re'], txt, re.DOTALL)
            if m:
                return (p['nodeType'], m.groupdict())
        return (None, None)

    def CallWithTextArgs(self, nodeType, txtArgs) -> Any:
        action = self.actions[nodeType]
        signature = action['signature']
        if set(txtArgs.keys()) != set(signature.parameters.keys()):
            return 'The function call failed because the arguments did not match. txtArgs.keys(): ' + str(txtArgs.keys()) + '. func params: ' + str(signature.parameters.keys())
        paras = dict()
        for k, v in txtArgs.items():
            paras[k] = v if k in action.get('noEval', []) else self.Eval(v)
            if type(paras[k]) != signature.parameters[k].annotation:
                raise TypeError(f'parameter {k} should be of type {signature.parameters[k].annotation.__name__}, but got {type(paras[k]).__name__}.')
        return action['func'](**paras)

    def Eval(self, txt: str) -> Any:
        nodeType, paras = self.Parse(txt)
        if None == nodeType:
            return txt
        elif '_STR' == nodeType:
            return self.EvalStr(txt)
        elif '_INT' == nodeType:
            return int(txt)
        elif '_FLOAT' == nodeType:
            return float(txt)
        elif '_BOOL' == nodeType:
            return {'true': True, 'false': False}[txt.strip().lower()]
        elif '_VAR' == nodeType:
            return self.EvalVar(varName=paras['varName'], content=self.Eval(paras['content']))
        elif '_VAR_REF' == nodeType:
            return self.EvalVarRef(txt)
        elif '_EXPR_CAT' == nodeType:
            return self.EvalExprCat(txt)
        else:
            return self.CallWithTextArgs(nodeType, paras)

    def ParseEntries(self, txt_input: str) -> list[str]:
        ms = {}
        for nodeType, pattern in self.GetEntryPatterns():
            for match in re.finditer(pattern, txt_input, re.DOTALL):
                ms[match.start(), match.end()] = match
        matches = sorted(list(ms.values()), key=lambda match: match.start())
        ret = []
        for match in matches:
            isSubstring = any((m.start() <= match.start() and m.end() >= match.end() and (m is not match) for m in matches))
            if not isSubstring:
                ret.append(match.group(0))
        return ret

    def EvalEntries(self, txt: str) -> str:
        scripts = self.ParseEntries(txt)
        resp = ''
        try:
            for script in scripts:
                r = self.Eval(script)
                r = self.ConvertToText(r)
                if r not in ['', None]:
                    resp += r + '\n\n'
        except SyntaxError as e:
            resp += f'EXCEPTION: {str(e)}\n{traceback.format_exc()}\n'
            if 'unterminated string literal' in str(e):
                resp += 'Please check if there are any issues with your string syntax. For instance, are you using a newline within a single-quoted string? Or should you use triple quotes to avoid error-prone escape sequences?'
        except AExceptionStop as e:
            raise e
        except AExceptionOutofGas as e:
            resp += 'The current task has run out of gas and has been terminated. Please ask the user to help recharge gas.'
        except Exception as e:
            resp += f'EXCEPTION: {str(e)}\n{(e.tb if hasattr(e, 'tb') else traceback.format_exc())}'
        return resp

    def EvalStr(self, txt: str) -> str:
        return ast.literal_eval(txt)

    def EvalVarRef(self, varName: str) -> Any:
        if varName in self.env:
            return self.env[varName]
        else:
            raise ValueError(f'Variable name {varName} NOT FOUND, did you mean to use a string "{varName}" but forgot the quotation marks?')

    def EvalVar(self, varName: str, content: Any):
        self.env[varName] = content
        return

    def EvalExprCat(self, expr: str) -> str:
        pattern = f'{ARegexMap['str']}|{ARegexMap['ref']}'
        ret = ''
        for match in re.finditer(pattern, expr):
            ret += self.Eval(match.group(0))
        return ret

    def EvalObjDefault(self, typeBra: str, args: str, typeKet: str) -> Any:
        if typeBra != typeKet:
            raise ValueError(f'The left and right types in braket should be the same. But in fact the left side is ({typeBra}), and the right side is ({typeKet}). Please correct your syntax.')
        if typeBra not in [t.__name__ for t in typeInfo.keys()] + ['&', '!']:
            raise ValueError(f'The specified object type ({typeBra}) is not supported. Please check your input.')
        if '!' == typeBra.strip():
            return args
        elif '&' == typeBra.strip():
            return self.env.get(args.strip())
        else:
            raise ValueError(f'It looks like you are trying to create an object of type ({typeBra}), but syntax parsing fails for unrecognized reasons. Please check your syntax.')

    def EvalPrint(self, txt: str) -> str:
        return txt

    def CreateObjCB(self, dataType):

        def callback(*args, **kwargs):
            return dataType(*args, **kwargs)
        newSignature = inspect.Signature(parameters=[inspect.Parameter(name=t.name, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=t.annotation) for p, t in inspect.signature(dataType.__init__).parameters.items() if t.name != 'self'], return_annotation=dataType)
        callback.__signature__ = newSignature
        return callback

    def ConvertToText(self, r) -> str:
        if type(r) == str or r is None:
            return r
        elif type(r) in typeInfo:
            varName = self.CreateVar(content=r, basename='ret')
            return f'![Returned data is stored to variable: {varName} := {str(r)}]({varName})<&>'
        elif type(r) == list:
            return f'{str([self.ConvertToText(item) for item in r])}'
        elif type(r) == tuple:
            return f'{str((self.ConvertToText(item) for item in r))}'
        elif type(r) == dict:
            res = {k: self.ConvertToText(v) for k, v in r.items()}
            return f'{str(res)}'
        else:
            return str(r)

    def ToJson(self):
        return {'env': {k: ToJson(v) for k, v in self.env.items()}}

    def FromJson(self, data):
        self.env = {k: FromJson(v) for k, v in data['env'].items()}
        return

def ParseEntries(self, txt_input: str) -> list[str]:
    ms = {}
    for nodeType, pattern in self.GetEntryPatterns():
        for match in re.finditer(pattern, txt_input, re.DOTALL):
            ms[match.start(), match.end()] = match
    matches = sorted(list(ms.values()), key=lambda match: match.start())
    ret = []
    for match in matches:
        isSubstring = any((m.start() <= match.start() and m.end() >= match.end() and (m is not match) for m in matches))
        if not isSubstring:
            ret.append(match.group(0))
    return ret

def EvalExprCat(self, expr: str) -> str:
    pattern = f'{ARegexMap['str']}|{ARegexMap['ref']}'
    ret = ''
    for match in re.finditer(pattern, expr):
        ret += self.Eval(match.group(0))
    return ret

