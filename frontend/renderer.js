/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

import addTmpl from "./templates/add.html";
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
