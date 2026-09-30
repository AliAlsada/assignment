FROM nodered/node-red:4.1.15-22-minimal

COPY --chown=node-red:node-red package.json copy.js /data/

RUN cd /data && npm install --omit=dev --no-audit --no-fund

COPY --chown=node-red:node-red nodered/settings.js nodered/flows.json /data/
