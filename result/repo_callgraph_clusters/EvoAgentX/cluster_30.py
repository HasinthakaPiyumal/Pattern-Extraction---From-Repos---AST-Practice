# Cluster 30

class PyObjectId(ObjectId):

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(cls.validate, core_schema.str_schema())

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid ObjectId')
        return ObjectId(v)

@classmethod
def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
    return core_schema.no_info_after_validator_function(cls.validate, core_schema.str_schema())

