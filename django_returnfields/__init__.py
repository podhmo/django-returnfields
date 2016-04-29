# -*- coding:utf-8 -*-
from collections import OrderedDict


INCLUDE_KEY = "return_fields"
PATH_KEY = "_drf__path"  # {name: string, candidates: string[]}[]


class Restriction(object):
    def __init__(self, include_key=INCLUDE_KEY, path_key=PATH_KEY):
        self.include_key = include_key
        self.path_key = path_key

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
        candidates = serializer.context[self.path_key][-1]["candidates"]
        if "" in candidates:  # all fields
            return fields

        relations = [field_name.split("__", 2)[0] for field_name in candidates]
        ret = OrderedDict()
        for k in fields.keys():
            if k in candidates or k in relations:
                ret[k] = fields[k]
        return ret

    def to_representation(self, serializer, data):
        if not serializer.field_name or self.path_key not in serializer.context:
            return serializer._to_representation(data)
        frame = serializer.context[self.path_key][-1]
        prefix = "{}__".format(serializer.field_name)
        candidates = [s.lstrip(prefix) for s in frame["candidates"]]
        serializer.context[self.path_key].append({"name": serializer.field_name, "candidates": candidates})
        ret = serializer._to_representation(data)
        serializer.context[self.path_key].pop()
        return ret

    def __hash__(self):
        return hash((self.__class__, self.include_key, self.path_key))

_cache = {}


def serializer_factory(serializer_class, restriction=Restriction(INCLUDE_KEY, PATH_KEY)):
    k = (serializer_class, False, restriction.__hash__())
    if k in _cache:
        return _cache[k]

    class ReturnFieldsSerializer(serializer_class):
        # override
        def get_fields(self):
            fields = super(ReturnFieldsSerializer, self).get_fields()
            return self.get_restricted_fields(fields)

        # override
        def to_representation(self, instance):
            return restriction.to_representation(self, instance)

        def _to_representation(self, instance):
            return super(ReturnFieldsSerializer, self).to_representation(instance)

        def get_restricted_fields(self, fields):
            if restriction.is_active(self):
                restriction.setup(self)
                return restriction.restrict(self, fields)
            else:
                return fields

    ReturnFieldsSerializer.__name__ = "ReturnFields{}".format(serializer_class.__name__)
    ReturnFieldsSerializer.__doc__ = serializer_class.__doc__
    _cache[k] = ReturnFieldsSerializer
    upgrade_member_classes(serializer_class, restriction)
    return ReturnFieldsSerializer


def list_serializer_factory(serializer_class, restriction=Restriction(INCLUDE_KEY, PATH_KEY)):
    k = (serializer_class, True, restriction.__hash__())
    if k in _cache:
        return _cache[k]

    class ReturnFieldsListSerializer(serializer_class):
        # override
        def to_representation(self, data):
            return restriction.to_representation(self, data)

        def _to_representation(self, data):
            return super(ReturnFieldsListSerializer, self).to_representation(data)

    ReturnFieldsListSerializer.__name__ = "ReturnFieldsList{}".format(serializer_class.__name__)
    ReturnFieldsListSerializer.__doc__ = serializer_class.__doc__
    _cache[k] = ReturnFieldsListSerializer
    return ReturnFieldsListSerializer


def upgrade_member_classes(serializer_class, restriction):
    fields = serializer_class._declared_fields
    for field in fields.values():
        # ListSerializer
        if getattr(field, "many", False) and hasattr(field, "child"):
            field.child.__class__ = serializer_factory(field.child.__class__, restriction)
            field.__class__ = list_serializer_factory(field.__class__, restriction)
        # serializer but not return fields serializer
        elif hasattr(field, "_declared_fields") and not hasattr(field, "get_restricted_fields"):
            field.__class__ = serializer_factory(field.__class__, restriction)
