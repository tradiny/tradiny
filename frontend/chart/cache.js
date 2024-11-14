/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

import { DequeOfSegmentTrees, ops } from "./tree4.js";

export class CacheHandler {
  constructor(chart) {
    this.chart = chart;
  }

  findFirstDefinedIndex(arr, key) {
    for (let i = 0; i < arr.length; i++) {
      if (arr[i][key] !== undefined) {
        return i;
      }
    }
    return -1;
  }

  stripUndefinedFromLeft(arr) {
    // Calculate the number of undefined values from the left
    let undefinedCount = 0;
    for (let i = 0; i < arr.length; i++) {
      if (arr[i] === undefined) {
        undefinedCount++;
      } else {
        break;
      }
    }

    // Strip the undefined values from the left
    const newArray = arr.slice(undefinedCount);

    return { undefinedCount, newArray };
  }

  buildCaches(dataKeys, addedFromLeft, addedFromRight, shift) {
    if (!this.chart.dataCache) {
      this.chart.dataCache = [];
    }
    for (let i = 0; i < this.chart.panes.length; i++) {
      if (!this.chart.dataCache[i]) {
        this.chart.dataCache[i] = {};
      }
    }
    for (let i = 0; i < this.chart.panes.length; i++) {
      for (let j = 0; j < this.chart.panes[i].metadata.length; j++) {
        for (
          let k = 0;
          k < this.chart.panes[i].metadata[j].dataKeys.length;
          k++
        ) {
          const dataKey = this.chart.panes[i].metadata[j].dataKeys[k];

          if (
            dataKeys &&
            dataKeys.length > 0 &&
            !dataKeys.includes(dataKey.dataKey)
          ) {
            if (shift) {
              const firstDefinedIdx = this.findFirstDefinedIndex(
                this.chart.dataProvider.data,
                dataKey,
              );
              if (firstDefinedIdx !== -1) {
                tree.setShift(firstDefinedIdx);
              }
            }
            continue;
          }

          let data = this.chart.dataProvider.data.map(
            (d) => d[dataKey.dataKey],
          );
          const o = this.stripUndefinedFromLeft(data);
          data = o.newArray;

          this.chart.dataCache[i][dataKey.dataKey] = new DequeOfSegmentTrees(
            dataKey.dataKey,
          );
          this.chart.dataCache[i][dataKey.dataKey].append(data);

          this.chart.dataCache[i][dataKey.dataKey].setShift(o.undefinedCount);
        }
      }
    }
  }

  buildCachesPartial(dataKeys, addedFromLeft, addedFromRight, shift) {
    if (!this.chart.dataCache) {
      this.chart.dataCache = [];
    }
    for (let i = 0; i < this.chart.panes.length; i++) {
      if (!this.chart.dataCache[i]) {
        this.chart.dataCache[i] = {};
      }
    }

    for (let i = 0; i < this.chart.panes.length; i++) {
      for (let dataKey of Object.keys(this.chart.dataCache[i])) {
        let tree = this.chart.dataCache[i][dataKey];

        if (!tree) {
          // create from scratch

          let data = this.chart.dataProvider.data.map((d) => d[dataKey]);
          const o = this.stripUndefinedFromLeft(data);
          data = o.newArray;

          this.chart.dataCache[i][dataKey] = new DequeOfSegmentTrees(dataKey);
          this.chart.dataCache[i][dataKey].append(data);

          this.chart.dataCache[i][dataKey].setShift(o.undefinedCount);
          continue;
        }

        if (dataKeys && dataKeys.length > 0 && !dataKeys.includes(dataKey)) {
          if (shift) {
            const firstDefinedIdx = this.findFirstDefinedIndex(
              this.chart.dataProvider.data,
              dataKey,
            );
            if (firstDefinedIdx !== -1) {
              tree.setShift(firstDefinedIdx);
            }
          }
          continue;
        }

        if (addedFromLeft) {
          let newData = this.chart.dataProvider.data.map((d) => d[dataKey]);

          const o = this.stripUndefinedFromLeft(newData);

          // const firstDefinedIdx = this.findFirstDefinedIndex(this.chart.dataProvider.data, dataKey);
          // if (firstDefinedIdx > addedFromLeft) {
          //     this.chart.dataCache[i][dataKey] = new DequeOfSegmentTrees(dataKey);
          //     this.chart.dataCache[i][dataKey].append(data);
          //     this.chart.dataCache[i][dataKey].setShift(o.undefinedCount);
          //     return;
          // }

          newData = o.newArray.slice(0, addedFromLeft);

          if (newData.length) {
            tree.prepend(newData);
          }
          tree.setShift(o.undefinedCount);

          // console.log(dataKey, tree.totalSize + o.undefinedCount, tree.totalSize, o.undefinedCount);
          // console.log(`prepend newData=${newData.length}, new shift=${o.undefinedCount}`)
        }
        if (addedFromRight) {
          const len = this.chart.dataProvider.data.length - 1;
          let newData = this.chart.dataProvider.data
            .slice(len - addedFromRight, len)
            .map((d) => d[dataKey]);

          tree.append(newData);
        }
        if (addedFromRight === 0) {
          // just update the last candlestick
          const len = this.chart.dataProvider.data.length;
          let newData = this.chart.dataProvider.data
            .slice(len - 1, len)
            .map((d) => d[dataKey]);
          tree.lastDatapointUpdate(newData);
        }
      }
    }
  }
}
