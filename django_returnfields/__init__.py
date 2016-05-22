# -*- coding:utf-8 -*-
import logging
from collections import OrderedDict
import warnings
from rest_framework.serializers import ListSerializer
from . import aggressive


logger = logging.getLogger(__name__)


# TODO: see settings
INCLUDE_KEY = "return_fields"
EXCLUDE_KEY = "skip_fields"
PATH_KEY = "_drf__path"  # {name: string, return_fields: string[], skip_fields: string[]}[]
INACTIVE_KEY = "_drf__inactive"
AGGRESSIVE_KEY = "_drf__aggressive"  # boolean
# xxx
ALL = ":all:"


def truncate_for_child(fields, prefix, field_name):
    if field_name is None:
        return fields
    if len(fields) == 1 and fields[0] == ALL:
        return fields
    r = []
    for s in fields:
        if s.startswith(prefix):
            r.append(s[len(prefix):])
        elif s == field_name:
            r.append(ALL)
    return r


def is_already_upgraded(cls):
    return hasattr(cls, "to_restricted_fields")


class RequestValue(object):
    # default is request.GET
    def get(self, context):
        return context["request"].GET

    def parse(self, context, key):
        fields_names_string = self.get(context).get(key, "")
        return [field_name.strip() for field_name in fields_names_string.split(",") if field_name]

    def is_active(self, context, active_check_keys):
        if PATH_KEY in context:
            return True
        if context.get(INACTIVE_KEY):
            return False
        try:
            values = self.get(context)
            return any(k in values for k in active_check_keys)
        except KeyError:
            context[INACTIVE_KEY] = True
            return False

    def make_initial_frame(self, context, include_key, exclude_key):
        frame = {
            "name": "",
            include_key: self.parse(context, include_key),
            exclude_key: self.parse(context, exclude_key),
        }
        try:
            logger.debug("restriction: start with %s", frame)
        except Exception:
            logger.warn("unexpected arguments: %s", self.get(context), exc_info=True)
        if frame[exclude_key] and not frame[include_key]:
            frame[include_key] = [ALL]
        return frame


class Restriction(object):
    def __init__(self, request_value,
                 include_key=INCLUDE_KEY, exclude_key=EXCLUDE_KEY, path_key=PATH_KEY):
        self.request_value = request_value
        self.include_key = include_key
        self.exclude_key = exclude_key
        self.path_key = path_key
        self.active_check_keys = (self.include_key, self.exclude_key)

    def is_toplevel(self, serializers):
        return self.current_frame(serializers).get("toplevel", False)

    def setup(self, context):
        if PATH_KEY in context:
            return False
        frame = self.request_value.make_initial_frame(context, self.include_key, self.exclude_key)
        context[PATH_KEY] = [frame]

        if frame.get(INCLUDE_KEY, None) and not frame.get(EXCLUDE_KEY, None):
            context[AGGRESSIVE_KEY] = "include"
        elif frame.get(EXCLUDE_KEY, None):
            context[AGGRESSIVE_KEY] = "exclude"
        return True

    def is_active(self, serializer):
        return self.request_value.is_active(serializer.context, self.active_check_keys)

    def current_frame(self, serializer):
        return serializer.context[self.path_key][-1]

    def push_frame(self, serializer, frame):
        # print("{}>>> {}".format(" " * len(serializer.context[self.path_key]), frame))
        return serializer.context[self.path_key].append(frame)

    def pop_frame(self, serializer):
        frame = serializer.context[self.path_key].pop()
        # print("{}<<< {}".format(" " * len(serializer.context[self.path_key]), frame))
        return frame

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

    def to_representation(self, serializer, data, many=True):
        field_name = serializer.field_name
        frame = self.current_frame(serializer)

        prefix = "{}__".format(field_name)
        new_frame = {
            "name": field_name,
            self.include_key: truncate_for_child(frame[self.include_key], prefix, field_name),
            self.exclude_key: truncate_for_child(frame[self.exclude_key], prefix, field_name)
        }
        self.push_frame(serializer, new_frame)
        if many and "aggressive" in self.request_value.get(serializer.context):
            data = self.optimize_query_aggressively(new_frame, data, serializer.context.get(AGGRESSIVE_KEY))
        ret = serializer._to_representation(data)
        self.pop_frame(serializer)
        return ret

    def optimize_query_aggressively(self, frame, data, optimize_type):
        if hasattr(data, "all"):
            if optimize_type == 'exclude':
                return aggressive.safe_defer(data.all(), frame[self.exclude_key])
            elif optimize_type == 'include':
                return aggressive.safe_only(data.all(), frame[self.include_key])
        return data

    def __hash__(self):
        return hash((self.__class__, self.include_key, self.path_key, self.exclude_key))

_cache = {}
_default_restriction = Restriction(RequestValue(), include_key=INCLUDE_KEY, exclude_key=EXCLUDE_KEY, path_key=PATH_KEY)


def restriction_factory(**kwargs):
    return Restriction(RequestValue(), **kwargs)


def serializer_factory(serializer_class, restriction=_default_restriction):
    k = (serializer_class, False, restriction.__hash__())
    if k in _cache:
        return _cache[k]
    if is_already_upgraded(serializer_class):
        _cache[k] = serializer_class
        return serializer_class

    class ReturnFieldsSerializer(serializer_class):
        # # override
        # def __new__(cls, *args, **kwargs):
        #     context = kwargs.get("context")
        #     if context:
        #         restriction.setup(context)
        #     return super(ReturnFieldsSerializer, cls).__new__(cls, *args, **kwargs)

        # override
        def get_fields(self):
            fields = super(ReturnFieldsSerializer, self).get_fields()
            return self.to_restricted_fields(fields)

        # override
        def to_representation(self, instance):
            if not restriction.is_active(self):
                return super(ReturnFieldsSerializer, self).to_representation(instance)
            elif not restriction.setup(self.context) and not self.field_name:
                return super(ReturnFieldsSerializer, self).to_representation(instance)
            return restriction.to_representation(self, instance)

        def _to_representation(self, instance):
            return super(ReturnFieldsSerializer, self).to_representation(instance)

        def to_restricted_fields(self, fields):
            if restriction.is_active(self):
                return restriction.to_restricted_fields(self, fields)
            else:
                return fields

        class Meta(getattr(serializer_class, 'Meta', object)):
            list_serializer_class = list_serializer_factory(
                getattr(getattr(serializer_class, 'Meta', object),
                        'list_serializer_class',
                        ListSerializer),
                restriction=restriction)

    ReturnFieldsSerializer.__name__ = "ReturnFields{}".format(serializer_class.__name__)
    try:
        ReturnFieldsSerializer.__doc__ = serializer_class.__doc__
    except AttributeError as e:
        warnings.warn(str(e), UserWarning)  # for python2.x

    _cache[k] = ReturnFieldsSerializer
    upgrade_member_classes(serializer_class, restriction)
    return ReturnFieldsSerializer


def list_serializer_factory(serializer_class, restriction=_default_restriction):
    k = (serializer_class, True, restriction.__hash__())
    if k in _cache:
        return _cache[k]
    if is_already_upgraded(serializer_class):
        _cache[k] = serializer_class
        return serializer_class

    class ReturnFieldsListSerializer(serializer_class):
        # override
        def to_representation(self, data):
            if not restriction.is_active(self):
                return super(ReturnFieldsListSerializer, self).to_representation(data)
            elif not restriction.setup(self.context) and not self.field_name:
                return super(ReturnFieldsListSerializer, self).to_representation(data)
            return restriction.to_representation(self, data, many=True)

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
