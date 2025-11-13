# Cluster 3

class OutputCapture:
    """Capture all output to both console and file"""

    def __init__(self, filename):
        self.filename = filename
        self.file = None
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def start(self):
        """Start capturing output"""
        try:
            self.file = open(self.filename, 'w', encoding='utf-8-sig')
            sys.stdout = self
            sys.stderr = self
            return True
        except Exception as e:
            print(f'❌ Error opening output file {self.filename}: {e}')
            return False

    def stop(self):
        """Stop capturing output"""
        if self.file:
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            self.file.close()
            print(f'📄 Output saved to: {self.filename}')

    def write(self, text):
        """Write to both console and file"""
        self.original_stdout.write(text)
        if self.file:
            self.file.write(text)
            self.file.flush()

    def flush(self):
        """Flush both outputs"""
        self.original_stdout.flush()
        if self.file:
            self.file.flush()

def write(self, text):
    """Write to both console and file"""
    self.original_stdout.write(text)
    if self.file:
        self.file.write(text)
        self.file.flush()

def flush(self):
    """Flush both outputs"""
    self.original_stdout.flush()
    if self.file:
        self.file.flush()

