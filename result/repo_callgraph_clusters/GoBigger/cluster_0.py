# Cluster 0

class BotAgent(BaseAgent):
    """
    Overview:
        A simple script bot
    """

    def __init__(self, name=None, level=3):
        self.name = name
        self.actions_queue = queue.Queue()
        self.last_clone_num = 1
        self.level = level

    def step(self, obs):
        if self.level == 1:
            return self.step_level_1(obs)
        if self.level == 2:
            return self.step_level_2(obs)
        if self.level == 3:
            return self.step_level_3(obs)

    def step_level_1(self, obs):
        if self.actions_queue.qsize() > 0:
            return self.actions_queue.get()
        overlap = obs['overlap']
        overlap = self.preprocess(overlap)
        food_balls = overlap['food']
        thorns_balls = overlap['thorns']
        spore_balls = overlap['spore']
        clone_balls = overlap['clone']
        my_clone_balls, others_clone_balls = self.process_clone_balls(clone_balls)
        min_distance, min_food_ball = self.process_food_balls(food_balls, my_clone_balls[0])
        if min_food_ball is not None:
            direction = (min_food_ball['position'] - my_clone_balls[0]['position']).normalize()
        else:
            direction = (Vector2(0, 0) - my_clone_balls[0]['position']).normalize()
        action_type = 0
        self.actions_queue.put([direction.x, direction.y, action_type])
        action_ret = self.actions_queue.get()
        return action_ret

    def step_level_2(self, obs):
        if self.actions_queue.qsize() > 0:
            return self.actions_queue.get()
        overlap = obs['overlap']
        overlap = self.preprocess(overlap)
        food_balls = overlap['food']
        thorns_balls = overlap['thorns']
        spore_balls = overlap['spore']
        clone_balls = overlap['clone']
        my_clone_balls, others_clone_balls = self.process_clone_balls(clone_balls)
        min_distance, min_thorns_ball = self.process_thorns_balls(thorns_balls, my_clone_balls[0])
        min_distance, min_food_ball = self.process_food_balls(food_balls, my_clone_balls[0])
        if min_thorns_ball is not None:
            direction = min_thorns_ball['position'] - my_clone_balls[0]['position']
        elif min_food_ball is not None:
            direction = min_food_ball['position'] - my_clone_balls[0]['position']
        else:
            direction = Vector2(0, 0) - my_clone_balls[0]['position']
        action_type = 0
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = Vector2(1, 1).normalize()
        self.actions_queue.put([direction.x, direction.y, action_type])
        action_ret = self.actions_queue.get()
        return action_ret

    def step_level_3(self, obs):
        if self.actions_queue.qsize() > 0:
            return self.actions_queue.get()
        overlap = obs['overlap']
        overlap = self.preprocess(overlap)
        food_balls = overlap['food']
        thorns_balls = overlap['thorns']
        spore_balls = overlap['spore']
        clone_balls = overlap['clone']
        my_clone_balls, others_clone_balls = self.process_clone_balls(clone_balls)
        if len(my_clone_balls) >= 9 and my_clone_balls[4]['radius'] > 4:
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([0, 0, 0])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            self.actions_queue.put([None, None, 1])
            action_ret = self.actions_queue.get()
            return action_ret
        if len(others_clone_balls) > 0 and self.can_eat(others_clone_balls[0]['radius'], my_clone_balls[0]['radius']):
            direction = my_clone_balls[0]['position'] - others_clone_balls[0]['position']
            action_type = 0
        else:
            min_distance, min_thorns_ball = self.process_thorns_balls(thorns_balls, my_clone_balls[0])
            if min_thorns_ball is not None:
                direction = min_thorns_ball['position'] - my_clone_balls[0]['position']
            else:
                min_distance, min_food_ball = self.process_food_balls(food_balls, my_clone_balls[0])
                if min_food_ball is not None:
                    direction = min_food_ball['position'] - my_clone_balls[0]['position']
                else:
                    direction = Vector2(0, 0) - my_clone_balls[0]['position']
            action_random = random.random()
            if action_random < 0.02:
                action_type = 1
            if action_random < 0.04 and action_random > 0.02:
                action_type = 2
            else:
                action_type = 0
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = Vector2(1, 1).normalize()
        direction = self.add_noise_to_direction(direction).normalize()
        self.actions_queue.put([direction.x, direction.y, action_type])
        action_ret = self.actions_queue.get()
        return action_ret

    def process_clone_balls(self, clone_balls):
        my_clone_balls = []
        others_clone_balls = []
        for clone_ball in clone_balls:
            if clone_ball['player'] == self.name:
                my_clone_balls.append(copy.deepcopy(clone_ball))
        my_clone_balls.sort(key=lambda a: a['radius'], reverse=True)
        for clone_ball in clone_balls:
            if clone_ball['player'] != self.name:
                others_clone_balls.append(copy.deepcopy(clone_ball))
        others_clone_balls.sort(key=lambda a: a['radius'], reverse=True)
        return (my_clone_balls, others_clone_balls)

    def process_thorns_balls(self, thorns_balls, my_max_clone_ball):
        min_distance = 10000
        min_thorns_ball = None
        for thorns_ball in thorns_balls:
            if self.can_eat(my_max_clone_ball['radius'], thorns_ball['radius']):
                distance = (thorns_ball['position'] - my_max_clone_ball['position']).length()
                if distance < min_distance:
                    min_distance = distance
                    min_thorns_ball = copy.deepcopy(thorns_ball)
        return (min_distance, min_thorns_ball)

    def process_food_balls(self, food_balls, my_max_clone_ball):
        min_distance = 10000
        min_food_ball = None
        for food_ball in food_balls:
            distance = (food_ball['position'] - my_max_clone_ball['position']).length()
            if distance < min_distance:
                min_distance = distance
                min_food_ball = copy.deepcopy(food_ball)
        return (min_distance, min_food_ball)

    def preprocess(self, overlap):
        new_overlap = {}
        for k, v in overlap.items():
            if k == 'clone':
                new_overlap[k] = []
                for index, vv in enumerate(v):
                    tmp = {}
                    tmp['position'] = Vector2(vv[0], vv[1])
                    tmp['radius'] = vv[2]
                    tmp['player'] = int(vv[-2])
                    tmp['team'] = int(vv[-1])
                    new_overlap[k].append(tmp)
            else:
                new_overlap[k] = []
                for index, vv in enumerate(v):
                    tmp = {}
                    tmp['position'] = Vector2(vv[0], vv[1])
                    tmp['radius'] = vv[2]
                    new_overlap[k].append(tmp)
        return new_overlap

    def preprocess_tuple2vector(self, overlap):
        new_overlap = {}
        for k, v in overlap.items():
            new_overlap[k] = []
            for index, vv in enumerate(v):
                new_overlap[k].append(vv)
                new_overlap[k][index]['position'] = Vector2(*vv['position'])
        return new_overlap

    def add_noise_to_direction(self, direction, noise_ratio=0.1):
        direction = direction + Vector2((random.random() * 2 - 1) * noise_ratio * direction.x, (random.random() * 2 - 1) * noise_ratio * direction.y)
        return direction

    def radius_to_score(self, radius):
        return (math.pow(radius, 2) - 0.15) / 0.042 * 100

    def can_eat(self, radius1, radius2):
        return self.radius_to_score(radius1) > 1.3 * self.radius_to_score(radius2)

def radius_to_score(self, radius):
    return (math.pow(radius, 2) - 0.15) / 0.042 * 100

@total_ordering
class BaseBall(ABC):
    """
    Overview:
        Base class of all balls
    """

    @staticmethod
    def default_config():
        """
        Overview:
            Default config
        """
        cfg = dict()
        return EasyDict(cfg)

    def __init__(self, ball_id, position, score, border, **kwargs):
        """
        Parameters:
             vel <Vector2> : the direction of the ball's speed 
             acc <Vector2> : the direction of the ball's acceleration
        """
        self.ball_id = ball_id
        self.position = position
        kwargs = EasyDict(kwargs)
        cfg = BaseBall.default_config()
        cfg = deep_merge_dicts(cfg, kwargs)
        self.score = score
        self.border = border
        self.radius = self.score_to_radius(self.score)
        self.is_remove = False
        self.quad_node = None

    def set_score(self, score: float) -> None:
        self.score = score
        self.radius = self.score_to_radius(self.score)

    def radius_to_score(self, radius):
        return (math.pow(radius, 2) - 0.15) / 0.042 * 100

    def score_to_radius(self, score):
        return math.sqrt(score / 100 * 0.042 + 0.15)

    def move(self, direction, duration):
        """
        Overview:
            Realize the movement of the ball, pass in the direction and time parameters, and return the new position
        Parameters:
            direction <Vector2>: A point in the unit circle
            duration <float>: time
        Returns:
            position <Vector2>: position after moving 
        """
        raise NotImplementedError

    def eat(self, ball):
        """
        Overview:
            Describe the rules of eating and being eaten
        Parameters:
            ball <BaseBall>: Eaten ball
        """
        raise NotImplementedError

    def remove(self):
        """
        Overview:
            Things to do when being removed from the map
        """
        self.is_remove = True

    def check_border(self):
        """
        Overview:
            Check to see if the position of the ball exceeds the bounds of the map. 
            If it exceeds, the speed and acceleration in the corresponding direction will be zeroed, and the position will be edged
        """
        if self.position.x < self.border.minx or self.position.x > self.border.maxx:
            self.position.x = max(self.position.x, self.border.minx)
            self.position.x = min(self.position.x, self.border.maxx)
        if self.position.y < self.border.miny or self.position.y > self.border.maxy:
            self.position.y = max(self.position.y, self.border.miny)
            self.position.y = min(self.position.y, self.border.maxy)

    def get_dis(self, ball):
        """
        Overview:
            Get the distance between the centers of the two balls
        Parameters:
            ball <BaseBall>: another ball
        """
        return (self.position - ball.position).length()

    def judge_cover(self, ball):
        """
        Overview:
            Determine whether the center of the two balls is covered
        Parameters:
            ball <BaseBall>: another ball
        Returns:
            is_covered <bool>: covered or not
        """
        if ball.ball_id == self.ball_id:
            return False
        dis = self.get_dis(ball)
        if self.radius > dis or ball.radius > dis:
            return True
        else:
            return False

    def judge_in_rectangle(self, rectangle):
        """
        Overview:
            Determine if the ball and rectangle intersect
        Parameters:
            rectangle <List>: left_top_x, left_top_y, right_bottom_x, right_bottom_y
        Returns:
            <bool> : intersect or not
        """
        dx = rectangle[0] - self.position.x if rectangle[0] > self.position.x else self.position.x - rectangle[2] if self.position.x > rectangle[2] else 0
        dy = rectangle[1] - self.position.y if rectangle[1] > self.position.y else self.position.y - rectangle[3] if self.position.y > rectangle[3] else 0
        return dx ** 2 + dy ** 2 <= self.radius ** 2

    def __repr__(self) -> str:
        return 'position={}, score={:.3f}, radius={:.3f}'.format(self.position, self.score, self.radius)

    def __eq__(self, other):
        return self.score == other.score

    def __le__(self, other):
        return self.score < other.score

    def __gt__(self, other):
        return self.score > other.score

def radius_to_score(self, radius):
    return (math.pow(radius, 2) - 0.15) / 0.042 * 100

class Model(nn.Module):

    def __init__(self, cfg={}, use_value_network=False):
        super(Model, self).__init__()
        self.whole_cfg = deep_merge_dicts(default_config, cfg)
        self.model_cfg = self.whole_cfg.model
        self.use_value_network = use_value_network
        self.encoder = Encoder(self.whole_cfg)
        self.policy_head = PolicyHead(self.whole_cfg)
        self.temperature = self.whole_cfg.agent.get('temperature', 1)

    def compute_action(self, obs):
        action_mask = obs.pop('action_mask', None)
        embedding = self.encoder(obs)
        logit = self.policy_head(embedding, temperature=self.temperature)
        if action_mask is not None:
            logit.masked_fill_(mask=action_mask, value=-1000000000.0)
        dist = torch.distributions.Categorical(logits=logit)
        action = dist.sample()
        return {'action': action, 'logit': logit}

def compute_action(self, obs):
    action_mask = obs.pop('action_mask', None)
    embedding = self.encoder(obs)
    logit = self.policy_head(embedding, temperature=self.temperature)
    if action_mask is not None:
        logit.masked_fill_(mask=action_mask, value=-1000000000.0)
    dist = torch.distributions.Categorical(logits=logit)
    action = dist.sample()
    return {'action': action, 'logit': logit}

class PolicyHead(nn.Module):

    def __init__(self, cfg):
        super(PolicyHead, self).__init__()
        self.whole_cfg = cfg
        self.cfg = self.whole_cfg.model.policy
        self.embedding_dim = self.cfg.embedding_dim
        self.project_cfg = self.cfg.project
        self.project = fc_block(in_channels=self.project_cfg.input_dim, out_channels=self.embedding_dim, activation=self.project_cfg.activation, norm_type=self.project_cfg.norm_type)
        self.resnet_cfg = self.cfg.resnet
        blocks = [ResFCBlock(in_channels=self.embedding_dim, activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type) for _ in range(self.resnet_cfg.res_num)]
        self.resnet = nn.Sequential(*blocks)
        self.direction_num = self.whole_cfg.agent.features.get('direction_num', 12)
        self.action_num = 2 * self.direction_num + 3
        self.output_layer = fc_block(in_channels=self.embedding_dim, out_channels=self.action_num, norm_type=None, activation=None)

    def forward(self, x, temperature=1):
        x = self.project(x)
        x = self.resnet(x)
        logit = self.output_layer(x)
        logit /= temperature
        return logit

def forward(self, x, temperature=1):
    x = self.project(x)
    x = self.resnet(x)
    logit = self.output_layer(x)
    logit /= temperature
    return logit

class ValueHead(nn.Module):

    def __init__(self, cfg):
        super(ValueHead, self).__init__()
        self.whole_cfg = cfg
        self.cfg = self.whole_cfg.model.value
        self.embedding_dim = self.cfg.embedding_dim
        self.project_cfg = self.cfg.project
        self.project = fc_block(in_channels=self.project_cfg.input_dim, out_channels=self.embedding_dim, activation=self.project_cfg.activation, norm_type=self.project_cfg.norm_type)
        self.resnet_cfg = self.cfg.resnet
        blocks = [ResFCBlock(in_channels=self.embedding_dim, activation=self.resnet_cfg.activation, norm_type=self.resnet_cfg.norm_type) for _ in range(self.resnet_cfg.res_num)]
        self.resnet = nn.Sequential(*blocks)
        self.output_layer = fc_block(in_channels=self.embedding_dim, out_channels=1, norm_type=None, activation=None)

    def forward(self, x):
        x = self.project(x)
        x = self.resnet(x)
        x = self.output_layer(x)
        x = x.squeeze(1)
        return x

def forward(self, x):
    x = self.project(x)
    x = self.resnet(x)
    x = self.output_layer(x)
    x = x.squeeze(1)
    return x

class TimeEncoder(nn.Module):

    def __init__(self, embedding_dim):
        super(TimeEncoder, self).__init__()
        self.embedding_dim = embedding_dim
        self.position_array = torch.nn.Parameter(self.get_position_array(), requires_grad=False)

    def get_position_array(self):
        x = torch.arange(0, self.embedding_dim, dtype=torch.float)
        x = x // 2 * 2
        x = torch.div(x, self.embedding_dim)
        x = torch.pow(10000.0, x)
        x = torch.div(1.0, x)
        return x

    def forward(self, x: torch.Tensor):
        v = torch.zeros(size=(x.shape[0], self.embedding_dim), dtype=torch.float, device=x.device)
        assert len(x.shape) == 1
        x = x.unsqueeze(dim=1)
        v[:, 0::2] = torch.sin(x * self.position_array[0::2])
        v[:, 1::2] = torch.cos(x * self.position_array[1::2])
        return v

def get_position_array(self):
    x = torch.arange(0, self.embedding_dim, dtype=torch.float)
    x = x // 2 * 2
    x = torch.div(x, self.embedding_dim)
    x = torch.pow(10000.0, x)
    x = torch.div(1.0, x)
    return x

class Model(nn.Module):

    def __init__(self, cfg={}, **kwargs):
        super(Model, self).__init__()
        self.whole_cfg = deep_merge_dicts(default_config, cfg)
        self.encoder = Encoder(self.whole_cfg)
        self.policy_head = PolicyHead(self.whole_cfg)
        self.value_head = ValueHead(self.whole_cfg)
        self.only_update_value = False
        self.ortho_init = self.whole_cfg.model.get('ortho_init', True)
        self.player_num = self.whole_cfg.env.player_num_per_team
        self.team_num = self.whole_cfg.env.team_num

    def forward(self, obs, temperature=0):
        obs = flatten_data(obs, start_dim=0, end_dim=1)
        embedding = self.encoder(obs)
        logit = self.policy_head(embedding)
        if temperature == 0:
            action = logit.argmax(dim=-1)
        else:
            logit = logit.div(temperature)
            dist = torch.distributions.Categorical(logits=logit)
            action = dist.sample()
        return {'action': action, 'logit': logit}

    def compute_value(self, obs):
        obs = flatten_data(obs, start_dim=0, end_dim=1)
        embedding = self.encoder(obs)
        batch_size = embedding.shape[0] // self.team_num // self.player_num
        team_embedding = embedding.reshape(batch_size * self.team_num, self.player_num, -1)
        team_embedding = self.transform_ctde(team_embedding, device=team_embedding.device)
        value = self.value_head(team_embedding)
        return {'value': value.reshape(-1)}

    def compute_logp_action(self, obs, **kwargs):
        obs = flatten_data(obs, start_dim=0, end_dim=1)
        embedding = self.encoder(obs)
        batch_size = embedding.shape[0] // self.team_num // self.player_num
        logit = self.policy_head(embedding)
        dist = torch.distributions.Categorical(logits=logit)
        action = dist.sample()
        action_log_probs = dist.log_prob(action)
        log_action_probs = action_log_probs
        team_embedding = embedding.reshape(batch_size * self.team_num, self.player_num, -1)
        team_embedding = self.transform_ctde(team_embedding, device=team_embedding.device)
        value = self.value_head(team_embedding)
        return {'action': action, 'action_logp': log_action_probs, 'logit': logit, 'value': value.reshape(-1)}

    def rl_train(self, inputs: dict, **kwargs) -> Dict[str, Any]:
        """
        Overview:
            Forward and backward function of learn mode.
        Arguments:
            - inputs (:obj:`dict`): Dict type data
        ArgumentsKeys:
            - obs shape     :math:`(T+1, B)`, where T is timestep, B is batch size
            - action_logp: behaviour logits, :math:`(T, B,action_size)`
            - action: behaviour actions, :math:`(T, B)`
            - reward: shape math:`(T, B)`
            - done:shape math:`(T, B)`
        Returns:
            - metric_dict (:obj:`Dict[str, Any]`):
              Including current total_loss, policy_gradient_loss, critic_loss and entropy_loss
        """
        obs = inputs['obs']
        obs = flatten_data(obs, start_dim=0, end_dim=1)
        embedding = self.encoder(obs)
        batch_size = embedding.shape[0] // self.player_num
        logits = self.policy_head(embedding)
        critic_input = embedding.reshape(batch_size, self.player_num, -1)
        critic_input = self.transform_ctde(critic_input, device=critic_input.device)
        if self.only_update_value:
            critic_input = detach_grad(critic_input)
        values = self.value_head(critic_input)
        outputs = {'value': values.squeeze(-1).reshape(-1), 'logit': logits, 'action': inputs['action'].reshape(-1), 'action_logp': inputs['action_logp'].reshape(-1), 'old_value': inputs['old_value'].reshape(-1), 'advantage': inputs['advantage'].reshape(-1), 'return': inputs['return'].reshape(-1)}
        return outputs

    def transform_ctde(self, array, device):
        ret = []
        for i in range(self.player_num):
            index = [i for i in range(self.player_num)]
            index.pop(i)
            other_array = torch.index_select(array, dim=1, index=torch.LongTensor(index).to(device))
            self_array = array[:, i, :].unsqueeze(dim=1)
            ret.append(torch.cat((self_array, other_array), dim=1).flatten(start_dim=1, end_dim=2).unsqueeze(1))
        ret = torch.cat(ret, dim=1)
        return ret

def forward(self, obs, temperature=0):
    obs = flatten_data(obs, start_dim=0, end_dim=1)
    embedding = self.encoder(obs)
    logit = self.policy_head(embedding)
    if temperature == 0:
        action = logit.argmax(dim=-1)
    else:
        logit = logit.div(temperature)
        dist = torch.distributions.Categorical(logits=logit)
        action = dist.sample()
    return {'action': action, 'logit': logit}

def compute_value(self, obs):
    obs = flatten_data(obs, start_dim=0, end_dim=1)
    embedding = self.encoder(obs)
    batch_size = embedding.shape[0] // self.team_num // self.player_num
    team_embedding = embedding.reshape(batch_size * self.team_num, self.player_num, -1)
    team_embedding = self.transform_ctde(team_embedding, device=team_embedding.device)
    value = self.value_head(team_embedding)
    return {'value': value.reshape(-1)}

def compute_logp_action(self, obs, **kwargs):
    obs = flatten_data(obs, start_dim=0, end_dim=1)
    embedding = self.encoder(obs)
    batch_size = embedding.shape[0] // self.team_num // self.player_num
    logit = self.policy_head(embedding)
    dist = torch.distributions.Categorical(logits=logit)
    action = dist.sample()
    action_log_probs = dist.log_prob(action)
    log_action_probs = action_log_probs
    team_embedding = embedding.reshape(batch_size * self.team_num, self.player_num, -1)
    team_embedding = self.transform_ctde(team_embedding, device=team_embedding.device)
    value = self.value_head(team_embedding)
    return {'action': action, 'action_logp': log_action_probs, 'logit': logit, 'value': value.reshape(-1)}

def rl_train(self, inputs: dict, **kwargs) -> Dict[str, Any]:
    """
        Overview:
            Forward and backward function of learn mode.
        Arguments:
            - inputs (:obj:`dict`): Dict type data
        ArgumentsKeys:
            - obs shape     :math:`(T+1, B)`, where T is timestep, B is batch size
            - action_logp: behaviour logits, :math:`(T, B,action_size)`
            - action: behaviour actions, :math:`(T, B)`
            - reward: shape math:`(T, B)`
            - done:shape math:`(T, B)`
        Returns:
            - metric_dict (:obj:`Dict[str, Any]`):
              Including current total_loss, policy_gradient_loss, critic_loss and entropy_loss
        """
    obs = inputs['obs']
    obs = flatten_data(obs, start_dim=0, end_dim=1)
    embedding = self.encoder(obs)
    batch_size = embedding.shape[0] // self.player_num
    logits = self.policy_head(embedding)
    critic_input = embedding.reshape(batch_size, self.player_num, -1)
    critic_input = self.transform_ctde(critic_input, device=critic_input.device)
    if self.only_update_value:
        critic_input = detach_grad(critic_input)
    values = self.value_head(critic_input)
    outputs = {'value': values.squeeze(-1).reshape(-1), 'logit': logits, 'action': inputs['action'].reshape(-1), 'action_logp': inputs['action_logp'].reshape(-1), 'old_value': inputs['old_value'].reshape(-1), 'advantage': inputs['advantage'].reshape(-1), 'return': inputs['return'].reshape(-1)}
    return outputs

