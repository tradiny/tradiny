/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

import { DataProvider } from "./dataprovider.js";
import { Utils } from "./utils.js";

export class OperationsHandler {
  // ChartOperations
  constructor(chart) {
    this.chart = chart;
  }

  refresh(i) {
    const dataKeys = [];
    for (let j = 0; j < this.chart.panes[i].metadata.length; j++) {
      if (!this.chart.dataCache[i]) {
        this.chart.dataCache[i] = {};
      }
      for (
        let k = 0;
        k < this.chart.panes[i].metadata[j].dataKeys.length;
        k++
      ) {
        const dataKey = this.chart.panes[i].metadata[j].dataKeys[k].dataKey;
        dataKeys.push(dataKey);
        this.chart.dataCache[i][dataKey] = undefined;
      }
    }
    this.chart.cacheHandler.buildCaches(dataKeys);

    this.chart.DOMHandler.initializeChartDOMEls(i);
    this.chart.DOMHandler.gridPositionsUpdated();

    this.chart.axisHandler.configureYAxes(i);
    this.chart.dataHandler.configureSeries(i);
    this.chart.DOMHandler.createChart(i);

    this.chart.DOMHandler.gridSizesUpdated();
    this.chart.DOMHandler.gridUpdated();

    this.chart.renderHandler.render();
    this.chart.interactionHandler.setupInteractions(i);
  }

  addData(data, i, axesMap, scalesMap, colorMap) {
    const source = data.details.source;
    const name = data.details.name;
    const interval = this.chart.dataProvider.interval;

    const isReady =
      !this.chart.panes || (this.chart.panes && this.chart.panes.length === 0)
        ? false
        : true;

    if (!this.chart.panes || i === this.chart.panes.length) {
      // new pane

      if (!this.chart.panes) {
        this.chart.panes = [];
      }

      let pane;

      switch (data.details.type) {
        case "line":
          const color = colorMap["color"];

          const axisKey = Object.keys(axesMap)[0]; // it is only one, because it is one line
          let axis = axesMap[axisKey];
          let scale = scalesMap[axisKey];

          pane = {
            name: `Pane${i + 1}`,
            height: 3,
            yAxes: [
              {
                type: scale,
                key: `${source}-${name}-${interval}`,
                orient: axis === "New right axis" ? "right" : "left",
                dynamic: true,
                color: color,
              },
            ],
            metadata: [
              {
                type: data.details.type,
                legend: [
                  {
                    icon: this.chart.DOMHandler.getIcon("line"),
                    label: { source, name, interval },
                    color: color,
                  },
                ],
                dataKeys: [
                  {
                    dataKey: `${source}-${name}-${interval}`,
                    key: name,
                    yAxis:
                      axis === "New right axis" || axis === "New left axis"
                        ? `${source}-${name}-${interval}`
                        : axis,
                  },
                ],
                color: color,
              },
            ],
          };
          this.chart.panes.push(pane);

          this.chart.dataProvider.addData(
            {
              type: "data",
              source,
              name,
              interval,
            },
            () => {
              if (isReady) {
                this.refresh(i);
              }
            },
          );

          break;

        case "candlestick":
          pane = {
            name: `Pane${i + 1}`,
            height: 3,
            yAxes: [],
            metadata: [],
          };
          if (axesMap.price !== "Disable") {
            pane.yAxes.push({
              type: scalesMap.price,
              key: `${source}-${name}-${interval}-price`,
              orient: axesMap.price === "New right axis" ? "right" : "left",
              dynamic: true,
              height: axesMap.volume !== "Disable" ? 80 : 100,
              position: "top",
            });
            pane.metadata.push({
              type: data.details.type,
              legend: [
                {
                  icon: this.chart.DOMHandler.getIcon("candle"),
                  label: { source, name, interval },
                },
              ],
              dataKeys: [
                {
                  dataKey: `${source}-${name}-${interval}-open`,
                  key: "open",
                  yAxis: `${source}-${name}-${interval}-price`,
                },
                {
                  dataKey: `${source}-${name}-${interval}-high`,
                  key: "high",
                  yAxis: `${source}-${name}-${interval}-price`,
                },
                {
                  dataKey: `${source}-${name}-${interval}-low`,
                  key: "low",
                  yAxis: `${source}-${name}-${interval}-price`,
                },
                {
                  dataKey: `${source}-${name}-${interval}-close`,
                  key: "close",
                  yAxis: `${source}-${name}-${interval}-price`,
                  label: true,
                  labelBg: {
                    bullish: colorMap["bullish-candle"],
                    bearish: colorMap["bearish-candle"],
                    open: `${source}-${name}-${this.chart.dataProvider.interval}-open`,
                    close: `${source}-${name}-${this.chart.dataProvider.interval}-close`,
                  },
                  labelColor: { color: "#000000" },
                },
              ],
              spacingFactor: 0.2,
              color: {
                bullish: colorMap["bullish-candle"],
                bearish: colorMap["bearish-candle"],
                open: `${source}-${name}-${this.chart.dataProvider.interval}-open`,
                close: `${source}-${name}-${this.chart.dataProvider.interval}-close`,
              },
            });
          }
          if (axesMap.volume !== "Disable") {
            pane.yAxes.push({
              type: scalesMap.volume,
              key: `${source}-${name}-${interval}-volume`,
              orient: axesMap.volume === "New right axis" ? "right" : "left",
              dynamic: true,
              height: axesMap.price !== "Disable" ? 15 : 100,
              position: "bottom",
              tickFormat: "si",
            });
            pane.metadata.push({
              type: "bar",
              dataKeys: [
                {
                  dataKey: `${source}-${name}-${interval}-volume`,
                  yAxis: `${source}-${name}-${interval}-volume`,
                },
              ],
              spacingFactor: 0.2,
              color: {
                bullish: colorMap["bullish-candle"],
                bearish: colorMap["bearish-candle"],
                open: `${source}-${name}-${this.chart.dataProvider.interval}-open`,
                close: `${source}-${name}-${this.chart.dataProvider.interval}-close`,
              },
            });
          }

          this.chart.panes.push(pane);

          this.chart.dataProvider.addData(
            {
              type: "data",
              source,
              name,
              interval,
            },
            () => {
              if (isReady) {
                this.refresh(i);
              }
            },
          );

          break;
      }
    } else if (this.chart.panes && i < this.chart.panes.length) {
      // insert into an existing pane

      const pane = this.chart.panes[i];

      switch (data.details.type) {
        case "line":
          // remove pane and Y axis DOM elements, they will be recreated in refresh()
          this.chart.d3ChartEls[i].remove();
          for (let j = 0; j < pane.yAxes.length; j++) {
            const yAxis = pane.yAxes[j];
            this.chart.yAxesSvg[i][yAxis.key].remove();
          }

          const color = colorMap["color"];

          const axisKey = Object.keys(axesMap)[0]; // it is only one, because it is one line
          let axis = axesMap[axisKey];

          if (axis === "New right axis" || axis === "New left axis") {
            pane.yAxes.push({
              type: "linear",
              key: `${source}-${name}-${interval}`,
              orient: axis === "New right axis" ? "right" : "left",
              dynamic: true,
              color: color,
            });
            axis = `${source}-${name}-${interval}`;
          }

          pane.metadata.push({
            type: data.details.type,
            legend: [
              {
                icon: this.chart.DOMHandler.getIcon("line"),
                label: { source, name, interval },
                color: color,
              },
            ],
            dataKeys: [
              {
                dataKey: `${source}-${name}-${interval}`,
                key: name,
                yAxis: axis,
              },
            ],
            color: color,
          });

          this.chart.dataProvider.addData(
            {
              type: "data",
              source,
              name,
              interval,
            },
            () => {
              if (isReady) {
                this.refresh(i);
              }
            },
          );

          break;

        case "candlestick":
          // remove pane and Y axis DOM elements, they will be recreated in refresh()

          this.chart.d3ChartEls[i].remove();
          for (let j = 0; j < pane.yAxes.length; j++) {
            const yAxis = pane.yAxes[j];
            this.chart.yAxesSvg[i][yAxis.key].remove();
          }

          let priceAxis = axesMap.price,
            volumeAxis = axesMap.volume;
          if (
            axesMap.price === "New right axis" ||
            axesMap.price === "New left axis"
          ) {
            pane.yAxes.push({
              type: "linear",
              key: `${source}-${name}-${interval}-price`,
              orient: axesMap.price === "New right axis" ? "right" : "left",
              dynamic: true,
              height: axesMap.volume !== "Disable" ? 80 : 100,
              position: "top",
            });
            priceAxis = `${source}-${name}-${interval}-price`;
          }
          if (
            axesMap.volume === "New right axis" ||
            axesMap.volume === "New left axis"
          ) {
            pane.yAxes.push({
              type: "linear",
              key: `${source}-${name}-${interval}-volume`,
              orient: axesMap.volume === "New right axis" ? "right" : "left",
              dynamic: true,
              height: axesMap.price !== "Disable" ? 15 : 100,
              position: "bottom",
              tickFormat: "si",
            });
            volumeAxis = `${source}-${name}-${interval}-volume`;
          }

          if (axesMap.price !== "Disable") {
            pane.metadata.push({
              type: data.details.type,
              legend: [
                {
                  icon: this.chart.DOMHandler.getIcon("candle"),
                  label: { source, name, interval },
                },
              ],
              dataKeys: [
                {
                  dataKey: `${source}-${name}-${interval}-open`,
                  key: "open",
                  yAxis: priceAxis,
                },
                {
                  dataKey: `${source}-${name}-${interval}-high`,
                  key: "high",
                  yAxis: priceAxis,
                },
                {
                  dataKey: `${source}-${name}-${interval}-low`,
                  key: "low",
                  yAxis: priceAxis,
                },
                {
                  dataKey: `${source}-${name}-${interval}-close`,
                  key: "close",
                  yAxis: priceAxis,
                  label: true,
                  labelBg: {
                    bullish: colorMap["bullish-candle"],
                    bearish: colorMap["bearish-candle"],
                    open: `${source}-${name}-${this.chart.dataProvider.interval}-open`,
                    close: `${source}-${name}-${this.chart.dataProvider.interval}-close`,
                  },
                  labelColor: "#000000",
                },
              ],
              spacingFactor: 0.2,
              color: {
                bullish: colorMap["bullish-candle"],
                bearish: colorMap["bearish-candle"],
                open: `${source}-${name}-${this.chart.dataProvider.interval}-open`,
                close: `${source}-${name}-${this.chart.dataProvider.interval}-close`,
              },
            });
          }
          if (axesMap.volume !== "Disable") {
            pane.metadata.push({
              type: "bar",
              dataKeys: [
                {
                  dataKey: `${source}-${name}-${interval}-volume`,
                  yAxis: volumeAxis,
                },
              ],
              spacingFactor: 0.2,
              color: {
                bullish: colorMap["bullish-candle"],
                bearish: colorMap["bearish-candle"],
                open: `${source}-${name}-${this.chart.dataProvider.interval}-open`,
                close: `${source}-${name}-${this.chart.dataProvider.interval}-close`,
              },
            });
          }

          this.chart.dataProvider.addData(
            {
              type: "data",
              source,
              name,
              interval,
            },
            () => {
              if (isReady) {
                this.refresh(i);
              }
            },
          );
          break;
      }
    }
  }

  addIndicator(indicator, i, inputs, axesMap, scalesMap, dataMap, colorMap) {
    const inputId = Object.entries(inputs)
      .map(([key, value]) => `${key}-${value}`)
      .join("_");
    const dataId = Object.entries(dataMap)
      .map(([key, value]) => `${key}-${value.value}`)
      .join("_");
    const indicatorId = `${indicator.id.replace(/\./g, "-")}_${inputId}_${dataId}`;

    const settings = {
      type: "indicator",
      id: indicatorId,
      indicator,
      inputs,
      dataMap,
      render: {
        indicatorId: indicatorId,
        indicator: indicator,
        inputs: inputs,
        paneIdx: i,
        axesMap: axesMap,
        scalesMap: scalesMap,
        colorMap: colorMap,
      },
    };
    console.log(
      "You can copy the indicator settings (you may want to add `count`)",
      JSON.stringify(settings),
    );

    this.onIndicatorData(settings.render);
    this.chart.dataProvider.addIndicator(settings, () => {
      this.refresh(i);
    });
  }

  onIndicatorData(options) {
    const indicatorId = options.indicatorId;
    const indicator = options.indicator;
    const inputs = options.inputs;
    const inputText = Object.entries(inputs)
      .map(([key, value]) => `${key}=${value}`)
      .join(", ");
    const i = options.paneIdx;
    const axesMap = options.axesMap;
    const scalesMap = options.scalesMap;
    const colorMap = options.colorMap;

    const removeActions = []; // actions to perform to remove this indicator

    let pane;
    if (!this.chart.panes || i === this.chart.panes.length) {
      // new pane

      if (!this.chart.panes) {
        this.chart.panes = [];
      }

      pane = {
        name: `Pane${i + 1}`,
        height: 3,
        yAxes: [],
        metadata: [],
      };

      const removePane = (i) => () => {
        this._removePane(i);
      };
      removeActions.push(removePane(i));
    }
    if (this.chart.panes && i < this.chart.panes.length) {
      // insert into an existing pane

      pane = this.chart.panes[i];

      // remove pane and Y axis DOM elements, they will be recreated in refresh()
      this.chart.d3ChartEls[i].remove();
      for (let j = 0; j < pane.yAxes.length; j++) {
        const yAxis = pane.yAxes[j];
        this.chart.yAxesSvg[i][yAxis.key].remove();
      }

      const removeEls = (i) => () => {
        this.chart.d3ChartEls[i].remove();
        for (let j = 0; j < pane.yAxes.length; j++) {
          const yAxis = pane.yAxes[j];
          this.chart.yAxesSvg[i][yAxis.key].remove();
        }
      };
      removeActions.push(removeEls(i));
    }

    for (let j = 0; j < indicator.details.outputs.length; j++) {
      const dataKey = indicator.details.outputs[j].name;
      const axisKey = indicator.details.outputs[j].y_axis;
      const axis = axesMap[axisKey];

      const color = colorMap[dataKey];

      if (axis === "New right axis" || axis === "New left axis") {
        const scale = scalesMap[axisKey];
        const existingAxis = pane.yAxes.find((axis) => axis.key === axisKey);
        if (!existingAxis) {
          const a = {
            type: scale,
            key: axisKey,
            orient: axis === "New right axis" ? "right" : "left",
            dynamic: true,
            color: color,
          };
          pane.yAxes.push(a);

          if (this.chart.panes && i < this.chart.panes.length) {
            const rmAxis = (i, a) => () => {
              const idx = this.chart.panes[i].yAxes.indexOf(a);
              this.chart.panes[i].yAxes.splice(idx, 1);
            };
            removeActions.push(rmAxis(i, a));
          }
        }
      }

      if (axis !== "Disable") {
        const m = {
          type: "line",
          legend: [
            {
              icon: this.chart.DOMHandler.getIcon("line"),
              label: `${indicator.details.categories[0]} / ${indicator.name} ${dataKey} ${inputText}`,
              color: color,
            },
          ],
          dataKeys: [
            {
              dataKey: `${indicatorId}-${dataKey}`,
              key: axisKey,
              yAxis:
                axis === "New right axis" || axis === "New left axis"
                  ? axisKey
                  : axis,
            },
          ],
          color: color,
        };
        pane.metadata.push(m);

        if (this.chart.panes && i < this.chart.panes.length) {
          const rmMetadata = (i, m) => () => {
            const idx = this.chart.panes[i].metadata.indexOf(m);
            this.chart.panes[i].metadata.splice(idx, 1);
          };
          removeActions.push(rmMetadata(i, m));
        }
      }
    }
    if (this.chart.panes && i < this.chart.panes.length) {
      const doRefresh = (i) => () => {
        this.refresh(i);
      };
      removeActions.push(doRefresh(i));
    }

    if (!this.chart.panes || i === this.chart.panes.length) {
      // new pane
      this.chart.panes.push(pane);
    }

    this.chart.history.push({
      remove: () => {
        for (let j = 0; j < removeActions.length; j++) {
          removeActions[j]();
        }
      },
    });
  }

  destroyChart() {
    console.log(
      `called destroy for id ${this.chart.id} at ${this.chart.options.gridPosition}`,
    );

    this.chart.dataProvider.ws.websocket.close();
    this.chart.interactionHandler.disableAllInteractions();
    this.chart.dataProvider.disableEvents();

    for (let i = 0; i < this.chart.panes.length; i++) {
      this._removePane(0, false);
    }

    if (this.chart.d3ContainerEl) {
      this.chart.d3ContainerEl.selectAll("*").remove();
    }
  }

  removePane(i) {
    if (this.chart.panes.length === 1) {
      return alert("Cannot remove");
    }

    this._removePane(i);
  }

  _removePane(i, update = true) {
    // this.chart.interactionHandler.disableAllInteractions();
    // this.chart.dataProvider.disableEvents();

    this.chart.DOMHandler.removeDOMEls(i);

    // remove all metadata about the chart
    if (this.chart.panes) {
      this.chart.panes.splice(i, 1);
    }
    if (this.chart.paneHeights) {
      this.chart.paneHeights.splice(i, 1);
    }
    if (this.chart.d3ChartEls) {
      this.chart.d3ChartEls.splice(i, 1);
    }
    if (this.chart.fcCharts) {
      this.chart.fcCharts.splice(i, 1);
    }
    if (this.chart.firstAxisKey) {
      this.chart.firstAxisKey.splice(i, 1);
    }
    if (this.chart.yAxes) {
      this.chart.yAxes.splice(i, 1);
    }
    if (this.chart.yAxesSvg) {
      this.chart.yAxesSvg.splice(i, 1);
    }
    if (this.chart.webglMultiSeries) {
      this.chart.webglMultiSeries.splice(i, 1);
    }
    if (this.chart.svgMultiSeries) {
      this.chart.svgMultiSeries.splice(i, 1);
    }
    if (this.chart.gridlines) {
      this.chart.gridlines.splice(i, 1);
    }
    if (this.chart.crosshairs) {
      this.chart.crosshairs.splice(i, 1);
    }
    if (this.chart.pointers) {
      this.chart.pointers.splice(i, 1);
    }
    if (this.chart.dataCache) {
      this.chart.dataCache.splice(i, 1);
    }
    if (this.chart.drawingData) {
      this.chart.drawingData.splice(i, 1);
    }
    if (this.chart.drawingCanvases) {
      this.chart.drawingCanvases.splice(i, 1);
    }

    // rerender the chart
    if (update) {
      try {
        if (this.chart.d3ContainerEl && this.chart.d3ChartEls) {
          this.chart.DOMHandler.gridPositionsUpdated();
          this.chart.DOMHandler.gridSizesUpdated();
          this.chart.DOMHandler.gridUpdated();
          this.chart.renderHandler.render();
        }
      } catch (error) {
        console.error("An error occurred while updating the chart:", error);
      }
    }

    // setup new interactions after disabling
    // this.chart.dataProvider.enableEvents();
    // this.chart.interactionHandler.setupAllInteractions();
  }

  onIntervalChange(oldInterval, newInterval) {
    if (oldInterval === newInterval) {
      return;
    }

    this.chart.dataProvider.ws.websocket.close();
    this.chart.interactionHandler.disableAllInteractions();
    this.chart.dataProvider.disableEvents();

    const gridHandlerBackup = this.chart.options.gridHandler;
    delete this.chart.options.gridHandler;

    // preserve options
    let newOptions = Utils.deepCopy(this.chart.options);
    newOptions = Utils.replaceInObject(newOptions, oldInterval, newInterval);

    // preserve ID
    const id = Utils.deepCopy(this.chart.id);
    newOptions.id = id;

    // preserve panes
    let newPanes = Utils.replaceInObject(
      Utils.deepCopy(this.chart.panes),
      oldInterval,
      newInterval,
    );
    newOptions.panes = newPanes;
    newOptions.indicatorMetadataAlreadyAdded = true;

    // preserve dataProvider
    const newDataProviderConfig = Utils.replaceInObject(
      Utils.deepCopy(this.chart.dataProvider.config),
      oldInterval,
      newInterval,
    );

    const drawingData = this.chart.saveHandler.serializeDrawing(
      this.chart.drawingData,
    );

    // remove all panes
    for (let i = 0; i < this.chart.panes.length; i++) {
      this._removePane(0, false);
    }

    // wipe all other elements if any
    if (this.chart.d3ContainerEl) {
      this.chart.d3ContainerEl.selectAll("*").remove();
    }

    newOptions.gridHandler = gridHandlerBackup;
    newOptions.dataProvider = newDataProviderConfig;

    // recreate
    this.chart.initialize(newOptions, () => {
      this.chart.drawingData =
        this.chart.saveHandler.unserializeDrawing(drawingData);
    });
  }
}
