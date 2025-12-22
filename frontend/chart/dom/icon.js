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

export class DOMIconHandler {
  constructor(chart) {
    this.chart = chart;
  }
  getIcon(name) {
    const iconSizes = {
      dots: {
        large: 12,
        small: 12,
      },
      down: {
        large: 12,
        small: 12,
      },
      up: {
        large: 12,
        small: 12,
      },
      back: {
        large: 16,
        small: 21,
      },
      line: {
        large: 16,
        small: 21,
      },
      alert: {
        large: 16,
        small: 20,
      },
      candle: {
        large: 16,
        small: 21,
      },
      settings: {
        large: 12,
        small: 20,
      },
      grid: {
        large: 13,
        small: 18,
      },
      interval: {},
      add: {
        large: 25,
        small: 32,
      },
      drawing: {
        large: 16,
        small: 19,
      },
      save: {
        large: 16,
        small: 19,
      },
      prompt: {
        large: 16,
        small: 19,
      },

      line2: {
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
      ruler: {
        large: 21,
        small: 26,
      },
      fib: {
        large: 15,
        small: 20,
      },
    };

    switch (name) {
      case "dots":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.dots[this.chart.size]}" height="${iconSizes.dots[this.chart.size]}" fill="currentColor" class="bi bi-three-dots" viewBox="0 0 16 16">
  <path d="M3 9.5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3m5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3m5 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3"/>
</svg>`;
      case "dots-loading":
        // Remove stroke to avoid “thick” look; keep small filled circles
        return `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200' width="${iconSizes.dots[this.chart.size]}" height="${iconSizes.dots[this.chart.size]}" fill="currentColor">
    <circle r='15' cx='40' cy='65'>
      <animate attributeName='cy' calcMode='spline' dur='2' values='65;135;65;' keySplines='.5 0 .5 1;.5 0 .5 1' repeatCount='indefinite' begin='-.4'></animate>
    </circle>
    <circle r='15' cx='100' cy='65'>
      <animate attributeName='cy' calcMode='spline' dur='2' values='65;135;65;' keySplines='.5 0 .5 1;.5 0 .5 1' repeatCount='indefinite' begin='-.2'></animate>
    </circle>
    <circle r='15' cx='160' cy='65'>
      <animate attributeName='cy' calcMode='spline' dur='2' values='65;135;65;' keySplines='.5 0 .5 1;.5 0 .5 1' repeatCount='indefinite' begin='0'></animate>
    </circle>
  </svg>`;
      case "down":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.down[this.chart.size]}" height="${iconSizes.down[this.chart.size]}" fill="currentColor" class="bi bi-chevron-down" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708"/>
</svg>`;
      case "up":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.up[this.chart.size]}" height="${iconSizes.up[this.chart.size]}" fill="currentColor" class="bi bi-chevron-up" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M7.646 4.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1-.708.708L8 5.707l-5.646 5.647a.5.5 0 0 1-.708-.708z"/>
</svg>`;
      case "back":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.back[this.chart.size]}" height="${iconSizes.back[this.chart.size]}" fill="currentColor" class="bi bi-arrow-left" viewBox="0 0 16 16">
    <path fill-rule="evenodd" d="M15 8a.5.5 0 0 0-.5-.5H2.707l3.147-3.146a.5.5 0 1 0-.708-.708l-4 4a.5.5 0 0 0 0 .708l4 4a.5.5 0 0 0 .708-.708L2.707 8.5H14.5A.5.5 0 0 0 15 8"/>
    </svg>`;
      case "backRound":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.back[this.chart.size]}" height="${iconSizes.back[this.chart.size]}" fill="currentColor" class="bi bi-arrow-return-left" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M14.5 1.5a.5.5 0 0 1 .5.5v4.8a2.5 2.5 0 0 1-2.5 2.5H2.707l3.347 3.346a.5.5 0 0 1-.708.708l-4.2-4.2a.5.5 0 0 1 0-.708l4-4a.5.5 0 1 1 .708.708L2.707 8.3H12.5A1.5 1.5 0 0 0 14 6.8V2a.5.5 0 0 1 .5-.5"/>
</svg>`;
      case "line":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.line[this.chart.size]}" height="${iconSizes.line[this.chart.size]}" fill="currentColor" class="bi bi-graph-up" viewBox="0 0 16 16">
    <path fill-rule="evenodd" d="M14.817 3.113a.5.5 0 0 1 .07.704l-4.5 5.5a.5.5 0 0 1-.74.037L7.06 6.767l-3.656 5.027a.5.5 0 0 1-.808-.588l4-5.5a.5.5 0 0 1 .758-.06l2.609 2.61 4.15-5.073a.5.5 0 0 1 .704-.07"/>
    </svg>`;
      case "line2":
        return `<svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
         width="${iconSizes.line[this.chart.size]}px" height="${iconSizes.line[this.chart.size]}px" viewBox="0 0 512 512" enable-background="new 0 0 512 512" xml:space="preserve" fill="currentColor">
    <path d="M470,42h-96v71.785l-0.035-0.035L113.75,373.966l0.034,0.034H42v96h96v-71.785l0.035,0.035L398.25,138.035L398.215,138H470
        V42z M125,457H55v-70h70V457z M457,125h-70V55h70V125z"/>
    </svg>`;
      case "horizontalLine":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.horizontalLine[this.chart.size]}" height="${iconSizes.horizontalLine[this.chart.size]}" fill="currentColor" class="bi bi-dash-lg" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M2 8a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11A.5.5 0 0 1 2 8"/>
              </svg>`;
      case "verticalLine":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.verticalLine[this.chart.size]}" height="${iconSizes.verticalLine[this.chart.size]}" fill="currentColor" class="bi bi-dash-lg" viewBox="0 0 16 16">
                <path fill-rule="evenodd" d="M2 8a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11A.5.5 0 0 1 2 8" transform="rotate(90 8 8)"/>
              </svg>`;
      case "candle":
        return `<?xml version="1.0" encoding="utf-8"?><!-- Uploaded to: SVG Repo, www.svgrepo.com, Generator: SVG Repo Mixer Tools -->
    <svg width="${iconSizes.candle[this.chart.size]}px" height="${iconSizes.candle[this.chart.size]}px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M7.5 3.5V6.5" stroke="currentColor" stroke-linecap="round"/>
    <path d="M7.5 14.5V18.5" stroke="currentColor" stroke-linecap="round"/>
    <path d="M6.8 6.5C6.08203 6.5 5.5 7.08203 5.5 7.8V13.2C5.5 13.918 6.08203 14.5 6.8 14.5H8.2C8.91797 14.5 9.5 13.918 9.5 13.2V7.8C9.5 7.08203 8.91797 6.5 8.2 6.5H6.8Z" stroke="currentColor"/>
    <path d="M16.5 6.5V11.5" stroke="currentColor" stroke-linecap="round"/>
    <path d="M16.5 16.5V20.5" stroke="currentColor" stroke-linecap="round"/>
    <path d="M15.8 11.5C15.082 11.5 14.5 12.082 14.5 12.8V15.2C14.5 15.918 15.082 16.5 15.8 16.5H17.2C17.918 16.5 18.5 15.918 18.5 15.2V12.8C18.5 12.082 17.918 11.5 17.2 11.5H15.8Z" stroke="currentColor"/>
    </svg>`;
      case "settings":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.settings[this.chart.size]}" height="${iconSizes.settings[this.chart.size]}" fill="currentColor" class="bi bi-gear" viewBox="0 0 16 16">
  <path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492M5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0"/>
  <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115z"/>
</svg>`;
      case "grid":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.grid[this.chart.size]}" height="${iconSizes.grid[this.chart.size]}" fill="currentColor" class="bi bi-grid-3x3" viewBox="0 0 16 16">
        <path d="M0 1.5A1.5 1.5 0 0 1 1.5 0h13A1.5 1.5 0 0 1 16 1.5v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 14.5zM1.5 1a.5.5 0 0 0-.5.5V5h4V1zM5 6H1v4h4zm1 4h4V6H6zm-1 1H1v3.5a.5.5 0 0 0 .5.5H5zm1 0v4h4v-4zm5 0v4h3.5a.5.5 0 0 0 .5-.5V11zm0-1h4V6h-4zm0-5h4V1.5a.5.5 0 0 0-.5-.5H11zm-1 0V1H6v4z"/>
        </svg>`;
      case "add":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.add[this.chart.size]}" height="${iconSizes.add[this.chart.size]}" fill="currentColor" class="bi bi-plus" viewBox="0 0 16 16">
        <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4"/>
        </svg>`;
      case "brush":
      case "drawing":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.drawing[this.chart.size]}" height="${iconSizes.drawing[this.chart.size]}" fill="currentColor" class="bi bi-brush" width="16px" height="16px" viewBox="0 0 16 16">
      <path d="M15.825.12a.5.5 0 0 1 .132.584c-1.53 3.43-4.743 8.17-7.095 10.64a6.1 6.1 0 0 1-2.373 1.534c-.018.227-.06.538-.16.868-.201.659-.667 1.479-1.708 1.74a8.1 8.1 0 0 1-3.078.132 4 4 0 0 1-.562-.135 1.4 1.4 0 0 1-.466-.247.7.7 0 0 1-.204-.288.62.62 0 0 1 .004-.443c.095-.245.316-.38.461-.452.394-.197.625-.453.867-.826.095-.144.184-.297.287-.472l.117-.198c.151-.255.326-.54.546-.848.528-.739 1.201-.925 1.746-.896q.19.012.348.048c.062-.172.142-.38.238-.608.261-.619.658-1.419 1.187-2.069 2.176-2.67 6.18-6.206 9.117-8.104a.5.5 0 0 1 .596.04M4.705 11.912a1.2 1.2 0 0 0-.419-.1c-.246-.013-.573.05-.879.479-.197.275-.355.532-.5.777l-.105.177c-.106.181-.213.362-.32.528a3.4 3.4 0 0 1-.76.861c.69.112 1.736.111 2.657-.12.559-.139.843-.569.993-1.06a3 3 0 0 0 .126-.75zm1.44.026c.12-.04.277-.1.458-.183a5.1 5.1 0 0 0 1.535-1.1c1.9-1.996 4.412-5.57 6.052-8.631-2.59 1.927-5.566 4.66-7.302 6.792-.442.543-.795 1.243-1.042 1.826-.121.288-.214.54-.275.72v.001l.575.575zm-4.973 3.04.007-.005zm3.582-3.043.002.001h-.002z"/>
    </svg>`;
      case "save":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.save[this.chart.size]}" height="${iconSizes.save[this.chart.size]}" fill="currentColor" class="bi bi-cloud-plus" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M8 5.5a.5.5 0 0 1 .5.5v1.5H10a.5.5 0 0 1 0 1H8.5V10a.5.5 0 0 1-1 0V8.5H6a.5.5 0 0 1 0-1h1.5V6a.5.5 0 0 1 .5-.5"/>
  <path d="M4.406 3.342A5.53 5.53 0 0 1 8 2c2.69 0 4.923 2 5.166 4.579C14.758 6.804 16 8.137 16 9.773 16 11.569 14.502 13 12.687 13H3.781C1.708 13 0 11.366 0 9.318c0-1.763 1.266-3.223 2.942-3.593.143-.863.698-1.723 1.464-2.383m.653.757c-.757.653-1.153 1.44-1.153 2.056v.448l-.445.049C2.064 6.805 1 7.952 1 9.318 1 10.785 2.23 12 3.781 12h8.906C13.98 12 15 10.988 15 9.773c0-1.216-1.02-2.228-2.313-2.228h-.5v-.5C12.188 4.825 10.328 3 8 3a4.53 4.53 0 0 0-2.941 1.1z"/>
</svg>`;
      case "prompt":
        return `<svg role="img" fill="currentColor" width="${iconSizes.prompt[this.chart.size]}" height="${iconSizes.prompt[this.chart.size]}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/></svg>`;
      case "ruler":
        return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 116 116" width="${iconSizes.ruler[this.chart.size]}px" height="${iconSizes.ruler[this.chart.size]}px" fill="currentColor">
      <g transform="translate(128, 0) scale(-1, 1)">
        <path d="M17.89,31.878,31.878,17.89l2.963,2.963-5.481,5.482A1.25,1.25,0,1,0,31.127,28.1l6.365-6.365a1.249,1.249,0,0,0,0-1.767l-4.73-4.731a1.25,1.25,0,0,0-1.768,0L15.238,30.994a1.25,1.25,0,0,0,0,1.768l25.2,25.2a1.25,1.25,0,0,0,1.768-1.768Z"/>
        <path d="M45.633,59.621a1.25,1.25,0,1,0-1.769,1.766l.457.458a1.25,1.25,0,1,0,1.769-1.766Z"/>
        <path d="M108.033,98.2,96.122,110.11,49.131,63.119a1.25,1.25,0,0,0-1.768,1.768l47.875,47.875a1.25,1.25,0,0,0,1.768,0L109.8,99.967a1.25,1.25,0,1,0-1.768-1.768Z"/>
        <path d="M112.762,95.238,96.973,79.449l0,0,0,0-6.6-6.6,0,0,0,0L77.146,59.623l0,0,0,0-6.6-6.6,0,0,0,0-6.6-6.6,0,0,0,0L50.712,33.189l0,0,0,0-6.6-6.6,0,0,0,0-3.424-3.424a1.25,1.25,0,0,0-1.768,1.768l2.542,2.543-2.3,2.3a1.25,1.25,0,1,0,1.767,1.768l2.3-2.3,4.841,4.841-5.481,5.481a1.25,1.25,0,1,0,1.768,1.768l5.481-5.481,4.841,4.841-2.3,2.3a1.25,1.25,0,1,0,1.767,1.768l2.3-2.3,4.841,4.841-5.481,5.481a1.25,1.25,0,1,0,1.768,1.767l5.481-5.481L67.884,53.9l-2.3,2.3a1.25,1.25,0,1,0,1.768,1.768l2.3-2.3L74.493,60.5l-5.481,5.481a1.25,1.25,0,1,0,1.768,1.767l5.481-5.481L81.1,67.113l-2.3,2.3A1.25,1.25,0,1,0,80.57,71.18l2.3-2.3,4.841,4.841L82.229,79.2A1.25,1.25,0,1,0,84,80.971l5.481-5.481,4.841,4.841-2.3,2.3A1.25,1.25,0,1,0,93.788,84.4l2.3-2.3,4.841,4.841-2.3,2.3a1.25,1.25,0,1,0,1.768,1.768l2.3-2.3,8.3,8.3a1.25,1.25,0,0,0,1.768-1.768Z"/>
        <path d="M97.214,94.189,97.7,93.7a1.25,1.25,0,0,0-1.768-1.768l-.487.487a1.25,1.25,0,1,0,1.768,1.768Z"/>
      </g>
    </svg>`;
      case "alert":
        return `<svg xmlns="http://www.w3.org/2000/svg" width="${iconSizes.alert[this.chart.size]}" height="${iconSizes.alert[this.chart.size]}" fill="currentColor" class="bi bi-bell" viewBox="0 0 16 16">
  <path d="M8 16a2 2 0 0 0 2-2H6a2 2 0 0 0 2 2M8 1.918l-.797.161A4 4 0 0 0 4 6c0 .628-.134 2.197-.459 3.742-.16.767-.376 1.566-.663 2.258h10.244c-.287-.692-.502-1.49-.663-2.258C12.134 8.197 12 6.628 12 6a4 4 0 0 0-3.203-3.92zM14.22 12c.223.447.481.801.78 1H1c.299-.199.557-.553.78-1C2.68 10.2 3 6.88 3 6c0-2.42 1.72-4.44 4.005-4.901a1 1 0 1 1 1.99 0A5 5 0 0 1 13 6c0 .88.32 4.2 1.22 6"/>
</svg>`;
      case "fib":
        return `<svg
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
             </svg>`;
    }
  }
}
