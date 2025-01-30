"""Implement common functions for files processing."""

import glob
import json
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
    # PdfReader shouts errors
    # "Advanced encoding /NULL not implemented yet"
    # because encoding is incorrectly set in new pdf trade files
    # starting 2024
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
    files_list = glob.glob("_*.csv")
    xlsck.merge_all_to_a_book(files_list, "etrade.xlsx")
    for file_name in files_list:
        os.remove(file_name)


def write_objects_debug_json(data: dict, filename: str):
    """Save created objects for debug purposes."""
    out = {}
    for key, value in data.items():
        out[key] = [obj.__dict__ for obj in value]
    with open(filename, "w", encoding="utf-8") as fil:
        json.dump(out, fil, sort_keys=True, ensure_ascii=False, indent=4, default=str)
