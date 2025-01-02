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

import importlib


def fullname(o):
    klass = o.__class__
    module = klass.__module__
    if module == "builtins":
        return klass.__qualname__  # avoid outputs like 'builtins.str'
    return module + "." + klass.__qualname__


class Serializable(dict):

    def __getstate__(self):
        # Return a dictionary representing the object's state
        return self.__dict__

    def __setstate__(self, state):
        # Restore the object's state from the `state` dictionary
        self.__dict__.update(state)

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

    @staticmethod
    def deserialize(d):
        bn = d["klass_path"].split(".")
        base_name = bn[-1]
        bn.pop()
        package = ".".join(bn)
        base = getattr(importlib.import_module(package), base_name)
        b = base()
        b.update(d)
        return b

    def serialize(self):
        d = dict(self)
        if "klass_path" not in d:
            klass_path = fullname(self)
            d["klass_path"] = klass_path
        return d
