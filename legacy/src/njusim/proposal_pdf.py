"""Build the review proposal without changing simulation or frozen source.
Run with bundled Python: python -I -B src/njusim/proposal_pdf.py
Requires reportlab and pypdf in the document runtime, not the native simulator.
"""
import json
import os
from pathlib import Path
import sys
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from njusim.io import safe_path
from njusim.guard import install

TMP = safe_path("tmp/pdfs")
TMP.mkdir(parents=True, exist_ok=True)
for key in ("TEMP", "TMP", "TMPDIR"):
    os.environ[key] = str(TMP)
install()

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from pypdf import PdfReader

regular = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/msyh.ttc"
bold = regular.with_name("msyhbd.ttc")
pdfmetrics.registerFont(TTFont("CN", str(regular), subfontIndex=0))
pdfmetrics.registerFont(TTFont("CNBold", str(bold), subfontIndex=0))
pdfmetrics.registerFontFamily("CN", normal="CN", bold="CNBold")
INK = colors.HexColor("#142B3D")
TEAL = colors.HexColor("#147D81")
MUTED = colors.HexColor("#556574")
styles = {
    "p": ParagraphStyle("Body", fontName="CN", fontSize=10, leading=15.5,
                        textColor=INK, wordWrap="CJK", spaceAfter=6),
    "h": ParagraphStyle("Heading", fontName="CNBold", fontSize=11, leading=16,
                        textColor=TEAL, spaceBefore=7, spaceAfter=5, keepWithNext=True),
    "small": ParagraphStyle("Small", fontName="CN", fontSize=7.7, leading=11.3,
                        textColor=MUTED, wordWrap="CJK", spaceAfter=3),
    "cell": ParagraphStyle("Cell", fontName="CN", fontSize=9.0, leading=13.5,
                        textColor=INK, wordWrap="CJK"),
}
def para(text, kind="p"):
    return Paragraph(escape(text), styles[kind])

data = json.loads(safe_path("submission/proposal-20261010.json").read_text(encoding="utf-8"))
out = safe_path("output/pdf/nju-track-c-proposal-20261010-review.pdf")
out.parent.mkdir(parents=True, exist_ok=True)
story = []
story.append(Paragraph(escape(data["title"]), ParagraphStyle("Title", fontName="CNBold", fontSize=22,
                            leading=29, textColor=INK, spaceAfter=2)))
story.append(Paragraph(escape(data["subtitle"]), ParagraphStyle("Subtitle", fontName="CN", fontSize=13,
                            leading=20, textColor=TEAL, spaceAfter=9)))
story.append(para(data["meta"], "small"))
story.append(para(data["status"], "small"))
story.append(Spacer(1, 4))
for i, blocks in enumerate(data["pages"]):
    if i:
        story.append(PageBreak())
    for kind, value in blocks:
        if kind == "table":
            rows = [[para(c, "cell") for c in row] for row in value]
            table = Table(rows, colWidths=[115, A4[0]-88-115], hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E4EFF1")),
                ("BACKGROUND",(0,1),(0,-1),colors.HexColor("#F3F6F7")),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("LEFTPADDING",(0,0),(-1,-1),8),
                ("RIGHTPADDING",(0,0),(-1,-1),8),
                ("TOPPADDING",(0,0),(-1,-1),6),
                ("BOTTOMPADDING",(0,0),(-1,-1),6),
                ("LINEBELOW",(0,0),(-1,-1),.4,colors.HexColor("#D4DEE2")),
            ]))
            story.extend([table, Spacer(1,7)])
        elif kind == "links":
            for label, url in value:
                story.append(Paragraph(f'<link href="{escape(url)}" color="#147D81">{escape(label)}</link>', styles["small"]))
        else:
            story.append(para(value, kind))
def footer(canvas, doc):
    canvas.saveState()
    w,h = A4
    canvas.setStrokeColor(colors.HexColor("#CEDADF"))
    canvas.line(44, 34, w-44, 34)
    canvas.setFont("CN",7.3)
    canvas.setFillColor(MUTED)
    canvas.drawString(44, 22, "NJU 社会模拟 | 提案审阅稿 | 尚未提交")
    canvas.drawRightString(w-44, 22, f"{doc.page} / 2")
    if doc.page > 1:
        canvas.setFont("CN", 8)
        canvas.drawString(44, h-29, data["subtitle"])
    canvas.restoreState()
doc = SimpleDocTemplate(str(out), pagesize=A4, rightMargin=44, leftMargin=44,
        topMargin=43, bottomMargin=45, title=data["title"]+"："+data["subtitle"],
        author="NJU independent research project", pageCompression=1)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(out)
assert len(reader.pages) == 2, f"Expected 2 pages, got {len(reader.pages)}"
texts=[p.extract_text() for p in reader.pages]
assert all(len(t)>500 for t in texts)
assert "真实有效性验证为0" in "".join(texts)
safe_path("tmp/pdfs/proposal-extracted.txt").write_text("\n\n".join(texts), encoding="utf-8")
print(json.dumps({"output":str(out),"pages":len(reader.pages),"page_characters":[len(x) for x in texts]},ensure_ascii=False))
