# This software is licensed under a dual-license model:
# 1. Under the Affero General Public License (AGPL) for open-source use.
# 2. With additional terms tailored to individual users (e.g., traders and investors):
#
#    - Individual users may use this software for personal profit (e.g., trading/investing)
#      without releasing proprietary strategies.
#
#    - Redistribution, public tools, or commercial use require compliance with AGPL
#      or a commercial license. Contact: license@tradiny.com
#
# For full details, see the LICENSE.md file in the root directory of this project.

from os import listdir
from os.path import isfile, isdir, join, dirname, abspath
import importlib
import sys, inspect


def _get_modules(module_name):

    module = importlib.import_module(module_name)
    objs = []

    for name, obj in inspect.getmembers(module):
        if (
            inspect.isclass(obj)
            and hasattr(obj, "inputs")
            and hasattr(obj, "outputs")
            and hasattr(obj, "calc")
        ):

            if hasattr(obj, "disabled") and obj.disabled:
                continue

            objs.append(obj)

    return objs


def _iterator():
    indicator_names = []
    d = dirname(abspath(__file__))
    fs = [f for f in listdir(d) if isfile(join(d, f)) and f.lower().endswith(".py")]
    for f in fs:
        yield "indicators." + f[:-3]

    fs = [
        f for f in listdir(d) if isdir(join(d, f)) and f not in [".git", "__pycache__"]
    ]
    for d2 in fs:
        if d2 in ["data"]:
            continue
        fs = [
            f
            for f in listdir(join(d, d2))
            if isfile(join(d, d2, f)) and f.lower().endswith(".py")
        ]
        dirs = [d3 for d3 in listdir(join(d, d2)) if isdir(join(d, d2, d3))]
        for f in fs:
            yield "indicators." + d2 + "." + f[:-3]

        for d3 in dirs:
            fs2 = [
                f
                for f in listdir(join(d, d2, d3))
                if isfile(join(d, d2, d3, f)) and f.lower().endswith(".py")
            ]
            for f in fs2:
                yield "indicators." + d2 + "." + d3 + "." + f[:-3]


def get_indicator_data():
    indicators = {}
    for m in _iterator():
        objs = _get_modules(m)
        for obj in objs:
            k = m + "." + obj.__name__
            if hasattr(obj, "disabled") and obj.disabled:
                continue
            indicators[k] = {
                "path": k,
                "klass": obj,
                "name": obj.name if hasattr(obj, "name") else None,
                "categories": obj.categories if hasattr(obj, "categories") else [],
            }
            for i, c in enumerate(indicators[k]["categories"]):
                indicators[k]["categories"][i] = c.lower()
    return indicators


def get_indicator_names():
    indicator_names = []
    for m in _iterator():
        objs = _get_modules(m)
        for obj in objs:
            indicator_names.append(m + "." + obj.__name__)
    return indicator_names
