# Cluster 26

@pytest.mark.unittest
class TestEnvRender:

    def test_init(self):
        render = EnvRender()
        assert True

    def test_fill_all(self):
        border = Border(0, 0, 1000, 1000)
        render = EnvRender()
        food_balls = [BaseBall('0', border.sample(), border=border, score=100)]
        thorns_balls = [BaseBall('0', border.sample(), border=border, score=10000)]
        spore_balls = [BaseBall('0', border.sample(), border=border, score=1400)]
        players = [HumanPlayer(cfg=Server.default_config().manager_settings.player_manager.ball_settings, team_id=0, player_id=0, border=border, spore_settings=Server.default_config().manager_settings.spore_manager.ball_settings)]
        screen_data_all = render.get_screen(food_balls, thorns_balls, spore_balls, players, 1)
        assert len(screen_data_all.shape) == 3

def test_init(self):
    render = EnvRender()
    assert True

class Border:
    """
    Overview:
        used to specify a rectangular range
    """

    def __init__(self, minx, miny, maxx, maxy, random_generator=None):
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny
        if random_generator is not None:
            self._random = random_generator
        else:
            self._random = random.Random()

    def __repr__(self) -> str:
        return '[' + str(self.minx) + ',' + str(self.miny) + ',' + str(self.maxx) + ',' + str(self.maxy) + ']'

    def contains(self, position: Vector2) -> bool:
        """
        Overview:
            To judge whether a position in this border.
        Parameters:
            position <Vector2>: the position to be judged.
        Returns:
            bool: True or False, whether the position in this border.
        """
        return position.x > self.minx and position.x < self.maxx and (position.y > self.miny) and (position.y < self.maxy)

    def sample(self) -> Vector2:
        """
        Overview:
            Randomly sample a position in the border.
        Returns:
            Vector2: the sampled position.
        """
        x = self._random.uniform(self.minx, self.maxx)
        y = self._random.uniform(self.miny, self.maxy)
        return Vector2(x, y)

    def get_joint(self, border):
        new_minx = max(self.minx, border.minx)
        new_maxx = min(self.maxx, border.maxx)
        new_miny = max(self.miny, border.miny)
        new_maxy = min(self.maxy, border.maxy)
        if new_minx > new_maxx or new_miny > new_maxy:
            return None
        return Border(new_minx, new_maxx, new_miny, new_maxy, self._random)

def __repr__(self) -> str:
    return '[' + str(self.minx) + ',' + str(self.miny) + ',' + str(self.maxx) + ',' + str(self.maxy) + ']'

class TestSpeed:

    def test_get_speed_by_query_num(self, total_num=30, start_num=0, end_num=1, stride=0.5, changed_p=0.2, iter=1):
        speed_test = SpeedTest(total_num, border=Border(0, 0, 1000, 1000))
        exhaustive_time = []
        precision_time = []
        rebuild_time = []
        remove_time = []
        x_index = []
        for epoch in np.arange(start_num, end_num, stride):
            logging.debug('epoch ' + str(epoch) + ' begin')
            x_index.append(epoch)
            result = speed_test.cal_speed(int(total_num * epoch), int(total_num * changed_p), int(iter))
            exhaustive_time.append(result[0])
            precision_time.append(result[1])
            rebuild_time.append(result[2])
            remove_time.append(result[3])
        return (x_index, exhaustive_time, precision_time, rebuild_time, remove_time)

    def test_get_speed_by_change_num(self, total_num=30, start_num=0, end_num=1, stride=0.5, query_p=0.2, iter=1):
        speed_test = SpeedTest(total_num, border=Border(0, 0, 1000, 1000))
        exhaustive_time = []
        precision_time = []
        rebuild_time = []
        remove_time = []
        x_index = []
        for epoch in np.arange(start_num, end_num, stride):
            logging.debug('epoch ' + str(epoch) + ' begin')
            x_index.append(epoch)
            result = speed_test.cal_speed(int(total_num * query_p), int(total_num * epoch), int(iter))
            exhaustive_time.append(result[0])
            precision_time.append(result[1])
            rebuild_time.append(result[2])
            remove_time.append(result[3])
        return (x_index, exhaustive_time, precision_time, rebuild_time, remove_time)

    def test_get_speed_by_iter(self, total_num=30, start_num=1, end_num=51, stride=25, query_p=0.2, changed_p=0.2):
        speed_test = SpeedTest(total_num, border=Border(0, 0, 1000, 1000))
        exhaustive_time = []
        precision_time = []
        rebuild_time = []
        remove_time = []
        x_index = []
        for epoch in np.arange(start_num, end_num, stride):
            logging.debug('epoch ' + str(epoch) + ' begin')
            x_index.append(epoch)
            result = speed_test.cal_speed(int(total_num * query_p), int(total_num * changed_p), int(epoch))
            exhaustive_time.append(result[0])
            precision_time.append(result[1])
            rebuild_time.append(result[2])
            remove_time.append(result[3])
        return (x_index, exhaustive_time, precision_time, rebuild_time, remove_time)

def test_get_speed_by_query_num(self, total_num=30, start_num=0, end_num=1, stride=0.5, changed_p=0.2, iter=1):
    speed_test = SpeedTest(total_num, border=Border(0, 0, 1000, 1000))
    exhaustive_time = []
    precision_time = []
    rebuild_time = []
    remove_time = []
    x_index = []
    for epoch in np.arange(start_num, end_num, stride):
        logging.debug('epoch ' + str(epoch) + ' begin')
        x_index.append(epoch)
        result = speed_test.cal_speed(int(total_num * epoch), int(total_num * changed_p), int(iter))
        exhaustive_time.append(result[0])
        precision_time.append(result[1])
        rebuild_time.append(result[2])
        remove_time.append(result[3])
    return (x_index, exhaustive_time, precision_time, rebuild_time, remove_time)

def test_get_speed_by_change_num(self, total_num=30, start_num=0, end_num=1, stride=0.5, query_p=0.2, iter=1):
    speed_test = SpeedTest(total_num, border=Border(0, 0, 1000, 1000))
    exhaustive_time = []
    precision_time = []
    rebuild_time = []
    remove_time = []
    x_index = []
    for epoch in np.arange(start_num, end_num, stride):
        logging.debug('epoch ' + str(epoch) + ' begin')
        x_index.append(epoch)
        result = speed_test.cal_speed(int(total_num * query_p), int(total_num * epoch), int(iter))
        exhaustive_time.append(result[0])
        precision_time.append(result[1])
        rebuild_time.append(result[2])
        remove_time.append(result[3])
    return (x_index, exhaustive_time, precision_time, rebuild_time, remove_time)

def test_get_speed_by_iter(self, total_num=30, start_num=1, end_num=51, stride=25, query_p=0.2, changed_p=0.2):
    speed_test = SpeedTest(total_num, border=Border(0, 0, 1000, 1000))
    exhaustive_time = []
    precision_time = []
    rebuild_time = []
    remove_time = []
    x_index = []
    for epoch in np.arange(start_num, end_num, stride):
        logging.debug('epoch ' + str(epoch) + ' begin')
        x_index.append(epoch)
        result = speed_test.cal_speed(int(total_num * query_p), int(total_num * changed_p), int(epoch))
        exhaustive_time.append(result[0])
        precision_time.append(result[1])
        rebuild_time.append(result[2])
        remove_time.append(result[3])
    return (x_index, exhaustive_time, precision_time, rebuild_time, remove_time)

class ActionPB(BasePB):

    def __init__(self, playback_settings, **kwargs):
        self.playback_settings = playback_settings
        self.save_action = self.playback_settings.save_action
        self.save_dir = self.playback_settings.save_dir
        self.save_name_prefix = self.playback_settings.save_name_prefix
        if self.save_action:
            if not os.path.isdir(self.save_dir):
                try:
                    os.makedirs(self.save_dir)
                except:
                    pass
                logging.warning('save_dir={} must be an existed directory!'.format(self.save_dir))
            if not self.save_name_prefix:
                self.save_name_prefix = str(uuid.uuid1())
        self.playback_data = {}
        logging.warning('`by_action` is not available now, please use `by_video` or `by_frame`.')

    def need_save(self, *args, **kwargs):
        return self.save_action

    def save_step(self, actions, last_frame_count):
        self.playback_data[last_frame_count] = actions

    def save_final(self, cfg, seed):
        self.playback_data['cfg'] = cfg
        self.playback_data['seed'] = seed
        self.playback_path = os.path.join(self.save_dir, self.save_name_prefix + '.ac')
        compressed_data = lz4.frame.compress(pickle.dumps(self.playback_data))
        with open(self.playback_path, 'wb') as f:
            pickle.dump(compressed_data, f)
        logging.info('save ac at {}'.format(self.playback_path))

def __init__(self, playback_settings, **kwargs):
    self.playback_settings = playback_settings
    self.save_action = self.playback_settings.save_action
    self.save_dir = self.playback_settings.save_dir
    self.save_name_prefix = self.playback_settings.save_name_prefix
    if self.save_action:
        if not os.path.isdir(self.save_dir):
            try:
                os.makedirs(self.save_dir)
            except:
                pass
            logging.warning('save_dir={} must be an existed directory!'.format(self.save_dir))
        if not self.save_name_prefix:
            self.save_name_prefix = str(uuid.uuid1())
    self.playback_data = {}
    logging.warning('`by_action` is not available now, please use `by_video` or `by_frame`.')

class FramePB(BasePB):

    def __init__(self, playback_settings, **kwargs):
        self.playback_settings = playback_settings
        self.save_frame = self.playback_settings.save_frame
        self.save_all = self.playback_settings.save_all
        self.save_partial = self.playback_settings.save_partial
        self.save_dir = self.playback_settings.save_dir
        self.save_name_prefix = self.playback_settings.save_name_prefix
        if self.save_frame:
            if not os.path.isdir(self.save_dir):
                try:
                    os.makedirs(self.save_dir)
                except:
                    pass
                logging.warning('save_dir={} must be an existed directory!'.format(self.save_dir))
            if not self.save_name_prefix:
                self.save_name_prefix = str(uuid.uuid1())
        self.playback_data = {}

    def need_save(self, *args, **kwargs):
        return self.save_frame

    def save_step(self, diff_balls_remove, diff_balls_modify, leaderboard, last_frame_count, *args, **kwargs):
        self.playback_data[last_frame_count] = [diff_balls_modify, diff_balls_remove, leaderboard]

    def save_final(self, cfg, *args, **kwargs):
        if self.save_frame:
            self.playback_data['cfg'] = cfg
            self.playback_path = os.path.join(self.save_dir, self.save_name_prefix + '.pb')
            compressed_data = lz4.frame.compress(pickle.dumps(self.playback_data))
            with open(self.playback_path, 'wb') as f:
                pickle.dump(compressed_data, f)
            logging.info('save pb at {}'.format(self.playback_path))

def __init__(self, playback_settings, **kwargs):
    self.playback_settings = playback_settings
    self.save_frame = self.playback_settings.save_frame
    self.save_all = self.playback_settings.save_all
    self.save_partial = self.playback_settings.save_partial
    self.save_dir = self.playback_settings.save_dir
    self.save_name_prefix = self.playback_settings.save_name_prefix
    if self.save_frame:
        if not os.path.isdir(self.save_dir):
            try:
                os.makedirs(self.save_dir)
            except:
                pass
            logging.warning('save_dir={} must be an existed directory!'.format(self.save_dir))
        if not self.save_name_prefix:
            self.save_name_prefix = str(uuid.uuid1())
    self.playback_data = {}

class VideoPB(BasePB):

    def __init__(self, playback_settings, **kwargs):
        self.playback_settings = playback_settings
        self.fps = kwargs['fps']
        self.map_width = kwargs['map_width']
        self.map_height = kwargs['map_height']
        self.save_video = self.playback_settings.save_video
        self.save_fps = self.playback_settings.save_fps
        self.save_resolution = self.playback_settings.save_resolution
        self.save_all = self.playback_settings.save_all
        self.save_partial = self.playback_settings.save_partial
        self.save_dir = self.playback_settings.save_dir
        self.save_name_prefix = self.playback_settings.save_name_prefix
        if self.save_video:
            if not os.path.isdir(self.save_dir):
                try:
                    os.makedirs(self.save_dir)
                except:
                    pass
                logging.warning('save_dir={} must be an existed directory!'.format(self.save_dir))
            if not self.save_name_prefix:
                self.save_name_prefix = str(uuid.uuid1())
            self.save_fps = int(self.save_fps)
            self.save_resolution = int(self.save_resolution)
            self.save_freq = self.fps // self.save_fps
        self.render = EnvRender(game_screen_width=self.save_resolution, game_screen_height=self.save_resolution, map_width=self.map_width, map_height=self.map_width)
        self.screens_all = []
        self.screens_partial = []

    def get_clip_screen(self, screen_data, rectangle):
        rectangle_tmp = copy.deepcopy(rectangle)
        left_top_x, left_top_y, right_bottom_x, right_bottom_y = rectangle_tmp
        left_top_x_fix = max(left_top_x, 0)
        left_top_y_fix = max(left_top_y, 0)
        right_bottom_x_fix = min(right_bottom_x, self.width)
        right_bottom_y_fix = min(right_bottom_y, self.height)
        if len(screen_data.shape) == 3:
            screen_data_clip = screen_data[left_top_x_fix:right_bottom_x_fix, left_top_y_fix:right_bottom_y_fix, :]
            screen_data_clip = np.pad(screen_data_clip, ((left_top_x_fix - left_top_x, right_bottom_x - right_bottom_x_fix), (left_top_y_fix - left_top_y, right_bottom_y - right_bottom_y_fix), (0, 0)), mode='constant')
        elif len(screen_data.shape) == 2:
            screen_data_clip = screen_data[left_top_x_fix:right_bottom_x_fix, left_top_y_fix:right_bottom_y_fix]
            screen_data_clip = np.pad(screen_data_clip, ((left_top_x_fix - left_top_x, right_bottom_x - right_bottom_x_fix), (left_top_y_fix - left_top_y, right_bottom_y - right_bottom_y_fix)), mode='constant')
        else:
            raise NotImplementedError
        return screen_data_clip

    def need_save(self, last_frame_count, *args, **kwargs):
        return self.save_video and last_frame_count % self.save_freq == 0

    def save_step(self, food_balls, thorns_balls, spore_balls, players, player_num_per_team, *args, **kwargs):
        self.screens_all.append(self.render.get_screen(food_balls, thorns_balls, spore_balls, players, player_num_per_team))

    def save_final(self, *args, **kwargs):
        if self.save_video:
            if self.save_all:
                video_file_all = os.path.join(self.save_dir, '{}-all.mp4'.format(self.save_name_prefix))
                out = cv2.VideoWriter(video_file_all, cv2.VideoWriter_fourcc(*'mp4v'), self.save_fps, (self.screens_all[0].shape[1], self.screens_all[0].shape[0]))
                for index, screen in enumerate(self.screens_all):
                    out.write(screen)
                out.release()
                cv2.destroyAllWindows()
            if self.save_partial:
                for player_id, screens in self.screens_partial.items():
                    video_file_partial = os.path.join(self.save_dir, '{}-{:02d}.mp4'.format(self.save_name_prefix, player_id))
                    out = cv2.VideoWriter(video_file_partial, cv2.VideoWriter_fourcc(*'mp4v'), self.save_fps, (screens[0].shape[1], screens[0].shape[0]))
                    for index, screen in enumerate(self.screens):
                        if index % self.save_freq == 0:
                            out.write(screen)
                    out.release()
                    cv2.destroyAllWindows()

def __init__(self, playback_settings, **kwargs):
    self.playback_settings = playback_settings
    self.fps = kwargs['fps']
    self.map_width = kwargs['map_width']
    self.map_height = kwargs['map_height']
    self.save_video = self.playback_settings.save_video
    self.save_fps = self.playback_settings.save_fps
    self.save_resolution = self.playback_settings.save_resolution
    self.save_all = self.playback_settings.save_all
    self.save_partial = self.playback_settings.save_partial
    self.save_dir = self.playback_settings.save_dir
    self.save_name_prefix = self.playback_settings.save_name_prefix
    if self.save_video:
        if not os.path.isdir(self.save_dir):
            try:
                os.makedirs(self.save_dir)
            except:
                pass
            logging.warning('save_dir={} must be an existed directory!'.format(self.save_dir))
        if not self.save_name_prefix:
            self.save_name_prefix = str(uuid.uuid1())
        self.save_fps = int(self.save_fps)
        self.save_resolution = int(self.save_resolution)
        self.save_freq = self.fps // self.save_fps
    self.render = EnvRender(game_screen_width=self.save_resolution, game_screen_height=self.save_resolution, map_width=self.map_width, map_height=self.map_width)
    self.screens_all = []
    self.screens_partial = []

def build_activation(activation: str, inplace: bool=None) -> nn.Module:
    """
    Overview:
        Return the activation module according to the given type.
    Arguments:
        - actvation (:obj:`str`): the type of activation module, now supports ['relu', 'glu', 'prelu']
        - inplace (:obj:`bool`): can optionally do the operation in-place in relu. Default ``None``
    Returns:
        - act_func (:obj:`nn.module`): the corresponding activation module
    """
    if inplace is not None:
        assert activation == 'relu', 'inplace argument is not compatible with {}'.format(activation)
    else:
        inplace = True
    act_func = {'relu': nn.ReLU(inplace=inplace), 'glu': GLU, 'prelu': nn.PReLU(), 'swish': Swish()}
    if activation in act_func.keys():
        return act_func[activation]
    else:
        raise KeyError('invalid key for activation: {}'.format(activation))

def build_normalization(norm_type: str, dim: Optional[int]=None) -> nn.Module:
    """
    Overview:
        Build the corresponding normalization module
    Arguments:
        - norm_type (:obj:`str`): type of the normaliztion, now support ['BN', 'IN', 'SyncBN', 'AdaptiveIN']
        - dim (:obj:`int`): dimension of the normalization, when norm_type is in [BN, IN]
    Returns:
        - norm_func (:obj:`nn.Module`): the corresponding batch normalization function

    .. note::
        For beginers, you can refer to <https://zhuanlan.zhihu.com/p/34879333> to learn more about batch normalization.
    """
    if dim is None:
        key = norm_type
    elif norm_type in ['BN', 'IN', 'SyncBN']:
        key = norm_type + str(dim)
    elif norm_type in ['LN']:
        key = norm_type
    else:
        raise NotImplementedError('not support indicated dim when creates {}'.format(norm_type))
    norm_func = {'BN1': nn.BatchNorm1d, 'BN2': nn.BatchNorm2d, 'LN': nn.LayerNorm, 'IN2': nn.InstanceNorm2d}
    if key in norm_func.keys():
        return norm_func[key]
    else:
        raise KeyError('invalid norm type: {}'.format(key))

