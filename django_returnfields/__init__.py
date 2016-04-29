# -*- coding:utf-8 -*-
from collections import OrderedDict

INCLUDE_KEY = "return_fields"
EXCLUDE_KEY = "exclude"
PATH_KEY = "_drf__path"  # {name: string, candidates: string[]}[]


class Restriction(object):
    def __init__(self, include_key=INCLUDE_KEY, exclude_key=EXCLUDE_KEY, path_key=PATH_KEY):
        self.include_key = include_key
        self.exclude_key = exclude_key
        self.path_key = path_key

    def setup(self, serializer):
        if PATH_KEY not in serializer.context:
            frame = {"name": "", "candidates": self.parse_passed_values(serializer)}
            serializer.context[PATH_KEY] = [frame]

    def get_passed_values(self, serializer):
        return serializer.context["request"].GET

    def is_active(self, serializer):
        return self.include_key in self.get_passed_values(serializer)

    def parse_passed_values(self, serializer):
        fields_names_string = self.get_passed_values(serializer)[self.include_key]
        return [field_name.strip() for field_name in fields_names_string.split(",")]

    def current_frame(self, serializer):
        return serializer.context[self.path_key][-1]

    def push_frame(self, serializer, frame):
        return serializer.context[self.path_key].append(frame)

    def pop_frame(self, serializer):
        return serializer.context[self.path_key].pop()

    def to_restricted_fields(self, serializer, fields):
        candidates = self.current_frame(serializer)["candidates"]
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
        frame = self.current_frame(serializer)
        prefix = "{}__".format(serializer.field_name)
        candidates = [s.lstrip(prefix) for s in frame["candidates"]]
        self.push_frame(serializer, {"name": serializer.field_name, "candidates": candidates})
        ret = serializer._to_representation(data)
        self.pop_frame(serializer)
        return ret

    def __hash__(self):
        return hash((self.__class__, self.include_key, self.path_key, self.exclude_key))

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
                return restriction.to_restricted_fields(self, fields)
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
