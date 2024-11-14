To add a data source, create a new class in the `backend/data_providers/` directory and include it in the `populate.py` and `server.py` scripts.

Here are the existing data source providers:

1. **Binance** - Fetches and streams live data from the Binance cryptocurrency exchange.
1. **Polygon** - Fetches and streams live data from Polygon.io.
1. **CSV** - Parses and provides data from CSV files.

The `populate.py` script retrieves all symbol names (e.g., stock META, EUR-USD pair, or Bitcoin-USD cryptocurrency) and stores them in an SQLite database to allow fast access.

If you create your own provider, for example, `MyProvider`, add this code to `populate.py` to fetch the list of symbols:

```python
from data_providers.my_provider import MyProvider
my_provider = MyProvider()
db.populate_database_from_provider(Config.DB, my_provider)
```

This will execute the `get_dataset` method, which should return a list of objects specifying the symbols. For example:

```python
{
    "source": "my_provider",
    "name": "BTCUSDT", # your symbol key
    "name_label": "Bitcoin - USD pair",
    "type": "candlestick", # or "line"
    "categories": ['Crypto'], # category
    "intervals": [ # which intervals your provider support
        '1m',
        '3m',
        '5m',
        '15m',
        '30m',
        '1h',
        '2h',
        '4h',
        '6h',
        '8h',
        '12h',
        '1d',
        '1w',
        '1M'
    ],
    "outputs": [ # what outputs and their axes your class provide
        {
            "name": f"open", # example: this is OPEN price
            "y_axis": f"price"
        },
        {
            "name": f"high",
            "y_axis": f"price"
        },
        {
            "name": f"low",
            "y_axis": f"price"
        },
        {
            "name": f"close",
            "y_axis": f"price"
        },
        {
            "name": f"volume",
            "y_axis": f"volume"
        }
    ]
}
```

After implementing the `get_dataset` method, run the `populate.py` script. This allows you to see the data sources in the user interface and begin implementing methods for streaming data and fetching historical data.

Each provider operates as a separate process, communicating with the asynchronous WebSocket FastAPI application using queues. You don't need to worry about asynchronous programming; your entire implementation will be synchronous.

Note: We chose to use a process because it provides a safer, more stable approach for data source libraries, based on our experience.

For convenience, if you inherit from the `Provider` class, communication methods and process management are included. This means you only need to implement:

- `init(self)`: Optionally initialize objects.
- `start_streaming(self, ws_client, symbol, interval)`: Triggered when a user, identified by `ws_client` (which is an `id()`), connects to your data source. Your task is to send new data points to the queue.

```python
self.send_from({
    'action': 'write_message',
    'ws_clients': ws_clients, # send the message to these ws_clients
    'source': "my_provider",
    'name': symbol,
    'interval': interval,
    'args': [
        json.dumps({
            'type': 'data_update',
            'source': "my_provider",
            'name': symbol,
            'interval': interval,
            'data': data
        })
    ]
})
```

The format of a data point is as follows:

```python
def format_datapoint(self, symbol, interval, k):
    date_str = datetime.fromtimestamp(k[0] / 1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    return {
        "date": date_str,
        f"my_provider-{symbol}-{interval}-open": k[1],
        f"my_provider-{symbol}-{interval}-high": k[2],
        f"my_provider-{symbol}-{interval}-low": k[3],
        f"my_provider-{symbol}-{interval}-close": k[4],
        f"my_provider-{symbol}-{interval}-volume": k[5]
    }
```

You might consider storing each user ID (`ws_client`) and starting the data stream only once when the first client connects. When all clients have disconnected, stop the streaming in the `on_close` method (explained below).

Note: You can see the complete example in `backend/data_providers/binance.py`.

- `no_update(self, symbol, interval)`: Triggered when there hasn't been an update for a while.
- `get_history(self, symbol, interval, start_time_query, end_time_query, count)`: Triggered when a user requests historical data for a symbol. Your task is to return an array of historical data points for each date in the format `%Y-%m-%d %H:%M:%S`.

Note: Caching is already set up, so you don't need to worry about it.

- `on_close(self, ws_client, symbol, interval)`: Triggered when the client disconnects.

To get your MyProvider process going, register it in the `server.py` file to include it in the application:

```python
    from data_providers.my_provider import MyProvider
    my_provider = MyProvider()
    my_provider.start()

    async def startup_event():
        ...
        register_provider(my_provider)
```
