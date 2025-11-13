# Cluster 0

class ModuleInput(object):

    def __init__(self, name):
        self.name = name
        self.mouse_pos = (0, 0)
        self.mouse_offset = [0.0, 0.0]
        self.wheel_offset = 0.1
        self.wheel_amount = 0.025
        self._steer_cache = 0.0
        self.control = None
        self._autopilot_enabled = False

    def start(self):
        hud = module_manager.get_module(MODULE_HUD)
        hud.notification("Press 'H' or '?' for help.", seconds=4.0)

    def render(self, display):
        pass

    def tick(self, clock):
        self.parse_input(clock)

    def _parse_events(self):
        self.mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    exit_game()
                elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                    module_hud = module_manager.get_module(MODULE_HUD)
                    module_hud.help.toggle()
                elif event.key == K_TAB:
                    module_world = module_manager.get_module(MODULE_WORLD)
                    module_hud = module_manager.get_module(MODULE_HUD)
                    if module_world.hero_actor is None:
                        module_world.select_hero_actor()
                        self.wheel_offset = HERO_DEFAULT_SCALE
                        self.control = carla.VehicleControl()
                        module_hud.notification('Hero Mode')
                    else:
                        self.wheel_offset = MAP_DEFAULT_SCALE
                        self.mouse_offset = [0, 0]
                        self.mouse_pos = [0, 0]
                        module_world.scale_offset = [0, 0]
                        module_world.hero_actor = None
                        module_hud.notification('Map Mode')
                elif event.key == K_F1:
                    module_hud = module_manager.get_module(MODULE_HUD)
                    module_hud.show_info = not module_hud.show_info
                elif event.key == K_i:
                    module_hud = module_manager.get_module(MODULE_HUD)
                    module_hud.show_actor_ids = not module_hud.show_actor_ids
                elif isinstance(self.control, carla.VehicleControl):
                    if event.key == K_q:
                        self.control.gear = 1 if self.control.reverse else -1
                    elif event.key == K_m:
                        self.control.manual_gear_shift = not self.control.manual_gear_shift
                        world = module_manager.get_module(MODULE_WORLD)
                        self.control.gear = world.hero_actor.get_control().gear
                        module_hud = module_manager.get_module(MODULE_HUD)
                        module_hud.notification('%s Transmission' % ('Manual' if self.control.manual_gear_shift else 'Automatic'))
                    elif self.control.manual_gear_shift and event.key == K_COMMA:
                        self.control.gear = max(-1, self.control.gear - 1)
                    elif self.control.manual_gear_shift and event.key == K_PERIOD:
                        self.control.gear = self.control.gear + 1
                    elif event.key == K_p:
                        world = module_manager.get_module(MODULE_WORLD)
                        if world.hero_actor is not None:
                            self._autopilot_enabled = not self._autopilot_enabled
                            world.hero_actor.set_autopilot(self._autopilot_enabled)
                            module_hud = module_manager.get_module(MODULE_HUD)
                            module_hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self.wheel_offset += self.wheel_amount
                    if self.wheel_offset >= 1.0:
                        self.wheel_offset = 1.0
                elif event.button == 5:
                    self.wheel_offset -= self.wheel_amount
                    if self.wheel_offset <= 0.1:
                        self.wheel_offset = 0.1

    def _parse_keys(self, milliseconds):
        keys = pygame.key.get_pressed()
        self.control.throttle = 1.0 if keys[K_UP] or keys[K_w] else 0.0
        steer_increment = 0.0005 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self.control.steer = round(self._steer_cache, 1)
        self.control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self.control.hand_brake = keys[K_SPACE]

    def _parse_mouse(self):
        if pygame.mouse.get_pressed()[0]:
            x, y = pygame.mouse.get_pos()
            self.mouse_offset[0] += 1.0 / self.wheel_offset * (x - self.mouse_pos[0])
            self.mouse_offset[1] += 1.0 / self.wheel_offset * (y - self.mouse_pos[1])
            self.mouse_pos = (x, y)

    def parse_input(self, clock):
        self._parse_events()
        self._parse_mouse()
        if not self._autopilot_enabled:
            if isinstance(self.control, carla.VehicleControl):
                self._parse_keys(clock.get_time())
                self.control.reverse = self.control.gear < 0
            world = module_manager.get_module(MODULE_WORLD)
            if world.hero_actor is not None:
                world.hero_actor.apply_control(self.control)

    @staticmethod
    def _is_quit_shortcut(key):
        return key == K_ESCAPE or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)

def tick(self, clock):
    self.parse_input(clock)

