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

import { ColorPicker } from "../colorpicker.js";
import { Renderer } from "../renderer.js";
import { PopupWindow } from "../window.js";
import { Utils } from "./utils.js";

export class DrawingHandler {
  static fibs = [
    { v: 0, c: "#338e3f" },
    { v: 0.236, c: "#4c984d" },
    { v: 0.382, c: "#a5bc47" },
    { v: 0.5, c: "#f5cd30" },
    { v: 0.618, c: "#efb83a" },
    { v: 0.786, c: "#e29b41" },
    { v: 0.886, c: "#ce6023" },
    { v: 1.0, c: "#c5291d" },
    { v: 1.272, c: "#ce6023" },
    { v: 1.414, c: "#e29b41" },
    { v: 1.618, c: "#efb83a" },
    { v: 2.0, c: "#f5cd30" },
    { v: 2.24, c: "#a5bc47" },
    { v: 2.618, c: "#4c984d" },
    { v: 3.618, c: "#338e3f" },
    { v: 4.236, c: "#338e3f" },
  ];

  constructor(chart) {
    this.chart = chart;

    this.active = false;
    this.activeColor = "#00ffff";
    this.activeWidth = 2;
    this.activeText = null;
    this.activeTool = null;
    this.lineId = 0;

    this.renderLine = d3
      .line()
      .x((d) => {
        return d[0];
      })
      .y((d) => {
        return d[1];
      })
      .curve(d3.curveLinear);

    this.boundHandleKeyDown = this.handleKeyDown.bind(this);
    document.addEventListener("keydown", this.boundHandleKeyDown);
  }

  handleKeyDown(event) {
    if (event.key === "Escape" && this.active) {
      this._toggle(this.activeTool);
    }
  }

  rulerLabels(i, xScale, yScale) {
    const that = this;
    return [
      {
        // left date
        coordinates: (d) => {
          if (d.line.points.length < 2) {
            return [0, 0];
          }
          const xShift = xScale(0) + d.bbox.width / 2;
          let yShift =
            (d.line.points[1][1] - d.line.points[3][1]) / 2 -
            yScale.invert(yScale(0) + d.bbox.height / 2);
          const p = d.line.points[0];
          return [p[0] - xScale.invert(xShift), p[1] - yShift];
        },
        text: (d) => {
          let text;
          if (d.line.points.length) {
            const x = d.line.points[0][0];

            text = that.chart.customTickDateFormater
              .datumFormat(Math.round(x), 0, [null])
              .trim();
          }
          return text ? text : "";
        },
      },
      {
        // right date
        coordinates: (d) => {
          if (d.line.points.length < 2) {
            return [0, 0];
          }
          const xShift = xScale(0) + d.bbox.width / 2;
          let yShift =
            (d.line.points[1][1] - d.line.points[3][1]) / 2 -
            yScale.invert(yScale(0) + d.bbox.height / 2);
          const p = d.line.points[1];
          return [p[0] - xScale.invert(xShift), p[1] - yShift];
        },
        text: (d) => {
          if (d.line.points.length >= 2) {
            const xPrev = Math.round(d.line.points[0][0]);
            const x = Math.round(d.line.points[1][0]);
            if (
              that.chart.dataProvider.data[xPrev] &&
              that.chart.dataProvider.data[x]
            ) {
              const xPrevDate = that.chart.dataProvider.data[xPrev]._dateObj;
              const xDate = that.chart.dataProvider.data[x]._dateObj;

              const diff = Utils.secondsToDhms(
                Math.abs((xPrevDate - xDate) / 1000),
              );

              const text = that.chart.customTickDateFormater
                .datumFormat(Math.round(x), 1, [xPrev, x])
                .trim();
              return `${text} (${diff})`;
            }
          }
          return "";
        },
      },
      {
        // from value
        coordinates: (d) => {
          if (d.line.points.length < 2) {
            return [0, 0];
          }
          const xShift =
            (d.line.points[1][0] - d.line.points[0][0]) / 2 -
            xScale.invert(xScale(0) + d.bbox.width / 2);
          const yShift =
            d.line.points[0][1] > d.line.points[3][1]
              ? yScale.invert(yScale(0) + d.bbox.height / 2)
              : 0;
          const p = d.line.points[0];

          return [p[0] + xShift, p[1] + yShift];
        },
        text: (d) => {
          if (d.line.points.length < 2) {
            return "";
          }
          const division = that.chart.yAxesDivision[that.chart.firstAxisKey[i]];
          const precision =
            that.chart.yAxesPrecision[that.chart.firstAxisKey[i]];
          const value = this.chart.dataProvider.preciseMultiply(
            d.line.points[1][1],
            division,
          );
          return Utils.formatFloat(value, precision);
        },
      },
      {
        // to value
        coordinates: (d) => {
          if (d.line.points.length < 2) {
            return [0, 0];
          }
          const p = d.line.points[3];
          const xShift =
            (d.line.points[1][0] - d.line.points[0][0]) / 2 -
            xScale.invert(xScale(0) + d.bbox.width / 2);
          const yShift =
            d.line.points[0][1] < d.line.points[3][1]
              ? yScale.invert(yScale(0) + d.bbox.height / 2)
              : 0;
          return [p[0] + xShift, p[1] + yShift];
        },
        text: (d) => {
          if (d.line.points.length < 2) {
            return "";
          }
          const division = that.chart.yAxesDivision[that.chart.firstAxisKey[i]];
          const precision =
            that.chart.yAxesPrecision[that.chart.firstAxisKey[i]];
          const value = this.chart.dataProvider.preciseMultiply(
            d.line.points[2][1],
            division,
          );

          const xPrev = this.chart.dataProvider.preciseMultiply(
            d.line.points[0][1],
            division,
          );
          const x = value;

          const diff = Utils.formatFloat(Math.abs(xPrev - x), precision);
          const diffpercent = Utils.formatFloat(Utils.getChange(xPrev, x), 2);

          const text = Utils.formatFloat(value, precision);

          return `${text} (${diffpercent}%, ${xPrev - x < 0 ? "+" : "-"}${diff})`;
        },
      },
    ];
  }

  fibLabels(i, xScale, yScale) {
    return [
      {
        coordinates: (d) => {
          const p = d.line.points[0];
          return [p[0], p[1] + yScale.invert(yScale(0) + d.bbox.height / 2)];
        },
        text: (d) => {
          return d.line.fib.v;
        },
      },
    ];
  }

  textLabels(i, xScale, yScale) {
    return [
      {
        coordinates: (d) => {
          const p = d.line.points[0];
          return p;
        },
        text: (d) => {
          return d.line.text;
        },
        color: (d) => {
          return d.line.color;
        },
        fontSize: (d) => {
          return `${d.line.size}pt`;
        },
      },
    ];
  }

  create(i) {
    if (!this.chart.drawingData[i]) {
      this.chart.drawingData[i] = {
        lines: [],
      };
    }

    this.chart.drawingCanvases[i] = this.chart.d3ChartSvgEls[i]
      .append("g")
      .attr("class", "drawing")
      .attr("pointer-events", "all")
      .style("cursor", "crosshair")
      .style("touch-action", "none");

    this.chart.drawingCanvases[i]
      .append("rect")
      // .attr('width', this.chart.paneWidth)
      // .attr('height', this.chart.paneHeights[i])
      .attr("width", 1920 * 2)
      .attr("height", 1080 * 2)
      .attr("fill", "none")
      .attr("pointer-events", "all")
      .style("touch-action", "none");
  }

  disableInteractions(i) {
    if (this.chart.drawingCanvases[i]) {
      this.chart.drawingCanvases[i].on("drag", null);
      this.chart.drawingCanvases[i].on("click", null);
      this.chart.drawingCanvases[i].on("mousemove", null);
    }
  }

  enableInteractions(i) {
    const that = this;

    const xScale = this.chart.xScale;
    const yScale = this.chart.yAxes[i][this.chart.firstAxisKey[i]].scale;

    const rm = (i, linesToRemove) => {
      return () => {
        for (let j = 0; j < linesToRemove.length; j++) {
          const _lines = this.chart.drawingData[i].lines;
          const index = _lines.indexOf(linesToRemove[j]);
          if (index > -1) {
            // only splice array when item is found
            _lines.splice(index, 1); // 2nd parameter means remove one item only
          }
        }
        this._redraw(i, null);
      };
    };

    this.chart.drawingDrags[i] = d3
      .drag()
      .on("start", () => {
        if (this.activeTool === "brush") {
          this.activeLine = {
            type: "brush",
            i,
            id: this.lineId++,
            points: [],
            color: this.activeColor,
            width: this.activeWidth,
            labels: [],
            movePoints: false,
            move: true,
          };
          this.chart.drawingData[i].lines.push(this.activeLine);
          this.chart.history.push({ remove: rm(i, [this.activeLine]) });
          return this._redraw(i, this.activeLine);
        }
      })
      .on("drag", function (event) {
        if (that.activeTool === "brush") {
          let coordinates;
          if (event.sourceEvent.touches && event.sourceEvent.touches.length) {
            coordinates = d3.pointer(event.sourceEvent.touches[0], this);
          } else {
            coordinates = d3.pointer(event, this);
          }
          coordinates = [
            that.chart.xScale.invert(coordinates[0]),
            that.chart.yAxes[i][that.chart.firstAxisKey[i]].scale.invert(
              coordinates[1],
            ),
          ];
          that.activeLine.points.push(coordinates);
          return that._redraw(i, that.activeLine);
        }
      })
      .on("end", () => {
        if (this.activeTool === "brush") {
          if (this.activeLine.points.length === 0) {
            this.chart.drawingData[i].lines.pop();
          }
          this.activeLine = null;
        }
      });

    this.chart.drawingCanvases[i]
      .on("click", function (event, d) {
        let coordinates = d3.pointer(event, this);
        coordinates = [
          that.chart.xScale.invert(coordinates[0]),
          that.chart.yAxes[i][that.chart.firstAxisKey[i]].scale.invert(
            coordinates[1],
          ),
        ];

        if (["horizontal-line"].includes(that.activeTool)) {
          const line = {
            type: "horizontal-line",
            i,
            id: that.lineId++,
            points: [
              [-1000000, coordinates[1]],
              [1000000, coordinates[1]],
            ],
            color: that.activeColor,
            width: that.activeWidth,
            labels: [],
            movePoints: false,
            move: true,
          };
          that.chart.drawingData[i].lines.push(line);
          that.chart.history.push({ remove: rm(i, [line]) });
          return that._redraw(i, line);
        }
        if (["vertical-line"].includes(that.activeTool)) {
          const line = {
            type: "vertical-line",
            i,
            id: that.lineId++,
            points: [
              [coordinates[0], -1000000],
              [coordinates[0], 1000000],
            ],
            color: that.activeColor,
            width: that.activeWidth,
            labels: [],
            movePoints: false,
            move: true,
          };
          that.chart.drawingData[i].lines.push(line);
          that.chart.history.push({ remove: rm(i, [line]) });
          return that._redraw(i, line);
        }
        if (["line"].includes(that.activeTool)) {
          if (!that.activeLine) {
            that.activeLine = {
              type: "line",
              i,
              id: that.lineId++,
              points: [coordinates],
              color: that.activeColor,
              width: that.activeWidth,
              labels: [],
              movePoints: true,
              move: true,
            };
            that.chart.drawingData[i].lines.push(that.activeLine);
            that.chart.history.push({ remove: rm(i, [that.activeLine]) });
          } else {
            that.activeLine.points[1] = coordinates;

            if (that.activeLine.points.length === 0) {
              that.chart.drawingData[i].lines.pop();
            }
            that.activeLine = null;
          }
        }
        if (["ruler"].includes(that.activeTool)) {
          if (!that.activeLine) {
            that.activeLine = {
              type: "ruler",
              i,
              id: that.lineId++,
              points: [coordinates],
              color: "#888888",
              width: that.activeWidth,
              fill: "#888888",
              opacity: 0.5,
              labels: that.rulerLabels(i, xScale, yScale),
              movePoints: false,
              move: true,
            };
            that.chart.drawingData[i].lines.push(that.activeLine);

            that.chart.history.push({ remove: rm(i, [that.activeLine]) });
          } else {
            const p1 = that.activeLine.points[0];
            const p2 = coordinates;
            that.activeLine.points[1] = [p2[0], p1[1]];
            that.activeLine.points[2] = [p2[0], p2[1]];
            that.activeLine.points[3] = [p1[0], p2[1]];
            that.activeLine.points[4] = [p1[0], p1[1]];

            if (that.activeLine.points.length === 0) {
              that.chart.drawingData[i].lines.pop();
            }
            that.activeLine = null;
          }
        }

        if (["fib"].includes(that.activeTool)) {
          if (!that.activeLines) {
            that.initialPoint = coordinates;
            that.activeLines = [];
            for (let j = 0; j < DrawingHandler.fibs.length; j++) {
              const f = DrawingHandler.fibs[j];
              that.activeLines[j] = {
                type: "fib",
                i,
                id: that.lineId++,
                points: [
                  [0, 0],
                  [0, 0],
                ],
                color: f.c,
                width: 1,
                fill: f.c,
                opacity: 1,
                fib: f,
                labels: that.fibLabels(i, xScale, yScale),
                movePoints: false,
                move: false,
              };
              that.chart.drawingData[i].lines.push(that.activeLines[j]);
            }
            that.chart.history.push({ remove: rm(i, that.activeLines) });
            return that._redraw(i, that.activeLines);
          } else {
            that.initialPoint = null;
            that.activeLines = null;
          }
        }
        if (["text"].includes(that.activeTool)) {
          const w = Math.round(
            Utils.getTextWidth(
              that.activeText,
              `${that.activeWidth}px sans-serif`,
            ),
          );
          const h = Math.round(
            Utils.getTextHeight(
              that.activeText,
              `${that.activeWidth}px sans-serif`,
            ),
          );
          const line = JSON.parse(
            JSON.stringify({
              type: "text",
              text: that.activeText,
              color: that.activeColor,
              size: that.activeWidth,
              i,
              id: that.lineId++,
              points: [
                coordinates,
                [coordinates[0] + w, coordinates[1]],
                [coordinates[0] + w, coordinates[1] + h],
                [coordinates[0], coordinates[1] + h],
                coordinates,
              ],
              width: 10,
              opacity: 0.01,
              movePoints: false,
              move: true,
            }),
          );
          line.labels = that.textLabels(i, xScale, yScale);

          that.chart.drawingData[i].lines.push(line);
          that.chart.history.push({ remove: rm(i, [line]) });
          that._redraw(i, line);

          that.activeWidth = 1; // revert
          that.activeText = null; // revert
          return that._toggle("text");
        }
        return that._redraw(i, that.activeLine);
      })
      .on("mousemove", function (event, d) {
        let coordinates = d3.pointer(event, this);
        coordinates = [
          that.chart.xScale.invert(coordinates[0]),
          that.chart.yAxes[i][that.chart.firstAxisKey[i]].scale.invert(
            coordinates[1],
          ),
        ];
        if (that.activeLine && ["line"].includes(that.activeTool)) {
          that.activeLine.points[1] = coordinates;
        }
        if (that.activeLine && ["ruler"].includes(that.activeTool)) {
          const p1 = that.activeLine.points[0];
          const p2 = coordinates;
          that.activeLine.points[1] = [p2[0], p1[1]];
          that.activeLine.points[2] = [p2[0], p2[1]];
          that.activeLine.points[3] = [p1[0], p2[1]];
          that.activeLine.points[4] = [p1[0], p1[1]];
        }

        if (
          that.initialPoint &&
          that.activeLines &&
          ["fib"].includes(that.activeTool)
        ) {
          const x =
            that.initialPoint[0] < coordinates[0]
              ? that.initialPoint[0]
              : coordinates[0];
          const diff = coordinates[1] - that.initialPoint[1];

          for (let j = 0; j < DrawingHandler.fibs.length; j++) {
            const f = DrawingHandler.fibs[j];
            const val = coordinates[1] - f.v * diff;
            that.activeLines[j].points[0] = [x, val];
            that.activeLines[j].points[1] = [1000000, val];
          }

          return that._redraw(i, that.activeLines);
        }
        return that._redraw(i, that.activeLine);
      });
  }

  toggle(tool) {
    if (this.activeTool === tool) {
      return this._toggle(this.activeTool);
    }
    if (this.active) {
      // first disable, then activate `tool`
      this._toggle(this.activeTool);
    }

    if (["ruler", "fib"].includes(tool)) {
      this._toggle(tool);
    }

    if (["text"].includes(tool)) {
      new Renderer().render(
        "text",
        { self: this, title: "Settings", tool },
        (content) => {
          this._win = new PopupWindow(this.chart.elementId, 350);
          this._win.render(content);

          const that = this;
          this.chart.d3ContainerEl
            .selectAll("div.line-color")
            .each(function (d, i) {
              const dEl = d3.select(this);
              const colorPicker = new ColorPicker(null, dEl.node(), (c) => {});
            });

          this.chart.d3ContainerEl.select("input.text").node().focus();
        },
      );
    }

    if (["line", "horizontal-line", "vertical-line", "brush"].includes(tool)) {
      new Renderer().render(
        "line",
        { self: this, title: "Settings", tool },
        (content) => {
          this._win = new PopupWindow(this.chart.elementId, 250);
          this._win.render(content);

          const that = this;
          this.chart.d3ContainerEl
            .selectAll("div.line-color")
            .each(function (d, i) {
              const dEl = d3.select(this);
              const colorPicker = new ColorPicker(null, dEl.node(), (c) => {});
            });
        },
      );
    }
  }

  _toggle(tool) {
    if (this._win) {
      try {
        this.activeColor = this.chart.d3ContainerEl
          .select("div.line-color")
          .attr("data-value");
      } catch (e) {
        this.activeColor = null;
      }
      try {
        this.activeWidth = parseInt(
          this.chart.d3ContainerEl.select("select.line-width").node().value,
        );
      } catch (e) {
        this.activeWidth = 1;
      }
      try {
        this.activeText = this.chart.d3ContainerEl
          .select("input.text")
          .node().value;
      } catch (e) {
        this.activeText = null;
      }

      this._win.closePopup();
      this._win = null;
    }

    this.active = !this.active;

    if (this.active) {
      this.activeTool = tool;
    } else {
      this.activeTool = undefined;
    }

    const icon = this.chart.controlsEl.select(`.${tool}-icon`);
    if (this.active) {
      icon.attr("class", `icon ${tool}-icon active`);

      for (let i = 0; i < this.chart.panes.length; i++) {
        this.chart.drawingCanvases[i].raise();
        this.chart.drawingCanvases[i].select("rect").raise();
      }
    } else {
      icon.attr("class", `icon ${tool}-icon`);
    }

    for (let i = 0; i < this.chart.panes.length; i++) {
      this.chart.drawingCanvases[i].call(
        this.chart.drawingDrags[i].filter(this.active),
      );
    }
  }

  setMaxId() {
    let maxId = 0;

    for (let i = 0; i < this.chart.panes.length; i++) {
      for (let j = 0; j < this.chart.drawingData[i].lines.length; j++) {
        if (this.chart.drawingData[i].lines[j].id > maxId) {
          maxId = this.chart.drawingData[i].lines[j].id;
        }
      }
    }

    this.lineId = maxId + 1;
  }

  shift(s) {
    for (let i = 0; i < this.chart.panes.length; i++) {
      for (let j = 0; j < this.chart.drawingData[i].lines.length; j++) {
        for (
          let k = 0;
          k < this.chart.drawingData[i].lines[j].points.length;
          k++
        ) {
          this.chart.drawingData[i].lines[j].points[k][0] += s;
        }
      }
    }
  }

  _redraw(i, specificLines) {
    if (!this.chart.drawingCanvases[i]) {
      // DOM not yet created
      return;
    }
    const that = this;

    const x = this.chart.xScale;
    const y = this.chart.yAxes[i][this.chart.firstAxisKey[i]].scale;

    const lines = this.chart.drawingCanvases[i]
      .selectAll(".line")
      .data(this.chart.drawingData[i].lines, (d) => d.id);

    const linesEnter = lines
      .enter()
      .append("path")
      .attr("class", "line")
      .attr("vector-effect", "non-scaling-stroke")
      .attr("stroke-width", (d) => d.width)
      .attr("stroke", (d) => d.color)
      .attr("fill", (d) => (d.fill ? d.fill : "none"))
      .attr("opacity", (d) => (d.opacity ? d.opacity : 1.0))
      .attr("stroke-opacity", (d) => (d.opacity ? d.opacity : 1.0))
      .attr("fill-opacity", (d) => (d.opacity ? d.opacity : 1.0))
      .each(function (d) {
        d.elem = d3.select(this);
      });

    const linesMerge = lines.merge(linesEnter);

    if (specificLines) {
      if (Array.isArray(specificLines)) {
        specificLines.forEach((specificLine) => {
          specificLine.elem.attr("d", (d) =>
            that.renderLine(
              d.points.map((point) => [x(point[0]), y(point[1])]),
            ),
          );
        });
      } else {
        specificLines.elem.attr("d", (d) =>
          that.renderLine(d.points.map((point) => [x(point[0]), y(point[1])])),
        );
      }
    } else {
      linesMerge.attr("d", (d) => {
        return that.renderLine(
          d.points.map((point) => [x(point[0]), y(point[1])]),
        );
      });
    }

    lines.exit().remove();

    // Adding draggable boxes
    const boxSize = 15;
    const points = this.chart.drawingCanvases[i].selectAll(".point-box").data(
      this.chart.drawingData[i].lines.flatMap((d) => {
        d.points.forEach((point) => {
          point.line = d;
        });
        return d.points;
      }),
      (d, j) => `${d[0]}-${d[1]}-${j}`,
    );

    const pointsEnter = points
      .enter()
      .append("rect")
      .attr("class", "point-box")
      .attr("width", boxSize)
      .attr("height", boxSize)
      .attr("fill", "transparent")
      // .attr('stroke', 'blue')
      // .attr('stroke-width', 1)
      .attr("rx", 5) // Optional: rounded corners
      .attr("ry", 5) // Optional: rounded corners
      .call(
        d3
          .drag()
          .filter((event, d) => d.line.movePoints)
          .on("drag", function (event, d) {
            const newX = x.invert(event.x);
            const newY = y.invert(event.y);
            d[0] = newX;
            d[1] = newY;
            that._redraw(i, d.line); // Redraw to update lines
          }),
      );

    const pointsMerge = points
      .merge(pointsEnter)
      .attr("x", (d) => x(d[0]) - boxSize / 2) // Center the box on the point
      .attr("y", (d) => y(d[1]) - boxSize / 2) // Center the box on the point
      .each(function () {
        d3.select(this).raise(); // Bring the box to the front during redraw
      });

    points.exit().remove();

    // Adding draggable lines
    const lineRectHeight = 15;
    const allLineRects = this.chart.drawingCanvases[i]
      .selectAll(".line-rect")
      .data(
        this.chart.drawingData[i].lines.flatMap((line) => {
          return line.points.slice(0, -1).map((point, index) => ({
            line,
            index,
            point1: point,
            point2: line.points[index + 1],
          }));
        }),
        (d) => `${d.line.id}-${d.index}`,
      );

    const lineRectsEnter = allLineRects
      .enter()
      .append("rect")
      .attr("class", "line-rect")
      .attr("fill", "transparent")
      // .attr('stroke', 'blue')
      // .attr('stroke-width', 1)
      .call(
        d3
          .drag()
          .filter((event, d) => d.line.move)
          .on("drag", function (event, d) {
            const dx = x.invert(event.dx) - x.invert(0);
            const dy = y.invert(event.dy) - y.invert(0);
            d.line.points.forEach((point) => {
              point[0] += dx;
              point[1] += dy;
            });
            that._redraw(i, d.line); // Redraw to update lines and points
          }),
      );

    const lineRectsMerge = lineRectsEnter
      .merge(allLineRects)
      .attr("width", (d) => {
        const x1 = x(d.point1[0]);
        const x2 = x(d.point2[0]);
        const y1 = y(d.point1[1]);
        const y2 = y(d.point2[1]);
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
      })
      .attr("height", lineRectHeight)
      .attr("x", (d) => {
        const x1 = x(d.point1[0]);
        const x2 = x(d.point2[0]);
        return (
          (x1 + x2) / 2 -
          Math.sqrt(
            Math.pow(x2 - x1, 2) + Math.pow(y(d.point2[1]) - y(d.point1[1]), 2),
          ) /
            2
        );
      })
      .attr("y", (d) => {
        const y1 = y(d.point1[1]);
        const y2 = y(d.point2[1]);
        return (y1 + y2) / 2 - lineRectHeight / 2;
      })
      .attr("transform", (d) => {
        const x1 = x(d.point1[0]);
        const x2 = x(d.point2[0]);
        const y1 = y(d.point1[1]);
        const y2 = y(d.point2[1]);
        const angle = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI;
        return `rotate(${angle}, ${(x1 + x2) / 2}, ${(y1 + y2) / 2})`;
      })
      .each(function () {
        d3.select(this).raise(); // Bring the box to the front during redraw
      });

    allLineRects.exit().remove();

    // Label handling (existing code)
    const labelData = this.chart.drawingData[i].lines.flatMap((d) => {
      d.labels.forEach((label, index) => {
        label.line = d;
        label.index = index;
      });
      return d.labels;
    });

    const labels = this.chart.drawingCanvases[i]
      .selectAll(".label-group")
      .data(labelData, (d) => `${d.line.id}-${d.index}`);

    const labelEnter = labels.enter().append("g").attr("class", "label-group");

    labelEnter
      .append("rect")
      .attr("class", "label-bg")
      .attr("rx", 1) // Rounded corners, optional
      .attr("ry", 1); // Rounded corners, optional

    labelEnter
      .append("text")
      .attr("class", "label")
      .attr("fill", (d) => {
        if (d.color) {
          return d.color(d);
        } else {
          return "currentColor";
        }
      })
      .attr("font-size", (d) => {
        if (d.fontSize) {
          return d.fontSize(d);
        } else {
          return `${this.chart.fontSize}px`;
        }
      });

    const labelsMerge = labels.merge(labelEnter);

    const ls = labelsMerge.select(".label");

    ls.each(function (d) {
      const bbox = this.getBBox();
      d.bbox = { width: bbox.width, height: bbox.height };
    });

    labelsMerge
      .select(".label-bg")
      .attr("x", (d) => x(d.coordinates(d)[0]) - 2)
      .attr("y", (d) => y(d.coordinates(d)[1]) - d.bbox.height - 2)
      .attr("width", (d) => d.bbox.width + 4)
      .attr("height", (d) => d.bbox.height + 4);

    ls.text((d) => d.text(d))
      .attr("x", (d) => x(d.coordinates(d)[0]))
      .attr("y", (d) => y(d.coordinates(d)[1]))
      .each(function () {
        d3.select(this).raise(); // Bring the box to the front during redraw
      });

    labels.exit().remove();
  }
}
