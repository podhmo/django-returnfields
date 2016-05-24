# -*- coding:utf-8 -*-
from collections import defaultdict, OrderedDict
import django

from .structures import Hint, TmpResult, Result


NOREL = ":norel:"
REL = ":rel:"
ALL = ":all:"


class HintIterator(object):
    def __init__(self, d, tokens):
        self.d = d
        self.tokens = tokens

    def parse_token(self, t):
        if t == ALL:
            for s in self.d.values():
                yield s
        elif t == REL:
            for s in self.d.values():
                if s.is_relation:
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
        self.cache = {}  # Dict[model, Hint]

    def extract(self, model):
        d = OrderedDict()
        for f in get_all_fields(model):
            name, is_relation, defer_name = f.name, f.is_relation, getattr(f, "attname", None)
            rel_name = None
            is_reverse_related = False
            rel_model = None
            if is_relation:
                if hasattr(f, "rel_class"):
                    is_reverse_related = True
                    rel_name = f.rel.get_accessor_name()
                    rel_model = f.rel.model
                else:
                    rel_name = f.field.name
                    rel_model = f.field.model
            d[f.name] = Hint(name=name,
                             is_relation=is_relation,
                             is_reverse_related=is_reverse_related,
                             rel_name=rel_name,
                             rel_model=rel_model,
                             defer_name=defer_name,
                             field=f)
            # hmm. supporting accessor_name? (e.g. `customerposition_set`)
            if hasattr(f, "get_accessor_name"):
                d[f.get_accessor_name()] = d[f.name]
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

    def __init__(self, sorted=True):
        # TODO
        self.sorted = sorted
        self.bidirectional = False
        self.hintmap = HintMap()

    def extract(self, model, name_list):
        tmp_result = self.drilldown(model, name_list, backref="")
        return self.classify(tmp_result)

    def seq(self, seq, key):
        return sorted(seq, key=key) if self.sorted else seq

    def classify(self, tmp_result):
        result = Result(name=tmp_result.name,
                        fields=[],
                        related=[],
                        reverse_related=[],
                        foreign_keys=[],
                        subresults=[])
        for h in self.seq(tmp_result.hints, key=lambda h: h.name):
            if not h.is_relation:
                result.fields.append(h)
                continue

            if h.defer_name is not None and not h.field.many_to_many:
                result.foreign_keys.append(h.defer_name)
            if h.is_reverse_related:
                result.reverse_related.append(h)
            else:
                result.related.append(h)
        for sr in self.seq(tmp_result.subresults, key=lambda r: r.name):
            result.subresults.append(self.classify(sr))
        return result

    def drilldown(self, model, name_list, backref, parent_name=""):
        hints = []
        names = []
        rels = defaultdict(list)
        for name in name_list:
            if name == self.ALL:
                names.append(NOREL)
            elif "__" not in name:
                names.append(name)
            else:
                prefix, sub_name = name.split("__", 1)
                rels[prefix].append(sub_name)

        iterator = self.hintmap.iterator(model, names)
        for hint in iterator:
            hints.append(hint)

        subresults = []
        for prefix, sub_name_list in rels.items():
            if prefix == self.ALL:
                prefix = REL
            for hint in iterator.clone([prefix]):
                if hint.name == backref:
                    print("skip {}".format(backref))
                hints.append(hint)
                subresults.append(
                    self.drilldown(
                        hint.rel_model, sub_name_list,
                        backref=hint.rel_name, parent_name=hint.name
                    )
                )
        return TmpResult(name=parent_name, hints=hints, subresults=subresults)


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
            for subresult in result.subresults:
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
            for subresult in result.subresults:
                names.append(subresult.name)
                rec(subresult, names)
                names.pop()
        rec(result, [result.name])
        return r

    def collect_without_defer_name_fields(self, model):
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
