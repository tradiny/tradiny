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

export class RenderHandler {
  constructor(chart) {
    this.chart = chart;

    this.R = {
      DATA: 1,
      MOVE: 2,
      ZOOM: 3,
      CROSSHAIR: 4,
      X_DOMAIN: 5,
      Y_DOMAIN: 6,
      X_LABEL: 7,
      Y_LABEL: 8,
      any(array1, array2) {
        if (!array1 || !array2) {
          return false;
        }
        return array1.some((value) => array2.includes(value));
      },
    };
  }

  render(refresh, event) {
    const newDomain = this.chart.xScale.domain();

    if (
      event &&
      this.chart.mousePosition &&
      this.chart.mousePosition.position
    ) {
      const currentMouse = d3.pointer(
        event,
        this.chart.domChartEls[this.chart.mousePosition.i],
      );
      this.chart.mousePosition.position.x = currentMouse[0];
      this.chart.mousePosition.position.y = currentMouse[1];
    }

    if (refresh && this.R.any([this.R.MOVE, this.R.ZOOM], refresh)) {
      if (newDomain[0] < 0) {
        this.chart.dataProvider.history(newDomain[0]);
      }
    }

    if (!refresh || this.R.any([this.R.ZOOM], refresh)) {
      // update width of candlesticks on this.R
      for (let i = 0; i < this.chart.panes.length; i++) {
        const pane = this.chart.panes[i];

        for (let j = 0; j < pane.metadata.length; j++) {
          const metadata = pane.metadata[j];

          switch (metadata.type) {
            case "candlestick":
              metadata.series.bandwidth(
                this.bandwidth(newDomain, metadata.spacingFactor),
              );
              break;

            case "bar":
              metadata.series.bandwidth(
                this.bandwidth(newDomain, metadata.spacingFactor),
              );
              break;
          }
        }
      }
    }

    if (
      !refresh ||
      this.R.any([this.R.MOVE, this.R.ZOOM, this.R.Y_DOMAIN], refresh)
    ) {
      // dynamic Y axis or autoscale
      for (let i = 0; i < this.chart.yAxes.length; i++) {
        const chartAxes = this.chart.yAxes[i];
        for (let j of Object.keys(chartAxes)) {
          const yAxis = this.chart.yAxes[i][j];
          if (yAxis.meta.dynamic) {
            const yDomain = this.dynamicYAxisDomain(
              i,
              this.chart.panes[i].metadata,
              newDomain,
              yAxis,
            );
            if (yDomain) {
              yAxis.scale.domain(yDomain);
            }
          }
        }
      }
    }

    if (
      !refresh ||
      (refresh &&
        this.R.any(
          [this.R.MOVE, this.R.ZOOM, this.R.Y_DOMAIN, this.R.X_DOMAIN],
          refresh,
        ))
    ) {
      for (let i = 0; i < this.chart.panes.length; i++) {
        this.chart.drawingHandler._redraw(i, null);
      }
    }

    if (
      !refresh ||
      this.R.any(
        [
          this.R.DATA,
          this.R.MOVE,
          this.R.ZOOM,
          this.R.X_DOMAIN,
          this.R.X_LABEL,
          this.R.CROSSHAIR,
        ],
        refresh,
      )
    ) {
      // x-scale
      this.chart.xAxisSvg.call(this.chart.xAxis.scale(this.chart.xScale));
      this.chart.axisHandler.addXLabel(
        this.chart.xAxisSvg,
        this.chart.mousePosition,
      );
    }

    if (
      !refresh ||
      this.R.any(
        [
          this.R.DATA,
          this.R.MOVE,
          this.R.ZOOM,
          this.R.Y_DOMAIN,
          this.R.Y_LABEL,
          this.R.CROSSHAIR,
        ],
        refresh,
      )
    ) {
      // y-scales
      this.chart.panes.forEach((pane, i) => {
        if (!this.chart.yAxes[i]) return;
        Object.keys(this.chart.yAxes[i]).forEach((j) => {
          const yAxis = this.chart.yAxes[i][j];
          const svg = this.chart.yAxesSvg[i][j];
          svg.call(yAxis.axis.scale(yAxis.scale));

          this.chart.axisHandler.addYLabels(
            i,
            yAxis,
            svg,
            this.chart.mousePosition,
          );
        });
      });
    }

    if (
      !refresh ||
      this.R.any(
        [
          this.R.DATA,
          this.R.MOVE,
          this.R.ZOOM,
          this.R.X_DOMAIN,
          this.R.Y_DOMAIN,
          this.R.X_LABEL,
          this.R.Y_LABEL,
          this.R.CROSSHAIR,
        ],
        refresh,
      )
    ) {
      // charts
      for (let i = 0; i < this.chart.panes.length; i++) {
        if (this.chart.d3ChartEls[i]) {
          this.chart.d3ChartEls[i]
            .datum(this.chart.dataProvider.data)
            .call(this.chart.fcCharts[i]);
        }
      }
    }

    if (!refresh || this.R.any([this.R.CROSSHAIR], refresh)) {
      // crosshair
      for (let i = 0; i < this.chart.panes.length; i++) {
        if (i < this.chart.pointers.length) {
          this.chart.d3ChartEls[i].call(this.chart.pointers[i]);
        }
      }
    }
  }

  bandwidth(newDomain, spacingFactor) {
    spacingFactor = spacingFactor ?? this.chart.pointSpacingFactor;
    return Math.max(
      1,
      (this.chart.paneWidth / (newDomain[1] - newDomain[0])) *
        (1 - spacingFactor),
    );
  }

  adjustRange(start, end, percentage, position = "bottom") {
    if (position === "bottom") {
      let newEnd;
      const originalRange = end - start;

      if (percentage < 50) {
        // For percentages below 50%, use the scaling factor method
        const scaleFactor = 100 / percentage;
        const newRange = originalRange * scaleFactor;
        newEnd = start + newRange;
      } else {
        // For percentages 50% and above, use the direct proportion method
        const additionalAmount = originalRange * ((100 - percentage) / 100);
        newEnd = end + additionalAmount;
      }

      return [start, newEnd];
    }
    if (position === "top") {
      let newStart;
      const originalRange = end - start;

      if (percentage < 50) {
        // For percentages below 50%, use the scaling factor method
        const scaleFactor = 100 / percentage;
        const newRange = originalRange * scaleFactor;
        newStart = start - newRange;
      } else {
        // For percentages 50% and above, use the direct proportion method
        const additionalAmount = originalRange * ((100 - percentage) / 100);
        newStart = start - additionalAmount;
      }

      return [newStart, end];
    }
  }

  dynamicYAxisDomain(paneI, metadata, domain, yAxis) {
    let yMin = Number.MAX_VALUE,
      yMax = -Number.MAX_VALUE;
    for (let i = 0; i < metadata.length; i++) {
      for (let j = 0; j < metadata[i].dataKeys.length; j++) {
        if (yAxis.meta.key == metadata[i].dataKeys[j].yAxis) {
          if (
            this.chart.dataCache[paneI] &&
            this.chart.dataCache[paneI][metadata[i].dataKeys[j].dataKey]
          ) {
            // has MinMax cache
            const o = this.chart.dataCache[paneI][
              metadata[i].dataKeys[j].dataKey
            ].query(domain[0], domain[1]);

            if (o.min !== undefined) {
              if (o.min < yMin) {
                yMin = o.min;
              }
            }
            if (o.max !== undefined) {
              if (o.max > yMax) {
                yMax = o.max;
              }
            }
          }
        }
      }
    }
    if (yMin === Number.MAX_VALUE || yMax === -Number.MAX_VALUE) {
      if (yAxis.prevDomain) {
        return yAxis.prevDomain;
      }
      return null;
    }
    const yRange = yMax - yMin;
    const pixelToDataScale = yRange / this.chart.domContainerEl.clientHeight;
    const paddingData = this.chart.paddingPixels * pixelToDataScale;
    let newDomain = [yMin - paddingData, yMax + paddingData];

    // in case of log scale newDomain[0] can be negative, fix this
    if (yAxis.meta.type === "log" && newDomain[0] < 0) {
      newDomain[0] = yMin;
    }

    if (yAxis.meta.height) {
      // if (yAxis.meta.position === "top") {
      newDomain = this.adjustRange(
        newDomain[0],
        newDomain[1],
        yAxis.meta.height,
        yAxis.meta.position,
      ); //(newDomain[1] - newDomain[0]) * (10.0-((100-this.chart.yAxes[chartI][yAxis].meta.height)/10));
      // }
    }

    // in case of log scale newDomain[0] can be negative, fix this
    if (yAxis.meta.type === "log" && newDomain[0] < 0) {
      newDomain[0] = yMin;
    }

    yAxis.prevDomain = newDomain;
    return newDomain;
  }
}
