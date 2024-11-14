## Configuring and Visualizing an Indicator

To configure and visualize an indicator as a line in your application, follow these steps:

1. Open the browser developer console.

1. Open the chart and load the indicator with your desired settings.

1. The console will display an indicator setting string, which has the following format:

    ```json
    {
        "type": "indicator",
        "id": "indicators-pandas_ta-overlap-ema-EMA_length-50_close-Binance-BTCUSDT-5m-close",
        "indicator": {
            "id": "indicators.pandas_ta.overlap.ema.EMA",
            "name": "Exponential Moving Average",
            "details": {
                "categories": ["overlap"],
                "library": "pandas_ta",
                "columns": ["close"],
                "inputs": [{"name": "length", "default": [10]}],
                "outputs": [{"name": "EMA", "y_axis": "price"}]
            },
            "type": "indicator"
        },
        "inputs": {"length": "50"},
        "dataMap": {
            "close": {
                "source": "Binance",
                "name": "BTCUSDT",
                "interval": "5m",
                "value": "Binance-BTCUSDT-5m-close",
                "dataKey": "close"
            }
        },
        "render": {
            "indicatorId": "indicators-pandas_ta-overlap-ema-EMA_length-50_close-Binance-BTCUSDT-5m-close",
            "indicator": {
                "id": "indicators.pandas_ta.overlap.ema.EMA",
                "name": "Exponential Moving Average",
                "details": {
                    "categories": ["overlap"],
                    "library": "pandas_ta",
                    "columns": ["close"],
                    "inputs": [{"name": "length", "default": [10]}],
                    "outputs": [{"name": "EMA", "y_axis": "price"}]
                },
                "type": "indicator"
            },
            "inputs": {"length": "50"},
            "paneIdx": 0,
            "axesMap": {"price": "Binance-BTCUSDT-5m-price"},
            "scalesMap": {"price": "linear"},
            "colorMap": {"EMA": "#e60049"}
        }
    }
    ```

1. To integrate this indicator with line metadata for backend data representation, add the following configuration:

    ```json
    {
        type: 'line',
        legend: [{
            'icon': '&nbsp;',
            'label': `EMA length=50`,
            'color': '#e60049',
        }],
        dataKeys: [
            {
                dataKey: `indicators-pandas_ta-overlap-ema-EMA_length-50_close-Binance-BTCUSDT-5m-close-EMA`,
                yAxis: `${source}-${name}-${interval}-price`
            },
        ],
        color: '#e60049'
    }
    ```

This configuration will render the Exponential Moving Average indicator as a line on the chart, using the specified parameters for visual representation, like the line color and legend details.
