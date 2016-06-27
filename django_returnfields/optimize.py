import logging
from collections import namedtuple
from collections import OrderedDict
from . import aggressive
from . import constants

logger = logging.getLogger(__name__)
Token = namedtuple("Token", "name, nested, queryname")


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
    ALL_LIST = [constants.ALL]

    def __init__(self):
        self.fields_cache = {}  # hmm
        self.mapping_cache = {}

    def translate(self, serializer_class, name_list):
        if name_list == self.ALL_LIST:
            name_list = None
        mapping = self.get_mapping(serializer_class)
        if name_list:
            return flatten1(mapping[name].queryname for name in name_list if name in mapping)
        else:
            return flatten1(token.queryname for token in mapping.values() if not token.nested)

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
                token = Token(name=name, nested=True, queryname=["{}__*".format(name), "{}__*__*".format(name)])
                d[token.name] = token
                for subname, stoken in self.get_mapping(field.__class__).items():
                    fullname = "{}__{}".format(name, subname)
                    token = Token(name=fullname, nested=False, queryname=fullname)
                    d[token.queryname] = token
            else:
                token = Token(name=name, nested=False, queryname=name)
                d[token.queryname] = token
        return d


def flatten1(xs):
    r = []
    for x in xs:
        if isinstance(x, (list, tuple)):
            r.extend(x)
        else:
            r.append(x)
    return r
