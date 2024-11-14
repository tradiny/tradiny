# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

from json import JSONEncoder, loads, dumps
from pandas import Timestamp, DataFrame
import numpy as np
import pickle
import importlib
import inspect
import copy
import codecs


class CustomEncoder:

    def encode(self, d, debug=False):
        serializable = self.do_encode(d, 0, debug=debug)
        return dumps(serializable, sort_keys=True)

    def do_encode(self, d, l=0, debug=False):

        d = copy.copy(d)

        if isinstance(d, dict) or type(d) == dict:

            todel = ["_cache", "df_cache"]
            for key in todel:
                if key in d:
                    del d[key]

            for k, v in d.items():
                # print(k) # for debug purposes
                d[k] = self.do_encode(v, l + 1, debug)

        if isinstance(d, (np.ndarray,)):
            d = d.tolist()

        if isinstance(d, list) or type(d) == list:
            for k, v in enumerate(d):
                d[k] = self.do_encode(v, l + 1, debug)

        if type(d) == Timestamp:
            return str(d)

        if hasattr(d, "serialize"):
            s = d.serialize()
            s = self.do_encode(s, 0, debug=True)
            return s

        if isinstance(d, dict) or type(d) == dict:
            d = dict(d)

        if isinstance(d, list) or type(d) == list:
            d = list(d)

        if (
            hasattr(d, "__class__")
            and d.__class__.__name__ == "Connection"
            and d.__class__.__module__ == "sqlite3"
        ):
            d = None

        if isinstance(d, DataFrame):
            d = {
                "type": "DataFrame",
                "data": codecs.encode(pickle.dumps(d), "base64").decode(),
            }

        if isinstance(
            d,
            (
                np.int_,
                np.intc,
                np.intp,
                np.int8,
                np.int16,
                np.int32,
                np.int64,
                np.uint8,
                np.uint16,
                np.uint32,
                np.uint64,
            ),
        ):
            d = int(d)

        if isinstance(d, (np.float_, np.float16, np.float32, np.float64)):
            d = float(d)

        if isinstance(d, np.bool_):
            d = bool(d)

        if isinstance(d, (np.void)):
            d = None

        if callable(d):
            d = str(d)

        # if type(d) == bytes:
        #    print(d)
        #    input()

        return d


class CustomDecoder:
    def decode(self, d):
        if type(d) == str:
            try:
                d = loads(d)
            except:
                pass

        if type(d) == dict:
            for k, v in d.items():
                d[k] = self.decode(v)

        if type(d) == list:
            for k, v in enumerate(d):
                d[k] = self.decode(v)

        if type(d) == dict and "type" in d and d["type"] == "DataFrame" and "data" in d:
            return pickle.loads(codecs.decode(d["data"], "base64"))

        if type(d) == dict and "klass_path" in d:
            bn = d["klass_path"].split(".")
            base_name = bn[-1]
            bn.pop()
            package = ".".join(bn)
            base = getattr(importlib.import_module(package), base_name)
            return base.deserialize(d)

        return d
