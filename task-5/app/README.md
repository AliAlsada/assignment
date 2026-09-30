# app

A small HTTP service that reads from and writes to PostgreSQL. It is built into a Docker
image and deployed by the Ansible role `app`.

| Request | Database | Response |
|---|---|---|
| `GET /` | read | database time, version and the number of notes |
| `GET /notes` | read | the last 20 notes |
| `POST /notes` with `{"text": "..."}` | write | the created note, 201 |
| `GET /health` | none | 200 |

The `notes` table is created on the first connection. When the database is not
reachable the service answers 503.

## Configuration

| Variable | Description |
|---|---|
| `LISTEN_ADDRESS`, `LISTEN_PORT` | address and port of the service |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | database connection |
