/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

class SegmentTree {
  constructor(data) {
    this.originalData = data; // Store original data
    this.data = data.filter((x) => x !== undefined && x !== null); // Filter out undefined or null values
    this.n = this.data.length;
    this.minTree = new Array(4 * this.n).fill(Infinity); // Tree for range minimum queries
    this.maxTree = new Array(4 * this.n).fill(-Infinity); // Tree for range maximum queries
    this.build();
  }

  build() {
    // Initialize leaves in the segment tree
    for (let i = 0; i < this.n; i++) {
      this.minTree[this.n + i] = this.data[i];
      this.maxTree[this.n + i] = this.data[i];
    }

    // Build the rest of the tree by calculating parents
    for (let i = this.n - 1; i > 0; --i) {
      this.minTree[i] = Math.min(this.minTree[i * 2], this.minTree[i * 2 + 1]);
      this.maxTree[i] = Math.max(this.maxTree[i * 2], this.maxTree[i * 2 + 1]);
    }
  }

  queryRangeMin(l, r) {
    l += this.n;
    r += this.n;
    let res = Infinity;

    while (l <= r) {
      if (l % 2 === 1) {
        res = Math.min(res, this.minTree[l]);
        l++;
      }
      if (r % 2 === 0) {
        res = Math.min(res, this.minTree[r]);
        r--;
      }
      l = l >> 1;
      r = r >> 1;
    }
    return res;
  }

  queryRangeMax(l, r) {
    l += this.n;
    r += this.n;
    let res = -Infinity;

    while (l <= r) {
      if (l % 2 === 1) {
        res = Math.max(res, this.maxTree[l]);
        l++;
      }
      if (r % 2 === 0) {
        res = Math.max(res, this.maxTree[r]);
        r--;
      }
      l = l >> 1;
      r = r >> 1;
    }
    return res;
  }

  queryMin(L, R) {
    return this.queryRangeMin(L, R);
  }

  queryMax(L, R) {
    return this.queryRangeMax(L, R);
  }
}

export class DequeOfSegmentTrees {
  constructor(segmentSize) {
    this.segmentSize = segmentSize;
    this.deque = [];
    this.shift = 0;
  }

  shifted(shift) {
    this.shift = shift;
  }

  prepend(data) {
    if (
      this.deque.length === 0 ||
      this.deque[0].data.length + data.length > this.segmentSize
    ) {
      this.deque.unshift(new SegmentTree(data));
    } else {
      const newData = data.concat(this.deque[0].data);
      this.deque[0] = new SegmentTree(newData); // Rebuild the segment tree with the new data
    }
  }

  append(data) {
    if (
      this.deque.length === 0 ||
      this.deque[this.deque.length - 1].data.length + data.length >
        this.segmentSize
    ) {
      this.deque.push(new SegmentTree(data));
    } else {
      const newData = this.deque[this.deque.length - 1].data.concat(data);
      this.deque[this.deque.length - 1] = new SegmentTree(newData); // Rebuild the segment tree with the new data
    }
  }

  queryMin(startIdx, endIdx) {
    startIdx -= this.shift;
    endIdx -= this.shift;

    let result = Infinity;
    let currentIndex = 0;

    for (let tree of this.deque) {
      let currentSize = tree.originalData.length;

      let treeStart = Math.max(0, startIdx - currentIndex);
      let treeEnd = Math.min(currentSize - 1, endIdx - currentIndex);

      if (treeStart <= treeEnd) {
        result = Math.min(result, tree.queryMin(treeStart, treeEnd));
      }
      currentIndex += currentSize;
      if (currentIndex > endIdx) break;
    }

    return result;
  }

  queryMax(startIdx, endIdx) {
    startIdx -= this.shift;
    endIdx -= this.shift;

    let result = -Infinity;
    let currentIndex = 0;

    for (let tree of this.deque) {
      let currentSize = tree.originalData.length;

      let treeStart = Math.max(0, startIdx - currentIndex);
      let treeEnd = Math.min(currentSize - 1, endIdx - currentIndex);

      if (treeStart <= treeEnd) {
        result = Math.max(result, tree.queryMax(treeStart, treeEnd));
      }
      currentIndex += currentSize;
      if (currentIndex > endIdx) break;
    }

    return result;
  }
}
