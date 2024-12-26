/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

function parent(element) {
  return element.node().parentNode;
}

export class DOMAlertRuleHandler {
  constructor(chart) {
    this.chart = chart;
    this.step = "constructed";
    this.nextAvailableRuleId = 1;
    this.rules = {};

    const dataKeys = this.chart.dataProvider.config.data.filter(
      (obj) => obj.type === "data",
    );
    this._data = this.extractUniqueDataKeys(
      dataKeys,
      Object.keys(this.chart.dataProvider.keyToData),
    );

    const indicators = this.chart.dataProvider.config.data.filter(
      (obj) => obj.type === "indicator",
    );
    this._indicators = {};
    for (let j = 0; j < indicators.length; j++) {
      const i = indicators[j];
      const inputText = Object.entries(i.inputs)
        .map(([key, value]) => `${key}=${value}`)
        .join(", ");
      const name = `${i.indicator.name} ${inputText}`;
      this._indicators[name] = {
        indicator: i,
        outputs: i.indicator.details.outputs,
      };
    }
  }

  token() {
    this.chart.dataProvider.getVapidPublicKey((data) => {
      function urlB64ToUint8Array(base64String) {
        const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
        const base64 = (base64String + padding)
          .replace(/\-/g, "+")
          .replace(/_/g, "/");

        const rawData = window.atob(base64);
        const outputArray = Uint8Array.from(
          [...rawData].map((char) => char.charCodeAt(0)),
        );

        return outputArray;
      }

      const applicationServerKey = urlB64ToUint8Array(data.publicKey);

      if ("serviceWorker" in navigator && "PushManager" in window) {
        const that = this;
        navigator.serviceWorker
          .register("/service-worker.js")
          .then(function (registration) {
            console.log(
              "Service Worker registered with scope:",
              registration.scope,
            );

            registration.pushManager
              .getSubscription()
              .then(function (subscription) {
                if (subscription) {
                  console.log("Already subscribed:", subscription);
                  that.chart.dataProvider.subscription = subscription;
                  return;
                }

                return registration.pushManager
                  .subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: applicationServerKey,
                  })
                  .then(function (subscription) {
                    console.log("User is subscribed:", subscription);
                    that.chart.dataProvider.subscription = subscription;
                  })
                  .catch(function (error) {
                    console.error("Failed to subscribe:", error);
                  });
              });
          })
          .catch(function (error) {
            console.error("Service Worker registration failed:", error);
          });
      } else {
        console.warn("Service Workers or Push API not supported");
      }
    });
  }

  getRule(ruleId) {
    const ruleSelector = `.alert-rules .rule-${ruleId}`;
    const elements = this.chart.d3ContainerEl.selectAll(
      `${ruleSelector} input, ${ruleSelector} select`,
    );
    const ruleData = {};

    elements.each(function () {
      const element = d3.select(this);
      const dataKey = element.attr("data-key");
      let value;

      if (element.node().tagName === "INPUT") {
        if (
          element.attr("type") === "checkbox" ||
          element.attr("type") === "radio"
        ) {
          value = element.property("checked");
        } else {
          value = element.property("value");
        }
      } else if (element.node().tagName === "SELECT") {
        value = element.property("value");
      }

      if (dataKey) {
        ruleData[dataKey] = value;
      }
    });

    return ruleData;
  }

  count(cls) {
    return this.chart.d3ContainerEl.selectAll(`.${cls}`).size() + 1;
  }

  countRulePart(ruleId) {
    const cls = "rule-type";
    const numOfTypes = this.chart.d3ContainerEl
      .selectAll(`.rule-${ruleId} .${cls}`)
      .size();
    if (numOfTypes <= 1) {
      return "1";
    } else {
      return "2";
    }
  }

  countPerRule(ruleId, cls) {
    return (
      this.chart.d3ContainerEl.selectAll(`.rule-${ruleId} .${cls}`).size() + 1
    );
  }

  createOperator(rulesEl) {
    const operators = ["and", "or"];

    const inputGroup = rulesEl
      .append("div")
      .attr("class", "input-group operator")
      .style("margin", "10px 7px 10px 7px");

    inputGroup.append("label").text("Operator");

    const count = this.count("rule-operator");
    const select = inputGroup
      .append("select")
      .attr("class", "rule-operator")
      .attr("data-key", `operator${count}`);

    // Add option elements to the select element in a loop
    operators.forEach((o) => {
      const option = select.append("option").attr("value", o).text(o);
    });
  }

  createControls(ruleId) {
    const cntrls = this.rules[ruleId].container
      .append("div")
      .attr("class", "controls");

    cntrls.append("p").attr("class", "title").text(`Rule #${ruleId}`);

    cntrls
      .append(`input`)
      .attr("type", "button")
      .attr("value", `Remove rule #${ruleId}`)
      .on("click", () => {
        const el = this.rules[ruleId].container.node();
        let operatorEl = el.nextSibling;
        if (!operatorEl) {
          operatorEl = el.previousSibling;
        }
        if (operatorEl && operatorEl.classList.contains("operator")) {
          const parent = operatorEl.parentNode;
          parent.removeChild(operatorEl);
        }

        const parent = el.parentNode;
        parent.removeChild(el);

        delete this.rules[ruleId];
      });
  }

  extractUniqueDataKeys(data, keys) {
    const sources = {};

    for (const key in data) {
      const { source, name, interval } = data[key];

      if (!sources[source]) {
        sources[source] = {
          names: new Set(),
          intervals: new Set(),
          keys: new Set(),
        };
      }

      sources[source].names.add(name);
      sources[source].intervals.add(interval);

      for (let i = 0; i < keys.length; i++) {
        if (keys[i].startsWith(`${source}-${name}`)) {
          const k = keys[i].split("-").splice(3).join("-");
          sources[source].keys.add(k);
        }
      }
    }

    // Convert Sets to Arrays for easier use
    for (const source in sources) {
      sources[source].names = Array.from(sources[source].names);
      sources[source].intervals = Array.from(sources[source].intervals);
      sources[source].keys = Array.from(sources[source].keys);
    }

    return sources;
  }

  createTypeEl(ruleId) {
    const ruleObj = this.getRule(ruleId);

    const types = ["data"];
    if (Object.keys(this._indicators).length) {
      types.push("indicator");
    }
    types.push("value");

    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Type");

    const count = this.countPerRule(ruleId, "rule-type");
    const select = inputGroup
      .append("select")
      .attr("class", "rule-type")
      .attr("data-key", `type${count}`);

    let defaultType = "data";
    if (ruleObj[`type${count - 1}`] === "data") {
      defaultType = "value";
    }

    // Add option elements to the select element in a loop
    types.forEach((t) => {
      const option = select.append("option").attr("value", t).text(t);

      if (defaultType === t) {
        option.attr("selected", "selected");
      }
    });

    const onTypeChange = this.onTypeChange(ruleId, select);
    onTypeChange();
    select.on("change", onTypeChange);
  }

  createSourceEl(ruleId) {
    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Source");

    const count = this.countRulePart(ruleId);
    const select = inputGroup
      .append("select")
      .attr("class", "rule-source")
      .attr("data-key", `source${count}`);

    // Add option elements to the select element in a loop
    Object.keys(this._data).forEach((source) => {
      select.append("option").attr("value", source).text(source);
    });

    const onSourceChange = this.onSourceChange(ruleId, select);
    onSourceChange();
    select.on("change", onSourceChange);
  }

  createNameEl(ruleId) {
    const ruleObj = this.getRule(ruleId);

    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Name");

    const count = this.countRulePart(ruleId);
    const select = inputGroup
      .append("select")
      .attr("class", "rule-name")
      .attr("data-key", `name${count}`);

    // Add option elements to the select element in a loop
    this._data[ruleObj[`source${count}`]].names.forEach((name) => {
      select.append("option").attr("value", name).text(name);
    });

    const onNameChange = this.onNameChange(ruleId, select);
    onNameChange();
    select.on("change", onNameChange);
  }

  createIntervalEl(ruleId) {
    const intervals = [
      "1m",
      "5m",
      "15m",
      "30m",
      "1h",
      "2h",
      "3h",
      "4h",
      "6h",
      "8h",
      "12h",
      "1d",
      "3d",
      "1w",
      "1M",
    ];

    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Interval");

    const count = this.countRulePart(ruleId);
    const select = inputGroup
      .append("select")
      .attr("class", "rule-interval")
      .attr("data-key", `interval${count}`);

    const defaultInterval = this.chart.dataProvider.interval;

    // Add option elements to the select element in a loop
    intervals.forEach((interval) => {
      const option = select
        .append("option")
        .attr("value", interval)
        .text(interval);

      if (defaultInterval && interval === defaultInterval) {
        option.attr("selected", "selected");
      }
    });

    const onIntervalChange = this.onIntervalChange(ruleId, select);
    onIntervalChange();
    select.on("change", onIntervalChange);
  }

  createKeyEl(ruleId) {
    const ruleObj = this.getRule(ruleId);

    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Key");

    const count = this.countRulePart(ruleId);
    const select = inputGroup
      .append("select")
      .attr("class", "rule-key")
      .attr("data-key", `key${count}`);

    // Add option elements to the select element in a loop
    this._data[ruleObj[`source${count}`]].keys.forEach((k) => {
      const option = select.append("option").attr("value", k).text(k);

      if (k === "close") {
        option.attr("selected", "selected");
      }
    });

    const onKeyChange = this.onKeyChange(ruleId, select);
    onKeyChange();
    select.on("change", onKeyChange);
  }

  createComparatorEl(ruleId) {
    const ruleObj = this.getRule(ruleId);

    if (ruleObj.comparator) {
      return;
    }

    const actions = ["<", ">", "near"];

    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Comparator");

    const select = inputGroup
      .append("select")
      .attr("class", "rule-comparator")
      .attr("data-key", `comparator`);

    // Add option elements to the select element in a loop
    actions.forEach((action) => {
      select.append("option").attr("value", action).text(action);
    });

    const onComparatorChange = this.onComparatorChange(ruleId, select);
    onComparatorChange();
    select.on("change", onComparatorChange);
  }
  createIndicatorEl(ruleId) {
    const ruleObj = this.getRule(ruleId);

    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Indicator");

    const count = this.countRulePart(ruleId);
    const select = inputGroup
      .append("select")
      .attr("class", "rule-indicator")
      .attr("data-key", `indicator${count}`);

    // Add option elements to the select element in a loop
    Object.keys(this._indicators).forEach((k) => {
      select.append("option").attr("value", k).text(k);
    });

    const onIndicatorChange = this.onIndicatorChange(ruleId, select);
    onIndicatorChange();
    select.on("change", onIndicatorChange);
  }
  createIndicatorIntervalEl(ruleId) {
    const ruleObj = this.getRule(ruleId);
    const intervals = [
      "1m",
      "5m",
      "15m",
      "30m",
      "1h",
      "2h",
      "3h",
      "4h",
      "6h",
      "8h",
      "12h",
      "1d",
      "3d",
      "1w",
      "1M",
    ];

    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Interval");

    const count = this.countRulePart(ruleId);
    const select = inputGroup
      .append("select")
      .attr("class", "rule-indicator-interval")
      .attr("data-key", `indicator_interval${count}`);

    let defaultInterval = null;

    const dm = this._indicators[ruleObj[`indicator${count}`]].indicator.dataMap;
    Object.keys(dm).forEach((k) => {
      if (dm[k].interval) {
        defaultInterval = dm[k].interval;
      }
    });

    // Add option elements to the select element in a loop
    intervals.forEach((interval) => {
      const option = select
        .append("option")
        .attr("value", interval)
        .text(interval);

      if (defaultInterval && interval === defaultInterval) {
        option.attr("selected", "selected");
      }
    });

    const onIndicatorIntervalChange = this.onIndicatorIntervalChange(
      ruleId,
      select,
    );
    onIndicatorIntervalChange();
    select.on("change", onIndicatorIntervalChange);
  }

  createIndicatorDetailEl(ruleId) {
    const ruleObj = this.getRule(ruleId);

    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Data");

    const count = this.countRulePart(ruleId);
    let descr = `<table>
        <thead>
        <tr>
            <td>Data</td>
            <td>Source</td>
            <td>Symbol</td>
            <td>Key</td>
        </tr>
        </thead>
        <tbody>`;
    const dm = this._indicators[ruleObj[`indicator${count}`]].indicator.dataMap;
    Object.keys(dm).forEach((k) => {
      descr += `<tr>
                <td>${k}</td>
                <td>${dm[k].source}</td>
                <td>${dm[k].name}</td>
                <td>${dm[k].dataKey}</td>
            </tr>`;
    });

    descr += "</tbody></table>";

    const p = inputGroup.append("p").attr("class", "input-info").html(descr);

    const onIndicatorDetailChange = this.onIndicatorDetailChange(ruleId, p);
    onIndicatorDetailChange();
  }

  createOutputEl(ruleId) {
    const ruleObj = this.getRule(ruleId);

    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Output");

    const count = this.countRulePart(ruleId);
    const select = inputGroup
      .append("select")
      .attr("class", "rule-output")
      .attr("data-key", `output${count}`);

    // Add option elements to the select element in a loop
    this._indicators[ruleObj[`indicator${count}`]].outputs.forEach((k) => {
      select.append("option").attr("value", k.name).text(k.name);
    });

    const onOutputChange = this.onOutputChange(ruleId, select);
    onOutputChange();
    select.on("change", onOutputChange);
  }

  createValueEl(ruleId) {
    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("Value");

    const count = this.countRulePart(ruleId);
    const select = inputGroup
      .append("input")
      .attr("type", "number")
      .attr("class", "rule-value")
      .attr("data-key", `value${count}`);

    const onValueChange = this.onValueChange(ruleId, select);
    onValueChange();
    select.on("change", onValueChange);
  }
  createNearEl(ruleId) {
    const inputGroup = this.rules[ruleId].container
      .append("div")
      .attr("class", "input-group");

    inputGroup.append("label").text("%");

    const select = inputGroup
      .append("input")
      .attr("type", "number")
      .attr("class", "rule-near")
      .attr("data-key", `near`);

    const onNearChange = this.onNearChange(ruleId, select);
    onNearChange();
    select.on("change", onNearChange);
  }

  removeAllElementsAfter(element) {
    const ruleEl = element.parentNode;

    let nodesToRemove = [];
    let nextElement = element.nextSibling;

    // Collect all nodes to be removed
    while (nextElement) {
      nodesToRemove.push(nextElement);
      nextElement = nextElement.nextSibling;
    }

    // Remove collected nodes
    nodesToRemove.forEach((node) => {
      ruleEl.removeChild(node);
    });
  }

  onTypeChange(ruleId, select) {
    return () => {
      this.removeAllElementsAfter(parent(select));

      switch (select.property("value")) {
        case "data":
          this.createSourceEl(ruleId);

          break;
        case "indicator":
          this.createIndicatorEl(ruleId);

          break;
        case "value":
          this.createValueEl(ruleId);

          break;
      }
    };
  }
  onSourceChange(ruleId, select) {
    return () => {
      this.removeAllElementsAfter(parent(select));

      this.createNameEl(ruleId);
    };
  }
  onIndicatorChange(ruleId, select) {
    return () => {
      this.removeAllElementsAfter(parent(select));

      this.createIndicatorDetailEl(ruleId);
    };
  }
  onIndicatorDetailChange(ruleId, select) {
    return () => {
      this.removeAllElementsAfter(parent(select));

      this.createIndicatorIntervalEl(ruleId);
    };
  }
  onIndicatorIntervalChange(ruleId, select) {
    return () => {
      this.removeAllElementsAfter(parent(select));

      this.createOutputEl(ruleId);
    };
  }
  onNameChange(ruleId, select) {
    return () => {
      const name = select.property("value");
      this.removeAllElementsAfter(parent(select));

      this.createIntervalEl(ruleId);
    };
  }
  onIntervalChange(ruleId, select) {
    return () => {
      this.removeAllElementsAfter(parent(select));

      this.createKeyEl(ruleId);
    };
  }
  onKeyChange(ruleId, select) {
    return () => {
      this.removeAllElementsAfter(parent(select));

      this.createComparatorEl(ruleId);
    };
  }
  onOutputChange(ruleId, select) {
    return () => {
      this.removeAllElementsAfter(parent(select));

      this.createComparatorEl(ruleId);
    };
  }
  onValueChange(ruleId, select) {
    return () => {
      this.removeAllElementsAfter(parent(select));

      this.createComparatorEl(ruleId);
    };
  }
  onNearChange(ruleId, input) {
    return () => {
      this.removeAllElementsAfter(parent(input));

      const ruleObj = this.getRule(ruleId);
      if (!ruleObj.type2) {
        // second side
        this.createTypeEl(ruleId);
      }
    };
  }

  onComparatorChange(ruleId, select) {
    return () => {
      const action = select.property("value");
      this.removeAllElementsAfter(parent(select));

      if (action === "near") {
        this.createNearEl(ruleId);
      } else {
        const ruleObj = this.getRule(ruleId);
        if (!ruleObj.type2) {
          // second side
          this.createTypeEl(ruleId);
        }
      }
    };
  }

  initialize(rulesEl) {
    const ruleId = this.nextAvailableRuleId;
    this.nextAvailableRuleId += 1;

    const rule = rulesEl
      .append("div")
      .attr("class", `rule rule-${ruleId}`)
      .attr("data-rule", `${ruleId}`);

    this.rules[ruleId] = {};
    this.rules[ruleId].container = rule;

    this.createControls(ruleId);
    this.createTypeEl(ruleId);
  }
}
