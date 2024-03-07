# dividends_tax_poland

There is a script prepared that calculates paid tax vs due tax for dividends
based on multiple E*Trade statements.

## Example output

```txt
DIVIDENDS GROSS: 1385.48 zł
DIVIDENDS PROPER TAX: 263.24 zł
DIVIDENDS PAID TAX: 207.82 zł
DIVIDENDS DUE TAX: 55.42 zł
```

This script also creates a `dividends.csv` file with dividents entries one by one.

## Usage

Prepare a directory with all the statements from E*TRADE to be considered during tax calculation.
Those statements are named like: `Brokerage Statement - XXXXX4108 - 202301.pdf`
or `MS_ClientStatements_4108_202309.pdf`. Multiple files allowed.

Those statements can be found on <https://edoc.etrade.com/e/t/onlinedocs/docsearch?doc_type=stmt>.

Install script dependencies:

```bash
python3 -m pip install pypdf requests
```

Run the script:

```bash
python3 dividends.py /tmp/statements
```

or copy this script to the directory with statements and run:

```bash
python3 dividends.py
```
