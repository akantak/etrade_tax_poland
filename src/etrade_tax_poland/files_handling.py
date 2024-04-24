"""Implement common functions for files processing."""

import glob
import os

import pyexcel.cookbook as xlsck
from pypdf import PdfReader


def pdfs_in_dir(directory):
    """Get all PDF statements files."""
    os.chdir(directory)
    return glob.glob("*.pdf")


def file_to_text(filename):
    """Parse PDF file to text only."""
    reader = PdfReader(filename)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def save_csv(filename, header, lines):
    """Save header and lines to a csv file."""
    if not lines:
        return
    with open(filename, "w", encoding="utf-8") as file:
        file.write(f"{header}\n")
        for line in lines:
            file.write(f"{line}\n")


def merge_csvs():
    """Merge csvs into xlsx and remove them."""
    files_list = glob.glob("*.csv")
    xlsck.merge_all_to_a_book(files_list, "etrade.xlsx")
    for file_name in files_list:
        os.remove(file_name)


def sum_header():
    """Return sum csv file header."""
    return ",".join(
        [
            "NAME",
            "VALUE",
            "PIT_FIELD",
        ]
    )
