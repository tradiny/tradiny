## Configuration

Create `backend/.env` and enter configuration variables

```
CSV_FILE_PATH=sample.csv # Note, leave empty if you want to disable
CSV_DATE_COLUMN=timestamp
CSV_DATE_COLUMN_FORMATTER=timestamp_formatter

POLYGON_IO_API_KEY=...

BINANCE_API_KEY=... # Note, you can use any string here, all Binance requests are public
BINANCE_API_SECRET=...

OPENAI_API_KEY=...
```

Note, see all env variables in `backend/config.py`.

### (Optional) Setup Script

Before running the setup script, ensure you install the necessary requirements with the following command:

```bash
pip install -r requirements.txt
```

Once the dependencies are installed, execute the setup script in your terminal:

```bash
python setup.py
```

This script will help configure your environment efficiently.

## Building

Build the image:

```
docker build --build-arg POPULATE=true -t tradiny-charts:latest .
```

## Running locally

Run the image:

```
docker run -d -p 8000:8000 --name tradiny-charts tradiny-charts:latest
```

Navigate to `http://localhost:8000`, you should see the application.

## Running on server

Create DNS A records to link your server IP with the domain for your application.

Create `docker-compose.yml`

```yaml
services:
  traefik:
    image: traefik:v3.1.2
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.httpchallenge=true"
      - "--certificatesresolvers.myresolver.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.myresolver.acme.email=tradiny@tradiny.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080" # Adds the dashboard port for easier debugging
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "letsencrypt:/letsencrypt"
    restart: always
    labels:
      - "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"

  tradiny-populate:
    image: tradiny-charts:latest
    command: python3 populate.py
    volumes:
      - ./host:/app/host
    profiles:
      - populate

  tradiny-charts:
    image: tradiny-charts:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.tradiny-charts-http.rule=Host(`demo.tradiny.com`)" # HTTP router
      - "traefik.http.routers.tradiny-charts-https.rule=Host(`demo.tradiny.com`)" # HTTPS router
      - "traefik.http.services.tradiny-charts.loadbalancer.server.port=8000"
      - "traefik.http.routers.tradiny-charts-http.entrypoints=web"
      - "traefik.http.routers.tradiny-charts-http.middlewares=redirect-to-https"
      - "traefik.http.routers.tradiny-charts-https.entrypoints=websecure"
      - "traefik.http.routers.tradiny-charts-https.tls=true"
      - "traefik.http.routers.tradiny-charts-https.tls.certresolver=myresolver"
    restart: always
    volumes:
      - ./host:/app/host
```

Notice in this example

1. We configure to run the application at `https://demo.tradiny.com`
1. We use [Traefik proxy](https://traefik.io/) to  manage HTTPS certificates.

Now, populate the DB:

```
docker compose --profile populate up tradiny-populate
```

Run the application in daemon mode:

```
docker compose up -d
```

Navigate to `https://demo.tradiny.com`, you should see the application.

## Preserving Changes

First, setup volume in your `docker-compose.yml`

```yaml
    volumes:
      - ./host:/app/host
```

Second,

1. Setup `DB` env variable to `/app/host/db.sqlite3`
1. Setup `VAPID_KEY_PATH` env variable to `/app/host/private_key.pem`
