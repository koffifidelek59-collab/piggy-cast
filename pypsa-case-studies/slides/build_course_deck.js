// Presentation in the layout of the course slides (white background, navy uppercase titles,
// navy subtitles, Arial, numbered footer; title slide with a picture and a navy band).
// Build:  node build_course_deck.js   ->  PyPSA_Case_Studies_Presentation.pptx
// All numbers are read from ../results/tables (written by the case-study notebooks).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

let applyTheme = async () => console.warn("apply_theme.js not found: default Office colours kept");
for (const p of [process.env.PPTX_SKILL_DIR && path.join(process.env.PPTX_SKILL_DIR, "scripts/apply_theme.js"),
                 path.join(__dirname, "apply_theme.js")].filter(Boolean)) {
  if (fs.existsSync(p)) { applyTheme = require(p).applyTheme; break; }
}

const TAB = path.join(__dirname, "../results/tables");
const FIG = path.join(__dirname, "../workbook/figures");
const DIA = path.join(__dirname, "../workbook/diagrams");
const J = (n) => JSON.parse(fs.readFileSync(path.join(TAB, `${n}_summary.json`)));
function csv(name) {                     // small CSV reader (handles quoted fields)
  const rows = fs.readFileSync(path.join(TAB, name), "utf8").trim().split("\n").map((line) => {
    const out = []; let cur = "", q = false;
    for (const ch of line) {
      if (ch === '"') q = !q; else if (ch === "," && !q) { out.push(cur); cur = ""; } else cur += ch;
    }
    out.push(cur); return out;
  });
  return { head: rows[0], rows: rows.slice(1) };
}
const S1 = J("cs01"), S3 = J("cs03"), S4 = J("cs04"), S5 = J("cs05"), S6 = J("cs06"), S7 = J("cs07"), S8 = J("cs08");

// ------------------------------------------------------------------ theme and layouts
const NAVY = "023D6B";
const THEME = {
  name: "Course", headFontFace: "Arial", bodyFontFace: "Arial",
  colors: { dk1: "000000", lt1: "FFFFFF", dk2: NAVY, lt2: "E8EEF3", accent1: NAVY, accent2: "2A78D6",
            accent3: "E59E1B", accent4: "C0392B", accent5: "6B7A90", accent6: "1F8A70", hlink: "2A78D6", folHlink: "6B7A90" },
};
const HX = THEME.colors, GREY = "7F7F7F";
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "KOUAME Koffi Fidele";
pres.title = "Power system case studies with PyPSA";
pres.theme = { headFontFace: "Arial", bodyFontFace: "Arial" };
const C = pres.SchemeColor;
const footer = [
  { text: { text: "KOUAME Koffi Fidèle | IMP-EGH", options: { x: 0.45, y: 7.05, w: 4.5, h: 0.3, fontSize: 9, color: GREY, margin: 0 } } },
  { text: { text: "PyPSA case studies", options: { x: 9.4, y: 7.05, w: 3.5, h: 0.3, fontSize: 9, color: GREY, align: "right", margin: 0 } } },
];
pres.defineSlideMaster({
  title: "COURSE_TITLE", background: { color: C.background1 },
  objects: [
    { rect: { x: 0, y: 4.35, w: 8.4, h: 2.15, fill: { color: C.text2 }, line: { color: C.text2, width: 0 } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.45, y: 4.55, w: 7.7, h: 1.15, fontSize: 26,
        bold: true, color: C.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.45, y: 5.75, w: 7.7, h: 0.6, fontSize: 12,
        color: C.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
    ...footer,
  ],
});
pres.defineSlideMaster({
  title: "COURSE_CONTENT", background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.45, y: 0.3, w: 12.4, h: 0.6, fontSize: 26,
        bold: true, color: C.text2, align: "left", valign: "top", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "sub", type: "body", x: 0.45, y: 0.92, w: 12.4, h: 0.4, fontSize: 15,
        bold: true, color: C.text2, align: "left", valign: "top", margin: 0 }, text: "" } },
    ...footer,
  ],
  slideNumber: { x: 6.27, y: 7.05, w: 0.8, h: 0.3, fontSize: 9, color: GREY, align: "center" },
});

// ------------------------------------------------------------------ helpers
const content = (title, sub, section) => {
  const s = pres.addSlide({ masterName: "COURSE_CONTENT", sectionTitle: section });
  s.addText(title.toUpperCase(), { placeholder: "title" });
  s.addText(sub, { placeholder: "sub" });
  return s;
};
const bullets = (s, items, o) => s.addText(items.map((t, i) => {
    // strings have inherited methods .bold() and .sub(): normalise to plain objects first
    const it = typeof t === "string" ? { text: t, bold: false, sub: false } : { bold: false, sub: false, ...t };
    return { text: it.text, options: { bullet: true, indentLevel: it.sub ? 1 : 0,
                                       breakLine: i < items.length - 1, bold: it.bold === true } };
  }),
  { isTextBox: true, margin: 0, valign: "top", color: C.text1, fontSize: 16, paraSpaceAfter: 6, ...o });
const text = (s, t, o) => s.addText(t, { isTextBox: true, margin: 0, valign: "top", color: C.text1, fontSize: 16, ...o });
const img = (s, file, x, y, w, ratio, o = {}) => s.addImage({ path: file, x, y, w, h: w / ratio, ...o });
const box = (s, x, y, w, h, id) => s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.background2 },
  line: { color: C.background2, width: 0 }, objectName: id });
const chartOpts = (title, extra = {}) => ({
  showTitle: true, title, titleFontSize: 13, titleColor: NAVY, titleFontFace: "+mn-lt",
  catAxisLabelColor: "404040", valAxisLabelColor: "404040", catAxisLabelFontSize: 11, valAxisLabelFontSize: 11,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", valGridLine: { color: "D9D9D9", size: 0.5 },
  catGridLine: { style: "none" }, dataLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelColor: "000000",
  showLegend: false, legendFontSize: 11, legendFontFace: "+mn-lt", ...extra });
const tableStyle = { fontFace: "Arial", fontSize: 12, color: "000000", border: { type: "solid", pt: 0.5, color: "BFBFBF" }, margin: 0.05 };
const th = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: NAVY }, align: "center" } });

(async () => {
  // ================================================================= 1 title
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "COURSE_TITLE", sectionTitle: "Introduction" });
  s.addImage({ path: path.join(FIG, "tp_original_5.jpg"), x: 0, y: 0, w: 13.333, h: 4.35,
               sizing: { type: "cover", w: 13.333, h: 4.35 }, altText: "Solar plant with battery storage" });
  s.addText("POWER SYSTEM CASE STUDIES WITH PYPSA", { placeholder: "title" });
  s.addText("LOAD FLOW, OPERATING LIMITS AND RENEWABLE INTEGRATION | KOUAME KOFFI FIDÈLE, IMP-EGH", { placeholder: "body" });
  s.addNotes("Exercise 5 and the practical work on load flow, solved with PyPSA, plus two real cases on 2023 weather for Niger.");

  // ================================================================= 2 topics
  s = content("Case studies", "Topics", "Introduction");
  bullets(s, ["Exercise 5: Newton's method and the Newton-Raphson load flow",
    "TP case 1: power sharing (3 buses)", "TP case 2: undervoltage (5 buses)",
    "TP case 3: congestion and N-1 security (IEEE 9-bus)", "TP case 4: demand growth (IEEE 14-bus)",
    "TP case 5: solar, reverse power flow and storage (IEEE 14-bus)",
    "Real case A: Niamey, solar and storage, every hour of 2023", "Real case B: Agadez off-grid mini-grid"],
    { x: 0.6, y: 1.6, w: 6.6, h: 5.0, fontSize: 18 });
  img(s, path.join(FIG, "tp_original_4.jpg"), 7.6, 1.6, 5.2, 1.334, { altText: "IEEE 14-bus system" });
  s.addNotes("Each case isolates one type of problem and follows the same scientific approach.");

  // ================================================================= 3 approach
  s = content("Scientific approach", "The eight steps applied to every case", "Introduction");
  const steps = ["Statement and question", "Data and hypotheses", "Physical model (equations)", "Solution method (algorithm)",
                 "Implementation in PyPSA", "Results", "Verification", "Interpretation and recommendation"];
  steps.forEach((t, i) => {
    const col = i < 4 ? 0 : 1, row = i % 4, x = 0.6 + col * 6.3, y = 1.65 + row * 1.25;
    s.addShape(pres.shapes.OVAL, { x, y, w: 0.75, h: 0.75, fill: { color: C.text2 }, line: { color: C.text2, width: 0 }, objectName: `step-${i}` });
    text(s, String(i + 1), { x, y, w: 0.75, h: 0.75, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle" });
    text(s, t, { x: x + 1.0, y: y + 0.12, w: 4.9, h: 0.5, fontSize: 18 });
  });
  s.addNotes("Statement with the original diagram; data and hypotheses; model; method; PyPSA code; results; independent verification; interpretation.");

  // ================================================================= 4 PyPSA
  s = content("PyPSA in practice", "Build the network, solve it, read the results", "Introduction");
  box(s, 0.45, 1.55, 6.9, 4.3, "code-bg");
  text(s, [
    "import pypsa", "n = pypsa.Network()",
    'n.add("Bus", "1", v_nom=110, v_mag_pu_set=1.00)',
    'n.add("Line", "L1-2", bus0="1", bus1="2",', '      x=15.125, b=8.26e-4)      # ohm, siemens',
    'n.add("Generator", "G1", bus="1",', '      control="Slack", p_set=0)',
    'n.add("Load", "D3", bus="3", p_set=250, q_set=100)',
    "n.pf()                    # AC load flow",
    "n.buses_t.v_mag_pu        # voltages (p.u.)", "n.optimize()              # optimal power flow"].join("\n"),
    { x: 0.65, y: 1.7, w: 6.5, h: 4.0, fontFace: "Courier New", fontSize: 13 });
  bullets(s, ["Units: MW, MVAr, kV, ohm, siemens", "Per-unit data: Z_B = kV²/MVA, then x = x_pu · Z_B",
    "Bus types: Slack, PV (P and |V|), PQ (P and Q)", "n.pf(): Newton-Raphson AC load flow",
    "n.optimize(): dispatch and investment (HiGHS)",
    `Check: PyPSA = own Newton-Raphson to ${S1.max_diff_pypsa.toExponential(0)}`],
    { x: 7.7, y: 1.6, w: 5.2, h: 4.4 });
  s.addNotes("Five objects are enough: Network, Bus, Line, Generator, Load. Per-unit data are converted with the base impedance of the zone, as in the per-unit method sheet.");

  // ================================================================= 5 Ex5 A1
  pres.addSection({ title: "Exercise 5" });
  s = content("Exercise 5: Newton's method", "Assignment 1: f(x) = 10x² − 2x³ = 0, f'(x) = 20x − 6x²", "Exercise 5");
  const a = csv("cs00_newton_x0_1.csv").rows, b = csv("cs00_newton_x0_4.csv").rows;
  const rowsN = [[th("k"), th("x_k (x0 = 1)"), th("Δx"), th("x_k (x0 = 4)"), th("Δx")]];
  for (let k = 0; k < 5; k++) rowsN.push([String(k), (+a[k][1]).toFixed(5), (+a[k][4]).toFixed(5), (+b[k][1]).toFixed(5), (+b[k][4]).toFixed(5)]);
  rowsN.push(["5", (+a[4][5]).toFixed(5), "", (+b[4][5]).toFixed(8), ""]);
  s.addTable(rowsN, { x: 0.6, y: 1.65, w: 6.6, colW: [0.6, 1.6, 1.4, 1.6, 1.4], ...tableStyle, align: "center" });
  bullets(s, ["From x0 = 1: double root 0, linear convergence (error halved each step)",
    "From x0 = 4: overshoot to 6, then quadratic convergence to 5 (8 exact digits)",
    "At x0 = 10/3, f'(x) = 0: no step possible", "Load flow = vector Newton: the Jacobian replaces f'(x)"],
    { x: 7.6, y: 1.65, w: 5.3, h: 4.6 });
  s.addNotes("Five iterations from each start. The double root slows Newton down; a simple root gives quadratic convergence.");

  // ================================================================= 6 Ex5 A2 statement
  s = content("Exercise 5: load-flow problem", "Assignment 2: three buses, slack (1), PV (2), PQ (3)", "Exercise 5");
  img(s, path.join(FIG, "ex5_original_figure1.png"), 0.45, 1.55, 8.3, 1.71, { altText: "Exercise 5 Figure 1" });
  bullets(s, ["Find Y, solve with Newton-Raphson, give flows and losses",
    { text: "Data check: the table values are swapped", bold: true },
    "Series admittance −j8 (X = 0.125 p.u.)", "Total line charging +j0.1 (j0.05 per end)",
    "Literal reading: no solution exists", "Unknowns: θ2, θ3, |U3|"],
    { x: 9.0, y: 1.6, w: 3.9, h: 5.0, fontSize: 15 });
  s.addNotes("The literal values give a capacitive series element and an 8 p.u. reactor; the problem has no solution. Swapping the values gives a normal line.");

  // ================================================================= 7 Ex5 solution
  s = content("Exercise 5: solution", "Admittance matrix, Newton-Raphson iterations, flows and losses", "Exercise 5");
  text(s, "Y = [ −j15.9   j8   j8 ;  j8   −j15.9   j8 ;  j8   j8   −j15.9 ]", { x: 0.6, y: 1.55, w: 6.6, h: 0.4, fontSize: 14, bold: true });
  const it = csv("cs01_nr_iterations.csv").rows;
  const rowsI = [[th("It."), th("max |ΔF|"), th("θ2 (°)"), th("θ3 (°)"), th("|U3|")]];
  it.forEach((r) => rowsI.push([r[0], (+r[1]).toExponential(1), (+r[2]).toFixed(3), (+r[3]).toFixed(3), (+r[4]).toFixed(4)]));
  s.addTable(rowsI, { x: 0.6, y: 2.1, w: 6.6, colW: [0.7, 1.6, 1.4, 1.4, 1.5], ...tableStyle, align: "center" });
  bullets(s, [`|U3| = ${S1.U3.toFixed(3)} p.u., θ3 = ${S1.theta3_deg.toFixed(2)}°, 4 iterations`,
    `P_G1 = ${S1.P_G1.toFixed(3)}, Q_G1 = ${S1.Q_G1.toFixed(3)}, Q_G2 = ${S1.Q_G2.toFixed(3)} p.u.`,
    `Losses: 0 + j${S1.Q_loss_total.toFixed(3)} p.u. (lossless lines)`], { x: 0.6, y: 4.9, w: 6.6, h: 1.8, fontSize: 15 });
  img(s, path.join(DIA, "ex5_solved.png"), 7.6, 1.55, 5.3, 1.422, { altText: "Solved Exercise 5 diagram" });
  s.addNotes("Quadratic convergence: 2.5, 0.21, 4e-3, 2e-6, 4e-13. Active balance exact, reactive losses 0.269 p.u.; PyPSA identical.");

  // ================================================================= 8 TP thread
  pres.addSection({ title: "Practical work" });
  s = content("Practical work: load flow on a real network", "Common thread: a solar plant in a grid supplying Niamey (educational data)", "Practical work");
  img(s, path.join(FIG, "tp_original_0.jpg"), 0.45, 1.55, 6.6, 1.541, { altText: "Practical work illustration" });
  bullets(s, ["Build the network: buses, lines, generators, loads", "Set parameters: R, X, ratings, P, Q",
    "Set bus types: slack, PV, PQ", "Run the AC load flow", "Change the scenario: demand, solar, battery",
    "Compare, interpret, recommend", { text: "Indicators: V, θ, P, Q, loading, losses", bold: true }],
    { x: 7.5, y: 1.6, w: 5.4, h: 5.0 });
  s.addNotes("Same protocol for every network size: 3, 5, 9 and 14 buses.");

  // ================================================================= 9 TP1
  s = content("TP case 1: power sharing (3 buses)", "Thermal plant (slack), city 50 MW + 20 MVAr, solar plant 30 MW", "Practical work");
  img(s, path.join(DIA, "tp1_model.png"), 0.45, 1.55, 5.9, 1.537, { altText: "Three-bus model" });
  const d2 = csv("cs02_design_point.csv").rows;
  const rows2 = [[th("Variant"), th("|V2|"), th("P thermal"), th("Q thermal"), th("Q PV"), th("Losses")]];
  d2.forEach((r) => rows2.push([r[0].replace("PV 30 MW, ", "PV, "), (+r[1]).toFixed(3), (+r[3]).toFixed(1), (+r[4]).toFixed(1), (+r[5]).toFixed(1), (+r[7]).toFixed(2)]));
  s.addTable(rows2, { x: 6.7, y: 1.6, w: 6.2, colW: [2.0, 0.75, 0.9, 0.9, 0.75, 0.9], ...tableStyle, fontSize: 11, align: "center" });
  bullets(s, ["Thermal output 50.3 → 20.2 MW (estimate 50 − 30 = 20)", "Voltages 1.009-1.017 p.u.: close to nominal",
    "Max loading 33 %; losses 0.28 → 0.19 MW", "Voltage control: inverters give 11.7 MVAr (< 13.7 MVAr)"],
    { x: 6.7, y: 3.55, w: 6.2, h: 3.0, fontSize: 15 });
  s.addNotes("Answers to questions 1 to 5 of the statement.");

  // ================================================================= 10 TP1 day
  s = content("TP case 1: a real day", "4 May 2023 (annual demand peak), real solar profile from NASA POWER", "Practical work");
  const day = csv("cs02_day.csv").rows, hours = day.map((r) => String(r[0]));
  s.addChart(pres.charts.LINE, [
      { name: "City demand", labels: hours, values: day.map((r) => +(+r[1]).toFixed(1)) },
      { name: "Thermal plant", labels: hours, values: day.map((r) => +(+r[3]).toFixed(1)) },
      { name: "Solar PV", labels: hours, values: day.map((r) => +(+r[2]).toFixed(1)) }],
    { x: 0.45, y: 1.55, w: 8.0, h: 5.2, ...chartOpts("Power (MW) by hour, local time", {
      chartColors: ["2A78D6", "E8743B", "E59E1B"], lineSize: 2, lineDataSymbol: "none", showLegend: true, legendPos: "b",
      valAxisMinVal: 0, valAxisMaxVal: 60 }) });
  bullets(s, ["PV gives at most 20 MW and 15 % of the energy", "Peak at 19:00, after sunset",
    "Thermal must still cover 50 MW", "Steep thermal ramp 16:00-19:00", "Solar saves fuel, not capacity, without storage"],
    { x: 8.8, y: 1.6, w: 4.1, h: 5.0, fontSize: 16 });
  s.addNotes("24 AC load flows with the measured solar profile; energy balance 837 + 147 = 980 + 4 MWh.");

  // ================================================================= 11 TP2 problem
  s = content("TP case 2: undervoltage (5 buses)", "Remote industrial zone at the end of an 85 km line", "Practical work");
  img(s, path.join(DIA, "tp2_model.png"), 0.45, 1.55, 7.0, 2.281, { altText: "Five-bus model" });
  img(s, path.join(FIG, "tp_original_2.jpg"), 0.45, 4.75, 3.6, 1.847, { altText: "Original five-bus figure" });
  const vA = [1.02, 0.9965, 1.006, 0.9806, S3.V5_A], vB = [1.02, 0.9944, 1.0003, 0.9765, S3.V5_B];
  s.addChart(pres.charts.LINE, [
      { name: "A: PV 40 MW", labels: ["1", "2", "3", "4", "5"], values: vA.map((v) => +v.toFixed(3)) },
      { name: "B: evening, no PV", labels: ["1", "2", "3", "4", "5"], values: vB.map((v) => +v.toFixed(3)) },
      { name: "Limit 0.95", labels: ["1", "2", "3", "4", "5"], values: [0.95, 0.95, 0.95, 0.95, 0.95] }],
    { x: 7.7, y: 1.55, w: 5.2, h: 3.9, ...chartOpts("Bus voltage (p.u.)", {
      chartColors: ["2A78D6", "E8743B", "C0392B"], lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 7,
      showLegend: true, legendPos: "b", valAxisMinVal: 0.9, valAxisMaxVal: 1.04, valAxisLabelFormatCode: "0.00" }) });
  bullets(s, [`V5 = ${S3.V5_B.toFixed(3)} p.u. at the evening peak`, "Below 0.95 p.u. 24 hours a day",
    "Cause: X ≈ 3R and a reactive load (35 + j18 MW)"], { x: 4.4, y: 4.85, w: 8.5, h: 1.9, fontSize: 15 });
  s.addNotes("Only bus 5 violates the limit; the worst case is the evening peak without sun.");

  // ================================================================= 12 TP2 remedies
  s = content("TP case 2: remedies", "Compared at the evening peak; 3.1 points of voltage needed", "Practical work");
  const rem = [["Capacitor 15 MVAr", "capacitor 15 MVAr at bus 5"], ["SVC / STATCOM", "SVC/STATCOM at bus 5 (0.97 p.u.)"],
               ["Second circuit", "second circuit on line 4-5"], ["Set point 1.05", "plant set point 1.05 p.u."],
               ["PV inverters", "PV inverters Q-at-night, 1.03 p.u."]];
  s.addChart(pres.charts.BAR, [{ name: "gain", labels: rem.map((r) => r[0]), values: rem.map((r) => +(100 * (S3.remedies[r[1]] - S3.remedies.none)).toFixed(1)) }],
    { x: 0.45, y: 1.55, w: 6.6, h: 4.3, barDir: "bar", ...chartOpts("Voltage gain at bus 5 (points of %)", {
      chartColors: ["1F8A70", "2A78D6", "2A78D6", "2A78D6", "C0392B"], showValue: true, dataLabelPosition: "outEnd",
      dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisMaxVal: 6, catAxisOrientation: "maxMin" }) });
  img(s, path.join(DIA, "tp2_solved.png"), 7.3, 1.6, 5.6, 2.825, { altText: "Solved five-bus diagram" });
  bullets(s, [{ text: "Recommendation: 15 MVAr capacitor bank (3 × 5 MVAr)", bold: true },
    "V5 0.919 → 0.959 p.u.; Q on line 4-5: 17.5 → 2.7 MVAr", "Losses −14 % at the peak, −16 % over the day",
    "PV inverters would need 68 MVAr (> 44 MVA)"], { x: 7.3, y: 3.75, w: 5.6, h: 3.0, fontSize: 15 });
  s.addNotes("Smallest bank 11.8 MVAr by bisection; 15 MVAr chosen in three steps. Second circuit kept as long-term option.");

  // ================================================================= 13 TP3
  s = content("TP case 3: congestion and N-1 (IEEE 9-bus)", "Hot season (ratings −15 %) and evening peak (+15 %)", "Practical work");
  img(s, path.join(FIG, "tp_original_3.jpg"), 0.45, 1.6, 5.6, 1.804, { altText: "IEEE 9-bus" });
  const ne = csv("cs04_n1_economic_dispatch.csv").rows, ns = csv("cs04_n1_secure_dispatch.csv").rows;
  s.addChart(pres.charts.BAR, [
      { name: "Economic dispatch", labels: ne.map((r) => "loss of " + r[0]), values: ne.map((r) => +(+r[2]).toFixed(1)) },
      { name: "Secure dispatch", labels: ns.map((r) => "loss of " + r[0]), values: ns.map((r) => +(+r[2]).toFixed(1)) }],
    { x: 6.3, y: 1.55, w: 6.6, h: 4.4, barDir: "bar", barGrouping: "clustered", ...chartOpts("Worst post-outage loading (% of rating)", {
      chartColors: ["E8743B", "1F8A70"], showLegend: true, legendPos: "b", showValue: true, dataLabelPosition: "outEnd",
      dataLabelFormatCode: "0", valAxisMinVal: 0, valAxisMaxVal: 130, catAxisOrientation: "maxMin", dataLabelFontSize: 9 }) });
  bullets(s, [`Loss of 8-9 overloads 5-6: ${S4.n1_worst_ed.toFixed(0)} %`, "Security-constrained OPF: 99 %",
    "AC check: loss of 9-4 → bus 9 at 0.75 p.u."], { x: 0.6, y: 4.9, w: 5.5, h: 1.9, fontSize: 15 });
  s.addNotes("The 115 % of the statement is reproduced by physics: hot-season derating and evening peak, then N-1.");

  // ================================================================= 14 TP3 decision
  s = content("TP case 3: decision", "Redispatch first, reactive support where the AC check says so", "Practical work");
  const cols3 = [["Preventive redispatch", `+${S4.security_cost_per_h.toFixed(0)} $/h`, `${(100 * S4.security_cost_per_h / S4.cost_ed).toFixed(1)} % of cost; 18 MW moved to G1`],
                 ["Nodal prices", `${S4.lmp_sc[0].toFixed(1)}-${S4.lmp_sc[1].toFixed(1)}`, "$/MWh instead of one price: value of the corridor"],
                 ["Reactive support at bus 9", `${S4.q_cap9.toFixed(0)} MVAr`, "after the loss of 9-4: voltage 0.75 → 0.95 p.u."]];
  cols3.forEach((c, i) => {
    const x = 0.6 + i * 4.15;
    box(s, x, 1.65, 3.9, 3.0, `dec-${i}`);
    text(s, c[0], { x: x + 0.25, y: 1.85, w: 3.4, h: 0.5, fontSize: 16, bold: true, color: C.text2 });
    text(s, c[1], { x: x + 0.25, y: 2.45, w: 3.4, h: 0.9, fontSize: 34, bold: true, color: C.text2 });
    text(s, c[2], { x: x + 0.25, y: 3.45, w: 3.4, h: 1.0, fontSize: 14 });
  });
  bullets(s, ["Uprating line 5-6 fixes flows (97 %) but not the voltage at bus 9",
    `Redispatch ≈ ${S4["yearly_redispatch_k$"].toFixed(0)} k$ per year (600 critical hours): reinforce only if congestion becomes frequent`,
    "A DC optimisation must always be re-checked with the AC load flow"], { x: 0.6, y: 4.95, w: 12.3, h: 1.9, fontSize: 16 });
  s.addNotes("Three levers, from the cheapest; the price spread tells planners when to reinforce.");

  // ================================================================= 15 TP4
  s = content("TP case 4: demand growth (IEEE 14-bus)", "S0 to S5 (+0 to +50 %), generator reactive limits enforced", "Practical work");
  img(s, path.join(FIG, "tp_original_4.jpg"), 0.45, 1.6, 3.6, 1.334, { altText: "IEEE 14-bus" });
  const t5 = Object.values(S5.table), lab5 = ["S0", "S1", "S2", "S3", "S4", "S5"];
  s.addChart(pres.charts.LINE, [{ name: "min V", labels: lab5, values: t5.map((r) => +r["min |V| (p.u.)"].toFixed(3)) }],
    { x: 4.3, y: 1.55, w: 4.3, h: 3.6, ...chartOpts("Lowest bus voltage (p.u.)", { chartColors: ["2A78D6"], lineSize: 2,
      lineDataSymbol: "circle", lineDataSymbolSize: 7, valAxisMinVal: 0.88, valAxisMaxVal: 1.02, valAxisLabelFormatCode: "0.00",
      showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "0.000", dataLabelFontSize: 9 }) });
  s.addChart(pres.charts.BAR, [{ name: "at limit", labels: lab5, values: t5.map((r) => r["gens at Q limit"]) }],
    { x: 8.7, y: 1.55, w: 4.2, h: 3.6, barDir: "col", ...chartOpts("Units at their reactive limit (of 4)", { chartColors: ["C0392B"],
      valAxisMinVal: 0, valAxisMaxVal: 4, valAxisMajorUnit: 1, showValue: true, dataLabelPosition: "outEnd" }) });
  bullets(s, ["Up to +30 %: voltages fine, but all reactive reserve used", "+50 %: nine buses below 0.95 p.u.; losses 13.4 → 35.2 MW",
    { text: `Maximum loadability +${Math.round(100 * (S5.lambda_max - 1))} % (not +145 % as without limits)`, bold: true }],
    { x: 0.6, y: 5.35, w: 12.3, h: 1.5, fontSize: 16 });
  s.addNotes("The first warning is the loss of reactive reserve, not a low voltage.");

  // ================================================================= 16 TP5
  s = content("TP case 5: solar, reverse flow and storage", "PV plant at bus 14 of the IEEE 14-bus system, real profile of 16 March 2023", "Practical work");
  const hc = S6.hosting_capacity;
  s.addChart(pres.charts.BAR, [{ name: "MW", labels: ["Original set points", "Set points −0.03", "+ PF 0.95 absorbing"],
      values: [hc["unity PF, original set points"][0], hc["unity PF, set points -0.03"][0], hc["PF 0.95 absorbing, set points -0.03"][0]] }],
    { x: 0.45, y: 1.55, w: 5.4, h: 4.0, barDir: "col", ...chartOpts("Hosting capacity at noon (MW)", {
      chartColors: ["7F7F7F", "2A78D6", "1F8A70"], showValue: true, dataLabelPosition: "outEnd", valAxisMinVal: 0, catAxisLabelFontSize: 10 }) });
  const sc6 = S6.scenarios;
  const rows6 = [[th("Scenario"), th("max V14"), th("overvolt. h"), th("reverse h"), th("export MW")]];
  Object.entries(sc6).forEach(([k, v]) => rows6.push([k.replace(" + set points", ""), v["max V14 (p.u.)"].toFixed(3), String(v["hours with overvoltage"]),
    String(v["hours of reverse flow"]), v["max export from bus 14 (MW)"].toFixed(0)]));
  s.addTable(rows6, { x: 6.1, y: 1.6, w: 6.8, colW: [2.4, 1.1, 1.1, 1.1, 1.1], ...tableStyle, fontSize: 11, align: "center" });
  bullets(s, ["Flow reverses when PV > local load (≈ 14 MW): 60 − 40 = 20 MW logic",
    "Voltage rise is the limit, not line capacity", "Battery cuts peak voltage and export but must be voltage-aware"],
    { x: 0.6, y: 5.75, w: 12.3, h: 1.2, fontSize: 15 });
  s.addNotes("S4 = battery + PF 0.95 + set points lowered: no overvoltage hour.");

  // ================================================================= 17 real case A cost
  pres.addSection({ title: "Real cases" });
  s = content("Real case A: Niamey, every hour of 2023", "Least-cost solar and storage, with and without imports", "Real cases");
  bullets(s, ["Real weather: NASA POWER 2023, 1 710 kWh/kWp", "Demand 726 GWh, peak 105 MW (model)",
    "Fuel 180 $/MWh, imports 70 $/MWh", "PV 800 $/kW, battery 4 h 1 150 $/kW", "Islanded: 20 MW thermal must-run",
    "Linear OPF + investment, 8 760 hours"], { x: 0.6, y: 1.6, w: 4.6, h: 5.0, fontSize: 15 });
  const order = [["A imports, no PV", "A imports"], ["B no imports, no PV", "B islanded"], ["C no imports, 100 MW PV", "C +100 MW PV"],
                 ["D0 no imports, optimal PV, no battery", "D0 opt. PV"], ["D no imports, optimal PV+battery", "D PV+storage"],
                 ["E imports, optimal PV+battery", "E imports+PV"]];
  s.addChart(pres.charts.BAR, [{ name: "$/MWh", labels: order.map((o) => o[1]), values: order.map((o) => Math.round(S7.scenarios[o[0]]["average cost ($/MWh)"])) }],
    { x: 5.4, y: 1.55, w: 7.5, h: 5.2, barDir: "col", ...chartOpts("Average cost of supply ($/MWh)", {
      chartColors: ["7F7F7F", "E8743B", "E59E1B", "E59E1B", "1F8A70", "2A78D6"], showValue: true, dataLabelPosition: "outEnd",
      valAxisMinVal: 0, catAxisLabelFontSize: 10 }) });
  s.addNotes("Islanded, the cost is 180 $/MWh; solar plus storage brings it to 140; with imports, solar still lowers 78 to 68.");

  // ================================================================= 18 real case A results
  const D = S7.scenarios["D no imports, optimal PV+battery"], B = S7.scenarios["B no imports, no PV"];
  s = content("Real case A: results", "Storage, not the grid, unlocks solar", "Real cases");
  [[`${Math.round(D["PV (MW)"])} MW`, `solar with a ${Math.round(D["battery (MW)"])} MW / ${Math.round(D["battery (MWh)"])} MWh battery`],
   [`${Math.round(D["solar share (%)"])} %`, "of the yearly demand from the sun"],
   [`−${Math.round(100 * (1 - D["thermal (GWh)"] / B["thermal (GWh)"]))} %`, "fuel, and −22 % yearly cost"]].forEach((st, i) => {
    box(s, 0.6, 1.6 + i * 1.65, 4.6, 1.45, `stat-${i}`);
    text(s, st[0], { x: 0.85, y: 1.7 + i * 1.65, w: 4.2, h: 0.75, fontSize: 32, bold: true, color: C.text2 });
    text(s, st[1], { x: 0.85, y: 2.45 + i * 1.65, w: 4.2, h: 0.5, fontSize: 14 });
  });
  s.addChart(pres.charts.BAR, [{ name: "kt", labels: order.map((o) => o[1]), values: order.map((o) => Math.round(S7.scenarios[o[0]]["CO2 (kt)"])) }],
    { x: 5.4, y: 1.55, w: 7.5, h: 3.9, barDir: "col", ...chartOpts("CO2 of the thermal plant (kt per year)", {
      chartColors: ["7F7F7F"], showValue: true, dataLabelPosition: "outEnd", valAxisMinVal: 0, catAxisLabelFontSize: 10 }) });
  bullets(s, ["Without storage: 154 MW PV, 20 % curtailed", `Lines ≤ ${Math.round(D["max line loading (%)"])} %; AC check 0.968-1.02 p.u.`],
    { x: 5.5, y: 5.6, w: 7.4, h: 1.2, fontSize: 15 });
  s.addNotes("The battery at the solar site also smooths the line flows. Thermal stays for monsoon weeks.");

  // ================================================================= 19 real case B
  const G = S8.base;
  s = content("Real case B: Agadez mini-grid", "Solar + battery + diesel back-up, real weather 2023", "Real cases");
  const rowsB = [[th(""), th("Diesel only"), th("Optimal hybrid")],
    ["PV / battery", "-", `${(G["optimal hybrid"]["PV (kW)"] / 1000).toFixed(1)} MW / ${(G["optimal hybrid"]["battery (kWh)"] / 1000).toFixed(0)} MWh`],
    ["Renewable share", "0 %", `${Math.round(G["optimal hybrid"]["renewable share (%)"])} %`],
    ["Diesel per year", `${(G["diesel only"]["diesel (1000 litres)"] / 1000).toFixed(2)} M litres`, `${(G["optimal hybrid"]["diesel (1000 litres)"] / 1000).toFixed(2)} M litres`],
    ["CO2 per year", `${Math.round(G["diesel only"]["CO2 (t)"])} t`, `${Math.round(G["optimal hybrid"]["CO2 (t)"])} t`],
    ["Cost of electricity", `${G["diesel only"]["LCOE ($/kWh)"].toFixed(2)} $/kWh`, `${G["optimal hybrid"]["LCOE ($/kWh)"].toFixed(2)} $/kWh`]];
  s.addTable(rowsB, { x: 0.6, y: 1.6, w: 6.4, colW: [2.2, 2.0, 2.2], ...tableStyle, fontSize: 13 });
  const sens = S8.sensitivity;
  s.addChart(pres.charts.LINE, [
      { name: "Diesel only", labels: sens.map((r) => `${r["diesel price ($/l)"].toFixed(1)} $/l`), values: sens.map((r) => +r["LCOE diesel only ($/kWh)"].toFixed(3)) },
      { name: "Optimal hybrid", labels: sens.map((r) => `${r["diesel price ($/l)"].toFixed(1)} $/l`), values: sens.map((r) => +r["LCOE ($/kWh)"].toFixed(3)) }],
    { x: 7.3, y: 1.55, w: 5.6, h: 4.2, ...chartOpts("Cost of electricity ($/kWh) vs diesel price", {
      chartColors: ["E8743B", "1F8A70"], lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 7, valAxisMinVal: 0,
      valAxisMaxVal: 0.45, valAxisLabelFormatCode: "0.00", showLegend: true, legendPos: "b" }) });
  bullets(s, ["Hybrid halves the cost and cuts diesel by 94 %", "Cheaper at every fuel price tested", "Genset kept as back-up for monsoon days"],
    { x: 0.6, y: 4.95, w: 6.4, h: 1.8, fontSize: 15 });
  s.addNotes("Fuel-price risk is replaced by a predictable investment.");

  // ================================================================= 20 recommendations
  pres.addSection({ title: "Conclusion" });
  s = content("Recommendations", "For grid managers and decision-makers", "Conclusion");
  bullets(s, ["Fix voltage cheaply first: capacitor banks at remote substations, review voltage set points",
    "Monitor the reactive reserve, not only the voltage; plan compensation before demand grows 30 %",
    "Operate N-1 secure in the hot season: preventive redispatch and AC contingency checks",
    "Grid code for solar: reactive capability (PF 0.95) and voltage-aware storage",
    "Invest in solar + storage: security for Niamey, hybrid mini-grids for northern towns"],
    { x: 0.6, y: 1.6, w: 8.0, h: 5.2, fontSize: 17, paraSpaceAfter: 10 });
  box(s, 9.0, 1.6, 3.9, 3.4, "keynum");
  text(s, [{ text: "Key numbers", options: { bold: true, color: NAVY, breakLine: true, fontSize: 16 } },
    { text: "0.919 → 0.959 p.u. (capacitor)", options: { breakLine: true } }, { text: "113 % → 99 % for 54 $/h", options: { breakLine: true } },
    { text: "Loadability +77 %", options: { breakLine: true } }, { text: "Hosting 3 → 129 MW", options: { breakLine: true } },
    { text: "Niamey: −22 % cost, −68 % fuel", options: { breakLine: true } }, { text: "Agadez: 0.30 → 0.16 $/kWh", options: {} }],
    { x: 9.25, y: 1.85, w: 3.5, h: 4.6, fontSize: 14, paraSpaceAfter: 8 });
  s.addNotes("Cheap operational measures first; storage is what lets the grid absorb solar.");

  // ================================================================= 21 next steps
  s = content("Next steps and discussion", "From educational models to real decisions", "Conclusion");
  bullets(s, ["Replace educational grids with real network and load data", "Renewables.ninja and multi-year weather (2015-2023)",
    "N-1 checks on every hour of the solar and storage plan", "Feasibility of capacitor banks and a first solar + storage block",
    "Financing and grid-code update for inverters"], { x: 0.6, y: 1.6, w: 7.6, h: 4.0, fontSize: 18 });
  text(s, "THANK YOU - QUESTIONS", { x: 0.6, y: 5.75, w: 7.6, h: 0.6, fontSize: 24, bold: true, color: C.text2 });
  img(s, path.join(FIG, "tp_original_5.jpg"), 8.5, 1.6, 4.4, 1.779, { altText: "Solar plant with storage" });
  s.addNotes("Code, datasets, notebooks and the workbook are in pypsa-case-studies/.");

  const out = path.join(__dirname, "PyPSA_Case_Studies_Presentation.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("written", out);
})();
