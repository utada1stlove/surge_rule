#!/usr/bin/env node
import { readFile, writeFile, mkdir, readdir, rm } from "node:fs/promises";
import { resolve, join } from "node:path";
import { argv, exit } from "node:process";

const args = new Map();
for (let i = 2; i < argv.length; i += 1) {
  if (argv[i].startsWith("--")) args.set(argv[i].slice(2), argv[i + 1]);
}
const manifestPath = resolve(args.get("manifest") ?? "config/external-manifest.json");
const outputDir = resolve(args.get("output") ?? "rules/vendor");

const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
const sources = manifest.sources ?? [];
if (!Array.isArray(sources) || sources.length === 0) {
  console.error("No sources in manifest");
  exit(2);
}
await mkdir(outputDir, { recursive: true });
const expected = new Set(sources.map((s) => `${s.name}.list`));
for (const f of await readdir(outputDir).catch(() => [])) {
  if (f.endsWith(".list") && !expected.has(f)) await rm(join(outputDir, f));
}

function normalize(text, format = "surge") {
  const lines = new Set();
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#") || line.startsWith(";") || line.startsWith("//")) continue;
    if (format === "domain-list") {
      const domain = line.replace(/^full:/i, "").replace(/^\|\|/, "").replace(/^https?:\/\//, "").replace(/\^.*$/, "").replace(/\/$/, "");
      if (/^[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}$/.test(domain)) lines.add(`DOMAIN-SUFFIX,${domain}`);
      continue;
    }
    // Keep Surge rule line as-is, but normalize whitespace around commas
    const parts = line.split(",").map((p) => p.trim());
    if (parts.length === 0) continue;
    // Basic validation: must be known Surge type or skip
    const type = parts[0].toUpperCase();
    const allowed = new Set(["DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-REGEX", "IP-CIDR", "IP-CIDR6", "GEOIP", "URL-REGEX", "USER-AGENT", "PROCESS-NAME", "RULE-SET"]);
    if (!allowed.has(type) && !line.includes(",")) continue;
    lines.add(parts.join(","));
  }
  return [...lines].sort();
}

let fetched = [];
for (const { name, url, format } of sources) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`fetch failed ${url}: ${res.status} ${res.statusText}`);
  const text = await res.text();
  const lines = normalize(text, format);
  const header = [
    `# Vendored from ${url}`,
    `# name: ${name}`,
    `# fetched-at: ${new Date().toISOString()}`,
    `# Do not edit manually; regenerate with tools/sync-external.mjs.`,
    "",
  ];
  await writeFile(join(outputDir, `${name}.list`), `${header.concat(lines).join("\n")}\n`, "utf8");
  fetched.push({ name, url, count: lines.length });
}
console.log(JSON.stringify({ fetched }, null, 2));
