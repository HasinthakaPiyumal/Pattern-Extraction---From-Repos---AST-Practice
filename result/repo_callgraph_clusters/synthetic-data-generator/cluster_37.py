# Cluster 37

class FrequencyEncoder(BaseTransformer):
    """Transformer for categorical data.

    This transformer computes a float representative for each one of the categories
    found in the fit data, and then replaces the instances of these categories with
    the corresponding representative.

    The representatives are decided by sorting the categorical values by their relative
    frequency, then dividing the ``[0, 1]`` interval by these relative frequencies, and
    finally assigning the middle point of each interval to the corresponding category.

    When the transformation is reverted, each value is assigned the category that
    corresponds to the interval it falls in.

    Null values are considered just another category.

    Args:
        add_noise (bool):
            Whether to generate gaussian noise around the class representative of each interval
            or just use the mean for all the replaced values. Defaults to ``False``.
    """
    INPUT_SDTYPE = 'categorical'
    SUPPORTED_SDTYPES = ['categorical', 'boolean']
    OUTPUT_SDTYPES = {'value': 'float'}
    DETERMINISTIC_REVERSE = True
    COMPOSITION_IS_IDENTITY = True
    mapping = None
    intervals = None
    starts = None
    means = None
    dtype = None

    def __setstate__(self, state):
        """Replace any ``null`` key by the actual ``np.nan`` instance."""
        intervals = state.get('intervals')
        if intervals:
            for key in list(intervals):
                if pd.isna(key):
                    intervals[np.nan] = intervals.pop(key)
        self.__dict__ = state

    def __init__(self, add_noise=False):
        self.add_noise = add_noise

    def is_transform_deterministic(self):
        """Return whether the transform is deterministic.

        Returns:
            bool:
                Whether or not the transform is deterministic.
        """
        return not self.add_noise

    @staticmethod
    def _get_intervals(data, normalized=False):
        """Compute intervals for each categorical value.

        Args:
            data (pandas.Series):
                Data to analyze.

        Returns:
            dict:
                intervals for each categorical value (start, end).
        """
        data = data.fillna(np.nan)
        frequencies = data.value_counts(dropna=False)
        start = -1.0 if normalized else 0.0
        end = 0.0
        elements = len(data)
        probes = frequencies / (elements / 2.0) if normalized else frequencies / elements
        intervals = {}
        means = []
        starts = []
        for value, prob in probes.items():
            end = start + prob
            mean = start + prob / 2
            std = prob / 6
            if pd.isna(value):
                value = np.nan
            intervals[value] = (start, end, mean, std)
            means.append(mean)
            starts.append((value, start))
            start = end
        means = pd.Series(means, index=list(frequencies.keys()))
        starts = pd.DataFrame(starts, columns=['category', 'start']).set_index('start')
        return (intervals, means, starts)

    def _fit(self, data):
        """Fit the transformer to the data.

        Compute the intervals for each categorical value.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
        self.dtype = data.dtype
        self.intervals, self.means, self.starts = self._get_intervals(data)

    @staticmethod
    def _clip_noised_transform(result, start, end):
        """Clip transformed values.

        Used to ensure the noise added to transformed values doesn't make it
        go out of the bounds of a given category.

        The upper bound must be slightly lower than ``end``
        so it doesn't get treated as the next category.
        """
        return np.clip(result, start, end - 1e-09)

    def _transform_by_category(self, data):
        """Transform the data by iterating over the different categories."""
        result = np.empty(shape=(len(data),), dtype=float)
        for category, values in self.intervals.items():
            start, end, mean, std = values
            if category is np.nan:
                mask = data.isna()
            else:
                mask = data.to_numpy() == category
            if self.add_noise:
                result[mask] = norm.rvs(mean, std, size=mask.sum())
                result[mask] = self._clip_noised_transform(result[mask], start, end)
            else:
                result[mask] = mean
        return result

    def _get_value(self, category):
        """Get the value that represents this category."""
        if pd.isna(category):
            category = np.nan
        start, end, mean, std = self.intervals[category]
        if self.add_noise:
            result = norm.rvs(mean, std)
            return self._clip_noised_transform(result, start, end)
        return mean

    def _transform_by_row(self, data):
        """Transform the data row by row."""
        return data.fillna(np.nan).apply(self._get_value).to_numpy()

    def _transform(self, data):
        """Transform the categorical values to float representatives.

        Args:
            data (pandas.Series):
                Data to transform.

        Returns:
            numpy.ndarray
        """
        fit_categories = pd.Series(self.intervals.keys())
        has_nan = pd.isna(fit_categories).any()
        unseen_indexes = ~(data.isin(fit_categories) | pd.isna(data) & has_nan)
        if unseen_indexes.any():
            unseen_categories = set(data[unseen_indexes][:5])
            warnings.warn(f'The data contains {unseen_indexes.sum()} new categories that were not seen in the original data (examples: {unseen_categories}). Assigning them random values. If you want to model new categories, please fit the transformer again with the new data.')
        data[unseen_indexes] = np.random.choice(fit_categories, size=unseen_indexes.size)
        if len(self.means) < len(data):
            return self._transform_by_category(data)
        return self._transform_by_row(data)

    def _reverse_transform_by_matrix(self, data):
        """Reverse transform the data with matrix operations."""
        num_rows = len(data)
        num_categories = len(self.starts)
        data = np.broadcast_to(data, (num_categories, num_rows)).T
        starts = np.broadcast_to(self.starts.index, (num_rows, num_categories))
        is_data_greater_than_starts = (data >= starts)[:, ::-1]
        interval_indexes = num_categories - np.argmax(is_data_greater_than_starts, axis=1) - 1
        get_category_from_index = list(self.starts['category']).__getitem__
        return pd.Series(interval_indexes).apply(get_category_from_index).astype(self.dtype)

    def _reverse_transform_by_category(self, data):
        """Reverse transform the data by iterating over all the categories."""
        result = np.empty(shape=(len(data),), dtype=self.dtype)
        for category, values in self.intervals.items():
            start = values[0]
            mask = start <= data.to_numpy()
            result[mask] = category
        return pd.Series(result, index=data.index, dtype=self.dtype)

    def _get_category_from_start(self, value):
        lower = self.starts.loc[:value]
        return lower.iloc[-1].category

    def _reverse_transform_by_row(self, data):
        """Reverse transform the data by iterating over each row."""
        return data.apply(self._get_category_from_start).astype(self.dtype)

    def _reverse_transform(self, data, normalize=False):
        """Convert float values back to the original categorical values.

        Args:
            data (pd.Series):
                Data to revert.

        Returns:
            pandas.Series
        """
        data = data.clip(-1 if normalize else 0, 1)
        num_rows = len(data)
        num_categories = len(self.means)
        needed_memory = num_rows * num_categories * 8 * 3
        available_memory = psutil.virtual_memory().available
        if available_memory > needed_memory:
            return self._reverse_transform_by_matrix(data)
        if num_rows > num_categories:
            return self._reverse_transform_by_category(data)
        return self._reverse_transform_by_row(data)

def _fit(self, data):
    """Fit the transformer to the data.

        Compute the intervals for each categorical value.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
    self.dtype = data.dtype
    self.intervals, self.means, self.starts = self._get_intervals(data)

class NormalizedFrequencyEncoder(FrequencyEncoder):
    """Same to FrequencyEncoder except the transform result is in [-1, 1] instead of [0, 1]"""

    def _fit(self, data):
        """Fit the transformer to the data.

        Compute the intervals for each categorical value.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
        self.dtype = data.dtype
        self.intervals, self.means, self.starts = self._get_intervals(data, normalized=True)

    def _reverse_transform(self, data):
        return super()._reverse_transform(data, True)

def _fit(self, data):
    """Fit the transformer to the data.

        Compute the intervals for each categorical value.

        Args:
            data (pandas.Series):
                Data to fit the transformer to.
        """
    self.dtype = data.dtype
    self.intervals, self.means, self.starts = self._get_intervals(data, normalized=True)

