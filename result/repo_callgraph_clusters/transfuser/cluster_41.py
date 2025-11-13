# Cluster 41

class ModuleHUD(object):

    def __init__(self, name, width, height):
        self.name = name
        self.dim = (width, height)
        self._init_hud_params()
        self._init_data_params()

    def start(self):
        pass

    def _init_hud_params(self):
        fonts = [x for x in pygame.font.get_fonts() if 'mono' in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 14)
        self._header_font = pygame.font.SysFont('Arial', 14, True)
        self.help = HelpText(pygame.font.Font(mono, 24), *self.dim)
        self._notifications = FadingText(pygame.font.Font(pygame.font.get_default_font(), 20), (self.dim[0], 40), (0, self.dim[1] - 40))

    def _init_data_params(self):
        self.show_info = True
        self.show_actor_ids = False
        self._info_text = {}

    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    def tick(self, clock):
        self._notifications.tick(clock)

    def add_info(self, module_name, info):
        self._info_text[module_name] = info

    def render_vehicles_ids(self, vehicle_id_surface, list_actors, world_to_pixel, hero_actor, hero_transform):
        vehicle_id_surface.fill(COLOR_BLACK)
        if self.show_actor_ids:
            vehicle_id_surface.set_alpha(150)
            for actor in list_actors:
                x, y = world_to_pixel(actor[1].location)
                angle = 0
                if hero_actor is not None:
                    angle = -hero_transform.rotation.yaw - 90
                color = COLOR_SKY_BLUE_0
                if int(actor[0].attributes['number_of_wheels']) == 2:
                    color = COLOR_CHOCOLATE_0
                if actor[0].attributes['role_name'] == 'hero':
                    color = COLOR_CHAMELEON_0
                font_surface = self._header_font.render(str(actor[0].id), True, color)
                rotated_font_surface = pygame.transform.rotate(font_surface, angle)
                rect = rotated_font_surface.get_rect(center=(x, y))
                vehicle_id_surface.blit(rotated_font_surface, rect)
        return vehicle_id_surface

    def render(self, display):
        if self.show_info:
            info_surface = pygame.Surface((240, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            i = 0
            for module_name, module_info in self._info_text.items():
                if not module_info:
                    continue
                surface = self._header_font.render(module_name, True, COLOR_ALUMINIUM_0).convert_alpha()
                display.blit(surface, (8 + bar_width / 2, 18 * i + v_offset))
                v_offset += 12
                i += 1
                for item in module_info:
                    if v_offset + 18 > self.dim[1]:
                        break
                    if isinstance(item, list):
                        if len(item) > 1:
                            points = [(x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                            pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                        item = None
                    elif isinstance(item, tuple):
                        if isinstance(item[1], bool):
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                            pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect, 0 if item[1] else 1)
                        else:
                            rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                            pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect_border, 1)
                            f = (item[1] - item[2]) / (item[3] - item[2])
                            if item[2] < 0.0:
                                rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                            else:
                                rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                            pygame.draw.rect(display, COLOR_ALUMINIUM_0, rect)
                        item = item[0]
                    if item:
                        surface = self._font_mono.render(item, True, COLOR_ALUMINIUM_0).convert_alpha()
                        display.blit(surface, (8, 18 * i + v_offset))
                    v_offset += 18
                v_offset += 24
        self._notifications.render(display)
        self.help.render(display)

def __init__(self, name, width, height):
    self.name = name
    self.dim = (width, height)
    self._init_hud_params()
    self._init_data_params()

