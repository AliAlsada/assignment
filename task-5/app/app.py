import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import psycopg

DSN = "host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} connect_timeout=3".format(**os.environ)

MAX_BODY = 4096
MAX_TEXT = 500

SCHEMA = """
create table if not exists notes (
    id bigserial primary key,
    text text not null,
    created_at timestamptz not null default now()
)
"""


def connect():
    conn = psycopg.connect(DSN)
    conn.execute(SCHEMA)
    return conn


def note(row):
    return {"id": row[0], "text": row[1], "created_at": str(row[2])}


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, body):
        body = (json.dumps(body) + "\n").encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self.respond(200, {"status": "ok"})

        try:
            with connect() as conn:
                if self.path == "/notes":
                    rows = conn.execute("select id, text, created_at from notes order by id desc limit 20").fetchall()
                    return self.respond(200, [note(row) for row in rows])

                if self.path == "/":
                    now, version, notes = conn.execute(
                        "select now(), current_setting('server_version'), (select count(*) from notes)"
                    ).fetchone()
                    return self.respond(
                        200,
                        {"app": socket.gethostname(), "db_time": str(now), "db_version": version, "notes": notes},
                    )
        except psycopg.Error:
            return self.respond(503, {"error": "database unavailable"})

        self.respond(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/notes":
            return self.respond(404, {"error": "not found"})

        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            return self.respond(413, {"error": "body too large"})

        try:
            text = json.loads(self.rfile.read(length))["text"]
        except (ValueError, KeyError, TypeError):
            return self.respond(400, {"error": 'expected {"text": "..."}'})
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
            return self.respond(400, {"error": f"text must be 1 to {MAX_TEXT} characters"})

        try:
            with connect() as conn:
                row = conn.execute(
                    "insert into notes (text) values (%s) returning id, text, created_at", (text,)
                ).fetchone()
        except psycopg.Error:
            return self.respond(503, {"error": "database unavailable"})

        self.respond(201, note(row))


ThreadingHTTPServer((os.environ["LISTEN_ADDRESS"], int(os.environ["LISTEN_PORT"])), Handler).serve_forever()
