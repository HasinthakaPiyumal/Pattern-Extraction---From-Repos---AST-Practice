# Cluster 165

class FinanceTerminalLogger:
    """Production-ready logger with automatic class detection"""
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.config = LogConfig()
        self.metrics = PerformanceMetrics()
        self.stack_inspector = StackInspector()
        self.logger = logging.getLogger('finance_terminal')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        self._setup_file_handler()
        if self.config.console_enabled:
            self._setup_console_handler()
        self.logger.propagate = False
        self._start_maintenance_thread()
        self._direct_log(logging.INFO, 'Finance terminal logger initialized', 'FinanceTerminalLogger')

    def _setup_file_handler(self):
        """Setup rotating file handler"""
        try:
            logs_dir = self.config.get_logs_dir()
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_file = logs_dir / 'finance_terminal.log'
            file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=self.config.max_file_size, backupCount=self.config.backup_count, encoding='utf-8')
            file_handler.setFormatter(AutoDetectFormatter(self.config))
            file_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)
            self.file_handler = file_handler
        except Exception as e:
            print(f'Failed to setup file logging: {e}')

    def _setup_console_handler(self):
        """Setup console handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(AutoDetectFormatter(self.config))
        level = logging.DEBUG if self.config.debug_mode else logging.INFO
        console_handler.setLevel(level)
        self.logger.addHandler(console_handler)
        self.console_handler = console_handler

    def _start_maintenance_thread(self):
        """Start background maintenance thread"""

        def maintenance():
            while True:
                try:
                    time.sleep(300)
                    self._cleanup_old_logs()
                    self._flush_handlers()
                except Exception:
                    pass
        thread = threading.Thread(target=maintenance, daemon=True, name='LogMaintenance')
        thread.start()

    def _cleanup_old_logs(self):
        """Clean up old log files"""
        try:
            logs_dir = self.config.get_logs_dir()
            cutoff = datetime.now() - timedelta(days=self.config.retention_days)
            for log_file in logs_dir.glob('*.log*'):
                if log_file.stat().st_mtime < cutoff.timestamp():
                    log_file.unlink()
        except Exception:
            pass

    def _flush_handlers(self):
        """Flush all handlers"""
        try:
            for handler in self.logger.handlers:
                handler.flush()
        except Exception:
            pass

    def _direct_log(self, level: int, message: str, class_name: str, context: Optional[Dict[str, Any]]=None, exc_info: bool=False):
        """Direct logging method without stack inspection"""
        try:
            if context:
                context_str = ' | '.join((f'{k}={v}' for k, v in context.items()))
                full_message = f'{message} | {context_str}'
            else:
                full_message = message
            record = self.logger.makeRecord(name=self.logger.name, level=level, fn='', lno=0, msg=full_message, args=(), exc_info=sys.exc_info() if exc_info else None)
            record.detected_class = class_name
            self.logger.handle(record)
            level_name = logging.getLevelName(level)
            self.metrics.record_log(level_name, full_message, class_name)
        except Exception:
            pass

    def _log(self, level: int, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None, exc_info: bool=False):
        """Core logging method with automatic class detection"""
        try:
            if module:
                class_name = module
            else:
                class_name = self.stack_inspector.get_caller_class_name()
            self._direct_log(level, message, class_name, context, exc_info)
        except Exception:
            pass

    def debug(self, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None):
        """Log debug message"""
        self._log(logging.DEBUG, message, module, context)

    def info(self, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None):
        """Log info message"""
        self._log(logging.INFO, message, module, context)

    def warning(self, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None):
        """Log warning message"""
        self._log(logging.WARNING, message, module, context)

    def error(self, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None, exc_info: bool=False):
        """Log error message"""
        self._log(logging.ERROR, message, module, context, exc_info)

    def critical(self, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None, exc_info: bool=False):
        """Log critical message"""
        self._log(logging.CRITICAL, message, module, context, exc_info)

    @contextmanager
    def operation(self, name: str, module: Optional[str]=None, **kwargs):
        """Context manager for operation logging"""
        start_time = time.time()
        self.debug(f'Starting: {name}', module=module, context=kwargs)
        try:
            yield
            duration = time.time() - start_time
            self.debug(f'Completed: {name}', module=module, context={'duration_ms': f'{duration * 1000:.1f}'})
        except Exception as e:
            duration = time.time() - start_time
            self.error(f'Failed: {name}', module=module, context={'duration_ms': f'{duration * 1000:.1f}', 'error': str(e)}, exc_info=True)
            raise

    def monitor_performance(self, func):
        """Performance monitoring decorator"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            class_name = None
            if args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
            with self.operation(func.__name__, module=class_name):
                return func(*args, **kwargs)
        return wrapper

    def set_level(self, level: Union[int, str]):
        """Set logging level"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.logger.setLevel(level)

    def enable_console(self, enable: bool=True):
        """Enable/disable console logging"""
        if enable and (not hasattr(self, 'console_handler')):
            self._setup_console_handler()
        elif not enable and hasattr(self, 'console_handler'):
            self.logger.removeHandler(self.console_handler)
            delattr(self, 'console_handler')

    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        stats = self.metrics.get_summary()
        stats['config'] = {'debug_mode': self.config.debug_mode, 'console_enabled': self.config.console_enabled, 'logs_directory': str(self.config.get_logs_dir())}
        return stats

    def get_recent_errors(self, limit: int=10) -> List[Dict[str, Any]]:
        """Get recent error messages"""
        with self.metrics._lock:
            errors = list(self.metrics.recent_errors)[-limit:]
            for error in errors:
                error['timestamp'] = datetime.fromtimestamp(error['timestamp']).isoformat()
            return errors

    def health_check(self) -> Dict[str, Any]:
        """Check logger health"""
        try:
            test_message = f'Health check at {datetime.now().isoformat()}'
            self._direct_log(logging.DEBUG, test_message, 'HealthCheck')
            return {'status': 'healthy', 'logs_directory': str(self.config.get_logs_dir()), 'stats': self.get_stats()}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}

def debug(self, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None):
    """Log debug message"""
    self._log(logging.DEBUG, message, module, context)

def info(self, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None):
    """Log info message"""
    self._log(logging.INFO, message, module, context)

def warning(self, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None):
    """Log warning message"""
    self._log(logging.WARNING, message, module, context)

def error(self, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None, exc_info: bool=False):
    """Log error message"""
    self._log(logging.ERROR, message, module, context, exc_info)

def critical(self, message: str, module: Optional[str]=None, context: Optional[Dict[str, Any]]=None, exc_info: bool=False):
    """Log critical message"""
    self._log(logging.CRITICAL, message, module, context, exc_info)

