# -*- coding:utf-8 -*-
from collections import namedtuple


Hint = namedtuple(
    "Hint",
    "name, is_relation, is_reverse_related, rel_name, defer_name, rel_model, field"
)
TmpResult = namedtuple(
    "TmpResult",
    "name, hints, subresults"
)
Result = namedtuple(
    "Result",
    "name, fields, related, reverse_related, foreign_keys, subresults"
)


def asdict_result(self):
    if not hasattr(self, "_asdict"):
        raise Exception("{!r} is not namedtuple".format(self))
    d = self._asdict()
    for k, v in d.items():
        if hasattr(v, "asdict"):
            d[k] = v.asdict()
        elif isinstance(v, (list, tuple)):
            d[k] = [sv.asdict() if hasattr(sv, "asdict") else sv for sv in v]
    return d


def repr_result(self):
    values = []
    for k, v in self._asdict().items():
        if v:
            values.append("{}={!r}".format(k, v))
    return "{}({})".format(self.__class__.__name__, ", ".join(values))
Result.__repr__ = repr_result
Result.asdict = asdict_result


def asdict_hint(self):
    d = self._asdict()
    d.pop("field")
    model = d.pop("rel_model", None)
    if model:
        d["_classname"] = model.__name__
    return d


def repr_hint(self):
    return "{}(name={!r})".format(self.__class__.__name__, self.name)


Hint.__repr__ = repr_hint
Hint.asdict = asdict_hint
