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

import { Utils } from "./utils.js";

import { WebSocketManager } from "../ws.js";

export class DataProvider {
  constructor(chart, config) {
    this.chart = chart;
    this.config = config;
    this._updateDataCount();
    this._onReady = [];
    this._connected = false;
    this._onConnect = [];
    this._onUpdated = [];
    this._onData = {};
    this._onIndicatorData = {};
    this.keyToData = {};
    this.keyToMetadata = {};
    this.keyToAxis = {};
    this.widths = {};
    this.dividers = {};
    this.dividersPerAxis = {};
    this.data = null;
    this.interval = null;
    this.subscription = null;
    this.disable = false;
    this._indicatorsOnDataInitAdded = false;
    this.indicatorsToAddOnDataInit = [];

    if (config && config.data) {
      // extract interval
      for (let i = 0; i < this.config.data.length; i++) {
        // on init, define interval
        const d = this.config.data[i];
        if (d.interval) {
          this.interval = d.interval;
          break;
        }
      }
    } else if (config) {
      this.config.data = [];
    }

    if (!this.interval) {
      this.interval = "1h"; // if no interval is specified
    }

    if (config && config.url) {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      this.config.full_url = `${protocol}//${config.url}/websocket/`;
      this.initServerConnection();
    }
  }

  prepareAnnotations(annotations) {
    this.chart.drawingData =
      this.chart.saveHandler.unserializeDrawing(annotations);
  }

  prepareData(data) {
    let newIndexesAdded = 0;
    let shift = 0;

    // Initialize or update the dateToIndexMap and data array
    if (!this.data) {
      this.dateToIndexMap = new Map();
      this.data = [];
    }

    // Extract existing dates
    const existingDates = new Set(this.dateToIndexMap.keys());

    // New data map to quickly lookup new data by date
    const dateToDataMap = new Map();
    data.forEach((d) => dateToDataMap.set(d.date, d));

    // Create a combined set of all dates and sort them
    const allDates = new Set([...dateToDataMap.keys(), ...existingDates]);
    const sortedDates = Array.from(allDates).sort(); // should be sorted already

    // Create new arrays for the sorted data and index map
    const mergedData = new Array(sortedDates.length);
    const newDateToIndexMap = new Map();

    // Determine updated keys
    let keysUpdated = [];
    if (data.length) {
      keysUpdated = Object.keys(data[0]).filter(
        (k) => !["date", "_date", "_dateObj"].includes(k),
      );
    }
    let newKeys = [];
    for (let i = 0; i < keysUpdated.length; i++) {
      if (!(keysUpdated[i] in this.data)) {
        newKeys.push(keysUpdated[i]);
      }
    }
    for (let i = 0; i < this.chart.panes.length; i++) {
      for (let j = 0; j < this.chart.panes[i].metadata.length; j++) {
        const meta = this.chart.panes[i].metadata[j];
        for (let k = 0; k < meta.dataKeys.length; k++) {
          const dataKey = meta.dataKeys[k].dataKey;
          const yAxis = meta.dataKeys[k].yAxis;
          this.keyToAxis[dataKey] = yAxis;
        }
      }
    }

    // set dividers
    this.setDividers(data);
    let newData;

    // Merge data based on sorted dates
    sortedDates.forEach((date, index) => {
      newDateToIndexMap.set(date, index);

      const existingIndex = this.dateToIndexMap.get(date);
      newData = dateToDataMap.get(date);

      if (newData !== undefined) {
        newData = this.divide(newData, keysUpdated);
      }

      if (existingIndex !== undefined && this.data[existingIndex]) {
        if (newData !== undefined) {
          mergedData[index] = {
            ...this.data[existingIndex],
            ...newData,
            date: index,
            _date: date,
            _dateObj: Utils.toDate(date),
          };
          const newKeys = Object.keys(newData);
          if (!(newKeys[newKeys.length - 1] in this.data[existingIndex])) {
            newIndexesAdded++;
          }
        } else {
          mergedData[index] = {
            ...this.data[existingIndex],
            date: index,
            _date: date,
            _dateObj: Utils.toDate(date),
          };
        }
        this.data[existingIndex] = undefined; // release memory
      } else if (newData !== undefined) {
        mergedData[index] = {
          ...newData,
          date: index,
          _date: date,
          _dateObj: Utils.toDate(date),
        };
        newIndexesAdded++;
        shift++;
      }
    });

    // Update internal state with the merged and sorted data
    this.data = mergedData;
    this.dateToIndexMap = newDateToIndexMap;

    return { data: this.data, newIndexesAdded, shift, keysUpdated, newKeys };
  }

  revertDivision(datapoint, keys, copyData = true) {
    // Copy the datapoint if copyData is true
    const targetDatapoint = copyData ? { ...datapoint } : datapoint;

    keys.forEach((key) => {
      if (
        key in targetDatapoint &&
        targetDatapoint[key] != null &&
        !isNaN(targetDatapoint[key]) &&
        key in this.dividers
      ) {
        targetDatapoint[key] = this.preciseMultiply(
          datapoint[key],
          this.dividers[key],
        );
      }
    });

    return targetDatapoint;
  }

  divide(datapoint, keysUpdated) {
    keysUpdated.forEach((key) => {
      if (
        key in datapoint &&
        datapoint[key] != null &&
        !isNaN(datapoint[key]) &&
        key in this.dividers
      ) {
        datapoint[key] = this.preciseDivide(datapoint[key], this.dividers[key]);
      }
    });
    return datapoint;
  }

  preciseDivide(a, b) {
    if (!b) return a;
    if (!a) return 0;

    if (b === 0) throw new Error("Division by zero is not allowed");

    // Helper function to get the number of decimal places
    function getDecimalPlaces(num) {
      const match = ("" + num).match(/(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/);
      if (!match) {
        return 0;
      }
      return Math.max(
        0,
        (match[1] ? match[1].length : 0) - (match[2] ? +match[2] : 0),
      );
    }

    const dpA = getDecimalPlaces(a);
    const dpB = getDecimalPlaces(b);

    // Convert a and b to integers to avoid floating-point errors
    const numerator = Math.round(a * Math.pow(10, dpA));
    const denominator = Math.round(b * Math.pow(10, dpB));

    let result;
    const exponentDiff = dpB - dpA;

    if (exponentDiff >= 0) {
      // When the exponent difference is positive or zero
      result = (numerator / denominator) * Math.pow(10, exponentDiff);
    } else {
      // When the exponent difference is negative
      result = numerator / denominator / Math.pow(10, -exponentDiff);
    }

    /* --- trim IEEE-754 noise ---------------------------------- */
    // IEEE-754 double precision keeps ~15-17 significant figures.
    // Using toPrecision removes the trailing 1 (or 9) artefacts.
    return +result.toPrecision(15);
  }

  preciseMultiply(a, b) {
    if (!b) return a;
    if (!a) return 0;

    const aStr = Utils.toFullNumberString(a);
    const bStr = Utils.toFullNumberString(b);

    // Split into integer and fractional parts or set fractional part to empty string
    const [aInt, aFrac = "0"] = aStr.includes(".")
      ? aStr.split(".")
      : [aStr, "0"];
    const [bInt, bFrac = "0"] = bStr.includes(".")
      ? bStr.split(".")
      : [bStr, "0"];

    // Concatenate integer and fractional parts to form whole numbers as strings
    const fullA = aInt + aFrac;
    const fullB = bInt + bFrac;

    // Calculate total number of decimal places in both numbers
    const totalDecimals = aFrac.length + bFrac.length;

    // Convert to BigInt for precise integer multiplication
    const fullABigInt = BigInt(fullA);
    const fullBBigInt = BigInt(fullB);

    // Multiply the two integers
    const result = fullABigInt * fullBBigInt;

    // Convert result to string
    let resultStr = result.toString();

    // Insert the decimal point in the correct position if needed
    if (totalDecimals > 0) {
      const integerPartLength = resultStr.length - totalDecimals;
      if (integerPartLength > 0) {
        resultStr =
          resultStr.slice(0, integerPartLength) +
          "." +
          resultStr.slice(integerPartLength);
      } else {
        resultStr = "0." + "0".repeat(-integerPartLength) + resultStr;
      }
    }

    // Remove any unnecessary trailing zeros and adjust if decimal point is at end
    return resultStr.replace(/\.?0+$/, "");
  }

  setKeysToAxisBasedOnIndicatorSettings(options) {
    const indicatorId = options.indicatorId;
    const indicator = options.indicator;
    for (let j = 0; j < indicator.details.outputs.length; j++) {
      const dataKey = indicator.details.outputs[j].name;
      const baseKey = `${indicatorId}-${dataKey}`;
      this.keyToAxis[baseKey] = indicator.details.outputs[j].y_axis;
    }
  }

  setDividers(data) {
    // To prevent display errors at high values, we must account for the 16-bit unsigned integer limit of 65,535.
    // Values exceeding this limit, such as 65,536, wrap around to 0.
    // To address this, we use a divider to scale down values received from the server, ensuring accurate display on the chart.

    const keys =
      data.length > 0
        ? Object.keys(data[0]).filter(
            (k) => !["date", "_date", "_dateObj"].includes(k),
          )
        : [];

    keys.forEach((key) => {
      // If a divider already exists for the key, skip further processing
      if (this.dividers[key] != null) {
        return;
      }

      let maxValue = -Infinity;
      let minValue = Infinity;

      // Iterate through the data to find the maximum value for the key
      for (let i = 0; i < data.length; i++) {
        const value = data[i][key];
        if (value != null && !isNaN(value)) {
          maxValue = Math.max(maxValue, Number(value));
          minValue = Math.min(minValue, Number(value));
        }
      }

      // Determine the divider based on the maximum value found
      // const axis = this.keyToAxis[key];

      // Iterate over the configured keys and pick the first one that
      // is a prefix of the incoming `key`.
      const matchedKey = Object.keys(this.keyToAxis).find((mappingKey) =>
        key.startsWith(mappingKey),
      );

      const axis = matchedKey ? this.keyToAxis[matchedKey] : undefined;

      if (axis) {
        if (this.dividersPerAxis[axis]) {
          this.dividers[key] = this.dividersPerAxis[axis];
        } else {
          this.dividersPerAxis[axis] = this.determineDivider(
            maxValue,
            minValue,
          );
          this.dividers[key] = this.dividersPerAxis[axis];
        }
      } else {
        this.dividers[key] = this.determineDivider(maxValue, minValue);
      }

      // if (this.dividers[key]) {
      //     console.log(`${key}'s divider ${this.dividers[key]} (example value ${minValue} transformed to ${this.preciseDivide(minValue, this.dividers[key])})`);
      // }
    });
  }

  determineDivider(maxValue, minValue) {
    let divider = null; // Default value

    if (maxValue >= 1) {
      // Handle values equal to or greater than 1 to bring them to a suitable scale
      let maxString = maxValue.toExponential();
      let maxExponent = parseInt(maxString.split("e+")[1] || 0);

      // Adjust the exponent to scale number around 1
      divider = Math.pow(10, maxExponent);
    } else if (minValue < 1) {
      // Handle values between 0 and 1 (exclusive) by finding the proper negative exponent
      let minString = minValue.toExponential();
      let minExponent = parseInt(minString.split("e-")[1] || 0);

      divider = Math.pow(10, -minExponent);
    }

    return divider;
  }

  _updateDataCount() {
    // count of data sources
    if (this.config && this.config.data && Array.isArray(this.config.data)) {
      this.dataCount = this.config.data.filter(function (object) {
        return object.type === "data";
      }).length;
    }
  }

  getVapidPublicKey(onVapidPublicKey) {
    this._onVapidPublicKey = onVapidPublicKey;

    this.ws.sendMessage(JSON.stringify([{ type: "vapid_public_key" }]));
  }

  scan(data, onProgress, onResult) {
    this._onScanProgress = onProgress;
    this._onScanResult = onResult;
    let d = JSON.parse(JSON.stringify(data));
    d.type = "scan";
    this.ws.sendMessage(JSON.stringify([d]));
  }

  scanStop() {
    const d = { type: "scan_stop" };
    this.ws.sendMessage(JSON.stringify([d]));
  }

  addAlert(data) {
    let d = JSON.parse(JSON.stringify(data));
    d.type = "alert";
    d.subscription = this.subscription;
    this.ws.sendMessage(JSON.stringify([d]));
  }

  addData(data, onData) {
    // new data
    this._onData[`${data["source"]}-${data["name"]}-${data["type"]}`] = onData;
    this.config.data.push(data);
    this._updateDataCount();
    let d = JSON.parse(JSON.stringify(data)); // deep copy
    if (!d.count) {
      d.count = this.data && this.data.length ? this.data.length : 300;
    }
    this.ws.sendMessage(JSON.stringify([d]));
  }

  addIndicator(data, onData) {
    // new data
    this._onIndicatorData[data.id] = onData;

    this.config.data.push(data);
    let d = JSON.parse(JSON.stringify(data));
    d.range = [this.data[0]._date, this.data[this.data.length - 1]._date];
    this.ws.sendMessage(JSON.stringify([d]));
  }

  addIndicatorsOnDataInit() {
    for (let i = 0; i < this.indicatorsToAddOnDataInit.length; i++) {
      const item = this.indicatorsToAddOnDataInit[i];
      this.chart.operationsHandler.addIndicator(
        item.indicator,
        item.render.paneIdx,
        item.inputs,
        item.render.axesMap,
        item.render.scalesMap,
        item.dataMap,
        item.render.colorMap,
      );
    }
  }

  initServerConnection() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    this.ws = new WebSocketManager(this.config.full_url, () => {
      console.log("WebSocket connection established");
      this.connected();
      const datas = [];
      for (let i = 0; i < this.config.data.length; i++) {
        const item = this.config.data[i];
        if (item.type === "data") {
          datas.push(item);
        }

        if (item.type === "indicator") {
          this.indicatorsToAddOnDataInit.push(item);
        }
      }
      this.ws.sendMessage(JSON.stringify(datas));
    });

    this.ws.onMessage((message) => {
      if (this.disable) {
        return;
      }

      const wasNotReady = this.data === null;
      let cbKey, obj, loaded, keysUpdated;
      switch (message.type) {
        case "data_history":
          loaded = true;
          for (let i = 0; i < this._dataHistory.length; i++) {
            const h = this._dataHistory[i];
            if (
              !h.loaded &&
              message.source === h.source &&
              message.name === h.name &&
              message.interval === h.interval
            ) {
              h.loaded = true;
            }
            if (!h.loaded) {
              loaded = false;
            }
          }

          obj = this.prepareData(message.data);

          this.updated(
            obj.keysUpdated,
            obj.newIndexesAdded,
            undefined,
            obj.shift,
          );
          if (loaded && this._onDataHistoryLoaded) {
            this._onDataHistoryLoaded();
            this._onDataHistoryLoaded = null;
          }
          break;

        case "indicator_history":
          loaded = true;
          for (let i = 0; i < this._indicatorHistory.length; i++) {
            const h = this._indicatorHistory[i];
            if (!h.loaded && message.id === h.id) {
              h.loaded = true;
            }
            if (!h.loaded) {
              loaded = false;
            }
          }

          obj = this.prepareData(message.data);

          this.updated(
            obj.keysUpdated,
            obj.newIndexesAdded,
            undefined,
            obj.shift,
          );
          if (loaded) {
            this.loadingHistory = false;
          }
          break;

        case "indicator_init":
          obj = this.prepareData(message.data);
          if (message.annotations) {
            this.prepareAnnotations(message.annotations);
          }
          cbKey = `${message["id"]}`;

          if (this._onIndicatorData[cbKey]) {
            const cb = this._onIndicatorData[cbKey];
            delete this._onIndicatorData[cbKey];

            cb(obj.newKeys);
          }

          this.updated(
            obj.keysUpdated,
            obj.newIndexesAdded,
            undefined,
            obj.shift,
            true, // new keys
          );

          break;

        case "data_init":
          if (message.data.length === 0) {
            // TODO: This causes strange behavior in various cases
            // So now just handling one case, when the user loads empty chart
            // and no data is returned, which removes it from data and new pane

            // remove from data arr
            this.config.data = this.config.data.filter((item) => {
              if (
                item.source === message.source &&
                item.name === message.name &&
                item.interval === message.interval
              ) {
                return false;
              } else {
                return true;
              }
            });

            // remove pane
            for (let i = 0; i < this.chart.panes.length; i++) {
              const pane = this.chart.panes[i];
              let keysMatching = 0;
              let allKeys = 0;

              for (let j = 0; j < pane.metadata.length; j++) {
                const meta = pane.metadata[j];
                allKeys += meta.dataKeys.length;

                for (let k = 0; k < meta.dataKeys.length; k++) {
                  const dk = meta.dataKeys[k];
                  if (
                    dk["dataKey"].includes(
                      `${message.source}-${message.name}-${message.interval}`,
                    )
                  ) {
                    keysMatching += 1;
                  }
                }
              }
              if (keysMatching === allKeys) {
                this.chart.operationsHandler._removePane(i, true);
                break;
              }
            }

            this.chart.addWindow();
            console.error("No data.");
          }

          if (message.data.length > 0) {
            if (message.metadata) {
              this.keyToMetadata[`${message["source"]}-${message["name"]}`] =
                message.metadata;
            }

            for (const key of Object.keys(message.data[0])) {
              const _key = key.slice(0);
              this.keyToData[key] = {
                source: message.source,
                name: message.name,
                interval: message.interval,
                key: _key.replace(
                  `${message.source}-${message.name}-${message.interval}-`,
                  "",
                ),
              };
            }
            obj = this.prepareData(message.data);

            cbKey = `${message["source"]}-${message["name"]}-data`;

            if (this._onData[cbKey]) {
              const cb = this._onData[cbKey];
              delete this._onData[cbKey];

              cb();
            }

            if (!wasNotReady) {
              this.updated(
                obj.keysUpdated,
                obj.newIndexesAdded,
                undefined,
                obj.shift,
                true, // new keys
              );
            }
          }

          if (!this._indicatorsOnDataInitAdded) {
            this._indicatorsOnDataInitAdded = true;
            this.addIndicatorsOnDataInit();
          }

          break;

        case "data_update":
        case "indicator_update":
          if (!this.data) {
            return;
          }

          keysUpdated = Object.keys(message.data).filter(
            (k) => !["date", "_date", "_dateObj"].includes(k),
          );
          if (keysUpdated.length === 0) {
            return;
          } // no update

          message.data = this.divide(message.data, keysUpdated);

          let right = 0;

          let idx = this.data.length - 1;
          let lastDate = null;
          for (
            let k = this.data.length - 1;
            k >= Math.max(0, this.data.length - 33);
            k--
          ) {
            if (this.data[k]._date === message.data.date) {
              lastDate = message.data.date;
              idx = k;
              break; // Exit the loop once lastDate is found
            }
          }

          if (lastDate == message.data.date) {
            message.data._date = message.data.date;
            message.data._dateObj = Utils.toDate(message.data.date);
            message.data.date = idx;

            this.data[idx] = Object.assign(this.data[idx], message.data);
          } else {
            idx = this.data.length;

            message.data._date = message.data.date;
            message.data._dateObj = Utils.toDate(message.data.date);
            message.data.date = idx;
            right = 1;

            this.data.push(message.data);
          }

          this.updated(keysUpdated, undefined, right);
          break;

        case "data_search":
          if (this.onSearchDone) {
            this.onSearchDone(message.data);
          }
          break;

        case "indicator_inputs":
          this._onCalculatedIndicatorInputs(message);
          break;

        case "scan_progress":
          if (this._onScanProgress) {
            this._onScanProgress(message.message);
          }
          break;

        case "scan_result":
          if (this._onScanResult) {
            this._onScanResult(message);
          }
          break;

        case "search_indicators_done":
          this._onSearchIndicatorsDone(message.results);
          break;

        case "search_data_done":
          this._onSearchDataDone(message.results);
          break;

        case "vapid_public_key":
          this._onVapidPublicKey(message.vapid_public_key);
          break;

        case "prompt_response":
          if (message.response) {
            this._onPromptChunk(message.response);
          }
          break;
        case "notification":
          alert(message.message);
          break;
      }

      const isReady = this.data !== null;
      if (wasNotReady && isReady) {
        this.ready();
      }
    });
  }

  disableEvents() {
    this.disable = true;
  }

  enableEvents() {
    this.disable = false;
  }

  prompt(conversationId, description, prompt, img, onChunk) {
    this._onPromptChunk = onChunk;
    this.ws.sendMessage(
      JSON.stringify([
        {
          type: "prompt",
          conversation_id: conversationId,
          description,
          prompt,
          img,
        },
      ]),
    );
  }

  reply(conversationId, prompt, onChunk) {
    this._onPromptChunk = onChunk;
    this.ws.sendMessage(
      JSON.stringify([
        {
          type: "prompt_reply",
          conversation_id: conversationId,
          prompt,
        },
      ]),
    );
  }

  searchData(search, onSearchDone) {
    this._onSearchDataDone = onSearchDone;
    this.ws.sendMessage(
      JSON.stringify([
        {
          type: "search_data",
          search,
        },
      ]),
    );
  }
  searchIndicators(search, onSearchDone) {
    this._onSearchIndicatorsDone = onSearchDone;
    this.ws.sendMessage(
      JSON.stringify([
        {
          type: "search_indicators",
          search,
        },
      ]),
    );
  }

  history(domain) {
    if (this.loadingHistory || !this.config || !this.config.url) {
      return;
    }
    this.loadingHistory = true;
    this.dataHistory(domain, this.indicatorHistory.bind(this));
  }

  dataHistory(domain, onLoaded) {
    const dataConfig = JSON.parse(JSON.stringify(this.config.data));
    const h = [];
    const count = Math.round(Math.abs(domain));
    for (let i = 0; i < dataConfig.length; i++) {
      const d = dataConfig[i];
      if (d.type === "data") {
        d.type = "data_history";
      } else {
        continue;
      }
      let found = false;
      for (let j = 0; j < this.data.length; j++) {
        for (let k of Object.keys(this.data[j])) {
          if (
            this.data[j][k] &&
            k.startsWith(`${d.source}-${d.name}-${d.interval}`)
          ) {
            d.end = this.data[j]._date;
            d.count = j + count;
            found = true;
            break;
          }
          if (found) break;
        }
        if (found) break;
      }
      h.push(d);
    }

    this._dataHistory = h;
    this._onDataHistoryLoaded = onLoaded;

    this.ws.sendMessage(JSON.stringify(h));
  }
  indicatorHistory() {
    const dataConfig = JSON.parse(JSON.stringify(this.config.data));
    const h = [];
    for (let i = 0; i < dataConfig.length; i++) {
      const d = dataConfig[i];
      if (d.type === "indicator") {
        d.type = "indicator_history";
      } else {
        continue;
      }
      let found = false;
      for (let j = 0; j < this.data.length; j++) {
        for (let k of Object.keys(this.data[j])) {
          if (this.data[j][k] && k.startsWith(d.id)) {
            d.end = this.data[j]._date;
            found = true;
            break;
          }
          if (found) break;
        }
        if (found) break;
      }

      d.range = [
        this.data[0]._date,
        d.end ? d.end : this.data[this.data.length - 1]._date,
      ];
      h.push(d);
    }

    if (h.length) {
      this._indicatorHistory = h;
      this.ws.sendMessage(JSON.stringify(h));
    } else {
      this.loadingHistory = false;
    }
  }

  optimizeIndicatorParams(data, _onCalculatedIndicatorInputs) {
    this._onCalculatedIndicatorInputs = _onCalculatedIndicatorInputs;
    data.type = "optimize_indicator_params";
    this.ws.sendMessage(JSON.stringify([data]));
  }

  onConnect(fn) {
    if (this._connected) {
      fn();
    } else {
      this._onConnect.push(fn);
    }
  }

  connected() {
    for (let i = 0; i < this._onConnect.length; i++) {
      this._onConnect[i]();
    }
    this._connected = true;
    this._onConnect = [];
  }

  onReady(fn) {
    this._onReady.push(fn);
    if (this.data !== null) {
      this.ready();
    }
  }

  ready() {
    for (let i = 0; i < this._onReady.length; i++) {
      this._onReady[i]();
    }
  }

  onUpdated(fn) {
    this._onUpdated.push(fn);
    if (this.data !== null) {
      this.updated();
    }
  }

  updated(keys, left, right, shift, addedKyes) {
    for (let i = 0; i < this._onUpdated.length; i++) {
      this._onUpdated[i](keys, left, right, shift, addedKyes);
    }
  }
}
