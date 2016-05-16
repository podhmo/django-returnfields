# -*- coding:utf-8 -*-
from collections import defaultdict, namedtuple
import django
State = namedtuple("State", "field, is_relation, candidates")


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
        collected = []
        relations = defaultdict(list)
        for name in name_list:
            s = candidates.get(name)
            if "__" not in name:
                if s is None:
                    continue
                collected.append(name)
            else:
                k, sub_name = name.split("__", 1)
                relations[k].append(sub_name)
                if with_relation and s is not None:
                    collected.append(k)
        for k, sub_name_list in relations.items():
            s = candidates.get(k)
            if s is None:
                continue
            if not s.candidates:
                s = candidates[k] = new_state(s, extract_candidates(s.field.model))
            sub_collected = self.drilldown(s.candidates, sub_name_list, with_relation)
            collected.extend(["__".join([k, suffix]) for suffix in sub_collected])
        return collected


def new_state(s, candidates):
    return State(field=s.field, is_relation=s.is_relation, candidates=candidates)


if django.VERSION >= (1, 8):
    def get_all_fields(m):
        return m._meta.get_fields()
else:
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
        if not hasattr(f, "attname"):
            # print("model: {}.{} does not have attname".format(model, f))
            continue
        s = State(field=f, is_relation=f.is_relation, candidates=None)
        d[f.name] = s
    return d


default_name_collector = CorrectNameCollector()


def safe_only(qs, name_list, collector=default_name_collector):
    fields = collector.collect(qs.model, name_list, with_relation=True)
    return qs.only(*fields)


def safe_defer(qs, name_list, collector=default_name_collector):
    fields = collector.collect(qs.model, name_list, with_relation=False)
    return qs.defer(*fields)
