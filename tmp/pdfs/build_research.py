from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
import pypdfium2 as pdfium
from pypdf import PdfReader

root = Path(__file__).resolve().parents[2]
source = root / 'output/pdf/mizan-university-applications-research.md'
target = source.with_suffix('.pdf')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyResearch', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=8, textColor=colors.HexColor('#263642')))
styles['Title'].fontSize = 23
styles['Title'].leading = 28
styles['Title'].alignment = TA_LEFT
styles['Title'].textColor = colors.HexColor('#123c45')
styles['Heading2'].textColor = colors.HexColor('#123c45')
styles['Heading2'].spaceBefore = 14
styles['Heading3'].spaceBefore = 10
styles['Heading3'].fontSize = 11
styles['Heading3'].leading = 15

def markup(text):
    text = escape(text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', lambda m: '<link href="'+m.group(2)+'" color="#146c80"><u>'+m.group(1)+'</u></link>', text)
    return text.replace('`', '')

story = []
for block in source.read_text(encoding='utf-8').split('\n\n'):
    if not block.strip():
        continue
    if block.startswith('# '):
        story.append(Paragraph(markup(block[2:]), styles['Title']))
        story.append(Spacer(1, 8))
    elif block.startswith('### '):
        story.append(Paragraph(markup(block[4:]), styles['Heading3']))
    elif block.startswith('## '):
        story.append(Paragraph(markup(block[3:]), styles['Heading2']))
    elif block.startswith('- '):
        for line in block.splitlines():
            story.append(Paragraph(markup(line[2:]), styles['BodyResearch'], bulletText='-'))
    else:
        story.append(Paragraph(markup(block.replace('\n',' ')), styles['BodyResearch']))

def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor('#d5dfe1'))
    canvas.line(42, 39, 553, 39)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#52666e'))
    canvas.drawString(42, 25, 'Mizan | Research brief | 5 October 2026')
    canvas.drawRightString(553, 25, str(doc.page))

SimpleDocTemplate(str(target), pagesize=(595.28,841.89), rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=54, title='Mizan university scheduling applications research', author='Mizan research brief').build(story,onFirstPage=footer,onLaterPages=footer)
pdf = pdfium.PdfDocument(str(target))
print(f'Created {target}: {len(pdf)} pages')
for index, page in enumerate(pdf):
    page.render(scale=1.1).to_pil().save(str(root / f'tmp/pdfs/research-page-{index+1}.png'))
    assert PdfReader(str(target)).pages[index].extract_text().strip(), f'Empty page {index+1}'
print('Text extraction checked; all pages rendered.')
