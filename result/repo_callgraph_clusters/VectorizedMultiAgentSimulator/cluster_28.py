# Cluster 28

def parse_point(element, device):
    """Parses a point element to extract x and y coordinates."""
    x = float(element.find('x').text) if element.find('x') is not None else None
    y = float(element.find('y').text) if element.find('y') is not None else None
    return torch.tensor([x, y], device=device)

def parse_bound(element, device):
    """Parses a bound (left boundary or right boundary) element to extract points and line marking."""
    points = [parse_point(point, device) for point in element.findall('point')]
    points = torch.vstack(points)
    line_marking = element.find('lineMarking').text if element.find('lineMarking') is not None else None
    return (points, line_marking)

def parse_intersections(element):
    """This function parses the lanes of the intersection."""
    intersection_info = []
    for incoming in element.findall('incoming'):
        incoming_info = {'incomingLanelet': int(incoming.find('incomingLanelet').get('ref')), 'successorsRight': int(incoming.find('successorsRight').get('ref')), 'successorsStraight': [int(s.get('ref')) for s in incoming.findall('successorsStraight')], 'successorsLeft': int(incoming.find('successorsLeft').get('ref'))}
        intersection_info.append(incoming_info)
    return intersection_info

