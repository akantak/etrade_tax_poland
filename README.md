# dividends_tax_poland

There is a script prepared that calculates paid tax vs due tax for dividends
based on multiple E*Trade statements.

## Example output

```txt
JSON data:
[{"pay_date": "03/01/2023", "gross_dividend": 96.36, "tax": 14.45, "net_dividend": 81.91, "ratio_date": "2023-02-24", "ratio_value": 4.463}, {"pay_date": "06/01/2023", "gross_dividend": 69.0, "tax": 10.35, "net_dividend": 58.65, "ratio_date": "2023-05-29", "ratio_value": 4.2234}, {"pay_date": "09/01/2023", "gross_dividend": 70.13, "tax": 10.52, "net_dividend": 59.61, "ratio_date": "2023-08-29", "ratio_value": 4.1341}, {"pay_date": "12/1/2023", "gross_dividend": 94.25, "tax": 14.14, "net_dividend": 80.22, "ratio_date": "2023-11-28", "ratio_value": 3.975}]

DIVIDENDS GROSS: $329.74
DIVIDENDS TAX PAID: $49.46
DIVIDENDS NET: $280.39

DIVIDENDS GROSS: 1386.04 zł
DIVIDENDS PROPER TAX: 263.35 zł
DIVIDENDS PAID TAX: 207.90 zł
DIVIDENDS DUE TAX: 55.45 zł
```

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
