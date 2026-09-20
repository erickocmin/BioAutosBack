"""Skeleton: extract selected legacy rows in deterministic batches; no production transfer yet."""


def extract(connection, query, batch_size=1000):
    with connection.cursor(name="sisgetran_etl") as cursor:
        cursor.itersize = batch_size
        cursor.execute(query)
        yield from cursor
