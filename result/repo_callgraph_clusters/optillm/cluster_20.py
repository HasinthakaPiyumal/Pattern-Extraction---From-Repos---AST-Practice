# Cluster 20

class DeviceManager:

    def __init__(self):
        self.available_devices = self._detect_devices()
        self.device_stats = {device: {'memory_used': 0, 'active_models': 0} for device in self.available_devices}

    def _detect_devices(self) -> List[str]:
        devices = ['cpu']
        if torch.cuda.is_available():
            devices.extend([f'cuda:{i}' for i in range(torch.cuda.device_count())])
        if torch.backends.mps.is_available():
            devices.append('mps')
        return devices

    def get_optimal_device(self, model_size: int=0) -> str:
        if not self.available_devices:
            return 'cpu'
        cuda_devices = [d for d in self.available_devices if 'cuda' in d]
        if cuda_devices:
            max_free_memory = 0
            optimal_device = cuda_devices[0]
            for device in cuda_devices:
                idx = int(device.split(':')[1])
                free_memory = torch.cuda.get_device_properties(idx).total_memory - torch.cuda.memory_allocated(idx)
                if free_memory > max_free_memory:
                    max_free_memory = free_memory
                    optimal_device = device
            return optimal_device
        if 'mps' in self.available_devices:
            return 'mps'
        return 'cpu'

    def track_device_usage(self, device: str, memory_delta: int):
        if device in self.device_stats:
            self.device_stats[device]['memory_used'] += memory_delta

def __init__(self):
    self.available_devices = self._detect_devices()
    self.device_stats = {device: {'memory_used': 0, 'active_models': 0} for device in self.available_devices}

