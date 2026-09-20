"""Pure transformations from legacy rows to the approved target model."""


def normalize_text(value):
    return " ".join((value or "").strip().split())
