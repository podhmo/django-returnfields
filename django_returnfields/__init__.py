# -*- coding:utf-8 -*-
from collections import OrderedDict

INCLUDE_KEY = "return_fields"
PATH_KEY = "_drf__path"  # {name: string, candidates: string[]}[]


class Restriction(object):
    def __init__(self, include_key=INCLUDE_KEY):
        self.include_key = include_key

    def setup(self, serializer):
        if PATH_KEY not in serializer.context:
            fields_names_string = self.get_params(serializer)[self.include_key]
            includes = [field_name.strip() for field_name in fields_names_string.split(",")]
            serializer.context[PATH_KEY] = [{"name": "", "candidates": includes}]

    def get_params(self, serializer):
        return serializer.context["request"].GET

    def is_active(self, serializer):
        return self.include_key in self.get_params(serializer)

    def restrict(self, serializer, fields):
        candidates = serializer.context[PATH_KEY][-1]["candidates"]

        if "" in candidates:  # all fields
            return fields

        relations = [field_name.split("__", 2)[0] for field_name in candidates]
        ret = OrderedDict()
        for k in fields.keys():
            if k in candidates or k in relations:
                ret[k] = fields[k]
        return ret

    def __hash__(self):
        return hash((self.__class__, self.include_key))

_cache = {}


def serializer_factory(serializer_class, restriction=Restriction(INCLUDE_KEY)):
    k = (serializer_class, restriction.__hash__())
    if k in _cache:
        return _cache[k]

    class ReturnFieldsSerializer(serializer_class):
        # override
        def get_fields(self):
            fields = super().get_fields()
            return self.get_restricted_fields(fields)

        # override
        def to_representation(self, instance):
            if not self.field_name or PATH_KEY not in self.context:
                return super().to_representation(instance)
            frame = self.context[PATH_KEY][-1]
            prefix = "{}__".format(self.field_name)
            candidates = [s.lstrip(prefix) for s in frame["candidates"]]
            self.context[PATH_KEY].append({"name": self.field_name, "candidates": candidates})
            ret = super().to_representation(instance)
            self.context[PATH_KEY].pop()
            return ret

        def get_restricted_fields(self, fields):
            if restriction.is_active(self):
                restriction.setup(self)
                return restriction.restrict(self, fields)
            else:
                return fields

    ReturnFieldsSerializer.__name__ = "ReturnFields{}".format(serializer_class.__name__)
    ReturnFieldsSerializer.__doc__ = serializer_class.__doc__
    _cache[k] = ReturnFieldsSerializer
    upgrade_classes(serializer_class, restriction)
    return ReturnFieldsSerializer


def upgrade_classes(serializer_class, restriction):
    fields = serializer_class._declared_fields
    for field in fields.values():
        # serializer but not return fields serializer
        if hasattr(field, "_declared_fields") and not hasattr(field, "get_restricted_fields"):
            upgraded_class = serializer_factory(field.__class__, restriction)
            field.__class__ = upgraded_class
