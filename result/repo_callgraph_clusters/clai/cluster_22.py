# Cluster 22

class Provider:
    base_uri: str = ''
    excludes: list = []

    def __init__(self, name: str, description: str, section: dict):
        self.name = name
        self.description = description
        api_value: str = section.get('api')
        self.base_uri = api_value if api_value.endswith('/') else api_value + '/'
        if 'exclude' in section.keys():
            self.excludes = [excludeTarget.lower() for excludeTarget in section.get('exclude').split()]
        else:
            self.excludes = []
        if 'variants' in section.keys():
            self.variants = [variant.upper() for variant in section.get('variants').split()]
        else:
            self.variants = []

    def __str__(self) -> str:
        return self.description

    def __log_info__(self, message):
        logger.info(f'{self.name}: {message}')

    def __log_warning__(self, message):
        logger.warning(f'{self.name}: {message}')

    def __log_debug__(self, message):
        logger.debug(f'{self.name}: {message}')

    def __log_json__(self, data):
        output: List[str] = ['']
        getters: List[str] = []
        is_json_data: bool = False
        if isinstance(data, Request):
            output.append(f'{data.method} --> {data.url}')
            getters = ['files', 'data', 'json', 'params', 'auth', 'cookies', 'hooks']
        elif isinstance(data, Response):
            output.append(f'RESPONSE[{data.status_code}] <-- {data.url}')
            getters = ['apparent_encoding', 'cookies', 'elapsed', 'encoding', 'ok', 'status_code', 'reason', 'content']
        if data.headers.keys():
            output.append('.--[Headers]'.ljust(80, '-'))
            for key in data.headers.keys():
                if key == 'Content-Type':
                    if '/json' in data.headers[key]:
                        is_json_data = True
                line_header = f'|    {key}: '
                print_data: str = str(data.headers[key])
                if len(print_data) > 64:
                    print_data = f'{print_data[:50]} ... {print_data[-10:]}'
                output.append(f'{line_header}{print_data}')
            output.append('`'.ljust(80, '-'))
        for method in getters:
            result = getattr(data, method)
            if method == 'content' and is_json_data:
                outstr = json.dumps(json.loads(result), indent=2)
                output.append(f'{method}: ' + outstr.replace('\n', '\n\t'))
            else:
                print_data: str = str(result)
                line_header = f'{method}: '
                if len(print_data) > 64:
                    print_data = f'{print_data[:50]} ... {print_data[-10:]}'
                output.append(f'{line_header}{print_data}')
        self.__log_info__('\n\t'.join(output))

    def __set_default_values__(self, args: dict, **kwargs) -> dict:
        for key in kwargs.keys():
            if key not in args:
                args[key] = kwargs[key]
        return args

    def __send_request__(self, method: str, uri: str, **kwargs) -> Response:
        kwargs = self.__set_default_values__(kwargs, headers={'Content-Type': 'application/json', 'Accept': '*/*'}, data=None, params=None)
        request: Request = Request(method, uri.rstrip('/'), headers=kwargs['headers'], data=kwargs['data'], params=kwargs['params'])
        self.__log_json__(request)
        session: Session = Session()
        response: Response = session.send(request=request.prepare())
        self.__log_json__(response)
        return response

    def __send_get_request__(self, uri: str, **kwargs):
        return self.__send_request__(method='GET', uri=uri, **kwargs)

    def __send_post_request__(self, uri: str, **kwargs):
        return self.__send_request__(method='POST', uri=uri, **kwargs)

    def get_excludes(self) -> list:
        """Returns a list of operating systems that the search provider cannot
          be run from
        """
        return self.excludes

    def has_variants(self) -> bool:
        """Returns `True` if this search provider has more than one search
          variant
        """
        return len(self.variants) > 0

    def get_variants(self) -> list:
        """Returns a list of search variants supported by this search provider
        """
        return self.variants

    def can_run_on_this_os(self) -> bool:
        """Returns True if this search provider can be used on the client OS
        """
        if not self.excludes:
            return True
        os_name: str = os.uname().sysname.lower()
        return os_name not in self.excludes

    @abc.abstractclassmethod
    def extract_search_result(self, data: List[Dict]) -> str:
        """Given the result of an API search, extract the search result from it
        """
        pass

    @abc.abstractclassmethod
    def get_printable_output(self, data: List[Dict]) -> str:
        """Extract the result string from the data returned by an API search
        """
        pass

    @abc.abstractclassmethod
    def call(self, query: str, limit: int=1, **kwargs):
        """Perform a query on the API
        """
        pass

def __send_get_request__(self, uri: str, **kwargs):
    return self.__send_request__(method='GET', uri=uri, **kwargs)

def __send_post_request__(self, uri: str, **kwargs):
    return self.__send_request__(method='POST', uri=uri, **kwargs)

