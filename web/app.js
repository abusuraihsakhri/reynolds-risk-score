/* Presentation only. The risk model is defined in risk.js and runs offline. */
(function () {
  "use strict";
  const byId = id => document.getElementById(id);
  const form = byId("risk-form");
  const sex = byId("sex");
  const diabetes = byId("diabetes");
  const hba1cField = byId("hba1c-field");
  const hba1c = byId("hba1c");
  const error = byId("error");
  const result = byId("result");

  function updateApplicability() {
    const male = sex.value === "male";
    byId("age").min = male ? "50" : "45";
    byId("age-range").textContent = male ? "Men: 50 to under 80; without diabetes" : "Women: 45 to under 80";
    diabetes.disabled = male;
    if (male) diabetes.checked = false;
    hba1cField.hidden = male || !diabetes.checked;
    hba1c.required = !hba1cField.hidden;
    if (hba1cField.hidden) hba1c.value = "";
    result.hidden = true;
    byId("prompt").hidden = false;
    error.hidden = true;
  }
  sex.addEventListener("change", updateApplicability);
  diabetes.addEventListener("change", updateApplicability);

  function numberFrom(id) {
    const el = byId(id);
    if (el.value.trim() === "") throw new Error("Complete the " + el.labels[0].textContent + " field");
    const number = Number(el.value);
    if (!Number.isFinite(number)) throw new Error(el.labels[0].textContent + " must be a finite number");
    return number;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    error.hidden = true;
    result.hidden = true;
    byId("prompt").hidden = false;
    try {
      const data = {
        sex: sex.value,
        age: numberFrom("age"),
        systolic_bp: numberFrom("systolic_bp"),
        total_cholesterol: numberFrom("total_cholesterol"),
        hdl_cholesterol: numberFrom("hdl_cholesterol"),
        hs_crp: numberFrom("hs_crp"),
        smoker: byId("smoker").checked,
        parental_mi_before_60: byId("parental_mi_before_60").checked,
        diabetes: diabetes.checked && !diabetes.disabled,
        hba1c: hba1cField.hidden ? null : numberFrom("hba1c")
      };
      const risk = window.ReynoldsRisk.calculate(data);
      byId("risk-value").textContent = risk.toFixed(2) + "%";
      result.hidden = false;
      byId("prompt").hidden = true;
    } catch (err) {
      error.textContent = err.message || "Unable to calculate risk";
      error.hidden = false;
    }
  });
  updateApplicability();
})();
