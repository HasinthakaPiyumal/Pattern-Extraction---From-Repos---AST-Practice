# Cluster 0

def service_row(datasource, serviceTitle, serviceName):
    return Row(title=serviceTitle, showTitle=True, panels=[service_qps_graph(datasource, serviceTitle, serviceName), service_latency_graph(datasource, serviceTitle, serviceName)])

# Node: Row
# Node: service_qps_graph
# Node: service_latency_graph
