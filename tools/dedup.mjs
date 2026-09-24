#!/usr/bin/env node
import { readFile, readdir, writeFile, mkdir } from "node:fs/promises";
import { resolve, join } from "node:path";

const root = resolve(process.argv[2] ?? ".");
const diyDir = join(root, "rules");
const generatedDir = join(root, "rules/generated");
const vendorDir = join(root, "rules/vendor");
const outPath = join(root, "reports/dedup.json");

function effectiveLines(text) {
  const lines = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#") || line.startsWith(";")) continue;
    lines.push(line);
  }
  return lines;
}
async function loadDir(dir, label) {
  const map = new Map(); // effective line -> {file, label}
  let files = [];
  try { files = (await readdir(dir)).filter((f) => f.endsWith(".list")); } catch { return map; }
  for (const file of files) {
    const text = await readFile(join(dir, file), "utf8");
    for (const line of effectiveLines(text)) {
      const key = line;
      if (!map.has(key)) map.set(key, { file: `${label}/${file}`, label });
    }
  }
  return map;
}
function shadowReport(higher, lower) {
  const overlaps = [];
  for (const [line, info] of lower.entries()) {
    if (higher.has(line)) {
      overlaps.push({ rule: line, shadowed_by: higher.get(line).file, file: info.file });
    }
  }
  return overlaps;
}
const diy = await loadDir(diyDir, "rules");
const generated = await loadDir(generatedDir, "rules/generated");
const vendor = await loadDir(vendorDir, "rules/vendor");

// Priority: diy > generated > vendor
const higherThanGenerated = diy;
const higherThanVendor = new Map([...diy, ...generated]);

const genOverlaps = shadowReport(higherThanGenerated, generated);
const vendorOverlaps = shadowReport(higherThanVendor, vendor);

// Also report internal duplicates already flagged by lint, plus cross
const total = genOverlaps.length + vendorOverlaps.length;
const report = {
  generated_at: new Date().toISOString(),
  priority: ["diy (rules/*.list)", "generated (rules/generated/*.list)", "vendor (rules/vendor/*.list)"],
  counts: { diy: diy.size, generated: generated.size, vendor: vendor.size, shadowed_generated: genOverlaps.length, shadowed_vendor: vendorOverlaps.length, total_shadowed: total },
  shadowed_generated: genOverlaps.slice(0, 200),
  shadowed_vendor: vendorOverlaps.slice(0, 500),
  note: "Truncated to 200/500 entries; full counts in counts field. Shadowed means lower-priority file contains a rule already present in higher-priority layer; it will never match due to first-match semantics.",
};

await mkdir(join(root, "reports"), { recursive: true });
await writeFile(outPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ counts: report.counts, report: outPath }, null, 2));
if (total > 0) console.warn(`WARN ${total} shadowed rules found; see ${outPath}`);
