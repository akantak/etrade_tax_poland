"""Implement common functions for etrade documents processing."""
import datetime
import glob
import os
from time import sleep

from pypdf import PdfReader

import requests

NBP_URL = 'https://api.nbp.pl/api/exchangerates/rates/a/usd/{}/?format=json'
TAX_PL = 0.19


def pdfs_in_dir(directory):
    """Get all PDF statements files."""
    os.chdir(directory)
    return glob.glob('*.pdf')


def file_to_text(filename):
    """Parse PDF file to text only."""
    reader = PdfReader(filename)
    text = ''
    for page in reader.pages:
        text += page.extract_text() + '\n'
    return text


def date_to_usd_pln(date_obj):
    """Find 'day before vestment' USD/PLN ratio."""
    date_obj -= datetime.timedelta(days=1)
    while True:
        try:
            req = requests.get(NBP_URL.format(date_obj.strftime('%Y-%m-%d')), timeout=5)
        except requests.exceptions.ConnectTimeout:
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
            raise NotImplementedError('Not handled case during getting USD/PLN ratio')


def save_csv(filename, header, lines):
    """Save header and lines to a csv file."""
    if not lines:
        return
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(f'{header}\n')
        for line in lines:
            file.write(f'{line}\n')


def sum_file_header():
    """Return sum csv file header."""
    return ','.join([
        'NAME',
        'VALUE',
        'PIT_FIELD',
    ])
