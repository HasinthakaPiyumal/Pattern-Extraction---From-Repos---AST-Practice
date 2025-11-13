# Cluster 13

def generate_document_id(file_path: str, content: str) -> str:
    unique_str = f'{file_path}:{content}'
    return hashlib.md5(unique_str.encode('utf-8')).hexdigest()

class AssetConfig:

    def __init__(self):
        self.asset_url = os.getenv('ASSET_URL', '/static')
        self.cache_timeout = int(os.getenv('ASSET_CACHE_TIMEOUT', '31536000'))
        self.debug_assets = os.getenv('ASSET_DEBUG', 'False').lower() == 'true'
        self.asset_version = os.getenv('ASSET_VERSION', self._generate_version())

    def _generate_version(self) -> str:
        return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]

    def get_asset_url(self, filename: str) -> str:
        if self.debug_assets:
            timestamp = datetime.now().timestamp()
            return f'{self.asset_url}/{filename}?t={timestamp}'
        return f'{self.asset_url}/{filename}?v={self.asset_version}'

def _generate_version(self) -> str:
    return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]

def get_asset_url(self, filename: str) -> str:
    if self.debug_assets:
        timestamp = datetime.now().timestamp()
        return f'{self.asset_url}/{filename}?t={timestamp}'
    return f'{self.asset_url}/{filename}?v={self.asset_version}'

