# Cluster 28

class Logger(object):
    DEFAULT = None
    CURRENT = None

    def __init__(self, dir, output_formats, precision=None):
        self.name2val = OrderedDict()
        self.level = INFO
        self.dir = dir
        self.output_formats = output_formats
        self.precision = precision

    def logkv(self, key, val):
        if self.precision is not None and isinstance(val, float):
            self.name2val[key] = round(val, self.precision)
        else:
            self.name2val[key] = val

    def add_figure(self, *args):
        for fmt in self.output_formats:
            if isinstance(fmt, TensorBoardOutputFormat):
                fmt.add_figure(*args)

    def set_tb_step(self, step):
        for fmt in self.output_formats:
            if isinstance(fmt, TensorBoardOutputFormat):
                fmt.set_step(step)

    def dumpkvs(self):
        if self.level == DISABLED:
            return
        for fmt in self.output_formats:
            if isinstance(fmt, KVWriter):
                fmt.writekvs(self.name2val)
        self.name2val.clear()

    def log(self, *args, level=INFO):
        if self.level <= level:
            self._do_log(args)

    def set_level(self, level):
        self.level = level

    def get_dir(self):
        return self.dir

    def close(self):
        for fmt in self.output_formats:
            fmt.close()

    def _do_log(self, args):
        for fmt in self.output_formats:
            if isinstance(fmt, SeqWriter):
                fmt.writeseq(map(str, args))

def log(self, *args, level=INFO):
    if self.level <= level:
        self._do_log(args)

