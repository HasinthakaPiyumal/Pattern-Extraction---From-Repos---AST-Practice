# Cluster 12

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

def __init__(self, it):
    self._it = it
    self._f = io.StringIO()

# Node: StringIO
