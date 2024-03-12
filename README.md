# Etrade docs parsing for dividends and stocks vest/sell

Using on your own risk!

## General

### Dependencies

Install script dependencies:

```bash
python3 -m pip install pypdf requests
```

### Preparation

Prepare a directory with all PDF files to be considered for parsing process. Review sections
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

In previously indicated directory, there will be created detailed files:

- detailed_dividends.csv
- detailed_espp.csv
- detailed_trades.csv

and files with sum ups:

- sum_dividends.txt
- sum_stocks.csv

## Dividends

There is a script prepared that calculates paid tax vs due tax for dividends
based on multiple E*Trade statements.

### Dividends calculation methodology

The dividends withholding tax (`podatek u źródła`) is 15%, while in Poland, the tax is 19%,
so it is required to pay additional 4% in Poland.

The amounts in USD have to be converted with the NBP ratio from the day before granting/vesting.

### Dividends documents

Prepare a directory with all the statements from E*TRADE to be considered during tax calculation.
Those statements are named like: `Brokerage Statement - XXXXX4108 - 202301.pdf`
or `MS_ClientStatements_4108_202309.pdf`. Multiple files allowed.

Those statements can be found on <https://edoc.etrade.com/e/t/onlinedocs/docsearch?doc_type=stmt>.

## Stocks

Prase stocks purchase/sell documents.

### Stocks calculation methodology

For selling `Restricted Stocks RS`, there is 0 tax deductible costs.

For selling `Employee Stock Purchase Plan (ESPP)`, the purchase price is a tax deductible cost.

### Stocks documents

Go to <https://us.etrade.com/etx/sp/stockplan?accountIndex=0&traxui=tsp_portfolios/#/myAccount/benefitHistory>
open `Employee Stock Purchase Plan (ESPP)`, open an entry to be considered in the calculations,
select `View Confirmation Of Purchase` and download a pdf with the purchase details.
That would be file named `getEsppConfirmation.pdf`.

To get trade confirmations, go to <https://edoc.etrade.com/e/t/onlinedocs/docsearch?doc_type=cnf>
and download required confirmations.
