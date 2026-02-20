# Cluster 19

def ts_to_string_utc(timest_second_epoch, format_string='%Y-%m-%d %H:%M:%S'):
    return time.strftime(format_string, time.gmtime(timest_second_epoch))

# Node: strftime
# Node: gmtime
def ts_to_string_local(timest_second_epoch, format_string='%Y-%m-%d %H:%M:%S'):
    return time.strftime(format_string, time.localtime(timest_second_epoch))

# Node: localtime
