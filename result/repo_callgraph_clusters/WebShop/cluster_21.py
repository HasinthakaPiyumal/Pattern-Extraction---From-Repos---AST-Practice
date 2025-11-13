# Cluster 21

def parse_action(action):
    """
    Parse action string to action name and its arguments.
    """
    pattern = re.compile('(.+)\\[(.+)\\]')
    m = re.match(pattern, action)
    if m is None:
        action_name = action
        action_arg = None
    else:
        action_name, action_arg = m.groups()
    return (action_name, action_arg)

