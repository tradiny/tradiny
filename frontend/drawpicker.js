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

export class DrawPicker {
  constructor(domHandler) {
    this.domHandler = domHandler;
    this.chart = domHandler.chart;

    const disableActive = () => {
      if (this.chart.drawingHandler.active) {
        // first disable, then activate `tool`
        this.chart.drawingHandler._toggle(this.chart.drawingHandler.activeTool);
      }
    };

    this.controls = {
      "control-back": {
        className: "control-back-icon",
        onClick: () => {
          disableActive();
          this.closeControls();
        },
        innerHTML: this.domHandler.icon.getIcon("back"),
      },
      text: {
        className: "text-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("text");
        },
        innerHTML: `Abc`,
      },
      line: {
        className: "line-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("line");
        },
        innerHTML: this.domHandler.icon.getIcon("line2"),
      },
      "horizontal-line": {
        className: "horizontal-line-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("horizontal-line");
        },
        innerHTML: this.domHandler.icon.getIcon("horizontalLine"),
      },
      "vertical-line": {
        className: "vertical-line-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("vertical-line");
        },
        innerHTML: this.domHandler.icon.getIcon("verticalLine"),
      },
      brush: {
        className: "brush-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("brush");
        },
        innerHTML: this.domHandler.icon.getIcon("brush"),
      },
      ruler: {
        className: "ruler-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("ruler");
        },
        innerHTML: this.domHandler.icon.getIcon("ruler"),
      },
      fib: {
        className: "fib-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("fib");
        },
        innerHTML: this.domHandler.icon.getIcon("fib"),
      },
      back: {
        className: "back-icon",
        onClick: () => {
          disableActive();
          this.chart.back();
        },
        innerHTML: this.domHandler.icon.getIcon("backRound"),
      },
    };

    this.createControls();
  }
  createControls() {
    // Create a container for icons
    this.container = document.createElement("div");
    this.container.className = "draw-picker";
    this.container.style.top = "0";
    this.container.style.position = "absolute";
    this.container.style.display = "flex";
    this.container.style.flexDirection = "column";
    this.container.style.height = "auto";

    // Iterate over the controls to set up each one
    Object.keys(this.controls).forEach((control) => {
      if (this.chart.features.includes(control) || control === "control-back") {
        const controlInfo = this.controls[control];
        const controlElement = document.createElement("div");
        controlElement.className = `icon ${controlInfo.className}`;
        controlElement.innerHTML = controlInfo.innerHTML;
        controlElement.addEventListener("click", controlInfo.onClick);
        this.container.appendChild(controlElement);
      }
    });

    // Append the container to the target element
    this.chart.controlsEl.node().appendChild(this.container);
  }
  closeControls() {
    if (this.container && this.container.parentElement) {
      this.container.parentElement.removeChild(this.container);
    }
  }
}
