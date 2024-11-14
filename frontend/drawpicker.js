/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

export class DrawPicker {
  constructor(domHandler) {
    this.domHandler = domHandler;
    this.chart = domHandler.chart;

    const iconSizes = {
      line: {
        large: 18,
        small: 23,
      },
      horizontalLine: {
        large: 21,
        small: 26,
      },
      verticalLine: {
        large: 21,
        small: 26,
      },
      brush: {
        large: 16,
        small: 20,
      },
      ruler: {
        large: 21,
        small: 26,
      },
      fib: {
        large: 15,
        small: 20,
      },
      back: {
        large: 16,
        small: 20,
      },
    };

    this.controls = {
      "control-back": {
        className: "control-back-icon",
        onClick: () => {
          this.closeControls();
        },
        innerHTML: this.domHandler.getIcon("back"),
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
        innerHTML: `<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
         width="${iconSizes.line[this.chart.size]}px" height="${iconSizes.line[this.chart.size]}px" viewBox="0 0 512 512" enable-background="new 0 0 512 512" xml:space="preserve" fill="currentColor">
    <path d="M470,42h-96v71.785l-0.035-0.035L113.75,373.966l0.034,0.034H42v96h96v-71.785l0.035,0.035L398.25,138.035L398.215,138H470
        V42z M125,457H55v-70h70V457z M457,125h-70V55h70V125z"/>
    </svg>`,
      },
      "horizontal-line": {
        className: "horizontal-line-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("horizontal-line");
        },
        innerHTML: `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.horizontalLine[this.chart.size]}" height="${iconSizes.horizontalLine[this.chart.size]}" fill="currentColor" class="bi bi-dash-lg" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M2 8a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11A.5.5 0 0 1 2 8"/>
              </svg>`,
      },
      "vertical-line": {
        className: "vertical-line-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("vertical-line");
        },
        innerHTML: `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.verticalLine[this.chart.size]}" height="${iconSizes.verticalLine[this.chart.size]}" fill="currentColor" class="bi bi-dash-lg" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M2 8a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11A.5.5 0 0 1 2 8" transform="rotate(90 8 8)"/>
              </svg>`,
      },
      brush: {
        className: "brush-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("brush");
        },
        innerHTML: `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.brush[this.chart.size]}" height="${iconSizes.brush[this.chart.size]}" fill="currentColor" class="bi bi-brush" width="16px" height="16px" viewBox="0 0 16 16">
      <path d="M15.825.12a.5.5 0 0 1 .132.584c-1.53 3.43-4.743 8.17-7.095 10.64a6.1 6.1 0 0 1-2.373 1.534c-.018.227-.06.538-.16.868-.201.659-.667 1.479-1.708 1.74a8.1 8.1 0 0 1-3.078.132 4 4 0 0 1-.562-.135 1.4 1.4 0 0 1-.466-.247.7.7 0 0 1-.204-.288.62.62 0 0 1 .004-.443c.095-.245.316-.38.461-.452.394-.197.625-.453.867-.826.095-.144.184-.297.287-.472l.117-.198c.151-.255.326-.54.546-.848.528-.739 1.201-.925 1.746-.896q.19.012.348.048c.062-.172.142-.38.238-.608.261-.619.658-1.419 1.187-2.069 2.176-2.67 6.18-6.206 9.117-8.104a.5.5 0 0 1 .596.04M4.705 11.912a1.2 1.2 0 0 0-.419-.1c-.246-.013-.573.05-.879.479-.197.275-.355.532-.5.777l-.105.177c-.106.181-.213.362-.32.528a3.4 3.4 0 0 1-.76.861c.69.112 1.736.111 2.657-.12.559-.139.843-.569.993-1.06a3 3 0 0 0 .126-.75zm1.44.026c.12-.04.277-.1.458-.183a5.1 5.1 0 0 0 1.535-1.1c1.9-1.996 4.412-5.57 6.052-8.631-2.59 1.927-5.566 4.66-7.302 6.792-.442.543-.795 1.243-1.042 1.826-.121.288-.214.54-.275.72v.001l.575.575zm-4.973 3.04.007-.005zm3.582-3.043.002.001h-.002z"/>
    </svg>`,
      },
      ruler: {
        className: "ruler-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("ruler");
        },
        innerHTML: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 116 116" width="${iconSizes.ruler[this.chart.size]}px" height="${iconSizes.ruler[this.chart.size]}px" fill="currentColor">
      <g transform="translate(128, 0) scale(-1, 1)">
        <path d="M17.89,31.878,31.878,17.89l2.963,2.963-5.481,5.482A1.25,1.25,0,1,0,31.127,28.1l6.365-6.365a1.249,1.249,0,0,0,0-1.767l-4.73-4.731a1.25,1.25,0,0,0-1.768,0L15.238,30.994a1.25,1.25,0,0,0,0,1.768l25.2,25.2a1.25,1.25,0,0,0,1.768-1.768Z"/>
        <path d="M45.633,59.621a1.25,1.25,0,1,0-1.769,1.766l.457.458a1.25,1.25,0,1,0,1.769-1.766Z"/>
        <path d="M108.033,98.2,96.122,110.11,49.131,63.119a1.25,1.25,0,0,0-1.768,1.768l47.875,47.875a1.25,1.25,0,0,0,1.768,0L109.8,99.967a1.25,1.25,0,1,0-1.768-1.768Z"/>
        <path d="M112.762,95.238,96.973,79.449l0,0,0,0-6.6-6.6,0,0,0,0L77.146,59.623l0,0,0,0-6.6-6.6,0,0,0,0-6.6-6.6,0,0,0,0L50.712,33.189l0,0,0,0-6.6-6.6,0,0,0,0-3.424-3.424a1.25,1.25,0,0,0-1.768,1.768l2.542,2.543-2.3,2.3a1.25,1.25,0,1,0,1.767,1.768l2.3-2.3,4.841,4.841-5.481,5.481a1.25,1.25,0,1,0,1.768,1.768l5.481-5.481,4.841,4.841-2.3,2.3a1.25,1.25,0,1,0,1.767,1.768l2.3-2.3,4.841,4.841-5.481,5.481a1.25,1.25,0,1,0,1.768,1.767l5.481-5.481L67.884,53.9l-2.3,2.3a1.25,1.25,0,1,0,1.768,1.768l2.3-2.3L74.493,60.5l-5.481,5.481a1.25,1.25,0,1,0,1.768,1.767l5.481-5.481L81.1,67.113l-2.3,2.3A1.25,1.25,0,1,0,80.57,71.18l2.3-2.3,4.841,4.841L82.229,79.2A1.25,1.25,0,1,0,84,80.971l5.481-5.481,4.841,4.841-2.3,2.3A1.25,1.25,0,1,0,93.788,84.4l2.3-2.3,4.841,4.841-2.3,2.3a1.25,1.25,0,1,0,1.768,1.768l2.3-2.3,8.3,8.3a1.25,1.25,0,0,0,1.768-1.768Z"/>
        <path d="M97.214,94.189,97.7,93.7a1.25,1.25,0,0,0-1.768-1.768l-.487.487a1.25,1.25,0,1,0,1.768,1.768Z"/>
      </g>
    </svg>`,
      },
      fib: {
        className: "fib-icon",
        onClick: () => {
          this.chart.drawingHandler.toggle("fib");
        },
        innerHTML: `<svg
                xmlns:svg="http://www.w3.org/2000/svg"
                xmlns="http://www.w3.org/2000/svg"
                version="1.0"
                height="${iconSizes.fib[this.chart.size]}"
                width="${iconSizes.fib[this.chart.size]}"
                viewBox="0 0 915 580">
               <style>
                 .thick-stroke {
                   opacity: 1.0;
                   fill: none;
                   fill-opacity: 1;
                   fill-rule: nonzero;
                   stroke: currentColor;
                   stroke-linejoin: miter;
                   stroke-miterlimit: 4;
                   stroke-dasharray: none;
                   stroke-opacity: 1;
                   stroke-width: 50px;
                 }
               </style>
               <path
                  d="M 18.898132,563.14957 A 543.94263,543.75146 0 0 1 562.84077,19.398132"
                  id="path1873"
                  class="thick-stroke" />
               <path
                  class="thick-stroke"
                  id="path1875"
                  d="M -899.02731,355.46605 A 336.18655,336.06839 0 0 1 -562.84075,19.397675"
                  transform="scale(-1,1)" />
               <path
                  transform="matrix(0,-1,-1,0,0,0)"
                  d="m -563.14906,-691.27235 a 207.68251,207.75557 0 0 1 207.68251,-207.75556"
                  id="path2762"
                  class="thick-stroke" />
               <path
                  class="thick-stroke"
                  id="path2764"
                  d="M 562.84128,-434.76319 A 128.43051,128.38536 0 0 1 691.27179,-563.14854"
                  transform="scale(1,-1)" />
               <path
                  d="m 562.84184,434.7637 a 79.324539,79.296654 0 0 1 79.32454,-79.29665"
                  id="path2766"
                  class="thick-stroke" />
               <path
                  class="thick-stroke"
                  id="path2768"
                  d="m -691.27137,404.55478 a 49.105476,49.088211 0 0 1 49.10548,-49.08821"
                  transform="scale(-1,1)" />
               <path
                  transform="scale(-1)"
                  d="m -691.27178,-404.55426 a 30.218561,30.207939 0 0 1 30.21856,-30.20794"
                  id="path2770"
                  class="thick-stroke" />
               <path
                  class="thick-stroke"
                  id="path2772"
                  d="m 642.16632,-415.8829 a 18.886414,18.879776 0 0 1 18.88641,-18.87978"
                  transform="scale(1,-1)" />
               <path
                  d="m 642.16683,415.88342 a 11.331649,11.327665 0 0 1 11.33164,-11.32766"
                  id="path2774"
                  class="thick-stroke" />
               <path
                  id="rect2784"
                  d="M 653.49848,415.88344 V 404.55528"
                  class="thick-stroke" />
               <path
                  id="rect2786"
                  d="M 661.05275,415.88294 H 642.16583"
                  class="thick-stroke" />
               <path
                  id="rect2788"
                  d="m 653.49798,412.10688 h 7.55477"
                  class="thick-stroke" />
               <path
                  id="rect2790"
                  d="m 657.27586,412.10738 v 3.77606"
                  class="thick-stroke" />
             </svg>`,
      },
      back: {
        className: "back-icon",
        onClick: () => {
          this.chart.back();
        },
        innerHTML: `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.back[this.chart.size]}" height="${iconSizes.back[this.chart.size]}" fill="currentColor" class="bi bi-arrow-return-left" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M14.5 1.5a.5.5 0 0 1 .5.5v4.8a2.5 2.5 0 0 1-2.5 2.5H2.707l3.347 3.346a.5.5 0 0 1-.708.708l-4.2-4.2a.5.5 0 0 1 0-.708l4-4a.5.5 0 1 1 .708.708L2.707 8.3H12.5A1.5 1.5 0 0 0 14 6.8V2a.5.5 0 0 1 .5-.5"/>
</svg>`,
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
