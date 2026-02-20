# Cluster 2

def init_docker_build_paths():
    list_paths = os.listdir(os.getcwd())
    for p in list_paths:
        if os.path.isdir(p):
            if p.startswith('ts-'):
                build_path = base_path + '/' + p
                build_paths.append(build_path)

# Node: getcwd
# Node: isdir
# Node: startswith
# Node: append
class VirtualService(yaml.YAMLObject):
    yaml_tag = u'!VirtualService'

    def __init__(self, svcName, sw):
        self.apiVersion = 'networking.istio.io/v1alpha3'
        self.kind = 'VirtualService'
        self.metadata = Metadata(svcName)
        routes = []
        for subset, weight in sw.items():
            dest = Destination(svcName, subset)
            route = Route(dest, weight)
            routes.append(route)
        http = Http(routes)
        hosts = [svcName]
        self.spec = Spec(hosts, http)

def __init__(self, svcName, sw):
    self.apiVersion = 'networking.istio.io/v1alpha3'
    self.kind = 'VirtualService'
    self.metadata = Metadata(svcName)
    routes = []
    for subset, weight in sw.items():
        dest = Destination(svcName, subset)
        route = Route(dest, weight)
        routes.append(route)
    http = Http(routes)
    hosts = [svcName]
    self.spec = Spec(hosts, http)

# Node: Metadata
# Node: items
# Node: Destination
# Node: Route
# Node: Http
# Node: Spec
