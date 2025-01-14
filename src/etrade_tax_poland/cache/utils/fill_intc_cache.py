"""
To get quote media token go to: https://www.intc.com/stock-info/historical-data
enter developer mode, set some dates, press Show results
and extract the token from the request to getFullHistory.json?(...)
and export as a env variable QUOTEMEDIA_TOKEN before running this script

Example usage:
python3 -m etrade_tax_poland.cache.utils.fill_intc_cache
"""

import os
from datetime import datetime

try:
    from ..intc import INTC_CACHE
except ImportError:
    from etrade_tax_poland.cache.intc import INTC_CACHE

token = os.environ.get("QUOTEMEDIA_TOKEN", "")
if not token:
    raise ValueError("Token exported in QUOTEMEDIA_TOKEN env required. Check source for more info")
try:
    INTC_CACHE.fill_in(token, datetime.now())
except PermissionError:
    print("Check the QUOTEMEDIA_TOKEN env variable. For more details check this script source")
