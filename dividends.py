"""Find all statements for dividents in a directory and count the due tax."""

import datetime

import etrade_common as etc


class Dividend:
    """Keep all dividend data in an object."""

    def __init__(self, pay_date, gross, tax, net):
        """Initialize an object."""
        self.pay_date = datetime.datetime.strptime(pay_date, '%m/%d/%Y')
        self.usd_gross = float(gross)
        self.usd_tax = float(tax)
        self.usd_net = float(net)
        self.ratio_date = datetime.datetime.fromtimestamp(0)
        self.ratio_value = 0.0
        self.pln_gross = 0.0
        self.flat_rate_tax = 0.0
        self.pln_tax_paid = 0.0
        self.pln_tax_due = 0.0

    def get_csved_object(self):
        """Csved class object."""
        return ','.join([
            self.pay_date.strftime('%d.%m.%Y'),
            f'{self.usd_gross:.2f}',
            f'{self.usd_tax:.2f}',
            f'{self.usd_net:.2f}',
            self.ratio_date.strftime('%d.%m.%Y'),
            f'{self.ratio_value:.6f}',
            f'{self.pln_gross:.2f}',
            f'{self.flat_rate_tax:.2f}',
            f'{self.pln_tax_paid:.2f}',
            f'{self.pln_tax_due:.2f}',
        ])

    @staticmethod
    def get_table_header():
        """Return table header for CSVed objects."""
        return ','.join([
            'VEST_DATE',
            'USD_GROSS',
            'USD_TAX_PAID',
            'USD_NET',
            'RATIO_DATE',
            'RATIO_VALUE',
            'PLN_GROSS',
            'PLN_TAX_TOTAL',
            'PLN_TAX_PAID',
            'PLN_TAX_DUE',
        ])

    def insert_currencies_ratio(self, ratio_date, ratio_value):
        """Insert currencies ratio and calculate dependent variables."""
        self.ratio_date = ratio_date
        self.ratio_value = ratio_value
        self.pln_gross = round(self.usd_gross * ratio_value, 2)
        self.flat_rate_tax = round(self.pln_gross * etc.TAX_PL, 2)
        self.pln_tax_paid = round(self.usd_tax * ratio_value, 2)
        self.pln_tax_due = self.flat_rate_tax - self.pln_tax_paid


def get_dividend_from_text(text):
    """Get dividend data from text in an class object."""
    dividend_lines = []
    year_line = ''
    lines = text.split('\n')

    for i, line in enumerate(lines):
        if 'Dividend INTEL CORP' in line:
            dividend_lines = lines[i:i + 6]
        if 'Account DetailCLIENT STATEMENT' in line:
            year_line = line

    if not dividend_lines:
        return {}

    # latest 2023 doc version
    if 'Qualified' in dividend_lines[0]:
        year = year_line.split()[-1]
        return Dividend(
            f'{dividend_lines[0].split()[0]}/{year}',
            dividend_lines[0].split()[-1],
            dividend_lines[1].split()[-1][1:-1],
            dividend_lines[2].split()[-1][1:-1],
        )
    # before 09.2023 doc version
    date = dividend_lines[0].split()[0]
    return Dividend(
        f'{date[:-2]}20{date[-2:]}',
        dividend_lines[3].split()[-1],
        dividend_lines[3].split()[-2],
        dividend_lines[5].split()[-1][1:],
    )


def get_dividends_sum_up_lines(dividends):
    """Extract sum up lines from dividends list."""
    if not dividends:
        return []
    flat_rate_tax = sum(div.flat_rate_tax for div in dividends)
    tax_paid = sum(div.pln_tax_paid for div in dividends)
    tax_due = sum(div.pln_tax_due for div in dividends)

    return [
        f'DIVIDENDS TAX FLAT-RATE\t(PIT-38/G/45):\t{flat_rate_tax:.2f} zł',
        f'DIVIDENDS TAX PAID\t\t(PIT-38/G/46):\t{tax_paid:.2f} zł',
        f'DIVIDENDS TAX DIFF\t\t(PIT-38/G/47):\t{tax_due:.2f} zł'
    ]


def process_dividend_docs(directory):
    """Count due tax based on statements files in directory."""
    files = etc.get_all_pdf_files(directory)
    dividends = []
    for filename in files:
        text = etc.get_text_from_file(f'{directory}/{filename}')
        if dividend := get_dividend_from_text(text):
            dividends.append(dividend)

    for dividend in dividends:
        dividend.insert_currencies_ratio(*etc.get_usd_pln_ratio(dividend.pay_date))

    etc.save_txt('sum_dividends.txt', get_dividends_sum_up_lines(dividends))
    etc.save_csv('detailed_dividends.csv', Dividend.get_table_header(), dividends)
