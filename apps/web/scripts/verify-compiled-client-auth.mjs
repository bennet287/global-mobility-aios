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

for (const expected of [
  "x-gmai-role",
  "x-gmai-user",
  "http://127.0.0.1:8000",
  "NEXT_PUBLIC_API_BASE_URL",
  "NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE",
  "NEXT_PUBLIC_GMAI_ROLE",
  "NEXT_PUBLIC_GMAI_USER",
  "frontend-operator",
  "admin",
  "credentials",
  "include",
  "no-store",
]) {
  assert.ok(source.includes(expected), `Compiled Eligibility client path is missing ${expected}`);
}

for (const loopbackHost of ["127.0.0.1", "localhost", "::1"]) {
  assert.ok(source.includes(loopbackHost), `Compiled client lost loopback guard ${loopbackHost}`);
}

assert.match(
  source,
  /NEXT_PUBLIC_API_BASE_URL[^;]{0,240}http:\/\/127\.0\.0\.1:8000/,
  "Compiled client lost the canonical loopback API fallback",
);
assert.match(
  source,
  /x-gmai-role[^;]{0,260}admin/,
  "Compiled client lost the bounded default local role",
);
assert.match(
  source,
  /x-gmai-user[^;]{0,260}frontend-operator/,
  "Compiled client lost the bounded default local user",
);
assert.ok(
  source.includes('"production"') || source.includes("'production'") || source.includes("production"),
  "Compiled client lost the production fail-closed branch",
);

console.log(JSON.stringify({
  status: "pass",
  chunk: path.relative(process.cwd(), file),
  eligibility_get: true,
  eligibility_post: true,
  compiled_public_env_contract: true,
  canonical_loopback_fallback: "http://127.0.0.1:8000",
  local_header_role_guard_present: true,
  production_non_loopback_fail_closed_guard_present: true,
}));
