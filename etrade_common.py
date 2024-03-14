"""Implement common functions for etrade documents processing."""
import datetime
import glob
import json
import os
from time import sleep

from pypdf import PdfReader

import requests

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


class NbpRatiosCache():
    """Cache data instead of always requesting from NBP."""

    def __init__(self):
        """Initialize objects and fields."""
        self.date_format = '%Y-%m-%d'
        self.nbp_url = 'https://api.nbp.pl/api/exchangerates/rates/a/usd/{}/?format=json'
        self.cache_file = f'{os.path.dirname(os.path.abspath(__file__))}/nbp_cache.json'
        self.read_cache()

    def read_cache(self):
        """Read cache file."""
        if not os.path.isfile(self.cache_file):
            self.cache = {}
            return
        with open(self.cache_file, 'r', encoding='utf-8') as file:
            self.cache = json.load(file)

    def write_cache(self):
        """Write cache file."""
        with open(self.cache_file, 'w', encoding='utf-8') as file:
            json.dump(self.cache, file, sort_keys=True, indent=2, separators=(',', ': '))

    def get_ratio(self, date_obj):
        """Get ratio from cache if available, otherwise request from NBP."""
        key = date_obj.strftime(self.date_format)
        if key in self.cache:
            if not self.cache[key]:
                raise ValueError('Ratio for selected date is not available in NBP')
            return self.cache[key]

        while True:
            try:
                current_url = self.nbp_url.format(date_obj.strftime(self.date_format))
                req = requests.get(current_url, timeout=5)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout):
                print('Timeout 5 seconds when getting USD/PLN ratio, retrying after 1 second')
                sleep(1)
                continue
            if req.status_code == 200:
                self.cache[key] = req.json()['rates'][0]['mid']
                self.write_cache()
                return self.cache[key]
            if req.status_code == 404 and req.text == '404 NotFound - Not Found - Brak danych':
                self.cache[key] = ''
                self.write_cache()
                raise ValueError('Ratio for selected date is not available in NBP')
            print(f'{req.status_code} {req.text}')
            print('Unhandled error when getting USD/PLN ratio, retrying after 1 second')
            sleep(1)
            continue


NBP_CACHE = NbpRatiosCache()


def date_to_usd_pln(date_obj):
    """Find 'day before vestment' USD/PLN ratio."""
    while True:
        date_obj -= datetime.timedelta(days=1)
        try:
            ratio = NBP_CACHE.get_ratio(date_obj)
            break
        except ValueError:
            date_obj -= datetime.timedelta(days=1)
    return (date_obj, ratio)


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
