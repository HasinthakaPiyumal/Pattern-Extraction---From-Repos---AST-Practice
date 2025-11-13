# Cluster 21

def plot3d(img, proj_matrix, box_2d, dimensions, alpha, theta_ray, img_2d=None):
    location, X = calc_location(dimensions, proj_matrix, box_2d, alpha, theta_ray)
    orient = alpha + theta_ray
    if img_2d is not None:
        plot_2d_box(img_2d, box_2d)
    plot_3d_box(img, proj_matrix, orient, dimensions, location)
    return location

