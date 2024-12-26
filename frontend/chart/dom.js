/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

import * as fc from "d3fc";

import { GridPicker } from "../gridpicker.js";
import { IntervalPicker } from "../intervalpicker.js";
import { ColorPicker } from "../colorpicker.js";
import { DrawPicker } from "../drawpicker.js";
import { Renderer } from "../renderer.js";
import { PopupWindow } from "../window.js";

import { Utils } from "./utils.js";
import { DOMAlertRuleHandler } from "./dom/rule.js";
import TradinyChart from "./index.js";

export class DOMHandler {
  constructor(chart) {
    this.chart = chart;
  }

  getIcon(name) {
    const iconSizes = {
      back: {
        large: 16,
        small: 21,
      },
      line: {
        large: 16,
        small: 21,
      },
      candle: {
        large: 16,
        small: 21,
      },
    };
    switch (name) {
      case "back":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.back[this.chart.size]}" height="${iconSizes.back[this.chart.size]}" fill="currentColor" class="bi bi-arrow-left" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M15 8a.5.5 0 0 0-.5-.5H2.707l3.147-3.146a.5.5 0 1 0-.708-.708l-4 4a.5.5 0 0 0 0 .708l4 4a.5.5 0 0 0 .708-.708L2.707 8.5H14.5A.5.5 0 0 0 15 8"/>
</svg>`;
      case "line":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.line[this.chart.size]}" height="${iconSizes.line[this.chart.size]}" fill="currentColor" class="bi bi-graph-up" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M14.817 3.113a.5.5 0 0 1 .07.704l-4.5 5.5a.5.5 0 0 1-.74.037L7.06 6.767l-3.656 5.027a.5.5 0 0 1-.808-.588l4-5.5a.5.5 0 0 1 .758-.06l2.609 2.61 4.15-5.073a.5.5 0 0 1 .704-.07"/>
</svg>`;
      case "candle":
        return `<?xml version="1.0" encoding="utf-8"?><!-- Uploaded to: SVG Repo, www.svgrepo.com, Generator: SVG Repo Mixer Tools -->
<svg width="${iconSizes.candle[this.chart.size]}px" height="${iconSizes.candle[this.chart.size]}px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M7.5 3.5V6.5" stroke="currentColor" stroke-linecap="round"/>
<path d="M7.5 14.5V18.5" stroke="currentColor" stroke-linecap="round"/>
<path d="M6.8 6.5C6.08203 6.5 5.5 7.08203 5.5 7.8V13.2C5.5 13.918 6.08203 14.5 6.8 14.5H8.2C8.91797 14.5 9.5 13.918 9.5 13.2V7.8C9.5 7.08203 8.91797 6.5 8.2 6.5H6.8Z" stroke="currentColor"/>
<path d="M16.5 6.5V11.5" stroke="currentColor" stroke-linecap="round"/>
<path d="M16.5 16.5V20.5" stroke="currentColor" stroke-linecap="round"/>
<path d="M15.8 11.5C15.082 11.5 14.5 12.082 14.5 12.8V15.2C14.5 15.918 15.082 16.5 15.8 16.5H17.2C17.918 16.5 18.5 15.918 18.5 15.2V12.8C18.5 12.082 17.918 11.5 17.2 11.5H15.8Z" stroke="currentColor"/>
</svg>`;
    }
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

    const iconSizes = {
      settings: {
        large: 12,
        small: 20,
      },
      grid: {
        large: 13,
        small: 18,
      },
      interval: {},
      add: {
        large: 25,
        small: 32,
      },
      drawing: {
        large: 16,
        small: 19,
      },
      save: {
        large: 16,
        small: 19,
      },
      prompt: {
        large: 16,
        small: 19,
      },
    };

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
      .on("click", (event) => {
        new Renderer().render(
          "settings",
          {
            self: this.chart,
            theme: localStorage.getItem(TradinyChart.ThemeKey),
          },
          (content) => {
            this._win = new PopupWindow(this.chart.elementId);
            this._win.render(content);
            this.chart.panes.forEach((pane, i) => {
              this.chart.d3ContainerEl
                .select(`.tab-${Utils.toAlphanumeric(pane.name)}-autoscale`)
                .on("change", (event) => {
                  this.chart.yAxes[i][this.chart.firstAxisKey[i]].meta.dynamic =
                    !this.chart.yAxes[i][this.chart.firstAxisKey[i]].meta
                      .dynamic;
                  this.chart.renderHandler.render([this.chart.R.Y_DOMAIN]);
                });
              this.chart.d3ContainerEl
                .select(`.tab-${Utils.toAlphanumeric(pane.name)}-remove`)
                .on("click", (event) => {
                  if (
                    confirm(
                      `Are you sure you want to remove pane ${pane.name}?`,
                    )
                  ) {
                    this.chart.operationsHandler.removePane(i);
                    this._win.closePopup();
                  }
                });
            });
          },
        );
      })
      .html(`<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.settings[this.chart.size]}" height="${iconSizes.settings[this.chart.size]}" fill="currentColor" class="bi bi-gear" viewBox="0 0 16 16">
  <path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492M5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0"/>
  <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115z"/>
</svg>
`);

    if (this.chart.features.includes("grid")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon grid-icon")
        .on("click", this.gridSelect.bind(this))
        .html(`<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.grid[this.chart.size]}" height="${iconSizes.grid[this.chart.size]}" fill="currentColor" class="bi bi-grid-3x3" viewBox="0 0 16 16">
        <path d="M0 1.5A1.5 1.5 0 0 1 1.5 0h13A1.5 1.5 0 0 1 16 1.5v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 14.5zM1.5 1a.5.5 0 0 0-.5.5V5h4V1zM5 6H1v4h4zm1 4h4V6H6zm-1 1H1v3.5a.5.5 0 0 0 .5.5H5zm1 0v4h4v-4zm5 0v4h3.5a.5.5 0 0 0 .5-.5V11zm0-1h4V6h-4zm0-5h4V1.5a.5.5 0 0 0-.5-.5H11zm-1 0V1H6v4z"/>
        </svg>`);
    }

    if (this.chart.features.includes("interval")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon interval-icon")
        .on("click", this.intervalSelect.bind(this))
        .html(this.chart.dataProvider.interval);
    }

    if (this.chart.features.includes("add")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon")
        .on("click", (event) => {
          this.addWindow();
        })
        .html(`<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.add[this.chart.size]}" height="${iconSizes.add[this.chart.size]}" fill="currentColor" class="bi bi-plus" viewBox="0 0 16 16">
        <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4"/>
        </svg>`);
    }

    if (this.chart.features.includes("drawing")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon drawing-icon")
        .on("click", this.drawSelect.bind(this))
        .html(`<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.drawing[this.chart.size]}" height="${iconSizes.drawing[this.chart.size]}" fill="currentColor" class="bi bi-brush" width="16px" height="16px" viewBox="0 0 16 16">
      <path d="M15.825.12a.5.5 0 0 1 .132.584c-1.53 3.43-4.743 8.17-7.095 10.64a6.1 6.1 0 0 1-2.373 1.534c-.018.227-.06.538-.16.868-.201.659-.667 1.479-1.708 1.74a8.1 8.1 0 0 1-3.078.132 4 4 0 0 1-.562-.135 1.4 1.4 0 0 1-.466-.247.7.7 0 0 1-.204-.288.62.62 0 0 1 .004-.443c.095-.245.316-.38.461-.452.394-.197.625-.453.867-.826.095-.144.184-.297.287-.472l.117-.198c.151-.255.326-.54.546-.848.528-.739 1.201-.925 1.746-.896q.19.012.348.048c.062-.172.142-.38.238-.608.261-.619.658-1.419 1.187-2.069 2.176-2.67 6.18-6.206 9.117-8.104a.5.5 0 0 1 .596.04M4.705 11.912a1.2 1.2 0 0 0-.419-.1c-.246-.013-.573.05-.879.479-.197.275-.355.532-.5.777l-.105.177c-.106.181-.213.362-.32.528a3.4 3.4 0 0 1-.76.861c.69.112 1.736.111 2.657-.12.559-.139.843-.569.993-1.06a3 3 0 0 0 .126-.75zm1.44.026c.12-.04.277-.1.458-.183a5.1 5.1 0 0 0 1.535-1.1c1.9-1.996 4.412-5.57 6.052-8.631-2.59 1.927-5.566 4.66-7.302 6.792-.442.543-.795 1.243-1.042 1.826-.121.288-.214.54-.275.72v.001l.575.575zm-4.973 3.04.007-.005zm3.582-3.043.002.001h-.002z"/>
    </svg>`);
    }

    if (this.chart.features.includes("save")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon save-icon")
        .on("click", (event) => {
          this.chart.saveHandler.windowSave();
        })
        .html(`<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.save[this.chart.size]}" height="${iconSizes.save[this.chart.size]}" fill="currentColor" class="bi bi-cloud-plus" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M8 5.5a.5.5 0 0 1 .5.5v1.5H10a.5.5 0 0 1 0 1H8.5V10a.5.5 0 0 1-1 0V8.5H6a.5.5 0 0 1 0-1h1.5V6a.5.5 0 0 1 .5-.5"/>
  <path d="M4.406 3.342A5.53 5.53 0 0 1 8 2c2.69 0 4.923 2 5.166 4.579C14.758 6.804 16 8.137 16 9.773 16 11.569 14.502 13 12.687 13H3.781C1.708 13 0 11.366 0 9.318c0-1.763 1.266-3.223 2.942-3.593.143-.863.698-1.723 1.464-2.383m.653.757c-.757.653-1.153 1.44-1.153 2.056v.448l-.445.049C2.064 6.805 1 7.952 1 9.318 1 10.785 2.23 12 3.781 12h8.906C13.98 12 15 10.988 15 9.773c0-1.216-1.02-2.228-2.313-2.228h-.5v-.5C12.188 4.825 10.328 3 8 3a4.53 4.53 0 0 0-2.941 1.1z"/>
</svg>`);
    }
    if (this.chart.features.includes("prompt")) {
      this.chart.controlsEl
        .append("div")
        .attr("class", "icon prompt-icon")
        .on("click", async (event) => {
          await this.promptWindow();
        }).html(`
<svg role="img" fill="currentColor" width="${iconSizes.prompt[this.chart.size]}" height="${iconSizes.prompt[this.chart.size]}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/></svg>`);
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
        this.chart.yAxes[i][yAxis.key].scale.range([
          this.chart.paneHeights[i],
          0,
        ]); // svg height
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

        this.chart.yAxesSvg[i][key].attr("width", w);
        this.chart.yAxesSvg[i][key].attr("height", h);
        this.chart.yAxesSvg[i][key].attr("viewBox", `${minX} 0 ${w} ${h}`);

        yAxis.axis.ticks(
          this.chart.axisHandler.getYTicks(this.chart.paneHeights[i]),
        );
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

  getAxisWidthBasedOnSample(sample, formatter) {
    if (sample == undefined) {
      return 0;
    }
    if (formatter) {
      if (formatter === "si") {
        sample = d3.format(".3s")(sample);
      } else {
        sample = formatter(sample);
      }
    }
    let str = "" + sample;
    if (str.includes(".")) {
      str = str.replace(/0+$/, "");
    }
    const w = Math.round(
      Utils.getTextWidth(str + "0", `${this.chart.fontSize}px sans-serif`),
    );

    return w;
  }
  getPrecisionBasedOnSample(sample, formatter) {
    if (sample == undefined) {
      return 0;
    }
    if (formatter) {
      if (formatter === "si") {
        sample = d3.format(".3s")(sample);
      } else {
        sample = formatter(sample);
      }
    }
    let str = sample.toString();
    if (str.includes(".")) {
      str = str.replace(/\.?0+$/, "");
    }
    const decimalIndex = str.indexOf(".");
    if (decimalIndex === -1) {
      return 0; // No decimal places
    } else {
      return str.length - decimalIndex - 1;
    }
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

                  let w = this.getAxisWidthBasedOnSample(
                    axis.tickFormat === "si" ? datapoint * 5 : datapoint, // this is usually 20% of the chart, therefore actual values will be 5x
                    axis.tickFormat === "si" ? axis.tickFormat : null,
                  );

                  if (_widths[idx] < w) {
                    _widths[idx] = w;
                  }
                  const p = this.getPrecisionBasedOnSample(
                    datapoint,
                    null, //axis.tickFormat
                  );

                  if (
                    !this.chart.yAxesPrecision[axis.key] ||
                    this.chart.yAxesPrecision[axis.key] < p
                  ) {
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
    const sumLeft = widths[0].reduce((acc, curr) => acc + curr, 0);
    const sumRight = widths[1].reduce((acc, curr) => acc + curr, 0);
    this.chart.paneWidth =
      this.chart.domContainerEl.clientWidth -
      (this.chart.widthControls + sumLeft + sumRight);

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

    // columns:
    let templateColumns = `${this.chart.widthControls}px `;
    // left axes
    for (let i = 0; i < yGridAxes[0]; i++) {
      templateColumns += this.chart.yAxesWidths[0][i] + "px ";
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

    const series = [];

    this.chart.gridlines[i] = fc.annotationSvgGridline();
    this.chart.gridlines[i].xTicks(
      this.chart.axisHandler.getXTicks(this.chart.paneWidth),
    );
    this.chart.gridlines[i].yTicks(
      this.chart.axisHandler.getYTicks(this.chart.paneHeights[i]),
    );

    this.chart.crosshairs[i] = fc
      .annotationSvgCrosshair()
      .xLabel((o) => "")
      .yLabel((o) => "");

    this.chart.svgMultiSeries[i] = fc
      .seriesSvgMulti()
      .series([this.chart.gridlines[i], this.chart.crosshairs[i]]);

    const fcChart = fc
      .chartCartesian({
        xScale: this.chart.xScale,
        yScale: this.chart.yAxes[i][this.chart.firstAxisKey[i]].scale, // select first
      })
      .webglPlotArea(this.chart.webglMultiSeries[i])
      .svgPlotArea(this.chart.svgMultiSeries[i]);

    this.chart.fcCharts[i] = fcChart;

    this.chart.d3ChartEls[i].style("position", "relative");
    const legendEl = this.chart.d3ChartEls[i]
      .append("div")
      .style("z-index", "1")
      .style("position", "absolute")
      .style("top", "5px")
      .style("left", "5px")
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
                .html(this.getIcon("candle"));
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

  async promptWindow() {
    this.converastionId = Utils.generateUUID();
    this.messageId = 0;
    this.img = await this.chart.toImage();
    this.imgDesc = await this.chart.describe();

    new Renderer().render("prompt", { self: this }, (content) => {
      this._win = new PopupWindow(this.chart.elementId, "auto");
      this._win.render(content);

      const inputEl = this.chart.d3ContainerEl.select("textarea.prompt");
      inputEl.node().focus();

      const that = this;
      inputEl.node().addEventListener("keydown", function (event) {
        that.promptSubmitOnKeyDown(event);
      });
    });
  }

  promptSubmitOnKeyDown(event) {
    if (event.keyCode === 13 || event.key === "Enter") {
      this.promptSubmit();
      event.preventDefault();
    }
  }

  promptSubmit() {
    this.chart.d3ContainerEl.select(".conversation").style("display", "block");

    const container = this.chart.d3ContainerEl.select("div.popup-show");
    const containerEl = container.node();
    const inputEl = this.chart.d3ContainerEl.select("textarea.prompt");
    const prompt = inputEl.node().value;
    inputEl.node().value = "";
    const resEl = this.chart.d3ContainerEl.select(`.conversation`);

    this.messageId += 1;
    const userEl = resEl
      .append("div")
      .attr("class", `user user-${this.messageId}`)
      .html(prompt);

    this.messageId += 1;
    const assistantEl = resEl
      .append("div")
      .attr("class", `assistant assistant-${this.messageId}`)
      .html("Loading...");

    container.node().scrollTop = container.node().scrollHeight; // scroll

    let loading = true;
    let message = "";

    if (this.messageId === 2) {
      this.chart.dataProvider.prompt(
        this.converastionId,
        this.imgDesc,
        prompt,
        this.img,
        (data) => {
          if (loading) {
            assistantEl.html("");
            loading = false;
          }
          message += data;
          assistantEl.node().innerHTML = Utils.markdownToHtml(message);

          const diff =
            containerEl.scrollTop +
            containerEl.clientHeight -
            containerEl.scrollHeight +
            50;

          if (diff > 0) {
            containerEl.scrollTop = containerEl.scrollHeight;
          }
        },
      );
    } else {
      this.chart.dataProvider.reply(this.converastionId, prompt, (data) => {
        if (loading) {
          assistantEl.html("");
          loading = false;
        }
        message += data;
        assistantEl.node().innerHTML = Utils.markdownToHtml(message);

        containerEl.scrollTop = containerEl.scrollHeight;
      });
    }
  }

  addWindow(
    render = ["grids", "charts", "data", "indicators", "alert"],
    closeDisabled = false,
  ) {
    const grids = this.chart.saveHandler.getGrids();
    const charts = this.chart.saveHandler.getCharts();
    const d3ContainerEl = d3.select("#" + this.chart.elementId); // need to have its own reference, because it might be not initialized yet
    const frequentlyUsed = this.getFrequentlyUsed();

    let activeTab = "data";
    if (render.includes("charts") && Object.keys(charts).length) {
      activeTab = "charts";
    } else if (render.includes("grids") && Object.keys(grids).length) {
      activeTab = "grids";
    }

    new Renderer().render(
      "add",
      { self: this, render, grids, charts, activeTab },
      (content) => {
        this._win = new PopupWindow(
          this.chart.elementId,
          "auto",
          closeDisabled,
        );
        this._win.render(content);

        new Renderer().render(
          "data-search-results",
          { self: this.chart, data: [], loading: true },
          (content) => {
            d3ContainerEl.select("div.data-search-results").html(content);
          },
        );

        const searchData = (s) => {
          this.chart.dataProvider.searchData(s, (data) => {
            this._data = data;

            new Renderer().render(
              "data-search-results",
              {
                self: this.chart,
                s,
                data,
                frequentlyUsed: frequentlyUsed.data,
              },
              (content) => {
                d3ContainerEl.select("div.data-search-results").html(content);
              },
            );
          });
        };

        const searchIndicators = (s) => {
          this.chart.dataProvider.searchIndicators(s, (data) => {
            this._indicators = data;
            new Renderer().render(
              "indicators-search-results",
              {
                self: this.chart,
                s,
                that: this,
                data,
                frequentlyUsed: frequentlyUsed.indicator,
              },
              (content) => {
                d3ContainerEl
                  .select("div.indicators-search-results")
                  .html(content);
              },
            );
          });
        };

        d3ContainerEl.select("input.data-search").on("keydown", (event) => {
          setTimeout(() => {
            searchData(event.target.value);
          }, 0);
        });
        d3ContainerEl.select("input.data-search").node().focus();
        searchData("");

        d3ContainerEl
          .select("input.indicators-search")
          .on("keydown", (event) => {
            setTimeout(() => {
              searchIndicators(event.target.value);
            }, 0);
          });
        searchIndicators("");
      },
    );
  }

  getYAxesFromOutputs(outputs) {
    const axes = {};
    for (var i = 0; i < outputs.length; i++) {
      if (
        !axes[outputs[i].y_axis] ||
        !(outputs[i].y_axis in axes[outputs[i].y_axis])
      ) {
        axes[outputs[i].y_axis] = [outputs[i].name];
      } else {
        axes[outputs[i].y_axis].push(outputs[i].name);
      }
    }
    const axesArr = [];
    for (var i of Object.keys(axes)) {
      axesArr.push({
        y_axis: i,
        keys: axes[axes[i]],
      });
    }
    return axesArr;
  }

  dataWindow(id) {
    this._win.closePopup();
    this._data = this._data.find((item) => item.id === id);
    if (!this._data) {
      this._data = this.getFrequentlyUsed().data.find((item) => item.id === id);
    }

    if (
      !this.chart.panes ||
      (this.chart.panes && this.chart.panes.length === 0)
    ) {
      const y_axes = this.getYAxesFromOutputs(this._data.details.outputs);
      const axesMap = {},
        scalesMap = {};
      const axes = ["New right axis", "New left axis"];
      for (var i = 0; i < y_axes.length; i++) {
        const k = y_axes[i].y_axis;
        axesMap[k] = i % 2 === 0 ? axes[0] : axes[1];
        scalesMap[k] = "linear";
      }
      const colorMap = {};
      switch (this._data.details.type) {
        case "line":
          colorMap["color"] = "#e60049";
          break;
        case "candlestick":
          colorMap["bearish-candle"] = this.chart.defaultBearishCandleColor;
          colorMap["bullish-candle"] = this.chart.defaultBullishCandleColor;
          break;
      }

      this.chart.operationsHandler.addData(
        this._data,
        0,
        axesMap,
        scalesMap,
        colorMap,
      );
      this._data = null;
    } else {
      new Renderer().render(
        "data",
        {
          self: this.chart,
          data: this._data,
          y_axes: this.getYAxesFromOutputs(this._data.details.outputs),
          title: this._data.details.name,
        },
        (content) => {
          this._win = new PopupWindow(this.chart.elementId);
          this._win.render(content);

          this.onPaneChange(
            this.chart.d3ContainerEl.select("select.pane-select").node(),
          );
        },
      );
    }
  }

  addData() {
    this._win.closePopup();

    const i = parseInt(
      this.chart.d3ContainerEl.select("select.pane-select").node().value,
    );
    const axesMap = {};
    this.chart.d3ContainerEl
      .selectAll("select.axes-list")
      .each(function (d, i) {
        const key = d3.select(this).attr("data-key");
        const value = d3.select(this).node().value;
        axesMap[key] = value;
      });

    const scalesMap = {};
    this.chart.d3ContainerEl
      .selectAll("select.scales-list")
      .each(function (d, i) {
        const key = d3.select(this).attr("data-key");
        const value = d3.select(this).node().value;
        scalesMap[key] = value;
      });

    const colorMap = {};
    this.chart.d3ContainerEl.selectAll("div.color-list").each(function (d, i) {
      const key = d3.select(this).attr("data-key");
      const value = d3.select(this).attr("data-value");
      colorMap[key] = value;
    });

    this.chart.operationsHandler.addData(
      this._data,
      i,
      axesMap,
      scalesMap,
      colorMap,
    );
    this._data = undefined;
  }

  onPaneChange(el) {
    requestAnimationFrame(() => {
      const paneI = el.value;
      const pane = this.chart.panes ? this.chart.panes[paneI] : undefined;
      let nextNewAxisDirection = "right";

      this.chart.d3ContainerEl
        .selectAll("select.axes-list")
        .each(function (d, i) {
          const axEl = d3.select(this);
          const axes = ["New right axis", "New left axis", "Disable"];
          if (pane) {
            for (let j = 0; j < pane.yAxes.length; j++) {
              const yAxis = pane.yAxes[j];
              axes.push(yAxis.key);
            }
          }
          let content = "";
          let alreadySelected = false;
          for (let j = 0; j < axes.length; j++) {
            let selected =
              axEl.attr("data-preferred") &&
              axes[j]
                .toLowerCase()
                .includes(axEl.attr("data-preferred").toLowerCase());

            if (axes.length === 3) {
              // if new, select right, left, right, left etc.
              if (nextNewAxisDirection === "right" && j === 0) {
                selected = true;
              } else if (nextNewAxisDirection === "left" && j === 1) {
                selected = true;
              }
            }

            if (alreadySelected) {
              selected = false;
            }
            content += `<option value="${axes[j]}" ${selected ? "selected" : ""}>${axes[j].split("-").join(" ")}</option>`;
            if (selected) {
              alreadySelected = true;
            }
          }
          axEl.html(content);

          if (nextNewAxisDirection === "right") {
            nextNewAxisDirection = "left";
          } else if (nextNewAxisDirection === "left") {
            nextNewAxisDirection = "right";
          }
        });

      const self = this;
      this.chart.d3ContainerEl
        .selectAll("select.data-list")
        .each(function (d, i) {
          const dEl = d3.select(this);
          let content = "";
          let alreadySelected = false;

          if (!pane) {
            const keys = Object.keys(self.chart.dataProvider.data[0]);
            for (let j = 0; j < keys.length; j++) {
              const key = keys[j];
              if (["date", "_date", "_dateObj"].includes(key)) {
                continue;
              }
              let selected =
                dEl.attr("data-preferred") &&
                key
                  .toLowerCase()
                  .includes(dEl.attr("data-preferred").toLowerCase());

              if (alreadySelected) {
                selected = false;
              }
              content += `<option value="${key}" ${selected ? "selected" : ""}>${key.split("-").join(" ")}</option>`;
              if (selected) {
                alreadySelected = true;
              }
            }
          } else {
            for (let j = 0; j < pane.metadata.length; j++) {
              for (let k = 0; k < pane.metadata[j].dataKeys.length; k++) {
                const key = pane.metadata[j].dataKeys[k].dataKey;
                let selected =
                  dEl.attr("data-preferred") &&
                  key
                    .toLowerCase()
                    .includes(dEl.attr("data-preferred").toLowerCase());

                if (alreadySelected) {
                  selected = false;
                }
                content += `<option value="${key}" ${selected ? "selected" : ""}>${key.split("-").join(" ")}</option>`;
                if (selected) {
                  alreadySelected = true;
                }
              }
            }
          }

          dEl.html(content);
        });

      this.chart.d3ContainerEl
        .selectAll("div.color-list")
        .each(function (d, i) {
          const dEl = d3.select(this);

          let defaultColor;
          if (
            !self._indicator &&
            self._data &&
            self._data.details.type === "candlestick"
          ) {
            if (i === 0) {
              defaultColor = self.chart.defaultBullishCandleColor;
            }
            if (i === 1) {
              defaultColor = self.chart.defaultBearishCandleColor;
            }
          }
          const colorPicker = new ColorPicker(
            defaultColor,
            dEl.node(),
            (c) => {},
          );
        });
    });
  }

  onAxisChange(el) {
    // requestAnimationFrame(() => {
    //     console.log(el.value)
    // });
  }

  indicatorWindow(id) {
    this._win.closePopup();
    this._indicator = this._indicators.find((item) => item.id === id);
    if (!this._indicator) {
      this._indicator = this.getFrequentlyUsed().indicator.find(
        (item) => item.id === id,
      );
    }

    new Renderer().render(
      "indicator",
      {
        self: this.chart,
        indicator: this._indicator,
        y_axes: this.getYAxesFromOutputs(this._indicator.details.outputs),
        title: this._indicator.name,
      },
      (content) => {
        this._win = new PopupWindow(this.chart.elementId);
        this._win.render(content);

        this.onPaneChange(
          this.chart.d3ContainerEl.select("select.pane-select").node(),
        );
      },
    );
  }

  addIndicator() {
    const i = parseInt(
      this.chart.d3ContainerEl.select("select.pane-select").node().value,
    );

    const inputs = {};
    let someInputEmpty = false;
    this.chart.d3ContainerEl.selectAll(".input").each(function (d, i) {
      const key = d3.select(this).attr("data-key");
      const value = d3.select(this).node().value;
      inputs[key] = value;
      if (!Utils.isNumeric(value)) {
        someInputEmpty = true;
      }
    });
    if (someInputEmpty) {
      alert("All inputs are required!");
      return;
    }

    this._win.closePopup();

    const axesMap = {};
    this.chart.d3ContainerEl
      .selectAll("select.axes-list")
      .each(function (d, i) {
        const key = d3.select(this).attr("data-key");
        const value = d3.select(this).node().value;
        axesMap[key] = value;
      });

    const scalesMap = {};
    this.chart.d3ContainerEl
      .selectAll("select.scales-list")
      .each(function (d, i) {
        const key = d3.select(this).attr("data-key");
        const value = d3.select(this).node().value;
        scalesMap[key] = value;
      });

    const self = this;
    const dataMap = {};
    this.chart.d3ContainerEl
      .selectAll("select.data-list")
      .each(function (d, i) {
        const key = d3.select(this).attr("data-key");
        const value = d3.select(this).node().value;
        const datasource = self.chart.dataProvider.keyToData[value] || {};
        const source = datasource.source;
        const name = datasource.name;
        const interval = datasource.interval;
        const dataKey = datasource.key;
        dataMap[key] = {
          source,
          name,
          interval,
          value,
          dataKey,
        };
      });

    const colorMap = {};
    this.chart.d3ContainerEl.selectAll("div.color-list").each(function (d, i) {
      const key = d3.select(this).attr("data-key");
      const value = d3.select(this).attr("data-value");
      colorMap[key] = value;
    });

    this.chart.operationsHandler.addIndicator(
      this._indicator,
      i,
      inputs,
      axesMap,
      scalesMap,
      dataMap,
      colorMap,
    );
    this._indicator = undefined;
  }

  switchTheme(el) {
    const value = d3.select(el).node().value;
    localStorage.setItem(TradinyChart.ThemeKey, value);
    this.setTheme(value);
  }

  setTheme(theme = "") {
    d3.select(`#${this.chart.gridHandler.options.elementId}`).attr(
      "class",
      `tradiny-chart ${theme} ${this.chart.size}`,
    );
  }

  drawSelect() {
    const drawPicker = new DrawPicker(this, (tool) => {});
  }

  gridSelect() {
    const gridPicker = new GridPicker(
      null,
      this.chart.d3ContainerEl.select(".controls").node(),
      (grid) => {
        this.chart.gridHandler.changeGrid(grid);
      },
      this,
    );
  }

  intervalSelect() {
    const intervalPicker = new IntervalPicker(
      null,
      this.chart.d3ContainerEl.select(".controls").node(),
      (interval) => {
        const oldInterval = this.chart.controlsEl
          .select(".interval-icon")
          .text()
          .trim();
        this.chart.controlsEl.select(".interval-icon").html(interval);

        this.chart.operationsHandler.onIntervalChange(oldInterval, interval);
      },
      this,
    );
  }

  addAlertRule(init = 0) {
    const rulesEl = this.chart.d3ContainerEl.select(".alert-rules");
    let rulesSize = rulesEl.selectAll("*").size();
    if (init && rulesSize) {
      return;
    }

    if (!this.domAlert || init) {
      this.domAlert = new DOMAlertRuleHandler(this.chart);
      this.domAlert.token();
    }

    rulesSize = rulesEl.selectAll("*").size();
    if (rulesSize) {
      this.domAlert.createOperator(rulesEl);
    }
    this.domAlert.initialize(rulesEl);
  }

  saveAlert() {
    const message = this.chart.d3ContainerEl
      .select("textarea")
      .property("value");
    if (!message) {
      alert("All inputs are required!");
      return;
    }
    const operatorEls = this.chart.d3ContainerEl.selectAll(
      ".alert-rules .rule-operator",
    );
    let operators = [];
    operatorEls.each(function () {
      let value = d3.select(this).property("value");
      operators.push(value);
    });
    const rules = [];
    for (const ruleId of Object.keys(this.domAlert.rules)) {
      const rule = this.domAlert.getRule(ruleId);
      for (let i of Object.keys(rule)) {
        if (!rule[i]) {
          alert("All inputs are required!");
          return;
        }
      }
      rules.push(rule);
    }

    // copy
    const dataProviderConfig = JSON.parse(
      JSON.stringify(this.chart.dataProvider.config),
    );
    const indicators = JSON.parse(JSON.stringify(this.domAlert._indicators));

    const sides = ["1", "2"];
    const dataProviderConfigData2 = [];
    for (let j = 0; j < rules.length; j++) {
      for (let k = 0; k < sides.length; k++) {
        const side = sides[k];
        const rule = rules[j];
        if (rule[`type${side}`] === "data") {
          dataProviderConfigData2.push({
            type: "data",
            source: rule[`source${side}`],
            name: rule[`name${side}`],
            interval: rule[`interval${side}`],
          });
        } else if (rule[`type${side}`] === "indicator") {
          const indicatorId = indicators[rule[`indicator${side}`]].indicator.id;
          const firstDataKey = Object.keys(
            indicators[rule[`indicator${side}`]].indicator.dataMap,
          )[0];
          const source =
            indicators[rule[`indicator${side}`]].indicator.dataMap[firstDataKey]
              .source;
          const name =
            indicators[rule[`indicator${side}`]].indicator.dataMap[firstDataKey]
              .name;
          const currentInterval =
            indicators[rule[`indicator${side}`]].indicator.dataMap[firstDataKey]
              .interval;
          const selectedInterval = rule[`indicator_interval${side}`];

          dataProviderConfigData2.push({
            type: "data",
            source: source,
            name: name,
            interval: selectedInterval,
          });

          let indicatorDataProvider = JSON.parse(
            JSON.stringify(
              dataProviderConfig.data.find((obj) => obj.id === indicatorId),
            ),
          );
          if (currentInterval !== selectedInterval) {
            indicatorDataProvider = Utils.replaceAllInObj(
              indicatorDataProvider,
              `-${currentInterval}-`,
              `-${selectedInterval}-`,
            );
            indicatorDataProvider = Utils.replaceExactInObj(
              indicatorDataProvider,
              `${currentInterval}`,
              `${selectedInterval}`,
            );
            indicators[rule[`indicator${side}`]].indicator =
              Utils.replaceAllInObj(
                indicators[rule[`indicator${side}`]].indicator,
                `-${currentInterval}-`,
                `-${selectedInterval}-`,
              );
            indicators[rule[`indicator${side}`]].indicator =
              Utils.replaceExactInObj(
                indicators[rule[`indicator${side}`]].indicator,
                `${currentInterval}`,
                `${selectedInterval}`,
              );
          }
          dataProviderConfigData2.push(indicatorDataProvider);
        }
      }
    }

    dataProviderConfig.data = dataProviderConfigData2;

    const alertObj = {
      message,
      operators,
      rules,
      dataProviderConfig,
      indicators,
    };
    this.chart.dataProvider.addAlert(alertObj);
    this._win.closePopup();
  }

  getFrequentlyUsed() {
    const frequentlyUsed = { data: [], indicator: [] };
    let _ = this.chart.saveHandler.getFrequentlyUsed("data");
    for (let i = 0; i < _.length; i++) {
      const d = _[i].data;
      frequentlyUsed.data.push({
        details: d.data.details,
        id: `${d.source}-${d.name}`,
        name: d.name,
        type: "data",
      });
    }

    _ = this.chart.saveHandler.getFrequentlyUsed("indicator");
    for (let i = 0; i < _.length; i++) {
      const d = _[i].data;
      frequentlyUsed.indicator.push(d.indicator);
    }
    return frequentlyUsed;
  }
}
