# Cluster 75

class CallbackManager:

    def __init__(self):
        self.local_data = threading.local()

    def _ensure_callbacks(self):
        if not hasattr(self.local_data, 'callbacks'):
            self.local_data.callbacks = {}

    def set_callback(self, callback_type: str, callback: Callback):
        self._ensure_callbacks()
        self.local_data.callbacks[callback_type] = callback

    def get_callback(self, callback_type: str):
        self._ensure_callbacks()
        return self.local_data.callbacks.get(callback_type, None)

    def has_callback(self, callback_type: str):
        self._ensure_callbacks()
        return callback_type in self.local_data.callbacks

    def clear_callback(self, callback_type: str):
        self._ensure_callbacks()
        if callback_type in self.local_data.callbacks:
            del self.local_data.callbacks[callback_type]

    def clear_all(self):
        self._ensure_callbacks()
        self.local_data.callbacks.clear()

def __init__(self):
    self.local_data = threading.local()

