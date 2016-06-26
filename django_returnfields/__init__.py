# -*- coding:utf-8 -*-
import logging
from collections import OrderedDict
from collections import namedtuple
import warnings
from rest_framework.serializers import ListSerializer
from . import aggressive
from .structures import AgainstDeepcopyWrapper


logger = logging.getLogger(__name__)
Token = namedtuple("Token", "name, nested, queryname")

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

    def can_optimize(self, context):
        return self.get(context).get("aggressive", False)

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


class QueryOptimizer(object):
    view_aggressive_query_method_name = "aggressive_queryset"
    view_aggressive_intercept = "aggressive_intercept"

    def __init__(self, restriction, translator=None):
        self.restriction = restriction
        self.translator = translator or NameListTranslator()

    def optimize_query(self, context, instance, serializer_class):
        frame = self.restriction.frame_management.current_frame(context)
        qs = self._as_query(context, instance)
        optimized_qs = self._optimize_query(frame, qs, serializer_class)
        return optimized_qs

    def _as_query(self, context, data):
        # if paginated view, then data is maybe list type object.
        # and `order_by, group_by, select_related, ..` hints are dropped.
        qs, is_query = aggressive.revive_query(data)
        if not is_query:
            if qs:
                logger.info("%s is not queryset object", qs)
            return qs

        # get optimized query from view object
        if "view" in context:
            view = context["view"]
            optimize_fn_by_view = getattr(view, self.view_aggressive_query_method_name, None)
            if optimize_fn_by_view:
                qs = optimize_fn_by_view(qs)
                if getattr(view, self.view_aggressive_intercept, False):
                    return qs
        return qs

    def _optimize_query(self, frame, query, serializer_class):
        if not hasattr(query, "all"):
            return query

        skip_list = frame.get(self.restriction.exclude_key, None)
        name_list = frame.get(self.restriction.include_key, None)
        name_list = self.translator.translate(serializer_class, name_list)
        return aggressive.aggressive_query(
            query,
            name_list=name_list,
            skip_list=skip_list
        )


class NameListTranslator(object):
    ALL_LIST = [ALL]

    def __init__(self):
        self.fields_cache = {}  # hmm
        self.mapping_cache = {}

    def translate(self, serializer_class, name_list):
        if name_list == self.ALL_LIST:
            name_list = None
        mapping = self.get_mapping(serializer_class)
        if name_list:
            return [mapping[name].queryname for name in name_list if name in mapping]
        else:
            return [token.queryname for token in mapping.values() if not token.nested]

    def all_name_list(self, serializer_class):
        return self.translate(serializer_class, None)

    def get_mapping(self, serializer_class):
        mapping = self.mapping_cache.get(serializer_class)
        if mapping is None:
            mapping = self.mapping_cache[serializer_class] = self._get_mapping(serializer_class)
        return mapping

    def get_fields(self, serializer_class):
        fields = self.fields_cache.get(serializer_class)
        if fields is None:
            fields = serializer_class._dr_fields = serializer_class().get_fields()
        return fields

    def _get_mapping(self, serializer_class):
        fields = self.get_fields(serializer_class)
        d = OrderedDict()
        # todo: supporting SerializerMethodField, ModelField
        for name, field in fields.items():
            if hasattr(field, "child"):
                field = field.child  # ListSerialier -> Serializer
            if hasattr(field, "child_relation"):
                cr = field.child_relation
                subname = getattr(cr, "lookup_field", None) or cr.queryset.model._meta.pk.name
                token = Token(name=name, nested=False, queryname="{}__{}".format(name, subname))
                d[token.queryname] = token
            elif hasattr(field, "_declared_fields"):
                token = Token(name=name, nested=True, queryname="{}__*__*".format(name))
                d[token.name] = token
                for subname, stoken in self.get_mapping(field.__class__).items():
                    fullname = "{}__{}".format(name, subname)
                    token = Token(name=fullname, nested=False, queryname=fullname)
                    d[token.queryname] = token
            else:
                token = Token(name=name, nested=False, queryname=name)
                d[token.queryname] = token
        return d


class FrameManagement(object):
    def current_frame(self, context):
        return context[PATH_KEY][-1]

    def push_frame(self, context, frame):
        # print("{}>>> {}".format(" " * len(context[PATH_KEY]), frame))
        return context[PATH_KEY].append(frame)

    def pop_frame(self, context):
        frame = context[PATH_KEY].pop()
        # print("{}<<< {}".format(" " * len(context[PATH_KEY]), frame))
        return frame

    def is_toplevel(self, context):
        return context[PATH_KEY][-1].get("toplevel", False)

    def has_frame(self, context):
        return PATH_KEY in context

    def init_frame(self, context, frame):
        context[PATH_KEY] = [frame]


class Restriction(object):
    def __init__(self, request_value, frame_management, query_optimizer_cls,
                 include_key=INCLUDE_KEY, exclude_key=EXCLUDE_KEY):
        self.request_value = request_value
        self.frame_management = frame_management
        self.query_optimizer = query_optimizer_cls(self)
        self.include_key = include_key
        self.exclude_key = exclude_key
        self.active_check_keys = (self.include_key, self.exclude_key)

    def setup(self, context, many=False):
        if self.frame_management.has_frame(context):
            return self.frame_management.is_toplevel(context)
        frame = self._make_initial_frame(context)
        self.frame_management.init_frame(context, frame)
        return True

    def is_active(self, context):
        return self.request_value.is_active(context, self.active_check_keys)

    def can_optimize(self, context):
        return self.request_value.can_optimize(context)

    def to_restricted_fields(self, serializer, fields):
        frame = self.frame_management.current_frame(serializer.context)
        return self._make_new_fields(frame, fields)

    def to_representation(self, serializer, data):
        field_name = serializer.field_name
        frame = self.frame_management.current_frame(serializer.context)
        new_frame = self._make_new_frame(frame, field_name)
        self.frame_management.push_frame(serializer.context, new_frame)
        ret = serializer._to_representation(data)
        self.frame_management.pop_frame(serializer.context)
        return ret

    def _make_initial_frame(self, context):
        frame = {
            "name": "",
            "toplevel": True,
            self.include_key: self.request_value.parse(context, self.include_key),
            self.exclude_key: self.request_value.parse(context, self.exclude_key),
        }
        try:
            logger.debug("restriction: start with %s", frame)
        except Exception:
            logger.warn("unexpected arguments: %s", self.request_value.get(context), exc_info=True)
        if frame[self.exclude_key] and not frame[self.include_key]:
            frame[self.include_key] = [ALL]
        return frame

    def _make_new_fields(self, frame, fields):
        return_fields = frame[self.include_key]
        if ALL in return_fields:
            new_fields = fields
        else:
            # include filter
            new_fields = OrderedDict()
            relations = [field_name.split("__", 2)[0] for field_name in return_fields]
            for k in fields.keys():
                if k in return_fields or k in relations:
                    new_fields[k] = fields[k]
        # exclude filter
        for k in frame[self.exclude_key]:
            new_fields.pop(k, None)
        return new_fields

    def _make_new_frame(self, frame, field_name):
        prefix = "{}__".format(field_name)
        new_frame = {
            "name": field_name,
            self.include_key: truncate_for_child(frame[self.include_key], prefix, field_name),
            self.exclude_key: truncate_for_child(frame[self.exclude_key], prefix, field_name)
        }
        return new_frame

    def __hash__(self):
        return hash((self.__class__, self.include_key, self.exclude_key))


def restriction_factory(**kwargs):
    return Restriction(RequestValue(), FrameManagement(), QueryOptimizer, **kwargs)

_cache = {}
_default_restriction = restriction_factory(include_key=INCLUDE_KEY, exclude_key=EXCLUDE_KEY)


def serializer_factory(serializer_class, restriction=_default_restriction):
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
            if not restriction.is_active(self.context):
                return super(ReturnFieldsSerializer, self).to_representation(instance)
            elif not restriction.setup(self.context, many=False) and not self.field_name:
                return super(ReturnFieldsSerializer, self).to_representation(instance)
            return restriction.to_representation(self, instance)

        def _to_representation(self, instance):
            return super(ReturnFieldsSerializer, self).to_representation(instance)

        def to_restricted_fields(self, fields):
            if restriction.is_active(self.context):
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
        def __new__(cls, instance=None, **kwargs):
            # print(">>>>> start", type(instance), id(instance))
            context = kwargs.get("context")
            if context:
                if not restriction.is_active(context):
                    return serializer_class(instance, **kwargs)
                restriction.setup(context, many=True)
                if restriction.can_optimize(context):
                    instance = restriction.query_optimizer.optimize_query(context, instance, kwargs["child"].__class__)
                    # print(">>>>> changed", type(instance), id(instance))
                    # xxx: a constructor of ListSerializer calling deepcopy
                    instance = AgainstDeepcopyWrapper(instance)
                    # print(">>>>> wrapped", type(instance), id(instance))
            serializer = super(ReturnFieldsListSerializer, cls).__new__(cls, instance, **kwargs)
            return serializer

        def __init__(self, *args, **kwargs):
            super(ReturnFieldsListSerializer, self).__init__(*args, **kwargs)
            # xxx: rest_framework.fields:Field.__new__ is not passing arguments, so.
            if self._args and hasattr(self._args[0], "unwrap"):
                self.instance = self._args[0].unwrap()

        # override
        def to_representation(self, data):
            if not restriction.is_active(self.context):
                return super(ReturnFieldsListSerializer, self).to_representation(data)
            elif not restriction.setup(self.context, many=True) and not self.field_name:
                return super(ReturnFieldsListSerializer, self).to_representation(data)
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
