# Plotting Chart

Here is a minimal example:

```html
<!-- import dependencies -->
<script src="/js/blueimp-tmpl.min.js"></script>
<script src="/js/d3.min.js"></script>
<script src="/js/d3fc.min.js"></script>

<!-- import Tradiny -->
<link rel="stylesheet" href="/tradiny.css">
<script src="/tradiny.js"></script>

<!-- define target element -->
<div id="chart" class="tradiny-chart"></div>

<!-- render with backend at localhost:8000 -->
<script>
    var chart = TradinyChart.initialize({
        elementId: 'chart',
        charts: [
            {
                dataProvider: {
                    url: 'localhost:8000'
                },
            }
        ]
    });
</script>
```

In the example, we call `TradinyChart.initialize` to render the chart inside the `elementId` div. We specify rendering one chart and fetching data from `localhost:8000`.

Explore more examples in the `examples` folder:

- **candlestick.html**: Displays a candlestick chart with full control options, including exponential moving average.
- **candlestick2.html**: Features a dual-pane layout with a minimalist, white theme and no controls.
- **empty.html**: Offers a blank slate for selecting a data source.

## Customizing Features

You can customize the features of the chart by specifying a `features` array during initialization.

### Example Usage

```javascript
var chart = TradinyChart.initialize({
    elementId: 'chart',
    features: ['drawing', 'brush'], // <-- here
    charts: [
        {
            dataProvider: {
                url: 'localhost:8000'
            },
        }
    ]
});
```

### Available Features

| Feature             | Description                                   |
| ------------------- | --------------------------------------------- |
| **grid**            | Toggle grid                                   |
| **interval**        | Change the time interval / time frame         |
| **add**             | Window for adding data, indicators, or alerts |
| **drawing**         | Enable drawing tools                          |
| **back**            | Navigate backward                             |
| **text**            | Add text annotations                          |
| **line**            | Draw straight lines                           |
| **horizontal-line** | Draw horizontal lines                         |
| **vertical-line**   | Draw vertical lines                           |
| **brush**           | Use brush tool for curves                     |
| **ruler**           | Measure distances                             |
| **fib**             | Use Fibonacci tool                            |
| **save**            | Save the current chart                        |
| **prompt**          | Invoke ChatGPT                                |

This setup allows you to tailor the chart's functionality to your needs by selecting which features you wish to enable or disable.

## Displaying Data Range

To control the amount of data shown on the chart, you can use the `visiblePoints` option to display a specific number of data points. For example, to show the last 300 data points:

```javascript
var chart = TradinyChart.initialize({
    elementId: 'chart',
    charts: [
        {
            dataProvider: {
                url: 'localhost:8000'
            },
            visiblePoints: 300, // Display the last 300 data points
        }
    ]
});
```

The data provider uses the `count` parameter to manage the volume of data being loaded. Here's an example configuration:

```json
dataProvider: {
    url: url,
    data: [
        {
            'type': 'data',
            'source': source,
            'name': name,
            'interval': interval,
            'count': 300
        }
    ]
}
```

In this example, the `count` parameter is set to 300, specifying the desired number of data points to retrieve.

Alternatively, you can define a specific date range by setting an initial zoom with start and end dates:

```javascript
var chart = TradinyChart.initialize({
    elementId: 'chart',
    charts: [
        {
            dataProvider: {
                url: 'localhost:8000'
            },
            initialZoom: { 
                start: '2024-10-12 16:00:00', 
                end: '2024-10-12 16:30:00'
            },
        },
    ]
});
```
