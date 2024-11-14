/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

export class ColorPicker {
  static default = -1;

  constructor(defaultColor, targetElement, onColorSelect) {
    this.colors = [
      "#e60049",
      "#0bb4ff",
      "#50e991",
      "#e6d800",
      "#9b19f5",
      "#ffa300",
      "#dc0ab4",
      "#b3d4ff",
      "#00bfa0",
      "#ea5545",
      "#f46a9b",
      "#ef9b20",
      "#edbf33",
      "#ede15b",
      "#bdcf32",
      "#87bc45",
      "#27aeef",
      "#b33dc6",
      "#b30000",
      "#7c1158",
      "#4421af",
      "#1a53ff",
      "#0d88e6",
      "#00b7c7",
      "#5ad45a",
      "#8be04e",
      "#ebdc78",
      "#fd7f6f",
      "#7eb0d5",
      "#b2e061",
      "#bd7ebe",
      "#ffb55a",
      "#ffee65",
      "#beb9db",
      "#fdcce5",
      "#8bd3c7",
      "#115f9a",
      "#1984c5",
      "#22a7f0",
      "#48b5c4",
      "#76c68f",
      "#a6d75b",
      "#c9e52f",
      "#d0ee11",
      "#d0f400",
      "#d7e1ee",
      "#cbd6e4",
      "#bfcbdb",
      "#b3bfd1",
      "#a4a2a8",
      "#df8879",
      "#c86558",
      "#b04238",
      "#991f17",
      "#2e2b28",
      "#3b3734",
      "#474440",
      "#54504c",
      "#6b506b",
      "#ab3da9",
      "#de25da",
      "#eb44e8",
      "#ff80ff",
      "#0000b3",
      "#0010d9",
      "#0020ff",
      "#0040ff",
      "#0060ff",
      "#0080ff",
      "#009fff",
      "#00bfff",
      "#00ffff",
      "#1984c5",
      "#22a7f0",
      "#63bff0",
      "#a7d5ed",
      "#e2e2e2",
      "#e1a692",
      "#de6e56",
      "#e14b31",
      "#c23728",
      "#ffb400",
      "#d2980d",
      "#a57c1b",
      "#786028",
      "#363445",
      "#48446e",
      "#5e569b",
      "#776bcd",
      "#9080ff",
      "#54bebe",
      "#76c8c8",
      "#98d1d1",
      "#badbdb",
      "#dedad2",
      "#e4bcad",
      "#df979e",
      "#d7658b",
      "#c80064",
      "#e27c7c",
      "#a86464",
      "#6d4b4b",
      "#503f3f",
      "#333333",
      "#3c4e4b",
      "#466964",
      "#599e94",
      "#6cd4c5",
    ];

    if (!defaultColor) {
      ColorPicker.default += 1;
    }
    if (ColorPicker.default >= 9) {
      ColorPicker.default = 0;
    }

    this.defaultColor = defaultColor
      ? defaultColor
      : this.colors[ColorPicker.default];
    this.targetElement = targetElement;
    this.onColorSelect = onColorSelect;
    this.isPickerOpen = false;
    this.createColorPicker();
  }

  createColorPicker() {
    // Clear the target element
    this.targetElement.innerHTML = "";

    // Create a container for the default color and the color rectangles
    const container = document.createElement("div");
    container.style.position = "relative"; // Ensure the position is relative for the color picker

    // Create the default color rectangle
    const defaultColorRect = document.createElement("div");
    defaultColorRect.style.width = "15px"; // Half of the previous size
    defaultColorRect.style.height = "15px"; // Half of the previous size
    defaultColorRect.style.backgroundColor = this.defaultColor;
    defaultColorRect.style.cursor = "pointer";
    defaultColorRect.style.border = "1px solid #000";
    this.targetElement.setAttribute("data-value", this.defaultColor);
    defaultColorRect.addEventListener("click", () => {
      this.togglePicker();
    });

    container.appendChild(defaultColorRect);

    // Create a container for the color rectangles
    this.colorContainer = document.createElement("div");
    this.colorContainer.style.position = "absolute";
    this.colorContainer.style.display = "none";
    this.colorContainer.style.flexWrap = "wrap";
    this.colorContainer.style.width = "249px"; // Adjust width to fit more rectangles
    this.colorContainer.style.backgroundColor = "#fff";
    this.colorContainer.style.border = "1px solid #ccc";
    this.colorContainer.style.boxShadow = "0 2px 5px rgba(0,0,0,0.3)";
    this.colorContainer.style.zIndex = "1000";

    // Create a rectangle for each color
    this.colors.forEach((color) => {
      const colorRect = document.createElement("div");
      colorRect.style.width = "12px"; // Half of the previous size
      colorRect.style.height = "12px"; // Half of the previous size
      colorRect.style.backgroundColor = color;
      colorRect.style.cursor = "pointer";
      colorRect.style.border = "1px solid transparent";
      colorRect.style.transition = "border 0.3s";

      colorRect.addEventListener("click", () => {
        this.targetElement.setAttribute("data-value", color);
        this.onColorSelect(color);
        this.clearSelection();
        colorRect.style.border = "1px solid #000";
        defaultColorRect.style.backgroundColor = color;
        this.togglePicker();
      });

      this.colorContainer.appendChild(colorRect);
    });

    container.appendChild(this.colorContainer);
    this.targetElement.appendChild(container);
  }

  togglePicker() {
    this.isPickerOpen = !this.isPickerOpen;
    if (this.isPickerOpen) {
      document.body.appendChild(this.colorContainer);
      const rect = this.targetElement.getBoundingClientRect();
      this.colorContainer.style.top = `${rect.bottom + window.scrollY}px`;
      this.colorContainer.style.left = `${rect.left + window.scrollX}px`;
      this.colorContainer.style.display = "flex";
    } else {
      this.colorContainer.style.display = "none";
      if (this.colorContainer.parentElement) {
        this.colorContainer.parentElement.removeChild(this.colorContainer);
      }
    }
  }

  clearSelection() {
    const rects = this.colorContainer.querySelectorAll("div");
    rects.forEach((rect) => {
      rect.style.border = "1px solid transparent";
    });
  }
}
