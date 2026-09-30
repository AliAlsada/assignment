# Copy a file between S3 buckets with Node-RED

A Node-RED flow that copies a file from one S3 bucket to another using multipart upload.
Two RustFS servers (S3-compatible) stand in for the source and the destination.

## Start

```
cp .env.example .env
docker compose up -d --build
```

This creates the `src` and `dst` buckets and uploads a 100 MiB `sample.bin` to the source.

## Run the copy

Open `http://localhost:1880` and click the button on the `copy` inject node.
The result appears in the Debug sidebar.

To copy another file, edit the payload of the inject node:

```
{"from":"src/sample.bin","to":"dst/sample.bin"}
```

## Check

```
docker compose logs -f nodered
docker compose run --rm setup -c 'aws --endpoint-url http://dst:9000 s3 ls s3://dst'
```

## Stop

```
docker compose down             # keeps the data
docker compose down -v          # deletes the data too
```
