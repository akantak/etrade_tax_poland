# Etrade docs parsing for dividends and stocks vest/sell

Use at your own risk!

## General

### Dependencies

Install script dependencies:

```bash
python3 -m pip install -r requirements.txt
```

### Preparation

Prepare a directory with all PDF files to be considered for the parsing process. Review sections
[Dividends](#dividends) and [Stocks](#stocks).

### Usage

Run the script providing a directory with statements as a parameter (ex. `/tmp/statements`):

```bash
python3 etrade.py /tmp/statements
```

or copy this script to the directory with statements and run:

```bash
python3 etrade.py
```

### Output

In the previously indicated directory, there will be created a spreadsheet file `etrade.xslx`,
with multiple sheets, one for each data type.

## Dividends

There is a script prepared that calculates paid tax vs due tax for dividends
based on multiple E*Trade statements.

### Dividends calculation methodology

The dividends withholding tax (`podatek u źródła`) is 15%, while in Poland, the capital gains tax is 19%,
so it is required to pay an additional 4% in Poland.

The amounts in USD have to be converted with the NBP ratio from the day before granting/vesting.

### Dividends documents

Prepare a directory with all the statements from E*TRADE to be considered during tax calculation.
Those statements are named like: `Brokerage Statement (...).pdf`
or `MS_ClientStatements_(...).pdf`. Multiple files allowed.

Those statements can be found on <https://edoc.etrade.com/e/t/onlinedocs/docsearch?doc_type=stmt>.

## Stocks

Parse stocks purchase/sell documents.

### Stocks calculation methodology

For selling `Restricted Stocks RS`, there are 0 tax-deductible costs.

When selling the `Employee Stock Purchase Plan (ESPP)`, the purchase price is the tax-deductible cost.

### Stocks documents

Go to <https://us.etrade.com/etx/sp/stockplan#/myAccount/stockPlanConfirmations>
and download all files that should be taken into consideration.
Those files will be named `getEsppConfirmation.pdf` or `getReleaseConfirmation.pdf`.

### Trades confirmation

To get trade confirmations, go to <https://edoc.etrade.com/e/t/onlinedocs/docsearch?doc_type=cnf>
and download the required confirmations.
Those files will be named `ETRADE Brokerage Trade Confirmation (...).pdf`.
