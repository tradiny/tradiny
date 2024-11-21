## Backend

### Requirements

To install the necessary dependencies, run the following command:

```
pip3 install -r requirements.txt
```

Note: Tested with Python 3.12.

### Configuration

Create `backend/.env` to configure the application.

Note, see all env variables in `backend/config.py`.

### Running

To populate the DB, use:

```
python3 populate.py
```

To start the server, use

```
python3 server.py
```

Note: The server uses an SQLite3 database for fast search and caching purposes.

## Frontend

### Dependencies

To install the necessary dependencies, run:

```
npm install
npm update
```

This library has been tested with Node.js version 20.

### Building

To build, use:

```
npm run build
```

Note, you need to run this command for development, because it builds `d3fc`.

### Running

To start the development server using webpack, run:

```
npm start
```

Navigate to `http://localhost:9000/examples/candlestick.html`, for an example chart.
