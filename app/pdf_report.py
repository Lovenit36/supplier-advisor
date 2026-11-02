"""Evidence-first PDF report generated on the server from recomputed comparisons."""
import io
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm

NAVY=colors.HexColor('#102442'); BLUE=colors.HexColor('#1259e9')
GRAY=colors.HexColor('#526079'); LIGHT=colors.HexColor('#f0f4fc')

def render_pdf(report):
    out=io.BytesIO()
    doc=SimpleDocTemplate(out,pagesize=(210*mm,297*mm),rightMargin=17*mm,leftMargin=17*mm,topMargin=16*mm,bottomMargin=18*mm,title='Supplier offer & installation comparison',author='Independent Supplier Advisor Experiment')
    style=getSampleStyleSheet()
    style.add(ParagraphStyle(name='MainT',fontName='Helvetica-Bold',fontSize=17,leading=21,textColor=NAVY,spaceAfter=8))
    style.add(ParagraphStyle(name='SubT',fontName='Helvetica-Bold',fontSize=11,leading=14,textColor=NAVY,spaceBefore=12,spaceAfter=6))
    style.add(ParagraphStyle(name='BodyT',fontName='Helvetica',fontSize=8.6,leading=12,textColor=NAVY,spaceAfter=5))
    style.add(ParagraphStyle(name='SmallT',fontName='Helvetica',fontSize=7.5,leading=10,textColor=GRAY,spaceAfter=3,wordWrap='CJK'))
    style.add(ParagraphStyle(name='FooterT',fontName='Helvetica',fontSize=7,leading=10,textColor=GRAY,alignment=TA_CENTER))
    def P(text,name='BodyT'):return Paragraph(escape(str(text)),style[name])
    def money(v):return 'Not confirmed' if v is None else f'EUR {v:,.2f}'
    def table(rows,widths=None):
        t=Table(rows,colWidths=widths,hAlign='LEFT',repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('TEXTCOLOR',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#fafbfe')]),('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#d9e2f1')),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('VALIGN',(0,0),(-1,-1),'TOP')]))
        return t
    story=[P('SUPPLIER OFFER & COMPATIBILITY ADVISOR','MainT'),P('Independent candidate-built growth experiment | Preliminary pump screening','SmallT'),P('Created '+datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')+' | Supplier figures supplied by the user, not verified supplier pricing.','SmallT'),Spacer(1,7),P(report['title'],'SubT'),P(report['disclaimer']),P(report['price_message'])]
    ref=report.get('existing_reference')
    if ref:
        story.append(P('Existing pump reference: '+ref['model']+' ('+str(ref['length_mm'])+' mm). These are published dimensions; actual site measurements must be confirmed.','SmallT'))
    story.append(P('Side-by-side costs','SubT'))
    r0,r1=report['results']
    def cell(x):return P(x,'SmallT')
    rows=[list(map(cell,['Cost element','Offer A','Offer B']))]
    for label,k in [('Supplier','supplier_name'),('Pump model','model_text'),('Article','article_number')]:
        rows.append([cell(label),cell((r0['offer'].get(k) or 'Not confirmed') if label=='Supplier' else (r0['product']['model'] if label=='Pump model' and r0['product'] else r0['offer'].get(k,'Unknown'))),cell((r1['offer'].get(k) or 'Not confirmed') if label=='Supplier' else (r1['product']['model'] if label=='Pump model' and r1['product'] else r1['offer'].get(k,'Unknown')))])
    for label,k in [('Pump(s), gross','purchase_gross'),('Delivery, gross','delivery_gross'),('Extra parts, gross','extras_gross'),('Extra labour, gross','labour_gross'),('Known subtotal, gross','known_subtotal_gross'),('Total installed cost','total_gross')]:
        rows.append([cell(label),cell(money(r0['cost'][k])),cell(money(r1['cost'][k]))])
    rows.append([cell('Fit status'),cell(r0['fit']['status'].replace('_',' ')),cell(r1['fit']['status'].replace('_',' '))])
    story.append(table(rows,[51*mm,62*mm,62*mm]))
    for idx,r in enumerate(report['results']):
        story.append(P(f'Offer {"A" if idx==0 else "B"}: manufacturer checks','SubT'))
        story.append(P('Model: '+(r['product']['brand']+' '+r['product']['model'] if r['product'] else r['offer']['model_text'] or 'Unverified')+' | Article: '+(r['product']['article'] if r['product'] else 'Not verified'),'SmallT'))
        if r.get('identity_issue'):story.append(P('Identity issue: '+r['identity_issue']))
        for c in r['fit']['checks']:
            story.append(P(c['label']+' ['+c['status'].replace('_',' ')+']: '+c['detail'],'SmallT'))
            if c.get('source'):
                story.append(Paragraph('Manufacturer: <link href="'+escape(c['source'],{'"':'&quot;'})+'" color="#1259e9">'+escape(c['source'])+'</link>',style['SmallT']))
        if r['cost']['questions']:
            story.append(P('Costs still to confirm: '+'; '.join(r['cost']['questions']),'SmallT'))
    story.append(P('Other documented models to investigate','SubT'))
    if report['alternatives']:
        for x in report['alternatives']:
            p=x['product'];story.append(P(p['brand']+' '+p['model']+' (article '+p['article']+') - '+x['status'],'SmallT'))
            story.append(Paragraph('<link href="'+escape(p['details'],{'"':'&quot;'})+'" color="#1259e9">Official product evidence</link>',style['SmallT']))
    else:story.append(P('No mechanically matching alternative in this small catalogue.','SmallT'))
    story.append(P('Important limitations','SubT'))
    story.append(P('A mechanically matching product is not automatically suitable. Verify the duty-point flow and head together from the manufacturer pump curve, wiring and controls, installation position, site space, fittings, pressure, temperature and exact commercial quotation. Missing costs are never treated as EUR 0. No adapter or full lifetime saving is assumed.'))
    story.append(P('No Plancraft integration is claimed. The free tool does not replace a professional installation assessment.','SmallT'))
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',7);canvas.setFillColor(GRAY);canvas.drawCentredString(105*mm,10*mm,f'Independent supplier adviser | Page {doc.page} | Not an installation approval');canvas.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return out.getvalue()
