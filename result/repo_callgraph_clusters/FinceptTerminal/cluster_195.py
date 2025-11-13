# Cluster 195

class WebSocketClient:
    """WebSocket client for real-time data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws = None

    def connect(self, on_message=None, on_error=None, on_close=None):
        """Connect to WebSocket"""
        url = f'wss://ws.finnhub.io?token={self.api_key}'

        def on_open(ws):
            print('WebSocket connection opened')
        self.ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
        self.ws.run_forever()

    def subscribe(self, symbol: str, data_type: str='trade'):
        """Subscribe to real-time data"""
        if self.ws:
            message = json.dumps({'type': f'subscribe-{data_type}', 'symbol': symbol})
            self.ws.send(message)

    def unsubscribe(self, symbol: str, data_type: str='trade'):
        """Unsubscribe from real-time data"""
        if self.ws:
            message = json.dumps({'type': f'unsubscribe-{data_type}', 'symbol': symbol})
            self.ws.send(message)

def connect(self, on_message=None, on_error=None, on_close=None):
    """Connect to WebSocket"""
    url = f'wss://ws.finnhub.io?token={self.api_key}'

    def on_open(ws):
        print('WebSocket connection opened')
    self.ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
    self.ws.run_forever()

