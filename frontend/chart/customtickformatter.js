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

export class CustomTickDateFormatter {
  constructor(
    axis,
    offset = 0,
    dataProvider = null,
    strategy = "1h",
    months = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ],
    weekDays = ["Sun", "Mon", "Tue", "Wen", "Thu", "Fri", "Sat"],
    dateFormat,
    getTextWidth,
  ) {
    this.axis = axis;
    this.ticksArray = axis.scale().ticks();
    this.scale = axis.scale();
    this.offset = offset;
    this.dataProvider = dataProvider;
    this.dateFormat =
      dateFormat != "undefined" && dateFormat != ""
        ? dateFormat
        : this.offset >= -10 && this.offset <= -5
          ? "US"
          : "EU";
    this.getTextWidth = getTextWidth.bind(this);
    this.strategy = (d, i, a) => "NaN"; // placeholder
    this.months = months;
    this.weekDays = weekDays;
    this.preD = null;
    this.preDLinear = null;
    this.textArrayWidths = (a) => {
      let result = [];
      for (let i = 0; i < a.length; i++)
        result.push(this.getTextWidth(String(" " + a[i])));
      return result;
    };
    this.textWidth = {
      time: this.getTextWidth(" 00:00"),
      weekDays: this.textArrayWidths(this.weekDays),
      date: [this.getTextWidth(" 0"), this.getTextWidth(" 00")],
      orIn: this.getTextWidth("nd"),
      months: this.textArrayWidths(this.months),
      year: [this.getTextWidth(" 0000"), this.getTextWidth(" '00")],
    };
    this.resultPrototype = (d) => {
      let result = {
        time: String(" " + this.dateFormatT(d)),
        day: String(" " + this.weekDays[d.getUTCDay()]),
        date: String(" " + d.getUTCDate()),
        orIn: this.ordinalIndicator(d.getUTCDate()),
        month: String(" " + this.dateFormatM(d)),
        year: String(" " + this.dateFormatY(d)),
        toString: (() =>
          this.dateFormat == "US"
            ? () =>
                String(
                  result.time +
                    result.day +
                    result.month +
                    result.date +
                    result.orIn +
                    result.year,
                )
            : () =>
                String(
                  result.time +
                    result.day +
                    result.date +
                    result.orIn +
                    result.month +
                    result.year,
                ))(),
        width: () => {
          let width = 0;
          if (result.time != "undefined" && result.time != "")
            width += this.textWidth.time;
          if (result.day != "undefined" && result.day != "")
            width += this.textWidth.weekDays[d.getUTCDay()];
          if (result.date != "undefined" && result.date != "")
            width += this.textWidth.date[d.getUTCDate() < 10 ? 0 : 1];
          if (result.orIn != "undefined" && result.orIn != "")
            width += this.textWidth.orIn;
          if (result.month != "undefined" && result.month != "")
            width += this.textWidth.months[d.getUTCMonth()];
          if (result.year != "undefined" && result.year != "")
            width += this.textWidth.year[result.year.length == 5 ? 0 : 1];
          return width;
        },
      };
      return result;
    };
    this.paddNumber = (d) => (d < 10 ? String("0" + d) : String(d));
    this.makeUTC = (d) => {
      let result = new Date(d);
      result.setUTCDate(d.getDate());
      result.setUTCHours(d.getHours(), d.getMinutes());
      return result;
    };
    this.makeOffsetDate = (date, offset) => {
      if (!date) {
        return date;
      }
      let _offset = {
        value: offset,
        isPositive: offset >= 0,
        hours: Math.trunc(Math.abs(offset)),
        minutes: Math.trunc(
          (Math.abs(offset) - Math.trunc(Math.abs(offset))) * 60,
        ),
      };
      let result = this.makeUTC(date);
      let carryOver = 0;
      let newMinutes = 0;
      let newHours = 0;
      let newDate = 0;
      if (_offset.isPositive) {
        newMinutes = result.getUTCMinutes() + _offset.minutes;
        if (newMinutes > 59) {
          carryOver = Math.trunc(newMinutes / 60);
          newMinutes = newMinutes % 60;
        }
        newHours = result.getUTCHours() + _offset.hours + carryOver;
        if (newHours > 23) {
          carryOver = Math.trunc(newHours / 24);
          newHours = newHours % 24;
        } else {
          carryOver = 0;
        }
        newDate = result.getUTCDate() + carryOver;
      } else {
        newMinutes = result.getUTCMinutes() - _offset.minutes;
        if (newMinutes < 0) {
          carryOver = 1 + Math.abs(Math.trunc(newMinutes / 60));
          newMinutes = newMinutes + carryOver * 60;
        }
        newHours = result.getUTCHours() - _offset.hours - carryOver;
        if (newHours < 0) {
          carryOver = 1 + Math.abs(Math.trunc(newHours / 24));
          newHours = newHours + carryOver * 24;
        } else {
          carryOver = 0;
        }
        newDate = result.getUTCDate() - carryOver;
      }

      result.setUTCDate(newDate);
      result.setUTCHours(newHours, newMinutes);
      return result;
    };
    this.dateFormatY = (d) => String(d.getUTCFullYear());
    this.dateFormatM = (d) => String(this.months[d.getUTCMonth()]);
    this.dateFormatMY = (d) =>
      String(this.dateFormatM(d) + " " + this.dateFormatY(d));
    this.dateFormatDM = (d) =>
      String(d.getUTCDate() + " " + this.dateFormatM(d));
    this.dateFormatT = (d) =>
      String(
        this.paddNumber(d.getUTCHours()) +
          ":" +
          this.paddNumber(d.getUTCMinutes()),
      );
    this.ordinalIndicator = (n) =>
      String(
        n >= 4 ? "th" : n == 3 ? "rd" : n == 2 ? "nd" : n == 1 ? "st" : "",
      );
    this.strategy00 = (d, i, a) => {
      let result = this.resultPrototype(d.dDate);

      return result.toString();
    };
    this.strategyMinute = (d, i, a) => {
      const dLinear = d.dLinear;
      d = d.dDate;
      let result = this.resultPrototype(d);

      if (i != 0) {
        let preD = this.preD,
          isSameTime =
            preD.getUTCHours() == d.getUTCHours() &&
            preD.getUTCMinutes() == d.getUTCMinutes(),
          isSameMonth = preD.getUTCMonth() == d.getUTCMonth(),
          isSameDate = preD.getUTCDate() == d.getUTCDate(),
          isSameYear = preD.getUTCFullYear() == d.getUTCFullYear(),
          tickWidth = this.scale(dLinear) - this.scale(this.preDLinear),
          doesFit = () => result.width() < tickWidth;

        if (isSameYear) result.year = "";
        if (isSameTime) result.time = "";
        if (isSameDate && isSameMonth && isSameYear) {
          result.day = "";
          result.date = "";
          result.orIn = "";
          result.month = "";
          result.year = "";
        }
        if (!doesFit()) result.day = "";
        if (!doesFit()) result.orIn = "";
        if (!doesFit()) result.time = "";
      } else {
        let approximateTickWidth =
            this.scale(this.ticksArray[this.ticksArray.length - 1]) / a.length,
          doesFit = () =>
            result.width() < approximateTickWidth || a.length == 1;

        if (!doesFit()) {
          result.day = "";
          result.orIn = "";
        }
        if (!doesFit() && result.year != "")
          result.year = String(" '" + result.year.slice(-2));
        if (!doesFit()) result.year = "";
        if (!doesFit()) result.time = "";
      }
      return result.toString();
    };
    this.strategyDaily = (d, i, a) => {
      const dLinear = d.dLinear;
      d = d.dDate;
      let result = this.resultPrototype(d);
      if (i != 0) {
        let preD = this.preD,
          isSameTime =
            preD.getUTCHours() == d.getUTCHours() &&
            preD.getUTCMinutes() == d.getUTCMinutes(),
          isSameMonth = preD.getUTCMonth() == d.getUTCMonth(),
          isSameDate = preD.getUTCDate() == d.getUTCDate(),
          isSameYear = preD.getUTCFullYear() == d.getUTCFullYear(),
          tickWidth = this.scale(dLinear) - this.scale(this.preDLinear),
          doesFit = () => result.width() < tickWidth;

        if (isSameYear) result.year = "";
        result.time = ""; // time is not relevant for daily
        if (isSameTime) result.time = "";
        if (!isSameTime && isSameDate && isSameMonth && isSameYear) {
          result.day = "";
          result.date = "";
          result.orIn = "";
          result.month = "";
          result.year = "";
        }
        if (!doesFit()) result.day = "";
        if (!doesFit()) result.orIn = "";
        if (!doesFit() && !isSameMonth) result.date = "";
        if (!doesFit() && isSameMonth) result.month = "";
        if (!doesFit() && !isSameYear) result.month = "";
        if (!doesFit() && result.year != "")
          result.year = String(" '" + result.year.slice(-2));
      } else {
        let approximateTickWidth =
            this.scale(this.ticksArray[this.ticksArray.length - 1]) / a.length,
          doesFit = () =>
            result.width() < approximateTickWidth || a.length == 1,
          isSameTime = (function isST(dateArray, thisDate, i) {
            if (dateArray.length > 1 && i < dateArray.length)
              if (thisDate.getUTCHours() == dateArray[i].getUTCHours())
                if (i + 1 < dateArray.length)
                  return isST(dateArray, dateArray[i], i + 1);
                else return true;
              else return false;
            else return false;
          })(this.ticksArrayDate, this.ticksArrayDate[0], 1),
          isSameMonth = (function isSM(dateArray, thisDate, i) {
            if (dateArray.length > 1 && i < dateArray.length)
              if (thisDate.getUTCMonth() == dateArray[i].getUTCMonth())
                if (i + 1 < dateArray.length)
                  return isSM(dateArray, dateArray[i], i + 1);
                else return true;
              else return false;
            else return false;
          })(this.ticksArrayDate, this.ticksArrayDate[0], 1);
        result.time = ""; // time is not relevant for daily
        if (!doesFit()) {
          result.day = "";
          result.orIn = "";
        }
        if (!doesFit() && isSameTime) result.time = "";
        if (!doesFit() && !isSameMonth) result.time = "";
        if (!doesFit() && !isSameMonth) result.date = "";
        if (!doesFit() && result.year != "")
          result.year = String(" '" + result.year.slice(-2));
      }
      return result.toString();
    };
    this.strategyAnnual = (d, i, a) => {
      const dLinear = d.dLinear;
      d = d.dDate;
      let result = this.resultPrototype(d);

      if (i != 0) {
        let preD = this.preD,
          isSameTime =
            preD.getUTCHours() == d.getUTCHours() &&
            preD.getUTCMinutes() == d.getUTCMinutes(),
          isSameMonth = preD.getUTCMonth() == d.getUTCMonth(),
          isSameDate = preD.getUTCDate() == d.getUTCDate(),
          isSameYear = preD.getUTCFullYear() == d.getUTCFullYear(),
          tickWidth = this.scale(dLinear) - this.scale(this.preDLinear),
          doesFit = () => result.width() < tickWidth;

        if (isSameYear) result.year = "";
        if (isSameTime) result.time = "";
        if (!isSameTime && isSameDate && isSameMonth && isSameYear) {
          result.day = "";
          result.date = "";
          result.orIn = "";
          result.month = "";
          result.year = "";
        }
        if (!doesFit()) result.time = "";
        if (!doesFit()) result.day = "";
        if (!doesFit()) result.orIn = "";
        if (!doesFit() && !isSameMonth && !isSameYear) result.date = "";
        if (!doesFit() && !isSameYear) {
          result.date = "";
          result.month = "";
        }
        if (!doesFit() && !isSameMonth && isSameDate) result.date = "";
        if (!doesFit() && result.year != "")
          result.year = String(" '" + result.year.slice(-2));
      } else {
        let approximateTickWidth =
            this.scale(this.ticksArray[this.ticksArray.length - 1]) / a.length,
          doesFit = () =>
            result.width() < approximateTickWidth || a.length == 1,
          isSameTime = (function isST(dateArray, thisDate, i) {
            if (dateArray.length > 1 && i < dateArray.length)
              if (thisDate.getUTCHours() == dateArray[i].getUTCHours())
                if (i + 1 < dateArray.length)
                  return isST(dateArray, dateArray[i], i + 1);
                else return true;
              else return false;
            else return false;
          })(this.ticksArrayDate, this.ticksArrayDate[0], 1),
          isSameMonth = (function isSM(dateArray, thisDate, i) {
            if (dateArray.length > 1 && i < dateArray.length)
              if (thisDate.getUTCMonth() == dateArray[i].getUTCMonth())
                if (i + 1 < dateArray.length)
                  return isSM(dateArray, dateArray[i], i + 1);
                else return true;
              else return false;
            else return false;
          })(this.ticksArrayDate, this.ticksArrayDate[0], 1);
        if (!doesFit()) {
          result.day = "";
          result.orIn = "";
        }
        if (!doesFit()) result.time = "";
        if (!doesFit() && !isSameMonth) result.date = "";
        if (!doesFit() && result.year != "")
          result.year = String(" '" + result.year.slice(-2));
      }
      return result.toString();
    };
    switch (strategy) {
      case "1m":
      case "5m":
      case "15m":
      case "30m":
        this.strategy = this.strategyMinute;
        break;
      case "1h":
      case "2h":
      case "3h":
      case "4h":
      case "6h":
      case "8h":
      case "12h":
        this.strategy = this.strategyMinute;
        break;
      case "1d":
      case "3d":
      case "1w":
        this.strategy = this.strategyDaily;
        break;
      case "1M":
        this.strategy = this.strategyAnnual;
        break;
      default:
        this.strategy = this.strategy00;
    }
    this.datumFormat = (d, i, a) => {
      let dLinear = d,
        dDate;
      if (this.dataProvider && this.dataProvider.data[d]) {
        dDate = this.dataProvider.data[d]._dateObj;
      } else {
        return "";
      }
      d = { dLinear, dDate: this.makeOffsetDate(dDate, this.offset) };

      this.ticksArray = this.axis.scale().ticks();
      this.ticksArrayDate = this.ticksArray.map((i) =>
        this.dataProvider.data[i]
          ? this.dataProvider.data[i]._dateObj
          : new Date(),
      );
      // this.scale = this.axis.scale(); // has to update otherwise something else breaks

      let result = this.strategy(d, i, a);

      this.preD = d.dDate;
      this.preDLinear = d.dLinear;

      return result;
    };
  }
}
