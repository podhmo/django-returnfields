# -*- coding:utf-8 -*-
from collections import defaultdict, namedtuple
import django
# todo: fk_name
Hint = namedtuple(
    "Hint",
    "name, is_relation, fk_name, field"
)
TmpResult = namedtuple(
    "TmpResult",
    "name, current, children"
)


def tree():
    return defaultdict(tree)

NOREL = ":norel:"
REL = ":rel:"
ALL = ":all:"

Result = namedtuple(
    "Result",
    "fields, one_to_onerel, onerel_to_one, one_to_many, many_to_one, many_to_manyrel, manyrel_to_many"
)


def repr_result(self):
    values = []
    for k, v in self._asdict().items():
        if v:
            values.append("{}={!r}".format(k, v))
    return "{}({})".format(self.__class__.__name__, ", ".join(values))
Result.__repr__ = repr_result


class HintIterator(object):
    def __init__(self, d, tokens):
        self.d = d
        self.tokens = tokens

    def parse_token(self, t):
        if t == ALL:
            for s in self.d.values():
                yield s
        elif t == NOREL:
            for s in self.d.values():
                if not s.is_relation:
                    yield s
        else:
            s = self.d.get(t)
            if s is not None:
                yield s

    def clone(self, tokens):
        return self.__class__(self.d, tokens)

    def __iter__(self):
        hist = set()
        for t in self.tokens:
            for s in self.parse_token(t):
                if s not in hist:
                    hist.add(s)
                    yield s


class HintMap(object):
    iterator_cls = HintIterator

    def __init__(self):
        # model -> tree
        self.cache = {}

    def extract(self, model):
        d = tree()
        for f in get_all_fields(model):
            # if not hasattr(f, "attname"):
            #     # print("model: {}.{} does not have attname".format(model, f))
            #     continue
            s = Hint(
                name=f.name,
                is_relation=f.is_relation,
                fk_name=getattr(f, "attname", None),
                field=f,
            )
            d[f.name] = s
        return d

    def load(self, model):
        d = self.cache.get(model)
        if d is None:
            d = self.cache[model] = self.extract(model)
        return d

    def iterator(self, model, tokens):
        return self.iterator_cls(self.load(model), tokens)


class HintExtractor(object):
    ALL = "*"

    def __init__(self):
        self.hintmap = HintMap()

    def extract(self, model, name_list, with_relation=False):
        return self.drilldown(model, name_list, with_relation=with_relation)

    def classify(self, hint):
        print(dir(hint.field))

    def drilldown(self, model, name_list, with_relation, parent_name=""):
        hints = []
        names = []
        rels = defaultdict(list)
        for name in names:
            if self.ALL == name:
                names.append(NOREL)
            elif "__" not in name:
                names.append(name)
            else:
                prefix, sub_name = name.split("__", 1)
                if self.ALL == prefix:
                    names.append(REL)
                rels[prefix].append(sub_name)

        existing_rels = []
        iterator = self.hintmap.iterator(model, names)
        for hint in iterator:
            hints.append(hint)
            if hint.is_relation:
                existing_rels.append(hint)

        children = []
        for hint in existing_rels:
            children.append(self.drilldown(hint.field.model, rels[hint.name], with_relation, parent_name=hint.name))
        return TmpResult(name=parent_name, current=hints, children=children)


def new_hint(s, hint):
    return Hint(
        field=s.field,
        is_relation=s.is_relation,
        hint=hint,
        fk_name=s.fk_name
    )


if django.VERSION >= (1, 8):
    def get_all_fields(m):
        return m._meta.get_fields()
else:
    # planning to drop 1.7
    from django.db.models.fields.related import RelatedField

    class FieldAdapter(object):
        def __init__(self, f):
            self.f = f
            self.is_relation = isinstance(f, RelatedField)

        def __getattr__(self, k):
            return getattr(self.f, k)

    def get_all_fields(m):
        xs = [m._meta._name_map.get(name, None)[0] for name in m._meta.get_all_field_names()]
        return [FieldAdapter(x) for x in xs if x]


class Inspector(object):
    def collect_for_select_names(self, result):
        r = []

        def rec(result, names):
            for hint in result.for_select:
                names.append(hint.name)
                r.append("__".join(names[1:]))
                names.pop()
            for subresult in result.children:
                names.append(subresult.name)
                rec(subresult, names)
                names.pop()
        rec(result, [result.name])
        return r

    def collect_for_join_names(self, result):
        r = []

        def rec(result, names):
            for hint in result.for_join:
                names.append(hint.name)
                r.append("__".join(names[1:]))
                names.pop()
            for subresult in result.children:
                names.append(subresult.name)
                rec(subresult, names)
                names.pop()
        rec(result, [result.name])
        return r

    def collect_without_fk_name_fields(self, model):
        return [f for f in get_all_fields(model) if not getattr(f, "attname", None)]


default_hint_extractor = HintExtractor()


def safe_only(qs, name_list, extractor=default_hint_extractor):
    pair = extractor.extract(qs.model, name_list, with_relation=True)
    if qs.query.select_related or qs._prefetch_related_lookups:
        qs = qs._clone()
        s = set(pair.for_join)
        s.update(pair.for_select)
        if qs.query.select_related and hasattr(qs.query.select_related, "items"):
            qs.query.select_related = {k: v for k, v in qs.query.select_related.items() if k in s}
            s.update(qs.query.select_related.keys())
        if qs._prefetch_related_lookups:
            qs._prefetch_related_lookups = [k for k in qs._prefetch_related_lookups if k in s]
    return qs.only(*pair.for_select)


def safe_defer(qs, name_list, extractor=default_hint_extractor):
    pair = extractor.extract(qs.model, name_list, with_relation=False)
    if qs.query.select_related or qs._prefetch_related_lookups:
        qs = qs._clone()
        s = set(pair.for_join)
        s.update(pair.for_select)
        if qs.query.select_related and hasattr(qs.query.select_related, "items"):
            qs.query.select_related = {k: v for k, v in qs.query.select_related.items() if k not in s}
            s.update(qs.query.select_related.keys())
        if qs._prefetch_related_lookups:
            qs._prefetch_related_lookups = [k for k in qs._prefetch_related_lookups if k not in s]
    return qs.defer(*pair.for_select)


def revive_query(query_or_extraction):
    if hasattr(query_or_extraction, "query"):
        return query_or_extraction, True
    elif isinstance(query_or_extraction, (list, tuple)) and not len(query_or_extraction) == 0:
        pks = [x.pk for x in query_or_extraction]
        # order by is dropped..
        return query_or_extraction[0].__class__.objects.filter(pk__in=pks), True
    else:
        return query_or_extraction, False
