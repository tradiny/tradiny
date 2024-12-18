/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

import * as d3 from "d3";
import * as fc from "d3fc";

export class ImageHandler {
  constructor(chart) {
    this.chart = chart;
  }

  async downloadImage(
    sourceId,
    name,
    { scale = 1, format = "png", quality = 1 } = {},
  ) {
    const source = d3.select(`#${sourceId}`).node();
    if (!source) throw new Error(`Element with ID ${sourceId} not found`);

    this.chart.renderHandler.render();
    // Ensure WebGL content is captured after rendering
    requestAnimationFrame(() => {
      const file = this.captureWebGLAndSVG(source, scale, format, quality);
      this.startDownload({ file, name, format });
    });
  }

  async getImage(sourceId, { scale = 1, format = "png", quality = 1 } = {}) {
    const source = d3.select(`#${sourceId}`).node();
    if (!source) throw new Error(`Element with ID ${sourceId} not found`);

    this.chart.renderHandler.render();

    return new Promise((resolve) => {
      requestAnimationFrame(() => {
        const file = this.captureWebGLAndSVG(source, scale, format, quality);
        resolve(file);
      });
    });
  }

  async captureWebGLAndSVG(source, scale, format, quality) {
    // Create canvas and set dimensions
    const canvas = document.createElement("canvas");
    const ctxt = canvas.getContext("2d");
    const svgSize = source.getBoundingClientRect();

    canvas.width = svgSize.width * scale;
    canvas.height = svgSize.height * scale;
    canvas.style.width = `${svgSize.width}px`;
    canvas.style.height = `${svgSize.height}px`;

    ctxt.scale(scale, scale);

    // Draw WebGL canvases first
    const canvases = source.querySelectorAll("canvas");
    for (const cnv of canvases) {
      const cnvRect = cnv.getBoundingClientRect();
      try {
        ctxt.drawImage(
          cnv,
          cnvRect.left - svgSize.left,
          cnvRect.top - svgSize.top,
          cnvRect.width,
          cnvRect.height,
        );
      } catch (e) {
        console.error(`Failed to draw canvas: ${e}`);
      }
    }

    // Draw SVG elements on the same canvas
    const svgs = source.querySelectorAll("svg");
    for (const svg of svgs) {
      const svgData = new XMLSerializer().serializeToString(svg);
      const img = document.createElement("img");
      img.setAttribute(
        "src",
        "data:image/svg+xml;base64," +
          btoa(unescape(encodeURIComponent(svgData))),
      );

      await new Promise((resolve) => {
        img.onload = () => {
          const svgRect = svg.getBoundingClientRect();
          ctxt.drawImage(
            img,
            svgRect.left - svgSize.left,
            svgRect.top - svgSize.top,
            svgRect.width,
            svgRect.height,
          );
          resolve();
        };
      });
    }

    // Custom logic to capture HTML elements with text
    // Improved Position Calculation
    const classesToSkip = ["y-axis", "x-axis", "cartesian-chart", "chart"];
    const tagsToSkip = ["text"];
    const elements = source.querySelectorAll("*");

    for (const element of elements) {
      // Skip elements with certain classes or tag names
      if (
        classesToSkip.some((className) =>
          element.classList.contains(className),
        ) ||
        tagsToSkip.includes(element.tagName.toLowerCase())
      ) {
        continue;
      }

      // Now iterate through the child nodes of each element
      element.childNodes.forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          // Check if the node is a text node
          const elementText = child.nodeValue.trim();
          if (elementText) {
            const style = window.getComputedStyle(element);
            const elementRect = element.getBoundingClientRect();
            const font = `${style.fontSize} ${style.fontFamily}`;
            ctxt.font = font;
            ctxt.textBaseline = "top"; // Aligning text from the top

            let x = elementRect.left - svgSize.left;
            let y = elementRect.top - svgSize.top;

            // Adjust position if the element is using flex for centering
            if (style.display === "flex") {
              const justifyContent = style.justifyContent;
              const alignItems = style.alignItems;

              if (
                justifyContent === "center" ||
                justifyContent === "space-around" ||
                justifyContent === "space-evenly"
              ) {
                x +=
                  (elementRect.width - ctxt.measureText(elementText).width) / 2;
              } else if (justifyContent === "flex-end") {
                x += elementRect.width - ctxt.measureText(elementText).width;
              }

              if (alignItems === "center" || alignItems === "baseline") {
                y += (elementRect.height - parseFloat(style.fontSize)) / 2;
              } else if (alignItems === "flex-end") {
                y += elementRect.height - parseFloat(style.fontSize);
              }
            }

            // Draw text
            ctxt.fillText(elementText, x, y);
          }
        }
      });
    }

    // Convert to data URL and trigger download
    return canvas.toDataURL(
      `image/${format === "jpg" ? "jpeg" : format}`,
      quality,
    );
  }

  startDownload({ file, name, format }) {
    const a = document.createElement("a");
    a.download = `${name}.${format}`;
    a.href = file;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
}
