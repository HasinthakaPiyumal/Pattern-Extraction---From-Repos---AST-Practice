# Cluster 14

class WorkingDirectory(contextlib.ContextDecorator):

    def __init__(self, new_dir):
        self.dir = new_dir
        self.cwd = Path.cwd().resolve()

    def __enter__(self):
        os.chdir(self.dir)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.cwd)

def __enter__(self):
    os.chdir(self.dir)

def __exit__(self, exc_type, exc_val, exc_tb):
    os.chdir(self.cwd)

