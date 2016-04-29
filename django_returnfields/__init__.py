# -*- coding:utf-8 -*-
from collections import OrderedDict

INCLUDE_KEY = "return_fields"
EXCLUDE_KEY = "exclude"
PATH_KEY = "_drf__path"  # {name: string, return_fields: string[], exclude: string[]}[]

# xxx
ALL = ""


class Restriction(object):
    def __init__(self, include_key=INCLUDE_KEY, exclude_key=EXCLUDE_KEY, path_key=PATH_KEY):
        self.include_key = include_key
        self.exclude_key = exclude_key
        self.path_key = path_key
        self.active_check_keys = (self.include_key, self.exclude_key)

    def setup(self, serializer):
        if PATH_KEY not in serializer.context:
            frame = {
                "name": "",
                "return_fields": self.parse_passed_values(serializer, self.include_key),
                "exclude": self.parse_passed_values(serializer, self.exclude_key),
            }
            if frame["exclude"] and not frame["return_fields"]:
                frame["return_fields"] = [ALL]
            serializer.context[PATH_KEY] = [frame]

    def get_passed_values(self, serializer):
        return serializer.context["request"].GET

    def is_active(self, serializer):
        values = self.get_passed_values(serializer)
        return any(k in values for k in self.active_check_keys)

    def parse_passed_values(self, serializer, key):
        fields_names_string = self.get_passed_values(serializer).get(key, "")
        return [field_name.strip() for field_name in fields_names_string.split(",") if field_name]

    def current_frame(self, serializer):
        return serializer.context[self.path_key][-1]

    def push_frame(self, serializer, frame):
        return serializer.context[self.path_key].append(frame)

    def pop_frame(self, serializer):
        return serializer.context[self.path_key].pop()

    def to_restricted_fields(self, serializer, fields):
        frame = self.current_frame(serializer)
        return_fields = frame["return_fields"]
        if ALL in return_fields:
            ret = fields
        else:
            # include filter
            ret = OrderedDict()
            relations = [field_name.split("__", 2)[0] for field_name in return_fields]
            for k in fields.keys():
                if k in return_fields or k in relations:
                    ret[k] = fields[k]
        # exclude filter
        for k in frame["exclude"]:
            fields.pop(k, None)
        return ret

    def to_representation(self, serializer, data):
        if not serializer.field_name or self.path_key not in serializer.context:
            return serializer._to_representation(data)
        frame = self.current_frame(serializer)
        prefix = "{}__".format(serializer.field_name)
        new_frame = {
            "name": serializer.field_name,
            "return_fields": [s.lstrip(prefix) for s in frame["return_fields"]],
            "exclude": [s.lstrip(prefix) for s in frame["exclude"]]
        }
        self.push_frame(serializer, new_frame)
        ret = serializer._to_representation(data)
        self.pop_frame(serializer)
        return ret

    def __hash__(self):
        return hash((self.__class__, self.include_key, self.path_key, self.exclude_key))

_cache = {}


def serializer_factory(serializer_class, restriction=Restriction(include_key=INCLUDE_KEY, exclude_key=EXCLUDE_KEY, path_key=PATH_KEY)):
    k = (serializer_class, False, restriction.__hash__())
    if k in _cache:
        return _cache[k]

    class ReturnFieldsSerializer(serializer_class):
        # override
        def get_fields(self):
            fields = super(ReturnFieldsSerializer, self).get_fields()
            return self.to_restricted_fields(fields)

        # override
        def to_representation(self, instance):
            return restriction.to_representation(self, instance)

        def _to_representation(self, instance):
            return super(ReturnFieldsSerializer, self).to_representation(instance)

        def to_restricted_fields(self, fields):
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


def list_serializer_factory(serializer_class, restriction=Restriction(include_key=INCLUDE_KEY, exclude_key=EXCLUDE_KEY, path_key=PATH_KEY)):
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
        elif hasattr(field, "_declared_fields") and not hasattr(field, "to_restricted_fields"):
            field.__class__ = serializer_factory(field.__class__, restriction)
