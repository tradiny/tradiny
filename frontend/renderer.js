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

import addTmpl from "./templates/add.html";
import alertTmpl from "./templates/alert.html";
import settingsTmpl from "./templates/settings.html";

import dataSearchResultsTmpl from "./templates/data-search-results.html";
import dataTmpl from "./templates/data.html";
import dataTableTmpl from "./templates/data-table.html";

import indicatorsSearchResultsTmpl from "./templates/indicators-search-results.html";
import indicatorTmpl from "./templates/indicator.html";

import lineTmpl from "./templates/line.html";
import textTmpl from "./templates/text.html";
import saveTmpl from "./templates/save.html";

import alertRuleTmpl from "./templates/alert-rule.html";

import promptTmpl from "./templates/prompt.html";

const templateCache = {
  add: addTmpl,
  settings: settingsTmpl,

  "data-search-results": dataSearchResultsTmpl,
  data: dataTmpl,
  "data-table": dataTableTmpl,

  "indicators-search-results": indicatorsSearchResultsTmpl,
  indicator: indicatorTmpl,

  line: lineTmpl,
  text: textTmpl,
  save: saveTmpl,

  alert: alertTmpl,
  "alert-rule": alertRuleTmpl,
  prompt: promptTmpl,
};

export class Renderer {
  constructor(chart) {
    this.chart = chart;
  }

  render(template, object, callback) {
    if (template in templateCache) {
      const rawData = templateCache[template];
      callback(tmpl(rawData, object));
    } else {
      const request = d3.text(`templates/${template}.html`, {
        method: "GET",
        // headers: { "Content-Type": "application/x-www-form-urlencoded" },
        // body: "entry=" + JSON.stringify(playerData)
      });
      request.then((rawData) => {
        templateCache[template] = rawData;

        callback(tmpl(rawData, object));
      });
    }
  }
  openTab(evt, tabName) {
    var chartEl = d3.select("#" + this.chart.elementId);
    chartEl.selectAll(".tabcontent").style("display", "none");
    chartEl.selectAll(".tablinks").classed("active", false);
    chartEl.select("." + tabName).style("display", "block");
    d3.select(evt.currentTarget).classed("active", true);
  }
}
