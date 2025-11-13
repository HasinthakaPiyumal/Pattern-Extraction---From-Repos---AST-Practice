# Cluster 44

def set_model_params(loc, rot, rot_mode='XYZ', model_obj_name='Car', target_color=None):
    """
    Args:
        loc: list
            [x, y, z]
        rot: list
            [angle1, angle2, angle3] (rad.)
        rot_mode: str
            Euler angle order
        model_obj_name: str
            name of the entire model. New obj name.
        target_color: dict (optinoal)
            {"material_key":.., "color": ...}
    """
    model = bpy.data.objects[model_obj_name]
    model.location = loc
    model.rotation_mode = rot_mode
    model.rotation_euler = rot
    if target_color is not None:
        modify_car_color(model, target_color['material_key'], target_color['color'])

