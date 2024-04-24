"""Read all E*Trade files and parse."""
import os
import sys

from .dividends import process_dividend_docs

from .common import merge_csvs

from .stocks import process_stock_docs


def parse_all_docs():
    """Figure out directory and run all functions on it."""
    dir_path = '.'
    if len(sys.argv) > 1:
        dir_path = sys.argv[1]
        if not os.path.isdir(dir_path):
            print('Provided path is not a directory')
            sys.exit(1)
    dir_path = os.path.abspath(dir_path)
    process_dividend_docs(dir_path)
    process_stock_docs(dir_path)

if __name__ == '__main__':

    parse_all_docs()
    merge_csvs()
