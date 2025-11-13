# Cluster 15

def StopThread(thread):
    try:
        thread_id = GetThreadID(thread)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
        if res == 0:
            logger.error(f'Invalid thread ID')
        elif res > 1:
            logger.critical(f'PyThreadState_SetAsyncExc FAILED.')
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), None)
    except Exception as e:
        pass
    return

