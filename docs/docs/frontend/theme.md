## Styles

To apply a custom theme to a chart, specify the theme key during initialization. For example, to use the `dark` theme, configure it as follows:

```javascript
TradinyChart.initialize({
    elementId: "chart",
    grid: "1x1",
    theme: 'dark',  // <-- specify the theme here
    size: 'small',  // <-- specify the size here
    charts: [
        {
            dataProvider: {
                ...
            }
            ...
        }
    ]
})
```

After setting the theme, import the corresponding CSS file and define your styles. The styles for the `dark` theme can be found in `frontend/static/dark.css`.

## Size of the Chart

The chart supports two sizes: `small` and `large` (default). You can specify the size in the same way as the theme during initialization. If you do not specify a size in the chart configuration, mobile devices will automatically use the small size.

## Custom Legends

While defining metadata, you can set up the chart legend. For an automatic legend, provide an object with `source`, `name`, and `interval` as shown below:

```json
metadata: [
    {
        type: 'candlestick',
        legend: [{
            'label': {
                source: "Binance",
                name: "BTCUSDT",
                interval: '5m'
            }
        }],
    ...
    }
]
```

You can also define custom legends like this:

```json
legend: [{
    'icon': svgImage,
    'label': `EMA length=50`,
    'color': '#e60049',
}],
```
