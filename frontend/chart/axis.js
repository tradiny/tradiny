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
import { CustomTickDateFormatter } from "./customtickformatter.js";

export class AxisHandler {
  constructor(chart) {
    this.chart = chart;
  }

  configureXAxis() {
    this.chart.xAxisEl = this.chart.d3ContainerEl
      .append("div")
      .attr("class", "x-axis interactive")
      .style("grid-column", this.chart.xAxisGridPosition[0])
      .style("grid-row", this.chart.xAxisGridPosition[1]);

    let xExtent;
    if (
      this.chart.initialZoom &&
      this.chart.initialZoom.start &&
      this.chart.initialZoom.end
    ) {
      xExtent = [
        this.chart.dataProvider.dateToIndexMap.get(
          this.chart.initialZoom.start,
        ),
        this.chart.dataProvider.dateToIndexMap.get(this.chart.initialZoom.end),
      ];
    } else {
      xExtent = [
        Math.max(
          0,
          this.chart.dataProvider.data.length - this.chart.visiblePoints,
        ),
        this.chart.dataProvider.data.length - 1,
      ];
      const displayWidth = this.chart.paneWidth;
      const unitsPerPixel = (xExtent[1] - xExtent[0]) / displayWidth;
      const paddingUnits = unitsPerPixel * this.chart.paddingPixels;
      xExtent[1] += paddingUnits;
    }
    this.chart.xScale = d3
      .scaleLinear()
      .domain(xExtent)
      .range([0, this.chart.paneWidth]);
    this.chart.xAxis = fc.axisBottom(this.chart.xScale);

    this.chart.xAxisSvg = this.chart.xAxisEl
      .append("svg")
      .attr("width", this.chart.paneWidth)
      .attr("height", this.chart.xAxisHeight);

    this.chart.xAxisSvg.style("font-size", `${this.chart.fontSize}px`);

    this.chart.customTickDateFormater = new CustomTickDateFormatter(
      this.chart.xAxis,
      0, // timezone
      this.chart.dataProvider,
      this.chart.dataProvider.interval,
      [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
      ],
      ["Sun", "Mon", "Tue", "Wen", "Thu", "Fri", "Sat"],
      undefined,
      (text) => {
        return Utils.getTextWidth(text, `${this.chart.fontSize}px sans-serif`);
      },
    );
    this.chart.xAxis
      .ticks(this.getXTicks(this.chart.paneWidth))
      .tickFormat(this.chart.customTickDateFormater.datumFormat);
  }

  configureYAxes(i) {
    const pane = this.chart.panes[i];
    this.chart.firstAxisKey[i] = pane.yAxes[0].key;
    this.chart.yAxes[i] = {};
    this.chart.yAxesSvg[i] = {};

    for (let j = 0; j < pane.yAxes.length; j++) {
      const yAxis = pane.yAxes[j];

      let scale;
      if (yAxis.type === "linear") {
        scale = d3.scaleLinear();
      }
      if (yAxis.type === "log") {
        scale = d3.scaleLog();
      }

      this.chart.yAxes[i][yAxis.key] = {
        meta: yAxis,
        scale: scale,
        axis:
          yAxis.orient === "right" ? d3.axisRight(scale) : d3.axisLeft(scale),
      };

      this.chart.yAxes[i][yAxis.key].axis.ticks(
        this.getYTicks(this.chart.paneHeights[i]),
      );

      if (yAxis.tickFormat === "si") {
        const tick3s = d3.format(".3s");
        const fmt = (key) => (d, i, a) => {
          return tick3s(
            this.chart.dataProvider.preciseMultiply(
              d,
              this.chart.yAxesDivision[key],
            ),
          );
        };
        this.chart.yAxes[i][yAxis.key].axis.tickFormat(fmt(yAxis.key));
      } else {
        const fmt = (key) => (d, i, a) => {
          return Utils.formatFloat(
            this.chart.dataProvider.preciseMultiply(
              d,
              this.chart.yAxesDivision[key],
            ),
            this.chart.yAxesPrecision[key],
          );
        };
        yAxis.tickFormat = fmt(yAxis.key);
        this.chart.yAxes[i][yAxis.key].axis.tickFormat(yAxis.tickFormat);
      }

      if (!yAxis.dynamic) {
        const domain = this.chart.renderHandler.dynamicYAxisDomain(
          i,
          pane.metadata,
          [0, this.chart.dataProvider.data.length],
          this.chart.yAxes[i][yAxis.key],
        );
        if (domain) {
          scale.domain(domain);
        }
      }
    }

    Object.keys(this.chart.yAxes[i]).forEach((key, j) => {
      const yAxis = this.chart.yAxes[i][key];

      const yAxisEl = this.chart.d3ContainerEl
        .append("div")
        .attr(
          "class",
          `y-axis y-axis-${Utils.toAlphanumeric(yAxis.meta.key)} y-axis-${Utils.toAlphanumeric(this.chart.panes[i].name)}-${Utils.toAlphanumeric(yAxis.meta.key)} ` +
            (this.chart.firstAxisKey[i] === key ? "interactive" : ""),
        )
        .style("color", yAxis.meta.color)

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
      const svg = yAxisEl.append("svg");
      if (w) {
        svg.attr("width", w);
      }

      svg.style("font-size", `${this.chart.fontSize}px`);

      this.chart.yAxesSvg[i][key] = svg;
    });
  }

  getXTicks(w) {
    return Math.floor(Math.max(w / 80, 2));
  }
  getYTicks(h) {
    return Math.floor(Math.max(h / 80, 3));
  }

  addXLabel(svg, mousePosition) {
    if (mousePosition.position) {
      const text = this.chart.customTickDateFormater
        .datumFormat(
          Math.round(this.chart.xScale.invert(mousePosition.position.x)),
          0,
          [null],
        )
        .trim();
      if (!text) {
        if (this.chart.xAxisLabel) {
          for (const key of Object.keys(this.chart.xAxisLabel)) {
            if (this.chart.xAxisLabel[key].remove) {
              this.chart.xAxisLabel[key].remove();
            }
          }
          delete this.chart.xAxisLabel;
        }
        return;
      }
      const margin = 8;

      if (this.chart.xAxisLabel) {
        const parent = this.chart.xAxisLabel.g.node().parentNode;
        if (
          parent &&
          this.chart.xAxisLabel.g.node() !== parent.lastElementChild
        ) {
          for (const key of Object.keys(this.chart.xAxisLabel)) {
            if (this.chart.xAxisLabel[key].remove) {
              this.chart.xAxisLabel[key].remove();
            }
          }
          delete this.chart.xAxisLabel;
        }
      }
      if (!this.chart.xAxisLabel) {
        const w = Math.round(
          Utils.getTextWidth(text, `${this.chart.fontSize}px sans-serif`),
        );
        const h = this.chart.textHeight + 3;
        this.chart.xAxisLabel = {
          g: svg.append("g").attr("class", "label"),
          w: w,
        };
        this.chart.xAxisLabel.bg = this.chart.xAxisLabel.g
          .append("rect")
          .attr("class", "bg")
          .attr("width", w)
          .attr("height", h)
          .attr("transform", `translate(0, 0)`);
        this.chart.xAxisLabel.text = this.chart.xAxisLabel.g
          .append("text")
          .attr("class", "text")
          .attr("text-anchor", "middle")
          .attr("x", w / 2)
          .attr("y", h / 2 + 5);
      }

      this.chart.xAxisLabel.g.attr(
        "transform",
        `translate(${
          mousePosition.position.x - Math.floor(this.chart.xAxisLabel.w / 2)
        }, ${margin})`,
      );
      this.chart.xAxisLabel.text.text(text);
    } else if (this.chart.xAxisLabel) {
      for (const key of Object.keys(this.chart.xAxisLabel)) {
        if (this.chart.xAxisLabel[key].remove) {
          this.chart.xAxisLabel[key].remove();
        }
      }
      delete this.chart.xAxisLabel;
    }
  }

  addYLabels(i, yAxis, svg, mousePosition) {
    const pane = this.chart.panes[i];
    for (let k = 0; k < pane.metadata.length; k++) {
      for (let l = 0; l < pane.metadata[k].dataKeys.length; l++) {
        const key = pane.metadata[k].dataKeys[l];
        if (!key.label) {
          continue;
        }

        const dataKey = key.dataKey;

        const lastDataPoint =
          this.chart.dataProvider.data[this.chart.dataProvider.data.length - 1];
        if (!lastDataPoint) {
          continue;
        }
        const val = lastDataPoint[dataKey];
        if (!val) {
          continue;
        }
        let valFormatted = this.yAxisFormat(yAxis.meta.tickFormat, val);

        if (yAxis.meta.key === key.yAxis) {
          if (!yAxis.labelLast) {
            yAxis.labelLast = {};
          }

          if (yAxis.labelLast[dataKey]) {
            const parent = yAxis.labelLast[dataKey].g.node().parentNode;
            const children = parent.children;
            if (
              parent &&
              yAxis.labelLast[dataKey].g.node() !== parent.lastElementChild &&
              children.length >= 2 &&
              yAxis.labelLast[dataKey].g.node() !==
                children[children.length - 2]
            ) {
              for (const key of Object.keys(yAxis.labelLast[dataKey])) {
                yAxis.labelLast[dataKey][key].remove();
              }
              delete yAxis.labelLast[dataKey];
            }
          }

          if (!yAxis.labelLast[dataKey]) {
            yAxis.labelLast[dataKey] = {
              g: svg
                .append("g")
                .attr(
                  "class",
                  `label-last label-last-${Utils.toAlphanumeric(yAxis.meta.key)} label-last-${Utils.toAlphanumeric(dataKey)}`,
                ),
            };
            yAxis.labelLast[dataKey].bg = yAxis.labelLast[dataKey].g
              .append("rect")
              .attr("class", "bg");
            yAxis.labelLast[dataKey].text = yAxis.labelLast[dataKey].g
              .append("text")
              .attr("class", "text");
            const margin = 9;

            if (yAxis.meta.orient === "right") {
              yAxis.labelLast[dataKey].text.attr(
                "transform",
                `translate(${margin}, ${this.chart.textHeight + 3})`,
              );
            }
            if (yAxis.meta.orient === "left") {
              const column = yAxis.meta.gridPosition[0] - 1; // -1 for controls
              const w = this.chart.yAxesWidths[0][column - 1];

              yAxis.labelLast[dataKey].text.attr(
                "transform",
                `translate(${w - margin}, ${this.chart.textHeight + 3})`,
              );
            }
          }

          const _color = (meta) => {
            return (d) => {
              if (meta.bullish && meta.bearish) {
                if (d[meta.open] < d[meta.close]) {
                  return meta.bullish;
                } else {
                  return meta.bearish;
                }
              } else {
                return meta.color;
              }
            };
          };

          yAxis.labelLast[dataKey].bg.attr(
            "fill",
            _color(key.labelBg)(lastDataPoint),
          );
          yAxis.labelLast[dataKey].text.attr(
            "fill",
            _color(key.labelColor)(lastDataPoint),
          );

          if (yAxis.meta.orient === "right") {
            yAxis.labelLast[dataKey].g.attr(
              "transform",
              `translate(0, ${
                yAxis.scale(val) - Math.floor(this.chart.textHeight / 2)
              })`,
            );

            // let valFormatted;
            // const formatter = yAxis.meta.tickFormat;
            // if (formatter === 'si') {
            //     valFormatted = d3.format(".3s")(val)
            // } else {
            //     valFormatted = formatter(val);
            // }

            yAxis.labelLast[dataKey].text.text(valFormatted);
          }
          if (yAxis.meta.orient === "left") {
            const column = yAxis.meta.gridPosition[0] - 1; // -1 for controls
            const w = this.chart.yAxesWidths[0][column - 1];

            yAxis.labelLast[dataKey].g.attr(
              "transform",
              `translate(-${w}, ${
                yAxis.scale(val) - Math.floor(this.chart.textHeight / 2)
              })`,
            );
            yAxis.labelLast[dataKey].text.text(valFormatted);
          }
        }
      }
    }

    // update labels
    if (mousePosition.position && mousePosition.i == i) {
      if (yAxis.label) {
        const parent = yAxis.label.g.node().parentNode;
        if (parent && yAxis.label.g.node() !== parent.lastElementChild) {
          for (const key of Object.keys(yAxis.label)) {
            yAxis.label[key].remove();
          }
          delete yAxis.label;
        }
      }
      if (!yAxis.label) {
        yAxis.label = {
          g: svg.append("g").attr("class", "label"),
        };
        yAxis.label.bg = yAxis.label.g.append("rect").attr("class", "bg");
        yAxis.label.text = yAxis.label.g.append("text").attr("class", "text");
        const margin = 9;

        if (yAxis.meta.orient === "right") {
          yAxis.label.text.attr(
            "transform",
            `translate(${margin}, ${this.chart.textHeight + 3})`,
          );
        }
        if (yAxis.meta.orient === "left") {
          const column = yAxis.meta.gridPosition[0] - 1; // -1 for controls
          const w = this.chart.yAxesWidths[0][column - 1];

          yAxis.label.text.attr(
            "transform",
            `translate(${w - margin}, ${this.chart.textHeight + 3})`,
          );
        }
      }

      if (yAxis.meta.orient === "right") {
        yAxis.label.g.attr(
          "transform",
          `translate(0, ${
            mousePosition.position.y - Math.floor(this.chart.textHeight / 2) - 3
          })`,
        );

        yAxis.label.text.text(
          this.yAxisFormat(
            yAxis.meta.tickFormat,
            yAxis.scale.invert(mousePosition.position.y),
          ),
        );
      }
      if (yAxis.meta.orient === "left") {
        const column = yAxis.meta.gridPosition[0] - 1; // -1 for controls
        const w = this.chart.yAxesWidths[0][column - 1];

        yAxis.label.g.attr(
          "transform",
          `translate(-${w}, ${
            mousePosition.position.y - Math.floor(this.chart.textHeight / 2) - 3
          })`,
        );
        yAxis.label.text.text(
          this.yAxisFormat(
            yAxis.meta.tickFormat,
            yAxis.scale.invert(mousePosition.position.y),
          ),
        );
      }
    } else if (yAxis.label) {
      for (const key of Object.keys(yAxis.label)) {
        yAxis.label[key].remove();
      }
      delete yAxis.label;
    }
  }

  yAxisFormat(formatter, value) {
    let valFormatted;
    if (formatter === "si") {
      valFormatted = d3.format(".3s")(value);
    } else {
      valFormatted = formatter(value);
    }
    return valFormatted;
  }
}
