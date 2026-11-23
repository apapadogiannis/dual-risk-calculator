// Runs the calculations inside site/index.html on the cases of tests/vectors.json
// and compares every number with the Python result (relative tolerance 1e-9).
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
const html = readFileSync(new URL("../site/index.html", import.meta.url), "utf8");
const m = html.match(/<script id="core">([\s\S]*?)<\/script>/);
if (!m) throw new Error("core script not found in the page");
const ctx = { module: { exports: {} } }; vm.runInNewContext(m[1], ctx);
const DR = ctx.module.exports;
const cases = JSON.parse(readFileSync(new URL("./vectors.json", import.meta.url), "utf8"));
let n = 0, worst = 0;
const cmp = (a, b, path) => {
  if (b === null) { if (a !== null && a !== undefined) throw new Error(`${path}: expected null, got ${a}`); return; }
  if (typeof b === "number") { n++; const e = Math.abs(a - b) / Math.max(1e-12, Math.abs(b)); worst = Math.max(worst, e);
    if (!(e < 1e-9 || Math.abs(a - b) < 1e-12)) throw new Error(`${path}: page ${a}, python ${b}`); return; }
  if (Array.isArray(b)) { if (a.length !== b.length) throw new Error(`${path}: length ${a.length} vs ${b.length}`); b.forEach((x, i) => cmp(a[i], x, `${path}[${i}]`)); return; }
  if (typeof b === "object") { for (const k of Object.keys(b)) cmp(a[k], b[k], `${path}.${k}`); return; }
};
cases.forEach((c, i) => cmp(DR[c.fn](...c.args), c.result, `case ${i} ${c.fn}`));
console.log(`page agrees with python on ${n} numbers in ${cases.length} cases; largest relative difference ${worst.toExponential(1)}`);
