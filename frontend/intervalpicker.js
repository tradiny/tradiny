/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
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

    const rect = document.createElement("div");
    rect.className = "icon";
    // rect.style.width = "25px";
    // rect.style.height = "25px";
    rect.style.cursor = "pointer";
    rect.style.display = "flex";
    rect.style.alignItems = "center";
    rect.style.justifyContent = "center";
    rect.innerHTML = this.domHandler.getIcon("back");
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
