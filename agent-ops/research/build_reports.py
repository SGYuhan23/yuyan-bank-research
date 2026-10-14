"""Build PDFs, web manifests, editable Markdown and traceable archives from one manuscript."""
import json,shutil,zipfile,hashlib,os
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor,white
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from content import REPORTS,DATA,ROOT,strategies
OUT=ROOT/'output/pdf';WEB=ROOT/'agent-platform/frontend/public/research'
OUT.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('CN',os.environ.get('RESEARCH_CJK_FONT','/System/Library/Fonts/Supplemental/Arial Unicode.ttf')))
W,H=595.28,841.89;M=48;CW=W-2*M
INK=HexColor('#18352e');MUTED=HexColor('#52665f');ACCENT=HexColor('#207761');PALE=HexColor('#eef4f0')
style=ParagraphStyle('body',fontName='CN',fontSize=10.5,leading=19,textColor=INK,wordWrap='CJK',spaceAfter=12)
small=ParagraphStyle('small',parent=style,fontSize=8.5,leading=14)
layouts=[]

def paragraph(c,text,x,y,width,st=style):
 p=Paragraph(escape(str(text)).replace('\n','<br/>'),st);_,height=p.wrap(width,H);p.drawOn(c,x,y-height);return y-height-14

def frame(c,report,n):
 c.setFillColor(HexColor('#fbfaf7'));c.rect(0,0,W,H,fill=1,stroke=0)
 c.setFillColor(MUTED);c.setFont('CN',8);c.drawString(M,H-28,'渝研 / 银行经营研究');c.drawRightString(W-M,H-28,'2026.10.14')
 c.setStrokeColor(HexColor('#d8e3dd'));c.line(M,43,W-M,43)
 c.setFont('CN',7.5);c.drawString(M,28,'独立作品 · 合成情景 · 非银行内部数据或经营承诺');c.drawRightString(W-M,28,f'{n:02d}')

def drawtable(c,t,y):
 count=len(t['headers']);widths=[CW/count]*count
 if count==2:widths=[CW*.36,CW*.64]
 if count==3:widths=[CW*.26,CW*.27,CW*.47]
 rows=[[Paragraph(escape(str(v)),small) for v in row] for row in [t['headers']]+t['rows']]
 table=Table(rows,colWidths=widths,hAlign='LEFT')
 table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),.4,HexColor('#d8e3dd'))]))
 _,h=table.wrap(CW,H);table.drawOn(c,M,y-h);return y-h-20

def chart(c,kind,y):
 h=135;c.setFillColor(white);c.roundRect(M,y-h,CW,h,8,fill=1,stroke=0)
 if kind.startswith('fuling'):
  rows=strategies('正常环境' if kind=='fuling-base' else '组合压力');vals=[r['contribution'] for r in rows];mn=min(0,min(vals));mx=max(0,max(vals));span=max(1,mx-mn)
  left=M+95;length=CW-150;zero=left+(-mn/span)*length
  c.setStrokeColor(MUTED);c.line(zero,y-15,zero,y-h+15)
  for i,r in enumerate(rows):
   yy=y-22-i*22;v=r['contribution'];xx=left+(v-mn)/span*length
   c.setFont('CN',8);c.setFillColor(INK);c.drawString(M+10,yy-3,r['strategy']);c.setFillColor(ACCENT if v>=0 else HexColor('#b66a51'));c.rect(min(zero,xx),yy-7,max(1,abs(xx-zero)),12,fill=1,stroke=0);c.setFillColor(INK);c.drawRightString(W-M-8,yy-3,f'{v:.2f}')
 elif kind=='supplier-cash':
  seq=DATA['supplier']['base']['series'];vals=[p['balance_fen']/1000000 for p in seq];lo=min(vals)-5;hi=max(vals)+5;left=M+38;bottom=y-h+25;cw=CW-60;ch=h-48
  c.setStrokeColor(HexColor('#c6d4cd'));z=bottom+(0-lo)/(hi-lo)*ch;c.line(left,z,left+cw,z)
  p=c.beginPath()
  for i,v in enumerate(vals):
   xx=left+i/(len(vals)-1)*cw;yy=bottom+(v-lo)/(hi-lo)*ch
   (p.moveTo if i==0 else p.lineTo)(xx,yy)
  c.setStrokeColor(ACCENT);c.setLineWidth(2);c.drawPath(p);c.setLineWidth(1);c.setFillColor(MUTED);c.setFont('CN',8);c.drawString(left,y-h+8,seq[0]['date']);c.drawRightString(left+cw,y-h+8,seq[-1]['date']);c.drawString(M+6,y-14,'万元');c.drawString(M+9,z-3,'0')
 else:
  grid=DATA['deposit']['grid'];left=M+45;bottom=y-h+26;cw=(CW-60)/9;ch=(h-45)/11
  for r in grid:
   i=round((float(r['rate'])*10000-50)/25);j=round((float(r['effective_funding_factor'])*100-50)/5)
   v=r['contribution_fen']/1000000;c.setFillColor(HexColor('#4b9b83') if v>=0 else HexColor('#dca88e'));c.rect(left+i*cw,bottom+j*ch,cw-1,ch-1,fill=1,stroke=0)
  c.setFillColor(MUTED);c.setFont('CN',8);c.drawString(left,y-h+9,'利率0.5%');c.drawRightString(left+cw*9,y-h+9,'2.5%');c.drawString(M+3,y-18,'100%');c.drawString(M+8,bottom,'50%')
 return y-h-18

for report in REPORTS:
 filename=report['id']+'-research.pdf';path=OUT/filename;c=canvas.Canvas(str(path),pagesize=(W,H));c.setTitle(report['title']);c.setAuthor('渝研 · 独立研究作品')
 frame(c,report,1);c.setFillColor(INK);c.roundRect(M,370,CW,355,14,fill=1,stroke=0)
 c.setFillColor(HexColor('#b9dacc'));c.setFont('CN',11);c.drawString(M+26,686,report['tag']+' / RESEARCH SERIES')
 title_style=ParagraphStyle('cover',parent=style,fontSize=30,leading=43,textColor=white)
 y=paragraph(c,report['title'],M+26,640,CW-52,title_style)
 paragraph(c,report['subtitle'],M+26,y-15,CW-52,ParagraphStyle('sub',parent=style,fontSize=13,leading=23,textColor=HexColor('#d2e5dc')))
 y=paragraph(c,report['summary'],M,324,CW,ParagraphStyle('lead',parent=style,fontSize=15,leading=26))
 paragraph(c,'阅读路径：先读管理摘要，再看计算与假设，最后核查来源。公开事实、情景输入和研究判断分别标注；不把合成结果包装为真实客户收益。',M,y-10,CW)
 c.showPage();md=['# '+report['title'],'',report['subtitle'],'',report['summary'],'']
 for idx,p in enumerate(report['pages'],2):
  frame(c,report,idx);y=paragraph(c,p['title'],M,H-72,CW,ParagraphStyle('h',parent=style,fontSize=21,leading=30))
  y=paragraph(c,p['lead'],M,y-3,CW,ParagraphStyle('lead',parent=style,fontSize=12,leading=21,textColor=ACCENT))
  if p.get('chart'):y=chart(c,p['chart'],y)
  if p.get('table'):y=drawtable(c,p['table'],y)
  for para in p['paras']:y=paragraph(c,para,M,y,CW)
  if p.get('note'):y=paragraph(c,p['note'],M,y,CW,small)
  layouts.append({'report':report['id'],'page':idx,'bottom':round(y,2)})
  if y<58:raise ValueError(f'Page overflow: {report["id"]} {idx} bottom {y}')
  c.showPage();md+=['## '+p['title'],'',p['lead'],'']+p['paras']+['']
  if p.get('table'):
   t=p['table'];md+=['|'+'|'.join(t['headers'])+'|','|'+'|'.join(['---']*len(t['headers']))+'|']+['|'+'|'.join(map(str,r))+'|' for r in t['rows']]+['']
 frame(c,report,len(report['pages'])+2);y=paragraph(c,'来源、复算与披露',M,H-72,CW,ParagraphStyle('h',parent=style,fontSize=22,leading=31))
 for source in DATA['sources']:
  if source['id'] not in report['sources']:continue
  y=paragraph(c,f'[{source["id"]}] {source["title"].replace('重庆农商行', '公开银行资料：')} / {source["period"]}',M,y,CW)
  y=paragraph(c,f'发布：{source["published"]}；核查：{source["accessed"]}。{source["status"]}。{source["use"]}',M,y,CW,small)
  # Human-readable active link without spilling long encoded URLs into the margin.
  c.setFillColor(ACCENT);c.setFont('CN',9);c.drawString(M,y,'打开官方来源 →');c.linkURL(source['url'],(M,y-3,M+140,y+12),relative=0);y-=33
  md += [f'[{source["id"]}] [{source["title"].replace('重庆农商行', '公开银行资料：')}]({source["url"]})',source['status'],'']
 y=paragraph(c,'计算与来源附件：研究页提供输入数据、CSV、模型源码和运行说明。所有情景结果由确定性代码生成。Agent用于资料检索与审阅辅助；本报告没有虚构访谈、客户成效或银行系统接入。',M,y,CW)
 y=paragraph(c,'研究条件变化后须重新计算。本报告不构成授信、投资或对外业务承诺。',M,y,CW,small)
 if y<58:raise ValueError('Sources page overflow')
 c.save();shutil.copy2(path,WEB/filename);(OUT/(report['id']+'.md')).write_text('\n\n'.join(md),encoding='utf-8')
 report['pdf']='/research/'+filename;report['page_count']=len(report['pages'])+2
 print(filename,report['page_count'],'pages')
(OUT/'reports.json').write_text(json.dumps({'version':DATA['version'],'reports':REPORTS},ensure_ascii=False,indent=2))
(ROOT/'tmp/pdfs').mkdir(parents=True,exist_ok=True)
(ROOT/'tmp/pdfs/layout-check.json').write_text(json.dumps(layouts,indent=2))
