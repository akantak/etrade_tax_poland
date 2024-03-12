"""Read all E*Trade files and parse."""
import os
import sys

from dividends import count_dividend_taxes

from stocks import process_stocks_docs


def all_taxes():
    """Figure out directory and run all functions on it."""
    dir_path = '.'
    if len(sys.argv) > 1:
        dir_path = sys.argv[1]
        if not os.path.isdir(dir_path):
            print('Provided path is not a directory')
            sys.exit(1)
    count_dividend_taxes(dir_path)
    process_stocks_docs(dir_path)


all_taxes()
