"""Skeleton: idempotent MySQL loading will be implemented per approved domain."""


def load_in_batches(model, objects, batch_size=1000):
    return model.objects.bulk_create(objects, batch_size=batch_size, ignore_conflicts=False)
