# -*- coding:utf-8 -*-
INCLUDE_KEY = "return_fields"


class Restriction(object):
    def __init__(self, include_key=INCLUDE_KEY):
        self.include_key = include_key

    def get_params(self, serializer):
        return serializer.context["request"].GET

    def is_active(self, serializer):
        return self.include_key in self.get_params(serializer)

    def get_include_keys(self, serializer):
        fields_names_string = self.get_params(serializer)[self.include_key]
        return [s.strip() for s in fields_names_string.split(",")]

    def restrict(self, serializer, fields):
        fields_names_string = self.get_params(serializer)[self.include_key]
        includes = [s.strip() for s in fields_names_string.split(",")]
        return {k: v for k, v in fields.items() if k in includes}


def return_fields_serializer_factory(serializer_class, restriction=Restriction(INCLUDE_KEY)):
    class ReturnFieldsSerializer(serializer_class):
        # override
        def get_fields(self):
            fields = super().get_fields()
            return self.get_restricted_fields(fields)

        def get_restricted_fields(self, fields):
            if restriction.is_active(self):
                return restriction.restrict(self, fields)
            else:
                return fields

    ReturnFieldsSerializer.__name__ = "ReturnFields{}".format(serializer_class.__name__)
    ReturnFieldsSerializer.__doc__ = serializer_class.__doc__
    return ReturnFieldsSerializer
