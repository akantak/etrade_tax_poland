"""Read all E*Trade files and parse."""

from .args import parse_args
from .dividends import process_dividend_docs
from .files_handling import merge_csvs
from .stocks import process_stock_docs


def parse_all_docs(dir_path, debug=False):
    """Figure out directory and run all functions on it."""
    process_dividend_docs(dir_path, debug)
    process_stock_docs(dir_path, debug)


if __name__ == "__main__":
    args = parse_args()
    parse_all_docs(args.dirpath, debug=args.debug)
    if not args.no_xlsx:
        merge_csvs()
