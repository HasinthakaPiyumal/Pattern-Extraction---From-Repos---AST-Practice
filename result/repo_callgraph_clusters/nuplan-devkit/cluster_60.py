# Cluster 60

class MockAWSResponse(AioAWSResponse):
    """
    Mock AWS response to make aioboto work with moto.
    """

    def __init__(self, response: AWSResponse):
        """
        Wraps moto's mocked AWS response for use with aioboto.
        :param response: Mocked AWS response.
        """
        self._moto_response = response
        self.status_code = response.status_code
        self.raw = MockHttpClientResponse(response)

    async def _content_prop(self) -> bytes:
        """
        Return moto's response from handle used by aioboto.
        :return: Mocked response content.
        """
        response: bytes = self._moto_response.content
        return response

    async def _text_prop(self) -> str:
        """
        Return moto's response from handle used by aioboto.
        :return: Mocked response text.
        """
        response: str = self._moto_response.text
        return response

def __init__(self, response: AWSResponse):
    """
        Wraps moto's mocked AWS response for use with aioboto.
        :param response: Mocked AWS response.
        """
    self._moto_response = response
    self.status_code = response.status_code
    self.raw = MockHttpClientResponse(response)

