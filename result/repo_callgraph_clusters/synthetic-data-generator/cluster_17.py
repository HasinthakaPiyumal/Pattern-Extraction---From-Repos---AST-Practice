# Cluster 17

class DataExporterManager(Manager):
    register_type = DataExporter
    project_name = PROJECT_NAME
    hookspecs_model = extension

    @property
    def registed_exporters(self):
        return self.registed_cls

    def load_all_local_model(self):
        self._load_dir(data_exporters)

    def init_exporter(self, exporter_name, **kwargs: dict[str, Any]) -> DataExporter:
        return self.init(exporter_name, **kwargs)

def load_all_local_model(self):
    self._load_dir(data_exporters)

class CacherManager(Manager):
    register_type = Cacher
    project_name = PROJECT_NAME
    hookspecs_model = extension

    @property
    def registed_cachers(self):
        """
        redirect to registed_cls
        """
        return self.registed_cls

    def load_all_local_model(self):
        """
        Load all local model. Currently only ``sdgx.cachers``.
        """
        self._load_dir(cachers)

    def init_cacher(self, cacher_name, **kwargs: dict[str, Any]) -> Cacher:
        """
        redirect to init
        """
        return self.init(cacher_name, **kwargs)

def load_all_local_model(self):
    """
        Load all local model. Currently only ``sdgx.cachers``.
        """
    self._load_dir(cachers)

class DataProcessorManager(Manager):
    """
    This is a plugin management class for data processing components.

    Properties:
        - register_type: Specifies the type of data processors to register.
        - project_name: Stores the project name from the extension module.
        - hookspecs_model: Stores the hook specifications model from the extension module.
        - preset_default_processors: Stores a list of default processor names in lowercase.
        - registed_data_processors: Property that returns the registered data processors.
        - registed_default_processor_list: Property that returns the registered default data processors.

    Methods:
        - load_all_local_model: Loads all local models for formatters, generators, samplers, and transformers.
        - init_data_processor: Initializes a data processor with the given name and keyword arguments.
        - init_all_processors: Initializes all registered data processors with optional keyword arguments.
        - init_default_processors: Initializes default processors that are both registered and preset.

    """
    register_type = DataProcessor
    '\n    Specifies the type of data processors to register.'
    project_name = PROJECT_NAME
    '\n    Stores the project name from the extension module.\n    '
    hookspecs_model = extension
    '\n    The hook specifications model from the extension module.\n    '
    preset_defalut_processors = [p.lower() for p in ['SpecificCombinationTransformer', 'FixedCombinationTransformer', 'NonValueTransformer', 'OutlierTransformer', 'EmailGenerator', 'ChnPiiGenerator', 'IntValueFormatter', 'DatetimeFormatter']] + ['ConstValueTransformer'.lower(), 'PositiveNegativeFilter'.lower(), 'EmptyTransformer'.lower(), 'ColumnOrderTransformer'.lower()]
    '\n    preset_defalut_processors list stores the lowercase names of the transformers loaded by default. When using the synthesizer, they will be loaded by default to facilitate user operations.\n\n    Keep ColumnOrderTransformer always at the last one.\n    '

    @property
    def registed_data_processors(self):
        """
        This property returns all registered data processors
        """
        return self.registed_cls

    @property
    def registed_default_processor_list(self):
        """
        This property returns all registered default data processors
        """
        registed_processor_list = self.registed_data_processors.keys()
        default_processors = []
        for each_processor in self.preset_defalut_processors:
            if each_processor in registed_processor_list:
                default_processors.append(each_processor)
        return default_processors

    def load_all_local_model(self):
        """
        loads all local models
        """
        self._load_dir(data_processors.formatters)
        self._load_dir(data_processors.generators)
        self._load_dir(data_processors.samplers)
        self._load_dir(data_processors.transformers)
        self._load_dir(data_processors.filter)

    def init_data_processor(self, processor_name, **kwargs: dict[str, Any]) -> DataProcessor:
        """
        Initializes a data processor with the given name and parameters
        """
        return self.init(processor_name, **kwargs)

    def init_all_processors(self, **kwargs: Any) -> list[DataProcessor]:
        """
        Initializes all registered data processors
        """
        return [self.init(processor_name, **kwargs) for processor_name in self.registed_data_processors.keys()]

    def init_default_processors(self, **kwargs: Any) -> list[DataProcessor]:
        """
        Initializes all default data processors
        """
        return [self.init(processor_name, **kwargs) for processor_name in self.registed_default_processor_list]

def load_all_local_model(self):
    """
        loads all local models
        """
    self._load_dir(data_processors.formatters)
    self._load_dir(data_processors.generators)
    self._load_dir(data_processors.samplers)
    self._load_dir(data_processors.transformers)
    self._load_dir(data_processors.filter)

class InspectorManager(Manager):
    register_type = Inspector
    project_name = PROJECT_NAME
    hookspecs_model = extension

    @property
    def registed_inspectors(self):
        return self.registed_cls

    def load_all_local_model(self):
        self._load_dir(inspectors)

    def init_all_inspectors(self, **kwargs: Any) -> list[Inspector]:
        return [self.init(inspector_name, **kwargs) for inspector_name in self.registed_inspectors.keys()]

    def init_inspcetors(self, includes: Iterable[str] | None=None, excludes: Iterable[str] | None=None, **kwargs: Any) -> list[Inspector]:
        includes = includes or self.registed_inspectors.keys()
        if excludes:
            includes = list(set(includes) - set(excludes))
        return [self.init(inspector_name, **kwargs) for inspector_name in includes]

def load_all_local_model(self):
    self._load_dir(inspectors)

class ModelManager(Manager):
    register_type = SynthesizerModel
    project_name = PROJECT_NAME
    hookspecs_model = extension

    @property
    def registed_models(self):
        """
        redirect to registed_cls
        """
        return self.registed_cls

    def load_all_local_model(self):
        self._load_dir(ml.single_table)
        self._load_dir(ml.multi_tables)
        self._load_dir(statistics.single_table)
        self._load_dir(statistics.multi_tables)

    def init_model(self, model_name, **kwargs: dict[str, Any]) -> SynthesizerModel:
        """
        redirect to init
        """
        return self.init(model_name, **kwargs)

    def load(self, model: type[SynthesizerModel] | str, model_path, **kwargs) -> SynthesizerModel:
        if not (isinstance(model, type) or isinstance(model, str)):
            raise ManagerLoadModelError('model must be type of SynthesizerModel or str for model_name')
        if isinstance(model, str):
            model = self._normalize_name(model)
        if isinstance(model, str) and model not in self.registed_models:
            raise ManagerLoadModelError(f'{model} is not registered.')
        model = model if isinstance(model, type) else self.registed_models[model]
        try:
            return model.load(model_path, **kwargs)
        except Exception as e:
            raise ManagerLoadModelError(e)

def load_all_local_model(self):
    self._load_dir(ml.single_table)
    self._load_dir(ml.multi_tables)
    self._load_dir(statistics.single_table)
    self._load_dir(statistics.multi_tables)

class DataConnectorManager(Manager):
    register_type = DataConnector
    project_name = PROJECT_NAME
    hookspecs_model = extension

    @property
    def registed_data_connectors(self):
        return self.registed_cls

    def load_all_local_model(self):
        self._load_dir(data_connectors)

    def init_data_connector(self, connector_name, **kwargs: dict[str, Any]) -> DataConnector:
        return self.init(connector_name, **kwargs)

def load_all_local_model(self):
    self._load_dir(data_connectors)

