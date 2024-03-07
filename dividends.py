"""Find all statements for dividents in a directory and count the due tax."""

import datetime
import glob
import os
import sys
from time import sleep

from pypdf import PdfReader

import requests


DATE_FORMAT = '%m/%d/%Y'
TAX_PL = 0.19
NBP_URL = 'https://api.nbp.pl/api/exchangerates/rates/a/usd/{}/?format=json'


class Dividend:
    """Keep all dividend data in an object."""

    def __init__(self, pay_date, gross_dividend, tax, net_dividend):
        """Initialize an object."""
        self.pay_date = datetime.datetime.strptime(pay_date, DATE_FORMAT)
        self.usd_gross_dividend = float(gross_dividend)
        self.usd_tax = float(tax)
        self.usd_net_dividend = float(net_dividend)
        self.ratio_date = ''
        self.ratio_value = 0
        self.pln_gross = 0
        self.pln_tax_payable = 0
        self.pln_tax_paid = 0
        self.pln_tax_due = 0

    def __str__(self):
        """Stringify class object."""
        return '\t'.join([
            self.pay_date.strftime(DATE_FORMAT),
            f'{self.pln_gross:.2f}',
            f'{self.pln_tax_payable:.2f}',
            f'{self.pln_tax_paid:.2f}',
            f'{self.pln_tax_due:.2f}',
        ])

    def insert_currencies_ratio(self, ratio_date, ratio_value):
        """Insert currencies ratio and calculate dependent variables."""
        self.ratio_date = ratio_date
        self.ratio_value = ratio_value
        self.pln_gross = self.usd_gross_dividend * ratio_value
        self.pln_tax_payable = self.pln_gross * TAX_PL
        self.pln_tax_paid = self.usd_tax * ratio_value
        self.pln_tax_due = self.pln_tax_payable - self.pln_tax_paid


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


def get_dividend_from_text(text):
    """Get dividend data from text in an class object."""
    dividend_lines = []
    year_line = ''
    lines = text.split('\n')

    for i, line in enumerate(lines):
        if 'Dividend INTEL CORP' in line:
            dividend_lines = lines[i:i+6]
        if 'Account DetailCLIENT STATEMENT' in line:
            year_line = line

    if not dividend_lines:
        return {}

    # latest 2023 doc version
    if 'Qualified' in dividend_lines[0]:
        _ = """
        [
            '12/1 Qualified Dividend INTEL CORP 94.25',
            '12/1 Tax Withholding INTEL CORP (14.14)',
            '12/4 Funds Transferred WIRE OUT (80.22)',
            'NET CREDITS/(DEBITS) $0.00',
            'MONEY MARKET FUND (MMF) AND BANK DEPOSIT PROGRAM ACTIVITY',
            'Activity'
        ]
        """
        year = year_line.split()[-1]
        return Dividend(
            f'{dividend_lines[0].split()[0]}/{year}',
            dividend_lines[0].split()[-1],
            dividend_lines[1].split()[-1][1:-1],
            dividend_lines[2].split()[-1][1:-1],
        )
    # before 09.2023 doc version
    _ = """
    [
        '09/01/23 Dividend INTEL CORP',
        'CASH DIV  ON     561 SHS',
        'REC 08/07/23 PAY 09/01/23',
        'NON-RES TAX WITHHELD @ .15000INTC 10.52 70.13',
        'TOTALDIVIDENDS&INTERESTACTIVITY $10.52 $70.13',
        'NETDIVIDENDS&INTERESTACTIVITY $59.61'
    ]
    """
    date = dividend_lines[0].split()[0]
    return Dividend(
        f'{date[:-2]}20{date[-2:]}',
        dividend_lines[3].split()[-1],
        dividend_lines[3].split()[-2],
        dividend_lines[5].split()[-1][1:],
    )


def get_usd_pln_ratio_for_date(date_obj):
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


def count_taxes(directory):
    """Count due tax based on statements files in directory."""
    files = get_all_pdf_files(directory)
    dividends = []
    for filename in files:
        text = get_text_from_file(f'{directory}/{filename}')
        dividend = get_dividend_from_text(text)
        if dividend:
            dividends.append(dividend)

    for dividend in dividends:
        dividend.insert_currencies_ratio(*get_usd_pln_ratio_for_date(dividend.pay_date))
        print(dividend)

    print(f'DIVIDENDS GROSS:\t{sum(div.pln_gross for div in dividends):.2f} zł')
    print(f'DIVIDENDS TAX PAYABLE:\t{sum(div.pln_tax_payable for div in dividends):.2f} zł')
    print(f'DIVIDENDS TAX PAID:\t{sum(div.pln_tax_paid for div in dividends):.2f} zł')
    print(f'DIVIDENDS TAX DUE:\t{sum(div.pln_tax_due for div in dividends):.2f} zł')


if len(sys.argv) > 1:
    DIR_PATH = sys.argv[1]
    if not os.path.isdir(DIR_PATH):
        print('Provided path is not a directory')
        sys.exit(1)
    count_taxes(DIR_PATH)
else:
    count_taxes('.')
