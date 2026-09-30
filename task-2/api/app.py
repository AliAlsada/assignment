import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import psycopg

DSN = "host=db dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}".format(**os.environ)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with psycopg.connect(DSN) as conn:
            (now,) = conn.execute("select now()").fetchone()
        body = f"hello from api, db time is {now}\n".encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


HTTPServer(("", 8000), Handler).serve_forever()
