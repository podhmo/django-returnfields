# -*- coding:utf-8 -*-
from collections import defaultdict, namedtuple

State = namedtuple("State", "field, is_relation, candidates")


def tree():
    return defaultdict(tree)


class CorrectNameCollector(object):
    def __init__(self):
        # model -> tree
        self.cache = {}

    def collect(self, model, name_list):
        try:
            candidates = self.cache[model]
        except KeyError:
            candidates = self.cache[model] = self.load_candidates(model)
        return self.drilldown(candidates, name_list)

    def drilldown(self, candidates, name_list):
        r = []
        relations = defaultdict(list)
        for name in name_list:
            if "__" not in name:
                if name not in candidates:
                    continue
                r.append(name)
            else:
                k, subname = name.split("__", 1)
                relations[k].append(subname)
        for k, sub_name_list in relations.items():
            s = candidates.get(k)
            if s is None:
                continue
            if not s.candidates:
                candidates[k] = self.load_candidates(s.field.model)
            r.extend(self.drilldown(s.candidates, sub_name_list))
        return r

    def load_candidates(self, model):
        d = tree()
        for f in model._meta.get_fields():
            if f.is_relation:
                s = State(field=f, is_relation=True, candidates=tree())
            else:
                s = State(field=f, is_relation=False, candidates=None)
            d[f.name] = s
            if hasattr(f, "attrname"):
                d[f.attname] = s
        return d


default_name_collector = CorrectNameCollector()


def safe_only(qs, name_list, collector=default_name_collector):
    fields = collector.collect(qs.model, name_list)
    return qs.only(*fields)


def safe_defer(qs, name_list, collector=default_name_collector):
    fields = collector.collect(qs.model, name_list)
    return qs.defer(*fields)
