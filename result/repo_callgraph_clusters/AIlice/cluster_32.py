# Cluster 32

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

def __init__(self, api_key: str, cse_id: str):
    self.api_key = api_key
    self.cse_id = cse_id
    self.service = build('customsearch', 'v1', developerKey=self.api_key)
    self.sessions = {}
    self.functions = {'SCROLLDOWN': '#scroll down the page: \nSCROLL-DOWN-GOOGLE<!|session: str|!>'}
    return

