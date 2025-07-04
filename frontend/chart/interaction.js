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

export class InteractionHandler {
  constructor(chart) {
    this.chart = chart;
    this.resizeHandler = this.debounce(this.onResize.bind(this), 250, true);
  }

  setupAllInteractions() {
    this.chart.zoom = fc.zoom().on("zoom", (event) => {
      if (event.transform.k == 1) {
        this.chart.renderHandler.render([this.chart.R.MOVE], event);
      } else {
        this.chart.renderHandler.render([this.chart.R.ZOOM], event);
      }
    });

    if (this.chart.d3ContainerEl) {
      this.chart.d3ContainerEl
        .selectAll(".x-axis")
        .call(this.axisZoomInteraction(null, "x"));
    }

    this.chart.panes.forEach((chart, i) => {
      this.setupInteractions(i);
    });

    this.handleWindowResize();
  }

  setupInteractions(i) {
    const pane = this.chart.panes[i];

    this.chart.svgMultiSeries[i].mapping(this.seriesMapping(i));

    var chartEl = this.chart.d3ChartEls[i];
    console.assert(
      Array.isArray(this.chart.dataProvider.data),
      "Expected plain array for bar-series",
    );
    var updateSelection = chartEl.datum(this.chart.dataProvider.data);
    var enterSelection = updateSelection.enter().append("g"); // Adjust tag as necessary
    enterSelection.call(this.chart.fcCharts[i]);
    updateSelection.call(this.chart.fcCharts[i]);
    updateSelection.exit().remove();

    chartEl.call(
      this.chart.zoom,
      this.chart.xScale,
      this.chart.yAxes[i][this.chart.firstAxisKey[i]].scale,
    );

    Object.keys(this.chart.yAxes[i]).forEach((j, index) => {
      if (this.chart.firstAxisKey[i] !== j) return;
      const yAxis = this.chart.yAxes[i][j];
      this.chart.d3ContainerEl
        .selectAll(
          `.y-axis-${Utils.toAlphanumeric(this.chart.panes[i].name)}-${Utils.toAlphanumeric(yAxis.meta.key)}`,
        )
        .call(this.axisZoomInteraction(i, yAxis.meta.key));
    });

    this.setupPointer(i);
    this.setupContextMenu(i);

    if (i >= 1) {
      this.chart.delimiterEls[i - 1].call(
        this.chart.interactionHandler.setupDelimiterDrag(i - 1),
      );
    }

    this.chart.drawingHandler.enableInteractions(i);
  }

  disableAllInteractions() {
    if (this.chart.panes.length <= 0) {
      return; // nothing to disable
    }

    if (this.chart.d3ChartEls) {
      for (let i = 0; i < this.chart.d3ChartEls.length; i++) {
        // This will remove the zoom behavior from the elements
        this.chart.d3ChartEls[i].on(".zoom", null);
      }
    }

    if (this.chart.d3ContainerEl) {
      this.chart.d3ContainerEl.selectAll(".x-axis").on(".drag", null);
    }

    this.chart.panes.forEach((pane, i) => {
      if (this.chart.yAxes[i]) {
        Object.keys(this.chart.yAxes[i]).forEach((j, index) => {
          const yAxis = this.chart.yAxes[i][j];
          const selector = `.y-axis-${Utils.toAlphanumeric(this.chart.panes[i].name)}-${Utils.toAlphanumeric(yAxis.meta.key)}`;

          if (this.chart.d3ContainerEl) {
            this.chart.d3ContainerEl.selectAll(selector).on(".drag", null);
          }
        });
      }
    });

    for (let i = 0; i < this.chart.pointers.length; i++) {
      if (this.chart.pointers[i]) {
        this.chart.pointers[i].on("point", null);
      }
    }

    for (let i = 0; i < this.chart.panes.length; i++) {
      if (i < this.chart.panes.length - 1) {
        if (this.chart.delimiterEls[i]) {
          this.chart.delimiterEls[i].on(".drag", null);
        }
      }
    }

    for (let i = 0; i < this.chart.panes.length; i++) {
      this.chart.drawingHandler.disableInteractions(i);
    }

    console.log("remove", this.chart.options.gridPosition);
    this.removeWindowResizeHandler();
  }

  axisZoomInteraction(i, axis) {
    return d3
      .drag()
      .on("start", this.onAxisZoomStart(i, axis).bind(this))
      .on("drag", this.onAxisZoom(i, axis).bind(this))
      .on("end", this.onAxisZoomEnd(i, axis).bind(this));
  }

  onAxisZoomStart(i, axis) {
    return (event) => {
      this.chart.dataProvider.disableEvents();
      if (axis === "x") {
        this.chart._domain = this.chart.xScale.domain();
      } else {
        this.chart.yAxes[i][axis].meta.dynamic = false;
        // this.chart.d3ChartEls[i].call(this.chart.zoom.transform, d3.zoomIdentity);
        this.chart._domain = this.chart.yAxes[i][axis].scale.domain();
      }
      this.chart.initialPosition = { x: event.x, y: event.y };
    };
  }

  onAxisZoom(i, axis) {
    return (event) => {
      if (axis === "x") {
        const dx = event.x - this.chart.initialPosition.x;
        this._onAxisZoom(this.chart._domain, dx, i, axis);
        this.chart.renderHandler.render([this.chart.R.X_DOMAIN]);
      } else {
        const dy = event.y - this.chart.initialPosition.y;
        this._onAxisZoom(this.chart._domain, dy, i, axis);
        this.chart.renderHandler.render([this.chart.R.Y_DOMAIN]);
      }
    };
  }

  _onAxisZoom(domain, delta, i, axis) {
    let startValue = domain[0];
    let endValue = domain[1];
    let range = endValue - startValue;
    let scaleFactor =
      1 - delta / (axis === "x" ? window.innerWidth : window.innerHeight);
    scaleFactor = Math.max(scaleFactor, 0.1);

    const midpointValue = (startValue + endValue) / 2;
    const newRange = range * scaleFactor;
    const newStartValue = midpointValue - newRange / 2;
    const newEndValue = midpointValue + newRange / 2;

    if (axis === "x") {
      // Update the yScale domain using calculated values
      this.chart.xScale.domain([newStartValue, newEndValue]);
    } else {
      // Update the yScale domain using calculated values

      this.chart.yAxes[i][axis].scale.domain([newStartValue, newEndValue]);
    }
  }

  onAxisZoomEnd(j, axis) {
    return (event) => {
      this.chart.dataProvider.enableEvents();
      // this.chart.d3ChartEls[i].call(this.chart.zoom, this.chart.xScale, this.chart.yAxes[j][axis].scale);
      this.chart.renderHandler.render();
    };
  }

  handleWindowResize() {
    window.addEventListener("resize", this.resizeHandler);
  }

  removeWindowResizeHandler() {
    window.removeEventListener("resize", this.resizeHandler);
  }

  // Handle resizing
  onResize() {
    this.chart.DOMHandler.gridSizesUpdated();
    this.chart.DOMHandler.gridUpdated();
    this.chart.renderHandler.render();
  }

  debounce(func, wait, immediate) {
    var timeout;

    return function () {
      var context = this,
        args = arguments;

      var later = function () {
        timeout = null;
        func.apply(context, args); // Executes function after wait time if immediate is false
      };

      var callNow = immediate && !timeout; // Immediate is true and no timeout set

      clearTimeout(timeout); // Clear the existing timeout on every call
      timeout = setTimeout(later, wait); // Set new timeout to later

      if (callNow) func.apply(context, args); // If immediate and no timeout, execute function right away
    };
  }

  setupDelimiterDrag(j) {
    let startY;
    let initialpaneHeights;
    let paneHeights = [];
    let distanceDragged;
    let currentTransform = [];
    let isDragging = false;
    const drag = d3
      .drag()
      .on("start", (event) => {
        isDragging = false;
        this.chart.dataProvider.disableEvents();
        startY = event.y;
        initialpaneHeights = this.chart.paneHeights.slice(); // shallow copy
        for (let k = 0; k < this.chart.panes.length; k++) {
          currentTransform[k] = d3.zoomTransform(
            this.chart.d3ChartEls[k].node(),
          );
        }
      })
      .on("drag", (event) => {
        isDragging = true;
        const endY = event.y;
        distanceDragged = endY - startY;
        for (let k = 0; k < initialpaneHeights.length; k++) {
          if (k === j) {
            paneHeights[k] = initialpaneHeights[k] + distanceDragged;
          } else if (k === j + 1) {
            paneHeights[k] = initialpaneHeights[k] - distanceDragged;
          } else {
            paneHeights[k] = initialpaneHeights[k];
          }
        }
        // a partial calculation to achieve more speed
        const templateRows =
          this.chart.DOMHandler.calculateTemplateRowsOnly(paneHeights);
        this.chart.d3ContainerEl.style("grid-template-rows", templateRows);
        this.chart.DOMHandler.gridUpdated();
        this.chart.renderHandler.render();
        // this.chart.renderHandler.render([this.chart.R.Y_DOMAIN]);
      })
      .on("end", (event) => {
        if (!isDragging) {
          return;
        }
        // reset zoom
        const sumHeights = paneHeights.reduce(
          (partialSum, a) => partialSum + a,
          0,
        );

        for (let k = 0; k < this.chart.panes.length; k++) {
          const scaleFactor = paneHeights[k] / initialpaneHeights[k];

          let adjustedTransform = d3.zoomIdentity
            .translate(
              currentTransform[k].x,
              currentTransform[k].y * scaleFactor,
            )
            .scale(currentTransform[k].k);

          this.chart.zoom.extent([
            [0, 0],
            [this.chart.paneWidth, paneHeights[k]],
          ]);
          this.chart.d3ChartEls[k].call(d3.zoom().transform, adjustedTransform);
        }

        initialpaneHeights = paneHeights;

        // full update
        const grid = this.chart.DOMHandler.calculateTemplateGrid(paneHeights);
        const templateColumns = grid.templateColumns;
        const templateRows = grid.templateRows;
        this.chart.d3ContainerEl
          .style("grid-template-columns", templateColumns)
          .style("grid-template-rows", templateRows);

        this.chart.DOMHandler.gridUpdated();
        this.chart.renderHandler.render();

        this.chart.dataProvider.enableEvents();
        isDragging = false;
      });
    return drag;
  }

  seriesMapping(i) {
    return (data, index, series) => {
      if (series[index] === this.chart.gridlines[i]) {
        return data[index];
      }
      if (series[index] === this.chart.crosshairs[i]) {
        // crosshair
        if (!this.chart.mousePosition || !this.chart.mousePosition.position) {
          return [{ x: -5, y: -5 }]; // hide because mouse is outside
        }
        if (i === this.chart.mousePosition.i) {
          return [this.chart.mousePosition.position];
        } else {
          return [{ x: this.chart.mousePosition.position.x, y: -5 }];
        }
      }
      return data;
    };
  }

  setupPointer(i) {
    this.chart.pointers[i] = fc.pointer().on("point", this.pointerEvent(i));

    this.chart.d3ChartEls[i].call(this.chart.pointers[i]);
  }

  pointerEvent(i) {
    return (event) => {
      this.chart.mousePosition = {
        // update mouse position
        i,
        position: event[0],
      };
      this.chart.renderHandler.render([this.chart.R.CROSSHAIR]);
    };
  }

  setupContextMenu(i) {
    // TODO
  }
}
