"""Implement common functions for etrade documents processing."""
import datetime
import glob
import os
from time import sleep

from pypdf import PdfReader

import requests

NBP_URL = 'https://api.nbp.pl/api/exchangerates/rates/a/usd/{}/?format=json'
TAX_PL = 0.19


def get_all_pdf_files(directory):
    """Get all PDF statements files."""
    os.chdir(directory)
    return glob.glob('*.pdf')


def get_text_from_file(filename):
    """Parse PDF file to text only."""
    reader = PdfReader(filename)
    text = ''
    for page in reader.pages:
        text += page.extract_text() + '\n'
    return text


def get_usd_pln_ratio(date_obj):
    """Find 'day before vestment' USD/PLN ratio."""
    date_obj -= datetime.timedelta(days=1)
    while True:
        try:
            req = requests.get(NBP_URL.format(date_obj.strftime('%Y-%m-%d')), timeout=5)
        except Exception:
            print('Failed getting USD/PLN ratio in 5 seconds, retrying after 1 second')
            sleep(1)
            continue
        if req.status_code == 200:
            return (
                date_obj,
                req.json()['rates'][0]['mid'],
            )
        if req.status_code == 404 and req.text == '404 NotFound - Not Found - Brak danych':
            date_obj -= datetime.timedelta(days=1)
        else:
            print(f'{req.status_code} {req.text}')
            raise Exception('Not handled case during getting USD/PLN ratio')


def save_csv(filename, header, objects):
    """
    Save header and objects to a csv file.

    Objects have to implement .get_csved_object() method
    """
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(f'{header}\n')
        for obj in objects:
            file.write(f'{obj.get_csved_object()}\n')


def save_txt(filename, lines_list):
    """Save lines to a txt file."""
    with open(filename, 'w', encoding='utf-8') as file:
        for line in lines_list:
            file.write(f'{line}\n')
