"""Convert the existing report source to native editable Word content."""
from pathlib import Path
from html.parser import HTMLParser
import json
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from reportlab.platypus import Paragraph, Table, Image, Preformatted, PageBreak, Spacer

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'scripts/build_pdf.py'
namespace = {'__file__': str(source)}
# Build the same content model without modifying the original PDF.
exec(compile(source.read_text(encoding='utf-8').split('\ndef footer(')[0], str(source), 'exec'), namespace)
flow = namespace['flow']
doc = Document()
for style in doc.styles:
    # The bundled Word template can carry a decorative rule on Title.
    for border in style.element.xpath('.//w:pBdr'):
        border.getparent().remove(border)
section = doc.sections[0]
section.page_width = Pt(595.28)
section.page_height = Pt(841.89)
section.left_margin = section.right_margin = Pt(48)
section.top_margin = Pt(48)
section.bottom_margin = Pt(46)
section.footer_distance = Pt(24)
for name in ['Normal', 'Title', 'Heading 1', 'Heading 2', 'Caption']:
    style = doc.styles[name]
    style.font.name = 'Arial'
    style.font.color.rgb = RGBColor(0, 0, 0)
normal = doc.styles['Normal']
normal.font.size = Pt(10)
normal.paragraph_format.line_spacing = Pt(14)
normal.paragraph_format.space_after = Pt(9)
for name,size,leading,after in [('Title',28,32,18),('Heading 1',18,22,14),('Heading 2',12,16,8)]:
    style = doc.styles[name]
    style.font.size = Pt(size)
    style.font.bold = True
    style.paragraph_format.line_spacing = Pt(leading)
    style.paragraph_format.space_after = Pt(after)
    style.paragraph_format.space_before = Pt(10 if name == 'Heading 2' else 0)
    style.paragraph_format.keep_with_next = True
doc.core_properties.title = 'Integridad del carrito OWASP Juice Shop'
doc.core_properties.subject = 'Informe de prueba de vulnerabilidad del flujo de negocio'
doc.core_properties.author = 'Laboratorio de pruebas'

class RichText(HTMLParser):
    def __init__(self, paragraph):
        super().__init__(convert_charrefs=True)
        self.p = paragraph
        self.bold = 0
        self.href = None
    def handle_starttag(self, tag, attrs):
        if tag in ('b','strong'): self.bold += 1
        elif tag == 'br': self.p.add_run().add_break()
        elif tag == 'link': self.href = dict(attrs).get('href')
    def handle_endtag(self, tag):
        if tag in ('b','strong'): self.bold = max(0,self.bold-1)
        elif tag == 'link': self.href = None
    def handle_data(self, data):
        if not data: return
        if self.href:
            link = OxmlElement('w:hyperlink')
            link.set(qn('r:id'), self.p.part.relate_to(self.href, RT.HYPERLINK, is_external=True))
            run = OxmlElement('w:r')
            props = OxmlElement('w:rPr')
            color = OxmlElement('w:color'); color.set(qn('w:val'),'007E87'); props.append(color)
            underline = OxmlElement('w:u'); underline.set(qn('w:val'),'single'); props.append(underline)
            run.append(props)
            text = OxmlElement('w:t'); text.text = data; run.append(text)
            link.append(run); self.p._p.append(link)
        else:
            run = self.p.add_run(data)
            if self.bold: run.bold = True

def rich(p, markup):
    RichText(p).feed(markup)

def paragraph(obj, cell=None):
    name = obj.style.name
    style = {'TitleCustom':'Title','HeadingCustom':'Heading 1','SubCustom':'Heading 2'}.get(name,'Normal')
    p = cell.paragraphs[0] if cell else doc.add_paragraph(style=style)
    p.style = doc.styles[style]
    if name == 'SmallCustom' or cell:
        p.paragraph_format.line_spacing = Pt(11)
        p.paragraph_format.space_after = Pt(5 if not cell else 0)
    rich(p, obj.text)
    if name == 'SmallCustom' or cell:
        for r in p.runs: r.font.size = Pt(8.5)
        pPr=p._p.get_or_add_pPr()
        # Set paragraph default run size so hyperlinks inherit the same size.
        rPr=OxmlElement('w:rPr'); sz=OxmlElement('w:sz');sz.set(qn('w:val'),'17');rPr.append(sz);pPr.append(rPr)
    p.paragraph_format.widow_control = True
    return p

tables=images=0
for obj in flow:
    if isinstance(obj, Paragraph): paragraph(obj)
    elif isinstance(obj, PageBreak): doc.add_page_break()
    elif isinstance(obj, Spacer):
        # Table and image spacing is handled explicitly below.
        if obj.height >= 14:
            p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0)
            p.paragraph_format.line_spacing=Pt(obj.height)
            p.add_run().font.size=Pt(1)
    elif isinstance(obj, Preformatted):
        p=doc.add_paragraph()
        p.paragraph_format.line_spacing=Pt(11)
        p.paragraph_format.space_after=Pt(12)
        p.paragraph_format.keep_together=True
        r=p.add_run('\n'.join(obj.lines));r.font.name='Courier New';r.font.size=Pt(8)
    elif isinstance(obj, Table):
        tables+=1
        rows=obj._cellvalues
        t=doc.add_table(rows=len(rows),cols=len(rows[0]))
        t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.LEFT
        widths=obj._argW
        for col,width in zip(t.columns,widths):col.width=Pt(width)
        props=t._tbl.tblPr
        borders=OxmlElement('w:tblBorders')
        for side in ['top','left','bottom','right','insideH','insideV']:
            border=OxmlElement('w:'+side)
            for attr,value in [('val','single'),('sz','4'),('color','D9D9D9')]:border.set(qn('w:'+attr),value)
            borders.append(border)
        props.append(borders)
        for i,row in enumerate(rows):
            trPr=t.rows[i]._tr.get_or_add_trPr()
            cant=OxmlElement('w:cantSplit');trPr.append(cant)
            if i==0:trPr.append(OxmlElement('w:tblHeader'))
            for j,value in enumerate(row):
                cell=t.cell(i,j);cell.width=Pt(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                cp=cell._tc.get_or_add_tcPr()
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'DCEAF2' if i==0 else ('F4F7F9' if i%2==0 else 'FFFFFF'));cp.append(shade)
                margins=OxmlElement('w:tcMar')
                for edge,size in [('top',100),('bottom',80),('left',150),('right',150)]:
                    e=OxmlElement('w:'+edge);e.set(qn('w:w'),str(size));e.set(qn('w:type'),'dxa');margins.append(e)
                cp.append(margins)
                p=paragraph(value,cell)
                if i==0:
                    for run in p.runs:run.bold=True
                if widths[j]<90:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=Pt(7);p.add_run().font.size=Pt(1)
    elif isinstance(obj, Image):
        images+=1
        p=doc.add_paragraph();p.paragraph_format.space_after=Pt(9);p.paragraph_format.line_spacing=1
        inline=p.add_run().add_picture(obj.filename,width=Pt(obj.drawWidth),height=Pt(obj.drawHeight))
        inline._inline.docPr.set('descr',{'allure-overview.png':'Resumen real de Allure con una prueba aprobada','allure-case.png':'Pasos y adjuntos del caso en Allure','zap-report.png':'Resumen del reporte pasivo ZAP'}.get(Path(obj.filename).name,'Evidencia del reporte'))

fp=section.footer.paragraphs[0]
fp.paragraph_format.space_after=Pt(0)
fp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=fp.add_run('TC-BL-001 | Juice Shop local | 20/10/2026 | Página ');r.font.size=Pt(8)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');fp._p.append(field)
for r in fp.runs:r.font.color.rgb=RGBColor.from_string('546577')
out=ROOT/'output/word/informe-vulnerabilidad-juice-shop.docx'
out.parent.mkdir(parents=True,exist_ok=True)
doc.save(out)
print(json.dumps({'path':str(out),'tables':tables,'images':images,'paragraphs':len(doc.paragraphs)},ensure_ascii=False))
