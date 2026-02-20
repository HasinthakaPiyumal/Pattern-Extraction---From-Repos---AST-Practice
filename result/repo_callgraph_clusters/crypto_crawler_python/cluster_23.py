# Cluster 23

class ProcessDetails(object):

    def __init__(self, cmd, pid):
        self.cmd = cmd
        self.pid = pid
        self.pair_id = self._parse_cmd(self.cmd)

    def get_pair_id(self):
        return self.pair_id

    def _parse_cmd(self, cmd):
        return ''

def __init__(self, cmd, pid):
    self.cmd = cmd
    self.pid = pid
    self.pair_id = self._parse_cmd(self.cmd)

# Node: _parse_cmd
