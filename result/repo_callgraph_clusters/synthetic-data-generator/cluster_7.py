# Cluster 7

def get_demo_single_table(data_dir: str | Path='./dataset'):
    """
    Get demo single table as DataFrame and discrete columns names

    Args:
        data_dir(str | Path): data directory

    Returns:

        pd.DataFrame: demo single table
        list: discrete columns
    """
    demo_data_path = download_demo_data(data_dir)
    pd_obj = pd.read_csv(demo_data_path)
    discrete_cols = ['workclass', 'education', 'marital-status', 'occupation', 'relationship', 'race', 'gender', 'native-country', 'income']
    return (pd_obj, discrete_cols)

def get_demo_multi_table(data_dir: str | Path='./dataset', dataset_name='rossman') -> dict[str, pd.DataFrame]:
    """
    Get multi-table demo data as DataFrame and relationship

    Args:
        data_dir(str | Path): data directory

    Returns:
        dict[str, pd.DataFrame]: multi-table data dict, the key is table name, value is DataFrame.
    """
    multi_table_dict = {}
    demo_data_dict = download_multi_table_demo_data(data_dir, dataset_name)
    for table_name in demo_data_dict.keys():
        each_path = demo_data_dict[table_name]
        pd_obj = pd.read_csv(each_path)
        multi_table_dict[table_name] = pd_obj
    return multi_table_dict

class Univariate(object):
    """Univariate Distribution.

    Args:
        candidates (list[str or type or Univariate]):
            List of candidates to select the best univariate from.
            It can be a list of strings representing Univariate FQNs,
            or a list of Univariate subclasses or a list of instances.
        parametric (ParametricType):
            If not ``None``, only select subclasses of this type.
            Ignored if ``candidates`` is passed.
        bounded (BoundedType):
            If not ``None``, only select subclasses of this type.
            Ignored if ``candidates`` is passed.
        random_state (int or np.random.RandomState):
            Random seed or RandomState to use.
        selection_sample_size (int):
            Size of the subsample to use for candidate selection.
            If ``None``, all the data is used.
    """
    PARAMETRIC = ParametricType.NON_PARAMETRIC
    BOUNDED = BoundedType.UNBOUNDED
    fitted = False
    _constant_value = None
    _instance = None

    @classmethod
    def _select_candidates(cls, parametric=None, bounded=None):
        """Select which subclasses fulfill the specified constriants.

        Args:
            parametric (ParametricType):
                If not ``None``, only select subclasses of this type.
            bounded (BoundedType):
                If not ``None``, only select subclasses of this type.

        Returns:
            list:
                Selected subclasses.
        """
        candidates = []
        for subclass in cls.__subclasses__():
            candidates.extend(subclass._select_candidates(parametric, bounded))
            if ABC in subclass.__bases__:
                continue
            if parametric is not None and subclass.PARAMETRIC != parametric:
                continue
            if bounded is not None and subclass.BOUNDED != bounded:
                continue
            candidates.append(subclass)
        return candidates

    @store_args
    def __init__(self, candidates=None, parametric=None, bounded=None, random_state=None, selection_sample_size=None):
        self.candidates = candidates or self._select_candidates(parametric, bounded)
        self.random_state = validate_random_state(random_state)
        self.selection_sample_size = selection_sample_size

    @classmethod
    def __repr__(cls):
        """Return class name."""
        return cls.__name__

    def check_fit(self):
        """Check whether this model has already been fit to a random variable.

        Raise a ``NotFittedError`` if it has not.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        if not self.fitted:
            raise NotFittedError('This model is not fitted.')

    def _constant_sample(self, num_samples):
        """Sample values for a constant distribution.

        Args:
            num_samples (int):
                Number of rows to sample

        Returns:
            numpy.ndarray:
                Sampled values. Array of shape (num_samples,).
        """
        return np.full(num_samples, self._constant_value)

    def _constant_cumulative_distribution(self, X):
        """Cumulative distribution for the degenerate case of constant distribution.

        Note that the output of this method will be an array whose unique values are 0 and 1.
        More information can be found here: https://en.wikipedia.org/wiki/Degenerate_distribution

        Arguments:
            X (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Cumulative distribution values for points in X.
        """
        result = np.ones(X.shape)
        result[np.nonzero(X < self._constant_value)] = 0
        return result

    def _constant_probability_density(self, X):
        """Probability density for the degenerate case of constant distribution.

        Note that the output of this method will be an array whose unique values are 0 and 1.
        More information can be found here: https://en.wikipedia.org/wiki/Degenerate_distribution

        Arguments:
            X (numpy.ndarray):
                Values for which the probability density will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Probability density values for points in X.
        """
        result = np.zeros(X.shape)
        result[np.nonzero(X == self._constant_value)] = 1
        return result

    def _constant_percent_point(self, X):
        """Percent point for the degenerate case of constant distribution.

        Note that the output of this method will be an array whose unique values are `np.nan`
        and self._constant_value.
        More information can be found here: https://en.wikipedia.org/wiki/Degenerate_distribution

        Arguments:
            U (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1) and values must be in [0,1].

        Returns:
            numpy.ndarray:
                Inverse cumulative distribution values for points in U.
        """
        return np.full(X.shape, self._constant_value)

    def _replace_constant_methods(self):
        """Replace conventional distribution methods by its constant counterparts."""
        self.cumulative_distribution = self._constant_cumulative_distribution
        self.percent_point = self._constant_percent_point
        self.probability_density = self._constant_probability_density
        self.sample = self._constant_sample

    def _set_constant_value(self, constant_value):
        """Set the distribution up to behave as a degenerate distribution.

        The constant value is stored as ``self._constant_value`` and all
        the methods are replaced by their degenerate counterparts.

        Args:
            constant_value (float):
                Value to set as the constant one.
        """
        self._constant_value = constant_value
        self._replace_constant_methods()

    def _check_constant_value(self, X):
        """Check if a Series or array contains only one unique value.

        If it contains only one value, set the instance up to behave accordingly.

        Args:
            X (numpy.ndarray):
                Data to analyze.

        Returns:
            float:
                Whether the input data had only one value or not.
        """
        uniques = np.unique(X)
        if len(uniques) == 1:
            self._set_constant_value(uniques[0])
            return True
        return False

    def fit(self, X):
        """Fit the model to a random variable.

        Arguments:
            X (numpy.ndarray):
                Values of the random variable. It must have shape (n, 1).
        """
        if self.selection_sample_size and self.selection_sample_size < len(X):
            selection_sample = np.random.choice(X, size=self.selection_sample_size)
        else:
            selection_sample = X
        self._instance = select_univariate(selection_sample, self.candidates)
        self._instance.fit(X)
        self.fitted = True

    def probability_density(self, X):
        """Compute the probability density for each point in X.

        Arguments:
            X (numpy.ndarray):
                Values for which the probability density will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Probability density values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        return self._instance.probability_density(X)

    def log_probability_density(self, X):
        """Compute the log of the probability density for each point in X.

        It should be overridden with numerically stable variants whenever possible.

        Arguments:
            X (numpy.ndarray):
                Values for which the log probability density will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Log probability density values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        if self._instance:
            return self._instance.log_probability_density(X)
        return np.log(self.probability_density(X))

    def pdf(self, X):
        """Compute the probability density for each point in X.

        Arguments:
            X (numpy.ndarray):
                Values for which the probability density will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Probability density values for points in X.
        """
        return self.probability_density(X)

    def cumulative_distribution(self, X):
        """Compute the cumulative distribution value for each point in X.

        Arguments:
            X (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Cumulative distribution values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        return self._instance.cumulative_distribution(X)

    def cdf(self, X):
        """Compute the cumulative distribution value for each point in X.

        Arguments:
            X (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1).

        Returns:
            numpy.ndarray:
                Cumulative distribution values for points in X.
        """
        return self.cumulative_distribution(X)

    def percent_point(self, U):
        """Compute the inverse cumulative distribution value for each point in U.

        Arguments:
            U (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1) and values must be in [0,1].

        Returns:
            numpy.ndarray:
                Inverse cumulative distribution values for points in U.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        return self._instance.percent_point(U)

    def ppf(self, U):
        """Compute the inverse cumulative distribution value for each point in U.

        Arguments:
            U (numpy.ndarray):
                Values for which the cumulative distribution will be computed.
                It must have shape (n, 1) and values must be in [0,1].

        Returns:
            numpy.ndarray:
                Inverse cumulative distribution values for points in U.
        """
        return self.percent_point(U)

    def set_random_state(self, random_state):
        """Set the random state.

        Args:
            random_state (int, np.random.RandomState, or None):
                Seed or RandomState for the random generator.
        """
        self.random_state = validate_random_state(random_state)

    def sample(self, n_samples=1):
        """Sample values from this model.

        Argument:
            n_samples (int):
                Number of values to sample

        Returns:
            numpy.ndarray:
                Array of shape (n_samples, 1) with values randomly
                sampled from this model distribution.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        return self._instance.sample(n_samples)

    def _get_params(self):
        """Return attributes from self.model to serialize.

        Returns:
            dict:
                Parameters of the underlying distribution.
        """
        return self._instance._get_params()

    def _set_params(self, params):
        """Set the parameters of this univariate.

        Must be implemented in all the subclasses.

        Args:
            dict:
                Parameters to recreate this instance.
        """
        raise NotImplementedError()

    def to_dict(self):
        """Return the parameters of this model in a dict.

        Returns:
            dict:
                Dictionary containing the distribution type and all
                the parameters that define the distribution.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        params = self._get_params()
        if self.__class__ is Univariate:
            params['type'] = get_qualified_name(self._instance)
        else:
            params['type'] = get_qualified_name(self)
        return params

    @classmethod
    def from_dict(cls, params):
        """Build a distribution from its params dict.

        Args:
            params (dict):
                Dictionary containing the FQN of the distribution and the
                necessary parameters to rebuild it.
                The input format is exactly the same that is outputted by
                the distribution class ``to_dict`` method.

        Returns:
            Univariate:
                Distribution instance.
        """
        params = params.copy()
        distribution = get_instance(params.pop('type'))
        distribution._set_params(params)
        distribution.fitted = True
        return distribution

    def save(self, path):
        """Serialize this univariate instance using pickle.

        Args:
            path (str):
                Path to where this distribution will be serialized.
        """
        with open(path, 'wb') as pickle_file:
            pickle.dump(self, pickle_file)

    @classmethod
    def load(cls, path):
        """Load a Univariate instance from a pickle file.

        Args:
            path (str):
                Path to the pickle file where the distribution has been serialized.

        Returns:
            Univariate:
                Loaded instance.
        """
        with open(path, 'rb') as pickle_file:
            return pickle.load(pickle_file)

def _get_params(self):
    """Return attributes from self.model to serialize.

        Returns:
            dict:
                Parameters of the underlying distribution.
        """
    return self._instance._get_params()

def to_dict(self):
    """Return the parameters of this model in a dict.

        Returns:
            dict:
                Dictionary containing the distribution type and all
                the parameters that define the distribution.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
    self.check_fit()
    params = self._get_params()
    if self.__class__ is Univariate:
        params['type'] = get_qualified_name(self._instance)
    else:
        params['type'] = get_qualified_name(self)
    return params

class GaussianMultivariate(Multivariate):
    """Class for a multivariate distribution that uses the Gaussian copula.

    Args:
        distribution (str or dict):
            Fully qualified name of the class to be used for modeling the marginal
            distributions or a dictionary mapping column names to the fully qualified
            distribution names.
    """
    covariance = None
    columns = None
    univariates = None

    @store_args
    def __init__(self, distribution=DEFAULT_DISTRIBUTION, random_state=None):
        self.random_state = validate_random_state(random_state)
        self.distribution = distribution

    def __repr__(self):
        """Produce printable representation of the object."""
        if self.distribution == DEFAULT_DISTRIBUTION:
            distribution = ''
        elif isinstance(self.distribution, type):
            distribution = f'distribution="{self.distribution.__name__}"'
        else:
            distribution = f'distribution="{self.distribution}"'
        return f'GaussianMultivariate({distribution})'

    def _transform_to_normal(self, X):
        if isinstance(X, pd.Series):
            X = X.to_frame().T
        elif not isinstance(X, pd.DataFrame):
            if len(X.shape) == 1:
                X = [X]
            X = pd.DataFrame(X, columns=self.columns)
        U = []
        for column_name, univariate in zip(self.columns, self.univariates):
            if column_name in X:
                column = X[column_name]
                U.append(univariate.cdf(column.to_numpy()).clip(EPSILON, 1 - EPSILON))
        return stats.norm.ppf(np.column_stack(U))

    def _get_covariance(self, X):
        """Compute covariance matrix with transformed data.

        Args:
            X (numpy.ndarray):
                Data for which the covariance needs to be computed.

        Returns:
            numpy.ndarray:
                computed covariance matrix.
        """
        result = self._transform_to_normal(X)
        covariance = pd.DataFrame(data=result).corr().to_numpy()
        covariance = np.nan_to_num(covariance, nan=0.0)
        if np.linalg.cond(covariance) > 1.0 / sys.float_info.epsilon:
            covariance = covariance + np.identity(covariance.shape[0]) * EPSILON
        return pd.DataFrame(covariance, index=self.columns, columns=self.columns)

    @check_valid_values
    def fit(self, X):
        """Compute the distribution for each variable and then its covariance matrix.

        Arguments:
            X (pandas.DataFrame):
                Values of the random variables.
        """
        LOGGER.info('Fitting %s', self)
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        columns = []
        univariates = []
        for column_name, column in X.items():
            if isinstance(self.distribution, dict):
                distribution = self.distribution.get(column_name, DEFAULT_DISTRIBUTION)
            else:
                distribution = self.distribution
            LOGGER.debug('Fitting column %s to %s', column_name, distribution)
            univariate = get_instance(distribution)
            try:
                univariate.fit(column)
            except BaseException:
                warning_message = f'Unable to fit to a {distribution} distribution for column {column_name}. Using a Gaussian distribution instead.'
                warnings.warn(warning_message)
                univariate = GaussianUnivariate()
                univariate.fit(column)
            columns.append(column_name)
            univariates.append(univariate)
        self.columns = columns
        self.univariates = univariates
        LOGGER.debug('Computing covariance')
        self.covariance = self._get_covariance(X)
        self.fitted = True
        LOGGER.debug('GaussianMultivariate fitted successfully')

    def probability_density(self, X):
        """Compute the probability density for each point in X.

        Arguments:
            X (pandas.DataFrame):
                Values for which the probability density will be computed.

        Returns:
            numpy.ndarray:
                Probability density values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        transformed = self._transform_to_normal(X)
        return stats.multivariate_normal.pdf(transformed, cov=self.covariance)

    def cumulative_distribution(self, X):
        """Compute the cumulative distribution value for each point in X.

        Arguments:
            X (pandas.DataFrame):
                Values for which the cumulative distribution will be computed.

        Returns:
            numpy.ndarray:
                Cumulative distribution values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        transformed = self._transform_to_normal(X)
        return stats.multivariate_normal.cdf(transformed, cov=self.covariance)

    def _get_conditional_distribution(self, conditions):
        """Compute the parameters of a conditional multivariate normal distribution.

        The parameters of the conditioned distribution are computed as specified here:
        https://en.wikipedia.org/wiki/Multivariate_normal_distribution#Conditional_distributions

        Args:
            conditions (pandas.Series):
                Mapping of the column names and column values to condition on.
                The input values have already been transformed to their normal distribution.

        Returns:
            tuple:
                * means (numpy.array):
                    mean values to use for the conditioned multivariate normal.
                * covariance (numpy.array):
                    covariance matrix to use for the conditioned
                  multivariate normal.
                * columns (list):
                    names of the columns that will be sampled conditionally.
        """
        columns2 = conditions.index
        columns1 = self.covariance.columns.difference(columns2)
        sigma11 = self.covariance.loc[columns1, columns1].to_numpy()
        sigma12 = self.covariance.loc[columns1, columns2].to_numpy()
        sigma21 = self.covariance.loc[columns2, columns1].to_numpy()
        sigma22 = self.covariance.loc[columns2, columns2].to_numpy()
        mu1 = np.zeros(len(columns1))
        mu2 = np.zeros(len(columns2))
        sigma12sigma22inv = sigma12 @ np.linalg.inv(sigma22)
        mu_bar = mu1 + sigma12sigma22inv @ (conditions - mu2)
        sigma_bar = sigma11 - sigma12sigma22inv @ sigma21
        return (mu_bar, sigma_bar, columns1)

    def _get_normal_samples(self, num_rows, conditions):
        """Get random rows in the standard normal space.

        If no conditions are given, the values are sampled from a standard normal
        multivariate.

        If conditions are given, they are transformed to their equivalent standard
        normal values using their marginals and then the values are sampled from
        a standard normal multivariate conditioned on the given condition values.
        """
        if conditions is None:
            covariance = self.covariance
            columns = self.columns
            means = np.zeros(len(columns))
        else:
            conditions = pd.Series(conditions)
            normal_conditions = self._transform_to_normal(conditions)[0]
            normal_conditions = pd.Series(normal_conditions, index=conditions.index)
            means, covariance, columns = self._get_conditional_distribution(normal_conditions)
        samples = np.random.multivariate_normal(means, covariance, size=num_rows)
        return pd.DataFrame(samples, columns=columns)

    @random_state
    def sample(self, num_rows=1, conditions=None):
        """Sample values from this model.

        Argument:
            num_rows (int):
                Number of rows to sample.
            conditions (dict or pd.Series):
                Mapping of the column names and column values to condition on.

        Returns:
            numpy.ndarray:
                Array of shape (n_samples, *) with values randomly
                sampled from this model distribution. If conditions have been
                given, the output array also contains the corresponding columns
                populated with the given values.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        samples = self._get_normal_samples(num_rows, conditions)
        output = {}
        for column_name, univariate in zip(self.columns, self.univariates):
            if conditions and column_name in conditions:
                output[column_name] = np.full(num_rows, conditions[column_name])
            else:
                cdf = stats.norm.cdf(samples[column_name])
                output[column_name] = univariate.percent_point(cdf)
        return pd.DataFrame(data=output)

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this object.

        Returns:
            dict:
                Parameters of this distribution.
        """
        self.check_fit()
        univariates = [univariate.to_dict() for univariate in self.univariates]
        warnings.warn('`covariance` will be renamed to `correlation` in v0.4.0', DeprecationWarning)
        return {'covariance': self.covariance.to_numpy().tolist(), 'univariates': univariates, 'columns': self.columns, 'type': get_qualified_name(self)}

    @classmethod
    def from_dict(cls, copula_dict):
        """Create a new instance from a parameters dictionary.

        Args:
            params (dict):
                Parameters of the distribution, in the same format as the one
                returned by the ``to_dict`` method.

        Returns:
            Multivariate:
                Instance of the distribution defined on the parameters.
        """
        instance = cls()
        instance.univariates = []
        columns = copula_dict['columns']
        instance.columns = columns
        for parameters in copula_dict['univariates']:
            instance.univariates.append(Univariate.from_dict(parameters))
        covariance = copula_dict['covariance']
        instance.covariance = pd.DataFrame(covariance, index=columns, columns=columns)
        instance.fitted = True
        warnings.warn('`covariance` will be renamed to `correlation` in v0.4.0', DeprecationWarning)
        return instance

def to_dict(self):
    """Return a `dict` with the parameters to replicate this object.

        Returns:
            dict:
                Parameters of this distribution.
        """
    self.check_fit()
    univariates = [univariate.to_dict() for univariate in self.univariates]
    warnings.warn('`covariance` will be renamed to `correlation` in v0.4.0', DeprecationWarning)
    return {'covariance': self.covariance.to_numpy().tolist(), 'univariates': univariates, 'columns': self.columns, 'type': get_qualified_name(self)}

class Tree(Multivariate):
    """Helper class to instantiate a single tree in the vine model."""
    tree_type = None
    fitted = False

    def fit(self, index, n_nodes, tau_matrix, previous_tree, edges=None):
        """Fit this tree object.

        Args:
            index (int):
                index of the tree.
            n_nodes (int):
                number of nodes in the tree.
            tau_matrix (numpy.array):
                kendall's tau matrix of the data, shape (n_nodes, n_nodes).
            previous_tree (Tree):
                tree object of previous level.
        """
        self.level = index + 1
        self.n_nodes = n_nodes
        self.tau_matrix = tau_matrix
        self.previous_tree = previous_tree
        self.edges = edges or []
        if not self.edges:
            if self.level == 1:
                self.u_matrix = previous_tree
                self._build_first_tree()
            else:
                self._build_kth_tree()
            self.prepare_next_tree()
        self.fitted = True

    def _check_constraint(self, edge1, edge2):
        """Check if two edges satisfy vine constraint.

        Args:
            edge1 (Edge):
                edge object representing edge1
            edge2 (Edge):
                edge object representing edge2

        Returns:
            bool:
                True if the two edges satisfy vine constraints
        """
        full_node = {edge1.L, edge1.R, edge2.L, edge2.R}
        full_node.update(edge1.D)
        full_node.update(edge2.D)
        return len(full_node) == self.level + 1

    def _get_constraints(self):
        """Get neighboring edges for each edge in the edges."""
        num_edges = len(self.edges)
        for k in range(num_edges):
            for i in range(num_edges):
                if k != i and self.edges[k].is_adjacent(self.edges[i]):
                    self.edges[k].neighbors.append(i)

    def _sort_tau_by_y(self, y):
        """Sort tau matrix by dependece with variable y.

        Args:
            y (int):
                index of variable of intrest

        Returns:
            numpy.ndarray:
                sorted tau matrix.
        """
        tau_y = self.tau_matrix[:, y]
        tau_y[y] = np.NaN
        temp = np.empty([self.n_nodes, 3])
        temp[:, 0] = np.arange(self.n_nodes)
        temp[:, 1] = tau_y
        temp[:, 2] = abs(tau_y)
        temp[np.isnan(temp)] = -10
        sort_temp = temp[:, 2].argsort()[::-1]
        tau_sorted = temp[sort_temp]
        return tau_sorted

    def get_tau_matrix(self):
        """Get tau matrix for adjacent pairs.

        Returns:
            tau (numpy.ndarray):
                tau matrix for the current tree
        """
        num_edges = len(self.edges)
        tau = np.empty([num_edges, num_edges])
        for i in range(num_edges):
            edge = self.edges[i]
            for j in edge.neighbors:
                if self.level == 1:
                    left_u = self.u_matrix[:, edge.L]
                    right_u = self.u_matrix[:, edge.R]
                else:
                    left_parent, right_parent = edge.parents
                    left_u, right_u = Edge.get_conditional_uni(left_parent, right_parent)
                tau[i, j], pvalue = scipy.stats.kendalltau(left_u, right_u)
        return tau

    def get_adjacent_matrix(self):
        """Get adjacency matrix.

        Returns:
            numpy.ndarray:
                adjacency matrix
        """
        edges = self.edges
        num_edges = len(edges) + 1
        adj = np.zeros([num_edges, num_edges])
        for k in range(num_edges - 1):
            adj[edges[k].L, edges[k].R] = 1
            adj[edges[k].R, edges[k].L] = 1
        return adj

    def prepare_next_tree(self):
        """Prepare conditional U matrix for next tree."""
        for edge in self.edges:
            copula_theta = edge.theta
            if self.level == 1:
                left_u = self.u_matrix[:, edge.L]
                right_u = self.u_matrix[:, edge.R]
            else:
                left_parent, right_parent = edge.parents
                left_u, right_u = Edge.get_conditional_uni(left_parent, right_parent)
            left_u = [x for x in left_u if x is not None]
            right_u = [x for x in right_u if x is not None]
            X_left_right = np.array([[x, y] for x, y in zip(left_u, right_u)])
            X_right_left = np.array([[x, y] for x, y in zip(right_u, left_u)])
            copula = Bivariate(copula_type=edge.name)
            copula.theta = copula_theta
            left_given_right = copula.partial_derivative(X_left_right)
            right_given_left = copula.partial_derivative(X_right_left)
            left_given_right[left_given_right == 0] = EPSILON
            right_given_left[right_given_left == 0] = EPSILON
            left_given_right[left_given_right == 1] = 1 - EPSILON
            right_given_left[right_given_left == 1] = 1 - EPSILON
            edge.U = np.array([left_given_right, right_given_left])

    def get_likelihood(self, uni_matrix):
        """Compute likelihood of the tree given an U matrix.

        Args:
            uni_matrix (numpy.array):
                univariate matrix to evaluate likelihood on.

        Returns:
            tuple[float, numpy.array]:
                likelihood of the current tree, next level conditional univariate matrix
        """
        uni_dim = uni_matrix.shape[1]
        num_edge = len(self.edges)
        values = np.zeros([1, num_edge])
        new_uni_matrix = np.empty([uni_dim, uni_dim])
        for i in range(num_edge):
            edge = self.edges[i]
            value, left_u, right_u = edge.get_likelihood(uni_matrix)
            new_uni_matrix[edge.L, edge.R] = left_u
            new_uni_matrix[edge.R, edge.L] = right_u
            values[0, i] = np.log(value)
        return (np.sum(values), new_uni_matrix)

    def __str__(self):
        """Produce printable representation of the class."""
        template = 'L:{} R:{} D:{} Copula:{} Theta:{}'
        return '\n'.join([template.format(edge.L, edge.R, edge.D, edge.name, edge.theta) for edge in self.edges])

    def _serialize_previous_tree(self):
        if self.level == 1:
            return self.previous_tree.tolist()
        return None

    @classmethod
    def _deserialize_previous_tree(cls, tree_dict, previous):
        if tree_dict['level'] == 1:
            return np.array(tree_dict['previous_tree'])
        return previous

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this Tree.

        Returns:
            dict:
                Parameters of this Tree.
        """
        fitted = self.fitted
        result = {'tree_type': self.tree_type, 'type': get_qualified_name(self), 'fitted': fitted}
        if not fitted:
            return result
        result.update({'level': self.level, 'n_nodes': self.n_nodes, 'tau_matrix': self.tau_matrix.tolist(), 'previous_tree': self._serialize_previous_tree(), 'edges': [edge.to_dict() for edge in self.edges]})
        return result

    @classmethod
    def from_dict(cls, tree_dict, previous=None):
        """Create a new instance from a parameters dictionary.

        Args:
            params (dict):
                Parameters of the Tree, in the same format as the one
                returned by the ``to_dict`` method.

        Returns:
            Tree:
                Instance of the tree defined on the parameters.
        """
        instance = get_tree(tree_dict['tree_type'])
        fitted = tree_dict['fitted']
        instance.fitted = fitted
        if fitted:
            instance.level = tree_dict['level']
            instance.n_nodes = tree_dict['n_nodes']
            instance.tau_matrix = np.array(tree_dict['tau_matrix'])
            instance.previous_tree = cls._deserialize_previous_tree(tree_dict, previous)
            instance.edges = [Edge.from_dict(edge) for edge in tree_dict['edges']]
        return instance

def _serialize_previous_tree(self):
    if self.level == 1:
        return self.previous_tree.tolist()
    return None

def to_dict(self):
    """Return a `dict` with the parameters to replicate this Tree.

        Returns:
            dict:
                Parameters of this Tree.
        """
    fitted = self.fitted
    result = {'tree_type': self.tree_type, 'type': get_qualified_name(self), 'fitted': fitted}
    if not fitted:
        return result
    result.update({'level': self.level, 'n_nodes': self.n_nodes, 'tau_matrix': self.tau_matrix.tolist(), 'previous_tree': self._serialize_previous_tree(), 'edges': [edge.to_dict() for edge in self.edges]})
    return result

class Edge(object):
    """Represents an edge in the copula."""

    def __init__(self, index, left, right, copula_name, copula_theta):
        """Initialize an Edge object.

        Args:
            left (int):
                left_node index (smaller)
            right (int):
                right_node index (larger)
            copula_name (str):
                name of the fitted copula class
            copula_theta (float):
                parameters of the fitted copula class
        """
        self.index = index
        self.L = left
        self.R = right
        self.D = set()
        self.parents = None
        self.neighbors = []
        self.name = copula_name
        self.theta = copula_theta
        self.tau = None
        self.U = None
        self.likelihood = None

    @staticmethod
    def _identify_eds_ing(first, second):
        """Find nodes connecting adjacent edges.

        Args:
            first (Edge):
                Edge object representing the first edge.
            second (Edge):
                Edge object representing the second edge.

        Returns:
            tuple[int, int, set[int]]:
                The first two values represent left and right node
                indicies of the new edge. The third value is the new dependence set.
        """
        A = {first.L, first.R}
        A.update(first.D)
        B = {second.L, second.R}
        B.update(second.D)
        depend_set = A & B
        left, right = sorted(A ^ B)
        return (left, right, depend_set)

    def is_adjacent(self, another_edge):
        """Check if two edges are adjacent.

        Args:
            another_edge (Edge):
                edge object of another edge

        Returns:
            bool:
                True if the two edges are adjacent.
        """
        return self.L == another_edge.L or self.L == another_edge.R or self.R == another_edge.L or (self.R == another_edge.R)

    @staticmethod
    def sort_edge(edges):
        """Sort iterable of edges first by left node indices then right.

        Args:
            edges (list[Edge]):
                List of edges to be sorted.

        Returns:
            list[Edge]:
                Sorted list by left and right node indices.
        """
        return sorted(edges, key=lambda x: (x.L, x.R))

    @classmethod
    def get_conditional_uni(cls, left_parent, right_parent):
        """Identify pair univariate value from parents.

        Args:
            left_parent (Edge):
                left parent
            right_parent (Edge):
                right parent

        Returns:
            tuple[np.ndarray, np.ndarray]:
                left and right parents univariate.
        """
        left, right, _ = cls._identify_eds_ing(left_parent, right_parent)
        left_u = left_parent.U[0] if left_parent.L == left else left_parent.U[1]
        right_u = right_parent.U[0] if right_parent.L == right else right_parent.U[1]
        return (left_u, right_u)

    @classmethod
    def get_child_edge(cls, index, left_parent, right_parent):
        """Construct a child edge from two parent edges.

        Args:
            index (int):
                Index of the new Edge.
            left_parent (Edge):
                Left parent
            right_parent (Edge):
                Right parent

        Returns:
            Edge:
                The new child edge.
        """
        [ed1, ed2, depend_set] = cls._identify_eds_ing(left_parent, right_parent)
        left_u, right_u = cls.get_conditional_uni(left_parent, right_parent)
        X = np.array([[x, y] for x, y in zip(left_u, right_u)])
        copula = Bivariate.select_copula(X)
        name, theta = (copula.copula_type, copula.theta)
        new_edge = Edge(index, ed1, ed2, name, theta)
        new_edge.D = depend_set
        new_edge.parents = [left_parent, right_parent]
        return new_edge

    def get_likelihood(self, uni_matrix):
        """Compute likelihood given a U matrix.

        Args:
            uni_matrix (numpy.array):
                Matrix to compute the likelihood.

        Return:
            tuple (np.ndarray, np.ndarray, np.array):
                likelihood and conditional values.
        """
        if self.parents is None:
            left_u = uni_matrix[:, self.L]
            right_u = uni_matrix[:, self.R]
        else:
            left_ing = list(self.D - self.parents[0].D)[0]
            right_ing = list(self.D - self.parents[1].D)[0]
            left_u = uni_matrix[self.L, left_ing]
            right_u = uni_matrix[self.R, right_ing]
        copula = Bivariate(copula_type=self.name)
        copula.theta = self.theta
        X_left_right = np.array([[left_u, right_u]])
        X_right_left = np.array([[right_u, left_u]])
        value = np.sum(copula.probability_density(X_left_right))
        left_given_right = copula.partial_derivative(X_left_right)
        right_given_left = copula.partial_derivative(X_right_left)
        return (value, left_given_right, right_given_left)

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this Edge.

        Returns:
            dict:
                Parameters of this Edge.
        """
        parents = None
        if self.parents:
            parents = [parent.to_dict() for parent in self.parents]
        U = None
        if self.U is not None:
            U = self.U.tolist()
        return {'index': self.index, 'L': self.L, 'R': self.R, 'D': self.D, 'parents': parents, 'neighbors': self.neighbors, 'name': self.name, 'theta': self.theta, 'tau': self.tau, 'U': U, 'likelihood': self.likelihood}

    @classmethod
    def from_dict(cls, edge_dict):
        """Create a new instance from a parameters dictionary.

        Args:
            params (dict):
                Parameters of the Edge, in the same format as the one
                returned by the ``to_dict`` method.

        Returns:
            Edge:
                Instance of the edge defined on the parameters.
        """
        instance = cls(edge_dict['index'], edge_dict['L'], edge_dict['R'], edge_dict['name'], edge_dict['theta'])
        instance.U = np.array(edge_dict['U'])
        parents = edge_dict['parents']
        if parents:
            instance.parents = []
            for parent in parents:
                edge = Edge.from_dict(parent)
                instance.parents.append(edge)
        regular_attributes = ['D', 'tau', 'likelihood', 'neighbors']
        for key in regular_attributes:
            setattr(instance, key, edge_dict[key])
        return instance

def to_dict(self):
    """Return a `dict` with the parameters to replicate this Edge.

        Returns:
            dict:
                Parameters of this Edge.
        """
    parents = None
    if self.parents:
        parents = [parent.to_dict() for parent in self.parents]
    U = None
    if self.U is not None:
        U = self.U.tolist()
    return {'index': self.index, 'L': self.L, 'R': self.R, 'D': self.D, 'parents': parents, 'neighbors': self.neighbors, 'name': self.name, 'theta': self.theta, 'tau': self.tau, 'U': U, 'likelihood': self.likelihood}

class VineCopula(Multivariate):
    """Vine copula model.

    A :math:`vine` is a graphical representation of one factorization of the n-variate probability
    distribution in terms of :math:`n(n − 1)/2` bivariate copulas by means of the chain rule.

    It consists of a sequence of levels and as many levels as variables. Each level consists of
    a tree (no isolated nodes and no loops) satisfying that if it has :math:`n` nodes there must
    be :math:`n − 1` edges.

    Each node in tree :math:`T_1` is a variable and edges are couplings of variables constructed
    with bivariate copulas.

    Each node in tree :math:`T_{k+1}` is a coupling in :math:`T_{k}`, expressed by the copula
    of the variables; while edges are couplings between two vertices that must have one variable
    in common, becoming a conditioning variable in the bivariate copula. Thus, every level has
    one node less than the former. Once all the trees are drawn, the factorization is the product
    of all the nodes.

    Args:
        vine_type (str):
            type of the vine copula, could be 'center','direct','regular'
        random_state (int or np.random.RandomState):
            Random seed or RandomState to use.


    Attributes:
        model (copulas.univariate.Univariate):
            Distribution to compute univariates.
        u_matrix (numpy.array):
            Univariates.
        n_sample (int):
            Number of samples.
        n_var (int):
            Number of variables.
        columns (pandas.Series):
            Names of the variables.
        tau_mat (numpy.array):
            Kendall correlation parameters for data.
        truncated (int):
            Max level used to build the vine.
        depth (int):
            Vine depth.
        trees (list[Tree]):
            List of trees used by this vine.
        ppfs (list[callable]):
            percent point functions from the univariates used by this vine.
    """

    @store_args
    def __init__(self, vine_type, random_state=None):
        if sys.version_info > (3, 8):
            warnings.warn('Vines have not been fully tested on Python 3.8 and might produce wrong results. Please use Python 3.5, 3.6 or 3.7')
        self.random_state = validate_random_state(random_state)
        self.vine_type = vine_type
        self.u_matrix = None
        self.model = GaussianKDE

    @classmethod
    def _deserialize_trees(cls, tree_list):
        previous = Tree.from_dict(tree_list[0])
        trees = [previous]
        for tree_dict in tree_list[1:]:
            tree = Tree.from_dict(tree_dict, previous)
            trees.append(tree)
            previous = tree
        return trees

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this Vine.

        Returns:
            dict:
                Parameters of this Vine.
        """
        result = {'type': get_qualified_name(self), 'vine_type': self.vine_type, 'fitted': self.fitted}
        if not self.fitted:
            return result
        result.update({'n_sample': self.n_sample, 'n_var': self.n_var, 'depth': self.depth, 'truncated': self.truncated, 'trees': [tree.to_dict() for tree in self.trees], 'tau_mat': self.tau_mat.tolist(), 'u_matrix': self.u_matrix.tolist(), 'unis': [distribution.to_dict() for distribution in self.unis], 'columns': self.columns})
        return result

    @classmethod
    def from_dict(cls, vine_dict):
        """Create a new instance from a parameters dictionary.

        Args:
            params (dict):
                Parameters of the Vine, in the same format as the one
                returned by the ``to_dict`` method.

        Returns:
            Vine:
                Instance of the Vine defined on the parameters.
        """
        instance = cls(vine_dict['vine_type'])
        fitted = vine_dict['fitted']
        if fitted:
            instance.fitted = fitted
            instance.n_sample = vine_dict['n_sample']
            instance.n_var = vine_dict['n_var']
            instance.truncated = vine_dict['truncated']
            instance.depth = vine_dict['depth']
            instance.trees = cls._deserialize_trees(vine_dict['trees'])
            instance.unis = [GaussianKDE.from_dict(uni) for uni in vine_dict['unis']]
            instance.ppfs = [uni.percent_point for uni in instance.unis]
            instance.columns = vine_dict['columns']
            instance.tau_mat = np.array(vine_dict['tau_mat'])
            instance.u_matrix = np.array(vine_dict['u_matrix'])
        return instance

    @check_valid_values
    def fit(self, X, truncated=3):
        """Fit a vine model to the data.

        1. Transform all the variables by means of their marginals.
        In other words, compute

        .. math:: u_i = F_i(x_i), i = 1, ..., n

        and compose the matrix :math:`u = u_1, ..., u_n,` where :math:`u_i` are their columns.

        Args:
            X (numpy.ndarray):
                Data to be fitted to.
            truncated (int):
                Max level to build the vine.
        """
        LOGGER.info('Fitting VineCopula("%s")', self.vine_type)
        self.n_sample, self.n_var = X.shape
        self.columns = X.columns
        self.tau_mat = X.corr(method='kendall').to_numpy()
        self.u_matrix = np.empty([self.n_sample, self.n_var])
        self.truncated = truncated
        self.depth = self.n_var - 1
        self.trees = []
        self.unis, self.ppfs = ([], [])
        for i, col in enumerate(X):
            uni = self.model()
            uni.fit(X[col])
            self.u_matrix[:, i] = uni.cumulative_distribution(X[col])
            self.unis.append(uni)
            self.ppfs.append(uni.percent_point)
        self.train_vine(self.vine_type)
        self.fitted = True

    def train_vine(self, tree_type):
        """Build the vine.

        1. For the construction of the first tree :math:`T_1`, assign one node to each variable
           and then couple them by maximizing the measure of association considered.
           Different vines impose different constraints on this construction. When those are
           applied different trees are achieved at this level.

        2. Select the copula that best fits to the pair of variables coupled by each edge in
           :math:`T_1`.

        3. Let :math:`C_{ij}(u_i , u_j )` be the copula for a given edge :math:`(u_i, u_j)`
           in :math:`T_1`. Then for every edge in :math:`T_1`, compute either

           .. math:: {v^1}_{j|i} = \\\\frac{\\\\partial C_{ij}(u_i, u_j)}{\\\\partial u_j}

           or similarly :math:`{v^1}_{i|j}`, which are conditional cdfs. When finished with
           all the edges, construct the new matrix with :math:`v^1` that has one less column u.

        4. Set k = 2.

        5. Assign one node of :math:`T_k` to each edge of :math:`T_ {k−1}`. The structure of
           :math:`T_{k−1}` imposes a set of constraints on which edges of :math:`T_k` are
           realizable. Hence the next step is to get a linked list of the accesible nodes for
           every node in :math:`T_k`.

        6. As in step 1, nodes of :math:`T_k` are coupled maximizing the measure of association
           considered and satisfying the constraints impose by the kind of vine employed plus the
           set of constraints imposed by tree :math:`T_{k−1}`.

        7. Select the copula that best fit to each edge created in :math:`T_k`.

        8. Recompute matrix :math:`v_k` as in step 4, but taking :math:`T_k` and :math:`vk−1`
           instead of :math:`T_1` and u.

        9. Set :math:`k = k + 1` and repeat from (5) until all the trees are constructed.

        Args:
            tree_type (str or TreeTypes):
                Type of trees to use.
        """
        LOGGER.debug('start building tree : 0')
        tree_1 = get_tree(tree_type)
        tree_1.fit(0, self.n_var, self.tau_mat, self.u_matrix)
        self.trees.append(tree_1)
        LOGGER.debug('finish building tree : 0')
        for k in range(1, min(self.n_var - 1, self.truncated)):
            self.trees[k - 1]._get_constraints()
            tau = self.trees[k - 1].get_tau_matrix()
            LOGGER.debug(f'start building tree: {k}')
            tree_k = get_tree(tree_type)
            tree_k.fit(k, self.n_var - k, tau, self.trees[k - 1])
            self.trees.append(tree_k)
            LOGGER.debug(f'finish building tree: {k}')

    def get_likelihood(self, uni_matrix):
        """Compute likelihood of the vine."""
        num_tree = len(self.trees)
        values = np.empty([1, num_tree])
        for i in range(num_tree):
            value, new_uni_matrix = self.trees[i].get_likelihood(uni_matrix)
            uni_matrix = new_uni_matrix
            values[0, i] = value
        return np.sum(values)

    def _sample_row(self):
        """Generate a single sampled row from vine model.

        Returns:
            numpy.ndarray
        """
        unis = np.random.uniform(0, 1, self.n_var)
        first_ind = np.random.randint(0, self.n_var)
        adj = self.trees[0].get_adjacent_matrix()
        visited = []
        explore = [first_ind]
        sampled = np.zeros(self.n_var)
        itr = 0
        while explore:
            current = explore.pop(0)
            adj_is_one = adj[current, :] == 1
            neighbors = np.where(adj_is_one)[0].tolist()
            if itr == 0:
                new_x = self.ppfs[current](unis[current])
            else:
                for i in range(itr - 1, -1, -1):
                    current_ind = -1
                    if i >= self.truncated:
                        continue
                    current_tree = self.trees[i].edges
                    for edge in current_tree:
                        if i == 0:
                            if edge.L == current and edge.R == visited[0] or (edge.R == current and edge.L == visited[0]):
                                current_ind = edge.index
                                break
                        elif edge.L == current or edge.R == current:
                            condition = set(edge.D)
                            condition.add(edge.L)
                            condition.add(edge.R)
                            visit_set = set(visited)
                            visit_set.add(current)
                            if condition.issubset(visit_set):
                                current_ind = edge.index
                            break
                    if current_ind != -1:
                        copula_type = current_tree[current_ind].name
                        copula = Bivariate(copula_type=CopulaTypes(copula_type))
                        copula.theta = current_tree[current_ind].theta
                        U = np.array([unis[visited[0]]])
                        if i == itr - 1:
                            tmp = copula.percent_point(np.array([unis[current]]), U)[0]
                        else:
                            tmp = copula.percent_point(np.array([tmp]), U)[0]
                        tmp = min(max(tmp, EPSILON), 0.99)
                new_x = self.ppfs[current](np.array([tmp]))
            sampled[current] = new_x
            for s in neighbors:
                if s not in visited:
                    explore.insert(0, s)
            itr += 1
            visited.insert(0, current)
        return sampled

    @random_state
    def sample(self, num_rows):
        """Sample new rows.

        Args:
            num_rows (int):
                Number of rows to sample

        Returns:
            pandas.DataFrame:
                sampled rows.
        """
        sampled_values = []
        for i in range(num_rows):
            sampled_values.append(self._sample_row())
        return pd.DataFrame(sampled_values, columns=self.columns)

def to_dict(self):
    """Return a `dict` with the parameters to replicate this Vine.

        Returns:
            dict:
                Parameters of this Vine.
        """
    result = {'type': get_qualified_name(self), 'vine_type': self.vine_type, 'fitted': self.fitted}
    if not self.fitted:
        return result
    result.update({'n_sample': self.n_sample, 'n_var': self.n_var, 'depth': self.depth, 'truncated': self.truncated, 'trees': [tree.to_dict() for tree in self.trees], 'tau_mat': self.tau_mat.tolist(), 'u_matrix': self.u_matrix.tolist(), 'unis': [distribution.to_dict() for distribution in self.unis], 'columns': self.columns})
    return result

def load_demo():
    """Load the demo."""
    return pd.read_csv(DEMO_URL, compression='gzip')

class GaussianMultivariate(Multivariate):
    """Class for a multivariate distribution that uses the Gaussian copula.

    Args:
        distribution (str or dict):
            Fully qualified name of the class to be used for modeling the marginal
            distributions or a dictionary mapping column names to the fully qualified
            distribution names.
    """
    correlation = None
    columns = None
    univariates = None

    @store_args
    def __init__(self, distribution=DEFAULT_DISTRIBUTION, random_state=None):
        self.random_state = validate_random_state(random_state)
        self.distribution = distribution

    def __repr__(self):
        """Produce printable representation of the object."""
        if self.distribution == DEFAULT_DISTRIBUTION:
            distribution = ''
        elif isinstance(self.distribution, type):
            distribution = f'distribution="{self.distribution.__name__}"'
        else:
            distribution = f'distribution="{self.distribution}"'
        return f'GaussianMultivariate({distribution})'

    def _transform_to_normal(self, X):
        if isinstance(X, pd.Series):
            X = X.to_frame().T
        elif not isinstance(X, pd.DataFrame):
            if len(X.shape) == 1:
                X = [X]
            X = pd.DataFrame(X, columns=self.columns)
        U = []
        for column_name, univariate in zip(self.columns, self.univariates):
            if column_name in X:
                column = X[column_name]
                U.append(univariate.cdf(column.to_numpy()).clip(EPSILON, 1 - EPSILON))
        return stats.norm.ppf(np.column_stack(U))

    def _get_correlation(self, X):
        """Compute correlation matrix with transformed data.

        Args:
            X (numpy.ndarray):
                Data for which the correlation needs to be computed.

        Returns:
            numpy.ndarray:
                computed correlation matrix.
        """
        result = self._transform_to_normal(X)
        correlation = pd.DataFrame(data=result).corr().to_numpy()
        correlation = np.nan_to_num(correlation, nan=0.0)
        if np.linalg.cond(correlation) > 1.0 / sys.float_info.epsilon:
            correlation = correlation + np.identity(correlation.shape[0]) * EPSILON
        return pd.DataFrame(correlation, index=self.columns, columns=self.columns)

    @check_valid_values
    def fit(self, X):
        """Compute the distribution for each variable and then its correlation matrix.

        Arguments:
            X (pandas.DataFrame):
                Values of the random variables.
        """
        LOGGER.info('Fitting %s', self)
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)
        columns = []
        univariates = []
        for column_name, column in X.items():
            if isinstance(self.distribution, dict):
                distribution = self.distribution.get(column_name, DEFAULT_DISTRIBUTION)
            else:
                distribution = self.distribution
            LOGGER.debug('Fitting column %s to %s', column_name, distribution)
            univariate = get_instance(distribution)
            try:
                univariate.fit(column)
            except BaseException:
                warning_message = f'Unable to fit to a {distribution} distribution for column {column_name}. Using a Gaussian distribution instead.'
                warnings.warn(warning_message)
                univariate = GaussianUnivariate()
                univariate.fit(column)
            columns.append(column_name)
            univariates.append(univariate)
        self.columns = columns
        self.univariates = univariates
        LOGGER.debug('Computing correlation')
        self.correlation = self._get_correlation(X)
        self.fitted = True
        LOGGER.debug('GaussianMultivariate fitted successfully')

    def probability_density(self, X):
        """Compute the probability density for each point in X.

        Arguments:
            X (pandas.DataFrame):
                Values for which the probability density will be computed.

        Returns:
            numpy.ndarray:
                Probability density values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        transformed = self._transform_to_normal(X)
        return stats.multivariate_normal.pdf(transformed, cov=self.correlation)

    def cumulative_distribution(self, X):
        """Compute the cumulative distribution value for each point in X.

        Arguments:
            X (pandas.DataFrame):
                Values for which the cumulative distribution will be computed.

        Returns:
            numpy.ndarray:
                Cumulative distribution values for points in X.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        transformed = self._transform_to_normal(X)
        return stats.multivariate_normal.cdf(transformed, cov=self.correlation)

    def _get_conditional_distribution(self, conditions):
        """Compute the parameters of a conditional multivariate normal distribution.

        The parameters of the conditioned distribution are computed as specified here:
        https://en.wikipedia.org/wiki/Multivariate_normal_distribution#Conditional_distributions

        Args:
            conditions (pandas.Series):
                Mapping of the column names and column values to condition on.
                The input values have already been transformed to their normal distribution.

        Returns:
            tuple:
                * means (numpy.array):
                    mean values to use for the conditioned multivariate normal.
                * covariance (numpy.array):
                    covariance matrix to use for the conditioned
                  multivariate normal.
                * columns (list):
                    names of the columns that will be sampled conditionally.
        """
        columns2 = conditions.index
        columns1 = self.correlation.columns.difference(columns2)
        sigma11 = self.correlation.loc[columns1, columns1].to_numpy()
        sigma12 = self.correlation.loc[columns1, columns2].to_numpy()
        sigma21 = self.correlation.loc[columns2, columns1].to_numpy()
        sigma22 = self.correlation.loc[columns2, columns2].to_numpy()
        mu1 = np.zeros(len(columns1))
        mu2 = np.zeros(len(columns2))
        sigma12sigma22inv = sigma12 @ np.linalg.inv(sigma22)
        mu_bar = mu1 + sigma12sigma22inv @ (conditions - mu2)
        sigma_bar = sigma11 - sigma12sigma22inv @ sigma21
        return (mu_bar, sigma_bar, columns1)

    def _get_normal_samples(self, num_rows, conditions):
        """Get random rows in the standard normal space.

        If no conditions are given, the values are sampled from a standard normal
        multivariate.

        If conditions are given, they are transformed to their equivalent standard
        normal values using their marginals and then the values are sampled from
        a standard normal multivariate conditioned on the given condition values.
        """
        if conditions is None:
            covariance = self.correlation
            columns = self.columns
            means = np.zeros(len(columns))
        else:
            conditions = pd.Series(conditions)
            normal_conditions = self._transform_to_normal(conditions)[0]
            normal_conditions = pd.Series(normal_conditions, index=conditions.index)
            means, covariance, columns = self._get_conditional_distribution(normal_conditions)
        samples = np.random.multivariate_normal(means, covariance, size=num_rows)
        return pd.DataFrame(samples, columns=columns)

    @random_state
    def sample(self, num_rows=1, conditions=None):
        """Sample values from this model.

        Argument:
            num_rows (int):
                Number of rows to sample.
            conditions (dict or pd.Series):
                Mapping of the column names and column values to condition on.

        Returns:
            numpy.ndarray:
                Array of shape (n_samples, *) with values randomly
                sampled from this model distribution. If conditions have been
                given, the output array also contains the corresponding columns
                populated with the given values.

        Raises:
            NotFittedError:
                if the model is not fitted.
        """
        self.check_fit()
        samples = self._get_normal_samples(num_rows, conditions)
        output = {}
        for column_name, univariate in zip(self.columns, self.univariates):
            if conditions and column_name in conditions:
                output[column_name] = np.full(num_rows, conditions[column_name])
            else:
                cdf = stats.norm.cdf(samples[column_name])
                output[column_name] = univariate.percent_point(cdf)
        return pd.DataFrame(data=output)

    def to_dict(self):
        """Return a `dict` with the parameters to replicate this object.

        Returns:
            dict:
                Parameters of this distribution.
        """
        self.check_fit()
        univariates = [univariate.to_dict() for univariate in self.univariates]
        return {'correlation': self.correlation.to_numpy().tolist(), 'univariates': univariates, 'columns': self.columns, 'type': get_qualified_name(self)}

    @classmethod
    def from_dict(cls, copula_dict):
        instance = cls()
        instance.univariates = []
        columns = copula_dict['columns']
        instance.columns = columns
        for parameters in copula_dict['univariates']:
            instance.univariates.append(Univariate.from_dict(parameters))
        correlation = copula_dict['correlation']
        instance.correlation = pd.DataFrame(correlation, index=columns, columns=columns)
        instance.fitted = True
        return instance

def to_dict(self):
    """Return a `dict` with the parameters to replicate this object.

        Returns:
            dict:
                Parameters of this distribution.
        """
    self.check_fit()
    univariates = [univariate.to_dict() for univariate in self.univariates]
    return {'correlation': self.correlation.to_numpy().tolist(), 'univariates': univariates, 'columns': self.columns, 'type': get_qualified_name(self)}

class DataConnector:
    """
    DataConnector warps data source into ``pd.DataFrame``.

    For different data source, implement a specific subclass.
    """
    identity = None
    '\n    Identity of data source, e.g. table name, hash of content\n    '

    def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None | None:
        """
        Subclass must implement this for reading data.

        See ``read`` for more details.
        """
        raise NotImplementedError

    def _columns(self) -> list[str]:
        """
        Subclass should implement this for reading columns if there is an efficient way for peaking columns.

        See ``column`` for more details.
        """
        raise NotImplementedError

    def _iter(self, offset: int=0, chunksize: int=0) -> Generator[pd.DataFrame, None, None]:
        """
        Subclass should implement this for reading data in chunk.

        See ``iter`` for more details.
        """
        raise NotImplementedError

    def iter(self, offset: int=0, chunksize: int=0) -> Generator[pd.DataFrame, None, None]:
        """
        Interface for reading data in chunk.

        Args:
            offset (int, optional): Offset for reading. Defaults to 0.
            chunksize (int, optional): Chunksize for reading. Defaults to 0.

        Returns:
            typing.Generator[pd.DataFrame, None, None]: Generator/Iterator for readed dataframe
        """
        return self._iter(offset, chunksize)

    def read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
        """
        Interface for reading data.

        Args:
            offset (int, optional): Offset for reading. Defaults to 0.
            limit (int, optional): Limit for reading. Defaults to None.
                None is for reading all data and 0 is for reading no data(only header).

        Returns:
            pd.DataFrame: Readed dataframe
        """
        return self._read(offset, limit)

    def columns(self) -> list[str]:
        """
        Interface for peaking columns.
        """
        try:
            return self._columns()
        except NotImplementedError:
            return self.read(0, 1).columns.tolist()

    def keys(self) -> list[str]:
        """
        Same as ``columns``.
        """
        return self.columns()

    def finalize(self):
        """
        Finalize the data connector.
        """
        pass

def read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
    """
        Interface for reading data.

        Args:
            offset (int, optional): Offset for reading. Defaults to 0.
            limit (int, optional): Limit for reading. Defaults to None.
                None is for reading all data and 0 is for reading no data(only header).

        Returns:
            pd.DataFrame: Readed dataframe
        """
    return self._read(offset, limit)

def columns(self) -> list[str]:
    """
        Interface for peaking columns.
        """
    try:
        return self._columns()
    except NotImplementedError:
        return self.read(0, 1).columns.tolist()

class DataFrameConnector(DataConnector):
    """
    Directly Wraps DataFrame into :ref:`DataConnector`, for small dataset can be loaded all in memory.

    Args:
        df (pd.DataFrame): DataFrame to be wrapped.

    Example:

        .. code-block:: python
            from sdgx.data_connectors.dataframe_connector import DataFrameConnector
            connector = DataFrameConnector(
                df=pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}),
            )
            df = connector.read()


    """

    def __init__(self, df: pd.DataFrame, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.df: pd.DataFrame = df

    def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
        length = self.df.shape[0]
        if offset >= length:
            return None
        limit = limit or length
        return self.df.iloc[offset:min(offset + limit, length)]

    def _columns(self) -> list[str]:
        return list(self.df.columns)

    def _iter(self, offset=0, chunksize=0) -> Generator[pd.DataFrame, None, None]:

        def generator() -> Generator[pd.DataFrame, None, None]:
            length = self.df.shape[0]
            if offset < length:
                current = offset
                while current < length:
                    yield self.df.iloc[current:min(current + chunksize, length)]
                    current += chunksize
        return generator()

def _iter(self, offset=0, chunksize=0) -> Generator[pd.DataFrame, None, None]:

    def generator() -> Generator[pd.DataFrame, None, None]:
        length = self.df.shape[0]
        if offset < length:
            current = offset
            while current < length:
                yield self.df.iloc[current:min(current + chunksize, length)]
                current += chunksize
    return generator()

class CsvConnector(DataConnector):
    """
    Wraps csv file into :ref:`DataConnector`

    Args:
        path (str): Path to csv file
        sep (str, optional): Separator. Defaults to ','.
        header (str, optional): Header. Defaults to 'infer'.
        read_csv_kwargs (dict, optional): kwargs for pd.read_csv, please refer to https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html

    Example:

        .. code-block:: python

            from sdgx.data_connectors.csv_connector import CsvConnector
            connector = CsvConnector(
                path="data.csv",
            )
            df = connector.read()


    """

    @cached_property
    def identity(self):
        """
        Identity of the data source is the sha256 of the file
        """
        with open(self.path, 'rb') as f:
            return f'csvfile-{hashlib.sha256(f.read()).hexdigest()}'

    def __init__(self, path, sep=',', header='infer', **read_csv_kwargs):
        self.path = path
        self.sep = sep
        self.header = header
        self.read_csv_kwargs = read_csv_kwargs

    def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
        return pd.read_csv(self.path, sep=self.sep, header=self.header, skiprows=range(1, offset + 1), nrows=limit, **self.read_csv_kwargs)

    def _columns(self) -> list[str]:
        d = pd.read_csv(self.path, sep=self.sep, header=self.header, nrows=0, **self.read_csv_kwargs).columns.tolist()
        return d

    def _iter(self, offset: int=0, chunksize: int=1000) -> Generator[pd.DataFrame, None, None]:
        if chunksize is None:
            yield self._read(offset=offset)
            return
        for d in pd.read_csv(self.path, sep=self.sep, header=self.header, skiprows=range(1, offset + 1), chunksize=chunksize, **self.read_csv_kwargs):
            yield d

def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
    return pd.read_csv(self.path, sep=self.sep, header=self.header, skiprows=range(1, offset + 1), nrows=limit, **self.read_csv_kwargs)

def _columns(self) -> list[str]:
    d = pd.read_csv(self.path, sep=self.sep, header=self.header, nrows=0, **self.read_csv_kwargs).columns.tolist()
    return d

def _iter(self, offset: int=0, chunksize: int=1000) -> Generator[pd.DataFrame, None, None]:
    if chunksize is None:
        yield self._read(offset=offset)
        return
    for d in pd.read_csv(self.path, sep=self.sep, header=self.header, skiprows=range(1, offset + 1), chunksize=chunksize, **self.read_csv_kwargs):
        yield d

class GeneratorConnector(DataConnector):
    """
    A virtual data connector that wrap
    `Generator <https://docs.python.org/3/glossary.html#term-generator>`_
    into a DataConnector.

    Passing ``offset=0`` to ``read`` will reset the generator.

    Warning:
        ``offset`` and ``limit`` are ignored as ``Generator`` not supporting random access.
        But we can use :ref:`Cacher` to support it. See :ref:`Data Loader` for more details.

    Note:
        This connector is not been registered by default.
        So only be used with the library way.
    """

    @cached_property
    def identity(self) -> str:
        return f'generator-{os.getpid()}-{id(self.generator_caller)}'

    def __init__(self, generator_caller: Callable[[], Generator[pd.DataFrame, None, None]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.generator_caller = generator_caller
        self._generator = self.generator_caller()

    def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
        """
        Ingore limit and allow sequential reading.
        """
        if offset == 0:
            self._generator = self.generator_caller()
        try:
            return next(self._generator)
        except StopIteration:
            return None

    def _columns(self) -> list[str]:
        for df in self._iter():
            return list(df.columns)

    def _iter(self, offset=0, chunksize=0) -> Generator[pd.DataFrame, None, None]:
        """
        Subclass should implement this for reading data in chunk.

        See ``iter`` for more details.
        """
        return self.generator_caller()

def _read(self, offset: int=0, limit: int | None=None) -> pd.DataFrame | None:
    """
        Ingore limit and allow sequential reading.
        """
    if offset == 0:
        self._generator = self.generator_caller()
    try:
        return next(self._generator)
    except StopIteration:
        return None

def _iter(self, offset=0, chunksize=0) -> Generator[pd.DataFrame, None, None]:
    """
        Subclass should implement this for reading data in chunk.

        See ``iter`` for more details.
        """
    return self.generator_caller()

@pytest.fixture
def demo_single_table_data_pos_neg_connector(demo_single_table_data_pos_neg):
    yield DataFrameConnector(df=demo_single_table_data_pos_neg)

@pytest.fixture
def demo_single_table_path():
    yield download_demo_data(DATA_DIR).as_posix()

@pytest.fixture
def demo_multi_table_path():
    yield download_multi_table_demo_data(DATA_DIR)

@pytest.fixture
def ndarray_loaders(tmp_path, ndarray_list):

    def generator():
        cache_dir = tmp_path / 'ndarrycache'
        for save in [True, False]:
            loader = NDArrayLoader(cache_root=cache_dir, save_to_file=save)
            for ndarray in ndarray_list:
                loader.store(ndarray)
            yield loader
            loader.cleanup()
    yield generator()

def test_csv_exporter_df(csv_exporter: CsvExporter, export_dst):
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    csv_exporter.write(export_dst, df)
    pd.testing.assert_frame_equal(df, pd.read_csv(export_dst))

def test_csv_exporter_generator(csv_exporter: CsvExporter, export_dst):

    def generator():
        yield pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        yield pd.DataFrame({'a': [7, 8, 9], 'b': [10, 11, 12]})
    df_all = pd.concat(generator(), ignore_index=True)
    csv_exporter.write(export_dst, generator())
    pd.testing.assert_frame_equal(df_all, pd.read_csv(export_dst))

@pytest.fixture
def single_demo_data_df(demo_single_table_path):
    df = pd.read_csv(demo_single_table_path)
    return df[['workclass', 'age', 'occupation']]

@pytest.fixture
def attach_demo_data_df(demo_single_table_path):
    df = pd.read_csv(demo_single_table_path)
    return df[['education', 'capital-gain']]

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

@pytest.fixture
def test_const_data(demo_single_table_path):
    const_col_df = pd.read_csv(demo_single_table_path)
    const_col_df['age'] = const_col_df['age'].astype(float)
    const_col_df['fnlwgt'] = const_col_df['fnlwgt'].astype(float)
    const_col_df['age'].values[:] = 100
    const_col_df['fnlwgt'].values[:] = 1.41421
    const_col_df['workclass'].values[:] = 'President'
    yield const_col_df

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

@pytest.fixture
def test_const_data(demo_single_table_path):
    const_col_df = pd.read_csv(demo_single_table_path)
    const_col_df['age'] = const_col_df['age'].astype(float)
    const_col_df['fnlwgt'] = const_col_df['fnlwgt'].astype(float)
    const_col_df['age'].values[:] = 100
    const_col_df['fnlwgt'].values[:] = 3.14
    const_col_df['workclass'].values[:] = 'President'
    yield const_col_df

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

@pytest.fixture
def dummy_data(demo_relational_table_path):
    table_path_a, table_path_b, _ = demo_relational_table_path
    df_a = pd.read_csv(table_path_a)
    df_b = pd.read_csv(table_path_b)
    yield [(df_a, 'parent', Metadata.from_dataframe(df_a)), (df_b, 'child', Metadata.from_dataframe(df_b))]

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path)

class MockCsvConnector(CsvConnector):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._readed = False

    @property
    def is_readed(self):
        return self._readed

    def reset(self):
        self._readed = False

    def _read(self, offset=0, limit=0) -> pd.DataFrame:
        self._readed = True
        try:
            return super()._read(offset, limit)
        except Exception:
            self._readed = False
            raise

    def _columns(self) -> list[str]:
        self._readed = True
        try:
            return super()._columns()
        except Exception:
            self._readed = False
            raise

    def iter(self, offset=0, chunksize=0) -> Generator[pd.DataFrame, None, None]:
        self._readed = True
        try:
            return super().iter(offset, chunksize)
        except Exception:
            self._readed = False
            raise

def _read(self, offset=0, limit=0) -> pd.DataFrame:
    self._readed = True
    try:
        return super()._read(offset, limit)
    except Exception:
        self._readed = False
        raise

def _columns(self) -> list[str]:
    self._readed = True
    try:
        return super()._columns()
    except Exception:
        self._readed = False
        raise

@pytest.fixture
def generator_connector():
    yield GeneratorConnector(generator_caller)

def test_generator_connector():
    c = GeneratorConnector(generator_caller)
    assert c._columns() == ['a', 'b']
    assert_frame_equal(c._read(), pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}))
    assert_frame_equal(c._read(offset=1), pd.DataFrame({'a': [7, 8, 9], 'b': [10, 11, 12]}))
    assert_frame_equal(c._read(offset=2), pd.DataFrame({'a': [13, 14, 15], 'b': [16, 17, 18]}))
    assert c._read(offset=3) is None
    assert_frame_equal(c._read(offset=0), pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}))
    assert_frame_equal(c._read(offset=1000), pd.DataFrame({'a': [7, 8, 9], 'b': [10, 11, 12]}))
    assert_frame_equal(c._read(offset=3), pd.DataFrame({'a': [13, 14, 15], 'b': [16, 17, 18]}))
    assert c._read(offset=5555) is None
    for d, g in zip(c.iter(), generator_caller()):
        assert_frame_equal(d, g)

def test_dataframe_connector(data_for_test):
    df = data_for_test.copy()
    c = DataFrameConnector(data_for_test)
    assert c._columns() == ['a', 'b']
    assert_frame_equal(c._read(), df)
    assert_frame_equal(c._read(offset=1), df[1:])
    assert_frame_equal(c._read(offset=2), df[2:])
    assert c._read(offset=3) is None
    assert_frame_equal(c._read(offset=0), df)
    assert c._read(offset=5555) is None
    for d, g in zip(c.iter(chunksize=3), [data_for_test]):
        assert_frame_equal(d, g)
    for d, g in zip(c.iter(chunksize=2), [data_for_test[:2], data_for_test[2:]]):
        assert_frame_equal(d, g)

def test_generator(csv_connector: CsvConnector):
    for df in csv_connector.iter(chunksize=1):
        assert len(df) == 1
        assert df.columns.tolist() == ['index', 'a', 'b', 'c']
    for df in csv_connector.iter(offset=1, chunksize=1):
        assert len(df) == 1
        assert df.columns.tolist() == ['index', 'a', 'b', 'c']
    assert len(list(csv_connector.iter(chunksize=1))) == 2
    assert len(list(csv_connector.iter(offset=1, chunksize=1))) == 1

@pytest.fixture
def dummy_data(dummy_single_table_path):
    yield pd.read_csv(dummy_single_table_path)

@pytest.fixture
def raw_data(demo_single_table_path):
    yield pd.read_csv(demo_single_table_path).head(100)

@pytest.fixture
def dummy_data(dummy_single_table_path):
    yield pd.read_csv(dummy_single_table_path)

