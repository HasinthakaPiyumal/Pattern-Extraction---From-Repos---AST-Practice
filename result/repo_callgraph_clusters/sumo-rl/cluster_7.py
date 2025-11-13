# Cluster 7

class QLAgent:
    """Q-learning Agent class."""

    def __init__(self, starting_state, state_space, action_space, alpha=0.5, gamma=0.95, exploration_strategy=EpsilonGreedy()):
        """Initialize Q-learning agent."""
        self.state = starting_state
        self.state_space = state_space
        self.action_space = action_space
        self.action = None
        self.alpha = alpha
        self.gamma = gamma
        self.q_table = {self.state: [0 for _ in range(action_space.n)]}
        self.exploration = exploration_strategy
        self.acc_reward = 0

    def act(self):
        """Choose action based on Q-table."""
        self.action = self.exploration.choose(self.q_table, self.state, self.action_space)
        return self.action

    def learn(self, next_state, reward, done=False):
        """Update Q-table with new experience."""
        if next_state not in self.q_table:
            self.q_table[next_state] = [0 for _ in range(self.action_space.n)]
        s = self.state
        s1 = next_state
        a = self.action
        self.q_table[s][a] = self.q_table[s][a] + self.alpha * (reward + self.gamma * max(self.q_table[s1]) - self.q_table[s][a])
        self.state = s1
        self.acc_reward += reward

def learn(self, next_state, reward, done=False):
    """Update Q-table with new experience."""
    if next_state not in self.q_table:
        self.q_table[next_state] = [0 for _ in range(self.action_space.n)]
    s = self.state
    s1 = next_state
    a = self.action
    self.q_table[s][a] = self.q_table[s][a] + self.alpha * (reward + self.gamma * max(self.q_table[s1]) - self.q_table[s][a])
    self.state = s1
    self.acc_reward += reward

def movingaverage(interval, window_size):
    window = np.ones(int(window_size)) / float(window_size)
    return np.convolve(interval, window, 'same')

class TrafficSignal:
    """This class represents a Traffic Signal controlling an intersection.

    It is responsible for retrieving information and changing the traffic phase using the Traci API.

    IMPORTANT: It assumes that the traffic phases defined in the .net file are of the form:
        [green_phase, yellow_phase, green_phase, yellow_phase, ...]
    Currently it is not supporting all-red phases (but should be easy to implement it).

    # Observation Space
    The default observation for each traffic signal agent is a vector:

    obs = [phase_one_hot, min_green, lane_1_density,...,lane_n_density, lane_1_queue,...,lane_n_queue]

    - ```phase_one_hot``` is a one-hot encoded vector indicating the current active green phase
    - ```min_green``` is a binary variable indicating whether min_green seconds have already passed in the current phase
    - ```lane_i_density``` is the number of vehicles in incoming lane i dividided by the total capacity of the lane
    - ```lane_i_queue``` is the number of queued (speed below 0.1 m/s) vehicles in incoming lane i divided by the total capacity of the lane

    You can change the observation space by implementing a custom observation class. See :py:class:`sumo_rl.environment.observations.ObservationFunction`.

    # Action Space
    Action space is discrete, corresponding to which green phase is going to be open for the next delta_time seconds.

    # Reward Function
    The default reward function is 'diff-waiting-time'. You can change the reward function by implementing a custom reward function and passing to the constructor of :py:class:`sumo_rl.environment.env.SumoEnvironment`.
    """
    MIN_GAP = 2.5

    def __init__(self, env, ts_id: str, delta_time: int, yellow_time: int, min_green: int, max_green: int, enforce_max_green: bool, begin_time: int, reward_fn: Union[str, Callable, List], reward_weights: List[float], sumo):
        """Initializes a TrafficSignal object.

        Args:
            env (SumoEnvironment): The environment this traffic signal belongs to.
            ts_id (str): The id of the traffic signal.
            delta_time (int): The time in seconds between actions.
            yellow_time (int): The time in seconds of the yellow phase.
            min_green (int): The minimum time in seconds of the green phase.
            max_green (int): The maximum time in seconds of the green phase.
            enforce_max_green (bool): If True, the traffic signal will always change phase after max green seconds.
            begin_time (int): The time in seconds when the traffic signal starts operating.
            reward_fn (Union[str, Callable]): The reward function. Can be a string with the name of the reward function or a callable function.
            reward_weights (List[float]): The weights of the reward function.
            sumo (Sumo): The Sumo instance.
        """
        self.id = ts_id
        self.env = env
        self.delta_time = delta_time
        self.yellow_time = yellow_time
        self.min_green = min_green
        self.max_green = max_green
        self.enforce_max_green = enforce_max_green
        self.green_phase = 0
        self.is_yellow = False
        self.time_since_last_phase_change = 0
        self.next_action_time = begin_time
        self.last_ts_waiting_time = 0.0
        self.last_reward = None
        self.reward_fn = reward_fn
        self.reward_weights = reward_weights
        self.sumo = sumo
        if type(self.reward_fn) is list:
            self.reward_dim = len(self.reward_fn)
            self.reward_list = [self._get_reward_fn_from_string(reward_fn) for reward_fn in self.reward_fn]
        else:
            self.reward_dim = 1
            self.reward_list = [self._get_reward_fn_from_string(self.reward_fn)]
        if self.reward_weights is not None:
            self.reward_dim = 1
        self.reward_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.reward_dim,), dtype=np.float32)
        self.observation_fn = self.env.observation_class(self)
        self._build_phases()
        self.lanes = list(dict.fromkeys(self.sumo.trafficlight.getControlledLanes(self.id)))
        self.out_lanes = [link[0][1] for link in self.sumo.trafficlight.getControlledLinks(self.id) if link]
        self.out_lanes = list(set(self.out_lanes))
        self.lanes_length = {lane: self.sumo.lane.getLength(lane) for lane in self.lanes + self.out_lanes}
        self.observation_space = self.observation_fn.observation_space()
        self.action_space = spaces.Discrete(self.num_green_phases)

    def _get_reward_fn_from_string(self, reward_fn):
        if type(reward_fn) is str:
            if reward_fn in TrafficSignal.reward_fns.keys():
                return TrafficSignal.reward_fns[reward_fn]
            else:
                raise NotImplementedError(f'Reward function {reward_fn} not implemented')
        return reward_fn

    def _build_phases(self):
        phases = self.sumo.trafficlight.getAllProgramLogics(self.id)[0].phases
        if self.env.fixed_ts:
            self.num_green_phases = len(phases) // 2
            return
        self.green_phases = []
        self.yellow_dict = {}
        for phase in phases:
            state = phase.state
            if 'y' not in state and state.count('r') + state.count('s') != len(state):
                self.green_phases.append(self.sumo.trafficlight.Phase(60, state))
        self.num_green_phases = len(self.green_phases)
        self.all_phases = self.green_phases.copy()
        for i, p1 in enumerate(self.green_phases):
            for j, p2 in enumerate(self.green_phases):
                if i == j:
                    continue
                yellow_state = ''
                for s in range(len(p1.state)):
                    if (p1.state[s] == 'G' or p1.state[s] == 'g') and (p2.state[s] == 'r' or p2.state[s] == 's'):
                        yellow_state += 'y'
                    else:
                        yellow_state += p1.state[s]
                self.yellow_dict[i, j] = len(self.all_phases)
                self.all_phases.append(self.sumo.trafficlight.Phase(self.yellow_time, yellow_state))
        programs = self.sumo.trafficlight.getAllProgramLogics(self.id)
        logic = programs[0]
        logic.type = 0
        logic.phases = self.all_phases
        self.sumo.trafficlight.setProgramLogic(self.id, logic)
        self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[0].state)

    @property
    def time_to_act(self):
        """Returns True if the traffic signal should act in the current step."""
        return self.next_action_time == self.env.sim_step

    def update(self):
        """Updates the traffic signal state.

        If the traffic signal should act, it will set the next green phase and update the next action time.
        """
        self.time_since_last_phase_change += 1
        if self.is_yellow and self.time_since_last_phase_change == self.yellow_time:
            self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[self.green_phase].state)
            self.is_yellow = False

    def set_next_phase(self, new_phase: int):
        """Sets what will be the next green phase and sets yellow phase if the next phase is different than the current.

        Args:
            new_phase (int): Number between [0 ... num_green_phases]
        """
        new_phase = int(new_phase)
        if self.enforce_max_green and new_phase == self.green_phase and (self.time_since_last_phase_change >= self.max_green):
            new_phase = (self.green_phase + 1) % self.num_green_phases
        if self.green_phase == new_phase or self.time_since_last_phase_change < self.yellow_time + self.min_green:
            self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[self.green_phase].state)
            self.next_action_time = self.env.sim_step + self.delta_time
        else:
            self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[self.yellow_dict[self.green_phase, new_phase]].state)
            self.green_phase = new_phase
            self.next_action_time = self.env.sim_step + self.delta_time
            self.is_yellow = True
            self.time_since_last_phase_change = 0

    def compute_observation(self):
        """Computes the observation of the traffic signal."""
        return self.observation_fn()

    def compute_reward(self) -> Union[float, np.ndarray]:
        """Computes the reward of the traffic signal. If it is a list of rewards, it returns a numpy array."""
        if self.reward_dim == 1:
            self.last_reward = self.reward_list[0](self)
        else:
            self.last_reward = np.array([reward_fn(self) for reward_fn in self.reward_list], dtype=np.float32)
            if self.reward_weights is not None:
                self.last_reward = np.dot(self.last_reward, self.reward_weights)
        return self.last_reward

    def _pressure_reward(self):
        return self.get_pressure()

    def _average_speed_reward(self):
        return self.get_average_speed()

    def _queue_reward(self):
        return -self.get_total_queued()

    def _diff_waiting_time_reward(self):
        ts_wait = sum(self.get_accumulated_waiting_time_per_lane()) / 100.0
        reward = self.last_ts_waiting_time - ts_wait
        self.last_ts_waiting_time = ts_wait
        return reward

    def _observation_fn_default(self):
        phase_id = [1 if self.green_phase == i else 0 for i in range(self.num_green_phases)]
        min_green = [0 if self.time_since_last_phase_change < self.min_green + self.yellow_time else 1]
        density = self.get_lanes_density()
        queue = self.get_lanes_queue()
        observation = np.array(phase_id + min_green + density + queue, dtype=np.float32)
        return observation

    def get_accumulated_waiting_time_per_lane(self) -> List[float]:
        """Returns the accumulated waiting time per lane.

        Returns:
            List[float]: List of accumulated waiting time of each intersection lane.
        """
        wait_time_per_lane = []
        for lane in self.lanes:
            veh_list = self.sumo.lane.getLastStepVehicleIDs(lane)
            wait_time = 0.0
            for veh in veh_list:
                veh_lane = self.sumo.vehicle.getLaneID(veh)
                acc = self.sumo.vehicle.getAccumulatedWaitingTime(veh)
                if veh not in self.env.vehicles:
                    self.env.vehicles[veh] = {veh_lane: acc}
                else:
                    self.env.vehicles[veh][veh_lane] = acc - sum([self.env.vehicles[veh][lane] for lane in self.env.vehicles[veh].keys() if lane != veh_lane])
                wait_time += self.env.vehicles[veh][veh_lane]
            wait_time_per_lane.append(wait_time)
        return wait_time_per_lane

    def get_average_speed(self) -> float:
        """Returns the average speed normalized by the maximum allowed speed of the vehicles in the intersection.

        Obs: If there are no vehicles in the intersection, it returns 1.0.
        """
        avg_speed = 0.0
        vehs = self._get_veh_list()
        if len(vehs) == 0:
            return 1.0
        for v in vehs:
            avg_speed += self.sumo.vehicle.getSpeed(v) / self.sumo.vehicle.getAllowedSpeed(v)
        return avg_speed / len(vehs)

    def get_pressure(self):
        """Returns the pressure (#veh leaving - #veh approaching) of the intersection."""
        return sum((self.sumo.lane.getLastStepVehicleNumber(lane) for lane in self.out_lanes)) - sum((self.sumo.lane.getLastStepVehicleNumber(lane) for lane in self.lanes))

    def get_out_lanes_density(self) -> List[float]:
        """Returns the density of the vehicles in the outgoing lanes of the intersection."""
        lanes_density = [self.sumo.lane.getLastStepVehicleNumber(lane) / (self.lanes_length[lane] / (self.MIN_GAP + self.sumo.lane.getLastStepLength(lane))) for lane in self.out_lanes]
        return [min(1, density) for density in lanes_density]

    def get_lanes_density(self) -> List[float]:
        """Returns the density [0,1] of the vehicles in the incoming lanes of the intersection.

        Obs: The density is computed as the number of vehicles divided by the number of vehicles that could fit in the lane.
        """
        lanes_density = [self.sumo.lane.getLastStepVehicleNumber(lane) / (self.lanes_length[lane] / (self.MIN_GAP + self.sumo.lane.getLastStepLength(lane))) for lane in self.lanes]
        return [min(1, density) for density in lanes_density]

    def get_lanes_queue(self) -> List[float]:
        """Returns the queue [0,1] of the vehicles in the incoming lanes of the intersection.

        Obs: The queue is computed as the number of vehicles halting divided by the number of vehicles that could fit in the lane.
        """
        lanes_queue = [self.sumo.lane.getLastStepHaltingNumber(lane) / (self.lanes_length[lane] / (self.MIN_GAP + self.sumo.lane.getLastStepLength(lane))) for lane in self.lanes]
        return [min(1, queue) for queue in lanes_queue]

    def get_total_queued(self) -> int:
        """Returns the total number of vehicles halting in the intersection."""
        return sum((self.sumo.lane.getLastStepHaltingNumber(lane) for lane in self.lanes))

    def _get_veh_list(self):
        veh_list = []
        for lane in self.lanes:
            veh_list += self.sumo.lane.getLastStepVehicleIDs(lane)
        return veh_list

    @classmethod
    def register_reward_fn(cls, fn: Callable):
        """Registers a reward function.

        Args:
            fn (Callable): The reward function to register.
        """
        if fn.__name__ in cls.reward_fns.keys():
            raise KeyError(f'Reward function {fn.__name__} already exists')
        cls.reward_fns[fn.__name__] = fn
    reward_fns = {'diff-waiting-time': _diff_waiting_time_reward, 'average-speed': _average_speed_reward, 'queue': _queue_reward, 'pressure': _pressure_reward}

def update(self):
    """Updates the traffic signal state.

        If the traffic signal should act, it will set the next green phase and update the next action time.
        """
    self.time_since_last_phase_change += 1
    if self.is_yellow and self.time_since_last_phase_change == self.yellow_time:
        self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[self.green_phase].state)
        self.is_yellow = False

def set_next_phase(self, new_phase: int):
    """Sets what will be the next green phase and sets yellow phase if the next phase is different than the current.

        Args:
            new_phase (int): Number between [0 ... num_green_phases]
        """
    new_phase = int(new_phase)
    if self.enforce_max_green and new_phase == self.green_phase and (self.time_since_last_phase_change >= self.max_green):
        new_phase = (self.green_phase + 1) % self.num_green_phases
    if self.green_phase == new_phase or self.time_since_last_phase_change < self.yellow_time + self.min_green:
        self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[self.green_phase].state)
        self.next_action_time = self.env.sim_step + self.delta_time
    else:
        self.sumo.trafficlight.setRedYellowGreenState(self.id, self.all_phases[self.yellow_dict[self.green_phase, new_phase]].state)
        self.green_phase = new_phase
        self.next_action_time = self.env.sim_step + self.delta_time
        self.is_yellow = True
        self.time_since_last_phase_change = 0

class SumoEnvironment(gym.Env):
    """SUMO Environment for Traffic Signal Control.

    Class that implements a gym.Env interface for traffic signal control using the SUMO simulator.
    See https://sumo.dlr.de/docs/ for details on SUMO.
    See https://gymnasium.farama.org/ for details on gymnasium.

    Args:
        net_file (str): SUMO .net.xml file
        route_file (str): SUMO .rou.xml file
        out_csv_name (Optional[str]): name of the .csv output with simulation results. If None, no output is generated
        use_gui (bool): Whether to run SUMO simulation with the SUMO GUI
        virtual_display (Optional[Tuple[int,int]]): Resolution of the virtual display for rendering
        begin_time (int): The time step (in seconds) the simulation starts. Default: 0
        num_seconds (int): Number of simulated seconds on SUMO. The duration in seconds of the simulation. Default: 20000
        max_depart_delay (int): Vehicles are discarded if they could not be inserted after max_depart_delay seconds. Default: -1 (no delay)
        waiting_time_memory (int): Number of seconds to remember the waiting time of a vehicle (see https://sumo.dlr.de/pydoc/traci._vehicle.html#VehicleDomain-getAccumulatedWaitingTime). Default: 1000
        time_to_teleport (int): Time in seconds to teleport a vehicle to the end of the edge if it is stuck. Default: -1 (no teleport)
        delta_time (int): Simulation seconds between actions. Default: 5 seconds
        yellow_time (int): Duration of the yellow phase. Default: 2 seconds
        min_green (int): Minimum green time in a phase. Default: 5 seconds
        max_green (int): Max green time in a phase. Default: 60 seconds. Warning: This parameter is currently ignored!
        enforce_max_green (bool): If true, it enforces the max green time and selects the next green phase when the max green time is reached. Default: False
        single_agent (bool): If true, it behaves like a regular gym.Env. Else, it behaves like a MultiagentEnv (returns dict of observations, rewards, dones, infos).
        reward_fn (str/function/dict/List): String with the name of the reward function used by the agents, a reward function, dictionary with reward functions assigned to individual traffic lights by their keys, or a List of reward functions.
        reward_weights (List[float]/np.ndarray): Weights for linearly combining the reward functions, in case reward_fn is a list. If it is None, the reward returned will be a np.ndarray. Default: None
        observation_class (ObservationFunction): Inherited class which has both the observation function and observation space.
        add_system_info (bool): If true, it computes system metrics (total queue, total waiting time, average speed) in the info dictionary.
        add_per_agent_info (bool): If true, it computes per-agent (per-traffic signal) metrics (average accumulated waiting time, average queue) in the info dictionary.
        sumo_seed (int/string): Random seed for sumo. If 'random' it uses a randomly chosen seed.
        ts_ids (Optional[List[str]]): List of traffic light IDs to be controlled by SUMO-RL. If None, all traffic lights in the simulation are controlled.
        fixed_ts (bool): If true, it will follow the phase configuration in the route_file and ignore the actions given in the :meth:`step` method.
        sumo_warnings (bool): If true, it will print SUMO warnings.
        additional_sumo_cmd (str): Additional SUMO command line arguments.
        render_mode (str): Mode of rendering. Can be 'human' or 'rgb_array'. Default: None
    """
    metadata = {'render_modes': ['human', 'rgb_array']}
    CONNECTION_LABEL = 0

    def __init__(self, net_file: str, route_file: str, out_csv_name: Optional[str]=None, use_gui: bool=False, virtual_display: Tuple[int, int]=(3200, 1800), begin_time: int=0, num_seconds: int=20000, max_depart_delay: int=-1, waiting_time_memory: int=1000, time_to_teleport: int=-1, delta_time: int=5, yellow_time: int=2, min_green: int=5, max_green: int=50, enforce_max_green: bool=False, single_agent: bool=False, reward_fn: Union[str, Callable, dict, List]='diff-waiting-time', reward_weights: Optional[List[float]]=None, observation_class: type[ObservationFunction]=DefaultObservationFunction, add_system_info: bool=True, add_per_agent_info: bool=True, sumo_seed: Union[str, int]='random', ts_ids: Optional[List[str]]=None, fixed_ts: bool=False, sumo_warnings: bool=True, additional_sumo_cmd: Optional[str]=None, render_mode: Optional[str]=None) -> None:
        """Initialize the environment."""
        assert render_mode is None or render_mode in self.metadata['render_modes'], 'Invalid render mode.'
        self.render_mode = render_mode
        self.virtual_display = virtual_display
        self.disp = None
        self._net = net_file
        self._route = route_file
        self.use_gui = use_gui
        if self.use_gui or self.render_mode is not None:
            self._sumo_binary = sumolib.checkBinary('sumo-gui')
        else:
            self._sumo_binary = sumolib.checkBinary('sumo')
        assert delta_time > yellow_time, 'Time between actions must be at least greater than yellow time.'
        assert max_green > min_green, 'Max green time must be greater than min green time.'
        self.begin_time = begin_time
        self.sim_max_time = begin_time + num_seconds
        self.delta_time = delta_time
        self.max_depart_delay = max_depart_delay
        self.waiting_time_memory = waiting_time_memory
        self.time_to_teleport = time_to_teleport
        self.min_green = min_green
        self.max_green = max_green
        self.enforce_max_green = enforce_max_green
        self.yellow_time = yellow_time
        self.single_agent = single_agent
        self.reward_fn = reward_fn
        self.reward_weights = reward_weights
        self.sumo_seed = sumo_seed
        self.fixed_ts = fixed_ts
        self.sumo_warnings = sumo_warnings
        self.additional_sumo_cmd = additional_sumo_cmd
        self.add_system_info = add_system_info
        self.add_per_agent_info = add_per_agent_info
        self.label = str(SumoEnvironment.CONNECTION_LABEL)
        SumoEnvironment.CONNECTION_LABEL += 1
        self.sumo = None
        if LIBSUMO:
            traci.start([sumolib.checkBinary('sumo'), '-n', self._net])
            conn = traci
        else:
            traci.start([sumolib.checkBinary('sumo'), '-n', self._net], label='init_connection' + self.label)
            conn = traci.getConnection('init_connection' + self.label)
        if ts_ids is None:
            self.ts_ids = list(conn.trafficlight.getIDList())
        else:
            self.ts_ids = ts_ids
        self.observation_class = observation_class
        self._build_traffic_signals(conn)
        conn.close()
        self.vehicles = dict()
        self.reward_range = (-float('inf'), float('inf'))
        self.episode = 0
        self.metrics = []
        self.out_csv_name = out_csv_name
        self.observations = {ts: None for ts in self.ts_ids}
        self.rewards = {ts: None for ts in self.ts_ids}

    def _build_traffic_signals(self, conn):
        if not isinstance(self.reward_fn, dict):
            self.reward_fn = {ts: self.reward_fn for ts in self.ts_ids}
        self.traffic_signals = {ts: TrafficSignal(self, ts, self.delta_time, self.yellow_time, self.min_green, self.max_green, self.enforce_max_green, self.begin_time, self.reward_fn[ts], self.reward_weights, conn) for ts in self.ts_ids}

    def _start_simulation(self):
        sumo_cmd = [self._sumo_binary, '-n', self._net, '-r', self._route, '--max-depart-delay', str(self.max_depart_delay), '--waiting-time-memory', str(self.waiting_time_memory), '--time-to-teleport', str(self.time_to_teleport)]
        if self.begin_time > 0:
            sumo_cmd.append(f'-b {self.begin_time}')
        if self.sumo_seed == 'random':
            sumo_cmd.append('--random')
        else:
            sumo_cmd.extend(['--seed', str(self.sumo_seed)])
        if not self.sumo_warnings:
            sumo_cmd.append('--no-warnings')
        if self.additional_sumo_cmd is not None:
            sumo_cmd.extend(self.additional_sumo_cmd.split())
        if self.use_gui or self.render_mode is not None:
            sumo_cmd.extend(['--start', '--quit-on-end'])
            if self.render_mode == 'rgb_array':
                sumo_cmd.extend(['--window-size', f'{self.virtual_display[0]},{self.virtual_display[1]}'])
                from pyvirtualdisplay.smartdisplay import SmartDisplay
                print('Creating a virtual display.')
                self.disp = SmartDisplay(size=self.virtual_display)
                self.disp.start()
                print('Virtual display started.')
        if LIBSUMO:
            traci.start(sumo_cmd)
            self.sumo = traci
        else:
            traci.start(sumo_cmd, label=self.label)
            self.sumo = traci.getConnection(self.label)
        if self.use_gui or self.render_mode is not None:
            if 'DEFAULT_VIEW' not in dir(traci.gui):
                traci.gui.DEFAULT_VIEW = 'View #0'
            self.sumo.gui.setSchema(traci.gui.DEFAULT_VIEW, 'real world')

    def reset(self, seed: Optional[int]=None, **kwargs):
        """Reset the environment."""
        super().reset(seed=seed, **kwargs)
        if self.episode != 0:
            self.close()
            self.save_csv(self.out_csv_name, self.episode)
        self.episode += 1
        self.metrics = []
        if seed is not None:
            self.sumo_seed = seed
        self._start_simulation()
        self._build_traffic_signals(self.sumo)
        self.vehicles = dict()
        self.num_arrived_vehicles = 0
        self.num_departed_vehicles = 0
        self.num_teleported_vehicles = 0
        if self.single_agent:
            return (self._compute_observations()[self.ts_ids[0]], self._compute_info())
        else:
            return self._compute_observations()

    @property
    def sim_step(self) -> float:
        """Return current simulation second on SUMO."""
        return self.sumo.simulation.getTime()

    def step(self, action: Union[dict, int]):
        """Apply the action(s) and then step the simulation for delta_time seconds.

        Args:
            action (Union[dict, int]): action(s) to be applied to the environment.
            If single_agent is True, action is an int, otherwise it expects a dict with keys corresponding to traffic signal ids.
        """
        if self.fixed_ts or action is None or action == {}:
            for _ in range(self.delta_time):
                self._sumo_step()
        else:
            self._apply_actions(action)
            self._run_steps()
        observations = self._compute_observations()
        rewards = self._compute_rewards()
        dones = self._compute_dones()
        terminated = False
        truncated = dones['__all__']
        info = self._compute_info()
        if self.single_agent:
            return (observations[self.ts_ids[0]], rewards[self.ts_ids[0]], terminated, truncated, info)
        else:
            return (observations, rewards, dones, info)

    def _run_steps(self):
        time_to_act = False
        while not time_to_act:
            self._sumo_step()
            for ts in self.ts_ids:
                self.traffic_signals[ts].update()
                if self.traffic_signals[ts].time_to_act:
                    time_to_act = True

    def _apply_actions(self, actions):
        """Set the next green phase for the traffic signals.

        Args:
            actions: If single-agent, actions is an int between 0 and self.num_green_phases (next green phase)
                     If multiagent, actions is a dict {ts_id : greenPhase}
        """
        if self.single_agent:
            if self.traffic_signals[self.ts_ids[0]].time_to_act:
                self.traffic_signals[self.ts_ids[0]].set_next_phase(actions)
        else:
            for ts, action in actions.items():
                if self.traffic_signals[ts].time_to_act:
                    self.traffic_signals[ts].set_next_phase(action)

    def _compute_dones(self):
        dones = {ts_id: False for ts_id in self.ts_ids}
        dones['__all__'] = self.sim_step >= self.sim_max_time
        return dones

    def _compute_info(self):
        info = {'step': self.sim_step}
        if self.add_system_info:
            info.update(self._get_system_info())
        if self.add_per_agent_info:
            info.update(self._get_per_agent_info())
        self.metrics.append(info.copy())
        return info

    def _compute_observations(self):
        self.observations.update({ts: self.traffic_signals[ts].compute_observation() for ts in self.ts_ids if self.traffic_signals[ts].time_to_act or self.fixed_ts})
        return {ts: self.observations[ts].copy() for ts in self.observations.keys() if self.traffic_signals[ts].time_to_act or self.fixed_ts}

    def _compute_rewards(self):
        self.rewards.update({ts: self.traffic_signals[ts].compute_reward() for ts in self.ts_ids if self.traffic_signals[ts].time_to_act or self.fixed_ts})
        return {ts: self.rewards[ts] for ts in self.rewards.keys() if self.traffic_signals[ts].time_to_act or self.fixed_ts}

    @property
    def observation_space(self):
        """Return the observation space of a traffic signal.

        Only used in case of single-agent environment.
        """
        return self.traffic_signals[self.ts_ids[0]].observation_space

    @property
    def action_space(self):
        """Return the action space of a traffic signal.

        Only used in case of single-agent environment.
        """
        return self.traffic_signals[self.ts_ids[0]].action_space

    @property
    def reward_space(self):
        """Return the reward space of a traffic signal.

        Only used in case of single-agent environment.
        """
        return self.traffic_signals[self.ts_ids[0]].reward_space

    @property
    def reward_dim(self):
        """Return the reward dimension of a traffic signal.

        Only used in case of single-agent environment.
        """
        return self.traffic_signals[self.ts_ids[0]].reward_dim

    def observation_spaces(self, ts_id: str):
        """Return the observation space of a traffic signal."""
        return self.traffic_signals[ts_id].observation_space

    def action_spaces(self, ts_id: str) -> gym.spaces.Discrete:
        """Return the action space of a traffic signal."""
        return self.traffic_signals[ts_id].action_space

    def _sumo_step(self):
        self.sumo.simulationStep()
        self.num_arrived_vehicles += self.sumo.simulation.getArrivedNumber()
        self.num_departed_vehicles += self.sumo.simulation.getDepartedNumber()
        self.num_teleported_vehicles += self.sumo.simulation.getEndingTeleportNumber()

    def _get_system_info(self):
        vehicles = self.sumo.vehicle.getIDList()
        speeds = [self.sumo.vehicle.getSpeed(vehicle) for vehicle in vehicles]
        waiting_times = [self.sumo.vehicle.getWaitingTime(vehicle) for vehicle in vehicles]
        num_backlogged_vehicles = len(self.sumo.simulation.getPendingVehicles())
        return {'system_total_running': len(vehicles), 'system_total_backlogged': num_backlogged_vehicles, 'system_total_stopped': sum((int(speed < 0.1) for speed in speeds)), 'system_total_arrived': self.num_arrived_vehicles, 'system_total_departed': self.num_departed_vehicles, 'system_total_teleported': self.num_teleported_vehicles, 'system_total_waiting_time': sum(waiting_times), 'system_mean_waiting_time': 0.0 if len(vehicles) == 0 else np.mean(waiting_times), 'system_mean_speed': 0.0 if len(vehicles) == 0 else np.mean(speeds)}

    def _get_per_agent_info(self):
        stopped = [self.traffic_signals[ts].get_total_queued() for ts in self.ts_ids]
        accumulated_waiting_time = [sum(self.traffic_signals[ts].get_accumulated_waiting_time_per_lane()) for ts in self.ts_ids]
        average_speed = [self.traffic_signals[ts].get_average_speed() for ts in self.ts_ids]
        info = {}
        for i, ts in enumerate(self.ts_ids):
            info[f'{ts}_stopped'] = stopped[i]
            info[f'{ts}_accumulated_waiting_time'] = accumulated_waiting_time[i]
            info[f'{ts}_average_speed'] = average_speed[i]
        info['agents_total_stopped'] = sum(stopped)
        info['agents_total_accumulated_waiting_time'] = sum(accumulated_waiting_time)
        return info

    def close(self):
        """Close the environment and stop the SUMO simulation."""
        if self.sumo is None:
            return
        if not LIBSUMO:
            traci.switch(self.label)
        traci.close()
        if self.disp is not None:
            self.disp.stop()
            self.disp = None
        self.sumo = None

    def __del__(self):
        """Close the environment and stop the SUMO simulation."""
        self.close()

    def render(self):
        """Render the environment.

        If render_mode is "human", the environment will be rendered in a GUI window using pyvirtualdisplay.
        """
        if self.render_mode == 'human':
            return
        elif self.render_mode == 'rgb_array':
            img = self.disp.grab()
            return np.array(img)

    def save_csv(self, out_csv_name, episode):
        """Save metrics of the simulation to a .csv file.

        Args:
            out_csv_name (str): Path to the output .csv file. E.g.: "results/my_results
            episode (int): Episode number to be appended to the output file name.
        """
        if out_csv_name is not None:
            df = pd.DataFrame(self.metrics)
            Path(Path(out_csv_name).parent).mkdir(parents=True, exist_ok=True)
            df.to_csv(out_csv_name + f'_conn{self.label}_ep{episode}' + '.csv', index=False)

    def encode(self, state, ts_id):
        """Encode the state of the traffic signal into a hashable object."""
        phase = int(np.where(state[:self.traffic_signals[ts_id].num_green_phases] == 1)[0])
        min_green = state[self.traffic_signals[ts_id].num_green_phases]
        density_queue = [self._discretize_density(d) for d in state[self.traffic_signals[ts_id].num_green_phases + 1:]]
        return tuple([phase, min_green] + density_queue)

    def _discretize_density(self, density):
        return min(int(density * 10), 9)

def encode(self, state, ts_id):
    """Encode the state of the traffic signal into a hashable object."""
    phase = int(np.where(state[:self.traffic_signals[ts_id].num_green_phases] == 1)[0])
    min_green = state[self.traffic_signals[ts_id].num_green_phases]
    density_queue = [self._discretize_density(d) for d in state[self.traffic_signals[ts_id].num_green_phases + 1:]]
    return tuple([phase, min_green] + density_queue)

class EpsilonGreedy:
    """Epsilon Greedy Exploration Strategy."""

    def __init__(self, initial_epsilon=1.0, min_epsilon=0.0, decay=0.99):
        """Initialize Epsilon Greedy Exploration Strategy."""
        self.initial_epsilon = initial_epsilon
        self.epsilon = initial_epsilon
        self.min_epsilon = min_epsilon
        self.decay = decay

    def choose(self, q_table, state, action_space):
        """Choose action based on epsilon greedy strategy."""
        if np.random.rand() < self.epsilon:
            action = int(action_space.sample())
        else:
            action = np.argmax(q_table[state])
        self.epsilon = max(self.epsilon * self.decay, self.min_epsilon)
        return action

    def reset(self):
        """Reset epsilon to initial value."""
        self.epsilon = self.initial_epsilon

def choose(self, q_table, state, action_space):
    """Choose action based on epsilon greedy strategy."""
    if np.random.rand() < self.epsilon:
        action = int(action_space.sample())
    else:
        action = np.argmax(q_table[state])
    self.epsilon = max(self.epsilon * self.decay, self.min_epsilon)
    return action

def moving_average(interval, window_size):
    if window_size == 1:
        return interval
    window = np.ones(int(window_size)) / float(window_size)
    return np.convolve(interval, window, 'same')

