# Cluster 155

class FinanceNotificationSystem:
    """Main notification system for finance terminal"""
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
        self.config = NotificationConfig()
        self.rate_limiter = NotificationRateLimiter(self.config)
        self.metrics = NotificationMetrics()
        self.available = NOTIFYPY_AVAILABLE and self.config.enabled and (not self.config.silent_mode)
        if LOGGER_AVAILABLE:
            if self.available:
                info('Notification system initialized', module='notifications')
            else:
                warning('Notification system disabled or unavailable', module='notifications')

    def _create_notification(self, title: str, message: str, level: NotificationLevel) -> Optional[Notify]:
        """Create a notification object"""
        if not self.available:
            return None
        try:
            notification = Notify()
            notification.title = title
            notification.message = message
            notification.application_name = self.config.app_name
            if self.config.app_icon:
                notification.icon = self.config.app_icon
            return notification
        except Exception as e:
            if LOGGER_AVAILABLE:
                error(f'Failed to create notification: {e}', module='notifications')
            self.metrics.record_failed()
            return None

    def _send_notification(self, title: str, message: str, level: NotificationLevel, module: Optional[str]=None, **kwargs) -> bool:
        """Core notification sending method"""
        if level.value not in self.config.enabled_levels:
            return False
        if not self.rate_limiter.should_allow(title, message, level):
            self.metrics.record_rate_limited()
            if LOGGER_AVAILABLE and self.config.debug_notifications:
                debug(f'Rate limited notification: {title}', module='notifications')
            return False
        if module:
            tab_prefix = self.config.get_tab_prefix(module)
            title = f'{tab_prefix} {title}'
        if LOGGER_AVAILABLE:
            info(f'Sending notification: {title}', module='notifications', context={'level': level.value, 'source_module': module})
        notification = self._create_notification(title, message, level)
        if notification:
            try:
                notification.send()
                self.metrics.record_sent(level)
                return True
            except Exception as e:
                if LOGGER_AVAILABLE:
                    error(f'Failed to send notification: {e}', module='notifications')
                self.metrics.record_failed()
                return False
        return False

    def debug(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send debug notification"""
        if not self.config.debug_notifications:
            return False
        return self._send_notification(title, message, NotificationLevel.DEBUG, module, **kwargs)

    def info(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send info notification"""
        return self._send_notification(title, message, NotificationLevel.INFO, module, **kwargs)

    def success(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send success notification"""
        return self._send_notification(title, message, NotificationLevel.SUCCESS, module, **kwargs)

    def warning(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send warning notification"""
        return self._send_notification(title, message, NotificationLevel.WARNING, module, **kwargs)

    def error(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send error notification"""
        return self._send_notification(title, message, NotificationLevel.ERROR, module, **kwargs)

    def critical(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
        """Send critical notification"""
        return self._send_notification(title, message, NotificationLevel.CRITICAL, module, **kwargs)

    def trade_executed(self, symbol: str, action: str, quantity: int, price: float, module: Optional[str]='trading') -> bool:
        """Template for trade execution notifications"""
        title = 'Trade Executed'
        message = f'{action.upper()} {quantity} {symbol} @ ${price:.2f}'
        return self.success(title, message, module)

    def price_alert(self, symbol: str, current_price: float, target_price: float, condition: str, module: Optional[str]='alerts') -> bool:
        """Template for price alert notifications"""
        title = f'Price Alert: {symbol}'
        message = f'Price ${current_price:.2f} {condition} target ${target_price:.2f}'
        return self.warning(title, message, module)

    def connection_status(self, service: str, status: str, module: Optional[str]='api') -> bool:
        """Template for connection status notifications"""
        title = f'Connection {status.title()}'
        message = f'{service} connection is now {status.lower()}'
        if status.lower() in ['connected', 'restored']:
            return self.success(title, message, module)
        else:
            return self.error(title, message, module)

    def data_update(self, data_type: str, count: int, module: Optional[str]='market') -> bool:
        """Template for data update notifications"""
        title = 'Data Updated'
        message = f'{data_type}: {count} items updated'
        return self.info(title, message, module)

    def system_status(self, component: str, status: str, details: str='', module: Optional[str]='main') -> bool:
        """Template for system status notifications"""
        title = f'System {status.title()}'
        message = f'{component}: {details}' if details else component
        if status.lower() in ['started', 'ready', 'healthy']:
            return self.success(title, message, module)
        elif status.lower() in ['warning', 'degraded']:
            return self.warning(title, message, module)
        else:
            return self.error(title, message, module)

    def enable(self, enabled: bool=True):
        """Enable or disable notifications"""
        self.config.enabled = enabled
        self.available = NOTIFYPY_AVAILABLE and enabled and (not self.config.silent_mode)
        if LOGGER_AVAILABLE:
            status = 'enabled' if enabled else 'disabled'
            info(f'Notifications {status}', module='notifications')

    def set_silent_mode(self, silent: bool=True):
        """Enable or disable silent mode"""
        self.config.silent_mode = silent
        self.available = NOTIFYPY_AVAILABLE and self.config.enabled and (not silent)
        if LOGGER_AVAILABLE:
            mode = 'silent' if silent else 'normal'
            info(f'Notification mode: {mode}', module='notifications')

    def set_debug_notifications(self, enabled: bool=True):
        """Enable or disable debug notifications"""
        self.config.debug_notifications = enabled

    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        stats = self.metrics.get_stats()
        stats.update({'config': {'enabled': self.config.enabled, 'silent_mode': self.config.silent_mode, 'available': self.available, 'rate_limiting': self.config.rate_limit_enabled, 'enabled_levels': list(self.config.enabled_levels)}})
        return stats

    def health_check(self) -> Dict[str, Any]:
        """Check notification system health"""
        try:
            if not NOTIFYPY_AVAILABLE:
                return {'status': 'unavailable', 'reason': 'notifypy not installed'}
            if not self.config.enabled:
                return {'status': 'disabled', 'reason': 'notifications disabled in config'}
            if self.config.silent_mode:
                return {'status': 'silent', 'reason': 'silent mode enabled'}
            test_title = 'Health Check'
            test_message = f'Notification system test at {datetime.now().strftime('%H:%M:%S')}'
            return {'status': 'healthy', 'available': self.available, 'stats': self.get_stats()}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

def debug(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
    """Send debug notification"""
    if not self.config.debug_notifications:
        return False
    return self._send_notification(title, message, NotificationLevel.DEBUG, module, **kwargs)

def info(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
    """Send info notification"""
    return self._send_notification(title, message, NotificationLevel.INFO, module, **kwargs)

def success(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
    """Send success notification"""
    return self._send_notification(title, message, NotificationLevel.SUCCESS, module, **kwargs)

def warning(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
    """Send warning notification"""
    return self._send_notification(title, message, NotificationLevel.WARNING, module, **kwargs)

def error(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
    """Send error notification"""
    return self._send_notification(title, message, NotificationLevel.ERROR, module, **kwargs)

def critical(self, title: str, message: str, module: Optional[str]=None, **kwargs) -> bool:
    """Send critical notification"""
    return self._send_notification(title, message, NotificationLevel.CRITICAL, module, **kwargs)

