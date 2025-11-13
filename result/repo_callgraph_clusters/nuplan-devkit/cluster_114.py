# Cluster 114

class PathKeywordMatch(logging.Filter):
    """
    This implements simple logging.Filter, by running a regexp match on the path of the log record path name.
    """

    def __init__(self, regexp: str=''):
        """
        :param regexp: Regexp used for filtering.
        """
        self.regexp = regexp
        super().__init__()

    def filter(self, log_record: logging.LogRecord) -> bool:
        """
        Determine if the specified record is to be logged.
        :param log_record: Logging.LogRecord, the record to emit.
        :return: Is the specified record to be logged? False for no, True for yes.
        """
        return re.match(self.regexp, log_record.pathname) is not None

def filter(self, log_record: logging.LogRecord) -> bool:
    """
        Determine if the specified record is to be logged.
        :param log_record: Logging.LogRecord, the record to emit.
        :return: Is the specified record to be logged? False for no, True for yes.
        """
    return re.match(self.regexp, log_record.pathname) is not None

