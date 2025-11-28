FROM node:20 AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm install

COPY frontend/ .

RUN npm run build

FROM python:3.12-slim AS backend

ARG POPULATE=false

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

COPY backend/requirements.txt ./
RUN pip3 install --upgrade pip setuptools wheel && pip3 install -r requirements.txt

COPY backend/ .

RUN if [ "$POPULATE" = "true" ] ; then \
      python3 populate.py; \
    fi

COPY --from=frontend-builder /app/frontend/dist ./dist

EXPOSE 8000

CMD ["python3", "server.py"]
