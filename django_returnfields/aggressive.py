import logging
from django_aggressivequery import from_queryset


logger = logging.getLogger(__name__)


def aggressive_query(qs, name_list, skip_list=None):
    assert qs.model
    aqs = from_queryset(qs, name_list, more_specific=True)
    if skip_list:
        aqs = aqs.skip_filter(skip_list)
    return aqs


def revive_query(query_or_extraction):
    if hasattr(query_or_extraction, "query"):
        return query_or_extraction, True
    elif isinstance(query_or_extraction, (list, tuple)) and not len(query_or_extraction) == 0:
        pks = [x.pk for x in query_or_extraction]
        # order by is dropped..
        return query_or_extraction[0].__class__.objects.filter(pk__in=pks), True
    elif hasattr(query_or_extraction, "_meta"):
        ob = query_or_extraction
        pk = ob._meta.pk.name
        try:
            return ob.__class__.objects.filter(**{pk: getattr(ob, pk)}), True
        except Exception:
            logger.warning("unsupported type. ignored", exc_info=True)
    else:
        return query_or_extraction, False
