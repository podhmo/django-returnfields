# -*- coding:utf-8 -*-
from collections import OrderedDict
import warnings

# TODO: see settings
INCLUDE_KEY = "return_fields"
EXCLUDE_KEY = "skip_fields"
PATH_KEY = "_drf__path"  # {name: string, return_fields: string[], skip_fields: string[]}[]

# xxx
ALL = ""


def truncate_for_child(s, prefix, field_name):
    if s.startswith(prefix):
        return s[len(prefix):]
    elif s == field_name:
        return ALL
    else:
        return s


def is_already_upgraded(cls):
    return hasattr(cls, "to_restricted_fields")


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
                self.include_key: self.parse_passed_values(serializer, self.include_key),
                self.exclude_key: self.parse_passed_values(serializer, self.exclude_key),
            }
            if frame[self.exclude_key] and not frame[self.include_key]:
                frame[self.include_key] = [ALL]
            serializer.context[PATH_KEY] = [frame]

    def get_passed_values(self, serializer):
        return serializer.context["request"].GET

    def is_active(self, serializer):
        try:
            values = self.get_passed_values(serializer)
        except KeyError:
            return False
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
        return_fields = frame[self.include_key]
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
        for k in frame[self.exclude_key]:
            ret.pop(k, None)
        return ret

    def to_representation(self, serializer, data):
        if not serializer.field_name or self.path_key not in serializer.context:
            return serializer._to_representation(data)
        field_name = serializer.field_name
        frame = self.current_frame(serializer)
        prefix = "{}__".format(field_name)
        new_frame = {
            "name": field_name,
            self.include_key: [truncate_for_child(s, prefix, field_name) for s in frame[self.include_key]],
            self.exclude_key: [truncate_for_child(s, prefix, field_name) for s in frame[self.exclude_key]]
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
    if is_already_upgraded(serializer_class):
        _cache[k] = serializer_class
        return serializer_class

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
    try:
        ReturnFieldsSerializer.__doc__ = serializer_class.__doc__
    except AttributeError as e:
        warnings.warn(str(e), UserWarning)  # for python2.x

    _cache[k] = ReturnFieldsSerializer
    upgrade_member_classes(serializer_class, restriction)
    return ReturnFieldsSerializer


def list_serializer_factory(serializer_class, restriction=Restriction(include_key=INCLUDE_KEY, exclude_key=EXCLUDE_KEY, path_key=PATH_KEY)):
    k = (serializer_class, True, restriction.__hash__())
    if k in _cache:
        return _cache[k]
    if is_already_upgraded(serializer_class):
        _cache[k] = serializer_class
        return serializer_class

    class ReturnFieldsListSerializer(serializer_class):
        # override
        def to_representation(self, data):
            return restriction.to_representation(self, data)

        def _to_representation(self, data):
            return super(ReturnFieldsListSerializer, self).to_representation(data)

        def to_restricted_fields(self, fields):
            raise Exception("dont't use this")

    ReturnFieldsListSerializer.__name__ = "ReturnFieldsList{}".format(serializer_class.__name__)
    try:
        ReturnFieldsListSerializer.__doc__ = serializer_class.__doc__
    except AttributeError as e:
        warnings.warn(str(e), UserWarning)  # for python2.x
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
        elif hasattr(field, "_declared_fields") and not is_already_upgraded(field):
            field.__class__ = serializer_factory(field.__class__, restriction)
