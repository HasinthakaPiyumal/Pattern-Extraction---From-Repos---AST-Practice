# Cluster 19

class BaseRender:

    def __init__(self, game_screen_width, game_screen_height, info_width=0, info_height=0, with_show=False):
        pygame.init()
        if platform.system() == 'Linux':
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
        self.game_screen_width = game_screen_width
        self.game_screen_height = game_screen_height
        self.total_screen_width = game_screen_width + info_width
        self.total_screen_height = game_screen_height + info_height
        if with_show:
            self.screen = pygame.display.set_mode((self.total_screen_width, self.total_screen_height), 0, 32)
            pygame.display.set_caption('GoBigger - OpenDILab Environment')

    def fill(self, server):
        raise NotImplementedError

    def show(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

def __init__(self, game_screen_width, game_screen_height, info_width=0, info_height=0, with_show=False):
    pygame.init()
    if platform.system() == 'Linux':
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
    self.game_screen_width = game_screen_width
    self.game_screen_height = game_screen_height
    self.total_screen_width = game_screen_width + info_width
    self.total_screen_height = game_screen_height + info_height
    if with_show:
        self.screen = pygame.display.set_mode((self.total_screen_width, self.total_screen_height), 0, 32)
        pygame.display.set_caption('GoBigger - OpenDILab Environment')

