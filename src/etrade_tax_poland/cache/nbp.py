"""Implement NBP currencies ratios gathering."""

import datetime
import os
from time import sleep

import requests

from .cache_file import CacheFile


class NbpRatiosCache(CacheFile):
    """Cache data instead of always requesting from NBP."""

    date_format = "%Y-%m-%d"
    nbp_url = "https://api.nbp.pl/api/exchangerates/rates/a/usd/{}/?format=json"

    def __init__(self):
        """Initialize objects and fields."""
        super().__init__(f"{os.path.dirname(os.path.abspath(__file__))}/.nbp_cache.json")

    def get_ratio(self, date_obj):
        """Get ratio from cache if available, otherwise request from NBP."""
        key = date_obj.strftime(self.date_format)
        if key in self.cache:
            if not self.cache[key]:
                raise ValueError("Ratio for selected date is not available in NBP")
            return self.cache[key]

        while True:
            try:
                current_url = self.nbp_url.format(date_obj.strftime(self.date_format))
                req = requests.get(current_url, timeout=5)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout):
                print("Timeout 5s when getting USD/PLN ratio, retrying after 1 second")
                sleep(1)
                continue
            if req.status_code == 200:
                self.cache[key] = req.json()["rates"][0]["mid"]
                self.write_cache()
                return self.cache[key]
            if req.status_code == 404:
                self.cache[key] = ""
                self.write_cache()
                raise ValueError("Ratio for selected date is not available in NBP")
            print(f"{req.status_code} {req.text}")
            print("Unhandled error when getting USD/PLN ratio, retrying after 1 second")
            sleep(1)
            continue


NBP_CACHE = NbpRatiosCache()


def date_to_usd_pln(date_obj):
    """Find 'day before vestment' USD/PLN ratio."""
    while True:
        date_obj -= datetime.timedelta(days=1)
        try:
            ratio = NBP_CACHE.get_ratio(date_obj)
            break
        except ValueError:
            date_obj -= datetime.timedelta(days=1)
    return (date_obj, ratio)
