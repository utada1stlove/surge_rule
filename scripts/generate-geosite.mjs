#!/usr/bin/env node

import { readFile, writeFile, mkdir, rm, readdir } from "node:fs/promises";
import { resolve, join } from "node:path";
import { argv, exit } from "node:process";

const args = new Map();
for (let i = 2; i < argv.length; i += 1) {
  if (argv[i].startsWith("--")) args.set(argv[i].slice(2), argv[i + 1]);
}

const input = args.get("input");
const manifestPath = resolve(args.get("manifest") ?? "config/geosite-manifest.json");
const outputDir = resolve(args.get("output") ?? "rules/generated");
if (!input) {
  console.error("Usage: generate-geosite.mjs --input geosite.dat [--manifest file] [--output dir]");
  exit(2);
}

const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
const wanted = new Set(manifest.geosites);
const excluded = new Set(manifest.exclude ?? []);
const bytes = await readFile(resolve(input));

function varint(buffer, offset) {
  let value = 0n;
  let shift = 0n;
  let index = offset;
  while (index < buffer.length) {
    const byte = buffer[index++];
    value |= BigInt(byte & 0x7f) << shift;
    if ((byte & 0x80) === 0) return [Number(value), index];
    shift += 7n;
    if (shift > 63n) throw new Error("protobuf varint is too large");
  }
  throw new Error("truncated protobuf varint");
}

function fields(buffer) {
  const result = [];
  let offset = 0;
  while (offset < buffer.length) {
    const [key, afterKey] = varint(buffer, offset);
    offset = afterKey;
    const field = key >>> 3;
    const wire = key & 7;
    if (wire === 0) {
      const [value, after] = varint(buffer, offset);
      result.push({ field, wire, value });
      offset = after;
    } else if (wire === 2) {
      const [length, afterLength] = varint(buffer, offset);
      const end = afterLength + length;
      if (end > buffer.length) throw new Error("truncated protobuf field");
      result.push({ field, wire, value: buffer.subarray(afterLength, end) });
      offset = end;
    } else if (wire === 1) {
      result.push({ field, wire, value: buffer.subarray(offset, offset + 8) });
      offset += 8;
    } else if (wire === 5) {
      result.push({ field, wire, value: buffer.subarray(offset, offset + 4) });
      offset += 4;
    } else {
      throw new Error(`unsupported protobuf wire type ${wire}`);
    }
  }
  return result;
}

function text(buffer) {
  return new TextDecoder().decode(buffer);
}

function parseDomain(buffer) {
  let type = 0;
  let value = "";
  for (const item of fields(buffer)) {
    if (item.field === 1 && item.wire === 0) type = item.value;
    if (item.field === 2 && item.wire === 2) value = text(item.value);
  }
  return { type, value };
}

function parseSite(buffer) {
  let name = "";
  const domains = [];
  for (const item of fields(buffer)) {
    if (item.field === 1 && item.wire === 2) name = text(item.value).toLowerCase();
    if (item.field === 2 && item.wire === 2) domains.push(parseDomain(item.value));
  }
  return { name, domains };
}

const sites = new Map();
for (const item of fields(bytes)) {
  if (item.field === 1 && item.wire === 2) {
    const site = parseSite(item.value);
    sites.set(site.name, site);
  }
}

const typePrefix = new Map([
  [0, "DOMAIN-KEYWORD"],
  [1, "DOMAIN-REGEX"],
  [2, "DOMAIN-SUFFIX"],
  [3, "DOMAIN"]
]);
await mkdir(outputDir, { recursive: true });
const expectedOutputs = new Set([...wanted].map((name) => `${name}.list`));
for (const filename of await readdir(outputDir)) {
  if (filename.endsWith(".list") && !expectedOutputs.has(filename)) {
    await rm(join(outputDir, filename));
  }
}
const generated = [];
for (const name of manifest.geosites) {
  if (excluded.has(name)) continue;
  const site = sites.get(name.toLowerCase());
  if (!site) throw new Error(`geosite not found in upstream file: ${name}`);
  const lines = new Set();
  for (const domain of site.domains) {
    const prefix = typePrefix.get(domain.type);
    if (!prefix || !domain.value) continue;
    lines.add(`${prefix},${domain.value}`);
  }
  const output = join(outputDir, `${name}.list`);
  const header = [
    `# Generated from ${manifest.source.url}`,
    `# geosite: ${name}`,
    "# Do not edit manually; regenerate with scripts/generate-geosite.mjs.",
    ""
  ];
  await writeFile(output, `${header.concat([...lines].sort()).join("\n")}\n`, "utf8");
  generated.push({ name, count: lines.size, output });
}

console.log(JSON.stringify({ generated: generated.map(({ name, count }) => ({ name, count })) }, null, 2));
