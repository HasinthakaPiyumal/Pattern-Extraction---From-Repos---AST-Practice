# Cluster 24

class AttributeCurriculum:
    """
    Curriculum that increases the value of an attribute (e.g. requirement) as the success rate increases.
    Currently support only attributes that are increasing.
    """
    INFO_CURRICULUM_PREFIX: str = 'curriculum/'

    def __init__(self, success_rate_impl: SuccessRateImpl, attribute_owner: Type, attribute_name: str, initial_value: float, target_value: float, target_value_threshold: float, **kwargs):
        self.__success_rate_impl = success_rate_impl
        self.__attribute_owner = attribute_owner
        self.__attribute_name = attribute_name
        self.__initial_value = initial_value
        self.__target_value_threshold = target_value_threshold
        self.__current_value = initial_value
        self.__value_diff = target_value - initial_value

    def get_info(self) -> Dict:
        info = {f'{self.INFO_CURRICULUM_PREFIX}{self.__attribute_name}': self.__current_value}
        return info

    def reset_task(self):
        self.__update_attribute()

    def __update_attribute(self):
        scale = min(1.0, max(self.__initial_value, self.__success_rate_impl.success_rate / self.__target_value_threshold))
        self.__current_value = self.__initial_value + scale * self.__value_diff
        if hasattr(self.__attribute_owner, self.__attribute_name):
            setattr(self.__attribute_owner, self.__attribute_name, self.__current_value)
        elif hasattr(self.__attribute_owner, f'_{self.__attribute_name}'):
            setattr(self.__attribute_owner, f'_{self.__attribute_name}', self.__current_value)
        elif hasattr(self.__attribute_owner, f'__{self.__attribute_name}'):
            setattr(self.__attribute_owner, f'__{self.__attribute_name}', self.__current_value)
        else:
            raise Exception(f"Attribute owner '{self.__attribute_owner}' does not have any attribute named {self.__attribute_name}.")

def reset_task(self):
    self.__update_attribute()

