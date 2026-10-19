from pathlib import Path
from io import BytesIO
import json,html
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader,PdfWriter,Transformation
R=Path(__file__).resolve().parents[1];S=R/'article/supplementary_layout'
def main():
 pdfmetrics.registerFont(TTFont('LayoutCaption','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('LayoutCaptionBold','C:/Windows/Fonts/arialbd.ttf'));pdfmetrics.registerFontFamily('LayoutCaption',normal='LayoutCaption',bold='LayoutCaptionBold')
 style=ParagraphStyle('Caption',fontName='LayoutCaption',fontSize=13,leading=17,spaceAfter=0)
 manifest=json.loads((S/'manifest.json').read_text());count=0
 for row in manifest['views']:
  p=R/row['figure'];source=PdfReader(BytesIO(p.read_bytes()))
  if source.metadata.get('/CaptionedLayout')=='true':continue
  assert len(source.pages)==1,p
  pg=source.pages[0];w=float(pg.mediabox.width);h=float(pg.mediabox.height);body=Paragraph('<b>Figure S%d.</b> %s'%(row['actor_index']+1,html.escape(row['caption_text'])),style);cw,ch=body.wrap(w,1000);bottom=ch+48;output=PdfWriter();target=output.add_blank_page(width=w+48,height=h+bottom+24);target.merge_transformed_page(pg,Transformation().translate(24,bottom),over=True)
  buf=BytesIO();c=canvas.Canvas(buf,pagesize=(w+48,h+bottom+24),pageCompression=1);body.drawOn(c,24,24);c.showPage();c.save();target.merge_page(PdfReader(buf).pages[0]);target.compress_content_streams();output.add_metadata({'/Title':'EventSpikeSeg Supplementary Figure S%d'%(row['actor_index']+1),'/CaptionedLayout':'true'});dest=p.with_suffix('.captioned.tmp')
  output.compress_identical_objects(remove_duplicates=True,remove_unreferenced=True)
  with dest.open('wb') as fh:output.write(fh)
  dest.replace(p);count+=1
 print('Embedded captions in',count,'individual vector PDFs.')
if __name__=='__main__':main()
