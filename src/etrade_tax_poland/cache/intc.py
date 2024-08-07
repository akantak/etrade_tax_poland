"""Implement Intc prices gathering."""

import datetime
import os

import requests

from .cache_file import CacheFile


class IntcPricesCache(CacheFile):
    """Cached data for intc stocks"""

    date_format = "%Y-%m-%d"

    def __init__(self):
        """Initialize objects and fields."""
        super().__init__(f"{os.path.dirname(os.path.abspath(__file__))}/.intc_cache.json")
        self.begin_date = datetime.datetime(2000, 1, 1, 0, 0)

    def fill_in(self, token: str, end_date: datetime.datetime):
        """Ask url for intc stock prices, requires token"""
        url = "https://app.quotemedia.com/datatool/getFullHistory.json"
        params = {
            "symbol": "INTC",
            "unadjusted": "true",
            "adjusted": "true",
            "adjustmentType": "None",
            "zeroTradeDays": "true",
            "start": self.begin_date.strftime(self.date_format),
            "end": end_date.strftime(self.date_format),
            "token": token,
        }
        headers = {
            "accept": "*/*",
            "accept-language": "en",
            "origin": "https://www.intc.com",
            "priority": "u=1, i",
            "referer": "https://www.intc.com/",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",  # pylint: disable=line-too-long
        }

        response = requests.get(url, headers=headers, params=params, timeout=60)

        cache = {"_": ""}
        if response.status_code == 200:
            for entry in response.json()["results"]["history"][0]["eoddata"]:
                cache[entry["date"]] = entry["close"]
            self.write_cache()
        else:
            print(f"Request failed with status code: {response.status_code}.")
            if response.status_code == 403:
                raise PermissionError()

    def get_ratio(self, date_obj):
        """Get ratio from cache if available, otherwise raise exception."""
        key = date_obj.strftime(self.date_format)
        if key in self.cache:
            return self.cache[key]
        raise ValueError(f"Price for {date_obj.strftime(self.date_format)} was not found")


INTC_CACHE = IntcPricesCache()


def date_to_intc_price(date_obj):
    """Find intc price for date."""
    days = 10  # check up to 10 days back, otherwise raise exception
    for _ in range(days):
        try:
            ratio = INTC_CACHE.get_ratio(date_obj)
            return (date_obj, ratio)
        except ValueError:
            date_obj -= datetime.timedelta(days=1)
    raise ValueError(f"Price for {date_obj.strftime('%Y-%m-%d')} and {days} days back not found")
