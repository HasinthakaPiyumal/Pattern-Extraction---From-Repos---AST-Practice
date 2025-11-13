# Cluster 153

def safe_monitor_performance(func):
    """Safe performance monitor that never fails"""
    try:
        from fincept_terminal.utils.Logging.logger import monitor_performance
        return monitor_performance(func)
    except:
        return func

def monitor_performance(func):
    return logger.monitor_performance(func)

