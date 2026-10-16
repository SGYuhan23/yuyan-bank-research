from pathlib import Path
import re,json
from html import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle,Flowable

ROOT=Path(__file__).parent
FONT=ROOT/'fonts'/'NotoSansSC-Regular.ttf'
if not FONT.exists():FONT=ROOT.parent/'report_rewrite_20261016'/'NotoSansSC-Regular.ttf'
pdfmetrics.registerFont(TTFont('CN',str(FONT)))
pdfmetrics.registerFontFamily('CN',normal='CN',bold='CN',italic='CN',boldItalic='CN')
W,H=595.28,841.89;M=43;CW=W-2*M
INK=HexColor('#142e3b');BODY=HexColor('#273e49');TEAL=HexColor('#126e68');MUTED=HexColor('#5c707a');LINE=HexColor('#d9e1e5')
DATA=json.loads((ROOT/'dist/data.json').read_text())

class Chart(Flowable):
    def __init__(self):super().__init__();self.width=CW;self.height=154
    def draw(self):
        c=self.canv;left=30;bottom=25;width=CW-40;height=96
        c.setFont('CN',7.5)
        for val in [-60,-30,0,30,60]:
            y=bottom+(val+60)/120*height
            c.setStrokeColor(LINE);c.line(left,y,left+width,y)
            c.setFillColor(MUTED);c.drawRightString(left-6,y-2,str(val))
        colors=['#177d75','#b9792c','#546fa0']
        for idx,s in enumerate(DATA['supplier']['scenarios'][:3]):
            rows=s['result']['daily'];c.setStrokeColor(HexColor(colors[idx]));c.setLineWidth(1.7)
            p=c.beginPath()
            for i,row in enumerate(rows):
                x=left+i/(len(rows)-1)*width;y=bottom+(row['balance_fen']/1e6+60)/120*height
                if i:p.lineTo(x,y)
                else:p.moveTo(x,y)
            c.drawPath(p)
            c.setFillColor(HexColor(colors[idx]));c.drawString(left+idx*155,137,['现金付款','持票到期','次日贴现成功'][idx])
        c.setFillColor(MUTED);c.drawString(0,121,'万元')
        c.drawString(left,8,'1月1日');c.drawCentredString(left+width*.51,8,'4月19日收款/收票');c.drawRightString(left+width,8,'7月31日')

def parse(chunk):
    lines=chunk.strip().splitlines();out=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+',c) for c in cells):rows.append(cells)
                i+=1
            out.append(('table',rows));continue
        if line=='[[SUPPLIER_CHART]]':out.append(('chart',None));i+=1;continue
        kind='p'
        for pre,k in [('## ','h2'),('# ','h1')]:
            if line.startswith(pre):kind=k;line=line[len(pre):];break
        if line.startswith('http'):kind='url'
        if len(line)<18 and kind=='p':kind='h3'
        out.append((kind,line));i+=1
    return out

def objects(blocks,scale):
    st={k:ParagraphStyle(k,fontName='CN',fontSize=size*scale,leading=leading*scale,textColor=col,wordWrap='CJK',splitLongWords=True) for k,size,leading,col in [('h1',21,29,INK),('h2',12,20,TEAL),('h3',11,17,TEAL),('p',11,19.5,BODY),('url',7.4,10.5,TEAL),('cell',9.8,15.5,BODY)]}
    out=[]
    for kind,val in blocks:
        if kind=='chart':obj=Chart();gap=12
        elif kind=='table':
            n=len(val[0]); widths=[CW/n]*n
            if n==3:widths=[CW*.23,CW*.40,CW*.37]
            if n==4:widths=[CW*.38,CW*.24,CW*.18,CW*.20]
            obj=Table([[Paragraph(escape(x),st['cell']) for x in row] for row in val],colWidths=widths)
            obj.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e9f1f1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7*scale),('BOTTOMPADDING',(0,0),(-1,-1),7*scale),('LINEBELOW',(0,0),(-1,-1),.4,LINE)]));gap=13*scale
        else:
            txt=escape(val)
            if kind=='url':txt=f'<link href="{escape(val,quote=True)}">{txt}</link>'
            obj=Paragraph(txt,st[kind]);gap={'h1':8,'h2':19,'h3':7,'p':12,'url':9}[kind]*scale
        _,height=obj.wrap(CW,H);out.append((obj,height,gap))
    return out

pages=[parse(p) for p in (ROOT/'研究报告.md').read_text().split('<!-- PAGE -->')]
path=ROOT/'dist'/'渝研_产业经营研究报告.pdf';c=canvas.Canvas(str(path),pagesize=(W,H))
c.setTitle('先理解生意，再安排金融服务');c.setAuthor('渝研 · 独立个人研究');log=[]
for i,blocks in enumerate(pages,1):
    scale=1;objs=objects(blocks,scale)
    while sum(h+g for _,h,g in objs)>H-116:
        scale-=.01
        if scale<.90:raise RuntimeError(f'page {i} needs editorial shortening')
        objs=objects(blocks,scale)
    c.setFillColor(TEAL);c.rect(M,H-34,20,3,fill=1,stroke=0)
    c.setFont('CN',8);c.setFillColor(MUTED);c.drawString(M+29,H-34,'渝研 / 产业经营研究');c.drawRightString(W-M,H-34,'2026.10.16')
    y=H-64
    for o,h,g in objs:o.drawOn(c,M,y-h);y-=h+g
    c.setStrokeColor(LINE);c.line(M,43,W-M,43);c.setFont('CN',7);c.setFillColor(MUTED)
    c.drawString(M,28,'公开依据 + 模拟案例 · 不对应真实企业账户或银行经营成果')
    c.drawRightString(W-M,28,f'{i:02d} / {len(pages):02d}');c.showPage()
    log.append(dict(page=i,scale=round(scale,2),bottom=round(y,1)))
c.save();(ROOT/'qa/pdf-layout.json').write_text(json.dumps(log));print(json.dumps(log))
