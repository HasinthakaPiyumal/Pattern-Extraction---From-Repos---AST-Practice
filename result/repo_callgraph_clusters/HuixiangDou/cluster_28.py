# Cluster 28

class ErrorCode(Enum):
    """Define an enumerated type for error codes, each has a numeric value and
    a description.

    Each enum member is associated with a numeric code and a description
    string. The numeric code is used as the return code in function calls, and
    the description provides a human-readable explanation of the error.
    """
    SUCCESS = (0, 'success')
    NOT_A_QUESTION = (1, 'query is not a question')
    NO_TOPIC = (2, 'The question does not have a topic. It might be a meaningless sentence.')
    UNRELATED = (3, 'Topics unrelated to the knowledge base. Updating good_questions and bad_questions can improve accuracy.')
    NO_SEARCH_KEYWORDS = (4, 'Cannot extract keywords.')
    NO_SEARCH_RESULT = (5, 'No search result.')
    BAD_ANSWER = (6, 'Irrelevant answer.')
    SECURITY = (7, 'Reply has a high relevance to prohibited topics.')
    NOT_WORK_TIME = (8, 'Non-working hours. The config.ini file can be modified to adjust this. **In scenarios where speech may pose risks, let the robot operate under human supervision**')
    PARAMETER_ERROR = (9, "HTTP interface parameter error. Query cannot be empty; the format of history is list of lists, like [['question1', 'reply1'], ['question2'], ['reply2']]")
    PARAMETER_MISS = (10, 'Missing key in http json input parameters.')
    WORK_IN_PROGRESS = (11, 'Not finish')
    FAILED = (12, 'Fail')
    BAD_PARAMETER = (13, 'Bad parameter')
    INTERNAL_ERROR = (14, 'Internal error')
    WEB_SEARCH_FAIL = (15, 'Web search fail, please check network, TOKEN and quota')
    SG_SEARCH_FAIL = (16, 'SourceGraph not result, please check token or input query')
    LLM_NOT_RESPONSE_SG = (17, 'LLM not response query with sg search')
    QUESTION_TOO_SHORT = (18, 'Query length too short')
    INIT = (19, 'Init state')

    def __new__(cls, value, description):
        """Create new instance of ErrorCode."""
        obj = object.__new__(cls)
        obj._value_ = value
        obj.description = description
        return obj

    def __int__(self):
        """Return the integer representation of the error code."""
        return self.value

    def __str__(self):
        """Return the str representation of the error code."""
        return self.description

    def describe(self):
        """Return the description of the error code."""
        return self.description

    @classmethod
    def format(cls, code):
        """Format the error code into a JSON result.

        Args:
            code (ErrorCode): Error code to be formatted.

        Returns:
            dict: A dictionary that includes the error code and its description.  # noqa E501

        Raises:
            TypeError: If the input is not an instance of ErrorCode.
        """
        if isinstance(code, cls):
            return {'code': int(code), 'message': code.describe()}
        raise TypeError(f'Expected type {cls}, got {type(code)}')

def __new__(cls, value, description):
    """Create new instance of ErrorCode."""
    obj = object.__new__(cls)
    obj._value_ = value
    obj.description = description
    return obj

