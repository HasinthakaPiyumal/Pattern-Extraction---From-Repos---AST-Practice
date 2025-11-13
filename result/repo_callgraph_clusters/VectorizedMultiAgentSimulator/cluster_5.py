# Cluster 5

class LineStyle(Attr):

    def __init__(self, style):
        self.style = style

    def enable(self):
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(1, self.style)

    def disable(self):
        glDisable(GL_LINE_STIPPLE)

def disable(self):
    glDisable(GL_LINE_STIPPLE)

