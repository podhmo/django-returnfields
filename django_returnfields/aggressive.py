# -*- coding:utf-8 -*-
from collections import defaultdict, namedtuple

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
                if with_relation:
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


def extract_candidates(model):
    d = tree()
    for f in model._meta.get_fields():
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
