"""Find all statements for dividents in a directory and count the due tax."""

import datetime
import glob
import json
import os
import sys
from time import sleep

from pypdf import PdfReader

import requests


F_PAY_DATE = 'pay_date'
F_GROSS_DIVIDENT = 'gross_dividend'
F_TAX = 'tax'
F_NET_DIVIDENT = 'net_dividend'

F_RATIO_DATE = 'ratio_date'
F_RATIO_VALUE = 'ratio_value'

TAX_PL = 0.19
NBP_URL = 'https://api.nbp.pl/api/exchangerates/rates/a/usd'


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


def get_unified_dividends_from_text(text):
    """Get dividends data from text in unified format."""
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
        return {
            F_PAY_DATE: f'{dividend_lines[0].split()[0]}/{year}',
            F_GROSS_DIVIDENT: float(dividend_lines[0].split()[-1]),
            F_TAX: float(dividend_lines[1].split()[-1][1:-1]),
            F_NET_DIVIDENT: float(dividend_lines[2].split()[-1][1:-1]),
        }
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
    return {
        F_PAY_DATE: f'{date[:-2]}20{date[-2:]}',
        F_GROSS_DIVIDENT: float(dividend_lines[3].split()[-1]),
        F_TAX: float(dividend_lines[3].split()[-2]),
        F_NET_DIVIDENT: float(dividend_lines[5].split()[-1][1:]),
    }


def get_usd_pln_ratio_for_date(date_str):
    """Find 'day before vestment' USD/PLN ratio."""
    date_format = '%m/%d/%Y'
    date_obj = datetime.datetime.strptime(date_str, date_format)
    date_obj -= datetime.timedelta(days=1)
    while True:
        try:
            req = requests.get(f'{NBP_URL}/{date_obj.strftime("%Y-%m-%d")}/?format=json', timeout=5)
        except Exception:
            print('Failed getting USD/PLN ratio in 5 seconds, retrying after 1 second')
            sleep(1)
            continue
        if req.status_code == 200:
            return {
                F_RATIO_DATE: date_obj.strftime('%Y-%m-%d'),
                F_RATIO_VALUE: req.json()['rates'][0]['mid'],
            }
        if req.status_code == 404 and req.text == '404 NotFound - Not Found - Brak danych':
            date_obj -= datetime.timedelta(days=1)
        else:
            raise Exception('Not handled case during getting USD/PLN ratio')


def count_taxes(directory):
    """Count due tax based on statements files in directory."""
    files = get_all_pdf_files(directory)
    dividends = []
    for filename in files:
        text = get_text_from_file(f'{directory}/{filename}')
        dividend = get_unified_dividends_from_text(text)
        if dividend:
            dividends.append(dividend)

    for dividend in dividends:
        dividend |= get_usd_pln_ratio_for_date(dividend[F_PAY_DATE])

    print('JSON data:')
    print(json.dumps(dividends))
    print()

    print(f'DIVIDENDS GROSS: ${sum(div[F_GROSS_DIVIDENT] for div in dividends):.2f}')
    print(f'DIVIDENDS TAX PAID: ${sum(div[F_TAX] for div in dividends):.2f}')
    print(f'DIVIDENDS NET: ${sum(div[F_NET_DIVIDENT] for div in dividends):.2f}')
    print()

    div_gross_pln = sum(div[F_GROSS_DIVIDENT] * div[F_RATIO_VALUE] for div in dividends)
    div_proper_tax_pln = div_gross_pln * TAX_PL
    div_paid_tax_pln = sum(div[F_TAX] * div[F_RATIO_VALUE] for div in dividends)
    div_due_tax_pln = div_proper_tax_pln - div_paid_tax_pln
    print(f'DIVIDENDS GROSS: {div_gross_pln:.2f} zł')
    print(f'DIVIDENDS PROPER TAX: {div_proper_tax_pln:.2f} zł')
    print(f'DIVIDENDS PAID TAX: {div_paid_tax_pln:.2f} zł')
    print(f'DIVIDENDS DUE TAX: {div_due_tax_pln:.2f} zł')


if len(sys.argv) > 1:
    dir_path = sys.argv[1]
    if not os.path.isdir(dir_path):
        print('Provided path is not a directory')
        exit(1)
    count_taxes(dir_path)
else:
    count_taxes('.')
