# Cluster 6

class Item:

    def __init__(self, icon, offset, row, column):
        self.icon = icon
        self.offset = offset
        self.row = row
        self.column = column
        self.uid = str(uuid.uuid4())
        self.x = column * 100 + offset
        self.y = row * 100 + offset
        self.grid_x = self.x % 25
        self.grid_y = self.y % 25
        self.accessible = 1
        self.visible = 1

    def __repr__(self) -> str:
        return 'icon({})'.format(self.icon)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=2)

def to_json(self):
    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=2)

