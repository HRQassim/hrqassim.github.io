// HR Qassim — ويدجت مجتمع محترفي الموارد البشرية (Scriptable)
// https://hrqassim.github.io
const SITE = "https://hrqassim.github.io/";
const NAVY = new Color("#20324C"), BLUE = new Color("#35547D"), SKY = new Color("#8FC0E6"), SOFT = new Color("#C9D8E8");

let d = null;
try { d = await new Request(SITE + "data/stats.json?t=" + Date.now()).loadJSON(); } catch (e) {}
let logo = null;
try { logo = await new Request(SITE + "assets/logo-icon-white.png").loadImage(); } catch (e) {}

const fam = config.widgetFamily || "medium";
const w = new ListWidget();
const g = new LinearGradient(); g.colors = [BLUE, NAVY]; g.locations = [0, 1]; w.backgroundGradient = g;
w.setPadding(14, 16, 14, 16);
w.url = SITE;
w.refreshAfterDate = new Date(Date.now() + 3 * 3600 * 1000);

// header
const h = w.addStack(); h.centerAlignContent();
if (logo) { const im = h.addImage(logo); im.imageSize = new Size(22, 22); h.addSpacer(6); }
const ht = h.addText("HR Qassim"); ht.font = Font.boldSystemFont(13); ht.textColor = Color.white();
w.addSpacer();

function stat(parent, num, label) {
  const s = parent.addStack(); s.layoutVertically();
  const n = s.addText(String(num)); n.font = Font.boldRoundedSystemFont(fam === "small" ? 30 : 24); n.textColor = Color.white();
  const l = s.addText(label); l.font = Font.mediumSystemFont(11); l.textColor = SOFT;
}

if (!d) {
  const t = w.addText("افتح الموقع لعرض آخر التحديثات"); t.font = Font.systemFont(12); t.textColor = SOFT;
} else if (fam === "small") {
  stat(w, d.cvs, "سيرة ذاتية");
  w.addSpacer(6);
  if (d.next) { const t = w.addText("التوطين القادم: " + d.next.date); t.font = Font.systemFont(10); t.textColor = SKY; t.lineLimit = 2; }
} else {
  const r = w.addStack(); r.bottomAlignContent();
  stat(r, d.cvs, "سيرة ذاتية"); r.addSpacer();
  stat(r, d.decisions, "قرار توطين"); r.addSpacer();
  stat(r, d.jd, "وصف وظيفي");
  if (d.next) {
    w.addSpacer(10);
    const b = w.addStack(); b.backgroundColor = new Color("#ffffff", 0.12); b.cornerRadius = 10; b.setPadding(6, 10, 6, 10); b.layoutVertically();
    const a = b.addText("التوطين القادم · " + d.next.date); a.font = Font.boldSystemFont(11); a.textColor = SKY;
    const c = b.addText(d.next.t + (d.next.pct ? " — " + d.next.pct + "%" : "")); c.font = Font.mediumSystemFont(12); c.textColor = Color.white(); c.lineLimit = fam === "large" ? 2 : 1;
  }
}

if (config.runsInWidget) Script.setWidget(w);
else if (fam === "small") await w.presentSmall(); else await w.presentMedium();
Script.complete();
