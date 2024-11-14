/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

function getValue(n) {
  return typeof n === "number" ? n : n.value;
}

class SegmentTree {
  constructor(data, fn) {
    if (!fn) {
      throw new Error("Function parameter 'fn' is required.");
    }

    const n = data.length;
    const buf = new Array(n << 1);

    for (let i = 0; i < n; ++i) buf[i + n] = data[i];
    for (let i = n - 1; i > 0; --i) {
      buf[i] = fn.combine(buf[i << 1], buf[(i << 1) | 1]);
    }

    this.buf = buf;
    this.n = n;
    this.fn = fn;
  }

  update(i, v) {
    for (this.buf[(i += this.n)] = v; i > 1; i >>= 1)
      this.buf[i >> 1] = this.fn.combine(this.buf[i], this.buf[i ^ 1]);
  }

  query(l, r) {
    let res = this.fn.identity;

    for (l += this.n, r += this.n; l < r; l >>= 1, r >>= 1) {
      if (l & 1) res = this.fn.combine(res, this.buf[l++]);
      if (r & 1) res = this.fn.combine(res, this.buf[--r]);
    }

    return res;
  }
}

const ops = {
  combine(a, b) {
    return {
      min: getValue(a.min) < getValue(b.min) ? a.min : b.min,
      max: getValue(a.max) > getValue(b.max) ? a.max : b.max,
    };
  },
  identity: {
    min: Number.MAX_SAFE_INTEGER,
    max: Number.MIN_SAFE_INTEGER,
  },
};

export class DequeOfSegmentTrees {
  constructor(id) {
    this.id = id;
    this.segmentTrees = [];
    this.totalSize = 0;
    this.fn = ops;
    this.shift = 0;
  }

  setShift(shift) {
    this.shift = shift;
  }

  replaceNaNs(data) {
    for (let i = 0; i < data.length; i++) {
      if (isNaN(data[i].min)) {
        let j = i;
        // Find the closest previous value
        while (j >= 0 && isNaN(data[j].min)) {
          j--;
        }
        let prevValue = j >= 0 ? data[j].min : NaN;

        j = i;
        // Find the closest next value
        while (j < data.length && isNaN(data[j].min)) {
          j++;
        }
        let nextValue = j < data.length ? data[j].min : NaN;

        // Replace NaN with the closest available value
        if (!isNaN(prevValue) && !isNaN(nextValue)) {
          data[i].min = i - j < j - i ? prevValue : nextValue;
        } else if (!isNaN(prevValue)) {
          data[i].min = prevValue;
        } else if (!isNaN(nextValue)) {
          data[i].min = nextValue;
        }
        data[i].max = data[i].min;
      }
    }
    return data;
  }
  lastDatapointUpdate(data) {
    if (data.length !== 1) {
      throw new Error("Input array should contain exactly one element.");
    }

    if (this.segmentTrees.length > 0) {
      // Get the last segment tree
      const lastSegmentTree = this.segmentTrees[this.segmentTrees.length - 1];

      // Check if the index exists
      if (lastSegmentTree.n > 0) {
        // Replace the last data point
        const processedData = this.replaceNaNs([
          { min: parseFloat(data[0]), max: parseFloat(data[0]) },
        ]);
        // console.log(this.id, 'updating', data[0]);
        lastSegmentTree.update(lastSegmentTree.n - 1, processedData[0]);
      }
    }
  }

  append(data) {
    const processedData = this.replaceNaNs(
      data.map((value) => ({ min: parseFloat(value), max: parseFloat(value) })),
    );
    const segmentTree = new SegmentTree(processedData, this.fn);
    this.segmentTrees.push(segmentTree);
    this.totalSize += data.length;
  }

  prepend(data) {
    const processedData = this.replaceNaNs(
      data.map((value) => ({ min: parseFloat(value), max: parseFloat(value) })),
    );
    const segmentTree = new SegmentTree(processedData, this.fn);
    this.segmentTrees.unshift(segmentTree);
    this.totalSize += data.length;
  }

  query(l, r) {
    l = Math.round(l);
    r = Math.round(r);

    l -= this.shift;
    r -= this.shift;

    if (r > this.totalSize) {
      r = this.totalSize;
    }

    if (l < 0) {
      l = 0;
    }

    if (l >= r) {
      return { min: undefined, max: undefined };
      throw new Error(
        `l > r? for ${this.id}, from ${l}, to ${r}, cache totalSize ${this.totalSize}`,
      );
    }

    if (this.totalSize === 0) {
      return { min: undefined, max: undefined };
      throw new Error(`No data in cache for ${this.id}`);
    }

    if (l < 0 || r > this.totalSize || l >= r) {
      throw new Error(
        `Invalid query range for ${this.id}, from ${l}, to ${r}, cache totalSize ${this.totalSize}`,
      );
    }

    let res = {
      min: Number.MAX_SAFE_INTEGER,
      max: Number.MIN_SAFE_INTEGER,
    };
    let currentSize = 0;

    for (const segmentTree of this.segmentTrees) {
      const treeSize = segmentTree.n;
      const treeL = Math.max(0, l - currentSize);
      const treeR = Math.min(treeSize, r - currentSize);

      if (treeL < treeR) {
        res = this.fn.combine(res, segmentTree.query(treeL, treeR));
        // console.log(this.id, segmentTree.n, treeL, treeR, segmentTree.query(treeL, treeR), 'combined', res)
      }

      currentSize += treeSize;
      if (currentSize >= r) break;
    }
    // console.log(`${this.id} l=${l}, r=${r}, ${JSON.stringify(res)}, totalSize=${this.totalSize}, shift=${this.shift}`);

    return res;
  }
}
