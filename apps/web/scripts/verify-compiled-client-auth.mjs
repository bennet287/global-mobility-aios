import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const outputDirectory = path.resolve(process.argv[2] || ".next");
const chunksDirectory = path.join(outputDirectory, "static", "chunks");

async function javascriptFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(entries.map(async (entry) => {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) return javascriptFiles(target);
    return entry.isFile() && entry.name.endsWith(".js") ? [target] : [];
  }));
  return nested.flat();
}

const files = await javascriptFiles(chunksDirectory);
const candidates = [];
for (const file of files) {
  const source = await readFile(file, "utf8");
  if (
    source.includes("/api/v1/eligibility/evaluate") &&
    source.includes("/api/v1/eligibility/") &&
    source.includes("v13_10_2_15_f01_browser_runtime")
  ) {
    candidates.push({ file, source });
  }
}

assert.equal(candidates.length, 1, "Expected one compiled client chunk containing the Eligibility API/config path");
const [{ file, source }] = candidates;
for (const expected of ["x-gmai-role", "x-gmai-user"]) {
  assert.ok(source.includes(expected), `Compiled Eligibility client path is missing ${expected}`);
}
for (const [setting, expected] of Object.entries({
  apiBase: "http://127.0.0.1:8000",
  authAllowHeaderRole: "true",
  role: "admin",
  user: "frontend-operator",
})) {
  assert.match(
    source,
    new RegExp(`${setting}\\s*:\\s*["']${expected.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")}["']`),
    `Compiled Eligibility client config did not statically resolve ${setting}=${expected}`,
  );
}

console.log(JSON.stringify({
  status: "pass",
  chunk: path.relative(process.cwd(), file),
  eligibility_get: true,
  eligibility_post: true,
  api_base: "http://127.0.0.1:8000",
  allow_header_role: true,
  role: "admin",
  user: "frontend-operator",
}));
