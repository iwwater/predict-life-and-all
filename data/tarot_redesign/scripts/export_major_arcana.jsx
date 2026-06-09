#target photoshop
app.displayDialogs = DialogModes.NO;

var sourcePath = "E:/work/predict life and all/data/ChatGPT Image 2026年6月7日 15_42_09 (2).png";
var outDir = Folder("E:/work/predict life and all/data/tarot_redesign/major_arcana");
var previewDir = Folder("E:/work/predict life and all/data/tarot_redesign/preview");
if (!outDir.exists) outDir.create();
if (!previewDir.exists) previewDir.create();

var cards = [
  ["00_the_fool", "0", "愚者", "THE FOOL", 0, 0],
  ["01_the_magician", "I", "魔术师", "THE MAGICIAN", 1, 0],
  ["02_the_high_priestess", "II", "女祭司", "THE HIGH PRIESTESS", 2, 0],
  ["03_the_empress", "III", "女皇", "THE EMPRESS", 3, 0],
  ["04_the_emperor", "IV", "皇帝", "THE EMPEROR", 4, 0],
  ["05_the_hierophant", "V", "教皇", "THE HIEROPHANT", 5, 0],
  ["06_the_lovers", "VI", "恋人", "THE LOVERS", 0, 1],
  ["07_the_chariot", "VII", "战车", "THE CHARIOT", 1, 1],
  ["08_strength", "VIII", "力量", "STRENGTH", 2, 1],
  ["09_the_hermit", "IX", "隐士", "THE HERMIT", 3, 1],
  ["10_wheel_of_fortune", "X", "命运之轮", "WHEEL OF FORTUNE", 4, 1],
  ["11_justice", "XI", "正义", "JUSTICE", 5, 1],
  ["12_the_hanged_man", "XII", "倒吊人", "THE HANGED MAN", 0, 2],
  ["13_death", "XIII", "死神", "DEATH", 1, 2],
  ["14_temperance", "XIV", "节制", "TEMPERANCE", 2, 2],
  ["15_the_devil", "XV", "恶魔", "THE DEVIL", 3, 2],
  ["16_the_tower", "XVI", "塔", "THE TOWER", 4, 2],
  ["17_the_star", "XVII", "星星", "THE STAR", 5, 2],
  ["18_the_moon", "XVIII", "月亮", "THE MOON", 0, 3],
  ["19_the_sun", "XIX", "太阳", "THE SUN", 1, 3],
  ["20_judgement", "XX", "审判", "JUDGEMENT", 2, 3],
  ["21_the_world", "XXI", "世界", "THE WORLD", 3, 3]
];

// Sheet is 1024 x 1536. The card grid is 6 columns x 4 rows.
// These coordinates intentionally keep the printed card border and remove the sheet background gutter.
var left0 = 10;
var top0 = 10;
var cardW = 160;
var cardH = 372;
var stepX = 169;
var stepY = 384;

function savePng(doc, file) {
  var opts = new PNGSaveOptions();
  opts.compression = 6;
  opts.interlaced = false;
  doc.saveAs(file, opts, true, Extension.LOWERCASE);
}

function selectAllFill(doc, rgb) {
  var color = new SolidColor();
  color.rgb.red = rgb[0]; color.rgb.green = rgb[1]; color.rgb.blue = rgb[2];
  doc.selection.selectAll();
  doc.selection.fill(color, ColorBlendMode.NORMAL, 100, false);
  doc.selection.deselect();
}

function addText(doc, text, size, x, y, colorRgb, fontName) {
  var layer = doc.artLayers.add();
  layer.kind = LayerKind.TEXT;
  layer.textItem.contents = text;
  layer.textItem.size = size;
  layer.textItem.position = [x, y];
  layer.textItem.justification = Justification.CENTER;
  if (fontName) layer.textItem.font = fontName;
  var color = new SolidColor();
  color.rgb.red = colorRgb[0]; color.rgb.green = colorRgb[1]; color.rgb.blue = colorRgb[2];
  layer.textItem.color = color;
  return layer;
}

function strokeRect(doc, left, top, right, bottom, rgb, width) {
  var color = new SolidColor();
  color.rgb.red = rgb[0]; color.rgb.green = rgb[1]; color.rgb.blue = rgb[2];
  doc.selection.select([[left, top], [right, top], [right, bottom], [left, bottom]]);
  doc.selection.stroke(color, width, StrokeLocation.INSIDE, ColorBlendMode.NORMAL, 100, false);
  doc.selection.deselect();
}

var src = app.open(File(sourcePath));
for (var i = 0; i < cards.length; i++) {
  var c = cards[i];
  var x = left0 + c[4] * stepX;
  var y = top0 + c[5] * stepY;
  var dup = src.duplicate(c[0], false);
  dup.crop([x, y, x + cardW, y + cardH]);
  dup.resizeImage(UnitValue(768, "px"), UnitValue(1152, "px"), 300, ResampleMethod.PRESERVEDETAILS);
  savePng(dup, File(outDir + "/" + c[0] + ".png"));
  dup.close(SaveOptions.DONOTSAVECHANGES);
}
src.close(SaveOptions.DONOTSAVECHANGES);

// Create a redesigned card back using the same paper/gold/ink visual system.
var back = app.documents.add(UnitValue(768, "px"), UnitValue(1152, "px"), 300, "tarot_card_back_redesign", NewDocumentMode.RGB, DocumentFill.WHITE);
selectAllFill(back, [244, 238, 226]);
strokeRect(back, 42, 42, 726, 1110, [190, 155, 88], 4);
strokeRect(back, 68, 68, 700, 1084, [43, 45, 42], 2);
strokeRect(back, 112, 112, 656, 1040, [190, 155, 88], 1);
addText(back, "玄枢", 82, 384, 454, [38, 38, 35], "SimSun");
addText(back, "MYSTIC HUB", 42, 384, 565, [120, 93, 45], "TimesNewRomanPSMT");
addText(back, "☉  ☽  ✦  ♄  ✦  ☽  ☉", 32, 384, 655, [190, 155, 88], "TimesNewRomanPSMT");
addText(back, "问事 · 观心 · 起局", 34, 384, 756, [38, 38, 35], "SimSun");
savePng(back, File(previewDir + "/tarot_card_back.png"));
back.close(SaveOptions.DONOTSAVECHANGES);

// Contact sheet for quick visual QA.
var sheet = app.documents.add(UnitValue(1600, "px"), UnitValue(2400, "px"), 150, "major_arcana_contact_sheet", NewDocumentMode.RGB, DocumentFill.WHITE);
selectAllFill(sheet, [238, 230, 214]);
for (var j = 0; j < cards.length; j++) {
  var f = File(outDir + "/" + cards[j][0] + ".png");
  var d = app.open(f);
  d.resizeImage(UnitValue(220, "px"), UnitValue(330, "px"), 150, ResampleMethod.BICUBICSHARPER);
  d.selection.selectAll(); d.selection.copy(); d.close(SaveOptions.DONOTSAVECHANGES);
  app.activeDocument = sheet; sheet.paste();
  var layer = sheet.activeLayer;
  var col = j % 6; var row = Math.floor(j / 6);
  layer.translate(70 + col * 250, 80 + row * 500);
  addText(sheet, cards[j][1] + "  " + cards[j][2], 26, 180 + col * 250, 455 + row * 500, [38, 38, 35], "SimSun");
}
savePng(sheet, File(previewDir + "/major_arcana_contact_sheet.png"));
sheet.close(SaveOptions.DONOTSAVECHANGES);

alert("Tarot redesign export complete: " + outDir.fsName);
