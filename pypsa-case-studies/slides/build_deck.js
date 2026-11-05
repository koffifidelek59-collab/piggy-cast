// Executive briefing deck: Power-system case studies with PyPSA (Niamey / Agadez context)
// Build:  node build_deck.js   (writes PyPSA_Case_Studies_Briefing.pptx next to this file)
// Numbers come from ../results/tables/*_summary.json (produced by the case-study notebooks).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
// apply_theme.js writes the theme colours into the .pptx (pptxgenjs cannot). It ships with
// the PowerPoint tooling used to build this deck; without it the deck is still valid but
// scheme colours fall back to the default Office palette.
let applyTheme = async () => console.warn("apply_theme.js not found: default Office colours kept");
for (const p of [process.env.PPTX_SKILL_DIR && path.join(process.env.PPTX_SKILL_DIR, "scripts/apply_theme.js"),
                 path.join(__dirname, "apply_theme.js")].filter(Boolean)) {
  if (fs.existsSync(p)) { applyTheme = require(p).applyTheme; break; }
}

const T = (n) => JSON.parse(fs.readFileSync(path.join(__dirname, "../results/tables", `${n}_summary.json`)));
const S3 = T("cs03"), S4 = T("cs04"), S5 = T("cs05"), S6 = T("cs06"), S7 = T("cs07"), S8 = T("cs08");

// ------------------------------------------------------------------ theme
const THEME = {
  name: "Sahel Grid",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2433", lt1: "FFFFFF", dk2: "14213D", lt2: "EEF2F6",
    accent1: "E59E1B",   // solar gold
    accent2: "1F8A70",   // storage teal
    accent3: "2A78D6",   // grid blue
    accent4: "C0392B",   // violation red
    accent5: "6B7A90",   // slate
    accent6: "E8743B",   // thermal orange
    hlink: "2A78D6", folHlink: "6B7A90",
  },
};
const HEX = THEME.colors;
const MUTED = "6B7A90", GRID = "D9DEE5";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                 // 13.333 x 7.5 in
pres.author = "KOUAME Koffi Fidele";
pres.title = "Power system case studies with PyPSA - executive briefing";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const W = 13.333, M = 0.6;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.0, w: 11.4, h: 1.9,
        fontSize: 40, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.1, w: 11.0, h: 1.0,
        fontSize: 20, color: C.background2, valign: "top", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "byline", type: "body", x: M, y: 6.2, w: 8, h: 0.6,
        fontSize: 14, color: C.accent1, margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: W - 2 * M, h: 0.85,
        fontSize: 32, bold: true, color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "PyPSA case studies | real weather 2023 (NASA POWER), IEEE data (MATPOWER, PGLib) | grid parameters of the Niger cases are fictitious",
        options: { x: M, y: 7.0, w: 10.6, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.55, h: 0.3, fontSize: 10, color: C.accent5, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSING_DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 1.0, w: 12.1, h: 1.0,
        fontSize: 36, bold: true, color: C.background1, align: "left", margin: 0 }, text: "" } },
  ],
});

// ------------------------------------------------------------------ helpers
const ICON_CACHE = {};
async function icon(name, color = "FFFFFF") {
  const key = name + color;
  if (!ICON_CACHE[key]) {
    const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color: "#" + color, size: 256 }));
    const buf = await sharp(Buffer.from(svg)).png().toBuffer();
    ICON_CACHE[key] = "image/png;base64," + buf.toString("base64");
  }
  return ICON_CACHE[key];
}
async function iconCircle(slide, name, x, y, d, fill, id) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 },
    objectName: `${id}-circle` });
  const p = d * 0.26;
  slide.addImage({ data: await icon(name), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, objectName: `${id}-icon` });
}
function card(slide, x, y, w, h, id, fill = C.background2) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill },
    line: { color: fill, width: 0 }, objectName: id });
}
function txt(slide, text, o) {
  slide.addText(text, { isTextBox: true, margin: 0, valign: "top", color: C.text1, fontSize: 14, ...o });
}
function chartBase(extra = {}) {   // a fresh options object for every chart (pptxgenjs mutates them)
  return {
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    valGridLine: { color: GRID, size: 0.5 }, catGridLine: { style: "none" },
    catAxisLineShow: true, valAxisLineShow: false,
    showTitle: true, titleFontSize: 14, titleColor: HEX.dk2, titleFontFace: "+mn-lt",
    dataLabelColor: HEX.dk1, dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt",
    showLegend: false, ...extra,
  };
}
const pct = (v) => `${Math.round(v)} %`;
const sc = S7.scenarios, sD = sc["D no imports, optimal PV+battery"], sB = sc["B no imports, no PV"];
const ag = S8.base, agD = ag["diesel only"], agH = ag["optimal hybrid"];

(async () => {
  // ================================================================ 1 title
  pres.addSection({ title: "Message" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Message" });
  s.addText("Keeping the lights on in the Sahel: what grid studies tell decision-makers", { placeholder: "title" });
  s.addText("Nine power-system case studies with PyPSA, from load-flow basics to solar and storage plans for Niamey and the Agadez region, on real 2023 weather data", { placeholder: "body" });
  s.addText("KOUAME Koffi Fidèle  |  IMP-EGH, System Analysis", { placeholder: "byline" });
  await iconCircle(s, "FaSolarPanel", 11.1, 0.7, 1.5, C.accent1, "title");
  s.addNotes("Purpose: show what grid simulations tell us about keeping electricity reliable and affordable in Niger as solar grows. All numbers come from executed PyPSA models. Grid parameters of the Niger cases are educational, weather data are real (NASA POWER 2023).");

  // ================================================================ 2 summary
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Message" });
  s.addText("Three numbers that matter for decisions", { placeholder: "title" });
  const stats = [
    { big: `-${Math.round(100 * (1 - sD["total cost (M$/yr)"] / sB["total cost (M$/yr)"]))} %`, col: C.accent2, ic: "FaChargingStation",
      head: "Niamey: yearly cost of supply", body: `when imports stop, with ${Math.round(sD["PV (MW)"])} MW of solar and a ${Math.round(sD["battery (MWh)"])} MWh battery, compared with thermal generation only` },
    { big: `-${Math.round(100 * (1 - agH["diesel (1000 litres)"] / agD["diesel (1000 litres)"]))} %`, col: C.accent1, ic: "FaGasPump",
      head: "Agadez mini-grid: diesel burnt", body: `electricity cost falls from ${agD["LCOE ($/kWh)"].toFixed(2)} to ${agH["LCOE ($/kWh)"].toFixed(2)} $/kWh with solar and storage` },
    { big: `x${Math.round(S6.hosting_capacity["PF 0.95 absorbing, set points -0.03"][0] / S6.hosting_capacity["unity PF, original set points"][0])}`, col: C.accent3, ic: "FaNetworkWired",
      head: "Solar a weak grid node can accept", body: `from ${S6.hosting_capacity["unity PF, original set points"][0]} to ${S6.hosting_capacity["PF 0.95 absorbing, set points -0.03"][0]} MW by changing voltage settings and inverter controls: almost free` },
  ];
  for (let i = 0; i < 3; i++) {
    const x = M + i * 4.1, st = stats[i];
    card(s, x, 1.55, 3.8, 3.85, `stat-card-${i}`);
    await iconCircle(s, st.ic, x + 0.3, 1.85, 0.75, st.col, `stat-${i}`);
    txt(s, st.big, { x: x + 0.3, y: 2.8, w: 3.3, h: 1.1, fontSize: 60, bold: true, color: st.col, fontFace: THEME.headFontFace, valign: "middle" });
    txt(s, st.head, { x: x + 0.3, y: 4.0, w: 3.3, h: 0.45, fontSize: 16, bold: true });
    txt(s, st.body, { x: x + 0.3, y: 4.5, w: 3.3, h: 1.4, fontSize: 14, color: C.accent5 });
  }
  txt(s, "Cheap operational fixes come first; storage is what lets the grid absorb cheap solar; every linear plan must be checked with a full AC load flow.",
    { x: M, y: 5.75, w: 12.1, h: 0.6, fontSize: 18, italic: true, color: C.text2 });
  s.addNotes("Main message up front. 1) In the Niamey area, if imports are interrupted, solar plus a 4-hour battery cuts the yearly cost of supply by about a fifth and fuel by two thirds. 2) For an isolated town in the north, a hybrid mini-grid cuts diesel by 94 percent and halves the cost per kWh. 3) At a weak node, the amount of solar the grid can host is multiplied by about forty with settings that cost almost nothing.");

  // ================================================================ 3 nine problems
  pres.addSection({ title: "Approach" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Approach" });
  s.addText("Nine problems engineers face, one per case study", { placeholder: "title" });
  const probs = [
    ["FaCalculator", "Solving the equations", "How simulators find the grid state", C.accent5],
    ["FaProjectDiagram", "Load flow of a meshed grid", "Voltages, flows, losses (Exercise 5)", C.accent5],
    ["FaBolt", "Power sharing", "Thermal plant versus solar plant", C.accent3],
    ["FaIndustry", "Undervoltage", "A remote industrial zone at 0.92 p.u.", C.accent3],
    ["FaExclamationTriangle", "Congestion and N-1", "Line overload after an outage", C.accent3],
    ["FaTachometerAlt", "Demand growth", "When the reactive reserve runs out", C.accent3],
    ["FaSun", "Solar at a weak node", "Voltage rise and reverse power flow", C.accent3],
    ["FaCity", "Real case: Niamey", "Solar and storage, every hour of 2023", C.accent2],
    ["FaGlobeAfrica", "Real case: Agadez", "Sizing an off-grid mini-grid", C.accent2],
  ];
  for (let i = 0; i < 9; i++) {
    const col = i % 3, row = Math.floor(i / 3), x = M + col * 4.1, y = 1.5 + row * 1.75;
    card(s, x, y, 3.8, 1.5, `prob-card-${i}`);
    await iconCircle(s, probs[i][0], x + 0.25, y + 0.35, 0.8, probs[i][3], `prob-${i}`);
    txt(s, `${i}. ${probs[i][1]}`.replace(/^(\d)\./, "CS0$1"), { x: x + 1.25, y: y + 0.28, w: 2.4, h: 0.45, fontSize: 14, bold: true });
    txt(s, probs[i][2], { x: x + 1.25, y: y + 0.75, w: 2.4, h: 0.6, fontSize: 12, color: C.accent5 });
  }
  s.addNotes("The work is organised by type of problem, not by network size. Grey: numerical foundations. Blue: grid problems with their remedies. Teal: two planning cases on real hourly weather for Niger.");

  // ================================================================ 4 method
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Approach" });
  s.addText("One method, from data to a verified recommendation", { placeholder: "title" });
  const steps = [
    ["FaDatabase", "Real data", "IEEE test grids (MATPOWER, PGLib); NASA POWER hourly weather 2023"],
    ["FaLayerGroup", "PyPSA model", "Buses, lines, generators, loads and their hourly time series"],
    ["FaCogs", "Solve", "AC load flow, optimal and security-constrained power flow, investment optimisation"],
    ["FaSearch", "Verify", "Own Newton-Raphson solver; full AC check of every linear plan"],
    ["FaLightbulb", "Recommend", "The cheapest fix that removes the violation"],
  ];
  for (let i = 0; i < 5; i++) {
    const x = M + i * 2.48;
    card(s, x, 1.6, 2.2, 3.2, `step-card-${i}`);
    await iconCircle(s, steps[i][0], x + 0.7, 1.85, 0.8, i === 4 ? C.accent1 : C.accent3, `step-${i}`);
    txt(s, steps[i][1], { x: x + 0.2, y: 2.85, w: 1.8, h: 0.45, fontSize: 16, bold: true, align: "center" });
    txt(s, steps[i][2], { x: x + 0.2, y: 3.35, w: 1.8, h: 1.35, fontSize: 12, color: C.accent5, align: "center" });
    if (i < 4) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.24, y: 3.0, w: 0.2, h: 0.35, fill: { color: C.accent5 }, line: { color: C.accent5, width: 0 }, objectName: `arrow-${i}` });
  }
  card(s, M, 5.15, 12.1, 1.4, "validation-card", C.background2);
  await iconCircle(s, "FaCheckCircle", M + 0.3, 5.42, 0.85, C.accent2, "validation");
  txt(s, "Trust in the numbers", { x: M + 1.4, y: 5.35, w: 10.4, h: 0.4, fontSize: 16, bold: true });
  txt(s, "PyPSA agrees with our own Newton-Raphson solver to 15 decimal places and reproduces the published IEEE solutions (9-bus: 71.64 MW at the slack, 4.641 MW of losses; 14-bus: 13.393 MW of losses).",
    { x: M + 1.4, y: 5.78, w: 10.4, h: 0.7, fontSize: 14, color: C.accent5 });
  s.addNotes("Every case follows the same chain. The verification step matters: unit errors are the most common mistake in grid studies, and linear optimisation tools ignore voltage, so every plan is re-checked with the full AC load flow.");

  // ================================================================ 5 undervoltage
  pres.addSection({ title: "Grid problems" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Grid problems" });
  s.addText("A remote industrial zone: fix the voltage locally", { placeholder: "title" });
  card(s, M, 1.5, 3.9, 5.2, "uv-card");
  await iconCircle(s, "FaIndustry", M + 0.3, 1.8, 0.75, C.accent4, "uv");
  txt(s, S3.V5_B.toFixed(3) + " p.u.", { x: M + 0.3, y: 2.75, w: 3.4, h: 0.9, fontSize: 44, bold: true, color: C.accent4, fontFace: THEME.headFontFace, valign: "middle" });
  txt(s, `voltage at the evening peak (limit 0.95), below the limit ${S3.hours_below_without} hours out of 24`, { x: M + 0.3, y: 3.7, w: 3.4, h: 0.9, fontSize: 14, color: C.accent5 });
  txt(s, "Recommendation", { x: M + 0.3, y: 4.75, w: 3.4, h: 0.4, fontSize: 16, bold: true });
  txt(s, `15 MVAr switched capacitor bank (3 x 5 MVAr) at the industrial substation: ${S3.remedies["capacitor 15 MVAr at bus 5"].toFixed(3)} p.u., losses -${Math.round(100 * (1 - S3.losses["capacitor 15 MVAr at bus 5"] / S3.losses["none"]))} %.`,
    { x: M + 0.3, y: 5.15, w: 3.4, h: 1.3, fontSize: 14 });
  const base = S3.remedies["none"];
  const rem = [["Capacitor bank", "capacitor 15 MVAr at bus 5"], ["SVC / STATCOM", "SVC/STATCOM at bus 5 (0.97 p.u.)"],
               ["Second circuit", "second circuit on line 4-5"], ["Plant set point", "plant set point 1.05 p.u."],
               ["Solar inverters", "PV inverters Q-at-night, 1.03 p.u."]];
  s.addChart(pres.charts.BAR, [{ name: "voltage gain", labels: rem.map((r) => r[0]),
      values: rem.map((r) => +(100 * (S3.remedies[r[1]] - base)).toFixed(1)) }],
    { x: 4.85, y: 1.5, w: 7.9, h: 4.45, barDir: "bar", ...chartBase({
      title: `Voltage gain at the remote bus (points of %); ${(100 * (0.95 - base)).toFixed(1)} needed`,
      chartColors: [HEX.accent2, HEX.accent3, HEX.accent3, HEX.accent3, HEX.accent4],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisMaxVal: 6,
      catAxisOrientation: "maxMin" }) });
  txt(s, "Solar inverters are too far away: they would need 68 MVAr, more than their 44 MVA rating, and still fail.",
    { x: 4.95, y: 6.1, w: 7.7, h: 0.6, fontSize: 14, color: C.accent5 });
  s.addNotes("The industrial zone sits at the end of an 85 km line and its load is strongly reactive. On such a line reactive power costs three times more voltage than active power. The solar plant does not help: it is far away and the peak occurs after sunset. A capacitor bank produces reactive power where it is consumed: cheapest option, and it also cuts losses.");

  // ================================================================ 6 congestion
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Grid problems" });
  s.addText("Hot-season N-1: a cheap dispatch can be unsafe", { placeholder: "title" });
  const cols = [
    { head: "Market dispatch", col: C.accent4, ic: "FaExclamationTriangle", rows: [
      [`${Math.round(S4.n1_worst_ed)} %`, "loading of line 5-6 if line 8-9 trips"],
      [`${Math.round(S4.cost_ed).toLocaleString("en-US")} $/h`, "generation cost"],
      [`${S4.lmp_ed[0].toFixed(1)} $/MWh`, "same price at every bus"]] },
    { head: "Security-constrained dispatch", col: C.accent2, ic: "FaCheckCircle", rows: [
      ["99 %", "loading of line 5-6 if line 8-9 trips"],
      [`+${Math.round(S4.security_cost_per_h)} $/h`, `extra cost (${(100 * S4.security_cost_per_h / S4.cost_ed).toFixed(1)} %)`],
      [`${S4.lmp_sc[0].toFixed(1)}-${S4.lmp_sc[1].toFixed(1)}`, "$/MWh: prices now differ by bus"]] },
  ];
  for (let i = 0; i < 2; i++) {
    const x = M + i * 4.3, c = cols[i];
    card(s, x, 1.5, 4.0, 4.0, `n1-card-${i}`);
    await iconCircle(s, c.ic, x + 0.3, 1.75, 0.65, c.col, `n1-${i}`);
    txt(s, c.head, { x: x + 1.1, y: 1.8, w: 2.8, h: 0.55, fontSize: 18, bold: true, valign: "middle" });
    c.rows.forEach((r, j) => {
      txt(s, r[0], { x: x + 0.3, y: 2.65 + j * 0.92, w: 3.5, h: 0.5, fontSize: 26, bold: true, color: c.col, fontFace: THEME.headFontFace });
      txt(s, r[1], { x: x + 0.3, y: 3.12 + j * 0.92, w: 3.5, h: 0.35, fontSize: 12, color: C.accent5 });
    });
  }
  card(s, 9.2, 1.5, 3.53, 4.0, "hidden-card", "FBEAE8");
  await iconCircle(s, "FaSearch", 9.5, 1.75, 0.65, C.accent4, "hidden");
  txt(s, "Hidden risk", { x: 10.3, y: 1.8, w: 2.3, h: 0.55, fontSize: 18, bold: true, valign: "middle" });
  txt(s, `Losing line 9-4 drops one substation to ${S4.v9_after_L94.toFixed(2)} p.u.: a voltage collapse that linear tools cannot see. About ${Math.round(S4.q_cap9)} MVAr of switched reactive support is needed.`,
    { x: 9.5, y: 2.6, w: 2.95, h: 2.7, fontSize: 14 });
  txt(s, `Preventive redispatch costs about ${Math.round(S4["yearly_redispatch_k$"])} k$ a year (600 critical hours): far cheaper than a new line while congestion stays rare. The price spread tells planners when to reinforce.`,
    { x: M, y: 5.8, w: 12.1, h: 0.9, fontSize: 16, color: C.text2 });
  s.addNotes("IEEE 9-bus system with hot-season ratings 15 percent lower and an evening peak 15 percent higher. The cheapest dispatch is fine with all lines in service, but the loss of one line overloads another by 13 percent. Moving 18 MW between plants removes the risk for less than one percent of the cost. The full AC check revealed a second problem, a voltage collapse after another outage, which needs reactive support.");

  // ================================================================ 7 demand growth
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Grid problems" });
  s.addText("Demand growth: the reactive reserve runs out first", { placeholder: "title" });
  const labs = ["100 %", "110 %", "120 %", "130 %", "140 %", "150 %"];
  const t5 = Object.values(S5.table);
  s.addChart(pres.charts.LINE, [{ name: "lowest voltage", labels: labs, values: t5.map((r) => +r["min |V| (p.u.)"].toFixed(3)) }],
    { x: M, y: 1.45, w: 6.0, h: 4.3, ...chartBase({ title: "Lowest bus voltage (p.u.) as demand grows", chartColors: [HEX.accent3],
      lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 8, valAxisMinVal: 0.88, valAxisMaxVal: 1.02,
      valAxisLabelFormatCode: "0.00", showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "0.000" }) });
  s.addChart(pres.charts.BAR, [{ name: "units at limit", labels: labs, values: t5.map((r) => r["gens at Q limit"]) }],
    { x: 6.8, y: 1.45, w: 5.9, h: 4.3, barDir: "col", ...chartBase({ title: "Voltage-control units at their reactive limit (of 4)",
      chartColors: [HEX.accent4], valAxisMinVal: 0, valAxisMaxVal: 4, valAxisMajorUnit: 1, showValue: true, dataLabelPosition: "outEnd", barGapWidthPct: 60 }) });
  txt(s, [
    { text: `At +30 % the voltages still look fine, but all four voltage-control units are at their limit. Maximum loadability: +${Math.round(100 * (S5.lambda_max - 1))} %. `, options: {} },
    { text: `Ignoring reactive limits would wrongly suggest more than +${Math.round(100 * (S5.lambda_nolim - 1))} %.`, options: { bold: true } }],
    { x: M, y: 5.95, w: 12.1, h: 0.8, fontSize: 16, color: C.text2 });
  s.addNotes("IEEE 14-bus system, all loads growing. Classic indicators stay green up to +30 percent, yet the machines that hold voltage are already at their reactive limits; one more step and nine buses fall below 0.95 p.u. Monitor reactive reserve, not only voltage. Default simulator settings that ignore these limits give a dangerously optimistic answer.");

  // ================================================================ 8 solar weak node
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Grid problems" });
  s.addText("Solar at a weak node: voltage, not lines, is the limit", { placeholder: "title" });
  const hc = S6.hosting_capacity;
  s.addChart(pres.charts.BAR, [{ name: "hosting capacity", labels: ["Original settings", "Voltage set points -3 %", "+ inverters absorb Q (PF 0.95)"],
      values: [hc["unity PF, original set points"][0], hc["unity PF, set points -0.03"][0], hc["PF 0.95 absorbing, set points -0.03"][0]] }],
    { x: M, y: 1.45, w: 6.3, h: 4.6, barDir: "col", ...chartBase({ title: "Solar the weak node can host at noon (MW)",
      chartColors: [HEX.accent5, HEX.accent3, HEX.accent2], valAxisMinVal: 0, showValue: true, dataLabelPosition: "outEnd",
      barGapWidthPct: 55, catAxisLabelFontSize: 11 }) });
  const sc6 = S6.scenarios;
  const rows6 = [
    ["FaArrowsAltH", C.accent3, "Reverse power flow", `Above about ${Math.round(S6.load14_noon)} MW of solar the node exports: up to ${Math.round(sc6["S2 PV 100 MW"]["max export from bus 14 (MW)"])} MW with a 100 MW plant.`],
    ["FaBatteryFull", C.accent2, "Battery helps, with care", `Peak voltage ${sc6["S2 PV 100 MW"]["max V14 (p.u.)"].toFixed(3)} to ${sc6["S3 PV 100 + battery"]["max V14 (p.u.)"].toFixed(3)} p.u., export ${Math.round(sc6["S2 PV 100 MW"]["max export from bus 14 (MW)"])} to ${Math.round(sc6["S3 PV 100 + battery"]["max export from bus 14 (MW)"])} MW, but evening discharge at the weak node raises voltage.`],
    ["FaCheckCircle", C.accent1, "Full package works", `Battery + reactive control + lower set points: no overvoltage hour (max ${sc6["S4 S3 + PF 0.95 + set points"]["max V14 (p.u.)"].toFixed(3)} p.u.).`],
  ];
  for (let i = 0; i < 3; i++) {
    const y = 1.55 + i * 1.55;
    await iconCircle(s, rows6[i][0], 7.25, y, 0.7, rows6[i][1], `hc-${i}`);
    txt(s, rows6[i][2], { x: 8.15, y: y - 0.02, w: 4.6, h: 0.4, fontSize: 16, bold: true });
    txt(s, rows6[i][3], { x: 8.15, y: y + 0.4, w: 4.6, h: 1.0, fontSize: 14, color: C.accent5 });
  }
  txt(s, "Review the voltage plan and require reactive capability before connecting solar.", { x: M, y: 6.25, w: 12.1, h: 0.5, fontSize: 16, italic: true, color: C.text2 });
  s.addNotes("A solar plant at the weakest node of the IEEE 14-bus system, with the real solar profile of a clear day in Niamey. Line capacity is not the issue; voltage rise is. Lowering generator voltage set points and asking inverters to absorb reactive power raise the hosting capacity from 3 to 129 MW. Storage reduces exports but must be dispatched with voltage in mind.");

  // ================================================================ 9 Niamey cost
  pres.addSection({ title: "Real cases" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Real cases" });
  s.addText("Niamey 2023: what each option costs per MWh", { placeholder: "title" });
  card(s, M, 1.5, 3.9, 5.2, "niamey-context");
  await iconCircle(s, "FaCity", M + 0.3, 1.8, 0.75, C.accent3, "niamey");
  txt(s, "The question", { x: M + 0.3, y: 2.75, w: 3.4, h: 0.4, fontSize: 16, bold: true });
  txt(s, "How much solar and storage minimise the cost of supply if imports stop, as in 2023?", { x: M + 0.3, y: 3.15, w: 3.4, h: 0.9, fontSize: 14 });
  txt(s, "The data", { x: M + 0.3, y: 4.2, w: 3.4, h: 0.4, fontSize: 16, bold: true });
  txt(s, [
    { text: `Every hour of 2023, real weather: solar yield ${Math.round(S7.yield_kwh_kwp).toLocaleString("en-US")} kWh/kWp`, options: { bullet: true, breakLine: true } },
    { text: `Demand ${Math.round(S7.demand_gwh)} GWh, peak ${Math.round(S7.peak_mw)} MW (modelled)`, options: { bullet: true, breakLine: true } },
    { text: "Fuel 180 $/MWh, imports 70 $/MWh", options: { bullet: true } }],
    { x: M + 0.3, y: 4.6, w: 3.45, h: 1.9, fontSize: 14, color: C.accent5, paraSpaceAfter: 4 });
  const order7 = [["A imports, no PV", "A: imports"], ["B no imports, no PV", "B: islanded"], ["C no imports, 100 MW PV", "C: +100 MW PV"],
                  ["D0 no imports, optimal PV, no battery", "D0: best PV"], ["D no imports, optimal PV+battery", "D: PV+storage"],
                  ["E imports, optimal PV+battery", "E: imports+PV"]];
  s.addChart(pres.charts.BAR, [{ name: "$/MWh", labels: order7.map((o) => o[1]), values: order7.map((o) => Math.round(sc[o[0]]["average cost ($/MWh)"])) }],
    { x: 4.85, y: 1.5, w: 7.9, h: 4.6, barDir: "col", ...chartBase({ title: "Average cost of supply ($/MWh)",
      chartColors: [HEX.accent5, HEX.accent6, HEX.accent1, HEX.accent1, HEX.accent2, HEX.accent3],
      valAxisMinVal: 0, showValue: true, dataLabelPosition: "outEnd", barGapWidthPct: 45, catAxisLabelFontSize: 11 }) });
  txt(s, "Islanded, the city pays 180 $/MWh; solar + storage brings it to 140. With imports, adding solar still saves 13 %.",
    { x: 4.95, y: 6.2, w: 7.7, h: 0.55, fontSize: 14, color: C.text2 });
  s.addNotes("Real hourly weather for Niamey in 2023 from NASA POWER, converted to solar output with the same physics as Renewables.ninja. Demand is modelled from temperature. When imports stop, thermal fuel at 180 dollars per MWh sets the cost; the optimal solar and storage portfolio brings it down to 140. Even with imports, about 145 MW of solar lowers the cost from 78 to 68 dollars per MWh.");

  // ================================================================ 10 Niamey results
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Real cases" });
  s.addText("Storage, not the grid, is what unlocks solar", { placeholder: "title" });
  const big10 = [
    [`${Math.round(sD["PV (MW)"])} MW`, `of solar with a ${Math.round(sD["battery (MW)"])} MW / ${Math.round(sD["battery (MWh)"])} MWh battery`, C.accent1],
    [pct(sD["solar share (%)"]), "of the yearly demand supplied by the sun", C.accent2],
    [`-${Math.round(100 * (1 - sD["thermal (GWh)"] / sB["thermal (GWh)"]))} %`, "fuel burnt compared with thermal only", C.accent6],
  ];
  big10.forEach((b, i) => {
    card(s, M, 1.5 + i * 1.6, 4.6, 1.4, `big10-${i}`);
    txt(s, b[0], { x: M + 0.3, y: 1.6 + i * 1.6, w: 4.1, h: 0.7, fontSize: 34, bold: true, color: b[2], fontFace: THEME.headFontFace, valign: "middle" });
    txt(s, b[1], { x: M + 0.3, y: 2.3 + i * 1.6, w: 4.1, h: 0.5, fontSize: 14, color: C.accent5 });
  });
  s.addChart(pres.charts.BAR, [{ name: "kt CO2", labels: order7.map((o) => o[1]), values: order7.map((o) => Math.round(sc[o[0]]["CO2 (kt)"])) }],
    { x: 5.55, y: 1.5, w: 7.2, h: 3.9, barDir: "col", ...chartBase({ title: "CO2 emissions of the thermal plant (kt per year)",
      chartColors: [HEX.accent5], valAxisMinVal: 0, showValue: true, dataLabelPosition: "outEnd", barGapWidthPct: 45, catAxisLabelFontSize: 11 }) });
  txt(s, [
    { text: "Without storage, solar stops at about 150 MW: ", options: { bold: true } },
    { text: `at midday the city cannot absorb more (20 % would be curtailed). Lines never exceed ${Math.round(sD["max line loading (%)"])} % of their rating. The thermal plant stays for monsoon weeks.`, options: {} }],
    { x: 5.65, y: 5.55, w: 7.1, h: 1.2, fontSize: 14, color: C.text2 });
  s.addNotes("The optimiser builds solar until the next megawatt is useless. Without storage that happens at about 150 MW because midday demand is limited. With a 4-hour battery the optimum is about 330 MW of solar, 72 percent of the energy, and fuel falls by two thirds. The grid is not the bottleneck: the battery sits at the solar site and smooths the flows. An AC check at the peak hours confirmed voltages and loadings within limits.");

  // ================================================================ 11 Agadez
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Real cases" });
  s.addText("Agadez mini-grid: solar and storage halve the cost", { placeholder: "title" });
  const cmp = [["Diesel only", C.accent6, "FaGasPump", agD], ["Solar + battery + diesel back-up", C.accent2, "FaSolarPanel", agH]];
  for (let i = 0; i < 2; i++) {
    const x = M + i * 3.3, d = cmp[i][3];
    card(s, x, 1.5, 3.05, 5.2, `ag-card-${i}`);
    await iconCircle(s, cmp[i][2], x + 0.3, 1.75, 0.7, cmp[i][1], `ag-${i}`);
    txt(s, cmp[i][0], { x: x + 0.3, y: 2.55, w: 2.5, h: 0.75, fontSize: 16, bold: true });
    [[`${d["LCOE ($/kWh)"].toFixed(2)} $/kWh`, "cost of electricity"],
     [`${(d["diesel (1000 litres)"] / 1000).toFixed(2)} M litres`, "diesel per year"],
     [`${Math.round(d["CO2 (t)"]).toLocaleString("en-US")} t`, "CO2 per year"]].forEach((r, j) => {
      txt(s, r[0], { x: x + 0.3, y: 3.35 + j * 1.07, w: 2.6, h: 0.5, fontSize: 24, bold: true, color: cmp[i][1], fontFace: THEME.headFontFace });
      txt(s, r[1], { x: x + 0.3, y: 3.83 + j * 1.07, w: 2.6, h: 0.35, fontSize: 12, color: C.accent5 });
    });
  }
  const sens = S8.sensitivity;
  s.addChart(pres.charts.LINE, [
      { name: "Diesel only", labels: sens.map((r) => `${r["diesel price ($/l)"].toFixed(1)} $/l`), values: sens.map((r) => +r["LCOE diesel only ($/kWh)"].toFixed(3)) },
      { name: "Optimal hybrid", labels: sens.map((r) => `${r["diesel price ($/l)"].toFixed(1)} $/l`), values: sens.map((r) => +r["LCOE ($/kWh)"].toFixed(3)) }],
    { x: 7.25, y: 1.5, w: 5.5, h: 3.9, ...chartBase({ title: "Cost of electricity ($/kWh) versus diesel price",
      chartColors: [HEX.accent6, HEX.accent2], lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 8,
      valAxisMinVal: 0, valAxisMaxVal: 0.45, valAxisLabelFormatCode: "0.00", showLegend: true, legendPos: "b",
      legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: MUTED }) });
  txt(s, `Optimum: ${(agH["PV (kW)"] / 1000).toFixed(1)} MW of solar and a ${(agH["battery (kWh)"] / 1000).toFixed(0)} MWh battery supply ${Math.round(agH["renewable share (%)"])} % of the energy. The hybrid stays cheaper at every fuel price tested.`,
    { x: 7.35, y: 5.55, w: 5.4, h: 1.2, fontSize: 14, color: C.text2 });
  s.addNotes("An isolated town in the Agadez region, 2 MW peak, supplied only by diesel trucked over long distances. With real 2023 weather, the least-cost system is solar plus a 4-hour battery, keeping the genset as back-up for cloudy monsoon days. The answer does not depend on the diesel price assumption: the dearer the fuel, the more solar and storage the optimiser builds.");

  // ================================================================ 12 recommendations
  pres.addSection({ title: "Decisions" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Decisions" });
  s.addText("Five recommendations", { placeholder: "title" });
  const recs = [
    ["FaBolt", "Fix voltage cheaply first", "Capacitor banks at remote substations; review generator voltage set points."],
    ["FaTachometerAlt", "Watch the reactive reserve", "Alarm when machines near their reactive limits; plan compensation before demand grows 30 %."],
    ["FaExclamationTriangle", "Operate N-1 secure in the hot season", "Hot-season line ratings, preventive redispatch, AC contingency checks."],
    ["FaSun", "Update the grid code for solar", "Reactive capability (PF 0.95, volt-var) and voltage-aware storage dispatch."],
    ["FaChargingStation", "Invest in solar + storage", "Niamey: security when imports stop. Northern towns: hybrid mini-grids halve the cost."],
  ];
  for (let i = 0; i < 5; i++) {
    const col = i < 3 ? 0 : 1, row = i < 3 ? i : i - 3, x = M + col * 6.15, y = 1.5 + row * 1.7;
    card(s, x, y, 5.9, 1.5, `rec-card-${i}`);
    await iconCircle(s, recs[i][0], x + 0.3, y + 0.35, 0.8, i === 4 ? C.accent2 : C.accent3, `rec-${i}`);
    txt(s, `${i + 1}. ${recs[i][1]}`, { x: x + 1.35, y: y + 0.25, w: 4.4, h: 0.45, fontSize: 16, bold: true });
    txt(s, recs[i][2], { x: x + 1.35, y: y + 0.72, w: 4.4, h: 0.7, fontSize: 14, color: C.accent5 });
  }
  card(s, M + 6.15, 1.5 + 2 * 1.7, 5.9, 1.5, "rec-quote", C.text2);
  txt(s, "Cheap fixes first. Storage unlocks solar. Always check the AC grid.",
    { x: M + 6.45, y: 1.5 + 2 * 1.7 + 0.3, w: 5.3, h: 0.9, fontSize: 18, bold: true, italic: true, color: C.background1, valign: "middle" });
  s.addNotes("These recommendations come straight from the case studies: undervoltage, demand growth, N-1 security, solar hosting capacity and the two real planning cases. Most of them are operational and cheap; the investments are the solar and storage portfolios.");

  // ================================================================ 13 next steps
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Decisions" });
  s.addText("Next steps", { placeholder: "title" });
  const next = [
    ["FaDatabase", "Real data", "NIGELEC network and load data; Renewables.ninja multi-year solar profiles"],
    ["FaSearch", "Deeper checks", "N-1 on every hour of the plan, reserves for forecast errors, monsoon years"],
    ["FaCogs", "Feasibility", "Capacitor banks for remote substations; first solar + storage block for Niamey"],
    ["FaMoneyBillWave", "Finance and rules", "Concessional finance for mini-grids; grid-code update for inverters"],
  ];
  s.addShape(pres.shapes.LINE, { x: M + 0.6, y: 2.4, w: 10.9, h: 0, line: { color: C.accent5, width: 1.5 }, objectName: "timeline" });
  for (let i = 0; i < 4; i++) {
    const x = M + i * 3.1;
    await iconCircle(s, next[i][0], x + 0.2, 1.95, 0.9, C.accent3, `next-${i}`);
    txt(s, `${i + 1}. ${next[i][1]}`, { x, y: 3.1, w: 2.8, h: 0.45, fontSize: 16, bold: true });
    txt(s, next[i][2], { x, y: 3.6, w: 2.8, h: 1.6, fontSize: 14, color: C.accent5 });
  }
  card(s, M, 5.0, 12.1, 1.2, "repro-card");
  txt(s, "Everything is reproducible: datasets, executed notebooks and this deck are generated from one code base (PyPSA 1.4, HiGHS, pvlib). Swapping in real data re-runs every case study.",
    { x: M + 0.3, y: 5.2, w: 11.5, h: 0.9, fontSize: 14, color: C.text1 });
  s.addNotes("The models are ready for real data. The highest-value next step is to replace the educational network with real network data and to use several weather years, then to run hourly N-1 checks on the solar and storage plan.");

  // ================================================================ 14 closing
  s = pres.addSlide({ masterName: "CLOSING_DARK", sectionTitle: "Decisions" });
  s.addText("Thank you", { placeholder: "title" });
  txt(s, "Cheap fixes first. Storage unlocks solar. Always check the AC grid.", { x: M, y: 2.3, w: 12.1, h: 0.9, fontSize: 26, italic: true, color: C.accent1 });
  txt(s, "Questions and discussion", { x: M, y: 3.4, w: 12.1, h: 0.6, fontSize: 20, color: C.background2 });
  txt(s, "KOUAME Koffi Fidèle  |  PyPSA case studies, code and data in pypsa-case-studies/", { x: M, y: 6.4, w: 12.1, h: 0.5, fontSize: 14, color: C.background2 });
  await iconCircle(s, "FaLightbulb", 11.3, 4.8, 1.3, C.accent1, "closing");
  s.addNotes("Close on the three messages and open the discussion.");

  const out = path.join(__dirname, "PyPSA_Case_Studies_Briefing.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("written", out);
})();
