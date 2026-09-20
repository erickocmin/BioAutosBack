"""Reconciliation primitives: counts, sums and relationship checks."""


def reconcile_count(source_count, target_count):
    return {"source": source_count, "target": target_count, "matches": source_count == target_count}
