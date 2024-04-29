"""Common variables and functions."""

import math

TAX_PL = 0.19
ISO_DATE = "%Y-%m-%d"


def round_up(number):
    """Round number up to the second decimal point."""
    return math.ceil(number * 100) / 100
