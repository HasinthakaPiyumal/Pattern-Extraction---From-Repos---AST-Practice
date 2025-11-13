# Cluster 79

class AsyncTestCase(asynctest.TestCase):
    use_default_loop = False
    forbid_get_event_loop = True
    TEST_TIMEOUT = int(os.getenv('ASYNCIO_TEST_TIMEOUT', '30'))

    def _run_test_method(self, method):
        result = method()
        if asyncio.iscoroutine(result):
            self.loop.run_until_complete(asyncio.wait_for(result, timeout=self.TEST_TIMEOUT))

def _run_test_method(self, method):
    result = method()
    if asyncio.iscoroutine(result):
        self.loop.run_until_complete(asyncio.wait_for(result, timeout=self.TEST_TIMEOUT))

