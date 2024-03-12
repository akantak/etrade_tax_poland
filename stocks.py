"""Find all statements for stocks in a directory and parse."""

import datetime

import etrade_common as etc


class Trade():
    """Contains all data for stock sell."""

    def __init__(self):
        """Init trade object."""
        self.shares_sold = 0
        self.usd_net_income = 0.0
        self.trade_date = datetime.datetime.fromtimestamp(0)
        self.ratio_date = datetime.datetime.fromtimestamp(0)
        self.ratio_value = 0.0
        self.pln_income = 0.0
        self.file = ''

    def get_csved_object(self):
        """Csved class object."""
        return ','.join([
            self.trade_date.strftime('%d.%m.%Y'),
            f'{self.usd_net_income:.2f}',
            f'{self.shares_sold}',
            self.ratio_date.strftime('%d.%m.%Y'),
            f'{self.ratio_value:.6f}',
            f'{self.pln_income:.2f}',
            self.file,
        ])

    @staticmethod
    def get_table_header():
        """Return table header for CSVed objects."""
        return ','.join([
            'TRADE_DATE',
            'USD_NET_INCOME',
            'SHARES_SOLD',
            'RATIO_DATE',
            'RATIO_VALUE',
            'PLN_INCOME',
            'FILE',
        ])

    def insert_currencies_ratio(self, ratio_date, ratio_value):
        """Insert currencies ratio and calculate dependent variables."""
        self.ratio_date = ratio_date
        self.ratio_value = ratio_value
        self.pln_income = ratio_value * self.usd_net_income


class EsppStock():
    """Contains all data for ESPP stock purchase."""

    def __init__(self):
        """Init espp bought stock object."""
        self.purchase_date = datetime.datetime.fromtimestamp(0)
        self.pln_contribution_gross = 0.0
        self.usd_contribution_refund = 0.0
        self.pln_contribution_net = 0.0
        self.vest_day_ratio = 0.0
        self.shares_purchased = 0
        self.file = ''

    def calculate_pln_contribution_net(self):
        """Based on set values, calculated net pln contribution."""
        refund = round(self.usd_contribution_refund / self.vest_day_ratio, 2)
        self.pln_contribution_net = self.pln_contribution_gross - refund

    def get_csved_object(self):
        """Csved class object."""
        return ','.join([
            self.purchase_date.strftime('%d.%m.%Y'),
            f'{self.pln_contribution_gross:.2f}',
            f'{self.usd_contribution_refund:.2f}',
            f'{self.vest_day_ratio:.6f}',
            f'{self.pln_contribution_net:.2f}',
            f'{self.shares_purchased}',
            self.file,
        ])

    @staticmethod
    def get_table_header():
        """Return table header for CSVed objects."""
        return ','.join([
            'VEST_DATE',
            'PLN_CONTRIB_GROSS',
            'USD_CONTRIB_REFUND',
            'VEST_DAY_RATIO',
            'PLN_CONTRIB_NET',
            'SHARES_PURCHASED',
            'FILE',
        ])


class RestrictedStock():
    """Contains all data for RS stock vest."""

    def __init__(self):
        """Init restricted stock object."""
        self.release_date = datetime.datetime.fromtimestamp(0)
        self.shares_released = 0
        self.release_gain = 0.0
        self.file = ''

    def get_csved_object(self):
        """Csved class object."""
        return ','.join([
            self.release_date.strftime('%d.%m.%Y'),
            f'{self.shares_released}',
            f'{self.release_gain:.2f}',
            self.file,
        ])

    @staticmethod
    def get_table_header():
        """Return table header for CSVed objects."""
        return ','.join([
            'VEST_DATE',
            'SHARES_RELEASED',
            'USD_GAIN',
            'FILE',
        ])


class Stock():
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

    def get_csved_object(self):
        """Csved class object."""
        return ','.join([
            self.buy_date.strftime('%d.%m.%Y') if self.buy_date else '',
            f'{self.buy_shares_count}' if self.buy_shares_count else '',
            f'{self.buy_tax_deductible:.2f}' if self.buy_tax_deductible else '',
            self.sale_date.strftime('%d.%m.%Y') if self.sale_date else '',
            f'{self.sale_shares_count}' if self.sale_shares_count else '',
            f'{self.sale_income:.2f}' if self.sale_income else '',
        ])

    @staticmethod
    def get_table_header():
        """Return table header for CSVed objects."""
        return ','.join([
            'BUY_DATE',
            'BUY_SHARES_COUNT',
            'BUY_TAX_DEDUCT',
            'SELL_DATE',
            'SELL_SHARES_COUNT',
            'SELL_INCOME',
        ])


def cash_to_float(str_number):
    """Cast cash string with comma separator to float."""
    return float(str_number.replace(',', ''))


def get_espp_from_text(text):
    """Find all ESPP bought stocks data in text."""
    if 'EMPLOYEE STOCK PLAN PURCHASE CONFIRMATION' not in text:
        return ''
    lines = text.split('\n')
    stock = EsppStock()
    for line in lines:
        if 'Purchase Date' in line:
            stock.purchase_date = datetime.datetime.strptime(line.split()[2][:-6], '%m-%d-%Y')
        if 'Foreign Contributions' in line:
            stock.pln_contribution_gross = cash_to_float(line.split()[-1])
        if 'Average Exchange Rate' in line:
            stock.vest_day_ratio = float(line.split()[-1][1:])
        if 'Amount Refunded' in line:
            stock.usd_contribution_refund = float(line.split()[-1][2:-1])
        if 'Shares Purchased' in line and len(line.split()) == 3:
            stock.shares_purchased = int(float(line.split()[-1]))

    stock.calculate_pln_contribution_net()
    return stock


def get_rs_from_text(text):
    """Find all Restricted Stocks vested data in text."""
    if 'EMPLOYEE STOCK PLAN RELEASE CONFIRMATION' not in text:
        return ''
    lines = text.split('\n')
    rest = RestrictedStock()
    for line in lines:
        if 'Release Date' in line:
            rest.release_date = datetime.datetime.strptime(line.split()[-1], '%m-%d-%Y')
        if 'Shares Released' in line and len(line.split()) == 3:
            rest.shares_released = int(float(line.split()[-1]))
        if 'Total Gain' in line:
            rest.release_gain = cash_to_float(line.split()[-1][1:])
    return rest


def get_trade_from_text(text):
    """Find all trade data in text."""
    if 'TRADECONFIRMATION' not in text:
        return ''
    lines = text.split('\n')
    trade = Trade()
    for line in lines:
        if 'Stock Plan' in line:
            trade.shares_sold = int(line.split()[5])
            date_str = f'{line.split()[0][:-2]}20{line.split()[0][-2:]}'
            trade.trade_date = datetime.datetime.strptime(date_str, '%m/%d/%Y')
        if 'NET AMOUNT' in line:
            trade.usd_net_income = cash_to_float(line.split()[-1][1:])
    return trade


def process_stock_docs(directory):
    """Process all docs and find stocks data."""
    files = etc.get_all_pdf_files(directory)
    espps = []  # Employee Stock Purchase Plan
    rests = []  # Restricted Stock
    trades = []  # stocks sell events
    for filename in files:
        full_path = f'{directory}/{filename}'
        text = etc.get_text_from_file(full_path)
        espp = get_espp_from_text(text)
        rest = get_rs_from_text(text)
        trade = get_trade_from_text(text)
        if espp:
            espp.file = full_path
            espps.append(espp)
        if rest:
            rest.file = full_path
            rests.append(rest)
        if trade:
            trade.file = full_path
            trade.insert_currencies_ratio(*etc.get_usd_pln_ratio(trade.trade_date))
            trades.append(trade)

    etc.save_csv('detailed_espp.csv', EsppStock.get_table_header(), espps)
    etc.save_csv('detailed_rs.csv', RestrictedStock.get_table_header(), rests)
    etc.save_csv('detailed_trades.csv', Trade.get_table_header(), trades)
    stocks_events = [Stock(x) for x in espps + rests + trades]
    etc.save_csv('sum_stocks.csv', Stock.get_table_header(), stocks_events)
