const {
  S3Client, HeadObjectCommand, GetObjectCommand, CreateMultipartUploadCommand,
  UploadPartCommand, CompleteMultipartUploadCommand, AbortMultipartUploadCommand,
} = require("@aws-sdk/client-s3");

const MiB = 1024 * 1024;
const MIN_PART = 5 * MiB;
const MAX_PART = 5 * 1024 * MiB;
const MAX_PARTS = 10000;
const MAX_OBJECT = 5 * 1024 * 1024 * MiB;   // 5 TiB
const META = ["ContentType", "Metadata", "CacheControl", "ContentEncoding", "ContentDisposition", "ContentLanguage", "Expires"];


function envFor(side, name, fallback) {
  return process.env[`${side}_${name}`] || process.env[name] || fallback;
}

function client(side) {
  return new S3Client({
    endpoint: envFor(side, "ENDPOINT"),
    region: envFor(side, "REGION", "us-east-1"),
    forcePathStyle: true,
    credentials: {
      accessKeyId: envFor(side, "ACCESS_KEY"),
      secretAccessKey: envFor(side, "SECRET_KEY"),
    },
    // socketTimeout is idle based, so a slow part is fine but a dead socket is not
    requestHandler: { connectionTimeout: 5000, socketTimeout: 60000 },
    maxAttempts: 1,   // a streamed part cannot be replayed, so the sdk must not try
    // otherwise the sdk wraps every streamed part in a chunked checksum stream
    requestChecksumCalculation: "WHEN_REQUIRED",
    responseChecksumValidation: "WHEN_REQUIRED",
    logger: { debug() {}, info() {}, warn() {}, error() {} },   // our own log lines are enough
  });
}

// smallest part that still fits the object in 10000 parts, never below 5 MiB
function partSizeFor(bytes) {
  const evenSplit = Math.ceil(bytes / MAX_PARTS);
  return Math.min(MAX_PART, Math.max(MIN_PART, evenSplit));
}

function formatSize(bytes) {
  if (bytes < MiB)
    return `${bytes} B`;
  return (bytes / MiB).toFixed(1) + " MiB";
}

function parseLocation(location) {
  if (typeof location !== "string") 
    return location;
  const slash = location.indexOf("/");
  if (slash < 1 || slash === location.length - 1) {
    throw new Error(`expected bucket/key, got "${location}"`);
  }
  return { Bucket: location.slice(0, slash), Key: location.slice(slash + 1) };
}

function consoleLogger() {
  function line(level, message) {
    return `${new Date().toISOString()} ${level.padEnd(5)} ${message}`;
  }
  return {
    info(message) { console.log(line("INFO", message)); },
    warn(message) { console.warn(line("WARN", message)); },
    error(message) { console.error(line("ERROR", message)); },
  };
}

function taggedLogger(logger, tag) {
  return {
    info(message) { logger.info(`${tag} ${message}`); },
    warn(message) { logger.warn(`${tag} ${message}`); },
    error(message) { logger.error(`${tag} ${message}`); },
  };
}

async function copy(from, to, opts = {}) {
  from = parseLocation(from);
  to = parseLocation(to);
  const log = taggedLogger(opts.log || consoleLogger(), `[${from.Bucket}/${from.Key}]`);
  const parallel = Math.max(1, opts.parallel || Number(process.env.PARALLEL) || 8);

  const src = client("SRC");
  const dst = client("DST");
  const t0 = Date.now();

  try {
    let head;
    try {
      head = await src.send(new HeadObjectCommand(from));
    } catch (e) {
      if (e.$metadata?.httpStatusCode === 404) throw new Error(`${from.Bucket}/${from.Key} not found on source`);
      throw e;
    }
    const size = head.ContentLength;
    if (size > MAX_OBJECT) throw new Error(`${formatSize(size)} is over the 5 TiB S3 object limit`);

    const meta = {};
    for (const name of META) meta[name] = head[name];

    const partSize = partSizeFor(size);
    const count = Math.max(1, Math.ceil(size / partSize));
    const logEvery = Math.max(1, Math.ceil(count / 20));
    log.info(`${formatSize(size)} in ${count} parts of ${formatSize(partSize)}, ${parallel} parallel -> ${to.Bucket}/${to.Key}`);

    const { UploadId } = await dst.send(new CreateMultipartUploadCommand({ ...to, ...meta }));
    log.info(`upload id ${UploadId}`);


    async function copyPart(index) {
      const start = index * partSize;
      const end = Math.min(start + partSize, size) - 1;
      const length = end - start + 1;
      // an empty object has no bytes to ask for, so no Range header
      const range = size > 0 ? `bytes=${start}-${end}` : undefined;

      const { Body } = await src.send(new GetObjectCommand({ ...from, Range: range }));
      const uploaded = await dst.send(new UploadPartCommand({
        ...to, UploadId, PartNumber: index + 1, Body, ContentLength: length,
      }));
      return uploaded.ETag;
    }

    // workers take the next part until none are left; the first failure stops all of them
    const etags = new Array(count);
    let nextPart = 0;
    let doneParts = 0;
    let failure = null;

    async function worker() {
      while (nextPart < count && !failure) {
        const index = nextPart++;
        try {
          etags[index] = await copyPart(index);
        } catch (e) {
          failure = e;
          return;
        }
        doneParts++;
        if (doneParts % logEvery === 0 || doneParts === count) {
          const copied = Math.min(doneParts * partSize, size);
          log.info(`part ${doneParts}/${count} (~${formatSize(copied)})`);
        }
      }
    }

    const workers = Array.from({ length: Math.min(parallel, count) }, worker);
    await Promise.all(workers);

    try {
      if (failure) throw failure;
      const parts = etags.map((ETag, i) => ({ ETag, PartNumber: i + 1 }));
      const result = await dst.send(new CompleteMultipartUploadCommand({
        ...to, UploadId, MultipartUpload: { Parts: parts },
      }));
      const seconds = (Date.now() - t0) / 1000;
      log.info(`done in ${seconds.toFixed(1)}s, ${formatSize(size / seconds)}/s, etag ${result.ETag}`);
      return result;
    } catch (e) {
      // abort so no half-uploaded parts are left behind billing space
      log.error(`${e.name}: ${e.message}, aborting upload ${UploadId}`);
      try {
        await dst.send(new AbortMultipartUploadCommand({ ...to, UploadId }));
      } catch (abortError) {
        log.warn(`abort failed: ${abortError.message}`);
      }
      throw e;
    }
  } finally {
    src.destroy();
    dst.destroy();
  }
}

module.exports = copy;

if (require.main === module) {
  const [from, to] = process.argv.slice(2);
  if (!from || !to) {
    console.error("usage: node copy.js src-bucket/key dst-bucket/key");
    process.exit(2);
  }
  copy(from, to)
    .then(() => process.exit(0))
    .catch((e) => {
      console.error(`copy failed: ${e.name}: ${e.message}`);
      process.exit(1);
    });
}
