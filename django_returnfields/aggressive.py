# -*- coding:utf-8 -*-
import itertools
import sys
import json
import logging
from collections import defaultdict, OrderedDict
import django
from django.db.models.fields import related
from django.db.models.fields import reverse_related
from django.utils.functional import cached_property
from .structures import Hint, TmpResult, Result


logger = logging.getLogger(__name__)

NOREL = ":norel:"
REL = ":rel:"
ALL = ":all:"


class HintIterator(object):
    def __init__(self, d, tokens, history=None):
        self.d = d
        self.tokens = tokens
        self.history = history or set()

    def parse_token(self, t):
        if t == ALL:
            for s in self.d.values():
                yield s, False
        elif t == REL:
            for s in self.d.values():
                if s.is_relation:
                    yield s, False
        elif t == NOREL:
            for s in self.d.values():
                if not s.is_relation:
                    yield s, False
        else:
            s = self.d.get(t)
            if s is not None:
                yield s, True

    def clone(self, tokens):
        return self.__class__(self.d, tokens)

    def __iter__(self):
        for t in self.tokens:
            for s, selected in self.parse_token(t):
                if s not in self.history:
                    self.history.add(s)
                    yield s, selected


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
        for hint, _ in iterator:
            hints.append(hint)

        subresults_dict = OrderedDict()
        for prefix, sub_name_list in rels.items():
            if prefix == self.ALL:
                prefix = REL
            for hint, selected in iterator.clone([prefix]):
                if not selected and hint.name == backref:
                    logger.info("skip %s".format(backref))
                    continue
                hints.append(hint)
                self._merge(
                    subresults_dict,
                    self.drilldown(
                        hint.rel_model, sub_name_list,
                        backref=hint.rel_name, parent_name=hint.name
                    )
                )
        return TmpResult(name=parent_name, hints=hints, subresults=list(subresults_dict.values()))

    def _merge(self, d, r):
        if r.name not in d:
            d[r.name] = r
        else:
            cr = d[r.name]
            cr.hints.extend(r.hints)
            cr.subresults.extend(r.subresults)


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
    def __init__(self, hintmap=None):
        self.hintmap = hintmap

    def depth(self, result, i=1):
        if not result.subresults:
            return i
        else:
            return max(self.depth(r, i + 1) for r in result.subresults)
    """\
one_to_onerel customer <class 'django.db.models.fields.related.OneToOneField'>
many_to_one order <class 'django.db.models.fields.related.ForeignKey'>
onerel_to_one karma <class 'django.db.models.fields.reverse_related.OneToOneRel'>
manyrel_to_many orders <class 'django.db.models.fields.reverse_related.ManyToManyRel'>
many_to_manyrel customers <class 'django.db.models.fields.related.ManyToManyField'>
one_to_many items <class 'django.db.models.fields.reverse_related.ManyToOneRel'>
"""
    # todo: performance
    def collect_joins(self, result):
        # can join: one to one*, one* to one, many to one
        xs = [h.name for h in result.related if isinstance(h.field.field, (related.OneToOneField, related.ForeignKey))]
        ys = [h.name for h in result.reverse_related if isinstance(h.field.rel, (reverse_related.OneToOneRel))]
        return itertools.chain(xs, ys)

    def collect_selections(self, result):
        xs = [f.name for f in result.fields]
        ys = []
        related_mapping = {h.name: h.rel_model for h in result.related}
        for sr in result.subresults:
            if sr.name in related_mapping:
                # this is limitation. for django's compiler.
                sub_fields = (h.name for h in self.hintmap.iterator(related_mapping[sr.name], NOREL))
            else:
                sub_fields = self.collect_selections(sr)
            ys.append(["{}__{}".format(sr.name, name) for name in sub_fields])
        return itertools.chain(xs, *ys)


default_hint_extractor = HintExtractor()


class AggressiveQuery(object):
    def __init__(self, queryset, result, hintmap):
        self.queryset = queryset
        self.result = result
        self.inspector = Inspector(hintmap)

    @property
    def query(self):
        return self.aggressive_queryset.query

    @cached_property
    def aggressive_queryset(self):
        return self.optimize(self.queryset)

    def optimize(self, qs):
        return self._optimize_join(
            self._optimize_selections(qs.all())
        )

    def _optimize_selections(self, qs):
        fields = list(self.inspector.collect_selections(self.result))
        print(fields, "@fields")
        return qs.only(*fields)

    def _optimize_join(self, qs):
        if not (qs.query.select_related and hasattr(qs.query.select_related, "items")):
            return qs
        join_targets = self.inspector.collect_joins(self.result)
        print(join_targets, "@join")
        qs.query.select_related = {k: {} for k in join_targets}  # hmm.
        print(qs.query.select_related, "@@join")
        return qs

    def pp(self, out=sys.stdout):
        d = self.result.asdict()
        return out.write(json.dumps(d, indent=2))


def safe_only(qs, name_list, extractor=default_hint_extractor):
    result = extractor.extract(qs.model, name_list)
    return AggressiveQuery(qs, result, extractor.hintmap)
    # if qs.query.select_related or qs._prefetch_related_lookups:
    #     qs = qs._clone()
    #     s = set(pair.for_join)
    #     s.update(pair.for_select)
    #     if qs.query.select_related and hasattr(qs.query.select_related, "items"):
    #         qs.query.select_related = {k: v for k, v in qs.query.select_related.items() if k in s}
    #         s.update(qs.query.select_related.keys())
    #     if qs._prefetch_related_lookups:
    #         qs._prefetch_related_lookups = [k for k in qs._prefetch_related_lookups if k in s]
    # return qs.only(*pair.for_select)


def revive_query(query_or_extraction):
    if hasattr(query_or_extraction, "query"):
        return query_or_extraction, True
    elif isinstance(query_or_extraction, (list, tuple)) and not len(query_or_extraction) == 0:
        pks = [x.pk for x in query_or_extraction]
        # order by is dropped..
        return query_or_extraction[0].__class__.objects.filter(pk__in=pks), True
    else:
        return query_or_extraction, False
