/*
 * This software is licensed under a dual-license model:
 * 1. Under the Affero General Public License (AGPL) for open-source use.
 * 2. With additional terms tailored to individual users (e.g., traders and investors):
 *
 *    - Individual users may use this software for personal profit (e.g., trading/investing)
 *      without releasing proprietary strategies.
 *
 *    - Redistribution, public tools, or commercial use require compliance with AGPL
 *      or a commercial license. Contact: license@tradiny.com
 *
 * For full details, see the LICENSE.md file in the root directory of this project.
 */

import { Renderer } from "../renderer.js";

import { Utils } from "./utils.js";
import { GridHandler } from "./grid.js";
import { DataProvider } from "./dataprovider.js";
import { AxisHandler } from "./axis.js";
import { CacheHandler } from "./cache.js";
import { DataHandler } from "./data.js";
import { DOMHandler } from "./dom.js";
import { InteractionHandler } from "./interaction.js";
import { OperationsHandler } from "./operations.js";
import { DrawingHandler } from "./drawing.js";
import { RenderHandler } from "./render.js";
import { SaveHandler } from "./save.js";
import { ImageHandler } from "./image.js";

export default class TradinyChart {
  static DataProvider = DataProvider;
  static Utils = Utils;
  static ThemeKey = "TradinyTheme";
  afterCreatedEvents = [];
  alreadyCreated = false;

  static initialize(options) {
    const gridHandler = new GridHandler(options);
    gridHandler.createGrid();
    gridHandler.initializeCharts();
    return gridHandler;
  }

  constructor() {
    this.saveHandler = new SaveHandler(this); // for loading

    this._onRendered = [];
    this._rendered = false;
  }

  async initialize(options, afterCreated) {
    this.gridHandler = options.gridHandler || new GridHandler(this);
    this.dataProvider = new DataProvider(this, options.dataProvider);
    this.dataHandler = new DataHandler(this); // please, do not store any state in handlers
    this.cacheHandler = new CacheHandler(this);
    this.DOMHandler = new DOMHandler(this);
    this.axisHandler = new AxisHandler(this);
    this.renderHandler = new RenderHandler(this);
    this.interactionHandler = new InteractionHandler(this);
    this.operationsHandler = new OperationsHandler(this);
    this.drawingHandler = new DrawingHandler(this);
    this.imageHandler = new ImageHandler(this);

    if (afterCreated) {
      this.afterCreatedEvents.push(afterCreated);
    }

    this.R = this.renderHandler.R; // shortcut

    this.initializeProperties(options);

    const theme = localStorage.getItem(TradinyChart.ThemeKey);
    this.DOMHandler.controls.setTheme(
      this.gridHandler.options.theme || options.theme || theme || "dark",
    );

    this.dataProvider.onReady(async () => {
      this.cacheHandler.buildCaches();
      this.DOMHandler.initializeDOMElements();

      this.axisHandler.configureXAxis(options);

      for (let i = 0; i < this.panes.length; i++) {
        this.axisHandler.configureYAxes(i);
        this.dataHandler.configureSeries(i);
        this.DOMHandler.createChart(i);
      }

      for (let i = 0; i < this.afterCreatedEvents.length; i++) {
        this.afterCreatedEvents[i]();
      }
      this.alreadyCreated = true;

      this.DOMHandler.gridUpdated();

      this.renderHandler.render();
      this.interactionHandler.setupAllInteractions();

      this.dataProvider.onUpdated(
        this.dataHandler.onData.bind(this.dataHandler),
      );
    });

    await this.parseArgs();

    // attach events to add indicators, initial loading
    if (options.dataProvider.config) {
      for (let i = 0; i < options.dataProvider.config.data.length; i++) {
        const data = options.dataProvider.config.data[i];
        if (["indicator"].includes(data.type)) {
          let onIndicatorData;
          if (!options.indicatorMetadataAlreadyAdded) {
            onIndicatorData = (render) => () =>
              this.operationsHandler.onIndicatorData(render);
          } else {
            onIndicatorData = (_) => () => {
              this.renderHandler.render();
            };
          }
          options.dataProvider._onIndicatorData[data.id] = onIndicatorData(
            data.render,
          );
        }
      }
    }

    requestAnimationFrame(() => {
      console.log("rendered");
      this.rendered();
    });
  }
  extractIndicators(searchParams) {
    const indicators = [];
    let index = 1;
    let indicator;

    while ((indicator = searchParams.get(`indicator${index}`))) {
      const params = {};
      const indicatorPrefix = `indicator${index}-`; // Prefix for the current indicator

      searchParams.forEach((value, key) => {
        // Match params for the current indicator with the specific index
        if (key.startsWith(indicatorPrefix)) {
          const paramName = key.substring(indicatorPrefix.length); // Extract the parameter name after the prefix
          params[paramName] = value;
        }
      });

      indicators.push({
        name: indicator,
        params: params,
      });

      index++;
    }

    return indicators;
  }

  async searchData(symbol) {
    return new Promise((resolve, reject) => {
      this.dataProvider.searchData(symbol, (data) => {
        for (let i = 0; i < data.length; i++) {
          if (data[i].name === symbol) {
            resolve(data[i]);
          }
        }
      });
    });
  }
  async searchIndicators(name) {
    return new Promise((resolve, reject) => {
      this.dataProvider.searchIndicators(name, (data) => {
        resolve(data[0]);
      });
    });
  }
  addData(data) {
    return new Promise((resolve, reject) => {
      this.DOMHandler.controls.defaultAddData(data, () => {
        resolve();
      });
    });
  }
  addIndicator(indicator, indicator_params) {
    return new Promise((resolve, reject) => {
      this.DOMHandler.controls.defaultAddIndicator(
        indicator,
        indicator_params,
        () => {
          resolve();
        },
      );
    });
  }
  onConnect() {
    return new Promise((resolve, reject) => {
      this.dataProvider.onConnect(resolve);
    });
  }

  async parseArgs() {
    if (
      !this.options.dataProvider.data ||
      this.options.dataProvider.data.length === 0
    ) {
      const currentUrl = window.location.href;
      const urlObj = new URL(currentUrl);
      const searchParams = new URLSearchParams(urlObj.search);
      const symbol = searchParams.get("s");
      const interval = searchParams.get("i");
      const count = searchParams.get("c");
      const indicators = this.extractIndicators(searchParams);

      if (symbol && interval) {
        this.dataProvider.interval = interval;
        await this.onConnect();

        const data = await this.searchData(symbol);
        if (count) {
          data.count = count;
        }
        await this.addData(data);

        for (let i = 0; i < indicators.length; i++) {
          const indicator_name = indicators[i].name;
          const indicator_params = indicators[i].params;
          const indicator = await this.searchIndicators(indicator_name);

          await this.addIndicator(indicator, indicator_params);
        }
      } else {
        const tabs = ["charts", "data"];
        if (this.options.gridPosition === "1x1") {
          tabs.unshift("grids");
        }
        this.DOMHandler.controls.addWindow(tabs, true);
      }
    }
  }

  initializeProperties(options) {
    if (options.id) {
      this.id = options.id;
    } else {
      let count = 1;
      while (window[`Tradiny${count}`] !== undefined) {
        count++;
      }
      this.id = `Tradiny${count}`;
    }
    window[this.id] = this; // save reference to window object to be able to access it from templates

    this.options = options;
    this.metadata = options.metadata;
    this.elementId = options.elementId;
    this.panes = options.panes;
    this.initialZoom = options.initialZoom;
    this.paddingPixels = options.paddingPixels || 10;
    this.dynamicYAxis = options.dynamicYAxis || true;
    this.visiblePoints = options.visiblePoints || 300;
    this.pointSpacingFactor = options.pointSpacingFactor || 0.2;
    let calculatedSize = "large";
    if (window.innerWidth < 844) {
      calculatedSize = "small";
    }
    this.size =
      this.gridHandler.options.size || this.options.size || calculatedSize;
    if (this.options.size === "small") {
      this.widthControls = 34;
      this.xAxisHeight = 35;
      this.fontSize = 14;
    } else {
      this.widthControls = 27;
      this.xAxisHeight = 25;
      this.fontSize = 12;
    }
    this.features = options.features || [
      "grid",
      "interval",
      "add",
      "drawing",
      "back",
      "text",
      "line",
      "horizontal-line",
      "vertical-line",
      "brush",
      "ruler",
      "fib",
      "save",
      "load",
      "prompt",
    ];
    if (this.features.length === 0) {
      this.widthControls = 0;
    }
    this.defaultBullishCandleColor = "#8be04e";
    this.defaultBearishCandleColor = "#ea5545";
    this.textHeight = Utils.getTextHeight("0", `${this.fontSize}px sans-serif`);
    this.resizing = false;
    this.renderer = new Renderer(this);
    this.yAxisPadding = 10;

    this.history = [];

    // per chart:
    this.d3ChartEls = [];
    this.domChartEls = [];

    this.fcCharts = []; // fc.chartCartesian
    this.d3ChartSvgEls = [];

    this.firstAxisKey = [];
    this.yAxes = [];
    this.yAxesSvg = [];

    this.webglMultiSeries = [];
    this.svgMultiSeries = [];

    this.gridlines = []; // fc.annotationSvgGridline
    this.crosshairs = []; //fc.annotationSvgCrosshair()
    this.pointers = []; // fc.pointer
    this.mousePosition = []; // {i, position}
    this.delimiterEls = [];

    this.drawingData = [];
    this.drawingCanvases = [];
    this.drawingDrags = [];
  }

  afterCreated(cb) {
    if (this.alreadyCreated) {
      cb();
    } else {
      this.afterCreatedEvents.push(cb);
    }
  }

  back() {
    if (this.history.length) {
      const h = this.history.pop();
      h.remove();
    }
  }

  select(selector) {
    return d3.select("#" + this.elementId).select(selector);
  }

  async downloadImage() {
    return await this.imageHandler.downloadImage(this.elementId, "data", {
      scale: 3,
      format: "png",
      quality: 1,
    });
  }

  async toImage() {
    return await this.imageHandler.getImage(this.elementId, {
      scale: 3,
      format: "png",
      quality: 1,
    });
  }

  async describe() {
    function numberToOrdinal(n) {
      if (typeof n !== "number" || isNaN(n)) return `${n}`;

      const suffixes = ["th", "st", "nd", "rd"];
      const remainder = n % 100;

      return (
        n +
        (suffixes[(remainder - 20) % 10] || suffixes[remainder] || suffixes[0])
      );
    }

    let desc = `The chart is on a ${this.dataProvider.interval} interval.\n`;

    for (let i = 0; i < this.panes.length; i++) {
      if (i === 0 && this.panes.length > 1) {
        desc = `The chart has ${this.panes.length} panes.\n\n`;
      }

      if (this.panes.length > 1) {
        desc += `${numberToOrdinal(i + 1)} pane contains: \n `;
      }

      const pane = this.panes[i];
      for (let j = 0; j < pane.metadata.length; j++) {
        const metadata = pane.metadata[j];
        if (!metadata.legend) {
          continue;
        }

        switch (metadata.type) {
          case "candlestick":
            for (let k = 0; k < metadata.legend.length; k++) {
              const l = metadata.legend[k];
              desc += `  - Candlestick chart ${this.DOMHandler.toLabelText(l.label)}.\n`;
            }
            break;
          case "line":
            for (let k = 0; k < metadata.legend.length; k++) {
              const l = metadata.legend[k];
              desc += `  - Line ${this.DOMHandler.toLabelText(l.label)}, color ${l.color}.\n`;
            }
            break;
          case "bar":
            for (let k = 0; k < metadata.legend.length; k++) {
              const l = metadata.legend[k];
              desc += `  - Line ${this.DOMHandler.toLabelText(l.label)}, color ${l.color}.\n`;
            }
            break;
        }
      }

      for (let j = 0; j < pane.yAxes.length; j++) {
        const ax = pane.yAxes[j];
        const axKey = ax.key.split("-").pop();
        desc += `  - The ${axKey} axis is on the ${ax.orient} side.\n`;
      }
      desc += `\n`;
    }

    return desc;
  }

  onRendered(cb) {
    this._onRendered.push(cb);
    if (this._rendered) {
      cb();
    }
  }

  rendered() {
    this._rendered = true;
    for (let i = 0; i < this._onRendered.length; i++) {
      this._onRendered[i]();
    }
  }
}
