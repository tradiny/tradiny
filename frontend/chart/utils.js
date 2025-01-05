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

export class Utils {
  static canvas = document.createElement("canvas");

  static toDate(d) {
    const ds = d.split(/-|\s|:/);
    if (ds.length === 6) {
      return new Date(
        parseInt(ds[0], 10),
        parseInt(ds[1], 10) - 1,
        parseInt(ds[2], 10),
        parseInt(ds[3], 10),
        parseInt(ds[4], 0),
        parseInt(ds[5], 10),
      );
    }
  }

  static toAlphanumeric(name) {
    return name.replace(/[^a-zA-Z0-9]/g, "_");
  }

  static getTextHeight(text, font) {
    const context = Utils.canvas.getContext("2d");
    context.font = font;
    const metrics = context.measureText(text);
    const fontBoundingBoxAscent = metrics.fontBoundingBoxAscent;
    if (fontBoundingBoxAscent !== undefined) {
      return fontBoundingBoxAscent;
    } else {
      console.log("fontBoundingBoxAscent is not supported.");
      return 12;
    }
    return metrics.fontBoundingBoxAscent;
  }
  static getTextWidth(text, font) {
    text = text.toString() + "00";
    const context = Utils.canvas.getContext("2d");
    context.font = font;
    const metrics = context.measureText(text);
    return metrics.width;
  }

  static formatFloat(f, precision) {
    // Ensure precision is a non-negative integer
    if (precision < 0) {
      throw new Error("Precision must be a non-negative integer");
    }

    // Convert the input to a float
    let num = parseFloat(f);
    if (isNaN(num)) {
      return f;
      // throw new Error('Invalid input: not a number');
    }

    // Use toFixed to format the float to the specified precision
    let str = num.toFixed(precision);

    // Remove trailing zeros after the decimal point, if any
    if (str.includes(".")) {
      str = str.replace(/\.?0+$/, "");
    }

    return str;
  }

  static toFixed(x) {
    if (Math.abs(x) < 1.0) {
      var e = parseInt(x.toString().split("e-")[1]);
      if (e) {
        const precision = x.toString().split("e-")[0].length;
        x *= Math.pow(10, e - 1);
        x =
          "0." +
          new Array(e).join("0") +
          x.toString().substring(2, 2 + precision);
      }
    } else {
      var e = parseInt(x.toString().split("+")[1]);
      if (e > 20) {
        e -= 20;
        x /= Math.pow(10, e);
        x += new Array(e + 1).join("0");
      }
    }
    return x;
  }

  static webglColor(identifier) {
    const { r, g, b, opacity } = d3.color(identifier).rgb();
    return [r / 255, g / 255, b / 255, opacity];
  }

  static toFullNumberString(number) {
    // Convert to string and check if it already doesn't use scientific notation
    if (!number.toString().includes("e")) {
      return number.toString();
    }

    // Use a large enough `toFixed` or a loop with incremented decimals
    const places = Math.max(1, Math.abs(Math.floor(Math.log10(number))));
    return number.toFixed(places);
  }

  static filterInsignificantPrecision(numberStr, rangeStart, rangeEnd) {
    const number = parseFloat(numberStr);
    const range = Math.abs(rangeEnd - rangeStart);

    if (range === 0) {
      return number; // If the range is zero, return the number as it is.
    }

    // Determine the range order of magnitude
    const rangeMagnitude = Math.floor(Math.log10(range));

    // Calculate number of decimal places needed
    // Ensure that 'decimalPlaces' is sufficient for small numbers
    let decimalPlaces = Math.max(0, -rangeMagnitude + 2);

    // Use Number to ensure proper numeric type conversion
    const factor = Math.pow(10, decimalPlaces);
    const roundedNumber = Math.round(number * factor) / factor;

    return Utils.toFullNumberString(roundedNumber);
  }

  static deepCopy(obj, hash = new WeakMap()) {
    // Handle null or undefined
    if (obj === null || typeof obj !== "object") {
      return obj;
    }

    // Handle DataProvider and GridHandler by reference
    const className = obj.constructor && obj.constructor.name;
    if (className === "DataProvider" || className === "GridHandler") {
      return obj;
    }

    // Handle Date
    if (obj instanceof Date) {
      return new Date(obj);
    }

    // Handle Array
    if (Array.isArray(obj)) {
      const arrCopy = [];
      for (let i = 0; i < obj.length; i++) {
        arrCopy[i] = Utils.deepCopy(obj[i], hash);
      }
      return arrCopy;
    }

    // Handle Function
    if (typeof obj === "function") {
      // Arrow functions have no prototype property
      if (!obj.prototype) {
        return obj;
      } else {
        return function (...args) {
          return obj.apply(this, args);
        };
      }
    }

    // Avoid copying instantiated objects
    if (obj.constructor !== Object) {
      return obj;
    }

    // Handle regular Object (including RegExp and others)
    if (hash.has(obj)) {
      return hash.get(obj);
    }
    const objCopy = new obj.constructor();
    hash.set(obj, objCopy);
    for (let key in obj) {
      if (obj.hasOwnProperty(key)) {
        objCopy[key] = Utils.deepCopy(obj[key], hash);
      }
    }
    return objCopy;
  }

  static getChange(previous, current) {
    if (current === previous) {
      return 0.0;
    }
    return (Math.abs(current - previous) / previous) * 100.0;
  }

  static secondsToDhms(seconds) {
    seconds = Number(seconds);
    const d = Math.floor(seconds / (3600 * 24));
    const h = Math.floor((seconds % (3600 * 24)) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    let dDisplay = d > 0 ? d + (d == 1 ? "d" : "d") : "";
    if (d > 0 && (h > 0 || m > 0)) {
      dDisplay += ", ";
    }
    let hDisplay = h > 0 ? h + (h == 1 ? "h" : "h") : "";
    if (h > 0 && m > 0) {
      hDisplay += ", ";
    }
    let mDisplay = m > 0 ? m + (m == 1 ? "m" : "m") : "";
    return dDisplay + hDisplay + mDisplay;
  }

  static isNumeric(str) {
    if (typeof str != "string") return false; // we only process strings!
    return !isNaN(str) && !isNaN(parseFloat(str)); // use parseFloat to check if it's a float
  }

  static getPeriod(interval) {
    const minute = 60 * 1000;
    const hour = minute * 60;
    const day = hour * 24;
    switch (interval) {
      case "1m":
        return minute * 1;
      case "3m":
        return minute * 3;
      case "5m":
        return minute * 5;
      case "15m":
        return minute * 15;
      case "30m":
        return minute * 30;
      case "1h":
        return hour;
      case "2h":
        return hour * 2;
      case "4h":
        return hour * 4;
      case "6h":
        return hour * 6;
      case "8h":
        return hour * 8;
      case "12h":
        return hour * 12;
      case "1d":
        return day;
      case "3d":
        return day * 3;
      case "1w":
        return day * 7;
      case "1M":
        return day * 30;
    }
  }

  static serializeAbsolutePoints(points, xA, yA, data, interval) {
    const MILLISECONDS_IN_A_YEAR = 365 * 24 * 60 * 60 * 1000;
    const MAX_YEAR_DIFFERENCE = 40;
    const MAX_DIFFERENCE_MILLISECONDS =
      MAX_YEAR_DIFFERENCE * MILLISECONDS_IN_A_YEAR;
    const MIN_DIFFERENCE_MILLISECONDS =
      -MAX_YEAR_DIFFERENCE * MILLISECONDS_IN_A_YEAR;

    const parseDate = d3.timeParse("%Y-%m-%d %H:%M:%S");
    const formatDate = d3.timeFormat("%Y-%m-%d %H:%M:%S");

    const candleSizeInDate = Utils.getPeriod(interval);

    const closestAvailableX = (x) => {
      if (0 <= x && x < data.length) {
        return { closestX: Math.floor(x), diffX: x - Math.floor(x) };
      } else if (x < 0) {
        return { closestX: 0, diffX: x };
      } else if (x >= data.length) {
        return { closestX: data.length - 1, diffX: x - (data.length - 1) };
      }
    };

    const translated = [];
    for (let j of Object.keys(points)) {
      const pt = points[j];
      const x = closestAvailableX(pt[0]);
      const xDifference = x.diffX;
      let xDifferenceDate = xDifference * candleSizeInDate;

      // Limit xDifferenceDate to a maximum of 40 years and a minimum of -40 years
      if (xDifferenceDate > MAX_DIFFERENCE_MILLISECONDS) {
        xDifferenceDate = MAX_DIFFERENCE_MILLISECONDS;
      } else if (xDifferenceDate < MIN_DIFFERENCE_MILLISECONDS) {
        xDifferenceDate = MIN_DIFFERENCE_MILLISECONDS;
      }

      const xDateWithDiff = new Date(
        parseDate(data[x.closestX]._date).getTime() + xDifferenceDate,
      );
      translated.push([formatDate(xDateWithDiff), pt[1]]);
    }
    return translated;
  }

  static unserializeRelativePoints(points, xA, yA, data, interval) {
    const parseDate = d3.timeParse("%Y-%m-%d %H:%M:%S");
    const formatDate = d3.timeFormat("%Y-%m-%d %H:%M:%S");

    const candleSizeInDate = Utils.getPeriod(interval);

    const closestAvailableDate = (date) => {
      const inputDate = parseDate(date);
      let closestDate = null;
      let closestIndex = -1;
      let minDiff = Infinity;

      data.forEach((item, index) => {
        const itemDate = parseDate(item._date);
        const diff = inputDate - itemDate;

        if (Math.abs(diff) < Math.abs(minDiff)) {
          closestDate = itemDate;
          closestIndex = index;
          minDiff = diff;
        }
      });

      if (closestDate !== null) {
        return {
          x: closestIndex,
          diffDate: inputDate.getTime() - closestDate.getTime(),
        };
      }
    };

    const translated = [];
    for (let j of Object.keys(points)) {
      const pt = points[j];

      const x = closestAvailableDate(pt[0]);
      if (!x) {
        continue;
      }

      const xVal = x.x + x.diffDate / candleSizeInDate;
      translated.push([xVal, pt[1]]);
    }
    return translated;
  }

  static replaceInObject(obj, oldStr, newStr, visited = new Map()) {
    if (visited.has(obj)) {
      return visited.get(obj);
    }

    if (typeof obj === "object" && obj !== null) {
      if (Array.isArray(obj)) {
        const newArr = obj.map((item) =>
          Utils.replaceInObject(item, oldStr, newStr, visited),
        );
        visited.set(obj, newArr);
        return newArr;
      } else {
        const newObj = {};
        visited.set(obj, newObj);
        for (const key in obj) {
          const newKey = key.includes(oldStr)
            ? key.replace(oldStr, newStr)
            : key;
          newObj[newKey] = Utils.replaceInObject(
            obj[key],
            oldStr,
            newStr,
            visited,
          );
        }
        return newObj;
      }
    } else if (typeof obj === "string") {
      return obj.includes(oldStr) ? obj.replace(oldStr, newStr) : obj;
    } else {
      return obj;
    }
  }

  static replaceAllInObj(
    obj,
    targetValue,
    replacementValue,
    visited = new Map(),
  ) {
    if (visited.has(obj)) {
      return visited.get(obj);
    }

    if (typeof obj !== "object" || obj === null) {
      if (typeof obj === "string") {
        return obj.replace(new RegExp(targetValue, "g"), replacementValue);
      }
      return obj === targetValue ? replacementValue : obj;
    }

    const result = Array.isArray(obj) ? [] : {};
    visited.set(obj, result);

    for (const [key, value] of Object.entries(obj)) {
      const newKey = key === targetValue ? replacementValue : key;
      if (typeof value === "string") {
        result[newKey] = value.replace(
          new RegExp(targetValue, "g"),
          replacementValue,
        );
      } else {
        result[newKey] = Utils.replaceAllInObj(
          value,
          targetValue,
          replacementValue,
          visited,
        );
      }
    }

    return result;
  }

  static replaceExactInObj(
    obj,
    targetValue,
    replacementValue,
    visited = new Map(),
  ) {
    if (visited.has(obj)) {
      return visited.get(obj);
    }

    if (typeof obj !== "object" || obj === null) {
      if (typeof obj === "string") {
        const regex = new RegExp("\\b" + targetValue + "\\b", "g");
        return obj.replace(regex, replacementValue);
      }
      return obj === targetValue ? replacementValue : obj;
    }

    const result = Array.isArray(obj) ? [] : {};
    visited.set(obj, result);

    for (const [key, value] of Object.entries(obj)) {
      const newKey = key === targetValue ? replacementValue : key;
      if (typeof value === "string") {
        const regex = new RegExp("\\b" + targetValue + "\\b", "g");
        result[newKey] = value.replace(regex, replacementValue);
      } else {
        result[newKey] = Utils.replaceExactInObj(
          value,
          targetValue,
          replacementValue,
          visited,
        );
      }
    }

    return result;
  }
  static generateUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
      /[xy]/g,
      function (c) {
        const r = (Math.random() * 16) | 0;
        const v = c === "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      },
    );
  }
  static markdownToHtml(markdown) {
    // Convert headers
    markdown = markdown.replace(/^#{1,6}\s+(.*)$/gm, (match, p1) => {
      const level = match.indexOf(" ");
      return `<h${level}>${p1}</h${level}>`;
    });

    // Convert bold (strong emphasis)
    markdown = markdown.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Convert italics (emphasis)
    markdown = markdown.replace(/\*(.*?)\*/g, "<em>$1</em>");

    // Convert links
    markdown = markdown.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');

    // Convert unordered lists
    markdown = markdown.replace(
      /(\n|^)([-*])\s+(.*)/g,
      (match, newline, p1, p2) => {
        const listItem = `<li>${p2}</li>`;
        // Start a new list or continue a list
        return `${newline || ""}<ul>${listItem}</ul>`;
      },
    );

    // Ensure all lists are properly closed
    markdown = markdown.replace(/<\/ul>\n<ul>/g, "");

    // Wrap text in paragraph tags if it's not already wrapped
    markdown = markdown
      .split("\n")
      .map((line) => {
        if (!line.startsWith("<") && line.trim() !== "") {
          return `<p>${line.trim()}</p>`;
        }
        return line;
      })
      .join("\n");

    return markdown;
  }

  static getAxisWidthBasedOnSample(sample, formatter, fontSize) {
    if (sample == undefined) {
      return 0;
    }
    if (formatter) {
      if (formatter === "si") {
        sample = d3.format(".3s")(sample);
      } else {
        sample = formatter(sample);
      }
    }
    let str = "" + sample;
    if (str.includes(".")) {
      str = str.replace(/0+$/, "");
    }
    const w = Math.round(
      Utils.getTextWidth(str + "0", `${fontSize}px sans-serif`),
    );

    return w;
  }

  static getPrecisionBasedOnSample(sample, formatter) {
    if (sample == undefined) {
      return 0;
    }
    if (formatter) {
      if (formatter === "si") {
        sample = d3.format(".3s")(sample);
      } else {
        sample = formatter(sample);
      }
    }
    let str = sample.toString();
    if (str.includes(".")) {
      str = str.replace(/\.?0+$/, "");
    }
    const decimalIndex = str.indexOf(".");
    if (decimalIndex === -1) {
      return 0; // No decimal places
    } else {
      return str.length - decimalIndex - 1;
    }
  }

  static removeDuplicates(array) {
    const seen = new Set();

    return array.filter((item) => {
      const serialized = JSON.stringify(item);

      if (seen.has(serialized)) {
        return false; // This item is a duplicate
      }

      seen.add(serialized);
      return true; // This item is unique so far
    });
  }
  static downloadCSV(arrOfObjects) {
    function replacer(key, value) {
      return value === null ? "" : value;
    }

    if (!arrOfObjects || !arrOfObjects.length) {
      throw new Error("Array of objects is required");
    }

    // Create a mapping of original to sanitized header names
    const originalHeaders = Object.keys(arrOfObjects[0]);
    const sanitizedHeaders = originalHeaders.map((header) =>
      header.replace(/,/g, ""),
    );

    const csvRows = arrOfObjects.map((obj) =>
      sanitizedHeaders
        .map((sanitizedHeader, index) =>
          JSON.stringify(obj[originalHeaders[index]], replacer),
        )
        .join(","),
    );

    const csvString = [sanitizedHeaders.join(","), ...csvRows].join("\n");

    const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);

    link.setAttribute("href", url);
    link.setAttribute("download", "data.csv");
    link.style.visibility = "hidden";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
