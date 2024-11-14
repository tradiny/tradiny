/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */
import { Utils } from "./utils.js";
import * as d3 from "d3";

export class GridHandler {
  constructor(options) {
    this.options = options;
    this.created = false;
    this.gridElements = [];
    this.cellToIdMap = {};
    this.colDragDistances = [];
    this.rowDragDistances = [];

    if (options.charts) {
      for (let i = 0; i < options.charts.length; i++) {
        const chartOptions = options.charts[i];
        if (chartOptions.dataProvider) {
          this.emptyDataProviderConfig = Utils.deepCopy(
            chartOptions.dataProvider,
          );
          this.emptyDataProviderConfig.data = [];
        }
      }
    }

    let calculatedSize = "large";
    if (window.innerWidth <= 844) {
      calculatedSize = "small";
    }
    this.options.size = this.options.size || calculatedSize;

    window.addEventListener("resize", () => {
      this.updateGridTemplate();
    });
  }

  getGrid() {
    return (this.grid || this.options.grid || "1x1").split("x").map(Number);
  }

  changeGrid(grid) {
    this.grid = grid;
    this.destroyGrid();
    this.createGrid();
    this.initializeCharts();
    this.resize();
  }

  initializeCharts() {
    let opt = this.next();
    while (opt) {
      const chart = new TradinyChart();
      this.setChart(opt.gridPosition, chart);
      chart.initialize(opt);
      opt = this.next();
    }
  }

  getChart(position) {
    if (!position) {
      position = "1x1";
    }

    let [row, col] = position.split("x").map(Number);
    row -= 1;
    col -= 1;

    if (isNaN(row) || isNaN(col)) {
      console.warn(
        'Invalid input format. Expected "rowxcol" where row and col are integers.',
      );
      return;
    }

    if (row < 0 || col < 0) {
      console.warn("Row and column indices must be non-negative.");
      return;
    }

    if (
      row >= this.gridElements.length ||
      col >= (this.gridElements[row] || []).length
    ) {
      console.warn("Row or column index is out of bounds.");
      return;
    }

    const cell = this.gridElements[row][col];
    if (!cell) {
      console.warn("Cell does not exist at the specified indices.");
      return;
    }

    return cell.chart;
  }

  setChart(position, chart) {
    let [row, col] = position.split("x").map(Number);
    row -= 1;
    col -= 1;

    if (isNaN(row) || isNaN(col)) {
      console.warn(
        'Invalid input format. Expected "rowxcol" where row and col are integers.',
      );
      return;
    }

    if (row < 0 || col < 0) {
      console.warn("Row and column indices must be non-negative.");
      return;
    }

    if (
      row >= this.gridElements.length ||
      col >= (this.gridElements[row] || []).length
    ) {
      console.warn("Row or column index is out of bounds.");
      return;
    }

    const cell = this.gridElements[row][col];
    if (!cell) {
      console.warn("Cell does not exist at the specified indices.");
      return;
    }

    cell.chart = chart;

    this.cellToIdMap[`${row + 1}x${col + 1}`] = this.getElementId(row, col);
  }
  updateGridTemplate() {
    const gridElementId = this.options.elementId;
    const container = document.getElementById(gridElementId);

    if (!container) throw new Error("Grid container element not found");

    const delimiterSize = this.getDelimiterSize();
    const fullWidth = container.offsetWidth;
    const fullHeight = container.offsetHeight;

    const colDelimiterSizeAbs = (this.colWidths.length - 1) * delimiterSize;
    const rowDelimiterSizeAbs = (this.rowHeights.length - 1) * delimiterSize;

    // Calculate the new absolute sizes based on the container size
    const totalRelativeColWidth = this.colWidths.reduce(
      (acc, val) => acc + val,
      0,
    );
    const totalRelativeRowHeight = this.rowHeights.reduce(
      (acc, val) => acc + val,
      0,
    );

    this.colWidths = this.colWidths.map(
      (relativeWidth) =>
        (relativeWidth / totalRelativeColWidth) *
        (fullWidth - colDelimiterSizeAbs),
    );

    this.rowHeights = this.rowHeights.map(
      (relativeHeight) =>
        (relativeHeight / totalRelativeRowHeight) *
        (fullHeight - rowDelimiterSizeAbs),
    );

    container.style.gridTemplateRows = this.generateTemplateString(
      this.rowHeights,
      delimiterSize,
    );
    container.style.gridTemplateColumns = this.generateTemplateString(
      this.colWidths,
      delimiterSize,
    );
  }

  getDelimiterSize() {
    return this.options.size === "small" ? 15 : 5;
  }

  destroyGrid(removeExisting = false) {
    const gridElementId = this.options.elementId;
    const container = document.getElementById(gridElementId);

    if (container) {
      const [newRows, newCols] = this.getGrid();
      for (let row = 0; row < this.gridElements.length; row++) {
        for (let col = 0; col < (this.gridElements[row] || []).length; col++) {
          const cell = this.gridElements[row][col];
          if (!cell) continue;

          if (removeExisting || row >= newRows || col >= newCols) {
            if (cell.chart) {
              cell.chart.operationsHandler.destroyChart();
            }

            container.removeChild(cell);

            delete this.gridElements[row][col];
            delete this.cellToIdMap[`${row + 1}x${col + 1}`];
          }
        }
      }

      const elements = container.children;
      for (let i = elements.length - 1; i >= 0; i--) {
        const el = elements[i];
        const row = parseInt(el.style.gridRow) / 2;
        const col = parseInt(el.style.gridColumn) / 2;

        if (isNaN(row) || isNaN(col)) continue;
        if (row >= newRows || col >= newCols) container.removeChild(el);
      }

      this.gridElements = this.gridElements
        .slice(0, newRows)
        .map((row) => row.slice(0, newCols));

      const delimiterSize = this.getDelimiterSize();
      const fullWidth = container.offsetWidth;
      const fullHeight = container.offsetHeight;

      const colDelimiterSizeAbs = (newCols - 1) * delimiterSize;
      const rowDelimiterSizeAbs = (newRows - 1) * delimiterSize;

      this.colWidths = Array(newCols).fill(
        (fullWidth - colDelimiterSizeAbs) / newCols,
      );

      this.rowHeights = Array(newRows).fill(
        (fullHeight - rowDelimiterSizeAbs) / newRows,
      );

      const rowsTemplate = this.generateTemplateString(
        this.rowHeights,
        delimiterSize,
      );
      const colsTemplate = this.generateTemplateString(
        this.colWidths,
        delimiterSize,
      );

      container.style.gridTemplateRows = rowsTemplate;
      container.style.gridTemplateColumns = colsTemplate;

      this.created = newRows > 0 && newCols > 0;
    }
  }

  makeColDelimiterDraggable(element, colIndex, onDrag) {
    this.colDragDistances[colIndex] = 0;

    d3.select(element).call(
      d3
        .drag()
        .on("start", () => {
          d3.select("body").style("cursor", "col-resize");
          this.colDragDistances[colIndex] = 0;

          this.fixedColWidths = [...this.colWidths];
        })
        .on("drag", (event) => {
          const dx = event.dx;
          this.colDragDistances[colIndex] += dx;

          let newWidth =
            this.fixedColWidths[colIndex] + this.colDragDistances[colIndex];
          let nextColIndex = colIndex + 1;
          let nextNewWidth =
            this.fixedColWidths[nextColIndex] - this.colDragDistances[colIndex];

          if (newWidth > 0 && nextNewWidth > 0) {
            const totalWidth = this.fixedColWidths.reduce(
              (acc, w) => acc + w,
              0,
            );
            this.colWidths[colIndex] = newWidth;
            this.colWidths[nextColIndex] = nextNewWidth;

            onDrag();

            this.resize();
          }
        })
        .on("end", () => {
          d3.select("body").style("cursor", "default");
        }),
    );
  }

  resize() {
    this.gridElements.forEach((row) =>
      row.forEach((cell) => {
        const chart = cell.chart;
        if (chart && chart.panes && chart.panes.length > 0) {
          chart.interactionHandler.onResize();
        }
      }),
    );
  }

  makeRowDelimiterDraggable(element, rowIndex, onDrag) {
    this.rowDragDistances[rowIndex] = 0;

    d3.select(element).call(
      d3
        .drag()
        .on("start", () => {
          d3.select("body").style("cursor", "row-resize");
          this.rowDragDistances[rowIndex] = 0;

          this.fixedRowHeights = [...this.rowHeights];
        })
        .on("drag", (event) => {
          const dy = event.dy;
          this.rowDragDistances[rowIndex] += dy;

          let newHeight =
            this.fixedRowHeights[rowIndex] + this.rowDragDistances[rowIndex];
          let nextRowIndex = rowIndex + 1;
          let nextNewHeight =
            this.fixedRowHeights[nextRowIndex] -
            this.rowDragDistances[rowIndex];

          if (newHeight > 0 && nextNewHeight > 0) {
            const totalHeight = this.fixedRowHeights.reduce(
              (acc, h) => acc + h,
              0,
            );
            this.rowHeights[rowIndex] = newHeight;
            this.rowHeights[nextRowIndex] = nextNewHeight;

            onDrag();
            this.resize();
          }
        })
        .on("end", () => {
          d3.select("body").style("cursor", "default");
        }),
    );
  }

  generateTemplateString(sizes, delimiterSize) {
    return sizes.map((size) => `${size}px`).join(` ${delimiterSize}px `);
  }
  createGrid(preserveWidthsHeights = false) {
    const gridElementId = this.options.elementId;
    const [rows, cols] = this.getGrid();
    const container = document.getElementById(gridElementId);

    if (!container) throw new Error("Grid container element not found");

    container.style.display = "grid";
    container.style.overflow = "hidden";
    container.style.position = "relative";

    const delimiterSize = this.getDelimiterSize();
    const fullWidth = container.offsetWidth;
    const fullHeight = container.offsetHeight;

    const colDelimiterSizeAbs = (cols - 1) * delimiterSize;
    const rowDelimiterSizeAbs = (rows - 1) * delimiterSize;

    if (!preserveWidthsHeights) {
      const colWidth = (fullWidth - colDelimiterSizeAbs) / cols;
      const rowHeight = (fullHeight - rowDelimiterSizeAbs) / rows;

      this.colWidths = Array(cols).fill(colWidth);
      this.rowHeights = Array(rows).fill(rowHeight);
    }

    container.style.gridTemplateRows = this.generateTemplateString(
      this.rowHeights,
      delimiterSize,
    );
    container.style.gridTemplateColumns = this.generateTemplateString(
      this.colWidths,
      delimiterSize,
    );

    this.gridElements = [];

    container
      .querySelectorAll(".col-delimiter, .row-delimiter, .corner-delimiter")
      .forEach((el) => {
        if (el.parentNode === container) {
          container.removeChild(el);
        }
      });

    for (let row = 0; row < rows; row++) {
      this.gridElements[row] = [];
      for (let col = 0; col < cols; col++) {
        let cell = container.querySelector(
          `.grid-cell[data-row="${row}"][data-col="${col}"]`,
        );
        if (!cell) {
          cell = document.createElement("div");
          const elementId = this.getElementId(row + 1, col + 1);
          cell.id = elementId;
          cell.className = "grid-cell";
          cell.dataset.row = row;
          cell.dataset.col = col;
          container.appendChild(cell);
        }
        this.gridElements[row].push(cell);

        if (col < cols - 1) {
          let colDelimiter = document.createElement("div");
          colDelimiter.className = "col-delimiter";
          colDelimiter.style.gridRow = `${2 * row + 1}`;
          colDelimiter.style.gridColumn = `${2 * col + 2}`;
          container.appendChild(colDelimiter);
          this.makeColDelimiterDraggable(colDelimiter, col, () => {
            container.style.gridTemplateColumns = this.generateTemplateString(
              this.colWidths,
              delimiterSize,
            );
          });
        }
      }
      if (row < rows - 1) {
        for (let col = 0; col < cols; col++) {
          let rowDelimiter = document.createElement("div");
          rowDelimiter.className = "row-delimiter";
          rowDelimiter.style.gridRow = `${2 * row + 2}`;
          rowDelimiter.style.gridColumn = `${2 * col + 1}`;
          container.appendChild(rowDelimiter);

          this.makeRowDelimiterDraggable(rowDelimiter, row, () => {
            container.style.gridTemplateRows = this.generateTemplateString(
              this.rowHeights,
              delimiterSize,
            );
          });

          if (col < cols - 1) {
            let cornerDelimiter = document.createElement("div");
            cornerDelimiter.className = "corner-delimiter";
            cornerDelimiter.style.gridRow = `${2 * row + 2}`;
            cornerDelimiter.style.gridColumn = `${2 * col + 2}`;
            container.appendChild(cornerDelimiter);
          }
        }
      }
    }
    this.created = true;
  }

  getElementId(row, col) {
    return `chart-${row}x${col}`;
  }

  next() {
    const [rows, cols] = this.getGrid();

    for (let row = 1; row <= rows; row++) {
      for (let col = 1; col <= cols; col++) {
        const cell = `${row}x${col}`;
        const elementId = this.getElementId(row, col);
        if (!this.cellToIdMap.hasOwnProperty(cell)) {
          this.cellToIdMap[cell] = elementId;

          const chartOptions = Utils.deepCopy(this.options);
          chartOptions.elementId = elementId;
          chartOptions.gridPosition = cell;
          chartOptions.gridHandler = this;

          let chart = chartOptions.charts?.find(
            (chart) => chart.gridPosition === cell,
          );
          if (chart) {
            Object.assign(chartOptions, chart);
            if (!this.emptyDataProviderConfig) {
              this.emptyDataProviderConfig = Utils.deepCopy(
                chartOptions.dataProvider,
              );
              this.emptyDataProviderConfig.data = [];
            }
          } else {
            chartOptions.panes = [];
            chartOptions.dataProvider = Utils.deepCopy(
              this.emptyDataProviderConfig,
            );
          }

          delete chartOptions.charts;

          return chartOptions;
        }
      }
    }
    return null;
  }
}
