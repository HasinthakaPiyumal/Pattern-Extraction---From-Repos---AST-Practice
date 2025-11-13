# Cluster 28

def _set_mini_splits(split2samples: DefaultDict[str, List[Sample]], db: NuPlanDB, core_splits_names: List[str]) -> None:
    """
    Populates split2samples with mini splits done on top of core splits.

    For example:
        "train" -> "train", "train.mini"

    :param split2samples: Main dictionary containing a mapping from split name to its corresponding data. The data is
     given as a list of samples. This function assumes the existence the following splits:
      - core splits (e.g. "train", "val, "test").
      - location splits (e.g. "train.bs", "val.United_States").
    :param db: NuPlanDB.
    :param core_splits_names: Name of the core splits to be considered.
    """
    return _set_subsampled_splits(split2samples, db, core_splits_names, random_seed='42', n_samples_per_region=100, split_suffix='mini')

def _set_dev_splits(split2samples: DefaultDict[str, List[Sample]], db: NuPlanDB, core_splits_names: List[str]) -> None:
    """
    Populates split2samples with smaller evaluation splits done on top of core splits, to use in dev. experiments.
    For example:
        "train" -> "train", "train.dev"

    :param split2samples: Main dictionary containing a mapping from split name to its corresponding data. The data is
     given as a list of samples. This function assumes the existence the following splits:
      - core splits (e.g. "train", "val, "test")
      - location splits (e.g. "train.bs", "val.United_States").
    :param db: NuPlanDB.
    :param core_splits_names: Name of the core splits to be considered.
    """
    return _set_subsampled_splits(split2samples, db, core_splits_names, random_seed='42', n_samples_per_region=250, split_suffix='dev')

