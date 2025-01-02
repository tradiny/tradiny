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

import { Renderer } from "../../renderer.js";
import { PopupWindow } from "../../window.js";
import { GridPicker } from "../../gridpicker.js";
import { IntervalPicker } from "../../intervalpicker.js";
import { ColorPicker } from "../../colorpicker.js";
import { DrawPicker } from "../../drawpicker.js";
import { DOMRuleHandler } from "./rule.js";

import { Utils } from "../utils.js";
import TradinyChart from "../index.js";

export class DOMControlsHandler {
  constructor(domHandler) {
    this.domHandler = domHandler;
    this.chart = domHandler.chart;
  }

  settingsWindow(event) {
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
                !this.chart.yAxes[i][this.chart.firstAxisKey[i]].meta.dynamic;
              this.chart.renderHandler.render([this.chart.R.Y_DOMAIN]);
            });
          this.chart.d3ContainerEl
            .select(`.tab-${Utils.toAlphanumeric(pane.name)}-remove`)
            .on("click", (event) => {
              if (
                confirm(`Are you sure you want to remove pane ${pane.name}?`)
              ) {
                this.chart.operationsHandler.removePane(i);
                this._win.closePopup();
              }
            });
        });
      },
    );
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

  downloadCSV() {
    Utils.downloadCSV(this._rows);
  }

  scan() {
    const search = this.chart.d3ContainerEl
      .select(".data-search")
      .property("value");
    if (!search) {
      alert("All inputs are required!");
      return;
    }
    const scanObj = this.serializeRules(this.domFilter);
    if (scanObj && scanObj.rules.length === 0) {
      alert("Add at least one condition.");
      return;
    }

    new Renderer().render(
      "data-search-results",
      { self: this.chart, data: [], loading: true },
      (content) => {
        this.chart.d3ContainerEl
          .select("div.data-search-results")
          .html(content);
      },
    );

    if (scanObj) {
      scanObj.search = search;

      this.toggleFilter(0);
      const data = [];
      const rows = [];

      this._win.onClose(() => {
        this.scanning = false; // disable scanning on selection if there is any
        this.chart.dataProvider.scanStop();
      });

      this.scanning = true;
      this.chart.dataProvider.scan(
        scanObj,
        (progressMessage) => {
          const rulesSize = this.chart.d3ContainerEl
            .selectAll(".filter-rules .rule")
            .size();
          if (rulesSize) {
            this.chart.d3ContainerEl
              .select(".scanner > div > span")
              .html(`Filters (${rulesSize}): ${progressMessage}`);
          }
        },
        (d) => {
          if (!this.scanning) {
            return;
          }
          const dbEntry = d.data;
          data.push(dbEntry);
          this._data = data;

          const dataValues = d.data_values;
          let row = {
            Source: dbEntry.details.source_label
              ? `${dbEntry.details.source_label} (${dbEntry.details.source})`
              : dbEntry.details.source,
            Categories: dbEntry.details.categories.join(", "),
            Name: dbEntry.details.name_label
              ? `${dbEntry.details.name_label} (${dbEntry.details.name})`
              : dbEntry.details.name,
          };
          row = { ...row, ...dataValues };
          rows.push(row);
          this._rows = rows;

          new Renderer().render(
            "data-table",
            {
              self: this.chart,
              rows: rows,
              data,
            },
            (content) => {
              const el = this.chart.d3ContainerEl.select(
                "div.data-search-results",
              );
              if (el) {
                el.html(content);
              }
            },
          );
        },
      );
    }
  }

  toggleFilter(open = 1) {
    const d3ContainerEl = d3.select("#" + this.chart.elementId);
    const isScannerOpen =
      d3ContainerEl.select(".scanner .open").style("display") !== "none";

    if (open && !isScannerOpen) {
      d3ContainerEl.select(".filter-rules").style("display", "block");
      // d3ContainerEl.select(".data-search-results").style("display", "none");
      d3ContainerEl.select(".scanner .open").style("display", "inline");
      d3ContainerEl.select(".scanner .close").style("display", "none");

      d3ContainerEl.select(".add-filter-button").style("display", "block");
      d3ContainerEl.select(".scan-button").style("display", "block");

      d3ContainerEl
        .select(".tab-data input.data-search")
        .attr("disabled", "disabled");
    } else {
      d3ContainerEl.select(".filter-rules").style("display", "none");
      d3ContainerEl.select(".data-search-results").style("display", "block");
      d3ContainerEl.select(".scanner .open").style("display", "none");
      d3ContainerEl.select(".scanner .close").style("display", "inline");

      d3ContainerEl.select(".add-filter-button").style("display", "none");
      // d3ContainerEl.select(".scan-button").style("display", "none");

      d3ContainerEl
        .select(".tab-data input.data-search")
        .attr("disabled", null);
    }

    this.addFilterRule(1);
  }

  addFilterRule(init = 0) {
    const rulesEl = this.chart.d3ContainerEl.select(".filter-rules");
    let rulesSize = rulesEl.selectAll("*").size();
    if (init && rulesSize) {
      return;
    }

    if (!this.domFilter || init) {
      this.domFilter = new DOMRuleHandler(this.chart, ".filter-rules");
      this.domFilter.hideSource = true;
      this.domFilter.hideName = true;
    }

    rulesSize = rulesEl.selectAll("*").size();
    if (rulesSize) {
      this.domFilter.createOperator(rulesEl);
    }
    this.domFilter.initialize(rulesEl);
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
                if (this.scanning) {
                  this.scanning = false;
                  this.chart.dataProvider.scanStop();
                }
                if (this.chart.d3ContainerEl) {
                  const filtersEl = this.chart.d3ContainerEl.select(
                    ".scanner > div > span",
                  );
                  if (filtersEl) {
                    filtersEl.html(`Filters`);
                  }
                }
                if (s && this.chart.d3ContainerEl) {
                  d3ContainerEl.select(".scanner").style("display", "block");
                } else {
                  d3ContainerEl.select(".scanner").style("display", "none");
                }
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
    const drawPicker = new DrawPicker(this.domHandler, (tool) => {});
  }

  gridSelect() {
    const gridPicker = new GridPicker(
      null,
      this.chart.d3ContainerEl.select(".controls").node(),
      (grid) => {
        this.chart.gridHandler.changeGrid(grid);
      },
      this.domHandler,
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
      this.domHandler,
    );
  }

  addAlertRule(init = 0) {
    const rulesEl = this.chart.d3ContainerEl.select(".alert-rules");
    let rulesSize = rulesEl.selectAll("*").size();
    if (init && rulesSize) {
      return;
    }

    if (!this.domAlert || init) {
      this.domAlert = new DOMRuleHandler(this.chart, ".alert-rules");
      this.domAlert.token();
    }

    rulesSize = rulesEl.selectAll("*").size();
    if (rulesSize) {
      this.domAlert.createOperator(rulesEl);
    }
    this.domAlert.initialize(rulesEl);
  }

  serializeRules(domRules) {
    const operatorEls = this.chart.d3ContainerEl.selectAll(
      ".rules .rule-operator",
    );
    let operators = [];
    operatorEls.each(function () {
      let value = d3.select(this).property("value");
      operators.push(value);
    });
    const rules = [];
    for (const ruleId of Object.keys(domRules.rules)) {
      const rule = domRules.getRule(ruleId);
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
    const indicators = JSON.parse(JSON.stringify(domRules._indicators));

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

    dataProviderConfig.data = Utils.removeDuplicates(dataProviderConfigData2);

    const serialized = {
      operators,
      rules,
      dataProviderConfig,
      indicators,
    };
    return serialized;
  }

  saveAlert() {
    const message = this.chart.d3ContainerEl
      .select("textarea")
      .property("value");
    if (!message) {
      alert("All inputs are required!");
      return;
    }
    const alertObj = this.serializeRules(this.domAlert);
    if (alertObj) {
      alertObj.message = message;
      this.chart.dataProvider.addAlert(alertObj);
      this._win.closePopup();
    }
  }

  // TODO move to saveHandler
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
