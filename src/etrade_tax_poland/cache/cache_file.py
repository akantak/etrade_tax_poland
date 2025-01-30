"""Handle file operations for cache in file"""

import json
import os


class CacheFile:
    """Handle Cache in file stored locally"""

    def __init__(self, cache_file_name):
        self.cache_file = cache_file_name
        self.cache = {"_": ""}
        self.read_cache()

    def read_cache(self):
        """Read cache file."""
        if not os.path.isfile(self.cache_file):
            return
        with open(self.cache_file, "r", encoding="utf-8") as file:
            self.cache = json.load(file)

    def write_cache(self):
        """Write cache file."""
        json_dump_params = {
            "sort_keys": True,
            "indent": 2,
            "separators": (",", ": "),
        }
        with open(self.cache_file, "w", encoding="utf-8") as file:
            json.dump(self.cache, file, **json_dump_params)
            file.write("\n")
