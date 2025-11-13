# Cluster 40

class MetricsManager(object):
    """
    Main class of the metrics module. Handles the parsing and execution of
    the metrics.
    """

    def __init__(self, args):
        """
        Initialization of the metrics manager. This creates the client, needed to parse
        the information from the recorder, extract the metrics class, and runs it
        """
        self._args = args
        recorder_str = self._get_recorder(self._args.log)
        criteria_dict = self._get_criteria(self._args.criteria)
        map_name = self._get_recorder_map(recorder_str)
        world = self._client.load_world(map_name)
        town_map = world.get_map()
        log = MetricsLog(recorder_str)
        metric_class = self._get_metric_class(self._args.metric)
        metric_class(town_map, log, criteria_dict)

    def _get_recorder(self, log):
        """
        Parses the log argument into readable information
        """
        self._client = carla.Client(self._args.host, self._args.port)
        recorder_file = '{}/{}'.format(os.getenv('SCENARIO_RUNNER_ROOT', './'), log)
        if recorder_file[-4:] != '.log':
            print('ERROR: The log argument has to point to a .log file')
            sys.exit(-1)
        if not os.path.exists(recorder_file):
            print('ERROR: The specified log file does not exist')
            sys.exit(-1)
        recorder_str = self._client.show_recorder_file_info(recorder_file, True)
        return recorder_str

    def _get_criteria(self, criteria_file):
        """
        Parses the criteria argument into a dictionary
        """
        if criteria_file:
            with open(criteria_file) as fd:
                criteria_dict = json.load(fd)
        else:
            criteria_dict = None
        return criteria_dict

    def _get_metric_class(self, metric_file):
        """
        Function to extract the metrics class from the path given by the metrics
        argument. Returns the first class found that is a child of BasicMetric

        Args:
            metric_file (str): path to the metric's file.
        """
        module_name = os.path.basename(metric_file).split('.')[0]
        sys.path.insert(0, os.path.dirname(metric_file))
        metric_module = importlib.import_module(module_name)
        for member in inspect.getmembers(metric_module, inspect.isclass):
            member_parent = member[1].__bases__[0]
            if 'BasicMetric' in str(member_parent):
                return member[1]
        print('No child class of BasicMetric was found ... Exiting')
        sys.exit(-1)

    def _get_recorder_map(self, recorder_str):
        """
        Returns the name of the map the simulation took place in
        """
        header = recorder_str.split('\n')
        sim_map = header[1][5:]
        return sim_map

def __init__(self, args):
    """
        Initialization of the metrics manager. This creates the client, needed to parse
        the information from the recorder, extract the metrics class, and runs it
        """
    self._args = args
    recorder_str = self._get_recorder(self._args.log)
    criteria_dict = self._get_criteria(self._args.criteria)
    map_name = self._get_recorder_map(recorder_str)
    world = self._client.load_world(map_name)
    town_map = world.get_map()
    log = MetricsLog(recorder_str)
    metric_class = self._get_metric_class(self._args.metric)
    metric_class(town_map, log, criteria_dict)

