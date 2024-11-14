To add a new indicator, create a class using this folder structure:

`indicators/YOUR_LIBRARY_NAME/CATEGORY/INDICATOR_NAME.py`

Let's use the EMA indicator as an example. The class should be structured as follows:

```python
import pandas as pd
import pandas_ta as ta
import numpy as np

from indicators.data.indicator import Indicator

class EMA(Indicator):
    name = 'Exponential Moving Average' # name of indicator
    categories = ['Overlap'] # category

    columns = ['close'] # which columns from data source, the indicator uses
    
    inputs = [
        {
            'name': 'length', # key to identify the input value
            'space': list(range(2, 300)), # (optional) available values for length
            'default': [ # default values, first is used in placeholder
                10
            ]
        }
    ]

    outputs = [
        {
            'name': 'EMA', # outputs just one array on price axis
            'y_axis': 'price'
        }
    ]

    def calc(self, data, length): # implement your indicator here
        
        # here is the example of using pandas_ta for EMA

        # create DataFrame from the incoming data
        df = pd.DataFrame(data)
        df.columns = ["Date"] + self.columns
        df.set_index(pd.DatetimeIndex(df["Date"]), inplace=True) # set Date as an index
        df[df.columns.difference(['Date'])] = df[df.columns.difference(['Date'])].apply(pd.to_numeric, errors='coerce').astype(np.float64)

        # calculate EMA
        df.ta.ema(length=int(length), cumulative=True, append=True)

        # extract name
        out_name = df.columns[-1]

        # return EMA
        return [
            [[r['Date'], r[out_name]] for r in df.to_dict(orient='records')] # return one output named EMA on price axis
        ]
```

Then, simply run the `populate.py` script to display your indicator in the list of indicators.
