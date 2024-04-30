"""Common variables and functions."""

import math

TAX_PL = 0.19
ISO_DATE = "%Y-%m-%d"


def round_up(number):
    """Round number up to the second decimal point."""
    return math.ceil(number * 100) / 100


def cash_float(str_number):
    """Cast cash string with many additional chars to float."""
    # cash formats:
    # ['1,000.00', '$100.00', '(100.00)', '($2.00)']
    for char in "$,()":
        str_number = str_number.replace(char, "")
    return float(str_number)
