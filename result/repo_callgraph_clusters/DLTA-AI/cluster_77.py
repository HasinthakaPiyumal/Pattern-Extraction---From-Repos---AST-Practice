# Cluster 77

class CallerClassForTest:

    def __init__(self):
        self.caller_name = callee_func()

def __init__(self):
    self.caller_name = callee_func()

def test_get_caller_name():
    caller_name = callee_func()
    assert caller_name == 'test_get_caller_name'
    caller_class = CallerClassForTest()
    assert caller_class.caller_name == 'CallerClassForTest.__init__'

