# -*- coding:utf-8 -*-
from collections import defaultdict, namedtuple
import django
# todo: fk_name
State = namedtuple("State", "field, is_relation, candidates, fk_name")
Pair = namedtuple("Pair", "for_select, for_join")


def tree():
    return defaultdict(tree)


class CorrectNameCollector(object):
    def __init__(self):
        # model -> tree
        self.cache = {}

    def collect(self, model, name_list, with_relation=False):
        try:
            candidates = self.cache[model]
        except KeyError:
            candidates = self.cache[model] = extract_candidates(model)
        return self.drilldown(candidates, name_list, with_relation=with_relation)

    def drilldown(self, candidates, name_list, with_relation):
        for_select = []
        for_join = []
        relations = defaultdict(list)
        for name in name_list:
            s = candidates.get(name)
            if "__" not in name:
                if s is None:
                    continue
                for_select.append(name)
            else:
                k, sub_name = name.split("__", 1)
                relations[k].append(sub_name)

        for k, sub_name_list in relations.items():
            s = candidates.get(k)
            if s is None:
                continue
            if with_relation:
                if s.fk_name is None:
                    for_join.append(k)
                    continue  # hmm
                else:
                    for_select.append(k)
            if not s.candidates:
                s = candidates[k] = new_state(s, extract_candidates(s.field.model))
            pair = self.drilldown(s.candidates, sub_name_list, with_relation)
            for_select.extend(["__".join([k, suffix]) for suffix in pair.for_select])
            for_join.extend(["__".join([k, suffix]) for suffix in pair.for_join])
        return Pair(for_select=for_select, for_join=for_join)


def new_state(s, candidates):
    return State(
        field=s.field,
        is_relation=s.is_relation,
        candidates=candidates,
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


def extract_candidates(model):
    d = tree()
    for f in get_all_fields(model):
        # if not hasattr(f, "attname"):
        #     # print("model: {}.{} does not have attname".format(model, f))
        #     continue
        s = State(
            field=f,
            is_relation=f.is_relation,
            candidates=None,
            fk_name=getattr(f, "attname", None)
        )
        d[f.name] = s
    return d


default_name_collector = CorrectNameCollector()


def safe_only(qs, name_list, collector=default_name_collector):
    pair = collector.collect(qs.model, name_list, with_relation=True)
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


def safe_defer(qs, name_list, collector=default_name_collector):
    pair = collector.collect(qs.model, name_list, with_relation=False)
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
