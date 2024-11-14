### Data Flow

The backend and frontend communicate through WebSocket to ensure efficient and real-time data updates. Aside from this, the server only serves static files over HTTP/S; there is no other form of communication.

### Data

- SQLite is used for caching.
- SQLite also stores alert states, without user information.
- Charts are saved in the browser using `localStorage`.

### Deployment

The deployment process involves building the frontend and integrating it into a Docker container alongside the backend. The backend serves the frontend, resulting in a single, self-contained container without external dependencies. This straightforward design enables the chaining of containers, facilitating a scalable architecture.

### Data Provider

Each data provider functions as a separate process, communicating with the FastAPI application via queues. This setup ensures efficient and asynchronous message processing between the providers and the API. For detailed information on message handling, refer to `websocket_server.py` and `provider.py`.

Learn more in [Add Data Source](../backend/data.md).

### Thread Usage

To ensure timely and non-blocking execution, alerts are processed using threads. Indicators utilize `ThreadPoolExecutor` for efficient parallel computation. Additionally, there is an asyncio thread within FastAPI to manage asynchronous tasks, optimizing performance and responsiveness across the system.

### Periodic Actions

To maintain optimal performance and reliability, the system performs periodic actions managed in `websocket_server.py`. These actions include cleaning up cached data to free resources. If live updates are not detected, the system sends notifications to providers to restart the live data stream, ensuring continuous data availability and preventing disruptions.

### WebGL vs. SVG

We utilize WebGL for rendering lines, candlesticks, and bars on the GPU, harnessing the speed of the D3FC library. This approach ensures optimal performance.

Conversely, elements such as axes, labels, and drawings are rendered using SVG, allowing us to implement high-level features while maintaining fast performance.

The remainder of the interface is built with standard HTML, CSS, and JavaScript to keep the application lightweight, avoiding the overhead of high-level frameworks like React or Angular.

### Consequences of Using WebGL

Mobile devices support WebGL, but they often face limitations with smaller integer sizes, leading to integer overflow issues. For instance, values exceeding 65,535 can cause overflow. Similarly, very small numbers can become problematic. To address these issues, we implemented additional logic to scale down large values, for example by a factor of 10,000, and scale up small values, ensuring all values sent to WebGL remain within a manageable range, preventing overflow and underflow problems.
