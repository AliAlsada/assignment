# MediaLive stack

Creates what the stream needs in AWS: an S3 bucket for the recordings, an IAM role for
MediaLive, an RTP push input restricted to the source address, and a single-pipeline
channel that encodes HEVC 1080p at 12 Mbps with AAC 192 kbps and writes MPEG-TS files
to the bucket.

```
export PULUMI_BACKEND_URL="file://$PWD/.state"
export PULUMI_CONFIG_PASSPHRASE=""
mkdir -p .state
pulumi stack select dev --create
pulumi up
aws medialive describe-input --input-id $(pulumi stack output input_id) --query 'Destinations[].Url'
```

The first URL is the RTP endpoint OBS sends to.

Set `stream:source_cidr` in `Pulumi.dev.yaml` to the public address of the machine
that runs OBS. `pulumi destroy` removes everything, including the recordings.
