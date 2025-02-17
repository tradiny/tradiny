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

export class IntervalPicker {
  constructor(intervals, targetElement, onIntervalSelect, domHandler) {
    this.intervals = intervals || [
      "1m",
      "3m",
      "5m",
      "15m",
      "30m",
      "1h",
      "2h",
      "4h",
      "6h",
      "8h",
      "12h",
      "1d",
      "1w",
      "1M",
    ];
    this.targetElement = targetElement;
    this.onIntervalSelect = onIntervalSelect;
    this.domHandler = domHandler;
    this.chart = domHandler.chart;
    this.createIntervalPicker();
  }

  createIntervalPicker() {
    // Create a container for the interval rectangles
    this.container = document.createElement("div");
    this.container.className = "interval-picker";
    this.container.style.position = "absolute"; // Ensure the position is relative for the interval picker
    this.container.style.display = "flex";
    this.container.style.flexDirection = "column";
    this.container.style.height = "auto";

    const rect = document.createElement("div");
    rect.className = "icon";
    // rect.style.width = "25px";
    // rect.style.height = "25px";
    rect.style.cursor = "pointer";
    rect.style.display = "flex";
    rect.style.alignItems = "center";
    rect.style.justifyContent = "center";
    rect.innerHTML = this.domHandler.icon.getIcon("back");
    rect.addEventListener("click", this.closePicker.bind(this));
    this.container.appendChild(rect);

    // Create a rectangle for each interval
    this.intervals.forEach((interval) => {
      const intervalRect = document.createElement("div");
      intervalRect.className = "icon";
      // intervalRect.style.width = "25px";
      // intervalRect.style.height = "25px";
      intervalRect.style.cursor = "pointer";
      intervalRect.style.display = "flex";
      intervalRect.style.alignItems = "center";
      intervalRect.style.justifyContent = "center";
      intervalRect.innerText = interval;

      intervalRect.addEventListener("click", () => {
        this.onIntervalSelect(interval);
        this.clearSelection();
        this.closePicker(); // Close the picker on selection
      });

      this.container.appendChild(intervalRect);
    });

    this.targetElement.appendChild(this.container);
  }

  closePicker() {
    if (this.container && this.container.parentElement) {
      this.container.parentElement.removeChild(this.container);
    }
  }

  clearSelection() {
    const rects = this.targetElement.querySelectorAll(".icon");
    rects.forEach((rect) => {});
  }
}
