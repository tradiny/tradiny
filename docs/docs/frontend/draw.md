### Drawing on a Tradiny Chart

The `TradinyChart.initialize` function provides a `GridHandler` object. You can use this object to access a chart by calling the `getChart` method with a grid position, such as `'1x1'`.

Once you have the chart object, you can attach an `afterCreated` event to it. This event allows you to define and draw lines or other elements on the chart after it has been created.

```javascript
const chartGrid = TradinyChart.initialize(...);
const chart = chartGrid.getChart(); // gets the chart at grid position 1x1 by default
chart.afterCreated(() => {
    chart.drawingData = chart.saveHandler.unserializeDrawing([
        {
            "lines": [
                {
                    "type": "line",
                    "i": 0, // represents the pane ID, top-bottom
                    "id": 0, // ID of object
                    "points": [
                        [
                            "2024-10-13 17:04:29",
                            63629.51844578113
                        ],
                        [
                            "2024-10-14 02:45:09",
                            63944.328615839855
                        ]
                    ],
                    "color": "#e60049",
                    "width": 2,
                    "move": true, // is movable
                    "movePoints": false // points are movable
                },
            ]
        }
    ]);
    chart.drawingHandler.setMaxId(); // set next ID iterator
})
```

Notes:

1. You can define multiple points when drawing.
1. The variable `i` represents the pane index, starting from the top.
1. The options `move` and `movePoints` indicate whether the line or points can be moved.

## Draw Text

You can extend the `line` object by setting its `type` to `text`. This requires two additional parameters: `text`, which specifies the text to be displayed, and `size`, which defines the text size in pixels.

Note: Although this is a `line` object, the line itself is hidden by setting its opacity to `0.01`. This technique allows us to utilize the line's movable functionality.

```javascript
const chartGrid = TradinyChart.initialize(...);
const chart = chartGrid.getChart(); // gets the chart at grid position 1x1 by default
chart.afterCreated(() => {
    chart.drawingData = chart.saveHandler.unserializeDrawing([
        {
            "lines": [
                {
                    "type": "text",
                    "i": 0,
                    "id": 1,
                    "points": [
                        [
                            "2024-10-13 16:31:49",
                            63899.80404935314
                        ],
                        [
                            "2024-10-13 18:21:49",
                            63899.80404935314
                        ],
                        [
                            "2024-10-13 18:21:49",
                            63910.80404935314
                        ],
                        [
                            "2024-10-13 16:31:49",
                            63910.80404935314
                        ],
                        [
                            "2024-10-13 16:31:49",
                            63899.80404935314
                        ]
                    ],
                    "color": "#e60049",
                    "width": 10,
                    "move": true,
                    "movePoints": false,
                    "opacity": 0.01,
                    "text": "Test",
                    "size": 9
                }
            ]
        }
    ]);
    chart.drawingHandler.setMaxId(); // set next ID iterator
})
```
