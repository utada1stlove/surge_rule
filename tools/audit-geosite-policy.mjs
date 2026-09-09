#!/usr/bin/env node

import { readFile, readdir } from "node:fs/promises";
import { resolve, join } from "node:path";

const root = resolve(process.argv[2] ?? ".");
const manifest = JSON.parse(await readFile(join(root, "config/geosite-manifest.json"), "utf8"));
const policy = JSON.parse(await readFile(join(root, "config/geosite-policy.json"), "utf8"));
const profile = await readFile(join(root, policy.profile), "utf8");
const files = new Set((await readdir(join(root, "rules/generated"))).filter((name) => name.endsWith(".list")));
const errors = [];
const warnings = [];

for (const name of manifest.geosites) {
  if (manifest.exclude?.includes(name)) {
    errors.push(`excluded geosite must not be generated: ${name}`);
    continue;
  }
  if (!files.has(`${name}.list`)) errors.push(`missing generated file: ${name}.list`);
  const mapping = policy.mappings[name];
  if (!mapping) errors.push(`missing policy mapping: ${name}`);
  if (mapping && !mapping.policy) errors.push(`missing policy value: ${name}`);
  if (mapping?.runtime?.length === 0) warnings.push(`reference-only or locally covered: ${name} -> ${mapping.policy}`);
  for (const source of mapping?.runtime ?? []) {
    const line = profile.split("\n").find((candidate) => candidate.includes(source));
    if (!line) errors.push(`runtime source not referenced by ${policy.profile}: ${name} -> ${source}`);
    else if (!line.endsWith(`,${mapping.policy}`) && !line.includes(`,${mapping.policy},`)) {
      errors.push(`runtime policy mismatch: ${name} expects ${mapping.policy}: ${line}`);
    }
  }
}

for (const name of Object.keys(policy.mappings)) {
  if (!manifest.geosites.includes(name)) errors.push(`policy mapping is not in geosite manifest: ${name}`);
}
for (const excluded of manifest.exclude ?? []) {
  if (files.has(`${excluded}.list`)) errors.push(`excluded geosite has generated file: ${excluded}.list`);
}
if (profile.split("\n").filter((line) => /^FINAL,/.test(line)).length !== 1) errors.push("profile must contain exactly one FINAL rule");
if (!/^FINAL,/.test(profile.trim().split("\n").at(-1))) errors.push("FINAL must be the last profile rule");

for (const warning of warnings) console.warn(`WARN ${warning}`);
if (errors.length) {
  for (const error of errors) console.error(`ERROR ${error}`);
  process.exitCode = 1;
} else {
  console.log(`OK: audited ${manifest.geosites.length} geosites; ${files.size} independent generated files`);
}
