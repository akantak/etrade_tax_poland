"""Find all statements for stocks in a directory and parse."""

from datetime import datetime

from . import files_handling as fh
from . import nbp
from .common import ISO_DATE, TAX_PL, cash_float


class Trade:
    """Contains all data for stock sell."""

    def __init__(self):
        """Init trade object."""
        self.shares_sold = 0
        self.usd_net_income = 0.0
        self.trade_date = datetime.fromtimestamp(0)
        self.ratio_date = datetime.fromtimestamp(0)
        self.ratio_value = 0.0
        self.pln_income = 0.0
        self.file = ""

    def csved(self):
        """Csved class object."""
        return ",".join(
            [
                self.trade_date.strftime(ISO_DATE),
                f"{self.usd_net_income:.2f}",
                f"{self.shares_sold}",
                self.ratio_date.strftime(ISO_DATE),
                f"{self.ratio_value:.6f}",
                f"{self.pln_income:.2f}",
                self.file,
            ]
        )

    @staticmethod
    def csv_header():
        """Return table header for CSVed objects."""
        return ",".join(
            [
                "TRADE_DATE",
                "USD_NET_INCOME",
                "SHARES_SOLD",
                "RATIO_DATE",
                "RATIO_VALUE",
                "PLN_INCOME",
                "FILE",
            ]
        )

    def insert_currencies_ratio(self, ratio_date, ratio_value):
        """Insert currencies ratio and calculate dependent variables."""
        self.ratio_date = ratio_date
        self.ratio_value = ratio_value
        self.pln_income = ratio_value * self.usd_net_income


class EsppStock:
    """Contains all data for ESPP stock purchase."""

    def __init__(self):
        """Init espp bought stock object."""
        self.purchase_date = datetime.fromtimestamp(0)
        self.pln_contribution_gross = 0.0
        self.usd_contribution_refund = 0.0
        self.pln_contribution_net = 0.0
        self.vest_day_ratio = 0.0
        self.shares_purchased = 0
        self.file = ""

    def calculate_pln_contribution_net(self):
        """Based on set values, calculated net pln contribution."""
        refund = round(self.usd_contribution_refund / self.vest_day_ratio, 2)
        self.pln_contribution_net = self.pln_contribution_gross - refund

    def csved(self):
        """Csved class object."""
        return ",".join(
            [
                self.purchase_date.strftime(ISO_DATE),
                f"{self.pln_contribution_gross:.2f}",
                f"{self.usd_contribution_refund:.2f}",
                f"{self.vest_day_ratio:.6f}",
                f"{self.pln_contribution_net:.2f}",
                f"{self.shares_purchased}",
                self.file,
            ]
        )

    @staticmethod
    def csv_header():
        """Return table header for CSVed objects."""
        return ",".join(
            [
                "VEST_DATE",
                "PLN_CONTRIB_GROSS",
                "USD_CONTRIB_REFUND",
                "VEST_DAY_RATIO",
                "PLN_CONTRIB_NET",
                "SHARES_PURCHASED",
                "FILE",
            ]
        )


class RestrictedStock:
    """Contains all data for RS stock vest."""

    def __init__(self):
        """Init restricted stock object."""
        self.release_date = datetime.fromtimestamp(0)
        self.shares_released = 0
        self.release_gain = 0.0
        self.file = ""

    def csved(self):
        """Csved class object."""
        return ",".join(
            [
                self.release_date.strftime(ISO_DATE),
                f"{self.shares_released}",
                f"{self.release_gain:.2f}",
                self.file,
            ]
        )

    @staticmethod
    def csv_header():
        """Return table header for CSVed objects."""
        return ",".join(
            [
                "VEST_DATE",
                "SHARES_RELEASED",
                "USD_GAIN",
                "FILE",
            ]
        )


class StockEvent:
    """Contains sum up data for stock event."""

    def __init__(self, base_object):
        """Init sum-up Stock object."""
        self.buy_date = 0
        self.buy_shares_count = 0
        self.buy_tax_deductible = 0
        self.sale_date = 0
        self.sale_shares_count = 0
        self.sale_income = 0
        if isinstance(base_object, EsppStock):
            self.buy_date = base_object.purchase_date
            self.buy_shares_count = base_object.shares_purchased
            self.buy_tax_deductible = base_object.pln_contribution_net
        elif isinstance(base_object, RestrictedStock):
            self.buy_date = base_object.release_date
            self.buy_shares_count = base_object.shares_released
            self.buy_tax_deductible = 0.0
        elif isinstance(base_object, Trade):
            self.sale_date = base_object.trade_date
            self.sale_shares_count = base_object.shares_sold
            self.sale_income = base_object.pln_income
        self.file = base_object.file

    def csved(self):
        """Csved class object."""
        return ",".join(
            [
                self.buy_date.strftime(ISO_DATE) if self.buy_date else "",
                f"{self.buy_shares_count}" if self.buy_shares_count else "",
                f"{self.buy_tax_deductible:.2f}" if self.buy_tax_deductible else "",
                self.sale_date.strftime(ISO_DATE) if self.sale_date else "",
                f"{self.sale_shares_count}" if self.sale_shares_count else "",
                f"{self.sale_income:.2f}" if self.sale_income else "",
                self.file,
            ]
        )

    @staticmethod
    def csv_header():
        """Return table header for CSVed objects."""
        return ",".join(
            [
                "BUY_DATE",
                "BUY_SHARES_COUNT",
                "BUY_TAX_DEDUCT",
                "SELL_DATE",
                "SELL_SHARES_COUNT",
                "SELL_INCOME",
                "FILE",
            ]
        )


def espp_from_text(text):
    """Find all ESPP bought stocks data in text."""
    if "EMPLOYEE STOCK PLAN PURCHASE CONFIRMATION" not in text:
        return ""
    lines = text.split("\n")
    stock = EsppStock()
    for line in lines:
        if "Purchase Date" in line:
            # 'Purchase Date 02-18-2022Shares Purchased to Date in Current Offering'
            date_str = line.split()[2].replace("Shares", "")
            stock.purchase_date = datetime.strptime(date_str, "%m-%d-%Y")
        if "Foreign Contributions" in line:
            # 'Foreign Contributions 10,000.00'
            stock.pln_contribution_gross = cash_float(line.split()[-1])
        if "Average Exchange Rate" in line:
            # 'Average Exchange Rate $0.250000'
            stock.vest_day_ratio = cash_float(line.split()[-1])
        if "Amount Refunded" in line:
            # 'Amount Refunded ($2.00)'
            stock.usd_contribution_refund = cash_float(line.split()[-1])
        if "Shares Purchased" in line and len(line.split()) == 3:
            # 'Shares Purchased 50.0000'
            stock.shares_purchased = int(float(line.split()[-1]))
    stock.calculate_pln_contribution_net()
    return stock


def rs_from_text(text):
    """Find all Restricted Stocks vested data in text."""
    if "EMPLOYEE STOCK PLAN RELEASE CONFIRMATION" not in text:
        return ""
    lines = text.split("\n")
    rest = RestrictedStock()
    for line in lines:
        if "Release Date" in line:
            # 'Plan I06Release Date 01-31-2022'
            rest.release_date = datetime.strptime(line.split()[-1], "%m-%d-%Y")
        if "Shares Released" in line and len(line.split()) == 3:
            # 'Shares Released 10.0000'
            rest.shares_released = int(float(line.split()[-1]))
        if "Total Gain" in line:
            # 'Total Gain $500.00'
            rest.release_gain = cash_float(line.split()[-1])
    return rest


def trade_from_text(text):
    """Find all trade data in text."""
    if "TRADECONFIRMATION" not in text:
        return ""
    lines = text.split("\n")
    trade = Trade()
    for line in lines:
        if "Stock Plan" in line:
            # 05/10/22 05/12/22 61 INTC SELL 50 $50.00 Stock Plan PRINCIPAL $2,500.00
            trade.shares_sold = int(line.split()[5])
            date_str = f"{line.split()[0][:-2]}20{line.split()[0][-2:]}"
            trade.trade_date = datetime.strptime(date_str, "%m/%d/%Y")
        if "NET AMOUNT" in line:
            # 'NET AMOUNT $2,499.48'
            trade.usd_net_income = cash_float(line.split()[-1])
    return trade


def stocks_sum_csved(stocks):
    """Extract sum up lines from stocks list."""
    if not stocks:
        return []

    other_income = sum(s.sale_income for s in stocks)
    tax_deductible = sum(s.buy_tax_deductible for s in stocks)
    profit = other_income - tax_deductible
    rounded_profit = int(round(profit, 0))
    tax_base = rounded_profit * TAX_PL
    tax_rounded = int(round(tax_base, 0))
    return [
        f"other income,{other_income:.2f},PIT-38/C/22&24",
        f"tax deductible,{tax_deductible:.2f},PIT-38/C/23&25",
        f"profit,{profit:.2f},PIT-38/C/26",
        f"profit_rounded,{rounded_profit},PIT-38/C/29",
        f"tax_base,{tax_base:.2f},PIT-38/C/31",
        f"tax_rounded,{tax_rounded},PIT-38/C/33",
    ]


def process_stock_docs(directory):
    """Process all docs and find stocks data."""
    files = fh.pdfs_in_dir(directory)
    espps = []  # Employee Stock Purchase Plan
    rests = []  # Restricted Stock
    trades = []  # stocks sell events

    for filename in files:
        full_path = f"{directory}/{filename}"
        text = fh.file_to_text(full_path)
        if espp := espp_from_text(text):
            espp.file = full_path
            espps.append(espp)
        if rest := rs_from_text(text):
            rest.file = full_path
            rests.append(rest)
        if trade := trade_from_text(text):
            trade.file = full_path
            trade.insert_currencies_ratio(*nbp.date_to_usd_pln(trade.trade_date))
            trades.append(trade)

    ses = [StockEvent(x) for x in espps + rests + trades]

    fh.save_csv("_espp.csv", EsppStock.csv_header(), [e.csved() for e in espps])
    fh.save_csv("_rs.csv", RestrictedStock.csv_header(), [r.csved() for r in rests])
    fh.save_csv("_trade.csv", Trade.csv_header(), [t.csved() for t in trades])
    fh.save_csv("_stocks.csv", StockEvent.csv_header(), [s.csved() for s in ses])
    fh.save_csv("stocks_summary.csv", fh.sum_header(), stocks_sum_csved(ses))
