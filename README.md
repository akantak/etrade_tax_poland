# Etrade docs parsing for dividends and stocks vest/sell

Use at your own risk! Do not treat it as a tax consultancy.

## General

Those scripts were initially designed to calculate taxes from E\*TRADE dividends for Intel employees.
Stock sales/vesting and liquidity funds were added later. It was not tested with any other entities.
Those scripts also calculates buy/vest day price in PLN for stock, so user can use cross-check that
with potential selling price.

### Installation

Install python module:

```bash
python3 -m pip install --upgrade git+https://github.com/akantak/etrade_tax_poland.git@v0.0.12
```

### Preparation

Prepare a directory with all PDF files to be considered for the parsing process. Review sections
[Dividends](#dividends) and [Stocks](#stocks).

### Usage

Run the installed python module directly in the directory with PDFs:

```bash
python3 -m etrade_tax_poland
```

or pass the directory as an argument (if the statements are in ex. `/tmp/statements`):

```bash
python3 -m etrade_tax_poland /tmp/statements
```

#### Additional parameter flags

- `-x` - don't compile to xlsx, data would stay in csv files
- `-d` - debug version, would save all objects in json format to *.json files

Example command using all possible parameters

```bash
python3 -m etrade_tax_poland -d -x /tmp/statements
```

### Output

In the previously indicated directory, there will be created a spreadsheet file `etrade.xslx`,
with multiple sheets, one for each data type.

After the spreadsheet is prepared, review if all entries are valid for the selected fiscal year,
and review if any stock purchase data were not already included in previous PITs.

## Dividends

There is a script prepared that calculates paid tax vs due tax for stock dividends
based on multiple E\*Trade statements.

Also, there is a second dividend type for dividends paid from the Liquidity Fund.
For those, there is no tax paid in the US.

### Dividends calculation methodology

The dividends withholding tax (`podatek u źródła`) is 15% (for stocks dividends), while in Poland,
the capital gains tax is 19%, so it is required to pay an additional 4% in Poland.

While, for the Liquidity Fund dividends, one has to pay the whole 19% tax in Poland.

The amounts in USD have to be converted with the NBP ratio from the day before granting/vesting.

### Dividends documents

Prepare a directory with all the statements from E\*TRADE to be considered during tax calculation.
Those statements are named like: `Brokerage Statement (...).pdf`
or `MS_ClientStatements_(...).pdf`. Multiple files allowed.

Those statements can be found on <https://edoc.etrade.com/e/t/onlinedocs/docsearch?doc_type=stmt>.

### Dividends PIT-38 filling

Open dividends' spreadsheet. Start with filtering data for selected year only.
Then, in PIT-38, section E:

- sum of `PLN_TAX_TOTAL` column values for selected year should be put in field 34
- sum of `PLN_TAX_PAID` column values for selected year should be put in field 35
- sum of `PLN_TAX_DUE` column values for selected year should be put in field 36

## Stocks

Parse stocks purchase/vest/sell documents.

### Stocks calculation methodology

For selling `Restricted Stocks RS`, there are 0 tax-deductible costs.

When selling the `Employee Stock Purchase Plan (ESPP)`, the purchase price is the tax-deductible cost.

### Stocks gain (bought or vest) documents

Go to <https://us.etrade.com/etx/sp/stockplan#/myAccount/stockPlanConfirmations>
and download all files that should be taken into consideration.
Those files will be named `getEsppConfirmation.pdf` or `getReleaseConfirmation.pdf`.

### Trades confirmation

To get trade confirmations, go to <https://edoc.etrade.com/e/t/onlinedocs/docsearch?doc_type=cnf>
and download the required confirmations.
Those files will be named `ETRADE Brokerage Trade Confirmation (...).pdf`.

### Stocks PIT-38 filling

Open stocks' spreadsheet. It contains all three types of actions:

- espp (stocks bought)
- rs (stocks vested)
- trade (stocks sold)

Sell rows are shifted on purpose, so those can be cut and pasted to according acquisition action.
If it is Restricted Stock, there is nothing that is deductible from tax.
If it is Employee Stock Purchase Plan, the net contribution is deductible.

Match all selling actions with the corresponding acquisition action, based on shares count.
According to the law, stocks are sold FIFO (first in first out). If you did not sell the
oldest stocks first, do the matching on your own.
Remove the rest of acquisition actions that do not have a match, to not pollute the tax deduct.

PLN prices (`REAL_BUY_PRICE_PLN` and `DATE_BUY_PRICE_PLN`) are for information only.

Following statements are considering these calculations the only ones that are put in PIT-38.
If it is not true and there are more incomes to be considered, adjust the required fields.

In PIT-38, section C and D:

- sum of `SELL_INCOME` column for selected year should be put fields 21 and 23
- sum of `BUY_TAX_DEDUCT` columns for selected year should be put in fields 22 and 24
- difference between fields 23 and 24 should be put in field 25
- rounded field 25 should be put in field 28
- field 28 multiplied by tax 19% should be put in field 30
- rounded field 30 should be put in field 32
