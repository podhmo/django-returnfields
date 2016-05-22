# -*- coding:utf-8 -*-
from collections import defaultdict, namedtuple
import django
# todo: fk_name
State = namedtuple("State", "field, is_relation, candidates, fk_name")
Hint = namedtuple("Hint", "name, state")
Result = namedtuple("Result", "name, for_select, for_join, children")


def tree():
    return defaultdict(tree)


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


class HintExtractor(object):
    def __init__(self):
        # model -> tree
        self.cache = {}

    def extract(self, model, name_list, with_relation=False):
        try:
            candidates = self.cache[model]
        except KeyError:
            candidates = self.cache[model] = extract_candidates(model)
        return self.drilldown(candidates, name_list, with_relation=with_relation)

    def drilldown(self, candidates, name_list, with_relation, parent_name=""):
        print("@", name_list, "@")
        for_select = []
        for_join = []
        relations = defaultdict(list)
        for name in name_list:
            s = candidates.get(name)
            if "__" not in name:
                if s is None:
                    continue
                for_select.append(Hint(name=name, state=s))
            else:
                k, sub_name = name.split("__", 1)
                relations[k].append(sub_name)

        children = []
        for k, sub_name_list in relations.items():
            s = candidates.get(k)
            if s is None:
                continue
            if with_relation:
                if s.fk_name is None:
                    if not s.candidates:
                        s = candidates[k] = new_state(s, extract_candidates(s.field.model))
                    for_join.append(self.drilldown(s.candidates, sub_name_list, with_relation, parent_name=k))
                    continue  # hmm
                else:
                    for_select.append(Hint(name=k, state=s))
            if not s.candidates:
                s = candidates[k] = new_state(s, extract_candidates(s.field.model))
            children.append(self.drilldown(s.candidates, sub_name_list, with_relation, parent_name=k))
        return Result(name=parent_name, for_select=for_select, for_join=for_join, children=children)


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
        if not s.fk_name:
            print(model, s.field.name)
        d[f.name] = s
    return d


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
