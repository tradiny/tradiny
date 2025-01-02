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

export class WebSocketManager {
  constructor(url, onopen) {
    this.url = url;
    this.websocket = null;
    this.handler = null;
    this.queue = [];
    this.connect(onopen);
  }

  // Establishes the WebSocket connection
  connect(onopen) {
    this.websocket = new WebSocket(this.url);

    this.websocket.onopen = () => {
      onopen();

      for (let j = 0; j < this.queue.length; j++) {
        this.sendMessage(this.queue[j]);
      }
      this.queue = [];
    };

    this.websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
      alert(`Cannot connect: ${this.url}`);
    };

    this.websocket.onclose = (event) => {
      console.log("WebSocket connection closed:", event);
      // Attempt to reconnect every 5 seconds if the connection is not deliberately closed
      if (!event.wasClean) {
        setTimeout(() => this.connect(onopen), 5000);
      }
    };

    this.onMessage(); // bind onmessage
  }

  // Sends a message through the WebSocket
  sendMessage(message) {
    if (this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(message);
    } else {
      this.queue.push(message);
    }
  }

  // Sets up a handler for incoming WebSocket messages
  onMessage(handler) {
    if (handler) {
      this.handler = handler;
    }

    if (this.handler) {
      this.websocket.onmessage = (event) => {
        this.handler(JSON.parse(event.data));
      };
    }
  }
}
