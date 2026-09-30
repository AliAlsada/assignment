# Multi-container system on Docker Compose

Traefik in front of a static page (nginx), an API (python) and a database (postgres).

## Start

```
cp .env.example .env            # then set DB_PASSWORD
docker compose up -d --build
```

Open `http://localhost` for the page and `http://localhost/api` for the API.

If port 80 is taken, change `HTTP_PORT` in `.env`.

## Check

```
docker compose ps
docker compose logs -f
```

## Stop

```
docker compose down             # keeps the data
docker compose down -v          # deletes the data too
```
