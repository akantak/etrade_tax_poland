"""Find all statements for stocks in a directory and parse."""

from datetime import datetime

from . import files_handling as fh
from .cache.intc import date_to_intc_price
from .cache.nbp import date_to_usd_pln
from .maths import ISO_DATE, cash_float


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
        self.initial_price_pln = 0.0
        self.pln_contribution_gross = 0.0
        self.usd_contribution_refund = 0.0
        self.pln_contribution_net = 0.0
        self.vest_day_ratio = 0.0
        self.shares_purchased = 0
        self.file = ""
        self.period_start_value = 0.0
        self.period_end_value = 0.0
        self.purchase_price_base = 0.0

    def calculate_pln_contribution_net(self):
        """Based on set values, calculated net pln contribution."""
        refund = round(self.usd_contribution_refund / self.vest_day_ratio, 2)
        self.pln_contribution_net = self.pln_contribution_gross - refund

    def insert_initial_price_pln(self):
        """Insert intc price and calculate dependent variables."""
        _, intc = date_to_intc_price(self.purchase_date)
        _, ratio = date_to_usd_pln(self.purchase_date)
        self.initial_price_pln = intc * ratio


class RestrictedStock:
    """Contains all data for RS stock vest."""

    def __init__(self):
        """Init restricted stock object."""
        self.release_date = datetime.fromtimestamp(0)
        self.shares_released = 0
        self.release_gain = 0.0
        self.ratio_date = datetime.fromtimestamp(0)
        self.ratio_value = 0.0
        self.stock_price_pln = 0.0
        self.initial_price_pln = 0.0
        self.file = ""

    def insert_ratios(self):
        """Insert currencies ratio and calculate dependent variables."""
        self.ratio_date, self.ratio_value = date_to_usd_pln(self.release_date)
        total_pln_gain = self.ratio_value * self.release_gain
        self.stock_price_pln = total_pln_gain / self.shares_released
        _, intc = date_to_intc_price(self.release_date)
        self.initial_price_pln = intc * self.ratio_value


class StockEvent:
    """Contains sum up data for stock event."""

    def __init__(self, base_object):
        """Init sum-up Stock object."""
        self.buy_date = 0
        self.buy_shares_count = 0
        self.buy_tax_deductible = 0
        self.buy_price_pln = 0
        self.initial_price_pln = 0
        self.sale_date = 0
        self.sale_shares_count = 0
        self.sale_income = 0
        if isinstance(base_object, EsppStock):
            self.buy_date = base_object.purchase_date
            self.buy_shares_count = base_object.shares_purchased
            self.buy_tax_deductible = base_object.pln_contribution_net
            self.buy_price_pln = self.buy_tax_deductible / self.buy_shares_count
            self.initial_price_pln = base_object.initial_price_pln
        elif isinstance(base_object, RestrictedStock):
            self.buy_date = base_object.release_date
            self.buy_shares_count = base_object.shares_released
            self.buy_tax_deductible = 0.0
            self.initial_price_pln = base_object.initial_price_pln
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
                f"{self.buy_price_pln:.2f}" if self.buy_price_pln else "",
                f"{self.initial_price_pln:.2f}" if self.initial_price_pln else "",
                self.sale_date.strftime(ISO_DATE) if self.sale_date else "",
                f"{self.sale_shares_count}" if self.sale_shares_count else "",
                f"{self.sale_income:.2f}" if self.sale_income else "",
            ]
        )

    @staticmethod
    def csv_header():
        """Return table header for CSVed objects."""
        return ",".join(
            [
                "BUY_DATE",
                "BUY_SHARES_COUNT",
                "TAX_DEDUCTIBLE",
                "REAL_BUY_PRICE_PLN",
                "DATE_BUY_PRICE_PLN",
                "SELL_DATE",
                "SELL_SHARES_COUNT",
                "SELL_INCOME",
            ]
        )


def espp_from_text(text):
    """Find all ESPP bought stocks data in text."""
    if "EMPLOYEE STOCK PLAN PURCHASE CONFIRMATION" not in text:
        return []
    lines = text.split("\n")
    stock = EsppStock()
    for i, line in enumerate(lines):
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
        if "Grant Date Market Value" in line:
            stock.period_start_value = cash_float(line.split()[-1])
        if "Purchase Value per Share" in line:
            stock.period_end_value = cash_float(line.split()[-1])
        if "Purchase Price per Share" in line:
            stock.purchase_price_base = cash_float(lines[i + 1].split()[-2])
    stock.calculate_pln_contribution_net()
    stock.insert_initial_price_pln()
    return stock


def rs_from_text(text):
    """Find all Restricted Stocks vested data in text."""
    if "EMPLOYEE STOCK PLAN RELEASE CONFIRMATION" not in text:
        return []
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
    rest.insert_ratios()
    return rest


def trade_from_text(text):
    """Find all trade data in text."""
    if "TRADECONFIRMATION" in text:
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
        trade.insert_currencies_ratio(*date_to_usd_pln(trade.trade_date))
        return trade
    if "Transaction Type: Sold" in text:
        lines = text.split("\n")
        trade = Trade()
        for i, line in enumerate(lines):
            if "Net Amount" in line:
                # 'Net Amount $5,805.60'
                trade.usd_net_income = cash_float(line.split()[-1])
            if "Trade Date Settlement Date Quantity Price Settlement Amount" in line:
                # 'Trade Date Settlement Date Quantity Price Settlement Amount'
                # '02/20/2024 02/22/2024 100 45.00'
                line_plus_one = lines[i + 1]
                trade.shares_sold = int(line_plus_one.split()[2])
                trade.trade_date = datetime.strptime(line_plus_one.split()[0], "%m/%d/%Y")
        trade.insert_currencies_ratio(*date_to_usd_pln(trade.trade_date))
        return trade

    return []


def process_stock_docs(directory, debug=False):
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
            trades.append(trade)

    ses = [StockEvent(x) for x in espps + rests + trades]

    if debug:
        fh.write_objects_debug_json({"espp": espps, "rs": rests, "trade": trades}, "stocks.json")
    fh.save_csv("_stocks.csv", StockEvent.csv_header(), [s.csved() for s in ses])
