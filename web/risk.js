/* Published Reynolds Risk Score equations. Runs locally; no network calls. */
(function (root) {
  "use strict";
  function positive(name, value) {
    if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
      throw new Error(name + " must be a finite number greater than zero");
    }
    return value;
  }
  function calculate(input) {
    const sex = input.sex;
    if (sex !== "female" && sex !== "male") throw new Error("Choose female or male");
    const age = positive("Age", input.age);
    const minAge = sex === "female" ? 45 : 50;
    if (age < minAge || age >= 80) throw new Error("Age must be from " + minAge + " to under 80 years for this model");
    const bp = positive("Systolic BP", input.systolic_bp);
    const tc = positive("Total cholesterol", input.total_cholesterol);
    const hdl = positive("HDL cholesterol", input.hdl_cholesterol);
    const crp = positive("hsCRP", input.hs_crp);
    for (const name of ["smoker", "parental_mi_before_60", "diabetes"]) {
      if (typeof input[name] !== "boolean") throw new Error(name + " must be a boolean");
    }
    let linear, baseline, offset;
    if (sex === "male") {
      if (input.diabetes) throw new Error("Male model is not validated for diabetes");
      if (input.hba1c != null) throw new Error("HbA1c is only used for diabetic women");
      linear = 4.385 * Math.log(age) + 2.607 * Math.log(bp) +
        0.963 * Math.log(tc) - 0.772 * Math.log(hdl) +
        0.405 * Number(input.smoker) + 0.102 * Math.log(crp) +
        0.541 * Number(input.parental_mi_before_60);
      baseline = 0.8990;
      offset = 33.097;
    } else {
      if (input.diabetes) positive("HbA1c", input.hba1c);
      if (!input.diabetes && input.hba1c != null) throw new Error("HbA1c is only used with diabetes");
      linear = 0.0799 * age + 3.137 * Math.log(bp) +
        0.180 * Math.log(crp) + 1.382 * Math.log(tc) -
        1.172 * Math.log(hdl) + (input.diabetes ? 0.134 * input.hba1c : 0) +
        0.818 * Number(input.smoker) + 0.438 * Number(input.parental_mi_before_60);
      baseline = 0.98634;
      offset = 22.325;
    }
    const pct = -100 * Math.expm1(Math.log(baseline) * Math.exp(Math.min(linear - offset, 700)));
    return Math.round(Math.min(100, Math.max(0, pct)) * 100) / 100;
  }
  root.ReynoldsRisk = { calculate };
  if (typeof module !== "undefined" && module.exports) module.exports = { calculate };
})(typeof globalThis !== "undefined" ? globalThis : this);
