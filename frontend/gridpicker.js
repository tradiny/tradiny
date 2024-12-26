/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

export class GridPicker {
  constructor(grids, targetElement, onGridSelect, domHandler) {
    this.grids = grids || [
      "1x1",
      "1x2",
      "1x3",
      "2x1",
      "2x2",
      "2x3",
      "3x1",
      "3x2",
      "3x3",
    ];
    this.targetElement = targetElement;
    this.onGridSelect = onGridSelect;
    this.domHandler = domHandler;
    this.createGridicker();
  }

  createGridicker() {
    this.container = document.createElement("div");
    this.container.className = "grid-picker";
    this.container.style.position = "absolute";
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
    rect.innerHTML = this.domHandler.icon.getIcon("back");
    rect.addEventListener("click", this.closePicker.bind(this));
    this.container.appendChild(rect);

    // Create a rectangle for each interval
    this.grids.forEach((grid) => {
      const rect = document.createElement("div");
      rect.className = "icon";
      // rect.style.width = "25px";
      // rect.style.height = "25px";
      rect.style.cursor = "pointer";
      rect.style.display = "flex";
      rect.style.alignItems = "center";
      rect.style.justifyContent = "center";
      rect.innerText = grid;

      rect.addEventListener("click", () => {
        this.onGridSelect(grid);
        this.clearSelection();
        this.closePicker(); // Close the picker on selection
      });

      this.container.appendChild(rect);
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
