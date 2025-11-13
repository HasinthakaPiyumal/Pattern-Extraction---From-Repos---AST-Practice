# Cluster 14

class CustomizedFeatureProcessor(FeatureProcessor):

    def convert_weekday(self, col_name=None):

        def _convert_weekday(timestamp):
            dt = date(int('20' + timestamp[0:2]), int(timestamp[2:4]), int(timestamp[4:6]))
            return int(dt.strftime('%w'))
        return pl.col('hour').apply(_convert_weekday)

    def convert_weekend(self, col_name=None):

        def _convert_weekend(timestamp):
            dt = date(int('20' + timestamp[0:2]), int(timestamp[2:4]), int(timestamp[4:6]))
            return 1 if dt.strftime('%w') in ['6', '0'] else 0
        return pl.col('hour').apply(_convert_weekend)

    def convert_hour(self, col_name=None):
        return pl.col('hour').apply(lambda x: int(x[6:8]))

def _convert_weekday(timestamp):
    dt = date(int('20' + timestamp[0:2]), int(timestamp[2:4]), int(timestamp[4:6]))
    return int(dt.strftime('%w'))

def _convert_weekend(timestamp):
    dt = date(int('20' + timestamp[0:2]), int(timestamp[2:4]), int(timestamp[4:6]))
    return 1 if dt.strftime('%w') in ['6', '0'] else 0

class CustomizedFeatureProcessor(FeatureProcessor):
    """
    This is a demo for implementing customized feature processing functions.

    In the config/example7_config/dataset_config.yaml file, the 'convert_weekday' and 'convert_hour'
    processors are called. Hence, it is necessary to implement the two functions by inheriting from
    'fuxictr.preprocess.FeatureProcessor'. Some concrete examples can be found in 'fuxictr.datasets'.

    Each processor function ONLY accepts one argument: col_name, and returns an expression based on 
    polars. We use polars instead of pandas for speedup.
    """

    def convert_weekday(self, col_name=None):

        def _convert_weekday(timestamp):
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            return int(dt.strftime('%w'))
        return pl.col('time_stamp').apply(_convert_weekday)

    def convert_hour(self, col_name=None):

        def _convert_hour(timestamp):
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            return int(dt.hour)
        return pl.col('time_stamp').apply(_convert_hour)

def _convert_weekday(timestamp):
    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return int(dt.strftime('%w'))

def _convert_hour(timestamp):
    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return int(dt.hour)

