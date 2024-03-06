# dividends_tax_poland

Copy this script to the directory with statements from E*TRADE, like:
`Brokerage Statement - XXXXX4108 - 202301.pdf` or `MS_ClientStatements_4108_202309.pdf`.
Multiple files allowed.

Those statements can be found on <https://edoc.etrade.com/e/t/onlinedocs/docsearch?doc_type=stmt>.

Install dependencies:

```bash
python3 -m pip install pypdf requests
```

Run the script:

```bash
python3 dividends.py
```
