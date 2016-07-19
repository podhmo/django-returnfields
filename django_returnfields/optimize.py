import logging
from collections import OrderedDict
from . import aggressive
from . import constants

logger = logging.getLogger(__name__)
DECORATE_KEY = "_drf_decorated"


class StaticToken(object):
    def __init__(self, translator, name, nested, queryname):
        self.translator = translator
        self.name = name
        self.nested = nested
        self.queryname = queryname

    def renamed(self, fullname, fullqueryname):
        return self.__class__(self, name=fullname, nested=self.nested, queryname=fullqueryname)

    def __call__(self, context):
        return self.queryname


class RelatedToken(object):
    def __init__(self, translator, name, nested, queryname, mapping):
        self.translator = translator
        self.name = name
        self.nested = nested
        self.queryname = queryname
        self.mapping = mapping

    def renamed(self, fullname, fullqueryname):
        return self.__class__(self, name=fullname, nested=self.nested, queryname=fullqueryname, mapping=self.mapping)

    def __call__(self, context):
        return ["{}__{}".format(self.queryname, t(context)) for t in self.mapping.values()]


class DynamicToken(object):
    def __init__(self, translator, name, nested, queryname, fn):
        self.translator = translator
        self.name = name
        self.nested = nested
        self.queryname = queryname
        self.fn = fn

    def renamed(self, fullname, fullqueryname):
        return self.__class__(self, name=fullname, nested=self.nested, queryname=fullqueryname, fn=self.fn)

    # with decorators
    def __call__(self, context):
        return self.fn(self, context)


class QueryOptimizer(object):
    view_aggressive_query_method_name = "aggressive_queryset"

    def __init__(self, restriction, translator=None):
        self.restriction = restriction
        self.translator = translator or NameListTranslator()

    def optimize_query(self, context, instance, serializer_class):
        qs = self._as_query(context, instance)
        optimized_qs = self._optimize_query(context, qs, serializer_class)
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
            # re-attach filter
            if hasattr(view, "filter_queryset"):
                qs = view.filter_queryset(qs)
        return qs

    def _optimize_query(self, context, query, serializer_class):
        if not hasattr(query, "all"):
            logger.warning("%s doen't have all method. this is not query", query)
            return query

        frame = self.restriction.frame_management.current_frame(context)

        skip_list = frame.get(self.restriction.exclude_key, None)
        name_list = frame.get(self.restriction.include_key, None)
        name_list = self.translator.translate(serializer_class, name_list, context)
        aqs = aggressive.aggressive_query(
            query,
            name_list=name_list,
            skip_list=skip_list
        )
        # custom hook
        if "view" in context:
            view = context["view"]
            custom_fn_by_view = getattr(view, self.view_aggressive_query_method_name, None)
            if custom_fn_by_view:
                aqs = custom_fn_by_view(aqs)
        return aqs


class NameListTranslator(object):
    ALL_LIST = [constants.ALL]

    def __init__(self):
        self.fields_cache = {}  # <Serializer class> -> (str -> <Field>)
        self.mapping_cache = {}  # <Serializer class> -> (str -> <Token>)

    def translate(self, serializer_class, name_list, context, include_all=False):
        if name_list == self.ALL_LIST:
            name_list = None
        mapping = self.get_mapping(serializer_class)
        if name_list:
            return flatten1(mapping[name](context) for name in name_list if name in mapping)
        elif include_all:
            return flatten1(token(context) for token in mapping.values())
        else:
            return flatten1(token(context) for token in mapping.values() if not token.nested)

    def all_name_list(self, serializer_class):
        return self.translate(serializer_class, None, {})

    def get_mapping(self, serializer_class):
        mapping = self.mapping_cache.get(serializer_class)
        if mapping is None:
            mapping = self.mapping_cache[serializer_class] = self._get_mapping(serializer_class)
        return mapping

    def get_fields(self, serializer_class):
        fields = self.fields_cache.get(serializer_class)
        if fields is None:
            fields = self.fields_cache[serializer_class] = serializer_class().get_fields()
        return fields

    def get_decoration(self, serializer_class, name, field):
        return get_decoration(serializer_class, name, field)

    def _get_queryname(self, field, name):
        if field.source and field.source != "*":
            # field.source == "*" when field extends HyperlinkedIdentityField.
            return field.source
        else:
            return name

    def _get_mapping(self, serializer_class):
        fields = self.get_fields(serializer_class)
        d = OrderedDict()
        # todo: supporting SerializerMethodField
        for name, field in fields.items():
            if field.write_only:
                continue

            # decorated field
            token_factory = self.get_decoration(serializer_class, name, field)
            if token_factory is not None:
                d[name] = token_factory(self, name)
                continue

            if hasattr(field, "child"):
                field = field.child  # ListSerialier -> Serializer
            if hasattr(field, "child_relation"):  # ModelField
                cr = field.child_relation
                queryname = self._get_queryname(field, name)
                subname = getattr(cr, "lookup_field", None) or cr.queryset.model._meta.pk.name
                fullqueryname = "{}__{}".format(queryname, subname)
                fullname = "{}__{}".format(name, subname)
                token = StaticToken(self, name=name, nested=False, queryname=fullqueryname)
                d[fullname] = token
            elif hasattr(field, "_declared_fields"):  # sub Serializer
                mapping = self.get_mapping(field.__class__)
                queryname = self._get_queryname(field, name)
                token = RelatedToken(self, name=name, nested=True, queryname=queryname, mapping=mapping)
                for subname, stoken in mapping.items():
                    fullqueryname = "{}__{}".format(token.queryname, stoken.queryname)
                    fullname = "{}__{}".format(token.name, subname)
                    d[fullname] = stoken.renamed(fullname, fullqueryname)
                d[name] = token
            else:
                queryname = self._get_queryname(field, name)
                token = StaticToken(self, name=queryname, nested=False, queryname=queryname)
                d[name] = token
        return d


def flatten1(xs):
    r = []
    for x in xs:
        if isinstance(x, (list, tuple)):
            r.extend(x)
        else:
            r.append(x)
    return r


# decorators
def get_decoration(serializer_class, name, serializer_method_field):
    # xxx: only support SerializerMethodField
    method = getattr(serializer_class, "get_{}".format(name), None)
    if method is None:
        return method
    return getattr(method, DECORATE_KEY, None)


def set_decoration(serialiezer_method, fn):
    setattr(serialiezer_method, DECORATE_KEY, fn)


def depends(on=[], nested=False):
    def _depends(field):
        fn = lambda token, context: on
        factory = lambda translator, name: DynamicToken(translator, name, nested, name, fn)
        set_decoration(field, factory)
        return field
    return _depends


def contextual(fn, nested=False):
    def _contextual(field):
        set_decoration(field, lambda translator, name: DynamicToken(translator, name, nested, name, fn))
        return field
    return _contextual
