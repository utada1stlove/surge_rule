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

// These generated Apple inventories are retained as source material but are
// not referenced by any active Profile. They must not shadow the separately
// classified Apple vendor feeds, or the Apple/Foreign-Apple split would lose
// matching rules merely because both inventories contain the same hostname.
for (const [line, info] of generated) {
  if (/rules\/generated\/apple(?:-cn)?\.list$/.test(info.file)) generated.delete(line);
}

// Priority: diy > generated > vendor  (diy+geosite 为权威)
const higherThanGenerated = diy;
const higherThanVendor = new Map([...diy, ...generated]);

const genOverlaps = shadowReport(higherThanGenerated, generated);
const vendorOverlaps = shadowReport(higherThanVendor, vendor);

// 产出去重后的 vendor：远端去重掉已在 diy/generated 存在的条目
const shadowedSet = new Set(vendorOverlaps.map((o) => o.rule));
let dedupedCounts = {};
try {
  const files = (await readdir(vendorDir)).filter((f) => f.endsWith(".list") && !f.endsWith(".deduped.list"));
  for (const file of files) {
    const text = await readFile(join(vendorDir, file), "utf8");
    const header = [];
    const body = [];
    for (const raw of text.split(/\r?\n/)) {
      if (raw.startsWith("# Vendored") || raw.startsWith("# name:") || raw.startsWith("# fetched-at") || raw.startsWith("# Do not edit")) header.push(raw);
      else if (raw.trim() && !raw.trim().startsWith("#")) body.push(raw);
    }
    const deduped = body.filter((line) => !shadowedSet.has(line.trim()));
    dedupedCounts[file] = { before: body.length, after: deduped.length, removed: body.length - deduped.length };
    const out = [
      ...header,
      `# deduped-at: ${new Date().toISOString()}`,
      `# deduped-against: diy+generated (${higherThanVendor.size} rules)`,
      "",
      ...deduped.sort(),
    ].join("\n") + "\n";
    await writeFile(join(vendorDir, file.replace(/\.list$/, ".deduped.list")), out, "utf8");
  }
} catch {}

const total = genOverlaps.length + vendorOverlaps.length;
const report = {
  generated_at: new Date().toISOString(),
  priority: ["diy (rules/*.list)", "generated (rules/generated/*.list)", "vendor (rules/vendor/*.list)"],
  counts: { diy: diy.size, generated: generated.size, vendor: vendor.size, shadowed_generated: genOverlaps.length, shadowed_vendor: vendorOverlaps.length, total_shadowed: total, deduped_vendor: dedupedCounts },
  shadowed_generated: genOverlaps.slice(0, 200),
  shadowed_vendor: vendorOverlaps.slice(0, 500),
  note: "Shadowed means lower-priority file contains a rule already present in higher-priority layer; deduped vendor files are written as *.deduped.list",
};

await mkdir(join(root, "reports"), { recursive: true });
await writeFile(outPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ counts: report.counts, report: outPath }, null, 2));
if (total > 0) console.warn(`WARN ${total} shadowed rules found; see ${outPath}`);
