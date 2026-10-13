const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { calculate } = require("./risk.js");

const vectors = [
  [{ sex: "female", age: 55, systolic_bp: 125, total_cholesterol: 208,
     hdl_cholesterol: 52, hs_crp: 2, smoker: false, parental_mi_before_60: false,
     diabetes: false, hba1c: null }, 1.49],
  [{ sex: "female", age: 65, systolic_bp: 150, total_cholesterol: 240,
     hdl_cholesterol: 42, hs_crp: 4, smoker: true, parental_mi_before_60: true,
     diabetes: true, hba1c: 8.2 }, 66.83],
  [{ sex: "male", age: 60, systolic_bp: 130, total_cholesterol: 205,
     hdl_cholesterol: 48, hs_crp: 2, smoker: false, parental_mi_before_60: false,
     diabetes: false, hba1c: null }, 7.99],
  [{ sex: "male", age: 70, systolic_bp: 160, total_cholesterol: 245,
     hdl_cholesterol: 35, hs_crp: 6, smoker: true, parental_mi_before_60: true,
     diabetes: false, hba1c: null }, 70.72],
];

test("Reynolds equations: published reference vectors", () => {
  for (const [inputs, expected] of vectors) assert.equal(calculate(inputs), expected);
});

test("reject invalid numerical values and inapplicable populations", () => {
  const base = vectors[0][0];
  for (const change of [
    { age: 42 }, { sex: "other" }, { systolic_bp: 0 },
    { hs_crp: Number.POSITIVE_INFINITY }, { hdl_cholesterol: -4 },
    { diabetes: true }, { hba1c: 7 }, { smoker: 1 }
  ]) {
    assert.throws(() => calculate({ ...base, ...change }));
  }
  assert.throws(() => calculate({ ...vectors[2][0], diabetes: true }));
});

test("browser page uses local scripts and has key accessible elements", () => {
  const html = fs.readFileSync(__dirname + "/index.html", "utf8");
  assert.match(html, /id="risk-form"/);
  assert.match(html, /id="result"/);
  assert.match(html, /src="risk.js"/);
  assert.match(html, /src="app.js"/);
  assert.doesNotMatch(html, /fetch\(/);
});
