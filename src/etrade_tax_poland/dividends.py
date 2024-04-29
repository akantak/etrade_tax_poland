"""Find all statements for dividents in a directory and count the due tax."""

from datetime import datetime

from . import files_handling as fh
from . import nbp
from .common import ISO_DATE, TAX_PL, round_up


class Dividend:
    """Keep all dividend data in an object."""

    def __init__(self, pay_date, gross, tax, net):
        """Initialize an object."""
        self.pay_date = pay_date
        self.usd_gross = float(gross)
        self.usd_tax = float(tax)
        self.usd_net = float(net)
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
        if (
            "Dividend " in line
            and "Next Dividend Payable" not in line
            and "LIQUIDITY" not in line
        ):
            dividend_lines = lines[i : i + 6]
        if "Account DetailCLIENT STATEMENT" in line:
            year_line = line

    if not dividend_lines:
        return {}

    if "Qualified" in dividend_lines[0]:
        # latest 2023 doc version
        str_date = f"{dividend_lines[0].split()[0]}/{year_line.split()[-1]}"
        pay_date = datetime.strptime(str_date, "%m/%d/%Y")
        gross = dividend_lines[0].split()[-1].replace("$", "")
        tax = dividend_lines[1].split()[-1][1:-1]
        net = dividend_lines[2].split()[-1][1:-1]
    else:
        # before 09.2023 doc version
        date = dividend_lines[0].split()[0]
        pay_date = datetime.strptime(f"{date[:-2]}20{date[-2:]}", "%m/%d/%Y")
        gross = dividend_lines[3].split()[-1].replace("$", "")
        tax = dividend_lines[3].split()[-2]
        net = dividend_lines[5].split()[-1][1:]

    return Dividend(pay_date, gross, tax, net)


def get_liquidity_dividends_from_text(text):
    """Get liquidity dividend data from text."""
    ldivs = []
    year = ""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "Account DetailCLIENT STATEMENT" in line:
            year = line.split()[-1]
        if "Dividend TREASURY LIQUIDITY FUND" in line:
            date = datetime.strptime(f"{line.split()[0]}/{year}", "%m/%d/%Y")
            if "Transaction Reportable for the Prior Year" in line:
                amount = lines[i].split("$")[-1]
            else:
                amount = lines[i + 1].split("PAYMENT")[-1].replace("$", "")
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
        dividend.insert_currencies_ratio(*nbp.date_to_usd_pln(dividend.pay_date))

    fh.save_csv("_dividend.csv", Dividend.csv_header(), [d.csved() for d in dividends])
    fh.save_csv("dividends_summary.csv", fh.sum_header(), divs_sum_csved(dividends))
