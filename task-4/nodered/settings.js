module.exports = {
  flowFile: "flows.json",
  uiPort: 1880,
  functionGlobalContext: {
    s3copy: require("/data/copy.js"),
  },
  logging: { console: { level: "info" } },
};
