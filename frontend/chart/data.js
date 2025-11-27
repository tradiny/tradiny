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

export class DataHandler {
  constructor(chart) {
    this.chart = chart;
  }

  configureSeries(i) {
    const getDataKeyWithHeight = (dataKey) => {
      if (this.chart.yAxes[i][dataKey.yAxis].meta.height) {
        return (d) =>
          d[dataKey.dataKey] *
          (this.chart.yAxes[i][dataKey.yAxis].meta.height / 100);
      } else {
        return (d) => d[dataKey.dataKey];
      }
    };
    const getDataKey = (dataKey) => {
      return (d) => (d ? d[dataKey.dataKey] : d);
    };
    const pane = this.chart.panes[i];

    const series = [];
    for (let j = pane.metadata.length - 1; j >= 0; j--) {
      const metadata = pane.metadata[j];

      const findDataKey = (dataKeys, key) => {
        for (let k = 0; k < dataKeys.length; k++) {
          if (dataKeys[k].key === key) {
            return (d) => {
              return d[dataKeys[k].dataKey];
            };
          }
        }
      };
      const decorateSvgFill = (metadata) => {
        let color;
        if (metadata.color.bullish && metadata.color.bearish) {
          color = (d) => {
            if (d[metadata.color.open] < d[metadata.color.close]) {
              return metadata.color.bullish;
            } else {
              return metadata.color.bearish;
            }
          };
        } else {
          color = (d) => metadata.color.color;
        }
        return (sel) => {
          sel.attr("stroke", (d) => color(d)).attr("fill", (d) => color(d));
        };
      };
      const decorateWebglFill = (metadata) => {
        let color;
        if (metadata.color.bullish && metadata.color.bearish) {
          const bullishColor = Utils.webglColor(metadata.color.bullish);
          const bearishColor = Utils.webglColor(metadata.color.bearish);
          color = (d) => {
            if (d[metadata.color.open] < d[metadata.color.close]) {
              return bullishColor;
            } else {
              return bearishColor;
            }
          };
        } else {
          const c = Utils.webglColor(metadata.color.color);
          color = (d) => c;
        }
        return (program) => {
          fc.webglFillColor().data(this.chart.dataProvider.data).value(color)(
            program,
          );
        };
      };
      const decorateWebglStroke = (metadata) => {
        const color = Utils.webglColor(metadata.color);
        return (program) => {
          fc
            .webglStrokeColor()
            .data(this.chart.dataProvider.data)
            .value((d) => color)(program);
        };
      };
      const decorateSvgStroke = (metadata) => {
        const color = metadata.color;
        return (sel) => {
          sel.attr("stroke", color);
        };
      };

      let dataKey;
      switch (metadata.type) {
        case "candlestick":
          if (this.chart.type === "webgl") {
            metadata.series = fc.seriesWebglCandlestick();
          } else if (this.chart.type === "svg") {
            metadata.series = fc.seriesSvgCandlestick();
          }
          metadata.series
            .openValue(findDataKey(metadata.dataKeys, "open"))
            .highValue(findDataKey(metadata.dataKeys, "high"))
            .lowValue(findDataKey(metadata.dataKeys, "low"))
            .closeValue(findDataKey(metadata.dataKeys, "close"));

          if (this.chart.type === "webgl") {
            metadata.series.decorate(
              decorateWebglFill(
                metadata,
                findDataKey(metadata.dataKeys, "open"),
                findDataKey(metadata.dataKeys, "close"),
              ),
            );
          } else if (this.chart.type === "svg") {
            metadata.series.decorate(
              decorateSvgFill(
                metadata,
                findDataKey(metadata.dataKeys, "open"),
                findDataKey(metadata.dataKeys, "close"),
              ),
            );
          }

          dataKey = metadata.dataKeys[0];
          metadata.series.yScale(this.chart.yAxes[i][dataKey.yAxis].scale);
          metadata.series.yScale = () => {};
          series.push(metadata.series);
          break;

        case "bar":
          dataKey = metadata.dataKeys[0];

          if (this.chart.type === "webgl") {
            metadata.series = fc.seriesWebglBar();
          } else if (this.chart.type === "svg") {
            metadata.series = fc.seriesSvgBar();
          }
          metadata.series
            .crossValue((d) => {
              if (d && d.date) {
                return d.date;
              }
            })
            .mainValue((d) => getDataKey(dataKey)(d));

          if (this.chart.type === "webgl") {
            metadata.series.decorate(
              decorateWebglFill(
                metadata,
                findDataKey(metadata.dataKeys, "open"),
                findDataKey(metadata.dataKeys, "close"),
              ),
            );
          } else if (this.chart.type === "svg") {
            metadata.series.decorate(
              decorateSvgFill(
                metadata,
                findDataKey(metadata.dataKeys, "open"),
                findDataKey(metadata.dataKeys, "close"),
              ),
            );
          }
          metadata.series.yScale(this.chart.yAxes[i][dataKey.yAxis].scale);
          metadata.series.yScale = () => {};
          series.push(metadata.series);
          break;

        case "line":
          dataKey = metadata.dataKeys[0];

          if (this.chart.type === "webgl") {
            metadata.series = fc.seriesWebglLine();
          } else if (this.chart.type === "svg") {
            metadata.series = fc.seriesSvgLine();
          }
          metadata.series
            .crossValue((d) => {
              if (d && d.date) {
                return d.date;
              }
            })
            .mainValue((d) => getDataKey(dataKey)(d));

          if (this.chart.type === "webgl") {
            metadata.series.decorate(decorateWebglStroke(metadata));
          } else if (this.chart.type === "svg") {
            metadata.series.decorate(decorateSvgStroke(metadata));
          }
          metadata.series.yScale(this.chart.yAxes[i][dataKey.yAxis].scale);
          metadata.series.yScale = () => {};
          series.push(metadata.series);
          break;
      }
    }
    this.chart.series = series;
  }

  onData(dataKeys, addedFromLeft, addedFromRight, shift, newKeys = false) {
    // console.log(`updated keys ${JSON.stringify(dataKeys)}, added from left ${addedFromLeft}, added from right ${addedFromRight}, shift=${shift}`)
    const currentDomain = this.chart.xScale.domain();
    if (addedFromRight === 1) {
      // maintain the position of last data point on screen (shift=1) if the last data point is visible
      const idx = Math.ceil(currentDomain[1]);
      if (this.chart.dataProvider.data.length - 1 <= idx) {
        shift = 1;
      }
    }
    if (shift) {
      this.chart.xScale.domain([
        currentDomain[0] + shift,
        currentDomain[1] + shift,
      ]);
      this.chart.drawingHandler.shift(shift); // TODO check if needed
    }

    if (
      (this.chart.dataProvider.dataCount > 1 &&
        (addedFromRight > 0 || addedFromLeft > 0)) ||
      addedFromLeft > 0 // this handles also the case when a new indicator is added so addedFromLeft is > 0
    ) {
      this.chart.cacheHandler.buildCaches(
        null,
        addedFromLeft,
        addedFromRight,
        shift,
      ); // rebuild all
    } else {
      // The following code works only if the data has the same X-axis; otherwise, the cache needs to be fully rebuilt.
      // Therefore, it makes sense only when dataCount === 1.
      // TODO: This might be detected in the dataProvider in the future, and a new argument could be passed to this function
      // to fully rebuild the cache in such cases.

      if (addedFromLeft === undefined && addedFromRight === undefined) {
        this.chart.cacheHandler.buildCaches(
          dataKeys,
          addedFromLeft,
          addedFromRight,
          shift,
        ); // rebuild all
      } else {
        this.chart.cacheHandler.buildCachesPartial(
          dataKeys,
          addedFromLeft,
          addedFromRight,
          shift,
        );
      }
    }

    if (newKeys) {
      this.chart.DOMHandler.calculateTemplateGrid(this.chart.paneHeights);
      this.chart.DOMHandler.gridSizesUpdated();
      this.chart.DOMHandler.gridUpdated();
      this.chart.renderHandler.render();
    } else {
      this.chart.renderHandler.render([
        this.chart.R.DATA,
        this.chart.R.Y_DOMAIN,
        this.chart.R.Y_LABEL,
      ]);
    }
  }
}
