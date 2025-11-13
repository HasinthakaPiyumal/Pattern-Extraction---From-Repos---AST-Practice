# Cluster 63

def raster_layer_from_map_layer(map_layer: MapLayer) -> RasterLayer:
    """
    Convert MapDB's MapLayer to the generic RasterLayer.
    :param map_layer: input MapLayer object.
    :return: output RasterLayer object.
    """
    return RasterLayer(map_layer.data, map_layer.precision, map_layer.transform_matrix)

