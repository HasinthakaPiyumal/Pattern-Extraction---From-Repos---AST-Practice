# Cluster 39

class KeyboardControl(object):
    """
    Keyboard control for the human agent
    """

    def __init__(self, path_to_conf_file):
        """
        Init
        """
        self._control = carla.VehicleControl()
        self._steer_cache = 0.0
        self._clock = pygame.time.Clock()
        if path_to_conf_file:
            with open(path_to_conf_file, 'r') as f:
                lines = f.read().split('\n')
                self._mode = lines[0].split(' ')[1]
                self._endpoint = lines[1].split(' ')[1]
            if self._mode == 'log':
                self._log_data = {'records': []}
            elif self._mode == 'playback':
                self._index = 0
                self._control_list = []
                with open(self._endpoint) as fd:
                    try:
                        self._records = json.load(fd)
                        self._json_to_control()
                    except json.JSONDecodeError:
                        pass
        else:
            self._mode = 'normal'
            self._endpoint = None

    def _json_to_control(self):
        for entry in self._records['records']:
            control = carla.VehicleControl(throttle=entry['control']['throttle'], steer=entry['control']['steer'], brake=entry['control']['brake'], hand_brake=entry['control']['hand_brake'], reverse=entry['control']['reverse'], manual_gear_shift=entry['control']['manual_gear_shift'], gear=entry['control']['gear'])
            self._control_list.append(control)

    def parse_events(self, timestamp):
        """
        Parse the keyboard events and set the vehicle controls accordingly
        """
        if self._mode == 'playback':
            self._parse_json_control()
        else:
            self._parse_vehicle_keys(pygame.key.get_pressed(), timestamp * 1000)
        if self._mode == 'log':
            self._record_control()
        return self._control

    def _parse_vehicle_keys(self, keys, milliseconds):
        """
        Calculate new vehicle controls based on input keys
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYUP:
                if event.key == K_q:
                    self._control.gear = 1 if self._control.reverse else -1
                    self._control.reverse = self._control.gear < 0
        if keys[K_UP] or keys[K_w]:
            self._control.throttle = 0.6
        else:
            self._control.throttle = 0.0
        steer_increment = 0.0003 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        steer_cache = min(0.95, max(-0.95, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]

    def _parse_json_control(self):
        if self._index < len(self._control_list):
            self._control = self._control_list[self._index]
            self._index += 1
        else:
            print('JSON file has no more entries')

    def _record_control(self):
        new_record = {'control': {'throttle': self._control.throttle, 'steer': self._control.steer, 'brake': self._control.brake, 'hand_brake': self._control.hand_brake, 'reverse': self._control.reverse, 'manual_gear_shift': self._control.manual_gear_shift, 'gear': self._control.gear}}
        self._log_data['records'].append(new_record)

    def __del__(self):
        if self._mode == 'log' and self._log_data:
            with open(self._endpoint, 'w') as fd:
                json.dump(self._log_data, fd, indent=4, sort_keys=True)

def parse_events(self, timestamp):
    """
        Parse the keyboard events and set the vehicle controls accordingly
        """
    if self._mode == 'playback':
        self._parse_json_control()
    else:
        self._parse_vehicle_keys(pygame.key.get_pressed(), timestamp * 1000)
    if self._mode == 'log':
        self._record_control()
    return self._control

class WorldSR(World):
    restarted = False

    def restart(self):
        if self.restarted:
            return
        self.restarted = True
        self.player_max_speed = 1.589
        self.player_max_speed_fast = 3.713
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        while self.player is None:
            print('Waiting for the ego vehicle...')
            time.sleep(1)
            possible_vehicles = self.world.get_actors().filter('vehicle.*')
            for vehicle in possible_vehicles:
                if vehicle.attributes['role_name'] == 'hero':
                    print('Ego vehicle found')
                    self.player = vehicle
                    break
        self.player_name = self.player.type_id
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.imu_sensor = IMUSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud, self._gamma)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)

    def tick(self, clock):
        if len(self.world.get_actors().filter(self.player_name)) < 1:
            return False
        self.hud.tick(self, clock)
        return True

def restart(self):
    if self.restarted:
        return
    self.restarted = True
    self.player_max_speed = 1.589
    self.player_max_speed_fast = 3.713
    cam_index = self.camera_manager.index if self.camera_manager is not None else 0
    cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
    while self.player is None:
        print('Waiting for the ego vehicle...')
        time.sleep(1)
        possible_vehicles = self.world.get_actors().filter('vehicle.*')
        for vehicle in possible_vehicles:
            if vehicle.attributes['role_name'] == 'hero':
                print('Ego vehicle found')
                self.player = vehicle
                break
    self.player_name = self.player.type_id
    self.collision_sensor = CollisionSensor(self.player, self.hud)
    self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
    self.gnss_sensor = GnssSensor(self.player)
    self.imu_sensor = IMUSensor(self.player)
    self.camera_manager = CameraManager(self.player, self.hud, self._gamma)
    self.camera_manager.transform_index = cam_pos_index
    self.camera_manager.set_sensor(cam_index, notify=False)
    actor_type = get_actor_display_name(self.player)
    self.hud.notification(actor_type)

class ModuleWorld(object):

    def __init__(self, name, args, timeout):
        self.client = None
        self.name = name
        self.args = args
        self.timeout = timeout
        self.server_fps = 0.0
        self.simulation_time = 0
        self.server_clock = pygame.time.Clock()
        self.world = None
        self.town_map = None
        self.actors_with_transforms = []
        self.module_hud = None
        self.module_input = None
        self.surface_size = [0, 0]
        self.prev_scaled_size = 0
        self.scaled_size = 0
        self.hero_actor = None
        self.spawned_hero = None
        self.hero_transform = None
        self.scale_offset = [0, 0]
        self.vehicle_id_surface = None
        self.result_surface = None
        self.traffic_light_surfaces = TrafficLightSurfaces()
        self.affected_traffic_light = None
        self.map_image = None
        self.border_round_surface = None
        self.original_surface_size = None
        self.hero_surface = None
        self.actors_surface = None

    def _get_data_from_carla(self):
        try:
            self.client = carla.Client(self.args.host, self.args.port)
            self.client.set_timeout(self.timeout)
            if self.args.map is None:
                world = self.client.get_world()
            else:
                world = self.client.load_world(self.args.map)
            town_map = world.get_map()
            return (world, town_map)
        except RuntimeError as ex:
            logging.error(ex)
            exit_game()

    def start(self):
        self.world, self.town_map = self._get_data_from_carla()
        self.map_image = MapImage(carla_world=self.world, carla_map=self.town_map, pixels_per_meter=PIXELS_PER_METER, show_triggers=self.args.show_triggers, show_connections=self.args.show_connections, show_spawn_points=self.args.show_spawn_points)
        self.module_hud = module_manager.get_module(MODULE_HUD)
        self.module_input = module_manager.get_module(MODULE_INPUT)
        self.original_surface_size = min(self.module_hud.dim[0], self.module_hud.dim[1])
        self.surface_size = self.map_image.big_map_surface.get_width()
        self.scaled_size = int(self.surface_size)
        self.prev_scaled_size = int(self.surface_size)
        self.actors_surface = pygame.Surface((self.map_image.surface.get_width(), self.map_image.surface.get_height()))
        self.actors_surface.set_colorkey(COLOR_BLACK)
        self.vehicle_id_surface = pygame.Surface((self.surface_size, self.surface_size)).convert()
        self.vehicle_id_surface.set_colorkey(COLOR_BLACK)
        self.border_round_surface = pygame.Surface(self.module_hud.dim, pygame.SRCALPHA).convert()
        self.border_round_surface.set_colorkey(COLOR_WHITE)
        self.border_round_surface.fill(COLOR_BLACK)
        center_offset = (int(self.module_hud.dim[0] / 2), int(self.module_hud.dim[1] / 2))
        pygame.draw.circle(self.border_round_surface, COLOR_ALUMINIUM_1, center_offset, int(self.module_hud.dim[1] / 2))
        pygame.draw.circle(self.border_round_surface, COLOR_WHITE, center_offset, int((self.module_hud.dim[1] - 8) / 2))
        scaled_original_size = self.original_surface_size * (1.0 / 0.9)
        self.hero_surface = pygame.Surface((scaled_original_size, scaled_original_size)).convert()
        self.result_surface = pygame.Surface((self.surface_size, self.surface_size)).convert()
        self.result_surface.set_colorkey(COLOR_BLACK)
        self.select_hero_actor()
        self.hero_actor.set_autopilot(False)
        self.module_input.wheel_offset = HERO_DEFAULT_SCALE
        self.module_input.control = carla.VehicleControl()
        weak_self = weakref.ref(self)
        self.world.on_tick(lambda timestamp: ModuleWorld.on_world_tick(weak_self, timestamp))

    def select_hero_actor(self):
        hero_vehicles = [actor for actor in self.world.get_actors() if 'vehicle' in actor.type_id and actor.attributes['role_name'] == 'hero']
        if len(hero_vehicles) > 0:
            self.hero_actor = random.choice(hero_vehicles)
            self.hero_transform = self.hero_actor.get_transform()
        else:
            self._spawn_hero()

    def _spawn_hero(self):
        blueprint = random.choice(self.world.get_blueprint_library().filter(self.args.filter))
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        while self.hero_actor is None:
            spawn_points = self.world.get_map().get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.hero_actor = self.world.try_spawn_actor(blueprint, spawn_point)
        self.hero_transform = self.hero_actor.get_transform()
        self.spawned_hero = self.hero_actor

    def tick(self, clock):
        actors = self.world.get_actors()
        self.actors_with_transforms = [(actor, actor.get_transform()) for actor in actors]
        if self.hero_actor is not None:
            self.hero_transform = self.hero_actor.get_transform()
        self.update_hud_info(clock)

    def update_hud_info(self, clock):
        hero_mode_text = []
        if self.hero_actor is not None:
            hero_speed = self.hero_actor.get_velocity()
            hero_speed_text = 3.6 * math.sqrt(hero_speed.x ** 2 + hero_speed.y ** 2 + hero_speed.z ** 2)
            affected_traffic_light_text = 'None'
            if self.affected_traffic_light is not None:
                state = self.affected_traffic_light.state
                if state == carla.TrafficLightState.Green:
                    affected_traffic_light_text = 'GREEN'
                elif state == carla.TrafficLightState.Yellow:
                    affected_traffic_light_text = 'YELLOW'
                else:
                    affected_traffic_light_text = 'RED'
            affected_speed_limit_text = self.hero_actor.get_speed_limit()
            hero_mode_text = ['Hero Mode:                 ON', 'Hero ID:              %7d' % self.hero_actor.id, 'Hero Vehicle:  %14s' % get_actor_display_name(self.hero_actor, truncate=14), 'Hero Speed:          %3d km/h' % hero_speed_text, 'Hero Affected by:', '  Traffic Light: %12s' % affected_traffic_light_text, '  Speed Limit:       %3d km/h' % affected_speed_limit_text]
        else:
            hero_mode_text = ['Hero Mode:                OFF']
        self.server_fps = self.server_clock.get_fps()
        self.server_fps = 'inf' if self.server_fps == float('inf') else round(self.server_fps)
        module_info_text = ['Server:  % 16s FPS' % self.server_fps, 'Client:  % 16s FPS' % round(clock.get_fps()), 'Simulation Time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)), 'Map Name:          %10s' % self.town_map.name]
        module_info_text = module_info_text
        module_hud = module_manager.get_module(MODULE_HUD)
        module_hud.add_info(self.name, module_info_text)
        module_hud.add_info('HERO', hero_mode_text)

    @staticmethod
    def on_world_tick(weak_self, timestamp):
        self = weak_self()
        if not self:
            return
        self.server_clock.tick()
        self.server_fps = self.server_clock.get_fps()
        self.simulation_time = timestamp.elapsed_seconds

    def _split_actors(self):
        vehicles = []
        traffic_lights = []
        speed_limits = []
        walkers = []
        for actor_with_transform in self.actors_with_transforms:
            actor = actor_with_transform[0]
            if 'vehicle' in actor.type_id:
                vehicles.append(actor_with_transform)
            elif 'traffic_light' in actor.type_id:
                traffic_lights.append(actor_with_transform)
            elif 'speed_limit' in actor.type_id:
                speed_limits.append(actor_with_transform)
            elif 'walker' in actor.type_id:
                walkers.append(actor_with_transform)
        info_text = []
        if self.hero_actor is not None and len(vehicles) > 1:
            location = self.hero_transform.location
            vehicle_list = [x[0] for x in vehicles if x[0].id != self.hero_actor.id]

            def distance(v):
                return location.distance(v.get_location())
            for n, vehicle in enumerate(sorted(vehicle_list, key=distance)):
                if n > 15:
                    break
                vehicle_type = get_actor_display_name(vehicle, truncate=22)
                info_text.append('% 5d %s' % (vehicle.id, vehicle_type))
        module_manager.get_module(MODULE_HUD).add_info('NEARBY VEHICLES', info_text)
        return (vehicles, traffic_lights, speed_limits, walkers)

    def _render_traffic_lights(self, surface, list_tl, world_to_pixel):
        self.affected_traffic_light = None
        for tl in list_tl:
            world_pos = tl.get_location()
            pos = world_to_pixel(world_pos)
            if self.args.show_triggers:
                corners = Util.get_bounding_box(tl)
                corners = [world_to_pixel(p) for p in corners]
                pygame.draw.lines(surface, COLOR_BUTTER_1, True, corners, 2)
            if self.hero_actor is not None:
                corners = Util.get_bounding_box(tl)
                corners = [world_to_pixel(p) for p in corners]
                tl_t = tl.get_transform()
                transformed_tv = tl_t.transform(tl.trigger_volume.location)
                hero_location = self.hero_actor.get_location()
                d = hero_location.distance(transformed_tv)
                s = Util.length(tl.trigger_volume.extent) + Util.length(self.hero_actor.bounding_box.extent)
                if d <= s:
                    self.affected_traffic_light = tl
                    srf = self.traffic_light_surfaces.surfaces['h']
                    surface.blit(srf, srf.get_rect(center=pos))
            srf = self.traffic_light_surfaces.surfaces[tl.state]
            surface.blit(srf, srf.get_rect(center=pos))

    def _render_speed_limits(self, surface, list_sl, world_to_pixel, world_to_pixel_width):
        font_size = world_to_pixel_width(2)
        radius = world_to_pixel_width(2)
        font = pygame.font.SysFont('Arial', font_size)
        for sl in list_sl:
            x, y = world_to_pixel(sl.get_location())
            white_circle_radius = int(radius * 0.75)
            pygame.draw.circle(surface, COLOR_SCARLET_RED_1, (x, y), radius)
            pygame.draw.circle(surface, COLOR_ALUMINIUM_0, (x, y), white_circle_radius)
            limit = sl.type_id.split('.')[2]
            font_surface = font.render(limit, True, COLOR_ALUMINIUM_5)
            if self.args.show_triggers:
                corners = Util.get_bounding_box(sl)
                corners = [world_to_pixel(p) for p in corners]
                pygame.draw.lines(surface, COLOR_PLUM_2, True, corners, 2)
            if self.hero_actor is not None:
                angle = -self.hero_transform.rotation.yaw - 90.0
                font_surface = pygame.transform.rotate(font_surface, angle)
                offset = font_surface.get_rect(center=(x, y))
                surface.blit(font_surface, offset)
            else:
                surface.blit(font_surface, (x - radius / 2, y - radius / 2))

    def _render_walkers(self, surface, list_w, world_to_pixel):
        for w in list_w:
            color = COLOR_PLUM_0
            bb = w[0].bounding_box.extent
            corners = [carla.Location(x=-bb.x, y=-bb.y), carla.Location(x=bb.x, y=-bb.y), carla.Location(x=bb.x, y=bb.y), carla.Location(x=-bb.x, y=bb.y)]
            w[1].transform(corners)
            corners = [world_to_pixel(p) for p in corners]
            pygame.draw.polygon(surface, color, corners)

    def _render_vehicles(self, surface, list_v, world_to_pixel):
        for v in list_v:
            color = COLOR_SKY_BLUE_0
            if int(v[0].attributes['number_of_wheels']) == 2:
                color = COLOR_CHOCOLATE_1
            if v[0].attributes['role_name'] == 'hero':
                color = COLOR_CHAMELEON_0
            bb = v[0].bounding_box.extent
            corners = [carla.Location(x=-bb.x, y=-bb.y), carla.Location(x=bb.x - 0.8, y=-bb.y), carla.Location(x=bb.x, y=0), carla.Location(x=bb.x - 0.8, y=bb.y), carla.Location(x=-bb.x, y=bb.y), carla.Location(x=-bb.x, y=-bb.y)]
            v[1].transform(corners)
            corners = [world_to_pixel(p) for p in corners]
            pygame.draw.lines(surface, color, False, corners, int(math.ceil(4.0 * self.map_image.scale)))

    def render_actors(self, surface, vehicles, traffic_lights, speed_limits, walkers):
        self._render_traffic_lights(surface, [tl[0] for tl in traffic_lights], self.map_image.world_to_pixel)
        self._render_speed_limits(surface, [sl[0] for sl in speed_limits], self.map_image.world_to_pixel, self.map_image.world_to_pixel_width)
        self._render_vehicles(surface, vehicles, self.map_image.world_to_pixel)
        self._render_walkers(surface, walkers, self.map_image.world_to_pixel)

    def clip_surfaces(self, clipping_rect):
        self.actors_surface.set_clip(clipping_rect)
        self.vehicle_id_surface.set_clip(clipping_rect)
        self.result_surface.set_clip(clipping_rect)

    def _compute_scale(self, scale_factor):
        m = self.module_input.mouse_pos
        px = (m[0] - self.scale_offset[0]) / float(self.prev_scaled_size)
        py = (m[1] - self.scale_offset[1]) / float(self.prev_scaled_size)
        diff_between_scales = (float(self.prev_scaled_size) * px - float(self.scaled_size) * px, float(self.prev_scaled_size) * py - float(self.scaled_size) * py)
        self.scale_offset = (self.scale_offset[0] + diff_between_scales[0], self.scale_offset[1] + diff_between_scales[1])
        self.prev_scaled_size = self.scaled_size
        self.map_image.scale_map(scale_factor)

    def render(self, display):
        if self.actors_with_transforms is None:
            return
        self.result_surface.fill(COLOR_BLACK)
        vehicles, traffic_lights, speed_limits, walkers = self._split_actors()
        scale_factor = self.module_input.wheel_offset
        self.scaled_size = int(self.map_image.width * scale_factor)
        if self.scaled_size != self.prev_scaled_size:
            self._compute_scale(scale_factor)
        self.actors_surface.fill(COLOR_BLACK)
        self.render_actors(self.actors_surface, vehicles, traffic_lights, speed_limits, walkers)
        self.module_hud.render_vehicles_ids(self.vehicle_id_surface, vehicles, self.map_image.world_to_pixel, self.hero_actor, self.hero_transform)
        surfaces = ((self.map_image.surface, (0, 0)), (self.actors_surface, (0, 0)), (self.vehicle_id_surface, (0, 0)))
        angle = 0.0 if self.hero_actor is None else self.hero_transform.rotation.yaw + 90.0
        self.traffic_light_surfaces.rotozoom(-angle, self.map_image.scale)
        center_offset = (0, 0)
        if self.hero_actor is not None:
            hero_location_screen = self.map_image.world_to_pixel(self.hero_transform.location)
            hero_front = self.hero_transform.get_forward_vector()
            translation_offset = (hero_location_screen[0] - self.hero_surface.get_width() / 2 + hero_front.x * PIXELS_AHEAD_VEHICLE, hero_location_screen[1] - self.hero_surface.get_height() / 2 + hero_front.y * PIXELS_AHEAD_VEHICLE)
            clipping_rect = pygame.Rect(translation_offset[0], translation_offset[1], self.hero_surface.get_width(), self.hero_surface.get_height())
            self.clip_surfaces(clipping_rect)
            Util.blits(self.result_surface, surfaces)
            self.border_round_surface.set_clip(clipping_rect)
            self.hero_surface.fill(COLOR_ALUMINIUM_4)
            self.hero_surface.blit(self.result_surface, (-translation_offset[0], -translation_offset[1]))
            rotated_result_surface = pygame.transform.rotozoom(self.hero_surface, angle, 0.9).convert()
            center = (display.get_width() / 2, display.get_height() / 2)
            rotation_pivot = rotated_result_surface.get_rect(center=center)
            display.blit(rotated_result_surface, rotation_pivot)
            display.blit(self.border_round_surface, (0, 0))
        else:
            translation_offset = (self.module_input.mouse_offset[0] * scale_factor + self.scale_offset[0], self.module_input.mouse_offset[1] * scale_factor + self.scale_offset[1])
            center_offset = (abs(display.get_width() - self.surface_size) / 2 * scale_factor, 0)
            clipping_rect = pygame.Rect(-translation_offset[0] - center_offset[0], -translation_offset[1], self.module_hud.dim[0], self.module_hud.dim[1])
            self.clip_surfaces(clipping_rect)
            Util.blits(self.result_surface, surfaces)
            display.blit(self.result_surface, (translation_offset[0] + center_offset[0], translation_offset[1]))

    def destroy(self):
        if self.spawned_hero is not None:
            self.spawned_hero.destroy()

def update_hud_info(self, clock):
    hero_mode_text = []
    if self.hero_actor is not None:
        hero_speed = self.hero_actor.get_velocity()
        hero_speed_text = 3.6 * math.sqrt(hero_speed.x ** 2 + hero_speed.y ** 2 + hero_speed.z ** 2)
        affected_traffic_light_text = 'None'
        if self.affected_traffic_light is not None:
            state = self.affected_traffic_light.state
            if state == carla.TrafficLightState.Green:
                affected_traffic_light_text = 'GREEN'
            elif state == carla.TrafficLightState.Yellow:
                affected_traffic_light_text = 'YELLOW'
            else:
                affected_traffic_light_text = 'RED'
        affected_speed_limit_text = self.hero_actor.get_speed_limit()
        hero_mode_text = ['Hero Mode:                 ON', 'Hero ID:              %7d' % self.hero_actor.id, 'Hero Vehicle:  %14s' % get_actor_display_name(self.hero_actor, truncate=14), 'Hero Speed:          %3d km/h' % hero_speed_text, 'Hero Affected by:', '  Traffic Light: %12s' % affected_traffic_light_text, '  Speed Limit:       %3d km/h' % affected_speed_limit_text]
    else:
        hero_mode_text = ['Hero Mode:                OFF']
    self.server_fps = self.server_clock.get_fps()
    self.server_fps = 'inf' if self.server_fps == float('inf') else round(self.server_fps)
    module_info_text = ['Server:  % 16s FPS' % self.server_fps, 'Client:  % 16s FPS' % round(clock.get_fps()), 'Simulation Time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)), 'Map Name:          %10s' % self.town_map.name]
    module_info_text = module_info_text
    module_hud = module_manager.get_module(MODULE_HUD)
    module_hud.add_info(self.name, module_info_text)
    module_hud.add_info('HERO', hero_mode_text)

@staticmethod
def on_world_tick(weak_self, timestamp):
    self = weak_self()
    if not self:
        return
    self.server_clock.tick()
    self.server_fps = self.server_clock.get_fps()
    self.simulation_time = timestamp.elapsed_seconds

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

def start(self):
    hud = module_manager.get_module(MODULE_HUD)
    hud.notification("Press 'H' or '?' for help.", seconds=4.0)

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

@staticmethod
def _is_quit_shortcut(key):
    return key == K_ESCAPE or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)

class Weather(object):
    """
    Class to simulate weather in CARLA according to the astronomic behavior of the sun

    The sun position (azimuth and altitude angles) is obtained by calculating its
    astronomic position for the CARLA reference position (x=0, y=0, z=0) using the ephem
    library.

    Args:
        carla_weather (carla.WeatherParameters): Initial weather settings.
        dtime (datetime): Initial date and time in UTC (required for animation only).
            Defaults to None.
        animation (bool): Flag to allow animating the sun position over time.
            Defaults to False.

    Attributes:
        carla_weather (carla.WeatherParameters): Weather parameters for CARLA.
        animation (bool): Flag to allow animating the sun position over time.
        _sun (ephem.Sun): The sun as astronomic entity.
        _observer_location (ephem.Observer): Holds the geographical position (lat/lon/altitude)
            for which the sun position is obtained.
        datetime (datetime): Date and time in UTC (required for animation only).
    """

    def __init__(self, carla_weather, dtime=None, animation=False):
        """
        Class constructor
        """
        self.carla_weather = carla_weather
        self.animation = animation
        self._sun = ephem.Sun()
        self._observer_location = ephem.Observer()
        geo_location = CarlaDataProvider.get_map().transform_to_geolocation(carla.Location(0, 0, 0))
        self._observer_location.lon = str(geo_location.longitude)
        self._observer_location.lat = str(geo_location.latitude)
        self.datetime = dtime
        if self.datetime:
            self._observer_location.date = self.datetime
        self.update()

    def update(self, delta_time=0):
        """
        If the weather animation is true, the new sun position is calculated w.r.t delta_time

        Nothing happens if animation or datetime are None.

        Args:
            delta_time (float): Time passed since self.datetime [seconds].
        """
        if not self.animation or not self.datetime:
            return
        self.datetime = self.datetime + datetime.timedelta(seconds=delta_time)
        self._observer_location.date = self.datetime
        self._sun.compute(self._observer_location)
        self.carla_weather.sun_altitude_angle = math.degrees(self._sun.alt)
        self.carla_weather.sun_azimuth_angle = math.degrees(self._sun.az)

def update(self, delta_time=0):
    """
        If the weather animation is true, the new sun position is calculated w.r.t delta_time

        Nothing happens if animation or datetime are None.

        Args:
            delta_time (float): Time passed since self.datetime [seconds].
        """
    if not self.animation or not self.datetime:
        return
    self.datetime = self.datetime + datetime.timedelta(seconds=delta_time)
    self._observer_location.date = self.datetime
    self._sun.compute(self._observer_location)
    self.carla_weather.sun_altitude_angle = math.degrees(self._sun.alt)
    self.carla_weather.sun_azimuth_angle = math.degrees(self._sun.az)

class ChangeAutoPilot(AtomicBehavior):
    """
    This class contains an atomic behavior to disable/enable the use of the autopilot.

    Important parameters:
    - actor: CARLA actor to execute the behavior
    - activate: True (=enable autopilot) or False (=disable autopilot)
    - lane_change: Traffic Manager parameter. True (=enable lane changes) or False (=disable lane changes)
    - distance_between_vehicles: Traffic Manager parameter
    - max_speed: Traffic Manager parameter. Max speed of the actor. This will only work for road segments
                 with the same speed limit as the first one

    The behavior terminates after changing the autopilot state
    """

    def __init__(self, actor, activate, parameters=None, name='ChangeAutoPilot'):
        """
        Setup parameters
        """
        super(ChangeAutoPilot, self).__init__(name, actor)
        self.logger.debug('%s.__init__()' % self.__class__.__name__)
        self._activate = activate
        self._tm = CarlaDataProvider.get_client().get_trafficmanager(CarlaDataProvider.get_traffic_manager_port())
        self._parameters = parameters

    def update(self):
        """
        De/activate autopilot
        """
        self._actor.set_autopilot(self._activate)
        if self._parameters is not None:
            if 'auto_lane_change' in self._parameters:
                lane_change = self._parameters['auto_lane_change']
                self._tm.auto_lane_change(self._actor, lane_change)
            if 'max_speed' in self._parameters:
                max_speed = self._parameters['max_speed']
                max_road_speed = self._actor.get_speed_limit()
                if max_road_speed is not None:
                    percentage = (max_road_speed - max_speed) / max_road_speed * 100.0
                    self._tm.vehicle_percentage_speed_difference(self._actor, percentage)
                else:
                    print("ChangeAutopilot: Unable to find the vehicle's speed limit")
            if 'distance_between_vehicles' in self._parameters:
                dist_vehicles = self._parameters['distance_between_vehicles']
                self._tm.distance_to_leading_vehicle(self._actor, dist_vehicles)
            if 'force_lane_change' in self._parameters:
                force_lane_change = self._parameters['force_lane_change']
                self._tm.force_lane_change(self._actor, force_lane_change)
            if 'ignore_vehicles_percentage' in self._parameters:
                ignore_vehicles = self._parameters['ignore_vehicles_percentage']
                self._tm.ignore_vehicles_percentage(self._actor, ignore_vehicles)
        new_status = py_trees.common.Status.SUCCESS
        self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
        return new_status

def update(self):
    """
        De/activate autopilot
        """
    self._actor.set_autopilot(self._activate)
    if self._parameters is not None:
        if 'auto_lane_change' in self._parameters:
            lane_change = self._parameters['auto_lane_change']
            self._tm.auto_lane_change(self._actor, lane_change)
        if 'max_speed' in self._parameters:
            max_speed = self._parameters['max_speed']
            max_road_speed = self._actor.get_speed_limit()
            if max_road_speed is not None:
                percentage = (max_road_speed - max_speed) / max_road_speed * 100.0
                self._tm.vehicle_percentage_speed_difference(self._actor, percentage)
            else:
                print("ChangeAutopilot: Unable to find the vehicle's speed limit")
        if 'distance_between_vehicles' in self._parameters:
            dist_vehicles = self._parameters['distance_between_vehicles']
            self._tm.distance_to_leading_vehicle(self._actor, dist_vehicles)
        if 'force_lane_change' in self._parameters:
            force_lane_change = self._parameters['force_lane_change']
            self._tm.force_lane_change(self._actor, force_lane_change)
        if 'ignore_vehicles_percentage' in self._parameters:
            ignore_vehicles = self._parameters['ignore_vehicles_percentage']
            self._tm.ignore_vehicles_percentage(self._actor, ignore_vehicles)
    new_status = py_trees.common.Status.SUCCESS
    self.logger.debug('%s.update()[%s->%s]' % (self.__class__.__name__, self.status, new_status))
    return new_status

class KeyboardControl(object):
    """
    Keyboard control for the human agent
    """

    def __init__(self):
        """
        Init
        """
        self._control = carla.VehicleControl()
        self._steer_cache = 0.0

    def parse_events(self, control, clock):
        """
        Parse the keyboard events and set the vehicle controls accordingly
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
            control.steer = self._control.steer
            control.throttle = self._control.throttle
            control.brake = self._control.brake
            control.hand_brake = self._control.hand_brake

    def _parse_vehicle_keys(self, keys, milliseconds):
        """
        Calculate new vehicle controls based on input keys
        """
        self._control.throttle = 0.6 if keys[K_UP] or keys[K_w] else 0.0
        steer_increment = 15.0 * 0.0005 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.95, max(-0.95, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]

def parse_events(self, control, clock):
    """
        Parse the keyboard events and set the vehicle controls accordingly
        """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return
        self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
        control.steer = self._control.steer
        control.throttle = self._control.throttle
        control.brake = self._control.brake
        control.hand_brake = self._control.hand_brake

