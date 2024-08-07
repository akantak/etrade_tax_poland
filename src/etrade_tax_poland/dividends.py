"""Find all statements for dividends in a directory and count the due tax."""

from datetime import datetime

from . import files_handling as fh
from .cache.nbp import date_to_usd_pln
from .common import ISO_DATE, TAX_PL, cash_float, round_up


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
                f"{self.usd_gross:.2f}",
                f"{self.usd_tax:.2f}",
                f"{self.usd_net:.2f}",
                self.ratio_date.strftime(ISO_DATE),
                f"{self.ratio_value:.6f}",
                f"{self.pln_gross:.2f}",
                f"{self.flat_rate_tax:.2f}",
                f"{self.pln_tax_paid:.2f}",
                f"{self.pln_tax_due:.2f}",
                self.file,
            ]
        )

    @staticmethod
    def csv_header():
        """Return table header for CSVed objects."""
        return ",".join(
            [
                "VEST_DATE",
                "USD_GROSS",
                "USD_TAX_PAID",
                "USD_NET",
                "RATIO_DATE",
                "RATIO_VALUE",
                "PLN_GROSS",
                "PLN_TAX_TOTAL",
                "PLN_TAX_PAID",
                "PLN_TAX_DUE",
                "FILE",
            ]
        )

    def insert_currencies_ratio(self, ratio_date, ratio_value):
        """Insert currencies ratio and calculate dependent variables."""
        self.ratio_date = ratio_date
        self.ratio_value = ratio_value
        self.pln_gross = round(self.usd_gross * ratio_value, 2)
        self.flat_rate_tax = round(self.pln_gross * TAX_PL, 2)
        self.pln_tax_paid = round(self.usd_tax * ratio_value, 2)
        self.pln_tax_due = self.flat_rate_tax - self.pln_tax_paid


def get_stock_dividend_from_text(text):
    """Get dividend data from text."""
    dividend_lines = []
    year_line = ""
    lines = text.split("\n")

    for i, line in enumerate(lines):
        if "Dividend " in line and "Next Dividend Payable" not in line and "LIQUIDITY" not in line:
            dividend_lines = lines[i : i + 6]
        if "Account DetailCLIENT STATEMENT" in line:
            # 'Account DetailCLIENT STATEMENT     For the Period September 1 -30, 2023'
            year_line = line

    if not dividend_lines:
        return {}

    if "Qualified" in dividend_lines[0]:
        # latest 2023 doc version, example:
        # [0] '12/1 Qualified Dividend INTEL CORP 125.00'
        # [1] '12/1 Tax Withholding INTEL CORP (18.75)'
        # [2] '12/4 Funds Transferred WIRE OUT (106.25)'
        str_date = f"{dividend_lines[0].split()[0]}/{year_line.split()[-1]}"
        pay_date = datetime.strptime(str_date, "%m/%d/%Y")
        gross = cash_float(dividend_lines[0].split()[-1])
        tax = cash_float(dividend_lines[1].split()[-1])
        net = cash_float(dividend_lines[2].split()[-1])
    else:
        # before 09.2023 doc version, example:
        # [0] '03/01/23 Dividend INTEL CORP'
        # [1] 'CASH DIV  ON     264 SHS'
        # [2] 'REC 02/07/23 PAY 03/01/23'
        # [3] 'NON-RES TAX WITHHELD @ .15000INTC 54.75 365.00'
        # [4] 'TOTALDIVIDENDS&INTERESTACTIVITY $54.75 $365.00'
        # [5] 'NETDIVIDENDS&INTERESTACTIVITY $310.25'
        date = dividend_lines[0].split()[0]
        pay_date = datetime.strptime(f"{date[:-2]}20{date[-2:]}", "%m/%d/%Y")
        gross = cash_float(dividend_lines[3].split()[-1])
        tax = cash_float(dividend_lines[3].split()[-2])
        net = cash_float(dividend_lines[5].split()[-1])

    return Dividend(pay_date, gross, tax, net)


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
            ldivs.append(Dividend(date, amount, 0, amount))
    return ldivs


def divs_sum_csved(dividends):
    """Extract sum up lines from dividends list."""
    if not dividends:
        return []

    flat_rate = round_up(sum(div.flat_rate_tax for div in dividends))
    tax_paid = round_up(sum(div.pln_tax_paid for div in dividends))
    tax_diff = flat_rate - tax_paid

    return [
        f"tax flat-rate,{flat_rate:.2f},PIT-38/G/45",
        f"tax paid,{tax_paid:.2f},PIT-38/G/46",
        f"tax diff,{tax_diff:.2f},PIT-38/G/47",
    ]


def process_dividend_docs(directory):
    """Count due tax based on statements files in directory."""
    files = fh.pdfs_in_dir(directory)
    dividends = []
    for filename in files:
        text = fh.file_to_text(f"{directory}/{filename}")
        if dividend := get_stock_dividend_from_text(text):
            dividend.file = filename
            dividends.append(dividend)
        if ldivs := get_liquidity_dividends_from_text(text):
            for ldiv in ldivs:
                ldiv.file = filename
            dividends += ldivs

    for dividend in dividends:
        dividend.insert_currencies_ratio(*date_to_usd_pln(dividend.pay_date))

    fh.save_csv("_dividend.csv", Dividend.csv_header(), [d.csved() for d in dividends])
    fh.save_csv("dividends_summary.csv", fh.sum_header(), divs_sum_csved(dividends))
