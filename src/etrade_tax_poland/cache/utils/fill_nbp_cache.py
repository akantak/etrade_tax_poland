"""Fill the NBP cache."""

import datetime

try:
    from ..nbp import date_to_usd_pln
except ImportError:
    from etrade_tax_poland.cache.nbp import date_to_usd_pln


date_obj = datetime.datetime.now()
end = datetime.datetime.fromisoformat("2020-01-01")
while True:
    print(f"{date_obj.year}.{date_obj.month}.{date_obj.day}")
    if date_obj < end:
        break
    date_to_usd_pln(date_obj)
    date_obj -= datetime.timedelta(days=1)
