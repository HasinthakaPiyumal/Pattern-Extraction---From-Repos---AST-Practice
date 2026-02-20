# Cluster 6

# Node: next
# Node: open
def save_list_to_file(some_data, file_name):
    with open(file_name, 'a') as myfile:
        for entry in some_data:
            myfile.write('%s\n' % str(entry))

# Node: write
def log_to_file(data, file_name, log_dir=None):
    if log_dir is None:
        log_dir = get_log_folder()
    full_path = os.path.join(log_dir, file_name)
    with open(full_path, 'a') as the_file:
        ts = get_now_seconds_utc()
        pid = os.getpid()
        the_file.write('{ts}: PID: {pid} {data}\n'.format(ts=ts, pid=pid, data=str(data)))

# Node: get_log_folder
# Node: getpid
def save_to_csv_file(file_name, fields_list, array_list):
    with open(file_name, 'w') as f:
        writer = csv.writer(f, delimiter=';', quotechar=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(fields_list)
        for entry in array_list:
            writer.writerow(list(entry))

# Node: writer
# Node: writerow
# Node: list
class IteratorFile(io.TextIOBase):
    """ given an iterator which yields strings,
    return a file like object for reading those strings

    credits: https://gist.github.com/jsheedy/ed81cdf18190183b3b7d
    discussion: https://stackoverflow.com/questions/8134602/psycopg2-insert-multiple-rows-with-one-query

    """

    def __init__(self, it):
        self._it = it
        self._f = io.StringIO()

    def read(self, length=sys.maxsize):
        try:
            while self._f.tell() < length:
                self._f.write(next(self._it) + '\n')
        except StopIteration as e:
            pass
        except Exception as e:
            print('uncaught exception: {}'.format(e))
        finally:
            self._f.seek(0)
            data = self._f.read(length)
            remainder = self._f.read()
            self._f.seek(0)
            self._f.truncate(0)
            self._f.write(remainder)
            return data

    def readline(self):
        return next(self._it)

def read(self, length=sys.maxsize):
    try:
        while self._f.tell() < length:
            self._f.write(next(self._it) + '\n')
    except StopIteration as e:
        pass
    except Exception as e:
        print('uncaught exception: {}'.format(e))
    finally:
        self._f.seek(0)
        data = self._f.read(length)
        remainder = self._f.read()
        self._f.seek(0)
        self._f.truncate(0)
        self._f.write(remainder)
        return data

# Node: tell
# Node: seek
# Node: read
# Node: truncate
def readline(self):
    return next(self._it)

class CommonSettings(BaseData):

    def __init__(self, logging_level_id=LOG_ALL_DEBUG, log_folder=LOGS_FOLDER, key_path=API_KEY_PATH, cache_host=CACHE_HOST, cache_port=CACHE_PORT, db_host=DB_HOST, db_port=DB_PORT, db_name=DB_NAME, exchanges_ids=None):
        self.logging_level_id = logging_level_id
        self.logging_level_name = get_debug_level_name_by_id(self.logging_level_id)
        self.log_folder = log_folder
        self.key_path = key_path
        self.cache_host = cache_host
        self.cache_port = cache_port
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        if not exchanges_ids:
            self.exchanges = EXCHANGE.values()
        else:
            self.exchanges = exchanges_ids

    @classmethod
    def from_cfg(cls, file_name):
        config = ConfigParser.RawConfigParser()
        config.read(file_name)
        log_level_name = config.get('logging', 'log_level')
        log_level_id = get_logging_level_id_by_name(log_level_name)
        exchanges_ids = parse_exchange_ids(config.get('common', 'exchanges'))
        return CommonSettings(log_level_id, config.get('logging', 'logs_folder'), config.get('keys', 'path_to_api_keys'), config.get('redis', 'redis_host'), config.get('redis', 'redis_port'), config.get('postgres', 'db_host'), config.get('postgres', 'db_port'), config.get('postgres', 'db_name'), exchanges_ids)

@classmethod
def from_cfg(cls, file_name):
    config = ConfigParser.RawConfigParser()
    config.read(file_name)
    log_level_name = config.get('logging', 'log_level')
    log_level_id = get_logging_level_id_by_name(log_level_name)
    exchanges_ids = parse_exchange_ids(config.get('common', 'exchanges'))
    return CommonSettings(log_level_id, config.get('logging', 'logs_folder'), config.get('keys', 'path_to_api_keys'), config.get('redis', 'redis_host'), config.get('redis', 'redis_port'), config.get('postgres', 'db_host'), config.get('postgres', 'db_port'), config.get('postgres', 'db_name'), exchanges_ids)

# Node: RawConfigParser
# Node: get_logging_level_id_by_name
# Node: parse_exchange_ids
# Node: CommonSettings
