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

import * as fc from "d3fc";

import { Utils } from "./utils.js";
import { DOMIconHandler } from "./dom/icon.js";
import { DOMControlsHandler } from "./dom/controls.js";

export class DOMHandler {
  constructor(chart) {
    this.chart = chart;

    this.icon = new DOMIconHandler(chart);
    this.controls = new DOMControlsHandler(this);
  }

  initializeDOMElements() {
    this.chart.d3ContainerEl = d3.select("#" + this.chart.elementId);
    this.chart.domContainerEl = this.chart.d3ContainerEl.node();
    this.chart.d3ChartEls = [];
    this.chart.domChartEls = [];

    const initHeights = this.getInitHeights();
    const grid = this.calculateTemplateGrid(initHeights);
    const yGridAxes = grid.yGridAxes;
    const templateColumns = grid.templateColumns;
    const templateRows = grid.templateRows;

    this.chart.d3ContainerEl
      .style("display", "grid")
      .style("position", "relative")
      .style("grid-template-columns", templateColumns)
      .style("grid-template-rows", templateRows);

    this.chart.controlsOuterEl = this.chart.d3ContainerEl
      .append("div")
      .attr("class", "controls");

    this.chart.controlsEl = this.chart.controlsOuterEl
      .append("div")
      .attr("class", "controls-inner");

    for (let i = 0; i < this.chart.panes.length; i++) {
      this.initializeChartDOMEls(i);
    }

    this.chart.settingsEl = this.chart.d3ContainerEl
      .append("div")
      .attr("class", "settings")
      .style("display", "flex")
      .style("justify-content", "center")
      .style("align-items", "center");

    this.chart.settingsEl
      .append("button")
      .attr("class", "settings-button")
      .style("display", "flex")
      .style("justify-content", "center")
      .style("align-items", "center")
      .style("height", "20px")
      .style("width", "20px")

      .style("margin", "0")
      .style("padding", "0")
      // .style('border', '0')
      .style("background", "none")
      .on("click", this.controls.settingsWindow.bind(this.controls))
      .html(this.icon.getIcon("settings"));

    if (this.chart.features.includes("grid")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon grid-icon")
        .on("click", this.controls.gridSelect.bind(this.controls))
        .html(this.icon.getIcon("grid"));
    }

    if (this.chart.features.includes("interval")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon interval-icon")
        .on("click", this.controls.intervalSelect.bind(this.controls))
        .html(this.chart.dataProvider.interval);
    }

    if (this.chart.features.includes("add")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon")
        .on("click", (event) => {
          this.controls.addWindow();
        })
        .html(this.icon.getIcon("add"));
    }

    if (this.chart.features.includes("alert")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon")
        .on("click", (event) => {
          this.controls.addAlert();
        })
        .html(this.icon.getIcon("alert"));
    }

    if (this.chart.features.includes("drawing")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon drawing-icon")
        .on("click", this.controls.drawSelect.bind(this.controls))
        .html(this.icon.getIcon("drawing"));
    }

    if (this.chart.features.includes("save")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon save-icon")
        .on("click", (event) => {
          this.chart.saveHandler.windowSave();
        })
        .html(this.icon.getIcon("save"));
    }
    if (this.chart.features.includes("prompt")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon prompt-icon")
        .on("click", async (event) => {
          await this.controls.promptWindow();
        })
        .html(this.icon.getIcon("prompt"));
    }

    this.gridPositionsUpdated();
  }

  initializeChartDOMEls(i) {
    const d3El = this.chart.d3ContainerEl.append("div").attr("class", "chart");
    const domEl = d3El.node();
    this.chart.d3ChartEls[i] = d3El;
    this.chart.domChartEls[i] = domEl;

    // delimiters
    if (i >= 1) {
      this.chart.delimiterEls[i - 1] = this.chart.d3ContainerEl
        .append("div")
        .attr("class", "row-delimiter");
    }
  }

  gridPositionsUpdated() {
    this.chart.controlsOuterEl
      .style("grid-row", `1 / ${this.chart.panes.length * 2 + 1}`)
      .style("grid-column", "1");
    const grid = this.calculateTemplateGrid(this.chart.paneHeights);
    const yGridAxes = grid.yGridAxes;

    for (let i = 0; i < this.chart.panes.length; i++) {
      const pane = this.chart.panes[i];

      const leftAxes = pane.yAxes.filter((a) => a.orient === "left");
      const rightAxes = pane.yAxes.filter((a) => a.orient === "right");

      for (let j = 0; j < leftAxes.length; j++) {
        leftAxes[j].gridPosition = [yGridAxes[0] + 1 - j, i * 2 + 1]; // x+1 for controls
      }
      for (let j = 0; j < rightAxes.length; j++) {
        rightAxes[j].gridPosition = [yGridAxes[0] + 1 + j + 1 + 1, i * 2 + 1];
      }

      pane.gridPosition = [yGridAxes[0] + 1 + 1, i * 2 + 1];

      this.chart.d3ChartEls[i]
        .attr("data-i", i)
        .style("grid-column", pane.gridPosition[0])
        .style("grid-row", pane.gridPosition[1]);
    }

    this.chart.xAxisGridPosition = [
      yGridAxes[0] + 1 + 1,
      this.chart.panes.length * 2,
    ];

    for (let i = 0; i < this.chart.panes.length; i++) {
      if (i < this.chart.panes.length - 1) {
        this.chart.delimiterEls[i].style(
          "grid-column",
          `${yGridAxes[0] + 1} / ${yGridAxes[0] + 1 + 2}`,
        ); // +1 for controls
      }
    }

    this.chart.settingsEl
      .style("grid-column", yGridAxes[0] + 1 + 1 + 1) // +1 for controls
      .style("grid-row", this.chart.panes.length * 2);
  }

  gridUpdated() {
    this.chart.panes.forEach((pane, i) => {
      for (let j = 0; j < pane.yAxes.length; j++) {
        const yAxis = pane.yAxes[j];
        let height = this.chart.paneHeights[i];
        let padding = 0;
        if (yAxis.height && yAxis.position === "bottom") {
          if (this.chart.type === "webgl") {
            height *= yAxis.height / 100;
          }
          padding = this.chart.yAxisPadding;
        }
        this.chart.yAxes[i][yAxis.key].scale.range([height, padding]); // svg height
      }
      Object.keys(this.chart.yAxes[i]).forEach((key, j) => {
        const yAxis = this.chart.yAxes[i][key];

        let w = 0;
        if (yAxis.meta.orient === "left") {
          let column = pane.yAxes[j].gridPosition[0];
          column -= 1; // -1 for controls
          w = this.chart.yAxesWidths[0][column - 1];
        }
        if (yAxis.meta.orient === "right") {
          let column = pane.yAxes[j].gridPosition[0];
          column -= 1;
          const leftCols = this.chart.yAxesWidths[0].length + 1;
          w = this.chart.yAxesWidths[1][column - 1 - leftCols];
        }

        let minX = 0;
        if (yAxis.meta.orient === "left") {
          minX = -w;
        }
        let h = this.chart.paneHeights[i];
        if (yAxis.meta.height && yAxis.meta.position === "bottom") {
          h *= yAxis.meta.height / 100;
        }

        this.chart.yAxesSvg[i][key].attr("width", w);
        this.chart.yAxesSvg[i][key].attr("height", h);
        this.chart.yAxesSvg[i][key].attr("viewBox", `${minX} 0 ${w} ${h}`);

        yAxis.axis.ticks(this.chart.axisHandler.getYTicks(h));
      });
      if (this.chart.gridlines[i]) {
        this.chart.gridlines[i].xTicks(
          this.chart.axisHandler.getXTicks(this.chart.paneWidth),
        );
        this.chart.gridlines[i].yTicks(
          this.chart.axisHandler.getYTicks(this.chart.paneHeights[i]),
        );
      }
    });
  }

  gridSizesUpdated() {
    if (this.chart.paneHeights.length < this.chart.panes.length) {
      this.chart.paneHeights.push(
        this.chart.paneHeights[this.chart.paneHeights.length - 1],
      );
    }

    const fullHeight =
      this.chart.domContainerEl.clientHeight -
      this.chart.xAxisHeight -
      this.getSizeOfDelimiters();
    const sumHeights = this.chart.paneHeights.reduce(
      (partialSum, a) => partialSum + a,
      0,
    );
    const newHeights = [];

    for (let i = 0; i < this.chart.paneHeights.length; i++) {
      newHeights.push(fullHeight * (this.chart.paneHeights[i] / sumHeights));
    }

    const grid = this.calculateTemplateGrid(newHeights);

    const yGridAxes = grid.yGridAxes;
    const templateColumns = grid.templateColumns;
    const templateRows = grid.templateRows;

    this.chart.d3ContainerEl
      .style("display", "grid")
      .style("position", "relative")
      .style("grid-template-columns", templateColumns)
      .style("grid-template-rows", templateRows);

    this.chart.xScale.range([0, this.chart.paneWidth]);
    this.chart.xAxisSvg
      .attr("width", this.chart.paneWidth)
      .attr("height", this.chart.xAxisHeight);
    this.chart.xAxisEl
      .style("grid-column", this.chart.xAxisGridPosition[0])
      .style("grid-row", this.chart.xAxisGridPosition[1]);
    this.chart.xAxis.ticks(
      this.chart.axisHandler.getXTicks(this.chart.paneWidth),
    );

    this.chart.panes.forEach((pane, i) => {
      Object.keys(this.chart.yAxes[i]).forEach((key, j) => {
        const yAxis = this.chart.yAxes[i][key];

        const yAxisEl = this.chart.d3ContainerEl
          .select(
            `div.y-axis-${Utils.toAlphanumeric(this.chart.panes[i].name)}-${Utils.toAlphanumeric(yAxis.meta.key)}`,
          )
          .style("grid-column", yAxis.meta.gridPosition[0])
          .style("grid-row", yAxis.meta.gridPosition[1]);

        let w = 0;
        if (yAxis.meta.orient === "left") {
          const column = pane.yAxes[j].gridPosition[0];
          w = this.chart.yAxesWidths[0][column - 1];
        }
        if (yAxis.meta.orient === "right") {
          const column = pane.yAxes[j].gridPosition[0];
          w = this.chart.yAxesWidths[1][column - 1];
        }

        this.chart.yAxesSvg[i][key].attr("width", w);
      });
    });
  }

  getSizeOfDelimiters() {
    let ds;
    if (this.chart.size === "small") {
      ds = 15;
    } else {
      ds = 5;
    }

    return (this.chart.panes.length - 1) * ds;
  }

  getInitHeights() {
    const fullHeight =
      this.chart.domContainerEl.clientHeight -
      this.chart.xAxisHeight -
      this.getSizeOfDelimiters(); // minus X-axis
    const initHeights = [];
    let heights = [];
    let sumHeights = 0;
    for (let i = 0; i < this.chart.panes.length; i++) {
      const pane = this.chart.panes[i];
      let height = 1;
      if (pane.height) {
        height = pane.height;
      }
      heights.push(height);
      sumHeights += height;
    }
    for (let i = 0; i < this.chart.panes.length; i++) {
      const pane = this.chart.panes[i];
      const percentRatio = (100 * heights[i]) / sumHeights / 100;
      initHeights.push(percentRatio * fullHeight);
    }
    return initHeights;
  }

  calculateTemplateGrid(paneHeights) {
    // calculate amount of axes to setup a grid
    let yGridAxes = [0, 0]; // left, right
    for (let i = 0; i < this.chart.panes.length; i++) {
      const pane = this.chart.panes[i];

      const leftAxes = pane.yAxes.filter((a) => a.orient === "left").length;
      if (yGridAxes[0] < leftAxes) {
        yGridAxes[0] = leftAxes;
      }

      const rightAxes = pane.yAxes.filter((a) => a.orient === "right").length;
      if (yGridAxes[1] < rightAxes) {
        yGridAxes[1] = rightAxes;
      }
    }

    let widths = [[], []]; // 0 = left, 1 = right
    this.chart.yAxesPrecision = {};
    this.chart.yAxesDivision = {};

    for (let i = 0; i < yGridAxes[0]; i++) {
      widths[0].push(0); // min
    }
    for (let i = 0; i < yGridAxes[1]; i++) {
      widths[1].push(0); // min
    }
    for (let lr = 0; lr < 2; lr++) {
      const orient = lr === 0 ? "left" : "right";
      const _widths = widths[lr];
      for (let li = 0; li < yGridAxes[1]; li++) {
        for (let i = 0; i < this.chart.panes.length; i++) {
          const pane = this.chart.panes[i];
          const axes = pane.yAxes.filter((a) => a.orient === orient);
          for (let j = axes.length - 1; j >= 0; j--) {
            const axis = axes[j];

            for (let k = 0; k < pane.metadata.length; k++) {
              for (let l = 0; l < pane.metadata[k].dataKeys.length; l++) {
                const key = pane.metadata[k].dataKeys[l];
                if (axis.key === key.yAxis) {
                  let idx;
                  if (lr === 0) {
                    idx = axes.length - 1 - j;
                  }
                  if (lr === 1) {
                    idx = j;
                  }
                  // find first datapoint with a defined value
                  let datapoint = undefined,
                    datapointBeforeDivision = undefined;
                  if (!this.chart.dataProvider.data) {
                    return;
                  } // hardly reporoducible but can happend when loading chart and previous event in place

                  for (
                    let m = 0;
                    m < this.chart.dataProvider.data.length;
                    m++
                  ) {
                    datapointBeforeDivision =
                      this.chart.dataProvider.data[m][key.dataKey];
                    const dp = this.chart.dataProvider.revertDivision(
                      this.chart.dataProvider.data[m],
                      [key.dataKey],
                    );
                    datapoint = dp[key.dataKey];
                    if (datapoint) break;
                  }
                  // console.log(datapointBeforeDivision, datapoint)

                  const last300Points = this.chart.dataProvider.data.slice(
                    Math.max(this.chart.dataProvider.data.length - 300, 0),
                  ); // Get the last 300 points
                  let min = Infinity;
                  let max = -Infinity;
                  for (let m = 0; m < last300Points.length; m++) {
                    const dp = this.chart.dataProvider.revertDivision(
                      last300Points[m],
                      [key.dataKey],
                    );
                    const v = parseFloat(dp[key.dataKey]);
                    if (v < min) {
                      min = v;
                    }
                    if (v > max) {
                      max = v;
                    }
                  }
                  if (min !== Infinity && max !== -Infinity) {
                    datapoint = Utils.filterInsignificantPrecision(
                      max,
                      min,
                      max,
                    );
                  }

                  let w = Utils.getAxisWidthBasedOnSample(
                    axis.tickFormat === "si" ? datapoint * 5 : datapoint, // this is usually 20% of the chart, therefore actual values will be 5x
                    axis.tickFormat === "si" ? axis.tickFormat : null,
                    this.chart.fontSize,
                  );

                  if (_widths[idx] < w) {
                    _widths[idx] = w;
                  }
                  const p = Utils.getPrecisionBasedOnSample(
                    datapoint,
                    null, //axis.tickFormat
                  );

                  if (
                    !this.chart.yAxesPrecision[axis.key] ||
                    this.chart.yAxesPrecision[axis.key] < p
                  ) {
                    // console.log(axis.key, p, datapoint, key.dataKey)
                    this.chart.yAxesPrecision[axis.key] = p;
                  }

                  const division =
                    this.chart.dataProvider.dividers[key.dataKey];
                  if (
                    !this.chart.yAxesDivision[axis.key] ||
                    (this.chart.yAxesDivision[axis.key] &&
                      this.chart.yAxesDivision[axis.key] < division)
                  ) {
                    this.chart.yAxesDivision[axis.key] = division;
                  }
                }
              }
            }
          }
        }
      }
    }

    this.chart.yAxesWidths = widths;

    if (paneHeights) {
      this.chart.paneHeights = paneHeights;
    } else {
      this.chart.paneHeights = [];

      for (let i = 0; i < this.chart.panes.length; i++) {
        const pane = this.chart.panes[i];
        this.chart.paneHeights[i] =
          (this.chart.domContainerEl.clientHeight -
            this.chart.xAxisHeight -
            this.getSizeOfDelimiters()) /
          this.chart.panes.length;
      }
    }

    let leftAxisNearChartWidth = 0;
    let leftAxisNearChartRealWidth = 0;
    for (let lr = 0; lr < 2; lr++) {
      const orient = lr === 0 ? "left" : "right";
      if (orient === "right") {
        continue;
      }
      for (let li = 0; li < yGridAxes[1]; li++) {
        for (let i = 0; i < this.chart.panes.length; i++) {
          const pane = this.chart.panes[i];
          const axes = pane.yAxes.filter((a) => a.orient === orient);
          for (let j = axes.length - 1; j >= 0; j--) {
            const axis = axes[j];

            for (let k = 0; k < pane.metadata.length; k++) {
              for (let l = 0; l < pane.metadata[k].dataKeys.length; l++) {
                const key = pane.metadata[k].dataKeys[l];
                if (axis.key === key.yAxis) {
                  let idx;
                  if (lr === 0) {
                    idx = axes.length - 1 - j;
                    idx = yGridAxes[0] - idx - 1;
                  }
                  // it is left axis and the one closest to the chart
                  if (orient === "left" && yGridAxes[0] === idx + 1) {
                    if (
                      axis.position === "bottom" &&
                      axis.orient === "left" &&
                      axis.key.endsWith("-volume")
                    ) {
                      // leave 0
                    } else {
                      leftAxisNearChartWidth = this.chart.yAxesWidths[lr][idx];
                    }
                    leftAxisNearChartRealWidth =
                      this.chart.yAxesWidths[lr][idx];
                  }
                }
              }
            }
          }
        }
      }
    }

    const sumLeft = widths[0].reduce((acc, curr) => acc + curr, 0);
    const sumRight = widths[1].reduce((acc, curr) => acc + curr, 0);
    this.chart.paneWidth =
      this.chart.domContainerEl.clientWidth -
      (this.chart.widthControls + sumLeft + sumRight);
    if (leftAxisNearChartWidth === 0) {
      this.chart.paneWidth += leftAxisNearChartRealWidth;
      this.chart.paneWidth += this.chart.widthControls;
    }

    // columns:
    let templateColumns = "";
    if (leftAxisNearChartWidth === 0) {
      templateColumns += `0px `;
    } else {
      templateColumns += `${this.chart.widthControls}px `;
    }
    // left axes
    for (let i = 0; i < yGridAxes[0]; i++) {
      if (i + 1 === yGridAxes[0] && leftAxisNearChartWidth === 0) {
        templateColumns += "0px ";
      } else {
        templateColumns += this.chart.yAxesWidths[0][i] + "px ";
      }
    }
    // chart column
    templateColumns += "1fr ";
    // right axes
    for (let i = 0; i < yGridAxes[1]; i++) {
      templateColumns += this.chart.yAxesWidths[1][i] + "px ";
    }

    // rows:
    let templateRows = "";
    // chart rows
    for (let i = 0; i < this.chart.panes.length; i++) {
      templateRows += `${this.chart.paneHeights[i]}px `;
      if (i < this.chart.panes.length - 1) {
        if (this.chart.size === "small") {
          templateRows += `15px `; // delimiter
        } else {
          templateRows += `5px `; // delimiter
        }
      }
    }
    // x-axis
    templateRows += this.chart.xAxisHeight + "px ";

    return {
      yGridAxes: yGridAxes,
      templateColumns: templateColumns,
      templateRows: templateRows,
    };
  }

  calculateTemplateRowsOnly(paneHeights) {
    if (paneHeights) {
      this.chart.paneHeights = paneHeights;
    } else {
      this.chart.paneHeights = [];

      for (let i = 0; i < this.chart.panes.length; i++) {
        const pane = this.chart.panes[i];
        this.chart.paneHeights[i] =
          (this.chart.domContainerEl.clientHeight -
            this.chart.xAxisHeight -
            this.getSizeOfDelimiters()) /
          this.chart.panes.length;
      }
    }

    // rows:
    let templateRows = "";
    // chart rows
    for (let i = 0; i < this.chart.panes.length; i++) {
      templateRows += `${this.chart.paneHeights[i]}px `;
      if (i < this.chart.panes.length - 1) {
        if (this.chart.size === "small") {
          templateRows += ` 15px `; // delimiter
        } else {
          templateRows += ` 5px `; // delimiter
        }
      }
    }
    // x-axis
    templateRows += this.chart.xAxisHeight + "px ";

    return templateRows;
  }

  createChart(i) {
    const pane = this.chart.panes[i];

    this.chart.gridlines[i] = fc.annotationSvgGridline();
    this.chart.crosshairs[i] = fc.annotationSvgCrosshair();

    if (this.chart.type === "webgl") {
      this.chart.webglMultiSeries[i] = fc
        .seriesWebglMulti()
        .series(this.chart.series);
    }
    let series = [this.chart.gridlines[i], this.chart.crosshairs[i]];
    if (this.chart.type === "svg") {
      series = series.concat(this.chart.series);
    }
    this.chart.svgMultiSeries[i] = fc.seriesSvgMulti().series(series);
    this.chart.svgMultiSeries[i].mapping((d) => d);

    this.chart.crosshairs[i].xLabel((o) => "").yLabel((o) => "");

    this.chart.gridlines[i].xTicks(
      this.chart.axisHandler.getXTicks(this.chart.paneWidth),
    );
    this.chart.gridlines[i].yTicks(
      this.chart.axisHandler.getYTicks(this.chart.paneHeights[i]),
    );

    const fcChart = fc.chartCartesian({
      xScale: this.chart.xScale,
      yScale: this.chart.yAxes[i][this.chart.firstAxisKey[i]].scale,
    });

    if (this.chart.webglMultiSeries[i]) {
      fcChart.webglPlotArea(this.chart.webglMultiSeries[i]);
    }
    fcChart.svgPlotArea(this.chart.svgMultiSeries[i]);

    this.chart.fcCharts[i] = fcChart;

    this.chart.d3ChartEls[i].style("position", "relative");
    const legendEl = this.chart.d3ChartEls[i]
      .append("div")
      .style("z-index", "1")
      .style("position", "absolute")
      .style("top", "5px")
      .style("left", "37px")
      .style("max-width", "75%");

    const legendElIn = legendEl.append("div").attr("class", `legend`);

    for (let j = 0; j < pane.metadata.length; j++) {
      const metadata = pane.metadata[j];
      if (!metadata.legend) {
        continue;
      }

      for (let k = 0; k < metadata.legend.length; k++) {
        const legend = metadata.legend[k];

        const rowEl = legendElIn.append("div").attr("class", "row");
        if (legend.color) {
          rowEl.style("color", legend.color);
        }

        if (legend.icon) {
          rowEl.append("div").attr("class", "icon").html(legend.icon);
        } else {
          switch (metadata.type) {
            case "candlestick":
              rowEl
                .append("div")
                .attr("class", "icon")
                .html(this.icon.getIcon("candle"));
              break;
          }
        }

        const labelText = this.toLabelText(legend.label);

        rowEl.append("div").attr("class", "label").text(labelText);
      }
    }

    // this forces to create svg element
    this.chart.d3ChartEls[i]
      .datum(this.chart.dataProvider.data)
      .call(this.chart.fcCharts[i]);

    this.chart.d3ChartSvgEls[i] =
      this.chart.d3ChartEls[i].select(".plot-area svg");
    this.chart.drawingHandler.create(i);
  }

  toLabelText(label) {
    let labelText = label;

    if (
      typeof label === "object" &&
      label !== null &&
      label.source &&
      label.name
    ) {
      const meta =
        this.chart.dataProvider.keyToMetadata[`${label.source}-${label.name}`];
      if (meta && meta.name_label) {
        labelText = `${meta.name_label} (${label.name}), ${label.interval}`;
      } else {
        labelText = `${label.name}, ${label.interval}`;
      }
    }

    return labelText;
  }

  removeDOMEls(i) {
    const pane = this.chart.panes[i]; // chart to be removed

    if (
      this.chart.d3ContainerEl &&
      this.chart.domChartEls &&
      this.chart.delimiterEls
    ) {
      this.chart.domChartEls[i].remove(); // remove chart from DOM

      if (this.chart.panes.length === 2) {
        // remove delimiters from DOM
        this.chart.d3ContainerEl.selectAll(".delimiter").remove();
        this.chart.delimiterEls.splice(0, 1);
      } else if (this.chart.panes.length >= 3) {
        if (i - 1 < 0) {
          this.chart.delimiterEls.splice(i, 1);
          const delimiterEls = this.chart.d3ContainerEl
            .selectAll(".delimiter")
            .nodes();
          if (delimiterEls.length) {
            delimiterEls[0].remove();
          }
        } else {
          this.chart.delimiterEls.splice(i - 1, 1);
          const delimiterEls = this.chart.d3ContainerEl
            .selectAll(".delimiter")
            .nodes();
          if (delimiterEls.length >= i) {
            delimiterEls[i - 1].remove();
          }
        }
      }
    }

    // remove Y axes
    if (this.chart.yAxes[i]) {
      Object.keys(this.chart.yAxes[i]).forEach((key, j) => {
        const yAxis = this.chart.yAxes[i][key];
        if (this.chart.d3ContainerEl) {
          this.chart.d3ContainerEl
            .select(
              `.y-axis-${Utils.toAlphanumeric(pane.name)}-${Utils.toAlphanumeric(yAxis.meta.key)}`,
            )
            .remove();
        }
      });
    }
  }
}
