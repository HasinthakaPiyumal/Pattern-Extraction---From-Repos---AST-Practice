# Cluster 38

class TextLine(Geom):

    def __init__(self, text: str='', font_size: int=15, x: float=0.0, y: float=0.0):
        super().__init__()
        if pyglet.font.have_font('Courier'):
            font = 'Courier'
        elif pyglet.font.have_font('Secret Code'):
            font = 'Secret Code'
        else:
            font = None
        self.label = pyglet.text.Label(text, font_name=font, font_size=font_size, color=(0, 0, 0, 255), x=x, y=y, anchor_x='left', anchor_y='bottom')

    def render1(self):
        if self.label is not None:
            self.label.draw()

    def set_text(self, text, font_size: Optional[int]=None):
        self.label.text = text
        if font_size is not None:
            self.label.font_size = font_size

def render1(self):
    if self.label is not None:
        self.label.draw()

class Image(Geom):

    def __init__(self, img, x, y, scale):
        super().__init__()
        self.x = x
        self.y = y
        self.scale = scale
        img_shape = img.shape
        img = img.astype(np.uint8).reshape(-1)
        tex_data = (pyglet.gl.GLubyte * img.size)(*img)
        pyg_img = pyglet.image.ImageData(img_shape[1], img_shape[0], 'RGBA', tex_data, pitch=img_shape[1] * img_shape[2] * 1)
        self.img = pyg_img
        self.sprite = pyglet.sprite.Sprite(img=self.img, x=self.x, y=self.y, subpixel=True)
        self.sprite.update(scale=self.scale)

    def render1(self):
        self.sprite.draw()

def render1(self):
    self.sprite.draw()

