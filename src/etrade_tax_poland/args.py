"""Parse CLI arguments."""

import argparse
import os
import sys


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("dirpath", nargs="?", default=".", help="Get statements path")
    parser.add_argument("-x", "--no-xlsx", action="store_true")
    args = parser.parse_args()
    if not os.path.isdir(args.dirpath):
        print("Provided path is not a directory")
        sys.exit(1)
    args.dirpath = os.path.abspath(args.dirpath)
    return args
