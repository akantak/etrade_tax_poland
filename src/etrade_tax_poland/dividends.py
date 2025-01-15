"""Find all statements for dividends in a directory and count the due tax."""

from datetime import datetime

from . import files_handling as fh
from .cache.nbp import date_to_usd_pln
from .maths import ISO_DATE, TAX_PL, cash_float


class Dividend:
    """Keep all dividend data in an object."""

    def __init__(self, pay_date: datetime, gross: float, tax: float, net: float):
        """Initialize an object."""
        self.pay_date = pay_date
        self.usd_gross = gross
        self.usd_tax = tax
        self.usd_net = net
        self.ratio_date = datetime.fromtimestamp(0)
        self.ratio_value = 0.0
        self.pln_gross = 0.0
        self.flat_rate_tax = 0.0
        self.pln_tax_paid = 0.0
        self.pln_tax_due = 0.0
        self.file = ""

    def csved(self):
        """Csved class object."""
        return ",".join(
            [
                self.pay_date.strftime(ISO_DATE),
                f"{self.flat_rate_tax:.2f}",
                f"{self.pln_tax_paid:.2f}",
                f"{self.pln_tax_due:.2f}",
            ]
        )

    @staticmethod
    def csv_header():
        """Return table header for CSVed objects."""
        return ",".join(
            [
                "VEST_DATE",
                "PLN_TAX_TOTAL",
                "PLN_TAX_PAID",
                "PLN_TAX_DUE",
            ]
        )

    def insert_currencies_ratio(self):
        """Insert currencies ratio and calculate dependent variables."""
        self.ratio_date, self.ratio_value = date_to_usd_pln(self.pay_date)
        self.pln_gross = round(self.usd_gross * self.ratio_value, 2)
        self.flat_rate_tax = round(self.pln_gross * TAX_PL, 2)
        self.pln_tax_paid = round(self.usd_tax * self.ratio_value, 2)
        self.pln_tax_due = self.flat_rate_tax - self.pln_tax_paid


def get_stock_dividends_from_text(text):
    """Get dividend data from text."""
    dividend_lines_starts = []
    year_line = ""
    dividends = []
    lines = text.split("\n")

    for i, line in enumerate(lines):
        if "Dividend " in line and "Next Dividend Payable" not in line and "LIQUIDITY" not in line:
            dividend_lines_starts.append(i)
        if "Account DetailCLIENT STATEMENT" in line:
            # 'Account DetailCLIENT STATEMENT     For the Period September 1 -30, 2023'
            year_line = line

    if not dividend_lines_starts:
        return []

    for dividend_lines_start in dividend_lines_starts:
        if "Qualified Dividend" in lines[dividend_lines_start]:
            # latest 2023 doc version, example:
            # [0] '12/1 Qualified Dividend INTEL CORP 125.00'
            # [1] '12/1 Tax Withholding INTEL CORP (18.75)'
            offset = dividend_lines_start
            str_date = f"{lines[offset].split()[0]}/{year_line.split()[-1]}"
            pay_date = datetime.strptime(str_date, "%m/%d/%Y")
            gross = cash_float(lines[offset].split()[-1])

            # depends on the file, table can be continued on the next page
            while offset < len(lines) and "Tax Withholding" not in lines[offset]:
                offset += 1
            if offset == len(lines):
                print(f"Did not found all dividend fields for {gross} gross value")
                continue
            tax = cash_float(lines[offset].split()[-1])
            net = gross - tax
        else:
            # before 09.2023 doc version, example:
            # [0] '03/01/23 Dividend INTEL CORP'
            # [1] 'CASH DIV  ON     264 SHS'
            # [2] 'REC 02/07/23 PAY 03/01/23'
            # [3] 'NON-RES TAX WITHHELD @ .15000INTC 54.75 365.00'
            # [4] 'TOTALDIVIDENDS&INTERESTACTIVITY $54.75 $365.00'
            # [5] 'NETDIVIDENDS&INTERESTACTIVITY $310.25'
            dividend_lines = lines[dividend_lines_start : dividend_lines_start + 6]
            date = dividend_lines[0].split()[0]
            pay_date = datetime.strptime(f"{date[:-2]}20{date[-2:]}", "%m/%d/%Y")
            gross = cash_float(dividend_lines[3].split()[-1])
            tax = cash_float(dividend_lines[3].split()[-2])
            net = cash_float(dividend_lines[5].split()[-1])
        dividend = Dividend(pay_date, gross, tax, net)
        dividend.insert_currencies_ratio()
        dividends.append(dividend)
    return dividends


def get_liquidity_dividends_from_text(text):
    """Get liquidity dividend data from text."""
    ldivs = []
    year = ""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "Account DetailCLIENT STATEMENT" in line:
            # 'Account DetailCLIENT STATEMENT     For the Period September 1 -30, 2023'
            year = line.split()[-1]
        if "Dividend TREASURY LIQUIDITY FUND" in line:
            date = datetime.strptime(f"{line.split()[0]}/{year}", "%m/%d/%Y")
            if "Transaction Reportable for the Prior Year" in line:
                # '1/2 Dividend TREASURY LIQUIDITY FUND Transaction \
                # Reportable for the Prior Year. $0.01'
                amount = cash_float(lines[i].split()[-1])
            else:
                # [i]   '10/2 Dividend TREASURY LIQUIDITY FUND'
                # [i+1] 'DIV PAYMENT$0.23'
                amount = cash_float(lines[i + 1].split("PAYMENT")[-1])
            dividend = Dividend(date, amount, 0, amount)
            dividend.insert_currencies_ratio()
            ldivs.append(dividend)
    return ldivs


def process_dividend_docs(directory, debug=False):
    """Count due tax based on statements files in directory."""
    files = fh.pdfs_in_dir(directory)
    dividends = []
    for filename in files:
        text = fh.file_to_text(f"{directory}/{filename}")
        if divs := get_stock_dividends_from_text(text):
            for div in divs:
                div.file = filename
            dividends += divs
        if ldivs := get_liquidity_dividends_from_text(text):
            for ldiv in ldivs:
                ldiv.file = filename
            dividends += ldivs
    if debug:
        fh.write_objects_debug_json({"dividends": dividends}, "dividends.json")
    fh.save_csv("_dividend.csv", Dividend.csv_header(), [d.csved() for d in dividends])
