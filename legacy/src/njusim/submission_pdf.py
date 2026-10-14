"""Typeset the submission proposal with the separate document runtime."""
import json, os, sys
from pathlib import Path
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from njusim.io import safe_path
from njusim.guard import install
tmp=safe_path('tmp/pdfs');tmp.mkdir(parents=True,exist_ok=True)
for k in ('TEMP','TMP','TMPDIR'):os.environ[k]=str(tmp)
install()
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
from pypdf import PdfReader
fonts=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
pdfmetrics.registerFont(TTFont('Song',str(fonts/'simsun.ttc'),subfontIndex=0))
pdfmetrics.registerFont(TTFont('Hei',str(fonts/'msyhbd.ttc'),subfontIndex=0))
d=json.loads(safe_path('submission/proposal-submit-20261010.json').read_text(encoding='utf-8'))
out=safe_path('output/pdf/赛道C-蒋成康-校园活动参与的多智能体模拟-开题提案.pdf')
out.parent.mkdir(parents=True,exist_ok=True)
styles={
'p':ParagraphStyle('p',fontName='Song',fontSize=10.7,leading=17.1,firstLineIndent=21.4,wordWrap='CJK',spaceAfter=5),
'h':ParagraphStyle('h',fontName='Hei',fontSize=11.4,leading=18,spaceBefore=8,spaceAfter=5,keepWithNext=True),
'title':ParagraphStyle('title',fontName='Hei',fontSize=18,leading=25,alignment=1,spaceAfter=3),
'sub':ParagraphStyle('sub',fontName='Song',fontSize=12.3,leading=20,alignment=1,spaceAfter=7),
'meta':ParagraphStyle('meta',fontName='Song',fontSize=9.8,leading=16,alignment=1,spaceAfter=2)}
story=[Paragraph(escape(d['title']),styles['title']),Paragraph(escape(d['subtitle']),styles['sub']),Paragraph(escape(d['author']),styles['meta']),Paragraph(escape(d['track']),styles['meta']),Spacer(1,7)]
for i,blocks in enumerate(d['pages']):
 if i:story.append(PageBreak())
 for kind,text in blocks:story.append(Paragraph(escape(text),styles[kind]))
def footer(c,doc):
 c.setFont('Song',9);c.drawCentredString(A4[0]/2,27,str(doc.page))
doc=SimpleDocTemplate(str(out),pagesize=A4,leftMargin=51,rightMargin=51,topMargin=42,bottomMargin=43,title=d['title']+'：'+d['subtitle'],author='蒋成康',pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
r=PdfReader(out)
assert len(r.pages)==2,len(r.pages)
assert out.stat().st_size<20_000_000
text='\n'.join(p.extract_text() for p in r.pages)
for phrase in ['研究问题','人群','环境','行为','数据来源','尚未取得']:
 assert phrase in text,phrase
for phrase in ['审阅稿','待确认','real_observed','B0','B2','9c3ac77']:
 assert phrase not in text,phrase
print(json.dumps({'path':str(out),'pages':len(r.pages),'bytes':out.stat().st_size},ensure_ascii=False))
