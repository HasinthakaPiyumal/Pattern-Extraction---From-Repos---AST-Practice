# Cluster 105

def generate_convex_hull(points):
    hull = ConvexHull(points)
    return points[hull.vertices]

