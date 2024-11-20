/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

import { Renderer } from "../renderer.js";
import { PopupWindow } from "../window.js";
import { Utils } from "./utils.js";

import { DataProvider } from "./dataprovider.js";
import { GridHandler } from "./grid.js";

export class SaveHandler {
  static chartsKey = "MyCharts";
  static gridsKey = "MyGrids";
  static mostAddedKey = "MyMostAdded";
  constructor(chart) {
    this.chart = chart;
  }

  windowSave() {
    new Renderer().render("save", { self: this, title: "Save" }, (content) => {
      this._win = new PopupWindow(this.chart.elementId, 400);
      this._win.render(content);
      this.chart.d3ContainerEl.select("input.save-chart").node().focus();
    });
  }

  getGrids() {
    const grids = localStorage.getItem(SaveHandler.gridsKey);
    if (!grids) {
      return {};
    } else {
      return JSON.parse(grids);
    }
  }

  getCharts() {
    const charts = localStorage.getItem(SaveHandler.chartsKey);
    if (!charts) {
      return {};
    } else {
      return JSON.parse(charts);
    }
  }

  loadChart(id) {
    this.chart.DOMHandler._win.closePopup();
    const charts = JSON.parse(localStorage.getItem(SaveHandler.chartsKey));
    const chart = charts[id];

    if (this.chart.panes) {
      this.chart.dataProvider.ws.websocket.close();
      this.chart.interactionHandler.disableAllInteractions();
      this.chart.dataProvider.disableEvents();

      // remove all panes
      for (let i = 0; i < this.chart.panes.length; i++) {
        this.chart.operationsHandler._removePane(0, false);
      }

      // wipe all other elements
      if (this.chart.d3ContainerEl) {
        this.chart.d3ContainerEl.selectAll("*").remove();
      }
    }

    this._loadChart(
      chart,
      this.chart.elementId,
      this.chart.gridPosition,
      this.chart.gridHandler,
      () => {},
    );
  }

  _loadChart(chart, elementId, gridPosition, gridHandler, onDone) {
    chart.options.dataProvider = chart.dataProviderConfig;

    if (elementId) {
      chart.options.elementId = elementId;
    }
    if (gridPosition) {
      chart.options.gridPosition = gridPosition;
    }
    if (gridHandler) {
      chart.options.gridHandler = gridHandler;
    }

    console.log("new chart config", chart);

    // recreate
    this.chart.initialize(chart.options, () => {
      if (chart.drawingData) {
        this.chart.drawingData = this.unserializeDrawing(chart.drawingData);
        this.chart.drawingHandler.setMaxId();
      }

      onDone();
    });
  }
  removeGrid(id, event) {
    if (confirm(`Are you sure you want to remove grid #${id}?`)) {
      let grids = JSON.parse(localStorage.getItem(SaveHandler.gridsKey));
      delete grids[id];
      localStorage.setItem(SaveHandler.gridsKey, JSON.stringify(grids));

      const parentElement = event.target.closest("tr");

      if (parentElement) {
        parentElement.remove();
      }
    }
  }

  removeChart(id, event) {
    if (confirm(`Are you sure you want to remove chart #${id}?`)) {
      let charts = JSON.parse(localStorage.getItem(SaveHandler.chartsKey));
      delete charts[id];
      localStorage.setItem(SaveHandler.chartsKey, JSON.stringify(charts));

      const parentElement = event.target.closest("tr");

      if (parentElement) {
        parentElement.remove();
      }
    }
  }

  saveChart() {
    const name = this.chart.d3ContainerEl
      .select("input.save-chart")
      .node().value;
    const id = `${this.chart.id}-${Utils.toAlphanumeric(name)}`;

    this._win.closePopup();

    const chartConfig = this._saveChart(id, name);

    if (!localStorage.getItem(SaveHandler.chartsKey)) {
      localStorage.setItem(SaveHandler.chartsKey, JSON.stringify({}));
    }
    let charts = JSON.parse(localStorage.getItem(SaveHandler.chartsKey));
    charts[id] = chartConfig;
    localStorage.setItem(SaveHandler.chartsKey, JSON.stringify(charts));
  }

  _saveChart(id, name) {
    this.chart.options.indicatorMetadataAlreadyAdded = true;
    this.chart.options.panes = this.chart.panes; // update options with panes

    for (let i = 0; i < this.chart.options.panes.length; i++) {
      this.chart.options.panes[i].height = this.chart.paneHeights[i]; // preserve heights
    }

    const options = Utils.deepCopy(this.chart.options);

    delete options.gridHandler;
    delete options.grid;
    delete options.gridPosition;
    delete options.elementId;

    const chartConfig = {
      id: id,
      name: name,
      options: options,
      dataProviderConfig: this.chart.dataProvider.config,
      drawingData: this.serializeDrawing(this.chart.drawingData),
    };

    return chartConfig;
  }

  loadGrid(id) {
    this.chart.DOMHandler._win.closePopup();

    this.chart.gridHandler.destroyGrid(true);

    const grids = JSON.parse(localStorage.getItem(SaveHandler.gridsKey));
    const gOpts = grids[id];

    const gridHandler = this.chart.gridHandler;
    // const gridHandler = new GridHandler(gOpts.options);
    gridHandler.options = gOpts.options;
    gridHandler.colWidths = gOpts.colWidths;
    gridHandler.rowHeights = gOpts.rowHeights;

    gridHandler.createGrid(true);

    let [row_len, col_len] = gridHandler.getGrid();
    for (let row = 1; row <= row_len; row++) {
      for (let col = 1; col <= col_len; col++) {
        const pos = `${row}x${col}`;

        const chart = new TradinyChart();

        const chartOptions = gOpts.chartConfigs[pos];

        chart.saveHandler._loadChart(
          chartOptions,
          gridHandler.getElementId(row, col),
          pos,
          gridHandler,
          () => {
            gridHandler.setChart(pos, chart); // set reference
          },
        );
      }
    }

    gridHandler.resize();
  }

  saveGrid() {
    const name = this.chart.d3ContainerEl
      .select("input.save-grid")
      .node().value;
    const id = `Trad-Grid${Math.random()
      .toString(16)
      .slice(2)}-${Utils.toAlphanumeric(name)}`;

    this._win.closePopup();

    const g = this.chart.gridHandler;

    let [row_len, col_len] = g.getGrid();
    const chartConfigs = {};
    for (let row = 1; row <= row_len; row++) {
      for (let col = 1; col <= col_len; col++) {
        const position = `${row}x${col}`;
        const chart = g.getChart(position);
        const chart_id = `${chart.id}`;
        const chart_name = `grid-${position}`;
        chartConfigs[position] = chart.saveHandler._saveChart(
          chart_id,
          chart_name,
        );
      }
    }

    const options = Utils.deepCopy(g.options);
    options.grid = `${row_len}x${col_len}`;

    const gridConfig = {
      id,
      name,
      grid: options.grid,
      options: options,
      colWidths: g.colWidths,
      rowHeights: g.rowHeights,
      chartConfigs,
    };

    if (!localStorage.getItem(SaveHandler.gridsKey)) {
      localStorage.setItem(SaveHandler.gridsKey, JSON.stringify({}));
    }
    let grids = JSON.parse(localStorage.getItem(SaveHandler.gridsKey));
    grids[id] = gridConfig;
    localStorage.setItem(SaveHandler.gridsKey, JSON.stringify(grids));
  }

  unserializeDrawing(drawingData) {
    const unserializedDrawing = JSON.parse(JSON.stringify(drawingData)); // deep copy
    if (unserializedDrawing) {
      for (let i = 0; i < unserializedDrawing.length; i++) {
        const ddata = unserializedDrawing[i];

        for (let j = 0; j < ddata.lines.length; j++) {
          const d = ddata.lines[j];

          const x = this.chart.xScale;
          const y = this.chart.yAxes[d.i][this.chart.firstAxisKey[d.i]].scale;

          d.points = Utils.unserializeRelativePoints(
            d.points,
            x,
            y,
            this.chart.dataProvider.data,
            this.chart.dataProvider.interval,
          );
          switch (d.type) {
            case "ruler":
              d.labels = this.chart.drawingHandler.rulerLabels(d.i, x, y);
              break;
            case "fib":
              d.labels = this.chart.drawingHandler.fibLabels(d.i, x, y);
              break;
            case "text":
              d.labels = this.chart.drawingHandler.textLabels(d.i, x, y);
              break;
            default:
              d.labels = [];
              break;
          }
        }
      }
    }
    return unserializedDrawing;
  }

  serializeDrawing(drawingData) {
    let serializedDrawing = [];
    if (drawingData) {
      for (let i = 0; i < drawingData.length; i++) {
        const ddata = drawingData[i];
        serializedDrawing[i] = { lines: [] };

        for (let j = 0; j < ddata.lines.length; j++) {
          const d = ddata.lines[j];

          const x = this.chart.xScale;
          const y = this.chart.yAxes[d.i][this.chart.firstAxisKey[d.i]].scale;

          const s = {
            type: d.type,
            i: d.i,
            id: d.id,
            points: Utils.serializeAbsolutePoints(
              d.points,
              x,
              y,
              this.chart.dataProvider.data,
              this.chart.dataProvider.interval,
            ),
            color: d.color,
            width: d.width,
            move: d.move,
            movePoints: d.movePoints,
          };

          const optional = ["fill", "opacity", "fib", "text", "size"];

          for (let k = 0; k < optional.length; k++) {
            const key = optional[k];
            const value = d[key];
            if (value) {
              s[key] = d[key];
            }
          }

          serializedDrawing[i].lines[j] = s;
        }
      }
      if (serializedDrawing.length === 0) {
        serializedDrawing = null;
      }
    }
    return serializedDrawing;
  }

  onAdd(type, id, data) {
    if (!localStorage.getItem(SaveHandler.mostAddedKey)) {
      localStorage.setItem(SaveHandler.mostAddedKey, JSON.stringify({}));
    }
    let mostAdded = JSON.parse(localStorage.getItem(SaveHandler.mostAddedKey));
    if (!mostAdded[type]) {
      mostAdded[type] = {};
    }
    if (!mostAdded[type][id]) {
      mostAdded[type][id] = { data, count: 0 };
    }
    mostAdded[type][id].count += 1;
    localStorage.setItem(SaveHandler.mostAddedKey, JSON.stringify(mostAdded));
  }

  getMostAdded(type) {
    let mostAdded = localStorage.getItem(SaveHandler.mostAddedKey);
    if (!mostAdded) {
      return [];
    }
    mostAdded = JSON.parse(mostAdded);
    if (!mostAdded[type]) {
      return [];
    }
    let items = mostAdded[type];
    const entries = Object.entries(items);
    const sortedEntries = entries.sort(([, a], [, b]) => b.count - a.count);
    const topEntries = sortedEntries.slice(0, 5);
    const topItems = Object.fromEntries(topEntries);
    return Object.values(topItems);
  }
}
