"""Fill the NBP cache."""

import datetime

from .nbp import date_to_usd_pln

date_obj = datetime.datetime.now()
end = datetime.datetime.fromisoformat("2020-01-01")
while True:
    if date_obj < end:
        break
    date_to_usd_pln(date_obj)
    date_obj -= datetime.timedelta(days=1)
